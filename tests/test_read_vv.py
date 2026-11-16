"""Merge V&V reader (merge_vv.md §6): planted rows give the readings the protocol fixes; V1's checks catch planted faults."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "docs" / "research" / "vv"))
import read_vv as rv  # noqa: E402

ARMS = rv.V3W + rv.RULES + rv.REFS
N = 120


@pytest.fixture(autouse=True)
def small(monkeypatch):
    monkeypatch.setattr(rv, "B", 2000)
    monkeypatch.setattr(rv, "SWAPS", 200)
    monkeypatch.setattr(rv, "NB", 200)
    monkeypatch.setattr(rv, "RE_SWAPS", 400)
    monkeypatch.setattr(rv, "NB_W", 200)


def rows(ttc: dict, meter: dict | None = None, stand: tuple = (200.0, 400.0), seed=0) -> dict:
    """(cell, arm) -> seed -> derived values; ttc[(cell, arm)] is the mean close-following, with seed noise shared by all arms."""
    rng = np.random.default_rng(seed)
    base = rng.normal(0.0, 40.0, N)
    T = {}
    for (cell, arm), m in ttc.items():
        noise = rng.normal(0.0, 20.0, N)
        x = m + base + noise
        st = stand if cell == "L300" else (stand[0] * 0.05, stand[1] * 0.05)
        T[(cell, arm)] = {}
        for i, s in enumerate(range(N)):
            d = {k: 0.0 for k in rv.KEYS}
            d |= {"ttc_net": x[i], "vv_ttc3_main": 0.3 * x[i], "g_merge": 0.8 * x[i], "g_edge1": 0.05 * x[i], "g_rest": 0.15 * x[i],
                  "ttc_no_e1": 0.95 * x[i], "all_delay": 1e5 + base[i], "N": 6e5, "passed": 2180.0, "end_stop": st[0], "end_stop2": st[1],
                  "vv_m_time": x[i] * (meter or {}).get((cell, arm), 1.0), "jams": 8.0}
            d |= {"meter_ok": True, "x_out": 0.0, "c15": [1.0, 100.0], "stand_n": {"3a_0": 5, "4a_0": 9}}
            T[(cell, arm)][s] = d
    return T


def plan(v300: float, r300: float, v600: float, r600: float) -> dict:
    t = {}
    for cell, v, r in (("L300", v300, r300), ("L600", v600, r600)):
        t |= {(cell, w): v for w in rv.V3W} | {(cell, a): r for a in rv.RULES} | {(cell, "p333"): r, (cell, "nc"): r * 1.2}
    return t


def test_holds_and_replicated():
    out = rv.v3(rows(plan(900, 1100, 400, 500)), list(range(N)), [], ["cpu"])
    assert out["v3a"]["replication"]["reading"] == "REPLICATED" and out["v3b"]["reading"] == "HOLDS"
    assert out["v3a"]["main_lane"]["reading"] == "also shown on main-lane samples"
    assert out["v2"]["outcome"] == "MET" and not out["void"]


def test_worse_at_600():
    out = rv.v3(rows(plan(900, 1100, 600, 450)), list(range(N)), [], ["cpu"])
    assert out["v3b"]["reading"] == "WORSE" and set(out["v3b"]["worse"]["worse"]) == set(rv.RULES)
    ch = out["v3b"]["change"]["lr400_16_1"]
    assert ch["hi"] < 0 and ch["depends"]


def test_not_shown_and_no_change():
    out = rv.v3(rows(plan(500, 500, 500, 500)), list(range(N)), [], ["cpu"])
    assert out["v3a"]["replication"]["reading"] == "NOT REPLICATED" and out["v3b"]["reading"] == "NOT SHOWN"
    assert not out["v3b"]["change"]["lr400_16_1"]["depends"]


def test_v2_limit_when_the_01s_edge_differs():
    meter = {("L300", w): 1.15 for w in rv.V3W}     # 0.1-s time 15 % higher for the policy only: its edge drops by about 15 points
    out = rv.v3(rows(plan(900, 1100, 400, 500), meter=meter), list(range(N)), [], ["cpu"])
    assert out["v2"]["outcome"] == "LIMIT" and out["v2"]["lr400_16_1"]["diff"]["hi"] < -rv.V2_MARGIN


def test_standing_cut():
    out = rv.v3(rows(plan(900, 1100, 400, 500)), list(range(N)), [], ["cpu"])
    c = out["v3b"]["cut"]
    assert c["merge1"]["removed"] and c["merge2"]["removed"] and c["merge2"]["nc"]["cut"] == pytest.approx(0.95)


def test_meter_bug_and_cpu_void():
    T = rows(plan(900, 1100, 400, 500))
    T[("L300", "nc")][3]["meter_ok"] = False
    out = rv.v3(T, list(range(N)), [], ["a", "b"])
    assert out["v2"]["outcome"] == "BUG" and out["void"]


def traced_row():
    """Two closing pairs: one on 3a_0 behind a vehicle standing at the lane end, one on a main lane; then a lane-end stander."""
    tr = [[700.0, "f1", "l1", "car", "alks", "3a", "3a_0", 250.0, 5.0, "3a", "3a_0", 290.0, 5.0, 32.5, 2.5, 15.0, 0.5],
          [701.0, "f1", "l1", "car", "alks", "3a", "3a_0", 256.0, 5.0, "3a", "3a_0", 290.0, 5.0, 26.5, 2.5, 12.0, 0.4],
          [705.0, "f2", "l2", "alks", "car", "3", "3_1", 100.0, 5.0, "3", "3_1", 140.0, 5.0, 32.5, 2.5, 30.0, 10.0]]
    et = [[700.0, "3a_0", 294.72, [["l1", 290.0, 0.5], ["f1", 250.0, 8.0]]], [701.0, "3a_0", 294.72, [["l1", 290.0, 0.4]]], [700.0, "4a_0", 294.72, []]]
    return {"name": "L300|nc~trace", "seed": 1, "ttc_net": 3.0, "vv_trace": tr, "m_road_ttc3": {"3a": {"after": 2}, "3": {"rest": 1}},
            "vv_ttc3_main": 1.0, "vv_enc": 2.0, "end_trace": et, "end_stop": 2.0, "end_stop2": 0.0, "vv_stand_s": {"3a_0": 2, "4a_0": 0},
            "vv_stand_n": {"3a_0": 1, "4a_0": 0}, "pert_log": [["drawn", 500.0, 180.0]], "vv_lanes": {"3a_0": 294.72, "4a_0": 294.72}}


def test_v1_clean_row():
    o = rv.v1_row(traced_row(), [{"v": "f2", "t": 702.0}])
    assert o["wiring"] == [] and o["definition"] == []
    assert o["encounters"] == {"n": 2, "durations": {2: 1, 1: 1}}
    keys = list(o["classes"])
    assert any("acc/ramp | same lane | leader standing" in k and "| after |" in k for k in keys)
    assert any(k.startswith("main | same lane | - | merged 5 s | alks | hi") for k in keys)


def test_v1_catches_planted_faults():
    r = traced_row()
    r["vv_trace"][2][13] = 30.0     # SUMO gap no longer matches the positions
    r["ttc_net"] = 4.0               # counter and log disagree
    r["vv_stand_s"]["3a_0"] = 1
    o = rv.v1_row(r, [])
    assert any("gap" in x for x in o["definition"])
    assert any("samples" in x for x in o["wiring"]) and any("end_stop" in x for x in o["wiring"])
    r = traced_row()
    r["vv_trace"][2][10] = "3_2"     # the leader on another lane of the same edge
    assert any("cross-lane" in x for x in rv.v1_row(r, [])["definition"])
