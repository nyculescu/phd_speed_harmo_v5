"""Merge V&V reader (docs/research/protocols/merge_vv.md v1.1 on v5b1, V532), fixed before data and run once by the remote script.

usage: read_vv.py v1 OUT --trace ROWS --vv DIR [--replay ROWS]           V1 counter trace (wiring, definition, classification)
       read_vv.py v3 OUT --rows ROWS --st DIR --seeds LO-HI [--workers N]  V2 and V3 readings

Statistic as C1 (C-D5, c1_confirm.md §1): per learner, the median of paired % differences against an arm (its median in the
denominator); the effect is the mean of the five; seeds resampled jointly (B = 20,000, rng 20261108). Positive = v3w better (less)."""
import argparse
import gzip
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "c1"))
sys.path.insert(0, str(HERE.parents[2]))
import read_c1 as rc  # noqa: E402
import read_cf as rf  # noqa: E402
from v5b.fleet import vv_merge as vm  # noqa: E402
from v5b.fleet.measure import group as road_group  # noqa: E402

V3W = rc.V3W
RULES = ("lr400_16_1", "grid_lr400_13_1")     # VV-D2: the deciding rules
REFS = ("p333", "nc")
B, RNG = 20_000, 20261108
P975, P9875, P95 = (1.25, 98.75), (0.625, 99.375), (2.5, 97.5)
BAR, BAR_W = 0.019, 0.0094     # null bars: both-must-pass readings; WORSE
SWAPS, NB, RE_SWAPS, NB_W = 2000, 1000, 20000, 4000
V2_MARGIN = 3.0     # VV-D9
CUT_BAR = 0.80     # VV-D12
MERGE1, MERGE2, EDGE1 = ("3a", "ramp1"), ("4a", "ramp2"), ("1",)
PERIODS = ("before", "taper", "hold", "after", "rest")
EXTRA = ("ttc2", "ttc15", "sev3")
KEYS = ("all_delay", "ttc_net", "b45_step", "passed", "N", "collisions", "jams", "vv_m_time", "vv_ttc3_main", "vv_enc", "ttc_no_e1",
        "g_merge", "g_edge1", "g_rest", "g_m1", "g_m2", "end_stop", "end_stop2") + EXTRA + tuple(f"p_{p}" for p in PERIODS)


def derive(r: dict, st: Path | None) -> dict:
    d = rc.derive(r, st)
    ttc = r.get("m_road_ttc3", {})
    m1, m2, e1 = rc.gsum(ttc, MERGE1), rc.gsum(ttc, MERGE2), rc.gsum(ttc, EDGE1)
    d |= {"g_m1": m1, "g_m2": m2, "g_merge": m1 + m2, "g_edge1": e1, "g_rest": d["ttc_net"] - m1 - m2 - e1, "ttc_no_e1": d["ttc_net"] - e1}
    d |= {k: float(r.get(k, 0.0)) for k in EXTRA + ("vv_m_time", "vv_m_whole", "vv_m_half", "vv_ttc3_main", "vv_enc", "ttc_half")}
    d |= {f"p_{p}": float(r.get(f"ttc3_p_{p}", 0.0)) for p in PERIODS}
    d["stand_n"] = r.get("vv_stand_n", {})
    d["meter_ok"] = "vv_m_step" not in r or (r.get("vv_m_whole", 0.0) == r["ttc_net"] and r.get("vv_m_half", 0.0) == r.get("ttc_half"))
    d["x_out"] = r.get("vv_x_out", 0.0)
    d["c15"] = [r.get("vv_c15_cap", 0.0), r.get("vv_c15_n", 0.0)]
    return d


def load(rows: Path, st: Path | None) -> dict:
    T = defaultdict(dict)
    with open(rows) as f:
        for line in f:
            r = json.loads(line)
            c, a = r["name"].split("|", 1)
            if r["seed"] in T[(c, a)]:
                raise SystemExit(f"duplicate row {r['name']} {r['seed']}")
            T[(c, a)][r["seed"]] = derive(r, st)
    return dict(T)


