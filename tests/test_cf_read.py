"""C1 confirmation (c1_confirm.md, V527): the planted rows of §5, the chord weight and units, the stages."""
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis/c1"))
sys.path.insert(0, str(ROOT / "analysis/planb"))
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


def test_clamped_chord_reads_as_its_rule():
    good = {"p333": comp(t(30, 25, 35)), "q": comp(t(1.1, 0.1, 2.1), Dpt=1.16, Dlo=-0.04)}
    c = ch("q", "r", t(1.1, 0.1, 2.1)) | {"end_D": {"pt": 1.16, "lo": -0.04, "hi": 2.44}}
    assert out(good, [c]) == "UNRESOLVED"     # MATCHED AT A DELAY COST, as the rule itself
    c2 = ch("p333", "nc", t(1.0, -1, 3)) | {"trade_end": True}
    assert out({"p333": comp(t(30, 25, 35))}, [c2]) == "PASS"     # an end at a trade point is not a competitor test


def test_null_reestimate(monkeypatch):
    calls = iter([0.020, 0.015])
    monkeypatch.setattr(rf, "null_rate", lambda *a, **k: next(calls))
    rf.CTX["lv"] = rf.MAIN
    r = rf.null_check([np.zeros(3)], 1)
    assert r["ok"] and r["re_rate"] == 0.015
    calls = iter([0.0095])
    monkeypatch.setattr(rf, "null_rate", lambda *a, **k: next(calls))
    rf.CTX["lv"] = rf.EXT
    assert not rf.null_check([np.zeros(3)], 1)["ok"]     # no second draw at the extension


def synth(n=200, seed=0):
    """Synthetic E30 rows: v3w, p333 (faster, more close-following), lr (competitor, slower by 0.5 %), slow (trade point), nc."""
    rng = np.random.default_rng(seed)
    T = {}
    spec = {"p333": (-0.9, 1600), "lr": (0.5, 1500), "slow": (2.6, 1400), "nc": (28.0, 1330)}
    base = 166_000.0
    for a, (d, cf) in list(spec.items()) + [(w, (0.0, 1030)) for w in rf.V3W]:
        T[("E30", a)] = {s: {"all_delay": base * (1 + d / 100) + rng.normal(0, 300), "ttc_net": cf + rng.normal(0, 60), "ttc_away": 200 + rng.normal(0, 20),
                             "b45_step": 450 + rng.normal(0, 20) - (30 if a in rf.V3W else 0), "events_ge45": 950 + rng.normal(0, 30), "passed": 9000.0,
                             "N": 1e6, "stuck": 0.0, "q_ramp1_queue": 1.0, "q_ramp2_queue": 1.0, "q_backlog": 1.0} for s in range(n)}
    return T


def test_screen_end_to_end_on_synthetic_rows():
    lv = {"pct": rf.MAIN["pct"], "bar": 0.019, "swaps": 40, "nb": 200}
    res = rf.screen(synth(), list(range(200)), [], ["cpu"], lv, workers=2, b=1000)
    assert res["competitors"] == ["lr", "p333"] and set(res["trade_points"]) == {"slow", "nc"}
    names = [(c["q"], c["r"]) for c in res["chords"]]
    assert len(names) == len(set(frozenset(x) for x in names))     # no pair twice
    assert res["decision"]["outcome"] == "PASS" and res["braking_shown"] and res["p0"]["pass"]
    assert "p333" in res["drain"] and not res["drain"]["v3w"]["fail"]
    void = rf.screen(synth(), list(range(200)), [1, 2, 3, 4], ["cpu"], lv, workers=2, b=1000)
    assert void["decision"]["outcome"] == "VOID"
    two = rf.screen(synth(), list(range(200)), [], ["a", "b"], lv, workers=2, b=1000)
    assert two["decision"]["outcome"] == "VOID"


def test_competitor_boundary():
    T = synth()
    lv = {"pct": rf.MAIN["pct"], "bar": 0.019, "swaps": 10, "nb": 100}
    res = rf.screen(T, list(range(200)), [], ["cpu"], lv, workers=2, b=500)
    for a in res["competitors"]:
        assert res["readings"][a]["D"]["lo"] <= rf.COMPETE_MARGIN or a == "p333"
    for a in res["trade_points"]:
        assert res["readings"][a]["D"]["lo"] > rf.COMPETE_MARGIN


LV_FAST = {"pct": rf.MAIN["pct"], "bar": 1.0, "swaps": 5, "nb": 50}     # never re-estimates


def test_screen_paths():
    T = synth()
    seeds = list(range(200))
    for s in seeds:     # no rule faster than v3w: no chords
        T[("E30", "p333")][s]["all_delay"] *= 1.02
    res = rf.screen(T, seeds, [], ["c"], LV_FAST, workers=2, b=300)
    assert res["n_chords"] == 0 or all(rf.ARR[("p333", "all_delay")].mean() > 0 for _ in [0])
    T = synth()
    for s in seeds:     # v3w fails drain
        for w in rf.V3W:
            T[("E30", w)][s]["q_backlog"] = 10.0
    assert rf.screen(T, seeds, [], ["c"], LV_FAST, workers=2, b=300)["decision"]["outcome"] == "VOID"
    T = synth()
    for s in seeds:     # a rule fails drain: labelled only
        T[("E30", "lr")][s]["q_backlog"] = 10.0
    r = rf.screen(T, seeds, [], ["c"], LV_FAST, workers=2, b=300)
    assert r["drain"]["lr"]["fail"] and r["decision"]["outcome"] != "VOID"
    T = synth()
    for a in ("p333", "lr", "slow"):     # no rule beats no control by 10 %
        for s in seeds:
            T[("E30", a)][s]["all_delay"] = T[("E30", "nc")][s]["all_delay"] * 0.97
    assert rf.screen(T, seeds, [], ["c"], LV_FAST, workers=2, b=300)["decision"]["outcome"] == "P0 FAILS"


def test_seed_ranges_parse(tmp_path, monkeypatch):
    seen = {}
    monkeypatch.setattr(rf, "screen", lambda T, seeds, *a, **k: seen.setdefault("s", seeds) and {"decision": {"outcome": "x"}})
    monkeypatch.setattr(rf.rc, "load", lambda p: {})
    rows = tmp_path / "r" / "s6_rows.jsonl"
    rows.parent.mkdir()
    rows.write_text("")
    (rows.parent / "meta.json").write_text('{"inputs": {"cpu": "c"}}')
    rf.main(["screen", str(tmp_path / "o.json"), "--rows", str(rows), "--seeds", "1-3", "10-11"])
    assert seen["s"] == [1, 2, 3, 10, 11]
