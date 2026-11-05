"""Confirmatory 3: rule counts, the statistic, the claim logic and the reproduction of the shot's table."""
import csv
import gzip
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "docs/research/conf3"))
import common as cm  # noqa: E402
import decide3 as dc  # noqa: E402
import make_env as me  # noqa: E402
import select_opp as so  # noqa: E402
import collapse as cl  # noqa: E402


def row(seed, **k):
    return {"seed": seed, **k}


def arm(n=20, **k):
    return {7_000 + s: row(7_000 + s, **{a: (b[s] if isinstance(b, list) else b) for a, b in k.items()}) for s in range(n)}


def test_rule_counts():
    f = cm.families()
    assert {k: len(v) for k, v in f.items()} == {"uniform": 4, "zone": 30, "on4a": 3, "local": 12, "adapt4a": 12, "own": 8}
    assert sum(len(v) for v in f.values()) + 1 == 70
    assert "p333" in f["uniform"] and "z33333" not in f["zone"] and "z11111" not in f["zone"]


def test_conditions_match_the_earlier_runs():
    sys.path.insert(0, str(ROOT / "docs/research/phase3"))
    text = (ROOT / "docs/research/phase3/runs.py").read_text()
    assert '"limit_kmh": 25, "dur": 120.0, "times": [600.0, 1200.0], "taper": 20.0' in text and cm.COND["X1"]["times"] == [600.0, 1200.0]
    assert '"limit_kmh": 30, "dur": 180.0, "times": [700.0], "taper": 20.0' in text and cm.COND["X2"]["dur"] == 180.0


def test_missing_counter_is_zero():
    A, B = arm(alks_full_moving=2.0), {k: {"seed": k} for k in arm()}
    assert cm.paired_median(A, B, "alks_full_moving") == 2.0
    assert cm.med(B, "alks_full_moving") == 0.0


def test_statistic_reproduces_the_shot_table():
    T = {}
    for line in gzip.open(ROOT / "docs/research/phase3/shot_rows.jsonl.gz", "rt"):
        r = json.loads(line)
        T.setdefault(r["name"], {})[r["seed"]] = r
    n = 0
    for x in csv.DictReader(open(ROOT / "docs/research/phase3/shot_table.csv")):
        a, b = T[f"{x['cell']}|{x['policy']}"], T[f"{x['cell']}|r4a1"]
        for key, field in (("ttc_net", "ttc"), ("delay", "delay")):
            assert cm.effect(a, b, key) == (float(x[field]), float(x[field + "_lo"]), float(x[field + "_hi"]))
            n += 1
    assert n == 28


def good(**k):
    base = dict(ttc_net=1000.0, all_delay=1000.0, passed=2000.0, b3_step=1000.0, alks_full_moving=10.0, collisions=0.0, sev3=50.0)
    return arm(**{**base, **k})


def spread(x, sd=1.0):
    return [x + sd * ((i % 5) - 2) for i in range(20)]


def test_clears_needs_the_margin_and_the_limits():
    O = good(ttc_net=spread(1000.0, 5.0))
    assert dc.clears(good(ttc_net=spread(800.0, 5.0)), O, 10.0)
    assert not dc.clears(good(ttc_net=spread(950.0, 5.0)), O, 10.0)
    assert not dc.clears(good(ttc_net=spread(800.0, 5.0), all_delay=1030.0), O, 10.0)
    assert not dc.clears(good(ttc_net=spread(800.0, 5.0), passed=1980.0), O, 10.0)
    assert not dc.clears(good(ttc_net=spread(800.0, 5.0), b3_step=1060.0), O, 10.0)
    assert not dc.clears(good(ttc_net=spread(800.0, 5.0), alks_full_moving=30.0), O, 10.0)
    assert not dc.clears(good(ttc_net=spread(800.0, 5.0), collisions=[1.0, 1.0] + [0.0] * 18), O, 10.0)
    assert dc.clears(good(ttc_net=spread(800.0, 5.0), collisions=[1.0] + [0.0] * 19), O, 10.0)
    assert not dc.clears(good(ttc_net=spread(5.0, 0.1)), good(ttc_net=spread(20.0, 0.1)), 10.0), "fewer than 20 per run lower"


def table(cell, **arms):
    return {(f"{cell}|{k}", cm.Q): v for k, v in arms.items()}


def opp(forms, single="r"):
    return {"cells": {"X1": {"forms": forms, "delay_opponent": "p333", "front_row": "r"}}, "single_rule": single}


