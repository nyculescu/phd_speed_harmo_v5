"""Screen D2 incidents (Rule 2): onset / duration window, closure applied and removed, no teleports in a short
SUMO smoke (smoke seed 7,400,000 only), and the controller switch at onset."""
import json
import os
import subprocess
from pathlib import Path

import pytest

from v5b.d1.config import PYTHON_BIN, REPO_ROOT, clean_sumo_env
from v5b.d1.episode import FBMeter
from v5b.d2 import controllers as ctl
from v5b.d2 import episode
from v5b.d2.incidents import (BLOCK_LANE, BLOCK_MPS, DUR_MAX_S, DUR_MIN_S, INCIDENTS, SLOW_EDGE, SLOW_MPS, Incident,
                              incident_window)

SMOKE_SEED = 7_400_000


def test_window_bounds_and_determinism():
    for s in range(7_400_000, 7_401_000):
        on, dur = incident_window(s, 40.0, 900.0)
        assert 40.0 <= on <= 340.0 and DUR_MIN_S <= dur <= DUR_MAX_S
        assert on + dur < 40.0 + 900.0                     # every incident ends inside the control period
    assert incident_window(7_400_123, 40.0, 900.0) == incident_window(7_400_123, 40.0, 900.0)
    assert incident_window(7_400_123, 40.0, 900.0) != incident_window(7_400_124, 40.0, 900.0)


def test_window_spreads_over_its_range():
    w = [incident_window(s, 40.0, 900.0) for s in range(7_400_000, 7_402_000)]
    on, dur = [x[0] for x in w], [x[1] for x in w]
    assert min(on) < 50 and max(on) > 330 and min(dur) < 130 and max(dur) > 470


class _Lane:
    def __init__(self, speeds):
        self.speeds, self.calls = speeds, []

    def getMaxSpeed(self, ln):
        return self.speeds[ln]

    def setMaxSpeed(self, ln, v):
        self.calls.append((ln, v))
        self.speeds[ln] = v


class _Edge:
    def __init__(self, lane):
        self.lane, self.calls = lane, []

    def setMaxSpeed(self, e, v):
        self.calls.append((e, v))
        for ln in self.lane.speeds:
            if ln.rsplit("_", 1)[0] == e:
                self.lane.speeds[ln] = v


class _API:
    def __init__(self):
        self.lane = _Lane({"4_0": 23.0, "4_1": 23.0, "5_0": 23.0})
        self.edge = _Edge(self.lane)


@pytest.mark.parametrize("kind", INCIDENTS)
def test_closure_applied_at_onset_and_removed_after_duration(kind):
    api = _API()
    inc = Incident(kind, onset=100.4, duration=200.0, api=api)
    evs = {t: inc.tick(float(t)) for t in range(40, 940)}
    assert evs[101] == "on" and inc.t_on == 101.0               # first 1-s tick at or after the onset
    assert evs[301] == "off" and inc.t_off == 301.0             # first tick at or after onset + duration
    assert [t for t, e in evs.items() if e] == [101, 301]
    if kind == "slow":
        assert api.edge.calls == [(SLOW_EDGE, SLOW_MPS)] and inc.log[0][2] == {"5_0": SLOW_MPS}
    else:
        assert api.lane.calls[0] == (BLOCK_LANE, BLOCK_MPS) and inc.log[0][2] == {BLOCK_LANE: BLOCK_MPS}
    assert api.lane.speeds == {"4_0": 23.0, "4_1": 23.0, "5_0": 23.0}   # restored
    assert inc.assert_state(500.0)[0]


def test_none_never_acts_and_clear_is_safe():
    api = _API()
    inc = Incident("none", 100.0, 200.0, api=api)
    assert all(inc.tick(float(t)) is None for t in range(40, 940))
    assert api.lane.calls == [] and api.edge.calls == [] and inc.clear(940.0) is None
    blk = Incident("block", 100.0, 200.0, api=api)
    blk.tick(100.0)
    assert blk.assert_state(150.0)[0]
    api.lane.speeds["4_1"] = 23.0                                # state drift is caught (H-I1)
    assert not blk.assert_state(150.0)[0]
    blk.clear(150.0)
    assert api.lane.speeds["4_1"] == 23.0 and blk.done and blk.tick(400.0) is None


class _TL:
    def setRedYellowGreenState(self, tls, s):
        pass


class _LS:
    trafficlight = _TL()


def test_switch_changes_meter_in_place(monkeypatch):
    from v5b.d1 import episode as e1
    monkeypatch.setattr(e1, "ls", _LS())
    m = FBMeter(read=lambda t: 4.0, **ctl.meter_kwargs("c1600"))
    assert m.q == 1600.0 and m.K_F == 0.0
    m.step(40.0)
    m.step(70.0)
    assert m.q == 1600.0                                         # constant rate holds
    ctl.switch(m, "f40_10")
    assert (m.K_F, m.n_crit, m.q) == (40.0, 10.0, 1600.0)       # feedback continues from the current rate
    m.step(100.0)
    assert m.q == pytest.approx(1600.0 + 40.0 * (10.0 - 4.0))
    ctl.switch(m, "c800")
    assert (m.q, m.K_F) == (800.0, 0.0)
    m.step(130.0)
    assert m.q == 800.0


