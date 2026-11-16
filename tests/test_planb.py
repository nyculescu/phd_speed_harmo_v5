"""Plan B (planb.md §7.1): spec tests for the new perturbation kinds, without SUMO."""
import dataclasses
import inspect
import pickle
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from v5b2.freeway import merge_bind_check as bm, vehicles as fl, disturbances as pt

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "analysis/conf3"))
from common import COND  # noqa: E402

SURGE, TRUCK = COND["SURGE"], COND["TRUCK"]     # the spec tests run on the dicts the runs use (review F28)
SEEDS = range(7_480_000, 7_480_010)
TIE_SEEDS = (7_480_025, 7_480_027, 7_480_400, 7_480_402, 7_480_460)     # a truck departs exactly at a slot (review F28)


def test_cells_equal_the_protocol_literals():
    assert SURGE == {"kind": "surge", "profile": [[0.0, 600.0, 5300.0], [600.0, 1200.0, 6000.0], [1200.0, 1800.0, 4600.0]]}
    assert TRUCK == {"kind": "truck_fixed", "n": 10, "first": 360.0, "spacing": 80.0, "cap_kmh": 40.0, "route": "main", "lane": 0}


@pytest.mark.parametrize("seed", (*SEEDS[:3], *TIE_SEEDS))
def test_truck_fixed_takes_the_first_eligible_truck_at_or_after_each_slot(seed):
    env = env_for(seed)
    elig = sorted((v.depart, v.vid) for v, r in zip(env.dem.veh, env.dem.route_of) if v.cls == "truck" and r == "main" and v.lane == 0)
    p = pt.Perturb(env, TRUCK, seed)
    p.demand()
    taken = set()
    for k, vid, dep in p.log:
        want = next((d, v) for d, v in elig if d >= 360.0 + 80.0 * k and v not in taken)
        assert (dep, vid) == want
        taken.add(vid)


def test_reset_builds_the_vehicle_sets_after_the_perturbed_demand():
    from v5b2.freeway import environments as be
    src = inspect.getsource(be.MergeEnv.reset)
    assert src.index("self.pert.demand()") < src.index("self._demand_sets()") < src.index("self.dem.write(")
    env = env_for(7_480_001)
    pt.Perturb(env, SURGE, 7_480_001).demand()
    be.MergeEnv._demand_sets(env)
    assert env.alks_all == {v.vid for v in env.dem.veh if v.cls == "alks"} and env.alks_all
    assert env.ramp == {v.vid for v, r in zip(env.dem.veh, env.dem.route_of) if r.startswith("ramp")}
    assert env.alks == env.alks_all - env.ramp and len(env.desired) == len(env.dem.veh)


def env_for(seed, q=5300.0):
    cfg = dataclasses.replace(bm.setup(0.5, 0.1), geom="r2m3")
    return SimpleNamespace(cfg=cfg, t_end=1800.0, warm=300.0, plant={}, dem=fl.FleetDemand(seed, [(0.0, 1800.0, q)], cfg))


@pytest.mark.parametrize("seed", SEEDS)
def test_truck_fixed_selects_ten_named_trucks(seed):
    env = env_for(seed)
    before = {v.vid: v.max_speed for v in env.dem.veh}
    p = pt.Perturb(env, TRUCK, seed)
    p.demand()
    chosen = [x[1] for x in p.log]
    assert len(chosen) == 10 == len(set(chosen))
    route = dict(zip((v.vid for v in env.dem.veh), env.dem.route_of))
    for k, vid, dep in p.log:
        v = env.dem.by_id[vid]
        assert v.cls == "truck" and route[vid] == "main" and v.lane == 0
        assert 360.0 + 80.0 * k <= dep == v.depart < 1800.0     # not always before 1,200 s: s0_deviations.md D1
        assert v.max_speed == pytest.approx(40.0 / 3.6)
        assert 'maxSpeed="11.1111"' in v.vtype_xml()
    changed = {v.vid for v in env.dem.veh if v.max_speed != before[v.vid]}
    assert changed == set(chosen)


