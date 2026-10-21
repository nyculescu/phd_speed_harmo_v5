"""P1b confirmation C1 (p1b_confirm_c1.md, V114), pure tests: frozen arms, seeds, statement C1 on synthetic numbers,
the V109 spill indicator, sentinel and run-once. No simulation; no test touches seeds 7,400,700-799 beyond building
run keys."""
import json
import os
import subprocess
from types import SimpleNamespace

import numpy as np
import pytest

from v5b.d1.config import PYTHON_BIN, REPO_ROOT, clean_sumo_env
from v5b.p1 import family as fam
from v5b.p1 import run as p1run
from v5b.p1b import analysis as an
from v5b.p1b import confirm_c1 as cf
from v5b.p1b import run as rs


# ---------------------------------------------------------------- arms
def test_arms_resolve_to_the_frozen_p1b_arms():
    s = 7_400_000
    ip, pi, n, nc = (cf.arm_spec(x, s) for x in cf.ARMS)
    assert (ip["pre"], ip["post"], ip["back"], ip["incident"], ip["q"], ip["d"], ip["c"], ip["rs"], ip["k"]) == \
        ("c1800", "p20_20_16_e4", False, "block", 1600.0, 0.0, 0.0, 0.0, 0)
    assert (pi["pre"], pi["post"], pi["back"]) == ("p70_120_8_e4", None, False)
    assert (n["pre"], n["post"]) == ("c1800", None) and (nc["pre"], nc["post"]) == (fam.NC, None)
    assert all(x["incident"] == "block" and x["q"] == 1600.0 and x["rs"] == 0.0 and x["vsl_b"] is None
               for x in (ip, pi, n, nc))
    chk = cf.frozen_arms_check()
    assert chk["checked"] and chk["match"], chk
    a = json.loads((REPO_ROOT / cf.P1B_RESULT).read_text())["tune"]["arms"]["1600"]
    assert an.sw(a["N"], a["IP"]["block"], "block", 1600.0, s)["key"] == ip["key"]    # P1b's own IP run
    assert an.fixed(a["PI"], "block", 1600.0, s)["key"] == pi["key"]
    assert cf.ip_spec(s, rs_=0.3)["rs"] == 0.3 and cf.ip_spec(s, rs_=0.3)["post"] == "p20_20_16_e4"
    for d in cf.D_ROWS:
        x = cf.ip_spec(s, d=d)
        assert x["key"] in (an.sw("c1800", "c1800", "block", 1600.0, s)["key"],
                            an.sw("c1800", "p20_20_16_e4", "block", 1600.0, s, d=d)["key"])


# ---------------------------------------------------------------- seeds
def test_seeds_are_the_confirmatory_block_700_799_only():
    assert cf.SEEDS == tuple(range(7_400_700, 7_400_800)) and len(cf.SEEDS) == 100
    used = set().union(*(set(v) for v in rs.SEEDS.values()), *(set(v) for v in p1run.SEEDS.values()))
    assert not used & set(cf.SEEDS)
    sp = cf.c1_specs(cf.SEEDS)                                  # run keys only, no simulation
    assert {x["seed"] for x in sp} == set(cf.SEEDS)
    assert all(x["k"] == 0 and x["rep"] is None and not x["fa"] and x["vsl_b"] is None for x in sp)
    assert all(x["incident"] == "block" and x["q"] == 1600.0 for x in sp)
    assert 9 * 100 <= len(sp) <= 11 * 100 and len({x["key"] for x in sp}) == len(sp)
    assert cf.SMOKE_SEEDS == tuple(range(7_400_000, 7_400_004))
    assert all(s in rs.CALIB_ONLY for s in cf.SMOKE_SEEDS)


# ---------------------------------------------------------------- statement C1
def _st(pi, ip, inv=None):
    pi, ip = np.asarray(pi, float), np.asarray(ip, float)
    return cf.statement_c1(pi, ip, np.zeros(pi.size, bool) if inv is None else inv)


def test_statement_pass_and_boundary():
    rng = np.random.default_rng(1)
    pi = 100.0 + rng.normal(0, 3, 100)
    s = _st(pi, pi - 20.0 + rng.normal(0, 1, 100))
    assert s["confirmed"] and s["text"] == "CONFIRMED"
    assert s["all_seeds"]["pass"] and s["valid_only"]["pass"] and s["B"] == 20_000
    assert s["all_seeds"]["level"] == 0.95
    assert _st(np.full(100, 100.0), np.full(100, 90.0))["confirmed"]          # rel = 10 % exactly passes


def test_statement_fails_on_rel():
    rng = np.random.default_rng(2)
    pi = 100.0 + rng.normal(0, 3, 100)
    s = _st(pi, pi - 5.0 + rng.normal(0, 0.5, 100))
    assert s["all_seeds"]["ci_ok"] and not s["all_seeds"]["rel_ok"] and not s["confirmed"]


