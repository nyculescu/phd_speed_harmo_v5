"""C1 confirmation reader (docs/research/protocols/c1_confirm.md on v5b1, V527), fixed before data and run once by the remote script.

usage: read_cf.py ident ROWS OUT --cpu MODEL             §3 identity replays of the 29 stored arms against S6
       read_cf.py screen OUT --rows R [R2] --seeds LO-HI [--ext] [--workers N]     §1 readings and outcome

Statistic as C1 (C-D5): per learner, the median of paired % differences against an arm (its median in the denominator); the effect is
the mean of the five; seeds resampled jointly (B = 20,000, rng 20261108). Positive = v3w better (less)."""
import argparse
import json
import multiprocessing as mp
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import read_c1 as rc  # noqa: E402

V3W = rc.V3W
LEARNER_LIKE = V3W + ("MPC-F",)     # §3: MPC-F's traffic keys are read as the learners' (an MLP model)
L95 = rc.L95
MAIN = {"pct": rc.L975, "bar": 0.019, "swaps": 2000, "nb": 1000}     # §1
EXT = {"pct": (0.625, 99.375), "bar": 0.0094, "swaps": 20000, "nb": 4000}     # CF-D7's extension read
RE_SWAPS = 20000     # §1: a null rate above its bar is re-estimated once with this many swaps
COMPETE_MARGIN, EDGE_MIN, P0_BAR = 1.0, 5.0, 10.0     # CF-D3, CF-D4, CLAUDE.md early KILL
ARR = {}     # (arm, key) -> per-seed values on the read seeds; set before the worker pool forks
CTX = {}


def col(arm: str, key: str) -> np.ndarray:
    return ARR[(arm, key)]


def ci(b: np.ndarray, pct: tuple) -> tuple:
    lo, hi = np.percentile(b, pct)
    return float(lo), float(hi)


def summary(pt: float, b: np.ndarray, pct: tuple) -> dict:
    lo, hi = ci(b, pct)
    lo95, hi95 = ci(b, L95)
    return {"pt": pt, "lo": lo, "hi": hi, "lo95": lo95, "hi95": hi95, "se": float(np.std(b))}


def learner_d(opp: str, key: str) -> list:
    """Per learner, the per-seed paired % differences against opp, positive = v3w less."""
    O = col(opp, key)
    m = max(float(np.median(O)), 1e-9)
    return [-(col(w, key) - O) / m * 100.0 for w in V3W]


def moe(D: list, idx: np.ndarray) -> tuple:
    return float(np.mean([np.median(d) for d in D])), np.mean([np.median(d[idx], axis=1) for d in D], axis=0)


def edge(opp: str, key: str) -> dict:
    D = learner_d(opp, key)
    pt, b = moe(D, CTX["idx"])
    return summary(pt, b, CTX["pct"]) | {"_D": D}


def chord(q: str, r: str) -> dict:
    """§1: the straight mix of q and r at v3w's delay. w = m_q / (m_q + m_r) on each resample, clamped to [0, 1] (0.5 if the sum is 0);
    the per-seed mix M = (1 - w) q + w r on close-following, in units of c_M = (1 - w) median(q) + w median(r)."""
    idx, pct = CTX["idx"], CTX["pct"]
    P = [col(w, "all_delay") for w in V3W]
    Qd, Rd = col(q, "all_delay"), col(r, "all_delay")
    mq = float(np.mean([np.median(p - Qd) for p in P]))
    mr = float(np.mean([np.median(Rd - p) for p in P]))
    mqb = np.mean([np.median((p - Qd)[idx], axis=1) for p in P], axis=0)
    mrb = np.mean([np.median((Rd - p)[idx], axis=1) for p in P], axis=0)
    w0 = weight(np.array([mq]), np.array([mr]))[0]
    wb = weight(mqb, mrb)
    Qc, Rc = col(q, "ttc_net"), col(r, "ttc_net")
    mdq, mdr = float(np.median(Qc)), float(np.median(Rc))
    M0 = (1 - w0) * Qc + w0 * Rc
    c0 = max((1 - w0) * mdq + w0 * mdr, 1e-9)
    D = [-(col(w, "ttc_net") - M0) / c0 * 100.0 for w in V3W]
    pt = float(np.mean([np.median(d) for d in D]))
    cb = np.maximum((1 - wb) * mdq + wb * mdr, 1e-9)[:, None]
    Mb = (1 - wb)[:, None] * Qc[idx] + wb[:, None] * Rc[idx]
    b = np.mean([np.median(-(col(w, "ttc_net")[idx] - Mb) / cb * 100.0, axis=1) for w in V3W], axis=0)
    return summary(pt, b, pct) | {"q": q, "r": r, "w": float(w0), "w_ci": ci(wb, pct), "_D": D}


