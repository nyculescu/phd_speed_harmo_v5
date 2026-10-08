"""Unit tests for protocol v4 (docs/plans/day_pattern_metanet_protocol_v4.md §A10). Synthetic inputs only; the A3
thresholds read the committed c_s (v3 raw file, sha256-verified)."""
from __future__ import annotations

import math
import re
from pathlib import Path

import numpy as np
import pytest

from vsl_lab.jobs import metanet_calibrate as C
from vsl_lab.jobs import metanet_postcal as Q
from vsl_lab.plants import metanet as M

NB = M.N_BINS
T = M.T_S_V4
REPO = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def net4():
    return M.build_network("v4")


def feasible(**kw) -> dict:
    """An explicit A3-feasible parameter set (midpoint_params violates G1 at 73.7 km/h)."""
    p = M.midpoint_params(g4=True)
    p.update({"vf1": 125.0, "vf2": 125.0, "vf3": 120.0, "a1": 2.5, "a2": 2.5, "a3": 2.5, "rc4": 30.0, "a4": 2.5})
    p.update(kw)
    return p


def inputs(net, d0=2600.0, ramp=60.0, beta=0.02, D=1):
    ne, nx = len(net.entrances), len(net.exits)
    return M.Inputs(d0=np.full((D, NB), d0), d_o=np.full((D, ne, NB), ramp), beta=np.full((D, nx, NB), beta))


# ---------------------------------------------------------------- test 9: table, groups, B cells, variants
KM_FROM = [-8.413, -8.074, -7.670, -7.233, -6.835, -6.221, -5.896, -5.4495, -5.003, -4.576, -4.034, -3.492, -2.901,
           -2.300, -1.866, -1.435, -1.005, -0.574, 0.000, 0.466, 0.9105, 1.355, 1.730, 2.390, 2.844, 3.297, 3.751,
           4.055, 4.496, 4.9365, 5.377, 5.818, 6.118, 6.5675, 7.017, 7.518, 8.012, 8.505, 8.999]
LAM = [2] * 18 + [3, 3, 3, 2, 4, 3, 3, 3] + [2] * 13
STATION_CELL = {"S453": 1, "S455": 3, "S456": 4, "S457": 6, "S458": 9, "S459": 12, "S460": 14, "S461": 17,
                "S462": 18, "S1770": 19, "S1771": 21, "S1772": 22, "S1773": 25, "S1147": 27, "S1140": 32,
                "S1141": 35, "S1610": 39}
CORR = {"S453": (["E1"], ["X1"]), "S461": ([], ["X8"]), "S1770": ([], ["X9"]), "S1771": ([], ["X10"])}
ENTR_CELL = {"E1": 1, "E2": 4, "E3": 5, "E4": 7, "E5": 10, "E6": 13, "E7": 14, "E8": 15, "E9": 19, "E10": 23,
             "E11": 23, "E12": 23, "E13": 28, "E14": 33, "E15": 36}
EXIT_CELL = {"X1": 1, "X2": 2, "X3": 5, "X4": 8, "X5": 11, "X67": 13, "X8": 17, "X9": 19, "X10": 21, "X11": 26,
             "X12": 31, "X13": 34, "X14": 38, "X15": 39}


def test9_table_groups_b_cells(net4):
    assert net4.N == 39
    assert np.all(np.abs(net4.km_from - np.array(KM_FROM)) <= 0.0005)          # +-0.5 m
    assert abs(net4.km_to[-1] - 9.390) < 1e-9 and np.allclose(net4.km_from[1:], net4.km_to[:-1])
    assert list(net4.lam.astype(int)) == LAM
    assert round(1000 * net4.L.min()) == 300 and round(1000 * net4.L.max()) == 660
    assert "".join(str(int(g) + 1) for g in net4.group) == "1" * 18 + "2" * 8 + "3" * 9 + "4" * 4
    assert [i + 1 for i in net4.b1_cells] == [28, 29, 30, 31] and net4.head1 + 1 == 28
    assert [i + 1 for i in net4.b2_cells] == [33, 34] and net4.phi_cell + 1 == 23
    assert [m["length_m"] for m in net4.merge_log] == [23, 31, 80, 173, 249]
    assert [m["ramps_now_inside"] for m in net4.merge_log] == [["E12"], ["E1"], ["E11"], ["X15"], ["X67"]]
    for s in net4.stations:
        assert s["cell"] + 1 == STATION_CELL[s["id"]]
        assert (s["corr_entr"], s["corr_exit"]) == CORR.get(s["id"], ([], []))
    assert {e["id"]: e["cell"] + 1 for e in net4.entrances} == ENTR_CELL
    assert {x["id"]: x["cell"] + 1 for x in net4.exits} == EXIT_CELL
    assert {e["id"] for e in net4.entrances if not e["merging"]} == {"E9", "E10", "E11", "E15"}   # V9: E15 adds


