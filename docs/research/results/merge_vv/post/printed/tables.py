"""Renders recomputed.json, v3.json and the smoke, identity, V1 and status files into printed_tables.md (post hoc, printed only).
usage: python -I tables.py"""
import json
from pathlib import Path

RUN = Path("/home/catalin/work/phd/v5b1_runs/vv_remote")
OUT = Path("/home/catalin/work/phd/v5b1_runs/vv_post/printed")
R = json.loads((OUT / "recomputed.json").read_text())
V3 = json.loads((RUN / "vv_screen" / "v3.json").read_text())
SMOKE = json.loads((RUN / "vv_smoke" / "smoke.json").read_text())
IDENT = json.loads((RUN / "vv_replay" / "ident.json").read_text())
V1 = json.loads((RUN / "vv_trace" / "v1.json").read_text())
V3W = ("w0u250", "w1u500", "w2u250", "w3u500", "w4u500")
RULES = ("lr400_16_1", "grid_lr400_13_1")
ARMS = V3W + RULES + ("p333", "nc")
PER = ("before", "taper", "hold", "after", "rest")
L = []


def e(x: dict, d: int = 1) -> str:
    return f"{x['pt']:+.{d}f} [{x['lo95']:+.{d}f}, {x['hi95']:+.{d}f}]"


def table(head: list, rows: list) -> None:
    def cell(x) -> str:
        return str(x).replace("|", "\\|")
    L.append("| " + " | ".join(cell(x) for x in head) + " |")
    L.append("|" + "---|" * len(head))
    for r in rows:
        L.append("| " + " | ".join(cell(x) for x in r) + " |")
    L.append("")


def edges_table(keys: list, opps=RULES) -> None:
    head = ["measure"] + [f"{o} {c[1:]} m" for o in opps for c in ("L300", "L600")]
    rows = []
    for k, label in keys:
        rows.append([label] + [e(R["edges"][c][o][k]) + (" †" if R["edges"][c][o][k]["opp_med"] == 0 else "") for o in opps for c in ("L300", "L600")])
    table(head, rows)
    L.append("† the opponent's median is 0, so the C-D5 denominator is 1e-9: the cell is 0 only because most paired differences are exactly 0; it is not a percentage.")
    L.append("")


def medians_table(keys: list) -> None:
    head = ["measure"] + [f"{a} {c[1:]} m" for a in ("v3w",) + RULES + ("p333", "nc") for c in ("L300", "L600")]
    rows = []
    for k, label in keys:
        r = [label]
        for a in ("v3w",) + RULES + ("p333", "nc"):
            for c in ("L300", "L600"):
                if a == "v3w":
                    r.append(f"{R['edges'][c]['nc'][k]['v3w_med']:.1f}")
                else:
                    r.append(f"{R['edges'][c][a][k]['opp_med']:.1f}")
        rows.append(r)
    table(head, rows)


L.append("# Merge V&V printed items (V2, V3a, V3b): post hoc assembly")
L.append("")
L.append("Plan: merge_vv.md v1.1 (V532) §2, 'Printed, never deciding' and V2's missed share. Nothing here decides anything. "
         "Edges use C-D5 (c1_confirm.md §1): per learner the median over seeds of −(v3w − opponent)/median(opponent) × 100, mean of the 5 learners, "
         "joint seed resamples B = 20,000 (rng 20261108), **95 % percentile intervals** (the reader's printed level). Positive = v3w has less; "
         "for served flow (`passed`) positive = v3w serves more.")
L.append("")
L.append("**Sources.** [v3] = `vv_remote/vv_screen/v3.json` (committed reader `read_vv.py` at 6e96988). [rows] = recomputed by `printed.py` in this folder "
         "from `vv_screen/s6_rows.jsonl` with an own implementation (does not import the reader). [smoke], [ident], [v1], [status] = the files of those names. "
         f"Every [v3] number listed below was recomputed from [rows]: {R['compare']['n_numbers']} numbers compared, largest absolute difference "
         f"{R['compare']['max_abs_diff']}, so [v3] and [rows] agree exactly (`compare_v3.tsv`). Jams are the exception: [v3] only, not recomputed "
         "(they need read6's space-time reading of the `st/` side files).")