def test_statement_fails_on_ci():
    pi = np.full(100, 100.0)
    d = np.array([15.0] * 51 + [-20.0] * 49)
    s = _st(pi, pi - d)
    assert s["all_seeds"]["rel"] == pytest.approx(0.15)
    assert s["all_seeds"]["rel_ok"] and not s["all_seeds"]["ci_ok"] and not s["confirmed"]
    assert s["text"] == "NOT CONFIRMED"


def test_statement_must_hold_in_both_views():
    pi = np.full(100, 100.0)
    d = np.array([20.0] * 70 + [0.0] * 30)
    inv = np.zeros(100, bool)
    inv[:50] = True                                   # the big wins come from runs with an invalid IP or PI
    s = _st(pi, pi - d, inv)
    assert s["all_seeds"]["pass"] and not s["valid_only"]["pass"] and not s["confirmed"]
    assert s["n_invalid_seeds"] == 50
    d2 = np.array([0.0] * 50 + [20.0] * 50)           # fails on all seeds, passes on the valid ones
    s2 = _st(pi, pi - d2, inv)
    assert not s2["all_seeds"]["pass"] and s2["valid_only"]["pass"] and not s2["confirmed"]
    s3 = _st(pi, pi - 20.0, np.ones(100, bool))       # no valid seed left: fails closed
    assert s3["all_seeds"]["pass"] and s3["valid_only"] is None and not s3["confirmed"]


def test_bootstrap_seed_fixed_and_deterministic():
    rng = np.random.default_rng(3)
    pi = 100.0 + rng.normal(0, 10, 100)
    ip = pi - 12.0 + rng.normal(0, 10, 100)
    a, b = _st(pi, ip), _st(pi, ip)
    assert a == b and a["boot_seed"] == cf.BOOT_SEED_C1 == 20261020


def test_spill_v109():
    base = {"max_queue_m": 100.0, "avail_m": 410.0, "depart_delay_s": 1.0}
    assert not cf.spill_v109(base)
    assert cf.spill_v109({**base, "max_queue_m": 360.0})                        # tail within 50 m of the entry
    assert not cf.spill_v109({**base, "max_queue_m": 359.9})
    assert cf.spill_v109({**base, "depart_delay_s": 5.01})
    assert not cf.spill_v109({**base, "depart_delay_s": 5.0})
    assert "depart_delay_s" in cf.Pool.KEEP_FIELDS and cf.Pool.MODULE == "v5b.p1b.episode"
    assert rs.Pool.KEEP_FIELDS == rs.KEEP                                       # P1b unchanged


# ---------------------------------------------------------------- sentinel, run-once, launch rules
def test_sentinel_paths_follow_runs_root(tmp_path):
    if "V5B1_RUNS" not in os.environ:
        assert str(cf.SENTINEL) == "/home/catalin/work/phd/v5b1_runs/P1B_C1_STARTED.json"
        assert str(cf.DEFAULT_OUT) == "/home/catalin/work/phd/v5b1_runs/p1b_c1/v114"
    env = {**clean_sumo_env(), "V5B1_RUNS": str(tmp_path / "root")}
    o = subprocess.run([PYTHON_BIN, "-c", "from v5b.p1b import confirm_c1 as c; print(c.SENTINEL, c.DEFAULT_OUT)"],
                       cwd=REPO_ROOT, env=env, capture_output=True, text=True).stdout.split()
    assert o == [str(tmp_path / "root" / "P1B_C1_STARTED.json"), str(tmp_path / "root" / "p1b_c1" / "v114")]


def test_launch_rules():
    a = SimpleNamespace(workers=32, cpu_limit=0.90, smoke=False, confirm_run_once=True)
    cf.check_launch(a, dirty=False)
    for bad, dirty in (({"confirm_run_once": False}, False), ({}, True), ({"workers": 101}, False),
                       ({"cpu_limit": 0.95}, False), ({"smoke": True, "workers": 5}, False)):
        with pytest.raises(SystemExit):
            cf.check_launch(SimpleNamespace(**{**vars(a), **bad}), dirty=dirty)
    cf.check_launch(SimpleNamespace(**{**vars(a), "smoke": True, "workers": 4}), dirty=True)
    with pytest.raises(SystemExit):
        cf.main(["--smoke"])                                                    # smoke needs its own --out


