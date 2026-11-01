"""E1 parts of the day runner (V213 §5.2, §7.1): tripinfo parsing and the blocker choice, on hand-built inputs."""
from types import SimpleNamespace

import pytest

from v5b.fleet import day


def test_parse_trips_leaves_out_removed_vehicles(tmp_path):
    x = tmp_path / "t.xml"
    x.write_text("""<tripinfos>
  <tripinfo id="a" depart="100.00" departLane="2_0" departDelay="5.00" arrival="200.00" duration="100.00" routeLength="2500.00"/>
  <tripinfo id="b" depart="300.00" departLane="r_0" departDelay="20.00" arrival="420.00" duration="120.00" routeLength="2000.00"/>
  <tripinfo id="blk" depart="50.00" departLane="2_1" departDelay="0.00" arrival="3000.00" duration="2950.00" routeLength="900.00"/>
</tripinfos>""")
    v = lambda cls: SimpleNamespace(cls=cls, desired=25.0, max_speed=None)      # noqa: E731
    trips, delays, wet, ttt = day.parse_trips(x, {"a": v("hdv_car"), "b": v("truck"), "blk": v("hdv_car")}, {"blk"})
    assert len(trips) == 2 and ttt == pytest.approx(105.0 + 140.0)
    assert trips[0][:4] == (pytest.approx(5.0), 95.0, 200.0, False)          # delay 105 - 100, scheduled 100 - 5
    assert trips[1][0] == pytest.approx(140.0 - 80.0) and trips[1][1] == 280.0 and trips[1][3] is True
    assert delays["hdv_car"] == [pytest.approx(5.0)]                         # the removed blocker is not in the means


class _LS:
    class TraCIException(Exception):
        pass

    def __init__(self, veh):
        self.veh, self.stops, self.lcm = veh, [], {}
        self.lane = SimpleNamespace(getLastStepVehicleIDs=lambda ln: [k for k, v in veh.items() if v["lane"] == ln])
        self.vehicle = SimpleNamespace(getLanePosition=lambda k: veh[k]["x"], getSpeed=lambda k: veh[k]["v"],
                                       getDecel=lambda k: 4.5, setStop=self._stop,
                                       setLaneChangeMode=lambda k, m: self.lcm.__setitem__(k, m))

    def _stop(self, k, edge, pos, laneIndex, duration):
        self.stops.append((k, edge, pos, laneIndex, duration))


def test_blocker_takes_the_nearest_human_that_can_stop(monkeypatch):
    veh = {"near": {"lane": "3_1", "x": 600.0, "v": 27.0},       # needs 81 + 10 m: cannot stop by 650
           "ok": {"lane": "3_1", "x": 500.0, "v": 27.0},
           "far": {"lane": "3_1", "x": 300.0, "v": 27.0},
           "cav": {"lane": "3_1", "x": 520.0, "v": 27.0},
           "other": {"lane": "3_0", "x": 540.0, "v": 27.0}}
    fake = _LS(veh)
    monkeypatch.setattr(day, "ls", fake)
    cls = {"near": "hdv_car", "ok": "truck", "far": "hdv_car", "cav": "alks", "other": "hdv_car"}
    dem = SimpleNamespace(by_id={k: SimpleNamespace(cls=c) for k, c in cls.items()})
    b = {"t": 57600.0, "edge": "3", "lane": 1, "pos": 650.0, "duration": 2700.0}
    r = day._block(b, dem, 57600.0)
    assert r["vid"] == "ok" and fake.stops == [("ok", "3", 650.0, 1, 3000.0)] and fake.lcm == {"ok": 0}
    assert day._block(b, SimpleNamespace(by_id={k: SimpleNamespace(cls="alks") for k in cls}), 57600.0) is None
