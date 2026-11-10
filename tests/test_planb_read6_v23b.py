"""read6 v2.3, amendment 5a: coverage tests from the review of v2.3. The code at 09f49ad has each behaviour; each test fails on a mutant
the review ran (planb_s6_review_v23/review/mutants.log, mutants2.log: N1, N3-N11, V1-V3). The last test is for read6_superset.py."""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "docs/research/planb"))
sys.path.insert(0, str(ROOT))
import read6_regress  # noqa: E402
from test_planb_read6 import cfg, r6  # noqa: E402
from test_planb_read6_v22 import JAM, P333, X, gate, jam_world, main_world, picks_files, st_row  # noqa: E402
from v5b.fleet import measure  # noqa: E402

REAL_WAVES = measure.waves


def capped_fields(path: Path, shape=(12, 20), extra=None) -> dict:
    """3 vehicles a cell at 100 km/h, a 3 x 3 jam at 20 km/h, and time bins 7-9 where 2 capped trucks at 20 km/h ride with one car at
    100 km/h. Without the trucks (v_nc, n_nc) those cells hold the car alone, at 100 km/h."""
    kmh = np.full(shape, 100.0)
    kmh[2:5, 3:6] = 20.0
    n = np.full(shape, 3.0)
    v = kmh / 3.6 * n
    v[7:10, :] = (2 * 20.0 + 100.0) / 3.6
    v_nc, n_nc = v.copy(), n.copy()
    v_nc[7:10, :], n_nc[7:10, :] = 100.0 / 3.6, 1.0
    f = {k: x.astype(np.float32) for k, x in (("v", v), ("n", n), ("v_nc", v_nc), ("n_nc", n_nc))} | (extra or {})
    np.savez_compressed(path, **f)
    return f


def row_for(f: dict, name="k.npz", dt=10.0, dx=50.0) -> dict:
    (cv, cr), (cvn, crn) = measure.congestion(f["v"], f["n"], dt, dx), measure.congestion(f["v_nc"], f["n_nc"], dt, dx)
    return st_row(f=name, shape=f["v"].shape) | {"m_st_dt": dt, "m_st_dx": dx, "m_cong_vs": cv, "m_cong_run_s": cr, "m_cong_vs_nc": cvn,
                                                 "m_cong_run_s_nc": crn}


def test_coverage_the_nc_field_uses_its_own_counts(tmp_path):
    """N1: waves and congestion on (v_nc, n_nc), not (v_nc, n)."""
    f = capped_fields(tmp_path / "k.npz")
    d = r6.derive(row_for(f), tmp_path)
    right, wrong = measure.waves(f["v_nc"], f["n_nc"], 10.0, 50.0), measure.waves(f["v_nc"], f["n"], 10.0, 50.0)
    assert right["congested_share"] != wrong["congested_share"]
    assert {k: d[f"{k}_nc"] for k in JAM} == {k: right[k] for k in JAM}
    assert d["bind"]["run_s_nc_equal"] and d["bind"]["vs_nc_rel"] == 0.0


@pytest.mark.parametrize("bad", ["n", "n_nc", "v_nc"])
def test_coverage_every_array_must_have_the_rows_shape(tmp_path, bad):
    """N3, V3: n, v_nc and n_nc are each checked against v and the row's shape."""
    f = capped_fields(tmp_path / "k.npz")
    f[bad] = np.ones((12, 21), np.float32)
    np.savez_compressed(tmp_path / "k.npz", **f)
    with pytest.raises(SystemExit):
        r6.derive(row_for(capped_fields(tmp_path / "ok.npz")), tmp_path)     # the row names k.npz


def test_coverage_front_none_comes_from_the_main_field(tmp_path):
    """N6, N6b: the main field has no jam (front None) while the _nc field has one."""
    v = np.full((12, 20), 3 * 100.0 / 3.6, np.float32)
    n = np.full((12, 20), 3.0, np.float32)
    v_nc = v.copy()
    v_nc[2:6, 3:6] = 3 * 20.0 / 3.6
    f = {"v": v, "n": n, "v_nc": v_nc, "n_nc": n}
    np.savez_compressed(tmp_path / "k.npz", **f)
    assert REAL_WAVES(v, n, 10.0, 50.0)["front_kmh_median"] is None and REAL_WAVES(v_nc, n, 10.0, 50.0)["front_kmh_median"] is not None
    assert r6.derive(row_for(f), tmp_path)["front_none"] is True


def test_coverage_front_none_counts_only_true():
    """N11: rows with front_none False are not counted."""
    T = jam_world()
    for s, x in ((0, True), (1, True), (2, False), (3, False), (4, False)):
        T[("X", "p333")][s]["front_none"] = x
    assert r6.read(T, cfg() | {"st_dir": "st"})["space_time"]["front_none_rows"] == 2


def test_coverage_measure_is_this_trees_file_even_behind_another_v5b(tmp_path, monkeypatch):
    """N7: a v5b earlier on sys.path, whose waves returns constants, is not used."""
    fake = tmp_path / "fake" / "v5b" / "fleet"
    fake.mkdir(parents=True)
    (fake.parent / "__init__.py").write_text("")
    (fake / "__init__.py").write_text("")
    (fake / "measure.py").write_text("def waves(*a, **k):\n    return dict.fromkeys(('jam_share', 'congested_share', 'jams', 'congested_km_mean', "
                                     "'congested_km_max', 'osc_kmh', 'front_kmh_median'), 0.5)\n\n\ndef congestion(*a, **k):\n    return 0.0, 0.0\n")
    for m in [k for k in sys.modules if k == "v5b" or k.startswith("v5b.")]:
        monkeypatch.delitem(sys.modules, m)
    monkeypatch.syspath_prepend(str(tmp_path / "fake"))
    monkeypatch.setattr(r6, "_measure", [])
    f = capped_fields(tmp_path / "k.npz")
    d = r6.derive(row_for(f), tmp_path)
    assert d["jam_share"] == REAL_WAVES(f["v"], f["n"], 10.0, 50.0)["jam_share"] != 0.5


