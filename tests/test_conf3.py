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