def test9_build_checks_and_variants(net4):
    scaled = set(net4.b1_cells) | set(net4.b2_cells)
    assert not scaled & {s["cell"] for s in net4.stations}                     # check (1)
    weave, sa, sc = (M.build_network(v) for v in ("v4_weave", "v4_step_a", "v4_step_c"))
    for n in (weave, sa, sc):
        assert list(n.km_from[:35]) == pytest.approx(list(net4.km_from[:35]))
        assert n.b1_cells == net4.b1_cells and n.b2_cells == net4.b2_cells
    assert list(weave.lam[32:34]) == [3, 3]
    assert list(weave.group) == list(net4.group)                       # weave changes only lambda (and E14's event)
    assert {e["id"] for e in weave.entrances if not e["merging"]} == {"E9", "E10", "E11", "E14", "E15"}
    for n in (weave, sa, sc):
        for st in n.stations:
            assert st["cell"] + 1 == STATION_CELL[st["id"]] and (st["corr_entr"], st["corr_exit"]) == CORR.get(st["id"], ([], []))
    assert list(sa.lam[35:39]) == [3, 3, 3, 3]
    assert sc.N == 35 and not any(g == 3 for g in sc.group)


def test9_a3_thresholds(net4):
    thr = C.a3_thresholds(net4)
    exp = {0: 75.2829, 1: 67.6900, 2: 64.3738, 3: 72.9309}
    assert set(thr) == set(exp)
    for g, t in exp.items():
        assert abs(thr[g] - t) < 1e-4, (g, thr[g])


# ---------------------------------------------------------------- test 2: numerics
def test2_conditions_and_gate(net4):
    c = M.v4_conditions(net4, T)
    assert c["a"] == pytest.approx(0.208, abs=5e-4) and c["b"] == pytest.approx(0.234, abs=5e-4)
    assert c["c"] == pytest.approx(0.075) and c["d"] == pytest.approx(0.541, abs=5e-4)
    assert c["f"] == pytest.approx(0.713, abs=5e-4)
    assert c["d_cell"] == 1 and c["f_cell"] == 1
    r = M.vn_scan(T, net4.L)
    assert r["PASS"] and r["n_stable"] > 0 and r["worst_stable_growth"] == pytest.approx(1.10e-5, rel=0.05)
    assert r["worst_state"]["kind"] == "floorVp"
    bad = M.vn_scan(1.25, net4.L)                              # the gate can fail: 1.25 s fails it
    assert not bad["PASS"] and bad["n_stable_above_eps"] == 217
    assert bad["worst_stable_growth"] == pytest.approx(4.95e-3, rel=0.02)
    for Tbad in (5.0, 2.5):                                    # (ii): the v4 table rejects v3's steps
        with pytest.raises(ValueError, match="§A2"):
            M.simulate(net4, feasible(), inputs(net4), T_s=Tbad)
    # the ladder rule picks 0.75 s: 1.25 and 1.0 fail (a)
    ok = [t for t in M.T_LADDER_V4 if M.v4_conditions(net4, t)["a"] <= 0.25]
    assert max(ok) == 0.75