def test_truck_fixed_is_the_same_for_every_arm():
    a, b = env_for(7_480_003), env_for(7_480_003)
    pa, pb = pt.Perturb(a, TRUCK, 7_480_003), pt.Perturb(b, TRUCK, 7_480_003)
    pa.demand()
    pb.demand()
    assert pa.log == pb.log


def test_truck_fixed_fails_loudly_when_trucks_run_out():
    env = env_for(7_480_000)
    with pytest.raises(ValueError):
        pt.Perturb(env, {**TRUCK, "n": 200}, 7_480_000).demand()


def rows(dem):
    return [(v.vid, v.depart, r, v.vtype_xml()) for v, r in zip(dem.veh, dem.route_of)]


@pytest.mark.parametrize("seed", SEEDS)
def test_surge_equals_steady_before_600_s(seed):
    s, e = env_for(seed), env_for(seed)
    p = pt.Perturb(e, SURGE, seed)
    p.demand()
    a = [x for x in rows(s.dem) if x[1] < 600.0]
    b = [x for x in rows(e.dem) if x[1] < 600.0]
    assert a == b and len(a) > 0
    assert e.dem.profile == [(0.0, 600.0, 5300.0), (600.0, 1200.0, 6000.0), (1200.0, 1800.0, 4600.0)]
    assert p.log == [("profile", [[0.0, 600.0, 5300.0], [600.0, 1200.0, 6000.0], [1200.0, 1800.0, 4600.0]])]
    # vehicles are drawn by index, so the shorter list's vehicles carry the same class and attributes
    n = min(len(s.dem.veh), len(e.dem.veh))
    assert [v.vtype_xml() for v in s.dem.veh[:n]] == [v.vtype_xml().replace(v.vid, v.vid) for v in e.dem.veh[:n]]


def test_surge_departures_follow_the_profile():
    counts = np.zeros((40, 3))
    for i, seed in enumerate(range(7_480_000, 7_480_040)):
        e = env_for(seed)
        pt.Perturb(e, SURGE, seed).demand()
        d = np.array([v.depart for v in e.dem.veh])
        counts[i] = [(d < 600).sum(), ((d >= 600) & (d < 1200)).sum(), (d >= 1200).sum()]
    want = np.array([5300, 6000, 4600]) / 6.0
    se = np.sqrt(want / 40.0)     # Poisson counts, pooled over 40 seeds
    assert np.all(np.abs(counts.mean(axis=0) - want) <= 3 * se)


def test_surge_rejects_a_profile_with_a_gap():
    e = env_for(7_480_000)
    with pytest.raises(ValueError):
        pt.Perturb(e, {"kind": "surge", "profile": [[0, 600, 5300], [700, 1800, 5300]]}, 7_480_000).demand()


def test_existing_kinds_leave_the_demand_list_alone():
    for spec in ({"kind": "slowdown", "edge": "4", "limit_kmh": 25, "dur": 120.0, "times": [600.0], "taper": 20.0},
                 {"kind": "truck", "cap_kmh": 50, "period": 300.0, "first": 360.0}, {"kind": "random"}):
        a, b = env_for(7_480_001), env_for(7_480_001)
        pt.Perturb(b, spec, 7_480_001).demand()
        assert rows(a.dem) == rows(b.dem)


# The pack's Plan B keys on planted traces (planb.md §5, PR-24).
from v5b2.freeway import measures as me


class _Pert:
    def __init__(self, spec, log=()):
        self.s, self.kind, self.log = spec, spec["kind"], list(log)


class _Env:
    def __init__(self, pert=None):
        self.alks_all, self.warm, self.t_end, self.pert = {"a"}, 300.0, 1800.0, pert

        class D:
            veh, route_of = [], []
        self.dem = D()


class _Sim:
    """A planted world: per second, vehicle -> (road, lane index, position, speed, leader, gap)."""
    def __init__(self):
        self.vehicle, self.simulation, self.now, self.pending = self, self, {}, []

    def getIDList(self):
        return list(self.now)

    def getRoadID(self, v):
        return self.now[v][0]

    def getLaneID(self, v):
        return f"{self.now[v][0]}_{self.now[v][1]}"

    def getLanePosition(self, v):
        return self.now[v][2]

    def getSpeed(self, v):
        return self.now[v][3]

    def getLeader(self, v, dist):
        lead, gap = self.now[v][4], self.now[v][5]
        return (lead, gap) if lead else ("", -1.0)

    def getMinGap(self, v):
        return 2.5

    def getPendingVehicles(self):
        return self.pending