L.append("")
L.append(f"Rows: {R['n_rows']} (9 arms × 480 seeds 7,492,000-479 × 2 lengths), 0 missing, 0 dropped ([v3] `dropped` empty, `drops.json` empty); "
         f"CPU {V3['cpus']}; [v3] `bugs` all empty ({', '.join(V3['bugs'])}); [v3] `void` empty.")
L.append("")

L.append("## 1. Smoke, identity and V1 automatic checks")
L.append("")
sm = SMOKE
rows = [["smoke overall", "pass = " + str(sm["pass"]), "[smoke]"],
        ["missing / replay differs / side files differ / twin differs", f"{len(sm['missing_in_a'])} / {len(sm['replay_differs'])} / {len(sm['side_files_differ'])} / {len(sm['twin_differs'])}", "[smoke]"],
        ["T0 lane-length differences outside 3a/4a", str(len(sm["t0_lengths"])), "[smoke]"],
        ["meter bugs (whole-second = ttc_net, half = ttc_half)", str(len(sm["meter_bugs"])), "[smoke]"],
        ["remapped x outside the 300-m training range (x_out)", "0 in all 8 controlled L600 runs of seed 7,493,010", "[smoke] obs"],
        ["column-15 cap share, L600 seed 7,493,010", "0.0 for all 8 controlled arms", "[smoke] obs"],
        ["demand differs between lengths", str(len(sm["demand_differs"])), "[smoke]"],
        ["wall time per run, s (300 m / 600 m)", f"{min(v for k, v in sm['wall_s'].items() if k.startswith('L300'))}-{max(v for k, v in sm['wall_s'].items() if k.startswith('L300'))} / "
         f"{min(v for k, v in sm['wall_s'].items() if k.startswith('L600'))}-{max(v for k, v in sm['wall_s'].items() if k.startswith('L600'))}", "[smoke]"],
        ["identity replay (9 arms, stored E30 seeds 7,489,160-161): rule / learner / diagnostic differences, missing",
         f"{len(IDENT['rule_diff'])} / {len(IDENT['learner_diff'])} / {len(IDENT['diagnostics'])}, {len(IDENT['missing'])}; traced replays the same: "
         f"{len(IDENT['traced']['rule_diff'])} / {len(IDENT['traced']['learner_diff'])} / {len(IDENT['traced']['diagnostics'])}, {len(IDENT['traced']['missing'])}", "[ident]"],
        ["identity CPU = CF CPU", f"{IDENT['cpu'] == IDENT['cf_cpu']} ({IDENT['cpu']}); learner mismatch disclosed = {IDENT['learner_diff_disclosed']}; tracer_bug = {IDENT['tracer_bug']}; action = {IDENT['action']}", "[ident]"],
        ["V1 outcome", V1["outcome"], "[v1], [status]"],
        ["V1 wiring / definition / twin failures", f"{len(V1['wiring_fail'])} / {len(V1['definition_fail'])} / {len(V1['twin_fail'])}", "[v1]"],
        ["V1 twins compared (traced vs untraced, smoke seeds)", f"{len(V1['twins'])}, all equal", "[v1]"],
        ["V1 traced runs classified", f"{len(V1['runs'])} (12 smoke-seed traces, 6 stored-E30-seed traces)", "[v1]"],
        ["V1 visual sample drawn", f"{len(V1['sample'])} samples (rng 20261115); visual check still pending (not done here)", "[v1]"]]
table(["check", "value", "source"], rows)

