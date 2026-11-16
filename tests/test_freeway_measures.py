"""The round-2 measurement pack (V468): binning, quantiles, braking events and cascades, wave and merge metrics on inputs with
known answers."""
import numpy as np
import pytest

from v5b2.freeway import measures as me


class _Env:
    def __init__(self):
        self.alks_all = {"a"}
        self.warm, self.t_end = 300.0, 1800.0

        class D:
            veh, route_of = [], []
        self.dem = D()


class _Ls:
    """Only getLeader, which the event code calls."""
    def __init__(self, leaders):
        self.vehicle = self
        self.leaders = leaders

    def getLeader(self, v, dist):
        lead = self.leaders.get(v)
        return (lead, 10.0) if lead else ("", -1.0)

    def getRoadID(self, v):     # Plan B: the braking event's place
        return "4"

    def getLanePosition(self, v):
        return 100.0


def _meas():
    return me.Measure(_Env(), {"t"}, {"main": ("1 2", 1.0, 3)}, lambda e: 1000.0, 0.1)


def test_bins():
    assert me.v_bin(0.0) == 0 and me.v_bin(100.0 / 3.6) == 20 and me.v_bin(500.0) == me.V_N - 1
    assert me.a_bin(-10.0) == 0 and me.a_bin(-50.0) == 0 and me.a_bin(0.0) == 20 and me.a_bin(9.0) == me.A_N - 1
    assert me.bin_of(-3.2, me.PEAK_EDGES) == 0 and me.bin_of(-8.5, me.PEAK_EDGES) == 7 and me.bin_of(-9.0, me.PEAK_EDGES) == 8 and me.bin_of(-4.5, me.PEAK_EDGES) == 3
    assert me.bin_of(0.3, me.DUR_EDGES) == 0 and me.bin_of(12.0, me.DUR_EDGES) == 6


def test_offsets():
    o = me.offsets("1 2 3a", {"1": 3000.0, "2": 498.3, "3a": 294.72}.get)
    assert o == {"1": 0.0, "2": 3000.0, "3a": 3498.3, "_end": pytest.approx(3793.02)}


def test_quantiles_uniform():
    q = me.quantiles([10, 10, 10, 10], 0.0, 1.0, (0.25, 0.5, 1.0))
    assert q == pytest.approx([1.0, 2.0, 4.0])
    assert me.quantiles([0, 0], 0.0, 1.0) == [None] * 5


def test_braking_events_sum_to_b3_and_cascade():
    m = _meas()
    ls = _Ls({"f": "l"})
    acc = {"l": [0, -4, -5, -4, 0, 0, 0, 0], "f": [0, 0, -3.5, -6, -3, 0, -3.1, 0]}
    b3 = 0.0
    for k in range(8):
        t = 301.0 + 0.1 * k
        for v in ("l", "f"):
            a = acc[v][k]
            m.vehicle_step(ls, v, a, 20.0, 1000.0, t)
            b3 += 0.1 * (a <= -3.0)
    row = m.finish(302.0, None, "x")
    assert row["m_events_car"] == 3
    assert row["m_event_s_car"] == pytest.approx(b3)
    assert row["m_cascade_car"] == 2     # both of f's events start within 3 s after l's
    assert sum(row["m_peak_car"]) == 3 and row["m_peak_car"][5] == 1     # f's -6 m/s² event is in the -6..-7 bin
    assert row["m_fuel_mg_car"] == pytest.approx(16 * 1000.0 * 0.1)
    assert sum(row["m_vh_car"]) == sum(row["m_ah_car"]) == row["m_n_car"] == 16


def test_open_event_closed_at_finish():
    m = _meas()
    ls = _Ls({})
    for k in range(5):
        m.vehicle_step(ls, "t", -4.0, 10.0, 0.0, 301.0 + 0.1 * k)
    row = m.finish(301.5, None, "x")
    assert row["m_events_truck"] == 1 and row["m_event_s_truck"] == pytest.approx(0.5)


def test_waves_backward_jam_front():
    nt, nx = 60, 80
    v = np.full((nt, nx), 25.0)     # 90 km/h everywhere
    n = np.ones((nt, nx))
    for i in range(10, 40):     # a jam moving upstream one cell (50 m) per time bin (10 s): -18 km/h
        j = 60 - (i - 10)
        v[i, j:j + 4] = 3.0
    w = me.waves(v * n, n)
    assert w["jams"] == 1
    assert w["front_kmh_median"] == pytest.approx(-18.0, abs=0.01)
    assert w["jam_clusters"][0]["duration_s"] == 300.0
    assert w["jam_share"] == pytest.approx(30 * 4 / (nt * nx))
    assert w["congested_km_max"] == pytest.approx(0.2)
    assert w["osc_stations"] == nx