def _fake_run(s: dict) -> dict:
    rng = np.random.default_rng(s["seed"])
    base = 100.0 + rng.normal(0, 5)
    delay = {"p70_120_8_e4": base}.get(s["pre"], base + 10.0)
    if s["post"] == "p20_20_16_e4":
        delay = base - 20.0 + 5.0 * bool(s["d"]) + 3.0 * bool(s["rs"])
    return {"delay_s": delay, "valid": True, "teleports": 0, "collisions": 0, "served_ctrl_vph": 1500.0,
            "ttt_ctrl_vehh": 50.0, "ttt_full_vehh": 60.0, "max_queue": 10.0, "emergency_meter": 0,
            "emergency_stops": 1, "approach_red_mps": {"median": 1.0, "max": 3.0, "n_ge_10": 0},
            "red_cross_share": 0.0, "runner_red_cross_share": None, "commanded_mean_vph": 900.0,
            "discharge_vph": {"G": 1800.0, "y": 600.0, "r": 0.0}, "max_queue_m": 200.0,
            "max_queue_halted_veh": 20.0, "avail_m": 410.0, "depart_delay_s": 2.0}


def _patch(monkeypatch, tmp_path, calls, commit="abc", dirty=""):
    sen = tmp_path / "P1B_C1_STARTED.json"

    class FakePool:
        def __init__(self, out, workers, cpu_limit, log, **kw):
            self.stage_wall, self.n_pauses, self.temp_max = {}, 0, float("nan")

        def run(self, specs, stage):
            calls.append(sen.exists())                 # the sentinel exists before the first C1 run
            return {x["key"]: _fake_run(x) for x in specs}, []

    monkeypatch.setattr(cf, "SENTINEL", sen)
    monkeypatch.setattr(cf, "ALLOWED_ROOTS", (tmp_path,))
    monkeypatch.setattr(cf, "SEEDS", tuple(range(7_400_000, 7_400_010)))      # no confirmatory seed in tests
    monkeypatch.setattr(cf, "Pool", FakePool)
    monkeypatch.setattr(cf, "tree_state", lambda: ("h", "t"))
    monkeypatch.setattr(cf, "make_verify", lambda state0, log: (lambda where: None))
    monkeypatch.setattr(cf.net, "build", lambda: None)
    monkeypatch.setattr(cf.os, "nice", lambda inc: 0)
    monkeypatch.setattr(cf.p1run, "_git", lambda *a: commit if a[0] == "rev-parse" else dirty)
    return sen


def test_run_once_sentinel_and_resume(monkeypatch, tmp_path):
    calls = []
    sen = _patch(monkeypatch, tmp_path, calls)
    out = tmp_path / "c1"
    args = ["--confirm-run-once", "--workers", "2", "--out", str(out)]
    assert cf.main(args) == 0
    assert calls == [True] and json.loads(sen.read_text())["code_commit"] == "abc"
    r = json.loads((out / "result.json").read_text())
    assert r["c1"]["C1"]["confirmed"] and r["decision"] == "CONFIRMED" and r["c1"]["n_seeds"] == 10
    assert (out / "summary.md").read_text().startswith("# P1b confirmation C1 (block_q1600)")
    with pytest.raises(SystemExit):
        cf.main(args)                                                           # result exists: runs once
    (out / "result.json").unlink()                                              # an interrupted run
    with pytest.raises(SystemExit):
        cf.main(args)                                                           # sentinel: no fresh start
    with pytest.raises(SystemExit):
        cf.main(args + ["--out", str(tmp_path / "other"), "--resume"])           # resume only of the same --out
    _patch(monkeypatch, tmp_path, calls, commit="def")
    with pytest.raises(SystemExit):
        cf.main(args + ["--resume"])                                            # resume only at the same commit
    _patch(monkeypatch, tmp_path, calls, commit="abc")
    assert cf.main(args + ["--resume"]) == 0 and len(calls) == 2


def test_dirty_tree_refused_and_smoke_writes_no_sentinel(monkeypatch, tmp_path):
    calls = []
    sen = _patch(monkeypatch, tmp_path, calls, dirty=" M v5b/p1b/confirm_c1.py")
    with pytest.raises(SystemExit):
        cf.main(["--confirm-run-once", "--workers", "2", "--out", str(tmp_path / "c1")])
    assert not sen.exists() and calls == []
    assert cf.main(["--smoke", "--workers", "4", "--out", str(tmp_path / "smoke")]) == 0
    assert calls == [False] and not sen.exists()
    r = json.loads((tmp_path / "smoke" / "result.json").read_text())
    assert r["smoke"] and r["seeds"] == [7_400_000, 7_400_003]
    d = r["c1"]["descriptive"]
    assert set(d) >= {"PI_vs_IP_d30", "PI_vs_IP_d60", "PI_vs_IP_d120", "PI_s0.1_vs_IP_s0.1", "PI_s0.3_vs_IP_s0.3",
                      "N_vs_IP", "NC_vs_PI"}
    assert r["c1"]["rows"]["IP"]["spill_share"] == 0.0 and "spill_share_b4_7m" in r["c1"]["rows"]["IP"]
