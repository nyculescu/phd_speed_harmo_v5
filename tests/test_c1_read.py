"""C1 (c1_screen.md, V521): the planted rows of §5 read as written under §7's order; the n rule; the stage plans; key classes; splits."""
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis/c1"))
sys.path.insert(0, str(ROOT / "analysis/planb"))
import c1  # noqa: E402
import read_c1 as rc  # noqa: E402


def iv(pt, lo, hi, lo95=None, hi95=None):
    """A reading with a 97.5 % interval; the 95 % one is narrower in the same proportion as normal quantiles."""
    se = (hi - lo) / (2 * rc.Z975)
    mid = (hi + lo) / 2
    return {"pt": pt, "lo": lo, "hi": hi, "lo95": lo95 if lo95 is not None else mid - rc.Z95 * se, "hi95": hi95 if hi95 is not None else mid + rc.Z95 * se}


def base(**kw):
    x = {"void": [], "p0": True, "p333_stuck": False, "else_readable": True, "edge": iv(10, 4, 16), "delay": iv(0, -0.5, 0.5),
         "cost": iv(-5, -8, -2), "else": iv(10, 2, 18), "ev45": iv(0, -3, 3), "jams": iv(0, -3, 3)}
    return x | kw


def out(**kw):
    return rc.decide(base(**kw))["outcome"]


def test_planted_rows_of_section_5():
    assert out() == "ROOM WITH COST"
    assert out(edge=iv(0, -4, 4)) == "K1 NO ROOM"
    assert out(edge=iv(0, -4, 12)) == "NOT RESOLVABLE (edge)"
    assert out(edge=iv(0, -4, 4), delay=iv(-1.5, -3, 0.5)) == "K1 NO ROOM"     # delay is read only after an edge is shown
    assert out(cost=iv(1, -2, 4)) == "NO COST"
    assert out(cost=iv(1, -2, 4), ev45=iv(-6, -9, -3)) == "COST ON ANOTHER MEASURE"
    assert out(cost=iv(-4, -4.8, -0.5)) == "ROOM WITH COST"     # present is read first
    assert out(cost=iv(-2.5, -4.9, -0.1)) == "COST UNDECIDED"     # a shown cost under 3 % never reads absent
    assert out(delay=iv(-0.5, -0.8, -0.2)) == "ROOM WITH COST"     # a shown loss inside the band is KEPT
    assert out(**{"else": iv(-10, -18, -2)}) == "K3 MERGES ONLY"
    assert out(else_readable=False) == "ROOM WITH COST, merge-weighted"
    assert out(**{"else": iv(3, -5, 11)}) == "ROOM WITH COST, merge-weighted"


def test_delay_cost_and_order():
    assert out(delay=iv(-1.5, -2.5, -0.5)) == "K2 DELAY"
    assert out(delay=iv(-0.9, -2.0, 0.2)) == "NOT RESOLVABLE (delay)"
    assert out(p333_stuck=True) == "NOT RESOLVABLE (delay)"
    assert out(p0=False) == "P0 FAILS"
    assert out(void=["x"]) == "VOID"
    assert out(cost=iv(-4, -9, 1)) == "COST UNDECIDED"
    x = iv(-0.95, -0.99, -0.9)     # kept and worse cannot both hold
    assert rc.r_delay(x) == "KEPT"


def test_p0_reads_positive_as_less_delay():
    rng = np.random.default_rng(1)
    s = list(range(60))
    nc = 1000 + rng.normal(0, 5, 60)
    T = {("E30", "nc"): {i: {"all_delay": nc[i], "ttc_net": 100.0} for i in s}}
    for a, f in (("p333", 0.65), ("3E-C_TRUCK", 0.95)):
        T[("E30", a)] = {i: {"all_delay": nc[i] * f, "ttc_net": 90.0} for i in s}
    idx = np.random.default_rng(0).integers(0, 60, (2000, 60))
    p = rc.p0(T, "E30", s, idx)
    assert p["pass"] and p["p333"]["pt"] == pytest.approx(35.0, abs=0.5)
    for a in ("p333", "3E-C_TRUCK"):
        T[("E30", a)] = {i: {"all_delay": nc[i] * 0.95, "ttc_net": 90.0} for i in s}
    assert not rc.p0(T, "E30", s, idx)["pass"]


def test_n_rule_projects_the_pilot_se():
    se60 = {"edge": 2.79 * 2, "cost": 1.47 * 2, "delay": 0.25 * 2}     # TRUCK-like spreads (SE at 240 x sqrt(240/60))
    assert rc.n_rule(se60)["n"] == 480
    assert rc.n_rule({"edge": 5.99 * 2, "cost": 3.48 * 2, "delay": 0.44 * 2})["n"] == 1920
    assert rc.n_rule({"edge": 30.0, "cost": 30.0, "delay": 3.0})["n"] is None


