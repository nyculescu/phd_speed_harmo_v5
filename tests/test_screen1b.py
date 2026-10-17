"""Screen #1b integrity tests: must pass on synthetic data before any TGSIM read (screen #1's tests also run)."""
import numpy as np
import pandas as pd

from v5b import screen1 as s1
from v5b import screen1b as sb


def test_batched_tracker_reaches_alpha():
    rng = np.random.default_rng(11)
    n = 200_000
    gt = np.sort(rng.integers(0, n // 2, n))            # ~20 windows per second -> large batches
    sc = rng.exponential(1.5, n)
    c = sb.c_regime(gt)
    q = sb.track_batched(gt, sc, q0=8.0, c=c)
    assert c > 5
    assert abs((sc > q).mean() - s1.ALPHA) < 0.01
    # and it does not swing like the unnormalised NGSIM tracker
    assert np.percentile(q[n // 2:], 90) - np.percentile(q[n // 2:], 10) < 2.0


def test_batched_tracker_uses_only_known_outcomes():
    rng = np.random.default_rng(12)
    gt = np.sort(rng.integers(0, 20_000, 3000))
    sc = rng.exponential(1.5, 3000)
    c = sb.c_regime(gt)
    q1 = sb.track_batched(gt, sc, 3.0, c)
    sc2 = sc.copy(); k = 1500; sc2[k:] = 99.0
    q2 = sb.track_batched(gt, sc2, 3.0, c)
    known_tick = (gt[k] + sb.DELAY + sb.TICK - 1) // sb.TICK * sb.TICK
    keep = gt < known_tick
    assert np.array_equal(q1[keep], q2[keep])


def test_placebo_reaches_alpha():
    rng = np.random.default_rng(13)
    sc = rng.exponential(1.5, 100_000)
    q = sb.track_placebo(sc, 8.0, 15.0)
    assert abs((sc > q).mean() - s1.ALPHA) < 0.01


def _lanes():
    # run 1: lane 2 vehicles 10 (x=0), 11 (x=30), 12 (x=200, too far); lane 3 vehicle 13 (x=10)
    # run 2: lane 2 vehicle 20 (x=5): must not be matched with run 1
    rows = []
    for step in range(0, 50):
        dx = step * 1.0
        for run, lane, vid, x in ((1, 2, 10, 0.0), (1, 2, 11, 30.0), (1, 2, 12, 200.0), (1, 3, 13, 10.0), (2, 2, 20, 5.0)):
            rows.append((run, vid, step / 10, x + dx, 0.0, lane, 10.0))
    df = pd.DataFrame(rows, columns=["run_index", "id", "time", "xloc_kf", "yloc_kf", "lane_kf", "speed_kf"])
    df["step"] = np.rint(df.time * 10).astype(np.int64)
    return df.sort_values(["run_index", "id", "step"]).reset_index(drop=True)


def test_leader_matching():
    df = _lanes()
    lead = sb.leaders(df)
    got = pd.Series(lead, index=df.index).groupby(df.id).first().to_dict()
    assert got[10] == 11            # nearest ahead, same lane
    assert got[11] == -1            # 12 is 170 m ahead: beyond 150 m
    assert got[12] == -1            # nobody ahead
    assert got[13] == -1            # alone in lane 3
    assert got[20] == -1            # alone in run 2 (run 1 vehicles ignored)


def test_leader_direction_follows_travel():
    df = _lanes()
    df["xloc_kf"] = -df["xloc_kf"]  # same scene, travelling towards -x
    lead = sb.leaders(df)
    got = pd.Series(lead, index=df.index).groupby(df.id).first().to_dict()
    assert got[10] == 11 and got[11] == -1


def test_evaluate_smoke():
    rng = np.random.default_rng(14)
    n = 6000
    W = pd.DataFrame({"site": rng.choice(list(sb.SITES), n), "run": rng.integers(0, 3, n),
                      "step": rng.integers(0, 30_000, n), "regime": rng.choice(["R1", "R2", "R3"], n),
                      "s": rng.exponential(1.5, n), "clipped": False, "v0": rng.uniform(0, 30, n)})
    W["gtime"] = W.run * sb.RUN_SPAN + W.step
    res = sb.evaluate(W)
    assert res["outcome"] in {"CONTINUE", "STOP", "STOP (data)"} and len(res["cells"]) == 6
