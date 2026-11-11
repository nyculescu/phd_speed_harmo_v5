"""EV part 2 (v505_ev_informed_rule.md v2 §3, §5): job plans, picks and the reading, on planted rows."""
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "docs/research/v505"))
import ev2  # noqa: E402
import v5  # noqa: E402

need = pytest.mark.skipif(not v5.S6_JOBS.is_file(), reason="stored job files not on this machine")


@need
def test_fx_and_sw_plans(tmp_path):
    fx = ev2.plan("ev_tune_fx", tmp_path, 20.0)
    assert len(fx["arms"]) == 21 and fx["seed_range"] == [7_488_280, 7_488_339] and "copy" not in str(sorted(fx["arms"]))
    assert all("measure" not in c for c in fx["arms"].values())
    sw = ev2.plan("ev_tune_sw", tmp_path, 20.0, {"fx": "p333"})["arms"]
    ip = [n for n in sw if "|ip_" in n]
    swa = [n for n in sw if "|swa_" in n]
    swb = [n for n in sw if "|swb_" in n]
    assert (len(ip), len(swa), len(swb)) == (27, 81, 54)     # p333's uniform 0.8 s drops L = 3 as a duplicate of FX
    c = sw["EVA20|ip_d1000_L1_a60"]["ctrl"]
    assert c["told"]["base"] == {"cav_rule": [3, 3, 3]} and c["env"]["perturb"]["limit_kmh"] == 20.0 and c["env"]["hold"] == 10.0
    assert len([n for n in ev2.plan("ev_tune_sw", tmp_path, 20.0, {"fx": "3e"})["arms"] if "|ip_" in n]) == 36


@need
def test_eval_and_va_plans(tmp_path):
    sw = ev2.plan("ev_tune_sw", tmp_path, 20.0, {"fx": "os0_10_10"})["arms"]
    p = {"fx": "os0_10_10", "sw_cfg": sw["EVA20|swa_r1000_th13_L1_a60"], "ip_cfg": sw["EVA20|ip_d1000_L1_a60"]}
    j = ev2.plan("ev_eval", tmp_path, 20.0, p)
    assert sorted(j["arms"]) == ["EVA20|FX", "EVA20|IP", "EVA20|N", "EVA20|SW", "EVA20|nc", "S|FX", "S|N", "S|SW", "S|nc"]
    assert "perturb" not in j["arms"]["S|SW"]["ctrl"].get("env", {}) and "detect" in j["arms"]["S|SW"]["ctrl"]
    assert all(c["measure"].endswith("/st") for c in j["arms"].values()) and j["seed_range"] == [7_488_340, 7_488_459]
    va = ev2.plan("ev_va", tmp_path, 20.0, p, a=3.0)
    assert "EVA20V3|IP" in va["arms"] and "SV3|SW" in va["arms"] and all(c["ramp2_assertive"] == 3.0 for c in va["arms"].values())


def rows(seeds, gain_pct=0.0, ip_pick_better=True, seed=2):
    """A cell where the untold arms share one delay and IP saves gain_pct of the event cost; S rows below."""
    rng = np.random.default_rng(seed)
    T = {}
    for s in seeds:
        base = 150_000.0 + rng.normal(0, 4_000)
        cost = 30_000.0 + rng.normal(0, 3_000)
        for u in ("N", "FX", "SW", "nc"):
            d = base + rng.normal(0, 1_500)
            T.setdefault(("EVA20", u), {})[s] = {"all_delay": d, "passed": 2_000.0, "collisions": 0.0, "b45_step": 100.0}
            T.setdefault(("S", u), {})[s] = {"all_delay": d - cost}
        T.setdefault(("EVA20", "IP"), {})[s] = {"all_delay": base - gain_pct / 100.0 * cost + rng.normal(0, 1_500), "passed": 2_000.0,
                                                "collisions": 0.0, "b45_step": 100.0}
    return T


@pytest.fixture
def no_null(monkeypatch):
    monkeypatch.setattr(ev2.read6, "swap_null", lambda *a, **k: 0.0)


def test_reading_gain_kill_and_kill_by_pick(no_null, monkeypatch):
    seeds = list(range(120))
    monkeypatch.setattr(ev2, "location_share", lambda *a, **k: 0.1)
    p = {"bU": "FX", "kill_by_pick": False}
    assert ev2.read(rows(seeds, 25.0), p, "EVA20", seeds)["outcome"] == "GAIN"
    monkeypatch.setattr(ev2, "gain_off", None, raising=False)
    T = rows(seeds, 0.0)
    monkeypatch.setattr(ev2.read6, "location", lambda r: {"delay|1|rest": r["all_delay"]})
    r = ev2.read(T, p, "EVA20", seeds)
    assert r["outcome"] == "KILL" and "not excluded" in r["kill_sentence"] and r["lane_end_bound"] is False
    assert ev2.read(T, {**p, "kill_by_pick": True}, "EVA20", seeds)["outcome"] == "KILL BY PICK"


def test_failed_null_blocks_the_reading(monkeypatch):
    seeds = list(range(120))
    monkeypatch.setattr(ev2.read6, "swap_null", lambda *a, **k: 0.2)
    assert ev2.read(rows(seeds, 25.0), {"bU": "FX", "kill_by_pick": False}, "EVA20", seeds)["outcome"] == ev2.read6.FAILED_NULL


def test_picks_paired_and_kill_by_pick():
    seeds = list(range(60))
    rng = np.random.default_rng(5)
    T, jobs = {}, {}
    for n, shift in (("p333", 0.0), ("os0_10_10", -500.0), ("ip_a", -3_000.0), ("ip_b", 200.0), ("swa_x", -1_000.0), ("swb_y", 100.0)):
        T[("EVA20", n)] = {s: {"all_delay": 150_000.0 + s * 10.0 + shift + rng.normal(0, 200)} for s in seeds}
        jobs[f"EVA20|{n}"] = {"name": n}
    p = ev2.picks(T, "EVA20", "os0_10_10", seeds, jobs)
    assert p["ip"] == "ip_a" and not p["kill_by_pick"] and p["sw"] == "swa_x" and p["bU"] == "SW"
    for s in seeds:
        T[("EVA20", "ip_a")][s]["all_delay"] += 5_000.0
    assert ev2.picks(T, "EVA20", "os0_10_10", seeds, jobs)["kill_by_pick"]


def test_merge_joins_seeds_of_the_same_arm():
    A = {("EVA20", "p333"): {1: {"all_delay": 1.0}}}
    B = {("EVA20", "p333"): {2: {"all_delay": 2.0}}, ("EVA20", "3e"): {2: {"all_delay": 3.0}}}
    assert ev2.merge(A, B) == {("EVA20", "p333"): {1: {"all_delay": 1.0}, 2: {"all_delay": 2.0}}, ("EVA20", "3e"): {2: {"all_delay": 3.0}}}
