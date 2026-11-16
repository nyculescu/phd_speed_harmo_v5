import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from e1_meter import SafetyMeter, flags


def test_no_leader_only_braking_counts():
    f = flags(30.0, -8.0, None, None)
    assert f["brake3"] and f["brake7"] and not f["ttc3"] and not f["drac3"]


def test_ttc_and_drac_while_closing():
    f = flags(30.0, 0.0, 20.0, 20.0)  # TTC 2 s, DRAC 2.5
    assert f["ttc3"] and not f["drac3"]
    f = flags(30.0, 0.0, 10.0, 20.0)  # TTC 1 s, DRAC 5
    assert f["ttc3"] and f["drac3"] and not f["drac7"]


def test_opening_gap_is_safe():
    f = flags(20.0, 0.0, 5.0, 30.0)
    assert not any(f[m] for m in ("ttc3", "drac3", "drac7"))


def test_braking_between_whole_seconds_is_missed_at_1hz():
    # V367's pattern: 0.5 s of hard braking starting at t = 0.3 s.
    m = SafetyMeter()
    for k in range(20):
        a = -9.0 if 3 <= k < 8 else 0.0
        m.step([("v", 25.0, a, None, None)])
    r = m.result()
    assert math.isclose(r["fine_vs"]["brake7"], 0.5)
    assert r["hz1_vs"]["brake7"] == 0.0
    assert r["missed_share"]["brake7"] == 1.0
    assert r["brake_events"]["brake7"] == 1


def test_steady_condition_agrees_at_both_resolutions():
    m = SafetyMeter()
    for _ in range(100):  # 10 s closing at TTC 2 s
        m.step([("v", 30.0, 0.0, 20.0, 20.0)])
    r = m.result()
    assert math.isclose(r["fine_vs"]["ttc3"], 10.0)
    assert r["hz1_vs"]["ttc3"] == 10.0
    assert abs(r["missed_share"]["ttc3"]) < 1e-9


def test_event_onsets_per_vehicle():
    m = SafetyMeter()
    pattern = [-4, -4, 0, -4, 0]
    for a in pattern:
        m.step([("a", 20.0, a, None, None), ("b", 20.0, -4.0, None, None)])
    assert m.result()["brake_events"]["brake3"] == 3  # a twice, b once
