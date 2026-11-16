"""EV part 1 (v505_ev_informed_rule.md §2): sizing picks the mildest level that no control finds costly enough; the gate; T0."""
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis/v505"))
import read_ev as re_  # noqa: E402
import v5  # noqa: E402
from v5b2.fleet.v505 import slowdown_limit  # noqa: E402

Q = {"ramp1_queue": [60.0] * 30, "ramp2_queue": [60.0] * 30, "ramp1_pending": [0.0] * 30, "ramp2_pending": [0.0] * 30}


def row(d, queue=Q, stuck_n=0):
    return {"all_delay": d, "m_stuck_n": stuck_n, "m_minute": queue, "m_main_pending_min": [0.0] * 30}


def rows(stage, share, seed=3, stuck_lvl=()):
    """S at 200,000 veh-s; each level adds share[level] x S, with noise; p333 adds half as much."""
    rng = np.random.default_rng(seed)
    seeds = v5.seeds(stage)
    T = {("S", a): {s: row(200_000.0) for s in seeds} for a in ("nc", "p333")}
    for lv, sh in share.items():
        for a, f in (("nc", 1.0), ("p333", 0.5)):
            T[(f"EVA{lv:g}", a)] = {s: row(200_000.0 * (1 + f * sh) + rng.normal(0, 2_000), stuck_n=int(lv in stuck_lvl)) for s in seeds}
    return T, seeds


def test_size_takes_the_mildest_level_that_qualifies_on_no_control_alone():
    T, seeds = rows("ev_size", {30.0: 0.05, 20.0: 0.18, 15.0: 0.3, 10.0: 0.5})
    r = re_.size(T, seeds)
    assert r["limit_kmh"] == 20.0 and r["levels"]["20"]["p333"]["share"] < 0.15     # p333 below 15 % does not matter


def test_size_skips_a_level_with_stuck_rows_and_is_void_when_none_qualifies():
    T, seeds = rows("ev_size", {30.0: 0.05, 20.0: 0.18, 15.0: 0.3, 10.0: 0.5}, stuck_lvl=(20.0,))
    assert re_.size(T, seeds)["limit_kmh"] == 15.0
    T, seeds = rows("ev_size", {30.0: 0.01, 20.0: 0.05, 15.0: 0.08, 10.0: 0.12})
    assert re_.size(T, seeds)["outcome"] == "VOID"


def test_gate_needs_both_arms_ten_percent_above_s():
    T, seeds = rows("ev_gate", {20.0: 0.3})
    assert re_.gate(T, 20.0, seeds)["outcome"] == "pass"
    T, seeds = rows("ev_gate", {20.0: 0.15})     # p333 adds 7.5 %
    g = re_.gate(T, 20.0, seeds)
    assert g["outcome"] == "VOID" and g["arms"]["nc"]["g1a_pass"] and not g["arms"]["p333"]["g1a_pass"]


def test_gate_fails_on_drain():
    T, seeds = rows("ev_gate", {20.0: 0.3})
    long_q = {**Q, "ramp2_queue": [60.0] * 20 + [60.0 * 5] * 10}
    for s in seeds:
        T[("EVA20", "nc")][s]["m_minute"] = long_q
    assert re_.gate(T, 20.0, seeds)["outcome"] == "VOID"


def test_slowdown_limit_schedule_and_t0_check():
    spec = {"times": [500.0], "dur": 300.0, "taper": 20.0, "limit_kmh": 36.0}
    free = 27.78
    assert slowdown_limit(spec, 499.9, free) == free and abs(slowdown_limit(spec, 510.0, free) - (free + (10.0 - free) * 0.5)) < 1e-9
    assert slowdown_limit(spec, 530.0, free) == 10.0 and slowdown_limit(spec, 800.0, free) == free
    cfg = {"ctrl": {"env": {"perturb": {"limit_kmh": 36.0}}}}
    ok = {"t0_event": {"steps": 15_000, "limit_bad": 0, "hold_steps": 2_000, "hold_speed_sum": 2_000 * 9.5}}
    assert v5.t0_event_ok(ok, cfg)["pass"]
    assert not v5.t0_event_ok({"t0_event": {**ok["t0_event"], "limit_bad": 3}}, cfg)["pass"]
    assert not v5.t0_event_ok({"t0_event": {**ok["t0_event"], "hold_speed_sum": 2_000 * 11.0}}, cfg)["pass"]


def test_ev_jobs(tmp_path):
    if not v5.S6_JOBS.is_file():
        return
    j = v5.plan("ev_size", tmp_path)
    assert len(j["arms"]) == 10 and j["arms"]["EVA20|nc"]["ctrl"]["env"]["perturb"]["limit_kmh"] == 20.0
    assert "perturb" not in j["arms"]["S|p333"]["ctrl"].get("env", {})
    g = v5.plan("ev_gate", tmp_path, 15.0)
    assert sorted(g["arms"]) == ["EVA15|nc", "EVA15|p333", "S|nc", "S|p333"] and g["seed_range"] == [7_488_240, 7_488_279]
    sm = v5.plan("ev_smoke", tmp_path)
    assert all(c.get("t0_event") for n, c in sm["arms"].items() if n.startswith("EVA") and not n.endswith("~untraced"))
    assert sm["seed_range"] == [7_488_200, 7_488_200] and "t0_event" not in sm["arms"]["EVA10|nc~untraced"]
