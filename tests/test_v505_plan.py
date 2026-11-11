"""V505 job planning and checks (v505_common.md §5, M2 §2, §6, §7): stage seeds, job contents, the trace recount, the identity rule."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "docs/research/v505"))
import read_m2 as rm  # noqa: E402
import v5  # noqa: E402

need = pytest.mark.skipif(not v5.S6_JOBS.is_file() or not v5.pb.JOB.is_file(), reason="stored job files not on this machine")


def test_stage_ranges_do_not_overlap_and_match_the_protocol():
    r = sorted(v for k, v in v5.STAGES.items() if k != "m2_ident")     # identity replays reuse the first 3 verdict seeds (M2 §6)
    assert all(b < c for (_, b), (c, _) in zip(r, r[1:]))
    assert v5.STAGES["m2_verdict"] == (7_480_400, 7_480_639) and v5.STAGES["m2_fallback"] == (7_488_760, 7_488_999)
    assert len(v5.seeds("ev_eval")) == 120 and len(v5.seeds("m2_pick")) == 60 and len(v5.seeds("m2_x1")) == 160


def test_seeds_outside_a_stage_are_refused():
    with pytest.raises(SystemExit):
        v5.seeds("m2_pick", 7_488_019, 7_488_030)
    with pytest.raises(SystemExit):
        v5.seeds("ev_tune", 7_488_280, 7_488_400)


@need
def test_ident_job_is_s6_configs_unchanged(tmp_path):
    j = v5.plan("m2_ident", tmp_path)
    arms = v5.s6_arms()
    assert len(j["arms"]) == 22 and j["seed_range"] == [7_480_400, 7_480_402]
    for n, c in j["arms"].items():
        assert {k: v for k, v in c.items() if k != "measure"} == {k: v for k, v in arms[n].items() if k != "measure"}


@need
def test_pick_and_verdict_jobs_add_only_the_v505_keys(tmp_path):
    arms = v5.s6_arms()
    j = v5.plan("m2_pick", tmp_path)
    assert len(j["arms"]) == 10 and j["seed_range"] == [7_488_020, 7_488_079]
    assert j["arms"]["S|p333"]["m2_counts"] is True and j["arms"]["SV5|nc"]["ramp2_assertive"] == 5.0
    v = v5.plan("m2_verdict", tmp_path, 3.0)
    assert len(v["arms"]) == 22 and "TRUCKV3|w2u250" in v["arms"]
    c = v["arms"]["TRUCKV3|w2u250"]
    assert {k: x for k, x in c.items() if k not in ("measure", "ramp2_assertive")} == {k: x for k, x in arms["TRUCK|w2u250"].items() if k != "measure"}
    with pytest.raises(SystemExit):
        v5.plan("m2_verdict", tmp_path)


@need
def test_x1_job_has_both_plants_and_the_x1_slowdown(tmp_path):
    j = v5.plan("m2_x1", tmp_path, 3.0)
    assert len(j["arms"]) == 18
    for n, c in j["arms"].items():
        assert c["ctrl"]["env"]["perturb"]["kind"] == "slowdown" and c["ctrl"]["env"]["perturb"]["edge"] == "4"
        assert ("ramp2_assertive" in c) == ("X1V3|" in n) and ("m2_counts" in c) == n.startswith("X1|")


def trace_rows(miscount=0):
    cars = [["a", 290.0, 0.5], ["b", 200.0, 0.2], ["c", 291.0, 3.0]]
    tr = [[300.0 + i, "4a_0", 294.72, cars] for i in range(5)] + [[300.0, "3a_0", 294.72, [["d", 280.0, 0.0]]]]
    row = {"end_stop": 1.0, "end_stop2": 5.0 + miscount, "all_delay": 1.0}
    return {("S", "p333"): {7_488_010: {**row, "end_trace": tr}}, ("S", "p333~untraced"): {7_488_010: dict(row)}}


def test_trace_recount_matches_and_a_miscount_fails():
    r = rm.trace(trace_rows())
    assert r["pass"] and r["runs"]["S|p333 7488010"]["cars_waiting"]["4a_0"] == 1
    assert not rm.trace(trace_rows(miscount=1))["pass"]


def test_ident_rule_difference_stops_learner_difference_switches_to_fresh_seeds():
    old = {("S", "p333"): {1: {"all_delay": 5.0, "commit": "x"}}, ("S", "w0u250"): {1: {"all_delay": 4.0}}}
    same = {("S", "p333"): {1: {"all_delay": 5.0, "commit": "y"}}, ("S", "w0u250"): {1: {"all_delay": 4.0}}}
    assert rm.ident(same, old)["action"] == "go"
    assert rm.ident({**same, ("S", "w0u250"): {1: {"all_delay": 4.1}}}, old)["action"] == "fresh_seeds"
    assert rm.ident({**same, ("S", "p333"): {1: {"all_delay": 5.1}}}, old)["action"] == "stop"