def test_coverage_binding_aggregates_both_fields():
    """N4, N5: an unequal run_s on the _nc field lists the file; the _nc relative difference counts in the maximum."""
    T = jam_world()
    T[("X", "lr")][3] |= {"st_file": "a.npz", "bind": {"run_s_equal": True, "vs_rel": 0.0, "run_s_nc_equal": False, "vs_nc_rel": 0.0}}
    T[("X", "lr")][4] |= {"st_file": "b.npz", "bind": {"run_s_equal": True, "vs_rel": 0.0, "run_s_nc_equal": True, "vs_nc_rel": 0.01}}
    b = r6.read(T, cfg() | {"st_dir": "st"})["space_time"]["binding"]
    assert b == {"rows": 2, "run_s_unequal": ["a.npz"], "vs_max_rel": 0.01}


def test_coverage_binding_uses_the_rows_dt_and_dx(tmp_path):
    """N8: with dt 20 and dx 25, congestion on measure's defaults would give another run length."""
    f = capped_fields(tmp_path / "k.npz")
    row = row_for(f, dt=20.0, dx=25.0)
    assert row["m_cong_run_s"] != measure.congestion(f["v"], f["n"])[1]
    assert r6.derive(row, tmp_path)["bind"]["run_s_equal"] is True


def test_coverage_nc_keys_name_their_none_cause():
    """N9."""
    T = jam_world()
    for rows in T.values():
        for b in rows.values():
            b |= {f"{k}_nc": b[k] for k in JAM}
    T[("X", "w0")][2]["jam_share_nc"] = None
    m = r6.read(T, cfg() | {"st_dir": "st"})["cells"]["X"]["map_report_only"]["p333"]
    assert m["jam_share_nc"]["why"] == r6.NONE_WHY["jam_share"] and m["jam_share"]["effect"] is not None


def test_coverage_mechanism_g_is_per_cell(tmp_path, monkeypatch):
    """N10: a forms file with another cell's mechanism G carries only the reading's cells."""
    conf = main_world(tmp_path, monkeypatch)
    p, f = picks_files(tmp_path)
    rep = json.loads(Path(f).read_text()) | {"mechanism_G": {"X": {"differs": True}, "Y": {"differs": False}}}
    Path(f).write_text(json.dumps(rep))
    out = tmp_path / "o.json"
    r6.main(["rows", conf, str(out), "--seeds", "0-59", "--picks", p, "--forms", f])
    assert json.loads(out.read_text())["provenance"]["mechanism_G"] == {"X": {"differs": True}}


def test_coverage_gate_hidden_needs_a_failed_null_ok():
    """V1: an opponent with no null_ok is not hidden, so its changed R is reported."""
    def edit(a, b):
        P333(a).pop("null_ok")
        P333(b).pop("null_ok")
        P333(b).update(R=read6_regress.FAILED, pct_of_nc_loss=None)
    assert sorted(x.split(":")[0] for x in gate(edit)) == ["cells.X.resilience.per_opponent.p333.R", "cells.X.resilience.per_opponent.p333.pct_of_nc_loss"]


def test_coverage_gate_r_allowance_only_under_resilience():
    """V2: the same keys under another block are compared."""
    def edit(a, b):
        blk = {"per_opponent": {"p333": {"R": [1.0, 0.5, 2.0], "pct_of_nc_loss": 4.0, "null_ok": 0.0}}}
        X(a)["other"] = json.loads(json.dumps(blk))
        X(b)["other"] = blk
        blk["per_opponent"]["p333"].update(R=read6_regress.FAILED, pct_of_nc_loss=None)
    assert sorted(x.split(":")[0] for x in gate(edit)) == ["cells.X.other.per_opponent.p333.R", "cells.X.other.per_opponent.p333.pct_of_nc_loss"]


def test_superset_check(tmp_path):
    """read6_superset.py: every leaf of the older output is in the newer one with the same value; report_version may differ."""
    old = {"report_version": "2.2", "a": {"x": 1.0, "y": [0.0, None]}, "b": "T"}
    cases = {"same, keys added": (dict(old, report_version="2.3", c=5) | {"a": {**old["a"], "z": 2}}, 0),
             "a changed leaf": (dict(old, a={"x": 1.0000000001, "y": [0.0, None]}), 1),
             "-0.0": (dict(old, a={"x": 1.0, "y": [-0.0, None]}), 1),
             "a missing key": ({k: v for k, v in old.items() if k != "b"}, 1),
             "a type change": (dict(old, a={"x": 1, "y": [0.0, None]}), 1)}
    o = tmp_path / "old.json"
    o.write_text(json.dumps(old))
    for name, (new, rc) in cases.items():
        n = tmp_path / "new.json"
        n.write_text(json.dumps(new))
        p = subprocess.run([sys.executable, str(ROOT / "docs/research/planb/read6_superset.py"), str(o), str(n)], capture_output=True, text=True)
        assert p.returncode == rc, (name, p.stdout)
