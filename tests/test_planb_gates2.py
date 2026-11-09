"""Plan B's S2 gates (planb.md §7.3) on planted rows: one planted failure per world, so each gate component must bite on its own."""
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "docs/research/planb"))
import gates2 as g2  # noqa: E402

TRACE = {"S": True, "SURGE": True, "TRUCK": True}
CELLS = ["SURGE", "TRUCK"]


def row(seed, delay, cong=1000.0, run=0.0, stuck=0, pend=2.0, b3=50.0, coll=0.0, rng=None, sd=0.003):
    e = rng.normal(0, sd)
    m = {k: [60.0] * 25 for k in ("ramp1_pending", "ramp2_pending", "ramp1_queue", "ramp2_queue")}
    return {"seed": seed, "all_delay": delay * (1 + e), "ttc_net": 1000.0, "passed": 3000.0, "collisions": coll, "contact_steps": coll,
            "b3_step": b3, "brake3": b3 * 0.4, "out_b3": b3 * 0.6, "end_stop": 1.0, "end_stop2": 2.0, "m_cong_vs": cong * (1 + e),
            "m_cong_run_s": run, "m_cong_vs_nc": cong * (1 + e), "m_cong_run_s_nc": run, "m_stuck_n": stuck, "m_pending_end": pend,
            "m_main_pending_min": [30.0] * 25, "m_minute": m, "m_road_ttc3": {"3": {"before": 5}}}


def world(cell_delay=1.25, cell_cong=2.0, cell_run=600.0, placebo_delay=1.002, rule_gain=0.7, gain=None):
    rng = np.random.default_rng(3)
    T = {}
    for cond in ("S", "SURGE", "TRUCK", "PLACEBO"):
        for a in ("nc", "p333", "3e"):
            if cond == "PLACEBO" and a == "3e":
                continue
            base = 100000.0 * (1.0 if a == "nc" else (gain or {}).get(a, rule_gain))
            f = {"S": 1.0, "PLACEBO": placebo_delay}.get(cond, cell_delay)
            cong = 1000.0 * ({"S": 1.0, "PLACEBO": 1.0}.get(cond, cell_cong))
            run = 0.0 if cond in ("S", "PLACEBO") else cell_run
            T[f"{cond}|{a}"] = [row(s, base * f, cong, run, rng=rng) for s in range(40)]
    return T


def read(T, cells=CELLS, trace=TRACE):
    return g2.read(T, cells, trace)


def scale(T, name, key, f):
    for r in T[name]:
        r[key] *= f


def test_a_binding_cell_passes():
    res = read(world())
    assert not res["null_broken"] and res["kill"] is False
    c = res["cells"]["SURGE"]
    assert c["G1_pass"] and c["G2_pass"] and c["G4_pass"] and c["passes"] and c["status"] == "passes"
    assert c["drain_cap"] == 1.5 * 2.0
    assert c["G2"]["p333"][0] == pytest.approx(30.0, abs=0.5)     # (100,000 - 70,000) / 100,000 against no control


def test_g1_components_each_drop_the_cell():
    res = read(world(cell_delay=1.05), ["SURGE"])
    assert not res["cells"]["SURGE"]["G1_pass"] and res["kill"] is True
    assert not read(world(cell_cong=1.05))["cells"]["SURGE"]["passes"]     # G1b's congested vehicle-seconds alone
    assert not read(world(cell_run=290.0))["cells"]["SURGE"]["passes"]
    assert read(world(cell_run=310.0))["cells"]["SURGE"]["passes"]
    assert not read(world(cell_delay=1.09))["cells"]["SURGE"]["passes"]
    assert read(world(cell_delay=1.11))["cells"]["SURGE"]["passes"]
    T = world()
    scale(T, "SURGE|p333", "all_delay", 1.05 / 1.25)     # only p333 is not hurt: G1 needs both arms
    assert not read(T)["cells"]["SURGE"]["passes"]


def test_g1b_for_truck_uses_the_field_without_capped_trucks():
    T = world()
    for a in ("nc", "p333"):
        for r, s in zip(T[f"TRUCK|{a}"], T[f"S|{a}"]):
            r["m_cong_vs_nc"] = s["m_cong_vs"]     # congested only in the capped trucks' own samples
    res = read(T)
    assert not res["cells"]["TRUCK"]["passes"] and res["cells"]["SURGE"]["passes"]
    T = world()
    for a in ("nc", "p333"):
        for r, s in zip(T[f"SURGE|{a}"], T[f"S|{a}"]):
            r["m_cong_vs_nc"] = s["m_cong_vs"]     # SURGE reads the full field
    assert read(T)["cells"]["SURGE"]["passes"]


