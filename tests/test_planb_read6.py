"""Plan B's S6 reading (planb.md §8) on planted rows with known outcomes."""
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "docs/research/planb"))
import read6 as r6  # noqa: E402

N = 60
LEARN = ["w0", "w1", "w2", "w3", "w4"]
OPP = ["p333", "lr", "3e"]


def base(seed, rng):
    return {"all_delay": 100000.0 + rng.normal(0, 3000), "ttc_net": 1000.0 + rng.normal(0, 30), "passed": 3000.0, "collisions": 0.0,
            "alks_full_moving": 0.0, "robust_rate": 50.0, "stuck_n": 0.0, "pending_end": 5.0, "b3_step": 100.0}


def world(cell="X", delay=(-0.03,) * 5, cf=(-0.2,) * 5, brake=0.0, brake_sd=0.0, coll=0.0, stuck=None, opp_delay=None, s_loss=lambda n, s: 7000.0):
    """Seed-paired rows: every arm shares the seed's base; v3w learners shift delay and close-following by the given fractions."""
    T = {}
    rng = np.random.default_rng(1)
    bases = {s: base(s, rng) for s in range(N)}
    noise = np.random.default_rng(2)
    for name in OPP + ["nc"]:
        T[(cell, name)] = {}
        for s in range(N):
            b = dict(bases[s])
            b["all_delay"] *= (1.3 if name == "nc" else 1.0) * (1 + (opp_delay or {}).get(name, 0.0)) * (1 + noise.normal(0, 0.002))
            b["ttc_net"] *= 1 + noise.normal(0, 0.005)
            T[(cell, name)][s] = b
    for i, n in enumerate(LEARN):
        T[(cell, n)] = {}
        for s in range(N):
            b = dict(bases[s])
            b["all_delay"] *= (1 + delay[i]) * (1 + noise.normal(0, 0.002))
            b["ttc_net"] *= (1 + cf[i]) * (1 + noise.normal(0, 0.005))
            b["robust_rate"] *= 1 + brake + noise.normal(0, brake_sd)
            b["collisions"] = coll
            if stuck and stuck == (n, s):
                b["stuck_n"] = 1.0
            T[(cell, n)][s] = b
    if s_loss is not None:     # steady rows: each controller's delay in S is its cell delay minus its loss
        for name in OPP + ["nc"] + LEARN:
            T[("S", name)] = {s: {**T[(cell, name)][s], "all_delay": T[(cell, name)][s]["all_delay"] - s_loss(name, s)} for s in range(N)}
    return T


def cfg(cells=("X",), m=2):
    return {"m": m, "cells": list(cells), "learners": LEARN, "opponents": {c: OPP for c in cells}, "drain_cap": {c: 50.0 for c in cells},
            "p333": "p333", "nc": "nc", "t3e": "3e", "e3c": {}, "e3d": {}, "null_swaps": 40}


def test_clear_win_is_w_with_clauses():
    res = r6.read(world(), cfg())
    c = res["cells"]["X"]
    assert c["outcome"] == "W" and res["study"] == "PASS"
    assert c["k_policies"] == 5 and c["t2_policies"] == 5 and c["t2_passes"]
    assert all(v["ok"] for v in c["null"].values())
    assert c["d4"]["delay"]["arm"][0] == pytest.approx(3.0, abs=0.3)
    assert c["no_control"]["delay"][0] > 20.0


def test_braking_point_over_tolerance_is_w_b_and_shown_over_fails():
    c = r6.read(world(brake=0.14, brake_sd=0.15), cfg())["cells"]["X"]
    assert c["outcome"] == "W-b" and c["brake_point_over"] and not c["brake_failed"]
    c = r6.read(world(brake=0.25, brake_sd=0.01), cfg())["cells"]["X"]
    assert c["outcome"] == "metric win, braking constraint failed"


