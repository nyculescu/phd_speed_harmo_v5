"""Merge V&V runner checks (vv.py) on rows shaped as run6 writes them, and the shipped remap and bins code on a fake libsumo."""
import copy
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis" / "vv"))
import vv  # noqa: E402
import read_vv as rv  # noqa: E402
from vv import run6  # noqa: E402
from v5b2.fleet import b_env as be, vv_merge as vm  # noqa: E402

LANES300 = {"3a_0": 294.72, "4a_0": 294.72, "3_0": 1194.3, "4_0": 996.0}


def fake_rows(plan: dict, seed: int, mutate=None) -> list:
    """One row per job as run6.wrap labels it, with the instrument keys VV.finish would write."""
    out = []
    for n, c in plan["arms"].items():
        L = c.get("accel_len", 300.0)
        r = {"name": n, "seed": seed, "ttc_net": 100.0, "ttc_half": 98.0, "c1_t0": {"veh_n": 3000, "alks_sha": "x"}}
        if vm.wanted(c):
            r["vv_lanes"] = {k: v + (L - 300.0 if k[:2] in ("3a", "4a") else 0.0) for k, v in LANES300.items()}
        if c.get("vv_meter"):
            r |= {"vv_m_time": 110.0, "vv_m_whole": 100.0, "vv_m_half": 98.0, "vv_m_step": 1100.0}
        if c.get("vv_obs"):
            r |= {"vv_x_acc_n": 50.0, "vv_x_out": 0.0, "vv_c15_n": 500.0, "vv_c15_cap": 0.0}
        r = run6.wrap(r, (n, c, 5300.0, seed, "rd", "abc"))
        out.append(mutate(r) if mutate else r)
    return out


@pytest.fixture(scope="module")
def smoke_plan(tmp_path_factory):
    return vv.plan("vv_smoke", tmp_path_factory.mktemp("s"))


def test_plan_shapes(tmp_path):
    n = {s: len(vv.plan(s, tmp_path)["arms"]) for s in vv.STAGES}
    assert n == {"vv_replay": 12, "vv_trace": 12, "vv_smoke": 24, "vv_screen": 18}
    p = vv.plan("vv_smoke", tmp_path)["arms"]
    assert "vv_obs" not in p["L600|nc" + vv.TWIN] and p["L600|nc"]["vv_obs"] and "vv_obs" not in p["L300|nc"]
    assert p["L300|nc"]["vv_meter"] and "vv_meter" not in p["L600|nc"] and p["L600|w1u500"]["x_remap"]


def test_t0_lengths_pass_and_fail(smoke_plan):
    rows = fake_rows(smoke_plan, 1)
    assert vv.t0_lengths(rows, smoke_plan["arms"]) == []
    bad = fake_rows(smoke_plan, 1, lambda r: r | {"vv_lanes": {**r["vv_lanes"], "3_0": 1000.0}} if r["name"] == "L600|nc" else r)
    assert vv.t0_lengths(bad, smoke_plan["arms"]) == ["L600|nc 1: 3_0 1194.30 -> 1000.00"]


def test_meter_and_obs_and_demand(smoke_plan):
    rows = fake_rows(smoke_plan, 1)
    assert vv.meter_bugs(rows) == [] and vv.same_demand(rows) == []
    r2 = fake_rows(smoke_plan, 1, lambda r: {k: v for k, v in r.items() if not k.startswith("vv_m_")} if r["name"] == "L300|p333" else r)
    assert len(vv.meter_bugs(r2)) == 1
    r3 = fake_rows(smoke_plan, 1, lambda r: r | {"c1_t0": {"veh_n": 2999, "alks_sha": "x"}} if r["name"] == "L600|nc" else r)
    assert vv.same_demand(r3) == ["L600|nc 1"]


def stored():
    return [json.loads(x) for x in vv.REPLAY_ROWS.read_text().splitlines()]


