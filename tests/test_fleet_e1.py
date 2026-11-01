"""E1 runner and metrics (V213 §2, §7.1-7.2, §10.1): output layout, command lines, the all-vehicle delay metrics."""
import numpy as np
import pytest

from v5b.fleet import e1
from v5b.fleet.day import e1_metrics


def test_twins_and_arms_never_share_a_file():
    a = e1.job("s", "R", "nc", "base", 7430040)
    b = e1.job("s", "R", "nc", "base", 7430040, 7435040)
    c = e1.job("s", "I", "nc", "base", 7430040)
    d = e1.job("s", "R", "ma", "p0.95", 7430040)
    paths = {e1.out_path(j) for j in (a, b, c, d)}
    assert len(paths) == 4
    assert e1.out_path(b).parent.name == "ss7435040"


def test_command_lines():
    j = e1.job("s", "I", "c", "p0.95_long", 7430230, 7435230, {"alks": {"zone": "long"}}, "15,18")
    a = e1.argv(j)
    assert a[a.index("--plant") + 1] == "v199" and a[a.index("--adt") + 1] == "45000"
    assert a[a.index("--blocker") + 1] == e1.BLOCKER and a[a.index("--crash-k") + 1] == "0"
    assert a[a.index("--sumo-seed") + 1] == "7435230" and "--ctrl" in a and a[a.index("--hours") + 1] == "15,18"
    r = e1.argv(e1.job("s", "R", "nc", "base", 7430230))
    assert "--blocker" not in r and "--sumo-seed" not in r and "--ctrl" not in r
    assert r[2:4] == ["v5b.fleet.day", "one"]             # matches the CPU guard pattern


def test_order_puts_i_days_and_full_days_first():
    js = [e1.job("s", "R", "nc", "x", 1, hours="15,19"), e1.job("s", "R", "nc", "x", 2), e1.job("s", "I", "nc", "x", 3)]
    assert [j["seed"] for j in e1.order(js)] == [3, 2, 1]


def test_wave1_contents():
    js = e1.wave1(5.22)
    full = [j for j in js if j["hours"] is None and j["arm"] == "nc"]
    assert len(full) == 40 and sum(j["ss"] is not None for j in full) == 20
    assert {j["ss"] - j["seed"] for j in full if j["ss"]} == {e1.TWIN}
    assert len({e1.out_path(j) for j in js}) == len(js)


def test_e1_metrics():
    # delay, scheduled departure, arrival, ramp, class
    tr = np.array([[10.0, 1000.0, 1100.0, 0, 0], [30.0, 16 * 3600.0, 16 * 3600.0 + 400, 1, 4],
                   [700.0, 17 * 3600.0, 87000.0, 0, 1], [20.0, 19.5 * 3600.0, 19.5 * 3600.0 + 300, 1, 0]])
    m = e1_metrics(tr, {"t": 57600.0, "duration": 2700.0})
    assert m["d_all"] == pytest.approx(190.0) and m["d_main"] == pytest.approx(355.0) and m["d_ramp"] == pytest.approx(25.0)
    assert m["d_pm_depart"] == pytest.approx(250.0)
    assert m["d_recovery"] == pytest.approx(360.0)          # departures from 16:45 to 20:00
    assert m["share_over_600"] == pytest.approx(0.25)
    assert m["delay_after24_share"] == pytest.approx(700.0 / 760.0, abs=1e-5)
    assert m["served"]["pm"] == {"main": 0, "ramp": 2} and m["served"]["day"]["main"] == 1
    assert "d_recovery" not in e1_metrics(tr, None)


FZ = {"o_cr": {"alinea": 12.0, "drop": 16.0, "dropend": 18.0}, "drop_loop": "drop", "c_loop": "drop",
      "gains": {"k_r": 70.0, "pi": "wang", "k_i": 0.02}, "l_bar": 5.224}


