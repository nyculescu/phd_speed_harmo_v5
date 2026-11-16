"""Training status of every DRL run behind round 1 and round 2, from their stored logs (report-only, V468): TensorBoard event files
(V394) for v3w and the candidates, the JSON lines of baseline-v3. Per learner: reward and PPO diagnostics at the start and the end, round 1's
collapse rule (tbcheck1.collapse), the trend of the last 100 updates, entropy against its maximum, and what the policy did in training
(level changes, reversals, the V2V share, the level mix). ASCII curves; the checkpoints validation chose are marked.

usage: trainreport2.py RUNS_DIR OUT_DIR [VALIDATION_JSON]"""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent.parent), str(HERE), str(HERE.parent / "round1")]

GROUPS = {"baseline-v3": ("jsonl", "baseline_v3/conf3/train"), "v3w": ("tb", "round1_remote/out/train_v3w/tb"),
          "res": ("tb", "round1_remote/out/train_res/tb"), "attr": ("tb", "round1_remote/out/train_attr/tb"), "lagr": ("tb", "round1_remote/out/train_lagr/tb"),
          **{k: ("tb", f"round2_remote/train_{k}/tb") for k in ("2b", "1b", "1d", "ahead", "rep")}}
PPO = ("reward_per_decision", "entropy", "kl", "clipfrac", "ev", "value_loss")
RAMP = " .:-=+*#%@"
N_ACT = {"res": 3}     # 3B acts by an offset of -1, 0 or +1; every other learner picks one of 4 levels


def read_tb(d: Path) -> tuple:
    """(ppo: tag -> array over updates, episodes: list per update of dicts per environment slot)."""
    from tensorboard.backend.event_processing.event_accumulator import EventAccumulator
    acc = EventAccumulator(str(d), size_guidance={"scalars": 0})
    acc.Reload()
    tags = acc.Tags()["scalars"]
    ppo = {k: np.array([e.value for e in acc.Scalars(f"ppo/{k}")]) for k in PPO if f"ppo/{k}" in tags}
    slots = sorted({t.split("/")[1] for t in tags if t.startswith("ep/")})
    n = len(next(iter(ppo.values())))
    eps = [[{} for _ in slots] for _ in range(n)]
    for i, s in enumerate(slots):
        for t in (t for t in tags if t.startswith(f"ep/{s}/")):
            k = t.split("/", 2)[2]
            for e in acc.Scalars(t):
                if e.step < n:
                    eps[e.step][i][k] = e.value
    for u in eps:
        for ep in u:
            ep["lv"] = [ep.pop(f"lv{j}") for j in range(12) if f"lv{j}" in ep]
    return ppo, eps


def read_jsonl(d: Path, i: int) -> tuple:
    U = [json.loads(x) for x in (d / f"C{i}_updates.jsonl").read_text().splitlines()]
    ppo = {"reward_per_decision": np.array([u["r"] for u in U]), **{k: np.array([u[k] for u in U]) for k in PPO[1:] if k in U[0]}}
    E = [json.loads(x) for x in (d / f"C{i}_episodes.jsonl").read_text().splitlines()]
    by_u = {}
    for e in E:
        by_u.setdefault(e["u"], []).append(e)
    return ppo, [by_u.get(u, []) for u in range(len(U))]


def spark(x: np.ndarray, width: int = 50) -> str:
    x = np.asarray(x, float)
    b = np.array_split(x, width)
    m = np.array([c.mean() for c in b if len(c)])
    lo, hi = m.min(), m.max()
    return "".join(RAMP[int((v - lo) / (hi - lo) * (len(RAMP) - 1)) if hi > lo else 0] for v in m) + f"  [{lo:.3g} .. {hi:.3g}]"


def behaviour(eps: list) -> dict:
    """What the policy did in training, first 50 against last 50 updates: level changes per 1,000 ALKS-seconds, reversals per change,
    ignored requests per change, V2V share of ALKS-seconds, and the level mix with V2V on (summed over zones)."""
    def part(us):
        E = [e for u in us for e in u if e]
        alks = sum(e.get("alks_s", 0) for e in E)
        ch = sum(e.get("changes", 0) for e in E)
        lv = np.sum([np.asarray(e["lv"], float).reshape(-1, 4).sum(0) for e in E if len(e.get("lv", [])) == 12], axis=0) if E else np.zeros(4)
        return {"changes_per_1000_alks_s": 1000.0 * ch / alks if alks else None, "reversals_per_change": sum(e.get("reversals", 0) for e in E) / ch if ch else None,
                "ignored_per_change": sum(e.get("ignored", 0) for e in E) / ch if ch else None,
                "v2v_share": sum(e.get("v2v_s", 0) for e in E) / alks if alks else None,
                "level_mix_on": (lv / lv.sum()).round(3).tolist() if np.sum(lv) else None}
    return {"first50": part(eps[:50]), "last50": part(eps[-50:])}