L.append("Smoke lane-end standing printed for the author (plan §4), one seed (7,493,010) [smoke]:")
L.append("")
table(["run", "`end_stop` merge 1 (veh-s)", "`end_stop2` merge 2 (veh-s)", "vehicles stood at 3a / 4a end"],
      [[k, f"{v['end_stop']:.0f}", f"{v['end_stop2']:.0f}", f"{v['stand_n']['3a_0']} / {v['stand_n']['4a_0']}"] for k, v in sorted(SMOKE["standing_for_author"].items())])
L.append("V1 per traced run (printed by the plan: distinct encounters, distinct vehicles standing per lane end; next-lane share = leader on the next lane of the route):")
L.append("")
rows = []
for k, v in V1["runs"].items():
    rows.append([k.replace("~trace", ""), int(sum(v["classes"].values())), v["encounters"]["n"], f"{100 * v['next_lane_share']:.1f}",
                 v["stand_n"].get("3a_0"), v["stand_n"].get("4a_0"), len(v["edge1"])])
table(["run (cell|arm seed)", "counted samples", "distinct encounters", "next-lane share %", "stood at 3a end (vehicles)", "stood at 4a end (vehicles)", "edge-1 samples"], rows)

agg = {}
for v in V1["runs"].values():
    for cls, n in v["classes"].items():
        f = cls.split(" | ")
        for i, name in enumerate(("follower lane", "leader relation", "leader standing", "merged 5 s", "follower type", "speed band", "period", "road group")):
            agg.setdefault(name, {}).setdefault(f[i], 0)
            agg[name][f[i]] += n
tot = sum(agg["follower lane"].values())
L.append(f"V1 classification pooled over the 18 traced runs ({tot} counted samples; pooling across arms and lengths is post hoc and descriptive only) [v1]:")
L.append("")
rows = [[name, ", ".join(f"{k} {100 * n / tot:.1f} %" for k, n in sorted(d.items(), key=lambda x: -x[1]))] for name, d in agg.items()]
table(["dimension", "shares"], rows)

L.append("## 2. V2 resolution (300-m runs)")
L.append("")
rows = []
for r in RULES:
    x = V3["v2"][r]
    rows.append([r, e(x["edge_01s"]), e(x["edge_1hz"]), e(x["diff"], 2), str(x["within"])])
table(["opponent", "0.1-s edge", "1-Hz edge", "difference (points)", "within ±3"], rows)
L.append(f"Outcome [v3]: **{V3['v2']['outcome']}**. Meter equality in every 300-m run [rows]: whole-second count ≠ `ttc_net` in "
         f"{R['checks']['meter_whole_ne_ttc_net']} rows, half-second ≠ `ttc_half` in {R['checks']['meter_half_ne_ttc_half']}; "
         f"300-m rows without the meter {R['checks']['L300_rows_without_meter']}, 600-m rows with it {R['checks']['L600_rows_with_meter']}.")
L.append("")
L.append("Missed share per arm = (0.1-s time − 1-Hz count × 1 s) / 0.1-s time. [v3] prints the median over seeds; the pooled ratio and the 10th-90th percentiles are [rows], post hoc.")
L.append("")
rows = []
for a in ARMS:
    m = R["missed_share"][a]
    rows.append([a, f"{100 * V3['v2']['missed_share'][a]:+.3f}", f"{100 * m['pooled']:+.3f}", f"{100 * m['q10']:+.2f} to {100 * m['q90']:+.2f}",
                 f"{m['sum_01s']:.0f}", f"{m['sum_1hz']:.0f}"])
table(["arm", "missed share, median % [v3]", "pooled % [rows]", "10th-90th pct of per-run share %", "Σ 0.1-s time (veh-s)", "Σ 1-Hz count"], rows)

L.append("## 3. Deciding readings, for context only [v3]")
L.append("")
rows = [["V3a replication (`ttc_net`, 97.5 %)", e({"pt": V3["v3a"]["replication"][r]["pt"], "lo95": V3["v3a"]["replication"][r]["lo"], "hi95": V3["v3a"]["replication"][r]["hi"]}),
         r, V3["v3a"]["replication"]["reading"]] for r in RULES]