def test2_shock_no_negative_speed_or_overflow(net4):
    shape = np.where(np.arange(NB) % 6 < 3, 6000.0, 0.0)
    ne, nx = len(net4.entrances), len(net4.exits)
    inp = M.Inputs(d0=shape[None, :].copy(), d_o=np.full((1, ne, NB), 1500.0), beta=np.full((1, nx, NB), 0.0))
    o = M.simulate(net4, feasible(nu=90.0, kappa=5.0, tau=10.0, delta_m=4.0, phi=4.0), inp)
    assert np.all(o.v_cell >= M.V_MIN - 1e-9) and np.all(o.rho_cell <= M.RHO_MAX + 1e-9) and not o.nonfinite.any()


# ---------------------------------------------------------------- tests 11, 17, 20: heads, theta1, station cells
def _b1_overload(net4, d0, e13, a, b):
    ne = len(net4.entrances)
    i13 = [e["id"] for e in net4.entrances].index("E13")
    d_o = np.full((1, ne, NB), 60.0)
    d_o[:, i13, a:b] = e13
    inp = M.Inputs(d0=np.full((1, NB), d0), d_o=d_o, beta=np.full((1, len(net4.exits), NB), 0.02))
    o = M.simulate(net4, feasible(theta1=0.8), inp)
    return o.rho_cell[0] > o.rc_cell[0]


def test11_overloaded_b1_queue_starts_in_28_and_reaches_25(net4):
    """Deep overload (d0 3,000, E13 1,800 veh/h for 80 bins): the head is cell 28 and the queue propagates upstream
    to cell 25 (S of Highwood Ave), later than at the head. (Under this deep overload METANET's convection also lifts
    cell 29 above rho_cr part of the time, as v3's test 17 documented; test 17 uses a moderate overload.)"""
    over = _b1_overload(net4, 3000.0, 1800.0, 120, 200)
    first = {c: int(np.argmax(over[c - 1])) if over[c - 1].any() else None for c in (25, 26, 27, 28, 29)}
    assert first[28] is not None and first[28] == min(v for v in first.values() if v is not None)
    assert first[25] is not None and first[25] > first[28]


def test17_moderate_overload_head_in_28_cells_29_31_free(net4):
    over = _b1_overload(net4, 2600.0, 1500.0, 120, 170)
    assert over[27, 125:170].mean() > 0.5                                  # cell 28 (H1) congested
    assert over[28:31, 125:170].mean() < 0.05                               # cells 29-31 free-flowing


def test17_theta1_scales_only_cell_28(net4):
    o = M.simulate(net4, feasible(theta1=0.8), inputs(net4, d0=1500.0), c1=1.1)
    rc = o.rc_cell[0, :, 20]
    assert rc[27] == pytest.approx(0.8 * 1.1 * 30.0) and np.allclose(rc[28:31], 1.1 * 30.0)


def test20_station_cells_never_scaled(net4):
    sc = [s["cell"] for s in net4.stations]
    for c in (0.8, 1.2):
        o = M.simulate(net4, feasible(), inputs(net4, d0=1500.0), c1=c, c2=c)
        o1 = M.simulate(net4, feasible(), inputs(net4, d0=1500.0))
        assert np.allclose(o.rc_cell[0, sc, 20], o1.rc_cell[0, sc, 20])
        assert np.allclose(o.rc_cell[0, net4.b2_cells, 20], c * o1.rc_cell[0, net4.b2_cells, 20])


# ---------------------------------------------------------------- test 15: relocation domain 35-39 and c2*
def _b2_sweep(net4):
    """Pinned smooth scenario: d0 3,600, E14 900, E15 300 veh/h, 90-min ramp to the 15:30-18:00 peak, c1 = 1.2."""
    ne, nx = len(net4.entrances), len(net4.exits)
    h = 4.0 + np.arange(NB) / 12.0
    shape = np.clip(0.5 + 0.5 * (h - 14.0) * 60 / 90, 0.5, 1.0) * (h < 18) + 0.5 * (h >= 18)
    ids = [e["id"] for e in net4.entrances]
    d_o = np.full((1, ne, NB), 50.0) * shape
    d_o[0, ids.index("E14")] = 900.0 * shape
    d_o[0, ids.index("E15")] = 300.0 * shape
    inp = M.Inputs(d0=(3600.0 * shape)[None, :], d_o=d_o, beta=np.zeros((1, nx, NB)))
    c2s = np.round(np.arange(0.80, 1.2001, 0.05), 2)
    o = M.simulate(net4, {k: np.full(len(c2s), v) for k, v in feasible().items()}, inp, n_param_sets=len(c2s),
                   c1=1.2, c2=c2s)
    return c2s, o


