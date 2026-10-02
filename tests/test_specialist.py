"""Unit tests for vsl_lab/controllers/specialist.py (no SUMO).

Plant used: detectors at the ends of up3 (1000 m), up2 (2000), up1 (3000), up0a (3500), up0b (4000) of a 3-lane road
and at 5245 m (2-lane edge after the 3->2 lane drop at 4000 m); VSL segments are up3..up0b.

Run: pytest -p no:cacheprovider tests/test_specialist.py -v
"""
from __future__ import annotations

import math

from vsl_lab.controllers.specialist import Specialist, front_speed, scheme_states

DET_X = [1000.0, 2000.0, 3000.0, 3500.0, 4000.0, 5245.0]
SEGS = [(0.0, 1000.0), (1000.0, 2000.0), (2000.0, 3000.0), (3000.0, 3500.0), (3500.0, 4000.0)]
FREE_Q, FREE_V = 1800.0, 90.0


def close(a: float, b: float, tol: float = 1e-6) -> bool:
    return abs(a - b) <= tol * max(1.0, abs(b))


def free_data(n: int = 6) -> tuple[list[float], list[float]]:
    return [FREE_Q] * n, [FREE_V] * n


def test_free_flow_no_detection():
    c = Specialist(DET_X, SEGS)
    q, v = free_data()
    q[2], v[2] = 0.0, -1.0          # missing reading (no vehicles): neither jam nor free
    for k in range(5):
        assert c.step(60.0 * k, q, v) == [1.0] * 5
    assert c.n_detected == 0 and c.n_solvable == 0 and c.n_unsolvable == 0
    assert not c.active and c.last_reason == "no_shock_wave"


def test_isolated_jam_default_params_does_not_fit_plant():
    """P1 parameters (m_t = 1.5 km): the required speed-limited stretch is ~11 km, the plant has 4 km of signs."""
    c = Specialist(DET_X, SEGS)
    q, v = free_data()
    q[4], v[4] = 800.0, 20.0
    assert c.step(600.0, q, v) == [1.0] * 5
    assert c.n_detected == 1 and c.n_unsolvable == 1 and not c.active
    assert "outside_signs" in c.last_reason
    # hand: tau2 = 1.5 / (-6 + 15) h, x_P = 4 - 15 tau2 = 1.5, x_c0 = x_P - 60 tau2 = -8.5 km < 0 km
    assert close(c.last_eval["x_c0"], -8.5)


def test_isolated_jam_activates_then_deactivates():
    c = Specialist(DET_X, SEGS, m_t_km=0.25)
    q, v = free_data()
    q[4], v[4] = 800.0, 20.0                                  # jam at 4000 m, neighbours free 1800 veh/h/lane, 90 km/h
    t0 = 600.0
    # hand computation (km, h): rho1 = rho6 = 20, rho2 = 20 + (800-1800)/(-15) = 86.667, q3 = 60*20 = 1200
    w12, w23 = -15.0, (800.0 - 1200.0) / (86.6666667 - 20.0)  # -6 km/h
    x_h0, x_t0 = 4.0, 3.75
    tau2 = (x_h0 - x_t0) / (w23 - w12)                        # 1/36 h = 100 s
    x_P = x_h0 + w12 * tau2
    x_c0 = x_P - 60.0 * tau2                                  # 3|4 front moves at V = 60 km/h
    w64 = (1800.0 - 60.0 * 33.0) / (20.0 - 33.0)              # +13.846 km/h
    w45 = (60.0 * 33.0 - 2033.3) / (33.0 - 26.0)              # -7.614 km/h
    # 6|4 meets 4|5:  x_c0 + w64 s = x_P + w45 (s - tau2)
    s4 = (x_P - x_c0 - w45 * tau2) / (w64 - w45)
    assert close(tau2 * 3600.0, 100.0, 1e-5) and close(s4 * 3600.0, 315.06, 1e-4)

    b = c.step(t0, q, v)
    assert c.active and c.n_detected == 1 and c.n_solvable == 1
    assert close(c.scheme["x_c0"], x_c0, 1e-5) and close(c.scheme["x_P"], x_P, 1e-5)
    assert close((c.scheme["t_end_h"] * 3600.0 - t0), s4 * 3600.0, 1e-5)
    assert b == [1.0, 0.5, 0.5, 0.5, 0.5]                     # [x_c0 = 1.917, x_h0 = 4.0] km

    fq, fv = free_data()                                      # new data ignored while the scheme is active
    assert c.step(t0 + 60.0, fq, fv) == [1.0, 1.0, 0.5, 0.5, 0.5]    # [2.147, 3.750]
    assert c.step(t0 + 120.0, fq, fv) == [1.0, 1.0, 0.5, 0.5, 0.5]   # area 4 only: [2.378, 3.541]
    assert c.step(t0 + 300.0, fq, fv) == [1.0, 1.0, 1.0, 0.5, 1.0]   # [3.071, 3.160]
    assert c.active and c.n_detected == 1
    assert c.step(t0 + 360.0, fq, fv) == [1.0] * 5            # 360 s > 315 s: areas 2-4 in the past
    assert not c.active and c.n_finished == 1 and c.last_reason == "no_shock_wave"


