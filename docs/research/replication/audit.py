"""Evidence for the thesis section on open implementations (sec:open-impl).

Reads three cloned repositories at pinned commits, as text only: nothing from them is imported, run or unpickled.
Any fact that no longer holds exits 1 and writes nothing, so the thesis cannot quote a stale number.

usage: python3 -I audit.py [--repos DIR]
writes: audit_facts.json beside this file, docs/thesis/tables/open_impl_numbers.tex
"""
import argparse
import csv
import io
import json
import math
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]

ACMPC = "adaptive-compliance-mpc-rl-motorway-traffic"
VSL2 = "vsl2"
DWL = "Multi_Agent_Based_Spatio_Temporal_Variable_Speed_Limit"
PIN = {
    ACMPC: "6cca815928acaf36add3bf92abf42319a4709ac3",
    VSL2: "4819675b6acf90097b64f1ea91f53ead146e0df7",
    DWL: "c040edcadbc03cce1735e9993966bcedd06af506",
}
FINAL_POOL = "scenarios/_pools/s1_motorway_medium+s2_motorway_medium+s4_motorway_medium/rl-proper-final-mixed-pool/coordinated/"
ROBUST = "sac_vsl/evaluate/eval_results_robust/"

# (id, repo, path, regex): the regex must match a line of the file.
PRESENT = [
    ("a_ratio", ACMPC, "macroscopic/vsl.py", r'engine\.min\(\(self\.actions\["v_ctrl"\] / self\.V\) \* \(1\+self\.alpha\), 1\.0\)'),
    ("a_vstar", ACMPC, "macroscopic/vsl.py", r"v_star = engine\.min\(ratio \* self\.V, self\.v_free\)"),
    ("a_rhostar", ACMPC, "macroscopic/vsl.py", r"rho_star = self\.rho_crit \* \(1 \+ self\.A \* \(1 - ratio\)\)"),
    ("a_astar", ACMPC, "macroscopic/vsl.py", r"a_star = self\.a \* \(self\.E - \(self\.E - 1\) \* ratio\)"),
    ("a_objective", ACMPC, "macroscopic/solvers/coordinated.py", r"self\.environment\.parameters\.T \* tts_term"),
    ("a_q_update", ACMPC, "microscopic/agents/qlearning.py", r"target_q = total_reward \+ self\.gamma \* max_next_q"),
    ("a_reward_scope", ACMPC, "microscopic/agents/reward_components.py", r"system \(mainline \+ ramp queues\)"),
    ("a_collision_clip", ACMPC, "microscopic/agents/reward_components.py", r"collisions = min\(collisions, self\.clip\)"),
    ("a_seed_default", ACMPC, "microscopic/simulation/base.py", r"seed: int = 42"),
    ("a_seed_passed", ACMPC, "microscopic/simulation/base.py", r'"--seed", str\(self\.seed\)'),
    ("a_ignored_net", ACMPC, ".gitignore", r"^micronet/$"),
    ("a_ignored_data", ACMPC, ".gitignore", r"^data/$"),
    ("a_report_reads_data", ACMPC, "report/report_config.json", r'"rl_path": "data/s1_medium'),
    ("a_readme_no_tests", ACMPC, "README.md", r"\*\*No tests\*\*"),
    ("a_readme_unseeded", ACMPC, "README.md", r"\*\*Unseeded RL\*\*"),
    ("a_final_cfg_tts_trend", ACMPC, FINAL_POOL + "rl_descriptor.json", r'"source": "tts_trend"'),
    ("v_bias_range", VSL2, "sac_vsl/env.py", r"self\.curr_speed_bias = bias_act \* 3\.0"),
    ("v_sign_edge", VSL2, "sac_vsl/env.py", r'self\._vsl_edges = \["i80_upstream_n"\]'),
    ("v_cav_cmd", VSL2, "sac_vsl/env.py", r"self\.sumo\.vehicle\.setSpeed\(veh, target_v\)"),
    ("v_sign_cmd", VSL2, "sac_vsl/env.py", r"self\.sumo\.lane\.setMaxSpeed\(lane\.getID\(\), vsl_ms\)"),
    ("v_worker_reward", VSL2, "sac_vsl/env.py", r"worker_reward = -normalized_speed_variance"),
    ("v_manager_reward_entry", VSL2, "sac_vsl/env.py", r'self\._tt_entry_edge = "i80_upstream_n"'),
    ("v_eval_tt", VSL2, "sac_vsl/evaluate/evaluate_logger.py", r"getLastIntervalMeanTravelTime\('weaving_e3'\)"),
    ("v_e3_entry", VSL2, "sac_vsl/assets/I80/i80.add.xml", r'detEntry lane="i80_weaving_n_0" pos="0\.0"'),
    ("v_e3_exit", VSL2, "sac_vsl/assets/I80/i80.add.xml", r'detExit lane="i80_weaving_n_0" pos="200\.0"'),
    ("v_test_seeds", VSL2, "sac_vsl/evaluate/plot_figure_5_final.py", r"TEST_SEEDS = \[101, 102, 103\]"),
    ("v_latest_ckpt", VSL2, "sac_vsl/evaluate/evaluate_all.py", r"latest_exp = max\(candidates, key=os\.path\.getmtime\)"),
    ("d_seed", DWL, "DWL_ST_VSL_2Agents.py", r'"--seed", str\(28815\)'),
    ("d_learning_runs", DWL, "DWL_ST_VSL_2Agents.py", r"^end_learning=14000"),
    ("d_exploit_runs", DWL, "DWL_ST_VSL_2Agents.py", r"^exploit=100"),
    ("d_run_seconds", DWL, "DWL_ST_VSL_2Agents.py", r"while\(step <= 5400\)"),
    ("d_control_period", DWL, "DWL_ST_VSL_2Agents.py", r"control_time_perid = 150"),
    ("d_cooperation", DWL, "DWL_ST_VSL_2Agents.py", r"C = 0\.75"),
    ("d_epsilon", DWL, "DWL_ST_VSL_2Agents.py", r"epsilon=math\.exp\(\(\(\(-1\)\*math\.log\(20\)\)/6000\)\*run\)"),
    ("d_rate_limit", DWL, "DWL_ST_VSL_2Agents.py", r"abs\(actions_A\[:\] - actions_A\[previous_action_index\]\)<=20"),
    ("d_actions", DWL, "DWL_ST_VSL_2Agents.py", r"np\.array\(\[60, 60, 80, 80, 100, 100, 120, 120\]\)"),
    ("d_positions", DWL, "DWL_ST_VSL_2Agents.py", r"position = np\.array\(\[1,3,1,3,1,3,1,3\]\)"),
    ("d_states", DWL, "DWL_ST_VSL_2Agents.py", r"reshape\(4608,1\)"),
    ("d_arbitration", DWL, "DWL_ST_VSL_2Agents.py", r"C\*Ws_RP\[0, index_max_W_RP\]"),
    ("d_w_update", DWL, "DWL_ST_VSL_2Agents.py", r"W\[x\] = \(1 - alpha_W\)\*W\[x\] \+ alpha_W\*\(\(1-alpha_Q_ai\)\*\*w\)"),
    ("d_tts_scope", DWL, "DWL_ST_VSL_2Agents.py", r"numberOfVeh = traci\.vehicle\.getIDCount\(\)"),
    ("d_tts_is_total", DWL, "DWL_ST_VSL_2Agents.py", r"numVehTotal = TTS_Total\(\)"),
    ("d_rate_limit_kmh", DWL, "DWL_ST_VSL_2Agents.py", r"A1\.prevActionWin, A1\.actions_kmph\[0,:\], run, numberSaveData"),
    ("d_windows_path", DWL, "DWL_ST_VSL_2Agents.py", r'root="C:/Users/kusic'),
    ("d_exploit_start", DWL, "plot_results.py", r"start_exploit=14000\+1"),
    ("d_exploit_end", DWL, "plot_results.py", r"end_exploit=14100"),
    ("d_select_best", DWL, "plot_results.py", r"indx_best = int\(df_TTS\.loc\[df_TTS\[\['TTS'\]\]\.idxmin\(\)"),
    ("d_novsl_single", DWL, "plot_results.py", r'"NO_VSL_controlFile"\+str\(end_exploit\+1\)'),
    ("d_readme_synthetic", DWL, "README.md", r"SUMO synthetic motorway model"),
    ("d_readme_version", DWL, "README.md", r"results might slightly vary"),
]

