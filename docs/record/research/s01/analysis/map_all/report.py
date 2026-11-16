"""tables.md from results.json (no computation beyond formatting and counting)."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
D = json.load(open(HERE / "results.json"))
C = D["cells"]
ORDER = ["nc", "p333", "os1_15_10", "os0_10_10", "os1_10_0", "3e", "3ex1", "3ex2", "copy", "lr1000_10_1", "lr1000_16_2",
         "lr400_13_2", "lr400_16_1", "a4400_10_1", "r4a1", "z33133"]
LABEL = {"3e": "3E-T", "3ex1": "3E-X1", "3ex2": "3E-X2", "nc": "no control"}
MET = [("all_delay", "delay"), ("ttc_net", "close-following"), ("passed", "flow"), ("b3_step", "b3"), ("b45_step", "b45")]
CELLS_T = ["X1|5300", "X2|5300"]
BAND = ["B|4500", "B|5000", "B|5250", "B|5500", "B|6000"]
S1 = ["B|3500", "B|7000"]
DESC = {
    "nc": "no control: every vehicle keeps its default behaviour, no headway commands",
    "p333": "fixed 0.8 s headway level for every ALKS in all three zones (cav_rule [3, 3, 3])",
    "os1_15_10": "own-state rule: 0.8 s, or 1.2 s when past 500 m, own speed below 15 m/s and at least 10 vehicles on the accelerating lane",
    "os0_10_10": "own-state rule: 0.8 s, or 1.6 s when past 500 m, own speed below 10 m/s and at least 10 vehicles on the accelerating lane",
    "os1_10_0": "own-state rule: 0.8 s, or 1.2 s when past 500 m and own speed below 10 m/s (no crowd condition)",
    "3e": "3E-T: per-zone own-state rule (5 zones, each with speed and crowd thresholds, active and free levels), CMA-ES-tuned under the training slowdowns at 4,500-6,000 veh/h (g032i20)",
    "3ex1": "3E-X1: the same per-zone family, CMA-ES-tuned for cell X1 on separate seeds (pick g003i02, search not converged; outside the delay filter)",
    "3ex2": "3E-X2: the same per-zone family, CMA-ES-tuned for cell X2 on separate seeds (pick g016i21, search not converged)",
    "copy": "copy rule: a fixed level per road, traced from baseline-v3's policies (confirmatory 3)",
    "lr1000_10_1": "local rule: 0.8 s unless the roadside mean speed in the next 1,000 m is below 10 m/s, then 1.2 s",
    "lr1000_16_2": "local rule: 0.8 s unless the roadside mean speed in the next 1,000 m is below 16 m/s, then 1.0 s",
    "lr400_13_2": "local rule: 0.8 s unless the roadside mean speed in the next 400 m is below 13 m/s, then 1.0 s",
    "lr400_16_1": "local rule: 0.8 s unless the roadside mean speed in the next 400 m is below 16 m/s, then 1.2 s",
    "a4400_10_1": "adaptive on 4a: local rule (400 m, 10 m/s, 1.2 s) plus a fixed 1.2 s on road 4a (the second merge)",
    "r4a1": "road levels: 1.2 s on road 4a, 0.8 s elsewhere",
    "z33133": "zone pattern: fixed level per zone (up, merge 1, between, merge 2, down) = 0.8, 0.8, 1.2, 0.8, 0.8 s",
}
ARMDESC = {
    "v3w": "incumbent per-CAV PPO headway policy, 5 learners at their chosen checkpoints (w0u250, w1u500, w2u250, w3u500, w4u500)",
    "tail": "per learner, the argmax of the mean action probabilities of v3w's u250-u500 checkpoints (t0-t4)",
    "sw": "hybrid: 0.8 s upstream of 500 m, os1_15_10 to 594.72 m, v3w's greedy level after (s0u500-s4u500)",
}


def lab(r):
    return LABEL.get(r, r)


def sgn(x):
    s = f"{abs(x):.1f}"
    if s == "0.0":
        return "0.0"
    return ("+" if x > 0 else "−") + s


def fe(c):
    return f"{sgn(c['pt'])} [{sgn(c['lo'])}, {sgn(c['hi'])}] {c['cls']}"


def rules_of(cell):
    return [r for r in ORDER if r in C[cell]["rules"]]


L = []
w = L.append
n_total = sum(len(c["cmp"]) for c in C.values())
w("# Operating map: v3w, tail and sw against every non-learning controller (S0 + S1 rows, report-only)")
w("")
w("Data: /home/catalin/work/phd/v5b1_runs/measure_s01_remote/ (rows_test, rows_band, rows_s1). Descriptive only, no pass/fail, no thesis claim.")
w("")
w(f"Statistic (round 2's `common1.raw`, conf3/common.py): paired seeds; an arm's value per seed is the mean over its 5 learners (`arm_mean`); effect = sign × median(arm − rule) / median(rule) × 100, positive = the arm is better (less delay, close-following or braking; more flow); 95 % percentile bootstrap, 20,000 seed resamples, `default_rng(20261104)`. Comparisons: {n_total} CIs (count below). Unadjusted 95 % CIs: with this many intervals, some exclusions of 0 are expected by chance alone.")
w("")
w("Marks (from the arm's side): A = arm ahead (CI above 0); R = rule ahead (CI below 0); = tie (CI includes 0). Classification uses unrounded CI bounds.")
w("")
w("Metrics: delay = `all_delay` (door-to-door vehicle-seconds, ramp and insertion queues included); close-following = `ttc_net` (vehicle-seconds at TTC < 3 s, = E30 + out_E30, verified on all 5,560 rows); flow = `passed` (vehicles served); b3 = `b3_step` (vehicle-seconds at ≤ −3 m/s², 0.1-s steps); b45 = `b45_step` (vehicle-seconds at ≤ −4.5 m/s²).")
w("")
w("## Controllers")
w("")
w("| Name | What it is |")
w("|---|---|")
for r in ORDER:
    w(f"| {lab(r)} | {DESC[r]} |")
for a, t in ARMDESC.items():
    w(f"| {a} (arm) | {t} |")
w("")
w("Headway levels: 0 = 1.6 s, 1 = 1.2 s, 2 = 1.0 s, 3 = 0.8 s (`HEADWAYS_S`). Cells: X1 = two tapered slowdowns to 25 km/h for 120 s on edge 4 at 600 and 1,200 s; X2 = one tapered slowdown to 30 km/h for 180 s on edge 3 at 700 s; B = the training slowdowns (random).")
w("")
w("## Comparison count")
w("")
w("| Block | Cells/levels | Arms | Opponents | Metrics | CIs |")
w("|---|---|---|---|---|---|")
w(f"| X1, X2 at 5,300 | 2 | 3 (v3w, tail, sw) | 15 (14 rules + no control) | 5 | {sum(len(C[c]['cmp']) for c in CELLS_T)} |")
w(f"| Band B 4,500-6,000 | 5 | 3 | 4 (no control, p333, os1_15_10, 3E-T) | 5 | {sum(len(C[c]['cmp']) for c in BAND)} |")
w(f"| S1 B 3,500 and 7,000 | 2 | 1 (v3w; tail and sw were not run in S1) | 4 | 5 | {sum(len(C[c]['cmp']) for c in S1)} |")
w(f"| Total | | | | | {n_total} |")
w("")

# (1)
w("## (1) X1 and X2 at 5,300 veh/h: each arm against each rule (40 seeds, 7,440,840-879)")
for cell in CELLS_T:
    for a in ("v3w", "tail", "sw"):
        w("")
        w(f"### {cell.split('|')[0]}: {a} against each controller")
        w("")
        w("| Opponent | Delay | Close-following | Flow | b3 | b45 |")
        w("|---|---|---|---|---|---|")
        for r in rules_of(cell):
            w(f"| {lab(r)} | " + " | ".join(fe(C[cell]["cmp"][f"{a}|{r}|{k}"]) for k, _ in MET) + " |")
    w("")
    w(f"### {cell.split('|')[0]}: which rules beat, tie with or lose to each arm, per metric")
    w("")
    w("| Arm | Metric | Rule ahead (R) | Tie (=) | Arm ahead (A) |")
    w("|---|---|---|---|---|")
    for a in ("v3w", "tail", "sw"):
        for k, ml in MET:
            g = {"R": [], "=": [], "A": []}
            for r in rules_of(cell):
                g[C[cell]["cmp"][f"{a}|{r}|{k}"]["cls"]].append(lab(r))
            w(f"| {a} | {ml} | {', '.join(g['R']) or 'none'} | {', '.join(g['=']) or 'none'} | {len(g['A'])} of {len(rules_of(cell))}: {', '.join(g['A']) or 'none'} |")

# (2)
w("")
w("## (2) Band B (4,500-6,000 veh/h, seeds 7,440,880-899) and S1 (3,500 and 7,000 veh/h, seeds 7,440,900-919): each arm against each rule present (20 seeds)")
for cell in BAND + S1:
    q = cell.split("|")[1]
    w("")
    w(f"### B at {int(q):,} veh/h" + (" (S1)" if cell in S1 else ""))
    w("")
    w("| Arm | Opponent | Delay | Close-following | Flow | b3 | b45 |")
    w("|---|---|---|---|---|---|---|")
    for a in C[cell]["arms"]:
        for r in rules_of(cell):
            w(f"| {a} | {lab(r)} | " + " | ".join(fe(C[cell]["cmp"][f"{a}|{r}|{k}"]) for k, _ in MET) + " |")
    if C[cell]["identical"]:
        w("")
        w(f"Note: at this level {', '.join(f'{lab(a)} = {lab(b)}' for a, bs in C[cell]['identical'].items() for b in bs)} on every seed and every stored key (os1_15_10 never fires), so these two rows are the same comparison.")
w("")
w("Note: at 4,500 veh/h p333 and os1_15_10 differ on 3 of 20 seeds only (7,440,884, 7,440,894, 7,440,895), so their medians coincide on most metrics.")

# (3)
w("")
w("## (3) Point positions, strongest rule per metric and the delay/close-following front")
w("")
w("Point positions are each controller's median over the paired seeds (arm = per-seed mean of 5 learners). The front is read from these point estimates only, not from CIs. Front = rules (of those present) that no other rule matches or beats on both delay and close-following. \"inside\" = some rule has lower delay and lower close-following than the arm; \"beyond\" = the arm is not dominated and itself dominates at least one front rule; \"on\" = not dominated and dominating no front rule. The paired check repeats the dominance test with medians of paired differences (rule − arm) instead of per-controller medians.")
for cell in CELLS_T + S1[:1] + BAND + S1[1:]:
    c = C[cell]
    name, q = cell.split("|")
    w("")
    w(f"### {name} at {int(q):,} veh/h ({c['n_seeds']} seeds)")
    w("")
    w("| Controller | Delay (veh·s) | Close-following (veh·s) | Flow (veh) | b3 (veh·s) | b45 (veh·s) | On front (with no control) | On front (rules only) |")
    w("|---|---|---|---|---|---|---|---|")
    fw, fo = c["fronts"]["with_nc"]["front"], c["fronts"]["without_nc"]["front"]
    for r in rules_of(cell) + c["arms"]:
        m = c["meds"][r]
        isarm = r in c["arms"]
        w(f"| {lab(r) + (' (arm)' if isarm else '')} | {m['all_delay']:.0f} | {m['ttc_net']:.1f} | {m['passed']:.1f} | {m['b3_step']:.1f} | {m['b45_step']:.1f} | "
          f"{'n/a' if isarm else ('yes' if r in fw else 'no')} | {'n/a' if isarm or r == 'nc' else ('yes' if r in fo else 'no')} |")
    w("")
    w("| Arm | Front | Arm's position | Dominated by (point medians) | Dominates on the front (point medians) | Dominated by (paired medians) | Dominates on the front (paired medians) |")
    w("|---|---|---|---|---|---|---|")
    for tag, tl in (("with_nc", "with no control"), ("without_nc", "rules only")):
        F = c["fronts"][tag]
        for a in c["arms"]:
            p = F["pos"][a]
            w(f"| {a} | {tl}: {', '.join(lab(r) for r in F['front'])} | {p['status']} | {', '.join(lab(r) for r in p['dominated_by']) or 'none'} | {', '.join(lab(r) for r in p['dominates_front']) or 'none'} | {', '.join(lab(r) for r in p['paired_dominated_by']) or 'none'} | {', '.join(lab(r) for r in p['paired_dominates_front']) or 'none'} |")
    w("")
    w("| Metric | Best rule (incl. no control) | Best rule other than no control |")
    w("|---|---|---|")
    for k, ml in MET:
        b = c["best"][k]
        w(f"| {ml} | {lab(b['best_rule'])} ({c['meds'][b['best_rule']][k]:.1f}) | {lab(b['best_rule_not_nc'])} ({c['meds'][b['best_rule_not_nc']][k]:.1f}) |")

# (4)
w("")
w("## (4) Direct answer: does any non-learning controller beat v3w? (95 % paired CIs, from (1)-(2))")
w("")
w("| Cell/level | Opponents | Rule ahead on delay AND close-following | Rule ahead on delay | Rule ahead on close-following | Tie on delay | Tie on close-following | v3w ahead on delay | v3w ahead on close-following |")
w("|---|---|---|---|---|---|---|---|---|")
for cell in CELLS_T + S1[:1] + BAND + S1[1:]:
    c = C[cell]
    rs = rules_of(cell)
    g = {k: {"R": [], "=": [], "A": []} for k, _ in MET}
    for r in rs:
        for k, _ in MET:
            g[k][c["cmp"][f"v3w|{r}|{k}"]["cls"]].append(lab(r))
    both = [x for x in g["all_delay"]["R"] if x in g["ttc_net"]["R"]]
    name, q = cell.split("|")
    w(f"| {name} {int(q):,} | {len(rs)} | {', '.join(both) or 'none'} | {', '.join(g['all_delay']['R']) or 'none'} | {', '.join(g['ttc_net']['R']) or 'none'} | "
      f"{', '.join(g['all_delay']['=']) or 'none'} | {', '.join(g['ttc_net']['=']) or 'none'} | {len(g['all_delay']['A'])} of {len(rs)} | {len(g['ttc_net']['A'])} of {len(rs)} |")
w("")
w("Same reading for flow and braking (v3w against each rule present; counts of R / = / A):")
w("")
w("| Cell/level | Flow R/=/A | b3 R/=/A | b45 R/=/A | Rules ahead of v3w on flow, b3 or b45 |")
w("|---|---|---|---|---|")
for cell in CELLS_T + S1[:1] + BAND + S1[1:]:
    c = C[cell]
    rs = rules_of(cell)
    cnt, ahead = [], []
    for k, ml in MET[2:]:
        cls = [c["cmp"][f"v3w|{r}|{k}"]["cls"] for r in rs]
        cnt.append(f"{cls.count('R')}/{cls.count('=')}/{cls.count('A')}")
        ahead += [f"{lab(r)} ({ml})" for r in rs if c["cmp"][f"v3w|{r}|{k}"]["cls"] == "R"]
    name, q = cell.split("|")
    w(f"| {name} {int(q):,} | {cnt[0]} | {cnt[1]} | {cnt[2]} | {', '.join(ahead) or 'none'} |")

w("")
w("tail and sw, the same reading (rules ahead of the arm, 95 % CI below 0):")
w("")
w("| Arm | Cell/level | Rule ahead on delay AND close-following | Rule ahead on delay | Rule ahead on close-following | Rules ahead on flow, b3 or b45 |")
w("|---|---|---|---|---|---|")
for a in ("tail", "sw"):
    for cell in CELLS_T + BAND:
        c = C[cell]
        rs = rules_of(cell)
        rd = [lab(r) for r in rs if c["cmp"][f"{a}|{r}|all_delay"]["cls"] == "R"]
        rt = [lab(r) for r in rs if c["cmp"][f"{a}|{r}|ttc_net"]["cls"] == "R"]
        ro = [f"{lab(r)} ({ml})" for k, ml in MET[2:] for r in rs if c["cmp"][f"{a}|{r}|{k}"]["cls"] == "R"]
        name, q = cell.split("|")
        w(f"| {a} | {name} {int(q):,} | {', '.join(x for x in rd if x in rt) or 'none'} | {', '.join(rd) or 'none'} | {', '.join(rt) or 'none'} | {', '.join(ro) or 'none'} |")
w("")
w("Marginal intervals (a CI bound that rounds to 0.0 while the unrounded bound decides the mark; any rounding or resampling change could flip these):")
w("")
w("| Cell/level | Arm | Opponent | Metric | Effect | Unrounded bound |")
w("|---|---|---|---|---|---|")
for cell in CELLS_T + S1[:1] + BAND + S1[1:]:
    for key_, x in C[cell]["cmp"].items():
        a, r, k = key_.split("|")
        b = x["lo"] if x["cls"] == "A" else (x["hi"] if x["cls"] == "R" else None)
        if b is not None and abs(b) < 0.05:
            name, q = cell.split("|")
            w(f"| {name} {int(q):,} | {a} | {lab(r)} | {dict(MET)[k]} | {fe(x)} | {b:.4f} |")
w("")
w("Multiplicity: these are unadjusted 95 % intervals. A wider (adjusted) percentile interval from the same bootstrap contains the 95 % one, so an adjustment can only turn A or R into a tie, never create a new A or R. \"No rule ahead of v3w on delay\" therefore holds under any adjustment; the counts of v3w ahead are upper bounds.")
w("")
w("Low-demand caveat: at 3,500 and 4,500 veh/h close-following medians are 5.5-99 veh·s per run (no control 5.5 and 37), so percentage effects on it are large and unstable (for example −272.7 % against no control at 3,500 is 21.9 against 5.5 veh·s).")

# (5)
w("")
w("## (5) Coverage gap: rules run only in X1/X2 at 5,300 veh/h")
w("")
band_rules = set().union(*[set(C[c]["rules"]) for c in BAND + S1])
xr = set(C["X1|5300"]["rules"]) | set(C["X2|5300"]["rules"])
gap = [r for r in ORDER if r in xr and r not in band_rules]
grid = [r for r in gap if r not in ("3ex1", "3ex2")]
w(f"Present in band and S1: {', '.join(lab(r) for r in ORDER if r in band_rules)}. Absent from band and S1 ({len(gap)}): {', '.join(lab(r) for r in gap)}.")
w("")
w("| Rules | Band levels (5 × 20 seeds) | S1 levels (2 × 20 seeds) | Runs |")
w("|---|---|---|---|")
w(f"| {len(grid)} fixed rules ({', '.join(lab(r) for r in grid)}) | {len(grid) * 5 * 20} | {len(grid) * 2 * 20} | {len(grid) * 7 * 20} |")
w(f"| + 3E-X1 and 3E-X2 (tuned for X1 / X2; running them under B's slowdowns tests them outside their tuning cell) | {2 * 5 * 20} | {2 * 2 * 20} | {2 * 7 * 20} |")
w(f"| All {len(gap)} | {len(gap) * 5 * 20} | {len(gap) * 2 * 20} | {len(gap) * 7 * 20} |")
w("")
w(f"Per level: {len(grid)} × 20 = {len(grid) * 20} runs for the fixed rules, {len(gap)} × 20 = {len(gap) * 20} with the two 3E-X rules. Learning arms also absent from S1: tail and sw (5 learners × 2 levels × 20 seeds = 200 runs each). Every rule, in every cell, was run only at its listed levels; X1 and X2 were run only at 5,300 veh/h. Nothing was run for this analysis.")
(HERE / "tables.md").write_text("\n".join(L) + "\n")
print("lines", len(L))
