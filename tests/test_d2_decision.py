"""Screen D2 Rules 1 and 5 on synthetic numbers: HD_f = (f - OR) / f against every fallback, the invalid-seed
check, CONTINUE / STOP, and the T0, T1 and T4 logic."""
import numpy as np
import pytest

from v5b.d2 import run_screen as rs
from v5b.d2 import stats


def _rng(k=0):
    return np.random.default_rng(3000 + k)


def _cell(gains, n=50, k=0):
    """OR delays ~ 300 s; fallback f = OR / (1 - gain_f) + small noise, so HD_f ~ gain_f."""
    r = _rng(k)
    o = 300.0 + r.normal(0, 10, n)
    return o, {a: o / (1.0 - g) + r.normal(0, 2, n) for a, g in gains.items()}


def test_hd_formula_is_relative_to_the_fallback():
    o = np.array([90.0, 80.0, 70.0])
    f = np.array([100.0, 100.0, 100.0])
    c = stats.headroom_cell(o, {"FX": f, "FB": f, "IP": f})
    assert c["per_fallback"]["FX"]["HD"] == pytest.approx(20.0 / 100.0)   # median(f - OR) / median(f)


def test_pass_needs_every_fallback():
    o, fb = _cell({"FX": 0.25, "FB": 0.20, "IP": 0.15})
    assert stats.headroom_cell(o, fb)["pass"]
    o, fb = _cell({"FX": 0.25, "FB": 0.20, "IP": 0.05})
    c = stats.headroom_cell(o, fb)
    assert not c["pass"] and c["binding"] == "IP"
    o, fb = _cell({"FX": 0.25, "FB": 0.20, "IP": 0.10}, n=50)
    c = stats.headroom_cell(o, fb)                               # HD ~ 10 %: passes only if the point estimate >= 10 %
    assert c["per_fallback"]["IP"]["pass"] == (c["per_fallback"]["IP"]["HD"] >= 0.10)


def test_ci_lower_bound_must_exceed_zero():
    r = _rng(5)
    o = r.normal(300, 80, 12)
    f = o * 1.2 + r.normal(0, 200, 12)                           # large median gain, very noisy
    c = stats.headroom_cell(o, {"FX": f, "FB": f, "IP": f})
    p = c["per_fallback"]["FX"]
    assert p["pass"] == (p["HD"] >= 0.10 and p["HD_ci"][0] > 0.0)


def test_invalid_seed_check():
    o, fb = _cell({"FX": 0.3, "FB": 0.3, "IP": 0.3}, n=20)
    inv = [False] * 20
    c = stats.cell_with_invalid_check(o, fb, inv)
    assert c["pass"] and c["pass_valid_only"] and c["n_invalid_seeds"] == 0
    o2 = o.copy()
    fb2 = {a: v.copy() for a, v in fb.items()}
    for i in range(16):                                         # the gain lives only on invalid seeds
        fb2["IP"][i] = o2[i] * 1.5
    for i in range(16, 20):
        fb2["IP"][i] = o2[i]
    inv = [i < 16 for i in range(20)]
    c = stats.cell_with_invalid_check(o2, fb2, inv)
    assert c["pass_all_seeds"] and not c["pass_valid_only"] and not c["pass"]
    assert not stats.cell_with_invalid_check(o, fb, [True] * 20)["pass"]


def test_decide():
    o, good = _cell({"FX": 0.3, "FB": 0.3, "IP": 0.3})
    o2, bad = _cell({"FX": 0.3, "FB": 0.3, "IP": 0.0}, k=1)
    g = stats.cell_with_invalid_check(o, good, [False] * 50)
    b = stats.cell_with_invalid_check(o2, bad, [False] * 50)
    assert stats.decide({"slow_q1600": b, "block_q2000": g}) == "CONTINUE"
    assert stats.decide({"slow_q1600": b, "block_q2000": b}) == "STOP"
    assert stats.decide({"x": {"n": 0, "pass": False}}) == "STOP"


def test_t4_logic():
    r = _rng(7)
    n = 400.0 + r.normal(0, 20, 20)
    c = stats.t4_cell(n, n * 0.85, "c1600", "c800")              # incident changes what is best by 15 %
    assert c["pass"] and c["rel"] == pytest.approx(0.15, abs=0.02)
    c = stats.t4_cell(n, n * 0.95, "c1600", "c800")              # only 5 %
    assert not c["pass"]
    c = stats.t4_cell(n, n, "c1600", "c1600")                    # the incident-best is N itself
    assert not c["pass"] and c["same_controller"]
    cells = {"slow_q1600": stats.t4_cell(n, n * 0.95, "a", "b"), "block_q2000": stats.t4_cell(n, n * 0.8, "a", "b")}
    assert stats.t4_overall(cells)["pass"] and stats.t4_overall(cells)["n_pass"] == 1
    cells["block_q2000"] = stats.t4_cell(n, n, "a", "a")
    assert not stats.t4_overall(cells)["pass"]


def test_t0_every_cell_and_t1_per_cell():
    r = _rng(9)
    nc = 600.0 + r.normal(0, 20, 20)
    best = {"a": nc * 0.7, "b": nc * 0.95}
    t0 = stats.t0_cells(best, {"a": nc, "b": nc}, {"a": "OR", "b": "FX"})
    assert t0["cells"]["a"]["pass"] and not t0["cells"]["b"]["pass"] and not t0["pass"]
    assert stats.t0_cells({"a": nc * 0.7}, {"a": nc}, {"a": "OR"})["pass"]
    t1 = stats.t1_cells({"slow_q1600": [0] * 99 + [1], "block_q2000": [0] * 90 + [2] * 10})
    assert t1["cells"]["slow_q1600"]["pass"] and not t1["cells"]["block_q2000"]["pass"] and not t1["pass"]


def test_tcheck_decision_text():
    tc = {"T3_pass": True, "T0": {"pass": True}, "T1": {"pass": True}, "T4": {"pass": False}}
    assert rs.tcheck_decision(tc) == "STOP (tool check T4)"
    tc["T1"]["pass"] = False
    assert rs.tcheck_decision(tc).startswith("STOP (tool check T1, T4; T1:")
    tc["T3_pass"] = False
    assert rs.tcheck_decision(tc).startswith("FIX CODE")
