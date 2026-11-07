"""Round 2 (round_2.md): unit tests of the new classes, cma2's round-2 options and decide2's rules, on planted rows."""
import json
import sys
from pathlib import Path

import numpy as np
import pytest
import torch

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "docs/research/round2"), str(ROOT / "docs/research/round1"), str(ROOT)]

import cma2  # noqa: E402
import decide2 as dc  # noqa: E402
from v5b.fleet import b_env as be, c_train as ct  # noqa: E402

E3 = ROOT / "docs/research/round2/3e"
FINAL_RUNS = Path("/home/catalin/work/phd/v5b1_runs/round2_remote/cma3e/final_runs.jsonl")


class FakeNet:
    def __init__(self, logits):
        self.l = torch.tensor(logits, dtype=torch.float32)

    def logits(self, x):
        return self.l.repeat(len(x), 1)


class FakeMember:
    def __init__(self, logits):
        self.net = FakeNet(logits)


def obs(xs, due=None):
    lo = np.zeros((len(xs), 16), np.float32)
    lo[:, 0] = np.array(xs) / 1000.0
    return ([f"v{i}" for i in range(len(xs))], lo, None, np.ones(len(xs), bool) if due is None else np.array(due))


def test_tailmean_mean_of_probabilities():
    t = ct.TailMean.__new__(ct.TailMean)
    # member 1 prefers level 0 strongly; member 2 prefers level 1 mildly: the mean probability picks level 0
    t.members = [FakeMember([4.0, 0.0, 0.0, 0.0]), FakeMember([0.0, 0.5, 0.0, 0.0])]
    assert set(t(obs([0, 1])).values()) == {0}
    t.members = [FakeMember([0.0, 2.0, 0.0, 0.0]), FakeMember([0.0, 2.0, 0.0, 0.0])]
    assert set(t(obs([0])).values()) == {1}
    assert t(obs([0], due=[False])) == {}


def test_zoneswitch_sides():
    rule = lambda o: {v: 7 for v in o[0]}
    pol = lambda o: {v: 9 for v, d in zip(o[0], o[3]) if d}
    sw = ct.ZoneSwitch(rule, pol, 594.72)
    out = sw(obs([100.0, 594.71, 594.72, 1500.0], due=[True, False, True, False]))
    assert out == {"v0": 7, "v1": 7, "v2": 9}     # upstream: the rule for every vehicle; downstream: the policy for due vehicles only
    assert ct.ZoneSwitch(rule, pol, -1e9)(obs([100.0, 2000.0])) == {"v0": 9, "v1": 9}
    assert ct.ZoneSwitch(rule, pol, 1e9)(obs([100.0, 2000.0])) == {"v0": 7, "v1": 7}


def test_zone_own_state_matches_old_code():
    zones = json.load(open(E3 / "final.json"))["pick"]["params"]
    r = be.ZoneOwnState(zones)
    rng = np.random.default_rng(1)
    lo = rng.random((500, 16)).astype(np.float32)
    lo[:, 0] = rng.uniform(-0.5, 3.0, 500)
    lo[:, 2] = rng.random(500) > 0.8
    out = r(([f"v{i}" for i in range(500)], lo))
    z = be.zone_of_3e(lo[:, 0] * 1000.0, lo[:, 2])
    hit = (lo[:, 4] * (100.0 / 3.6) < r.th[z]) & (lo[:, 15] * 40.0 >= r.crowd[z])
    assert list(out.values()) == np.where(hit, r.level[z], r.free[z]).tolist()


def test_cma2_defaults_reproduce_3e_objective():
    """With the defaults, the objective on 3E's stored final rows reproduces final.json."""
    if not FINAL_RUNS.exists():
        pytest.skip("3E's final rows not on this machine")
    rows = [json.loads(x) for x in open(FINAL_RUNS)]
    fin = json.load(open(E3 / "final.json"))
    ref = [r for r in rows if r["name"] == "ref"]
    for c in fin["candidates"]:
        o = cma2.objective([r for r in rows if r["name"] == c["name"]], ref)
        assert o["loss"] == pytest.approx(c["loss"], abs=1e-9)


