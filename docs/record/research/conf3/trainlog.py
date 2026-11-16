"""Confirmatory 3 training logs: checked, then turned into the series that TensorBoard and the DRL page both show. usage: trainlog.py train_dir out.json
Training logs say how training went, not how good a policy is. Every series states its unit and what it covers."""
import json
import math
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from common import ENVS, FIRST_WORKER, LEARNERS, LEVELS, PER_WORKER, SEED0, UPDATES
from v5b.fleet import perturb as pt

ZONES = ("upstream", "merge1", "downstream_incl_merge2")
LEVEL_S = ("1.6s", "1.2s", "1.0s", "0.8s")


def slowdown(seed: int) -> dict:
    """The slowdown each training episode drew, from the training code itself: the draw depends on the seed only."""
    return pt.Perturb(SimpleNamespace(warm=0.0, plant={}), {"kind": "random"}, seed).s


def finite(x) -> bool:
    return isinstance(x, (int, float)) and math.isfinite(x)


def load(d: Path, i: int) -> tuple:
    U = [json.loads(x) for x in open(d / f"C{i}_updates.jsonl")]
    E = [json.loads(x) for x in open(d / f"C{i}_episodes.jsonl")]
    P = json.load(open(d / f"C{i}_pilot.json"))
    return U, E, P


def check(d: Path) -> list:
    bad = []
    for i in range(LEARNERS):
        for k in ("updates", "episodes"):
            if (d / f"C{i}_{k}.attempt1").exists():
                bad.append(f"C{i}: a crashed first attempt exists; only the final attempt is used")
        U, E, P = load(d, i)
        if [x["u"] for x in U] != list(range(UPDATES)):
            bad.append(f"C{i}: updates are not 0-{UPDATES - 1} once each")
        if len({x["scale"] for x in U}) != 1:
            bad.append(f"C{i}: critic scale changes")
        for x in U:
            for k in ("r", "entropy", "value_loss", "kl", "clipfrac", "ev", "n", "scale", "wall"):
                if not finite(x.get(k)):
                    bad.append(f"C{i} u{x['u']}: {k} missing or not finite")
        # environment k starts at episode k of its worker's block (c_train: n_ep0 = k); the pilot takes the first
        workers = [(FIRST_WORKER + i * ENVS + k, k) for k in range(ENVS)]
        want = {SEED0 + w * PER_WORKER + k + n for w, k in workers for n in range(1, UPDATES + 1)}
        pilot = {SEED0 + w * PER_WORKER + k for w, k in workers}
        if sorted(P["seeds"]) != sorted(pilot):
            bad.append(f"C{i}: pilot seeds are not each environment's first episode")
        if {e["seed"] for e in E} != want or len(E) != len(want):
            bad.append(f"C{i}: episode seeds are not each environment's next {UPDATES} episodes, once each")
        by_u = {}
        for e in E:
            by_u.setdefault(e["u"], []).append(e)
            if e["steps"] != 1500:
                bad.append(f"C{i} seed {e['seed']}: {e['steps']} steps")
            if e["out_E30"] or e["out_b3"]:
                bad.append(f"C{i} seed {e['seed']}: network counts present, but training does not measure them")
            if e["offset_s"]:
                bad.append(f"C{i} seed {e['seed']}: the merge-cap actuator acted")
            if len(e["lv"]) != 12 or min(e["lv"]) < 0:
                bad.append(f"C{i} seed {e['seed']}: level counts malformed")
        for u in range(UPDATES):
            if sorted(e["q"] for e in by_u.get(u, [])) != sorted(LEVELS):
                bad.append(f"C{i} u{u}: not one episode per demand level")
    return bad


def series(d: Path) -> dict:
    out = {"learners": {}, "levels": list(LEVELS)}
    for i in range(LEARNERS):
        U, E, P = load(d, i)
        s = U[0]["scale"]
        ppo = {
            "reward_per_decision": [x["r"] for x in U],
            "entropy": [x["entropy"] for x in U],
            "value_loss_scaled": [x["value_loss"] for x in U],
            "value_loss_reward_units": [x["value_loss"] * s * s for x in U],
            "explained_variance": [x["ev"] for x in U],
            "approx_kl": [x["kl"] for x in U],
            "clip_fraction": [x["clipfrac"] for x in U],
            "decisions": [x["n"] for x in U],
            "seconds_per_update": [None] + [b["wall"] - a["wall"] for a, b in zip(U, U[1:])],
        }
        lv = {f"{z}/{l}": [None] * UPDATES for z in ZONES for l in LEVEL_S}
        acc = {}
        for e in E:
            a = acc.setdefault(e["u"], np.zeros(12))
            a += np.array(e["lv"], float)
        for u, a in acc.items():
            a = a.reshape(3, 4)
            for zi, z in enumerate(ZONES):
                tot = a[zi].sum()
                for li, l in enumerate(LEVEL_S):
                    lv[f"{z}/{l}"][u] = float(a[zi, li] / tot) if tot else None
        traffic = {}
        for q in LEVELS:
            t = {k: [None] * UPDATES for k in ("vehicles_into_road4", "vehicle_seconds_in_system", "mean_speed_kmh", "ttc_below_3s_merge1_lanes", "braking_3ms2_merge1_lanes", "collisions", "level_moves", "level_reversals", "slowdown_limit_kmh")}
            for e in E:
                if e["q"] != q:
                    continue
                u, sd = e["u"], slowdown(e["seed"])
                t["vehicles_into_road4"][u] = e["passed"]
                t["vehicle_seconds_in_system"][u] = e["N"]
                t["mean_speed_kmh"][u] = e["mean_v"] / e["steps"] * 3.6
                t["ttc_below_3s_merge1_lanes"][u] = e["E30"]
                t["braking_3ms2_merge1_lanes"][u] = e["brake3"]
                t["collisions"][u] = e["collisions"]
                t["level_moves"][u] = e["changes"]
                t["level_reversals"][u] = e["reversals"]
                t["slowdown_limit_kmh"][u] = sd.get("limit_kmh", 0.0) if sd["kind"] == "slowdown" else 0.0
            traffic[str(int(q))] = t
        out["learners"][f"C{i}"] = {"scale": s, "ppo": ppo, "levels": lv, "traffic": traffic, "pilot_n": P["n"]}
    return out


if __name__ == "__main__":
    d, out = Path(sys.argv[1]), Path(sys.argv[2])
    bad = check(d)
    print("checks:", "all pass" if not bad else bad[:20], flush=True)
    if bad:
        sys.exit(1)
    json.dump(series(d), open(out, "w"))
    print("written", out, flush=True)