class Cell:
    """Per-seed arrays of one lane length on the read seeds."""

    def __init__(self, T: dict, cell: str, seeds: list):
        self.a = {(arm, k): np.array([float(T[(cell, arm)][s][k] or 0.0) for s in seeds]) for (c, arm) in T if c == cell for k in KEYS}

    def col(self, arm, k):
        return self.a[(arm, k)]

    def D(self, opp: str, k: str) -> list:
        O = self.col(opp, k)
        m = max(float(np.median(O)), 1e-9)
        return [-(self.col(w, k) - O) / m * 100.0 for w in V3W]


def summ(pt: float, b: np.ndarray, pct: tuple) -> dict:
    lo, hi = np.percentile(b, pct)
    lo95, hi95 = np.percentile(b, P95)
    return {"pt": pt, "lo": float(lo), "hi": float(hi), "lo95": float(lo95), "hi95": float(hi95), "se": float(np.std(b))}


def edge(D: list, idx: np.ndarray, pct: tuple = P975) -> dict:
    pt, b = rf.moe(D, idx)
    return summ(pt, b, pct) | {"_b": b}


def null(D: list, seed: int, worse: bool = False) -> dict:
    """c1_confirm.md §1's swap null; WORSE's 0.94 % bar at 20,000 swaps and 4,000 resamples; one re-estimate above the bar."""
    if worse:
        rate = rf.null_rate(D, RE_SWAPS, NB_W, P9875, seed)
        return {"rate": rate, "swaps": RE_SWAPS, "ok": rate <= BAR_W}
    rate = rf.null_rate(D, SWAPS, NB, P975, seed)
    out = {"rate": rate, "swaps": SWAPS}
    if rate > BAR:
        out["re_rate"] = rate = rf.null_rate(D, RE_SWAPS, NB, P975, seed + 7_919)
    out["ok"] = rate <= BAR
    return out


def strip(x: dict) -> dict:
    return {k: v for k, v in x.items() if not k.startswith("_")}


def holds(c: Cell, idx: np.ndarray, k: str, seed0: int) -> dict:
    """Both rules: 97.5 % lower bounds above 0 with nulls under 1.9 % (computed only where a bound clears 0)."""
    out = {}
    for i, r in enumerate(RULES):
        D = c.D(r, k)
        e = edge(D, idx)
        if e["lo"] > 0:
            e["null"] = null(D, seed0 + 2 * i)
        out[r] = strip(e)
    out["shown"] = all(out[r]["lo"] > 0 and out[r].get("null", {}).get("ok") for r in RULES)
    return out


def worse(c: Cell, idx: np.ndarray, seed0: int) -> dict:
    out = {}
    for i, r in enumerate(RULES):
        D = c.D(r, "ttc_net")
        e = edge(D, idx, P9875)
        if e["hi"] < 0:
            e["null"] = null(D, seed0 + 2 * i, worse=True)
        out[r] = strip(e)
    out["worse"] = [r for r in RULES if out[r]["hi"] < 0 and out[r].get("null", {}).get("ok")]
    return out


def v2(c: Cell, idx: np.ndarray) -> dict:
    """The 0.1-s edge minus the 1-Hz edge, same runs, 95 %; MET if both intervals lie within ±3 points."""
    out = {}
    for r in RULES:
        a, b = edge(c.D(r, "vv_m_time"), idx), edge(c.D(r, "ttc_net"), idx)
        d = summ(a["pt"] - b["pt"], a["_b"] - b["_b"], P95)
        out[r] = {"edge_01s": strip(a), "edge_1hz": strip(b), "diff": d, "within": -V2_MARGIN < d["lo"] and d["hi"] < V2_MARGIN}
    out["outcome"] = "MET" if all(out[r]["within"] for r in RULES) else "LIMIT"
    out["missed_share"] = {}
    for arm in V3W + RULES + REFS:
        t01, t1 = c.col(arm, "vv_m_time"), c.col(arm, "ttc_net")
        out["missed_share"][arm] = float(np.median((t01 - t1) / np.maximum(t01, 1e-9)))
    return out


def change(c3: Cell, c6: Cell, idx: np.ndarray, k: str = "ttc_net") -> dict:
    out = {}
    for r in RULES:
        a, b = edge(c6.D(r, k), idx), edge(c3.D(r, k), idx)
        out[r] = summ(a["pt"] - b["pt"], a["_b"] - b["_b"], P95)
        out[r]["depends"] = out[r]["lo"] > 0 or out[r]["hi"] < 0
    return out


def arm_series(c: Cell, arm: str, k: str) -> np.ndarray:
    return np.mean([c.col(w, k) for w in V3W], axis=0) if arm == "v3w" else c.col(arm, k)


