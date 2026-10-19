"""P1 statistics and decision rules on synthetic numbers (page §3-§6)."""
import numpy as np
import pytest

from v5b.p1 import stats as st

rng = np.random.default_rng(1)


def test_levels_and_bootstrap_size():
    assert st.B_BOOT == 20_000
    assert st.LEVEL_S1 == pytest.approx(1 - 0.05 / 8) and st.LEVEL_S2 == pytest.approx(1 - 0.05 / 4)
    assert st.LEVEL_TV == pytest.approx(1 - 0.05 / 12) and st.PLATEAU_Z == 0.01
    r = 100 + rng.normal(0, 5, 60)
    t = r - 8 + rng.normal(0, 3, 60)
    a, b = st.paired(r, t, 0.95), st.paired(r, t, st.LEVEL_S1)
    assert a["rel"] == b["rel"] == pytest.approx(np.median(r - t) / np.median(r))
    assert b["diff_ci"][0] <= a["diff_ci"][0] and b["diff_ci"][1] >= a["diff_ci"][1]     # wider at the S1 level
    m = st.paired(r, t, mean=True)
    assert m["rel"] == pytest.approx(np.mean(r - t) / np.mean(r)) and m["version"] == "mean"


def _cell(rel, lo):
    return {"rel": rel, "diff_ci": [lo, lo + 10.0]}


def test_rule_R_needs_a_in_one_cell_and_b_in_every_cell():
    ok = {"c1": _cell(0.12, 1.0), "c2": _cell(-0.04, -9.0)}
    assert st.rule_R(ok)["pass"]
    assert not st.rule_R({"c1": _cell(0.12, 1.0), "c2": _cell(-0.06, -9.0)})["pass"]     # (b) on the point estimate
    assert not st.rule_R({"c1": _cell(0.12, -0.1), "c2": _cell(0.0, -1.0)})["pass"]      # (a) needs the CI > 0
    assert not st.rule_R({"c1": _cell(0.09, 1.0)})["pass"]                               # (a) needs >= 10 %
    assert st.rule_R({"c1": _cell(0.10, 1e-9)})["pass"]
    assert not st.rule_R({"c1": _cell(0.2, 1.0), "c2": None})["pass"]                    # no data in a view: fail


def test_s1a_intersection_union_same_cell():
    per_r = {r: {"c1": _cell(0.2, 1.0), "c2": _cell(0.0, -1.0)} for r in ("N", "FX", "FB", "PI", "AD")}
    assert st.s1a(per_r)["pass"] and st.s1a(per_r)["common_a_cells"] == ["c1"]
    per_r["AD"] = {"c1": _cell(0.05, 1.0), "c2": _cell(0.2, 1.0)}          # AD's (a) only in c2: no common cell
    out = st.s1a(per_r)
    assert all(v["pass"] for v in out["R"].values()) and not out["pass"]
    per_r["AD"] = {"c1": _cell(0.2, 1.0), "c2": _cell(-0.051, -1.0)}       # AD breaks (b)
    assert not st.s1a(per_r)["pass"]


def test_two_views_must_both_pass():
    good = {"c1": _cell(0.2, 1.0)}
    bad = {"c1": _cell(0.2, -1.0)}
    assert st.two_views(st.rule_R, good, good)["pass"]
    assert not st.two_views(st.rule_R, good, bad)["pass"] and not st.two_views(st.rule_R, bad, good)["pass"]


def test_views_drop_invalid_seeds():
    v = st.views({"a": [1, 2, 3], "b": [4, 5, 6]}, [False, True, False])
    assert v["n_invalid_seeds"] == 1 and list(v["valid"]["a"]) == [1, 3] and list(v["all"]["b"]) == [4, 5, 6]
    assert st.views({"a": [1]}, [True])["valid"] is None


def test_s2_bracket_plateau_and_statements():
    n = 100
    ip = 200 + rng.normal(0, 10, n)
    or_in = ip * 0.80
    orx = {1: ip * 0.97, 2: ip * 0.95, 4: ip * 0.95 + rng.normal(0, 0.2, n)}
    v = st.s2_cell(ip, or_in, orx)
    assert v["x"] >= 0.19 and v["y"] > 0.04 and v["plateau_holds"] and v["y_hat"] == pytest.approx(0.05, abs=0.003)
    s = st.s2_statements(v, v)
    assert s["adds_at_least_pct"] > 4 and s["adds_about_pct"] == pytest.approx(5.0, abs=0.3) and "biased low" in s["text"]
    orx2 = {1: ip * 0.99, 2: ip * 0.99, 4: ip * 0.95}           # no plateau: R = 2 -> 4 still moves by ~4 points
    v2 = st.s2_cell(ip, or_in, orx2)
    assert not v2["plateau_holds"]
    s2 = st.s2_statements(v2, v2)
    assert s2["adds_about_pct"] is None and "bracket" in s2["text"]
    orx3 = {1: ip * 1.01, 2: ip * 1.01, 4: ip * 1.01}           # ORX worse than IP: y < 0, no 'at least'
    s3 = st.s2_statements(st.s2_cell(ip, or_in, orx3), None)
    assert s3["adds_at_least_pct"] is None and s3["x"] == float("inf")   # a view without seeds: no claim
    va, vb = dict(v), dict(v)
    vb["x"], vb["y"] = v["x"] + 0.05, v["y"] - 0.01
    c = st.s2_statements(va, vb)
    assert c["x"] == vb["x"] and c["y"] == vb["y"]              # larger x, smaller y over the two views


