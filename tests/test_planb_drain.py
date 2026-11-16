"""Plan B G4(ii)(a,b) (V486) on planted rows; the realised placebo as a regression."""
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "analysis/planb"))
import drain as drain_rule  # noqa: E402

ROWS = Path("/home/catalin/work/phd/v5b1_runs/planb_remote/s2/s2_runs.jsonl")
SEEDS = list(drain_rule.GATE_SEEDS)
N = len(SEEDS)
# Fractional base values make float summation inexact, as real window means do.
BASE = np.arange(N) / 300.0


def world(value=BASE):
    return {a: {k: np.array(value, float) for k in drain_rule.KEYS} for a in drain_rule.ARMS}


def with_change(arm, key, series):
    C = world()
    C[arm][key] = np.array(series, float)
    return C


def report(D, C, S, **kw):
    return D.drain_report(C, S, SEEDS, SEEDS, C, S, **{"surge": False, **kw})


def flat(x):
    return [0.0] * 20 + [x] * 5


def varied(first, last):
    return [0.0] * 20 + [first, 0.0, 0.0, 0.0, last]


def row(q1, q2, p1, p2, main, seed=1, make=flat):
    return {"seed": seed, "m_main_pending_min": make(main),
            "m_minute": {"ramp1_queue": make(q1), "ramp2_queue": make(q2), "ramp1_pending": make(p1), "ramp2_pending": make(p2)}}


def test_no_excess_passes(D=drain_rule):
    r = D.drain_test(world(), world(), SEEDS, SEEDS)
    assert r["pass"] and all(v == 0 for v in r["excess"].values())


def test_exactly_at_limit_passes(D=drain_rule):
    r = D.drain_test(world(BASE + 2.0), world(), SEEDS, SEEDS)
    assert r["pass"]
    assert all(v == 2.0 for v in r["excess"].values())


def test_at_limit_survives_float_summation(D=drain_rule):
    # The exact mean is 2, and unrounded float summation lands just above it.
    rng = np.random.default_rng(1)
    for _ in range(200):
        a = rng.integers(0, 3000, N)
        e = rng.integers(-900, 900, N)
        e[-1] -= e.sum()
        s, c = a / 300.0, (a + 600 + e) / 300.0
        if float(np.mean(c - s)) > 2.0:
            break
    else:
        pytest.fail("no float-error case found")
    assert D.drain_test(world(c), world(s), SEEDS, SEEDS)["pass"]


def test_just_over_limit_fails(D=drain_rule):
    for over in (2.0004, 2.01):
        assert not D.drain_test(world(BASE + over), world(), SEEDS, SEEDS)["pass"], over


def test_every_arm_and_key_can_fail_alone(D=drain_rule):
    for a in drain_rule.ARMS:
        for k in drain_rule.KEYS:
            r = D.drain_test(with_change(a, k, BASE + 3.0), world(), SEEDS, SEEDS)
            assert not r["pass"], (a, k)
            assert r["excess"][f"{a}|{k}"] == pytest.approx(3.0)


def test_each_queue_has_its_own_limit(D=drain_rule):
    # Three queues at 1.99 add to about 6 vehicles and pass, because each is read alone.
    assert D.drain_test(world(BASE + 1.99), world(), SEEDS, SEEDS)["pass"]


def test_absolute_margin_not_a_ratio(D=drain_rule):
    # A median of 0.015 with +1.5 vehicles is 100 times S's value, and it must pass.
    s = np.full(N, 0.015)
    S = world(s)
    assert D.drain_test(world(s + 1.5), S, SEEDS, SEEDS)["pass"]


def test_tail_seen_by_mean_median_flat(D=drain_rule):
    # 4 of 40 seeds at +30: paired median 0, mean +3.
    x = BASE.copy()
    x[:4] += 30.0
    C = with_change("p333", "ramp2_queue", x)
    r = D.drain_test(C, world(), SEEDS, SEEDS)
    assert np.median(x - BASE) == 0
    assert not r["pass"]
    assert r["excess"]["p333|ramp2_queue"] == pytest.approx(3.0)


