"""Protocol v5 §B10 end-to-end tests of the production J5 objective (J5Eval.day_items and __call__) on stubbed
synthetic days: the gate's model-day layer, model speeds and real station series are stubbed; no real day is read
and nothing is simulated except where a test stubs `simulate` itself. Tests 24, 26, 28 (h), 38, 41.
"""
from __future__ import annotations

import types

import numpy as np
import pytest

from vsl_lab.data import metanet_inputs as I
from vsl_lab.jobs import metanet_calibrate as C
from vsl_lab.jobs import metanet_j5 as J
from vsl_lab.jobs import metanet_j5_eval as E
from vsl_lab.jobs import metanet_postcal as Q
from vsl_lab.plants import metanet as M

EV0, NEV, NB = Q.EV0, Q.NEV, M.N_BINS
NET = M.build_network(C.VARIANT)
NS = len(NET.stations)
U1, D1 = Q.PAIR["B1"]
U2, D2 = Q.PAIR["B2"]
REAL_B1 = (100, 120)


def _speeds(b1=None, b2=()):
    sp = {s: np.full(NEV, 60.0) for s in I.EVENT_STATIONS}
    for s, e in ([b1] if b1 else []):
        sp[U1][s:e + 1] = 30.0
    for s, e in b2:
        sp[U2][s:e + 1] = 30.0
    return sp


def _cells(backed=True, extra=None):
    rc = np.ones((NET.N, NB))
    rho = np.full((NET.N, NB), 0.5)
    if backed:
        rho[25:28, EV0 + REAL_B1[0]:EV0 + REAL_B1[1] + 1] = 1.1           # cells 26-28 congested in the episode
    for (c, a, b) in (extra or []):
        rho[c - 1, a:b] = 1.2
    return rho, rc


def _evaluator(real_b2=(), censor=None):
    """A J5Eval with a one-day real side built in memory (no facts file): B1 heavy and real-active; B2 as given."""
    d = "SYN0"
    ev = {"B1": [list(REAL_B1)], "B2": [list(x) for x in real_b2], "censor": dict(censor or {}),
          "B1_long": {"ep": list(REAL_B1), "heavy": True, "dur_min": 105, "censored": False,
                      "c4": {"Q_dis": 1800.0, "r": 0.1}}, "B2_long": None, "first": "B1", "heavy_first": True}
    rec = dict(ev, censor={str(k): v for k, v in (censor or {}).items()}, merge=[None, None], pairs={},
               P1c_null_N1=0.30, P1c_null_N2=0.20)
    if real_b2:
        rec["B2_long"] = {"ep": list(real_b2[0]), "heavy": True, "dur_min": 5 * (real_b2[0][1] - real_b2[0][0] + 1),
                          "censored": False, "c4": {"Q_dis": 1700.0, "r": 0.1}}
    ev_ = object.__new__(E.J5Eval)
    rows = ["P3-1", "P4-1", "P5a-1", "P7a-1", "P3-2", "X-2", "P7b", "P7c", "P8g", "P1a_h", "P1b_h", "P1a_ff",
            "P1b_ff", "P1c_h"] + (["P4-2", "P5a-2", "P7a-2"] if real_b2 else [])
    w = {r: 1.0 for r in rows}
    w["X-2"] = 5.0
    q = np.full((1, NS, NB), 1500.0)
    v = np.full((1, NS, NB), 90.0)
    m = np.zeros((1, NS, NB), bool)
    m[:, :, EV0:] = True
    ev_.f = {"per_day": {d: rec}}
    ev_.Fm, ev_.Pm = m.copy(), m.copy()
    ev_.days, ev_.data = [d], {"days": np.array([d]), "q": q, "v": v, "mq": m, "mv": m,
                               "d0": np.zeros((1, NB)), "d_o": np.zeros((1, len(NET.entrances), NB)),
                               "beta": np.zeros((1, 5, NB))}
    ev_.net, ev_.cs = NET, {}
    ev_.ev = {d: E.real_events(rec)}
    ev_.q = {"heavy": {"B1": [d], "B2": [d] if real_b2 else []}, "both_q": [], "heavy_any": [d], "P1c_days": [d]}
    ev_.rows, ev_.w = rows, w
    ev_.sids = [s["id"] for s in NET.stations]
    ev_.scell = {st["id"]: st["cell"] for st in NET.stations}
    ev_.record = (24, 39)
    return ev_, d


