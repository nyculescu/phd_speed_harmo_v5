"""P1 -> P1b comparison (descriptive): verdicts, S1 rows, S2 brackets, TP, S3 break-evens, combined row, arms;
emergency stops (field 'emergency_stops', both studies; P1b also 'emergency_meter') and max queues.
Reads both result.json files and P1b recs.pkl. Usage: p1_vs_p1b.py recs.pkl"""
import json, pickle, sys
import numpy as np
P1 = json.load(open("/home/catalin/work/phd/v5b1_runs/p1/v99/result.json"))
P2 = json.load(open("/home/catalin/work/phd/v5b1_runs/p1b/v108/result.json"))
L0 = ("N", "FX", "FB", "PI", "AD")
CELLS = ("slow_q1600", "slow_q2000", "block_q1600", "block_q2000")
pc = lambda x: f"{100 * x:+.1f}"
for tag, R in (("P1", P1), ("P1b", P2)):
    e = R["eval"]
    print(f"== {tag}: S1a {e['S1']['S1a_pass']} S1b {e['S1']['S1b_pass']} cells {e['S1']['S1b_cells_both_views']}")
    for q in ("1600", "2000"):
        a = R["tune"]["arms"][q]
        print(f"  arms q{q}: " + ", ".join(f"{k} {a[k]}" for k in L0 + ("ID",)) + f", IP {a['IP']}")
    for c in CELLS:
        s1 = e["S1"]["per_cell_stats"][c]
        idv = " ".join(f"{r} {pc(s1['ID_vs'][r]['all_seeds']['rel'])}" for r in L0)
        ipid = s1["IP_vs_ID"]["all_seeds"]
        ipl0 = " ".join(f"{r} {pc(e['cells'][c]['IP_vs_L0'][r]['all_seeds']['rel'])}" for r in L0)
        s2 = e["S2"][c]["all_seeds"]
        s3 = e["S3"][c]
        be = "; ".join(f"{l}* {s3[l + '_star']['all_seeds']['value']:.2f} {s3[l + '_star']['all_seeds']['flag']} "
                       f"{s3[l + '_star']['all_seeds']['binding_arm']} [{s3[l + '_star']['all_seeds']['ci'][0]:.2f}, "
                       f"{s3[l + '_star']['all_seeds']['ci'][1]:.2f}]" for l in "dcp")
        cb = s3["combined_row"]["vs_IP"]["all_seeds"]["rel"]
        t1 = e["table1_operating_map"][c]["arms"]
        mq = " ".join(f"{x} {t1[x]['median_max_queue']:g}" for x in ("N", "FB", "PI", "AD", "ID", "IP"))
        print(f"  {c}: ID vs [{idv}]; IP vs ID {pc(ipid['rel'])} [{pc(ipid['rel_ci'][0])}, {pc(ipid['rel_ci'][1])}] "
              f"diffCI [{ipid['diff_ci'][0]:.1f}, {ipid['diff_ci'][1]:.1f}]; IP vs [{ipl0}]")
        print(f"     S2 [{pc(s2['y'])}, {pc(s2['x'])}] TP {pc(e['TP'][c]['rel'])}; {be}; comb vs IP {pc(cb)}; "
              f"max queue veh med: {mq}")
# emergency stops in P1b (same field as P1's safety.py; non-replicate evaluation runs)
recs = pickle.load(open(sys.argv[1], "rb"))
ev = [r for r in recs if 7400600 <= r["seed"] <= 7400699 and r["k"] == 0]
ev0 = [r for r in ev if not r["rs"]]
for lab, rr in (("k=0 all", ev), ("k=0, rs=0", ev0)):
    print(f"P1b {lab}: runs {len(rr)}, with emergency_stops>0 {sum(r['emergency_stops'] > 0 for r in rr)}, "
          f"with emergency_meter>0 {sum((r['emergency_meter'] or 0) > 0 for r in rr)}, total emergency_stops "
          f"{sum(r['emergency_stops'] for r in rr)}, total emergency_meter {sum(r['emergency_meter'] or 0 for r in rr)}, "
          f"collisions {sum(r['collisions'] for r in rr)}")
# per arm (main runs, Table 1 arms) emergency stops: median per run and seeds with > 0
IX = {(r["pre"], r["post"], bool(r["back"]), r["incident"], float(r["q"]), int(r["seed"]), float(r["d"]), float(r["c"]),
       bool(r["fa"]), float(r["rs"] or 0)): r for r in ev}
for q in ("1600", "2000"):
    a = P2["tune"]["arms"][q]
    for inc in ("slow", "block", "none"):
        row = []
        arms = {"NC": ("NC", None, False), **{x: (a[x], None, False) for x in L0}}
        if inc != "none":
            for x in ("ID", "IP"):
                p = a["ID"] if x == "ID" else a["IP"][inc]
                arms[x] = (a["N"], p.replace("+back", ""), p.endswith("+back"))
        for nm, (pre, post, back) in arms.items():
            rr = [IX[(pre, post, back, inc, float(q), s, 0.0, 0.0, False, 0.0)] for s in range(7400600, 7400700)]
            es = [r["emergency_stops"] for r in rr]
            em = [r["emergency_meter"] or 0 for r in rr]
            row.append(f"{nm} {np.median(es):g}/{np.median(em):g} ({sum(x > 0 for x in es)}/{sum(x > 0 for x in em)})")
        print(f"P1b {inc}_q{q} emergency_stops/emergency_meter median (runs>0): " + "; ".join(row))
