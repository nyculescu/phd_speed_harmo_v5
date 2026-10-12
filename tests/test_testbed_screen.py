"""Testbed stage-1b screen job (vsl_lab/jobs/testbed_screen.py; prereg docs/plans/day_pattern_testbed_stage1b_screen.md v1 + §11).

venv314/bin/python -m pytest -p no:cacheprovider tests/test_testbed_screen.py -q
Reads the 12 train-source days only (design input allowed; no validation/test day). No seed of 7,193,xxx is used here.
"""
import json

import numpy as np
import pytest

from vsl_lab.jobs import metanet_calibrate as C
from vsl_lab.jobs import testbed_screen as S


@pytest.fixture(scope="module")
def setup():
    days = S.train_days()
    net, inp, listing = S.build_inputs(days)
    return days, net, inp, listing, S.params()


def test_guards_train_only():
    days = S.train_days()
    split = json.loads(S.SPLIT.read_text())
    assert len(days) == 12 and not set(days) & (set(split["val"]) | set(split["test"]))
    S.provenance_guards(days)


def test_demand_totals_within_5pct_and_e2_single_detector(setup):
    days, net, inp, _, _ = setup
    data = C.load_data()
    cal = [str(d) for d in data["days"]]
    eid = {e["id"]: i for i, e in enumerate(net.entrances)}
    for k, d in enumerate(days):
        for e in S.METERS["10"]:
            new = inp.d_o[k, eid[e], S.B05:S.B23].sum()
            rep = data["d_o"][cal.index(d), eid[e], S.B05:S.B23].sum()
            assert abs(new / rep - 1.0) <= 0.05 + 1e-9, (d, e, new / rep)
    assert S.QDETS["E2"] == ["3678"] and S.QDETS["E5"] == ["3669"] and "E3" not in S.QDETS
    assert inp.d0.shape[1] == 228 + S.NPAD and float(inp.d0[:, 228:].max()) == 0.0


def test_storage_rows():
    s1 = dict(zip(S.METERS["10"], S.storage("x1", S.METERS["10"])))
    sg = dict(zip(S.METERS["10"], S.storage("gen", S.METERS["10"])))
    assert abs(s1["E9"] - 300 * 0.3048 / 8.94) < 1e-9 and abs(sg["E4"] / s1["E4"] - 3.0) < 1e-12
    assert abs(sg["E1"] / s1["E1"] - 1.25) < 1e-12


def test_decode_tables_and_window_resolution():
    ctx = {"nc": 2, "nb": 252, "coords": [(0, 1000.0), (1, 500.0)]}
    pol = S.decode("CONST", np.array([[0.0, 1.0]]), ctx)
    assert pol.r[0, 0, S.B05] == S.R_MIN and pol.r[0, 1, S.B05] == 500.0 and np.isinf(pol.r[0, 0, S.B05 - 1])
    assert np.isinf(pol.r[0, 0, S.B23])
    ctxf = {"nc": 1, "nb": 252, "coords": [(0, 800.0)]}
    span = S.FINE_MIN[1] - S.FINE_MIN[0]
    for dt in (1, 2, 3):                                     # 60-s resolution: one minute moves the window start
        w = S.decode("TOD-fine-day", np.array([[dt / span, 0.5, 1.0]]), ctxf)
        assert np.isinf(w.rates(None, S.FINE_MIN[0] + dt - 1)[0, 0]) and w.rates(None, S.FINE_MIN[0] + dt)[0, 0] == 800.0


class _St:
    def __init__(self, r_eff, layer):
        self.last_r_eff, self.last_layer, self.last_net = r_eff, layer, np.zeros_like(layer)


def test_alinea_reads_previous_period_and_antiwindup():
    pol = S.Alinea(np.full((1, 2), 50.0), np.full((1, 2), 20.0), [[26], [32, 33]], np.ones((1, 2), bool))

    class Rho:
        rho = np.zeros((1, 40))
    st = Rho()
    st.rho[0, 26], st.rho[0, 32], st.rho[0, 33] = 40.0, 10.0, 30.0
    r0 = pol.rates(st, 600.0)                                # first period: no density yet
    for _ in range(80):
        pol.observe(st)
        pol.post_step(_St(np.array([[900.0, np.inf]]), np.array([[_ == 3, False]])))   # bound once, early
    pol.after_period(st)
    assert pol.rbar[0, 0] == 40.0 and pol.rbar[0, 1] == 30.0                  # max of the 60-s means for E14
    assert pol.r_prev[0, 0] == 900.0                                          # bound inside the period -> applied r_eff
    r1 = pol.rates(st, 601.0)
    assert r1[0, 0] < S.R_MAX and r1[0, 0] == np.clip(900.0 + 50.0 * (20.0 - 40.0), S.R_MIN, S.R_MAX)
    assert np.all(r0 == S.R_MAX)


def test_alinea_rollout_meters_on_a_train_day(setup):
    days, net, inp, _, p = setup
    ctx = S.context("ALINEA-B-day", net, p, inp, [0], S.METERS["10"])
    n = len(ctx["x0"])
    aggressive = np.tile([1.0, 0.0], n // 2)                 # K = 300, rho* = 0.6 rho_cr
    off = np.tile([0.0, 1.0], n // 2)                        # K = 5, rho* = 1.2 rho_cr
    st = S._rollout_eval("ALINEA-B-day", net, p, inp, S.METERS["10"], "x1", [0, 0], [aggressive, off], {0: ctx})
    r = st.acc.r_eff / st.spb
    assert (r[0, :, S.B05:S.B23] < S.R_MAX - 1).any()
    J = S.J_of(st)
    assert J[0] != J[1]


def test_optimise_ragged_days_cap1(setup, monkeypatch):
    """Every per-day arm survives a generation with day-dependent coordinate counts (evaluation stubbed, seeds off-block)."""
    days, net, inp, _, p = setup
    monkeypatch.setattr(S, "seed_for", lambda *a: 12345 + a[2] * 10 + a[3])
    calls = []

    def stub(arm, net_, p_, inp_, meters, srow, rows, U, ctxs):
        S._pad(list(U))
        calls.append(len(rows))
        return np.array([1000.0 + 0.01 * k for k in range(len(rows))])
    monkeypatch.setattr(S, "_rollout_eval", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("final eval skipped")))
    J_nc = np.full(len(days), 1000.0)
    for arm in S.ARMS:
        try:
            S.optimise(arm, "10", "x1", net, p, inp, days, J_nc, np.full(10, 600.0), cap=1, evaluate_fn=stub)
        except RuntimeError as e:
            assert "final eval skipped" in str(e)
    assert len(calls) == 2 * len(S.ARMS)


def test_per_es_rng_independent_of_global_state():
    a = S.make_es([0.5] * 4, 777)
    np.random.seed(1)
    _ = np.random.rand(10)
    b = S.make_es([0.5] * 4, 777)
    assert np.allclose(np.array(a.ask()), np.array(b.ask()))
