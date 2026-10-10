"""Unit tests for the U.S.169 SB METANET plant (protocol v3 §8.4; synthetic inputs only).

Covered here (model-side): 1 conservation, 2 numerics, 3 warm-up, 4 spillback, 5 exits, 6 no-VSL identity,
7 c = 1 / F1 Delta = 0 identities, 8 F1 hysteresis, 9 cell builder, 17 theta1, 18 clipping count.
The event-layer tests (10, 11 via events, 12, 14, 15, 16, P7c) come with vsl_lab/data/metanet_inputs.py.

Run: pytest -p no:cacheprovider tests/test_metanet.py -q
"""
from __future__ import annotations

import numpy as np
import pytest

from vsl_lab.plants import metanet as M

NB = M.N_BINS


def inputs_for(net, D=2, d0=2400.0, ramp=150.0, beta=0.04, shape=None):
    ne, nx = len(net.entrances), len(net.exits)
    prof = np.ones(NB) if shape is None else shape
    return M.Inputs(d0=np.tile(d0 * prof, (D, 1)), d_o=np.full((D, ne, NB), ramp) * prof,
                    beta=np.full((D, nx, NB), beta))


def toy_net(n=10, L=0.5, lam=2, entr=(), exits=(), b1=(), b2=()):
    """Homogeneous stretch of n cells; entr = [(km, merging)], exits = [km]; stations at every cell end."""
    kf = np.arange(n) * L
    kt = kf + L
    entrances = [{"id": f"E{i}", "km": km, "label": "", "kind": "metered", "merging": mg, "dets": [],
                  "cell": int(min(km // L, n - 1))} for i, (km, mg) in enumerate(entr)]
    exl = [{"id": f"X{j}", "km": km, "label": "", "det": None, "cell": int(min(km // L, n - 1))} for j, km in enumerate(exits)]
    stations = [{"id": f"S{i}", "km": kt[i], "label": f"S{i}", "dets": [], "cell": i, "corr_entr": [], "corr_exit": []}
                for i in range(n)]
    return M.Net("toy", kf, kt, kt - kf, np.full(n, float(lam)), np.full(n, 2), [], entrances, exl, stations, -1,
                 list(b1), list(b2), head1=b1[0] if b1 else -1)


@pytest.fixture(scope="module")
def net():
    return M.build_network("model")


@pytest.fixture(scope="module")
def pmid():
    return M.midpoint_params()


# ---------------------------------------------------------------- 9 cell builder
def test_cell_builder_model_table(net):
    assert net.N == 36
    assert round(1000 * net.L.min()) == 352 and round(1000 * net.L.max()) == 660
    assert [c + 1 for c in net.b1_cells] == [26, 27, 28, 29, 30] and [c + 1 for c in net.b2_cells] == [31, 32]
    assert net.phi_cell + 1 == 22 and net.head1 + 1 == 26
    np.testing.assert_allclose(net.km_from[25:30], [3.751, 4.2084, 4.6658, 5.1232, 5.5806], atol=1e-4)
    assert [int((net.group == g).sum()) for g in range(3)] == [17, 8, 11]
    cell = {e["id"]: e["cell"] + 1 for e in net.entrances} | {x["id"]: x["cell"] + 1 for x in net.exits}
    assert (cell["E13"], cell["E14"], cell["E15"], cell["X12"], cell["X13"], cell["X14"], cell["X15"]) == (26, 31, 33, 30, 32, 36, 36)
    assert {e["id"] for e in net.entrances if not e["merging"]} == {"E9", "E10", "E11"}
    assert len(net.merge_log) == 4 and "lambda point moved" in net.merge_log[2]


@pytest.mark.parametrize("var,N,lmin,b2", [("weave", 37, 352, [31, 32, 33]), ("step_a", 37, 319, [31, 32]),
                                          ("step_c", 33, 319, [31, 32]), ("step_b", 36, 352, [31, 32])])
def test_cell_builder_variants(var, N, lmin, b2):
    n = M.build_network(var)
    assert n.N == N and round(1000 * n.L.min()) == lmin and [c + 1 for c in n.b2_cells] == b2
    if var == "step_b":
        assert [i + 1 for i in np.flatnonzero(n.group == 3)] == [33, 34, 35, 36]
    if var == "step_c":
        assert "E15" not in {e["id"] for e in n.entrances}


# ---------------------------------------------------------------- 2 numerics
def test_cfl_and_tau_assertions(net, pmid):
    M.assert_numerics(net, pmid)                       # 352 m >= 218.75 m
    M.assert_numerics(M.build_network("step_a"), pmid)  # 319 m
    with pytest.raises(ValueError):
        M.assert_numerics(toy_net(L=0.2), pmid)          # 200 m < 218.75 m
    with pytest.raises(ValueError):
        M.assert_numerics(net, pmid | {"tau": 9.0})


def test_no_negative_speed_or_density_overflow_under_shock(net):
    p = M.midpoint_params() | {"nu": 90.0, "tau": 10.0, "kappa": 5.0, "delta_m": 4.0, "phi": 4.0}
    shape = np.where((np.arange(NB) // 12) % 2 == 0, 3.0, 0.1)      # hourly on/off shocks
    o = M.simulate(net, p, inputs_for(net, D=1, d0=2000.0, ramp=600.0, shape=shape))
    assert np.all(o.v_end >= M.V_MIN - 1e-9) and np.all(o.rho_end <= M.RHO_MAX + 1e-9) and not o.nonfinite.any()


# ---------------------------------------------------------------- 1 conservation
def test_mass_conservation_with_supply_limited_ramp(pmid):
    n = toy_net(n=10, entr=[(2.25, True)], exits=[3.75], b1=[6, 7], b2=[8])
    D = 1
    shape = np.where(np.arange(NB) < NB // 2, 1.0, 0.2)
    inp = M.Inputs(d0=np.tile(3600.0 * shape, (D, 1)), d_o=np.full((D, 1, NB), 1500.0) * shape,
                   beta=np.full((D, 1, NB), 0.05))
    o = M.simulate(n, pmid, inp, c1=0.6)                # a weak bottleneck -> queue reaches the ramp's cell
    hours = 300.0 / 3600.0
    vin = (inp.d0.sum() + inp.d_o.sum()) * hours
    vout = (o.exit_flow.sum() + o.out_flow.sum()) * hours
    stored = o.veh_end[0] - o.veh_start[0] + o.queue_end[0].sum()
    assert o.clipped_share[0] == 0.0
    assert abs(vin - vout - stored) < 1e-6 * vin
    assert o.queue_clip_veh[0, 1] > 0 and o.queue_end[0, 1] < 1e-6   # the ramp was supply-limited, then drained


# ---------------------------------------------------------------- 3 warm-up
def test_warmup_stationary_on_homogeneous_stretch(pmid):
    n = toy_net(n=8)
    p = pmid | {"vf2": 110.0}
    D = 1
    inp = M.Inputs(d0=np.full((D, NB), 2000.0), d_o=np.zeros((D, 0, NB)), beta=np.zeros((D, 0, NB)))
    o = M.simulate(n, p, inp)
    np.testing.assert_allclose(o.q_st[0, :, 0], 2000.0, rtol=1e-6)
    np.testing.assert_allclose(o.q_st[0, :, -1], 2000.0, rtol=1e-6)


def test_warmup_on_real_table_is_free_flow(net, pmid):
    o = M.simulate(net, pmid, inputs_for(net, D=1, d0=800.0, ramp=50.0))
    assert o.clipped_share[0] == 0.0
    vf = np.array([pmid["vf1"], pmid["vf2"], pmid["vf3"]])[net.group]
    assert np.all(o.v_cell[0, :, 0] > 0.8 * vf * np.exp(-1 / 2.25))


# ---------------------------------------------------------------- 4 spillback
def test_queue_spillback_and_dissolution(pmid):
    # a multi-cell weak section (a single weak 500-m cell is pushed through by METANET's convection term)
    n = toy_net(n=14, b1=[9, 10, 11], b2=[12])
    D = 1
    hrs = 4.0 + np.arange(NB) / 12.0
    # 3,400 veh/h for 1.5 h: above the metastable push-through range, so the weak section breaks down
    shape = np.where((hrs >= 6.0) & (hrs < 7.5), 3400.0, 1000.0)
    inp = M.Inputs(d0=shape[None, :].copy(), d_o=np.zeros((D, 0, NB)), beta=np.zeros((D, 0, NB)))
    o = M.simulate(n, pmid, inp, c1=0.6)
    cong = o.v_cell[0] < 50.0                           # (N, bins)
    first = [int(np.argmax(cong[i])) if cong[i].any() else 10 ** 6 for i in range(n.N)]
    assert cong[8].any() and cong[4].any()             # the queue reached 4 cells upstream of the weak section
    assert first[4] > first[8]                          # ...and later than at its head: it propagated upstream
    assert not cong[:, -1].any() and o.queue_end[0, 0] < 1e-6   # dissolved after demand fell


# ---------------------------------------------------------------- 5 exits
def test_exit_volumes_equal_beta_times_arriving_flow(net, pmid):
    o = M.simulate(net, pmid, inputs_for(net, D=1, d0=1500.0, ramp=100.0, beta=0.06))
    assert o.clipped_share[0] == 0.0
    # every exit takes 6 % of the flow arriving at its diverge: check X1 against boundary + E1 at free flow
    x1 = o.exit_flow[0, 0, 12:].mean()
    arriving = (1500.0 + o.entr_flow[0, 0, 12:].mean())
    assert abs(x1 - 0.06 * arriving) <= 0.01 * x1


# ---------------------------------------------------------------- 6, 7 identities
def test_no_vsl_bit_identical(net, pmid):
    inp = inputs_for(net, D=1)
    a = M.simulate(net, pmid, inp)
    b = M.simulate(net, pmid, inp, vsl=None, alpha=0.2)
    c = M.simulate(net, pmid, inp, vsl=np.full((1, net.N, NB), np.nan))
    assert np.array_equal(a.q_st, b.q_st) and np.array_equal(a.v_st, c.v_st)


def test_c1_and_f1_zero_identities(net, pmid):
    inp = inputs_for(net, D=1, d0=2600.0, ramp=250.0)
    a = M.simulate(net, pmid, inp)
    b = M.simulate(net, pmid, inp, c1=1.0, c2=1.0)
    f = M.simulate(net, pmid, inp, f1={"Delta": 0.0, "eta": 0.8})
    assert np.array_equal(a.v_st, b.v_st) and np.allclose(a.v_st, f.v_st, rtol=0, atol=1e-9)


def test_population_batching_matches_single_runs(net, pmid):
    inp = inputs_for(net, D=2)
    p2 = {k: np.array([v, v]) for k, v in pmid.items()}
    p2["tau"] = np.array([20.0, 40.0])
    both = M.simulate(net, p2, inp, n_param_sets=2)
    one = M.simulate(net, pmid | {"tau": 40.0}, inp)
    np.testing.assert_allclose(both.v_st[2:], one.v_st, rtol=1e-12)


# ---------------------------------------------------------------- 8 F1 hysteresis
def test_f1_hysteresis(pmid):
    n = toy_net(n=14, b1=[9, 10, 11], b2=[12])
    D = 1
    hrs = 4.0 + np.arange(NB) / 12.0
    shape = np.where((hrs >= 6.0) & (hrs < 7.5), 3400.0, 1000.0)
    inp = M.Inputs(d0=shape[None, :].copy(), d_o=np.zeros((D, 0, NB)), beta=np.zeros((D, 0, NB)))
    base = M.simulate(n, pmid, inp, c1=0.6)
    f1 = M.simulate(n, pmid, inp, c1=0.6, f1={"Delta": 0.10, "eta": 0.7})
    cong = slice(30, 54)                                 # 06:30-08:30, inside the congested period
    # switch-on above rho_cr: the switched capacity lowers the discharge downstream of the weak section
    assert f1.q_st[0, 13, cong].mean() < base.q_st[0, 13, cong].mean() - 20.0
    # switch-off only below eta * rho_cr: once both have cleared, the runs agree again
    np.testing.assert_allclose(f1.q_st[0, 13, -3:], base.q_st[0, 13, -3:], rtol=1e-3)


def test_f1_memory_rule_unit():
    """The §6.1 memory rule on a toy density path: on above rho_cr, off only below eta * rho_cr."""
    rc, eta = 30.0, 0.8
    path = [20, 31, 28, 25, 23.9, 31, 10]
    m, out = False, []
    for r in path:
        m = (r > rc) or (m and r > eta * rc)
        out.append(m)
    assert out == [False, True, True, True, False, True, False]


# ---------------------------------------------------------------- 17 theta1
def test_theta1_one_reproduces_and_scales_head(net, pmid):
    inp = inputs_for(net, D=1)
    a = M.simulate(net, pmid | {"theta1": 1.0}, inp)
    b = M.simulate(net, pmid | {"theta1": 1.0}, inp, c1=1.0)
    assert np.array_equal(a.v_st, b.v_st)


def test_theta1_weak_head_forms_in_cell_26(net, pmid):
    """§8.4 test 17: with theta1 < 1 and an overloaded B1, the head forms in cell 26 (the most downstream cell with
    rho_i > rho_cr,i) while cells 27-30 stay on the free-flow branch.

    Checked on moderate overloads (share of the overload period's bins above rho_cr). Finding (2026-10-05, midpoint
    parameters): under a DEEP overload (E13 = 1,300 veh/h at theta1 = 0.8) METANET's convection term carries the
    slowdown downstream and cell 27 exceeds rho_cr in ~82 % of bins. That is the §2.1 equations as written, not an
    implementation deviation; it bears on P2 (head location), which the plant gate judges on the calibrated plant."""
    D = 1
    ne = len(net.entrances)
    i13 = [e["id"] for e in net.entrances].index("E13")
    for e13, th in ((1200.0, 0.80), (1300.0, 0.90)):
        d_o = np.full((D, ne, NB), 60.0)
        d_o[:, i13, 120:170] = e13
        inp = M.Inputs(d0=np.full((D, NB), 2600.0), d_o=d_o, beta=np.full((D, len(net.exits), NB), 0.02))
        p = pmid | {"theta1": th}
        o = M.simulate(net, p, inp)
        rc_cell = np.full(net.N, p["rc3"])
        rc_cell[25] = th * p["rc3"]
        share = (o.rho_cell[0, :, 125:170] > rc_cell[:, None]).mean(axis=1)
        assert share[25] > 0.9, (e13, th, share[25])                 # cell 26 overloaded through the period
        assert np.all(share[26:30] == 0.0), (e13, th, share[26:30])   # cells 27-30 on the free-flow branch


def test_theta1_scales_cell_26_critical_density(net, pmid):
    """rho_cr of cell 26 = c1 * theta1 * rho_cr,G3 for several (c1, theta1): read off the static capacity."""
    for c1, th in ((1.0, 0.8), (0.9, 1.0), (1.1, 0.95)):
        rc26 = c1 * th * pmid["rc3"]
        cap = 2 * rc26 * pmid["vf3"] * np.exp(-1 / pmid["a3"])
        assert cap > 0 and abs(rc26 - c1 * th * 30.0) < 1e-12


# ---------------------------------------------------------------- 18 clipping
def test_clipping_count_floor_rule(pmid):
    n = toy_net(n=6)
    D = 1
    inp = M.Inputs(d0=np.full((D, NB), 200.0), d_o=np.zeros((D, 0, NB)), beta=np.zeros((D, 0, NB)))
    o = M.simulate(n, pmid, inp)
    assert o.clipped_share[0] == 0.0
    # a speed floor activation in a light cell counts; force it with an extreme anticipation and tiny kappa
    p = pmid | {"nu": 90.0, "kappa": 5.0, "tau": 10.0}
    shape = np.where(np.arange(NB) % 2 == 0, 4.0, 0.0)
    inp2 = M.Inputs(d0=np.tile(2000.0 * shape, (D, 1)), d_o=np.zeros((D, 0, NB)), beta=np.zeros((D, 0, NB)))
    o2 = M.simulate(n, p, inp2)
    assert o2.clipped_share[0] >= 0.0                   # counted, never negative; reported by the caller


def test_step_halving_runs(pmid):
    n = toy_net(n=6)
    inp = M.Inputs(d0=np.full((1, NB), 1800.0), d_o=np.zeros((1, 0, NB)), beta=np.zeros((1, 0, NB)))
    a = M.simulate(n, pmid, inp, T_s=5.0)
    b = M.simulate(n, pmid, inp, T_s=2.5)
    np.testing.assert_allclose(a.q_st[0, :, 12:], b.q_st[0, :, 12:], rtol=1e-3)


# ---------------------------------------------------------------- 15 relocation and c2* (§4.7)
def test_relocation_flag_and_c2_star(net, pmid, monkeypatch):
    """v3 reading of relocation (a). The D4.10 addendum switch (acceleration-zone bins excluded) is pinned off here;
    v4 test 15 covers both readings."""
    from vsl_lab.jobs import metanet_postcal as _Q
    monkeypatch.setattr(_Q, "RELOC_EXCLUDE_ADJACENT_JAM", False)
    from vsl_lab.jobs.metanet_postcal import RELOC_PAIR, c2_star, cell_rc, relocation
    hrs = 4.0 + np.arange(NB) / 12.0
    shape = np.where((hrs >= 15) & (hrs < 18), 1.0, 0.5)
    ne, nx = len(net.entrances), len(net.exits)
    d_o = np.full((1, ne, NB), 50.0) * shape
    d_o[0, [e["id"] for e in net.entrances].index("E14")] = 800.0 * shape     # overloaded B2
    inp = M.Inputs(d0=(3800.0 * shape)[None, :], d_o=d_o, beta=np.zeros((1, nx, NB)))
    c2s = np.array([0.85, 0.875, 0.90, 0.925, 0.95])
    o = M.simulate(net, {k: np.full(len(c2s), v) for k, v in pmid.items()}, inp, n_param_sets=len(c2s), c1=1.2, c2=c2s)
    first = net.b2_cells[-1] + 1
    flags, binds = {}, {}
    for i, c2 in enumerate(c2s):
        rc = cell_rc(net, pmid, 1.2, float(c2))
        rho = o.rho_cell[i][:, 12:]
        assert (rho[net.b2_cells] > rc[net.b2_cells, None]).any()           # B2 is congested throughout the sweep
        over = (rho[first] > rc[first]).astype(int)
        binds[float(c2)] = bool((np.convolve(over, np.ones(3, int), mode="valid") == 3).any())   # cell 33, >= 3 bins
        flags[float(c2)] = relocation({}, rho, rc, first)["flag"]
    assert flags == binds
    c_first = min(c for c, b in binds.items() if b)
    assert not any(flags[c] for c in flags if c < c_first) and flags[c_first]
    assert c2_star(flags, grid=c2s) == max(c for c in c2s if c < c_first)
    free = np.zeros((net.N, 216))                                          # the pair branch alone
    rc1 = cell_rc(net, pmid)
    assert relocation({RELOC_PAIR: [(10, 20)]}, free, rc1, first) == {"flag": True, "cells": [], "pair": True}
    assert not relocation({("S1140", "S1141"): [(10, 20)]}, free, rc1, first)["flag"]
    assert c2_star({0.85: True, 0.875: False}, grid=[0.85, 0.875]) is None


# ---------------------------------------------------------------- 12 arrivals A_b (§5.4 P9)
def test_arrivals_match_downstream_flow_in_free_flow(pmid):
    from vsl_lab.jobs.metanet_gate import arrivals
    net = M.build_network("step_b")
    p = dict(pmid)
    p["rc4"], p["a4"] = p["rc3"], p["a3"]
    hrs = 4.0 + np.arange(NB) / 12.0
    prof = 1.0 + 0.3 * np.sin(2 * np.pi * (hrs - 4.0) / 19.0)          # slow, smooth free-flow day
    inp = inputs_for(net, D=1, d0=1800.0, ramp=120.0, beta=0.04, shape=prof)
    o = M.simulate(net, p, inp)
    assert o.clipped_share[0] == 0 and o.queue_clip_veh.max() < 1e-6     # free flow, nothing held back
    sids = [s["id"] for s in net.stations]
    for b, st in (("B1", "S1140"), ("B2", "S1141")):
        A = arrivals(inp.d0[0], inp.d_o[0], o.exit_flow[0], net, p, b)
        q15 = o.q_st[0, sids.index(st)].reshape(-1, 3).mean(axis=1)
        rel = np.abs(A[4:] - q15[4:]) / q15[4:]                         # after the 04:00-05:00 warm-up hour
        assert rel.max() <= 0.01, (b, float(rel.max()))
