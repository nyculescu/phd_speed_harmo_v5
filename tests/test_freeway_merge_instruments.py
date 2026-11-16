"""Merge V&V build (V532, merge_vv.md §3): geometry, remap, bins, guard and the read-only instruments. No traffic is simulated:
networks are built with netconvert and the instruments run on a fake libsumo."""
import json
import math
from types import SimpleNamespace

import pytest

from v5b2.freeway import environments as be, network as corridor, vehicles as fl, merge_instruments as vm
from v5b2.freeway.evaluate import geometry_guard

E30_NET = "r2m3_096c8f0288"     # the cached 300-m net every E30 row ran on


def lane_lengths(d):
    return json.loads((d / "spec.json").read_text())["lane_lengths"]


@pytest.fixture(scope="module")
def nets():
    return corridor.build(fl.LIMIT, corridor.R2M3), corridor.build(fl.LIMIT, corridor.R2M3, 600.0, 600.0)


def test_300m_net_is_e30s(nets):
    assert nets[0].name == E30_NET


def test_600m_changes_only_the_acceleration_lanes(nets):
    a, b = lane_lengths(nets[0]), lane_lengths(nets[1])
    assert set(a) == set(b)
    for k in a:
        d = b[k] - a[k]
        if k.split("_")[0] in ("3a", "4a"):
            assert abs(d - 300.0) < 0.01, k
        else:
            assert abs(d) < 0.01, k


def test_3a_only_keeps_4a():
    b = lane_lengths(corridor.build(fl.LIMIT, corridor.R2M3, 600.0, 300.0))
    assert abs(b["3a_0"] - 594.72) < 0.01 and abs(b["4a_0"] - 294.72) < 0.01 and abs(b["rj2_0"] - 28.33) < 0.01 and abs(b["3_0"] - 1194.3) < 0.01


def test_train_len_is_the_300m_net(nets):
    a = lane_lengths(nets[0])
    assert be.TRAIN_LEN == {"3a": a["3a_0"], "4a": a["4a_0"]}
    assert be.geometry_is_trained(lambda x: a[x]) and not be.geometry_is_trained(lambda x: lane_lengths(nets[1])[x])


def remap(lens, e, p):
    n = lambda r: lens[r + "_0"]
    train = be.road_starts(lambda r: be.TRAIN_LEN.get(r, n(r)))
    return train[e] + p * (be.TRAIN_LEN[e] / n(e) if e in be.TRAIN_LEN else 1.0)


def test_remap_is_identity_at_300m(nets):
    a = lane_lengths(nets[0])
    built = be.road_starts(lambda r: a[r + "_0"])
    for e in built:
        for p in (0.0, 10.5, a[e + "_0"]):
            assert remap(a, e, p) == built[e] + p


def test_remap_puts_600m_roads_on_their_training_places(nets):
    a, b = lane_lengths(nets[0]), lane_lengths(nets[1])
    train = be.road_starts(lambda r: a[r + "_0"])
    for e in ("3a", "4a"):
        assert remap(b, e, 0.0) == pytest.approx(train[e]) and remap(b, e, b[e + "_0"]) == pytest.approx(train[e] + a[e + "_0"])
    for e in ("1", "2", "3", "4", "5", "r", "rj", "r2", "rj2"):
        assert remap(b, e, 7.0) == pytest.approx(train[e] + 7.0)


def bins_of(lens):
    nb = dict(be.LocalRule.N_BINS) | {"4a": 2, "r2": 2, "rj2": 1}
    return nb, {e: int(math.ceil(lens[e + "_0"] / be.BIN_M - 1e-9)) for e in nb}


def test_bins_from_net_equal_n_bins_at_300m_and_grow_at_600m(nets):
    nb, got = bins_of(lane_lengths(nets[0]))
    assert got == nb
    _, got6 = bins_of(lane_lengths(nets[1]))
    assert got6["3a"] == 3 and got6["4a"] == 3 and {k: v for k, v in got6.items() if k not in ("3a", "4a")} == {k: v for k, v in nb.items() if k not in ("3a", "4a")}