rows += [["V3a main-lane (97.5 %)", e({"pt": V3["v3a"]["main_lane"][r]["pt"], "lo95": V3["v3a"]["main_lane"][r]["lo"], "hi95": V3["v3a"]["main_lane"][r]["hi"]}),
          r, V3["v3a"]["main_lane"]["reading"]] for r in RULES]
rows += [["V3b 600 m (98.75 % for WORSE)", e({"pt": V3["v3b"]["worse"][r]["pt"], "lo95": V3["v3b"]["worse"][r]["lo"], "hi95": V3["v3b"]["worse"][r]["hi"]}),
          r, V3["v3b"]["reading"]] for r in RULES]
rows += [["V3b change 600 − 300 (95 %)", e(V3["v3b"]["change"][r]), r, "depends on length" if V3["v3b"]["change"][r]["depends"] else "-"] for r in RULES]
table(["reading", "edge % [interval]", "rule", "outcome"], rows)

L.append("## 4. Close-following edges by road group, per merge and by period")
L.append("")
L.append("Edges, % [95 %], [v3] = [rows]. Merge area = 3a, r, rj, 4a, r2, rj2; merge 1 = 3a + ramp 1; merge 2 = 4a + ramp 2; rest = all other roads incl. junctions. "
         "Periods are the row's `ttc3_p_*` keys; they equal the sums of the `m_road_ttc3` period keys in every row "
         f"({R['checks']['period_ne_road_periods']} mismatches) and sum to `ttc_net` ({R['checks']['periods_sum_ne_ttc_net']} mismatches) [rows]. "
         f"Road keys that ever carry a sample: {', '.join(R['road_keys'])} (none on edges 4 or 5).")
L.append("")
G = [("g_merge", "merge area"), ("g_m1", "merge 1"), ("g_m2", "merge 2"), ("g_edge1", "edge 1"), ("g_rest", "rest"), ("ttc_no_e1", "all but edge 1"),
     ("ttc_net", "all (`ttc_net`)")] + [(f"p_{p}", f"period {p}") for p in PER]
edges_table(G)
L.append("Medians per arm, samples per run (opponent: its median, the C-D5 denominator; v3w: mean of the 5 learners' medians) [rows]:")
L.append("")
medians_table(G)
L.append(f"Largest remaining deficit at 600 m, samples per run (median over seeds of v3w's learner mean − rule) [v3] = [rows]: "
         + "; ".join(f"{r}: merge area {R['deficit_600'][r]['g_merge']:+.1f}, edge 1 {R['deficit_600'][r]['g_edge1']:+.1f}, rest {R['deficit_600'][r]['g_rest']:+.1f} → "
                     f"{V3['v3b']['deficit_600'][r]['largest_deficit']}" for r in RULES) + ".")
L.append("")

L.append("## 5. Delay, TTT, served flow, braking and stricter close-following measures")
L.append("")
L.append("TTC below 3 s and braking at 3 m/s² or harder are terms of v3w's training reward; TTC below 2 s and 1.5 s are stricter versions of the rewarded event "
         "and `b45_step` of the rewarded braking; only DRAC (`sev3`) is outside the reward.")
L.append("")
L.append("TTT is present: `N` is the per-step count of vehicles in the network plus the insertion queue, summed over the fixed window (vehicle-seconds; "
         "`b_env.py:440-442`; `plant_sweep.py:30` names it `ttt`). `all_delay` = `N` − distance / (100 km/h), insertion queue and unfinished vehicles included "
         "(`plant_sweep.py:432`). At 600 m the network holds 600 m more lane, so TTT and delay are compared within a length only.")
