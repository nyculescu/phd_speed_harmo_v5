"""V4 extraction on hand-made trajectories (merge_vv.md §3): the merge frame, the target-lane follower, gap and speed difference."""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "docs" / "research" / "vv"))
import ngsim_merges as nm  # noqa: E402

T0 = 1118848075000     # 08:07:55 PDT


def traj(site, vid, lanes, y0, vy, x):
    """One vehicle sampled every 0.1 s: lanes[k], Local_Y = y0 + vy k (ft), Local_X = x(k) (ft)."""
    return [{"Vehicle_ID": vid, "Frame_ID": k, "Global_Time": T0 + 100 * k, "Local_X": x(k), "Local_Y": y0 + vy * k, "v_length": 15.0,
             "v_Vel": vy * 10, "Lane_ID": lanes[k], "Location": site} for k in range(len(lanes))]


def prep(rows):
    d = pd.DataFrame(rows).sort_values(["Location", "Vehicle_ID", "Global_Time"]).reset_index(drop=True)
    return nm.smooth(nm.segments(d))


def test_us101_merge_follower_and_gap():
    m = traj("us-101", 1, [7] * 10 + [6] * 15 + [5] * 16, 500.0, 5.0, lambda k: 70.0)
    f = traj("us-101", 2, [5] * 41, 450.0, 6.0, lambda k: 58.0)
    d = prep(m + f)
    fr = nm.merge_frames("us-101", d)
    assert fr == [("us-101", 1, 0, float(T0 + 2500))]
    r = nm.at_merge("us-101", d, fr)[0]
    assert r["net_gap"] == pytest.approx((625 - 15 - 600) * nm.FT, abs=0.5)
    assert r["dv"] == pytest.approx((50 - 60) * nm.FT, abs=0.2) and r["lag"] == pytest.approx(r["net_gap"] / (60 * nm.FT), rel=0.05)
    assert r["period"] == 1


def test_us101_ignores_vehicles_not_from_the_ramp():
    a = traj("us-101", 3, [6] * 10 + [5] * 10, 500.0, 5.0, lambda k: 70.0)
    assert nm.merge_frames("us-101", prep(a)) == []


def test_i80_lateral_crossing():
    def x(k):
        return 72.0 if k < 15 else max(72.0 - (k - 15) * 1.0, 56.0)
    m = traj("i-80", 1, [7] * 29 + [6] * 21, 300.0, 5.0, x)
    f = traj("i-80", 2, [6] * 50, 250.0, 5.5, lambda k: 60.0)
    d = prep(m + f)
    fr = nm.merge_frames("i-80", d)
    assert len(fr) == 1 and fr[0][1] == 1
    k = (fr[0][3] - T0) / 100
    assert 15 < k < 29     # before the coded lane change: the line is crossed first
    r = nm.at_merge("i-80", d, fr)[0]
    assert r["dv"] == pytest.approx((50 - 55) * nm.FT, abs=0.3) and r["lag"] is not None


def test_slow_follower_has_no_lag_time():
    m = traj("us-101", 1, [7] * 10 + [6] * 15 + [5] * 16, 500.0, 5.0, lambda k: 70.0)
    f = traj("us-101", 2, [5] * 41, 400.0, 1.0, lambda k: 58.0)     # 3 m/s
    d = prep(m + f)
    r = nm.at_merge("us-101", d, nm.merge_frames("us-101", d))[0]
    assert r["lag"] is None and r["dv"] is not None


def test_plant_side_reads_human_merges(tmp_path):
    import gzip
    import json
    ms = [{"type": "car", "speed": 10.0, "lag": {"type": "car", "speed": 12.0, "same_lane": True, "net_gap": 18.0}},
          {"type": "alks", "speed": 10.0, "lag": {"type": "car", "speed": 12.0, "same_lane": True, "net_gap": 6.0}},
          {"type": "truck", "speed": 8.0, "lag": {"type": "alks", "speed": 4.0, "same_lane": True, "net_gap": 10.0}}]
    with gzip.open(tmp_path / "a.json.gz", "wt") as w:
        json.dump({"merges": ms}, w)
    rows = tmp_path / "rows.jsonl"
    rows.write_text(json.dumps({"name": "L300|nc", "seed": 1, "vv_log_file": "a.json.gz"}) + "\n"
                    + json.dumps({"name": "L300|p333", "seed": 1, "vv_log_file": "a.json.gz"}) + "\n")
    out = nm.plant(tmp_path, rows)
    assert out["all"]["dv_ms"]["n"] == 2 and out["all"]["lag_s"]["n"] == 1 and out["human"]["lag_s"]["median"] == pytest.approx(1.5)
    assert out["dropped"] == {"alks_merger": 1, "no_follower": 0}
    assert out["alks"]["dv_ms"]["median"] == pytest.approx(4.0)
