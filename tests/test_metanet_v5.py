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
    """Claim 1 (per (k, d)) on the pure P3-k and P4-k items; P5a/P7a are checked through the evaluator (e2e tests)."""
    rng = np.random.default_rng(12345)          # non-protocol synthetic seed
    for _ in range(3000):
        real = sorted({(int(s), int(s) + int(rng.integers(3, 30))) for s in rng.integers(20, 180, rng.integers(1, 3))})
        model = [(int(s), int(s) + int(rng.integers(1, 40))) for s in rng.integers(0, 200, rng.integers(0, 4))]
        credit = [bool(c) for c in rng.integers(0, 2, len(model))]
        s = float(rng.random())
        t_c = int(rng.integers(30, 220)) if rng.random() < 0.3 else None
        assert J.p3_item(real, model, credit, s) <= J.p3_item(real, [], [], 1.0)
        assert all(a <= 1.0 for a in J.p4_items(real, model, credit))


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


def test37_stephalving_conjunction():
    from vsl_lab.jobs.metanet_v5_freeze import stephalving_pass
    s = {"B1": ["a", "b"], "B2": ["a"]}
    assert stephalving_pass((0.5, 0.51), (0.2, 0.2), s, s)["PASS"]
    assert not stephalving_pass((0.5, 0.5), (0.2, 0.2), s, {"B1": ["a"], "B2": ["a"]})["PASS"]      # one-day flip, ΔJ5 = 0
    assert not stephalving_pass((0.5, 0.5), (0.2, 0.211), s, s)["PASS"]                              # J_v4 alone
    assert not stephalving_pass((0.5, 0.53), (0.2, 0.2), s, s)["PASS"]


def test39_route_labels():
    from vsl_lab.jobs.metanet_v5_freeze import STOPS, route
    ok = {s: True for s in STOPS}
    assert route(ok)["route"] == "continue to the ensemble step"
    r = route(dict(ok, **{"P11-k": False}))
    assert r["route"] == "STOP (P11-k)"
    assert r["stops"]["in-sample screen"] == "not run (route stopped at P11-k)"
    assert r["stops"]["step-halving"] == "PASS"
    assert route({"no admissible restart": False})["route"] == "STOP (no admissible restart)"
    with pytest.raises(ValueError):
        route({"no admissible restart": True})


def test36_gate_guard():
    from vsl_lab.jobs.metanet_v5_gate import PROTOCOL, guard
    rec = {"protocol": PROTOCOL, "stage": "freeze", "route": "continue to the plant gate", "nominal": 7192013,
           "members": [7192011], "candidates": [7192011, 7192015]}
    now = {"code": "c1", "freeze_blob": "b1"}
    ok = dict(audit_committed=True, first_record=True, fix_names_record=False, lock=None, now=now,
              fix_rerun_for_seed=False)
    assert guard(rec, None, **ok) == 7192013 and guard(rec, 7192011, **ok) == 7192011
    for bad in (dict(ok, audit_committed=False), dict(ok, first_record=False)):
        with pytest.raises(SystemExit):
            guard(rec, None, **bad)
    assert guard(rec, None, **dict(ok, first_record=False, fix_names_record=True)) == 7192013
    with pytest.raises(SystemExit):
        guard(rec, 7192015, **ok)                                        # recorded candidate, not a member
    with pytest.raises(SystemExit):
        guard(dict(rec, route="STOP (P11-k)"), None, **ok)
    lock = {"7192013": {"code": "c0", "freeze_blob": "b1"}}               # crashed / killed earlier run, other code
    with pytest.raises(SystemExit):
        guard(rec, None, **dict(ok, lock=lock))
    assert guard(rec, None, **dict(ok, lock=lock, fix_rerun_for_seed=True)) == 7192013
    assert guard(rec, None, **dict(ok, lock={"7192013": now})) == 7192013  # plain re-run, unchanged hashes


def test_members_rule():
    from vsl_lab.jobs.metanet_v5_gate import candidates, members
    rs = [{"seed": s, "admissible": True, "best_J5": j, "best_x": [x] * 17}
          for s, j, x in ((1, 0.30, 0.5), (2, 0.305, 0.9), (3, 0.31, 0.1), (4, 0.302, 0.6), (5, 0.40, 0.0))]
    c = candidates(rs, 1, [0, 1, 2, 3, 4])
    assert [x["seed"] for x in c] == [2, 4]                              # 3 and 5 outside 1.02; 2 farther than 4
    m = members(c, {2: dict(stephalving=True, P11=True, screen=True, F_hat=False),
                    4: dict(stephalving=True, P11=True, screen=True, F_hat=True)})
    assert m == {"gridded": [2, 4], "members": [4]}