def test15_relocation_on_cells_35_39_and_c2_star(net4):
    c2s, o = _b2_sweep(net4)
    first = net4.b2_cells[-1] + 1
    assert first + 1 == 35
    written, refined, binds = {}, {}, {}
    for i, c2 in enumerate(c2s):
        rho, rc = o.rho_cell[i][:, 12:], o.rc_cell[i][:, 12:]
        assert (rho[net4.b2_cells] > rc[net4.b2_cells]).any() or c2 >= 1.15     # B2 congested over the low range
        written[float(c2)] = Q.relocation({}, rho, rc, first, exclude_adjacent_jam=False)["flag"]
        refined[float(c2)] = Q.relocation({}, rho, rc, first, exclude_adjacent_jam=True)["flag"]
        free_b2 = ~(rho[first - 1] > rc[first - 1])                                 # independent re-derivation
        binds[float(c2)] = any(((np.convolve(((rho[c] > rc[c]) & free_b2).astype(int), np.ones(3, int),
                                             mode="valid")) == 3).any() for c in range(first, net4.N))
    # as written, the acceleration-zone transient next to an active B2 jam flags every c2 (2026-10-07 finding)
    assert all(written.values())
    # with the refinement, the flag first fires at 1.10 and not below; c2* = 1.05
    assert refined == binds
    c_first = min(c for c, b in refined.items() if b)
    assert c_first == 1.10 and not any(refined[c] for c in refined if c < c_first)
    assert Q.c2_star(refined, grid=c2s) == 1.05
    assert Q.c2_star({0.8: True, 0.81: False}, grid=[0.8, 0.81]) is None
    free = np.zeros((net4.N, 216))
    assert Q.relocation({Q.RELOC_PAIR: [(10, 20)]}, free, np.ones(net4.N), first) == {"flag": True, "cells": [],
                                                                                   "pair": True}
    assert not Q.relocation({("S1140", "S1141"): [(10, 20)]}, free, np.ones(net4.N), first)["flag"]


# ---------------------------------------------------------------- test 18b: clipping at T and T/2
def test18b_clipping_floor_classification_and_t_half(net4):
    a = M.simulate(net4, feasible(), inputs(net4, d0=1800.0), T_s=T)
    b = M.simulate(net4, feasible(), inputs(net4, d0=1800.0), T_s=T / 2)
    assert abs(a.q_st[0, :, 30:].mean() - b.q_st[0, :, 30:].mean()) / a.q_st[0, :, 30:].mean() < 0.01
    # forced floors (the classification code does not depend on T; a 5-s toy is allowed outside v4 tables):
    # an 8-cell toy with a deep jam behind a weak section (c1 = 0.3) gives both floor kinds.
    n = 8
    kf = np.arange(n) * 0.4
    st = [{"id": f"S{i}", "km": kf[i] + 0.4, "label": "", "dets": [], "cell": i, "corr_entr": [], "corr_exit": []}
          for i in range(n)]
    toy = M.Net("toy", kf, kf + 0.4, np.full(n, 0.4), np.full(n, 2.0), np.full(n, 2), [], [], [], st, -1, [6, 7], [],
                head1=6)
    p = M.midpoint_params() | {"nu": 90.0, "kappa": 5.0, "tau": 10.0, "theta1": 1.0}
    o = M.simulate(toy, p, M.Inputs(d0=np.full((1, NB), 3500.0), d_o=np.zeros((1, 0, NB)), beta=np.zeros((1, 0, NB))),
                   c1=0.3, T_s=5.0)
    nj, jm, cl = o.floor_nonjam_share[0], o.floor_jam_share[0], o.clipped_share[0]
    assert nj > 0 and jm > 0
    assert cl >= nj - 1e-15                                  # non-jam floors are counted as clipped
    assert cl < nj + jm                                      # jam floors are reported only


