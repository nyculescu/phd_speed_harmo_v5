"""read6 v2.3 (read6_v2_spec.md amendment 5): fixes from the review of v2.2. Written before the fix; each test fails on edebc7b,
except the coverage tests marked so, which pin behaviour edebc7b already has (each fails on a mutant the review ran)."""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "analysis/planb"))
sys.path.insert(0, str(ROOT))
import read6_regress  # noqa: E402
from test_planb_read6 import LEARN, N, OPP, cfg, r6, world  # noqa: E402
from test_planb_read6_v2 import with_report_keys  # noqa: E402
from test_planb_read6_v21 import universe_world  # noqa: E402
from test_planb_read6_v22 import JAM, P333, X, gate, jam_world, main_world, os1_world, picks_files, st_row  # noqa: E402
from v5b2.freeway import measures as measure  # noqa: E402


def two_fields(path: Path, nc: bool = True) -> tuple:
    """A field with a 3 x 3 jam and a 35 km/h strip that only a capped truck makes; v_nc/n_nc leave the strip out."""
    kmh = np.full((12, 10), 100.0)
    kmh[2:5, 3:6] = 20.0
    n = np.full((12, 10), 2.0)
    kmh_nc = kmh.copy()
    kmh[8, :] = 35.0
    v, v_nc = (kmh / 3.6 * n).astype(np.float32), (kmh_nc / 3.6 * n).astype(np.float32)
    n = n.astype(np.float32)
    side = {"v": v, "n": n} | ({"v_nc": v_nc, "n_nc": n} if nc else {})
    np.savez_compressed(path, **side)
    return v, n, v_nc


def bound_row(v, n, v_nc, f="k.npz", dt=10.0, dx=50.0) -> dict:
    cv, cr = measure.congestion(v, n, dt, dx)
    cvn, crn = measure.congestion(v_nc, n, dt, dx)
    return st_row(f=f) | {"m_st_dt": dt, "m_st_dx": dx, "m_cong_vs": cv, "m_cong_run_s": cr, "m_cong_vs_nc": cvn, "m_cong_run_s_nc": crn}


def test_jam_metrics_also_without_the_capped_trucks(tmp_path):
    v, n, v_nc = two_fields(tmp_path / "k.npz")
    d = r6.derive(bound_row(v, n, v_nc), tmp_path)
    w, w_nc = measure.waves(v, n, 10.0, 50.0), measure.waves(v_nc, n, 10.0, 50.0)
    assert {k: d[k] for k in JAM} == {k: w[k] for k in JAM}
    assert {k: d[f"{k}_nc"] for k in JAM} == {k: w_nc[k] for k in JAM} and d["congested_share"] > d["congested_share_nc"]
    v, n, _ = two_fields(tmp_path / "plain.npz", nc=False)     # no capped vehicle: the _nc keys are the field's own
    d = r6.derive(bound_row(v, n, v, f="plain.npz"), tmp_path)
    assert all(d[f"{k}_nc"] == d[k] for k in JAM)
    assert set(f"{k}_nc" for k in JAM) <= set(r6.REPORT_KEYS)


def test_front_speed_none_rows_are_counted(tmp_path):
    v, n, v_nc = two_fields(tmp_path / "k.npz")
    d = r6.derive(bound_row(v, n, v_nc), tmp_path)
    assert d["front_none"] is (measure.waves(v, n, 10.0, 50.0)["front_kmh_median"] is None)
    T = jam_world()
    for s in (0, 1):
        T[("X", "p333")][s]["front_none"] = True
    assert r6.read(T, cfg() | {"st_dir": "st"})["space_time"]["front_none_rows"] == 2


def test_each_side_file_is_bound_to_its_row(tmp_path):
    v, n, v_nc = two_fields(tmp_path / "k.npz")
    good = r6.derive(bound_row(v, n, v_nc), tmp_path)
    assert good["bind"] == {"run_s_equal": True, "vs_rel": 0.0, "run_s_nc_equal": True, "vs_nc_rel": 0.0}
    bad = r6.derive(bound_row(v, n, v_nc) | {"m_cong_run_s": 12345.0}, tmp_path)
    assert bad["bind"]["run_s_equal"] is False
    T = jam_world()
    T[("X", "lr")][3] |= {"st_file": "lr3.npz", "bind": bad["bind"]}
    T[("X", "lr")][4] |= {"st_file": "lr4.npz", "bind": good["bind"]}
    b = r6.read(T, cfg() | {"st_dir": "st"})["space_time"]["binding"]
    assert b == {"rows": 2, "run_s_unequal": ["lr3.npz"], "vs_max_rel": 0.0}