def _pack(pert=None, trucks=("t",)):
    return me.Measure(_Env(pert), set(trucks), {"main": ("1 2 3a 3 4a 4 5", 1.0, 3)}, lambda e: 1000.0, 0.1)


def test_event_period_labels():
    s = {"kind": "surge", "profile": [[0, 600, 5300], [600, 1200, 6000], [1200, 1800, 4600]]}
    assert [pt.event_period(s, t) for t in (599, 600, 1199, 1200)] == ["before", "surge", "surge", "post"]
    tr = {"kind": "truck_fixed", "first": 360.0}
    assert [pt.event_period(tr, t) for t in (359, 360, 1799)] == ["before", "trucks", "trucks"]
    x1 = {"kind": "slowdown", "times": [600.0, 1200.0], "dur": 120.0, "taper": 20.0}
    assert [pt.event_period(x1, t) for t in (500, 605, 650, 730, 900, 1210)] == ["before", "taper", "hold", "after", "rest", "taper"]
    assert pt.event_period(None, 700) == "rest" and pt.event_period({"kind": "brake"}, 700) == "rest"


def test_close_following_by_road_period_and_lane_change():
    m = _pack(_Pert({"kind": "truck_fixed", "first": 360.0}))
    w = _Sim()
    # f follows l on road 3 at 20 m/s against 10 m/s, gap 10 m: TTC 1.25 s, every second; f changes lane at 400 s
    for t in range(350, 420):
        w.now = {"l": ("3", 1, 500.0, 10.0, "", 0.0), "f": ("3", 0 if t < 400 else 1, 480.0, 20.0, "l", 10.0)}
        m.second(w, float(t))
    row = m.finish(420.0, None, "x")
    assert row["m_road_ttc3"] == {"3": {"before": 10, "trucks": 60}}
    assert row["m_ttc3_all"] == 70
    assert row["m_ttc3_lc"] == 6     # 400-405 s: within 5 s after f's lane change
    assert row["m_road_vs"]["3"] == {"before": 20, "trucks": 120}
    assert row["m_road_dist"]["3"]["trucks"] == pytest.approx(60 * 30.0)


def test_stuck_counts_only_outside_a_stopped_queue():
    m = _pack()
    w = _Sim()
    for t in range(301, 301 + 310):
        w.now = {"q1": ("4a", 0, 100.0, 0.0, "q0", 5.0), "q0": ("4a", 0, 110.0, 0.0, "", 0.0),     # q1 queues behind stopped q0
                 "d": ("3", 1, 50.0, 0.05, "m", 20.0), "m": ("3", 1, 75.0, 8.0, "", 0.0)}     # d sits still while its leader moves
    for t in range(301, 301 + 310):
        m.second(w, float(t))
    row = m.finish(700.0, None, "x")
    assert row["m_stuck_n"] == 2     # d, and q0 (no leader within 50 m); q1 is in a queue


def test_robust_braking_counted_where_it_peaks():
    m = _pack(_Pert({"kind": "surge", "profile": [[0, 600, 5300], [600, 1200, 6000], [1200, 1800, 4600]]}))

    class L(_Sim):
        def getRoadID(self, v):
            return "4a" if v == "c" else "1"

        def getLanePosition(self, v):
            return 42.0

        def getLeader(self, v, dist):
            return ("", -1.0)

    ls = L()
    for k, a in enumerate((-3.2, -4.1, -3.0, 0.0)):     # car c: one event peaking at -4.1, robust
        m.vehicle_step(ls, "c", a, 20.0, 0.0, 700.0 + 0.1 * k)
    for k, a in enumerate((-3.6, 0.0)):     # truck t: -3.6, robust for a truck
        m.vehicle_step(ls, "t", a, 20.0, 0.0, 500.0 + 0.1 * k)
    for k, a in enumerate((-3.8, 0.0)):     # ALKS a: -3.8, not robust
        m.vehicle_step(ls, "a", a, 20.0, 0.0, 1300.0 + 0.1 * k)
    row = m.finish(1800.0, None, "x")
    assert row["m_robust_road"] == {"4a": {"surge": 1}, "1": {"before": 1}}
    assert sum(row["m_peak_car"][2:]) + sum(row["m_peak_alks"][2:]) + sum(row["m_peak_truck"][1:]) == 2