def test_cma2_seed_block_and_start():
    with pytest.raises(SystemExit):
        cma2.check_seeds([7_440_740])
    cma2.check_seeds([7_440_740, 7_440_779], cma2.block_of("7440740-7440779"))
    with pytest.raises(SystemExit):
        cma2.check_seeds([7_440_739], cma2.block_of("7440740-7440779"))
    x = cma2.decode(cma2.start("os0_10_10"))
    assert x[1]["level"] == 0 and x[1]["th"] == 10.0 and x[1]["crowd"] == 10 and x[0]["th"] == 1.0


def test_cma2_shortlist_norm_and_convergence():
    recs = [{"gen": g, "idx": i, "loss": base + i, "params": [{"g": g, "i": i}]} for g, base in ((0, 0.0), (1, -30.0)) for i in range(3)]
    raw = cma2.shortlist(recs, 2, "raw")
    norm = cma2.shortlist(recs, 2, "norm")
    assert [(r["gen"], r["idx"]) for r in raw] == [(1, 0), (1, 1)]
    assert {(r["gen"], r["idx"]) for r in norm} == {(0, 0), (1, 0)}     # each generation's best ranks first once the window median is removed
    c = cma2.convergence([{"gen": g, "loss": -g} for g in range(20)])
    assert c["still_falling"] and c["generations"] == 20


def rows(vals: dict, key="all_delay", n=40, noise=0.0, seed=0):
    rng = np.random.default_rng(seed)
    base = rng.uniform(900, 1100, n)
    return {s: {"seed": s, key: float(base[s] * vals) + rng.normal(0, noise), "ttc_net": float(base[s] * vals)} for s in range(n)}


def table(spec: dict) -> dict:
    """spec: (cell, name) -> (delay factor, ttc factor), paired over 40 seeds with a shared base."""
    rng = np.random.default_rng(3)
    base_d, base_t = rng.uniform(900, 1100, 40), rng.uniform(900, 1100, 40)
    T = {}
    for (c, n), (fd, ft) in spec.items():
        T[(f"{c}|{n}", 5300.0)] = {s: {"seed": s, "all_delay": float(base_d[s] * fd), "ttc_net": float(base_t[s] * ft), "passed": 2000.0,
                                       "b3_step": 100.0, "collisions": 0.0, "alks_full_moving": 0.0} for s in range(40)}
    return T


def test_paths_and_harm():
    T = table({("X1", "k"): (0.97, 1.05), ("X1", "w"): (1.0, 1.0), ("X1", "b"): (1.015, 0.85), ("X1", "h"): (1.03, 0.9), ("X1", "t"): (1.0, 1.15)})
    A = lambda n: T[(f"X1|{n}", 5300.0)]
    a = dc.paths(A("k"), A("w"), dc.P95)
    assert a["a"] and not a["b"] and not a["harm"]
    b = dc.paths(A("b"), A("w"), dc.P95)
    assert b["b"] and not b["a"] and not b["harm"]     # 15 % less TTC at 1.5 % more delay: path (b), within the 2 % harm margin
    h = dc.paths(A("h"), A("w"), dc.P95)
    assert h["harm"] and not h["b"]                      # 3 % more delay, CI clear: harm
    t = dc.paths(A("t"), A("w"), dc.P95)
    assert t["harm"] and not t["better"]                 # 15 % more TTC: harm
    assert b["score"] == pytest.approx(max(b["delay"][0] / 2, b["ttc"][0] / 10))


def test_levels_and_ranking():
    assert dc.bonferroni(4) == pytest.approx((0.625, 99.375))
    assert dc.bonferroni(6)[1] == pytest.approx(100 - 2.5 / 6)
    res = {"2b": {"advances": True, "count": 10, "score": 1.0}, "1b": {"advances": True, "count": 10, "score": 2.0},
           "1d": {"advances": True, "count": 9, "score": 9.0}, "rep": {"advances": False, "count": 10, "score": 9.0}}
    assert dc.finalists(res) == ["1b", "2b"]
    res["2b"]["score"] = 2.0
    assert dc.finalists(res) == ["2b", "1b"]     # full tie: the Arms table's order