def test_run_checks():
    with pytest.raises(ValueError):
        episode.check_run("NC", "c800", "block")
    with pytest.raises(ValueError):
        episode.check_run("c1600", "c800", "none")
    with pytest.raises(ValueError):
        episode.check_run("c1650", None, "block")
    episode.check_run("NC", None, "slow")
    episode.check_run("f70_12", "c600", "slow")


# ---------------------------------------------------------------- SUMO smoke (smoke seed only)
SUMO_RUNS = {"block_fixed": ("c1600", None, "block"), "slow_fixed": ("c1600", None, "slow"),
             "block_to_c800": ("c1600", "c800", "block"), "slow_to_f40": ("c1600", "f40_10", "slow"),
             "block_to_c800_xf": ("c1600", "c800", "block")}   # cross-fit replicate (Addendum D2-A1)


@pytest.fixture(scope="module")
def sumo_runs(tmp_path_factory):
    d = tmp_path_factory.mktemp("d2_sumo")
    procs = {}
    for name, (pre, post, inc) in SUMO_RUNS.items():
        s = {"pre": pre, "post": post, "incident": inc, "q": 2000.0, "seed": SMOKE_SEED, "key": name,
             "xf": name.endswith("_xf")}
        procs[name] = subprocess.Popen([PYTHON_BIN, "-m", "v5b.d2.episode", "--spec", json.dumps(s),
                                        "--out", str(d / f"{name}.json"), "--run-dir", str(d / name)],
                                       cwd=REPO_ROOT, env=clean_sumo_env(), stdout=subprocess.DEVNULL,
                                       stderr=subprocess.PIPE, preexec_fn=lambda: os.nice(19))
    out = {}
    for name, p in procs.items():
        _, err = p.communicate(timeout=300)
        assert p.returncode == 0, err.decode()[-2000:]
        out[name] = json.loads((d / f"{name}.json").read_text())
    return out


def test_sumo_incident_applied_removed_no_teleports(sumo_runs):
    on, dur = incident_window(SMOKE_SEED, 40.0, 900.0)
    for name, r in sumo_runs.items():
        assert r["teleports"] == 0 and r["valid"] and r["drained"] and r["n_trips"] == r["generated"], name
        assert on <= r["t_on"] < on + 1.0 and on + dur <= r["t_off"] < on + dur + 1.0
        assert not r["incident_on_at_control_end"]
        (t1, e1, v1), (t2, e2, v2) = r["incident_log"]
        assert (e1, e2) == ("on", "off")
        if r["incident"] == "block":
            assert v1 == {BLOCK_LANE: BLOCK_MPS} and v2 == {BLOCK_LANE: 23.0}
        else:
            assert v1 == {"5_0": SLOW_MPS} and v2 == {"5_0": 23.0}
        assert "H-I1" not in r["health_codes"]


def test_sumo_switch_at_onset(sumo_runs):
    for name in ("block_fixed", "slow_fixed"):
        r = sumo_runs[name]
        assert r["t_switch"] is None and {e[2] for e in r["meter_log"]} == {1600.0}
    r = sumo_runs["block_to_c800"]
    assert r["t_switch"] == r["t_on"] and r["q_at_switch"] == 1600.0
    assert {e[2] for e in r["meter_log"] if e[0] < r["t_switch"]} == {1600.0}
    assert {e[2] for e in r["meter_log"] if e[0] >= r["t_switch"]} == {800.0}
    r = sumo_runs["slow_to_f40"]
    assert r["t_switch"] == r["t_on"]
    after = [e for e in r["meter_log"] if e[0] >= r["t_switch"]]
    q = 1600.0
    for t, n4, q_before in after:                                # the K_F = 40, n_crit = 10 law after the switch
        assert q_before == pytest.approx(q, abs=1e-3)
        q = min(max(q + 40.0 * (10.0 - n4), 200.0), 4000.0)


def test_sumo_crossfit_replicate(sumo_runs):
    """Addendum D2-A1: same demand and incident window, SUMO RNG seeded by seed + XF_SUMO_OFFSET, so the run differs."""
    m, x = sumo_runs["block_to_c800"], sumo_runs["block_to_c800_xf"]
    assert (m["xf"], m["sumo_seed"]) == (False, SMOKE_SEED)
    assert (x["xf"], x["sumo_seed"]) == (True, SMOKE_SEED + episode.XF_SUMO_OFFSET)
    assert (x["t_on"], x["t_off"], x["generated"]) == (m["t_on"], m["t_off"], m["generated"])
    assert x["t_switch"] == m["t_switch"] and x["hash"] != m["hash"]


def test_sumo_emergency_by_edge_recorded(sumo_runs):
    """Addendum D2-A8: per-edge counts from the SUMO log add up to SUMO's emergency warnings."""
    for name, r in sumo_runs.items():
        e = r["emergency_by_edge"]
        assert set(e) == {"all", "incident"}, name
        assert sum(e["all"].values()) >= sum(e["incident"].values())
