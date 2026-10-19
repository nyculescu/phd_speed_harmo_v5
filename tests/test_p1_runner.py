"""P1 runner: seed ranges (page §7, A9(a)), run-once sentinel, resume at the same commit, dirty-tree refusal,
directory and launch rules, the tool-check record, T3 coverage and run counts."""
import json
from types import SimpleNamespace

import pytest

from v5b.d1 import run_screen as d1
from v5b.d2 import run_screen as d2
from v5b.p1 import family as fam
from v5b.p1 import run as rs


def test_seed_ranges_as_approved():
    S = rs.SEEDS
    assert S["tcheck"] == tuple(range(7_400_240, 7_400_260))                   # A9(a)
    assert S["tune"] == tuple(range(7_400_200, 7_400_240)) and len(S["tune"]) == 40
    assert S["eval"] == tuple(range(7_400_500, 7_400_600)) and len(S["eval"]) == 100
    blocks = [set(v) for v in S.values()]
    assert sum(len(b) for b in blocks) == len(set().union(*blocks))            # disjoint
    used = set().union(*(set(v) for m in (d1, d2) for k, v in m.SEEDS.items() if k != "smoke"))
    assert not used & set().union(*blocks)                                      # D1 / D2 seeds not reused
    assert all(7_400_200 <= s <= 7_400_299 for s in S["tcheck"] + S["tune"])    # v5.B tuning block
    assert all(7_400_500 <= s <= 7_400_699 for s in S["eval"])                  # v5.B test block
    sm = rs.SMOKE_SEEDS
    assert all(s in rs.CALIB_ONLY for v in sm.values() for s in v) and set(rs.CALIB_ONLY) == set(range(7_400_000, 7_400_010))
    assert not set(sm["tcheck"]) & set(sm["tune"]) and not set(sm["tune"]) & set(sm["eval"])


def test_replicate_seeds_outside_every_block():
    from v5b.p1.meters import replicate_seeds
    reps = {replicate_seeds(s, k)["sumo_seed"] for s in rs.SEEDS["eval"] for k in (1, 2, 3, 4)}
    assert min(reps) == 17_400_500 and max(reps) == 47_400_599
    assert not reps & set(range(7_400_000, 7_401_000)) and not reps & set(range(7_410_000, 7_420_000))


def test_sentinel_run_once_and_resume_same_commit(tmp_path):
    sen = tmp_path / "P1_EVAL_STARTED.json"
    out = tmp_path / "p1" / "v99"
    rs.check_sentinel(out, False, "abc", sen)                                   # nothing started yet
    rs.write_sentinel(out, "abc", "sha", {"x": 1}, sen)
    assert json.loads(sen.read_text())["code_commit"] == "abc"
    with pytest.raises(SystemExit):
        rs.check_sentinel(out, False, "abc", sen)                               # not --resume
    with pytest.raises(SystemExit):
        rs.check_sentinel(tmp_path / "other", True, "abc", sen)                 # another --out
    with pytest.raises(SystemExit):
        rs.check_sentinel(out, True, "def", sen)                                # another commit
    rs.check_sentinel(out, True, "abc", sen)                                    # resume, same out, same commit
    rs.write_sentinel(out, "zzz", "sha", {}, sen)                               # never overwritten
    assert json.loads(sen.read_text())["code_commit"] == "abc"
    assert rs.SENTINEL == rs.Path("/home/catalin/work/phd/v5b1_runs/P1_EVAL_STARTED.json")


def test_out_dir_rules(monkeypatch, tmp_path):
    monkeypatch.setattr(rs, "ALLOWED_ROOT", tmp_path)
    with pytest.raises(SystemExit):
        rs.check_out_dir(rs.REPO_ROOT / "runs_here", False)
    out = tmp_path / "p1"
    rs.check_out_dir(out, False)
    (out / "runs").mkdir(parents=True)
    (out / "runs" / "x.json").write_text("{}")
    with pytest.raises(SystemExit):
        rs.check_out_dir(out, False)
    rs.check_out_dir(out, True)
    (out / "result.json").write_text("{}")
    with pytest.raises(SystemExit):
        rs.check_out_dir(out, True)