def test_measure_is_loaded_from_this_tree_and_recorded():
    m = ROOT / "v5b2/freeway/measures.py"
    sp = r6.read(with_report_keys(world()), cfg())["space_time"]
    assert sp["measure_file"] == str(m) and sp["measure_sha256"] == hashlib.sha256(m.read_bytes()).hexdigest()


def test_mechanism_g_is_carried_from_the_forms_file(tmp_path, monkeypatch):
    conf = main_world(tmp_path, monkeypatch)
    p, f = picks_files(tmp_path)
    rep = json.loads(Path(f).read_text()) | {"mechanism_G": {"X": {"vs_lowest_cf": {"all_delay": 2.7}, "differs": True}}}
    Path(f).write_text(json.dumps(rep))
    out = tmp_path / "o.json"
    r6.main(["rows", conf, str(out), "--seeds", f"0-{N - 1}", "--picks", p, "--forms", f])
    assert json.loads(out.read_text())["provenance"]["mechanism_G"] == {"X": {"vs_lowest_cf": {"all_delay": 2.7}, "differs": True}}


def test_gate_a_new_resilience_block_must_be_labelled_report_only():
    def put(blk, cell_v1_has=False):
        def edit(a, b):
            if not cell_v1_has:
                X(a).pop("resilience")
                X(b).pop("resilience")
            X(b)["cf_resilience"] = {"per_opponent": {}, "status": "report-only, not read"}
            if blk is not None:
                X(b)["resilience"] = blk
        return edit
    assert gate(put({"per_opponent": {}, "status": "report-only, not read"})) == []
    assert [x.split(":")[0] for x in gate(put({"per_opponent": {}, "status": "read"}))] == ["cells.X.resilience.status"]
    assert [x.split(":")[0] for x in gate(put({"per_opponent": {}}))] == ["cells.X.resilience.status"]
    d = gate(put({"per_opponent": {}, "status": "report-only, not read", "verdict": "passes", "pass": True}))
    assert sorted(x.split(":")[0] for x in d) == ["cells.X.resilience.pass", "cells.X.resilience.verdict"]
    assert [x.split(":")[0] for x in gate(lambda a, b: X(b).update(cf_resilience={"per_opponent": {}, "status": "read"}))] == ["cells.X.cf_resilience.status"]


def test_coverage_waves_take_the_rows_dt_and_dx(tmp_path):
    """Coverage: a row with dt 20 and dx 25 (not measure's defaults)."""
    v, n, v_nc = two_fields(tmp_path / "k.npz")
    d = r6.derive(bound_row(v, n, v_nc, dt=20.0, dx=25.0), tmp_path)
    assert d["congested_km_mean"] == measure.waves(v, n, 20.0, 25.0)["congested_km_mean"] != measure.waves(v, n)["congested_km_mean"]


def test_coverage_3e_intervals_are_95_percent_and_cf_uses_close_following():
    """Coverage: the exact 95 % bounds on the cell's index matrix; close-following against os1_15_10 reads ttc_net."""
    T, c = os1_world()
    for cond in ("X", "S"):
        for v in T[(cond, "os1_15_10")].values():
            v["ttc_net"] *= 1.05
    ex = r6.read(T, c)["cells"]["X"]["t2_counting_filter"]["excluded_3e"]["3e"]
    E, R = ({k: np.array([T[("X", n)][s][k] for s in range(N)]) for k in ("all_delay", "ttc_net")} for n in ("3e", "os1_15_10"))
    st = r6.Stat(N)
    for got, key in ((ex["vs_os1_15_10"]["delay"], "all_delay"), (ex["vs_os1_15_10"]["cf"], "ttc_net")):
        x, b = st.eff(E[key], R[key])
        assert list(got) == [x, *r6.ci(b, r6.P95)]
    assert ex["vs_os1_15_10"]["cf"][0] == pytest.approx(100.0 * (1.0 - 1.0 / 1.05), abs=1.5)


def test_coverage_policies_if_included_count_the_transfer_rules():
    """Coverage: 3ex2 is within the delay filter but far ahead on close-following, so it blocks every learner once included."""
    T, c = universe_world()
    for cond in ("X", "S"):
        T[(cond, "3ex2")] = {s: dict(v, all_delay=v["all_delay"] * 1.01, ttc_net=v["ttc_net"] * 0.7) for s, v in T[(cond, "p333")].items()}
    c["opponents"] = {"X": c["opponents"]["X"] + ["3ex2"]}
    f = r6.read(T, c)["cells"]["X"]["t2_counting_filter"]
    assert f["policies"] == 5 and "3ex2" in f["transfer_3e"]["counted_if_included"] and f["transfer_3e"]["policies_if_included"] == 0


