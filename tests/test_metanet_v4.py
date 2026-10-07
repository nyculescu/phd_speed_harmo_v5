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
    r = M.vn_scan(T, net4.L)
    assert r["PASS"] and r["worst_stable_growth"] <= M.VN_EPS
    for Tbad in (5.0, 2.5):                                    # (ii): the v4 table rejects v3's steps
        with pytest.raises(ValueError):
            M.simulate(net4, feasible(), inputs(net4), T_s=Tbad)
    # the ladder rule picks 0.75 s: 1.25 and 1.0 fail (a)
    ok = [t for t in M.T_LADDER_V4 if M.v4_conditions(net4, t)["a"] <= 0.25]
    assert max(ok) == 0.75


def test2_shock_no_negative_speed_or_overflow(net4):
    shape = np.where(np.arange(NB) % 6 < 3, 6000.0, 0.0)
    ne, nx = len(net4.entrances), len(net4.exits)
    inp = M.Inputs(d0=shape[None, :].copy(), d_o=np.full((1, ne, NB), 1500.0), beta=np.full((1, nx, NB), 0.0))
    o = M.simulate(net4, feasible(nu=90.0, kappa=5.0, tau=10.0), inp)
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
def test15_relocation_on_cells_35_39_and_c2_star(net4):
    ne, nx = len(net4.entrances), len(net4.exits)
    h = 4.0 + np.arange(NB) / 12.0
    shape = np.where((h >= 15) & (h < 18), 1.0, 0.5)
    d_o = np.full((1, ne, NB), 50.0) * shape
    d_o[0, [e["id"] for e in net4.entrances].index("E14")] = 900.0 * shape
    inp = M.Inputs(d0=(3800.0 * shape)[None, :], d_o=d_o, beta=np.zeros((1, nx, NB)))
    c2s = np.round(np.arange(0.80, 1.2001, 0.05), 2)
    p = feasible()
    o = M.simulate(net4, {k: np.full(len(c2s), v) for k, v in p.items()}, inp, n_param_sets=len(c2s), c1=1.2, c2=c2s)
    first = net4.b2_cells[-1] + 1
    assert first + 1 == 35
    flags, binds = {}, {}
    for i, c2 in enumerate(c2s):
        rho, rc = o.rho_cell[i][:, 12:], o.rc_cell[i][:, 12:]
        over = (rho[first:] > rc[first:]).astype(int)
        binds[float(c2)] = bool(any((np.convolve(r, np.ones(3, int), mode="valid") == 3).any() for r in over))
        flags[float(c2)] = Q.relocation({}, rho, rc.mean(axis=1), first)["flag"]
    assert flags == binds
    if any(flags.values()):
        c_first = min(c for c, b in flags.items() if b)
        assert not any(flags[c] for c in flags if c < c_first)
        assert Q.c2_star(flags, grid=c2s) == (max(c for c in c2s if c < c_first) if c_first > c2s[0] else None)
    free = np.zeros((net4.N, 216))
    assert Q.relocation({Q.RELOC_PAIR: [(10, 20)]}, free, np.ones(net4.N), first) == {"flag": True, "cells": [],
                                                                                   "pair": True}


# ---------------------------------------------------------------- test 18b: clipping at T and T/2
def test18b_clipping_share_t_and_t_half(net4):
    a = M.simulate(net4, feasible(), inputs(net4, d0=1800.0), T_s=T)
    b = M.simulate(net4, feasible(), inputs(net4, d0=1800.0), T_s=T / 2)
    assert a.clipped_share[0] >= 0 and b.clipped_share[0] >= 0
    assert abs(a.q_st[0, :, 30:].mean() - b.q_st[0, :, 30:].mean()) / a.q_st[0, :, 30:].mean() < 0.01


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
    v3_names = ("metanet_precal_facts.json\"", "metanet_calibration.json\"", "metanet_calibration.md\"")
    for mod in ("vsl_lab/jobs/metanet_calibrate.py", "vsl_lab/jobs/metanet_postcal.py",
                "vsl_lab/jobs/metanet_freeze.py", "vsl_lab/jobs/metanet_gate.py"):
        src = (REPO / mod).read_text()
        assert not re.search(r"V3_RUNS\s*/[^\n]*\.write_", src), mod
        for nm in v3_names[1:]:
            assert nm not in src, (mod, nm)


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