def test_placebo_passing_stops_the_stage_without_a_kill():
    res = read(world(placebo_delay=1.2))
    assert res["null_broken"] and res["kill"] is None
    assert all(c["passes"] is None and c["status"].startswith("stopped") for c in res["cells"].values())


def test_g2_either_rule_binds():
    assert read(world(gain={"p333": 0.7, "3e": 0.95}))["cells"]["SURGE"]["G2_pass"]
    assert read(world(gain={"p333": 0.95, "3e": 0.7}))["cells"]["SURGE"]["G2_pass"]
    T = world(gain={"p333": 0.8, "3e": 0.95})     # G1 still holds for p333 after the override below
    for s, (r, n) in enumerate(zip(T["SURGE|p333"], T["SURGE|nc"])):
        r["all_delay"] = n["all_delay"] * (0.85 if s <= 20 else 1.10)     # 21 seeds 15 % better, 19 seeds 10 % worse
    c = read(T)["cells"]["SURGE"]
    assert c["G2"]["p333"][0] >= 10.0 and c["G2"]["p333"][1] <= 0 and not c["G2_pass"] and c["passes"] is None     # a point is not enough


def test_g2_failure_waits_for_every_carried_rule():
    T = world(rule_gain=0.95)
    res = read(T)
    c = res["cells"]["TRUCK"]
    assert not c["G2_pass"] and c["passes"] is None and c["status"].startswith("G2 pending") and res["kill"] is None
    rng = np.random.default_rng(5)
    for i, r in enumerate(g2.FALLBACK):
        gain = 0.8 if i == 3 else 0.97
        T[f"TRUCK|{r}"] = [row(s, 100000.0 * gain * 1.25, rng=rng) for s in range(40)]
        T[f"SURGE|{r}"] = [row(s, 100000.0 * 0.97 * 1.25, rng=rng) for s in range(40)]
    res = read(T)
    assert res["cells"]["TRUCK"]["passes"] and res["cells"]["TRUCK"]["G2_fallback"][g2.FALLBACK[3]][0] == pytest.approx(20.0, abs=1.0)
    assert res["cells"]["SURGE"]["passes"] is False and res["kill"] is False     # no carried rule binds in SURGE: it drops


def test_g4_components_each_drop_the_cell():
    def drops(T, cell="SURGE", trace=TRACE):
        return not read(T, trace=trace)["cells"][cell]["passes"]
    T = world()
    T["SURGE|nc"][3]["m_stuck_n"] = 1
    assert drops(T)
    T = world()
    T["SURGE|p333"][3]["m_stuck_n"] = 1     # p333's rows are checked too
    assert drops(T)
    T = world()
    scale(T, "SURGE|p333", "brake3", 1.2)
    assert drops(T)
    T = world()
    for r in T["SURGE|nc"]:
        r["m_main_pending_min"] = [31.0] * 25     # any backlog above S fails SURGE's drain
    assert drops(T)
    T = world()
    for r in T["TRUCK|nc"]:
        r["m_main_pending_min"] = [31.0] * 25     # TRUCK allows S's + 10 %
    assert not drops(T, "TRUCK")
    T = world()
    for r in T["SURGE|nc"]:
        r["m_minute"]["ramp1_pending"] = [60.0] * 20 + [90.0] * 5     # ramp pending is part of the backlog, inside minutes 20-24
    assert drops(T)
    T = world()
    for r in T["SURGE|nc"]:
        r["m_main_pending_min"] = [99.0] * 20 + [30.0] * 5     # outside the window: no effect
    assert not drops(T)
    T = world()
    for r in T["SURGE|p333"]:
        r["m_minute"]["ramp2_queue"] = [60.0] * 20 + [63.0] * 5     # +5 %: within the tolerance
    assert not drops(T)
    for r in T["SURGE|p333"]:
        r["m_minute"]["ramp2_queue"] = [60.0] * 20 + [69.0] * 5     # +15 %
    assert drops(T)
    T = world()
    for r in T["SURGE|p333"]:
        r["collisions"] = r["contact_steps"] = 2.0
    assert drops(T)
    assert drops(world(), trace={"S": True, "SURGE": False, "TRUCK": True})     # G4(iv): a failed trace drops the cell
    assert drops(world(), trace={"S": False, "SURGE": True, "TRUCK": True})


def test_drain_cap_is_the_largest_no_control_backlog():
    T = world()
    for i, r in enumerate(T["SURGE|nc"]):
        r["m_pending_end"] = float(i % 10)
    assert read(T)["cells"]["SURGE"]["drain_cap"] == 1.5 * 9.0
