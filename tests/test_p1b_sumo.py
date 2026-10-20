"""P1b in SUMO, smoke seed 7,400,000 only (at most 8 processes): the pre-data runner check (B2, R4) and P1b episodes
(amber present, PI-plan switch, the same runners in every arm, valid and teleport-free)."""
import json
import subprocess

import pytest

from v5b.d1.config import PYTHON_BIN, REPO_ROOT, clean_sumo_env
from v5b.p1b.episode import make_spec

SEED, Q, MAX_PROCS = 7_400_000, 2000.0, 8


def _py(code: str) -> str:
    r = subprocess.run([PYTHON_BIN, "-c", code], cwd=REPO_ROOT, env=clean_sumo_env(), capture_output=True, text=True,
                       timeout=600)
    assert r.returncode == 0, r.stderr[-2000:]
    return r.stdout.strip().splitlines()[-1]


@pytest.mark.parametrize("mode", ["tick", "step"])
def test_runner_crosses_within_1p5s_of_red_onset_normal_driver_stops(mode):
    r = json.loads(_py(f"import json; from v5b.p1b.runners import signal_scenario; "
                       f"print(json.dumps(signal_scenario('{mode}')))"))
    c, t_red = r["cross_step_start"], r["t_red"]
    # the crossing happens during the 0.5-s step starting at c: within [t_red, t_red + 1.5]
    assert c["run35"] is not None and t_red <= c["run35"] and c["run35"] + 0.5 <= t_red + 1.5
    assert c["norm35"] is None and r["final"]["norm35"] == ["2", 0.0]       # the normal driver stops
    # red age counts from the actual r onset although the state is set every tick: a runner reaching the line
    # about 7 s into red stops (a reset at every set would make it run)
    assert c["run100"] is None and r["final"]["run100"] == ["2", 0.0]
    assert c["norm100"] is None


SPECS = {
    "c": make_spec("c1600", None, False, "block", Q, SEED),
    "c_rs": make_spec("c1600", None, False, "block", Q, SEED, rs=0.3),
    "pi_rs": make_spec("c1600", "p40_20_8_e4", True, "block", Q, SEED, rs=0.3),
    "pi": make_spec("c1600", "p40_20_8_e4", True, "block", Q, SEED),
    "pi_rep": make_spec("c1600", "p40_20_8_e4", True, "block", Q, SEED, rep=1),
    "ad": make_spec("ad1_f20_8", None, False, "slow", Q, SEED),
    "nc": make_spec("NC", None, False, "block", Q, SEED),
}


@pytest.fixture(scope="module")
def runs(tmp_path_factory):
    d = tmp_path_factory.mktemp("p1bsumo")
    todo, running = list(SPECS.items()), []
    while todo or running:
        while todo and len(running) < MAX_PROCS:
            name, s = todo.pop(0)
            running.append(subprocess.Popen([PYTHON_BIN, "-m", "v5b.p1b.episode", "--spec", json.dumps(s), "--out",
                                             str(d / f"{name}.json"), "--run-dir", str(d / name)], cwd=REPO_ROOT,
                                            env=clean_sumo_env(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
        assert running.pop(0).wait(timeout=600) == 0
    return {n: json.loads((d / f"{n}.json").read_text()) for n in SPECS}


def test_valid_teleport_free_amber_present(runs):
    for n, r in runs.items():
        assert r["valid"] and r["teleports"] == 0 and r["collisions"] == 0, n
        assert r["signal"] == "amber" and r["avail_m"] == pytest.approx(410.0)
    for n in ("c", "pi", "ad"):
        assert runs[n]["crossings"]["y"] > 0 and runs[n]["crossings"]["G"] > 0
        assert runs[n]["commanded_mean_vph"] is not None and runs[n]["approach_red_mps"]["n"] > 0
    assert runs["nc"]["crossings"]["y"] == runs["nc"]["crossings"]["r"] == 0
    assert runs["c"]["n_runners"] == 0 and runs["c"]["max_queue_m"] > 0


def test_same_runners_in_every_arm_and_leakage(runs):
    assert runs["c_rs"]["n_runners"] > 0
    assert runs["c_rs"]["runner_hash"] == runs["pi_rs"]["runner_hash"]
    assert runs["c_rs"]["generated"] == runs["c"]["generated"]
    assert runs["c_rs"]["red_cross_share"] > runs["c"]["red_cross_share"]


def test_pi_plan_switch_and_determinism(runs):
    r = runs["pi"]
    assert r["t_switch"] == r["t_on"] and r["t_back"] == r["t_off"] and r["q_at_switch"] == 1600.0
    assert all(q <= 2618.0 for _, _, q in r["meter_log"])
    assert r["hash"] == runs["pi_rep"]["hash"] and r["meter_log"] == runs["pi_rep"]["meter_log"]