def test_follows():
    mk = lambda better, harm, cells, learners, score: {"T1": {"X1": {"t1_better": better, "harm": harm}, "X2": {"t1_better": False, "harm": False}},
                                                      "t2_cells": cells, "t2_learners": learners, "score": score}
    assert dc.follows({"2b": mk(True, False, 1, 5, 1.0)}, 2)["incumbent"] == "v3w"
    assert dc.follows({"2b": mk(True, False, 2, 9, 1.0), "1b": mk(True, False, 2, 10, 0.5)}, 2)["incumbent"] == "1b"
    assert dc.follows({"2b": mk(True, True, 2, 10, 1.0)}, 0)["incumbent"] == "v3w"


def test_share_ci():
    s = dc.share_ci(np.array([1.0] * 11 + [0.0] * 9))
    assert s[0] == pytest.approx(0.55) and s[1] < 0.55 < s[2]


def test_checkpoint_rule():
    # u250 within 2 % of os1_15_10 in both cells, u500 in one: u250; equal counts: fewer TTC seconds; full tie: u500
    T = table({("X1", "os1_15_10"): (1.0, 1.0), ("X2", "os1_15_10"): (1.0, 1.0),
               ("X1", "w0u250"): (1.01, 0.8), ("X2", "w0u250"): (1.01, 0.8), ("X1", "w0u500"): (1.01, 0.7), ("X2", "w0u500"): (1.05, 0.7),
               ("X1", "w1u250"): (1.0, 0.8), ("X2", "w1u250"): (1.0, 0.8), ("X1", "w1u500"): (1.0, 0.7), ("X2", "w1u500"): (1.0, 0.7),
               ("X1", "w2u250"): (1.0, 0.7), ("X2", "w2u250"): (1.0, 0.7), ("X1", "w2u500"): (1.0, 0.7), ("X2", "w2u500"): (1.0, 0.7)})
    assert [dc.d1.choose(T, "w", i) for i in range(3)] == [250, 500, 500]


def test_floor_kill_on_u500_and_e3_counting(monkeypatch):
    spec = {}
    for c in ("X1", "X2"):
        spec |= {(c, "p333"): (1.0, 1.0), (c, "nc"): (1.3, 0.6), (c, "os1_15_10"): (1.02, 0.8), (c, "3e"): (1.03, 0.7)}
        for i in range(5):
            spec |= {(c, f"w{i}u250"): (1.0, 0.6), (c, f"w{i}u500"): (1.0, 0.6), (c, f"b{i}u250"): (0.97, 0.6), (c, f"b{i}u500"): (0.97, 0.95)}
    T = table(spec)
    for k in list(T):
        for s in T[k]:
            T[k][s].update({"sev3": 1.0, "alks_full_moving": 0.0})
    monkeypatch.setattr(dc, "e3_rules", lambda cell: {"3e": []})
    st = dc.e3_status(T, "X1")
    assert not st["3e"]["counts"]     # 3 % more delay than p333: outside the 2 % filter
    o2 = {"cells": {c: {"forms": {"uniform": "p333", "own": "os1_15_10", "3e": "3e"}} for c in ("X1", "X2")}, "ctrl": {}}
    r = dc.advance(T, "2b", {i: 250 for i in range(5)}, {i: 250 for i in range(5)}, o2)
    assert r["better"] == ["X1", "X2"] and r["floor_kill"] == ["X1", "X2"] and not r["advances"]     # u500: only 5 % fewer TTC than p333


def test_cma2_admit_pick(tmp_path):
    rows = lambda name, d, c: [{"name": name, "q": 5300.0, "seed": s, "all_delay": 100.0 * d, "ttc_net": 100.0, "collisions": c if s == 0 else 0.0,
                                "passed": 1.0, "teleports": 0.0, "alks_b45_step": 0.0, "alks_full_events": 0.0, "finished_pct": 100.0} for s in range(3)]
    ref = rows("ref", 1.0, 0.0)
    a = cma2.objective(rows("a", 1.03, 0.0), ref, cap=1.0)
    b = cma2.objective(rows("b", 1.015, 0.0), ref, cap=1.0)
    assert a["per_level"]["5300.0"]["delay_pct"] == pytest.approx(3.0) and b["per_level"]["5300.0"]["delay_pct"] == pytest.approx(1.5)
    assert a["delay_over"] == pytest.approx(2.0) and b["delay_over"] == pytest.approx(0.5)     # the +1 % hinge