# (id, repo, path, regex): the regex must match no line of the file.
ABSENT = [
    ("a_head_lacks_tts_trend", ACMPC, "microscopic/agents/state_features.py", r"tts_trend"),
    ("a_no_random_flag", ACMPC, "micro_main.py", r"--random"),
    ("v_train_unseeded", VSL2, "sac_vsl/scripts/train_sac.py", r"seed"),
    ("v_no_safety_in_env", VSL2, "sac_vsl/env.py", r"(?i)collision|teleport"),
    ("v_no_validation", VSL2, "sac_vsl/scripts/train_sac.py", r"(?i)validat"),
    ("v_sumo_version_unrecorded", VSL2, "run_logs/sac_i80_pr_0.1/system_info.txt", r"(?i)sumo"),
    ("d_python_unseeded", DWL, "DWL_ST_VSL_2Agents.py", r"random\.seed\("),
    ("d_no_proportional", DWL, "DWL_ST_VSL_2Agents.py", r"(?i)proportional|spsc"),
    ("d_no_safety", DWL, "DWL_ST_VSL_2Agents.py", r"(?i)collision|teleport"),
]


def git(repo_dir, *args):
    return subprocess.run(["git", "-C", str(repo_dir), *args], capture_output=True, check=True).stdout.decode("utf-8", "replace")


