"""Plan B's S6 reading (planb.md §8) on planted rows with known outcomes."""
import json
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
            "alks_full_moving": 0.0, "robust_rate": 50.0, "stuck_n": 0.0, "pending_end": 5.0, "b3_step": 100.0, "b45_step": 10.0, "alks_past": 1.0,
            "ttt": 200000.0, "loc": {"delay|3|before": 100.0, "cf|3|before": 5.0}}


def world(cell="X", delay=(-0.03,) * 5, cf=(-0.2,) * 5, brake=0.0, brake_sd=0.0, coll=0.0, stuck=None, opp_delay=None, s_loss=lambda n, s: 7000.0,
          full=0.0, flow=0.0):
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
            b["alks_full_moving"] = full
            b["passed"] *= 1 + flow
            if stuck and stuck == (n, s):
                b["stuck_n"] = 1.0
            T[(cell, n)][s] = b
    if s_loss is not None:     # steady rows: each controller's delay in S is its cell delay minus its loss
        for name in OPP + ["nc"] + LEARN:
            T[("S", name)] = {s: {**T[(cell, name)][s], "all_delay": T[(cell, name)][s]["all_delay"] - s_loss(name, s)} for s in range(N)}
    return T


def cfg(cells=("X",), m=2):
    return {"m": m, "cells": list(cells), "learners": LEARN, "opponents": {c: OPP for c in cells}, "drain_cap": {c: 50.0 for c in cells},
            "seed_range": [0, N - 1], "s_alias": {}, "p333": "p333", "nc": "nc", "t3e": "3e", "e3c": {}, "e3d": {}, "null_swaps": 40}


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


def pack_row(name, seed, **kw):
    r = {"name": name, "seed": seed, "all_delay": 1.0, "ttc_net": 2.0, "passed": 3.0, "collisions": 0, "alks_full_moving": 1, "N": 7.0,
         "m_peak_car": [5, 4, 3, 2, 1, 0, 0, 0, 0], "m_peak_alks": [9, 9, 1, 0, 2, 1, 0, 1, 5], "m_peak_truck": [7, 2, 1, 0, 0, 0, 0, 0, 0],
         "m_dist_m_car": 1e6, "m_dist_m_alks": 1e6, "m_dist_m_truck": 0.0, "m_stuck_n": 0, "m_pending_end": 3, "b3_step": 4.0, "b45_step": 1.0,
         "m_road_vs": {"3": {"before": 100.0}, "pending_main": {"before": 4.0}}, "m_road_dist": {"3": {"before": 2777.7777777777778}},
         "m_road_ttc3": {"3": {"before": 2}}, "m_robust_road": {"4a": {"trucks": 1}}, "end_stop2": 3.0}
    r |= {k: 1.0 for k in ("ttc2", "ttc15", "sev3", "gap25", "delay_ramp", "delay_ramp2", "m_cong_vs", "m_cong_run_s", "m_cong_vs_nc",
                           "m_cong_run_s_nc", "contact_steps")} | {"m_ttc3_lc": 0, "m_ttc3_all": 0}     # v2's report fields, present in every S6 row
    return r | kw


def test_derive_from_a_pack_row():
    d = r6.derive(pack_row("X|w0", 0))
    assert d["robust_rate"] == pytest.approx(1000.0 * (6 + 10 + 3) / 2000.0)
    assert d["alks_past"] == 2 + 1 + 0 + 1 and d["ttt"] == 7.0
    assert d["loc"] == {"delay|3|before": pytest.approx(0.0), "delay|pending_main|before": 4.0, "cf|3|before": 2.0, "brk|4a|trucks": 1.0, "end_stop2": 3.0}


def test_missing_data_stops_the_reading():
    T = world()
    del T[("X", "lr")]
    with pytest.raises(SystemExit):
        r6.read(T, cfg())     # an absent opponent never reads as "did not bind" (review F1)
    T = world()
    del T[("X", "p333")][7]
    with pytest.raises(SystemExit):
        r6.read(T, cfg())
    T = world()
    T[("X", "w1")][N + 5] = T[("X", "w1")][0]
    with pytest.raises(SystemExit):
        r6.read(T, cfg())
    T = world()
    del T[("S", "lr")]
    with pytest.raises(SystemExit):
        r6.read(T, cfg())


