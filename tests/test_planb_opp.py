"""Plan B's ASCH and MPC-F (planb.md §3.4-§3.5): the controllers on planted states, the tuning and fitting jobs on a fake plant."""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "analysis/planb"))
import asch  # noqa: E402
import mpcf  # noqa: E402
import pb  # noqa: E402
from v5b2.fleet import planb_ctrl as pc  # noqa: E402


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


def test_asch_reads_every_zone():
    env = SimpleNamespace(sim=SimpleNamespace(t=300.0), bins={})
    s = pc.Asch(env, Const(3), Const(1), theta_kmh=55, tau_s=0, h_kmh=15)
    env.bins = {("1", 0): 90 / 3.6, ("3", 0): 90 / 3.6, ("4", 0): 40 / 3.6}     # one slow zone of three switches
    assert s((None,))["v"] == 1
    env.sim.t = 305.0
    env.bins = {("1", 0): 90 / 3.6, ("3", 0): 60 / 3.6, ("4", 0): 90 / 3.6}     # back only when every zone is at theta + h
    assert s((None,))["v"] == 1
    env.sim.t = 310.0
    env.bins = {("1", 0): 90 / 3.6, ("3", 0): 70 / 3.6, ("4", 0): 90 / 3.6}
    assert s((None,))["v"] == 3


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
    sha = __import__("hashlib").sha256(f.read_bytes()).hexdigest()
    env = fake_env()
    m = pc.MpcF.__new__(pc.MpcF)
    pc.MpcF.__init__(m, env, {"actions": [{"lv": 0}, {"lv": 3}], "model": str(f), "model_sha256": sha}, True)
    m.ls = FakeLs
    assert m((None,))["v"] == 0 and m.log == [(300, 0)] and m.diag == {"model_sha256": sha}
    calls = [r.calls for r in m.rules]
    for t in (315.0, 329.0):
        env.sim.t = t
        m((None,))
    assert m.t_pick == 300.0     # re-picks only every 30 s
    env.sim.t = 330.0
    m((None,))
    assert m.t_pick == 330.0 and [r.calls for r in m.rules] == [c + 3 for c in calls]     # every member called at every decision
    with pytest.raises(ValueError):
        pc.MpcF.__init__(pc.MpcF.__new__(pc.MpcF), env, {"actions": [{"lv": 0}, {"lv": 3}], "model": str(f), "model_sha256": "0" * 64}, True)
    with pytest.raises(ValueError):
        pc.MpcF.__init__(pc.MpcF.__new__(pc.MpcF), env, {"actions": [{"lv": 0}, {"lv": 3}], "model": str(f)}, True)
    from v5b2.fleet import measure as me
    o = (["a"], np.zeros((1, 16), np.float32), None, np.array([True]))
    assert me.policy_probs(m, o) == {}     # the pack's probe never treats MPC-F's model as a policy (review F2)


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
    assert len(res["stage2"]) == 5 and res["steady"] == {"lv": 1} and sorted(res["library"]) == ["C_SURGE", "T3E"]
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
    assert {r["seed"] for r in pb.cma2.load(tmp_path / "fixed_runs.jsonl")} == set(mpcf.FIT)
    gate = pb.cma2.load(tmp_path / "gate_runs.jsonl")
    assert {r["seed"] for r in gate} == set(mpcf.GATE)
    assert {r["name"] for r in gate if "mpcf" in r["name"]} == {f"{c}|mpcf_{res['model_sha256'][:12]}" for c in ("S", "TRUCK")}
    assert set(res["split"]["test"]) | set(res["split"]["stop"]) | set(res["split"]["train"]) == set(mpcf.FIT)
    again = mpcf.all_steps(tmp_path, [{"lv": 0}, {"lv": 5}], ["S", "TRUCK"], 1, runner=fake_runner)
    assert again["model_sha256"] == res["model_sha256"]     # fitted once, reused (review F8)
    with pytest.raises(SystemExit):
        mpcf.all_steps(tmp_path, [{"lv": 0}, {"lv": 4}], ["S", "TRUCK"], 1, runner=fake_runner)     # other actions: refused (review F7)
    with pytest.raises(SystemExit):
        mpcf.all_steps(tmp_path, [{"lv": 0}, {"lv": 5}], ["S", "SURGE"], 1, runner=fake_runner)


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


