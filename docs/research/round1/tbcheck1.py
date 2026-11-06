"""Round 1 training checks, read from the TensorBoard event files (V394): every update once, every tag present and finite, the expected
seeds with one episode per level, constant critic scales, the dual variable's freeze, the settings as pinned, and the collapse rule.
usage: tbcheck1.py TRAIN_DIR KIND STAGE0B_JSON. Exit 1 if settings differ, a log check fails, more than one learner collapses, or 2C's
lambda sits at its cap in at least 3 of 5 learners."""
import json
import sys
from pathlib import Path

import numpy as np

from common1 import ENVS, FIRST_WORKER, GAMMA, LAM, LEARNERS, LEVELS, NET_SEED, PER_WORKER, SEED0, UPDATES, env_for
from v5b.fleet import c_train as ct

BASE_TAGS = ("ppo/reward_per_decision", "ppo/entropy", "ppo/value_loss", "ppo/kl", "ppo/clipfrac", "ppo/ev", "ppo/n", "ppo/scale", "ppo/wall_s")
LAGR_TAGS = ("cost/per_decision", "cost/value_loss", "cost/ev", "cost/scale", "lagr/lambda")


def read(d: Path) -> dict:
    """tag -> list of (step, value) in file order."""
    from tensorboard.backend.event_processing.event_accumulator import EventAccumulator
    acc = EventAccumulator(str(d), size_guidance={"scalars": 0})
    acc.Reload()
    return {t: [(e.step, e.value) for e in acc.Scalars(t)] for t in acc.Tags()["scalars"]}


def expected_seed(learner: int, env: int, u: int, seed0: int = SEED0, per: int = PER_WORKER, n_envs: int = ENVS) -> int:
    """Env i of a learner runs its pilot as episode i, so update u is its episode i + 1 + u."""
    return seed0 + (FIRST_WORKER + learner * n_envs + env) * per + env + 1 + u


def expected_level(env: int, u: int, levels: tuple = LEVELS) -> float:
    """The environment picks levels[episode mod number of levels]."""
    return float(levels[(env + 1 + u) % len(levels)])


def log_faults(S: dict, kind: str, learner: int, updates: int = UPDATES, levels: tuple = LEVELS, seed0: int = SEED0) -> list:
    out = []
    need = list(BASE_TAGS) + [f"ep/e{e}/{k}" for e in range(ENVS) for k in (*ct.EP_KEYS, "delay_s", "q")]
    need += list(LAGR_TAGS) if kind == "lagr" else []
    need += [f"ep/e{e}/offset_moves" for e in range(ENVS)] if kind == "res" else []
    out += [f"missing tag {t}" for t in need if t not in S]
    steps = list(range(updates))
    for t, xs in S.items():
        if [s for s, _ in xs] != steps:
            out.append(f"{t}: updates are not 0-{updates - 1} once each")
        if not all(np.isfinite(v) for _, v in xs):
            out.append(f"{t}: non-finite value")
    for e in range(ENVS):
        for tag, want in (("seed", [expected_seed(learner, e, u, seed0) for u in range(updates)]), ("q", [expected_level(e, u, levels) for u in range(updates)])):
            got = [v for _, v in S.get(f"ep/e{e}/{tag}", [])]
            if got != want:
                bad = next((u for u, (a, b) in enumerate(zip(got, want)) if a != b), len(got))
                out.append(f"env {e}: {tag} differs from update {bad}")
    for t in ("ppo/scale", "cost/scale"):
        if t in S and len({v for _, v in S[t]}) != 1:
            out.append(f"{t} is not constant")
    if kind == "lagr" and "lagr/lambda" in S:
        lam = [v for _, v in S["lagr/lambda"]]
        cfg = ct.LAGR
        if any(abs(x - cfg["start"]) > 1e-6 for x in lam[:cfg["freeze"] + 1]):
            out.append("lambda moved during its freeze")
        if min(lam) < -1e-6 or max(lam) > cfg["cap"] + 1e-6:
            out.append("lambda outside [0, cap]")
    return out


def collapse(r: np.ndarray, kind: str) -> tuple:
    """a = |mean 401-500 - mean 301-400|, b = mean 401-500 - mean 1-50, sigma = SD over 101-500 (1-based). Pass: a <= 0.4 sigma and,
    except for 2C, b >= 0."""
    a = abs(r[400:500].mean() - r[300:400].mean())
    b = r[400:500].mean() - r[:50].mean()
    s = r[100:500].std()
    return a, b, s, a <= 0.4 * s and (kind == "lagr" or b >= 0.0)


def at_cap(S: dict) -> bool:
    lam = np.array([v for _, v in S["lagr/lambda"]])
    return bool(np.all(lam[-100:] >= ct.LAGR["cap"] - 1e-6))


def settings_differ(cfg: dict, i: int, kind: str, d_ref: dict | None, refs: dict) -> list:
    want = {"learner": i, "updates": UPDATES, "n_envs": ENVS, "gamma": GAMMA, "lam": LAM, "levels": list(LEVELS), "seed": NET_SEED + i,
            "workers": [FIRST_WORKER + i * ENVS + k for k in range(ENVS)], "env": {**ct.ENV, **env_for(kind, refs)}, "inputs": ct.INPUT_NORM, "log": "tensorboard",
            "lagr": {**ct.LAGR, "ref": d_ref} if kind == "lagr" else None}
    return [k for k, v in want.items() if cfg.get(k) != v]


if __name__ == "__main__":
    d, kind = Path(sys.argv[1]), sys.argv[2]
    s0 = json.load(open(sys.argv[3]))
    d_ref = s0["d_ref"] if kind == "lagr" else None
    failed, wrong, capped = [], [], 0
    for i in range(LEARNERS):
        S = read(d / "tb" / f"C{i}")
        faults = log_faults(S, kind, i)
        bad = settings_differ(json.load(open(d / f"C{i}_config.json")), i, kind, d_ref, s0["refs"])
        r = np.array([v for _, v in S["ppo/reward_per_decision"]], dtype=np.float64)
        a, b, s, ok = collapse(r, kind)
        cap = kind == "lagr" and at_cap(S)
        capped += cap
        print(f"C{i}: logs {'ok' if not faults else faults[:5]}; collapse a {a:.4f} b {b:+.4f} sigma {s:.4f} {'ok' if ok else 'FAILS'}; settings {'as pinned' if not bad else bad}"
              + (f"; lambda end {S['lagr/lambda'][-1][1]:.3f}{' AT CAP' if cap else ''}" if kind == 'lagr' else ""), flush=True)
        failed += [] if ok else [i]
        wrong += [i] if bad or faults else []
    out = 1 if wrong or len(failed) > 1 or capped >= 3 else 0
    print(f"{kind}: {'PASS' if not out else 'OUT OF THE ROUND'}; collapsed {failed}, log or settings faults {wrong}, lambda at cap {capped}", flush=True)
    sys.exit(out)