def test_one_large_seed_within_mean_budget_passes(D=drain_rule):
    # +80 on one seed is +2.0 on the mean; a seed-count or maximum rule would fail it.
    x = BASE.copy()
    x[7] += 80.0
    assert D.drain_test(with_change("nc", "backlog", x), world(), SEEDS, SEEDS)["pass"]


def test_every_seed_counts_in_the_mean(D=drain_rule):
    # One seed carries the whole excess; dropping or trimming it would hide it.
    for pos in (0, N - 1):
        x = BASE.copy()
        x[pos] += 100.0
        r = D.drain_test(with_change("nc", "ramp1_queue", x), world(), SEEDS, SEEDS)
        assert not r["pass"], pos
        assert r["excess"]["nc|ramp1_queue"] == pytest.approx(2.5)


def test_mean_of_differences_not_mixed_with_median(D=drain_rule):
    s = np.r_[np.full(30, 1.0), np.full(10, 9.0)]
    S = world(s)
    # Mean excess 0: the mean of S is 3, its median 1.
    r = D.drain_test(world(s), S, SEEDS, SEEDS)
    assert r["excess"]["nc|backlog"] == 0.0 and r["pass"]


def test_lower_cell_passes(D=drain_rule):
    # A large negative excess must not be read as a large excess.
    assert D.drain_test(world(BASE - 10.0), world(), SEEDS, SEEDS)["pass"]


def test_seed_order_mismatch_raises(D=drain_rule):
    with pytest.raises(ValueError):
        D.drain_test(world(), world(), SEEDS, SEEDS[::-1])


def test_steady_seeds_checked_too(D=drain_rule):
    with pytest.raises(ValueError):
        D.drain_test(world(), world(), SEEDS[::-1], SEEDS)
    with pytest.raises(ValueError):
        D.drain_test(world(), world(), SEEDS, SEEDS[:-1] + [9])


def test_duplicate_seed_raises(D=drain_rule):
    dup = SEEDS[:-1] + [SEEDS[0]]
    with pytest.raises(ValueError):
        D.drain_test(world(), world(), dup, dup)


def test_too_few_seeds_raises(D=drain_rule):
    five = SEEDS[:5]
    short = {a: {k: np.zeros(5) for k in drain_rule.KEYS} for a in drain_rule.ARMS}
    with pytest.raises(ValueError):
        D.drain_test(short, short, five, five)


def test_other_seed_block_raises(D=drain_rule):
    other = list(range(N))
    with pytest.raises(ValueError):
        D.drain_test(world(), world(), other, other)


def test_report_checks_seeds(D=drain_rule):
    with pytest.raises(ValueError):
        D.drain_report(world(), world(), SEEDS[::-1], SEEDS, world(), world(), surge=False, b=100)
    with pytest.raises(ValueError):
        D.drain_report(world(), world(), SEEDS, SEEDS[::-1], world(), world(), surge=False, b=100)


def test_length_mismatch_raises(D=drain_rule):
    C = world()
    # One value would broadcast silently against 40 without the shape check.
    C["p333"]["backlog"] = np.array([0.0])
    with pytest.raises(ValueError):
        D.drain_test(C, world(), SEEDS, SEEDS)


def test_nan_raises(D=drain_rule):
    x = BASE.copy()
    x[3] = np.nan
    with pytest.raises(ValueError):
        D.drain_test(with_change("nc", "ramp1_queue", x), world(), SEEDS, SEEDS)


def test_missing_arm_raises(D=drain_rule):
    C = world()
    del C["p333"]
    with pytest.raises(KeyError):
        D.drain_test(C, world(), SEEDS, SEEDS)


def test_verdict_ignores_precision(D=drain_rule):
    # Mean excess under 2 with an upper limit above 2: the verdict stays pass.
    d = np.where(np.arange(N) % 2 == 0, 9.9, -6.1)
    C = with_change("nc", "backlog", BASE + d)
    S = world()
    r = D.drain_test(C, S, SEEDS, SEEDS)
    rep = report(D, C, S, b=2000)
    assert r["pass"]
    assert rep["nc|backlog"]["ci95"][1] > 2.0


