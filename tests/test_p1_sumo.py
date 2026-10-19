"""P1 episodes in SUMO on smoke seed 7,400,000 only: D2 equivalence, replicate redraw keeps the incident window,
PI / AD / VSL / false alarm / delayed switches run, are valid and teleport-free."""
import json
import subprocess
from pathlib import Path

import pytest

from v5b.d1.config import PYTHON_BIN, REPO_ROOT, clean_sumo_env
from v5b.d2.incidents import incident_window
from v5b.p1.episode import make_spec
from v5b.p1.meters import fa_schedule, incident_ticks

SEED = 7_400_000
Q = 2000.0
SPECS = {
    "sw": make_spec("c1600", "c800", True, "block", Q, SEED),
    "rep1": make_spec("c1600", "c800", True, "block", Q, SEED, k=1),
    "pi5": make_spec("p40_20_6_e5", None, False, "slow", Q, SEED),
    "ad": make_spec("ad1_f20_8", None, False, "block", Q, SEED),
    "nc": make_spec("NC", None, False, "block", Q, SEED),
    "ncv": make_spec("NC", None, False, "block", Q, SEED, vsl_b=0.4),
    "fa": make_spec("c1600", "c800", False, "none", Q, SEED, fa=True),
    "dc": make_spec("c1600", "c800", True, "block", Q, SEED, d=60.0, c=60.0),
}


@pytest.fixture(scope="module")
def runs(tmp_path_factory):
    d = tmp_path_factory.mktemp("p1sumo")
    procs = {}
    for name, s in SPECS.items():
        procs[name] = subprocess.Popen([PYTHON_BIN, "-m", "v5b.p1.episode", "--spec", json.dumps(s), "--out",
                                        str(d / f"{name}.json"), "--run-dir", str(d / name)], cwd=REPO_ROOT,
                                       env=clean_sumo_env(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    d2spec = {"pre": "c1600", "post": "c800", "incident": "block", "q": Q, "seed": SEED, "back": True}
    procs["d2"] = subprocess.Popen([PYTHON_BIN, "-m", "v5b.d2.episode", "--spec", json.dumps(d2spec), "--out",
                                    str(d / "d2.json"), "--run-dir", str(d / "d2")], cwd=REPO_ROOT,
                                   env=clean_sumo_env(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for p in procs.values():
        assert p.wait(timeout=600) == 0
    return {n: json.loads((d / f"{n}.json").read_text()) for n in procs}


def test_all_valid_no_teleports(runs):
    for n, r in runs.items():
        assert r["valid"] and r["teleports"] == 0, n


def test_d2_spec_reproduces_the_d2_run(runs):
    a, b = runs["sw"], runs["d2"]
    for k in ("hash", "delay_s", "served_ctrl_vph", "ttt_ctrl_vehh", "meter_log", "t_switch", "t_back", "t_on", "t_off"):
        assert a[k] == b[k], k


def test_replicate_redraws_demand_and_sumo_keeps_window(runs):
    a, r = runs["sw"], runs["rep1"]
    assert (r["onset_s"], r["duration_s"], r["t_on"], r["t_off"]) == (a["onset_s"], a["duration_s"], a["t_on"], a["t_off"])
    assert r["sumo_seed"] == r["demand_seed"] == SEED + 10_000_000 and a["demand_seed"] == SEED
    assert r["hash"] != a["hash"] and r["generated"] != a["generated"]


def test_pi_ad_vsl_fa_delayed(runs):
    on, dur = incident_window(SEED, 40.0, 900.0)
    t_on, t_off = incident_ticks(on, dur)
    assert runs["pi5"]["meter_log"] and runs["pi5"]["t_switch"] is None
    ad = runs["ad"]
    assert ad["nhat_log"][0][1] == 8.0 and ad["ad_max_dev"] is not None and ad["ad_max_dev"] >= 0
    assert runs["nc"]["entered_e4_incident"] > 0 and runs["ncv"]["entered_e4_incident"] > 0
    assert runs["ncv"]["vsl_log"][0] == [t_on, 0.8] and runs["ncv"]["vsl_log"][-1][1] == 1.0
    fa = runs["fa"]
    sw, bk = fa_schedule(SEED)
    assert (fa["t_switch"], fa["t_back"]) == (sw, bk) and fa["t_on"] is None
    dc = runs["dc"]
    assert (dc["t_switch"], dc["t_back"]) == (t_on + 60.0, t_off + 60.0)
    assert runs["sw"]["max_queue"] > 0