def test_grid_and_stage_a():
    pts = e1.grid(FZ)
    assert len(pts) == 12
    assert pts["ma/p0.85"]["meter"]["setpoint"] == pytest.approx(10.2)
    assert pts["mp/p1.05"]["meter"]["loop"] == "drop" and pts["mp/p1.05"]["meter"]["setpoint"] == pytest.approx(16.8)
    assert pts["c/p0.95_long"]["alks"]["zone"] == "long"
    first, rest = e1.stage_a(FZ, 10, True), e1.stage_a(FZ, 10, False)
    assert len(first) == 13 * 3 * 2 and len(rest) == 13 * 7 * 2
    assert len({e1.out_path(j) for j in first + rest}) == 260
    mc = e1.mc_ctrl(pts, "mp/p0.95", "c/p0.85_short")
    assert mc["cascade"] and "meter" in mc and "alks" in mc
    assert not e1.mc_ctrl(pts, "ma/p0.95", "c/p0.85_short")["cascade"]
    assert e1.fresh_seeds(10)[0] == 7430240 and e1.fresh_seeds(20)[-1] == 7430259


def test_idle():
    assert e1.idle({"meter": {"metering_s": 100}, "alks": None})
    assert not e1.idle({"meter": {"metering_s": 400}, "alks": None})
    assert not e1.idle({"meter": None, "alks": {"log": [[0, 0.9, 0, 1]] * 5}})


def _fake_day(seed, d, intr=0, brake=2, t_stop=57620.0):
    return {"seed": seed, "d_all": d, "drained": True, "teleports": 0, "sumo_errors": 0, "contacts": 0,
            "arrived_plus_removed": 100, "generated": 100, "mingap_intrusions": intr, "emergency_braking_warnings": brake,
            "served": {"pm": {"main": 9000, "ramp": 1500}}, "ttt_w_h": 3000.0 + d, "blocker": {"t_stop": t_stop, "x_stop": 650.0},
            "breakdowns_drop": [{"t_break": 58000.0, "drop": 0.11, "qdf": 3050.0}],
            "series": [(43200.0 + 30.0 * i, 25, None, 0, 0, None, None, 27.0, None) for i in range(40)],
            "loops30": {"groups": [], "rows": []}, "collision_events": [], "meter": None, "alks": None, "ctrl": None}


def _fake_root(root, gains, intr_arm="ma"):
    import json as js
    seeds = e1.main_seeds(10)
    rng = np.random.default_rng(0)
    for cell in ("R", "I"):
        for k, g in gains.items():
            arm, pt = k.split("/")
            for s in seeds:
                p = e1.out_path(e1.job("A", cell, arm, pt, s), root)
                p.parent.mkdir(parents=True)
                p.write_text(js.dumps(_fake_day(s, 400.0 * (1 - g) + rng.normal(0, 2.0), intr=6 if arm == intr_arm else 0)))
                np.savez(p.parent / f"conflicts_s{s}.npz", t=np.array([1.0, 2.0], np.float32),
                         follower=np.array([0, 0], np.int32), leader=np.array([1, 1], np.int32),
                         ttc=np.array([1.0, 0.8], np.float32), v_f=np.zeros(2, np.float32), v_l=np.zeros(2, np.float32),
                         cls=np.array([0, 0], np.int8))


