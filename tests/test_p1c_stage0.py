"""A stage 0 (V251): estimator, criteria and route on synthetic series."""
import numpy as np

from v5b.p1c import plant as pl
from v5b.p1c import stage0 as s0


def _series(drop, t_b=3000.0, q=1800.0, end=6000.0, rng=None):
    rows, x = [], 0.0
    for t in np.arange(30.0, end + 1, 30.0):
        out = q * (1 - drop) if t > t_b else q
        inflow = q * 1.2 if t > t_b else q
        ex = int(round(out / 120 + (rng.normal(0, 0.8) if rng is not None else 0)))
        rows.append((t, ex, 20.0, 20.0, None, 20.0, int(round(inflow / 120)), 0.0))
    return rows


def test_slow_profile_shape():
    p = s0.slow_profile(2000.0)
    assert p[0] == (0.0, 600.0, 1200.0) and p[-1] == (10200.0, 12000.0, 2300.0) and len(p) == 162
    assert abs(p[1][2] - 2000 * (0.75 + 0.4 * 0.5 / 160)) < 0.1


def test_estimate_recovers_drop_and_onset():
    e = s0.estimate(_series(0.10, rng=np.random.default_rng(1)))
    assert 3000 <= e["t_b"] <= 3150 and e["sustained"]
    assert abs(e["drop"] - 0.10) < 0.03 and len(e["qdf_counts"]) == 20


def test_estimate_without_queue():
    s = [(t, 15, 20.0, 20.0, None, 20.0, 15, 0.0) for t in np.arange(30.0, 6001, 30.0)]
    e = s0.estimate(s)
    assert e["t_b"] is None and e["drop"] is None


def test_step_locked_counts_fail_criterion_1():
    runs = [{"est": s0.estimate(_series(0.5)), "res": {"collisions": 0}} for _ in range(10)]
    st = s0.row_stats(runs)
    assert not st["c1"] and st["c3"]


def test_null_threshold_and_route():
    rng = np.random.default_rng(3)
    null = list(rng.normal(0.0, 0.03, 20))
    tau = s0.tau_null(null, 10)
    assert 0.0 < tau < 0.04
    assert s0.lower95(list(rng.normal(0.10, 0.02, 10))) > tau
    v = {"leIDM1": {"pass": False}, "leIDM26": {"pass": False}, "zipIDM": {"pass": True, "step": 0.25}}
    assert s0.route(v) == {"route": "zipIDM", "step": 0.25}
    assert s0.route({})["route"] == "A-UNTESTABLE(BN4)"


def test_config_knobs_in_tag_and_vtype():
    c = pl.Config(**s0.cfg("leIDM26", 0.25))
    assert "_a2.6" in c.tag() and "_tt-1" in c.tag() and 'accel="2.6"' in pl.vtype_xml(c)
    k = pl.Config(**s0.cfg("leKrauss", 0.5))
    assert "accel" not in pl.vtype_xml(k) and pl.Config().tag() == pl.Config(geom="bn4").tag()
