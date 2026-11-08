"""Checks beside the operating map (report-only, stored rows only).
1 measured rows (pack on) against round 2's stored rows; 2 band_table.csv and test_table.csv reproduced with report2's own code path;
3 close-following at 3,500 and 7,000: absolute, per vehicle-km, share of vehicle-time, speed bands, nc level per demand;
4 spread among controllers at 3,500, with slowdown and no-slowdown seeds apart; 5 seeds where p333 and os1_15_10 are identical.
usage: python -B checks.py OUTDIR"""
import csv
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
WT = Path("/home/catalin/work/phd/wt/r2-metrics")
sys.path[:0] = [str(WT / "docs/research/conf3"), str(WT / "docs/research/round1")]
import numpy as np  # noqa: E402
from common import raw, val, load, med, effect, collisions  # noqa: E402
from common1 import arm_mean  # noqa: E402

D = Path("/home/catalin/work/phd/v5b1_runs/measure_s01_remote")
R2 = Path("/home/catalin/work/phd/v5b1_runs/round2")
REP = Path("/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/round2/report")
OUT = Path(sys.argv[1])
P95 = (2.5, 97.5)
G = {"tail": [f"t{i}" for i in range(5)], "sw": [f"s{i}u500" for i in range(5)], "v3w": ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"],
     "baseline-v3": [f"d{i}u500" for i in range(5)]}
res = {}


def absdiff(A, B, key, n_boot=20000):
    ds = sorted(set(A) & set(B))
    d = np.array([val(A[k], key) - val(B[k], key) for k in ds])
    b = np.median(d[np.random.default_rng(20261104).integers(0, len(d), (n_boot, len(d)))], axis=1)
    return [round(float(np.median(d)), 4), round(float(np.percentile(b, 2.5)), 4), round(float(np.percentile(b, 97.5)), 4)]


# 1 identity of measured and stored rows, every stored key except cfg
TB, TT, TS1 = load(D / "rows_band.jsonl"), load(D / "rows_test.jsonl"), load(D / "rows_s1.jsonl")
SB, ST = load(R2 / "band/rows_6c49e7e.jsonl"), load(R2 / "test/rows_6c49e7e.jsonl")
ident = {}
for lab, M, S in (("band", TB, SB), ("test", TT, ST)):
    nrow = ndiff = missing = 0
    bad_keys = {}
    for k, A in S.items():
        for s, r in A.items():
            m = M.get(k, {}).get(s)
            if m is None:
                missing += 1
                continue
            nrow += 1
            diff = [x for x in r if x != "cfg" and json.loads(json.dumps(m.get(x))) != r[x]]
            if diff:
                ndiff += 1
                for x in diff:
                    bad_keys[x] = bad_keys.get(x, 0) + 1
    ident[lab] = {"stored_rows": sum(len(A) for A in S.values()), "measured_rows": sum(len(A) for A in M.values()), "compared": nrow,
                  "rows_with_any_difference": ndiff, "missing_in_measured": missing, "keys_differing": bad_keys}
res["identity_measured_vs_round2"] = ident
print("1 identity:", json.dumps(ident))

# 2a band_table.csv reproduced exactly as report2 writes it
ref = list(csv.DictReader(open(REP / "band_table.csv")))
rep = {"measured": {"cells": 0, "equal": 0, "diffs": []}, "stored": {"cells": 0, "equal": 0, "diffs": []}}
for src, T in (("measured", TB), ("stored", SB)):
    for q in sorted({k[1] for k in T}):
        A = {f"{lab} arm": arm_mean(T, [f"B|{n}" for n in nm], q) for lab, nm in G.items()} | {n: T[(f"B|{n}", q)] for n in ("p333", "os1_15_10", "3e", "nc")}
        for n, X in A.items():
            r = {"q": q, "name": n, **{k: round(med(X, k), 1) for k in ("all_delay", "passed", "ttc_net", "sev3", "b3_step")},
                 ("collisions_per_learner" if n.endswith(" arm") else "collisions_total"): round(collisions(X), 1)}
            if n != "nc":
                r |= {f"{lab}_vs_nc_95": "{} [{}, {}]".format(*effect(X, A["nc"], key, -1, P95)) for key, lab in (("ttc_net", "ttc"), ("all_delay", "delay"))}
            row = next((x for x in ref if float(x["q"]) == q and x["name"] == n), None)
            for k, v in r.items():
                if k in ("q", "name"):
                    continue
                rep[src]["cells"] += 1
                if row is not None and str(row.get(k)) == str(v):
                    rep[src]["equal"] += 1
                else:
                    rep[src]["diffs"].append([q, n, k, v, None if row is None else row.get(k)])
