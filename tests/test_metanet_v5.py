"""METANET v5 J5 item functions (protocol v5 §B10; slice A: synthetic inputs only)."""
from __future__ import annotations

import hashlib
import json

import numpy as np
import pytest

from vsl_lab.jobs import metanet_j5 as J


def test27_taper_continuity():
    """Items continuous in Δonset across 45 and 90 min; full credit up to 45, miss value at 90."""
    for item in (0.0, 0.3, 1.0):
        assert J.taper(item, 45.0) == pytest.approx(item)
        assert J.taper(item, 90.0) == pytest.approx(1.0)
        xs = np.arange(0, 120.01, 0.5)
        ys = [J.taper(item, x) for x in xs]
        assert max(abs(np.diff(ys))) <= 0.5 / 45 + 1e-12


def test31_hinges():
    assert J.hinge("P1a", 0.10) == 0.0 and J.hinge("P1a", 0.30) == pytest.approx(1.0) and J.hinge("P1a", 0.20) == pytest.approx(0.5)
    assert J.hinge("P1b", 0.15) == 0.0 and J.hinge("P1b", 0.60) == pytest.approx(1.0)
    assert J.p1c_hinge(0.30, n1=0.40, n2=0.30) == 0.0
    assert J.p1c_hinge(0.40, n1=0.40, n2=0.30) == pytest.approx(1.0)
    assert J.p1c_hinge(0.31, n1=0.30, n2=0.30) == pytest.approx(0.5)          # s_d floor 0.02
    assert J.realism("P1a_ff", 0.6) == 1.0 and J.realism("P1b_ff", 0.3) == pytest.approx(0.5)
    assert J.hinge("P1a", float("nan")) is None


def _cong(n_bins, cells, bins):
    c = np.zeros((39, n_bins), bool)
    for x in cells:
        c[x - 1, bins] = True
    return c


def test40_creditability_head_rule():
    nb = 40
    cond = np.zeros(nb, bool); cond[10:20] = True
    ep = (10, 19)
    assert J.creditable(ep, cond, _cong(nb, (26, 27, 28), list(range(10, 20))), "B1")
    assert not J.creditable(ep, cond, _cong(nb, (27,), list(range(10, 20))), "B1")           # cell 27 alone
    assert not J.creditable(ep, cond, _cong(nb, (25, 26), list(range(10, 20))), "B1")        # 4->3 drop queue
    assert J.creditable(ep, cond, _cong(nb, (26, 27, 28), list(range(10, 15))), "B1")        # exactly 50 %
    assert not J.creditable(ep, cond, _cong(nb, (26, 27, 28), list(range(10, 14))), "B1")
    assert J.creditable(ep, cond, _cong(nb, (33,), list(range(10, 20))), "B2")
    assert not J.creditable(ep, cond, _cong(nb, (34,), list(range(10, 20))), "B2")
    assert not J.creditable((30, 35), cond, _cong(nb, (26, 27, 28), list(range(nb))), "B1")  # no qualifying bin


def test_p3_items():
    real = [(100, 120)]
    assert J.p3_item(real, [(105, 118)], [True], s=0.3) == 0.0
    assert J.p3_item(real, [(105, 118)], [False], s=1.0) == pytest.approx(1.5)
    assert J.p3_item(real, [], [], s=0.0) == 1.0
    assert J.p3_item([], [(5, 9)], [False], s=0.0) == 1.0 and J.p3_item([], [], [], s=0.0) == 0.0


def test28_shaping():
    real = [(100, 120)]
    wins = J.windows(real, None, 228)
    assert J.s_override(real, [(110, 115)], [False], wins)                     # overlapping unbacked dip
    assert J.s_override(real, [(110, 115), (10, 20)], [False, True], wins)     # backed extra elsewhere: still 1
    assert J.s_override(real, [(84, 85)], [False], wins)                       # unbacked, in a g window, no overlap
    assert not J.s_override(real, [(10, 20)], [False], wins)                   # far away: leaves s to g, h
    assert J.shaping(-40.0, 0.0, False) == 1.0 and J.shaping(0.0, 1.0, False) == 0.0
    v_u = np.full(228, 60.0); v_d = np.full(228, 60.0)
    m = J.margins(v_u, v_d)
    assert J.g_value(m, wins) == pytest.approx(-20.0)
    v_u[100:110] = np.nan
    assert np.isneginf(J.margins(v_u, v_d)[105])
    v_u[:] = 40.0; v_d[:] = 60.0
    assert J.g_value(J.margins(v_u, v_d), wins) == 0.0                         # v_u = 40.0 edge: margin 0
    # censored B1 window ends at t_c
    assert max(J.windows([(100, 150)], {0: 110}, 228)[0]) == 110
    w2 = J.windows([(40, 50), (100, 150)], {1: 110}, 228)                     # censoring per episode
    assert max(w2[0]) == 62 and max(w2[1]) == 110
    assert len(J.windows([(10, 20), (100, 110)], None, 228)) == 2             # per-episode windows


