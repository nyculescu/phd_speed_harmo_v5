"""Plan B's ASCH and MPC-F (planb.md §3.4-§3.5): the controllers on planted states, the tuning and fitting jobs on a fake plant."""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "docs/research/planb"))
import asch  # noqa: E402
import mpcf  # noqa: E402
import pb  # noqa: E402
from v5b.fleet import planb_ctrl as pc  # noqa: E402


class Const:
    def __init__(self, lv):
        self.lv, self.calls = lv, 0

    def __call__(self, o):
        self.calls += 1
        return {"v": self.lv}


def test_zone_speeds():
    bins = {("1", 0): 20.0, ("2", 1): 10.0, ("3", 2): 5.0, ("r", 0): 1.0}
    assert pc.zone_speeds(bins) == [15.0, 5.0, None]


def test_asch_switches_after_tau_and_back_with_hysteresis():
    env = SimpleNamespace(sim=SimpleNamespace(t=300.0), bins={})
    a, b = Const(3), Const(1)
    s = pc.Asch(env, a, b, theta_kmh=55, tau_s=10, h_kmh=15)
    seq = []
    for t in range(300, 400, 5):
        env.sim.t = float(t)
        slow = 320 <= t < 350
        mid = 350 <= t < 370     # 60 km/h: above theta, below theta + h
        env.bins = {("4", 0): (40.0 if slow else 60.0 if mid else 90.0) / 3.6}
        seq.append(s((None,))["v"])
    # slow from 320: switch at 330 (10 s held); back needs >= 70 km/h held 10 s: from 370, switch at 380
    assert seq == [3] * 6 + [1] * 10 + [3] * 4
    assert s.log == [(330, 1), (380, 0)]
    assert a.calls == b.calls == 20     # both rules called at every decision


class FakeEdge:
    def getLastStepVehicleNumber(self, e):
        return 2

    def getLastStepVehicleIDs(self, e):
        return ["q"] if e in ("r", "r2") else []


class FakeLs:
    edge = FakeEdge()

    class lane:
        @staticmethod
        def getLastStepVehicleNumber(x):
            return 1

    class vehicle:
        @staticmethod
        def getSpeed(v):
            return 0.5


def fake_env(t_end=1800.0):
    return SimpleNamespace(sim=SimpleNamespace(t=300.0), bins={("1", 0): 25.0}, warm=300.0, t_end=t_end,
                           ep={"N": 0.0, "dist_s": 0.0, "E30": 0.0, "out_E30": 0.0})


def test_features_and_cost():
    env = fake_env()
    x = pc.features(env, FakeLs)
    assert x.tolist() == pytest.approx([25.0, pc.REF_SPEED, pc.REF_SPEED, 4, 4, 6, 1, 1, 1, 1])
    env.ep = {"N": 1000.0, "dist_s": 2777.78, "E30": 3.0, "out_E30": 2.0}
    assert pc.cost_now(env) == pytest.approx(1000.0 - 100.0 + 50.0, rel=1e-6)