def cut(c3: Cell, c6: Cell, idx: np.ndarray) -> dict:
    """VV-D12: cut = 1 - median(600 m)/median(300 m) of lane-end standing per merge, paired seeds; 95 % lower bound at least 80 %."""
    out = {}
    for m, k in (("merge1", "end_stop"), ("merge2", "end_stop2")):
        out[m] = {}
        for arm in ("v3w",) + RULES + REFS:
            x3, x6 = arm_series(c3, arm, k), arm_series(c6, arm, k)
            pt = 1.0 - float(np.median(x6)) / max(float(np.median(x3)), 1e-9)
            b = 1.0 - np.median(x6[idx], axis=1) / np.maximum(np.median(x3[idx], axis=1), 1e-9)
            out[m][arm] = {"cut": pt, "lo95": float(np.percentile(b, 2.5)), "med300": float(np.median(x3)), "med600": float(np.median(x6))}
        out[m]["removed"] = all(out[m][a]["lo95"] >= CUT_BAR for a in ("v3w",) + RULES + ("nc",))
    return out


def deficit_group(c: Cell) -> dict:
    """Per rule, the group with the largest remaining deficit in samples per run (v3w minus the rule, mean of learners, median)."""
    out = {}
    for r in RULES:
        g = {k: float(np.median(arm_series(c, "v3w", k) - c.col(r, k))) for k in ("g_merge", "g_edge1", "g_rest")}
        out[r] = {"by_group": g, "largest_deficit": max(g, key=g.get) if max(g.values()) > 0 else None}
    return out


def printed(c: Cell, idx: np.ndarray) -> dict:
    out = {}
    for r in RULES + REFS:
        out[r] = {k: strip(edge(c.D(r, k), idx, P95)) for k in ("g_merge", "g_edge1", "g_rest", "g_m1", "g_m2", "ttc_no_e1", "all_delay",
                                                                    "N", "b45_step", "vv_enc") + EXTRA + tuple(f"p_{p}" for p in PERIODS)}
        out[r]["passed"] = strip(edge([-d for d in c.D(r, "passed")], idx, P95))     # served flow: positive = v3w serves more
        if np.all(np.isfinite(c.col(r, "jams"))) and c.col(r, "jams").any():
            out[r]["jams"] = strip(edge(c.D(r, "jams"), idx, P95))
    out["collisions"] = {a: float(c.col(a, "collisions").sum()) for a in V3W + RULES + REFS}
    nc = c.col("nc", "all_delay")
    p0 = {}
    for a in RULES + REFS[:1]:
        d = -(c.col(a, "all_delay") - nc) / max(float(np.median(nc)), 1e-9) * 100.0
        b = np.median(d[idx], axis=1)
        p0[a] = {"pt": float(np.median(d)), "lo95": float(np.percentile(b, 2.5))}
    out["rule_beats_nc_by_10"] = {"by_rule": p0, "any": any(v["pt"] >= 10.0 and v["lo95"] > 0 for v in p0.values())}
    return out


