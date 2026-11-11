import json
J = json.load(open("/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/baseline_v5/readings/read6_v23_supplement.json"))
T = J["cells"]["TRUCK"]
f = lambda e: "%+.2f [%+.2f, %+.2f]" % (e["effect"], *e["ci_m"]) if "ci_m" in e else "%+.2f [%+.2f, %+.2f] (95)" % (e["effect"], *e["ci95"])
f95 = lambda e: "%+.2f [%+.2f, %+.2f]" % (e["effect"], *e["ci95"])
for name, M in (("TRUCK", T["map"]), ("S", J["S"]["map"])):
    print(name, "map, 97.5 %: opponent | cf | delay   (sorted by cf)")
    for o in sorted(M, key=lambda o: M[o]["cf"]["effect"]):
        print("  %-18s cf %s | delay %s" % (o, f(M[o]["cf"]), f(M[o]["delay"])))
print("overfit_vs_p333 (rule vs p333, 95 %?):")
for o, v in T["overfit_vs_p333"].items():
    print("  %-18s delay %+.2f [%+.2f, %+.2f] | cf %+.2f [%+.2f, %+.2f]" % (o, *v["delay"], *v["cf"]))
for name, R in (("TRUCK", T["map_report_only"]), ("S", J["S"]["map_report_only"])):
    for o in ("3E-C_TRUCK", "p333", "os0_10_10", "nc"):
        print(name, "report-only vs", o)
        for k in ("jam_share", "congested_share", "jams", "congested_km_mean", "congested_km_max", "osc_kmh", "jam_share_nc", "congested_km_mean_nc", "events_ge45", "ttc15", "ttc2", "sev3", "ttc3_lc_share", "robust_braking", "alks_past_limit", "b45_step", "delay_ramp", "delay_ramp2", "flow"):
            e = R[o].get(k)
            if e is None: print("   ", k, "absent"); continue
            try: print("    %-22s %s  (medians P %.4g, O %.4g)" % (k, f95(e), e.get("median_P", float("nan")), e.get("median_O", float("nan"))))
            except Exception as ex: print("   ", k, str(e)[:200])
print("no_control:", T["no_control"])
print("location v3w cf keys:", {k: v for k, v in T["location"]["v3w"].items() if k.startswith("cf|")})
print("location 3E-C cf:", {k: v for k, v in T["location"]["3E-C_TRUCK"].items() if k.startswith("cf|")})
print("location p333 cf:", {k: v for k, v in T["location"]["p333"].items() if k.startswith("cf|")})
print("end_stop2:", {a: T["location"][a].get("end_stop2") for a in ("v3w", "3E-C_TRUCK", "p333", "nc", "os0_10_10")})
print("must_carry:", J["must_carry"])