def weight(mq: np.ndarray, mr: np.ndarray) -> np.ndarray:
    s = mq + mr
    w = np.where(s == 0, 0.5, mq / np.where(s == 0, 1.0, s))
    return np.clip(w, 0.0, 1.0)


def null_rate(D: list, swaps: int, nb: int, pct: tuple, seed: int) -> float:
    """C1's swap null: one sign per learner and seed; the mean of the false rates of a lower bound above 0 and an upper bound below 0."""
    n = len(D[0])
    rng = np.random.default_rng(seed)
    idx = np.random.default_rng(seed + 1).integers(0, n, (nb, n))
    lo_hit = hi_hit = 0
    for _ in range(swaps):
        _, b = moe([d * rng.choice((-1.0, 1.0), n) for d in D], idx)
        lo, hi = ci(b, pct)
        lo_hit += lo > 0
        hi_hit += hi < 0
    return (lo_hit + hi_hit) / (2.0 * swaps)


def null_check(D: list, seed: int) -> dict:
    lv = CTX["lv"]
    rate = null_rate(D, lv["swaps"], lv["nb"], lv["pct"], seed)
    out = {"rate": rate, "swaps": lv["swaps"]}
    if rate > lv["bar"]:
        out["re_rate"] = rate = null_rate(D, RE_SWAPS, lv["nb"], lv["pct"], seed + 7_919)
        out["re_swaps"] = RE_SWAPS
    out["ok"] = rate <= lv["bar"]
    return out


def chord_job(a: tuple) -> dict:
    i, q, r = a
    c = chord(q, r)
    c["null"] = null_check(c.pop("_D"), 20261200 + 2 * i)
    return c


def null_job(a: tuple) -> dict:
    i, D = a
    return null_check(D, 20261100 + 2 * i)


def read_test(t: dict, competitor_D: dict | None = None) -> str:
    """§1, in this order: a failed null → UNRESOLVED; MATCHED (AT A DELAY COST for a competitor with D point above +1 %); BEATEN; UNRESOLVED."""
    if not t["null_ok"]:
        return "UNRESOLVED"
    if t["hi"] < EDGE_MIN:
        return "MATCHED AT A DELAY COST" if competitor_D is not None and competitor_D["pt"] > COMPETE_MARGIN else "MATCHED"
    if t["lo"] > 0:
        return "BEATEN"
    return "UNRESOLVED"


def decide(x: dict) -> dict:
    """x: void (list), p0 (bool), competitors {name: {"E": test, "D": reading}}, chords [test]; a test is {pt, lo, hi, null_ok}."""
    if x.get("void"):
        return {"outcome": "VOID", "why": x["void"]}
    if not x["p0"]:
        return {"outcome": "P0 FAILS"}
    reads = {f"competitor {n}": read_test(c["E"], c["D"]) for n, c in x["competitors"].items()}
    reads |= {f"chord {c['q']}~{c['r']}": read_test(c) for c in x["chords"]}
    matched = [k for k, v in reads.items() if v == "MATCHED"]
    if matched:
        return {"outcome": "KILL", "matched": matched, "reads": reads}
    if x["competitors"] and all(v == "BEATEN" for v in reads.values()):
        return {"outcome": "PASS", "reads": reads}
    return {"outcome": "UNRESOLVED", "not_beaten": {k: v for k, v in reads.items() if v != "BEATEN"}, "reads": reads}


