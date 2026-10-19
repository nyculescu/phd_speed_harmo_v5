"""Screen D2 Rule 3 on synthetic run dicts: G, N / FX / FB / IP tuning, the per-seed oracle and the cell assembly."""
import numpy as np
import pytest

from v5b.d1.run_screen import FX_GRID
from v5b.d2 import controllers as ctl
from v5b.d2 import run_screen as rs
from v5b.d2.episode import run_key


def test_family_g():
    assert ctl.RATES == tuple(FX_GRID) and len(ctl.CONST) == 19 and len(ctl.FEEDBACK) == 16 and len(ctl.G) == 35
    assert len(set(ctl.G)) == 35 and ctl.parse("c2600") == ("const", 2600.0) and ctl.parse("f70_12") == ("fb", 70.0, 12.0)
    assert ctl.meter_kwargs("c600") == {"K_F": 0.0, "q0": 600.0}
    assert ctl.meter_kwargs("f10_6") == {"K_F": 10.0, "n_crit": 6.0}
    with pytest.raises(ValueError):
        ctl.parse("NC")


def test_best_by_median_and_ties():
    d = {"c800": [3, 1, 2], "c600": [2, 2, 9], "f10_6": [1, 9, 9]}
    assert ctl.best_by_median(d) == "c600"                      # tie at median 2: earlier in G order
    assert ctl.best_by_median(d, among=ctl.FEEDBACK) == "f10_6"
    with pytest.raises(ValueError):
        ctl.best_by_median({}, among=ctl.FEEDBACK)


def test_oracle_pick():
    assert ctl.oracle_pick({"c800": 5.0, "f20_8": 4.0, "c600": 4.0}) == ("c600", 4.0)


def _run(pre, post, inc, q, s, delay, valid=True, back=False):
    return {"key": run_key(pre, post, inc, q, s, back=back), "pre": pre, "post": post, "back": back, "incident": inc,
            "q": q, "seed": s,
            "delay_s": float(delay), "served_ctrl_vph": 1500.0, "ttt_ctrl_vehh": 10.0, "ttt_full_vehh": 12.0,
            "valid": valid, "teleports": 0}


G3 = ("c800", "c1600", "f20_8")
SEEDS = (1, 2, 3)


def _synthetic():
    """No incident: c1600 best. Incidents (fixed): c800 best pooled constant; f20_8 the only feedback.
    Switch runs from N = c1600: slow -> c800 best on 2 of 3 seeds; block -> f20_8 best by median."""
    res = {}
    add = lambda r: res.__setitem__(r["key"], r)
    for q in rs.QS:
        for s in SEEDS:
            for g, v in {"c800": 300, "c1600": 200, "f20_8": 250}.items():
                add(_run(g, None, "none", q, s, v + s))
            for inc in ("slow", "block"):
                for g, v in {"c800": 400, "c1600": 500, "f20_8": 450}.items():
                    add(_run(g, None, inc, q, s, v + s))
                add(_run("NC", None, inc, q, s, 900))
            sw = {"slow": {"c800": [300, 310, 500], "c1600": [400, 400, 400], "f20_8": [350, 350, 350]},
                  "block": {"c800": [500, 500, 100], "c1600": [450, 450, 450], "f20_8": [420, 420, 420]}}
            for inc, tab in sw.items():
                for g, vals in tab.items():
                    add(_run("c1600", g, inc, q, s, vals[s - 1]))
                    add(_run("c1600", g, inc, q, s, 999, back=True))   # A12: switch-back runs, never best here
    return res


def test_fit_arms_and_ip():
    res = _synthetic()
    f = rs.fit_fixed_arms(res, SEEDS, G3, 2000.0)
    assert (f["N"], f["FX"], f["FB"]) == ("c1600", "c800", "f20_8")
    ip = rs.fit_ip(res, SEEDS, G3, 2000.0, "c1600")["IP"]
    assert ip == {"slow": "c800", "block": "f20_8"}             # medians: slow c800 310; block f20_8 420 < c1600 450