def test_congestion_run_and_capped_field():
    n = np.ones((40, 20))
    v = np.full((40, 20), 25.0)     # 90 km/h everywhere
    v[5:40, 0:6] = 10.0     # 36 km/h on 6 cells x 50 m = 0.3 km for 35 bins = 350 s
    cong_vs, run = me.congestion(v, n)
    assert cong_vs == 35 * 6 and run == 350.0
    v[20, 0] = 25.0     # one bin drops to 0.25 km: the run splits
    assert me.congestion(v, n)[1] == 190.0
    m = _pack(_Pert({"kind": "truck_fixed", "first": 360.0}, [(0, "cap", 400.0)]), trucks=("cap",))
    w = _Sim()
    w.now = {"cap": ("1", 0, 100.0, 11.1, "", 0.0), "c": ("1", 1, 100.0, 30.0, "", 0.0)}
    m.second(w, 301.0)
    assert m.st[1].sum() == 2 and m.st_nc[1].sum() == 1 and m.capped == {"cap"}


def test_step_is_a_no_op_for_demand_kinds():
    for spec in (SURGE, TRUCK):
        e = env_for(7_480_000)
        p = pt.Perturb(e, spec, 7_480_000)
        p.demand()
        n = len(p.log)
        p.step(700.0)     # step() dispatches to _<kind>; the demand kinds have no per-second action
        assert len(p.log) == n


class _World(_Sim):
    """A planted world for the pack and the PR-24 recount together: per second a scenario; braking steps read from acc."""
    def __init__(self):
        super().__init__()
        self.acc, self.extra = {}, {}

    def getAcceleration(self, v):
        return self.acc.get(v, 0.0)

    def getRoadID(self, v):
        return self.extra[v][0] if v in self.extra else self.now[v][0]

    def getLanePosition(self, v):
        return self.extra[v][1] if v in self.extra else self.now[v][2]

    def getLaneID(self, v):
        road, lane = self.now[v][0], self.now[v][1]
        return lane if isinstance(lane, str) else f"{road}_{lane}"

    def getLeader(self, v, dist):
        return ("", -1.0) if v in self.extra else super().getLeader(v, dist)


def scene(t):
    """vehicle -> (road, lane, position, speed, leader, gap)."""
    w = {"f": ("3" if t < 520 else "4a", (0 if t < 400 else 1) if t < 520 else 1, 480.0, 20.0, "l", 10.0),     # 3_1 -> 4a_1: index 1 -> 0
         "j": (":j1", ":j1_0", 1.0, 0.0, "", 0.0),     # deadlocked inside a junction
         "d299": ("2", 0, 100.0, 0.0 if t <= 599 else 5.0, "", 0.0), "d300": ("2", 1, 100.0, 0.0 if t <= 600 else 5.0, "", 0.0),
         "s60": ("2", 2, 100.0, 0.0, "x", 60.0), "x": ("2", 2, 162.5, 0.0, "", 0.0), "cr": ("1", 0, 50.0, 0.5, "", 0.0),
         "q1": ("4a", 0, 100.0, 0.0, "q0", 5.0), "q0": ("4a", 0, 107.5, 0.0, "", 0.0)}
    w["l"] = ("3", 1, 500.0, 10.0, "", 0.0) if t < 500 else (":j3", ":j3_0", 1.0, 10.0, "", 0.0) if t < 505 else ("4a", 2, 10.0, 10.0, "", 0.0)
    w["cap"] = ("1", 0, 300.0, 40.0 / 3.6, "", 0.0) if t < 600 else (":j0", ":j0_0", 1.0, 12.0, "", 0.0) if t < 603 else ("2", 0, 5.0, 40.0 / 3.6, "", 0.0)
    return w


