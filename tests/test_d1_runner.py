"""Screen D1 runner and meter: job lists, seed blocks, run-once refusal, determinism comparator, FBMeter law."""
from pathlib import Path

import pytest

from v5b.d1 import episode
from v5b.d1 import run_screen as rs
from v5b.d1.faults import ANY, FAULTS


def test_seed_blocks_disjoint_and_as_approved():
    S = rs.SEEDS
    assert S["tcheck"] == tuple(range(7_400_010, 7_400_030)) and S["tune"] == tuple(range(7_400_100, 7_400_120))
    assert S["eval"] == tuple(range(7_400_030, 7_400_080)) and len(S["eval"]) == 50
    assert all(s in rs.CALIB_ONLY for s in S["smoke"])
    blocks = [set(v) for v in S.values()]
    assert sum(len(b) for b in blocks) == len(set().union(*blocks))


def test_eval_job_lists():
    qfx, ratio = {"1600": 1000.0, "2000": 1200.0}, {"1600": 1.1, "2000": 1.2}
    lit = rs.eval_specs(qfx, ratio, True, 20.0, 8.0)
    assert len(lit) == 5 * 4 * 2 * 50 and len({s["key"] for s in lit}) == len(lit)
    ded = rs.eval_specs(qfx, ratio, False, 20.0, 8.0)
    assert len(ded) == 2 * 50 * (4 + 4) and len({s["key"] for s in ded}) == len(ded)
    assert {s["fault"] for s in ded if s["arm"] != "NV"} == {ANY}
    assert {s["fault"] for s in ded if s["arm"] == "NV"} == set(FAULTS)
    assert all(s["seed"] in rs.SEEDS["eval"] for s in ded)
    assert {s["q_fx"] for s in ded if s["arm"] == "FX"} == {1000.0, 1200.0}


def test_out_dir_rules(tmp_path):
    with pytest.raises(SystemExit):
        rs.check_out_dir(rs.REPO_ROOT / "runs_x", False)
    with pytest.raises(SystemExit):
        rs.check_out_dir(tmp_path, False)                    # not under /home/catalin/work/phd


def test_out_dir_refuses_existing_result(monkeypatch, tmp_path):
    monkeypatch.setattr(rs, "ALLOWED_ROOT", tmp_path)
    rs.check_out_dir(tmp_path / "new", False)
    (tmp_path / "done").mkdir()
    (tmp_path / "done" / "result.json").write_text("{}")
    with pytest.raises(SystemExit):
        rs.check_out_dir(tmp_path / "done", True)
    (tmp_path / "part" / "runs").mkdir(parents=True)
    (tmp_path / "part" / "runs" / "x.json").write_text("{}")
    with pytest.raises(SystemExit):
        rs.check_out_dir(tmp_path / "part", False)
    rs.check_out_dir(tmp_path / "part", True)


def test_determinism_comparator():
    a = {"hash": "h", "delay_s": 1.0, "served_ctrl_vph": 2.0, "ttt_ctrl_vehh": 3.0, "meter_log": [[70.0, 5, 6, 5.0, 1500.0]]}
    assert rs.same_run(a, dict(a))
    assert not rs.same_run(a, dict(a, delay_s=1.0000001))
    assert not rs.same_run(a, dict(a, meter_log=[[70.0, 5, 6, 5.0, 1500.1]]))


class _TL:
    def __init__(self):
        self.states = []

    def setRedYellowGreenState(self, tls, s):
        self.states.append(s)


class _LS:
    def __init__(self):
        self.trafficlight = _TL()


def test_fbmeter_law_and_missing_reading_holds_rate(monkeypatch):
    stub = _LS()
    monkeypatch.setattr(episode, "ls", stub)
    vals = iter([12.0, None, 4.0])
    m = episode.FBMeter(read=lambda t: next(vals))
    m.step(40.0)                                     # first call: no update
    assert m.q == 1500.0 and stub.trafficlight.states[-1] == "GGGG"
    m.step(70.0)
    assert m.q == pytest.approx(1500.0 + 20.0 * (8.0 - 12.0))
    m.step(100.0)                                    # no data: rate held
    assert m.q == pytest.approx(1420.0)
    m.step(130.0)
    assert m.q == pytest.approx(1420.0 + 20.0 * 4.0)
    assert m.cycle() == pytest.approx(max(6.0, 2 * 4 * 3600.0 / 1500.0))


def test_fbmeter_fx_freeze_and_clip(monkeypatch):
    monkeypatch.setattr(episode, "ls", _LS())
    m = episode.FBMeter(read=lambda t: 0.0)
    m.step(0.0)
    m.q, m.K_F = 1000.0, 0.0                         # FX switch
    for t in (30.0, 60.0, 90.0):
        m.step(t)
    assert m.q == 1000.0
    m2 = episode.FBMeter(read=lambda t: 1000.0)      # huge reading: clipped at q_min
    m2.step(0.0)
    m2.step(30.0)
    assert m2.q == 200.0