L.append("")
O5 = [("all_delay", "delay (`all_delay`)"), ("N", "TTT (`N`)"), ("passed", "served flow (`passed`, + = v3w more)"), ("b45_step", "`b45_step`"),
      ("ttc2", "`ttc2`"), ("ttc15", "`ttc15`"), ("sev3", "`sev3` (DRAC)"), ("vv_enc", "distinct encounters (`vv_enc`)"),
      ("vv_ttc3_main", "main-lane count (`vv_ttc3_main`) [rows] only")]
edges_table(O5)
L.append("Medians per arm [rows]:")
L.append("")
medians_table(O5)
L.append("Runs (of 480) with a zero count, per arm [rows]. These counters are written to a row only once they count something, so an absent key is 0; "
         "the reader reads it as 0 too (`r.get(k, 0.0)`), and no row stores an explicit 0 for them. A median of 0 for the opponent makes the "
         "C-D5 denominator 1e-9 (`max(median, 1e-9)`), so such an edge is not a percentage at all.")
L.append("")
rows = []
for a in ARMS:
    rows.append([a] + [str(R["absent_keys"].get(f"{c}|{a} {k}", 0)) for k in ("ttc2", "ttc15", "sev3", "vv_enc") for c in ("L300", "L600")])
table(["arm"] + [f"{k} {c[1:]} m" for k in ("ttc2", "ttc15", "sev3", "vv_enc") for c in ("L300", "L600")], rows)

L.append("## 6. Collisions and jams")
L.append("")
rows = []
for a in ARMS:
    rows.append([a] + [f"{R['arms'][c][a]['collisions_sum']:.0f} ({R['arms'][c][a]['collision_runs']} runs)" for c in ("L300", "L600")]
                + [f"{R['checks']['stuck_sum'][c][a]:.0f}" for c in ("L300", "L600")] + [f"{R['checks']['teleports_sum'][c][a]:.0f}" for c in ("L300", "L600")])
table(["arm", "collisions 300 m (sum over 480 runs) [v3]=[rows]", "collisions 600 m", "stuck vehicles 300 m [rows, post hoc]", "stuck 600 m", "teleports 300 m [rows, post hoc]", "teleports 600 m"], rows)
L.append("Jam edges [v3] only (not recomputed): % [95 %], + = v3w fewer jams.")
L.append("")
table(["opponent", "300 m", "600 m"], [[o, e(R["jams_v3json"]["L300"][o]) if R["jams_v3json"]["L300"][o] else "not printed",
                                        e(R["jams_v3json"]["L600"][o]) if R["jams_v3json"]["L600"][o] else "not printed"] for o in RULES + ("p333", "nc")])

L.append("## 7. Lane-end standing per arm and merge")
L.append("")
L.append("`end_stop` (3a end, merge 1) and `end_stop2` (4a end, merge 2): vehicle-seconds below 1 m/s in the last 30 m; distinct vehicles = `vv_stand_n`. "
         f"`vv_stand_s` equals `end_stop`/`end_stop2` in every row ({R['checks']['stand_s_ne_end_stop']} mismatches) [rows]. "
         "Median (mean) over 480 seeds; 'zero' = share of runs with no standing vehicle. Vehicle medians [v3] `standing_vehicles` = [rows].")
L.append("")
rows = []
for a in ARMS:
    r = [a]
    for c in ("L300", "L600"):
        x = R["arms"][c][a]
        r += [f"{x['end_stop_med']:.0f} ({x['end_stop_mean']:.0f})", f"{x['stand_n1_med']:.0f} ({x['stand_n1_mean']:.1f}); zero {100 * x['stand_n1_zero']:.0f} %",
              f"{x['end_stop2_med']:.0f} ({x['end_stop2_mean']:.0f})", f"{x['stand_n2_med']:.0f} ({x['stand_n2_mean']:.1f}); zero {100 * x['stand_n2_zero']:.0f} %"]
    rows.append(r)
table(["arm", "300 m merge 1 veh-s", "300 m merge 1 vehicles", "300 m merge 2 veh-s", "300 m merge 2 vehicles",
       "600 m merge 1 veh-s", "600 m merge 1 vehicles", "600 m merge 2 veh-s", "600 m merge 2 vehicles"], rows)
