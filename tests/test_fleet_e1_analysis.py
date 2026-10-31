"""E1 stage-0 rules (V213 §9.3-9.4, §10.3) on synthetic numbers."""
import numpy as np
import pytest

from v5b.fleet import e1_analysis as ea


def test_s_upper_factor():
    assert ea.s_upper(1.0) == pytest.approx(1.2934, abs=1e-4)


def test_power_and_n_choice():
    assert ea.p_pass(10, 0.15, 0.05, r=400) > 0.95
    assert ea.p_pass(10, 0.0, 0.05, r=400) < 0.05
    assert ea.p_pass(20, 0.10, 0.01, r=400) == pytest.approx(0.5, abs=0.1)      # the point must reach 0.10
    assert ea.choose_n(0.05)["n"] == 10
    big = ea.choose_n(0.11)
    assert big["n"] in (15, 20)
    assert ea.choose_n(0.30)["n"] is None


def test_noise_floors_match_the_protocol_precomputation():
    f = ea.noise_floors(0.10, 10, r=800)
    assert f["phi_O"] == pytest.approx(0.115, abs=0.01) and f["phi_T"] == pytest.approx(0.038, abs=0.01)
    assert f["rule1_c2_budgeted"] and not f["rule2_tuned_replicate"]


def _ser(speeds, t0=0.0):
    """day.py series rows with field 7 = drop speed, exit count 25 per 30 s."""
    return [(t0 + 30.0 * (i + 1), 25, None, 0, 0, None, None, v, None) for i, v in enumerate(speeds)]


def test_drop_onset_after_noon():
    sp = [27.0] * 1400 + [10.0] * 10 + [27.0] * 40 + [10.0] * 20 + [27.0] * 30
    t_b = ea.drop_onset(_ser(sp))
    assert t_b == pytest.approx(30.0 * 1451)              # the 11:40 episode is before noon and skipped
    assert ea.drop_onset(_ser([27.0] * 100 + [10.0] * 10 + [27.0] * 20)) is None


def test_ocr_day_takes_the_peak_flow_window():
    t = np.arange(30.0, 7230.0, 30.0)
    q = np.full(t.size, 3000.0)
    o = np.full(t.size, 10.0)
    k = (t > 5000) & (t <= 5300)
    q[k], o[k] = 3600.0, 17.0
    assert ea.ocr_day(t, q, o, 6000.0, []) == pytest.approx(17.0)
    assert ea.ocr_day(t, q, o, 6000.0, [(4900.0, 4950.0)]) == pytest.approx(10.0)   # 10 min after an episode


def test_lead_and_spill():
    t = np.arange(30.0, 14430.0, 30.0)
    o = np.full(t.size, 10.0)
    o[t >= 9900] = 30.0
    assert ea.lead_ok(t, o, 20.0, 10000.0)
    assert not ea.lead_ok(t, o, 20.0, 11000.0)            # crossed 18 min before the onset
    late = np.full(t.size, 10.0)
    late[t >= 11500] = 30.0
    assert ea.spill_ok(t, late, 20.0, 10000.0) and not ea.lead_ok(t, late, 20.0, 10000.0)
