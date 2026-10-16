"""Screen #1 Rule 5: these must pass on synthetic data before any NGSIM read."""
import numpy as np
import pandas as pd

from v5b import screen1 as s1


def brute_gap(b_hat, v, dt=1e-4):
    t = np.arange(0, 60, dt)
    xe = np.empty_like(t); ve, x = v, 0.0
    xl = np.minimum(t, v / b_hat); xl = v * xl - 0.5 * b_hat * xl ** 2
    for i in range(len(t)):
        xe[i] = x
        a = s1.A_ACC if t[i] < s1.RHO else -s1.B_MIN
        ve_new = max(ve + a * dt, 0.0)
        x += 0.5 * (ve + ve_new) * dt
        ve = ve_new
    return max((xe - xl).max(), 0.0)


def test_dsafe_matches_lemma2_when_bhat_ge_bmin():
    b = np.array([4.0, 5.0, 7.5, 10.0] * 4)
    v = np.repeat([1.0, 10.0, 25.0, 35.0], 4)
    assert np.allclose(s1.d_safe(b, v), s1.rss_lemma2(b, v), atol=0.05)


def test_dsafe_matches_bruteforce_when_bhat_lt_bmin():
    for b, v in [(1.0, 5.0), (2.0, 30.0), (3.0, 20.0), (1.5, 0.5)]:
        assert abs(s1.d_safe(b, v)[0] - brute_gap(b, v)) < 0.05
    # Lemma 2 understates there
    assert s1.d_safe(2.0, 30.0)[0] > s1.rss_lemma2(2.0, 30.0) + 1.0


def test_tracker_reaches_alpha_with_delay():
    rng = np.random.default_rng(1)
    n = 100_000
    st = np.sort(rng.integers(0, n * 2000, n))      # overlapping windows, delayed outcomes
    sc = rng.exponential(1.5, n)
    q = s1.track(st, sc, q0=8.0)
    assert abs((sc > q).mean() - s1.ALPHA) < 0.01


def test_tracker_uses_only_past_outcomes():
    rng = np.random.default_rng(2)
    st = np.arange(0, 400) * 3000
    sc = rng.exponential(1.5, 400)
    q = s1.track(st, sc, q0=3.0)
    sc2 = sc.copy(); sc2[200:] = 99.0                # change outcomes from window 200 on
    q2 = s1.track(st, sc2, q0=3.0)
    # windows whose start is before window 200's outcome is known keep their threshold
    known = st[200] + (s1.WIN + s1.LOOK) * s1.DT_MS
    keep = st < known
    assert np.array_equal(q[keep], q2[keep])


def _synthetic_ngsim(n_veh=6, n=400, seed=3):
    rng = np.random.default_rng(seed)
    rows = []
    for vid in range(1, n_veh + 1):
        v = np.clip(10 + np.cumsum(rng.normal(0, 0.3, n)), 0, 30) / s1.FT
        for i in range(n):
            rows.append((vid, i, 1_000_000 + i * 100, v[i], vid - 1, "i-80"))
    return pd.DataFrame(rows, columns=["Vehicle_ID", "Frame_ID", "Global_Time", "v_Vel", "Preceding", "Location"])


def test_regime_and_score_do_not_use_future():
    df = _synthetic_ngsim()
    W = s1.windows(df)
    assert len(W) > 0
    df2 = df.copy()
    # perturb everything after the first window of vehicle 1 ends (+10 s): its regime and score stay
    t_first = W.start_ms.min()
    m = (df2.Vehicle_ID == 1) & (df2.Global_Time >= t_first + 10_500)
    df2.loc[m, "v_Vel"] = 0.0
    W2 = s1.windows(df2)
    a = W[W.start_ms == t_first].iloc[0]
    b = W2[W2.start_ms == t_first].iloc[0]
    assert a.regime == b.regime and a.s == b.s


def test_regime_uses_only_history_before_window():
    df = _synthetic_ngsim()
    W = s1.windows(df)
    t_first = W.start_ms.min()
    df2 = df.copy()
    m = (df2.Vehicle_ID == 1) & (df2.Global_Time >= t_first)
    df2.loc[m, "v_Vel"] = 0.0                        # wipe the window itself and after
    W2 = s1.windows(df2)
    assert W[W.start_ms == t_first].iloc[0].regime == W2[W2.start_ms == t_first].iloc[0].regime


def test_evaluate_smoke():
    rng = np.random.default_rng(4)
    n = 4000
    W = pd.DataFrame({"site": rng.choice(list(s1.SITES), n), "start_ms": rng.integers(0, 2_700_000, n),
                      "regime": rng.choice(["R1", "R2", "R3"], n), "s": rng.exponential(1.5, n),
                      "clipped": False, "v0": rng.uniform(0, 30, n)})
    res = s1.evaluate(W)
    assert res["outcome"] in {"CONTINUE", "STOP", "STOP (data)"}
    assert len(res["cells"]) == 6