def test_simulated_outcomes_match_round_3():
    se = {k: v * np.sqrt(240 / 480) for k, v in {"edge": 2.79, "cost": 1.47, "delay": 0.25, "else": 6.63, "ev45": 1.67, "jams": 3.66}.items()}
    r = rc.simulate(se, rc.TRUTHS["premise"], None)
    assert sum(r.get(k, 0) for k in rc.OPENS) > 0.9
    assert rc.simulate(se, rc.TRUTHS["null"], None).get("K1 NO ROOM", 0) > 0.95


def test_else_readability():
    s = list(range(100))
    T = {("E30", "3E-C_TRUCK"): {i: {"ttc_away": float(i % 7)} for i in s}}
    for w in rc.V3W:
        T[("E30", w)] = {i: {"ttc_away": float(i % 7) + (0.0 if i < 15 else 1.0)} for i in s}
    assert not rc.else_readable(T, "E30", s)["readable"]     # 15 % exact ties
    for w in rc.V3W:
        T[("E30", w)] = {i: {"ttc_away": float(i % 7) + (0.0 if i < 5 else 1.0)} for i in s}
    assert rc.else_readable(T, "E30", s)["readable"]


def test_split_sums():
    r = {"ttc_net": 5.0, "m_road_ttc3": {"4a": {"rest": 3}, "3": {"hold": 2}}, "b45_step": 0.3, "b45_step_g_4a": 0.1, "b45_step_g_3": 0.2,
         "fuel": 10.0, "fuel_g_1": 4.0, "fuel_g_4a": 6.0, "m_peak_car": [0, 0, 0, 1, 1], "m_peak_alks": [0] * 5, "m_peak_truck": [0] * 5,
         "m_road_ge45": {"4a": 2}, "all_delay": 1.0}
    assert rc.split_sums(r) == []
    assert rc.split_sums(r | {"m_road_ge45": {"4a": 1}}) == ["events_ge45"]
    assert rc.split_sums(r | {"fuel_g_5": 1.0}) == ["fuel"]
    assert rc.split_sums({k: v for k, v in r.items() if k != "b45_step_g_3"}) == ["b45_step"]


def test_key_classes():
    assert rc.key_class("ctrl_sha256") == rc.key_class("name") == "provenance"
    assert rc.key_class("m_dec_entropy_mean") == rc.key_class("lv_sum_3") == rc.key_class("tau_on_match") == "diagnostic"
    assert rc.key_class("all_delay") == rc.key_class("m_road_ttc3") == "traffic"


def test_ident_actions():
    ref = {"name": "S|w0u250", "seed": 1, "all_delay": 5.0, "m_dec_entropy_mean": 1.0, "commit": "a"}
    S6 = {("S|w0u250", 1): ref, ("S|p333", 1): {**ref, "name": "S|p333"}}
    diag_only = [{**ref, "m_dec_entropy_mean": 1.0000001, "commit": "b"}, {**S6[("S|p333", 1)], "commit": "b"}]
    assert rc.ident(diag_only, S6, "AMD EPYC 7702")["action"] == "go"
    traffic = [{**ref, "all_delay": 5.1}, S6[("S|p333", 1)]]
    r = rc.ident(traffic, S6, "AMD EPYC 7702")
    assert r["action"] == "go" and r["learner_diff_disclosed"]
    assert rc.ident(traffic, S6, "Intel Xeon Platinum 8163")["action"] == "stop"
    assert rc.ident([ref, {**S6[("S|p333", 1)], "all_delay": 9.0}], S6, "AMD EPYC 7702")["action"] == "stop"


def test_stage_ranges_are_inside_the_approved_block_and_disjoint():
    rngs = sorted(v for k, v in c1.STAGES.items() if not k.endswith("_ident"))
    for a, b in rngs:
        assert 7_489_000 <= a <= b <= 7_491_919
    for (a, b), (c, d) in zip(rngs, rngs[1:]):
        assert b < c
    assert c1.STAGES["c1_pilot"] == (7_490_000, 7_490_059) and c1.STAGES["c1_screen"][0] == 7_490_060


def test_plans(tmp_path):
    p = c1.plan("c1_checks", tmp_path)
    assert set(p["arms"]) == {f"{c}|{a}" for c in ("S", "SL450", "SL600", "SH30", "SH70") for a in ("nc", "p333")}
    assert p["arms"]["SL450|p333"]["accel2_len"] == 450.0 and p["arms"]["SH30|nc"]["share"] == 0.3
    assert all(c["split"] for c in p["arms"].values())
    s = c1.plan("c1_screen", tmp_path, "E30", 480)
    assert s["seed_range"] == [7_490_060, 7_490_479] and len(s["arms"]) == 8
    ev = s["arms"]["E30|w0u250"]["ctrl"]["env"]["perturb"]
    assert ev["limit_kmh"] == 30.0 and ev["dur"] == [240.0, 420.0] and s["arms"]["E30|w0u250"]["ctrl"]["pt"].endswith("C0_u250.pt")
    assert c1.plan("c1_fallback", tmp_path)["arms"]["E30s|nc"]["ctrl"]["env"]["perturb"]["dur"] == [120.0, 240.0]
    with pytest.raises(SystemExit):
        c1.plan("c1_screen", tmp_path, "E30", 300)
    sm = c1.plan("c1_smoke", tmp_path)["arms"]
    assert "split" not in sm["S|nc~untraced"] and sm["E30|nc~trace"]["t0_event"] and sm["S|nc~share50"]["share"] == 0.5
    i = c1.plan("c1_ident", tmp_path)["arms"]
    assert "split" not in i["S|w0u250"] and set(i) == {f"S|{a}" for a in c1.RULES + c1.pb.V3W}