def test_report_counts_and_largest(D=drain_rule):
    x = BASE.copy()
    x[:3] += 7.0
    x[3:5] += 12.0
    x[5] += 20.0
    rep = report(D, with_change("p333", "backlog", x), world(), b=500)
    r = rep["p333|backlog"]
    assert r["n_seeds_over"] == {5.0: 6, 10.0: 3, 15.0: 1}
    assert r["largest_excess"] == pytest.approx(20.0)


def test_report_mean_and_median_differ(D=drain_rule):
    # 10 of 40 seeds at +4: mean excess 1, median paired excess 0.
    d = np.r_[np.full(10, 4.0), np.zeros(N - 10)]
    r = report(D, with_change("nc", "ramp2_queue", BASE + d), world(), b=500)["nc|ramp2_queue"]
    assert r["mean_excess"] == pytest.approx(1.0)
    assert r["median_paired_excess"] == pytest.approx(0.0)


def test_report_keeps_old_rule_on_skewed_series(D=drain_rule):
    # S has median 1 and mean 3, so a limit built on S's mean would be 3.3.
    s = np.r_[np.full(30, 1.0), np.full(10, 9.0)]
    S = world(s)
    above = np.r_[np.full(30, 1.15), np.full(10, 9.0)]
    r = report(D, world(above), S, b=500)["nc|ramp2_queue"]
    assert r["old_cell_median"] == pytest.approx(1.15)
    assert r["old_limit"] == pytest.approx(1.1)
    assert not r["old_pass"]
    within = np.r_[np.full(30, 1.05), np.full(10, 9.0)]
    r2 = report(D, world(within), S, b=500)["nc|ramp2_queue"]
    assert r2["old_cell_median"] == pytest.approx(1.05)
    # The mean of this series is 3, above the limit, and the registered form used the median.
    assert r2["old_pass"]


def test_report_surge_clause_backlog_only(D=drain_rule):
    s = np.full(N, 1.0)
    c = np.full(N, 1.05)
    S = world(s)
    C = world(c)
    assert report(D, C, S, b=500)["nc|backlog"]["old_pass"]
    surge = report(D, C, S, surge=True, b=500)
    assert not surge["nc|backlog"]["old_pass"]
    assert surge["nc|ramp2_queue"]["old_pass"]
    assert surge["nc|backlog"]["old_limit"] == pytest.approx(1.0)


def test_report_ci_is_95_percentile_of_means(D=drain_rule):
    d = np.arange(N, dtype=float)
    rep = report(D, with_change("nc", "ramp1_queue", BASE + d), world(), b=8000, seed=3)
    low, up = rep["nc|ramp1_queue"]["ci95"]
    assert low < d.mean() < up
    # The width is 2 * 1.96 * 11.54 / sqrt(40) = 7.15; a 90 % interval would be 6.0.
    assert 6.7 < up - low < 7.6


def test_report_last_minute_excess_and_sign(D=drain_rule):
    C, S = world(), world()
    lc = world(np.full(N, 2.5))
    ls = world(np.full(N, 1.0))
    r = D.drain_report(C, S, SEEDS, SEEDS, lc, ls, surge=False, b=200)
    for a in drain_rule.ARMS:
        for k in drain_rule.KEYS:
            assert r[f"{a}|{k}"]["last_minute_mean_excess"] == pytest.approx(1.5), (a, k)
            assert r[f"{a}|{k}"]["mean_excess"] == pytest.approx(0.0)


def test_read_drain_reports_last_minute_row(D=drain_rule):
    def make_rows(first, last):
        out = {}
        for a in drain_rule.ARMS:
            out[a] = []
            for s in SEEDS:
                r = row(0.0, 0.0, 0.0, 0.0, 0.0, seed=s)
                r["m_minute"]["ramp2_queue"] = varied(first, last)
                out[a].append(r)
        return out
    out = D.read_drain(make_rows(300.0, 600.0), make_rows(300.0, 300.0), surge=False, b=200)
    r = out["report"]["nc|ramp2_queue"]
    # Last minute 600 against 300 vehicle-seconds is +5 vehicles; over five minutes it is +1.
    assert r["last_minute_mean_excess"] == pytest.approx(5.0)
    assert r["mean_excess"] == pytest.approx(1.0)
    assert out["verdict"]["pass"]