# ---------------------------------------------------------------- test 19: A3
def test19_a3_penalty_not_simulated_and_graded(net4, monkeypatch):
    thr = C.a3_thresholds(net4)
    calls = []
    real_sim = M.simulate

    def spy(net, params, inp, n_param_sets=1, **kw):
        calls.append(n_param_sets)
        return real_sim(net, params, inp, n_param_sets=n_param_sets, **kw)
    monkeypatch.setattr(M, "simulate", spy)
    good = C.to_norm(feasible())
    bad1, bad2 = good.copy(), good.copy()
    i_a2 = C.NAMES.index("a2")
    bad1[i_a2] = 0.10                                      # a2 = 1.25 -> v_c,G2 below 67.69
    bad2[i_a2] = 0.0                                       # a2 = 1.0 -> a larger shortfall
    X = np.vstack([bad1, bad2])
    data = {"d0": np.full((1, NB), 1500.0), "d_o": np.full((1, len(net4.entrances), NB), 60.0),
            "d_o_": None, "beta": np.full((1, len(net4.exits), NB), 0.02),
            "q": np.full((1, 17, NB), np.nan), "v": np.full((1, 17, NB), np.nan),
            "mq": np.zeros((1, 17, NB), bool), "mv": np.zeros((1, 17, NB), bool), "mc": np.zeros((1, 17, NB), bool)}
    J, parts = C.objective(X, data, net4, return_parts=True)
    assert calls == []                                      # violators are never simulated (§A3 (a))
    assert np.all(J > 10.0) and J[1] > J[0]                 # graded, above every admissible J (§A3 (b))
    assert parts["a3_violation"].all()
    s = C.a3_shortfall(C.to_params(bad1[None, :]), thr)[0]
    assert J[0] == pytest.approx(10.0 + s)
    # profile points with no A3-feasible completion are skipped (§A3 (e)): v_f,G3 = 80 and 88.75 km/h
    for vf3, feas in ((80.0, False), (88.75, False), (97.5, True)):
        assert (Q.a3_warm_start(feasible(vf3=vf3), thr) is not None) == feas
    w = Q.a3_warm_start(feasible(a2=1.0), thr)
    assert w["vf2"] * math.exp(-1 / w["a2"]) >= thr[1] - 1e-9
    assert w["a2"] == pytest.approx(1.0 / math.log(w["vf2"] / thr[1]), rel=1e-6)        # minimal raise
    assert all(w[k] == feasible(a2=1.0)[k] for k in ("a1", "a3", "a4", "vf1", "vf2", "vf3"))
    calls.clear()                                            # a mixed batch: only feasible rows are simulated
    Xm = np.vstack([good, bad1, good])
    Jm, pm = C.objective(Xm, data, net4, return_parts=True)
    assert calls == [2] and list(pm["feasible_index"]) == [0, 2] and list(pm["a3_violation"]) == [False, True, False]
    assert Jm[1] > 10.0 and Jm[0] == Jm[2]


# ---------------------------------------------------------------- test 21: P11-k classifier and the toy
def _p11_case(cong_cells: list[int], pair=("S1773", "S1140"), nbins=20):
    scell = {"S1773": 24, "S1140": 31, "S1141": 34}
    speeds = {s: np.full(nbins, 60.0) for s in scell}
    u, d = pair
    speeds[u][5:15] = 30.0                                  # pair condition holds on bins 5-14
    eps = {("S1773", "S1140"): [], ("S1140", "S1141"): []}
    eps[pair] = [(5, 14)]
    cong = np.zeros((39, nbins), bool)
    for c in cong_cells:
        cong[c - 1, 5:15] = True
    return Q.p11_core(speeds, eps, cong, scell)


