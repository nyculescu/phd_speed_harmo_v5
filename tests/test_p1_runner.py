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
    s4 = rs.smoke_seeds(4)
    assert set().union(*map(set, s4.values())) == set(range(7_400_000, 7_400_004))     # task: smoke on 000-003 only
    assert not set(s4["tcheck"]) & set(s4["tune"]) and rs.smoke_seeds(10) == sm


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
    sen.unlink()
    flags = {"meter_signal": "continuous", "t3_replicate": "run", "tv_t0_window": "page", "gate_views": "both"}
    rs.write_sentinel(out, "abc", "sha", flags, sen)
    rs.check_sentinel(out, True, "abc", sen, args=dict(flags))
    for f, v in (("meter_signal", "d2"), ("gate_views", "all_seeds"), ("tv_t0_window", "ext120"), ("t3_replicate", "drop")):
        with pytest.raises(SystemExit):
            rs.check_sentinel(out, True, "abc", sen, args={**flags, f: v})      # a resume repeats the decisions
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


FLAGS = ["--meter-signal", "continuous", "--t3-replicate", "run", "--tv-t0-window", "page", "--gate-views", "both"]


def test_launch_rules():
    dec = {"meter_signal": "continuous", "t3_replicate": "run", "tv_t0_window": "page", "gate_views": "both"}
    a = SimpleNamespace(workers=32, cpu_limit=0.90, smoke=False, confirm_run_once=True, smoke_n=10, **dec)
    rs.check_launch(a, dirty=False)
    for f in dec:                                                               # every decision is explicit
        with pytest.raises(SystemExit):
            rs.check_launch(SimpleNamespace(**{**vars(a), f: None}), dirty=False)
    with pytest.raises(SystemExit):
        rs.check_launch(a, dirty=True)                                          # dirty tree refused
    with pytest.raises(SystemExit):
        rs.check_launch(SimpleNamespace(**{**vars(a), "confirm_run_once": False}), dirty=False)
    with pytest.raises(SystemExit):
        rs.check_launch(SimpleNamespace(**{**vars(a), "workers": 101}), dirty=False)
    with pytest.raises(SystemExit):
        rs.check_launch(SimpleNamespace(**{**vars(a), "cpu_limit": 0.95}), dirty=False)
    sm = SimpleNamespace(workers=8, cpu_limit=0.70, smoke=True, confirm_run_once=False, smoke_n=4, **dec)
    rs.check_launch(sm, dirty=True)
    with pytest.raises(SystemExit):
        rs.check_launch(SimpleNamespace(**{**vars(sm), "workers": 9}), dirty=False)
    assert rs.build_parser().parse_args(["--out", "x"] + FLAGS).cpu_limit == 0.90
    for i in range(0, len(FLAGS), 2):                                           # no default for any decision
        with pytest.raises(SystemExit):
            rs.build_parser().parse_args(["--out", "x"] + FLAGS[:i] + FLAGS[i + 2:])


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
    stored = {**s, "code_commit": "abc", "signal": "continuous"}
    assert rs.reuse_mismatch(stored, s, "abc", "continuous") == []
    assert rs.reuse_mismatch(stored, s, "def", "continuous") == ["code_commit"]
    assert rs.reuse_mismatch(stored, s, "abc", "d2") == ["signal"]             # never mix meter signals
    for f, v in (("k", 1), ("d", 0.0), ("vsl_b", 0.4), ("fa", True), ("rep", 1)):
        assert f in rs.reuse_mismatch({**stored, f: v}, s, "abc", "continuous")


def test_t3_pairs_cover_pi_ad_delayed_vsl():
    assert len(rs.t3_specs(7_400_240, replicate=False)) == 12                  # decision D2 'drop'
    assert not any(p[0]["k"] for p in rs.t3_specs(7_400_240, replicate=False))
    t3 = rs.t3_specs(7_400_240, replicate=True)
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


class _FakePool:
    """pool.run on a synthetic world (no SUMO); T3 pairs have no stored files, so T3 fails (not tested here)."""

    def __init__(self, world, out):
        self.world, self.out = world, out

    def run(self, specs, stage):
        return {s["key"]: {**s, **self.world(s)} for s in specs}, []


def _tc_world(bad=frozenset()):
    """N_t = c1600 (best clean). The f20_8 plans (ID / IP) are 50 % below NC; on the `bad` seeds that run is invalid,
    and on the other seeds it is only 5 % below NC when `bad` is non-empty. NC + VSL: entries -10 % in the page
    window (on the bad seeds only, invalid there, when `bad` is non-empty), unchanged over ext120."""
    def f(s):
        seed, inc = s["seed"], s["incident"]
        base = 300.0 + seed % 5
        if inc == "none":
            d = {"c1600": 0.5, "c800": 0.6, "f20_8": 0.55, "NC": 0.7}.get(s["pre"], 0.6) * base
            return {"delay_s": d, "valid": True, "teleports": 0, "entered_e4_incident": None,
                    "entered_e4_ext120": None, "ad_max_dev": None}
        hit = not bad or seed in bad
        valid = True
        if s["post"] is not None:
            d = (0.5 if hit else 0.95) * base if s["post"] == "f20_8" else 0.97 * base
            valid = not (seed in bad and s["post"] == "f20_8")
        elif s["pre"] == "NC":
            d, valid = base, not (seed in bad and s["vsl_b"] is not None)
        else:
            d = {"c1600": 0.99, "c800": 0.98, "f20_8": 0.985}.get(s["pre"], 0.99) * base
        n = 100 - (10 if s["vsl_b"] is not None and hit else 0)
        return {"delay_s": d, "valid": valid, "teleports": 0, "entered_e4_incident": n + seed % 3,
                "entered_e4_ext120": 130 + seed % 3, "ad_max_dev": 3.0}
    return f


@pytest.mark.parametrize("views", ["all_seeds", "both"])
def test_tool_check_views_and_tv_window(tmp_path, views):
    """Decision D4 (gate views) and D3 (TV-T0 window) on a synthetic world."""
    seeds = tuple(range(7_400_000, 7_400_006))
    G3 = ("c800", "c1600", "f20_8")
    pool = _FakePool(_tc_world(), tmp_path)                    # no invalid run: both views agree
    tc = rs.stage_tcheck(pool, seeds, G3, gate_views=views, tv_window="page", t3_replicate=False)
    assert tc["T0"]["pass"] and tc["T0"]["valid_only"]["pass"] and tc["TV_T0"]["pass"]       # -10 % entries bind
    assert "travel-time shift" in tc["TV_T0"]["caveat"]                                       # but not over ext120
    tc = rs.stage_tcheck(pool, seeds, G3, gate_views=views, tv_window="ext120", t3_replicate=False)
    assert not tc["TV_T0"]["pass"] and tc["TV_T0"]["count_field"] == "entered_e4_ext120"     # no change over ext120
    assert tc["TV_T0"]["other_window_entered_e4_incident_report_only"]["pass"]
    # the gains come from invalid runs only (seeds 1-5): all seeds pass, valid only fails
    pool = _FakePool(_tc_world(bad=frozenset(seeds[1:])), tmp_path)
    tc = rs.stage_tcheck(pool, seeds, G3, gate_views=views, tv_window="page", t3_replicate=False)
    assert tc["T0"]["pass_all_seeds"] and not tc["T0"]["valid_only"]["pass"]
    assert tc["T0"]["pass"] == (views == "all_seeds")
    assert tc["TV_T0"]["pass_all_seeds"] and not tc["TV_T0"]["valid_only"]["pass"]
    assert tc["TV_T0"]["pass"] == (views == "all_seeds")
