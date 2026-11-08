"""Plan B's S2 gates (planb.md §7.3) on planted rows."""
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "docs/research/planb"))
import gates2 as g2  # noqa: E402


def row(seed, delay, cong=1000.0, run=0.0, stuck=0, pend=2.0, b3=50.0, coll=0.0, rng=None):
    e = rng.normal(0, 0.003)
    m = {k: [60.0] * 25 for k in ("ramp1_pending", "ramp2_pending", "ramp1_queue", "ramp2_queue")}
    return {"seed": seed, "all_delay": delay * (1 + e), "ttc_net": 1000.0, "passed": 3000.0, "collisions": coll, "contact_steps": coll,
            "b3_step": b3, "brake3": b3 * 0.4, "out_b3": b3 * 0.6, "end_stop": 1.0, "end_stop2": 2.0, "m_cong_vs": cong * (1 + e),
            "m_cong_run_s": run, "m_cong_vs_nc": cong * (1 + e), "m_cong_run_s_nc": run, "m_stuck_n": stuck, "m_pending_end": pend,
            "m_main_pending_min": [30.0] * 25, "m_minute": m, "m_road_ttc3": {"3": {"before": 5}}}


def world(cell_delay=1.25, cell_cong=2.0, cell_run=600.0, placebo_delay=1.002, rule_gain=0.7):
    rng = np.random.default_rng(3)
    T = {}
    for cond in ("S", "SURGE", "TRUCK", "PLACEBO"):
        for a in ("nc", "p333", "3e"):
            if cond == "PLACEBO" and a == "3e":
                continue
            base = 100000.0 * (1.0 if a == "nc" else rule_gain)
            f = {"S": 1.0, "PLACEBO": placebo_delay}.get(cond, cell_delay)
            cong = 1000.0 * ({"S": 1.0, "PLACEBO": 1.0}.get(cond, cell_cong))
            run = 0.0 if cond in ("S", "PLACEBO") else cell_run
            T[f"{cond}|{a}"] = [row(s, base * f, cong, run, rng=rng) for s in range(40)]
    return T


def test_a_binding_cell_passes():
    res = g2.read(world(), ["SURGE", "TRUCK"])
    assert not res["null_broken"] and not res["kill"]
    c = res["cells"]["SURGE"]
    assert c["G1_pass"] and c["G2_pass"] and c["G4_pass"] and c["passes"]
    assert c["drain_cap"] == 1.5 * 2.0


def test_a_cell_that_does_not_hurt_drops_and_all_dropping_kills():
    res = g2.read(world(cell_delay=1.05), ["SURGE"])
    assert not res["cells"]["SURGE"]["G1_pass"] and res["kill"]
    res = g2.read(world(cell_run=200.0), ["SURGE"])     # congested 0.3 km for less than 5 minutes
    assert not res["cells"]["SURGE"]["G1"]["nc"]["G1b_pass"]


def test_placebo_passing_breaks_the_null():
    res = g2.read(world(placebo_delay=1.2), ["SURGE"])
    assert res["null_broken"] and not res["cells"]["SURGE"]["passes"]


def test_g2_needs_a_rule_10_percent_better_than_no_control():
    res = g2.read(world(rule_gain=0.95), ["TRUCK"])
    assert not res["cells"]["TRUCK"]["G2_pass"] and res["cells"]["TRUCK"]["g2_failed_action"]


def test_drain_and_pr09():
    T = world()
    T["SURGE|nc"][3]["m_stuck_n"] = 1
    for r in T["SURGE|p333"]:
        r["brake3"] *= 1.2
    c = g2.read(T, ["SURGE"])["cells"]["SURGE"]
    assert not c["G4"]["nc"]["stuck_pass"] and not c["G4"]["p333"]["pr09_pass"] and not c["passes"]
    T = world()
    for r in T["SURGE|nc"]:
        r["m_main_pending_min"] = [31.0] * 25     # any backlog above S fails SURGE's drain
    assert not g2.read(T, ["SURGE"])["cells"]["SURGE"]["G4"]["nc"]["backlog_pass"]
