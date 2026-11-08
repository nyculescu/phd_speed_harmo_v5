"""Operating map v3w (and tail, sw) against p333, 3E-T, os1_15_10 and no control across demand, report-only.
Uses round 2's own statistic (conf3 common.raw, pct (2.5, 97.5)) and arm_mean (common1). Reads stored rows only.
usage: python -B opmap.py OUTDIR"""
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
WT = Path("/home/catalin/work/phd/wt/r2-metrics")
sys.path[:0] = [str(WT / "docs/research/conf3"), str(WT / "docs/research/round1")]
import numpy as np  # noqa: E402
from common import raw, val, load, med  # noqa: E402
from common1 import arm_mean  # noqa: E402

D = Path("/home/catalin/work/phd/v5b1_runs/measure_s01_remote")
OUT = Path(sys.argv[1])
P95 = (2.5, 97.5)

V = json.load(open("/home/catalin/work/phd/v5b1_runs/round2/val/validation.json"))
G = {"v3w": [f"w{i}u{V['chosen']['v3w'][str(i)]}" for i in range(5)], "tail": [f"t{i}" for i in range(5)],
     "sw": [f"s{i}u{V['chosen']['sw'][str(i)]}" for i in range(5)], "baseline-v3": [f"d{i}u500" for i in range(5)]}
assert G["v3w"] == ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"], G["v3w"]
assert V["finalists"] == ["tail", "sw"]
RULES = ("p333", "3e", "os1_15_10", "nc")
METRICS = (("all_delay", -1), ("ttc_net", -1), ("passed", 1), ("b3_step", -1), ("b45_step", -1), ("finished_pct", 1),
           ("ttc_per_vkm", -1), ("ttc_share", -1), ("b45_per_vkm", -1))


def derive(T):
    """Per-run ratios, added before averaging over learners: TTC samples per vehicle-km (dist_step, metres, same window as the
    counters), TTC samples per 1-Hz vehicle-sample on the network (vs), b45 seconds per vehicle-km."""
    for A in T.values():
        for r in A.values():
            km = max(val(r, "dist_step"), 1.0) / 1000.0
            r["ttc_per_vkm"] = val(r, "ttc_net") / km
            r["ttc_share"] = val(r, "ttc_net") / max(val(r, "vs"), 1.0)
            r["b45_per_vkm"] = val(r, "b45_step") / km
    return T


def absdiff(A, B, key, n_boot=20000):
    """Median of A minus B over paired seeds, in the metric's units, with a 95 % percentile bootstrap CI (same generator as raw)."""
    ds = sorted(set(A) & set(B))
    d = np.array([val(A[k], key) - val(B[k], key) for k in ds])
    b = np.median(d[np.random.default_rng(20261104).integers(0, len(d), (n_boot, len(d)))], axis=1)
    return [float(np.median(d)), float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))]


TS1 = derive(load(D / "rows_s1.jsonl"))
TB = derive(load(D / "rows_band.jsonl"))
TT = derive(load(D / "rows_test.jsonl"))
SETTINGS = [("3500", TS1, "B", 3500.0), ("4500", TB, "B", 4500.0), ("5000", TB, "B", 5000.0), ("5250", TB, "B", 5250.0),
            ("X1@5300", TT, "X1", 5300.0), ("X2@5300", TT, "X2", 5300.0), ("5500", TB, "B", 5500.0), ("6000", TB, "B", 6000.0),
            ("7000", TS1, "B", 7000.0)]


def arms_of(T, cell, q):
    A = {}
    for lab, nm in G.items():
        if all((f"{cell}|{n}", q) in T for n in nm):
            A[lab] = arm_mean(T, [f"{cell}|{n}" for n in nm], q)
    for r in RULES:
        A[r] = T[(f"{cell}|{r}", q)]
    return A


