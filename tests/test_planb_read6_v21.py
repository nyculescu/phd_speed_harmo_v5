"""read6 v2.1 (read6_v2_spec.md amendment 3): fixes from the review of v2. Written before the fix; each test fails on f84c9dc,
except the coverage tests marked so, which pin behaviour f84c9dc already has."""
import json
import sys
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "docs/research/planb"))
import read6_regress  # noqa: E402
import test_planb_read6 as t1  # noqa: E402
from test_planb_read6 import LEARN, OPP, cfg, r6, world  # noqa: E402
from test_planb_read6_v2 import PICKS, with_report_keys  # noqa: E402


def universe_world():
    """dly is a re-pick that is only the delay opponent: at p333's delay but with far less close-following, so it blocks every
    learner's T2 bar. lr is a form 3 % slower than p333 and 3e is 4 % slower: neither counts. 3E-C_X and 3E-D_X equal p333."""
    T = with_report_keys(world(opp_delay={"lr": 0.03, "3e": 0.04}))
    for cond in ("X", "S"):
        src = T[(cond, "p333")]
        T[(cond, "dly")] = {s: dict(v, ttc_net=v["ttc_net"] * 0.7) for s, v in src.items()}
        for e in ("3E-C_X", "3E-D_X"):
            T[(cond, e)] = {s: dict(v) for s, v in src.items()}
    c = cfg() | {"opponents": {"X": OPP + ["dly", "3E-C_X", "3E-D_X"]}, "e3c": {"X": "3E-C_X"}, "e3d": {"X": "3E-D_X"},
                 "picks": PICKS | {"repicks": {"X": {"lr": {}, "p333": {}, "dly": {}}}}, "forms": {"X": ["p333", "lr"]}}
    return T, c


def test_universe_takes_the_forms_not_the_delay_opponent():
    T, c = universe_world()
    f = r6.read(T, c)["cells"]["X"]["t2_counting_filter"]
    assert "dly" not in f["universe"] and f["universe"] == ["p333", "lr", "3e", "3E-C_X", "3E-D_X"]
    assert f["counted"] == ["3E-C_X", "3E-D_X", "p333"] and f["policies"] == 5
    assert "dly" in f["v1_value"]["counted"] and f["v1_value"]["policies"] == 0


def test_excluded_3e_rules_are_listed():
    T, c = universe_world()
    ex = r6.read(T, c)["cells"]["X"]["t2_counting_filter"]["excluded_3e"]
    assert set(ex) == {"3e"}
    assert ex["3e"]["delay_vs_p333"] == pytest.approx(-4.0, abs=0.5) and abs(ex["3e"]["cf_vs_p333"]) < 2.0
    assert ex["3e"]["vs_os1_15_10"] == "not in the cell"


def test_forms_must_match_the_picks(tmp_path):
    rep = {"picks": {"X": {"forms": {"uniform": "p333", "local": "lr"}, "delay_opponent": "dly", "front_row": "lr"}}}
    assert r6.check_forms(rep, {"repicks": {"X": {"lr": {}, "p333": {}, "dly": {}}}}, ["X"]) == {"X": ["p333", "lr"]}
    with pytest.raises(SystemExit):
        r6.check_forms(rep, {"repicks": {"X": {"lr": {}, "p333": {}}}}, ["X"])


def test_unread_resilience_blocks_hold_no_verdict():
    c = r6.read(with_report_keys(world(delay=(0.0,) * 5, cf=(0.0,) * 5)), cfg())["cells"]["X"]
    assert c["outcome"] == "T"
    for k in ("resilience", "cf_resilience"):
        assert "passes" not in c[k] and "reading" not in c[k]
    loss = lambda name, s: 5000.0 if name in LEARN else 9000.0
    w = r6.read(with_report_keys(world(s_loss=loss)), cfg())["cells"]["X"]
    assert w["resilience"]["status"] == "read" and w["resilience"]["passes"]
    assert "passes" not in w["cf_resilience"] and "reading" not in w["cf_resilience"]


def test_cf_resilience_reads_close_following():
    """Coverage."""
    loss = lambda name, s: 5000.0 if name in LEARN else 9000.0
    T = with_report_keys(world(s_loss=loss))
    c = r6.read(T, cfg())["cells"]["X"]
    assert c["cf_resilience"]["nc_median_loss"] == pytest.approx(0.0, abs=1e-6)     # S copies ttc_net from the cell
    assert c["resilience"]["nc_median_loss"] == pytest.approx(9000.0)


def test_no_control_with_zero_median_on_a_v1_measure_has_no_effect():
    T = with_report_keys(world())
    for cond in ("X", "S"):
        for v in T[(cond, "nc")].values():
            v["b45_step"] = 0.0
        for v in T[(cond, "p333")].values():
            v["b45_step"] = 0.0
    c = r6.read(T, cfg())["cells"]["X"]
    assert c["map_report_only"]["nc"]["b45_step"]["effect"] is None
    assert c["map_report_only"]["p333"]["b45_step"]["effect"] == c["map"]["p333"]["b45_step"]["effect"]     # v1's floor kept