def _install(monkeypatch, model_b1=(), model_b2=(), real_b2=(), extra_pairs=None):
    msp = _speeds(model_b1[0] if model_b1 else None, model_b2)
    md = {"pairs": {**({Q.PAIR["B1"]: [tuple(x) for x in model_b1]} if model_b1 else {}),
                    **({Q.PAIR["B2"]: [tuple(x) for x in model_b2]} if model_b2 else {}), **(extra_pairs or {})}}
    md["B1"] = {"episodes": [tuple(x) for x in model_b1], "active": bool(model_b1),
                "agree": bool(model_b1) and Q.overlaps(list(model_b1), [REAL_B1]),
                "matched": list(model_b1[0]) if model_b1 else None,
                "c4": {"Q_dis": 1800.0, "r": 0.1} if model_b1 else None, "merge": None}
    md["B2"] = {"episodes": [tuple(x) for x in model_b2], "active": bool(model_b2),
                "agree": (not model_b2) if not real_b2 else Q.overlaps(list(model_b2), list(real_b2)),
                "matched": None, "c4": None, "merge": None}
    monkeypatch.setattr(Q, "model_day", lambda *a, **k: md)
    monkeypatch.setattr(Q, "model_speeds", lambda *a, **k: (msp, {s: True for s in I.EVENT_STATIONS}))
    real = _speeds(REAL_B1, real_b2)
    monkeypatch.setattr(I, "event_station", lambda d, s: {"v": real[s], "valid": True, "q": np.full(NEV, 1500.0)})


def _day(ev_, rho, rc):
    data = ev_.data
    return ev_.day_items(0, data["q"][0].copy(), data["v"][0].copy(), np.zeros((5, NB)), rho, rc)


def test24_e2e_zero_cost_and_unbacked(monkeypatch):
    ev_, _ = _evaluator()
    _install(monkeypatch, model_b1=[REAL_B1])
    it = _day(ev_, *_cells(backed=True))
    assert J.j5(it, ev_.w) == 0.0, it                                  # model = real, backed: every item 0
    it = _day(ev_, *_cells(backed=False))                              # companion: no backing -> miss values
    assert it["P3-1"] == [1.0 + J.EPS] and it["P4-1"] == [1.0] and it["P5a-1"] == [1.0] and it["P7a-1"] == [1.0]


def test26_e2e_parity_one_extra(monkeypatch):
    """One extra P_2 episode on the real-B2-inactive day raises Σ w·A on P3-2 and X-2 only."""
    ev_, _ = _evaluator()
    _install(monkeypatch, model_b1=[REAL_B1])
    base = _day(ev_, *_cells())
    _install(monkeypatch, model_b1=[REAL_B1], model_b2=[(170, 175)])  # > 90 min from every P_1 episode
    ext = _day(ev_, *_cells())
    changed = {r for r in ev_.rows if base[r] != ext[r]}
    assert changed == {"P3-2", "X-2"}, changed
    sw = sum(ev_.w.values())
    assert J.j5(ext, ev_.w) - J.j5(base, ev_.w) == pytest.approx((ev_.w["P3-2"] + ev_.w["X-2"]) / sw, abs=1e-12)


