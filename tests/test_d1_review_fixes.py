"""Screen D1 review fixes, Addendum (2026-10-19) A1-A7 of docs/research/protocols/screen_D1_detector_faults.md.
Each test fails on the code of 70d9a65 (no SUMO)."""
import json
from types import SimpleNamespace

import numpy as np
import pytest

from v5b.d1 import run_screen as rs
from v5b.d1 import stats
from v5b.d1.faults import ANY, FAULTS, fill_diagnostics


def _rng(k=0):
    return np.random.default_rng(2000 + k)


# A1: FX grid and the grid-edge halt
def test_fx_grid_is_100_step_superset_of_build_grid():
    build = {600.0, 800.0, 1000.0, 1200.0, 1400.0, 1600.0, 2000.0, 2400.0}
    g = rs.FX_GRID
    assert build <= set(g) and len(g) == len(set(g)) == 19
    assert {1700.0, 1800.0, 1900.0, 2100.0, 2600.0} <= set(g) and (min(g), max(g)) == (600.0, 2600.0)


def test_grid_edge_hits():
    g = rs.FX_GRID
    assert rs.grid_edge_hits({"1600": 1900.0, "2000": 1800.0}, g) == []
    assert rs.grid_edge_hits({"1600": 2600.0, "2000": 600.0}, g) == ["1600", "2000"]


# A2: HF against every fallback
def test_cell_fails_when_hl_closes_the_gap():
    o = 100 + _rng(1).normal(0, 2, 50)
    c = stats.headroom_cell(o, {"FX": o + 40, "RF": o + 60, "HL": o + 3})
    assert c["best"] == "FX" and c["rule5_pass"]           # the build's Rule 5 alone would pass
    assert c["binding"] == "HL" and not c["per_fallback"]["HL"]["pass"] and not c["pass"]
    c2 = stats.headroom_cell(o, {"FX": o + 40, "RF": o + 60, "HL": o + 30})
    assert c2["pass"]


# A5: invalid seeds
def test_cell_must_pass_without_invalid_seeds():
    o = np.r_[np.full(10, 50.0), np.full(10, 100.0)]        # the 10 low-delay O runs are invalid (biased low)
    fb = {"FX": np.full(20, 110.0), "RF": np.full(20, 130.0), "HL": np.full(20, 115.0)}
    inv = [True] * 10 + [False] * 10
    c = stats.cell_with_invalid_check(o, fb, inv)
    assert c["pass_all_seeds"] and not c["pass_valid_only"] and not c["pass"] and c["n_invalid_seeds"] == 10
    assert stats.cell_with_invalid_check(o, fb, [False] * 20)["pass"]
    assert not stats.cell_with_invalid_check(o, fb, [True] * 20)["pass"]


def _fake_res(sp, delay):
    return {s["key"]: {"delay_s": delay(s), "valid": True, "served_ctrl_vph": 1.0, "ttt_ctrl_vehh": 1.0,
                       "ttt_full_vehh": 1.0, "teleports": 0} for s in sp}


def test_build_cells_uses_nv_dropout_as_hl():
    sp = rs.eval_specs({"1600": 1900.0, "2000": 1800.0}, {"1600": 1.8, "2000": 1.9}, False, 20.0, 8.0)
    base = {"O": 100.0, "FX": 150.0, "RF": 160.0, "NC": 300.0}
    jit = lambda s: (s["seed"] % 7) * 0.1

    def delay(s):
        if s["arm"] == "NV":
            return (103.0 if s["fault"] == "dropout" else 400.0) + jit(s)
        return base[s["arm"]] + jit(s)

    idx = {(s["arm"], s["fault"], s["q"], s["seed"]): s["key"] for s in sp}
    cells, opmap = rs.build_cells(_fake_res(sp, delay), idx, False)
    assert set(cells) == {f"{f}_q{q}" for f in FAULTS for q in (1600, 2000)}
    for name, c in cells.items():
        assert c["rule5_pass"] and c["binding"] == "HL" and not c["pass"], name
        assert opmap[name]["arms"]["HL"]["median_delay_s"] == pytest.approx(103.3, abs=0.31)
    assert stats.decide(cells) == "STOP"


# A3: RF fill diagnostics
def test_fill_diagnostics():
    r = _rng(3)
    up = r.integers(0, 10, 500).astype(float)
    good = fill_diagnostics(2.0, up, 2.0 * up + r.normal(0, 0.1, 500))
    assert good["informative"] and good["corr"] > 0.99
    bad = fill_diagnostics(2.0, up, r.integers(0, 20, 500).astype(float))   # unrelated downstream count
    assert not bad["informative"] and abs(bad["corr"]) < 0.2 and bad["rmse"] >= bad["sd_down"]


