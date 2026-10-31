"""E1 runner and metrics (V213 §2, §7.1-7.2, §10.1): output layout, command lines, the all-vehicle delay metrics."""
import numpy as np
import pytest

from v5b.fleet import e1
from v5b.fleet.day import e1_metrics


def test_twins_and_arms_never_share_a_file():
    a = e1.job("s", "R", "nc", "base", 7430040)
    b = e1.job("s", "R", "nc", "base", 7430040, 7435040)
    c = e1.job("s", "I", "nc", "base", 7430040)
    d = e1.job("s", "R", "ma", "p0.95", 7430040)
    paths = {e1.out_path(j) for j in (a, b, c, d)}
    assert len(paths) == 4
    assert e1.out_path(b).parent.name == "ss7435040"


def test_command_lines():
    j = e1.job("s", "I", "c", "p0.95_long", 7430230, 7435230, {"alks": {"zone": "long"}}, "15,18")
    a = e1.argv(j)
    assert a[a.index("--plant") + 1] == "v199" and a[a.index("--adt") + 1] == "45000"
    assert a[a.index("--blocker") + 1] == e1.BLOCKER and a[a.index("--crash-k") + 1] == "0"
    assert a[a.index("--sumo-seed") + 1] == "7435230" and "--ctrl" in a and a[a.index("--hours") + 1] == "15,18"
    r = e1.argv(e1.job("s", "R", "nc", "base", 7430230))
    assert "--blocker" not in r and "--sumo-seed" not in r and "--ctrl" not in r
    assert r[2:4] == ["v5b.fleet.day", "one"]             # matches the CPU guard pattern


def test_order_puts_i_days_and_full_days_first():
    js = [e1.job("s", "R", "nc", "x", 1, hours="15,19"), e1.job("s", "R", "nc", "x", 2), e1.job("s", "I", "nc", "x", 3)]
    assert [j["seed"] for j in e1.order(js)] == [3, 2, 1]


def test_wave1_contents():
    js = e1.wave1(5.22)
    full = [j for j in js if j["hours"] is None and j["arm"] == "nc"]
    assert len(full) == 40 and sum(j["ss"] is not None for j in full) == 20
    assert {j["ss"] - j["seed"] for j in full if j["ss"]} == {e1.TWIN}
    assert len({e1.out_path(j) for j in js}) == len(js)


def test_e1_metrics():
    # delay, scheduled departure, arrival, ramp, class
    tr = np.array([[10.0, 1000.0, 1100.0, 0, 0], [30.0, 16 * 3600.0, 16 * 3600.0 + 400, 1, 4],
                   [700.0, 17 * 3600.0, 87000.0, 0, 1], [20.0, 19.5 * 3600.0, 19.5 * 3600.0 + 300, 1, 0]])
    m = e1_metrics(tr, {"t": 57600.0, "duration": 2700.0})
    assert m["d_all"] == pytest.approx(190.0) and m["d_main"] == pytest.approx(355.0) and m["d_ramp"] == pytest.approx(25.0)
    assert m["d_pm_depart"] == pytest.approx(250.0)
    assert m["d_recovery"] == pytest.approx(360.0)          # departures from 16:45 to 20:00
    assert m["share_over_600"] == pytest.approx(0.25)
    assert m["delay_after24_share"] == pytest.approx(700.0 / 760.0, abs=1e-5)
    assert m["served"]["pm"] == {"main": 0, "ramp": 2} and m["served"]["day"]["main"] == 1
    assert "d_recovery" not in e1_metrics(tr, None)
