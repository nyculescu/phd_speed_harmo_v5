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


def wrapped(name, cfg, seed, row):
    """A row as the runner writes it (run6.wrap adds cell, arm, learner, commit and the hashes): the review found that the planted
    test rows had no such fields, which hid a reader bug."""
    return v5.run6.wrap({"name": name, "seed": seed, **row}, (name, cfg, 5300.0, seed, "rd", "abc"))


def trace_rows(miscount=0, twin_extra=None, boundary=False):
    L = 294.72
    cars = [["a", L - 30.0 + 1e-4 if boundary else 290.0, 0.5], ["b", 200.0, 0.2], ["c", 291.0, 3.0]]
    tr = [[300.0 + i, "4a_0", L, cars] for i in range(5)] + [[300.0, "3a_0", L, [["d", 280.0, 0.0]]]]
    row = {"end_stop": 1.0, "end_stop2": 5.0 + miscount, "all_delay": 1.0}
    cfg = {"ctrl": {"cav_rule": [3, 3, 3]}}
    return {("S", "p333"): {7_488_010: wrapped("S|p333", {**cfg, "trace_end": True}, 7_488_010, {**row, "end_trace": tr})},
            ("S", "p333~untraced"): {7_488_010: wrapped("S|p333~untraced", cfg, 7_488_010, {**row, **(twin_extra or {})})}}


def test_trace_on_runner_rows_recount_twin_and_actions():
    r = rm.trace(trace_rows(), [7_488_010])
    assert r["action"] == "go" and r["runs"]["S|p333 7488010"]["cars_waiting"]["4a_0"] == 1
    assert rm.trace(trace_rows(boundary=True), [7_488_010])["action"] == "go"     # raw floats at the 30-m line
    assert rm.trace(trace_rows(miscount=1), [7_488_010])["action"] == "void"
    assert rm.trace(trace_rows(twin_extra={"all_delay": 1.5}), [7_488_010])["action"] == "stop"
    T = trace_rows()
    del T[("S", "p333~untraced")][7_488_010]
    assert rm.trace(T, [7_488_010])["action"] == "stop"


def test_ident_rule_difference_or_missing_stops_learner_difference_switches_to_fresh_seeds():
    names = [("S", "p333"), ("S", "w0u250")]
    old = {("S", "p333"): {1: {"all_delay": 5.0, "commit": "x"}}, ("S", "w0u250"): {1: {"all_delay": 4.0}}}
    same = {("S", "p333"): {1: {"all_delay": 5.0, "commit": "y"}}, ("S", "w0u250"): {1: {"all_delay": 4.0}}}
    assert rm.ident(same, old, names, [1])["action"] == "go"
    assert rm.ident({**same, ("S", "w0u250"): {1: {"all_delay": 4.1}}}, old, names, [1])["action"] == "fresh_seeds"
    assert rm.ident({**same, ("S", "p333"): {1: {"all_delay": 5.1}}}, old, names, [1])["action"] == "stop"
    assert rm.ident({("S", "w0u250"): same[("S", "w0u250")]}, old, names, [1])["action"] == "stop"


def test_drops_leave_every_arm_and_void_above_three(tmp_path):
    (tmp_path / "drops.json").write_text('{"SV2": [5], "S": [5, 7]}')
    assert rm.drops_of(tmp_path / "s6_rows.jsonl") == [5, 7]
    assert rm.usable(list(range(10)), [5, 7]) == ([0, 1, 2, 3, 4, 6, 8, 9], False)
    assert rm.usable(list(range(10)), [1, 2, 3, 4])[1] is True
    assert rm.drops_of(tmp_path / "x" / "s6_rows.jsonl") == []


@need
def test_smoke_jobs_hold_untraced_twins(tmp_path):
    m = v5.plan("m2_smoke", tmp_path)["arms"]
    pairs = v5.twin_pairs(m)
    assert ("S|nc", "S|nc~untraced") in pairs and ("S|p333~trace", "S|p333~untraced") in pairs and ("X1|p333", "X1|p333~untraced") in pairs
    assert "m2_counts" not in m["S|nc~untraced"] and m["S|p333~trace"]["trace_end"] is True
    e = v5.plan("ev_smoke", tmp_path)["arms"]
    assert ("EVA20|nc", "EVA20|nc~untraced") in v5.twin_pairs(e) and "t0_event" not in e["EVA20|nc~untraced"]
    assert v5.tracer_key("r2_lc_4") and v5.tracer_key("va_bad_on") and v5.tracer_key("end_trace") and not v5.tracer_key("all_delay")