def v3(T: dict, seeds: list, dropped: list, cpus: list) -> dict:
    seeds = [s for s in seeds if s not in set(dropped)]
    arms = V3W + RULES + REFS
    miss = [f"{c} {a} {s}" for c in ("L300", "L600") for a in arms for s in seeds if s not in T.get((c, a), {})]
    if miss:
        raise SystemExit(f"rows missing: {miss[:10]}")
    cpus = set(cpus)
    c3, c6 = Cell(T, "L300", seeds), Cell(T, "L600", seeds)
    n = len(seeds)
    idx = np.random.default_rng(RNG).integers(0, n, (B, n))
    meter_bad = [f"{a} {s}" for a in arms for s in seeds if not T[("L300", a)][s]["meter_ok"]]
    x_out = [f"{a} {s}" for a in arms for s in seeds if T[("L600", a)][s]["x_out"]]
    c15 = {a: sum(T[("L600", a)][s]["c15"][0] for s in seeds) / max(sum(T[("L600", a)][s]["c15"][1] for s in seeds), 1.0) for a in V3W}
    rep = holds(c3, idx, "ttc_net", 20261300)
    main = holds(c3, idx, "vv_ttc3_main", 20261320)
    h6 = holds(c6, idx, "ttc_net", 20261340)
    w6 = worse(c6, idx, 20261360)
    out = {
        "n": n, "dropped": dropped, "cpus": sorted(map(str, cpus)),
        "bugs": {"meter": meter_bad, "x_out": x_out},
        "v2": v2(c3, idx) if not meter_bad else {"outcome": "BUG", "meter": meter_bad[:20]},
        "v3a": {"replication": rep | {"reading": "REPLICATED" if rep["shown"] else "NOT REPLICATED"},
                "main_lane": main | {"reading": "also shown on main-lane samples" if main["shown"] else "not shown on main-lane samples alone"}},
        "v3b": {"holds": h6, "worse": w6,
                "reading": "WORSE" if w6["worse"] else "HOLDS" if h6["shown"] else "NOT SHOWN",
                "change": change(c3, c6, idx), "cut": cut(c3, c6, idx), "deficit_600": deficit_group(c6),
                "no_edge1_600": {r: strip(edge(c6.D(r, "ttc_no_e1"), idx, P95)) for r in RULES}},
        "printed_300": printed(c3, idx), "printed_600": printed(c6, idx), "c15_cap_share_600": c15,
        "standing_vehicles": {c: {a: {m: float(np.median([T[(c, a)][s]["stand_n"].get(m, 0) for s in seeds])) for m in ("3a_0", "4a_0")}
                                  for a in arms} for c in ("L300", "L600")}}
    out["void"] = [f"CPU models differ: {sorted(map(str, cpus))}"] if len(cpus) > 1 else []
    return out


def period(t: float, onset: float, dur: float, taper: float = 20.0) -> str:
    if t < onset:
        return "before"
    if t < onset + taper:
        return "taper"
    if t < onset + dur:
        return "hold"
    return "after" if t < onset + dur + 120.0 else "rest"


def v1_row(r: dict, merges: list) -> dict:
    """One traced run: wiring and definition checks, and every counted sample classified."""
    tr = r.get("vv_trace", [])
    lanes = r.get("vv_lanes", {})
    out = {"wiring": [], "definition": [], "classes": Counter()}
    if len(tr) != r["ttc_net"]:
        out["wiring"].append(f"samples {len(tr)} vs ttc_net {r['ttc_net']}")
    road = Counter(road_group(s[5]) for s in tr)
    want = {g: rc.gsum(r.get("m_road_ttc3", {}), (g,)) for g in set(road) | set(r.get("m_road_ttc3", {}))}
    if any(road.get(g, 0) != want[g] for g in want):
        out["wiring"].append(f"road groups {dict(road)} vs m_road_ttc3 {want}")
    if sum(vm.is_main(s[6], s[5]) for s in tr) != r.get("vv_ttc3_main"):
        out["wiring"].append("main-lane recount")
    last = {}
    if sum(vm.encounter_new(last, (s[1], s[2]), s[0]) for s in tr) != r.get("vv_enc"):
        out["wiring"].append("encounter recount")
    for x, k in (("3a_0", "end_stop"), ("4a_0", "end_stop2")):
        rec = sum(1 for t, ln, L, vs in r.get("end_trace", []) if ln == x for _, p, s in vs if s < 1.0 and p > L - 30.0)
        if rec != r.get(k, 0.0) or r.get("vv_stand_s", {}).get(x, 0) != r.get(k, 0.0):
            out["wiring"].append(f"{k}: end_trace {rec}, vv_stand {r.get('vv_stand_s', {}).get(x)}, row {r.get(k)}")
    onset, dur = r["pert_log"][0][1], r["pert_log"][0][2]
    mt = defaultdict(list)
    for m in merges:
        mt[m["v"]].append(m["t"])
    enc_len, cur = [], {}
    for t, v, w, fk, wk, froad, flane, fpos, flen, wroad, wlane, wpos, wlen, gap, mingap, s, sl in tr:
        if not (s > sl and (gap + mingap) / (s - sl) < 3.0):
            out["wiring"].append(f"TTC not below 3 s at {t} {v}")
        if wlane == flane:
            if abs((wpos - wlen - fpos) - (gap + mingap)) > 0.01:
                out["definition"].append(f"gap {t} {v}->{w}: positions {wpos - wlen - fpos:.3f} vs SUMO {gap + mingap:.3f}")
            rel = "same lane"
        elif wroad == froad:
            out["definition"].append(f"cross-lane leader {t} {v} on {flane}, {w} on {wlane}")
            rel = "cross lane"
        else:
            rel = "next lane"
        stand = wlane in ("3a_0", "4a_0") and sl < 1.0 and wpos > lanes.get(wlane, 1e9) - 30.0
        merged = any(t - 5.0 <= x <= t for u in (v, w) for x in mt.get(u, ()))
        band = "lo" if s < 5.0 else "mid" if s < 10.0 else "hi"
        per = period(t, onset, dur)
        cls = (("main" if vm.is_main(flane, froad) else "acc/ramp"), rel, "leader standing" if stand else "-", "merged 5 s" if merged else "-",
               fk, band, per, road_group(froad))
        out["classes"][" | ".join(cls)] += 1
        k = (v, w)
        if abs(cur.get(k, (-99, 0))[0] - (t - 1.0)) < 1e-6:
            cur[k] = (t, cur[k][1] + 1)
        else:
            if k in cur:
                enc_len.append(cur[k][1])
            cur[k] = (t, 1)
    enc_len += [n for _, n in cur.values()]
    out["encounters"] = {"n": len(enc_len), "durations": dict(Counter(enc_len))}
    out["stand_n"] = r.get("vv_stand_n")
    out["edge1"] = [{"t": s[0], "period": period(s[0], onset, dur), "pos": s[7], "type": s[3], "speed": s[15]} for s in tr if s[5] == "1"]
    out["classes"] = dict(out["classes"].most_common())
    return out