def test_every_counting_opponent_must_be_cleared():
    win, opp_weak, opp_strong = good(ttc_net=spread(700.0, 5.0)), good(ttc_net=spread(1000.0, 5.0)), good(ttc_net=spread(730.0, 5.0))
    pols = {f"d{i}": win for i in range(5)}
    nc = good(ttc_net=spread(500.0, 5.0), all_delay=1500.0)
    T = table("X1", p333=opp_weak, nc=nc, r=opp_weak, s=opp_strong, **pols)
    assert dc.read_cell(T, "X1", opp({"on4a": "r"}))["tuned_won"]
    assert not dc.read_cell(T, "X1", opp({"on4a": "r", "own": "s"}))["tuned_won"]
    assert dc.read_cell(T, "X1", opp({"on4a": "r"}))["worse_than_nc_on_ttc"] == 5


def test_an_opponent_slower_than_p333_on_evaluation_does_not_count():
    win = good(ttc_net=spread(700.0, 5.0))
    pols = {f"d{i}": win for i in range(5)}
    T = table("X1", p333=good(ttc_net=spread(1000.0, 5.0)), nc=good(), r=good(ttc_net=spread(600.0, 5.0), all_delay=1100.0), **pols)
    res = dc.read_cell(T, "X1", opp({"on4a": "r"}))
    assert res["excluded"] == ["r"] and res["only_p333"] and res["tuned_won"]


def test_four_of_five_decides():
    win, lose = good(ttc_net=spread(700.0, 5.0)), good(ttc_net=spread(990.0, 5.0))
    O = good(ttc_net=spread(1000.0, 5.0))
    T3 = table("X1", p333=O, nc=good(), r=O, d0=win, d1=win, d2=win, d3=lose, d4=lose)
    T4 = table("X1", p333=O, nc=good(), r=O, d0=win, d1=win, d2=win, d3=win, d4=lose)
    assert not dc.read_cell(T3, "X1", opp({"on4a": "r"}))["tuned_won"] and dc.read_cell(T4, "X1", opp({"on4a": "r"}))["tuned_won"]


def test_selection_and_early_kill():
    p = good(ttc_net=spread(1000.0, 5.0))
    fam = {"uniform": {"p333": {}}, "on4a": {"a": {}, "b": {}}}
    T = {}
    for c in cm.PRIMARY:
        T |= table(c, p333=p, nc=good(all_delay=spread(2000.0, 5.0)), a=good(ttc_net=spread(800.0, 5.0), all_delay=1010.0), b=good(ttc_net=spread(500.0, 5.0), all_delay=1100.0))
    o = so.choose(T, fam)
    assert o["cells"]["X1"]["forms"]["on4a"] == "a", "b is too slow to be admissible"
    assert o["cells"]["X1"]["front_row"] == "b" and o["single_rule"] == "a"
    assert so.early_kill(T, fam)
    for c in cm.PRIMARY:
        T[(f"{c}|nc", cm.Q)] = good(all_delay=spread(1000.0, 5.0))
    assert not so.early_kill(T, fam)


def test_training_config_is_pinned():
    T = {("S|nc", q): arm(brake3=300.0, E30=30.0, N=450000.0, steps=1500) for q in cm.LEVELS}
    env = me.make(T)
    me.check(env)
    assert env["plant"]["ref"]["5300.0"] == [0.2, 0.02, 300.0]
    env["plant"].pop("ease_max")
    with pytest.raises(AssertionError):
        me.check(env)


def test_rule_members():
    f = cm.families()
    assert f["uniform"]["u0"] == {"cav_rule": [0, 0, 0]} and f["uniform"]["p333"] == {"cav_rule": [3, 3, 3]}
    assert all(set(k["pattern"]) == {1, 3} for k in f["zone"].values())
    assert f["on4a"] == {"r4a0": {"road_levels": {"4a": 0}}, "r4a1": {"road_levels": {"4a": 1}}, "r4a2": {"road_levels": {"4a": 2}}}
    assert {k["local_rule"]["level"] for k in f["local"].values()} == {1, 2} and {k["local_rule"]["r"] for k in f["local"].values()} == {400, 1000} and {k["local_rule"]["th"] for k in f["local"].values()} == {10, 13, 16}
    assert all(k["adaptive_4a"]["level"] == k["adaptive_4a"]["road_level"] for k in f["adapt4a"].values())
    own = [k["own_state"] for k in f["own"].values()]
    assert {x["level"] for x in own} == {1, 0} and {x["th"] for x in own} == {10, 15} and {x["crowd"] for x in own} == {0, 10}