def test_waves_free_flow():
    v, n = np.full((20, 10), 30.0), np.ones((20, 10))
    w = me.waves(v * n, n)
    assert w["jams"] == 0 and w["jam_share"] == 0.0 and w["front_kmh_median"] is None and w["osc_kmh"] == pytest.approx(0.0)


def test_breakdown_capacity_drop():
    out = [35] * 10 + [30] * 10 + [34] * 5     # vehicles per minute: 2,100, then 1,800, then 2,040 veh/h
    n = [100] * 25
    vs = [100 * 25.0] * 10 + [100 * 10.0] * 10 + [100 * 25.0] * 5     # 90 km/h, then 36 km/h, then back
    b = me.breakdown(out, vs, n)
    assert b["breakdown_min"] == 10 and b["recovery_min"] == 20
    assert b["pre_q5max"] == pytest.approx(2100.0) and b["discharge"] == pytest.approx(1800.0)
    assert b["drop_pct"] == pytest.approx(100.0 * 300 / 2100)


def test_breakdown_none():
    b = me.breakdown([30] * 10, [2500.0] * 10, [100] * 10)
    assert b["breakdown_min"] is None and b["drop_pct"] is None and b["flow_mean"] == pytest.approx(1800.0)


class _CavEnv(_Env):
    def __init__(self):
        super().__init__()
        self.lvl, self.on, self.headways, self.n_level = {}, set(), (0.8, 1.0, 1.2, 1.6), 4


def test_decisions_counts_and_confidence():
    env = _CavEnv()
    m = me.Measure(env, set(), {"main": ("1 2", 1.0, 3)}, lambda e: 1000.0, 0.1)
    assert m.cav
    steps = [({"a": 2}, {"a": 1}), ({"a": 2}, {"a": 1}), ({"a": 0}, {"a": 1}), ({"a": 1}, {"a": 1}), ({"a": 3}, {"a": 0})]
    for act, after in steps:     # wanted level, level after the step
        before = dict(env.lvl)
        env.lvl.update(after)
        m.decisions(None, env, act, before, {"a": np.array([0.1, 0.2, 0.6, 0.1])}, {"a": "3"})
    row = m.finish(400.0, None, "x")
    assert row["m_dec_totals"] == {"asked": 5, "changed": 2, "ignored": 2, "kept": 1, "reversals": 1}
    assert row["m_dec_place"]["between"] == [5, 2, 2, 1]
    assert row["m_dec_want"] == [1, 1, 2, 1]
    assert row["m_dec_changes_hist"][2] == 1     # one vehicle with 2 changes
    assert row["m_dec_excess"] == 2     # 2 changes, back at level 0: both are excess
    assert sum(row["m_dec_conf"]) == 5
    s = me.summary({**row, **{f"m_{k}_{c}": 0 for k in ("n", "a2", "fuel_mg", "dist_m", "events", "cascade", "event_s") for c in me.CLASSES},
                    **{f"m_{k}_{c}": [0] for k in ("vh", "ah", "peak", "dur") for c in me.CLASSES}, "m_mergepos_m1": [], "m_mergepos_m2": []} | {"m_minute": {k: [0.0] for k in m.minute}})
    assert s["dec"]["applied_share"] == pytest.approx(0.4) and s["dec"]["reversal_share"] == pytest.approx(0.5)


def test_policy_probs_greedy_and_switch():
    torch = pytest.importorskip("torch")

    class _Net:
        def logits(self, x):
            return torch.stack([x[:, 0], -x[:, 0]], 1)

    class _G:
        net = _Net()

    class _Sw:
        policy, x_from = _G(), 500.0
    ids, lo = ["a", "b", "c"], np.array([[0.1, 0.0], [0.6, 0.0], [0.9, 0.0]], np.float32)
    due = np.array([True, True, False])
    p = me.policy_probs(_G(), (ids, lo, None, due))
    assert set(p) == {"a", "b"} and p["b"][0] == pytest.approx(float(torch.softmax(torch.tensor([0.6, -0.6]), 0)[0]))
    assert set(me.policy_probs(_Sw(), (ids, lo, None, due))) == {"b"}     # "a" is upstream of 500 m: the rule's side
    assert me.policy_probs(object(), (ids, lo, None, due)) == {}