def test_absent_delay_ramp2_is_none_and_counted():
    row = t1.pack_row("X|w0", 0)
    del row["delay_ramp2"]
    d = r6.derive(row)
    assert d["delay_ramp2"] is None and d["absent_none"] == ["delay_ramp2"]
    del row["delay_ramp"]
    with pytest.raises((KeyError, SystemExit)):
        r6.derive(row)


def test_none_reasons_name_the_cause():
    T = with_report_keys(world())
    T[("X", "w0")][3]["ttc3_lc_share"] = None
    T[("X", "w1")][5]["delay_ramp2"] = None
    m = r6.read(T, cfg())["cells"]["X"]["map_report_only"]["p333"]
    assert m["ttc3_lc_share"]["why"] == "m_ttc3_all = 0 on some seeds" and m["delay_ramp2"]["why"] == "no ramp-2 finisher on some seeds"


def test_pct_of_nc_loss_hidden_when_its_null_fails(monkeypatch):
    """Coverage."""
    calls = []

    def later(*a, **k):
        calls.append(1)
        return 0.0 if len(calls) <= 2 else 0.5
    monkeypatch.setattr(r6, "swap_null", later)
    loss = lambda name, s: 5000.0 if name in LEARN else 9000.0
    c = r6.read(with_report_keys(world(s_loss=loss)), cfg())["cells"]["X"]
    assert all(v["pct_of_nc_loss"] is None for v in c["resilience"]["per_opponent"].values())


def test_braking_clause_by_point_and_lowest_upper_bound():
    """Coverage."""
    comps ={"a": {"brake_excess": (5.0, 1.0, 20.0)}, "b": {"brake_excess": (4.0, 3.0, 9.0)}, "c": {"brake_excess": (-1.0, -3.0, 2.0)}}
    b = r6.braking_clause(comps)
    assert b["largest_point_excess"]["opponent"] == "a" and b["lowest_upper_bound"]["opponent"] == "c"


def test_main_requires_picks_and_forms_on_a_full_run(tmp_path, monkeypatch):
    monkeypatch.setattr(r6, "load_rows", lambda *a: {})
    monkeypatch.setattr(r6, "read", lambda *a: {"study": "NULL", "cells": {}})
    conf = tmp_path / "c.json"
    conf.write_text(json.dumps(cfg()))
    with pytest.raises(SystemExit):
        r6.main(["rows", str(conf), str(tmp_path / "o.json")])


def v1_like():
    """A v1-shaped output and its v2 copy, with the keys the gate needs."""
    a = {"study": "NULL", "cells": {"X": {"outcome": "W", "harm": {"delay": []}, "learner_signs": {"w0": True}, "pr28": None,
                                          "t2_counting_filter": {"counted": ["p333"], "policies": 5},
                                          "resilience": {"per_opponent": {"p333": {"R": [1.0, 0.5, 2.0], "pct_of_nc_loss": 44.0,
                                                                                   "null_false_better": 0.01, "null_ok": 1.0}}},
                                          "map": {}, "x": float("nan"), "z": 0.0}},
         "S": {"map": {}}}
    b = json.loads(json.dumps(a))
    b["cells"]["X"] |= {"t2_counting_filter": {"universe": ["p333"], "counted": ["p333"], "policies": 5, "v1_value": {"counted": ["p333"], "policies": 5}},
                        "map_report_only": {}, "closest": {}, "pr28": {"share": 0.1}}
    b["S"]["map_report_only"] = {}
    return a, b


def test_gate_passes_a_clean_copy_and_reports_planted_changes():
    a, b = v1_like()
    assert read6_regress.diff(a, b) == []
    for edit in (lambda b: b["cells"]["X"].update(outcome="T"), lambda b: b["cells"]["X"]["harm"].update(extra=["delay"]),
                 lambda b: b["cells"]["X"]["learner_signs"].update(w9=False), lambda b: b["cells"]["X"].update(k_policies=5),
                 lambda b: b["cells"]["X"]["t2_counting_filter"]["v1_value"].update(policies=4), lambda b: b["cells"]["X"].update(z=-0.0),
                 lambda b: b.update(extra=1)):
        _, c = v1_like()
        edit(c)
        assert len(read6_regress.diff(a, c)) == 1


def test_gate_allows_a_hidden_r_after_the_json_round_trip():
    a, b = v1_like()
    a["cells"]["X"]["resilience"]["per_opponent"]["p333"]["null_ok"] = 0.0
    p = b["cells"]["X"]["resilience"]["per_opponent"]["p333"]
    p |= {"R": read6_regress.FAILED, "pct_of_nc_loss": None, "null_ok": np.False_}
    b = json.loads(json.dumps(b, default=float))     # as read6.main writes it: the numpy bool becomes 0.0
    assert p["null_ok"] is np.False_ and b["cells"]["X"]["resilience"]["per_opponent"]["p333"]["null_ok"] == 0.0
    assert read6_regress.diff(a, b) == []


def test_gate_pr28_skip_only_at_cell_level():
    a, b = v1_like()
    a["S"]["pr28"] = None
    b["S"]["pr28"] = {"share": 0.1}
    d = read6_regress.diff(a, b)
    assert len(d) == 1 and d[0].startswith("S.pr28")