def test28_e2e_shaping_h_over_window_bins(monkeypatch):
    """A miss with no model episode: s from g and h; h ranges over every bin of the g windows on cells 26-28."""
    ev_, _ = _evaluator()
    _install(monkeypatch)                                              # no model episode
    rho, rc = _cells(backed=False)
    it = _day(ev_, rho, rc)
    s0 = (it["P3-1"][0] - 1.0) / J.EPS
    rho2 = rho.copy()
    edge = EV0 + REAL_B1[0] - 12 - 6                                  # first bin of the first 7-bin window
    rho2[25:28, edge] = 1.5                                            # beta = 1.5 at that edge bin only
    it2 = _day(ev_, rho2, rc)
    s2 = (it2["P3-1"][0] - 1.0) / J.EPS
    assert s2 == pytest.approx(s0 - 0.5 * 0.5)                         # h 0.5 -> >= 1: the h half of s drops by 0.25


def test41_e2e_p8g_relocation(monkeypatch):
    ev_, _ = _evaluator()
    _install(monkeypatch, model_b1=[REAL_B1])
    rho, rc = _cells(extra=[(37, EV0 + 50, EV0 + 60)])                # cell 37 over-critical for 10 bins, 34 not
    it = _day(ev_, rho, rc)
    assert it["P8g"] == [1.0]
    _install(monkeypatch, model_b1=[REAL_B1], extra_pairs={Q.RELOC_PAIR: [(50, 55)]})   # relocation (b)
    assert _day(ev_, *_cells())["P8g"] == [1.0]
    _install(monkeypatch, model_b1=[REAL_B1])
    assert _day(ev_, *_cells())["P8g"] == [0.0]


def test38_e2e_inadmissible_branches(monkeypatch):
    """A3 violators are not simulated and score 10 + shortfall; clipping > 1 % or a non-finite day scores 10."""
    ev_, _ = _evaluator()
    _install(monkeypatch, model_b1=[REAL_B1])
    calls = []

    def fake_sim(net, params, inp, n_param_sets=1, record_cells=True, T_s=None, **k):
        calls.append((n_param_sets, record_cells))
        B = n_param_sets
        rho, rc = _cells()
        return types.SimpleNamespace(
            clipped_share=np.array([0.0, 0.02, 0.0][:B]), nonfinite=np.array([False, False, True][:B]),
            q_st=np.repeat(ev_.data["q"], B, 0), v_st=np.repeat(ev_.data["v"], B, 0), exit_flow=np.zeros((B, 5, NB)),
            rho_cell=np.repeat(rho[None], B, 0), rc_cell=np.repeat(rc[None], B, 0))
    monkeypatch.setattr(E.M, "simulate", fake_sim)
    monkeypatch.setattr(C, "a3_thresholds", lambda net: {})
    monkeypatch.setattr(C, "to_params", lambda X: {"x": X[:, 0]})
    monkeypatch.setattr(C, "a3_shortfall", lambda p, thr: np.array([0.0, 0.0, 0.3, 0.0]))
    X = np.zeros((4, 17))
    Jv, parts = ev_(X, return_parts=True)
    assert Jv[2] == pytest.approx(10.3) and parts[2] is None             # A3 violator, not simulated
    assert calls == [(3, (24, 39))]                                     # only the 3 feasible sets; cells 25-39 recorded
    assert Jv[0] == 0.0 and Jv[1] == E.J_INADMISSIBLE and Jv[3] == E.J_INADMISSIBLE


def test29_real_anchoring(monkeypatch):
    """Qualifying sets, weights, rows, masks and the real side are unchanged under arbitrary model output."""
    import copy
    ev_, _ = _evaluator()
    snap = copy.deepcopy((ev_.q, ev_.w, ev_.rows, ev_.f, ev_.Fm, ev_.Pm, ev_.ev))
    rng = np.random.default_rng(7)                                      # non-protocol synthetic seed
    for _ in range(5):
        s = int(rng.integers(20, 140))                                   # model episodes stay inside the 216 event bins
        _install(monkeypatch, model_b1=[(s, s + int(rng.integers(2, 30)))], model_b2=[(s + 40, s + 45)])
        rho, rc = _cells(backed=bool(rng.random() < 0.5))
        _day(ev_, rho * rng.uniform(0.5, 1.5, rho.shape), rc)
    after = (ev_.q, ev_.w, ev_.rows, ev_.f, ev_.Fm, ev_.Pm, ev_.ev)
    assert all(np.array_equal(a, b) if isinstance(a, np.ndarray) else a == b for a, b in zip(snap, after))