def test21_p11_classifier():
    assert _p11_case([23, 24])["B1"]["unbacked"]            # (i) a 4 -> 3 drop queue only
    assert not _p11_case([26, 27, 28])["B1"]["unbacked"]    # (ii) an H1 queue spilling back
    assert not _p11_case([27])["B1"]["unbacked"]            # (ii) cell 27 counts
    assert _p11_case([25])["B1"]["unbacked"] and _p11_case([32])["B1"]["unbacked"]          # (iii) station cells
    P2 = ("S1140", "S1141")
    assert _p11_case([32], P2)["B2"]["unbacked"] and _p11_case([35], P2)["B2"]["unbacked"]  # (v)
    assert not _p11_case([33], P2)["B2"]["unbacked"] and not _p11_case([34], P2)["B2"]["unbacked"]
    half = _p11_case([], P2)                                # (vi) exactly 50 % backed is not unbacked
    scell = {"S1773": 24, "S1140": 31, "S1141": 34}
    speeds = {s: np.full(20, 60.0) for s in scell}
    speeds["S1140"][5:15] = 30.0
    cong = np.zeros((39, 20), bool)
    cong[32, 5:10] = True
    r = Q.p11_core(speeds, {("S1773", "S1140"): [], P2: [(5, 14)]}, cong, scell)
    assert r["B2"]["share"] == 0.5 and not r["B2"]["unbacked"] and half["B2"]["unbacked"]
    v = Q.p11_verdict({f"d{i}": _p11_case([23]) for i in range(22)})
    assert v["tolerance"] == 3 and not v["B1"]["PASS"]
    # pooling over two episodes: 5 qualifying bins in total, 1 backed -> share 0.2 -> unbacked
    speeds = {s_: np.full(20, 60.0) for s_ in scell}
    speeds["S1773"][[2, 3, 10, 11, 12]] = 30.0
    cong = np.zeros((39, 20), bool)
    cong[27, 2] = True
    r = Q.p11_core(speeds, {("S1773", "S1140"): [(1, 4), (9, 13)], P2: []}, cong, scell)
    assert r["B1"]["n_qualifying"] == 5 and r["B1"]["share"] == 0.2 and r["B1"]["unbacked"]
    for n, k_ok in ((22, 3), (19, 2)):                       # tolerance max(2, ceil(0.10 n))
        days = {f"d{i}": (_p11_case([23]) if i < k_ok else _p11_case([27])) for i in range(n)}
        assert Q.p11_verdict(days)["B1"]["PASS"]
        days[f"d{k_ok}"] = _p11_case([23])
        assert not Q.p11_verdict(days)["B1"]["PASS"]


def test21_iv_lane_drop_toy_reads_slow_without_a_queue():
    """(iv) pinned toy: 12 cells of 450 m, 3 -> 2 lanes after cell 6, v_f 100 km/h, rho_cr 35, a 3.5 (v_c 75.1 km/h,
    A3-feasible at every threshold), nu 90, kappa 5, tau 10 s, phi 4 (cell 6), delta_m 0, demand 0.9 x 2-lane
    capacity, c_s = 1: the last 3-lane station reads < 40 mph with no congested cell -> non-zero §A13 item 1."""
    from vsl_lab.jobs.metanet_freeze import a13_item1_core
    n, L = 12, 0.45
    kf = np.arange(n) * L
    kt = kf + L
    lam = np.array([3.0] * 6 + [2.0] * 6)
    st = [{"id": f"S{i}", "km": kt[i], "label": "", "dets": [], "cell": i, "corr_entr": [], "corr_exit": []}
          for i in range(n)]
    net = M.Net("toy", kf, kt, kt - kf, lam, np.full(n, 2), [], [], [], st, 5, [], [], head1=-1)
    p = M.midpoint_params() | {"vf3": 100.0, "rc3": 35.0, "a3": 3.5, "nu": 90.0, "kappa": 5.0, "tau": 10.0,
                               "phi": 4.0, "delta_m": 0.0}
    cap2 = 2 * 35.0 * 100.0 * math.exp(-1 / 3.5)
    o = M.simulate(net, p, M.Inputs(d0=np.full((1, NB), 0.9 * cap2), d_o=np.zeros((1, 0, NB)),
                                    beta=np.zeros((1, 0, NB))), T_s=T)
    v_mph = o.v_st[0, 5, 12:] / 1.609344
    cong = (o.rho_cell[0, 5:7, 12:] > o.rc_cell[0, 5:7, 12:]).any(axis=0)
    nv, nh = a13_item1_core(v_mph, cong)
    assert 100.0 * math.exp(-1 / 3.5) >= 75.0 and nh > 0 and nh / nv > 0.5