L.append("VV-D12 cut = 1 − median(600 m)/median(300 m) of standing vehicle-seconds, 95 % lower bound (v3w = per-seed mean of learners) [v3] = [rows]; "
         "'removed' needs every lower bound of v3w, both rules and no control ≥ 80 %:")
L.append("")
rows = []
for m in ("merge1", "merge2"):
    for a in ("v3w",) + RULES + ("p333", "nc"):
        x = R["cut"][m][a]
        rows.append([m, a, f"{x['med300']:.1f}", f"{x['med600']:.1f}", f"{100 * x['cut']:.1f}", f"{100 * x['lo95']:.1f}"])
table(["merge", "arm", "median 300 m", "median 600 m", "cut %", "95 % lower %"], rows)
L.append("Per learner (post hoc, [rows]): cut = 1 − median(600 m)/median(300 m) of each learner's own runs, the form the single-arm rows above use. "
         "The v3w row above is the median of the per-seed mean of the 5 learners; with these skewed counts (means far above medians at 600 m) "
         "that median sits above every single learner's median, so v3w's 600-m medians (32.1, 76.7) are not comparable with the rules' single-arm medians.")
L.append("")
rows = []
for a in V3W:
    r = [a]
    for k in ("end_stop", "end_stop2"):
        m3, m6 = R["arms"]["L300"][a][k + "_med"], R["arms"]["L600"][a][k + "_med"]
        r += [f"{m3:.1f}", f"{m6:.1f}", f"{100 * (1 - m6 / m3):.1f}"]
    rows.append(r)
table(["learner", "merge 1 median 300 m", "merge 1 median 600 m", "merge 1 cut %", "merge 2 median 300 m", "merge 2 median 600 m", "merge 2 cut %"], rows)
L.append(f"removed [v3]: merge 1 {V3['v3b']['cut']['merge1']['removed']}, merge 2 {V3['v3b']['cut']['merge2']['removed']} (no control's cut is far below 80 %).")
L.append("")

L.append("## 8. Does any rule beat no control on delay by 10 % at 600 m? (P0 form)")
L.append("")
L.append("Single arm against no control: median over seeds of −(arm − nc)/median(nc) × 100 on `all_delay`, 95 % percentile interval over seed resamples "
         "(B = 20,000, rng 20261108). [v3] prints the point and the lower bound; the upper bound and the learner rows are [rows] (learners post hoc). "
         "P0 passes if any rule has a point ≥ 10 % and a lower bound > 0.")
L.append("")
rows = []
for a in RULES + ("p333",) + V3W:
    r = [a + (" (learner, post hoc)" if a in V3W else "")]
    for c in ("L300", "L600"):
        x = R["p0"][c][a]
        r += [e(x), f"{x['arm_med']:.0f} / {x['ref_med']:.0f}"]
    rows.append(r)
table(["arm", "300 m: % less delay than nc [95 %]", "300 m: median delay arm / nc (veh-s)", "600 m: % less delay than nc [95 %]", "600 m: median delay arm / nc"], rows)
L.append(f"Any rule passes: 300 m {R['p0']['L300']['any_rule']} ([v3] {V3['printed_300']['rule_beats_nc_by_10']['any']}); "
         f"600 m {R['p0']['L600']['any_rule']} ([v3] {V3['printed_600']['rule_beats_nc_by_10']['any']}).")
L.append("")

L.append("## 9. The reader's other printed opponents: p333 and no control")
L.append("")
edges_table(G[:7] + O5[:-1], opps=("p333", "nc"))

L.append("## 10. Column 15 and position remap at 600 m")
L.append("")
rows = []
for a in V3W + RULES + ("p333",):
    x = R["checks"]["c15_600"][a]
    rows.append([a, f"{x['cap']:.0f} / {x['n']:.0f}", f"{x['x_out']:.0f} / {x['x_acc_n']:.0f}", f"{V3['c15_cap_share_600'][a]}" if a in V3W else "not in [v3]"])