def test_guard():
    pt = {"ctrl": {"pt": "x.pt"}, "fix_x": True}
    for c in ({}, {"ctrl": {"local_rule": {"r": 400}}}, {"ctrl": {"cav_rule": [3, 3, 3]}}, pt | {"x_remap": True}):
        geometry_guard(c | {"accel_len": 600.0, "accel2_len": 600.0}, {})
    geometry_guard({"ctrl": {"pattern": [1, 2, 3]}}, {})     # 300 m: anything goes
    for c in ({"ctrl": {"cav_rule": [1, 3, 3]}}, {"ctrl": {"pattern": [1, 2, 3]}}, pt, {"ctrl": {"cav_rule": [3, 3, 3], "speed": 1}}):
        with pytest.raises(ValueError):
            geometry_guard(c | {"accel_len": 600.0}, {})
    with pytest.raises(ValueError):
        geometry_guard(pt | {"x_remap": True, "accel2_len": 600.0}, {"base_rule": {"x_min": 500}})


def test_encounters_and_main_lane():
    last = {}
    seq = [(("a", "b"), 10.0), (("a", "b"), 11.0), (("a", "b"), 13.0), (("a", "c"), 13.0), (("a", "b"), 14.0)]
    assert [vm.encounter_new(last, p, t) for p, t in seq] == [True, False, True, True, False]
    assert vm.is_main("3_1", "3") and vm.is_main(":ae_0_0", ":ae") and not vm.is_main("3a_0", "3a") and not vm.is_main("rj_0", "rj")
    assert not vm.is_main("4a_0", "4a") and vm.is_main("4a_1", "4a")


class FakeLS:
    """A frozen traffic state: id -> dict(lane, pos, speed, len, mingap, lead, fol)."""

    def __init__(self, cars: dict, lane_len: dict):
        self.cars, self.lane_len = cars, lane_len
        g = lambda k: (lambda v: self._car(v)[k])
        self.vehicle = SimpleNamespace(getLaneID=g("lane"), getRoadID=lambda v: self._car(v)["lane"].rsplit("_", 1)[0],
                                       getLanePosition=g("pos"), getSpeed=g("speed"), getLength=g("len"), getMinGap=g("mingap"),
                                       getLeader=lambda v, d: self._car(v).get("lead"), getFollower=lambda v, d: self._car(v).get("fol"))
        self.lane = SimpleNamespace(getLength=lambda x: lane_len[x], getIDList=lambda: list(lane_len),
                                    getLastStepVehicleIDs=lambda x: [v for v, c in cars.items() if c["lane"] == x])

    def _car(self, v):
        if v not in self.cars:
            raise KeyError(v)
        return self.cars[v]


def car(lane, pos, speed, **kw):
    return {"lane": lane, "pos": pos, "speed": speed, "len": 5.0, "mingap": 2.5} | kw


def test_hit_counts_and_trace():
    ls = FakeLS({"f": car("3a_0", 100.0, 10.0), "l": car("3a_0", 120.0, 2.0), "g": car("3_1", 50.0, 20.0), "m": car("3_1", 80.0, 10.0)}, {})
    vv = vm.VV(ls, {"vv_trace": True}, alks={"f"}, trucks={"m"}, side=None)
    vv.hit(5.0, "f", ("l", 12.5), 10.0, 2.0, 15.0, "3a")
    vv.hit(5.0, "g", ("m", 22.5), 20.0, 10.0, 25.0, "3")
    vv.hit(6.0, "g", ("m", 20.0), 20.0, 10.0, 22.5, "3")
    r = vv.finish("x")
    assert r["vv_ttc3_main"] == 2 and r["vv_enc"] == 2 and len(r["vv_trace"]) == 3
    t = r["vv_trace"][0]
    assert t[:7] == [5.0, "f", "l", "alks", "car", "3a", "3a_0"] and t[13] == 12.5 and t[14] == 2.5
    # gap rebuilt from positions equals SUMO's gap + minGap: 120 - 5 - 100 = 15
    assert t[11] - t[12] - t[7] == pytest.approx(t[13] + t[14])