def test_cell_keys_oracle_per_seed_and_missing_runs():
    res = _synthetic()
    arms = {"N": "c1600", "FX": "c800", "FB": "f20_8", "IP": {"slow": "c800", "block": "f20_8"}}
    ok, keys, pick = rs.cell_keys(res, SEEDS, G3, 2000.0, "block", arms)
    assert ok == [1, 2, 3] and pick == ["f20_8", "f20_8", "c800"]
    assert [res[k]["delay_s"] for k in keys["OR"]] == [420, 420, 100]
    assert keys["N"][0] == run_key("c1600", "c1600", "block", 2000.0, 1)     # N = the switch run N -> N
    assert keys["IP"][2] == run_key("c1600", "f20_8", "block", 2000.0, 3)
    assert keys["FX"][0] == run_key("c800", None, "block", 2000.0, 1)
    del res[run_key("c1600", "c800", "block", 2000.0, 2)]      # a missing switch run drops the seed
    ok, _, _ = rs.cell_keys(res, SEEDS, G3, 2000.0, "block", arms)
    assert ok == [1, 3]


def test_incident_cells_end_to_end_synthetic():
    res = _synthetic()
    arms = {rs.qk(q): {"N": "c1600", "FX": "c800", "FB": "f20_8", "IP": {"slow": "c800", "block": "f20_8"}}
            for q in rs.QS}
    cells, opmap = rs.incident_cells(res, SEEDS, G3, arms)
    assert set(cells) == {"slow_q1600", "slow_q2000", "block_q1600", "block_q2000"}
    c = cells["slow_q2000"]
    assert c["n"] == 3 and c["med_OR"] == 310.0 and set(c["per_fallback"]) == {"FX", "FB", "IP"}
    assert opmap["block_q2000"]["or_picks"] == {"f20_8": 2, "c800": 1}
    assert np.isclose(opmap["slow_q2000"]["arms"]["NC"]["median_delay_s"], 900.0)


# ---------------------------------------------------------------- A12 (V92(c)): G x {stay, back}
def test_action_set_labels_order_and_ties():
    A = ctl.actions(G3)
    assert A == ("c800", "c1600", "f20_8", "c800+back", "c1600+back", "f20_8+back")
    assert len(ctl.actions()) == 70 and ctl.parse_action("f20_8+back") == ("f20_8", True)
    assert ctl.parse_action("c800") == ("c800", False) and ctl.action("c800", True) == "c800+back"
    with pytest.raises(ValueError):
        ctl.parse_action("NC+back")
    assert ctl.best_by_median({"c800+back": [2], "c1600": [2]}, A) == "c1600"     # tie: stay before back
    assert ctl.best_by_median({"c800+back": [1], "c1600": [2]}, A) == "c800+back"
    assert ctl.oracle_pick({"f20_8+back": 3.0, "c800+back": 3.0, "f20_8": 3.0}) == ("f20_8", 3.0)
    assert ctl.oracle_pick({"f20_8+back": 3.0, "c800+back": 3.0}) == ("c800+back", 3.0)
    assert ctl.grid_edges("c600+back") == ["rate=600"]
    assert rs.sw_key("c1600", "c800+back", "slow", 2000.0, 1) == "c1600-c800+back_slow_q2000_s1"
    assert rs.sw_key("c1600", "c800", "slow", 2000.0, 1, xf=True) == run_key("c1600", "c800", "slow", 2000.0, 1, xf=True)