def test_pack_and_recount_agree_on_a_planted_world():
    """PR-24 on a planted trace: the pack's Plan B counters equal the independent recount, and the hand counts hold."""
    import importlib
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "analysis/planb"))
    pr24 = importlib.import_module("pr24")
    saved = (me.Measure.__init__, me.Measure.second, me.Measure.vehicle_step)
    try:
        pr24.install()
        vs = [SimpleNamespace(vid=v, depart=290.0) for v in ("pr", "pr2", "pm")]
        env = _Env(_Pert({"kind": "truck_fixed", "first": 360.0}, [(0, "cap", 360.0)]))
        env.dem.veh, env.dem.route_of = vs, ["ramp", "ramp2", "main"]
        m = me.Measure(env, {"cap"}, {"main": ("1 2 3a 3 4a 4 5", 1.0, 3)}, lambda e: 1000.0, 0.1)
        w = _World()
        for t in range(301, 701):
            w.now = scene(t)
            w.pending = ["pr", "pr2", "pm"] if t < 400 else []
            if t == 360:     # car c brakes across the period boundary and peaks on road 2 at 360.0; truck cap at -3.6
                for tt, a, road in ((359.8, -3.2, "1"), (359.9, -3.5, "1"), (360.0, -4.2, "2"), (360.1, -3.1, "2"), (360.2, 0.0, "2")):
                    w.extra["c"], w.acc["c"] = (road, 42.0), a
                    m.vehicle_step(w, "c", a, 20.0, 0.0, tt)
            if t == 450:
                for tt, a in ((450.0, -3.6), (450.1, -3.6), (450.2, 0.0)):
                    w.acc["cap"] = a
                    m.vehicle_step(w, "cap", a, 10.0, 0.0, tt)
            m.second(w, float(t))
        row = m.finish(700.0, None, "x")
        rc = pr24.recount(pr24._REC)
    finally:
        me.Measure.__init__, me.Measure.second, me.Measure.vehicle_step = saved
    assert pr24.recount_differs(row, rc) == []
    assert pr24.recount_differs(row, pickle.loads(pickle.dumps(rc))) == []     # a worker process returns it
    assert row["m_stuck_n"] == 5     # j, d300, s60 (its stopped leader is 60 m ahead), x and q0; not d299, the crawler or q1
    assert row["m_robust_road"] == {"2": {"trucks": 1}, "1": {"trucks": 1}}     # c peaks on road 2 after 360 s; cap on road 1
    assert row["m_road_vs"]["junction"] == {"before": 59, "trucks": 341 + 5 + 3}     # j all along, l for 5 s, cap for 3 s
    assert row["m_capped_vmax"] == 12.0     # the capped truck's junction seconds count
    assert row["m_main_pending_min"][0] == 60 and row["m_minute"]["ramp1_pending"][0] == 60     # minute 0 is (300, 360] s
    f_lc = 6 + 6     # f's lane changes at 400 s (3_0 -> 3_1) and at 520 s (3_1 -> 4a_1, across the edge)
    assert row["m_ttc3_lc"] == f_lc


def test_ttc_threshold_includes_min_gap():
    m = _pack()
    w = _Sim()
    for t, gap in ((301, 26.5), (302, 27.5)):     # (gap + 2.5) / 10 = 2.9 s and 3.0 s
        w.now = {"l": ("r2", 0, 500.0, 10.0, "", 0.0), "f": ("r2", 0, 480.0, 20.0, "l", gap)}
        m.second(w, float(t))
    row = m.finish(400.0, None, "x")
    assert row["m_road_ttc3"] == {"ramp2": {"rest": 1}} and row["m_ttc3_all"] == 1


def test_congestion_counts_vehicle_seconds_not_cells():
    n = np.ones((40, 20))
    v = np.full((40, 20), 25.0)
    v[5:40, 0:6] = 10.0
    n[5:40, 0] = 4.0
    v[5:40, 0] *= 4.0     # speed sums: the same 36 km/h with 4 vehicles in the first cell
    assert me.congestion(v, n)[0] == 35 * (5 + 4)
