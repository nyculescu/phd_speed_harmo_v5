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


def test_main_pm_breakdown_skips_blips_and_merges_gaps():
    # 13:00 a 2.5-min blip; 15:30 a 30-min episode, a 5-min recovery, then 60 more minutes (V215 A3)
    sp = [27.0] * 1560 + [10.0] * 5 + [27.0] * 295 + [10.0] * 60 + [27.0] * 10 + [10.0] * 120 + [27.0] * 30
    e = ea.main_pm(_ser(sp))
    assert e["t_break"] == pytest.approx(30.0 * 1861) and e["n_merged"] == 2
    assert e["min"] == pytest.approx(95.0, abs=2.5)
    assert ea.drop_onset(_ser(sp)) == e["t_break"]


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
    early = np.full(t.size, 10.0)
    early[t >= 10000 - 540] = 30.0                         # crossed 9 min before t_b, 15 % of the pre-hour above
    assert not ea.lead_ok(t, early, 20.0, 10000.0)


def test_tuned_oracle_edge_and_verdict():
    nc = np.full(10, 100.0)
    pts = {"ma/p0.85": np.full(10, 95.0), "ma/p0.95": np.full(10, 97.0), "ma/p1.05": np.full(10, 99.0),
           "c/p0.85_short": np.full(10, 96.0), "c/p0.95_short": np.full(10, 95.95)}
    assert ea.tuned(nc, pts, ("ma", "mp")) == "ma/p0.85"
    assert ea.tuned(nc, pts, ("c",)) == "c/p0.95_short"          # within 0.1 s/veh: the middle setpoint wins
    pts2 = dict(pts, **{"ma/p0.95": np.r_[np.full(5, 80.0), np.full(5, 101.0)]})
    d, pick = ea.o_off(nc, pts2)
    assert d.max() <= 100.0 and pick[0] == "ma/p0.95" and pick[9] == "ma/p0.85"
    d3, pick3 = ea.o_off(nc, {"x/p": np.full(10, 101.0)})
    assert (d3 == 100.0).all() and set(pick3) == {"nc"}
    assert ea.edge_fires(nc, pts, "ma/p0.85", False) == 0.75
    assert ea.edge_fires(nc, pts, "ma/p0.85", True) is None
    up = dict(pts, **{"ma/p1.05": np.full(10, 90.0)})
    assert ea.edge_fires(nc, up, "ma/p1.05", False) == 1.15
    base = {"P_T": False, "P_O": False, "F": [], "powered": True}
    assert ea.verdict({"R": base, "I": base})["verdict"] == "KILL"
    assert ea.verdict({"R": base, "I": dict(base, P_O=True)})["verdict"] == "I-ONLY"
    assert ea.verdict({"R": dict(base, F=["x"]), "I": base})["kill_label"] == "powered"
    assert ea.verdict({"R": dict(base, P_O=True), "I": dict(base, P_T=True)})["verdict"] == "CONTINUE-O"
    assert ea.verdict({"R": base, "I": dict(base, powered=False)})["kill_label"] == "underpowered: I"


def test_safety_and_conflict_rules():
    assert ea.intrusion_flag(5, 0)["flag"] and not ea.intrusion_flag(4, 0)["flag"]
    assert ea.intrusion_flag(5, 0)["p"] == pytest.approx(1 / 32)
    nc = np.full(10, 10000.0)
    assert ea.throughput_loss(nc, nc - 200.0) and not ea.throughput_loss(nc, nc - 50.0)
    assert ea.ttt_conflict(np.full(10, 100.0), np.full(10, 110.0))
    assert ea.harm_label(ea.effect(np.full(10, 100.0), np.full(10, 106.0))) == "clearly worse"
    assert ea.harm_label(ea.effect(np.full(10, 100.0), np.full(10, 103.0))) == "no harm"
    mixed = np.r_[np.full(5, 92.0), np.full(5, 110.0)]
    assert ea.harm_label(ea.effect(np.full(10, 100.0), mixed)) == "harm not excluded"


def test_global_null_procedure():
    g = ea.global_null(0.02, 10, False, r=200)
    assert g["p_continue_cell"] == 0.0
    h = ea.global_null(0.25, 10, False, r=200)
    assert h["p_continue_cell"] > 0.1 and h["p_continue_either_cell"] >= h["p_continue_cell"]
    assert ea.global_null(0.25, 10, True, r=200)["p_tuned"] <= h["p_tuned"]       # Rule 2 only removes passes