def test_report_stage_end_to_end(tmp_path):
    _fake_root(tmp_path, {"nc/base": 0.0, "ma/p0.85": 0.25, "ma/p0.95": 0.12, "ma/p1.05": 0.05, "c/p0.85_long": 0.02,
                          "c/p0.95_long": 0.01, "c/p1.05_long": 0.0})
    rep = e1.report_stage(10, tmp_path, ("A",))
    r = rep["cells"]["R"]
    assert r["tuned"]["M*"] == "ma/p0.85" and r["tuned_pass"]
    assert r["B1_edges"]["M"]["next"] is None                      # a tuned arm passed: no extension
    assert r["B1_edges"]["C"]["variant"] == "c_long"
    assert r["o_off"]["pass"] and r["o_off_nc_picks"] == 0
    assert not r["C1_needed"] and not r["flags"]["M*"]["braking"]
    no_rule2 = {"R": False, "I": False}
    assert e1.stage_c1(rep, 10, tmp_path) == [] and e1.stage_c2(rep, 10, no_rule2, tmp_path) == []
    assert len(e1.stage_c2(rep, 10, {"R": True, "I": False}, tmp_path)) == 20     # NC and M* twins; O_off picks M*
    assert rep["intrusion_flags"]["ma/p0.85"]["flag"] and not rep["intrusion_flags"]["c/p0.95_long"]["flag"]
    assert r["harm_in_other_cell"]["M*"] == "no harm"
    assert rep["stop"] == [] and not rep["oracle_fails_both"]
    v = e1.final_verdict(rep, 10, {"R": True, "I": True}, {"R": False, "I": False}, tmp_path)
    assert v["verdict"] == "FLAGGED-ONLY" and v["cells"]["R"]["F"] == ["M*"]       # the meter arm carries the V211 flag
    js, fzc = e1.stage_b1(rep, FZ, 10)
    assert js == [] and len(e1.stage_b2(rep, fzc, 10)) == 20


def test_edge_extension_jobs(tmp_path):
    _fake_root(tmp_path, {"nc/base": 0.0, "ma/p0.85": 0.06, "ma/p0.95": 0.03, "ma/p1.05": 0.01, "c/p0.85_long": 0.0,
                          "c/p0.95_long": 0.01, "c/p1.05_long": 0.0}, intr_arm=None)
    rep = e1.report_stage(10, tmp_path, ("A",))
    r = rep["cells"]["R"]
    assert not r["tuned_pass"] and r["B1_edges"]["M"]["next"] == 0.75
    js, fzc = e1.stage_b1(rep, FZ, 10)
    assert {(j["cell"], j["arm"], j["point"]) for j in js} == {("R", "ma", "p0.75"), ("I", "ma", "p0.75")}
    assert js[0]["ctrl"]["meter"]["setpoint"] == pytest.approx(0.75 * 12.0)
    assert len(js) == 20


def test_gain_choice_rules():
    st = lambda sw, rms, acts=True, lead=True: {"swings": sw, "rms": rms, "acts": acts, "lead": lead}
    s = {"kr35": [st(0, 2.0)] * 3, "kr70": [st(3, 1.0)] * 3, "kr140": [st(0, 2.1)] * 3}
    assert e1.choose_gain(s, "alinea")["choice"] == "kr35"            # the swinging nominal is out
    idle = {"kr35": [st(0, None, False)] * 3, "kr70": [st(3, None, False)] * 3}
    assert e1.choose_gain(idle, "alinea")["stop"]                      # nothing acts and the nominal swings
    t = [60.0 * i for i in range(120)]
    x = ([900.0] * 25 + [250.0] * 10 + [900.0] * 10 + [250.0] * 10 + [900.0] * 10 + [250.0] * 10 + [900.0] * 45)
    assert e1.max_swings_per_hour(t, x, [True] * 120, 850.0, 300.0) == 3   # 3 swings across a clock-hour edge


def test_wave1b_and_n_rule():
    js = e1.wave1b(5.22)
    assert all(j["stage"] == e1.W1B for j in js)
    assert not any(j["cell"] == "R" and j["arm"] == "nc" and j["point"] == "base" for j in js)
    assert sum(j["cell"] == "I" and j["point"] == "base" for j in js) == 20
    assert {j["arm"] for j in js} >= {"t0_meter", "t0_alks", "smoke_mc", "nc"}
    assert e1.pick_n([10, 15]) == 15 and e1.pick_n([10, None]) == 20 and e1.pick_n([None, None]) == 20