def _with_back(xf_too=False):
    """_synthetic() plus back runs: slow -> 'c800+back' best on every seed (200 + s); block -> back runs never best.
    With xf_too, replicates of every switch run (main + 1, except block 'f20_8+back' which is best on the replicate)."""
    res = _synthetic()
    for k in [k for k, r in res.items() if r.get("back")]:
        del res[k]
    for q in rs.QS:
        for s in SEEDS:
            for g in G3:
                res[run_key("c1600", g, "slow", q, s, back=True)] = _run("c1600", g, "slow", q, s,
                                                                         200 + s if g == "c800" else 600, back=True)
                res[run_key("c1600", g, "block", q, s, back=True)] = _run("c1600", g, "block", q, s, 700, back=True)
    if xf_too:
        for k, r in list(res.items()):
            if r["post"] is not None:
                x = dict(r, xf=True, key=run_key(r["pre"], r["post"], r["incident"], r["q"], r["seed"], xf=True,
                                                  back=r["back"]), delay_s=r["delay_s"] + 1)
                if r["incident"] == "block" and rs.action_of(r) == "f20_8+back":
                    x["delay_s"] = 1.0
                res[x["key"]] = x
    return res


def test_a12_selection_over_doubled_set_ip_or_orx():
    res = _with_back(xf_too=True)
    ip = rs.fit_ip(res, SEEDS, G3, 2000.0, "c1600")
    assert ip["IP"] == {"slow": "c800+back", "block": "f20_8"} and len(ip["median_switch"]["slow"]) == 6
    arms = {"N": "c1600", "FX": "c800", "FB": "f20_8", "IP": ip["IP"]}
    ok, keys, pick = rs.cell_keys(res, SEEDS, G3, 2000.0, "slow", arms, xfit=True)
    assert ok == [1, 2, 3] and pick == ["c800+back"] * 3
    assert keys["IP"][0] == run_key("c1600", "c800", "slow", 2000.0, 1, back=True)
    assert keys["N"][0] == run_key("c1600", "c1600", "slow", 2000.0, 1)          # N = (N, stay)
    assert keys["OR"] == keys["ORX"] == keys["IP"]
    ok, keys, pick = rs.cell_keys(res, SEEDS, G3, 2000.0, "block", arms, xfit=True)
    assert pick == ["f20_8", "f20_8", "c800"]                                    # back runs not best on the main run
    assert keys["ORX"] == [run_key("c1600", "f20_8", "block", 2000.0, s, back=True) for s in SEEDS]   # picked on xf
    assert all(not res[k].get("xf") for k in keys["ORX"])
    del res[run_key("c1600", "c1600", "block", 2000.0, 2, xf=True, back=True)]  # a missing back replicate drops the seed
    ok, _, _ = rs.cell_keys(res, SEEDS, G3, 2000.0, "block", arms, xfit=True)
    assert ok == [1, 3]
    cells, opmap = rs.incident_cells(_with_back(xf_too=True), SEEDS, G3, {rs.qk(q): arms for q in rs.QS}, xfit=True)
    assert opmap["slow_q2000"]["n_back_picks"] == {"OR": 3, "ORX": 3}
    assert opmap["block_q2000"]["orx_picks"] == {"f20_8+back": 3}
    assert "c800+back" in opmap["slow_q2000"]["median_switch_by_target"]


def test_a12_switch_and_t3_specs_cover_back():
    N = {"1600": "c1600", "2000": "c1600"}
    sp = rs.switch_specs(N, G3, SEEDS)
    assert len(sp) == 2 * 3 * 2 * 2 * 3 and {(s["post"], s["back"]) for s in sp} == \
        {(g, b) for g in G3 for b in (False, True)}
    assert all(s["key"] == rs.sw_key(s["pre"], ctl.action(s["post"], s["back"]), s["incident"], s["q"], s["seed"])
               for s in sp)
    t3 = rs.t3_specs(7_400_080)
    assert any(p[0]["back"] and p[1]["back"] and p[0]["key"] != p[1]["key"] for p in t3)
    assert rs.run_counts(n_g=1) == {"tcheck": 2 * 3 * 2 * 20 + 12 + 2 * 2 * 2 * 20,
                                    "tune": 3 * 2 * 20 + 2 * 2 * 2 * 20,
                                    "eval": 2 * 2 * 2 * 2 * 50 + 3 * 2 * 2 * 50 + 4 * 2 * 50,
                                    "total": 412 + 280 + 1800}