class Audit:
    def __init__(self, repos):
        self.repos = repos
        self.facts = []
        self.failed = []

    def text(self, repo, path, commit=None):
        return git(self.repos / repo, "show", f"{commit or PIN[repo]}:{path}").removeprefix("\ufeff")

    def tree(self, repo):
        return git(self.repos / repo, "ls-tree", "-r", "--name-only", PIN[repo]).splitlines()

    def record(self, fid, ok, repo, path, detail):
        self.facts.append({"id": fid, "ok": ok, "repo": repo, "commit": PIN[repo], "path": path, "detail": detail})
        if not ok:
            self.failed.append(fid)

    def present(self, fid, repo, path, regex, commit=None):
        for n, line in enumerate(self.text(repo, path, commit).splitlines(), 1):
            if re.search(regex, line):
                self.record(fid, True, repo, path, f"line {n}: {line.strip()[:160]}")
                return
        self.record(fid, False, repo, path, f"no match: {regex}")

    def absent(self, fid, repo, path, regex):
        hits = [n for n, line in enumerate(self.text(repo, path).splitlines(), 1) if re.search(regex, line)]
        self.record(fid, not hits, repo, path, f"no line matches {regex}" if not hits else f"matches at {hits[:5]}")

    def check(self, fid, ok, repo, path, detail):
        self.record(fid, bool(ok), repo, path, detail)


def expected_min_gap(k):
    """c_k with E[min of k iid N(0,1)] = -c_k, by Simpson quadrature."""
    pdf = lambda x: math.exp(-x * x / 2) / math.sqrt(2 * math.pi)
    cdf = lambda x: 0.5 * (1 + math.erf(x / math.sqrt(2)))
    f = lambda x: x * k * pdf(x) * cdf(x) ** (k - 1)
    n, a, b = 20000, -12.0, 12.0
    h = (b - a) / n
    return h / 3 * sum(f(a + i * h) * (1 if i in (0, n) else 4 if i % 2 else 2) for i in range(n + 1))


def table(text):
    return list(csv.DictReader(io.StringIO(text)))


def nums(rows, key):
    return [float(r[key]) for r in rows if r[key] not in ("", "nan")]


