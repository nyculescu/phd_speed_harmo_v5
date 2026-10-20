"""P1b (p1b_addendum.md, V108), pure tests: amber and minimum red (R2), q clip in every law (R2), PI switch carry-over
(R3), action set A(q) (R1), runner assignment (R4), runner rows and queue flags (R5, B4), seeds (B5), sentinel,
launch rules and run counts."""
import json
import os
import subprocess
from types import SimpleNamespace

import numpy as np
import pytest

from v5b.d1 import plant
from v5b.d1.config import PYTHON_BIN, REPO_ROOT, clean_sumo_env
from v5b.d2.incidents import INCIDENTS, NONE
from v5b.p1 import family as fam
from v5b.p1 import run as p1run
from v5b.p1b import analysis as an
from v5b.p1b import family as fb
from v5b.p1b import meters as mt
from v5b.p1b import run as rs
from v5b.p1b import runners as rn
from v5b.p1b.episode import make_spec


# ---------------------------------------------------------------- meter (B1, R2, R3)
def _runs(states):
    out = []
    for s in states:
        if out and out[-1][0] == s:
            out[-1][1] += 1
        else:
            out.append([s, 1])
    return out


def _check_signal(states):
    runs = _runs(states)
    assert runs[0][0] == "G"
    nxt = {"G": "y", "y": "r", "r": "G"}
    for (a, _), (b, _) in zip(runs, runs[1:]):
        assert b == nxt[a], (a, b)
    for s, n in runs[:-1]:                     # the last run may be cut by the end of the horizon
        if s == "G":
            assert n == 6
        elif s == "y":
            assert n == 3                       # amber never cut
        else:
            assert n >= 2                       # red >= 2 s
    return runs


@pytest.mark.parametrize("seed", range(6))
def test_amber_never_cut_and_red_at_least_2s(seed):
    rng = np.random.default_rng(seed)
    m = mt.P1bMeter("c1600", read=lambda e, t: float(rng.integers(0, 40)), set_state=lambda s: None)
    plans = list(fam.G) + list(fam.PI)
    states = []
    for k in range(4000):
        t = 40.0 + k
        u = rng.random()
        if u < 0.05:
            m.set_law(plans[rng.integers(len(plans))])
        elif u < 0.15:                            # arbitrary jumps of q (any law, any switch)
            m.q = float(rng.choice([mt.Q_MIN, mt.Q_CAP, rng.uniform(mt.Q_MIN, mt.Q_CAP)]))
        states.append(m.step(t))
    _check_signal(states)


def test_cycle_and_states():
    assert mt.cycle_s(2618.0) == pytest.approx(28800 / 2618) and mt.cycle_s(2618.0) >= 11.0
    assert mt.cycle_s(5000.0) == 11.0 and mt.cycle_s(200.0) == 144.0
    assert [mt.state_of(x) for x in (0, 5.99, 6, 8.99, 9, 143)] == ["G", "G", "y", "y", "r", "r"]
    m = mt.P1bMeter("c2600", read=lambda e, t: 0.0, set_state=lambda s: None)
    runs = _check_signal([m.step(40.0 + k) for k in range(600)])
    assert min(n for s, n in runs[:-1] if s == "r") == 2                  # the minimum red is reached at the top rate


@pytest.mark.parametrize("cid,n,bound", [("c2600", 0.0, None), ("f120_16", 0.0, mt.Q_CAP), ("f120_6", 60.0, mt.Q_MIN),
                                         ("p70_120_16_e4", 0.0, mt.Q_CAP), ("p70_120_2_e5", 60.0, mt.Q_MIN),
                                         ("ad2_f120_16", 0.0, mt.Q_CAP), ("ad2_f120_6", 60.0, mt.Q_MIN)])
def test_q_clip_in_every_law(cid, n, bound):
    m = mt.P1bMeter(cid, read=lambda e, t: n, cum_out=lambda t: 0.0, set_state=lambda s: None)
    qs = []
    for k in range(900):
        m.step(40.0 + k)
        qs.append(m.q)
    assert all(mt.Q_MIN <= q <= mt.Q_CAP for q in qs)
    assert qs[-1] == (2600.0 if bound is None else bound)