def v1(trace_rows: list, vv_dir: Path) -> dict:
    from vv import twin_diff, TWIN
    by = {(r["name"], r["seed"]): r for r in trace_rows}
    out = {"twins": {}, "runs": {}, "sample": []}
    for (n, s), r in by.items():
        if n.endswith("~trace"):
            tw = by.get((n[: -len("~trace")] + TWIN, s))
            if tw is not None:
                out["twins"][f"{n} {s}"] = twin_diff(r, tw)
            f = vv_dir / r["vv_log_file"] if r.get("vv_log_file") else None
            merges = json.load(gzip.open(f, "rt"))["merges"] if f and f.is_file() else r.get("vv_merges_log", [])
            out["runs"][f"{n} {s}"] = v1_row(r, merges)
    pool = [(k, i) for k, r in sorted(by.items()) if k[0].endswith("~trace") for i in range(len(r.get("vv_trace", [])))]
    rng = np.random.default_rng(20261115)
    for j in rng.choice(len(pool), size=min(40, len(pool)), replace=False):
        k, i = pool[int(j)]
        out["sample"].append([f"{k[0]} {k[1]}"] + by[k]["vv_trace"][i])
    wiring = {k: v["wiring"] for k, v in out["runs"].items() if v["wiring"]}
    definition = {k: v["definition"][:20] for k, v in out["runs"].items() if v["definition"]}
    twins = {k: v for k, v in out["twins"].items() if v}
    out["outcome"] = "BUG" if definition else "TRACER BUG" if (wiring or twins) else "CHECKS PASS; visual check pending"
    out["wiring_fail"], out["definition_fail"], out["twin_fail"] = wiring, definition, twins
    return out


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("step", choices=("v1", "v3"))
    ap.add_argument("out")
    ap.add_argument("--trace", nargs="+")
    ap.add_argument("--vv")
    ap.add_argument("--rows")
    ap.add_argument("--st")
    ap.add_argument("--seeds")
    x = ap.parse_args(argv)
    if x.step == "v1":
        rows = [json.loads(line) for p in x.trace for line in open(p)]
        res = v1(rows, Path(x.vv))
        print("V1", res["outcome"])
    else:
        lo, hi = map(int, x.seeds.split("-"))
        T = load(Path(x.rows), Path(x.st) if x.st else None)
        meta = json.loads((Path(x.rows).parent / "meta.json").read_text())
        res = v3(T, list(range(lo, hi + 1)), rc.drops_of(Path(x.rows)), [meta["inputs"].get("cpu")])
        print("V2", res["v2"]["outcome"], "| V3a", res["v3a"]["replication"]["reading"], "|", res["v3a"]["main_lane"]["reading"],
              "| V3b", res["v3b"]["reading"])
    Path(x.out).write_text(json.dumps(res, indent=1, default=float))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
