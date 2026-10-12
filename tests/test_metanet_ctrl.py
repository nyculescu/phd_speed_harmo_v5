"""Testbed stepper (vsl_lab/plants/metanet_ctrl.py; testbed protocol §2, D5.11).

venv314/bin/python -m pytest -p no:cacheprovider tests/test_metanet_ctrl.py -q
M-EQ runs the frozen v5 nominal in replay on the 22 calibration days (replay only: no controlled-mode run touches any day).
"""
import json
from pathlib import Path

import numpy as np
import pytest

from vsl_lab.jobs import metanet_calibrate as C
from vsl_lab.plants import metanet as M
from vsl_lab.plants import metanet_ctrl as MC

REC = Path(__file__).resolve().parents[1] / "docs/lab/day_pattern/metanet_v5_calibration.json"


def _setup(days=None):
    data = C.load_data()
    sl = slice(None) if days is None else days
    inp = M.Inputs(data["d0"][sl], data["d_o"][sl], data["beta"][sl])
    p = json.loads(REC.read_text())["frozen_params"]
    return M.build_network(C.VARIANT), {k: np.array([v]) for k, v in p.items()}, inp


def _eq(a, b):
    if a is None or b is None:
        return a is None and b is None
    a, b = np.asarray(a), np.asarray(b)
    return a.shape == b.shape and bool(np.array_equal(a, b, equal_nan=a.dtype.kind == "f"))


def test_meq_replay_bit_for_bit():
    """M-EQ: with no control the stepper reproduces simulate() exactly on every SimOut field, all 22 days."""
    net, p, inp = _setup()
    ref = M.simulate(net, p, inp)
    st = MC.Stepper(net, p, inp)
    st.run_to_end()
    out = st.simout()
    bad = [f for f in ref.__dataclass_fields__ if not _eq(getattr(ref, f), getattr(out, f))]
    assert not bad, bad


def test_meq_split_stepping():
    """Stepping in uneven chunks (as a controller would) gives the same result as one run."""
    net, p, inp = _setup(slice(0, 2))
    a = MC.Stepper(net, p, inp)
    a.run_to_end()
    b = MC.Stepper(net, p, inp)
    while b.k < b.nb * b.spb:
        b.step(min(80 if b.k % 3 else 37, b.nb * b.spb - b.k))
    assert _eq(a.simout().q_st, b.simout().q_st) and _eq(a.acc.tts_cells, b.acc.tts_cells)


def test_nonbinding_rate_equals_replay():
    """A finite but non-binding rate (no queue layer) leaves every output unchanged."""
    net, p, inp = _setup(slice(0, 2))
    a = MC.Stepper(net, p, inp)
    a.run_to_end()
    b = MC.Stepper(net, p, inp)
    b.set_rates(np.full(4, 1e9))
    b.run_to_end()
    assert _eq(a.simout().q_st, b.simout().q_st) and _eq(a.simout().entr_flow, b.simout().entr_flow)


def test_binding_rate_holds_back_and_conserves():
    """A binding rate at E14 (the controlled ramp whose demand exceeds 240 veh/h most often) caps its release, builds a
    queue, and conserves vehicles at every entrance (demand volume = released volume + final queue)."""
    net, p, inp = _setup(slice(0, 1))
    st = MC.Stepper(net, p, inp)
    i14 = st.ctrl_idx[3]
    assert inp.d_o[0, i14].max() > 400.0
    st.set_rates([np.inf, np.inf, np.inf, 240.0])
    st.run_to_end()
    o = st.simout()
    assert o.entr_flow[0, i14].max() <= 240.0 + 1e-9
    T, spb = st.T, st.spb
    dem = inp.d_o.sum(axis=2) * T * spb
    rel = o.entr_flow.sum(axis=2) * T * spb
    assert np.allclose(dem, rel + o.queue_end[:, 1:], rtol=1e-9, atol=1e-6)
    assert st.acc.tts_queues[0, 1 + i14].sum() > 0


def test_queue_layer_bounds_wait_and_storage():
    """With the common queue layer, a very restrictive command cannot hold an unbounded queue."""
    net, p, inp = _setup(slice(0, 1))
    S = (40.0, 40.0, 40.0, 40.0)
    st = MC.Stepper(net, p, inp, queue=MC.QueueLayer(storage_veh=S))
    st.set_rates(np.full(4, 240.0))
    st.run_to_end()
    wq = st.acc.tts_queues[0, 1 + st.ctrl_idx, :] / (st.T * st.spb)     # bin-mean queue (veh)
    assert wq.max() <= max(S) * 1.2
    assert st.acc.layer_steps[0].sum() > 0