def replay_rows(tmp_path, change=None):
    plan = vv.plan("vv_replay", tmp_path)
    ref = {(r["name"], r["seed"]): r for r in stored()}
    out = []
    for n, c in plan["arms"].items():
        for s in vv.seeds("vv_replay"):
            r = copy.deepcopy(ref[(n.split("~")[0], s)]) | {"name": n}
            if n.endswith("~trace"):
                r |= {"vv_trace": [], "end_trace": [], "vv_lanes": LANES300}
            r = run6.wrap(r, (n, c, 5300.0, s, "rd", "abc"))
            out.append(change(r) if change else r)
    return out


def test_ident_go_on_perfect_replays(tmp_path):
    res = vv.ident(replay_rows(tmp_path), vv.CF_CPU)
    assert res["action"] == "go" and not res["tracer_bug"] and not res["learner_diff_disclosed"]


def test_ident_catches_a_traced_difference(tmp_path):
    rows = replay_rows(tmp_path, lambda r: r | {"all_delay": r["all_delay"] + 1.0} if r["name"] == "E30|nc~trace" else r)
    res = vv.ident(rows, vv.CF_CPU)
    assert res["action"] == "go" and res["tracer_bug"]
    rows = replay_rows(tmp_path, lambda r: r | {"all_delay": r["all_delay"] + 1.0} if r["name"] == "E30|p333" else r)
    assert vv.ident(rows, vv.CF_CPU)["action"] == "stop"
    rows = replay_rows(tmp_path, lambda r: r | {"ttc_net": r["ttc_net"] + 1.0} if r["name"] == "E30|w0u250" else r)
    assert vv.ident(rows, vv.CF_CPU)["action"] == "stop" and vv.ident(rows, "Other CPU")["learner_diff_disclosed"]


class FakeVeh:
    def __init__(self, road, pos):
        self.road, self.pos = road, pos


def fake_ls(lens: dict, cars: dict):
    return SimpleNamespace(lane=SimpleNamespace(getLength=lambda x: lens[x]),
                           vehicle=SimpleNamespace(getRoadID=lambda v: cars[v].road, getLanePosition=lambda v: cars[v].pos))


def env_with(lens, remap):
    e = SimpleNamespace(plant={"fix_x": True, "x_remap": remap}, cfg=SimpleNamespace(geom=be.R2M3), x_base={}, xlast={}, xlast_raw={})
    e._x_base = lambda train=False: be.CavEnv._x_base(e, train)
    e._x_scale = lambda r: be.CavEnv._x_scale(e, r)
    return e


L300 = {"1_0": 3000.0, "2_0": 498.3, "3a_0": 294.72, "3_0": 1194.3, "4a_0": 294.72, "4_0": 996.0, "5_0": 500.0, "r_0": 391.66, "rj_0": 28.33,
        "r2_0": 391.66, "rj2_0": 28.33}
L600 = {**L300, "3a_0": 594.72, "4a_0": 594.72}


def test_shipped_remap(monkeypatch):
    cars = {"a": FakeVeh("3a", 594.72), "b": FakeVeh("4a", 297.36), "c": FakeVeh("4", 10.0), "j": FakeVeh(":ae_0", 1.0)}
    monkeypatch.setattr(be, "ls", fake_ls(L600, cars))
    e = env_with(L600, True)
    x = lambda v, raw=False: be.CavEnv._x(e, v, raw)
    assert x("a") == pytest.approx(294.72) and x("a", raw=True) == pytest.approx(594.72)
    assert x("b") == pytest.approx(294.72 + 1194.3 + 147.36) and x("b", raw=True) == pytest.approx(594.72 + 1194.3 + 297.36)
    assert x("c") == pytest.approx(294.72 + 1194.3 + 294.72 + 10.0)
    assert x("j") == e.xlast.get("j", 0.0)     # inside a junction: the last value
    monkeypatch.setattr(be, "ls", fake_ls(L300, cars | {"a": FakeVeh("3a", 100.0)}))
    for remap in (False, True):
        e = env_with(L300, remap)
        assert be.CavEnv._x(e, "a") == be.CavEnv._x(e, "a", raw=True) == 100.0 and be.CavEnv._x(e, "c") == 294.72 + 1194.3 + 294.72 + 10.0