def test_standing_matches_end_stop_rule():
    L = {"3a_0": 294.72, "4a_0": 294.72}
    ls = FakeLS({"a": car("3a_0", 290.0, 0.5), "b": car("3a_0", 260.0, 0.2), "c": car("3a_0", 280.0, 1.5), "d": car("4a_0", 270.0, 0.0)}, L)
    vv = vm.VV(ls, {"vv_log": True}, set(), set(), side=None)
    vv.second(1.0, set(L))
    vv.second(2.0, {"3a_0"})
    r = vv.finish("x")
    assert r["vv_stand_s"] == {"3a_0": 2, "4a_0": 1} and r["vv_stand_n"] == {"3a_0": 1, "4a_0": 1}


def test_merge_record_and_min_speed():
    cars = {"v": car("3a_0", 200.0, 5.0), "lead": car("3a_1", 230.0, 12.0), "lag": car("3a_1", 180.0, 15.0)}
    ls = FakeLS(cars, {"3a_0": 294.72})
    vv = vm.VV(ls, {"vv_log": True}, alks={"lag"}, trucks=set(), side=None)
    vv.step(10.0, True)
    cars["v"]["speed"] = 3.0
    vv.step(10.1, True)
    cars["v"] |= {"lane": "3a_1", "pos": 201.0, "speed": 6.0, "lead": ("lead", 21.5), "fol": ("lag", 13.5)}
    vv.step(10.2, True)
    r = vv.finish("x")
    m = r["vv_merges_log"][0]
    assert r["vv_merges"] == 1 and m["v"] == "v" and m["pos0"] == 200.0 and m["min_speed_10s"] == 3.0
    assert m["lead"]["net_gap"] == pytest.approx(230.0 - 5.0 - 201.0) and m["lag"]["net_gap"] == pytest.approx(201.0 - 5.0 - 180.0)
    assert m["lag"]["type"] == "alks" and m["lead"]["same_lane"]


def test_meter_whole_and_half():
    ls = FakeLS({"f": car("3_1", 0.0, 10.0, lead=("l", 10.0)), "l": car("3_1", 20.0, 4.0)}, {})
    vv = vm.VV(ls, {"vv_meter": True}, set(), set(), side=None)
    for t in (100.0, 100.1, 100.5, 101.0 - 1e-9):
        vv.meter_step(t, "f", 10.0)
    r = vv.finish("x")     # (10 + 2.5) / 6 = 2.08 s < 3
    assert r["vv_m_step"] == 4 and r["vv_m_whole"] == 2 and r["vv_m_half"] == 1 and r["vv_m_time"] == pytest.approx(0.4)


def test_flags_off_by_default():
    assert not vm.wanted({"split": True, "measure": "x"})


def test_merge_origin_per_lane():
    cars = {"r1": car("3a_0", 100.0, 10.0), "m": car("3a_0", 150.0, 20.0), "q": car("4a_0", 50.0, 20.0)}
    ls = FakeLS(cars, {"3a_0": 294.72, "4a_0": 294.72})
    vv = vm.VV(ls, {"vv_log": True}, set(), set(), None, origin={"3a_0": {"r1", "q"}, "4a_0": set()})
    vv.step(1.0, True)
    for v in cars:
        cars[v]["lane"] = cars[v]["lane"][:-1] + "1"
    vv.step(1.1, True)
    r = vv.finish("x")
    assert [m["v"] for m in r["vv_merges_log"]] == ["r1"] and r["vv_exit_other_3a_0"] == 1 and r["vv_exit_other_4a_0"] == 1
    m = r["vv_merges_log"][0]
    assert "min_gap" not in m and "lane" not in m     # no target-lane neighbours in this state