table(["arm", "column 15 at cap / decisions [rows]", "x outside training range / positions read on 3a, 4a [rows]", "c15_cap_share_600 [v3]"], rows)

(OUT / "printed_tables.md").write_text("\n".join(L) + "\n")
print("written", len(L), "lines")

ed = R["edges"]
L.append("## 11. Spot-checks and notes (post hoc)")
L.append("")
L.append(f"**Spot-checks.** All {R['compare']['n_numbers']} [v3] numbers listed in `compare_v3.tsv` were recomputed from the rows by `printed.py`; every one matches "
         "exactly (largest difference 0.0; a NaN on either side would count as a mismatch). Five of them, with a hand check of the arithmetic where it is simple:")
L.append("")
rows = [["printed_600 lr400_16_1 g_edge1 pt", "−733.3", "−733.3", "rule median 3.0, v3w ≈ 25 samples: −(25 − 3)/3 × 100 ≈ −733"],
        ["printed_300 grid_lr400_13_1 ttc2 pt", "+42.69", "+42.69", "medians 169.9 vs 309.0; per-learner medians of paired % differ from the ratio of medians (+45 %)"],
        ["printed_600 rule_beats_nc_by_10 p333 pt / lo95", "+30.31 / +29.57", "+30.31 / +29.57", "medians 158,217 vs 234,307 veh-s: 32.5 % on the ratio of medians"],
        ["printed_600 lr400_16_1 all_delay pt [lo95, hi95]", "+0.66 [+0.39, +0.95]", "+0.66 [+0.39, +0.95]", "-"],
        ["standing_vehicles L600 nc 4a_0", "19", "19", "-"],
        ["v2 missed_share w4u500", "−0.205 %", "−0.205 %", "-"],
        ["printed_300 collisions grid_lr400_13_1", "2", "2", "2 runs with 1 collision each"],
        ["v3b cut merge1 v3w lo95", "81.77 %", "81.77 %", "-"]]