def test_shipped_bins(monkeypatch):
    for lens, want in ((L300, None), (L600, {"3a": 3, "4a": 3})):
        monkeypatch.setattr(be, "ls", fake_ls(lens, {}))
        rule = be.LocalRule.__new__(be.LocalRule)
        rule.n_bins = dict(be.LocalRule.N_BINS) | {"4a": 2, "r2": 2, "rj2": 1}
        ref = dict(rule.n_bins)
        rule._bins_from_net()
        assert rule.n_bins == (ref if want is None else ref | want)


def test_v1_missing_twin_and_off_route():
    import test_read_vv as t
    r = t.traced_row()
    out = rv.v1([r], [])
    assert out["twins"] == {"L300|nc~trace 1": ["missing twin"]} and out["outcome"] == "TRACER BUG"
    r = t.traced_row()
    r["vv_trace"][2][9], r["vv_trace"][2][10] = "r2", "r2_0"     # a leader on a road not ahead of edge 3
    assert any("off the route" in x for x in rv.v1_row(r, [])["definition"])
    assert rv.ahead("3", "4a") and rv.ahead("2", "3") and rv.ahead("3a", ":ae_1") and not rv.ahead("4", "3")


def test_failed_null_reads_not_shown(monkeypatch):
    import test_read_vv as t
    monkeypatch.setattr(rv, "B", 2000)
    calls = []

    def fake_rate(D, swaps, nb, pct, seed):
        calls.append((swaps, nb, pct))
        return 0.03
    monkeypatch.setattr(rv.rf, "null_rate", fake_rate)
    out = rv.v3(t.rows(t.plan(900, 1100, 600, 450)), list(range(t.N)), [], ["cpu"])
    assert out["v3a"]["replication"]["reading"] == "NOT REPLICATED" and out["v3b"]["reading"] == "NOT SHOWN"
    assert (rv.SWAPS, rv.NB, rv.P975) in calls and (rv.RE_SWAPS, rv.NB, rv.P975) in calls and (rv.RE_SWAPS, rv.NB_W, rv.P9875) in calls


def test_worse_null_bar_is_094(monkeypatch):
    import test_read_vv as t
    monkeypatch.setattr(rv, "B", 2000)
    for rate, ok in ((0.0094, True), (0.0095, False)):
        monkeypatch.setattr(rv.rf, "null_rate", lambda D, swaps, nb, pct, seed, rate=rate: rate)
        out = rv.v3(t.rows(t.plan(900, 1100, 600, 450)), list(range(t.N)), [], ["cpu"])
        assert out["v3b"]["reading"] == ("WORSE" if ok else "NOT SHOWN")


def test_derive_meter_presence():
    base = {"name": "L300|nc", "all_delay": 1.0, "ttc_net": 5.0, "ttc_half": 4.0, "passed": 1.0, "N": 1.0, "collisions": 0}
    ok = rv.derive(base | {"vv_m_time": 6.0, "vv_m_whole": 5.0, "vv_m_half": 4.0}, None)["meter_ok"]
    bad = rv.derive(base | {"vv_m_time": 6.0, "vv_m_whole": 4.0, "vv_m_half": 4.0}, None)["meter_ok"]
    absent = rv.derive(base, None)["meter_ok"]
    assert ok and not bad and not absent


def test_obs_and_missing_position_reads(smoke_plan):
    rows = fake_rows(smoke_plan, 1)
    assert all(v["x_out"] == 0 for v in vv.obs_checks(rows).values()) and len(vv.obs_checks(rows)) == 9
