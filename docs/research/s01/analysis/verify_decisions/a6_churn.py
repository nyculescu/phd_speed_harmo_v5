"""D10: share of level changes and reversals made by ALKS with V2V on < 20 % of their seconds; D11: S0 rows vs round-2 rows;
place split of decisions (m_dec_place) X1 vs X2 (my addition)."""
import numpy as np, json
from base import *
ST = "/home/catalin/work/phd/v5b1_runs/measure_s01_remote/st/"
rows, T = load()
for gname, names in [("v3w", ARMS["v3w"]), ("3e", ["3e"]), ("os1_15_10", ["os1_15_10"])]:
    for cell in ["X1", "X2"]:
        nv = nlow = ch = chlow = rv = rvlow = 0
        for n in names:
            for s, r in T[(cell, n, 5300.0)].items():
                z = np.load(ST + r["m_st_file"]); D = z["dec"]; L = z["dec_level_s"]
                tot = L.sum(1); low = (L[:, :4].sum(1) < 0.2 * tot) & (tot > 0)
                nv += (tot > 0).sum(); nlow += low.sum(); ch += D[:, 1].sum(); chlow += D[low, 1].sum(); rv += D[:, 4].sum(); rvlow += D[low, 4].sum()
                assert (D[:, 0] == D[:, 1] + D[:, 2] + D[:, 3]).all() and (D[:, 4] <= np.maximum(D[:, 1] - 1, 0)).all() and (D[:, 1] - D[:, 5] >= 0).all()
        print(f"D10 {gname:10s} {cell}: low-V2V ALKS {nlow/nv:.3f} of ALKS; {chlow/ch:.3f} of changes; {rvlow/rv:.3f} of reversals")
# D11
keys = ["all_delay", "ttc_net", "passed", "lv", "lv_sum_4", "lv_n_4", "tau_on_match", "N"]
R2 = {}
for f in ["/home/catalin/work/phd/v5b1_runs/round2/test/rows_6c49e7e.jsonl", "/home/catalin/work/phd/v5b1_runs/round2/band/rows_6c49e7e.jsonl"]:
    for line in open(f):
        r = json.loads(line); R2[(r["name"], float(r["q"]), int(r["seed"]))] = {k: r.get(k) for k in keys + ["E30", "out_E30", "b3_step", "collisions"]}
m = diff = 0; dk = {}
for r in rows:
    if r["src"] == "rows_s1.jsonl": continue
    o = R2.get((r["name"], float(r["q"]), int(r["seed"])))
    if o is None: continue
    m += 1
    bad = [k for k in keys if (r.get(k) != o.get(k))]
    if bad: diff += 1; dk.update({k: dk.get(k, 0) + 1 for k in bad})
print(f"D11 matched {m} rows of {sum(r['src']!='rows_s1.jsonl' for r in rows)}; rows with any difference on {keys}: {diff} {dk}; round2 rows available {len(R2)}")
# place split, X1 minus X2 changed per asked in 'down' (roads 4, 5) and 'm2' (4a)
for gname, names in [("v3w", ARMS["v3w"]), ("os1_15_10", ["os1_15_10"]), ("3e", ["3e"])]:
    out = []
    for pl in ["between", "m2", "down", "ramp2"]:
        f = lambda r, pl=pl: r["m_dec_place"][pl][1] / max(r["m_dec_place"][pl][0], 1)
        A = arm_series(T, "X1", names, 5300.0, f); B = arm_series(T, "X2", names, 5300.0, f)
        d, _ = paired_diff(A, B)
        out.append(f"{pl}: X1 {np.median(list(A.values())):.3f} X1-X2 {fmt(d)}")
    print("place applied share", gname, "; ".join(out))
