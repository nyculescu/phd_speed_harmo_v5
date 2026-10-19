"""P1 arms, oracles, run lists and the evaluation statements on synthetic run dicts (page §2, §4, §6, §7)."""
import numpy as np
import pytest

from v5b.d2.incidents import INCIDENTS, NONE, incident_window
from v5b.p1 import analysis as an
from v5b.p1 import family as fam
from v5b.p1.meters import switch_schedule

G3 = ("c800", "c1600", "f20_8")
A3 = fam.actions(G3)
SEEDS = tuple(range(7_400_006, 7_400_014))


def _res(specs, f, invalid=()):
    out = {}
    for s in specs:
        out[s["key"]] = {**s, "delay_s": float(f(s)), "valid": s["key"] not in invalid, "teleports": 0,
                         "served_ctrl_vph": 1500.0, "ttt_ctrl_vehh": 10.0, "ttt_full_vehh": 12.0, "max_queue": 40,
                         "hash": s["key"]}
    return out


def test_fit_fixed_switch_id_ip_ad_prevalence():
    seeds = SEEDS[:4]
    sp = an.fixed_specs(G3 + ("p40_20_8_e4", "p20_10_6_e5"), an.CONDITIONS, seeds)
    m = {"c800": (3, 2), "c1600": (1, 4), "f20_8": (2, 3), "p40_20_8_e4": (9, 1), "p20_10_6_e5": (9, 5)}
    res = _res(sp, lambda s: 100 * m[s["pre"]][0 if s["incident"] == NONE else 1] + s["seed"] % 3)
    fx = an.fit_fixed(res, seeds, G3, ("p40_20_8_e4", "p20_10_6_e5"), 2000.0)
    assert (fx["N"], fx["FX"], fx["FB"], fx["PI"]) == ("c1600", "c800", "f20_8", "p40_20_8_e4")
    sw = an.switch_specs({"1600": "c1600", "2000": "c1600"}, A3, seeds)
    best = {"slow": "f20_8+back", "block": "c800"}
    res.update(_res(sw, lambda s: 50 if fam.action(s["post"], s["back"]) == best[s["incident"]] else
                    (60 if fam.action(s["post"], s["back"]) == "c1600+back" else 80)))
    f = an.fit_switch(res, seeds, A3, 2000.0, "c1600")
    assert f["IP"] == best and f["ID"] == "c1600+back"     # pooled: 60 in both types beats 50 / 80
    ad = an.fixed_specs(an.ad_candidates("f20_8"), an.CONDITIONS, seeds)
    res.update(_res(ad, lambda s: {"ad0p5_f20_8": 70, "ad1_f20_8": 65, "ad2_f20_8": 65}[s["pre"]]))
    assert an.fit_ad(res, seeds, 2000.0, "f20_8")["AD"] == "ad1_f20_8"   # tie -> eta order
    fams = an.prevalence_families({"FB": "f20_8"}, G3, ("p40_20_8_e4", "p20_10_6_e5"))
    pv = an.fit_prevalence(res, seeds, 2000.0, fams)
    assert set(pv) == {"0.1", "0.25", "0.5"} and pv["0.1"]["N"] == "c1600" and pv["0.25"]["N"] == "c1600"
    assert pv["0.5"]["PI"] == "p40_20_8_e4" and pv["0.1"]["AD"] == "ad1_f20_8"


def test_prevalence_retuning_uses_the_mixture():
    seeds = SEEDS[:3]
    sp = an.fixed_specs(("c800", "c1600"), an.CONDITIONS, seeds)
    # c800: clean 100, incidents 300; c1600: clean 80, incidents 400 -> pi 0.1: c1600 (112 vs 120); pi 0.5: c800
    d = {("c800", NONE): 100, ("c800", "slow"): 300, ("c800", "block"): 300,
         ("c1600", NONE): 80, ("c1600", "slow"): 400, ("c1600", "block"): 400}
    res = _res(sp, lambda s: d[(s["pre"], s["incident"])])
    pv = an.fit_prevalence(res, seeds, 2000.0, {"N": ("c800", "c1600")})
    assert pv["0.1"]["N"] == "c1600" and pv["0.5"]["N"] == "c800"