def test_read_drain_verdict_can_fail(D=drain_rule):
    make_rows = lambda x: {a: [row(x, x, x, x, x, seed=s) for s in SEEDS] for a in drain_rule.ARMS}
    out = D.read_drain(make_rows(240.0), make_rows(60.0), surge=False, b=200)
    assert not out["verdict"]["pass"]
    assert out["verdict"]["excess"]["p333|ramp1_queue"] == pytest.approx(3.0)


def test_read_drain_surge_flag(D=drain_rule):
    make_rows = lambda x: {a: [row(x, x, x, x, x, seed=s) for s in SEEDS] for a in drain_rule.ARMS}
    # Backlog 3.15 against 3.0: within +10 %, above zero margin.
    cell, steady = make_rows(63.0), make_rows(60.0)
    assert D.read_drain(cell, steady, surge=False, b=200)["report"]["nc|backlog"]["old_pass"]
    assert not D.read_drain(cell, steady, surge=True, b=200)["report"]["nc|backlog"]["old_pass"]


def test_arms_with_different_seeds_raise(D=drain_rule):
    rows = {"nc": [row(0, 0, 0, 0, 0, seed=s) for s in SEEDS], "p333": [row(0, 0, 0, 0, 0, seed=s) for s in SEEDS[::-1]]}
    with pytest.raises(ValueError):
        D.series_from_rows(rows)


def test_row_adapter_units_and_window(D=drain_rule):
    r = row(q1=60.0, q2=120.0, p1=30.0, p2=60.0, main=90.0)
    v = D.series_from_row(r)
    assert v == {"ramp1_queue": 1.0, "ramp2_queue": 2.0, "backlog": 3.0}


def test_row_adapter_first_and_last_minute_of_window(D=drain_rule):
    # Only minutes 20 and 24 carry a queue, so a window one minute short or shifted changes the value.
    r = row(q1=300.0, q2=300.0, p1=0.0, p2=0.0, main=0.0, make=lambda x: varied(x, 2 * x))
    v = D.series_from_row(r)
    assert v["ramp1_queue"] == pytest.approx(3.0)
    assert v["ramp2_queue"] == pytest.approx(3.0)
    r2 = row(q1=0.0, q2=0.0, p1=300.0, p2=0.0, main=0.0, make=lambda x: varied(x, 2 * x))
    assert D.series_from_row(r2)["backlog"] == pytest.approx(3.0)


def test_last_minute_constant_is_minute_24(D=drain_rule):
    r = row(q1=300.0, q2=300.0, p1=0.0, p2=0.0, main=0.0, make=lambda x: varied(x, 2 * x))
    assert D.series_from_row(r, D.LAST_MINUTE)["ramp2_queue"] == pytest.approx(10.0)


def test_row_adapter_ignores_minutes_outside_window(D=drain_rule):
    r = row(q1=0.0, q2=0.0, p1=0.0, p2=0.0, main=0.0)
    r["m_minute"]["ramp2_queue"][19] = 6000.0
    r["m_main_pending_min"][19] = 6000.0
    v = D.series_from_row(r)
    assert v["ramp2_queue"] == 0.0 and v["backlog"] == 0.0


@pytest.mark.skipif(not ROWS.exists(), reason="S2's rows are not on this machine")
def test_realised_placebo_regression(D=drain_rule):
    by = {}
    for line in open(ROWS):
        if line.startswith(('{"name": "S|', '{"name": "PLACEBO|')):     # the perturbed rows are never parsed
            r = json.loads(line)
            by.setdefault(r["name"], []).append(r)
    assert len(by) == 5
    get = lambda c: {a: sorted(by[f"{c}|{a}"], key=lambda r: r["seed"]) for a in drain_rule.ARMS}
    C, sc = D.series_from_rows(get("PLACEBO"))
    S, ss = D.series_from_rows(get("S"))
    r = D.drain_test(C, S, sc, ss)
    assert r["pass"]
    want = {"nc|ramp1_queue": -0.013, "nc|ramp2_queue": 0.056, "nc|backlog": 0.398, "p333|ramp1_queue": 0.0, "p333|ramp2_queue": 0.208, "p333|backlog": -0.075}
    assert r["excess"] == pytest.approx(want, abs=0.001)     # each arm against its own S rows


