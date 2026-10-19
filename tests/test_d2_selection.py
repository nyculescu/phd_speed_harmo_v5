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


def _run(pre, post, inc, q, s, delay, valid=True):
    return {"key": run_key(pre, post, inc, q, s), "pre": pre, "post": post, "incident": inc, "q": q, "seed": s,
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
