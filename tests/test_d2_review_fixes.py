"""Screen D2 review fixes (page Addendum 2026-10-19, D2-A1 ... D2-A10). Each test fails on the code at bc69707."""
import json

import numpy as np
import pytest

from v5b.d2 import controllers as ctl
from v5b.d2 import episode
from v5b.d2 import run_screen as rs
from v5b.d2 import stats
from v5b.d2.episode import run_key

G3 = ("c800", "c1600", "f20_8")
G8 = ("c800", "c1000", "c1200", "c1400", "c1600", "f10_6", "f20_8", "f40_10")
SEEDS = tuple(range(1, 21))
Q = 2000.0


def _run(pre, post, inc, q, s, delay, xf=False, valid=True, back=False):
    return {"key": run_key(pre, post, inc, q, s, xf=xf, back=back), "pre": pre, "post": post, "incident": inc, "q": q,
            "seed": s, "xf": xf, "back": back, "delay_s": float(delay), "served_ctrl_vph": 1500.0, "ttt_ctrl_vehh": 10.0,
            "ttt_full_vehh": 12.0, "valid": valid, "teleports": 0}


def _noise_only(seed=0, G_=G3, sd=40.0):
    """Every switch target has the same expected delay (400 s); the per-run noise is large (sd 40 s) and
    independent between the main run and its replicate. FX / FB are 25 % worse. In-sample OR = per-seed min
    looks like headroom over IP; the cross-fitted ORX must not."""
    r = np.random.default_rng(seed)
    res = {}
    add = lambda x: res.__setitem__(x["key"], x)
    for q in rs.QS:
        for s in SEEDS:
            for inc in ("slow", "block"):
                for g in G_:
                    for b in (False, True):   # A12: every action of G x {stay, back} is equally good
                        add(_run("c1600", g, inc, q, s, 400 + r.normal(0, sd), back=b))
                        add(_run("c1600", g, inc, q, s, 400 + r.normal(0, sd), xf=True, back=b))
                add(_run("c800", None, inc, q, s, 533))
                add(_run("f20_8", None, inc, q, s, 533))
                add(_run("NC", None, inc, q, s, 900))
    return res


ARMS = {"N": "c1600", "FX": "c800", "FB": "f20_8", "IP": {"slow": "c1600", "block": "c1600"}}


def test_a1_crossfit_or_is_picked_on_the_replicate_and_scored_on_the_main_run():
    res = _noise_only()
    ok, keys, pick = rs.cell_keys(res, SEEDS, G3, Q, "block", ARMS, xfit=True)
    assert ok == list(SEEDS)
    for i, s in enumerate(ok):
        best_x = min(ctl.actions(G3), key=lambda a: (res[rs.sw_key("c1600", a, "block", Q, s, xf=True)]["delay_s"],
                                                     ctl.rank(a)))
        assert keys["ORX"][i] == rs.sw_key("c1600", best_x, "block", Q, s)       # a main run, not a replicate
        assert keys["IPX"][i] == run_key("c1600", "c1600", "block", Q, s, xf=True)
        assert res[keys["OR"][i]]["delay_s"] <= res[keys["ORX"][i]]["delay_s"]   # page OR is the per-seed min
    del res[run_key("c1600", "f20_8", "block", Q, 3, xf=True)]                   # a missing replicate drops the seed
    ok, _, _ = rs.cell_keys(res, SEEDS, G3, Q, "block", ARMS, xfit=True)
    assert 3 not in ok and len(ok) == len(SEEDS) - 1


def test_a1_noise_cannot_pass_a_cell_with_crossfit():
    """Pure selection noise (8 equal targets, sd 15 %): the page's OR alone gives CONTINUE; with ORX it is STOP."""
    res = _noise_only(G_=G8, sd=60.0)
    arms = {rs.qk(q): ARMS for q in rs.QS}
    cells_page, _ = rs.incident_cells(res, SEEDS, G8, arms)                      # page OR only (T-check use)
    cells, opmap = rs.incident_cells(res, SEEDS, G8, arms, xfit=True)
    assert stats.decide(cells_page) == "CONTINUE"                              # the defect: noise alone passes
    hd_page = cells_page["block_q2000"]["per_fallback"]["IP"]["HD"]
    hd_x = cells["block_q2000"]["crossfit"]["per_fallback"]["IP"]["HD"]
    assert hd_page >= 0.10 and hd_x < 0.10                                     # selection optimism shows up
    assert all(not c["pass"] for c in cells.values()) and stats.decide(cells) == "STOP"
    m = opmap["block_q2000"]
    assert m["selection_optimism_HD"]["IP"] == pytest.approx(hd_page - hd_x)
    assert 0.0 < m["replicate_noise_IP"]["median_abs_rel"] < 1.0 and "ORX" in m["arms"] and m["orx_picks"]


def test_a1_combine_needs_both_and_is_never_easier():
    base = {"n": 3, "med_OR": 1.0, "per_fallback": {}, "binding": "IP"}
    for a, b in ((True, True), (True, False), (False, True), (False, False)):
        c = stats.combine_crossfit({**base, "pass": a}, {**base, "pass": b})
        assert c["pass"] == (a and b) and c["pass_in_sample"] == a and c["pass_crossfit"] == b


