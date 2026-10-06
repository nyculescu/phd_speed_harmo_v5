"""Event-layer and comparison tests (protocol v3 §8.4 tests 10, 14, 16 and the P7c test; synthetic only)."""
from __future__ import annotations

import numpy as np

from vsl_lab.data import metanet_events as V
from vsl_lab.data import metanet_inputs as I

NB = 216


def test_nrmse_known_answer():
    x = np.full(200, 100.0)
    xhat = x + 10.0
    assert abs(V.nrmse(xhat, x, np.ones(200, bool)) - 0.10) < 1e-12
    assert V.nrmse(xhat, x, np.r_[np.ones(99, bool), np.zeros(101, bool)]) is None     # < 100 pairs


def test_cs_toy_single_lane_excluded_sentinel_included():
    # three G3 stations, one single-lane (not all lanes are speed lanes), plus a downstream sentinel
    m_s = {"PT": 71.8, "OSR": 70.9, "AL": 62.5, "TH101": 62.7}
    g = {k: "G3" for k in m_s}
    full = {"PT", "OSR", "TH101"}                      # AL is the single-lane station
    t = V.scale_table(m_s, g, full)
    assert t["AL"]["in_mG"] is False and t["TH101"]["in_mG"] is True
    assert abs(t["OSR"]["m_G"] - 70.9) < 1e-9          # median(71.8, 70.9, 62.7)
    assert abs(t["TH101"]["c_s"] - 70.9 / 62.7) < 1e-9 and t["AL"]["dropped"] is False
    # observation operator: a model equal to the scaled real speeds reproduces the raw real series
    real = np.array([60.0, np.nan, 30.0])
    model_kmh = real * t["TH101"]["c_s"] * V.MPH
    out = V.observe(model_kmh, t["TH101"]["c_s"], real, True)
    assert np.allclose(out[[0, 2]], real[[0, 2]]) and np.isnan(out[1])      # per-bin mask follows the real NaN
    assert np.isnan(V.observe(model_kmh, 1.0, real, False)).all()             # invalid station-day fully masked


def _toy(slow_station, kms):
    sp = {s: np.full(NB, 60.0) for s in kms}
    sp[slow_station][100:120] = 25.0
    return sp


def test_event_layer_ea2_named_pair_and_3km_limit():
    km = {"S1772": 1.667, "S1773": 2.893, "S1140": 6.038, "S1141": 7.199}
    valid = {k: True for k in km}
    ep = V.pair_episodes(_toy("S1773", km), km, valid)
    assert ("S1773", "S1140") in ep and ep[("S1773", "S1140")]               # P_1 evaluated at 3.145 km
    km2 = dict(km, X=10.5, Y=14.0)                                            # an unnamed > 3 km pair
    sp = _toy("S1773", km2)
    sp["X"][100:120] = 25.0
    ep2 = V.pair_episodes(sp, km2, {k: True for k in km2})
    assert ("X", "Y") not in ep2
    assert "S1147" not in I.EVENT_STATIONS                                    # Anderson Lakes Pkwy absent (EA-2)
    assert I.P1 == ("S1773", "S1140") and I.P2 == ("S1140", "S1141")


def test_event_layer_matches_committed_estimator_except_named_pair():
    from vsl_lab.data.corridor_analysis import episodes
    km = {"S1140": 6.038, "S1141": 7.199}
    sp = _toy("S1140", km)
    ep = V.pair_episodes(sp, km, {k: True for k in km})
    cond = (sp["S1140"] < 40) & ((sp["S1141"] - sp["S1140"]) >= 20)
    assert ep[("S1140", "S1141")] == episodes(cond)


def test_b1_censoring_by_b2():
    real_b1 = [(100, 130)]
    real_b2 = [(125, 160)]                       # B2 onset inside the B1 episode
    tc = V.censor_time(real_b1, real_b2)
    assert tc == {0: 125}
    assert V.censored_duration((100, 130), 125) == 25 * 5
    assert V.censored_duration((126, 150), 125) == 0                     # model episode starting after t_c
    assert V.censored_duration(None, 125) == 0                            # unmatched
    assert V.censor_time([(100, 110)], [(116, 130)]) == {0: 116}           # within 30 min after the end
    assert V.censor_time([(100, 110)], [(117, 130)]) == {}                 # beyond 30 min
    q = np.full(NB, 3600.0)
    q[100:] = 3400.0
    a = V.c4(q, (100, 140), 2)
    b = V.c4(q, (100, 140), 2, end_cap=125)
    assert a["window"] == (102, 140) and b["window"] == (102, 125)       # C4 window ends at t_c


def test_p7c_union():
    assert V.p7c([(10, 20)], [(15, 30)]) == 21 * 5                     # overlapping
    assert V.p7c([(10, 20)], [(21, 30)]) == 21 * 5                     # back-to-back
    assert V.p7c([(10, 20)], [(23, 30)]) == 21 * 5                     # gap of 2 bins (< 30 min): joined
    assert V.p7c([(10, 20)], [(27, 30)]) == 11 * 5                     # gap of 6 bins (30 min): separate, the longer
    assert V.p7c_pair([(10, 20)], [], [(30, 40)], []) == (55, 55)       # starts 50 min after the real end
    assert V.p7c_pair([(10, 20)], [], [(30, 40)], [(80, 90)]) == (55, 55)
    assert V.p7c_pair([(10, 20)], [], [(33, 43)], []) == (55, 0)        # 65 min after the real end: 0
    assert V.p7c([(10, 20)], [(15, 30)]) == V.p7c([(15, 30)], [(10, 20)])


def test_episode_matching_one_to_one():
    real = [(100, 120), (150, 160)]
    model = [(105, 125), (101, 110), (200, 210)]
    m = V.match_episodes(real, model)
    assert m == {0: 1} or m == {0: 1, 1: 0} or m[0] == 1
    assert 1 not in m or abs(model[m[1]][0] - 150) <= 18


def test_split_builder():
    cal, val = I.split_days()
    assert len(cal) == 28 and len(val) == 24
    assert cal[:3] == ["20230104", "20230118", "20230201"] and val[:2] == ["20230111", "20230125"]
    assert {"20230104", "20230705"} <= set(cal) and {"20231122", "20231227"} <= set(val)
