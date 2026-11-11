"""EXPLORATORY: low-demand references for delay, from stored rows (no simulation)."""
import json, gzip, pickle, collections
import numpy as np
REF = 100.0 / 3.6
W = 1500.0
def planned(q): return q * W / 3600.0
print("== r2m3 ladder (V354/V355), no control, steady, 10 seeds 7,440,000-009; all_delay recomputed as N - dist/REF from 1-Hz dist")
L = collections.defaultdict(list)
for line in gzip.open("/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/r2m3/ladder_rows.jsonl.gz", "rt"):
    r = json.loads(line)
    L[(r["name"], r["q"])].append((r["N"] - r["dist"] / REF, r["delay"], r["dist"] / r["vs"] * 3.6, r["passed"], r["N"] - r["vs"]))
for k in sorted(L):
    a = np.array(L[k], float)
    print(f" {k}: all_delay median {np.median(a[:,0]):.0f} veh-s = {np.median(a[:,0])/planned(k[1]):.1f} s per planned vehicle; 'delay' (finished, sf-adjusted) {np.median(a[:,1]):.1f} s; running mean speed {np.median(a[:,2]):.1f} km/h; passed {np.median(a[:,3]):.0f} of {planned(k[1]):.0f}; pending veh-s {np.median(a[:,4]):.0f}")
print("== S1 map rows_s1 (measure_s01_remote), cell B = training random slowdowns; 20 seeds 7,440,900-919; 'none' = seeds whose draw was no slowdown")
R = collections.defaultdict(list)
for line in open("/home/catalin/work/phd/v5b1_runs/measure_s01_remote/rows_s1.jsonl"):
    r = json.loads(line)
    arm = r["name"].split("|")[1]
    if arm in ("nc", "p333", "w0u250"):
        R[(arm, r["q"], "none" if not r.get("pert_log") else "pert")].append(r)
def stats(rows, q):
    ad = np.array([r["all_delay"] for r in rows]); dl = np.array([r["delay"] for r in rows])
    sp = {c: np.median([r[f"m_dist_m_{c}"] / (r[f"m_n_{c}"] * 0.1) * 3.6 for r in rows]) for c in ("alks", "car", "truck")}
    cd = {c: np.median([r[f"m_n_{c}"] * 0.1 - r[f"m_dist_m_{c}"] / REF for r in rows]) for c in ("alks", "car", "truck")}
    pend = np.array([r["N"] - r["vs"] for r in rows])
    return f"n={len(rows)} all_delay median {np.median(ad):.0f} veh-s = {np.median(ad)/planned(q):.1f} s per planned vehicle; 'delay' {np.median(dl):.1f} s; speeds km/h alks {sp['alks']:.1f} car {sp['car']:.1f} truck {sp['truck']:.1f}; class delay alks {cd['alks']:.0f} car {cd['car']:.0f} truck {cd['truck']:.0f}; pending veh-s {np.median(pend):.0f}; passed {np.median([r['passed'] for r in rows]):.0f} of {planned(q):.0f}"
for k in sorted(R):
    print(" ", k, stats(R[k], k[1]))
for arm in ("nc", "p333", "w0u250"):
    rows = R[(arm, 3500.0, "none")] + R[(arm, 3500.0, "pert")]
    print("  all 20:", arm, stats(rows, 3500.0))
# paired p333 vs nc on unperturbed seeds at 3,500
a = {r["seed"]: r["all_delay"] for r in R[("nc", 3500.0, "none")]}; b = {r["seed"]: r["all_delay"] for r in R[("p333", 3500.0, "none")]}
print("  unperturbed seeds:", sorted(a), "nc - p333 per seed:", [round(a[s] - b[s]) for s in sorted(a)])
print("== V419 sweep rows (round1_sweep/out/sweep1.jsonl), training random slowdowns, 10 seeds 7,440,600-609")
S = collections.defaultdict(list)
for line in open("/home/catalin/work/phd/v5b1_runs/round1_sweep/out/sweep1.jsonl"):
    r = json.loads(line)
    arm = r["name"].split("|")[1]
    if arm in ("nc", "p333"):
        S[(arm, r["q"])].append((r["all_delay"], r["delay"], 0 if not r.get("pert_log") else 1, r["passed"], r["dist"] / r["vs"] * 3.6, r["seed"]))
for q in (2500.0, 3000.0, 3500.0, 4000.0, 4500.0, 5000.0, 5250.0, 5500.0, 5750.0, 6000.0, 6250.0):
    out = []
    for arm in ("nc", "p333"):
        a = np.array(S[(arm, q)], float); u = a[a[:, 2] == 0]
        out.append(f"{arm}: all_delay median {np.median(a[:,0]):.0f} = {np.median(a[:,0])/planned(q):.1f} s/veh, 'delay' {np.median(a[:,1]):.1f}, speed {np.median(a[:,4]):.1f} km/h, passed {np.median(a[:,3]):.0f}/{planned(q):.0f}; unperturbed n={len(u)}: {u[:,0].mean():.0f} = {u[:,0].mean()/planned(q):.1f} s/veh")
    print(f" q={q:.0f} | " + " | ".join(out))
# per-edge speeds at 3,500 from the space-time side files (mainline edges, all lanes of the road)
print("== per-edge speeds from space-time side files, S1 map, 3,500 veh/h")
off = R[("p333", 3500.0, "none")][0]["m_offsets"]; print(" offsets", off, "dx", R[("p333", 3500.0, "none")][0]["m_st_dx"], "dt", R[("p333", 3500.0, "none")][0]["m_st_dt"])
edges = ["1", "2", "3a", "3", "4a", "4", "5"]
order = sorted(edges, key=lambda e: off[e]); bounds = {e: (off[e], off[order[i + 1]] if i + 1 < len(order) else off["_end"]) for i, e in enumerate(order)}
ST = "/home/catalin/work/phd/v5b1_runs/measure_s01_remote/st/"
ref_speed = {}
for arm in ("nc", "p333"):
    for kind in ("none", "pert"):
        acc = {e: [0.0, 0.0] for e in edges}
        for r in R[(arm, 3500.0, kind)]:
            z = np.load(ST + r["m_st_file"]); v, n = z["v"].astype(float), z["n"].astype(float)
            dx = r["m_st_dx"]
            for e in edges:
                j0, j1 = int(bounds[e][0] // dx), int(np.ceil(bounds[e][1] / dx))
                acc[e][0] += v[:, j0:j1].sum(); acc[e][1] += n[:, j0:j1].sum()
        sp = {e: acc[e][0] / acc[e][1] for e in edges}
        print(f"  {arm} {kind}: " + ", ".join(f"{e} {sp[e]*3.6:.1f}" for e in edges), "km/h (cells assigned by 50-m bins, so edge borders are approximate)")
        ref_speed[(arm, kind)] = sp
pickle.dump({"ref_speed": ref_speed, "bounds": bounds}, open("lowref.pkl", "wb"))