def test_a1_replicate_key_and_reuse_field():
    assert run_key("c1600", "c800", "block", Q, 7_400_140, xf=True) == "c1600-c800_block_q2000_s7400140_xf"
    s = rs.spec("c1600", "c800", "block", Q, 7_400_140, xf=True)
    stored = {**{k: s[k] for k in rs.SPEC_FIELDS}, "code_commit": "abc"}
    assert rs.reuse_mismatch(stored, s, "abc") == []
    assert rs.reuse_mismatch(dict(stored, xf=False), s, "abc") == ["xf"]
    assert episode.XF_SUMO_OFFSET == 10_000_000
    assert not any(7_100_000 <= x + episode.XF_SUMO_OFFSET <= 7_419_999 for v in rs.SEEDS.values() for x in v)


def test_a5_t4_needs_every_cell():
    n = np.full(20, 400.0)
    cells = {"slow_q1600": stats.t4_cell(n, n * 0.95, "a", "b"), "block_q2000": stats.t4_cell(n, n * 0.8, "a", "b")}
    assert not stats.t4_overall(cells)["pass"]


def test_a6_grid_edges_cover_every_dimension():
    assert ctl.grid_edges("c600") == ["rate=600"] and ctl.grid_edges("c2600") == ["rate=2600"]
    assert ctl.grid_edges("c1600") == []
    assert ctl.grid_edges("f70_8") == ["K_F=70"] and ctl.grid_edges("f10_12") == ["K_F=10", "n_crit=12"]
    assert ctl.grid_edges("f20_6") == ["n_crit=6"] and ctl.grid_edges("f40_10") == []
    assert sum(not ctl.grid_edges(g) for g in ctl.FEEDBACK) == 4


def test_a8_emergency_by_edge():
    lines = ["Warning: Vehicle 'main.17' performs emergency braking on lane '2_2' with decel=9.00, wished=1.50, "
             "severity=1.00, time=64.00.",
             "Warning: Vehicle 'main.9' performs emergency stop at the end of lane '2_3' because of a red traffic "
             "light (decel=-21.59, offset=1.39), time=146.00.",
             "Warning: Vehicle 'main.37' performs emergency braking on lane '4_1' with decel=9.00, wished=1.50, "
             "severity=1.00, time=152.00.",
             "Warning: Vehicle 'x' performs emergency braking on lane '5_0' with decel=9.00, wished=1.50, "
             "severity=1.00, time=400.00.",
             "Warning: Teleporting vehicle 'y'; waited too long (jam), lane='4_1', time=300.00."]
    e = episode.emergency_by_edge(lines, 150.0, 300.0)
    assert e == {"all": {"2": 2, "4": 1, "5": 1}, "incident": {"4": 1}}
    assert episode.emergency_by_edge(lines)["incident"] == {}
    r = {"emergency_by_edge": e}
    assert rs.eb_counts(r) == {"meter_e2": 2, "bottleneck_e45": 2, "bottleneck_e45_incident": 1}
    assert rs.eb_counts({})["meter_e2"] is None


def test_a9_tcheck_record_blocks_reruns(tmp_path):
    rec = tmp_path / "D2_TCHECK_RECORD.json"
    rs.check_tcheck_record("c1", record=rec)                                   # nothing recorded yet
    tc = lambda t0, t1, t3, t4: {"pass": t0 and t1 and t3 and t4, "T0": {"pass": t0}, "T1": {"pass": t1},
                                 "T3_pass": t3, "T4": {"pass": t4}}
    rs.append_tcheck_record(tmp_path / "a", "c1", "sha", tc(True, True, False, False), "FIX CODE", record=rec)
    with pytest.raises(SystemExit):
        rs.check_tcheck_record("c1", record=rec)                               # T3 failed: same commit refused
    rs.check_tcheck_record("c2", record=rec)                                   # after a fix: allowed
    rs.append_tcheck_record(tmp_path / "b", "c2", "sha", tc(True, False, True, True), "STOP (tool check T1; ...)",
                            record=rec)
    with pytest.raises(SystemExit):
        rs.check_tcheck_record("c2", record=rec)
    rs.check_tcheck_record("c3", record=rec)
    rs.append_tcheck_record(tmp_path / "c", "c3", "sha", tc(True, True, True, False), "STOP (tool check T4)", record=rec)
    for c in ("c3", "c4"):
        with pytest.raises(SystemExit):
            rs.check_tcheck_record(c, record=rec)                              # T0 / T4 STOP is final
    assert len(json.loads(rec.read_text())) == 3
    assert rs.TCHECK_RECORD.parent == rs.SENTINEL.parent
    ok = tmp_path / "ok.json"
    rs.append_tcheck_record(tmp_path / "d", "c1", "sha", tc(True, True, True, True), "PASS", record=ok)
    rs.check_tcheck_record("c1", record=ok)                                    # a pass does not block a resume


def test_a10_tree_change_stops_the_screen(monkeypatch, tmp_path):
    state = {"rev-parse": "aaa", "status": "", "diff": ""}
    monkeypatch.setattr(rs, "_git", lambda *a: state[a[0]])
    verify = rs.make_verify(rs.tree_state(), log=lambda m: None)
    verify("stage-1")                                                          # unchanged: fine
    state["diff"] = "edited"
    with pytest.raises(SystemExit):
        verify("stage-2")
    state.update(diff="", **{"rev-parse": "bbb"})
    with pytest.raises(SystemExit):
        verify("stage-3")
    called = []
    pool = rs.Pool(tmp_path, 1, 0.70, log=lambda m: None, verify=called.append)
    pool.run([], "tcheck-A")
    assert called == ["tcheck-A"]


def test_a10_cpu_limit_default_is_the_author_limit():
    assert rs.build_parser().parse_args(["--out", "x"]).cpu_limit == 0.70 == rs.CPU_LIMIT_DEFAULT