res = {"settings": [s[0] for s in SETTINGS], "groups": G, "medians": {}, "cmp": [], "seeds": {}}
ncmp = {"policy_vs_ref": 0, "rule_vs_nc": 0, "rule_vs_rule": 0}
ARMS_SET = {}
for lab, T, cell, q in SETTINGS:
    A = arms_of(T, cell, q)
    ARMS_SET[lab] = A
    res["seeds"][lab] = sorted(A["nc"])
    res["medians"][lab] = {a: {k: med(X, k) for k, _ in METRICS} | {"teleports_total": float(sum(val(x, "teleports") for x in X.values())),
                                                                    "collisions_total": float(sum(val(x, "collisions") for x in X.values())),
                                                                    "n": len(X)} for a, X in A.items()}
    pairs = [(p, o, "policy_vs_ref") for p in ("v3w", "tail", "sw") if p in A for o in RULES]
    pairs += [(r, "nc", "rule_vs_nc") for r in ("p333", "3e", "os1_15_10")]
    pairs += [("p333", "3e", "rule_vs_rule"), ("p333", "os1_15_10", "rule_vs_rule"), ("3e", "os1_15_10", "rule_vs_rule")]
    for p, o, kind in pairs:
        for key, sign in METRICS:
            e = raw(A[p], A[o], key, sign, P95)
            res["cmp"].append({"setting": lab, "P": p, "O": o, "kind": kind, "key": key, "sign": sign, "eff": e, "abs": absdiff(A[p], A[o], key),
                               "medP": med(A[p], key), "medO": med(A[o], key), "n": len(set(A[p]) & set(A[o]))})
            if key in ("all_delay", "ttc_net", "passed", "b3_step", "b45_step", "finished_pct"):
                ncmp[kind] += 1
res["n_comparisons_main_metrics"] = ncmp
json.dump(res, open(OUT / "opmap.json", "w"), indent=0)


def fmt(e):
    flag = ">" if e[1] > 0 else "<" if e[2] < 0 else " "
    return f"{e[0]:+.1f} [{e[1]:+.1f}, {e[2]:+.1f}]{flag}"


def table(key, rows_spec, use="eff"):
    labs = [s[0] for s in SETTINGS]
    lines = [f"{key} ({'effect %, positive = first arm better' if use == 'eff' else 'paired median difference P - O, units'}); "
             "> CI above 0, < CI below 0", "| P vs O | " + " | ".join(labs) + " |", "|---|" + "---|" * len(labs)]
    idx = {(c["setting"], c["P"], c["O"], c["key"]): c for c in res["cmp"]}
    for p, o in rows_spec:
        cells = []
        for lab in labs:
            c = idx.get((lab, p, o, key))
            cells.append("-" if c is None else (fmt(c[use]) if use == "eff" else "{:+.1f} [{:+.1f}, {:+.1f}]".format(*c["abs"])))
        lines.append(f"| {p} vs {o} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


SPEC = [(p, o) for p in ("v3w", "tail", "sw") for o in RULES] + [(r, "nc") for r in ("p333", "3e", "os1_15_10")] + [("p333", "3e"), ("p333", "os1_15_10")]
txt = []
for key, _ in METRICS:
    txt.append(table(key, SPEC))
txt.append(table("finished_pct", SPEC, use="abs"))
txt.append(table("ttc_net", SPEC, use="abs"))
med_lines = ["Medians per arm (arm = per-seed mean over 5 learners)", "| setting | arm | " + " | ".join(k for k, _ in METRICS) + " | teleports_total | collisions_total |",
             "|---|---|" + "---|" * (len(METRICS) + 2)]
for lab in res["medians"]:
    for a, m in res["medians"][lab].items():
        med_lines.append(f"| {lab} | {a} | " + " | ".join(f"{m[k]:.4g}" for k, _ in METRICS) + f" | {m['teleports_total']:.4g} | {m['collisions_total']:.4g} |")
txt.append("\n".join(med_lines))
txt.append(f"comparisons on the six main metrics: {ncmp} (total {sum(ncmp.values())}); derived per-km/share metrics are extra")
(OUT / "opmap_tables.txt").write_text("\n\n".join(txt) + "\n")
print("\n\n".join(txt[:6]))
print(txt[-1])
