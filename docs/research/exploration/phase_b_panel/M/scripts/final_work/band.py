"""EXPLORATORY, read-only: own check of the 6,000-veh/h band rows (condition T). Prints summaries only."""
import json
import numpy as np
p = "/home/catalin/work/phd/v5b1_runs/measure_s01_remote/rows_band.jsonl"
D = {}; aux = {}; arms = set(); qs = set(); pert = set()
for line in open(p):
    r = json.loads(line)
    a = r["name"].split("|")[-1]; arms.add(a); qs.add(r.get("q"))
    if r.get("q") != 6000.0:
        continue
    D.setdefault(a, {})[r["seed"]] = r["all_delay"]
    pert.add(json.dumps(r.get("cfg", {}).get("perturb")) if isinstance(r.get("cfg"), dict) else "?")
    if a == "p333":
        m = r["m_minute"]
        sp = lambda k: np.array([3.6 * v / n if n > 0 else np.nan for v, n in zip(m[k + "_vs"], m[k + "_n"])])
        vs = {}; tot = lambda x: float(np.sum(x))
        aux[r["seed"]] = dict(up=int(np.nansum(sp("m2_up") < 60)), acc=int(np.nansum(sp("m2_acc") < 60)), end2=r.get("end_stop2"), N=r["N"], fin=r.get("finished_pct"),
                              steady=len(r.get("pert_log") or []) == 0, passed=r["passed"], r2q=tot(m["ramp2_pending"]), r1q=tot(m["ramp1_pending"]), nmin=len(m["m2_up_vs"]))
print("arms in band rows:", sorted(arms)); print("levels:", sorted(x for x in qs if x)); print("perturb field at 6,000:", pert)
S = sorted(D["p333"]); P = np.array([D["p333"][s] for s in S]); med = np.median(P)
print("6,000: n %d seeds %d-%d; p333 median all_delay %.0f; N median %.0f; finished %% median %.1f; passed median %.0f (x 2.4 = %.0f veh/h)" % (len(S), S[0], S[-1], med, np.median([aux[s]["N"] for s in S]), np.median([aux[s]["fin"] for s in S]), np.median([aux[s]["passed"] for s in S]), 2.4 * np.median([aux[s]["passed"] for s in S])))
for lab, ss in (("all 20", S), ("no slowdown drawn", [s for s in S if aux[s]["steady"]])):
    print("  %s (n %d): edge-3 minutes below 60 km/h median %.1f of %d, seeds with 0: %d; 4a slow minutes median %.1f; end_stop2 median %.0f; ramp-2 insertion queue median %.0f veh-s (%.1f %% of delay)" % (
        lab, len(ss), np.median([aux[s]["up"] for s in ss]), aux[ss[0]]["nmin"], sum(aux[s]["up"] == 0 for s in ss), np.median([aux[s]["acc"] for s in ss]), np.median([aux[s]["end2"] for s in ss]),
        np.median([aux[s]["r2q"] for s in ss]), 100 * np.median([aux[s]["r2q"] for s in ss]) / np.median([D["p333"][s] for s in ss])))
    for a in sorted(D):
        if a == "p333" or len(D[a]) < len(S):
            continue
        x = 100 * (np.array([D["p333"][s] for s in ss]) - np.array([D[a][s] for s in ss])) / np.median([D["p333"][s] for s in ss])
        print("     %-12s median %+6.2f %%, paired SD %5.1f %%" % (a, np.median(x), x.std(ddof=1)))