def test_conditions_and_seeds_are_as_approved():
    assert cm.COND["X1"] == {"kind": "slowdown", "edge": "4", "limit_kmh": 25, "dur": 120.0, "times": [600.0, 1200.0], "taper": 20.0}
    assert cm.COND["X2"] == {"kind": "slowdown", "edge": "3", "limit_kmh": 30, "dur": 180.0, "times": [700.0], "taper": 20.0}
    assert cm.COND["H1"] == {"kind": "truck", "cap_kmh": 50, "period": 300.0, "first": 360.0} and cm.COND["H2"] == {"kind": "burst", "cycle": 120.0} and cm.COND["S"] is None
    assert (cm.SEEDS_CHECK[0], cm.SEEDS_CHECK[-1]) == (7_440_065, 7_440_074)
    assert (cm.SEEDS_TUNE[0], cm.SEEDS_TUNE[-1]) == (7_440_160, 7_440_179)
    assert (cm.SEEDS_TRACE[0], cm.SEEDS_TRACE[-1]) == (7_440_180, 7_440_189)
    assert (cm.SEEDS_EVAL[0], cm.SEEDS_EVAL[-1]) == (7_440_200, 7_440_219)
    assert cm.PLANT == {"smooth": True, "ease": True, "lcAssertive": 1.4, "smooth_s": 8.0, "ease_max": 4.4, "tau_rise": 0.2, "taper_fast": True, "fix_x": True, "geom": "r2m3"}
    assert cm.cfg({}, "S").get("ctrl") is None and cm.cfg({"cav_rule": [3, 3, 3]}, "X1")["ctrl"]["env"]["hold"] == 10.0


def test_bootstrap_level_and_denominator_guard():
    d = [float(i) for i in range(20)]
    A, B = arm(x=d), arm(x=0.0)
    assert cm.raw(A, B, "x")[0] < 0 and cm.raw(A, B, "x")[0] == pytest.approx(-9.5 / 1e-9 * 100)
    narrow, wide = cm.raw(arm(x=[100.0 + v for v in d]), arm(x=100.0), "x", pct=(2.5, 97.5)), cm.raw(arm(x=[100.0 + v for v in d]), arm(x=100.0), "x")
    assert wide[1] < narrow[1] and wide[2] > narrow[2]
    assert cm.effect(arm(x=102.04), arm(x=100.0), "x") == (-2.0, -2.0, -2.0) and cm.raw(arm(x=102.04), arm(x=100.0), "x")[0] < -2.0


def base_opp():
    return good(ttc_net=spread(1000.0, 5.0))


@pytest.mark.parametrize("kw, ok", [(dict(all_delay=1020.0), True), (dict(all_delay=1020.5), False), (dict(passed=1990.0), True), (dict(passed=1989.0), False), (dict(b3_step=1050.0), True), (dict(b3_step=1051.0), False),
                                    (dict(alks_full_moving=15.0), True), (dict(alks_full_moving=15.5), False), (dict(collisions=[1.0] + [0.0] * 19), True), (dict(collisions=[1.0, 1.0] + [0.0] * 18), False)])
def test_each_limit_at_its_edge(kw, ok):
    assert dc.clears(good(ttc_net=spread(800.0, 5.0), **kw), base_opp(), 10.0) is ok


def test_events_limit_is_either_or():
    O = good(alks_full_moving=200.0, ttc_net=spread(1000.0, 5.0))
    assert dc.clears(good(ttc_net=spread(800.0, 5.0), alks_full_moving=209.0), O, 10.0), "over 5 per run, within 5 %"
    O = good(alks_full_moving=2.0, ttc_net=spread(1000.0, 5.0))
    assert dc.clears(good(ttc_net=spread(800.0, 5.0), alks_full_moving=6.0), O, 10.0), "over 5 %, within 5 per run"


def test_margin_edge_and_ci_are_both_required():
    assert dc.clears(good(ttc_net=spread(900.0, 0.0)), good(ttc_net=spread(1000.0, 0.0)), 10.0)
    assert not dc.clears(good(ttc_net=spread(900.5, 0.0)), good(ttc_net=spread(1000.0, 0.0)), 10.0)
    noisy = [800.0] * 11 + [1400.0] * 9     # median 20 % better, but the CI reaches past 0
    assert cm.raw(good(ttc_net=noisy), good(ttc_net=1000.0), "ttc_net")[1] <= 0 and not dc.clears(good(ttc_net=noisy), good(ttc_net=1000.0), 10.0)


