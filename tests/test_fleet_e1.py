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
            "served": {"pm": {"main": 9000, "ramp": 1500}}, "ttt_w_h": 3000.0 + d, "blocker": {"t_stop": t_stop},
            "breakdowns_drop": [{"t_break": 58000.0, "drop": 0.11, "qdf": 3050.0}]}


def test_report_stage_end_to_end(tmp_path):
    import json as js
    seeds = e1.main_seeds(10)
    gains = {"nc/base": 0.0, "ma/p0.85": 0.25, "ma/p0.95": 0.12, "ma/p1.05": 0.05, "c/p0.85_long": 0.02,
             "c/p0.95_long": 0.01, "c/p1.05_long": 0.0}
    rng = np.random.default_rng(0)
    for cell in ("R", "I"):
        for k, g in gains.items():
            arm, pt = k.split("/")
            for s in seeds:
                p = e1.out_path(e1.job("A", cell, arm, pt, s), tmp_path)
                p.parent.mkdir(parents=True)
                p.write_text(js.dumps(_fake_day(s, 400.0 * (1 - g) + rng.normal(0, 2.0), intr=6 if arm == "ma" else 0)))
                np.savez(p.parent / f"conflicts_s{s}.npz", t=np.array([1.0, 2.0], np.float32),
                         follower=np.array([0, 0], np.int32), leader=np.array([1, 1], np.int32),
                         ttc=np.array([1.0, 0.8], np.float32), v_f=np.zeros(2, np.float32), v_l=np.zeros(2, np.float32),
                         cls=np.array([0, 0], np.int8))
    rep = e1.report_stage(10, tmp_path, ("A",))
    r = rep["cells"]["R"]
    assert r["tuned"]["M*"] == "ma/p0.85" and r["tuned_pass"]
    assert r["B1_edges"]["ma"]["next"] is None                     # a tuned arm passed: no extension
    assert r["o_off"]["pass"] and r["o_off_nc_picks"] == 0
    assert not r["C2_needed"] and not r["flags"]["M*"]["braking"]
    assert rep["intrusion_flags"]["ma/p0.85"]["flag"] and not rep["intrusion_flags"]["c/p0.95_long"]["flag"]
    assert r["harm_in_other_cell"]["M*"] == "no harm"