def test26_parity_numbers():
    """B2 on the calibration counts: 9 active days (1 episode, heavy, in P5c's set), 13 inactive."""
    n = dict(P3=22, P4=9, P5a=9, P7a=9, P5c=9, X=13)
    U, w = J.parity_omega([dict(e=1, heavy=True, both=True)] * 9, n)
    assert U == pytest.approx(1 / 22 + 4 / 9) and w == pytest.approx(52 / 9)
    # one extra on a real-inactive day raises the P3-2 + X-2 numerator by exactly U
    p3_before = [0.0] * 22; x_before = [0.0] * 13
    p3_after = [1.0] + [0.0] * 21; x_after = [1.0] + [0.0] * 12
    num = lambda p3, x: 1 * np.mean(p3) + w * np.mean(x)
    assert num(p3_after, x_after) - num(p3_before, x_before) == pytest.approx(U, abs=1e-12)


def test25_dominance_k_rows_random():
    """Claim 1 (per (k, d)): P3-k, P4-k, P7a-k items never exceed the no-episode, s = 1 reference."""
    rng = np.random.default_rng(12345)          # non-protocol synthetic seed
    for _ in range(3000):
        real = sorted({(int(s), int(s) + int(rng.integers(3, 30))) for s in rng.integers(20, 180, rng.integers(1, 3))})
        model = [(int(s), int(s) + int(rng.integers(1, 40))) for s in rng.integers(0, 200, rng.integers(0, 4))]
        credit = [bool(c) for c in rng.integers(0, 2, len(model))]
        s = float(rng.random())
        t_c = int(rng.integers(30, 220)) if rng.random() < 0.3 else None
        assert J.p3_item(real, model, credit, s) <= J.p3_item(real, [], [], 1.0)
        assert all(a <= 1.0 for a in J.p4_items(real, model, credit))
        assert J.p7a_item(real, model, credit, t_c) <= 1.0
        assert J.p5a_item(real, model, credit, 1800.0, [float(rng.uniform(1000, 3000)) for _ in model]) <= 1.0


def test_aggregation_and_unscored():
    rows = {"a": [0.0, 1.0], "b": [None, None], "c": [0.5]}
    assert J.j5(rows, {"a": 1, "b": 5, "c": 2}) == pytest.approx((0.5 + 2 * 0.5) / 3)


def test35_facts_hash(tmp_path):
    f = tmp_path / "facts.json"
    f.write_text(json.dumps({"x": 1}))
    good = hashlib.sha256(f.read_bytes()).hexdigest()
    assert J.load_facts(f, good) == {"x": 1}
    with pytest.raises(RuntimeError):
        J.load_facts(f, "0" * 64)


def test_p7c_item_merge_effect():
    """Disclosed bound (§B1.6): a non-matching B1 jam merging with the model's B2 episode raises P7c."""
    real1, real2 = [(100, 111)], [(104, 111)]
    base = J.p7c_item(real1, real2, [], [(104, 111)])
    worse = J.p7c_item(real1, real2, [(80, 140)], [(104, 111)])
    assert worse > base
    assert J.p7c_item(real1, real2, [], []) == 1.0


def test_v5_driver_with_stub_evaluator(tmp_path, monkeypatch):
    """Driver mechanics only (stub J5, synthetic seed 1): budget, counts, state file, continuation, seed guard."""
    from vsl_lab.jobs import metanet_v5_calibrate as V5

    class Stub:
        def __call__(self, X, return_parts=False):
            J = np.sum((X - 0.3) ** 2, axis=1)
            J[0] = 10.5                                              # an A3 violator
            parts = [None] + [{"rows": {}, "J_d": [], "any_creditable_B1": bool(i % 2)} for i in range(1, len(X))]
            return (J, parts) if return_parts else J

    monkeypatch.setattr(V5, "SEEDS", [1])
    monkeypatch.setattr(V5, "BUDGET", 36)
    r = V5.restart(1, ev=Stub(), runs=tmp_path)
    assert r["evals"] >= 36 and r["counts"]["a3"] == 3 and r["admissible"]
    assert r["counts"]["first_a3_feasible"] == 2
    r2 = V5.restart(1, continue_to=60, ev=Stub(), runs=tmp_path)
    assert r2["evals"] >= 60 and r2["best_J5"] <= r["best_J5"]
    with pytest.raises(SystemExit):
        V5.restart(7192099, ev=Stub(), runs=tmp_path)
