"""Bug re-runs of finished screens (CLAUDE.md bug rule: fix, re-run everything affected, log both outcomes).

V100 (docs/decisions.md, 2026-10-19): the D1/D2 meter recomputed its phase with the current cycle on every rate
change (greens skipped, reds up to 322 s). Screens D1 (V89/V90) and D2 (V92/V94) are re-run once with the corrected
'continuous' signal (v5b/d1/meter_signal.py) on the same seeds, arms, grids, tuning and decision rules.

A bug re-run (`--bug-rerun V100 --meter-signal continuous --confirm-run-once`):
- changes only the meter signal: every other protocol option must equal the original run's (result.json 'args');
  only operational options (OPERATIONAL) may differ; the seeds, demands, grids / G and the page hash of the original
  result must equal the current code's (checked);
- writes to a new --out (never the original's);
- bypasses the screen's own run-once sentinel and instead is itself run once through its own sentinel
  (D1_BUGRERUN_V100.json / D2_BUGRERUN_V100.json), written before the first SUMO run; only --resume of the same --out
  at the same commit is allowed after that;
- records the original result path, commit and decision in result.json['bug_rerun'].
With --smoke the same checks run, but on the smoke seeds and without any sentinel (a check that the mode works).
"""
from __future__ import annotations

import json
from pathlib import Path

from v5b.d1.meter_signal import LEGACY

RUNS_ROOT = Path("/home/catalin/work/phd/v5b1_runs")
BUG_RERUNS = {
    "V100": {
        "meter_signal": "continuous",
        "why": "meter phase recomputed with the current cycle on every rate change (greens skipped, reds up to "
               "322 s); fixed by the continuous signal rule (v5b/d1/meter_signal.py)",
        "D1": {"original": RUNS_ROOT / "screen_d1/v89/result.json",
               "original_commit": "a23613be3de27e4e8d84eaf38ec7b09f4e02d0d9",
               "sentinel": RUNS_ROOT / "D1_BUGRERUN_V100.json"},
        "D2": {"original": RUNS_ROOT / "screen_d2/v92/result.json",
               "original_commit": "72ba8f276c0b1fc1af87ccecc4a08118f8d40b38",
               "sentinel": RUNS_ROOT / "D2_BUGRERUN_V100.json"},
    },
}
OPERATIONAL = ("out", "workers", "cpu_limit", "nice", "resume", "smoke", "confirm_run_once")
NEW_FLAGS = ("meter_signal", "bug_rerun")


def add_args(ap) -> None:
    ap.add_argument("--meter-signal", choices=("d2", "continuous"), default=LEGACY,
                    help="meter phase rule (v5b/d1/meter_signal.py); default d2 = the original screen's rule. "
                         "'continuous' only with --bug-rerun or --smoke")
    ap.add_argument("--bug-rerun", choices=tuple(BUG_RERUNS), default=None,
                    help="re-run the finished screen once with the corrected meter (module v5b/bugrerun.py)")


def check(a, screen: str, identity, registry: dict = None) -> dict | None:
    """Validate the invocation; returns the bug-rerun record (None for a normal run). identity(orig) -> {label:
    (value in the original result, value in the current code)}, e.g. seeds, qs, grid, G, page_sha256."""
    if a.bug_rerun is None:
        if a.meter_signal != LEGACY and not a.smoke:
            raise SystemExit(f"--meter-signal {a.meter_signal} changes the registered screen: only with --bug-rerun "
                             "(or --smoke)")
        return None
    reg = (registry or BUG_RERUNS)[a.bug_rerun]
    entry = reg[screen]
    if a.meter_signal != reg["meter_signal"]:
        raise SystemExit(f"bug re-run {a.bug_rerun} needs --meter-signal {reg['meter_signal']}")
    if not a.smoke and not a.confirm_run_once:
        raise SystemExit("the bug re-run touches the evaluation seeds once: pass --confirm-run-once")
    orig_path = Path(entry["original"])
    if not orig_path.exists():
        raise SystemExit(f"bug re-run {a.bug_rerun}: the original result {orig_path} is missing")
    orig = json.loads(orig_path.read_text())
    if orig.get("code_commit") != entry["original_commit"]:
        raise SystemExit(f"bug re-run {a.bug_rerun}: {orig_path} is at commit {str(orig.get('code_commit'))[:10]}, "
                         f"not the registered {entry['original_commit'][:10]}")
    if Path(a.out).resolve() == orig_path.parent.resolve():
        raise SystemExit("the bug re-run writes to a new --out, never the original's")
    oargs, now = orig["args"], vars(a)
    keys = (set(oargs) | set(now)) - set(OPERATIONAL) - set(NEW_FLAGS)
    changed = sorted(k for k in keys if k not in oargs or k not in now or oargs[k] != now[k])
    if changed:
        raise SystemExit(f"bug re-run {a.bug_rerun} changes only the meter signal; these options differ from the "
                         f"original run: {changed}")
    bad = sorted(k for k, (o, c) in identity(orig).items() if _norm(o) != _norm(c))
    if bad:
        raise SystemExit(f"bug re-run {a.bug_rerun}: the current code differs from the original run in {bad}")
    return {"decision": a.bug_rerun, "screen": screen, "why": reg["why"], "meter_signal": reg["meter_signal"],
            "original_meter_signal": LEGACY, "original_result": str(orig_path),
            "original_code_commit": orig["code_commit"], "original_decision": orig.get("decision"),
            "original_args": oargs, "sentinel": None if a.smoke else str(entry["sentinel"]),
            "operational_changes": {k: [oargs.get(k), now.get(k)] for k in ("workers", "cpu_limit", "nice")
                                    if oargs.get(k) != now.get(k)},
            "smoke_only": bool(a.smoke)}


def _norm(x):
    return json.loads(json.dumps(x))


def sentinel_path(a, screen: str, registry: dict = None) -> Path:
    return Path((registry or BUG_RERUNS)[a.bug_rerun][screen]["sentinel"])


def summary_header(rec: dict) -> str:
    return (f"> **{rec['decision']} bug re-run** of screen {rec['screen']}: meter signal {rec['original_meter_signal']} "
            f"-> {rec['meter_signal']} ({rec['why']}). Same seeds, arms, grids, tuning and decision rules. Original "
            f"result `{rec['original_result']}` (code {rec['original_code_commit'][:10]}, decision "
            f"{rec['original_decision']}). Report both outcomes.\n\n")
