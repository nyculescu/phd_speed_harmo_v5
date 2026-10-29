"""Layer B crash rule (v5b/fleet/crash.py): weights, CRN draws, the live process and the calibration."""
import numpy as np

from v5b.fleet import crash as cr


def test_weight_and_cap():
    m = np.array([0.0, 0.75, 1.5, 2.0])
    assert np.allclose(cr.weight(m, 1.5, "linear"), [1.0, 0.5, 0.0, 0.0])
    assert np.allclose(cr.weight(m, 1.5, "constant"), 1.0)
    assert cr.p_crash(0.0, 5.0, 1.5, "linear") == 1.0


def test_draws_are_crn():
    assert cr.draws(7, 1, 2, 30.0) == cr.draws(7, 1, 2, 30.0)
    assert cr.draws(7, 1, 2, 30.0) != cr.draws(7, 1, 2, 31.0)
    u, dur = cr.draws(7, 1, 2, 30.0)
    assert 0 <= u < 1 and 1800 <= dur <= 3600


def test_process_human_only_and_trigger():
    p = cr.CrashProcess(seed=1, k=1e9)
    assert not p.observe(10.0, 0, 1, "a", "b", "alks", 0.5)            # CAV follower cannot crash
    assert p.observe(10.0, 2, 3, "c", "d", "hdv_car", 0.5)             # p capped at 1: crashes at once
    assert p.blocked("c") and p.blocked("d")
    assert not p.observe(11.0, 4, 3, "e", "d", "hdv_car", 0.2)         # leader already crashed
    t_rel = p.release["c"]
    assert p.due(t_rel - 1) == [] and sorted(p.due(t_rel)) == ["c", "d"]


def test_process_matches_offline_rule():
    """Crash iff p(running minimum) reaches the encounter's uniform, as in the calibration."""
    seed, k = 3, 0.4
    u0, _ = cr.draws(seed, 5, 6, 100.0)
    ttcs = [1.4, 1.1, 0.6, 0.9]
    p = cr.CrashProcess(seed=seed, k=k)
    hit = [p.observe(100.0 + i, 5, 6, "f", "l", "truck", x) for i, x in enumerate(ttcs)]
    running = np.minimum.accumulate(ttcs)
    want = [bool(cr.p_crash(m, k, 1.5, "linear") >= u0) for m in running]
    first = want.index(True) if True in want else None
    assert hit == [i == first for i in range(len(ttcs))]


def test_new_encounter_after_gap():
    p = cr.CrashProcess(seed=1, k=1e-12)
    p.observe(10.0, 0, 1, "a", "b", "hdv_car", 1.0)
    t0 = p.active[(0, 1)][0]
    p.observe(13.0, 0, 1, "a", "b", "hdv_car", 1.0)
    assert p.active[(0, 1)][0] == 13.0 != t0


def test_calibration_hits_target():
    rng = np.random.default_rng(0)
    days = [rng.uniform(0.2, 1.5, size=rng.integers(800, 1200)) for _ in range(10)]
    r = cr.calibrate(days, 1.5, "linear", 0.25)
    assert abs(r["p_day_mean"] - 0.25) < 1e-6 and r["p_max"] < 0.01