def test_crash_drops_apply_to_every_arm():
    T = world()
    del T[("X", "w2")][7]
    c = r6.read(T, cfg(), drops={"X": [7]})["cells"]["X"]
    assert c["n_seeds"] == N - 1 and c["dropped_seeds"] == [7] and c["outcome"] == "W"


def test_load_rows_splits_names_and_refuses_bad_rows(tmp_path):
    conf = cfg()
    f = tmp_path / "rows.jsonl"
    f.write_text("\n".join(json.dumps(pack_row(n, s)) for n in ("X|w0", "S|w0") for s in (0, 1)))
    T = r6.load_rows(f, conf, list(range(N)))
    assert set(T) == {("X", "w0"), ("S", "w0")} and set(T[("X", "w0")]) == {0, 1}
    for bad in ([pack_row("X|w0", 0)] * 2, [pack_row("X|zz", 0)], [pack_row("X|w0", N + 1)], [pack_row("X|w0", 0, cell="S")]):
        f.write_text("\n".join(json.dumps(r) for r in bad))
        with pytest.raises(SystemExit):
            r6.load_rows(f, conf, list(range(N)))


def test_w_clauses_can_fail_without_changing_w():
    c = r6.read(world(cf=(-0.08,) * 5), cfg())["cells"]["X"]
    assert c["outcome"] == "W" and c["t2_policies"] == 0 and not c["t2_passes"]     # 8 % is below T2's 10 % margin
    c = r6.read(world(delay=(-0.06, -0.06, -0.06, -0.06, 0.02)), cfg())["cells"]["X"]
    assert c["outcome"] == "W" and c["k_policies"] == 4


def test_side_constraints_and_flow():
    c = r6.read(world(full=0.2), cfg())["cells"]["X"]
    assert c["outcome"] == "metric win, gate failure" and not c["gate"]["p333"]["full_emergency"]
    c = r6.read(world(flow=-0.01), cfg())["cells"]["X"]
    assert c["outcome"] == "metric win, gate failure" and not c["gate"]["p333"]["flow"]


def test_close_following_harm_is_l():
    c = r6.read(world(delay=(-0.05,) * 5, cf=(0.15,) * 5), cfg())["cells"]["X"]
    assert c["outcome"] == "L" and all(h == ["close-following"] for h in c["harm"].values())
    assert c["no_control"]["cf_shown_higher"]


def test_adaptation_gain_not_read_on_an_unstable_denominator():
    T = world()
    rng = np.random.default_rng(9)
    T[("X", "cfx")] = {s: {**T[("X", "3e")][s], "ttc_net": T[("X", "3e")][s]["ttc_net"] * (0.98 + rng.normal(0, 0.05))} for s in range(N)}
    ag = r6.read(T, cfg() | {"e3c": {"X": "cfx"}})["cells"]["X"]["adaptation_gain"]["cf"]
    assert not ag["read"] and ag["AG"] is None


def test_null_failures(monkeypatch):
    monkeypatch.setattr(r6, "swap_null", lambda *a, **k: 0.5)
    c = r6.read(world(), cfg())["cells"]["X"]
    assert c["outcome"] == "statistic failed its null" and c["outcome_before_null"] == "W"
    assert c["resilience"]["status"].startswith("report-only, not read")     # v2 (read6_v2_spec.md §1.2): R is never read here
    calls = []

    def later(*a, **k):
        calls.append(1)
        return 0.0 if len(calls) <= 2 else 0.5
    monkeypatch.setattr(r6, "swap_null", later)
    loss = lambda name, s: 5000.0 if name in LEARN else 9000.0
    c = r6.read(world(s_loss=loss), cfg())["cells"]["X"]
    assert c["outcome"] == "W" and c["resilience"]["reading"] == "statistic failed its null" and not c["resilience"]["passes"]


def test_resilience_reads_an_s_twin():
    T = world(s_loss=lambda name, s: 5000.0 if name in LEARN else 9000.0)
    del T[("S", "lr")]
    c = r6.read(T, cfg() | {"s_alias": {"lr": "p333"}})["cells"]["X"]
    assert c["resilience"]["per_opponent"]["lr"]["R"][0] == pytest.approx(4000.0, rel=0.05)