def _write(root, stage, cell, key, seed, d_all, ss=None, **kw):
    import json as js
    arm, pt = key.split("/")
    p = e1.out_path(e1.job(stage, cell, arm, pt, seed, ss), root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(js.dumps(_fake_day(seed, d_all) | kw))
    np.savez(p.parent / f"conflicts_s{seed}.npz", t=np.array([1.0], np.float32), follower=np.array([0], np.int32),
             leader=np.array([1], np.int32), ttc=np.array([1.0], np.float32), v_f=np.zeros(1, np.float32),
             v_l=np.zeros(1, np.float32), cls=np.array([0], np.int8))


def _grid_root(root, special: dict):
    """NC at 400 and every grid point at 401 in both cells, except the per-seed D lists in special."""
    keys = ["nc/base"] + [k for k in e1.grid(FZ)]
    for cell in ("R", "I"):
        for k in keys:
            for i, s in enumerate(e1.main_seeds(10)):
                v = special.get(k, [400.0 if k == "nc/base" else 401.0] * 10)[i]
                _write(root, "A", cell, k, s, v)


def test_c1_rescues_an_oracle_fail_and_rule2_follows(tmp_path):
    _grid_root(tmp_path, {"ma/p0.85": [320.0] * 6 + [440.0] * 4})
    rep = e1.report_stage(10, tmp_path, ("A",))
    r = rep["cells"]["R"]
    assert not r["o_off"]["pass"] and rep["oracle_fails_both"]
    assert r["best_tuned"] == "ma/p0.85" and r["C1_needed"]
    js = e1.stage_c1(rep, 10, tmp_path)
    assert len(js) == 2 * 2 * 10 and {j["seed"] for j in js} == set(e1.fresh_seeds(10))
    assert e1.final_verdict(rep, 10, {"R": True, "I": True}, {"R": False, "I": False}, tmp_path)["incomplete"]
    for cell in ("R", "I"):
        for s in e1.fresh_seeds(10):
            _write(tmp_path, "C1", cell, "nc/base", s, 400.0)
            _write(tmp_path, "C1", cell, "ma/p0.85", s, 330.0)
    v = e1.final_verdict(rep, 10, {"R": True, "I": True}, {"R": False, "I": False}, tmp_path)
    assert v["verdict"] == "CONTINUE-T" and "C1" in v["note"]                          # V215 A4
    c2 = e1.stage_c2(rep, 10, {"R": True, "I": True}, tmp_path)
    assert {(j["arm"], j["point"]) for j in c2} == {("nc", "base"), ("ma", "p0.85")}   # Rule 2 on the C1 pass
    v2 = e1.final_verdict(rep, 10, {"R": True, "I": True}, {"R": True, "I": True}, tmp_path)
    assert v2["verdict"] is None and v2["incomplete"]


def test_invalid_run_blocks_the_pass_and_stops(tmp_path):
    _grid_root(tmp_path, {"ma/p0.85": [300.0] * 10})
    _write(tmp_path, "A", "R", "ma/p0.85", e1.main_seeds(10)[3], 300.0, drained=False)
    rep = e1.report_stage(10, tmp_path, ("A",))
    assert not rep["cells"]["R"]["effects"]["ma/p0.85"]["pass_valid"] and rep["cells"]["R"]["effects"]["ma/p0.85"]["pass"]
    assert any("invalid run" in x for x in rep["stop"])
    assert e1.final_verdict(rep, 10, {"R": True, "I": True}, {"R": False, "I": False}, tmp_path)["refused"]


def test_rule2_fail_leaves_room_for_the_oracle_replicate(tmp_path):
    _grid_root(tmp_path, {"ma/p0.85": [300.0] * 10})
    rep = e1.report_stage(10, tmp_path, ("A",))
    c2 = e1.stage_c2(rep, 10, {"R": True, "I": True}, tmp_path)
    assert {(j["arm"], j["point"]) for j in c2 if j["cell"] == "R"} == {("nc", "base"), ("ma", "p0.85")}
    for cell in ("R", "I"):
        for s in e1.main_seeds(10):
            _write(tmp_path, "C2", cell, "nc/base", s, 400.0, ss=s + e1.TWIN)
            _write(tmp_path, "C2", cell, "ma/p0.85", s, 395.0, ss=s + e1.TWIN)      # the replicate fails
    v = e1.final_verdict(rep, 10, {"R": True, "I": True}, {"R": True, "I": True}, tmp_path)
    assert v["detail"]["R"]["M*_rule2"]["pass"] is False and v["verdict"] == "KILL"   # O_off picks M*: same twins


def test_intrusions_pool_nc_only_over_the_cells_a_point_ran_in():
    from v5b.fleet import e1_analysis as ea
    assert ea.intrusion_flag(5, 0)["flag"]
    # a one-cell point with 5 intrusions against NC's 2 in that cell only, not 4 over both cells
    assert ea.intrusion_flag(5, 2)["p"] < ea.intrusion_flag(5, 4)["p"]


def test_decision_tree_order():
    from v5b.fleet import e1_analysis as ea
    base = {"P_T": False, "P_O": False, "F": [], "powered": True}
    assert ea.verdict({"R": dict(base, P_T=True), "I": base})["verdict"] == "CONTINUE-T"
    assert ea.verdict({"R": dict(base, F=["M*"]), "I": dict(base, P_O=True)})["verdict"] == "I-ONLY"
    assert ea.verdict({"R": dict(base, F=["M*"]), "I": base})["verdict"] == "FLAGGED-ONLY"


def test_stop_reasons_and_ratio_pairing():
    log = [(60, 300.0, 0.0, 30.0, 5, 500.0, 1, 0, 0, 0, None), (120, 400.0, 300.0, 30.0, 5, 500.0, 1, 0, 0, 0, 300.0),
           (180, 400.0, 400.0, 30.0, 5, 500.0, 1, 0, 0, 0, 400.0)]
    m = {"log": log, "red_passages": 0, "max_red_exposure_s": 100.0}
    assert e1.ratio_rows(m) == [(300.0, 300.0), (400.0, 400.0)]          # minute k's command against minute k+1
    d = _fake_day(1, 100.0) | {"meter": m, "alks": None}
    assert e1.stop_reasons(d, "R") == []
    bad = dict(m, log=[r[:2] + (r[2] * 0.5,) + r[3:] for r in log], red_passages=1)
    why = e1.stop_reasons(_fake_day(1, 100.0) | {"meter": bad, "alks": None, "blocker": None}, "I")
    assert {"red passage", "meter actuator fault", "blocker did not stop"} <= set(why)


def test_resume_refuses_stale_and_failed(tmp_path):
    j = e1.job("A", "R", "ma", "p0.85", 1, ctrl={"meter": {"setpoint": 10.0}})
    p = e1.out_path(j, tmp_path)
    p.parent.mkdir(parents=True)
    p.write_text('{"ctrl": {"meter": {"setpoint": 11.0}}, "sumo_seed": null, "hours": null}')
    with pytest.raises(SystemExit, match="stale"):
        e1.run([j], 1, tmp_path)
    p.unlink()
    (p.parent / "FAILED.txt").write_text("x")
    with pytest.raises(SystemExit, match="failed before"):
        e1.run([j], 1, tmp_path)
    with pytest.raises(SystemExit, match="27"):
        e1.run([], 28, tmp_path)


def test_idle_replacement(tmp_path):
    import json as js
    for cell in ("R", "I"):
        for k in e1.grid(FZ):
            for s in e1.main_seeds(10)[:3]:
                arm, pt = k.split("/")
                p = e1.out_path(e1.job("A", cell, arm, pt, s), tmp_path)
                p.parent.mkdir(parents=True, exist_ok=True)
                on = not (k in ("ma/p1.05", "ma/p0.95"))
                p.write_text(js.dumps({"meter": {"metering_s": 900 if on else 0}, "alks": None}))
    r = e1.replace_idle(FZ, 10, tmp_path)
    assert set(r["idle"]) == {"ma/p1.05", "ma/p0.95"}
    assert r["replaced"] == {"ma/p0.95": "ma/p0.75"} and r["extra_idle"] == ["ma/p1.05"]   # once per variant
    assert len(r["jobs"]) == 20 and r["fz"]["setpoints"]["ma"] == (0.75, 0.85, 1.05)
    assert all(j["point"] != "p0.95" or j["arm"] != "ma" for j in e1.stage_a(r["fz"], 10, False, tuple(r["replaced"])))


def test_tie_break_prefers_the_middle_then_short_then_alinea():
    from v5b.fleet import e1_analysis as ea
    nc = np.full(10, 100.0)
    pts = {"c/p0.85_short": np.full(10, 95.0), "c/p0.95_long": np.full(10, 95.05), "c/p1.05_short": np.full(10, 94.95)}
    assert ea.tuned(nc, pts, ("c",)) == "c/p0.95_long"             # not the strict best
    pts2 = {"c/p0.85_long": np.full(10, 95.0), "c/p1.05_short": np.full(10, 95.0)}
    assert ea.tuned(nc, pts2, ("c",)) == "c/p1.05_short"           # equal distance from 0.95: the short zone


def test_braking_flag_fires_on_a_clear_increase(tmp_path):
    import json as js
    _grid_root(tmp_path, {"ma/p0.85": [300.0] * 10})
    for s in e1.main_seeds(10):
        p = e1.out_path(e1.job("A", "R", "ma", "p0.85", s), tmp_path)
        d = js.loads(p.read_text())
        d["emergency_braking_warnings"] = 12 + s % 3
        p.write_text(js.dumps(d))
    rep = e1.report_stage(10, tmp_path, ("A",))
    assert rep["cells"]["R"]["flags"]["M*"]["braking"] and not rep["cells"]["I"]["flags"]["M*"]["braking"]


def test_gain_stats_on_a_meter_slice():
    log = [(46800 + 60 * i, 900.0 if i < 30 else 400.0, 0.0, 12.0 + (i % 2), 5, 500.0, int(i >= 30), 0, 0, 0, None)
           for i in range(60)]
    d = {"series": [(46800.0 + 30.0 * i, 25, None, 0, 0, None, None, 27.0, None) for i in range(40)],
         "meter": {"log": log, "law": {"setpoint": 12.0}}}
    s = e1.gain_stats(d, "alinea")
    assert s["acts"] and s["first_active"] == 46800 + 1800 and s["onset"] is None and s["lead"]
    idle = {**d, "meter": {"log": [r[:6] + (0,) + r[7:] for r in log], "law": {"setpoint": 12.0}}}
    assert not e1.gain_stats(idle, "alinea")["acts"]                       # r_law < 900 while resting green
    assert s["rms"] == pytest.approx(((0.0 ** 2 + 1.0 ** 2) / 2) ** 0.5)


def test_gain_stats_rms_reads_the_raw_occupancy():
    log = [(46800 + 60 * i, 400.0, 0.0, 12.0, 5, 500.0, 1, 0, 0, 0, None, 12.0 + (i % 2)) for i in range(60)]
    d = {"series": [(46800.0 + 30.0 * i, 25, None, 0, 0, None, None, 27.0, None) for i in range(40)],
         "meter": {"log": log, "law": {"setpoint": 12.0}}}
    assert e1.gain_stats(d, "pi")["rms"] == pytest.approx(((0.0 ** 2 + 1.0 ** 2) / 2) ** 0.5)


def test_pi_reads_the_3_min_window_and_wave2c():
    assert e1.meter_ctrl("pi", 20.0)["window"] == 180.0 and "window" not in e1.meter_ctrl("alinea", 20.0)
    cal = {"o_cr": {"alinea": 20.0, "drop": 18.0}, "drop_loop": "drop"}
    js = e1.wave2c(cal, 5.2)
    assert {j["arm"] for j in js} == {"t0_meter", "t0_alks", "gain_alinea", "gain_pi", "self_alks"}
    assert len(js) == 4 + 2 + 9 + 6 + 3


def test_hold_test_skips_breakdown_episodes(monkeypatch):
    from v5b.fleet import e1_analysis as ea
    monkeypatch.setattr(ea, "_episodes", lambda ser, f: [(1000.0, 2000.0)])
    d = {"series": [], "alks": {"hold_free": [(500, -0.2), (950, -5.0), (1500, -6.0), (2050, -4.0), (2100, -0.4)]},
         "blocker": {"t": 2080.0, "duration": 100.0}}
    assert e1.hold_uncongested(d) == [-0.2, -0.4]
    assert e1.hold_uncongested(d, blockage=True) == [-0.2]


def test_ratio_rows_skip_supply_limited_minutes():
    row = lambda t, starved: (t, 500.0, 480.0, 10.0, 5, 500.0, 1, 0, 0, 0, 500.0, 10.0, starved)   # noqa: E731
    m = {"log": [row(60, 0), row(120, 1), row(180, 0), (240, 500.0, 480.0, 10.0, 5, 500.0, 1, 0, 0, 0, 500.0)]}
    assert e1.ratio_rows(m) == [(500.0, 480.0), (500.0, 480.0)]


def test_grid_and_t3_arms_without_pi():
    fz = {"o_cr": {"alinea": 6.6, "drop": 10.7}, "drop_loop": "drop", "c_loop": "drop", "l_bar": 5.2,
          "gains": {"k_r": 35.0, "pi": None, "k_i": 0.02}}
    pts = e1.grid(fz)
    assert len(pts) == 9 and not any(k.startswith("mp/") for k in pts)
    js = e1.wave2b(fz)
    arms = {j["arm"] for j in js}
    assert "t3_mp" not in arms and {"t3_ma", "t3_c", "t3_mc"} <= arms
    mc = next(j for j in js if j["arm"] == "t3_mc")["ctrl"]
    assert mc["meter"]["law"] == "alinea" and not mc["cascade"]


def _smoke_day(window=180.0, used=None):
    occ = [float(k % 7) for k in range(1, 21)]
    rows = [[30 * k, 0, occ[k - 1], None] for k in range(1, 21)]
    log = []
    for t in range(60, 601, 60):
        o6 = np.mean([r[2] for r in rows if r[0] <= t][-int(window // 30):])
        o2 = np.mean([r[2] for r in rows if r[0] <= t][-2:])
        log.append((t, 500.0, 480.0, round(float(o6 if used is None else used), 2), 5, 500.0, 1, 0, 0, 0, 500.0,
                    round(float(o2), 2), 0))
    cm = e1.meter_ctrl("pi", 10.0)
    j = e1.job("smoke", "R", "gain_pi", "wang_0", 7430040, ctrl={"meter": cm}, hours=e1.SMOKE_HOURS)
    d = {"ctrl": j["ctrl"], "hours": j["hours"], "sumo_seed": None, "plant": e1.PLANT, "drained": True, "teleports": 0,
         "sumo_errors": 0, "contacts": 0, "arrived_plus_removed": 5, "generated": 5,
         "loops30": {"groups": ["drop"], "rows": rows},
         "meter": {"law": {"kind": "pi", "setpoint": 10.0, "k_r": 70.0, "k_p": cm["k_p"], "k_i": cm["k_i"], "rate": 900.0},
                   "loop": "drop", "window": window, "constants": e1.SMOKE_CONST["meter"], "metering_s": 100, "log": log}}
    return d, j


def test_smoke_check_catches_window_and_constants():
    d, j = _smoke_day()
    assert e1.smoke_check(d, j) == {"ok": True, "bad": [], "active": {"meter": True}}
    d2, _ = _smoke_day(window=60.0)
    assert "meter loop or window" in e1.smoke_check(d2, j)["bad"]
    d3, _ = _smoke_day(used=99.0)
    assert any(b.startswith("meter input occupancy off") for b in e1.smoke_check(d3, j)["bad"])
    d4, _ = _smoke_day()
    d4["meter"]["constants"] = {**e1.SMOKE_CONST["meter"], "STOP_DECEL": 4.5}
    assert "meter constants" in e1.smoke_check(d4, j)["bad"]
    assert len(e1.smoke_jobs([j, dict(j, seed=1), dict(j, ctrl=None)])) == 1
