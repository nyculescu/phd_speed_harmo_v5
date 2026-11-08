"""Plan B (planb.md §7.1): spec tests for the new perturbation kinds, without SUMO."""
import dataclasses
from types import SimpleNamespace

import numpy as np
import pytest

from v5b.fleet import b_merge as bm, fleet as fl, perturb as pt

SURGE = {"kind": "surge", "profile": [[0, 600, 5300], [600, 1200, 6000], [1200, 1800, 4600]]}
TRUCK = {"kind": "truck_fixed", "n": 10, "first": 360.0, "spacing": 80.0, "cap_kmh": 40.0, "route": "main", "lane": 0}
SEEDS = range(7_480_000, 7_480_010)


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
from v5b.fleet import measure as me


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
