"""V388: policy inputs are normalised by statistics saved with the weights."""
from pathlib import Path

import numpy as np
import pytest
import torch

from v5b.fleet import b_env as be, c_train as ct

OLD = Path(__file__).resolve().parent.parent / "docs/research/phase3/shot_policies/C1_final.pt"


def data(n=4000, seed=1):
    r = np.random.default_rng(seed)
    lo = r.uniform(0.0, 1.0, (n, be.CAV_LOCAL)).astype(np.float32)
    lo[:, 0] = r.uniform(-3.5, 3.3, n)
    lo[:, 11] = 0.0
    gl = r.uniform(0.0, 0.2, (n, be.CAV_GLOBAL)).astype(np.float32)
    return lo, gl


def net_with_stats():
    torch.manual_seed(3)
    net = ct.Net()
    lo, gl = data()
    net.observe(lo, gl)
    return net, lo, gl


def test_two_batches_equal_one():
    lo, gl = data(6000)
    a = ct.Net()
    a.observe(lo[:1000], gl[:1000])
    a.observe(lo[1000:], gl[1000:])
    assert a.n_seen.item() == 6000
    assert a.lo_mean.numpy() == pytest.approx(lo.astype(np.float64).mean(0), abs=1e-9)
    assert a.lo_var.numpy() == pytest.approx(lo.astype(np.float64).var(0), abs=1e-9)
    assert a.gl_var.numpy() == pytest.approx(gl.astype(np.float64).var(0), abs=1e-9)


def test_scaled_inputs_are_standard_and_the_dead_input_stays_zero():
    net, lo, _ = net_with_stats()
    z = net._scaled(torch.from_numpy(lo), net.lo_mean, net.lo_var).numpy()
    live = [i for i in range(be.CAV_LOCAL) if i != 11]
    assert z[:, live].mean(0) == pytest.approx(np.zeros(len(live)), abs=1e-3)
    assert z[:, live].std(0) == pytest.approx(np.ones(len(live)), abs=1e-3)
    assert (z[:, 11] == 0.0).all() and np.isfinite(z).all()


def test_extreme_inputs_are_clipped():
    net, lo, _ = net_with_stats()
    z = net._scaled(torch.from_numpy(lo * 1000.0), net.lo_mean, net.lo_var)
    assert z.abs().max().item() == pytest.approx(ct.CLIP_INPUT)


def test_policy_from_before_the_change_acts_exactly_as_before():
    g = ct.Greedy(str(OLD))
    assert g.net.n_seen.item() == 0
    lo, gl = data()
    due = np.ones(len(lo), dtype=bool)
    got = g((list(range(len(lo))), lo, gl, due))
    with torch.no_grad():
        want = g.net.actor(torch.from_numpy(lo)).argmax(1).numpy()
    assert list(got.values()) == want.tolist()


def test_saved_policy_uses_its_statistics(tmp_path):
    net, lo, gl = net_with_stats()
    f = tmp_path / "p.pt"
    torch.save({"net": net.state_dict(), "scale": 1.0, "u": 1, "n_local": be.CAV_LOCAL, "n_act": len(be.HEADWAYS_S)}, f)
    g = ct.Greedy(str(f))
    assert g.net.n_seen.item() == net.n_seen.item()
    got = g((list(range(len(lo))), lo, gl, np.ones(len(lo), dtype=bool)))
    with torch.no_grad():
        scaled = net.actor(net._scaled(torch.from_numpy(lo), net.lo_mean, net.lo_var)).argmax(1).numpy()
        raw = net.actor(torch.from_numpy(lo)).argmax(1).numpy()
    assert list(got.values()) == scaled.tolist()
    assert (scaled != raw).any()


def test_restore_refuses_a_checkpoint_without_weights():
    sd = ct.Net().state_dict()
    del sd["actor.0.weight"]
    with pytest.raises(KeyError):
        ct.Net().restore(sd)


def test_update_keeps_statistics_and_starts_from_ratio_one():
    net, lo, gl = net_with_stats()
    n = len(lo)
    r = np.random.default_rng(2)
    a = r.integers(0, len(be.HEADWAYS_S), n)
    with torch.no_grad():
        lp = net.dist(torch.from_numpy(lo)).log_prob(torch.from_numpy(a))
        again = net.dist(torch.from_numpy(lo)).log_prob(torch.from_numpy(a))
    assert (lp - again).abs().max().item() == 0.0
    adv, ret = r.normal(size=n).astype(np.float32), r.normal(size=n).astype(np.float32)
    before = {k: v.clone() for k, v in net.state_dict().items() if k in ct.NORM_KEYS}
    opt = torch.optim.Adam(net.parameters(), lr=ct.LR, eps=1e-5)
    st = ct.update(net, opt, (lo, gl, a, lp.numpy(), adv, ret, adv, []), 1.0, r)
    assert all(torch.equal(before[k], net.state_dict()[k]) for k in before)
    assert all(k in st for k in ("kl", "clipfrac", "ev")) and np.isfinite([st["kl"], st["clipfrac"], st["ev"]]).all()


def test_an_input_that_never_varied_carries_nothing():
    net, lo, _ = net_with_stats()
    odd = lo.copy()
    odd[:, 11] = 0.5     # as at an episode end, for a vehicle that is not due
    z = net._scaled(torch.from_numpy(odd), net.lo_mean, net.lo_var).numpy()
    assert (z[:, 11] == 0.0).all()