def test_front_speeds_match_front_rule():
    # synthetic states: 6 = (1900, 100 km/h), 1 = (1700, 85 km/h), q2 = 600; V = 60, rho4 = 33, (q5, rho5) = (2033.3, 26)
    rho6, rho1 = 1900.0 / 100.0, 1700.0 / 85.0               # 19, 20
    rho2 = 20.0 + (600.0 - 1700.0) / (-15.0)                  # 93.333
    hand = {
        "12": (1700.0 - 600.0) / (20.0 - 93.3333333),         # -15
        "62": (1900.0 - 600.0) / (19.0 - 93.3333333),         # -17.489
        "23": (600.0 - 1140.0) / (93.3333333 - 19.0),         # -7.265
        "34": (1140.0 - 1980.0) / (19.0 - 33.0),              # 60
        "64": (1900.0 - 1980.0) / (19.0 - 33.0),              # 5.714
        "45": (1980.0 - 2033.3) / (33.0 - 26.0),              # -7.614
        "15": (1700.0 - 2033.3) / (20.0 - 26.0),              # 55.55
    }
    sw = scheme_states(1700.0, rho1, 600.0, 1900.0, rho6, v_eff=60.0, v12=-15.0, rho4=33.0, q5=2033.3, rho5=26.0)
    assert close(sw["states"][2][1], rho2)
    for ab, val in hand.items():
        assert close(sw["w"][ab], val, 1e-6), (ab, sw["w"][ab], val)
    # end to end: same states estimated from detector data
    c = Specialist(DET_X, SEGS, m_t_km=0.25)
    q = [1900.0, 1900.0, 1900.0, 1900.0, 600.0, 1700.0]
    v = [100.0, 100.0, 100.0, 100.0, 10.0, 85.0]
    c.step(0.0, q, v)
    for ab, val in hand.items():
        assert close(c.last_eval["w"][ab], val, 1e-6), (ab, c.last_eval["w"][ab], val)
    # P2 p.1774 option: state 4 at speed V on the 1-2 line -> rho4 = (q1 - v12 rho1) / (V - v12) = 2000 / 75
    sw2 = scheme_states(1700.0, rho1, 600.0, 1900.0, rho6, v_eff=60.0, v12=-15.0, rho4=None, q5=2033.3, rho5=26.0)
    q4, r4 = sw2["states"][4]
    assert close(r4, 2000.0 / 75.0) and close(q4, 1700.0 - 15.0 * (r4 - 20.0))
    assert math.isnan(front_speed(1.0, 5.0, 2.0, 5.0))


def test_unsolvable_cases_return_ones():
    # (a) the downstream detector is congested too: no free downstream state 1
    c = Specialist(DET_X, SEGS, m_t_km=0.25)
    q, v = free_data()
    q[4], v[4], q[5], v[5] = 800.0, 20.0, 900.0, 25.0
    assert c.step(0.0, q, v) == [1.0] * 5
    assert not c.active and c.n_unsolvable == 1 and "no_downstream_free_detector" in c.last_reason
    # (b) upstream speed 55 km/h: not a jam (> v_max) but not above the 60 km/h limit
    c = Specialist(DET_X, SEGS, m_t_km=0.25)
    q, v = [1800.0] * 4 + [800.0, 1800.0], [55.0] * 4 + [20.0, 90.0]
    assert c.step(0.0, q, v) == [1.0] * 5
    assert not c.active and "v6_not_above_limit" in c.last_reason
    # (c) inflow 2100 veh/h/lane > q5: area 4 grows upstream faster than it discharges (w64 = -10 < w45 = -7.6)
    c = Specialist(DET_X, SEGS, m_t_km=0.25)
    q, v = [2100.0] * 4 + [800.0, 1800.0], [100.0] * 4 + [20.0, 90.0]
    assert c.step(0.0, q, v) == [1.0] * 5
    assert not c.active and "area4_not_converging" in c.last_reason
    assert close(c.last_eval["w"]["64"], -10.0)


def test_lane_scaling_downstream_two_lane_detector():
    c = Specialist(DET_X, SEGS, m_t_km=0.25, det_lanes=[3, 3, 3, 3, 3, 2])
    q, v = free_data()
    q[4], v[4] = 800.0, 20.0
    c.step(0.0, q, v)
    q1, rho1 = c.last_eval["states"][1]
    assert close(q1, 1200.0) and close(rho1, 1200.0 / 90.0)    # 2 lanes x 1800 = 3600 veh/h = 1200 per reference lane
