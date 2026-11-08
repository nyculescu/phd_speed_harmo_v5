"""Readable tables from results.json."""
import json
import sys
R = json.load(open("results.json"))
sec = sys.argv[1]
for cell in ("X1", "X2"):
    C = R[cell]
    arms = [a for a in C if a not in ("nc", "nc_medians")]
    print(f"== {cell}")
    if sec == "tot":
        print("nc medians:", {k: C["nc"]["medians"][k] for k in ("ttc_net", "ttc2", "ttc15", "all_delay", "passed", "dist", "vs", "e_mov5", "e_stop5", "e_lo", "e_mid", "e_hi", "jam_share", "rate_km", "rate_mov18", "rate_lo", "rate_mid", "rate_hi")})
        for a in arms:
            e = C[a]["effect_vs_nc"]
            print(f"{a:12s}", " ".join(f"{k}={v}" for k, v in e.items()))
    if sec == "split":
        for a in arms:
            sp = C[a]["splits"]
            print(f"-- {a}: total ttc3 diff median {C[a]['total_ttc3_diff']['median']} mean {C[a]['total_ttc3_diff']['mean']}")
            for k, v in sp.items():
                print(f"   {k:16s} nc {v['nc_med']:7.1f} arm {v['arm_med']:7.1f} dmed {v['diff_median']} dmean {v['diff_mean']} share {v['share_of_total_mean']}")
    if sec == "expo":
        for a in arms:
            print(f"-- {a}")
            print("   exposure (+ = more):", " ".join(f"{k}={v}" for k, v in C[a]["exposure_change_pct"].items()))
            print("   rates (+ = fewer):", " ".join(f"{k}={v}" for k, v in C[a]["rate_effect"].items()))
    if sec == "kit":
        for a in arms:
            k = C[a]["kitagawa_speed_band"]
            print(f"-- {a}: total {k['total_mean']} rate {k['rate_part_mean']} expo {k['exposure_part_mean']} rate_share {k['rate_share']}")
            for b, x in k["per_band"].items():
                print(f"     {b}: rate {x['rate_mean']} expo {x['exposure_mean']}")
    if sec == "seed":
        for a in arms:
            print(f"-- {a}: {C[a]['per_seed_counts']}")
            for k, v in C[a]["per_seed"].items():
                print(f"     {k}: {v}")
