"""Testbed stage-1b screen job (vsl_lab/jobs/testbed_screen.py; prereg docs/plans/day_pattern_testbed_stage1b_screen.md v1).

venv314/bin/python -m pytest -p no:cacheprovider tests/test_testbed_screen.py -q
Reads the 12 train-source days' Queue detectors (design input allowed; no validation/test day).
"""
import json

import numpy as np

from vsl_lab.jobs import metanet_calibrate as C
from vsl_lab.jobs import testbed_screen as S


def test_guards_train_only():
    days = S.train_days()
    split = json.loads(S.SPLIT.read_text())
    assert len(days) == 12 and not set(days) & (set(split["val"]) | set(split["test"]))


def test_demand_totals_within_5pct_and_e2_single_detector():
    days = S.train_days()
    net, inp, listing = S.build_inputs(days)
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


def test_decode_tables():
    ctx = {"nc": 2, "nb": 252, "coords": [(0, 1000.0), (1, 500.0)]}
    pol = S.decode("CONST", np.array([[0.0, 1.0]]), ctx)
    assert pol.r[0, 0, S.B05] == S.R_MIN and pol.r[0, 1, S.B05] == 500.0 and np.isinf(pol.r[0, 0, S.B05 - 1])
    assert np.isinf(pol.r[0, 0, S.B23])
    ctxf = {"nc": 1, "nb": 252, "coords": [(0, 800.0)]}
    pf = S.decode("TOD-fine-day", np.array([[0.0, 0.5, 1.0]]), ctxf)
    on = np.isfinite(pf.r[0, 0])
    assert on[S.FINE[0]] and not on[S.FINE[0] - 1] and on.sum() == (S.FINE[1] - S.FINE[0]) // 2


class _St:
    def __init__(self, r_eff, layer):
        self.last_r_eff, self.last_layer, self.last_net = r_eff, layer, np.zeros_like(layer)


def test_alinea_antiwindup():
    pol = S.Alinea(np.full((1, 2), 50.0), np.full((1, 2), 20.0), [[26], [26]], np.ones((1, 2), bool))
    pol.n, pol.acc = 1, np.full((1, 2), 40.0)                 # density above set-point -> rate falls
    r = pol.rates(None, 600.0)
    assert np.all(r == S.R_MAX + 50.0 * (20.0 - 40.0)) or np.all(r == np.clip(S.R_MAX - 1000.0, S.R_MIN, S.R_MAX))
    pol.after_period(_St(np.array([[900.0, np.inf]]), np.array([[True, False]])))
    assert pol.r_prev[0, 0] == 900.0 and pol.r_prev[0, 1] == pol._r[0, 1]