def test_pi_switch_carries_q_anchor_grid_and_no_p_kick():
    reads = []

    def read(e, t):
        n = 20.0 if t < 80 else 5.0
        reads.append((e, t))
        return n

    a = mt.P1bMeter("c1600", read=read, set_state=lambda s: None)
    b = mt.P1bMeter("c1600", read=lambda e, t: 20.0, set_state=lambda s: None)
    sa, sb = [], []
    for k in range(70):
        t = 40.0 + k
        if t == 85.0:
            a.set_law("p70_10_8_e5")
            assert a.q == 1600.0 and a.n_prev is None                   # q carries over
        sa.append(a.step(t))
        sb.append(b.step(t))
        if t == 99.0:
            assert a.q == 1600.0                                        # no update before the grid tick 100
        if t == 100.0:
            assert a.q == 1600.0 + 10.0 * (8.0 - 5.0)                    # n(k-1) = n(k): no K_P term
            assert reads[-1] == ("5", 100.0)                            # the plan's detector
    assert sa[:60] == sb[:60]                                           # same anchor until q changes at t = 100
    assert [t for e, t in reads] == [70.0, 100.0]                       # the 30-s grid from t = 40 carries over
    a.step(130.0)
    assert a.q == 1630.0 + 10.0 * (8.0 - 5.0)                           # later updates: P term uses n(k-1)
    a.set_law("c1600")                                                  # back to N (G rule)
    assert a.law == "fb" and a.q == 1600.0 and a.K_F == 0.0
    a.set_law("f20_8")
    a.set_law("p40_20_8_e4")
    assert a.n_prev is None and a.edge == "4"


def test_ad_is_not_a_plan():
    m = mt.P1bMeter("c1600", read=lambda e, t: 1.0, set_state=lambda s: None)
    with pytest.raises(ValueError):
        m.set_law("ad1_f20_8")


# ---------------------------------------------------------------- family (R1)
def test_action_set_120_and_order():
    gpi = fam.PI[:10]
    A = fb.actions(fam.G, gpi)
    assert len(A) == 120 and A[:100] == fam.A
    assert A[100:110] == gpi and A[110:] == tuple(g + "+back" for g in gpi)
    assert fb.parse_action("p40_20_8_e4+back") == ("p40_20_8_e4", True)
    with pytest.raises(ValueError):
        fb.parse_action("ad1_f20_8")
    with pytest.raises(ValueError):
        fb.actions(fam.G, ("c800",))


def test_top_pi_ties_in_pi_order():
    pooled = {p: [100.0 + (i % 5)] for i, p in enumerate(fam.PI)}
    top = fb.top_pi(pooled, fam.PI, 10)
    assert len(top) == 10
    zero = [p for i, p in enumerate(fam.PI) if i % 5 == 0]
    assert top == tuple(zero[:10])
    with pytest.raises(ValueError):
        fb.top_pi({fam.PI[0]: [1.0]}, fam.PI, 10)


# ---------------------------------------------------------------- runners (B2, R4)
def test_runner_assignment_same_vehicles_every_arm_nested_and_s0_identical(tmp_path):
    def dem():
        return plant.demand(7_400_600, [(0.0, 940.0, 2000.0)])
    base = dem()
    base.write(tmp_path / "base.xml")
    d0 = dem()
    assert rn.apply_runners(d0, 7_400_600, 0.0) == set()
    d0.write(tmp_path / "s0.xml")
    assert (tmp_path / "base.xml").read_bytes() == (tmp_path / "s0.xml").read_bytes()
    a, b = dem(), dem()                                   # two arms: the route file does not depend on the arm
    ra, rb = rn.apply_runners(a, 7_400_600, 0.3), rn.apply_runners(b, 7_400_600, 0.3)
    assert ra == rb and a.vehicles == b.vehicles
    assert [v[:3] for v in a.vehicles] == [v[:3] for v in base.vehicles]       # same departures and routes
    r10 = rn.apply_runners(dem(), 7_400_600, 0.1)
    assert r10 < ra                                                             # nested
    n = len(base.vehicles)
    assert abs(len(ra) / n - 0.3) < 0.06 and abs(len(r10) / n - 0.1) < 0.04
    assert rn.apply_runners(dem(), 7_400_601, 0.3) != ra                        # per seed
    xml = rn.runner_vtypes(plant.vtypes_xml())
    for t in ("human_run", "av_run"):
        line = [ln for ln in xml.splitlines() if f'id="{t}"' in ln][0]
        assert all(f'{k}="{v}"' in line for k, v in rn.RUNNER_JM.items())
    assert rn.RUNNER_JM == {"jmDriveAfterYellowTime": "3", "jmDriveAfterRedTime": "1.5", "jmDriveRedSpeed": "13.9"}
    assert rn.SHARES == (0.10, 0.30) and rn.RUNNER_SALT not in (3301, 5113, 2027, 4049)