def test_anchors_bind_against_p333_only_where_it_does_not_count():
    assert dc.anchored(good(all_delay=1050.0, passed=1980.0), good())
    assert not dc.anchored(good(all_delay=1051.0), good()) and not dc.anchored(good(passed=1979.0), good())


def test_delay_win_reads_the_right_way_and_needs_its_limits():
    O = good(all_delay=spread(1000.0, 2.0))
    win = dict(all_delay=spread(950.0, 2.0))
    assert dc.delay_clears(good(**win), O) and not dc.delay_clears(good(all_delay=spread(960.0, 2.0)), O) and not dc.delay_clears(good(all_delay=spread(1050.0, 2.0)), O)
    assert not dc.delay_clears(good(**win, passed=1989.0), O) and not dc.delay_clears(good(**win, ttc_net=1101.0), O) and not dc.delay_clears(good(**win, b3_step=1101.0), O)
    assert not dc.delay_clears(good(**win, collisions=[1.0, 1.0] + [0.0] * 18), O)
    noisy = [900.0] * 11 + [1200.0] * 9
    assert not dc.delay_clears(good(all_delay=noisy), good(all_delay=1000.0))


def cell_table(pol, p333=None, **more):
    p = p333 or base_opp()
    return table("X1", p333=p, nc=more.pop("nc", good(ttc_net=spread(500.0, 5.0), all_delay=1500.0)), **{f"d{i}": pol[i] for i in range(5)}, **more)


def test_delay_win_goes_against_the_lower_delay_of_the_two():
    win = good(all_delay=spread(900.0, 2.0))
    T = cell_table([win] * 5, p333=good(all_delay=spread(1000.0, 2.0)), r=good(all_delay=spread(880.0, 2.0)))
    res = dc.read_cell(T, "X1", {"cells": {"X1": {"forms": {"on4a": "r"}, "delay_opponent": "r", "front_row": "r"}}, "single_rule": "r"})
    assert res["delay_opponent"] == "r" and not res["delay_won"]
    T = cell_table([win] * 5, p333=good(all_delay=spread(1000.0, 2.0)), r=good(all_delay=spread(1100.0, 2.0)))
    res = dc.read_cell(T, "X1", {"cells": {"X1": {"forms": {"on4a": "r"}, "delay_opponent": "r", "front_row": "r"}}, "single_rule": "r"})
    assert res["delay_opponent"] == "p333" and res["delay_won"]


def test_replication_margin_and_the_safety_word_goes_with_the_winners():
    O = base_opp()
    at25 = good(ttc_net=spread(750.0, 5.0))
    at35 = good(ttc_net=spread(650.0, 5.0))
    assert not dc.read_cell(cell_table([at25] * 5, r=O), "X1", opp({"on4a": "r"}))["replication_met"]
    assert dc.read_cell(cell_table([at35] * 5, r=O), "X1", opp({"on4a": "r"}))["replication_met"]
    sev = good(ttc_net=spread(700.0, 5.0), sev3=60.0)
    win = good(ttc_net=spread(700.0, 5.0))
    res = dc.read_cell(cell_table([win, win, win, sev, good(ttc_net=spread(990.0, 5.0))], r=O), "X1", opp({"on4a": "r"}))
    assert res["tuned_won"] and not res["severe_ok"], "only 3 policies win and are no worse on severity"
    assert dc.read_cell(cell_table([win] * 5, r=O), "X1", opp({"on4a": "r"}))["severe_ok"]


def test_single_and_copy_rows_are_read_not_assumed():
    win, O = good(ttc_net=spread(700.0, 5.0)), base_opp()
    T = cell_table([win] * 5, r=O, s=good(ttc_net=spread(690.0, 5.0)), copy=good(ttc_net=spread(690.0, 5.0), all_delay=1100.0))
    res = dc.read_cell(T, "X1", opp({"on4a": "r"}, single="s"))
    assert res["single_cleared"] == 0 and not res["single_won"]
    assert res["copy_cleared"] == 0 and res["copy_counts"] is False and "copy" not in res["counts"]
    res = dc.read_cell(cell_table([win] * 5, r=O), "X1", opp({"on4a": "r"}))
    assert res["single_won"] and res["copy_cleared"] is None


