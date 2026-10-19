"""Screen D1 Rules 1 and 5 on synthetic numbers (no SUMO)."""
import numpy as np
import pytest

from v5b.d1 import stats


def _rng(k=0):
    return np.random.default_rng(1000 + k)


def test_paired_definition():
    r = stats.paired([10, 20, 30], [5, 10, 15])
    assert r["med_diff"] == 10.0 and r["rel"] == pytest.approx(0.5) and r["n"] == 3


def test_continue_when_clear_headroom():
    o = 100 + _rng(1).normal(0, 3, 50)
    fx, rf = o + 30 + _rng(2).normal(0, 3, 50), o + 40
    c = stats.headroom_cell(o, fx, rf)
    assert c["best"] == "FX" and c["HF"] == pytest.approx(30 / 130, abs=0.02)
    assert c["pass"] and c["HF_ci"][0] > 0.1
    assert stats.decide({"a": c}) == "CONTINUE"


def test_stop_when_headroom_below_10pct():
    o = 100 + _rng(3).normal(0, 1, 50)
    c = stats.headroom_cell(o, o + 5, o + 6)
    assert not c["pass"] and c["HF_ci"][0] > 0          # significant but small
    assert stats.decide({"a": c, "b": dict(c)}) == "STOP"


def test_stop_when_ci_includes_zero_despite_point_estimate():
    best = np.full(5, 100.0)
    o = np.array([150.0, 140.0, 85.0, 80.0, 70.0])      # d = -50, -40, 15, 20, 30: median 15 -> HF 15 %
    c = stats.headroom_cell(o, best, best + 50)
    assert c["HF"] == pytest.approx(0.15) and c["HF_ci"][0] <= 0 and not c["pass"]


def test_best_of_picks_lower_median_rf():
    o = np.full(20, 100.0) + _rng(4).normal(0, 1, 20)
    c = stats.headroom_cell(o, o + 50, o + 20)
    assert c["best"] == "RF" and c["HF"] == pytest.approx(20 / 120, abs=0.01)


def test_t0_rule():
    nc = 300 + _rng(5).normal(0, 10, 20)
    assert stats.t0_check(nc * 0.6, nc)["pass"]
    assert not stats.t0_check(nc * 0.95, nc)["pass"]     # 5 % < 10 %


def test_t1_rule_strictly_below_5pct():
    assert stats.t1_check([0] * 20)["pass"]
    assert not stats.t1_check([1] + [0] * 19)["pass"]    # 1/20 = 5 % is not < 5 %
    assert stats.t1_check([2] + [0] * 39)["pass"]        # 1/40 = 2.5 %


def test_fx_best_rate_tie_takes_lower_rate():
    assert stats.best_rate({800.0: 50.0, 1000.0: 40.0, 1200.0: 40.0}) == 1000.0


def test_bootstrap_is_deterministic():
    x, y = _rng(6).normal(100, 10, 30), _rng(7).normal(90, 10, 30)
    assert stats.paired(x, y) == stats.paired(x, y)
