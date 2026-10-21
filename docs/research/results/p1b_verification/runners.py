"""Runner rows (R5), descriptive: sign convention check, IP's plan per cell, cycle shares, realised discharge by
phase, per-seed tipping. Reads recs.pkl and rederive.py's output. Usage: runners.py recs.pkl mine.json"""
import json, pickle, sys
import numpy as np
recs = pickle.load(open(sys.argv[1], "rb"))
M = json.load(open(sys.argv[2]))
IX = {(r["pre"], r["post"], bool(r["back"]), r["incident"], float(r["q"]), int(r["seed"]), int(r["k"]), float(r["d"]),
       float(r["c"]), bool(r["fa"]), float(r["rs"] or 0.0)): r for r in recs if 7400600 <= r["seed"] <= 7400699}
EVAL = range(7400600, 7400700)


def run(a, x, inc, q, s, rs):
    N = a["N"]
    if x in ("ID", "IP"):
        p = a["ID"] if x == "ID" else a["IP"][inc]
        back = p.endswith("+back")
        return IX[(N, p[:-5] if back else p, back, inc, q, s, 0, 0.0, 0.0, False, rs)]
    return IX[(a[x], None, False, inc, q, s, 0, 0.0, 0.0, False, rs)]


def cyc(rate):   # R2: c(q) = max(11, 28800 / q); green 6, amber 3, red the rest
    c = max(11.0, 28800.0 / rate)
    return c, 3 / c, (c - 9) / c


for name, v in M["runner_rows"].items():
    s_, cell = name.split("_", 1)
    inc, qq = cell.split("_q")
    q, rs = float(qq), float(s_[1:])
    a = M["arms"][qq]
    x = v["IP_vs_ID"]
    chk = abs(x["rel"] - (np.median(np.array([run(a, "ID", inc, q, s, rs)["delay_s"] for s in EVAL]) -
                                    np.array([run(a, "IP", inc, q, s, rs)["delay_s"] for s in EVAL])) /
                          np.median([run(a, "ID", inc, q, s, rs)["delay_s"] for s in EVAL]))) < 1e-12
    out = [f"{name}: IP={a['IP'][inc]} ID={a['ID']}  IP vs ID rel {100 * x['rel']:.1f} % CI [{100 * x['rel_ci'][0]:.1f}, "
           f"{100 * x['rel_ci'][1]:.1f}] diff {x['diff']:.1f} s [{x['diff_ci'][0]:.1f}, {x['diff_ci'][1]:.1f}] "
           f"(sign check {chk}); medians ID {v['median']['ID']:.1f} IP {v['median']['IP']:.1f}; "
           f"hash-mismatch seeds {v['runner_hash_mismatch_seeds']}, runner share of trips {v['runner_share_of_trips_med']:.3f}"]
    for arm in ("IP", "ID", "PI", "FB"):
        sv = v["vs_self_s0"][arm]
        d0 = np.array([run(a, arm, inc, q, s, 0.0)["delay_s"] for s in EVAL])
        d1 = np.array([run(a, arm, inc, q, s, rs)["delay_s"] for s in EVAL])
        r0 = [run(a, arm, inc, q, s, 0.0) for s in EVAL]
        r1 = [run(a, arm, inc, q, s, rs) for s in EVAL]
        dis0 = {p: np.median([r["discharge_vph"][p] for r in r0]) for p in "Gyr"}
        dis1 = {p: np.median([r["discharge_vph"][p] for r in r1]) for p in "Gyr"}
        cm = np.median([r["commanded_mean_vph"] for r in r1])
        c, ya, re = cyc(cm)
        out.append(f"   {arm} vs self s0 rel {100 * sv['rel']:.1f} % CI [{100 * sv['rel_ci'][0]:.1f}, {100 * sv['rel_ci'][1]:.1f}]"
                   f" diff {sv['diff']:.1f} s; medians {np.median(d0):.1f} -> {np.median(d1):.1f}; mean +{np.mean(d1 - d0):.1f} s;"
                   f" seeds +>50 s {int(np.sum(d1 - d0 > 50))}, better {int(np.sum(d1 < d0 - 1e-9))}; commanded med {cm:.0f} "
                   f"(cycle {c:.1f} s, amber {100 * ya:.0f} %, red {100 * re:.0f} %); discharge G/y/r s0 "
                   f"{dis0['G']:.0f}/{dis0['y']:.0f}/{dis0['r']:.0f} -> {dis1['G']:.0f}/{dis1['y']:.0f}/{dis1['r']:.0f}; "
                   f"red-cross share med {np.median([r['red_cross_share'] for r in r1]):.3f}, runners "
                   f"{np.median([r['runner_red_cross_share'] for r in r1 if r['runner_red_cross_share'] is not None]):.3f}")
    print("\n".join(out))