# A6: run once across --out dirs, fixed meter law, reuse only identical runs
def test_sentinel_run_once(monkeypatch, tmp_path):
    sen = tmp_path / "D1_EVAL_STARTED.json"
    out_a, out_b = tmp_path / "a", tmp_path / "b"
    rs.check_sentinel(out_a, False, "c1", sen)                  # no sentinel yet
    rs.write_sentinel(out_a, "c1", "sha", {"x": 1}, sen)
    assert json.loads(sen.read_text())["out"] == str(out_a.resolve())
    with pytest.raises(SystemExit):
        rs.check_sentinel(out_b, True, "c1", sen)               # new tag: refused
    with pytest.raises(SystemExit):
        rs.check_sentinel(out_a, False, "c1", sen)              # same out without --resume: refused
    with pytest.raises(SystemExit):
        rs.check_sentinel(out_a, True, "c2", sen)               # resume across a code change: refused
    rs.check_sentinel(out_a, True, "c1", sen)                   # valid resume
    rs.write_sentinel(out_a, "c1", "sha", {"x": 2}, sen)        # kept as written
    assert json.loads(sen.read_text())["args"] == {"x": 1}
    assert rs.SENTINEL.parent.as_posix() == "/home/catalin/work/phd/v5b1_runs"


def test_screen_args_fix_the_meter_law():
    rs.check_screen_args(SimpleNamespace(kf=20.0, ncrit=8.0))
    for kf, nc in ((25.0, 8.0), (20.0, 6.0)):
        with pytest.raises(SystemExit):
            rs.check_screen_args(SimpleNamespace(kf=kf, ncrit=nc))


def test_reuse_refuses_other_config(monkeypatch, tmp_path):
    s = rs.spec("O", ANY, 1600.0, 7_400_100, kf=20.0, ncrit=8.0)
    stored = {k: s[k] for k in ("arm", "fault", "q", "seed", "q_fx", "ratio", "kf", "ncrit")}
    stored["code_commit"] = "c1"
    assert rs.reuse_mismatch(stored, s, "c1") == []
    assert rs.reuse_mismatch(dict(stored, kf=25.0, ncrit=6.0), s, "c1") == ["kf", "ncrit"]
    assert rs.reuse_mismatch(stored, s, "c2") == ["code_commit"]
    pool = rs.Pool(tmp_path, 1, 0.7, lambda m: None, commit="c2")
    (tmp_path / "runs" / f"{s['key']}.json").write_text(json.dumps(stored))
    with pytest.raises(SystemExit):
        pool.run([s], "test")
    pool.commit = "c1"
    res, failed = pool.run([s], "test")
    assert s["key"] in res and failed == []


# A7: the page of record
def test_page_renamed_approved_with_addendum():
    page = (rs.REPO_ROOT / rs.PAGE).read_text()
    assert rs.PAGE.endswith("screen_D1_detector_faults.md")
    assert "Status: **APPROVED (V89); addenda below.**" in page and "## Addendum (2026-10-19)" in page
    assert not (rs.REPO_ROOT / "docs/research/protocols/screen_D1_detector_faults_draft.md").exists()


def test_summary_renders_eval_and_halt():
    sp = rs.eval_specs({"1600": 1900.0, "2000": 1800.0}, {"1600": 1.8, "2000": 1.9}, False, 20.0, 8.0)
    res = _fake_res(sp, lambda s: 100.0 + s["seed"] % 5 + (40.0 if s["arm"] != "O" else 0.0))
    res[next(k for k in res if k.startswith("O_"))]["valid"] = False
    idx = {(s["arm"], s["fault"], s["q"], s["seed"]): s["key"] for s in sp}
    cells, opmap = rs.build_cells(res, idx, False)
    t0 = {"med_treat": 1.0, "med_base": 2.0, "rel": 0.5, "diff_ci": [0.5, 1.5], "pass": True}
    fill = {"rmse": 3.0, "sd_down": 2.5, "corr": 0.1, "informative": False, "n": 10}
    result = {"decision": stats.decide(cells), "page_sha256": "0" * 64, "code_commit": "c" * 40, "code_dirty": False,
              "args": {"literal": False},
              "tcheck": {"T0": {"1600": t0, "2000": t0}, "T1": {"n_with_teleports": 0, "n_runs": 90, "pass": True},
                         "T3_pass": True, "T3": {}},
              "tune": {"q_fx": {"1600": 1900.0, "2000": 1800.0}, "grid": list(rs.FX_GRID), "grid_edge": [],
                       "ratio": {"1600": 1.8, "2000": 1.9}, "rf_fill": {"1600": fill, "2000": fill}},
              "eval": {"cells": cells, "operating_map": opmap}}
    md = rs.summary_md(result)
    assert "| HL |" in md and "2 independent cells" in md and "RF uninformative" in md
    assert sum(c["n_invalid_seeds"] for c in cells.values()) == 4          # one O run, shared by the 4 fault cells of its demand
    halt = dict(result, decision="HALT (extend FX grid)")
    del halt["eval"]
    assert "HALT" in rs.summary_md(halt)