def test_tp_placebo_is_nonnegative_noise_inflation():
    ip = 100 + rng.normal(0, 5, 50)
    reps = ip[:, None] + rng.normal(0, 5, (50, 4))
    r = st.tp_placebo(ip, reps)
    assert r["rel"] > 0 and r["diff_ci"][0] >= 0


def test_mixtures_exact():
    a, b = np.array([10.0, 20.0]), np.array([30.0, 0.0])
    assert list(st.mixture(a, b, 0.25)) == [15.0, 15.0]
    assert list(st.mixture(a, b, 0.0)) == [10.0, 20.0] and list(st.mixture(a, b, 1.0)) == [30.0, 0.0]
    p = st.prevalence_mix([10.0], [30.0], [5.0], 0.1)
    assert p[0] == pytest.approx(0.1 * 20.0 + 0.9 * 5.0)


def test_crossing_linear_first_and_censoring():
    g = (0, 30, 60, 120, 240)
    v, f = st.crossing(np.array([[10, 5, -5, -6, -7]]), g, "linear")
    assert v[0] == pytest.approx(45.0) and f[0] == 0
    v, f = st.crossing(np.array([[10, 5, 0, -6, -7]]), g, "linear")
    assert v[0] == pytest.approx(60.0) and f[0] == 0
    v, f = st.crossing(np.array([[10, 5, 4, 3, 1]]), g, "linear")
    assert v[0] == 240 and f[0] == 2                              # '> max', censored at the grid end
    v, f = st.crossing(np.array([[0, 5, 4, 3, 1]]), g, "linear")
    assert v[0] == 0 and f[0] == 1                                # 'IP never ahead'
    v, f = st.crossing(np.array([[3, -1, 2, 2, 2]]), g, "linear")
    assert v[0] == pytest.approx(22.5)                            # first crossing, not the last
    pg = tuple(round(0.01 * i, 2) for i in range(101))
    M = 1.0 - 2.0 * np.array(pg)
    v, f = st.crossing(M[None, :], pg, "first")
    assert v[0] == 0.5 and f[0] == 0
    v, f = st.crossing((M + 5)[None, :], pg, "first")
    assert v[0] == 1.0 and f[0] == 2                              # '> 1'


def test_breakeven_smallest_over_l0_and_bootstrap_shares():
    n, g = 40, (0, 30, 60, 120, 240)
    base = rng.normal(0, 1, n)
    # L0 - IP_d: arm A crosses near 60, arm B never crosses (censored), arm C crosses near 30
    XA = np.stack([20 - x / 3.0 + base for x in g], axis=1)
    XB = np.stack([50 + 0 * x + base for x in g], axis=1)
    XC = np.stack([20 - x / 1.5 + base for x in g], axis=1)
    out = st.breakeven({"A": XA, "B": XB, "C": XC}, g, "linear", B=2000)
    assert out["binding_arm"] == "C" and out["value"] == pytest.approx(30.0, abs=3)
    assert out["per_arm"]["B"]["flag"] == "> max" and out["per_arm"]["A"]["value"] == pytest.approx(60, abs=6)
    assert out["ci"][0] <= out["value"] <= out["ci"][1] and out["share_censored_gt_max"] == 0.0
    out2 = st.breakeven({"B": XB}, g, "linear", B=2000)
    assert out2["share_censored_gt_max"] == 1.0 and out2["ci"] == [240.0, 240.0]
    out3 = st.breakeven({"D": -XB}, g, "linear", B=2000)
    assert out3["flag"] == "IP never ahead" and out3["share_never_ahead"] == 1.0


def test_t0_t4_tad():
    nc = 300 + rng.normal(0, 10, 20)
    t0 = st.t0_cells({"slow_q1600": nc * 0.8, "block_q1600": nc * 0.95}, {"slow_q1600": nc, "block_q1600": nc},
                     {"slow_q1600": "IP", "block_q1600": "IP"})
    assert t0["cells"]["slow_q1600"]["pass"] and not t0["cells"]["block_q1600"]["pass"] and not t0["pass"]
    t4 = st.t4_cell(nc, nc * 0.85, "c1600", "c1200")
    assert t4["pass"] and not st.t4_cell(nc, nc * 0.85, "c1600", "c1600")["pass"]
    assert not st.t4_overall({"a": t4, "b": {**t4, "pass": False}})["pass"]
    tad = st.tad_cells({"slow_q1600": [0, 2, 3], "block_q1600": [0, 1, 4]})
    assert tad["slow_q1600"]["binds"] and not tad["block_q1600"]["binds"]
    assert tad["block_q1600"]["note"] == "AD not identifiable on BN4"


def test_vsl_binding_precheck():
    nc = 100 + rng.normal(0, 3, 20)
    b = st.tv_binding({"c1": nc, "c2": nc}, {"c1": nc * 0.999, "c2": nc * 0.98})
    assert not b["pass"] and "cannot bind" in b["text"]           # changes < 5 %: TV ends
    b = st.tv_binding({"c1": nc, "c2": nc}, {"c1": nc * 1.08, "c2": nc})
    assert b["pass"] and b["cells"]["c1"]["binds"]                  # a 5 % change either way binds


def test_vsl_entry_bonferroni_m12():
    ip = 200 + rng.normal(0, 30, 20)
    k = {f"b{b}_c{i}": ip for b in (0.8, 0.6, 0.4) for i in range(4)}
    flat = {kk: ip * 0.95 for kk in k}
    assert not st.tv_entry(k, flat)["enters"]
    good = dict(flat)
    good["b0.4_c2"] = ip * 0.85
    e = st.tv_entry(k, good)
    assert e["enters"] and e["cells"]["b0.4_c2"]["level"] == pytest.approx(1 - 0.05 / 12)
