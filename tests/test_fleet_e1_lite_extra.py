"""V240 report-only additions to E1-lite on synthetic numbers."""
import numpy as np

from v5b.fleet import e1_lite_extra as ex


def test_null_floor_centres_and_flips():
    rng = np.random.default_rng(0)
    X = rng.normal(0.0, 0.2, (10, 9)) + 0.3
    f = ex.null_floor(X, R=4000)
    assert 0.0 < f["mean"] < 0.2
    part = np.array([True] * 3 + [False] * 6)
    X[:, 3:] = -0.3                                     # arms far below zero never win
    assert ex.null_floor(X, part, R=4000)["mean"] < f["mean"] + 0.05


def test_all_braking_counts_every_lane(tmp_path):
    log = tmp_path / "sumo.log"
    log.write_text("Warning: Vehicle 'a' performs emergency braking on lane 'r_0' with decel=9\n"
                   "Warning: Vehicle 'b' performs emergency braking on lane ':m_0_0' with decel=9\n"
                   "Warning: Teleporting vehicle 'c'\n")
    assert ex.all_braking(log) == 2
    assert ex.all_braking(tmp_path / "missing.log") is None
