"""CORR2 network build checks (vsl_lab/netgen/corr2.py): the net builds from scratch, lane counts and nominal
lengths are right, the mainline is never signalised (each meter TLS controls exactly its ramp link), and every
detector exists on an existing lane and loads in SUMO.

Run:
    unset SUMO_HOME; /home/catalin/work/phd/phd_speed_harmo_v6_toolchain/venv314/bin/python -m pytest \
        tests/test_corr2_build.py -v
"""
from __future__ import annotations

import json
import subprocess
import xml.etree.ElementTree as ET

import pytest

from vsl_lab.config import SUMO_BIN, clean_sumo_env
from vsl_lab.netgen import corr2 as N


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    """Fresh build into a temporary cache (the shared NET_CACHE is not touched)."""
    tmp = tmp_path_factory.mktemp("corr2_cache")
    orig = N.NET_CACHE
    N.NET_CACHE = tmp
    try:
        d = N.build(force=True)
    finally:
        N.NET_CACHE = orig
    return d


def _net_root(d):
    return ET.parse(d / "corr2.net.xml").getroot()


def test_net_builds(built):
    for fn in ("corr2.net.xml", "corr2.det.add.xml", "lanes.json", "spec.json"):
        assert (built / fn).exists(), fn


def test_lane_counts_and_lengths(built):
    chk = N.check_net(built / "corr2.net.xml")
    for e, n in N.N_LANES.items():
        assert chk["n_lanes"][e] == n, e
    for e in ("merge1", "merge2"):
        assert chk["n_lanes"][e] == 4
    for e in ("R1", "R1o", "R2", "R2o", "O1"):
        assert chk["n_lanes"][e] == 1, e
    lanes = json.loads((built / "lanes.json").read_text())
    for e, x0, x1, n in N.SPEC["main"]:
        for i in range(n):
            assert lanes[f"{e}_{i}"] == pytest.approx(x1 - x0, abs=0.01), (e, i)
    assert lanes["R1_0"] == pytest.approx(400.0, abs=0.01) and lanes["R2_0"] == pytest.approx(400.0, abs=0.01)
    assert lanes["R1o_0"] == pytest.approx(200.0, abs=0.01) and lanes["O1_0"] == pytest.approx(300.0, abs=0.01)


def test_connections(built):
    con = {(c.get("from"), c.get("to"), int(c.get("fromLane")), int(c.get("toLane")))
           for c in _net_root(built).iter("connection") if not c.get("from").startswith(":")}
    for m, up, dn in (("merge1", "m2", "m3"), ("merge2", "m5", "m6")):
        assert not any(c[0] == m and c[2] == 0 for c in con), f"{m} lane 0 must end (acceleration lane)"
        for i in range(3):
            assert (up, m, i, i + 1) in con and (m, dn, i + 1, i) in con
    assert ("R1", "merge1", 0, 0) in con and ("R2", "merge2", 0, 0) in con
    assert ("m3", "O1", 0, 0) in con and not any(c[0] == "m3" and c[1] == "O1" and c[2] > 0 for c in con)
    for i in range(3):
        assert ("m3", "m4", i, i) in con


def test_no_mainline_tls(built):
    chk = N.check_net(built / "corr2.net.xml")
    assert chk["main_controlled"] == []
    assert chk["tls_ids"] == sorted(N.TLS.values())
    assert chk["tl_links"] == {N.TLS["R1"]: [("R1", "merge1", "0", "0")], N.TLS["R2"]: [("R2", "merge2", "0", "0")]}
    root = _net_root(built)
    tl_junctions = sorted(j.get("id") for j in root.iter("junction") if j.get("type") == "traffic_light")
    assert tl_junctions == ["nm1", "nm2"]
    for tl in root.iter("tlLogic"):
        assert all(len(ph.get("state")) == 1 for ph in tl.iter("phase")), tl.get("id")
    add = ET.parse(built / "corr2.det.add.xml").getroot()
    ag = {t.get("id"): [p.get("state") for p in t.iter("phase")] for t in add.iter("tlLogic")}
    assert ag == {N.TLS["R1"]: ["G"], N.TLS["R2"]: ["G"]}


def test_detectors_exist(built):
    lanes = json.loads((built / "lanes.json").read_text())
    add = ET.parse(built / "corr2.det.add.xml").getroot()
    det = {el.get("id"): el for el in add if el.tag in ("inductionLoop", "laneAreaDetector")}
    want = [f"e1_{e}_{i}" for e in N.MAIN_EDGES for i in range(N.N_LANES[e])]
    want += [f"e1a_{e}_{i}" for e in N.ALINEA_LOOPS.values() for i in range(3)]
    want += [f"e1_{r}{k}_0" for r in N.RAMPS for k in ("in", "out")] + ["e1_O1_0"]
    want += [f"e2_{r}_0" for r in N.RAMPS] + [f"e2_{r}o_0" for r in N.RAMPS]
    missing = [w for w in want if w not in det]
    assert not missing, missing
    for k, el in det.items():
        assert el.get("lane") in lanes, k
        pos = float(el.get("pos"))
        assert 0.0 <= pos <= lanes[el.get("lane")], k
    for e in N.ALINEA_LOOPS.values():
        for i in range(3):
            assert float(det[f"e1a_{e}_{i}"].get("pos")) == pytest.approx(40.0)
            assert float(det[f"e1a_{e}_{i}"].get("period")) == pytest.approx(60.0)
    for r in N.RAMPS:
        assert float(det[f"e2_{r}_0"].get("length")) == pytest.approx(lanes[f"{r}_0"])


def test_sumo_loads(built, tmp_path):
    """SUMO loads net + additional (detectors, all-green programs) without errors (1 s, no vehicles)."""
    log = tmp_path / "load.log"
    r = subprocess.run([SUMO_BIN, "-n", str(built / "corr2.net.xml"), "-a", str(built / "corr2.det.add.xml"),
                        "--end", "1", "--no-step-log", "true", "--log", str(log)],
                       env=clean_sumo_env(), capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr[-1000:]
    assert "Error" not in log.read_text()