def test_asch_tune_none_admissible_is_a_failed_build(tmp_path, monkeypatch):
    monkeypatch.setattr(pb, "rule_cfg", lambda ctrl, cond: {"ctrl": ctrl, "cond": cond})

    def crashy(jobs, workers):     # every ASCH configuration collides more than p333 + 1
        for (name, q, seed), m in fake_runner(jobs, workers):
            yield (name, q, seed), {**m, "collisions": 2.0 if "|t" in name or "never" in name else 0.0}
    res = asch.tune(tmp_path, {"lv": 1}, {"T3E": {"lv": 2}}, ["S", "SURGE"], 1, runner=crashy)
    assert res["failed_build"] and res["pick"] is None and res["stage2"] == []


def test_guard_refuses_other_inputs_and_records_code(tmp_path):
    m = pb.guard(tmp_path, {"a": 1}, {"x": {"c": 1}}, strict=False)
    assert set(m["code"]) == {"commit", "clean", "detached", "diff_sha256"}
    pb.guard(tmp_path, {"a": 1}, {"x": {"c": 1}}, strict=False)
    with pytest.raises(SystemExit):
        pb.guard(tmp_path, {"a": 2}, {"x": {"c": 1}}, strict=False)
    with pytest.raises(SystemExit):
        pb.guard(tmp_path, {"a": 1}, {"x": {"c": 2}}, strict=False)


def test_reserve_caps_the_machine(tmp_path, monkeypatch):
    f = tmp_path / "w.json"
    f.write_text(json.dumps({"1": 90}))     # pid 1 is alive
    with pytest.raises(SystemExit):
        pb.reserve(20, f)
    monkeypatch.setattr(pb.atexit, "register", lambda *a: None)
    pb.reserve(10, f)
    assert json.loads(f.read_text())[str(__import__("os").getpid())] == 10
    with pytest.raises(SystemExit):
        pb.check_workers(101)


def test_repick_choose_on_planted_rows():
    import repick
    fam = {"own": {"o1": {}, "o2": {}}, "uniform": {"p333": {}, "u0": {}}}
    vals = {"p333": (100.0, 50.0, 0), "o1": (101.0, 40.0, 0), "o2": (99.0, 45.0, 0), "u0": (150.0, 10.0, 0)}     # u0: delay +50 %, not admissible
    T = {f"X|{r}": {s: {"all_delay": d + s % 3, "ttc_net": c, "collisions": k} for s in range(20)} for r, (d, c, k) in vals.items()}
    ch = repick.choose(T, "X", fam)
    assert ch["forms"] == {"own": "o1", "uniform": "p333"} and ch["lowest_cf"] == "o1"
    assert ch["front_row"] == "o1" and ch["delay_opponent"] == "o2"     # u0 has the lowest close-following but fails the delay band


def test_s1_helpers():
    import s1
    assert s1.diff({"a": 1, "cfg": 1, "m_st_file": "x"}, {"a": 1, "cfg": 2, "m_st_file": "y"}) == []
    assert s1.diff({"a": 1, "b": [1, 2]}, {"a": 1, "b": [1, 3]}) == ["b"]
    s_row = {"flow_min": list(range(30)), "v20_min": list(range(30)), "m_minute": {"k": list(range(25))}}
    c_row = {"flow_min": list(range(30)), "v20_min": list(range(30)), "m_minute": {"k": list(range(5)) + [99] * 20}}
    assert s1.minutes_equal(c_row, s_row, 600.0) == []     # minute 5 of m_minute is the first after 600 s
    c_row["m_minute"]["k"][4] = 98
    assert s1.minutes_equal(c_row, s_row, 600.0) == ["m_minute.k"]