table(["number", "[v3]", "[rows]", "hand check"], rows)
L.append("**Notes.**")
L.append("")
notes = [
    "Edge 1 shows −730 % to −2,340 %: the rules and no control have medians of 1-3 samples per run on edge 1 against about 25 for v3w (and 26-27 for p333), at both lengths. "
    "In samples per run the 600-m deficit there is +22.4 (lr400_16_1) and +22.6 (grid_lr400_13_1) [v3]. The plan's pre-stated E30 figures (22-26 against 2-3) recur here.",
    f"At 600 m v3w's total median is 98.3 against 76.5 (lr400_16_1), a gap of about the size of the edge-1 deficit (medians are not additive, so this is an inference). "
    f"With edge-1 samples left out the 600-m edge is {e(ed['L600']['lr400_16_1']['ttc_no_e1'])} against lr400_16_1 and {e(ed['L600']['grid_lr400_13_1']['ttc_no_e1'])} against grid_lr400_13_1 "
    "(95 %, printed only). The plan pre-stated that a WORSE carried by edge 1 is not a lane-length effect. V3b's deciding WORSE rests on lr400_16_1 alone "
    "(98.75 % upper bound −11.4, null 0.475 % at 20,000 swaps) [v3].",
    "The 'rest' group at 600 m has median 0 for the rules and p333, so its cells read +0.0 [+0.0, +0.0] (marked †): an artefact of a zero denominator, not a tie. "
    "The taper period (a 20-s window) has medians of 0-4 and reads the same way.",
    f"Hold period at 600 m: {e(ed['L600']['lr400_16_1']['p_hold'])} against lr400_16_1 (medians 27.2 against 4.0); in the V1 traces every edge-1 sample falls in the hold period (w1u500 93 samples, 86 of them with an ALKS follower; lr400_16_1 10 and no control 5, all car followers) [v1]. "
    "Most close-following of every arm falls in the 'rest' period (after the event end + 120 s): v3w's median there is 825 against a median total of 1,082 per run at 300 m.",
    "`ttc15` and `sev3` at 600 m are 0 in 40-54 % of the controlled arms' runs (and `ttc2` in 11-15 %); opponent medians are 1-2 events, so the percentages move on a coarse lattice "
    "and intervals such as [+0.0, +40.0] are lattice effects. Read them as 'a few events per run'.",
    f"`b45_step` changes sign between lengths: {e(ed['L300']['lr400_16_1']['b45_step'])} at 300 m and {e(ed['L600']['lr400_16_1']['b45_step'])} at 600 m against lr400_16_1 "
    f"(grid_lr400_13_1: {e(ed['L300']['grid_lr400_13_1']['b45_step'])}, {e(ed['L600']['grid_lr400_13_1']['b45_step'])}); distinct encounters too "
    f"({e(ed['L300']['lr400_16_1']['vv_enc'])} → {e(ed['L600']['lr400_16_1']['vv_enc'])}). Printed, never deciding.",
    "The V2 missed share is slightly negative for every arm (median −0.003 % to −0.205 %; pooled −0.01 % to −0.18 %): the 1-Hz count × 1 s is a little larger than the 0.1-s time, "
    "so the 1-Hz count misses no close-following time in aggregate. Per run the share spreads about ±1.5 %. I have not established why the bias is negative.",
    "`c15_cap_share_600` = 0.0 is a real zero, not an empty denominator: 0 of about 32 M decisions per learner. grid_lr400_13_1 (1,566) and p333 (2,991) do hit the cap; "
    "those arms also carry the observation counters (the smoke shows the same). What column 15 encodes was not traced here.",
    "No control at 600 m, seed 7,492,030, has `ttc_net` = 0 (its 300-m run: 717). The seed is light for every arm (600 m: 7-87 samples; delay below the medians) "
    "and the row looks complete (2,149 passed, 644 merges, 0 collisions, 0 teleports). One run; not investigated further.",
    "No control keeps most of its close-following and standing at 600 m (`ttc_net` median 1,340 → 673.5; standing medians 110 and 412 veh-s), while every controlled arm's `ttc_net` median "
    "falls by 91-94 % and its standing medians by 92-97 %. Hence the large edges against no control at 600 m (+72.7 %) and VV-D12's 'removed' = False at both merges (no control's lower bounds 36 % and 15 %).",
    "Lane-end standing at 600 m is heavy-tailed (e.g. lr400_16_1 merge 2: median 23, mean 289 veh-s; 18-36 % of controlled runs have no standing vehicle). "
    "v3w's VV-D12 row uses the per-seed mean of the learners, whose median exceeds every single learner's median (§7), so its cut (84-85 %) is not "
    "comparable with the rules' single-arm cuts (95-97 %). Per learner the cuts are 92.6-97.1 % (post hoc).",
    "Collisions: 0 in all 2,400 learner runs at each length; rules and p333 0-2 per 480 runs; no control 0 at 300 m and 1 at 600 m. Teleports 0 in all 8,640 runs. "
    "Stuck vehicles (post hoc): at most 6 per 480 runs (lr400_16_1 at 300 m).",
    "Jams were not recomputed. At 600 m the rules' jam edges are +0.0 [+0.0, +0.0] [v3]; whether that is a zero median (as in the † cells) cannot be told from v3.json.",
    "No close-following sample was ever counted on edges 4 or 5 in the 8,640 runs (road keys in `m_road_ttc3`).",
    "The V1 visual check (40 samples, rng 20261115) is drawn but not plotted or judged; V1 stays 'CHECKS PASS; visual check pending' [status]."]
for x in notes:
    L.append("- " + x)
L.append("")
(OUT / "printed_tables.md").write_text("\n".join(L) + "\n")
print("written", len(L), "lines")