def test_c1_inert_reports():
    from vsl_lab.jobs.metanet_v5_freeze import c1_inert
    G = [0.8, 1.0, 1.2]
    rows = []
    for c1 in G:
        for c2 in G:
            rows.append({"day": "a", "c1": c1, "c2": c2, "E1": True, "O1": True, "b1cells_qual": False})
            rows.append({"day": "b", "c1": c1, "c2": c2, "E1": c1 < 1.1, "O1": c1 < 1.1, "b1cells_qual": True})
            rows.append({"day": "c", "c1": c1, "c2": c2, "E1": True, "O1": True, "b1cells_qual": True})
    r = c1_inert(rows, 1.2)
    assert r["c1_inert_days"] == ["a"]                       # c: same E/O but B1 cells congested -> not inert
    assert r["upper_half_c1_inert_days"] == ["a", "c"]       # b changes inside [1.0, 1.2]


def test_finalize_stop_order(monkeypatch):
    """Stops run in order and stop at the first failure; later stops are not evaluated (stubbed, no simulation)."""
    from vsl_lab.jobs import metanet_v5_freeze as FZ
    from vsl_lab.jobs import metanet_calibrate as Cm
    called = []
    rs = [{"seed": 7192010, "admissible": True, "best_J5": 0.4, "best_x": [0.5] * 17, "best_rows": {}},
          {"seed": 7192011, "admissible": True, "best_J5": 0.3, "best_x": [0.4] * 17, "best_rows": {}}]
    monkeypatch.setattr(FZ, "restarts", lambda: rs)
    monkeypatch.setattr(Cm, "load_data", lambda: {"days": []})
    monkeypatch.setattr(FZ.M, "build_network", lambda v: None)
    monkeypatch.setattr(FZ.V5, "FACTS5_SHA", type("P", (), {"read_text": staticmethod(lambda: "abc  f")})())
    monkeypatch.setattr(FZ, "stephalving", lambda x, **k: called.append("sh") or {"PASS": True})
    monkeypatch.setattr(FZ, "p11_freeze", lambda x, d, n: called.append("p11") or {"PASS": False})
    monkeypatch.setattr(FZ, "screen", lambda *a: called.append("screen") or {"PASS": True})
    monkeypatch.setattr(FZ, "spread_v5", lambda *a: called.append("spread") or {"usable_spread": True})
    r = FZ.finalize()
    assert r["nominal"] == 7192011 and r["route"] == "STOP (P11-k)" and called == ["sh", "p11"]
    assert r["stops"]["§4.7 (7)(b)"].startswith("not run")
    monkeypatch.setattr(FZ, "restarts", lambda: [dict(x, admissible=False) for x in rs])
    assert FZ.finalize()["route"] == "STOP (no admissible restart)"


def test_v5_gate_bindings_and_verdict(tmp_path, monkeypatch):
    import json as _j
    from vsl_lab.jobs import metanet_gate as G
    from vsl_lab.jobs import metanet_v5_calibrate as V5
    from vsl_lab.jobs import metanet_v5_gate as VG
    rec = {"nominal": 7192013, "members": [7192011], "frozen_params": {"a": 1.0}, "member_params": {"7192011": {"a": 2.0}},
           "capacity_factors": {"nominal": {"spread_used": "Tobit"}}, "benchmarks": {}, "route": "continue",
           "stops": {"step-halving": "PASS"}}
    before = (G.plant, G.freeze, G.SEED_DRAW, G.SEED_BOOT, G.RUNS)
    with VG.bindings(rec) as g:
        assert g.SEED_DRAW == 7192301 and g.SEED_BOOT == 7192300 and g.RUNS == V5.RUNS5
        assert g.plant(None) == (7192013, {"a": 1.0}) and g.plant(7192011)[1] == {"a": 2.0}
        with pytest.raises(SystemExit):
            g.plant(7192015)
    assert (G.plant, G.freeze, G.SEED_DRAW, G.SEED_BOOT, G.RUNS) == before
    monkeypatch.setattr(V5, "RUNS5", tmp_path)
    f = tmp_path / "rec.json"
    f.write_text(_j.dumps(rec))
    monkeypatch.setattr(VG, "FREEZE5", f)
    (tmp_path / "gate_det_7192013.json").write_text(_j.dumps({"deterministic_PASS": True, "failed": []}))
    (tmp_path / "gate_sto_7192013.json").write_text(_j.dumps({"stochastic_PASS": True, "failed": []}))
    assert VG.verdict()["outcome"] == "PASS, substitute spread"
    (tmp_path / "gate_sto_7192013.json").write_text(_j.dumps({"stochastic_PASS": False, "failed": ["P8s"]}))
    assert VG.verdict()["outcome"].startswith("FAIL (stochastic")