# ---------------------------------------------------------------- test 22: v4 jobs never write v3 paths
def test22_no_v4_job_writes_v3_paths():
    from vsl_lab.data import metanet_facts as F
    from vsl_lab.jobs import metanet_freeze as Z
    from vsl_lab.jobs import metanet_gate as G
    assert C.RUNS != C.V3_RUNS and C.RUNS.name == "metanet_v4"
    assert Q.RUNS == C.RUNS and Z.RUNS == C.RUNS and G.RUNS == C.RUNS
    assert Z.RECORD == "metanet_v4_calibration" and G.FREEZE.name == "metanet_v4_calibration.json"
    with pytest.raises(SystemExit):
        F.main()                                            # the v3 facts writer refuses
    with pytest.raises(SystemExit):
        F.main_v3_frozen()
    v3_names = ("metanet_precal_facts.json\"", "metanet_calibration.json\"", "metanet_calibration.md\"")
    for mod in ("vsl_lab/jobs/metanet_calibrate.py", "vsl_lab/jobs/metanet_postcal.py",
                "vsl_lab/jobs/metanet_freeze.py", "vsl_lab/jobs/metanet_gate.py", "vsl_lab/data/metanet_facts.py"):
        src = (REPO / mod).read_text()
        assert not re.search(r"V3_RUNS\s*/[^\n]*\.write_", src), mod
        for nm in v3_names[1:]:
            assert nm not in src, (mod, nm)
    from vsl_lab.data.metanet_facts import f16_cells
    assert [c + 1 for c in f16_cells(M.build_network("v4"))] == [27, 32, 35, 36, 37, 38, 39]
    assert [c + 1 for c in f16_cells(M.build_network("v4_step_c"))] == [27, 32, 35]


# ---------------------------------------------------------------- test 23: F16 per-cell sources
def test23_f16_sources_on_synthetic_flows():
    from vsl_lab.data.metanet_facts import conservation_flow
    one = np.ones(4)
    elems = [(7.518, +1, 100 * one), (8.999, -1, 30 * one), (7.017, -1, 7 * one)]   # E15, X14, X13
    q_osr = 1000 * one
    a35 = conservation_flow(7.017, 7.199, q_osr, elems)       # cell 35 upstream end: OSR only
    a36 = conservation_flow(7.518, 7.199, q_osr, elems)       # cell 36: just after E15
    a39 = conservation_flow(8.999, 7.199, q_osr, elems)       # cell 39 upstream end: X14 already left
    assert np.allclose(a35, 1000) and np.allclose(a36, 1100) and np.allclose(a39, 1070)


# ---------------------------------------------------------------- F1 (§6.1 under v4)
def _synthetic_targets(net4):
    """A 1-day synthetic data dict whose targets are a base-plant run (masks all true): J is finite and admissible."""
    inp = inputs(net4, d0=2400.0)
    o = M.simulate(net4, feasible(), inp)
    ns = o.q_st.shape[1]
    m = np.ones((1, ns, NB), bool)
    return {"d0": inp.d0, "d_o": inp.d_o, "beta": inp.beta, "q": o.q_st.copy(), "v": o.v_st.copy(),
            "mq": m, "mv": m, "mc": m}


def test_f1_delta_zero_reproduces_base_objective_and_a3(net4):
    from vsl_lab.jobs import metanet_f1 as F1
    data = _synthetic_targets(net4)
    xb = C.to_norm(feasible())
    lo, hi = M.BOUNDS["eta"]
    x1 = np.concatenate([xb, [0.0, (0.9 - lo) / (hi - lo)]])            # Delta = 0, eta = 0.9
    Jb = C.objective(xb[None, :], data, net4)
    J1 = F1.objective(x1[None, :], data, net4)
    assert np.isfinite(Jb[0]) and Jb[0] < 10 and J1[0] == pytest.approx(Jb[0], rel=1e-12)
    bad = x1.copy()
    bad[C.NAMES.index("a2")] = 0.0                                      # violates A3 at G2
    Jv, pv = F1.objective(np.vstack([x1, bad]), data, net4, return_parts=True)
    assert list(pv["a3_violation"]) == [False, True] and Jv[1] > 10.0
    assert F1.NAMES_F1[-2:] == ["Delta", "eta"] and len(F1.NAMES_F1) == 19 and F1.SEEDS_F1[0] == 7191018