res["band_table_reproduction"] = rep
print("2a band_table:", {s: {k: (v if k != "diffs" else v[:6]) for k, v in x.items()} for s, x in rep.items()})

# 2b test_table.csv: policy arms against nc and p333 (the four effect columns report2 writes)
tref = list(csv.DictReader(open(REP / "test_table.csv")))
trep = {"cells": 0, "equal": 0, "diffs": []}
for cell in ("X1", "X2"):
    for lab, nm in G.items():
        X = arm_mean(TT, [f"{cell}|{n}" for n in nm], 5300.0)
        row = next(x for x in tref if x["cell"] == cell and x["name"] == f"{lab} arm")
        for refn in ("nc", "p333", "os1_15_10", "3e"):
            Rr = TT[(f"{cell}|{refn}", 5300.0)]
            for key, sign, short in (("ttc_net", -1, "ttc"), ("all_delay", -1, "delay"), ("passed", 1, "flow"), ("b3_step", -1, "brake")):
                col = f"{short}_vs_{refn}_95"
                if col not in row:
                    continue
                v = "{} [{}, {}]".format(*effect(X, Rr, key, sign, P95))
                trep["cells"] += 1
                if row[col] == v:
                    trep["equal"] += 1
                else:
                    trep["diffs"].append([cell, lab, col, v, row[col]])
res["test_table_reproduction"] = trep
print("2b test_table:", {k: (v if k != "diffs" else v[:6]) for k, v in trep.items()})


# 3 close-following at every level: nc level, controllers absolute / per vehicle-km / share of vehicle-time, speed bands
def add(T):
    for A in T.values():
        for r in A.values():
            km = max(val(r, "dist_step"), 1.0) / 1000.0
            r["ttc_per_vkm"] = val(r, "ttc_net") / km
            r["ttc_share_pct"] = 100.0 * val(r, "ttc_net") / max(val(r, "vs"), 1.0)
            r["vkm"] = km
            r["veh_h"] = val(r, "vs") / 3600.0
            for b in ("lo", "mid", "hi"):
                r[f"ttc3_s_{b}"] = val(r, f"ttc3_s_{b}")
            r["ttc3_minus_ttc_net"] = val(r, "ttc3") - val(r, "ttc_net")
    return T


for T in (TB, TT, TS1):
    add(T)
SET = [("3500", TS1, "B", 3500.0), ("4500", TB, "B", 4500.0), ("5000", TB, "B", 5000.0), ("5250", TB, "B", 5250.0), ("X1@5300", TT, "X1", 5300.0),
       ("X2@5300", TT, "X2", 5300.0), ("5500", TB, "B", 5500.0), ("6000", TB, "B", 6000.0), ("7000", TS1, "B", 7000.0)]
cf = {}
ident_ttc3 = {"rows": 0, "ttc3_eq_ttc_net": 0, "max_abs_diff": 0.0}
for lab, T, cell, q in SET:
    A = {a: arm_mean(T, [f"{cell}|{n}" for n in G[a]], q) for a in ("v3w", "tail", "sw") if (f"{cell}|{G[a][0]}", q) in T}
    A |= {n: T[(f"{cell}|{n}", q)] for n in ("p333", "3e", "os1_15_10", "nc")}
    for n in ("p333", "3e", "os1_15_10", "nc", *[f"{cell}|{x}" for a in ("v3w",) for x in G[a]]):
        X = T.get((n if "|" in n else f"{cell}|{n}", q), {})
        for r in X.values():
            ident_ttc3["rows"] += 1
            ident_ttc3["ttc3_eq_ttc_net"] += abs(r["ttc3_minus_ttc_net"]) < 1e-9
            ident_ttc3["max_abs_diff"] = max(ident_ttc3["max_abs_diff"], abs(r["ttc3_minus_ttc_net"]))
    c = {"medians": {a: {k: round(med(X, k), 5) for k in ("ttc_net", "ttc_per_vkm", "ttc_share_pct", "vkm", "veh_h", "ttc3_s_lo", "ttc3_s_mid", "ttc3_s_hi")} for a, X in A.items()}}
    for a, X in A.items():
        m = c["medians"][a]
        tot = sum(np.median([val(r, f"ttc3_s_{b}") for r in X.values()]) for b in ("lo", "mid", "hi"))
        m["speed_band_share_of_median_sum"] = {b: round(float(np.median([val(r, f"ttc3_s_{b}") for r in X.values()]) / tot), 3) if tot else None for b in ("lo", "mid", "hi")}
    c["vs_nc"] = {a: {k: {"eff": [round(x, 1) for x in raw(A[a], A["nc"], k, -1, P95)], "abs": absdiff(A[a], A["nc"], k)}
                      for k in ("ttc_net", "ttc_per_vkm", "ttc_share_pct", "vkm")} for a in A if a != "nc"}
    c["v3w_vs_p333"] = {k: {"eff": [round(x, 1) for x in raw(A["v3w"], A["p333"], k, -1, P95)], "abs": absdiff(A["v3w"], A["p333"], k)}
                        for k in ("ttc_net", "ttc_per_vkm", "ttc_share_pct")}
    cf[lab] = c
