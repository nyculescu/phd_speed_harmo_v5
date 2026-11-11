"""M2 reader (v505_m2_merge_check.md §2-§5): the base readings reproduce read6 v2.3's recorded values on the stored S6 rows; the
readings, binding check and pick rules on planted rows."""
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "docs/research/v505"))
import read_m2 as rm  # noqa: E402
import v5  # noqa: E402

KEEP = {f"{c}|{a}" for c in ("S", "TRUCK") for a in v5.pb.V3W + ("p333", "os0_10_10", "3E-C_TRUCK", "nc")}
RECORDED = {"C1": (-0.58, -0.93, 0.20), "C2": (11.80, 4.97, 19.71), "C3": (-1.57, -2.70, -0.24)}     # read6_v23.json, 97.5 %


@pytest.fixture(scope="module")
def s6():
    if not rm.S6_ROWS.is_file():
        pytest.skip("stored S6 rows not on this machine")
    return rm.load(rm.S6_ROWS, KEEP)


def test_base_readings_reproduce_read6_recorded_values(s6):
    seeds = v5.seeds("m2_verdict")
    st = rm.read6.Stat(len(seeds))
    for c, (e, lo, hi) in RECORDED.items():
        cell, opp, key = rm.CONCLUSIONS[c]
        r = rm.reading(st, rm.p_arm(s6, cell, seeds, key), rm.arr(s6, cell, opp, seeds, key))
        assert (round(r["e"], 2), round(r["ci"][0], 2), round(r["ci"][1], 2)) == (e, lo, hi), c
    assert [rm.component(rm.reading(st, rm.p_arm(s6, rm.CONCLUSIONS[c][0], seeds, rm.CONCLUSIONS[c][2]),
                                     rm.arr(s6, rm.CONCLUSIONS[c][0], rm.CONCLUSIONS[c][1], seeds, rm.CONCLUSIONS[c][2])), rm.CONCLUSIONS[c][2])
            for c in ("C1", "C2", "C3")] == ["neither", "better", "neither"]


def planted(n=240, shift=0.0, es_cut=0.9, seed=1):
    """A cell and its variant: v3w equals the opponent plus noise; the variant moves v3w by shift % and cuts end_stop2 by es_cut."""
    rng = np.random.default_rng(seed)
    T = {}
    seeds = list(range(7_480_400, 7_480_400 + n))
    for cell, s_, cut in (("TRUCK", 0.0, 0.0), ("TRUCKV3", shift, es_cut)):
        base = {s: 160_000.0 + rng.normal(0, 5_000) for s in seeds}
        es = lambda m: max(m * (1 - cut) * (1 + rng.normal(0, 0.3)), 0.0)     # skewed, noisy lane-end waiting
        T[(cell, "os0_10_10")] = {s: {"all_delay": base[s], "end_stop2": es(800.0)} for s in seeds}
        T[(cell, "nc")] = {s: {"all_delay": base[s] * 1.4, "end_stop2": es(600.0)} for s in seeds}
        for w in v5.pb.V3W:
            T[(cell, w)] = {s: {"all_delay": base[s] * (1 - s_ / 100) + rng.normal(0, 3_000), "end_stop2": es(500.0)} for s in seeds}
    return T, seeds


@pytest.fixture
def no_null(monkeypatch):
    """The reading logic apart from the swap null (2,000 swaps at B = 20,000 take minutes; the null has its own test)."""
    monkeypatch.setattr(rm.read6, "swap_null", lambda *a, **k: 0.0)


def test_null_failure_blocks_the_reading(monkeypatch):
    T, seeds = planted()
    monkeypatch.setattr(rm.read6, "swap_null", lambda *a, **k: 0.05)
    assert rm.conclusion(T, "C1", 3.0, seeds)["reading"] == rm.read6.FAILED_NULL


def test_same_when_nothing_changes_and_changed_on_a_large_shift(no_null):
    T, seeds = planted()
    r = rm.conclusion(T, "C1", 3.0, seeds)
    assert r["reading"] == "SAME" and r["base_reading"] == "neither" and "detectable_shift_80" in r
    T, seeds = planted(shift=4.0)
    assert rm.conclusion(T, "C1", 3.0, seeds)["reading"] == "CHANGED"


def test_variant_that_does_not_cut_lane_end_waiting_is_not_read(no_null):
    T, seeds = planted(es_cut=0.3)
    assert rm.conclusion(T, "C1", 3.0, seeds)["reading"] == "VARIANT DID NOT BIND"
    T, seeds = planted(es_cut=0.7)     # a cut well above the 50 % floor binds
    assert rm.conclusion(T, "C1", 3.0, seeds)["reading"] == "SAME"