def test_surge_flag_is_required(D=drain_rule):
    make = {a: [row(0, 0, 0, 0, 0, seed=s) for s in SEEDS] for a in drain_rule.ARMS}
    with pytest.raises(TypeError):
        D.read_drain(make, make, b=100)
    with pytest.raises(TypeError):
        D.drain_report(world(), world(), SEEDS, SEEDS, world(), world(), b=100)


def test_results_store_as_json(D=drain_rule):
    make = {a: [row(0, 0, 0, 0, 0, seed=s) for s in SEEDS] for a in drain_rule.ARMS}
    assert json.loads(json.dumps(D.read_drain(make, make, surge=False, b=100)))["verdict"]["pass"] is True


def test_nan_in_steady_raises(D=drain_rule):
    S = world()
    S["nc"]["backlog"] = BASE.copy()
    S["nc"]["backlog"][3] = np.nan
    with pytest.raises(ValueError):
        D.drain_test(world(), S, SEEDS, SEEDS)


def test_limit_argument_and_precision(D=drain_rule):
    r = D.drain_test(world(BASE + 1.5), world(), SEEDS, SEEDS, limit=1.0)
    assert not r["pass"] and r["limit"] == 1.0 and r["n"] == 40
    assert not D.drain_test(world(BASE + 2.0000001), world(), SEEDS, SEEDS)["pass"]     # rounding spares float noise only


def test_report_ci_is_the_percentile_bootstrap_of_the_mean(D=drain_rule):
    d = np.arange(N, dtype=float) ** 1.5
    rep = report(D, with_change("nc", "ramp1_queue", BASE + d), world(), b=3000, seed=11)["nc|ramp1_queue"]
    rng = np.random.default_rng(11)
    m = d[rng.integers(0, N, (3000, N))].mean(axis=1)
    assert rep["ci95"] == pytest.approx((np.percentile(m, 2.5), np.percentile(m, 97.5)))
    other = report(D, with_change("nc", "ramp1_queue", BASE + d), world(), b=3000, seed=12)["nc|ramp1_queue"]
    assert other["ci95"] != rep["ci95"]     # the seed argument is used
    assert D.BOOT_B == 20_000


def test_report_last_minute_is_a_mean_of_differences(D=drain_rule):
    x = np.r_[np.full(30, 0.0), np.full(10, 8.0)]
    lc, ls = world(x), world(np.zeros(N))
    r = D.drain_report(world(), world(), SEEDS, SEEDS, lc, ls, surge=False, b=100)["p333|backlog"]
    assert r["last_minute_mean_excess"] == pytest.approx(2.0)     # its median difference is 0


def test_report_edges(D=drain_rule):
    d = np.zeros(N)
    d[0], d[1] = 5.0, -30.0
    r = report(D, with_change("nc", "backlog", BASE + d), world(), b=100)["nc|backlog"]
    assert r["n_seeds_over"][5.0] == 0 and r["largest_excess"] == 5.0     # strictly above; signed, not absolute
    s = np.full(N, 1.0)
    at = report(D, world(s * 1.1), world(s), b=100)["nc|ramp2_queue"]
    assert at["old_pass"] and at["steady_median"] == 1.0     # the registered form allowed equality


def test_each_arm_is_paired_with_its_own_steady_rows(D=drain_rule):
    S, C = world(), world()
    S["p333"]["ramp2_queue"] = BASE + 3.0
    C["p333"]["ramp2_queue"] = BASE + 3.0     # equal to its own S: no excess, though 3 above S's no-control rows
    r = D.drain_test(C, S, SEEDS, SEEDS)
    assert r["pass"] and all(v == 0 for v in r["excess"].values())