def test_or_in_and_orx_pick_on_replicates_score_on_main():
    main = ["a", "b", "c"]
    reps = [["a1", "b1", "c1"], ["a2", "b2", "c2"], ["a3", "b3", "c3"], ["a4", "b4", "c4"]]
    d = {"a": 10, "b": 12, "c": 11, "a1": 13, "b1": 9, "c1": 12, "a2": 9, "b2": 10, "c2": 14, "a3": 5, "b3": 20,
         "c3": 9, "a4": 5, "b4": 20, "c4": 9}
    res = {k: {"delay_s": v, "valid": k != "c2"} for k, v in d.items()}
    assert an.or_in(res, [main]) == [(10, "a", False)]
    assert an.orx(res, [main], [reps], 1) == [(12, "b", False)]                 # best on k = 1, main score 12
    assert an.orx(res, [main], [reps], 2) == [(12, "b", True)]                  # means a 11, b 9.5; c2 invalid enters
    assert an.orx(res, [main], [reps], 4)[0][:2] == (10, "a")                   # means a 8, b 14.75, c 11


def test_canonical_imperfection_runs():
    s, q, N = 7_400_006, 2000.0, "c1600"
    on, dur = incident_window(s, 40.0, 900.0)
    big = dur + 10.0
    assert an.canon_sw(N, "c800", "slow", q, s, d=big)["key"] == an.sw(N, N, "slow", q, s)["key"]   # IP = N
    assert an.canon_sw(N, "c1600+back", "slow", q, s, d=30.0)["key"] == an.sw(N, N, "slow", q, s)["key"]
    assert an.canon_sw(N, "c800", "slow", q, s, c=60.0)["key"] == an.sw(N, "c800", "slow", q, s)["key"]
    k = an.canon_sw(N, "c800+back", "slow", q, s, d=30.0, c=60.0)
    assert (k["post"], k["back"], k["d"], k["c"]) == ("c800", True, 30.0, 60.0)
    t_sw, t_bk = switch_schedule(on, dur, 0.0, 900.0, True)
    assert t_bk is None and an.canon_sw(N, "c800+back", "slow", q, s, c=900.0)["key"] == \
        an.sw(N, "c800", "slow", q, s)["key"]
    fa = an.fa_spec(N, "c800+back", q, s)
    assert fa["fa"] and fa["post"] == "c800" and not fa["back"] and fa["incident"] == NONE
    assert an.fa_spec(N, "c1600+back", q, s)["key"] == an.fixed(N, NONE, q, s)["key"]


def _arms(pi_mult=1.0):
    a = {"N": "c1600", "FX": "c800", "FB": "f20_8", "PI": "p40_20_8_e4", "AD": "ad1_f20_8", "ID": "f20_8+back",
         "IP": {"slow": "f20_8", "block": "c800+back"}}
    a["prev"] = {str(p): {x: a[x] for x in an.L0} for p in an.PIS}
    return {"1600": dict(a), "2000": dict(a)}


def _world(arms, pi_mult=1.0):
    def f(s):
        b = 300.0 + 10.0 * (s["seed"] % 7) + 3.0 * s["k"]
        a = arms[str(int(s["q"]))]
        if s["incident"] == NONE:
            if s["fa"]:
                return 0.5 * b + 20.0
            return 0.75 * b if s["pre"] == "NC" else 0.5 * b
        if s["post"] is None:
            if s["pre"] == "NC":
                return 1.5 * b
            return (pi_mult if s["pre"] == a["PI"] else 1.0) * b + {"c1600": 0, "c800": 1, "f20_8": 2}.get(s["pre"], 3)
        act = fam.action(s["post"], s["back"])
        if act == a["ID"]:
            m = 0.8
        elif act == a["IP"][s["incident"]]:
            m = 0.7 + 0.002 * s["d"] + 0.0005 * s["c"]
        elif s["post"] == a["N"]:
            m = 1.0
        else:
            m = 0.95
        return m * b
    return f