def test_fallback_base_that_differs_from_the_record_is_not_replicated(no_null):
    T, seeds = planted(shift=0.0)
    for s in seeds:     # make the base read "better" for C1, recorded as "neither"
        for w in v5.pb.V3W:
            T[("TRUCK", w)][s]["all_delay"] *= 0.95
    assert rm.conclusion(T, "C1", 3.0, seeds, fallback=True)["reading"] == "NOT REPLICATED"
    assert rm.conclusion(T, "C1", 3.0, seeds, fallback=False)["reading"] != "NOT REPLICATED"


def test_pr28_status_needs_same_everywhere_and_waits_for_x1():
    same = {c: {"reading": "SAME"} for c in ("C1", "C2", "C3")}
    x1 = {"C5": {"reading": "SAME"}, "C5b": {"reading": "SAME"}}
    assert rm.pr28_status(same, 3.0, "full", 0.8, "pending") == "provisional, X1 pending"
    assert rm.pr28_status({**same, **x1}, 3.0, "full", 0.8, "read").startswith("partial: located by road and period (not lane)")
    assert rm.pr28_status(same, 3.0, "full", 0.8, "dropped").startswith("partial:")
    assert "partial variant (cut 60%)" in rm.pr28_status({**same, **x1}, 3.0, "partial", 0.6, "read")
    assert rm.pr28_status({**same, "C2": {"reading": "CHANGED"}, **x1}, 3.0, "full", 0.8, "read") == "gap"
    assert rm.pr28_status({**same, **x1, "C5": {"reading": "NOT REPLICATED"}}, 3.0, "full", 0.8, "read") == "gap"
    assert rm.pr28_status({**same, **x1, "C5": {"reading": "VARIANT DID NOT BIND"}}, 3.0, "full", 0.8, "read").startswith("partial:")


def pick_rows(cuts, unsafe=()):
    seeds = v5.seeds("m2_pick")
    q = {"ramp1_queue": [60.0] * 30, "ramp2_queue": [60.0] * 30, "ramp1_pending": [0.0] * 30, "ramp2_pending": [0.0] * 30}
    row = lambda es, b: {"end_stop2": es, "end_stop": 30.0, "b45_step": b, "alks_b45_step": b, "alks_full_moving": 0.0, "collisions": 0.0,
                         "m_stuck_n": 0, "m_minute": q, "m_main_pending_min": [0.0] * 30}
    T = {}
    for arm in ("nc", "p333"):
        T[("S", arm)] = {s: row(400.0, 200.0) for s in seeds}
        for a, cut in zip(v5.LADDER, cuts):
            T[(f"SV{a:g}", arm)] = {s: row(400.0 * (1 - cut), 260.0 if a in unsafe else 200.0) for s in seeds}
    return T, seeds


def test_pick_smallest_full_then_partial_then_void():
    T, seeds = pick_rows((0.5, 0.8, 0.9, 0.95))
    assert rm.pick(T, seeds)["a"] == 3.0 and rm.pick(T, seeds)["kind"] == "full"
    T, seeds = pick_rows((0.5, 0.8, 0.9, 0.95), unsafe=(3.0, 5.0, 10.0))
    p = rm.pick(T, seeds)
    assert p["a"] == 2.0 and p["kind"] == "partial" and abs(p["cut"] - 0.5) < 1e-9
    T, seeds = pick_rows((0.2, 0.3, 0.4, 0.45))
    assert rm.pick(T, seeds)["kind"] == "VOID"


def test_pick_needs_the_binding_bound_on_the_pick_seeds():
    """V513: a point cut of 60 % whose 95 % lower bound is below 50 % is not eligible."""
    T, seeds = pick_rows((0.6, 0.6, 0.6, 0.6))
    rng = np.random.default_rng(4)
    for a in v5.LADDER:
        for arm in ("nc", "p333"):
            for s in seeds:
                T[(f"SV{a:g}", arm)][s]["end_stop2"] = 400.0 * 0.4 * rng.lognormal(0, 1.2)
    p = rm.pick(T, seeds)
    weak = [k for k, r in p["levels"].items() if min(r[x]["cut"] for x in ("nc", "p333")) >= 0.5 and min(r[x]["cut_lb95"] for x in ("nc", "p333")) < 0.5]
    assert weak, "the planted rows should hold a level with a 50 %+ point cut but a lower bound under 50 %"
    assert p["a"] is None or f"{p['a']:g}" not in weak
    if p["a"] is not None:
        assert all(p["levels"][f"{p['a']:g}"][x]["cut_lb95"] >= 0.5 for x in ("nc", "p333"))
