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
        T[(cell, "os0_10_10")] = {s: {"all_delay": base[s], "end_stop2": 800.0 * (1 - cut)} for s in seeds}
        T[(cell, "nc")] = {s: {"all_delay": base[s] * 1.4, "end_stop2": 600.0 * (1 - cut)} for s in seeds}
        for w in v5.pb.V3W:
            T[(cell, w)] = {s: {"all_delay": base[s] * (1 - s_ / 100) + rng.normal(0, 3_000), "end_stop2": 500.0 * (1 - cut)} for s in seeds}
    return T, seeds


def test_same_when_nothing_changes_and_changed_on_a_large_shift():
    T, seeds = planted()
    r = rm.conclusion(T, "C1", 3.0, 0.75, seeds, swaps=200)
    assert r["reading"] == "SAME" and r["base_reading"] == "neither" and "detectable_shift_80" in r
    T, seeds = planted(shift=4.0)
    assert rm.conclusion(T, "C1", 3.0, 0.75, seeds, swaps=200)["reading"] == "CHANGED"


def test_variant_that_does_not_cut_lane_end_waiting_is_not_read():
    T, seeds = planted(es_cut=0.5)
    assert rm.conclusion(T, "C1", 3.0, 0.75, seeds, swaps=200)["reading"] == "VARIANT DID NOT BIND"


def test_pr28_status_needs_same_everywhere():
    same = {c: {"reading": "SAME"} for c in ("C1", "C2", "C3")}
    assert rm.pr28_status(same, 3.0, "full", 0.75).startswith("partial: located by road and period (not lane)")
    assert "partial variant (cut 60%)" in rm.pr28_status(same, 3.0, "partial", 0.6)
    assert rm.pr28_status({**same, "C2": {"reading": "CHANGED"}}, 3.0, "full", 0.75) == "gap"
    assert rm.pr28_status({**same, "C5": {"reading": "NOT REPLICATED"}}, 3.0, "full", 0.75) == "gap"


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
    assert p["a"] == 2.0 and p["kind"] == "partial" and abs(p["bar"] - 0.5) < 1e-9
    T, seeds = pick_rows((0.2, 0.3, 0.4, 0.45))
    assert rm.pick(T, seeds)["kind"] == "VOID"
