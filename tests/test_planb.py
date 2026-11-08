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