def test_report_map_and_flow_clause():
    res = r6.read(world(), cfg())
    c = res["cells"]["X"]
    assert set(c["map"]) == set(OPP) and all(c["map"][o]["cf"]["tile"] == "W" and c["map"][o]["cf"]["policies_w"] == 5 for o in OPP)
    assert set(c["map"]["p333"]) >= {"delay", "cf", "flow", "robust_braking", "alks_past_limit", "b45_step", "b3_step", "ttt", "markers", "per_learner"}
    assert c["closest"]["flow"] in OPP and len(c["comparisons"]["p333"]["flow"]) == 3
    assert c["location"]["v3w"]["delay|3|before"] == pytest.approx(100.0) and c["t2_counting_filter"]["policies"] == 5
    assert set(res["S"]["map"]) == set(OPP) and res["S"]["n_seeds"] == N


def test_drain_cap_on_the_end_of_run_backlog():
    T = world()
    T[("X", "w1")][3]["pending_end"] = 60.0     # above the cap of 50
    c = r6.read(T, cfg())["cells"]["X"]
    assert c["outcome"] == "metric win, gate failure" and c["drain_fail"]


def test_counting_filter_is_report_only_and_excludes_slow_opponents():
    T = world(opp_delay={"lr": 0.03})     # lr 3 % slower than p333: round 2's filter drops it
    for s in range(N):
        T[("X", "lr")][s]["ttc_net"] *= 0.85     # and v3w is only about 6 % better than lr on close-following
    c = r6.read(T, cfg())["cells"]["X"]
    assert c["outcome"] == "W" and c["t2_policies"] == 0     # the binding T2 has no filter (planb.md §8.3)
    assert c["t2_counting_filter"]["counted"] == ["3e", "p333"] and c["t2_counting_filter"]["policies"] == 5


def test_overfit_rows_point_the_right_way():
    c = r6.read(world(opp_delay={"lr": -0.03}), cfg())["cells"]["X"]
    assert c["overfit_vs_p333"]["lr"]["delay"][0] == pytest.approx(3.0, abs=0.5)     # positive: the opponent has less delay than p333


def test_flow_closest_opponent_and_interval_levels():
    T = world()
    rng = np.random.default_rng(11)
    for s in range(N):
        T[("X", "3e")][s]["passed"] *= 1.004 * (1 + rng.normal(0, 0.002))
    c = r6.read(T, cfg())["cells"]["X"]
    f, f95 = c["comparisons"]["3e"]["flow"], c["comparisons"]["3e"]["flow95"]
    assert c["closest"]["flow"] == "3e" and f[1] < f95[1] and f[2] > f95[2]     # the 1 - 0.05/m interval is the wider one


def test_markers_flag_a_side_limit_breach():
    T = world()
    for n in LEARN:
        for s in range(N):
            T[("X", n)][s]["b3_step"] *= 1.10     # 10 % more braking at 3 m/s² than every opponent
    c = r6.read(T, cfg())["cells"]["X"]
    assert all("brake" in c["map"][o]["markers"] for o in OPP)


def test_t2_turns_on_the_interval_from_the_cells_matrix():
    narrow = r6.read(world(cf=(-0.12,) * 5), cfg())["cells"]["X"]
    T = world(cf=(0.0,) * 5)
    for n in LEARN:
        for s in range(N):
            T[("X", n)][s]["ttc_net"] *= 0.8 if s < 31 else 1.2     # point +20 % for every learner, but its interval reaches -20 %
    wide = r6.read(T, cfg())["cells"]["X"]
    assert all(wide["map"]["p333"]["per_learner"][n]["cf"] >= 10.0 for n in LEARN)
    assert narrow["t2_counting_filter"]["policies"] == 5 and wide["t2_counting_filter"]["policies"] == 0


def test_pr28_share_from_the_road_bins():
    T = world()
    for n in LEARN:
        for s in range(N):
            T[("X", n)][s]["loc"] = {"delay|4a|before": 60.0, "delay|3|before": 90.0}
    for o in OPP:
        for s in range(N):
            T[("X", o)][s]["loc"] = {"delay|4a|before": 100.0, "delay|3|before": 100.0}     # 40 of the 50 veh-s gain on 4a
    c = r6.read(T, cfg())["cells"]["X"]
    assert c["pr28"]["share"] == pytest.approx(0.8) and c["pr28"]["adds_pr28"] and c["pr28"]["opponent"] == c["closest"]["delay"]
    for n in LEARN:
        for s in range(N):
            T[("X", n)][s]["loc"] = {"delay|4a|before": 100.0, "delay|3|before": 100.0}     # no road gain: not read
    assert not r6.read(T, cfg())["cells"]["X"]["pr28"]["read"]