def test_no_control_sentence_uses_the_primary_level():
    pol = good(ttc_net=spread(1040.0, 40.0))
    T = cell_table([pol] * 5, r=base_opp(), nc=good(ttc_net=spread(1000.0, 40.0)))
    a = dc.read_cell(T, "X1", opp({"on4a": "r"}))["worse_than_nc_on_ttc"]
    e97, e95 = cm.raw(pol, T[("X1|nc", cm.Q)], "ttc_net"), cm.raw(pol, T[("X1|nc", cm.Q)], "ttc_net", pct=(2.5, 97.5))
    assert a == (5 if e97[2] < 0 else 0) and e97[2] >= e95[2]


def test_harm_fires_on_delay_or_ttc_and_lists_each_reference_once():
    fine, slow, risky = good(), good(all_delay=spread(1100.0, 2.0)), good(ttc_net=1200.0)
    def full(p, n=3):
        T = {}
        for c in cm.COND:
            for q in (4600.0, cm.Q):
                T[(f"{c}|p333", q)] = T[(f"{c}|r", q)] = good()
                for i in range(5):
                    T[(f"{c}|d{i}", q)] = p
        return T
    assert dc.harm(full(fine), {"single_rule": "p333"}) == []
    h = dc.harm(full(slow), {"single_rule": "p333"})
    assert len(h) == 8 and {x[2] for x in h} == {"p333"} and (("X1", cm.Q, "p333", 5) not in h)
    assert len(dc.harm(full(risky), {"single_rule": "r"})) == 16


def test_blind_spot_report():
    ok = good(brake_net=1000.0, b3_step=1040.0, ttc_half=1000.0)
    assert dc.blind_spots({("a", cm.Q): ok}) == []
    assert dc.blind_spots({("a", cm.Q): good(brake_net=900.0, b3_step=1000.0, ttc_half=1000.0)})
    assert dc.blind_spots({("a", cm.Q): good(brake_net=1000.0, b3_step=1000.0, ttc_net=800.0, ttc_half=1000.0)})
    assert dc.blind_spots({("a", cm.Q): good(brake_net=0.0, b3_step=0.0, ttc_half=1000.0)}) == [], "nothing to compare"


def test_row_checks_refuse_partial_arms_and_missing_metrics():
    cm.check_rows({("a", cm.Q): good(dist_step=1.0, ttc_half=1.0)}, 20)
    with pytest.raises(AssertionError):
        cm.check_rows({("a", cm.Q): arm(n=19, all_delay=1.0, ttc_net=1.0, passed=1.0, dist_step=1.0, ttc_half=1.0)}, 20)
    with pytest.raises(AssertionError):
        cm.check_rows({("a", cm.Q): arm(ttc_net=1.0, passed=1.0, dist_step=1.0, ttc_half=1.0)}, 20)


def selection_table(**rules):
    T = {}
    for c in cm.PRIMARY:
        T |= table(c, p333=base_opp(), nc=good(all_delay=spread(2000.0, 5.0)), **rules)
    return T


def test_selection_edges():
    fam = {"uniform": {"p333": {}}, "on4a": {"a": {}, "b": {}}}
    T = selection_table(a=good(ttc_net=spread(800.0, 5.0), all_delay=1020.0), b=good(ttc_net=spread(700.0, 5.0), all_delay=1021.0))
    assert so.choose(T, fam)["cells"]["X1"]["forms"]["on4a"] == "a", "2 % admits, 2.1 % does not"
    T = selection_table(a=good(ttc_net=spread(800.0, 5.0)), b=good(ttc_net=spread(700.0, 5.0), collisions=[1.0, 1.0] + [0.0] * 18))
    assert so.choose(T, fam)["cells"]["X1"]["forms"]["on4a"] == "a", "collisions at most p333's plus 1"
    T = selection_table(a=good(ttc_net=spread(1099.0, 5.0), all_delay=900.0), b=good(ttc_net=spread(1101.0, 5.0), all_delay=800.0))
    assert so.choose(T, fam)["cells"]["X1"]["delay_opponent"] == "a", "TTC at most 10 % worse, then lowest delay"
    T = selection_table(a=good(ttc_net=spread(800.0, 5.0), all_delay=1100.0), b=good(ttc_net=spread(600.0, 5.0), all_delay=1101.0))
    assert so.choose(T, fam)["cells"]["X1"]["front_row"] == "a", "delay at most 10 % worse, then lowest TTC"