def test_runner_spec_rules():
    s = make_spec("c1600", None, False, "block", 2000.0, 1, rs=0.3)
    assert s["key"].endswith("_rs0p3_block_q2000_s1")
    assert make_spec("c1600", None, False, "block", 2000.0, 1)["key"] == "c1600_block_q2000_s1"   # P1 key at s = 0
    for kw in ({"k": 1}, {"vsl_b": 0.4}):
        with pytest.raises(ValueError):
            make_spec("c1600", None, False, "block", 2000.0, 1, rs=0.3, **kw)
    assert make_spec("c1600", "p40_20_8_e4", True, "block", 2000.0, 1)["post"] == "p40_20_8_e4"
    with pytest.raises(ValueError):
        make_spec("p40_20_8_e4", "c800", False, "block", 2000.0, 1)          # plans start from N (G)


# ---------------------------------------------------------------- analysis (R5, R6, R7, B4)
G3 = ("c800", "c1600", "f20_8")
GPI2 = ("p40_20_8_e4", "p20_10_6_e5")
A_Q = {"1600": fb.actions(G3, GPI2), "2000": fb.actions(G3, GPI2)}
SEEDS = tuple(range(7_400_006, 7_400_014))


def _arms():
    a = {"N": "c1600", "FX": "c800", "FB": "f20_8", "PI": "p40_20_8_e4", "AD": "ad1_f20_8", "ID": "f20_8+back",
         "IP": {"slow": "p20_10_6_e5", "block": "c800+back"}, "G_PI": list(GPI2)}
    a["prev"] = {str(p): {x: a[x] for x in an.L0} for p in an.PIS}
    return {"1600": dict(a), "2000": dict(a)}


def _world(arms):
    def f(s):
        b = (300.0 + 10.0 * (s["seed"] % 7) + 3.0 * s["k"]) * (1.0 + s["rs"])   # runners: +rs
        a = arms[str(int(s["q"]))]
        if s["incident"] == NONE:
            return 0.5 * b + (20.0 if s["fa"] else 0.0) if s["pre"] != "NC" else 0.75 * b
        if s["post"] is None:
            return 1.5 * b if s["pre"] == "NC" else b + {"c1600": 0, "c800": 1, "f20_8": 2}.get(s["pre"], 3)
        act = s["post"] + ("+back" if s["back"] else "")
        m = 0.8 if act == a["ID"] else 0.7 + 0.002 * s["d"] if act == a["IP"][s["incident"]] else \
            1.0 if s["post"] == a["N"] else 0.95
        return m * b
    return f


def _res(specs, f, spill=()):
    out = {}
    for s in specs:
        out[s["key"]] = {**s, "delay_s": float(f(s)), "valid": True, "teleports": 0, "served_ctrl_vph": 1500.0,
                         "ttt_ctrl_vehh": 10.0, "ttt_full_vehh": 12.0, "max_queue": 40, "hash": s["key"],
                         "emergency_meter": 1, "emergency_stops": 0, "collisions": 0,
                         "approach_red_mps": {"n": 3, "median": 2.0, "max": 11.0, "n_ge_10": 1},
                         "red_cross_share": 0.02 + s["rs"] / 10, "runner_red_cross_share": 0.1 if s["rs"] else None,
                         "commanded_mean_vph": 1500.0, "discharge_vph": {"G": 1300.0, "y": 150.0, "r": 20.0},
                         "max_queue_m": 410.0 if s["pre"] in spill and s["post"] is None else 120.0,
                         "max_queue_halted_veh": 30, "avail_m": 410.0}
    return out


def test_eval_specs_counts_with_gpi_and_runner_rows():
    arms = _arms()
    seeds = tuple(range(7_400_600, 7_400_700))
    g10 = GPI2 + tuple(p for p in fam.PI if p not in GPI2)[:8]            # IP's PI plan is in G_PI (as tuned)
    g10b = GPI2 + tuple(p for p in fam.PI if p not in GPI2)[8:16]
    A = {"1600": fb.actions(fam.G, g10), "2000": fb.actions(fam.G, g10b)}
    sp = an.eval_specs(arms, A, seeds)
    main = [s for s in sp if s["post"] and not s["k"] and not s["fa"] and not s["d"] and not s["c"]
            and s["vsl_b"] is None and not s["rs"]]
    assert len(main) == 120 * 2 * 2 * 100 and len([s for s in sp if s["k"]]) == 4 * len(main)
    run = [s for s in sp if s["rs"]]
    assert {s["rs"] for s in run} == {0.1, 0.3} and len(run) == 2 * 7 * 4 * 100
    assert {s["post"] for s in main if s["q"] == 1600.0} - set(fam.G) == set(g10)
    assert len({s["key"] for s in sp}) == len(sp)