def plan6_world(tmp_path, s2_cells=None, asch_ok=True, mpcf_ok=True, steady_equals=None, commit="c" * 40):
    import plan6
    code = {"commit": commit, "clean": True, "detached": True, "diff_sha256": "d"}
    s2 = {"null_broken": False, "code": code, "cells": s2_cells or {"SURGE": {"passes": True, "drain_cap": 30.0}, "TRUCK": {"passes": True, "drain_cap": 20.0}}}
    cells = [c for c in pb.CELLS if s2["cells"][c]["passes"]]
    rules = {f"r{i}": {"own_state": {"level": 1, "th": 10.5 + i, "crowd": 0}} for i in range(9)}
    steady = pb.arm_ctrl(steady_equals) if steady_equals else {"own_state": {"level": 0, "th": 99, "crowd": 0}}
    repick = {"conds": ["S"] + cells, "code": code, "ctrl": rules, "cell_opponents": {"SURGE": [f"r{i}" for i in range(8)], "TRUCK": [f"r{i}" for i in range(1, 9)]},
              "steady_pick": "rs", "steady_ctrl": steady}
    for c in cells:
        for i, obj in enumerate(("ttc", "delay")):
            d = tmp_path / f"{c}_{obj}"
            d.mkdir()
            z = [{"th": 5.0 + i + 2 * (c == "TRUCK"), "crowd": 0, "level": 1, "free": 3}] * 5
            (d / "pick.json").write_text(json.dumps({"cell": c, "objective": obj, "incumbent": {"params": z}, "label": "met the plateau criterion", "generations": 100}))
            (d / "meta.json").write_text(json.dumps({"cell": c, "objective": obj, **code}))
    x = plan6.inputs(repick, tmp_path, cells)
    asch_res = {"conds": ["S"] + cells, "code": code, "steady": x["steady"], "library": x["library"],
                "pick": {"ctrl": {"asch": {"steady": x["steady"], "dist": x["library"]["3E-T"], "theta_kmh": 55, "tau_s": 30, "h_kmh": 5}}} if asch_ok else None}
    (tmp_path / "mpcf_model.pt").write_bytes(b"model")
    mpcf_res = {"conds": ["S"] + cells, "code": code, "gate_passed": mpcf_ok, "actions": x["actions"], "model": "mpcf_model.pt",
                "model_sha256": __import__("hashlib").sha256(b"model").hexdigest()}
    return plan6, s2, repick, asch_res, mpcf_res


@pytest.mark.skipif(not pb.JOB.exists(), reason="round 2's job file is not on this machine")
def test_plan6_arm_counts_match_the_protocol(tmp_path):
    plan6, s2, repick, asch_res, mpcf_res = plan6_world(tmp_path)
    P = plan6.freeze(s2, repick, tmp_path, asch_res, mpcf_res, tmp_path)
    out = tmp_path / "jobs"
    out.mkdir()
    J, conf = plan6.jobs(P, out)
    per = lambda cond: sum(1 for k in J if k.startswith(cond + "|"))
    assert per("SURGE") == per("TRUCK") == 34
    assert per("S") == 24 + 10 * 2 - 7     # the two cells share 7 re-picks, which run once in S
    assert len(conf["opponents"]["SURGE"]) == 34 - 5 - 1 and conf["m"] == 2
    assert conf["e3c"] == {"SURGE": "3E-C_SURGE", "TRUCK": "3E-C_TRUCK"} and conf["seed_range"] == [7_480_400, 7_480_639]
    m = J["SURGE|MPC-F"]["ctrl"]["mpcf"]
    assert Path(m["model"]).read_bytes() == b"model" and m["model_sha256"] == mpcf_res["model_sha256"]     # the model travels in the picks file


@pytest.mark.skipif(not pb.JOB.exists(), reason="round 2's job file is not on this machine")
def test_plan6_freeze_refuses_inconsistent_inputs(tmp_path):
    plan6, s2, repick, asch_res, mpcf_res = plan6_world(tmp_path)
    for bad in ({**s2, "null_broken": True}, {**s2, "cells": {"SURGE": s2["cells"]["SURGE"]}},
                {**s2, "cells": {**s2["cells"], "TRUCK": {"passes": None, "drain_cap": 1.0}}}):
        with pytest.raises(SystemExit):
            plan6.freeze(bad, repick, tmp_path, asch_res, mpcf_res, tmp_path)
    for bad_asch in ({**asch_res, "library": {"3E-T": {"x": 1}}}, {**asch_res, "steady": {"x": 1}}, {**asch_res, "conds": ["S", "SURGE"]}):
        with pytest.raises(SystemExit):
            plan6.freeze(s2, repick, tmp_path, bad_asch, mpcf_res, tmp_path)
    with pytest.raises(SystemExit):
        plan6.freeze(s2, repick, tmp_path, asch_res, {**mpcf_res, "actions": mpcf_res["actions"][:3]}, tmp_path)
    with pytest.raises(SystemExit):
        plan6.freeze(s2, {**repick, "code": {**repick["code"], "commit": "e" * 40}}, tmp_path, asch_res, mpcf_res, tmp_path)
    with pytest.raises(SystemExit):     # S2 at another commit whose plant cannot be shown equal (here: not a commit at all)
        plan6.freeze({**s2, "code": {**s2["code"], "commit": "e" * 40}}, repick, tmp_path, asch_res, mpcf_res, tmp_path)
    (tmp_path / "TRUCK_ttc" / "pick.json").write_text(json.dumps({"cell": "SURGE", "objective": "ttc", "incumbent": None, "label": "x", "generations": 100}))
    with pytest.raises(SystemExit):
        plan6.freeze(s2, repick, tmp_path, asch_res, mpcf_res, tmp_path)     # a pick from the wrong cell