def audit_vsl2(a, out):
    stored = {(r["Penetration Rate"], r["Metric"]): r for r in table(a.text(VSL2, ROBUST + "Table2_Final_Stats.csv"))}
    seeds = (101, 102, 103)
    base = {s: table(a.text(VSL2, f"{ROBUST}no_control_pr_0.1_seed_{s}.csv")) for s in seeds}
    sac = {s: table(a.text(VSL2, f"{ROBUST}sac_pr_0.1_seed_{s}.csv")) for s in seeds}
    mean = lambda v: sum(v) / len(v)

    # The stored table keeps every 15th 4-s row, matching the detector's 60-s period.
    every_60s = lambda rows: [r for r in rows if float(r["Time"]) >= 120 and int(r["Step"]) % 15 == 0]
    tt_b = {s: mean(nums(every_60s(base[s]), "TT_s")) for s in seeds}
    tt_s = {s: mean(nums(every_60s(sac[s]), "TT_s")) for s in seeds}
    max_b = {s: max(nums(every_60s(base[s]), "TT_s")) for s in seeds}
    max_s = {s: max(nums(every_60s(sac[s]), "TT_s")) for s in seeds}
    b, c = mean(list(tt_b.values())), mean(list(tt_s.values()))
    gain = (b - c) / b * 100
    row = stored[("10%", "Mean TT")]
    a.check("v_table_mean_tt", abs(b - float(row["No Control"])) < 0.006 and abs(c - float(row["SAC Control"])) < 0.006,
            VSL2, ROBUST, f"recomputed {b:.3f} and {c:.3f}, stored {row['No Control']} and {row['SAC Control']}")
    a.check("v_table_gain", abs(gain - float(row["Improvement (%)"].strip("+%"))) < 0.02, VSL2, ROBUST, f"recomputed {gain:.2f} %")
    row = stored[("10%", "Max TT")]
    mb, ms = max(max_b.values()), max(max_s.values())
    a.check("v_table_max_tt", abs(mb - float(row["No Control"])) < 0.006 and abs(ms - float(row["SAC Control"])) < 0.006,
            VSL2, ROBUST, f"recomputed {mb:.3f} and {ms:.3f}, stored {row['No Control']} and {row['SAC Control']}")

    bias = [abs(float(r["wkr_action"])) * 3 for s in seeds for r in sac[s]]
    changes, jumps, at40 = [], [], []
    for s in seeds:
        v = [float(r["mgr_vsl_kmh"]) for r in sac[s]]
        d = [abs(y - x) for x, y in zip(v, v[1:]) if y != x]
        changes.append(len(d))
        jumps.append(max(d))
        at40.append(sum(x == 40 for x in v) / len(v) * 100)

    out.update({
        "VslSeedA": f"{(tt_b[101] - tt_s[101]) / tt_b[101] * 100:.2f}",
        "VslSeedB": f"{(tt_b[102] - tt_s[102]) / tt_b[102] * 100:.2f}",
        "VslSeedC": f"{(tt_b[103] - tt_s[103]) / tt_b[103] * 100:.2f}",
        "VslMaxSeedA": f"{(max_b[101] - max_s[101]) / max_b[101] * 100:.2f}",
        "VslMaxSeedB": f"{(max_b[102] - max_s[102]) / max_b[102] * 100:.2f}",
        "VslMaxSeedC": f"{(max_b[103] - max_s[103]) / max_b[103] * 100:.2f}",
        "VslGain": f"{gain:.2f}",
        "VslPooledMax": f"{(mb - ms) / mb * 100:.2f}",
        "VslBiasMean": f"{mean(bias):.4f}",
        "VslBiasMax": f"{max(bias):.4f}",
        "VslChangesMin": str(min(changes)),
        "VslChangesMax": str(max(changes)),
        "VslJumpMax": f"{max(jumps):.0f}",
        "VslShareFortyMin": f"{min(at40):.0f}",
        "VslShareFortyMax": f"{max(at40):.0f}",
    })