def test_evaluate_runner_rows_and_new_columns():
    arms = _arms()
    sp = an.eval_specs(arms, A_Q, SEEDS)
    res = _res(sp, _world(arms), spill=("c800",))
    ev = an.evaluate(res, SEEDS, A_Q, arms, log=lambda m: None)
    assert ev["S1"]["S1a_pass"] and ev["S1"]["S1b_pass"]
    rr = ev["runner_rows"]
    assert set(rr) == {f"s{s:g}_{i}_q{q}" for s in rn.SHARES for i in INCIDENTS for q in (1600, 2000)}
    r = rr["s0.3_block_q2000"]
    assert r["n_seeds"] == len(SEEDS)
    assert r["ID_vs"]["N"]["all_seeds"]["rel"] == pytest.approx(0.2, abs=0.01)          # ID 20 % below N at s = 0.3
    assert r["IP_vs_ID"]["all_seeds"]["rel"] == pytest.approx(1 - 0.7 / 0.8, abs=1e-6)
    for x in an.RUNNER_ARMS:
        assert r["vs_self_s0"][x]["all_seeds"]["rel"] == pytest.approx(-0.3, abs=0.01)  # leakage vs itself at 0
    assert r["arms"]["N"]["median_red_cross_share"] == pytest.approx(0.05)
    row = ev["table1_operating_map"]["block_q2000"]["arms"]["FX"]
    assert row["spill_share"] == 1.0 and row["avail_m"] == 410.0 and row["emergency_meter_total"] == len(SEEDS)
    assert row["approach_red_mps_max"] == 11.0 and row["median_discharge_vph"]["r"] == 20.0
    assert ("table1", "block_q2000", "FX", 1.0) in ev["queue_limit_flags"]
    assert not [f for f in ev["queue_limit_flags"] if f[2] == "N"]
    assert ev["table1_operating_map"]["slow_q1600"]["controllers"]["IP"] == "p20_10_6_e5"


def test_runner_rows_drop_seeds_missing_runs():
    arms = _arms()
    sp = an.eval_specs(arms, A_Q, SEEDS)
    res = _res(sp, _world(arms))
    k = an.fixed("c800", "slow", 2000.0, SEEDS[0], rs=0.1)["key"]
    del res[k]
    rr = an.runner_rows(res, SEEDS, arms)
    assert rr["s0.1_slow_q2000"]["n_seeds"] == len(SEEDS) - 1 and rr["s0.3_slow_q2000"]["n_seeds"] == len(SEEDS)


# ---------------------------------------------------------------- runner: seeds, sentinel, launch (B5)
def test_seed_ranges_as_approved():
    S = rs.SEEDS
    assert S["tcheck"] == tuple(range(7_400_260, 7_400_280))
    assert S["tune"] == tuple(range(7_400_300, 7_400_340))
    assert S["eval"] == tuple(range(7_400_600, 7_400_700))
    blocks = [set(v) for v in S.values()]
    assert sum(len(b) for b in blocks) == len(set().union(*blocks))
    p1 = set().union(*(set(v) for v in p1run.SEEDS.values()))
    assert not p1 & set().union(*blocks)                                        # fresh seeds (not P1's)
    assert all(7_400_010 <= s <= 7_400_699 for b in blocks for s in b)          # 700-999 untouched
    assert all(s in rs.CALIB_ONLY for v in rs.SMOKE_SEEDS.values() for s in v)
    from v5b.p1.meters import replicate_seeds
    reps = {replicate_seeds(s, k)["sumo_seed"] for s in S["eval"] for k in (1, 2, 3, 4)}
    assert min(reps) == 17_400_600 and max(reps) == 47_400_699
    t3 = [p for p in rs.t3_specs(S["tcheck"][0]) if p[0]["k"]]
    assert len(t3) == 1 and replicate_seeds(t3[0][0]["seed"], 1)["sumo_seed"] == 17_400_260