def learner(ppo: dict, eps: list, period: int, n_act: int = 4, kind: str = "v3w") -> dict:
    import tbcheck1
    r = ppo["reward_per_decision"]
    n = len(r)
    a, b, s, ok = tbcheck1.collapse(r, kind, period) if n >= 500 else (None, None, None, None)
    last = r[-100:]
    slope = float(np.polyfit(np.arange(len(last)), last, 1)[0] * len(last) / max(np.std(r[100:]) if n > 100 else np.std(r), 1e-12))
    ent = ppo.get("entropy", np.array([np.nan]))
    out = {"updates": n, "reward_first50": float(r[:50].mean()), "reward_last100": float(last.mean()), "reward_prev100": float(r[-200:-100].mean()) if n >= 200 else None,
           "collapse": {"a": a, "b": b, "sigma": s, "pass": None if ok is None else bool(ok)}, "trend_last100_in_sd": slope,
           "entropy_first": float(ent[:10].mean()), "entropy_last": float(ent[-50:].mean()), "entropy_max": float(np.log(n_act)),
           **{f"{k}_last50": float(ppo[k][-50:].mean()) for k in ("kl", "clipfrac", "ev", "value_loss") if k in ppo},
           "behaviour": behaviour(eps), "curves": {k: spark(ppo[k]) for k in ("reward_per_decision", "entropy", "ev") if k in ppo}}
    return out


def main(runs: Path, out: Path, v_f: str | None = None) -> dict:
    chosen = json.load(open(v_f))["chosen"] if v_f else {}
    res, txt = {}, []
    for g, (fmt, rel) in GROUPS.items():
        d = runs / rel
        if not d.exists():
            txt.append(f"{g}: no logs at {d}")
            continue
        res[g] = {}
        for i in range(5):
            try:
                ppo, eps = read_tb(d / f"C{i}") if fmt == "tb" else read_jsonl(d, i)
            except (FileNotFoundError, KeyError, StopIteration) as x:
                res[g][f"C{i}"] = {"error": repr(x)[:200]}
                continue
            L = learner(ppo, eps, 1 if fmt == "jsonl" else 7, N_ACT.get(g, 4), g)
            L["chosen"] = chosen.get(g, {}).get(str(i))
            res[g][f"C{i}"] = L
        txt.append(f"\n== {g} ({fmt}: {rel})")
        for i, L in res[g].items():
            if "error" in L:
                txt.append(f"  {i}: {L['error']}")
                continue
            c, bh = L["collapse"], L["behaviour"]
            txt.append(f"  {i}: {L['updates']} updates; reward {L['reward_first50']:.3f} -> {L['reward_last100']:.3f} (prev 100 {L['reward_prev100']:.3f}); "
                       f"trend last 100 {L['trend_last100_in_sd']:+.2f} SD; collapse {'pass' if c['pass'] else 'FAIL' if c['pass'] is False else 'n/a'}; "
                       f"entropy {L['entropy_first']:.2f} -> {L['entropy_last']:.2f} of {L['entropy_max']:.2f}; KL {L.get('kl_last50', float('nan')):.4f}; "
                       f"clip {L.get('clipfrac_last50', float('nan')):.3f}; EV {L.get('ev_last50', float('nan')):.2f}" + (f"; chosen u{L['chosen']}" if L["chosen"] else ""))
            f50, l50 = bh["first50"], bh["last50"]
            fmt_ = lambda x: "n/a" if x is None else f"{x:.3g}"
            txt.append(f"      in training: changes/1000 ALKS-s {fmt_(f50['changes_per_1000_alks_s'])} -> {fmt_(l50['changes_per_1000_alks_s'])}; "
                       f"reversals/change {fmt_(f50['reversals_per_change'])} -> {fmt_(l50['reversals_per_change'])}; V2V share {fmt_(f50['v2v_share'])} -> {fmt_(l50['v2v_share'])}; "
                       f"level mix (V2V on) {f50['level_mix_on']} -> {l50['level_mix_on']}")
            for k, sp in L["curves"].items():
                txt.append(f"      {k:<20}{sp}")
    out.mkdir(parents=True, exist_ok=True)
    (out / "train_status.json").write_text(json.dumps(res, indent=1, default=float))
    (out / "train_status.txt").write_text("\n".join(txt))
    print("\n".join(txt))
    return res


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]), *(sys.argv[3:4]))