def audit_acmpc(a, out):
    ranges = []
    for s in (1, 2, 4):
        rows = table(a.text(ACMPC, f"sweeps/alpha_sweep_s{s}.csv"))
        t = [float(r["tts"]) for r in rows]
        ranges.append((max(t) - min(t)) / min(t) * 100)
    a.check("a_sweep_ranges", len(ranges) == 3, ACMPC, "sweeps/", f"{[round(r, 2) for r in ranges]}")

    log = json.loads(a.text(ACMPC, FINAL_POOL + "runs_log.json"))
    desc = json.loads(a.text(ACMPC, FINAL_POOL + "rl_descriptor.json"))
    states = 1
    for feature in desc["state"]["features"]:
        states *= len(feature["labels"])
    actions = len(desc["actions"]["alpha_values"])
    a.check("a_final_size", states == 6 and actions == 5, ACMPC, FINAL_POOL, f"{states} states, {actions} actions")
    a.check("a_final_runs", log["runs_completed"] == len(log["runs"]), ACMPC, FINAL_POOL, f"{len(log['runs'])} runs logged")

    cfg = json.loads(a.text(ACMPC, "scenarios/s1_motorway_medium/scenario.json"))
    micro = cfg["micro"]
    decision = micro["solve_interval_steps"] * micro["step_length"]
    a.check("a_decision_period", decision == 240, ACMPC, "scenario.json", f"{decision} s")

    tree = a.tree(ACMPC)
    a.check("a_no_sumo_files", not [p for p in tree if re.search(r"\.sumocfg$|\.net\.xml$|\.rou\.xml$", p)], ACMPC, "(tree)", "no SUMO network files tracked")
    a.check("a_no_rule_controller", not [p for p in tree if p.endswith(".py") and re.search(r"(?i)alinea|mtfc", a.text(ACMPC, p))], ACMPC, "(*.py)", "no ALINEA or MTFC in any Python file")
    a.check("a_no_calibration", not [p for p in tree if p.endswith((".py", ".md")) and re.search(r"(?i)calibrat", a.text(ACMPC, p))], ACMPC, "(*.py, *.md)", "the word calibration appears nowhere")
    pools = {"/".join(p.split("/")[:4]) for p in tree if p.startswith("scenarios/_pools/") and p.count("/") >= 4}
    a.check("a_pool_experiments", len(pools) == 12, ACMPC, "scenarios/_pools/", f"{len(pools)} experiments")
    history = git(a.repos / ACMPC, "log", "--all", "--name-only", "--format=")
    a.check("a_network_never_committed", not re.search(r"micronet/|\.sumocfg", history), ACMPC, "(history)", "no network file in any commit")
    a.present("a_parent_has_tts_trend", ACMPC, "microscopic/agents/state_features.py", r"tts_trend", commit="a3f09e7^")

    block = a.text(ACMPC, "micro_main.py")
    m = re.search(r"SimulationConfig\.from_scenario\((.*?)\n\s*\)", block, re.S)
    a.check("a_seed_not_set", m and "seed" not in m.group(1), ACMPC, "micro_main.py", "from_scenario call passes no seed")
    cfgs = [p for p in tree if p.endswith("scenario.json")]
    a.check("a_scenarios_have_no_seed", cfgs and not [p for p in cfgs if '"seed"' in a.text(ACMPC, p)], ACMPC, "scenarios/*/scenario.json", f"{len(cfgs)} files, none sets a seed")

    out.update({
        "AcSweepMin": f"{min(ranges):.1f}",
        "AcSweepMax": f"{max(ranges):.1f}",
        "AcRuns": str(len(log["runs"])),
        "AcPools": str(len(pools)),
    })


def audit_dwl(a, out):
    tree = a.tree(DWL)
    results = [p for p in tree if p.startswith("Results/")]
    a.check("d_results_empty", results == ["Results/res_info"], DWL, "Results/", f"{results}")
    a.check("d_inputs_present", all(any(p.endswith(e) for p in tree) for e in (".sumocfg", ".net.xml", ".rou.xml")), DWL, "model_MD/", "net, routes and config tracked")
    routes = a.text(DWL, "model_MD/od_route_file.odtrips.rou.xml")
    vehicles = len(re.findall(r"<vehicle ", routes))
    a.check("d_vehicle_count", vehicles == 5860, DWL, "model_MD/od_route_file.odtrips.rou.xml", f"{vehicles} vehicles")
    runs = 14100 - (14000 + 1)
    out.update({"DwlExploitRuns": str(runs), "DwlVehicles": f"{vehicles:,}".replace(",", "{,}")})
    return runs


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--repos", type=Path, default=ROOT.parent / "other_projects")
    a = Audit(p.parse_args().repos)
    out = {}
    for fid, repo, path, regex in PRESENT:
        a.present(fid, repo, path, regex)
    for fid, repo, path, regex in ABSENT:
        a.absent(fid, repo, path, regex)
    audit_vsl2(a, out)
    audit_acmpc(a, out)
    runs = audit_dwl(a, out)
    out["SelectionGap"] = f"{expected_min_gap(runs):.2f}"
    out["FloorThree"] = f"{2 ** (1 - 3):.2f}"
    out["FactCount"] = str(len(a.facts))

    if a.failed:
        print("FAILED:", ", ".join(a.failed))
        for f in a.facts:
            if not f["ok"]:
                print(f"  {f['id']}: {f['path']}: {f['detail']}")
        return 1

    (HERE / "audit_facts.json").write_text(json.dumps({"pins": PIN, "numbers": out, "facts": a.facts}, indent=1, ensure_ascii=False) + "\n")
    tex = ROOT / "docs/thesis/tables/open_impl_numbers.tex"
    tex.parent.mkdir(exist_ok=True)
    lines = ["% Generated by docs/research/replication/audit.py; do not edit."]
    lines += [f"\\newcommand{{\\OI{k}}}{{{v}}}" for k, v in sorted(out.items())]
    tex.write_text("\n".join(lines) + "\n")
    print(f"{len(a.facts)} facts hold")
    for k, v in sorted(out.items()):
        print(f"{k} = {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
