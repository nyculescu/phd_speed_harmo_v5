"""C1 confirmation (c1_confirm.md, V527): the planted rows of §5, the chord weight and units, the stages."""
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "docs/research/c1"))
sys.path.insert(0, str(ROOT / "docs/research/planb"))
import c1  # noqa: E402
import read_cf as rf  # noqa: E402


def t(pt, lo, hi, ok=True):
    return {"pt": pt, "lo": lo, "hi": hi, "null_ok": ok}


def comp(E, Dpt=-0.5, Dlo=-1.0):
    return {"E": E, "D": {"pt": Dpt, "lo": Dlo}}


def x(competitors, chords=(), void=(), p0=True):
    return {"void": list(void), "p0": p0, "competitors": competitors, "chords": list(chords)}


def ch(q, r, test):
    return {"q": q, "r": r, **test}


def out(*a, **k):
    return rf.decide(x(*a, **k))["outcome"]


def test_planted_outcomes():
    good = {"p333": comp(t(30, 25, 35)), "lr": comp(t(20, 10, 30))}
    assert out(good, [ch("p333", "3E", t(28, 24, 33))]) == "PASS"
    assert out(good | {"os": comp(t(2, -1, 4))}) == "KILL"
    assert out(good, [ch("p333", "3E", t(2, -1, 4))]) == "KILL"
    assert out(good | {"os": comp(t(2, -1, 4), Dpt=1.5, Dlo=0.8)}) == "UNRESOLVED"     # MATCHED AT A DELAY COST
    assert out(good | {"os": comp(t(6, -2, 14))}) == "UNRESOLVED"
    assert out({}) == "UNRESOLVED"     # no competitor: never PASS
    assert out(good, p0=False) == "P0 FAILS"
    assert out(good | {"os": comp(t(2, -1, 4))}, void=["x"]) == "VOID"
    assert out(good | {"os": comp(t(2, -1, 4))}, p0=False) == "P0 FAILS"


def test_failed_null_reads_unresolved_whatever_it_read():
    good = {"p333": comp(t(30, 25, 35))}
    assert out(good | {"os": comp(t(2, -1, 4, ok=False))}) == "UNRESOLVED"
    assert out(good | {"os": comp(t(20, 10, 30, ok=False))}) == "UNRESOLVED"
    assert out(good | {"os": comp(t(2, -1, 4, ok=False)), "z": comp(t(1, -2, 3))}) == "KILL"     # a MATCHED elsewhere still kills


def setup(n=480, seed=0, d_p333=-0.9, d_r=2.6, cf=None):
    """Synthetic E30: v3w's learners at delay 100, p333 faster by d_p333 %, r slower by d_r %."""
    rng = np.random.default_rng(seed)
    rf.ARR.clear()
    base = 166_000.0
    for w in rf.V3W:
        rf.ARR[(w, "all_delay")] = base + rng.normal(0, 300, n)
        rf.ARR[(w, "ttc_net")] = 1030 + rng.normal(0, 60, n)
    cf = cf or {"p333": 1600.0, "r": 1400.0}
    for a, d in (("p333", d_p333), ("r", d_r)):
        rf.ARR[(a, "all_delay")] = base * (1 + d / 100.0) + rng.normal(0, 300, n)
        rf.ARR[(a, "ttc_net")] = cf[a] + rng.normal(0, 60, n)
    rf.CTX.update(idx=np.random.default_rng(1).integers(0, n, (2000, n)), pct=rf.MAIN["pct"], lv=rf.MAIN)


def test_chord_weight_and_edge():
    setup()
    c = rf.chord("p333", "r")
    assert c["w"] == pytest.approx(0.9 / (0.9 + 2.6 * (1 - 0.009)), abs=0.03)     # m_q / (m_q + m_r) on absolute delays
    mix = (1 - c["w"]) * 1600 + c["w"] * 1400
    assert c["pt"] == pytest.approx((mix - 1030) / mix * 100, abs=1.0)
    assert 0 <= c["w_ci"][0] <= c["w_ci"][1] <= 1


def test_chord_ends_equal_the_rule_edges_in_their_own_units():
    setup(d_p333=0.5, d_r=2.6)     # both slower: clamps to the nearer end, p333
    c = rf.chord("p333", "r")
    e = rf.edge("p333", "ttc_net")
    assert c["w"] == 0.0 and c["pt"] == pytest.approx(e["pt"], abs=1e-9)
    setup(d_p333=-0.9, d_r=-0.3)     # both faster: the nearer end is r
    c = rf.chord("p333", "r")
    assert c["w"] == 1.0 and c["pt"] == pytest.approx(rf.edge("r", "ttc_net")["pt"], abs=1e-9)
    assert rf.weight(np.array([0.0]), np.array([0.0]))[0] == 0.5


def test_null_rate_is_near_nominal_without_effect():
    rng = np.random.default_rng(3)
    D = [rng.normal(0, 10, 120) for _ in rf.V3W]
    r = rf.null_rate(D, 300, 400, rf.MAIN["pct"], 5)
    assert 0 <= r < 0.05


def test_ident_classes_mpcf_with_the_learners():
    ref = {"name": "S|MPC-F", "seed": 1, "all_delay": 5.0}
    S6 = {("S|MPC-F", 1): ref}
    rows = [{**ref, "all_delay": 5.1}]
    assert rf.ident(rows, S6, "AMD EPYC 7B13 64-Core Processor")["action"] == "go"
    assert rf.ident(rows, S6, "Intel(R) Xeon(R) Platinum 8163 CPU @ 2.50GHz")["action"] == "stop"
    assert rf.rc.V3W == rf.V3W     # restored


def test_stages(tmp_path):
    s = c1.plan("cf_screen", tmp_path)
    assert s["seed_range"] == [7_489_160, 7_489_639] and len(s["arms"]) == 31
    assert s["arms"]["E30|p222"]["ctrl"]["cav_rule"] == [2, 2, 2]
    assert s["arms"]["E30|MPC-F"]["ctrl"]["mpcf"]["model"].startswith(c1.MPCF_NEW)
    i = c1.plan("cf_ident", tmp_path)["arms"]
    assert len(i) == 29 and i["S|MPC-F"]["ctrl"]["mpcf"]["model"].startswith(c1.MPCF_NEW) and "split" not in i["S|p333"]
    sm = c1.plan("cf_smoke", tmp_path)["arms"]
    assert "E30|p111~untraced" in sm and sm["E30|nc~trace"]["t0_event"]
    for a, b in ((7_489_160, 7_489_639), (7_489_640, 7_489_640)):
        assert all(not (lo <= a <= hi) for k, (lo, hi) in c1.STAGES.items() if not k.startswith("cf_"))


def test_t0_uniform_level():
    row = {"tau_on_n": 10.0, "tau_on_match": 10.0, "tau_mismatch": 0.0, **{f"lv_sum_{r}": 20.0 * 0.98 for r in "2345"}, **{f"lv_n_{r}": 10.0 for r in "2345"}}
    A = {("E30|p222", 1): row}
    assert c1.t0_rows(A, {"E30|p222": {}})["bad"] == []
    A = {("E30|p111", 1): row}
    bad = c1.t0_rows(A, {"E30|p111": {}})["bad"]
    assert len(bad) == 1 and bad[0].startswith("T0 p111 level E30|p111 1")
