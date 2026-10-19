"""Compute guard (author rule 2026-10-05; v5b/ops/guard.py, ported from claude/vsl-lab-core@2a79e5e). No SUMO, no hardware reads.

Run: pytest -p no:cacheprovider tests/test_guard.py -v  (from the repo root, via python -m pytest)
"""
from __future__ import annotations

import json

from v5b.ops.guard import ComputeGuard


def run(g, seq, n_paused=0):
    """seq: list of (t, util, temp) -> list of decisions."""
    return [g.update(t, u, c, n_paused=n_paused) for t, u, c in seq]


def test_launch_blocked_above_cpu_limit_but_no_pause_before_two_minutes():
    g = ComputeGuard()
    d = run(g, [(t, 0.95, 80.0) for t in range(0, 119)])
    assert not any(x.allow_launch for x in d)
    assert not any(x.pause_one for x in d)


def test_cpu_over_limit_two_minutes_pauses_one_job_per_30s():
    g = ComputeGuard()
    d = run(g, [(t, 0.95, 80.0) for t in range(0, 200)])
    pauses = [t for t, x in zip(range(0, 200), d) if x.pause_one]
    assert pauses == [120, 150, 180]


def test_resume_one_per_step_after_cooling():
    g = ComputeGuard()
    run(g, [(t, 0.95, 80.0) for t in range(0, 121)])                   # paused one at t = 120
    d = [g.update(t, 0.50, 80.0, n_paused=1) for t in range(121, 200)]
    resumes = [t for t, x in zip(range(121, 200), d) if x.resume_one]
    assert resumes and resumes[0] == 151                               # cool for step_s (30 s) and step spacing
    assert all(b - a >= 30 for a, b in zip(resumes, resumes[1:]))


def test_cpu_at_or_below_limit_allows_launch():
    g = ComputeGuard()
    assert g.update(0, 0.90, 80.0).allow_launch
    assert not g.update(1, 0.901, 80.0).allow_launch


def test_thermal_hysteresis_v6():
    g = ComputeGuard()
    d = run(g, [(t, 0.5, 98.0) for t in range(0, 151)])
    assert d[149].allow_launch and not d[150].allow_launch             # >= 98 C for 150 s
    assert not any(x.pause_one for x in d)                             # thermal pause stops launches only
    d = run(g, [(t, 0.5, 94.0) for t in range(151, 400)])              # between 92 and 98: stays paused
    assert not any(x.allow_launch for x in d)
    d = run(g, [(t, 0.5, 92.0) for t in range(400, 551)])
    assert not d[149].allow_launch and d[150].allow_launch             # <= 92 C for 150 s


def test_emergency_pauses_at_once_and_pauses_jobs():
    g = ComputeGuard()
    d = g.update(0, 0.5, 99.0)
    assert not d.allow_launch and d.pause_one and d.reason == "emergency"


def test_missing_sensor_disables_thermal_only():
    g = ComputeGuard()
    assert g.update(0, 0.5, float("nan")).allow_launch


def test_live_config_override(tmp_path):
    f = tmp_path / "thermal.json"
    f.write_text(json.dumps({"cpu_limit": 0.5}))
    g = ComputeGuard(cfg_path=f)
    assert not g.update(0, 0.6, 80.0).allow_launch
    f.write_text(json.dumps({"cpu_limit": 0.9}))
    assert g.update(1, 0.6, 80.0).allow_launch


def test_in_code_override_sets_overnight_cpu_limit():
    """v5.B.1 addition: ComputeGuard(overrides={"cpu_limit": 0.70}) (V89 overnight rule)."""
    g = ComputeGuard(overrides={"cpu_limit": 0.70})
    assert g.update(0, 0.70, float("nan")).allow_launch
    assert not g.update(1, 0.71, float("nan")).allow_launch
    d = [g.update(t, 0.75, float("nan")) for t in range(2, 200)]
    assert [t for t, x in zip(range(2, 200), d) if x.pause_one] == [121, 151, 181]
    d = [g.update(t, 0.68, float("nan"), n_paused=1) for t in range(200, 260)]
    assert not any(x.resume_one for x in d)                            # 0.68 > 0.70 - 0.03: no resume
