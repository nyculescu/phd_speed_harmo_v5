"""B0 reader tests (b0_merge_stops.md §7): planted plant records and hand-made field trajectories."""
import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "docs" / "research" / "b0"))
import b0_read as b0  # noqa: E402

FT = b0.FT


def traj(speed, t0=0.0, t1=30.0):
    t = np.round(np.arange(t0, t1 + 1e-9, 0.1), 1)
    return t, np.array([speed(x) for x in t])


def test_stop_12s_before_not_counted_8s_counted():
    for at, want in ((13.0, False), (17.0, True)):
        t, v = traj(lambda x: 0.0 if abs(x - at) < 0.25 else 10.0)
        h = b0.history(t, v, 25.0)
        assert not h["censored"]
        assert b0.field_stop({"hist": h}, 1.0, False) is want


def test_short_history_is_censored_with_bounds():
    t, v = traj(lambda x: 10.0, t0=15.4)
    h = b0.history(t, v, 25.0)
    assert h["censored"] and abs(h["hist_s"] - 9.0) < 1e-6
    assert b0.field_stop({"hist": h}, 1.0, False) is False
    assert b0.field_stop({"hist": h}, 1.0, True) is True


def test_slow_entry_not_read_as_stopped_after_edge_drop():
    t = np.round(np.arange(0.0, 15.0 + 1e-9, 0.1), 1)
    d = pd.DataFrame({"Location": "i-80", "Vehicle_ID": 1, "traj": 0, "Local_X": 0.0, "Local_Y": 1.8 * t / FT,
                      "Global_Time": t * 1000.0, "v_length": 15.0, "Lane_ID": 7})
    s = b0.smooth(d)
    tt, vv = s["t"].to_numpy(), s["v_s"].to_numpy()
    assert vv[:6].min() < 1.0
    h = b0.history(tt, vv, 10.5)
    assert h["speeds"].min() > 1.7
    assert b0.field_stop({"hist": h}, 1.0, False) is False


def rec(t, v, lead=None, lag=None, typ="car", lane="3a_0", ms=5.0):
    r = {"t": t, "v": v, "type": typ, "lane0": lane, "pos0": 200.0, "pos": 201.0, "speed": 8.0, "min_speed_10s": ms}
    if lead:
        r["lead"] = {"speed": lead[0], "sumo_dist": lead[1], "type": "car"}
    if lag:
        r["lag"] = {"speed": lag[0], "sumo_dist": lag[1], "type": lag[2] if len(lag) > 2 else "car"}
    return r


def test_plant_repeat_early_and_range(tmp_path):
    merges = [rec(305.0, "a"), rec(400.0, "b", lead=(12.0, 50.0), lag=(3.0, 250.0)), rec(420.0, "b", ms=0.0),
              rec(500.0, "c", typ="alks", lead=(25.0, 10.0))]
    with gzip.open(tmp_path / "L300__nc__5300__7492001.json.gz", "wt") as w:
        json.dump({"merges": merges, "stand": {"3a_0": {"b": 3}, "4a_0": {}}}, w)
    pm = b0.plant_mergers(tmp_path)
    assert pm["stats"] == {"files": 1, "repeat": 1, "early": 1, "records": 4}
    b = [r for r in pm["recs"] if r["type"] == "car"][0]
    assert b["lead"] == 12.0 and b["fol"] is None and b["min10"] == 5.0 and b["stood_end"]
    assert b0.band(b["lead"]) == "10-15" and b0.band(b["fol"]) == "none"


def test_pooling_moves_small_bands_towards_10_15():
    pn = {"<5": 5, "5-10": 100, "10-15": 100, "15-20": 100, "20+": 3, "none": 1}
    fn = {"<5": 50, "5-10": 50, "10-15": 50, "15-20": 50, "20+": 50, "none": 50}
    g = b0.pooling(pn, fn)
    assert g["<5"] == "5-10" and g["20+"] == "15-20" and g["none"] == "15-20" and g["10-15"] == "10-15"


def test_compare_equal_shares_give_zero():
    rng = np.random.default_rng(1)
    pn = np.full((40, 2), 10.0)
    pk = np.tile([2.0, 5.0], (40, 1))
    fn = np.full((20, 2), 10.0)
    flo = np.tile([2.0, 5.0], (20, 1))
    out = b0.compare(pn, pk, fn, flo, flo.copy(), np.zeros(20), rng)
    assert abs(out["D_lo"]["point"]) < 1e-9 and abs(out["R_lo"]["point"] - 1.0) < 1e-9
    assert out["D_lo"]["lo"] <= 0 <= out["D_lo"]["hi"]


def test_standardisation_uses_field_weights():
    rng = np.random.default_rng(2)
    pn = np.tile([10.0, 10.0], (10, 1))
    pk = np.tile([0.0, 10.0], (10, 1))
    fn = np.tile([9.0, 1.0], (10, 1))
    out = b0.compare(pn, pk, fn, np.zeros((10, 2)), np.zeros((10, 2)), np.zeros(10), rng)
    assert abs(out["plant"]["point"] - 10.0) < 1e-9 and abs(out["D_lo"]["point"] - 10.0) < 1e-9