def test_mpcf_data_mode_logs_full_holds(monkeypatch):
    env = fake_env()
    monkeypatch.setattr(pc, "build_rule", lambda e, c, f: Const(c["lv"]))
    m = pc.MpcF.__new__(pc.MpcF)
    pc.MpcF.__init__(m, env, {"actions": [{"lv": 0}, {"lv": 3}], "data": 123}, True)
    m.ls = FakeLs
    start = m.next_hold
    for t in np.arange(300.0, 1800.0, 5.0):
        env.sim.t = float(t)
        env.ep["N"] = float(t)     # cost grows by 1 per second
        m((None,))
    assert 300.0 <= start < 600.0
    holds = [x for x in m.log if isinstance(x, dict)]
    assert all(h["y"] == pytest.approx(300.0) for h in holds)
    assert [h["t"] for h in holds] == [start + 300.0 * k for k in range(len(holds))]
    assert holds[-1]["t"] + 300.0 <= 1795.0 and len(holds) == int((1795.0 - start) // 300.0)


def test_mpcf_control_mode_picks_the_cheapest(tmp_path, monkeypatch):
    import torch
    monkeypatch.setattr(pc, "build_rule", lambda e, c, f: Const(c["lv"]))
    net = pc.Net(pc.N_FEAT + 2).m
    with torch.no_grad():
        for p in net.parameters():
            p.zero_()
        net[4].weight[0, 0] = 0.0
        net[0].weight[0, pc.N_FEAT + 1] = 5.0     # action 1 raises hidden unit 0 ...
        net[2].weight[0, 0] = 1.0
        net[4].weight[0, 0] = 1.0     # ... and the predicted cost: action 0 is cheaper
    f = tmp_path / "m.pt"
    torch.save({"state": net.state_dict(), "mu": np.zeros(pc.N_FEAT + 2), "sd": np.ones(pc.N_FEAT + 2), "n_act": 2}, f)
    env = fake_env()
    m = pc.MpcF.__new__(pc.MpcF)
    pc.MpcF.__init__(m, env, {"actions": [{"lv": 0}, {"lv": 3}], "model": str(f)}, True)
    m.ls = FakeLs
    assert m((None,))["v"] == 0 and m.log == [(300, 0)]
    env.sim.t = 315.0
    m((None,))
    assert m.t_pick == 300.0     # re-picks only every 30 s


def fake_runner(jobs, workers):
    """Delay falls with ASCH's theta and with level; MPC-F data carry samples whose cost is 100 x action + x[0]."""
    for name, cfg, q, seed, rd in jobs:
        ctrl = cfg["ctrl"]
        d, cf = 1000.0, 100.0
        log = None
        if "asch" in ctrl:
            d -= ctrl["asch"]["theta_kmh"] / 10.0
            cf -= 1.0
        elif "mpcf" in ctrl:
            if "data" in ctrl["mpcf"]:
                r = np.random.default_rng(ctrl["mpcf"]["data"])
                log = []
                for k in range(4):
                    x = r.uniform(0, 30, 10).round(3).tolist()
                    a = int(r.integers(0, 2))
                    log.append({"x": x, "a": a, "y": 100.0 * a + x[0], "t": 400 + 300 * k})
            else:
                d -= 50.0
        elif "cav_rule" not in ctrl:
            d -= ctrl.get("lv", 0)
        m = {"q": q, "seed": seed, "all_delay": d + seed % 3, "delay_s": d, "ttc_net": cf, "collisions": 0.0, "passed": 3000.0,
             "alks_full_moving": 0.0, "finished_pct": 99.0}
        if log is not None:
            m["ctrl_log"] = log
        yield (name, q, seed), m


def test_asch_tune_picks_admissible_best(tmp_path, monkeypatch):
    monkeypatch.setattr(pb, "rule_cfg", lambda ctrl, cond: {"ctrl": ctrl, "cond": cond})
    res = asch.tune(tmp_path, {"lv": 1}, {"T3E": {"lv": 2}, "C_SURGE": {"lv": 3}}, ["S", "SURGE"], 1, runner=fake_runner)
    assert res["n_configs"] == 1 + 3 * 3 * 2 * 2
    assert res["pick"]["name"].startswith("t70_")
    assert len(res["stage2"]) == asch.TOP
    runs = pb.cma2.load(tmp_path / "tune_runs.jsonl")
    assert len(runs) == (res["n_configs"] + 1) * 2 * 20
    assert {r["seed"] for r in runs} == set(asch.TUNE)
    assert {r["seed"] for r in pb.cma2.load(tmp_path / "check_runs.jsonl")} == set(asch.CHECK)


def test_mpcf_all_steps(tmp_path, monkeypatch):
    monkeypatch.setattr(pb, "rule_cfg", lambda ctrl, cond: {"ctrl": ctrl, "cond": cond})
    res = mpcf.all_steps(tmp_path, [{"lv": 0}, {"lv": 5}], ["S", "TRUCK"], 1, runner=fake_runner)
    assert res["n_samples"] == 2 * mpcf.SCHEDULES * 40 * 4
    assert res["best_fixed"] == "a1"
    assert len(res["split"]["test"]) == 8 and len(res["split"]["stop"]) == 4 and len(res["split"]["train"]) == 28
    assert res["fit_full"]["test_r2"] > 0.9     # the cost is a simple function of the inputs
    assert res["gate_passed"]     # the fake MPC-F has 50 less delay than any fixed action
    n = len(pb.cma2.load(tmp_path / "data_runs.jsonl")) + len(pb.cma2.load(tmp_path / "fixed_runs.jsonl")) + len(pb.cma2.load(tmp_path / "gate_runs.jsonl"))
    assert n == 2 * 4 * 40 + 2 * 2 * 40 + 2 * 3 * 30


@pytest.mark.skipif(not pb.JOB.exists(), reason="round 2's job file is not on this machine")
def test_stored_arms_rewrap_like_rule_cfg():
    arms = pb.stored_arms()
    assert len(arms) == 5 + 15 + 1
    for n in ("p333", "lr400_13_2", "os1_15_10", "copy"):
        for cond in ("S", "SURGE", "TRUCK", "X1"):
            assert pb.with_cond(arms[n], cond) == pb.rule_cfg(pb.ref_ctrl(n), cond), (n, cond)
    assert pb.with_cond(arms["nc"], "S") == pb.rule_cfg({}, "S")
    assert pb.with_cond(arms["nc"], "TRUCK") == pb.rule_cfg({}, "TRUCK")
    x1 = pb.with_cond(arms["w0u250"], "X1")
    assert x1 == {k: v for k, v in arms["w0u250"].items() if k != "measure"}     # X1 back to X1 is the stored config
    s = pb.with_cond(arms["w0u250"], "S")
    assert "perturb" not in s["ctrl"].get("env", {}) and s["ctrl"]["pt"] == arms["w0u250"]["ctrl"]["pt"]