def test_sentinel_paths_and_run_once(tmp_path):
    if "V5B1_RUNS" not in os.environ:
        assert str(rs.SENTINEL) == "/home/catalin/work/phd/v5b1_runs/P1B_EVAL_STARTED.json"
        assert str(rs.DEFAULT_OUT) == "/home/catalin/work/phd/v5b1_runs/p1b/v108"
    env = {**clean_sumo_env(), "V5B1_RUNS": str(tmp_path / "root")}
    o = subprocess.run([PYTHON_BIN, "-c", "from v5b.p1b import run as r; print(r.SENTINEL, r.DEFAULT_OUT)"],
                       cwd=REPO_ROOT, env=env, capture_output=True, text=True).stdout.split()
    assert o == [str(tmp_path / "root" / "P1B_EVAL_STARTED.json"), str(tmp_path / "root" / "p1b" / "v108")]
    sen, out = tmp_path / "P1B.json", tmp_path / "p1b" / "v108"
    rs.check_sentinel(out, False, "abc", sentinel=sen)
    rs.write_sentinel(out, "abc", "sha", {"x": 1}, sentinel=sen)
    with pytest.raises(SystemExit):
        rs.check_sentinel(out, False, "abc", sentinel=sen)
    with pytest.raises(SystemExit):
        rs.check_sentinel(out, True, "def", sentinel=sen)
    rs.check_sentinel(out, True, "abc", sentinel=sen)
    rs.write_sentinel(out, "zzz", "sha", {}, sentinel=sen)
    assert json.loads(sen.read_text())["code_commit"] == "abc"


def test_out_dir_and_launch_rules(monkeypatch, tmp_path):
    monkeypatch.setattr(rs, "ALLOWED_ROOTS", (tmp_path,))
    with pytest.raises(SystemExit):
        rs.check_out_dir(REPO_ROOT / "runs_here", False)
    with pytest.raises(SystemExit):
        rs.check_out_dir(tmp_path.parent / "elsewhere", False)
    out = tmp_path / "p1b"
    rs.check_out_dir(out, False)
    (out / "runs").mkdir(parents=True)
    (out / "runs" / "x.json").write_text("{}")
    with pytest.raises(SystemExit):
        rs.check_out_dir(out, False)
    rs.check_out_dir(out, True)
    (out / "result.json").write_text("{}")
    with pytest.raises(SystemExit):
        rs.check_out_dir(out, True)
    a = SimpleNamespace(workers=32, cpu_limit=0.90, smoke=False, confirm_run_once=True)
    rs.check_launch(a, dirty=False)
    for bad, dirty in (({"confirm_run_once": False}, False), ({}, True), ({"workers": 101}, False),
                       ({"cpu_limit": 0.95}, False), ({"smoke": True, "workers": 9}, False)):
        with pytest.raises(SystemExit):
            rs.check_launch(SimpleNamespace(**{**vars(a), **bad}), dirty=dirty)
    rs.check_launch(SimpleNamespace(**{**vars(a), "smoke": True, "workers": 8}), dirty=True)
    with pytest.raises(SystemExit):
        rs.main(["--smoke"])                                                    # smoke needs its own --out


def test_pool_reuse_checks_runner_share_and_signal():
    s = make_spec("c1600", None, False, "block", 2000.0, 1, rs=0.3)
    stored = {**s, "code_commit": "abc", "signal": mt.SIGNAL}
    assert p1run.reuse_mismatch(stored, s, "abc", mt.SIGNAL, rs.Pool.FIELDS) == []
    assert "rs" in p1run.reuse_mismatch({**stored, "rs": 0.1}, s, "abc", mt.SIGNAL, rs.Pool.FIELDS)
    assert p1run.reuse_mismatch(stored, s, "abc", "continuous", rs.Pool.FIELDS) == ["signal"]
    assert rs.Pool.MODULE == "v5b.p1b.episode" and p1run.Pool.MODULE == "v5b.p1.episode"     # P1 unchanged
    assert set(rs.KEEP) > set(p1run.KEEP)


def test_t3_and_run_counts():
    t3 = rs.t3_specs(7_400_260)
    assert len(t3) == 15 and all(p[0]["key"] != p[1]["key"] for p in t3)
    assert any(p[0]["post"] in fam.PI for p in t3) and any(p[0]["rs"] for p in t3)
    rc = rs.run_counts()
    assert rc["eval_runner_rows"] == 5600 and rc["eval_replicates"] == 4 * 120 * 2 * 2 * 100
    assert 300_000 < rc["total"] < 360_000


def test_tool_checks_run_on_a_synthetic_world(tmp_path):
    """P1's tool-check stage, carried over to P1b (A = G x {stay, back}; fixed V100 decisions)."""
    from test_p1_runner import _FakePool, _tc_world
    seeds = tuple(range(7_400_000, 7_400_006))
    pool = _FakePool(lambda s: {**_tc_world()(s), "rs": s["rs"]}, tmp_path)
    tc = rs.stage_tcheck(pool, seeds, ("c800", "c1600", "f20_8"), gate_views=rs.DECISIONS["gate_views"],
                         tv_window=rs.DECISIONS["tv_t0_window"], t3_replicate=True)
    assert tc["T0"]["pass"] and tc["TV_T0"]["pass"] and len(tc["T3"]) == 15