def drain(arms: list) -> dict:
    """C1 §2 per arm against p333 on the read seeds: queues in V486's form (v3w averaged per seed first) and stuck rows."""
    out = {}
    for a in ["v3w"] + [x for x in arms if x != "p333"]:
        names = V3W if a == "v3w" else (a,)
        ex = {k: float(np.mean(np.mean([col(w, f"q_{k}") for w in names], axis=0) - col("p333", f"q_{k}"))) for k in rc.drain.KEYS}
        share = float(np.mean([np.mean(col(w, "stuck") > 0) for w in names]))
        out[a] = {"queue_excess": ex, "stuck_share": share,
                  "fail": any(v > rc.DRAIN_VEH for v in ex.values()) or share > rc.STUCK_SHARE}
    return out


def p0(rules: list) -> dict:
    nc = col("nc", "all_delay")
    idx = CTX["idx"]
    out = {}
    for a in rules:
        if a == "nc":
            continue
        d = -(col(a, "all_delay") - nc) / max(float(np.median(nc)), 1e-9) * 100.0
        pt, (lo, _) = float(np.median(d)), ci(np.median(d[idx], axis=1), L95)
        out[a] = {"pt": pt, "lo95": lo, "pass": pt >= P0_BAR and lo > 0}
    return {"arms": out, "pass": any(v["pass"] for v in out.values())}


def single(a: str, opp: str, key: str) -> float:
    """Median paired % difference of rule a against opp, positive = a less."""
    O = col(opp, key)
    return float(np.median(-(col(a, key) - O) / max(float(np.median(O)), 1e-9) * 100.0))


def screen(T: dict, seeds: list, dropped: list, cpus: list, lv: dict = MAIN, workers: int = 16, b: int = rc.read6.B) -> dict:
    void = []
    if len(set(dropped)) > rc.DROP_VOID:
        void.append(f"{len(set(dropped))} seeds dropped (common §4)")
    if len(set(cpus)) != 1:
        void.append(f"CPU models differ across rows: {sorted(set(map(str, cpus)))} (CF §3)")
    arms = sorted({a for (_, a) in T})
    rules = [a for a in arms if a not in V3W]
    seeds = [s for s in seeds if s not in set(dropped)]
    miss = [f"{a} {s}" for a in arms for s in seeds if s not in T[("E30", a)]]
    if miss:
        raise SystemExit(f"rows missing: {miss[:10]}")
    keys = ("all_delay", "ttc_net", "ttc_away", "b45_step", "events_ge45", "passed", "N", "stuck", "q_ramp1_queue", "q_ramp2_queue", "q_backlog")
    ARR.clear()
    for a in arms:
        for k in keys:
            ARR[(a, k)] = np.array([float(T[("E30", a)][s][k]) for s in seeds])
    n = len(seeds)
    CTX.update(idx=np.random.default_rng(rc.read6.RNG).integers(0, n, (b, n)), pct=lv["pct"], lv=lv)
    R = {a: {k: edge(a, key) for k, key in (("D", "all_delay"), ("E", "ttc_net"), ("away", "ttc_away"), ("brake", "b45_step"), ("ev45", "events_ge45"))}
         for a in rules}
    comp = [a for a in rules if R[a]["D"]["lo"] <= COMPETE_MARGIN or a == "p333"]
    pairs = [(q, r) for q in rules for r in rules if q != r and R[q]["D"]["lo"] < 0 and R[r]["D"]["hi"] > 0]
    ctx = mp.get_context("fork")
    with ProcessPoolExecutor(min(workers, os.cpu_count() or 1), mp_context=ctx) as ex:
        chords = list(ex.map(chord_job, [(i, q, r) for i, (q, r) in enumerate(pairs)]))
        tests = [(f"E {a}", R[a]["E"]["_D"]) for a in comp] + [(f"brake {a}", R[a]["brake"]["_D"]) for a in comp]
        nulls = dict(zip([t for t, _ in tests], ex.map(null_job, [(i, D) for i, (_, D) in enumerate(tests)])))
    for a in rules:
        for k in R[a]:
            R[a][k].pop("_D", None)
    for c in chords:
        c["null_ok"] = c["null"]["ok"]
    competitors = {a: {"E": R[a]["E"] | {"null_ok": nulls[f"E {a}"]["ok"]}, "D": R[a]["D"]} for a in comp}
    dr = drain(rules)
    if dr["v3w"]["fail"]:
        void.append("v3w per-arm drain fails (C1 §2)")
    pz = p0(rules)
    x = {"void": void, "p0": pz["pass"], "competitors": competitors, "chords": chords}
    braking = {a: {"lo": R[a]["brake"]["lo"], "null_ok": nulls[f"brake {a}"]["ok"]} for a in comp}
    p333D = R["p333"]["D"]
    out = {"n": n, "level": lv, "dropped": dropped, "cpus": sorted(set(map(str, cpus))), "decision": decide(x),
           "competitors": comp, "trade_points": [a for a in rules if a not in comp], "n_chords": len(chords),
           "smallest_lower_bound": min([competitors[a]["E"]["lo"] for a in comp] + [c["lo"] for c in chords]),
           "braking_shown": bool(comp) and all(v["lo"] > 0 and v["null_ok"] for v in braking.values()), "braking": braking,
           "braking_vs_3E-C_TRUCK": R["3E-C_TRUCK"]["brake"] if "3E-C_TRUCK" in R else None,
           "delay_vs_p333": p333D | {"reading": rc.r_delay({"pt": p333D["pt"], "lo": p333D["lo"], "hi95": p333D["hi95"]})},
           "exchange": exchange(rules, R), "readings": R, "chords": chords, "nulls": nulls, "p0": pz, "drain": dr,
           "arm_medians": sorted(({"arm": a, **{k: float(np.median(np.mean([col(w, k) for w in V3W], axis=0) if a == "v3w" else col(a, k)))
                                              for k in ("all_delay", "ttc_net", "b45_step", "events_ge45", "passed", "N")}}
                                  for a in ["v3w"] + rules), key=lambda d: d["all_delay"]),
           "learners_vs_p333": {w: float(np.median(d)) for w, d in zip(V3W, learner_d("p333", "ttc_net"))}}
    return out