class _NoF11(dict):
    def __getitem__(self, k):
        if k == "F11" or (isinstance(k, str) and k.startswith("F11")):
            raise AssertionError("F11 field read on the calibration side")
        return super().__getitem__(k)

    def get(self, k, d=None):
        return self[k] if k in self else d


def test33_no_validation_input_on_calibration_side(monkeypatch, tmp_path):
    """Key-access and file-open audit: the J5 evaluator (P8g included), the CMA-ES driver and the screen open no
    validation-day input and read no F11 field."""
    import builtins
    import json as _j
    from pathlib import Path as _P
    opened = []
    real_open, real_load, real_rb, real_rt = builtins.open, np.load, _P.read_bytes, _P.read_text
    monkeypatch.setattr(builtins, "open", lambda f, *a, **k: opened.append(str(f)) or real_open(f, *a, **k))
    monkeypatch.setattr(np, "load", lambda f, *a, **k: opened.append(str(f)) or real_load(f, *a, **k))
    monkeypatch.setattr(_P, "read_bytes", lambda self: opened.append(str(self)) or real_rb(self))
    monkeypatch.setattr(_P, "read_text", lambda self, *a, **k: opened.append(str(self)) or real_rt(self, *a, **k))
    # 1) evaluator, full __call__ with a stub simulate
    ev_, _ = _evaluator()
    _install(monkeypatch, model_b1=[REAL_B1])
    rho, rc = _cells()
    monkeypatch.setattr(E.M, "simulate", lambda *a, n_param_sets=1, **k: types.SimpleNamespace(
        clipped_share=np.zeros(n_param_sets), nonfinite=np.zeros(n_param_sets, bool),
        q_st=np.repeat(ev_.data["q"], n_param_sets, 0), v_st=np.repeat(ev_.data["v"], n_param_sets, 0),
        exit_flow=np.zeros((n_param_sets, 5, NB)), rho_cell=np.repeat(rho[None], n_param_sets, 0),
        rc_cell=np.repeat(rc[None], n_param_sets, 0)))
    monkeypatch.setattr(C, "a3_thresholds", lambda net: {})
    monkeypatch.setattr(C, "a3_shortfall", lambda p, thr: np.zeros(len(next(iter(p.values())))))
    ev_(np.full((2, 17), 0.5))
    # 2) CMA-ES driver (stub evaluator inside, synthetic seed)
    from vsl_lab.jobs import metanet_v5_calibrate as V5
    monkeypatch.setattr(V5, "SEEDS", [1])
    monkeypatch.setattr(V5, "BUDGET", 24)
    V5.restart(1, ev=lambda X, return_parts=False: (np.zeros(len(X)), [None] * len(X)), runs=tmp_path)
    # 3) the screen: F8 read through a dict that refuses F11; the gate call itself stubbed
    from vsl_lab.jobs import metanet_gate as G
    from vsl_lab.jobs import metanet_v5_freeze as FZ
    f8 = {"F8": {"B1": {"ci_r": [0.95, 1.05]}, "B2": {"ci_r": [0.9, 1.0]}}}
    facts5 = {"days": ["SYN0"], "per_day": {"SYN0": {"B1": [[100, 120]], "B2": [], "heavy_first": True}},
              "qualifying": {"heavy": {"B1": ["SYN0"], "B2": []}}}
    real_loads = _j.loads

    def fake_loads(s, *a, **k):
        return _NoF11(f8) if "F8" in s else real_loads(s, *a, **k)
    monkeypatch.setattr(FZ.json, "loads", fake_loads)
    monkeypatch.setattr(FZ.V5, "FACTS5", type("F", (), {"read_text": staticmethod(lambda: _j.dumps(facts5))})())
    monkeypatch.setattr(FZ, "screen_data_path", lambda: tmp_path / "scr.npz")
    np.savez(tmp_path / "scr.npz", days=np.array(["SYN0"]), v=np.zeros((1, 2, NB)), mv=np.zeros((1, 2, NB), bool))
    import hashlib as _h
    monkeypatch.setattr(FZ.V5, "RUNS5", tmp_path)
    (tmp_path / "calib_screen_data.sha256").write_text(_h.sha256((tmp_path / "scr.npz").read_bytes()).hexdigest())
    monkeypatch.setattr(C, "FACTS", type("F", (), {"read_text": staticmethod(lambda: '{"F8": 1, "F11": 2}')})())
    monkeypatch.setattr(G, "deterministic", lambda seed, ctx=None: {"rows": {"P1a": {"PASS": True}}})
    r = FZ.screen([0.5] * 17, True)
    assert r["P8_tolerance"] == 2 and r["Lc_k"]["B1"] == 0.95
    bad = [p for p in opened if "val_data" in p or "gate_det" in p or "gate_draw" in p or "gate_sto" in p]
    assert not bad, bad


