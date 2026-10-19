"""Screen D2 runner: seed blocks, job lists, run-once sentinel, resume-with-commit, directory and launch rules."""
import json
from types import SimpleNamespace

import pytest

from v5b.d1 import run_screen as d1
from v5b.d2 import controllers as ctl
from v5b.d2 import run_screen as rs
from v5b.d2.incidents import INCIDENTS


def test_seed_blocks_as_approved_and_disjoint():
    S = rs.SEEDS
    assert S["smoke"] == tuple(range(7_400_000, 7_400_004)) and all(s in rs.CALIB_ONLY for s in S["smoke"])
    assert S["tcheck"] == tuple(range(7_400_080, 7_400_100))
    assert S["tune"] == tuple(range(7_400_120, 7_400_140))
    assert S["eval"] == tuple(range(7_400_140, 7_400_190)) and len(S["eval"]) == 50
    blocks = [set(v) for v in S.values()]
    assert sum(len(b) for b in blocks) == len(set().union(*blocks))
    used_by_d1 = set().union(*(set(v) for k, v in d1.SEEDS.items() if k != "smoke"))
    assert not used_by_d1 & set().union(*(set(v) for k, v in S.items() if k != "smoke"))   # fresh seeds
    assert all(7_400_000 <= s <= 7_400_299 for b in blocks for s in b)   # v5.B block: calibration / checks / tuning


def test_job_lists():
    rc = rs.run_counts()
    assert rc == {"tcheck": 9932, "tune": 9800, "eval": 29000, "total": 48732}   # A1 replicates; A12 back actions
    arms = {"1600": {"N": "c1600", "FX": "c1400", "FB": "f20_8", "IP": {}},
            "2000": {"N": "c1600", "FX": "c1600", "FB": "f20_8", "IP": {}}}
    ev = rs.eval_specs(arms, ctl.G, rs.SEEDS["eval"])
    assert len({s["key"] for s in ev}) == len(ev) == 29000 - 50   # q=2000: FX == N without incident (de-duplicated)
    assert all(s["seed"] in rs.SEEDS["eval"] for s in ev)
    sw = [s for s in ev if s["post"] and not s["xf"]]
    xf = [s for s in ev if s["xf"]]
    assert len(xf) == len(sw) and {(s["pre"], s["post"], s["incident"], s["q"], s["seed"]) for s in xf} == \
        {(s["pre"], s["post"], s["incident"], s["q"], s["seed"]) for s in sw} and all(s["key"].endswith("_xf") for s in xf)
    assert len(sw) == 2 * 35 * 2 * 2 * 50 and sum(s["back"] for s in sw) == 35 * 2 * 2 * 50 and {s["pre"] for s in sw} == {"c1600"} and {s["incident"] for s in sw} == set(INCIDENTS)
    fx = rs.fixed_specs(ctl.G, ("none", "slow", "block"), rs.SEEDS["tcheck"], True)
    assert len(fx) == 36 * 3 * 2 * 20 and {s["pre"] for s in fx} == set(ctl.G) | {"NC"}
    assert all(s["post"] is None for s in fx)


def test_reuse_mismatch():
    s = rs.spec("c1600", "f20_8", "block", 2000.0, 7_400_140)
    stored = {**{k: s[k] for k in rs.SPEC_FIELDS}, "code_commit": "abc"}
    assert rs.reuse_mismatch(stored, s, "abc") == []
    assert rs.reuse_mismatch(stored, s, "def") == ["code_commit"]
    assert rs.reuse_mismatch(dict(stored, post="c800"), s, "abc") == ["post"]


def test_out_dir_rules(monkeypatch, tmp_path):
    with pytest.raises(SystemExit):
        rs.check_out_dir(rs.REPO_ROOT / "runs_x", False)
    with pytest.raises(SystemExit):
        rs.check_out_dir(tmp_path, False)                        # not under /home/catalin/work/phd
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


def test_sentinel_run_once_and_resume_same_commit(tmp_path):
    sen = tmp_path / "D2_EVAL_STARTED.json"
    out = tmp_path / "screen"
    rs.check_sentinel(out, False, "c1", sentinel=sen)            # nothing started yet
    rs.write_sentinel(out, "c1", "sha", {}, sentinel=sen)
    assert json.loads(sen.read_text())["code_commit"] == "c1"
    with pytest.raises(SystemExit):
        rs.check_sentinel(out, False, "c1", sentinel=sen)        # no second run
    with pytest.raises(SystemExit):
        rs.check_sentinel(tmp_path / "other", True, "c1", sentinel=sen)
    with pytest.raises(SystemExit):
        rs.check_sentinel(out, True, "c2", sentinel=sen)         # resume at another commit
    rs.check_sentinel(out, True, "c1", sentinel=sen)
    rs.write_sentinel(out, "c1", "sha", {}, sentinel=sen)        # kept as is
    assert rs.SENTINEL.name == "D2_EVAL_STARTED.json" and rs.SENTINEL.parent.name == "v5b1_runs"


def test_launch_rules():
    a = SimpleNamespace(workers=16, smoke=False, confirm_run_once=False)
    with pytest.raises(SystemExit):
        rs.check_launch(a, dirty=False)                          # needs --confirm-run-once
    a.confirm_run_once = True
    with pytest.raises(SystemExit):
        rs.check_launch(a, dirty=True)                           # refuses a dirty tree
    rs.check_launch(a, dirty=False)
    s = SimpleNamespace(workers=16, smoke=True, confirm_run_once=False)
    with pytest.raises(SystemExit):
        rs.check_launch(s, dirty=True)                           # smoke: <= 8 workers
    s.workers = 8
    rs.check_launch(s, dirty=True)
    with pytest.raises(SystemExit):
        rs.check_launch(SimpleNamespace(workers=101, smoke=False, confirm_run_once=True), dirty=False)