def test_eval_specs_full_counts_and_replicates():
    arms = {"1600": {"N": "c1600", "FX": "c800", "FB": "f20_8", "PI": "p40_20_8_e4", "AD": "ad1_f20_8",
                     "ID": "f20_8+back", "IP": {"slow": "f20_8", "block": "c800+back"}},
            "2000": {"N": "c1700", "FX": "c1000", "FB": "f40_10", "PI": "p40_20_6_e5", "AD": "ad0p5_f40_10",
                     "ID": "c1200+back", "IP": {"slow": "c1100", "block": "f70_12+back"}}}
    for a in arms.values():
        a["prev"] = {str(p): {x: a[x] for x in an.L0} for p in an.PIS}
    seeds = tuple(range(7_400_500, 7_400_600))
    sp = an.eval_specs(arms, fam.A, seeds)
    main = [s for s in sp if s["post"] and not s["k"] and not s["fa"] and not s["d"] and not s["c"] and s["vsl_b"] is None]
    reps = [s for s in sp if s["k"]]
    assert len(main) == 100 * 2 * 2 * 100 and len(reps) == 4 * len(main)
    assert {s["k"] for s in reps} == {1, 2, 3, 4} and sp[-1]["k"] == 4 and not sp[0]["k"]   # replicates last
    tup = lambda s: (s["pre"], s["post"], s["back"], s["incident"], s["q"], s["seed"])
    assert {tup(s) for s in reps} == {tup(s) for s in main}
    fixed = [s for s in sp if s["post"] is None]
    assert len(fixed) == 6 * 3 * 2 * 100                       # N, FX, FB, PI, AD, NC x {none, slow, block}
    fa = [s for s in sp if s["fa"]]
    assert len(fa) == 2 * 2 * 100 and all(s["seed"] in seeds for s in sp)
    delayed = [s for s in sp if s["d"] or s["c"]]
    assert 0 < len(delayed) <= 2 * 2 * 100 * (4 + 2 + 2)
    assert len({s["key"] for s in sp}) == len(sp) and len(sp) < 210_000


def test_evaluate_end_to_end_statements():
    arms = _arms()
    sp = an.eval_specs(arms, A3, SEEDS, vsl=False)
    res = _res(sp, _world(arms))
    ev = an.evaluate(res, SEEDS, A3, arms, log=lambda m: None)
    assert ev["S1"]["S1a_pass"] and ev["S1"]["S1b_pass"]          # ID 20 % below every L0; IP 12.5 % below ID
    st_ = ev["S2"]["slow_q2000"]["statements"]
    assert st_["x"] == pytest.approx(0.0) and st_["adds_at_least_pct"] is None
    assert ev["S2"]["slow_q2000"]["all_seeds"]["plateau_holds"]
    s3 = ev["S3"]["block_q1600"]
    assert s3["clearance_delay_applies"] and not ev["S3"]["slow_q1600"]["clearance_delay_applies"]
    assert 120.0 <= s3["d_star"]["all_seeds"]["value"] <= 240.0 and s3["d_star"]["all_seeds"]["binding_arm"] == "N"
    assert s3["p_star"]["all_seeds"]["flag"] == "> max"
    assert ev["fig1_ladder"]["slow_q1600"]["strongest_L0"] == "N"
    assert [r["arm"] for r in ev["fig1_ladder"]["slow_q1600"]["rungs"]] == ["N", "ID", "IP", "ORX_4", "OR_in"]
    pq = ev["per_q"]["2000"]
    assert pq["false_alarm_cost"]["all_seeds"]["diff"] == pytest.approx(20.0)
    assert 0.4 < pq["prevalence"]["0.1"]["f_star"]["all_seeds"]["value"] < 0.7
    assert set(ev["table1_operating_map"]["block_q2000"]["arms"]) >= {"NC", "N", "FX", "FB", "PI", "AD", "ID", "IP",
                                                                     "OR_in", "ORX_1", "ORX_2", "ORX_4"}


def test_evaluate_intersection_union_and_invalid_runs():
    arms = _arms()
    sp = an.eval_specs(arms, A3, SEEDS, vsl=False)
    res = _res(sp, _world(arms, pi_mult=0.85))          # PI within 6 % of ID: R(ID, PI) fails (a) -> S1a fails
    ev = an.evaluate(res, SEEDS, A3, arms, log=lambda m: None)
    assert not ev["S1"]["S1a_pass"] and ev["S1"]["S1b_pass"]
    assert "did not pay" in ev["S1"]["S1a_text"]
    bad = an.sw("c1600", "f20_8+back", "slow", 1600.0, SEEDS[0])["key"]     # one invalid ID run
    res2 = _res(sp, _world(arms), invalid={bad})
    ev2 = an.evaluate(res2, SEEDS, A3, arms, log=lambda m: None)
    c = ev2["S1"]["per_cell_stats"]["slow_q1600"]
    assert c["ID_vs"]["N"]["n_invalid_seeds"] == 1 and c["ID_vs"]["N"]["valid_only"]["n"] == len(SEEDS) - 1
    assert ev2["S1"]["per_cell_stats"]["block_q1600"]["ID_vs"]["N"]["n_invalid_seeds"] == 0
    assert ev2["S2"]["slow_q1600"]["n_invalid_seeds"]["OR_in"] == 1          # the ID run is one of the A runs
    assert ev2["S1"]["S1a_pass"]