def test_coverage_st_reaches_derive_through_load_rows_and_main(tmp_path, monkeypatch):
    """Coverage: load_rows passes its folder to derive; main passes --st to load_rows."""
    rows = tmp_path / "rows.jsonl"
    rows.write_text("".join(json.dumps({"name": f"X|{n}", "seed": 0}) + "\n" for n in ("w0", "p333")))
    seen = []
    monkeypatch.setattr(r6, "derive", lambda r, st=None: seen.append(st) or {})
    r6.load_rows(rows, cfg(), [0], tmp_path)
    assert seen == [tmp_path, tmp_path]
    got = {}
    monkeypatch.setattr(r6, "load_rows", lambda path, c, seeds, st=None: got.update(st=st) or {})
    monkeypatch.setattr(r6, "read", lambda *a, **k: {"cells": {}})
    conf = tmp_path / "c.json"
    conf.write_text(json.dumps(cfg()))
    (tmp_path / "st").mkdir()
    r6.main(["rows", str(conf), str(tmp_path / "o.json"), "--seeds", "0-1", "--st", str(tmp_path / "st")])
    assert got["st"] == (tmp_path / "st").resolve()


def test_coverage_main_input_checks(tmp_path, monkeypatch):
    """Coverage: --st must be a folder; the picks' cells must be the config's; a full run needs each of --picks, --forms, --st."""
    conf = main_world(tmp_path, monkeypatch)
    o = str(tmp_path / "o.json")
    p, f = picks_files(tmp_path)
    st = tmp_path / "st"
    st.mkdir()
    with pytest.raises(SystemExit, match="not a folder"):
        r6.main(["rows", conf, o, "--seeds", f"0-{N - 1}", "--st", str(tmp_path / "nothing")])
    for drop in ("--picks", "--forms", "--st"):
        args = {"--picks": p, "--forms": f, "--st": str(st)}
        args.pop(drop)
        with pytest.raises(SystemExit, match="full reading"):
            r6.main(["rows", conf, o, *[x for kv in args.items() for x in kv]])
    p2, _ = picks_files(tmp_path, repicks={"X": {"lr": {}, "p333": {}, "dly": {}}, "Y": {"p333": {}}})
    with pytest.raises(SystemExit, match="belong"):
        r6.main(["rows", conf, o, "--seeds", f"0-{N - 1}", "--picks", p2])


def test_coverage_gate_map_repeats_on_intervals_lengths_s_and_a_missing_block():
    """Coverage."""
    def mro(k, val):
        return lambda a, b: X(b)["map_report_only"]["p333"]["delay"].update({k: val})
    assert [x.split(":")[0] for x in gate(mro("ci95", [0.0, 2.5]))] == ["cells.X.map_report_only.p333.delay.ci95"]
    assert [x.split(":")[0] for x in gate(mro("ci95", [-0.0, 2.0]))] == ["cells.X.map_report_only.p333.delay.ci95"]     # map has 0.0
    assert [x.split(":")[0] for x in gate(mro("ci_m", [-0.5, 2.6]))] == ["cells.X.map_report_only.p333.delay.ci_m"]
    assert [x.split(":")[0] for x in gate(mro("ci95", [0.0, 2.0, 3.0]))] == ["cells.X.map_report_only.p333.delay.ci95"]

    def s_block(a, b):
        for blk in (a, b):
            blk["S"]["map"] = {"p333": {m: {"effect": 1.0, "ci95": [0.0, 2.0], "ci_m": [-0.5, 2.5]} for m in read6_regress.V1_MEASURES}}
        b["S"]["map_report_only"] = json.loads(json.dumps(b["S"]["map"]))
        b["S"]["map_report_only"]["p333"]["cf"]["effect"] = 1.5
    assert [x.split(":")[0] for x in gate(s_block)] == ["S.map_report_only.p333.cf.effect"]
    assert [x.split(":")[0] for x in gate(lambda a, b: X(b).pop("map_report_only"))] == ["cells.X.map_report_only"]


def test_coverage_gate_no_verdict_on_both_blocks_and_keys():
    """Coverage: a NOT_READ delay resilience block (new in v2) with passes, and cf_resilience with reading."""
    def edit(a, b):
        X(a).pop("resilience")
        X(b)["resilience"] = {"per_opponent": {}, "status": "report-only, not read", "passes": False}
        X(b)["cf_resilience"] = {"per_opponent": {}, "status": "report-only, not read", "reading": "not shown"}
    assert sorted(x.split(":")[0] for x in gate(edit)) == ["cells.X.cf_resilience.reading", "cells.X.resilience.passes"]


def test_coverage_gate_hidden_r_needs_its_pct_key():
    """Coverage."""
    def edit(a, b):
        P333(a)["null_ok"] = P333(b)["null_ok"] = 0.0
        P333(b)["R"] = read6_regress.FAILED
        P333(b).pop("pct_of_nc_loss")
    assert [x.split(":")[0] for x in gate(edit)] == ["cells.X.resilience.per_opponent.p333.pct_of_nc_loss"]