def test_sensitivity_variants_change_and_restore(monkeypatch):
    """§B1.7 variants act through the module constants read at call time, and every constant is restored."""
    from vsl_lab.jobs import metanet_v5_freeze as FZ
    ev_, _ = _evaluator()
    _install(monkeypatch)                                              # a miss: P3-1 = 1 + eps*s
    rho, rc = _cells(backed=False)
    base = _day(ev_, rho, rc)["P3-1"][0]
    saved = (J.EPS, J.CAP_DUR, J.TAPER_A, dict(J.REALISM_CAP), dict(ev_.w))
    with FZ._variant(ev_, {"eps": 0.0}):
        assert _day(ev_, rho, rc)["P3-1"][0] == 1.0
    with FZ._variant(ev_, {"eps": 1.0}):
        assert _day(ev_, rho, rc)["P3-1"][0] == pytest.approx(1.0 + 2 * (base - 1.0))
    with FZ._variant(ev_, {"caps": 4 / 3, "taper": False, "equal_w": True}):
        assert J.CAP_DUR == pytest.approx(120.0) and J.taper(0.2, 80.0) == pytest.approx(0.2)
        assert set(ev_.w.values()) == {1.0}
    assert (J.EPS, J.CAP_DUR, J.TAPER_A, dict(J.REALISM_CAP), dict(ev_.w)) == saved


def test_best_point_report(monkeypatch):
    """§B2 report on a constructed day: a credited B1 hit that P11-k counts as unbacked is listed; relocation at
    c = 1 is counted; backing ratios and the screen medians are reported."""
    from vsl_lab.data import metanet_facts as Fm
    from vsl_lab.jobs import metanet_v5_freeze as FZ
    rho, rc = _cells(backed=True, extra=[(37, EV0 + 50, EV0 + 60)])
    o = types.SimpleNamespace(v_st=np.zeros((1, NS, NB)), rho_cell=rho[None], rc_cell=rc[None])
    monkeypatch.setattr(FZ.Q, "part1", lambda: {"c_s": {}})
    monkeypatch.setattr(FZ.Q, "simf", lambda *a, **k: o)
    monkeypatch.setattr(FZ, "params_of", lambda x: {"a": 1.0})
    monkeypatch.setattr(FZ.Q, "model_speeds", lambda *a, **k: (_speeds(REAL_B1), {}))
    monkeypatch.setattr(FZ.Q, "model_pairs", lambda *a, **k: {Q.PAIR["B1"]: [REAL_B1]})
    monkeypatch.setattr(FZ.Q, "p11_day", lambda *a, **k: {"B1": {"unbacked": True}, "B2": {"unbacked": False}})
    monkeypatch.setattr(Fm, "day_events", lambda d: {"B1": [list(REAL_B1)], "B2": []})
    monkeypatch.setattr(FZ, "screen", lambda x, sh: {"rows": {"P5b-1": {"median_r_diff": -0.01},
                                                                "P5b-2": {"median_r_diff": None},
                                                                "P9": {"median_S1_diff": 0.02}}})
    data = {"days": np.array(["SYN0"]), "d0": None, "d_o": None, "beta": None}
    r = FZ.best_point_report([0.5] * 17, data, NET)
    assert r["credited_hit_but_P11_unbacked"] == ["SYN0:B1"] and r["relocation_days_c_1"] == 1
    assert r["backing_cell_ratio_pct_5_25_50_75_95"][2] == pytest.approx(1.1)
    assert r["median_r_hat_minus_r"]["B1"] == -0.01 and r["median_S1_hat_minus_S1"] == 0.02