def test_f1_switch_changes_an_overloaded_jam(net4):
    """The pinned B2 scenario of test 15 at c2 = 0.85 (B2 jams): Delta = 0 is the base plant; Delta = 0.15 lowers
    the active B2 cells' effective rho_cr through the memory switch and changes the flows."""
    ne, nx = len(net4.entrances), len(net4.exits)
    h = 4.0 + np.arange(NB) / 12.0
    shape = np.clip(0.5 + 0.5 * (h - 14.0) * 60 / 90, 0.5, 1.0) * (h < 18) + 0.5 * (h >= 18)
    ids = [e["id"] for e in net4.entrances]
    d_o = np.full((1, ne, NB), 50.0) * shape
    d_o[0, ids.index("E14")] = 900.0 * shape
    d_o[0, ids.index("E15")] = 300.0 * shape
    inp = M.Inputs(d0=(3600.0 * shape)[None, :], d_o=d_o, beta=np.zeros((1, nx, NB)))
    base = Q.simf(net4, feasible(), inp, c1=1.2, c2=0.85)
    zero = Q.simf(net4, feasible() | {"Delta": 0.0, "eta": 0.9}, inp, c1=1.2, c2=0.85)
    drop = Q.simf(net4, feasible() | {"Delta": 0.15, "eta": 0.9}, inp, c1=1.2, c2=0.85)
    assert np.allclose(zero.q_st, base.q_st)                             # Delta = 0 is the base plant
    assert (base.rho_cell[0, 32] > base.rc_cell[0, 32]).any()            # B2 jams in this scenario
    assert drop.rc_cell[0, 32].min() < base.rc_cell[0, 32].min()          # memory lowers B2's rho_cr
    assert not np.allclose(drop.q_st, base.q_st)


def test_f1_plant_lookup_and_gate_seed(monkeypatch):
    from vsl_lab.jobs import metanet_gate as G
    base = {"nominal_seed": 7191012, "restarts": [{"seed": 7191012, "best_params": {"tau": 20.0}, "best_x": [0.1]}]}
    f1 = {"nominal_seed": 7191020, "restarts": [{"seed": 7191020, "best_params": {"tau": 21.0, "Delta": 0.05,
                                                                                    "eta": 0.8}, "best_x": [0.2]}]}
    monkeypatch.setattr(Q, "summary", lambda kind="base": base if kind == "base" else f1)
    assert Q.plant_params()["tau"] == 20.0 and "Delta" not in Q.plant_params()
    assert Q.plant_params(7191020)["Delta"] == 0.05 and Q.is_f1(Q.plant_params(7191020))
    monkeypatch.setattr(G, "SEED_BOOT", G.SEED_BOOT_F1)
    a = G.boot_median_ci([1.0, 2.0, 3.0, 4.0])
    b = G.boot_median_ci([1.0, 2.0, 3.0, 4.0], seed=7191302)
    assert a == b and G.SEED_BOOT_F1 == 7191302


def test_freeze_param_mapping_base_and_f1():
    """Regression (2026-10-07): _to_params recursed into itself after the F1 refactor."""
    from vsl_lab.jobs import metanet_f1 as F1
    from vsl_lab.jobs import metanet_freeze as Z
    x = np.full((1, len(C.NAMES)), 0.5)
    Z._S["kind"] = "base"
    assert Z._to_params(x)["tau"][0] == pytest.approx(C.to_params(x)["tau"][0]) and Z._names() == C.NAMES
    Z._S["kind"] = "f1"
    x1 = np.full((1, len(F1.NAMES_F1)), 0.5)
    assert "Delta" in Z._to_params(x1) and Z._names() == F1.NAMES_F1
    Z._S["kind"] = "base"
