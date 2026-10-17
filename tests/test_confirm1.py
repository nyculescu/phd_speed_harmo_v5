"""Confirmatory #1 (V84) synthetic tests: must pass before any confirmatory TGSIM row is downloaded."""
import io
import math

import numpy as np
import pandas as pd
from scipy import stats

from v5b import confirm1 as c1


def test_constants_match_protocol():
    assert c1.ALPHA == 0.04 and c1.LIMIT == 0.075 and c1.DELAY == 105 and c1.N_W == 300
    assert c1.SEED_BOOT == 7_420_200 and c1.SEEDS_P == list(range(7_420_201, 7_420_221)) and c1.B_BOOT == 10_000


def test_order_statistic_quantile():
    x = np.arange(1, 101)                       # 1..100
    k = math.ceil(0.96 * 101)                   # 97th smallest
    assert c1.qstat(x) == 97.0 == float(k)
    assert c1.qstat(np.arange(1, 11)) == 10.0   # ceil(0.96*11)=11 -> capped at n
    assert c1.qstat(x) != float(np.quantile(x, 0.96))


def test_tracker_holds_per_window_rate_when_busy_seconds_brake_harder():
    rng = np.random.default_rng(21)
    gts, sc = [], []
    for sec in range(40_000):
        busy = rng.random() < 0.3
        n = rng.poisson(12 if busy else 2)
        gts += [sec * 10 + rng.integers(0, 10) for _ in range(n)]
        sc += list(rng.exponential(2.5 if busy else 1.0, n))
    gt, sc = np.array(gts), np.array(sc)
    c = float(np.percentile(np.unique((gt + c1.DELAY + 9) // 10, return_counts=True)[1], 90))
    q = c1.track(gt, sc, 3.0, c, floor=0.0)
    assert abs((sc > q).mean() - c1.ALPHA) < 0.01


def test_tracker_uses_only_known_outcomes_and_delay_105():
    rng = np.random.default_rng(22)
    gt = np.sort(rng.integers(0, 30_000, 4000)); s = rng.exponential(1.5, 4000)
    q1 = c1.track(gt, s, 3.0, 4.0)
    k = 2000; s2 = s.copy(); s2[k:] = 50.0
    q2 = c1.track(gt, s2, 3.0, 4.0)
    known = (gt[k] + 105 + 9) // 10 * 10
    assert np.array_equal(q1[gt < known], q2[gt < known])


def test_tracker_carried_across_runs():
    rng = np.random.default_rng(23)
    g1 = np.sort(rng.integers(0, 20_000, 2000)); g2 = c1.RUN_SPAN + np.sort(rng.integers(0, 20_000, 2000))
    s = rng.exponential(3.0, 4000)
    q = c1.track(np.r_[g1, g2], s, 1.0, 4.0, floor=0.0)
    assert abs(q[2000] - 1.0) > 0.2              # run 2 does not restart from q0


def test_w_arm_and_comparison_windows():
    gt = np.arange(0, 6000, 10)                  # 600 windows, 1 s apart
    s = np.r_[np.full(300, 2.0), np.full(300, 9.0)]
    qW, freeze = c1.w_arm(gt, s, F=5.0, n_w=300, floor=1.0)
    assert freeze == gt[299] + 105
    assert np.all(qW[gt <= freeze] == 5.0) and np.all(qW[gt > freeze] == 2.0)
    cm = c1.comparison_mask(gt, 300)
    assert cm.sum() == (gt > freeze).sum() and not cm[:300].any()
    qW2, fr2 = c1.w_arm(gt[:300], s[:300], F=5.0)
    assert fr2 is None and np.all(qW2 == 5.0) and c1.comparison_mask(gt[:300]).all()


def test_placebo_keeps_each_window_and_equals_O_for_constant_scores():
    rng = np.random.default_rng(24)
    gt = np.sort(rng.integers(0, 50_000, 3000))
    s = np.full(3000, 2.0)
    # constant scores: same slot thresholds as O, each window gets the threshold of the slot it lands in
    qp, qo = c1.placebo(gt, s, 3.0, 4.0, 7_420_201), c1.track(gt, s, 3.0, 4.0)
    assert np.allclose(np.sort(qp), np.sort(qo)) and not np.allclose(qp, qo)
    s = rng.exponential(1.5, 3000)
    qp = c1.placebo(gt, s, 3.0, 4.0, 7_420_201)
    assert abs((s > qp).mean() - c1.ALPHA) < 0.02 and len(qp) == 3000


def test_miss_bounds_and_validity_rules():
    rng = np.random.default_rng(25)
    n = 4000
    blocks = np.repeat(np.arange(40), n // 40)
    miss = (rng.random(n) < 0.04).astype(float)
    b = c1.miss_bounds(miss, blocks, J=4)
    k = int(miss.sum())
    assert abs(b["ub_cp"] - stats.beta.ppf(0.95, k + 1, n - k)) < 1e-12
    assert b["ub"] >= b["p"] and c1.a1_valid(b) and not c1.clearly_invalid(b)
    bad = (rng.random(n) < 0.20).astype(float)
    bb = c1.miss_bounds(bad, blocks, J=4)
    assert c1.clearly_invalid(bb) and not c1.a1_valid(bb)


def test_efficiency_and_beats():
    rng = np.random.default_rng(26)
    n = 4000
    blocks = np.repeat(np.arange(40), n // 40)
    dY = rng.uniform(5, 10, n); dX = dY * 0.9
    e = c1.efficiency(dX, dY, blocks, J=4)
    assert abs(e["E"] - 0.1) < 1e-9 and c1.beats(e)
    e2 = c1.efficiency(dY * 0.99, dY, blocks, J=4)
    assert not c1.beats(e2)                      # below the 3 % gain


def _windows(n_per=1500, seed=27):
    rng = np.random.default_rng(seed)
    rows = []
    for ds in ("i294_l1", "i90_94_moving", "i294_l2"):
        for reg in ("R1", "R2", "R3"):
            for unit in (-1, 1):
                st = np.sort(rng.integers(0, 60_000, n_per))
                for k, t in enumerate(st):
                    rows.append((ds, 1, 1000 + k, int(t), 1 * c1.RUN_SPAN + int(t), reg, unit, False, 15.0))
    W = pd.DataFrame(rows, columns=["dataset", "run", "id", "step", "gtime", "regime", "unit", "test", "v0"])
    W["known"] = W.gtime + c1.DELAY
    return W


def test_stage1_ignores_scores_and_gates_correctly():
    W = _windows()
    fit = W.assign(dataset="i395")
    rows = dict(c1.ROWS)
    a = c1.stage1(W.assign(s=np.random.default_rng(1).random(len(W))), fit, rows)
    b = c1.stage1(W.assign(s=np.random.default_rng(2).random(len(W))), fit, rows)
    assert a == b
    gated = {(x["dataset"], x["regime"]) for x in a["cells"] if x["gated"]}
    assert gated == {("i294_l1", "R1"), ("i294_l1", "R2"), ("i90_94_moving", "R1"), ("i90_94_moving", "R2")}
    assert a["J"] == 4 and not a["stop_data"]
    bad = dict(rows); bad["i294_l1"] += 1
    assert c1.stage1(W, fit, bad)["stop_data"]


def test_test_vehicle_flags_in_loader(tmp_path):
    csv = ("id,time,xloc_kf,yloc_kf,lane_kf,speed_kf,acceleration_kf,length_smoothed,width_smoothed,type_most_common,acc,run_index\n"
           "1,0.1,0,0,-2,10,0,5,2,small,No,1\n2,0.1,5,0,-2,10,0,5,2,small,YES,1\n3,0.1,9,0,-2,10,0,5,2,small,yes,1\n")
    p = tmp_path / "x.csv"; p.write_text(csv)
    df, info, tv = c1.load(str(p), "i294_l1")
    assert tv == {(1, 2), (1, 3)} and info["test_vehicles"] == 2


def test_decide_outcome_order():
    st1 = {"stop_data": False, "J": 2}
    base = {"gated": True, "status": "gated", "clip_share": 0.0, "validO": True, "clearly_invalidO": False,
            "win": False, "clearly_worse": False, "beats_P": False, "harm_not_excluded": False, "floor_bound": False,
            "E": {"O_vs_F": {"E": 0.1, "ciB": [0.05, 0.15]}, "O_vs_W": {"E": 0.05, "ciB": [0.01, 0.09]}}}
    a = dict(base, dataset="i294_l1", regime="R1"); b = dict(base, dataset="i90_94_moving", regime="R2")
    assert c1.decide([a, b], {"stop_data": True})["outcome"] == "STOP-data"
    assert c1.decide([dict(a, clearly_invalidO=True), b], st1)["outcome"] == "KILL"
    assert c1.decide([dict(a, validO=False), b], st1)["outcome"] == "INCONCLUSIVE"
    assert c1.decide([a, b], st1)["outcome"] == "VALID-ONLY"
    r = c1.decide([dict(a, win=True), b], st1)
    assert r["outcome"] == "PASS, new road" and abs(r["x"]["E"] - 0.05) < 1e-12
    assert c1.decide([a, dict(b, win=True)], st1)["outcome"] == "PASS, same road"
    assert c1.decide([dict(a, win=True), dict(b, clearly_worse=True)], st1)["outcome"] == "VALID-ONLY"
    assert c1.decide([dict(a, clip_share=0.2), dict(b, clip_share=0.2)], st1)["outcome"] == "INCONCLUSIVE"


def test_stage2_smoke():
    W = _windows(n_per=700, seed=28)
    rng = np.random.default_rng(29)
    W["s"] = rng.exponential(1.2, len(W)); W["clipped"] = False
    fit = W.assign(dataset="i395").copy()
    st1 = c1.stage1(W, fit, dict(c1.ROWS))
    st1["J"] = max(st1["J"], 1); st1["stop_data"] = False
    for x in st1["cells"]:
        x["gated"] = x["regime"] in ("R1", "R2") and x["dataset"] != "i294_l2"
    old = c1.B_BOOT
    try:
        c1.B_BOOT = 300
        res = c1.stage2(W, fit, st1)
    finally:
        c1.B_BOOT = old
    assert res["outcome"]["outcome"] in {"KILL", "INCONCLUSIVE", "VALID-ONLY", "PASS, new road", "PASS, same road"}
    assert len(res["cells"]) == 9


# ---------------------------------------------------------------- review fixes (pre-download)
from v5b import screen1 as s1


def test_req_gap_equals_screen1_and_is_finite_at_zero():
    rng = np.random.default_rng(31)
    b = rng.uniform(0.3, 10, 500); v = rng.uniform(0, 35, 500)
    assert np.allclose(c1.req_gap(b, v), s1.req_gap(b, v), atol=1e-12)
    z = c1.req_gap(np.array([0.0, 1e-4, 1e-3]), 20.0)
    assert np.isfinite(z).all() and z[0] <= z[1] <= z[2]     # milder leader braking -> smaller gap


def test_known_time_delays_feedback_over_sample_gaps():
    gt = np.array([0, 10, 2000]); s = np.array([9.0, 9.0, 0.0])
    late = np.array([105, 2500, 2105])               # window 1's outcome known only at 2500
    q_default = c1.track(gt, s, 3.0, 1.0, floor=0.0)
    q_late = c1.track(gt, s, 3.0, 1.0, floor=0.0, known=late)
    assert q_late[2] < q_default[2]                  # one miss fewer applied before t = 2000
    assert c1.freeze_time(np.arange(0, 3010, 10), 300, np.r_[np.arange(0, 3010, 10)[:299] + 105, 9999, np.zeros(1)]) == 9999


def test_longest_miss_run_follows_time_not_vehicle_order():
    W = _windows(n_per=700, seed=32)
    W = W[(W.dataset == "i294_l1") & (W.regime == "R1")].copy()
    W = W.sample(frac=1.0, random_state=1)           # vehicle-major / random row order
    W["s"] = 0.0; W["clipped"] = False
    o = c1.time_order(W)
    W.loc[W.index[o[-8:]], "s"] = 50.0               # last 8 windows in time: consecutive misses for F, H
    fit = W.assign(dataset="i395")
    st1 = {"J": 1, "c": {"R1": 1.0}, "stop_data": False,
           "cells": [{"dataset": "i294_l1", "regime": "R1", "gated": True}]}
    res = c1.stage2(W, fit, st1)
    assert res["cells"][0]["longest_miss_run"]["F"] == 8


def test_placebo_bound_is_bootstrap_only():
    rng = np.random.default_rng(33)
    m = rng.random(2000) * 0.1; blocks = np.repeat(np.arange(20), 100)
    b = c1.miss_bounds(m, blocks, 2, cp=False)
    assert b["ub"] == b["ub_boot"] and b["ub_cp"] is None and not c1.clearly_invalid(b)


def test_boot_b_override_is_effective():
    old = c1.B_BOOT
    try:
        c1.B_BOOT = 17
        assert c1.boot_idx(5).shape == (17, 5)
    finally:
        c1.B_BOOT = old


def test_power_matches_protocol_figures():
    assert 0.95 <= c1.power_a1(1000, 10) <= 0.97 and 0.97 <= c1.power_a1(1000, 40) <= 0.99
    assert 0.70 <= c1.power_a1(1000, 10, p=0.05) <= 0.72


def test_l1_probe_md5_and_pairs(tmp_path):
    body = b'"id","time","run_index"\n"5","0.1","2"\n"6","0.1","2"\n'
    p = tmp_path / "probe.csv"; p.write_bytes(body)
    old = c1.L1_PROBE_MD5
    try:
        import hashlib
        c1.L1_PROBE_MD5 = hashlib.md5(body).hexdigest()
        info, pairs = c1.l1_probe(str(p))
        assert info["match"] and pairs == {(2, 5), (2, 6)}
    finally:
        c1.L1_PROBE_MD5 = old
    info, _ = c1.l1_probe(str(tmp_path / "missing.csv"))
    assert info["available"] is False


def test_stage2_floor0_with_zero_heavy_scores_runs():
    W = _windows(n_per=500, seed=34)
    W = W[W.dataset == "i294_l1"].copy()
    rng = np.random.default_rng(35)
    W["s"] = np.where(rng.random(len(W)) < 0.9, 0.0, rng.exponential(1.0, len(W))); W["clipped"] = False
    fit = W.assign(dataset="i395")
    st1 = {"J": 2, "c": {"R1": 6.0, "R2": 6.0, "R3": 6.0}, "stop_data": False,
           "cells": [{"dataset": "i294_l1", "regime": r, "gated": r != "R3"} for r in ("R1", "R2", "R3")]}
    old = c1.B_BOOT
    try:
        c1.B_BOOT = 200
        res = c1.stage2(W, fit, st1, floor=0.0)
    finally:
        c1.B_BOOT = old
    assert all(np.isfinite(c["mean_gap"]["O"]) for c in res["cells"] if "mean_gap" in c)


def test_window_meta_matches_screen1b_windows():
    rng = np.random.default_rng(36)
    rows = []
    v = 8 + np.cumsum(rng.normal(0, 0.3, 600))                     # same profile: the pair stays matched
    for vid, x0 in ((1, 0.0), (2, 30.0)):
        steps = np.r_[np.arange(0, 300), np.arange(301, 601)]       # one missing sample (kept in segment)
        x = x0 + np.cumsum(np.abs(v)) * 0.1
        for k, st in enumerate(steps):
            rows.append((1, vid, st / 10, x[k], 0.0, 2, abs(v[k]), False))
    df = pd.DataFrame(rows, columns=["run_index", "id", "time", "xloc_kf", "yloc_kf", "lane_kf", "speed_kf", "test_row"])
    df["step"] = np.rint(df.time * 10).astype(np.int64)
    df = df.sort_values(["run_index", "id", "step"]).reset_index(drop=True)
    lead = sb_leaders = __import__("v5b.screen1b", fromlist=["x"]).leaders(df)
    W, S = c1.window_meta(df, lead, set(), "x")
    s, clip = c1.scores(S)
    ref = __import__("v5b.screen1b", fromlist=["x"]).windows(df, lead)
    assert len(W) == len(ref) > 0
    assert np.allclose(np.sort(s), np.sort(ref.s.to_numpy())) and (W.regime.value_counts().sort_index() == ref.regime.value_counts().sort_index()).all()
    assert (W.known >= W.gtime + c1.DELAY).all() and (W.known > W.gtime + c1.DELAY).any()