def test25_e2e_miss_dominance_two_bottlenecks(monkeypatch):
    """Claims 1-2 (§B1.6) on ≥ 3,000 randomized outcomes through day_items: two real-active bottlenecks, B1
    censored at the B2 onset; model episodes at both pairs with random backing. Every target item stays ≤ its
    reference value (no model episode, s = 1): 1 + ε on P3-k, 1 elsewhere."""
    real_b2 = [(108, 118)]
    ev_, _ = _evaluator(real_b2=real_b2, censor={0: 108})
    rng = np.random.default_rng(2025)                                   # non-protocol synthetic seed
    target = ["P3-1", "P4-1", "P5a-1", "P7a-1", "P3-2", "P4-2", "P5a-2", "P7a-2", "P7b", "P7c"]
    n = 0
    for _ in range(3000):
        def eps(k):
            out = []
            for _ in range(int(rng.integers(0, 3))):
                s0 = int(rng.integers(60, 170))
                out.append((s0, s0 + int(rng.integers(2, 30))))
            return sorted(out)
        b1, b2 = eps(1), eps(2)
        _install(monkeypatch, model_b1=b1, model_b2=b2, real_b2=real_b2)
        it = _day(ev_, *_cells(backed=bool(rng.random() < 0.5)))
        for r in target:
            cap = 1.0 + J.EPS if r.startswith("P3") else 1.0
            assert all(x is None or -1e-12 <= x <= cap + 1e-12 for x in it[r]), (r, it[r], b1, b2)
        n += 1
    assert n == 3000


def test38_p8g_ii_extra_on_hit_day(monkeypatch):
    """P8g (ii): on a real-active day where the gate's P3 agrees (any overlap, creditable or not), a model P_1
    episode overlapping no real one is charged; rev2: also when the only overlap is non-creditable."""
    ev_, _ = _evaluator()
    _install(monkeypatch, model_b1=[REAL_B1, (180, 190)])
    assert _day(ev_, *_cells(backed=True))["P8g"] == [1.0]
    assert _day(ev_, *_cells(backed=False))["P8g"] == [1.0]
    _install(monkeypatch, model_b1=[REAL_B1])
    assert _day(ev_, *_cells(backed=True))["P8g"] == [0.0]


def test_p2_side_creditable(monkeypatch):
    """The P_2 path with a creditable episode (cell 33 congested) gives P3-2 = 0; cell 34 alone does not."""
    real_b2 = [(140, 150)]
    ev_, _ = _evaluator(real_b2=real_b2)
    _install(monkeypatch, model_b1=[REAL_B1], model_b2=real_b2, real_b2=real_b2)
    rho, rc = _cells(backed=True)
    r33 = rho.copy(); r33[32, EV0 + 140:EV0 + 151] = 1.1
    assert _day(ev_, r33, rc)["P3-2"] == [0.0]
    r34 = rho.copy(); r34[33, EV0 + 140:EV0 + 151] = 1.1
    assert _day(ev_, r34, rc)["P3-2"] == [1.0 + J.EPS]


