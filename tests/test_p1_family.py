"""P1 page §2 and A5(a): family G, action set A, the PI grid and AD ids."""
from types import SimpleNamespace

import pytest

from v5b.d2 import controllers as d2
from v5b.p1 import family as fam


def test_extended_grid_a5a():
    assert len(fam.CONST) == 20 and fam.RATES[0] == 400.0 and fam.RATES[1:] == d2.RATES
    assert fam.KF_GRID == d2.KF_GRID + (120.0,) and fam.NCRIT_GRID == d2.NCRIT_GRID + (14.0, 16.0)
    assert len(fam.G) == 50 and len(set(fam.G)) == 50 and set(d2.G) < set(fam.G)
    assert len(fam.A) == 100 and fam.A[:50] == fam.G and all(a.endswith("+back") for a in fam.A[50:])


def test_pi_grid_and_parse():
    assert len(fam.PI) == 3 * 5 * (6 + 6) == 180
    assert fam.parse("p40_20_8_e4") == ("pi", 40.0, 20.0, 8.0, "4")
    assert fam.parse("p70_120_2_e5") == ("pi", 70.0, 120.0, 2.0, "5")
    for bad in ("p40_20_2_e4", "p40_20_16_e5", "p30_20_8_e4", "p40_15_8_e4"):
        with pytest.raises(ValueError):
            fam.parse(bad)


def test_ad_ids():
    assert fam.ad_id(0.5, "f20_8") == "ad0p5_f20_8" and fam.parse("ad0p5_f20_8") == ("ad", 0.5, 20.0, 8.0)
    assert fam.parse(fam.ad_id(2.0, "f120_16")) == ("ad", 2.0, 120.0, 16.0)
    for eta, fb in ((1.5, "f20_8"), (1.0, "c800"), (1.0, "f20_9")):
        with pytest.raises(ValueError):
            fam.ad_id(eta, fb)
    with pytest.raises(ValueError):
        fam.parse("ad3_f20_8")


def test_switch_matches_d2_on_d2_members_and_refuses_non_g():
    for g in d2.G:
        m1 = SimpleNamespace(q=1234.0, K_F=20.0, n_crit=8.0)
        m2 = SimpleNamespace(q=1234.0, K_F=20.0, n_crit=8.0)
        d2.switch(m1, g)
        fam.switch(m2, g)
        assert vars(m1) == vars(m2)
    m = SimpleNamespace(q=1500.0, K_F=20.0, n_crit=8.0)
    fam.switch(m, "c400")
    assert (m.q, m.K_F) == (400.0, 0.0)
    fam.switch(m, "f120_16")
    assert (m.q, m.K_F, m.n_crit) == (400.0, 120.0, 16.0)
    for bad in ("p40_20_8_e4", "ad1_f20_8", "NC"):
        with pytest.raises(ValueError):
            fam.switch(m, bad)


def test_ties_and_rank():
    d = {"c800": [1, 2, 3], "c400": [1, 2, 3], "f10_6": [0, 9]}
    assert fam.best_by_median(d, fam.G) == "c400"            # tie -> earlier in G order
    a = {"c800+back": [1.0], "c800": [1.0]}
    assert fam.best_by_median(a, fam.A) == "c800"            # stay before back
    assert fam.rank("c400+back") == (True, 0)
    assert fam.argmin_tie({"x": 1, "y": 1}, ["y", "x"]) == "y"


def test_grid_edges_every_dimension():
    assert fam.grid_edges("c400") == ["rate=400"] and fam.grid_edges("c2600+back") == ["rate=2600"]
    assert fam.grid_edges("f120_16") == ["K_F=120", "n_crit=16"] and fam.grid_edges("f40_10") == []
    assert fam.grid_edges("p20_10_6_e4") == ["K_P=20", "K_I=10", "n_crit_e4=6"]
    assert fam.grid_edges("p40_40_12_e5") == ["n_crit_e5=12"]
    assert fam.grid_edges("ad0p5_f40_10") == ["eta=0.5"] and fam.grid_edges("ad1_f40_10") == []