def test_copy_rule_always_reaches_evaluation():
    fam = {"uniform": {"p333": {"cav_rule": [3, 3, 3]}}, "copy": {"copy": {"road_levels": {"4a": 1}}}}
    T = selection_table(copy=good(ttc_net=spread(1200.0, 5.0), all_delay=1200.0))
    o = so.choose(T, fam)
    assert "copy" not in o["cells"]["X1"]["forms"] and "copy" in o["ctrl"]


def test_early_kill_needs_the_margin_and_the_ci():
    fam = {"on4a": {"a": {}}}
    noisy = [800.0] * 11 + [1500.0] * 9
    assert so.early_kill({(f"{c}|{x}", cm.Q): (good(all_delay=noisy) if x == "a" else good()) for c in cm.PRIMARY for x in ("a", "nc")}, fam) == []
    assert so.early_kill({(f"{c}|{x}", cm.Q): (good(all_delay=899.0) if x == "a" else good()) for c in cm.PRIMARY for x in ("a", "nc")}, fam) != []
    assert so.early_kill({(f"{c}|{x}", cm.Q): (good(all_delay=901.0) if x == "a" else good()) for c in cm.PRIMARY for x in ("a", "nc")}, fam) == []


def test_make_env_refuses_partial_references():
    T = {("S|nc", q): arm(n=10, brake3=300.0, E30=30.0, N=450000.0, steps=1500) for q in cm.LEVELS}
    with pytest.raises(AssertionError):
        me.make(T)
    me.check(me.make(T, 10))


def test_collapse_statistic_and_saved_settings():
    rows = [{"r": -0.3 if u < 50 else -0.2} for u in range(500)]
    a, b = cl.stat(rows)
    assert a == pytest.approx(0.0) and b == pytest.approx(0.1)
    env = {"hold": 10.0}
    good_cfg = {"learner": 2, "updates": 500, "n_envs": 3, "gamma": 0.933, "lam": 0.967, "levels": list(cm.LEVELS), "seed": 20261207, "workers": [15, 16, 17], "env": {**cl.ct.ENV, **env}}
    assert cl.settings_differ(good_cfg, 2, env) == []
    assert cl.settings_differ({**good_cfg, "seed": 20261105}, 2, env) == ["seed"] and cl.settings_differ({**good_cfg, "env": {}}, 2, env) == ["env"]


def test_collapse_fails_on_a_collapse():
    fine = [{"r": -0.3 if u < 50 else -0.2} for u in range(500)]
    falling = [{"r": -0.2 if u < 400 else -0.4} for u in range(500)]
    worse = [{"r": -0.2 if u < 50 else -0.3} for u in range(500)]
    assert not cl.collapsed(fine) and cl.collapsed(falling) and cl.collapsed(worse)


def test_an_opponent_a_little_slower_than_the_limit_does_not_count():
    win = good(ttc_net=spread(700.0, 5.0))
    T = cell_table([win] * 5, r=good(ttc_net=spread(600.0, 5.0), all_delay=1030.0))
    assert dc.read_cell(T, "X1", opp({"on4a": "r"}))["excluded"] == ["r"]
    T = cell_table([win] * 5, r=good(ttc_net=spread(600.0, 5.0), all_delay=1020.0))
    assert dc.read_cell(T, "X1", opp({"on4a": "r"}))["counts"] == ["p333", "r"]


def test_no_control_sentence_is_at_97_5_not_95():
    import numpy as np
    for k in range(400):
        d = list(np.random.default_rng(k).normal(30.0, 50.0, 20))
        pol, nc = good(ttc_net=[1000.0 + x for x in d]), good(ttc_net=1000.0)
        if cm.raw(pol, nc, "ttc_net")[2] >= 0 > cm.raw(pol, nc, "ttc_net", pct=(2.5, 97.5))[2]:
            break
    else:
        raise AssertionError("no case separates the two levels")
    T = cell_table([pol] * 5, r=base_opp(), nc=nc)
    assert dc.read_cell(T, "X1", opp({"on4a": "r"}))["worse_than_nc_on_ttc"] == 0


def test_each_form_sends_its_lowest_ttc_rule():
    fam = {"uniform": {"p333": {}}, "on4a": {"a": {}, "b": {}}}
    T = selection_table(a=good(ttc_net=spread(800.0, 5.0)), b=good(ttc_net=spread(900.0, 5.0)))
    assert so.choose(T, fam)["cells"]["X1"]["forms"]["on4a"] == "a"
