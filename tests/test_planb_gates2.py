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
    return {"seed": g2.SEEDS[seed], "all_delay": delay * (1 + e), "ttc_net": 1000.0, "passed": 3000.0, "collisions": coll, "contact_steps": coll,
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
    assert c["drain_cap"] == 1.5 * 2.0 and c["passes_registered"] is True
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
    for r in T["SURGE|p333"]:
        r["collisions"] = r["contact_steps"] = 2.0
    assert drops(T)
    assert drops(world(), trace={"S": True, "SURGE": False, "TRUCK": True})     # G4(iv): a failed trace drops the cell
    assert drops(world(), trace={"S": False, "SURGE": True, "TRUCK": True})


def raise_queue(T, name, queue, extra):
    """Add `extra` vehicles to one queue over 1,500-1,800 s on every seed of an arm (or on the seeds listed)."""
    for r in T[name]:
        add = extra(r["seed"]) if callable(extra) else extra
        if queue == "backlog":
            r["m_main_pending_min"] = r["m_main_pending_min"][:20] + [x + 60.0 * add for x in r["m_main_pending_min"][20:]]
        else:
            r["m_minute"][queue] = r["m_minute"][queue][:20] + [x + 60.0 * add for x in r["m_minute"][queue][20:]]


@pytest.mark.parametrize("arm", ("nc", "p333"))
@pytest.mark.parametrize("queue", ("ramp1_queue", "ramp2_queue", "backlog"))
def test_each_of_the_six_queues_can_flip_the_cell(arm, queue):
    T = world()
    raise_queue(T, f"TRUCK|{arm}", queue, 3.0)
    c = read(T)["cells"]["TRUCK"]
    assert not c["G4_pass"] and not c["passes"] and not c["G4"]["drain"]["verdict"]["pass"] and c["status"] == "drops"
    assert c["G4"]["drain"]["verdict"]["excess"][f"{arm}|{queue}"] == pytest.approx(3.0, abs=1e-6)
    T = world()
    raise_queue(T, f"TRUCK|{arm}", queue, 1.9)
    assert read(T)["cells"]["TRUCK"]["G4_pass"]


def test_stuck_flips_the_cell_when_the_drain_passes():
    T = world()
    T["TRUCK|p333"][3]["m_stuck_n"] = 1
    c = read(T)["cells"]["TRUCK"]
    assert c["G4"]["drain"]["verdict"]["pass"] and not c["G4_pass"] and not c["G4_pass_registered"]


def test_both_verdicts_are_kept():
    T = world()
    raise_queue(T, "TRUCK|p333", "ramp2_queue", 0.5)     # a registered failure (+50 %), inside the new limit
    c = read(T)["cells"]["TRUCK"]
    assert c["G4"]["p333"]["ramp_queue_pass"] is False and not c["G4_pass_registered"] and not c["passes_registered"]
    assert c["G4_pass"] and c["passes"] and c["G4"]["drain"]["report"]["p333|ramp2_queue"]["old_pass"] is False
    T = world()
    tail = {g2.SEEDS[s] for s in range(4)}     # 4 of 40 seeds at +30: flat medians, registered pass, new failure
    raise_queue(T, "TRUCK|nc", "ramp2_queue", lambda s: 30.0 if s in tail else 0.0)
    c = read(T)["cells"]["TRUCK"]
    assert c["G4_pass_registered"] and not c["G4_pass"] and not c["passes"]


def test_surge_form_is_the_same_as_any_cell():
    T = world()
    for r in T["SURGE|nc"]:
        r["m_main_pending_min"] = [31.0] * 25     # above S: failed "at most S's", passes the new form
    c = read(T)["cells"]["SURGE"]
    assert c["G4"]["nc"]["backlog_pass"] is False and not c["G4_pass_registered"] and c["G4_pass"]
    assert c["G4"]["drain"]["report"]["nc|backlog"]["old_pass"] is False
    t = read(T)["cells"]["TRUCK"]
    assert t["G4"]["drain"]["report"]["nc|backlog"]["old_pass"] is True


def test_the_window_is_minutes_20_to_24():
    T = world()
    for r in T["TRUCK|nc"]:
        r["m_main_pending_min"] = [999.0] * 20 + [30.0] * 5     # outside the window: no effect
    assert read(T)["cells"]["TRUCK"]["G4_pass"]


def test_drain_cap_is_the_largest_no_control_backlog():
    T = world()
    for i, r in enumerate(T["SURGE|nc"]):
        r["m_pending_end"] = float(i % 10)
    assert read(T)["cells"]["SURGE"]["drain_cap"] == 1.5 * 9.0


def write_s2(out, T, code="c" * 40, trace_code=None):
    import json
    out.mkdir(parents=True, exist_ok=True)
    with (out / "s2_runs.jsonl").open("w") as w:
        for n, rs in T.items():
            for r in rs:
                w.write(json.dumps({"name": n, "q": 5300.0, **r}) + "\n")
    meta = {"inputs": {}, "jobs_sha256": "x", "code": {"commit": code, "clean": True, "detached": True, "diff_sha256": "d"}}
    (out / "meta.json").write_text(json.dumps(meta))
    (out / "trace").mkdir(exist_ok=True)
    (out / "trace" / "meta.json").write_text(json.dumps({**meta, "code": {**meta["code"], "commit": trace_code or code}}))
    (out / "s2_trace.json").write_text(json.dumps({"runs": {}, "pass": TRACE}))


CODE = {"commit": "c" * 40, "clean": True, "detached": True, "diff_sha256": "d"}


def test_main_read_writes_s2_json_and_exit_codes(tmp_path, monkeypatch):
    import json
    monkeypatch.setattr(g2.pb, "code_state", lambda: CODE)
    write_s2(tmp_path / "ok", world())
    assert g2.main(["read", "--out", str(tmp_path / "ok"), "--cells", "SURGE,TRUCK"]) == 0
    s2 = json.loads((tmp_path / "ok" / "s2.json").read_text())
    assert s2["kill"] is False and s2["cells"]["SURGE"]["passes"] is True and s2["code"]["commit"] == "c" * 40
    write_s2(tmp_path / "null", world(placebo_delay=1.2))
    assert g2.main(["read", "--out", str(tmp_path / "null"), "--cells", "SURGE,TRUCK"]) == 3
    assert json.loads((tmp_path / "null" / "s2.json").read_text())["kill"] is None
    write_s2(tmp_path / "mixed", world(), trace_code="e" * 40)
    with pytest.raises(SystemExit):     # traces from another commit than the rows
        g2.main(["read", "--out", str(tmp_path / "mixed"), "--cells", "SURGE,TRUCK"])
    T = world()
    T["SURGE|nc"] = T["SURGE|nc"][:-1]
    write_s2(tmp_path / "gap", T)
    with pytest.raises(SystemExit):
        g2.main(["read", "--out", str(tmp_path / "gap"), "--cells", "SURGE,TRUCK"])


def test_the_re_read_happens_once_from_a_clean_detached_tree(tmp_path, monkeypatch):
    import json
    write_s2(tmp_path / "x", world())
    args = ["read", "--out", str(tmp_path / "x"), "--cells", "SURGE,TRUCK", "--result", "s2_v486.json"]
    clean = {"commit": "a" * 40, "clean": True, "detached": True, "diff_sha256": "d"}
    for bad in ({"detached": False}, {"clean": False}):
        monkeypatch.setattr(g2.pb, "code_state", lambda: {**clean, **bad})
        with pytest.raises(SystemExit):
            g2.main(args)
        assert not (tmp_path / "x" / "s2_v486.json").exists()
    monkeypatch.setattr(g2.pb, "code_state", lambda: clean)
    assert g2.main(args) == 0
    res = json.loads((tmp_path / "x" / "s2_v486.json").read_text())
    assert res["read_code"]["commit"] == "a" * 40 and res["code"]["commit"] == "c" * 40 and "passes_registered" in res["cells"]["TRUCK"]
    with pytest.raises(SystemExit):
        g2.main(args)     # never twice


def test_the_registered_name_needs_the_rows_own_code_and_other_names_are_refused(tmp_path, monkeypatch):
    write_s2(tmp_path / "x", world())
    args = ["read", "--out", str(tmp_path / "x"), "--cells", "SURGE,TRUCK"]
    monkeypatch.setattr(g2.pb, "code_state", lambda: {**CODE, "commit": "a" * 40})
    with pytest.raises(SystemExit):
        g2.main(args)
    assert not (tmp_path / "x" / "s2.json").exists()
    with pytest.raises(SystemExit):
        g2.main(args + ["--result", "s2_other.json"])


def test_each_arm_is_read_against_its_own_steady_rows():
    T = world()
    raise_queue(T, "S|p333", "ramp2_queue", 3.0)
    raise_queue(T, "TRUCK|p333", "ramp2_queue", 3.0)     # equal to its own S, 3 above S|nc and the placebo
    c = read(T)["cells"]["TRUCK"]
    assert c["G4_pass"] and all(abs(v) < 1e-6 for v in c["G4"]["drain"]["verdict"]["excess"].values()) and c["G4_pass_registered"]


def test_g2_pending_follows_the_new_form():
    T = world(rule_gain=0.95)
    raise_queue(T, "TRUCK|p333", "ramp2_queue", 0.5)     # registered failure, inside the new limit: waits for the fallback
    c = read(T)["cells"]["TRUCK"]
    assert c["passes"] is None and c["status"].startswith("G2 pending") and c["passes_registered"] is False
    T = world(rule_gain=0.95)
    tail = {g2.SEEDS[s] for s in range(4)}
    raise_queue(T, "TRUCK|nc", "ramp2_queue", lambda s: 30.0 if s in tail else 0.0)     # the new form fails: it drops at once
    c = read(T)["cells"]["TRUCK"]
    assert c["passes"] is False and c["status"] == "drops" and c["passes_registered"] is None


def test_registered_verdict_follows_the_same_branches():
    assert read(world(cell_delay=1.05))["cells"]["TRUCK"]["passes_registered"] is False     # G1 fails
    assert read(world(rule_gain=0.95))["cells"]["TRUCK"]["passes_registered"] is None     # G2 pending
    assert read(world(placebo_delay=1.2))["cells"]["TRUCK"]["passes_registered"] is None     # null broken


@pytest.mark.parametrize("kw,drops", [({"contact_steps": 5.0, "collisions": 0.0}, True), ({"contact_steps": 0.0, "collisions": 5.0}, True),
                                      ({"contact_steps": 1.0, "collisions": 1.0}, False)])
def test_g4_iii_each_count_at_s_plus_one(kw, drops):
    T = world()
    for r in T["TRUCK|p333"]:
        r.update(kw)
    assert (not read(T)["cells"]["TRUCK"]["G4_pass"]) is drops


def test_g4_iii_reads_medians_against_p333s_own_steady_rows():
    T = world()
    T["TRUCK|p333"][0]["collisions"] = 50.0     # one seed: the median does not move
    assert read(T)["cells"]["TRUCK"]["G4_pass"]
    T = world()
    for r in T["S|nc"]:
        r["collisions"] = 5.0
    for r in T["TRUCK|p333"]:
        r["collisions"] = 2.0     # above S|p333 + 1, below S|nc
    assert not read(T)["cells"]["TRUCK"]["G4_pass"]


@pytest.mark.parametrize("arm,factor,ok", [("nc", 1.2, False), ("p333", 0.7, False), ("p333", 1.15, False), ("p333", 1.1, True)])
def test_g4_i_within_five_percent_for_both_arms(arm, factor, ok):
    T = world()
    scale(T, f"TRUCK|{arm}", "brake3", factor)     # ratios 1.08, 0.88, 1.06 and 1.04
    assert read(T)["cells"]["TRUCK"]["G4_pass"] is ok


@pytest.mark.parametrize("key", ("brake3", "b3_step"))
def test_g4_i_reads_medians(key):
    T = world()
    T["TRUCK|p333"][0][key] += 400.0
    assert read(T)["cells"]["TRUCK"]["G4_pass"]


@pytest.mark.parametrize("seed", (0, 25, 39))
@pytest.mark.parametrize("arm", ("nc", "p333"))
def test_stuck_on_any_gate_row_drops_the_cell(arm, seed):
    T = world()
    T[f"TRUCK|{arm}"][seed]["m_stuck_n"] = 1
    assert not read(T)["cells"]["TRUCK"]["G4_pass"]


def test_steady_stuck_rows_are_reported_beside():
    T = world()
    T["S|p333"][5]["m_stuck_n"] = 2
    c = read(T)["cells"]["TRUCK"]
    assert c["G4"]["p333"]["stuck_rows_S"] == 1 and c["G4"]["nc"]["stuck_rows_S"] == 0 and c["G4_pass"]


def bump_backlog(T, name, vehicles):
    for r in T[name]:
        r["m_main_pending_min"] = r["m_main_pending_min"][:20] + [x + 60.0 * vehicles for x in r["m_main_pending_min"][20:]]


def test_registered_verdicts_on_their_own_terms():
    def reg(name, queue, extra, arm="nc"):
        T = world()
        raise_queue(T, name, queue, extra)
        return read(T)["cells"]["TRUCK"]["G4_pass_registered"]
    assert not reg("TRUCK|nc", "ramp2_queue", 0.5)
    assert not reg("TRUCK|nc", "ramp2_queue", 0.15)     # +15 %
    assert reg("TRUCK|nc", "ramp2_queue", 0.05)     # +5 %
    assert not reg("TRUCK|p333", "backlog", 1.0)
    assert not reg("TRUCK|nc", "backlog", 0.4)     # 2.5 -> 2.9 vehicles, +16 %


def test_only_surge_loses_the_ten_percent_in_the_report():
    T = world()
    for cell in ("TRUCK", "SURGE"):
        bump_backlog(T, f"{cell}|nc", 0.075)     # +3 % of 2.5 vehicles
    res = read(T)["cells"]
    t, s = res["TRUCK"]["G4"]["drain"]["report"]["nc|backlog"], res["SURGE"]["G4"]["drain"]["report"]["nc|backlog"]
    assert t["old_pass"] is True and t["old_limit"] == pytest.approx(2.75) and s["old_pass"] is False and s["old_limit"] == pytest.approx(2.5)