def test_harm_is_l_and_vetoes_a_win_elsewhere():
    T = world("A") | {k: v for k, v in world("B", delay=(0.05,) * 5, cf=(0.0,) * 5).items() if k[0] == "B"}
    res = r6.read(T, cfg(("A", "B")))
    assert res["cells"]["B"]["outcome"] == "L" and res["cells"]["A"]["outcome"] == "W"
    assert res["study"] == "NULL" and res["vetoed_cells"] == ["A"]


def test_no_difference_is_t():
    c = r6.read(world(delay=(0.0,) * 5, cf=(0.0,) * 5), cfg())["cells"]["X"]
    assert c["outcome"] == "T"


def test_learner_condition():
    c = r6.read(world(delay=(-0.06, -0.06, -0.06, -0.06, 0.02)), cfg())["cells"]["X"]
    assert c["outcome"] == "W" and c["n_learner_signs"] == 4     # one bad learner: still W
    c = r6.read(world(delay=(-0.08, -0.08, -0.08, 0.02, 0.02)), cfg())["cells"]["X"]
    assert c["outcome"] == "arm win, learners inconsistent" and c["n_learner_signs"] == 3


def test_gates_drain_collisions_flow():
    c = r6.read(world(stuck=("w2", 7)), cfg())["cells"]["X"]
    assert c["outcome"] == "metric win, gate failure" and c["drain_fail"]
    c = r6.read(world(coll=0.1), cfg())["cells"]["X"]
    assert c["outcome"] == "metric win, gate failure" and not c["gate"]["p333"]["collisions"]


def test_closest_opponent_is_the_lowest_lower_bound():
    c = r6.read(world(opp_delay={"lr": -0.025}), cfg())["cells"]["X"]
    assert c["closest"]["delay"] == "lr"


def test_resilience_reading():
    loss = lambda name, s: 5000.0 if name in LEARN else 9000.0
    c = r6.read(world(s_loss=loss), cfg())["cells"]["X"]
    assert c["resilience"]["passes"] and c["resilience"]["per_opponent"]["p333"]["R"][0] == pytest.approx(4000.0, rel=0.05)
    same = lambda name, s: 7000.0
    c = r6.read(world(s_loss=same), cfg())["cells"]["X"]
    assert not c["resilience"]["passes"]


def test_swap_null_near_nominal_on_symmetric_noise():
    d = np.random.default_rng(5).normal(0, 1, 60)
    rate = r6.swap_null(d, 1.25, 400, 9, b=2000)
    assert rate <= 0.05


def test_adaptation_gain_reads_only_a_stable_denominator():
    T = world()
    for s in range(N):
        T[("X", "cfx")] = T.get(("X", "cfx"), {})
        T[("X", "cfx")][s] = {**T[("X", "3e")][s], "ttc_net": T[("X", "3e")][s]["ttc_net"] * 0.6}
    conf = cfg() | {"e3c": {"X": "cfx"}}
    ag = r6.read(T, conf)["cells"]["X"]["adaptation_gain"]["cf"]
    assert ag["read"] and ag["AG"][0] == pytest.approx(0.5, abs=0.05)     # v3w closes half of 3E-T -> 3E-C's 40 %


def test_derive_from_a_pack_row():
    r = {"all_delay": 1.0, "ttc_net": 2.0, "passed": 3.0, "collisions": 0, "alks_full_moving": 1,
         "m_peak_car": [5, 4, 3, 2, 1, 0, 0, 0, 0], "m_peak_alks": [9, 9, 1, 0, 0, 0, 0, 0, 0], "m_peak_truck": [7, 2, 1, 0, 0, 0, 0, 0, 0],
         "m_dist_m_car": 1e6, "m_dist_m_alks": 1e6, "m_dist_m_truck": 0.0, "m_stuck_n": 0, "m_pending_end": 3, "b3_step": 4.0}
    d = r6.derive(r)
    assert d["robust_rate"] == pytest.approx(1000.0 * (6 + 1 + 3) / 2000.0)