@pytest.mark.skipif(not pb.JOB.exists(), reason="round 2's job file is not on this machine")
def test_plan6_failed_builds_are_omitted_and_m_stays(tmp_path):
    s2c = {"SURGE": {"passes": True, "drain_cap": 30.0}, "TRUCK": {"passes": False, "drain_cap": 20.0}}
    plan6, s2, repick, asch_res, mpcf_res = plan6_world(tmp_path, s2_cells=s2c, asch_ok=False, mpcf_ok=False, steady_equals="os1_15_10")
    p = json.loads((tmp_path / "SURGE_delay" / "pick.json").read_text())
    (tmp_path / "SURGE_delay" / "pick.json").write_text(json.dumps({**p, "incumbent": None, "label": "not converged at 100 generations"}))
    P = plan6.freeze(s2, repick, tmp_path, asch_res, mpcf_res, tmp_path)
    assert P["cells"] == ["SURGE"] and P["m"] == 2 and P["asch"] is None and P["mpcf"] is None
    assert set(P["omitted"]) == {"ASCH", "MPC-F", "3E-D_SURGE"}
    out = tmp_path / "jobs"
    out.mkdir()
    J, conf = plan6.jobs(P, out)
    assert "TRUCK|p333" not in J and "SURGE|MPC-F" not in J and "SURGE|ASCH" not in J and "SURGE|3E-D_SURGE" not in J
    assert "steady_rs" not in conf["opponents"]["SURGE"] and "S|steady_rs" not in J     # the steady pick equals os1_15_10: runs once
    assert conf["s_alias"] == {"steady_rs": "os1_15_10"} and conf["m"] == 2


def no_own_in_truck(jobs, workers):
    """Every own-state rule is 10 % slower than p333 in TRUCK (none admissible); os0_15_10 has the lowest close-following."""
    for name, cfg, q, seed, rd in jobs:
        cond, rule = name.split("|", 1)
        slow = cond == "TRUCK" and rule.startswith("os")
        cf = 50.0 if rule == "os0_15_10" else 80.0 if rule.startswith("os") else 100.0
        yield (name, q, seed), {"q": q, "seed": seed, "all_delay": 1000.0 * (1.1 if slow else 1.0) + seed % 3, "delay_s": 1000.0, "ttc_net": cf,
                                "collisions": 0.0, "passed": 3000.0, "alks_full_moving": 0.0, "finished_pct": 99.0}


def test_repick_writes_the_v482_fallback_start(tmp_path):
    import repick
    res = repick.run(tmp_path, ["S", "SURGE", "TRUCK"], 1, runner=no_own_in_truck)
    assert "TRUCK" not in res["own_state_repick"] and "SURGE" in res["own_state_repick"]
    assert res["own_state_fallback"] == {"TRUCK": {"level": 0, "th": 15, "crowd": 10}}


def test_code_state_of_a_deployed_copy(tmp_path):
    import hashlib
    (tmp_path / "v5b2").mkdir()
    files = {"a.py": b"x = 1\n", "v5b2/b.py": b"y = 2\n"}
    for f, b in files.items():
        (tmp_path / f).write_bytes(b)
    (tmp_path / "COMMIT").write_text("f" * 40 + "\n")
    (tmp_path / "MANIFEST").write_text("".join(f"{hashlib.sha256(b).hexdigest()}  ./{f}\n" for f, b in sorted(files.items())))
    cs = pb.code_state(tmp_path)
    assert cs == {"commit": "f" * 40, "clean": True, "detached": True, "diff_sha256": hashlib.sha256(b"").hexdigest()}
    (tmp_path / "v5b2" / "__pycache__").mkdir()
    (tmp_path / "v5b2" / "__pycache__" / "b.py").write_bytes(b"cache")     # caches are not code
    assert pb.code_state(tmp_path)["clean"]
    (tmp_path / "v5b2" / "c.py").write_bytes(b"z = 3\n")     # a file added on the host
    assert not pb.code_state(tmp_path)["clean"]
    (tmp_path / "v5b2" / "c.py").unlink()
    (tmp_path / "a.py").write_bytes(b"x = 9\n")     # a file edited on the host
    assert not pb.code_state(tmp_path)["clean"]