res["close_following"] = cf
res["ttc3_vs_ttc_net_identity"] = ident_ttc3
print("3 ttc3 == ttc_net:", ident_ttc3)
for lab in ("3500", "7000"):
    print("3", lab, "medians:", json.dumps(cf[lab]["medians"]))
    print("3", lab, "vs nc:", json.dumps(cf[lab]["vs_nc"]))
    print("3", lab, "v3w vs p333:", json.dumps(cf[lab]["v3w_vs_p333"]))
print("3 nc level per demand (ttc_net median, per vkm, share %):", {lab: [cf[lab]["medians"]["nc"][k] for k in ("ttc_net", "ttc_per_vkm", "ttc_share_pct")] for lab in cf})

# 4 spread among controllers at 3,500 (and 7,000 beside), slowdown and no-slowdown seeds apart
sp = {}
for lab, q in (("3500", 3500.0), ("7000", 7000.0)):
    A = {"v3w": arm_mean(TS1, [f"B|{n}" for n in G["v3w"]], q)} | {n: TS1[(f"B|{n}", q)] for n in ("p333", "3e", "os1_15_10", "nc")}
    slow = sorted(s for s, r in A["nc"].items() if r.get("pert_log"))
    none = sorted(s for s, r in A["nc"].items() if not r.get("pert_log"))
    # the slowdown draw is per seed, so it must agree across arms
    agree = all(bool(TS1[(f"B|{n}", q)][s].get("pert_log")) == (s in slow) for n in ("p333", "3e", "os1_15_10", *G["v3w"]) for s in A["nc"])
    out = {"seeds_with_slowdown": len(slow), "seeds_without": len(none), "slowdown_flag_agrees_across_arms": agree, "pairs": {}, "medians": {}}
    ctrl = ("v3w", "p333", "3e", "os1_15_10")
    for a in (*ctrl, "nc"):
        out["medians"][a] = {k: round(med(A[a], k), 2) for k in ("all_delay", "delay", "delay_ramp", "delay_ramp2", "ttc_net", "b3_step", "b45_step", "passed", "N")}
    for i, a in enumerate(ctrl):
        for b in (*ctrl[i + 1:], "nc"):
            out["pairs"][f"{a} vs {b}"] = {}
            for k, sign in (("all_delay", -1), ("ttc_net", -1), ("b3_step", -1), ("b45_step", -1), ("passed", 1)):
                e = {"all": [round(x, 2) for x in raw(A[a], A[b], k, sign, P95)], "abs_all": absdiff(A[a], A[b], k)}
                for grp, ss in (("slow", slow), ("none", none)):
                    Ag, Bg = {s: A[a][s] for s in ss}, {s: A[b][s] for s in ss}
                    if len(ss) >= 3:
                        e[grp] = [round(x, 2) for x in raw(Ag, Bg, k, sign, P95)]
                out["pairs"][f"{a} vs {b}"][k] = e
    sp[lab] = out
res["spread"] = sp
print("4 3500 seeds slow/none:", sp["3500"]["seeds_with_slowdown"], sp["3500"]["seeds_without"], "agree", sp["3500"]["slowdown_flag_agrees_across_arms"])
print("4 3500 medians:", json.dumps(sp["3500"]["medians"]))
for p, v in sp["3500"]["pairs"].items():
    print("4 3500", p, {k: (x["all"], x.get("slow"), x.get("none")) for k, x in v.items() if k in ("all_delay", "ttc_net", "b3_step")})

# 5 seeds where p333 and os1_15_10 rows are identical on every key except name and cfg
idn = {}
for lab, T, cell, q in SET:
    P, O = T[(f"{cell}|p333", q)], T[(f"{cell}|os1_15_10", q)]
    same = sum(all(P[s].get(k) == O[s].get(k) for k in P[s] if k not in ("name", "cfg") and not k.startswith("m_")) for s in P)
    idn[lab] = [same, len(P)]
res["p333_eq_os1_seeds"] = idn
print("5 p333 == os1_15_10 seeds (non-pack keys):", idn)
json.dump(res, open(OUT / "checks.json", "w"), indent=1, default=float)
