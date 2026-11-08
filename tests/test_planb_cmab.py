"""Plan B's per-cell searches (planb.md §3.3) on a fake plant: checks, incumbent, admission, plateau label, replay, ceiling."""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "docs/research/planb"))
import cmab  # noqa: E402
import cma2  # noqa: E402

CALLS = []


def fake(jobs, workers):
    """Loss falls with the zones' levels and thresholds; p333 (cav_rule) is the reference. Seed noise is small and fixed."""
    for name, cfg, q, seed, rd in jobs:
        CALLS.append(name)
        ctrl = cfg["ctrl"]
        if "cav_rule" in ctrl:
            lv, th = 3 * 5, 0.0
        else:
            z = ctrl["zone_own_state"]["zones"]
            lv, th = sum(x["level"] for x in z), sum(x["th"] for x in z)
        e = (seed % 7) * 0.1
        yield (name, q, seed), {"q": q, "seed": seed, "ttc_net": 1000.0 - 5.0 * (15 - lv) + e, "all_delay": 200000.0 + 300.0 * (15 - lv) - 10.0 * th + e,
                                "collisions": 0.0, "passed": 3000.0, "teleports": 0.0, "alks_b45_step": 0.0, "alks_full_events": 0.0,
                                "finished_pct": 99.0, "alks_full_moving": 1.0}


def args(tmp, objective="ttc", start="p333"):
    return SimpleNamespace(out=str(tmp), cell="SURGE", objective=objective, start=start, workers=1)


def test_search_checks_incumbent_label_and_replay(tmp_path):
    CALLS.clear()
    cmab.search(args(tmp_path), runner=fake)
    checks = cma2.load(tmp_path / "checks.jsonl")
    assert [c["gen"] for c in checks] == list(range(20, 101, 10))
    assert all(len(c["candidates"]) <= cmab.K_CHECK + 1 for c in checks)
    losses = [c["incumbent"]["check_loss"] for c in checks if c["incumbent"]]
    assert losses == sorted(losses, reverse=True)     # the incumbent only improves
    pick = json.loads((tmp_path / "pick.json").read_text())
    assert pick["label"] in (cmab.LABEL_OK, cmab.LABEL_NOT) and pick["generations"] == 100
    meta = json.loads((tmp_path / "meta.json").read_text())
    assert meta["cma_seed"] == 20261108 and meta["pop"] == 24 and meta["seeds_per_gen"] == 16
    runs = cma2.load(tmp_path / "runs.jsonl")
    assert {r["seed"] for r in runs} == set(cmab.POOL)
    assert {r["seed"] for r in cma2.load(tmp_path / "check_runs.jsonl")} == set(cmab.CHECK)
    n = len(CALLS)
    assert n == len(runs) + len(cma2.load(tmp_path / "check_runs.jsonl"))
    before = {f: (tmp_path / f).read_bytes() for f in ("evals.jsonl", "checks.jsonl", "pick.json")}
    CALLS.clear()
    cmab.search(args(tmp_path), runner=fake)     # a restart replays everything and runs nothing
    assert CALLS == []
    assert {f: (tmp_path / f).read_bytes() for f in before} == before


def test_ceiling_stops_at_the_next_check(tmp_path):
    (tmp_path / "STOP_CEILING").write_text("")
    cmab.search(args(tmp_path, "delay"), runner=fake)
    pick = json.loads((tmp_path / "pick.json").read_text())
    assert pick["label"] == cmab.LABEL_CEIL and pick["generations"] == 20
    assert json.loads((tmp_path / "meta.json").read_text())["cma_seed"] == 20261118


def test_changed_settings_refuse_to_resume(tmp_path):
    (tmp_path / "STOP_CEILING").write_text("")
    cmab.search(args(tmp_path), runner=fake)
    with pytest.raises(SystemExit):
        cmab.search(args(tmp_path, start={"level": 1, "th": 15, "crowd": 10}), runner=fake)


def row(seed, d, ttc=100.0, coll=0.0, full=0.0):
    return {"q": 5300.0, "seed": seed, "all_delay": d, "ttc_net": ttc, "collisions": coll, "alks_full_moving": full}


def test_delay_objective_and_admission():
    ref = [row(s, 1000.0, coll=1.0, full=10.0) for s in range(5)]
    runs = [row(s, 980.0, coll=1.0 + (s == 0) + (s == 1), full=10.0) for s in range(5)]     # 2 % less delay, 2 extra collisions
    o = cmab.delay_objective(runs, ref, 5.0)
    assert o["delay_pct"] == pytest.approx(-2.0) and o["coll_extra"] == 2 and o["loss"] == pytest.approx(-2.0 + 10.0)
    assert not cmab.admissible("delay", o, runs, ref)     # collisions above p333's + 1
    runs[1]["collisions"] = 1.0
    assert cmab.admissible("delay", o, runs, ref)
    runs[0]["alks_full_moving"] = 10.0 + 6.0     # 56 against 50: above + max(2.5, 5)
    assert not cmab.admissible("delay", o, runs, ref)
    assert cmab.admissible("ttc", {"delay_pct": 2.0}, ref, ref) and not cmab.admissible("ttc", {"delay_pct": 2.01}, ref, ref)


def test_label_rule():
    c = lambda g, loss: {"gen": g, "objective": "ttc", "incumbent": {"check_loss": loss} if loss is not None else None}
    assert cmab.label([c(60, -10.0), c(100, -10.9)]) == cmab.LABEL_OK
    assert cmab.label([c(60, -10.0), c(100, -11.0)]) == cmab.LABEL_NOT     # exactly 1.0 is not below 1.0
    assert cmab.label([c(60, None), c(100, -11.0)]) == cmab.LABEL_NOT
    d = [{"gen": 60, "objective": "delay", "incumbent": {"check_loss": -3.0}}, {"gen": 100, "objective": "delay", "incumbent": {"check_loss": -3.4}}]
    assert cmab.label(d) == cmab.LABEL_OK


def test_start_vectors():
    assert cma2.decode(cmab.start_vector("p333")) == cmab.P333_ZONES
    z = cma2.decode(cmab.start_vector({"level": 1, "th": 15, "crowd": 10}))
    assert z == [{"th": 15.0, "crowd": 10, "level": 1, "free": 3}] * 5
    with pytest.raises(SystemExit):
        cmab.start_vector({"pattern": [1, 3, 3]})
