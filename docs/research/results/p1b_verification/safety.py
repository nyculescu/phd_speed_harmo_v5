"""Meter safety (B1, V109 minor), descriptive: per incident cell and arm (main runs, s = 0), the share of stopped-at-red
first vehicles that approached at >= 10 m/s, plus IP vs each L0 arm at the S1 level from result.json.
Usage: safety.py recs.pkl"""
import json, pickle, sys
recs = pickle.load(open(sys.argv[1], "rb"))
R = json.load(open("/home/catalin/work/phd/v5b1_runs/p1b/v108/result.json"))
A = R["tune"]["arms"]
IX = {(r["pre"], r["post"], bool(r["back"]), r["incident"], float(r["q"]), int(r["seed"])): r for r in recs
      if 7400600 <= r["seed"] <= 7400699 and r["k"] == 0 and not r["rs"] and not r["d"] and not r["c"] and not r["fa"]}
tot_n = tot_10 = 0
for q in ("1600", "2000"):
    a = A[q]
    for inc in ("slow", "block"):
        arms = {x: (a[x], None, False) for x in ("N", "FX", "FB", "PI", "AD")}
        for x in ("ID", "IP"):
            p = a["ID"] if x == "ID" else a["IP"][inc]
            arms[x] = (a["N"], p.replace("+back", ""), p.endswith("+back"))
        row = []
        for nm, (pre, post, back) in arms.items():
            rr = [IX[(pre, post, back, inc, float(q), s)]["approach_red_mps"] for s in range(7400600, 7400700)]
            n, n10 = sum(x["n"] for x in rr), sum(x["n_ge_10"] for x in rr)
            tot_n += n
            tot_10 += n10
            row.append(f"{nm} {n10}/{n} = {100 * n10 / n:.1f} %")
        c = f"{inc}_q{q}"
        ipl0 = R["eval"]["cells"][c]["IP_vs_L0"]
        print(f"{c}: approach >= 10 m/s: " + "; ".join(row))
        print("   IP vs L0 (S1 level): " + "; ".join(
            f"{r} {100 * v['all_seeds']['rel']:+.1f} [{100 * v['all_seeds']['rel_ci'][0]:+.1f}, "
            f"{100 * v['all_seeds']['rel_ci'][1]:+.1f}] diffCI lo {v['all_seeds']['diff_ci'][0]:+.1f}" for r, v in ipl0.items()))
print(f"all Table-1 L0/ID/IP main incident runs: {tot_10}/{tot_n} = {100 * tot_10 / tot_n:.1f} % at >= 10 m/s")