def exchange(rules: list, R: dict) -> dict:
    """% close-following per % delay against p333: v3w's, and every slower rule's (both positive when close-following is bought with delay)."""
    out = {}
    d = R["p333"]["D"]["pt"]
    if d < 0:
        out["v3w"] = R["p333"]["E"]["pt"] / -d
    for a in rules:
        if a != "p333":
            cut, cost = single(a, "p333", "ttc_net"), -single(a, "p333", "all_delay")
            if cost > 0:
                out[a] = cut / cost
    return out


def ident(rows: list, S6: dict, cpu: str) -> dict:
    """read_c1.ident's key classes; MPC-F's traffic keys read as the learners' (a mismatch on another CPU model is disclosed)."""
    saved = rc.V3W
    try:
        rc.V3W = LEARNER_LIKE
        return rc.ident(rows, S6, cpu)
    finally:
        rc.V3W = saved


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("step", choices=("ident", "screen"))
    ap.add_argument("rows", nargs="?")
    ap.add_argument("out")
    ap.add_argument("--rows", dest="rows_list", nargs="+")
    ap.add_argument("--cpu", default="")
    ap.add_argument("--seeds")
    ap.add_argument("--ext", action="store_true")
    ap.add_argument("--workers", type=int, default=16)
    x = ap.parse_args(argv)
    if x.step == "ident":
        rows = [json.loads(line) for line in open(x.rows)]
        names = {r["name"] for r in rows}
        S6 = {(r["name"], r["seed"]): r for r in map(json.loads, open(rc.S6_ROWS)) if r["name"] in names}
        res = ident(rows, S6, x.cpu)
    else:
        lo, hi = (int(v) for v in x.seeds.split("-"))
        T = rc.load(x.rows_list)
        dropped = sorted({s for p in x.rows_list for s in rc.drops_of(Path(p))})
        cpus = [json.loads((Path(p).parent / "meta.json").read_text())["inputs"].get("cpu") for p in x.rows_list]
        res = screen(T, list(range(lo, hi + 1)), dropped, cpus, EXT if x.ext else MAIN, x.workers)
    Path(x.out).parent.mkdir(parents=True, exist_ok=True)
    Path(x.out).write_text(json.dumps(res, indent=1, default=str))
    print(x.step, json.dumps({"action": res.get("action")} if x.step == "ident" else {"outcome": res["decision"]["outcome"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