def test_launch_rules():
    a = SimpleNamespace(workers=32, cpu_limit=0.90, smoke=False, confirm_run_once=True)
    rs.check_launch(a, dirty=False)
    with pytest.raises(SystemExit):
        rs.check_launch(a, dirty=True)                                          # dirty tree refused
    with pytest.raises(SystemExit):
        rs.check_launch(SimpleNamespace(**{**vars(a), "confirm_run_once": False}), dirty=False)
    with pytest.raises(SystemExit):
        rs.check_launch(SimpleNamespace(**{**vars(a), "workers": 101}), dirty=False)
    with pytest.raises(SystemExit):
        rs.check_launch(SimpleNamespace(**{**vars(a), "cpu_limit": 0.95}), dirty=False)
    sm = SimpleNamespace(workers=8, cpu_limit=0.70, smoke=True, confirm_run_once=False)
    rs.check_launch(sm, dirty=True)
    with pytest.raises(SystemExit):
        rs.check_launch(SimpleNamespace(**{**vars(sm), "workers": 9}), dirty=False)
    assert rs.build_parser().parse_args(["--out", "x"]).cpu_limit == 0.90


def test_tcheck_record_blocks_reruns(tmp_path):
    rec = tmp_path / "rec.json"
    tc = {"pass": False, "T0": {"pass": False}, "T1": {"pass": True}, "T3_pass": True, "T4": {"pass": True},
          "TV_T0": {"pass": False}, "vsl_enters": False}
    rs.check_tcheck_record("c1", rec)
    rs.append_tcheck_record(tmp_path, "c1", "sha", tc, "STOP (tool check T0)", rec)
    with pytest.raises(SystemExit):
        rs.check_tcheck_record("c2", rec)                                       # T0 failure is final
    rec.unlink()
    rs.append_tcheck_record(tmp_path, "c1", "sha", {**tc, "T0": {"pass": True}, "T3_pass": False}, "FIX", rec)
    with pytest.raises(SystemExit):
        rs.check_tcheck_record("c1", rec)                                       # T3 failure: same commit refused
    rs.check_tcheck_record("c2", rec)                                           # another commit may repeat


def test_reuse_mismatch_covers_every_spec_field():
    s = rs.make_spec("c1600", "c800", True, "block", 2000.0, 7_400_000, k=2, d=30.0, c=60.0)
    stored = {**s, "code_commit": "abc"}
    assert rs.reuse_mismatch(stored, s, "abc") == []
    assert rs.reuse_mismatch(stored, s, "def") == ["code_commit"]
    for f, v in (("k", 1), ("d", 0.0), ("vsl_b", 0.4), ("fa", True), ("rep", 1)):
        assert f in rs.reuse_mismatch({**stored, f: v}, s, "abc")


def test_t3_pairs_cover_pi_ad_delayed_vsl():
    t3 = rs.t3_specs(7_400_240)
    assert len(t3) == 13 and all(p[0]["rep"] == 0 and p[1]["rep"] == 1 for p in t3)
    assert all({k: v for k, v in p[0].items() if k not in ("rep", "key")} ==
               {k: v for k, v in p[1].items() if k not in ("rep", "key")} for p in t3)
    first = [p[0] for p in t3]
    assert any(s["pre"] in fam.PI for s in first) and any(s["pre"].startswith("ad") for s in first)
    assert any(s["d"] and s["c"] for s in first) and any(s["vsl_b"] for s in first)
    assert any(s["k"] for s in first) and any(s["fa"] for s in first) and sum(bool(s["back"]) for s in first) >= 1


def test_run_counts_match_the_page_estimate():
    rc = rs.run_counts()
    assert rc["eval_replicates"] == 160_000 and 205_000 < rc["eval"] < 215_000          # page §8: ~214k
    assert 71_000 < rc["tune"] < 73_000 and 14_000 < rc["tcheck"] < 15_500             # ~72k, ~15k
    assert 290_000 < rc["total"] < 305_000                                             # ~300k