def test_head_cell():
    nb = 20
    cond = np.zeros(nb, bool); cond[5:10] = True
    c = np.zeros((39, nb), bool)
    c[25:30, 5:8] = True          # cells 26-30 congested on bins 5-7 -> head 30
    c[25:28, 8:10] = True         # cells 26-28 on bins 8-9 -> head 28
    assert J.head_cell((5, 9), cond, c, "B1") == 30
    c2 = np.zeros((39, nb), bool); c2[32, :] = True
    assert J.head_cell((5, 9), cond, c2, "B2") == 33
    assert J.head_cell((5, 9), cond, np.zeros((39, nb), bool), "B1") is None


def test24_zero_cost_items():
    """Item-level zero cost: model episodes equal to the real ones, all creditable, equal C4 and durations -> every
    target item 0 (the end-to-end variant through the observation operator is pending, see the checkpoint)."""
    real = [(100, 130)]
    assert J.p3_item(real, real, [True], s=1.0) == 0.0
    assert J.p4_items(real, real, [True]) == [0.0]
    assert J.p7c_item(real, [], real, []) == 0.0
    assert J.p7b_item(0, 0.0) == 0.0
    assert J.j5({"a": [0.0], "b": [0.0, 0.0]}, {"a": 1.0, "b": 5.8}) == 0.0
    assert J.p3_item(real, real, [False], s=1.0) == 1.5                   # no backing: the miss value


def test_integrity_guards(tmp_path):
    """§B1.1/§B8: manifests verified; a tampered or missing file stops the batch; screen-data equality is NaN-safe."""
    import hashlib as _h
    import json as _j
    from vsl_lab.jobs import metanet_v5_calibrate as V5
    from vsl_lab.jobs.metanet_v5_freeze import same_array
    root = tmp_path / "raw"
    (root / "sub").mkdir(parents=True)
    (root / "a.json").write_text("1")
    (root / "sub" / "b.json").write_text("2")
    man = tmp_path / "m.sha256"
    man.write_text("".join(f"{_h.sha256(p.read_bytes()).hexdigest()}  ./{p.relative_to(root)}\n"
                           for p in sorted(root.rglob("*")) if p.is_file()))
    V5.verify_manifest(man, root)
    (root / "sub" / "b.json").write_text("3")
    with pytest.raises(RuntimeError):
        V5.verify_manifest(man, root)
    # Mayfly per-day digests
    mr = tmp_path / "mndot"
    dd = mr / "mayfly" / "2023" / "20230118"
    dd.mkdir(parents=True)
    for n in ("1.counts.json", "1.occupancy.json"):
        (dd / n).write_text(n)
    lines = [f"{_h.sha256(f.read_bytes()).hexdigest()}  {f.relative_to(mr)}" for f in sorted(dd.iterdir())]
    mm = tmp_path / "mayfly.json"
    mm.write_text(_j.dumps({"root": str(mr), "per_day": {"20230118": {
        "n_files": 2, "sha256_of_lines": _h.sha256(("\n".join(lines) + "\n").encode()).hexdigest()}}}))
    V5.verify_mayfly(mm)
    (dd / "2.counts.json").write_text("x")                         # an added file
    with pytest.raises(RuntimeError):
        V5.verify_mayfly(mm)
    a = np.array([1.0, np.nan]); b = a.copy()
    assert same_array(a, b) and not same_array(a, np.array([1.0, 2.0])) and same_array(np.array([1, 2]), np.array([1, 2]))
