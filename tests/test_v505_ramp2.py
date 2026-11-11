"""V-A hook and T0 step (v505_m2_merge_check.md §2, §7; v505_ev_informed_rule.md §8) against a fake libsumo."""
from collections import defaultdict
from types import SimpleNamespace

from v5b.fleet.v505 import AFTER, BEFORE, KEY, ON, Ramp2Assertive, slowdown_limit, t0_step


class FakeLs:
    def __init__(self):
        self.road, self.lane, self.param = {}, {}, {}
        self.departed, self.arrived = [], []
        self.sets = []
        self.simulation = SimpleNamespace(getDepartedIDList=lambda: list(self.departed), getArrivedIDList=lambda: list(self.arrived))
        self.vehicle = SimpleNamespace(getRoadID=lambda v: self.road[v], getLaneID=lambda v: self.lane[v],
                                       setParameter=self._set, getParameter=lambda v, k: self.param.get((v, k), "1.40"))

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
    assert h.state == {"r": BEFORE} and ls.sets == [("r", KEY, "3")]


def test_value_kept_on_4a_0_and_reset_the_step_after_leaving():
    ls, h = run(3)
    for ln, n_sets, state in (("rj2_0", 1, BEFORE), (":d_0_0", 1, BEFORE), ("4a_0", 1, ON), ("4a_0", 1, ON), ("4a_1", 2, AFTER), ("4_0", 2, AFTER)):
        ls.tick(r=ln)
        h.step()
        assert len(ls.sets) == n_sets and h.state["r"] == state, ln
    assert ls.sets[-1] == ("r", KEY, "1.4")


def test_car_that_enters_and_merges_in_one_step_is_reset_and_counted():
    """SUMO moves and changes lanes in the same step (MSNet.cpp:872-884): the hook may never see the car on 4a_0 (review finding)."""
    ls, h = run(3)
    ls.tick(r=":d_0_0")
    h.step()
    ls.tick(r="4a_1")
    h.step()
    assert h.state["r"] == AFTER and ls.sets[-1] == ("r", KEY, "1.4") and h.skipped == 1


def test_arrived_cars_are_dropped_and_tracking_only_sets_nothing():
    ls, h = run(3)
    ls.tick(arrived=["r"])
    h.step()
    assert h.state == {}
    ls, h = run(None)
    for ln in ("4a_0", "4a_1"):
        ls.tick(r=ln)
        h.step()
    assert ls.sets == [] and h.state["r"] == AFTER


def test_read_back_by_lane_catches_a_kept_value_downstream():
    ls, h = run(3)
    S = defaultdict(float)
    h.read_back(S)
    assert S["va_n_feed"] == 1 and S["va_bad_feed"] == 0
    ls.tick(r="4a_0")
    h.step()
    h.read_back(S)
    assert S["va_n_on"] == 1 and S["va_bad_on"] == 0
    ls.tick(r="4a_1")
    h.step()
    ls.param[("r", KEY)] = "3.00"     # as if the reset had not taken
    h.read_back(S)
    assert S["va_n_off"] == 1 and S["va_bad_off"] == 1


def test_read_back_off_without_variant():
    ls, h = run(None)
    S = defaultdict(float)
    h.read_back(S)
    assert not S


SPEC = {"times": [500.0], "dur": 300.0, "taper": 20.0, "limit_kmh": 36.0}
FREE = 100.0 / 3.6


def feed(spec, lane_before=27.78, lane_after=FREE, wrong_in_event=0.0, hold_speed=9.5):
    """The T0 step over a whole run: the lane holds netconvert's 27.78 before onset, perturb's values in the event, 100/3.6 after."""
    acc = {}
    for i in range(1, 18_001):
        t = i * 0.1
        in_ev = spec["times"][0] <= t < spec["times"][0] + spec["dur"]
        got = slowdown_limit(spec, t, FREE) + wrong_in_event if in_ev else lane_before if t < spec["times"][0] else lane_after
        t0_step(acc, spec, t, 0.1, got, hold_speed, FREE)
    return acc


def test_t0_accepts_the_nets_rounded_free_limit_before_onset():
    """The net stores 100/3.6 as 27.78 (review blocker): only a real schedule error may count."""
    acc = feed(SPEC)
    assert acc["limit_bad"] == 0 and acc["steps"] == 18_000 and acc["hold_steps"] > 0
    assert feed(SPEC, wrong_in_event=0.05)["limit_bad"] > 0
    assert feed(SPEC, lane_before=26.0)["limit_bad"] > 0


def test_t0_one_step_lag_in_the_taper_is_accepted():
    acc = {}
    for i in range(5_000, 5_400):
        t = i * 0.1
        t0_step(acc, SPEC, t, 0.1, slowdown_limit(SPEC, t - 0.1, FREE), 9.5, FREE)
    assert acc["limit_bad"] == 0