def test_batch_layout_two_sets_two_days(monkeypatch):
    """__call__ slices simulate's (P*D) outputs per parameter set: set 0 perfect, set 1 unbacked on both days."""
    ev_, d = _evaluator()
    ev_.days = [d, d + "b"]
    ev_.f["per_day"][d + "b"] = ev_.f["per_day"][d]
    ev_.ev[d + "b"] = ev_.ev[d]
    for k in ("q", "v", "mq", "mv"):
        ev_.data[k] = np.repeat(ev_.data[k], 2, 0)
    ev_.Fm, ev_.Pm = np.repeat(ev_.Fm, 2, 0), np.repeat(ev_.Pm, 2, 0)
    ev_.data["days"] = np.array(ev_.days)
    ev_.q = {"heavy": {"B1": ev_.days, "B2": []}, "both_q": [], "heavy_any": ev_.days, "P1c_days": ev_.days}
    _install(monkeypatch, model_b1=[REAL_B1])
    good, bad = _cells(backed=True), _cells(backed=False)

    def fake_sim(net, params, inp, n_param_sets=1, **k):
        rho = np.stack([good[0], good[0], bad[0], bad[0]])          # order: (set0,d0), (set0,d1), (set1,d0), (set1,d1)
        return types.SimpleNamespace(clipped_share=np.zeros(4), nonfinite=np.zeros(4, bool),
                                     q_st=np.repeat(ev_.data["q"][:1], 4, 0), v_st=np.repeat(ev_.data["v"][:1], 4, 0),
                                     exit_flow=np.zeros((4, 5, NB)), rho_cell=rho, rc_cell=np.stack([good[1]] * 4))
    monkeypatch.setattr(E.M, "simulate", fake_sim)
    monkeypatch.setattr(C, "a3_thresholds", lambda net: {})
    monkeypatch.setattr(C, "to_params", lambda X: {"x": X[:, 0]})
    monkeypatch.setattr(C, "a3_shortfall", lambda p, thr: np.zeros(2))
    Jv, parts = ev_(np.zeros((2, 17)), return_parts=True)
    assert Jv[0] == 0.0 and Jv[1] > 0.0
    assert parts[0]["J_d"] == [0.0, 0.0] and all(j > 0 for j in parts[1]["J_d"])


def test_j5eval_init_hash_and_days(tmp_path):
    """J5Eval.__init__: facts hash, masks hash and day list are enforced; record range is cells 25-39."""
    import hashlib as _h
    import json as _j
    days = ["SYN0"]
    np.savez_compressed(tmp_path / "metanet_v5_precal_masks.npz", F=np.zeros((1, NS, NB), bool),
                        P1c=np.zeros((1, NS, NB), bool))
    msha = _h.sha256((tmp_path / "metanet_v5_precal_masks.npz").read_bytes()).hexdigest()
    rec = {"B1": [], "B2": [], "censor": {}, "B1_long": None, "B2_long": None, "first": None, "heavy_first": False}
    f = tmp_path / "facts.json"
    f.write_text(_j.dumps({"days": days, "per_day": {"SYN0": rec}, "qualifying": {}, "rows": ["P3-1"],
                           "weights": {"P3-1": 1.0}, "masks_npz_sha256": msha}))
    sha = _h.sha256(f.read_bytes()).hexdigest()
    data = {"days": np.array(days)}
    ev_ = E.J5Eval(f, sha, data, NET, {})
    assert ev_.record == (24, 39) and ev_.rows == ["P3-1"]
    with pytest.raises(RuntimeError):
        E.J5Eval(f, "0" * 64, data, NET, {})
    with pytest.raises(RuntimeError):
        E.J5Eval(f, sha, {"days": np.array(["OTHER"])}, NET, {})
    (tmp_path / "metanet_v5_precal_masks.npz").write_bytes(b"x")
    with pytest.raises(RuntimeError):
        E.J5Eval(f, sha, data, NET, {})
