"""Screen #2 Rule 5: these must pass on synthetic signal logs before any archive read."""
import numpy as np

from v5b import screen2 as s2


def synth_log(t0=1_694_570_400, hours=30, cycle=90, green=30, seed=5):
    """Fixed-time signal: green [k*cycle, k*cycle+green), red otherwise; random reception delays."""
    rng = np.random.default_rng(seed)
    p, r = [], []
    for k in range(int(hours * 3600 / cycle)):
        g = t0 + k * cycle
        p += [g, g + green, g + green + 3]
        r += [3, 2, 1]
    p, r = np.array(p, float), np.array(r)
    recv = (p + rng.choice([0.5, 1.0, 2.0, 300.0], len(p), p=[0.4, 0.3, 0.2, 0.1])) * 1000
    return p, r, recv


def test_reachable_window():
    assert abs(s2.R0 - 14.388) < 0.01 and abs(s2.R1 - 24.096) < 0.01


def test_decide_arithmetic():
    t = 1000.0
    T = s2.decide(t, [(t + 10, t + 40)], [0.0, 5.0, 27.0])
    assert abs(T[0] - (t + s2.R0)) < 1e-9 and abs(T[1] - (t + 15.0)) < 1e-9 and np.isnan(T[2])


def test_forecast_has_no_leak():
    p, r, recv = synth_log()
    P, S, K = s2.timeline(p, r, recv)
    rng = np.random.default_rng(6)
    for t in rng.uniform(p[0] + 7200, p[-1] - 3600, 50):
        w = s2.forecast(t, P, S, K)
        # perturb every report that is not yet known at t (state and time)
        late = recv / 1000 > t
        r2, p2 = r.copy(), p.copy()
        r2[late] = 1
        p2[late] = p2[late] + rng.uniform(-30, 30, late.sum())
        P2, S2, K2 = s2.timeline(p2, r2, recv)
        assert s2.forecast(t, P2, S2, K2) == w


def test_forecast_recovers_fixed_cycle():
    p, r, recv = synth_log(seed=7)
    P, S, K = s2.timeline(p, r, recv * 0 + p * 1000)   # instant reception
    t = p[0] + 5 * 3600 + 50                              # 50 s into a cycle: red
    w = s2.forecast(t, P, S, K)
    assert w is not None and len(w) == 1
    ws, we = w[0]
    assert abs((we - ws) - 30) < 1e-9 and (ws - p[0]) % 90 == 0


def test_cdt_reaches_eps():
    rng = np.random.default_rng(8)
    m, losses, n = 0.0, 0, 100_000
    for _ in range(n):
        l = rng.random() < np.exp(-m / 3.0)
        losses += l
        m = s2.cdt_step(m, l)
    assert abs(losses / n - s2.EPS) < 0.01


def test_evaluate_smoke():
    tl = {}
    for g in range(25):
        p, r, recv = synth_log(t0=s2.local_ts(13), hours=12 * 24, cycle=80 + g, green=25 + g % 7, seed=g)
        tl[1000 + g] = s2.timeline(p, r, recv)
    res = s2.evaluate(tl)
    assert res["outcome"] in {"CONTINUE", "STOP", "STOP (data)"}
    assert len(res["cells"]) == 2
