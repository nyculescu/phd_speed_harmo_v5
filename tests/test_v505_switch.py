"""EV's told (IP) and detected (SW (a)) switches (v505_ev_informed_rule.md §3, §8), against a fake libsumo and a fake env."""
import sys
from types import SimpleNamespace

import pytest

from v5b2.freeway import merge_variants as v505


class FakeLs:
    def __init__(self):
        self.road, self.pos, self.tau = {}, {}, {}
        self.vehicle = SimpleNamespace(getRoadID=lambda v: self.road[v], getLanePosition=lambda v: self.pos[v], getTau=lambda v: self.tau.get(v, 1.6))


@pytest.fixture
def fls(monkeypatch):
    f = FakeLs()
    monkeypatch.setitem(sys.modules, "libsumo", f)
    return f


def env(t=0.0, spec=None):
    pert = SimpleNamespace(kind="slowdown", s=spec or {"times": [600.0], "dur": 300.0}) if spec is not False else None
    return SimpleNamespace(sim=SimpleNamespace(t=t), pert=pert, headways=(1.6, 1.2, 1.0, 0.8), v2v_lead={}, plant={"geom": "r2m3"}, bins={}, on=set())


def test_told_zone_and_window(fls):
    e = env()
    sw = v505.Told(e, d=1000.0, L=1, after=60.0)
    fls.road["a"], fls.pos["a"] = "1", 2500.0     # 500 m upstream of edge 2
    fls.road["b"], fls.pos["b"] = "1", 1500.0     # 1,500 m upstream: outside d
    fls.road["c"], fls.pos["c"] = "2", 100.0      # on edge 2
    fls.road["d"], fls.pos["d"] = "3a", 10.0      # downstream
    for t, want in ((559.0, 3), (560.0, 1), (899.0, 1), (959.9, 1), (960.0, 3)):     # window: 600 - 1000/25 to 600 + 300 + 60
        e.sim.t = t
        assert sw.level("a", 3, True) == want, t
    e.sim.t = 700.0
    assert sw.level("b", 3, True) == 3 and sw.level("c", 3, True) == 1 and sw.level("d", 3, True) == 3


def test_told_can_shorten_as_well_as_lengthen(fls):
    e = env(700.0)
    fls.road["a"], fls.pos["a"] = "2", 50.0
    assert v505.Told(e, d=500.0, L=3, after=0.0).level("a", 0, True) == 3     # base 1.6 s, told 0.8 s
    assert v505.Told(e, d=500.0, L=0, after=0.0).level("a", 3, True) == 0


def test_told_is_off_without_a_slowdown(fls):
    fls.road["a"], fls.pos["a"] = "2", 50.0
    assert v505.Told(env(700.0, spec=False), d=500.0, L=1, after=0.0).level("a", 3, True) == 3


def test_t0_counts_read_back_after_the_rise_time(fls):
    e = env(700.0)
    sw = v505.Told(e, d=500.0, L=0, after=0.0)
    fls.road["a"], fls.pos["a"] = "2", 50.0
    e.v2v_lead["a"] = "x"
    e.on.add("a")
    for k in range(8):
        e.sim.t = 700.0 + k
        fls.tau["a"] = 1.6 if k >= 4 else 0.8 + 0.2 * k
        sw.level("a", 3, True)
    assert sw.t0["switched_s"] == 8 and sw.t0["read_n"] == 3 and sw.t0["read_bad"] == 0
    fls.tau["a"] = 1.2
    e.sim.t = 708.0
    sw.level("a", 3, True)
    assert sw.t0["read_bad"] == 1


class FakeLook:
    def __init__(self, speeds):
        self.speeds = speeds

    def _ahead(self, v):
        return self.speeds.get(v)


def test_detect_fires_holds_and_releases(fls, monkeypatch):
    e = env()
    e.bins = {("1", 0): 20.0}
    sw = v505.Detect(e, r=1000.0, th=13.0, L=1, after=60.0)
    look = FakeLook({"a": 20.0})
    sw.look = look
    seq = ((100.0, 20.0, 3), (101.0, 8.0, 1), (130.0, 20.0, 1), (161.0, 20.0, 1), (161.1, 20.0, 3))
    for t, speed, want in seq:
        e.sim.t, look.speeds["a"] = t, speed
        assert sw.level("a", 3, True) == want, t


def test_detect_idle_before_the_bins_exist(fls):
    e = env()
    e.bins = {}
    sw = v505.Detect(e, r=1000.0, th=13.0, L=1, after=60.0)
    sw.look = FakeLook({"a": 1.0})
    assert sw.level("a", 3, True) == 3


def test_t0_read_back_skips_the_first_on_second_after_a_leader_change(fls):
    """Review blocker: after a second without an ALKS leader SUMO holds the contract 1.6 s; that second must not count as bad."""
    e = env(700.0)
    sw = v505.Told(e, d=500.0, L=3, after=0.0)
    fls.road["a"], fls.pos["a"] = "2", 50.0
    for k in range(20):
        e.sim.t = 700.0 + k
        lost = k == 10     # leader lost at k = 10: _v2v commands 1.6 s that second, so SUMO holds 1.6 at k = 11
        on_now = not lost
        fls.tau["a"] = 1.6 if k == 11 else 0.8
        sw.level("a", 0, on_now)
        (e.on.add if on_now else e.on.discard)("a")     # what CavEnv._v2v does after level() returns
    assert sw.t0["read_bad"] == 0 and sw.t0["read_n"] > 0
    fls.tau["a"] = 1.2     # a wrong tau on a second consecutive on-second is still caught
    e.sim.t = 720.0
    sw.level("a", 0, True)
    assert sw.t0["read_bad"] == 1


def test_detect_release_timing_is_checked(fls):
    e = env()
    e.bins = {("1", 0): 20.0}
    sw = v505.Detect(e, r=1000.0, th=13.0, L=1, after=60.0)

    class Look:
        sp = 8.0

        def _ahead(self, v):
            return self.sp
    sw.look = Look()
    for k in range(0, 80):
        e.sim.t = 100.0 + k
        sw.look.sp = 8.0 if k < 5 else 20.0
        sw.level("a", 3, True)
    assert sw.t0["release_n"] == 1 and sw.t0["release_bad"] == 0


def test_told_refuses_a_changed_edge2(fls, monkeypatch):
    from v5b2.freeway import environments as b_env
    monkeypatch.setitem(b_env.ROAD_X, "2", 2990.0)
    with pytest.raises(ValueError):
        v505.Told(env(), d=500.0, L=1, after=0.0)
