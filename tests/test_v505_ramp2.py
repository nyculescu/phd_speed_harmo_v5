"""V-A hook (v505_m2_merge_check.md §2, §7) against a fake libsumo: who gets the value, when it is reset, what read-back counts."""
from collections import defaultdict
from types import SimpleNamespace

from v5b.fleet.v505 import AFTER, BEFORE, KEY, ON, Ramp2Assertive


class FakeLs:
    def __init__(self):
        self.road, self.lane, self.param = {}, {}, {}
        self.departed, self.arrived = [], []
        self.sets = []
        self.simulation = SimpleNamespace(getDepartedIDList=lambda: list(self.departed), getArrivedIDList=lambda: list(self.arrived))
        self.vehicle = SimpleNamespace(getRoadID=lambda v: self.road[v], getLaneID=lambda v: self.lane[v],
                                       setParameter=self._set, getParameter=lambda v, k: self.param.get((v, k), "1.4"))

    def _set(self, v, k, x):
        self.sets.append((v, k, x))
        self.param[(v, k)] = x

    def tick(self, departed=(), arrived=(), **lanes):
        self.departed, self.arrived = list(departed), list(arrived)
        for v, ln in lanes.items():
            self.lane[v] = ln
            self.road[v] = ln.rsplit("_", 1)[0]


def run(a):
    ls = FakeLs()
    h = Ramp2Assertive(ls, a, 1.4)
    ls.tick(departed=["r", "m"], r="r2_0", m="1_0")
    h.step()
    return ls, h


def test_only_ramp2_cars_get_the_value_at_departure():
    ls, h = run(3)
    assert h.state == {"r": BEFORE}
    assert ls.sets == [("r", KEY, "3")]


def test_value_kept_on_4a_0_and_reset_the_step_after_leaving():
    ls, h = run(3)
    ls.tick(r="4a_0")
    h.step()
    assert h.state["r"] == ON and len(ls.sets) == 1
    ls.tick(r="4a_0")
    h.step()
    assert len(ls.sets) == 1
    ls.tick(r="4a_1")
    h.step()
    assert h.state["r"] == AFTER and ls.sets[-1] == ("r", KEY, "1.4")
    ls.tick(r="4_0")
    h.step()
    assert len(ls.sets) == 2


def test_internal_junction_lane_before_4a_0_is_not_a_reset():
    ls, h = run(3)
    ls.tick(r=":rm2_0_0")
    h.step()
    assert h.state["r"] == BEFORE and len(ls.sets) == 1


def test_arrived_cars_are_dropped():
    ls, h = run(3)
    ls.tick(arrived=["r"])
    h.step()
    assert h.state == {}


def test_tracking_only_sets_nothing():
    ls, h = run(None)
    ls.tick(r="4a_0")
    h.step()
    ls.tick(r="4a_1")
    h.step()
    assert ls.sets == [] and h.state["r"] == AFTER


def test_read_back_counts_by_state_and_catches_a_reset_value():
    ls, h = run(3)
    S = defaultdict(float)
    h.read_back(S)
    assert S["va_n_0"] == 1 and S["va_bad_0"] == 0
    ls.param[("r", KEY)] = "1.4"     # as if the plant's own settings had reset it (fleet.py:179)
    h.read_back(S)
    assert S["va_bad_0"] == 1
    ls.tick(r="4a_0")
    h.step()
    ls.tick(r="4a_1")
    h.step()
    h.read_back(S)
    assert S["va_n_2"] == 1 and S["va_bad_2"] == 0


def test_read_back_off_without_variant():
    ls, h = run(None)
    S = defaultdict(float)
    h.read_back(S)
    assert not S
