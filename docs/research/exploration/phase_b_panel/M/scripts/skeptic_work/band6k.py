"""EXPLORATORY, read-only: 6,000 veh/h band rows (condition T, seeds 7,440,880-899; 5 seeds drew no slowdown).
Paired delay differences against p333 in % of p333's median; edge-3 and 4a slow minutes under p333; finished share; run size N against cell S."""
import json
import numpy as np
p = "/home/catalin/work/phd/v5b1_runs/measure_s01_remote/rows_band.jsonl"
A = ("p333", "os1_15_10", "3e", "nc")
d = {a: {} for a in A}; aux = {}
for line in open(p):
    r = json.loads(line)
    a = r["name"].split("|")[-1]
    if a not in A or r.get("q") not in (6000.0, 5250.0, 5500.0):
        continue
    key = (r["q"], r["seed"])
    d[a][key] = r["all_delay"]
    if a == "p333":
        m = r["m_minute"]
        sp = lambda k: [3.6 * v / n if n > 0 else np.nan for v, n in zip(m[k + "_vs"], m[k + "_n"])]
        try:
            up = np.array(sp("m2_up")); acc = np.array(sp("m2_acc"))
        except Exception as e:
            up = acc = np.array([np.nan])
        aux[key] = dict(N=r["N"], fin=r["finished_pct"], passed=r["passed"], steady=len(r.get("pert_log") or []) == 0,
                        up_slow=int(np.nansum(up < 60)), acc_slow=int(np.nansum(acc < 60)), nmin=len(up), end2=r.get("end_stop2"))
for q in (5250.0, 5500.0, 6000.0):
    keys = sorted(k for k in d["p333"] if k[0] == q)
    for label, ks in (("all 20 (condition T)", keys), ("no slowdown drawn", [k for k in keys if aux[k]["steady"]])):
        P = np.array([d["p333"][k] for k in ks]); med = np.median(P)
        print(f"q {q:.0f} {label}: n {len(ks)}; p333 median all_delay {med:.0f}; N median {np.median([aux[k]['N'] for k in ks]):.0f}; finished % {np.median([aux[k]['fin'] for k in ks]):.1f}; "
              f"edge-3 minutes below 60 km/h median {np.median([aux[k]['up_slow'] for k in ks]):.1f} (of {aux[ks[0]]['nmin']}), seeds with 0: {sum(aux[k]['up_slow'] == 0 for k in ks)}; "
              f"4a slow minutes median {np.median([aux[k]['acc_slow'] for k in ks]):.1f}; end_stop2 median {np.median([aux[k]['end2'] for k in ks]):.0f}")
        for a in A[1:]:
            x = 100 * (P - np.array([d[a][k] for k in ks])) / med
            print(f"     {a:10s} edge vs p333 median {np.median(x):+6.2f} %, paired SD {x.std(ddof=1):5.1f} %, range [{x.min():+.1f}, {x.max():+.1f}]")