def test_longer_ramp2_lane_keeps_the_other_edges(tmp_path, monkeypatch):
    from v5b2.freeway import network as corridor
    monkeypatch.setattr(corridor, "NET_CACHE", tmp_path)
    import xml.etree.ElementTree as ET
    lens = {}
    for L in (300.0, 450.0, 600.0):
        d = corridor.build(100 / 3.6, corridor.R2M3, 300.0, L)
        lens[L] = {ln.get("id"): float(ln.get("length")) for ln in ET.parse(d / "net.xml").getroot().iter("lane") if not ln.get("id").startswith(":")}
    for L in (450.0, 600.0):
        assert lens[L]["4a_0"] - lens[300.0]["4a_0"] == pytest.approx(L - 300.0, abs=1.0)
        for e in ("3_0", "4_0", "5_0", "3a_0", "r2_0", "rj2_0"):
            assert lens[L][e] == pytest.approx(lens[300.0][e], abs=1e-6)
    assert corridor.build(100 / 3.6, corridor.R2M3) == corridor.build(100 / 3.6, corridor.R2M3, 300.0, 300.0)


def wrapped(name, cfg, seed=1):
    import run6
    return run6.wrap({"all_delay": 1.0, "name": name, "seed": seed}, (name, cfg, 5300.0, seed, "rd", "abc"))


def test_smoke_twins_differ_only_in_identity_fields(tmp_path):
    sm = c1.plan("c1_smoke", tmp_path)["arms"]
    pairs = [(n[: -len(c1.TWIN)], n) for n in sm if n.endswith(c1.TWIN)] + [("E30|nc~trace", "E30|nc" + c1.TWIN), ("S|nc~share50", "S|nc")]
    assert ("E30|w0u250", "E30|w0u250~untraced") in pairs
    for m, n in pairs:
        assert c1.twin_diff(wrapped(m, sm[m]), wrapped(n, sm[n])) == []


def test_t0_requires_p333_command_read_back():
    good = {"tau_on_n": 100.0, "tau_on_match": 100.0, "tau_mismatch": 0.0, **{f"lv_sum_{r}": 300.0 for r in "2345"}, **{f"lv_n_{r}": 100.0 for r in "2345"}}
    arms = {"S|p333": {}, "S|p333~untraced": {}, "S|nc": {}}
    A = {("S|p333", 1): dict(good), ("S|p333~untraced", 1): dict(good), ("S|nc", 1): {}}
    assert c1.t0_rows(A, arms)["bad"] == []
    for bad in ({"tau_on_match": 99.0}, {"tau_mismatch": 1.0}, {"tau_on_n": 0.0, "tau_on_match": 0.0}):
        A[("S|p333~untraced", 1)] = good | bad
        assert c1.t0_rows(A, arms)["bad"] == ["T0 p333 command S|p333~untraced 1"]


def test_ident_matches_the_real_lscpu_string():
    ref = {"name": "S|w0u250", "seed": 1, "all_delay": 5.0}
    S6 = {("S|w0u250", 1): ref}
    rows = [{**ref, "all_delay": 5.1}]
    assert rc.ident(rows, S6, "Intel(R) Xeon(R) Platinum 8163 CPU @ 2.50GHz")["action"] == "stop"
    assert rc.ident(rows, S6, "AMD EPYC 7702 64-Core Processor")["action"] == "go"


def test_n_rule_uses_the_pilot_seed_count():
    se = {"edge": 5.58, "cost": 2.94, "delay": 0.5}
    p = rc.n_rule(se, 57)["projected_se"][240]["edge"]
    assert p == pytest.approx(1.15 * 5.58 * np.sqrt(57 / 240))


def test_side_file_drift_at_float32_level_does_not_stop(monkeypatch):
    import json
    R = Path("/home/catalin/work/phd/v5b1_runs/v505_remote/ev_size")
    if not (R / "s6_rows.jsonl").is_file():
        pytest.skip("stored V505 rows not on this machine")
    r = json.loads(next(iter(open(R / "s6_rows.jsonl"))))
    real = rc.read6.space_time

    def drift(row, st, vs):
        out = real(row, st)
        out["bind"] = dict(out["bind"], vs_rel=vs)
        return out
    monkeypatch.setattr(rc.read6, "space_time", lambda row, st: drift(row, st, 7.3e-4))
    assert rc.jams_of(r, R / "st")[2] == 7.3e-4
    monkeypatch.setattr(rc.read6, "space_time", lambda row, st: drift(row, st, 0.05))
    with pytest.raises(SystemExit):
        rc.jams_of(r, R / "st")
