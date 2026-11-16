"""Every number the result note quotes: (P) from the run's result.json, (D) from rederive.py's output (page draws).
Usage: note_numbers.py mine_page.json"""
import json, sys
R = json.load(open("/home/catalin/work/phd/v5b1_runs/p1b/v108/result.json"))
M = json.load(open(sys.argv[1]))
e = R["eval"]
L0 = ("N", "FX", "FB", "PI", "AD")
CELLS = ("slow_q1600", "slow_q2000", "block_q1600", "block_q2000")
f = lambda s: f"{100 * s['rel']:+.1f} [{100 * s['rel_ci'][0]:+.1f}, {100 * s['rel_ci'][1]:+.1f}]"
g = lambda s: f"{s['diff']:+.1f} [{s['diff_ci'][0]:+.1f}, {s['diff_ci'][1]:+.1f}] s"
print("S1a per arm (a) cells:", {r: e["S1"]["all_seeds"]["S1a"]["R"][r]["a_cells"] for r in L0},
      "binding", e["S1"]["all_seeds"]["S1a"]["binding"])
print("S1a b-fail:", {r: [c for c, v in e["S1"]["all_seeds"]["S1a"]["R"][r]["cells"].items() if not v["b"]] for r in L0})
for c in CELLS:
    s1 = e["S1"]["per_cell_stats"][c]
    print(f"{c} (P, S1 level): ID vs " + "; ".join(f"{r} {f(s1['ID_vs'][r]['all_seeds'])}" for r in L0)
          + f" | IP vs ID {f(s1['IP_vs_ID']['all_seeds'])} {g(s1['IP_vs_ID']['all_seeds'])}")
    m = M["cells"][c]
    print(f"   (D, 95 %) IP vs " + "; ".join(f"{r} {f(m['IP_vs_L0_95'][r])}" for r in L0))
    lad = e["fig1_ladder"][c]
    print("   ladder (P): " + " -> ".join(f"{x['arm']} {x['median_delay_s']:.1f}" for x in lad["rungs"]))
    s2 = e["S2"][c]
    print(f"   S2 (P): {s2['statements']['text']}; TP {100 * e['TP'][c]['rel']:.1f} %; OR_in picks a PI plan on "
          f"{100 * m['S2']['or_in_pick_is_pi_plan']:.0f} % of seeds (D)")
    s3 = e["S3"][c]
    for l in "dcp":
        a = s3[l + "_star"]["all_seeds"]
        print(f"   {l}* (P) {a['value']:.2f} {a['flag']} {a['binding_arm']} CI [{a['ci'][0]:.2f}, {a['ci'][1]:.2f}] "
              f"never-ahead share {a['share_never_ahead']:.3f}")
    print(f"   combined vs IP (P) {f(s3['combined_row']['vs_IP']['all_seeds'])}; IP median by d (D) "
          f"{[round(x, 1) for x in m['S3']['IP_median_by_d']]}")
    t1 = e["table1_operating_map"][c]["arms"]
    print("   T1 (P) delay/served: " + "; ".join(f"{x} {t1[x]['median_delay_s']:.1f}/{t1[x]['median_served_vph']:.0f}"
                                            for x in ("NC",) + L0 + ("ID", "IP", "ORX_4", "OR_in")))
    print("   approach red (P) med/max/n>=10: " + "; ".join(
        f"{x} {t1[x]['approach_red_mps_median']}/{t1[x]['approach_red_mps_max']}/{t1[x]['approach_red_n_ge_10']}"
        for x in L0 + ("ID", "IP")))
    print("   queue m med/max (P) and spill V109 (D): " + "; ".join(
        f"{x} {t1[x]['median_max_queue_m']:.0f}/{t1[x]['max_max_queue_m']:.0f} {m['realism'][x]['spill_new']:.2f}"
        for x in ("NC",) + L0 + ("ID", "IP")))
    print("   commanded vs realised G+y+r (P): " + "; ".join(
        f"{x} {t1[x]['median_commanded_vph']}/{sum(t1[x]['median_discharge_vph'].values()):.0f}" for x in L0 + ("ID", "IP")))
for q in ("1600", "2000"):
    pq = e["per_q"][q]
    print(f"clean q{q} (P): " + "; ".join(f"{x} {v['median_delay_s']:.1f}" for x, v in pq["clean_day"].items() if isinstance(v, dict) and "median_delay_s" in v),
          "| spill (D):", {x: round(v["spill_new"], 2) for x, v in M["clean_realism"][q].items()},
          "| FA cost (P):", g(pq["false_alarm_cost"]["all_seeds"]))
    print(f"   IP tuning top-3 (D): {M['arms'][q]['IP_top3_tuning']}")
flags = [(c, x, round(v["realism"][x]["spill_new"], 3)) for c, v in M["cells"].items() for x in v["realism"]
         if v["realism"][x]["spill_new"] > 0.05]
print("V109 spill > 5 % (D, Table 1 arms):", flags)
print("max over cells/arms of max_queue_m (P):", max(t["max_max_queue_m"] for c in CELLS
                                                    for t in e["table1_operating_map"][c]["arms"].values()))
for c, v in e["runner_rows"].items():
    print(f"runner {c} (D): IP vs ID {f(v['IP_vs_ID']['all_seeds'])}; self: " + " ".join(
        f"{x} {100 * v['vs_self_s0'][x]['all_seeds']['rel']:+.1f}" for x in v["vs_self_s0"]))
print("runner IP slow_q1600 self CIs:", {s: f(e["runner_rows"][f"s{s}_slow_q1600"]["vs_self_s0"]["IP"]["all_seeds"])
                                        for s in ("0.1", "0.3")})
print("runner IP slow_q1600 self diffs:", {s: g(e["runner_rows"][f"s{s}_slow_q1600"]["vs_self_s0"]["IP"]["all_seeds"])
                                          for s in ("0.1", "0.3")})
