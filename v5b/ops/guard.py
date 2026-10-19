# Port: claude/vsl-lab-core@2a79e5e vsl_lab/ops/guard.py; change: optional in-code overrides (e.g. cpu_limit 0.70 for an overnight run), applied after the live config file. Thermal rules are kept but inactive when the caller passes temp = NaN (thermal rule removed by the author 2026-10-10).
"""Compute guard (author rule 2026-10-05, CLAUDE.md "Limits"): CPU > 90 % for 2 min -> pause; v6 thermal hysteresis.

Pure state machine, fed (now, cpu_util, temp_c) by the scheduler or the training watchdog; no I/O except the live
config file, which is re-read on every update so limits can change while a job runs (v6 cvsig/step2.py design).

Rules (defaults; overridable in RUNS_ROOT/ops/thermal.json):
- launches are allowed only while cpu_util < cpu_limit (0.90) and the thermal state is not paused;
- CPU pause: once cpu_util > cpu_limit continuously for cpu_hold_s (120 s), the caller pauses its newest running job,
  then one more every step_s (30 s) while the condition still holds; once cpu_util <= cpu_limit - resume_margin
  continuously for step_s, it resumes one paused job per step_s (one-at-a-time avoids pause/resume thrashing when
  our own workers are the load);
- thermal (v6): launches pause when temp >= center + band continuously for hold_s (150 s) and resume when
  temp <= center - band continuously for hold_s; temp >= emergency (99 C) pauses launches at once and also asks the
  caller to pause one running job per step_s.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

DEFAULTS = {"cpu_limit": 0.90, "cpu_hold_s": 120.0, "resume_margin": 0.03, "step_s": 30.0,
            "center": 95.0, "band": 3.0, "hold_s": 150.0, "emergency": 99.0}


def load_cfg(path: Path | None, overrides: dict | None = None) -> dict:
    cfg = dict(DEFAULTS)
    if path is not None:
        try:
            cfg.update({k: float(v) for k, v in json.loads(Path(path).read_text()).items() if k in DEFAULTS})
        except (OSError, ValueError):
            pass
    if overrides:
        cfg.update({k: float(v) for k, v in overrides.items() if k in DEFAULTS})
    return cfg


@dataclass
class Decision:
    allow_launch: bool
    pause_one: bool          # pause the newest running job now
    resume_one: bool         # resume the oldest paused job now
    reason: str = ""


@dataclass
class ComputeGuard:
    cfg_path: Path | None = None
    overrides: dict | None = None
    cfg: dict = field(default_factory=lambda: dict(DEFAULTS))
    cpu_hot_since: float | None = None
    cpu_cool_since: float | None = None
    t_hot_since: float | None = None
    t_cool_since: float | None = None
    thermal_paused: bool = False
    last_action: float = -1e18

    def update(self, now: float, cpu_util: float, temp_c: float, n_paused: int = 0) -> Decision:
        self.cfg = c = load_cfg(self.cfg_path, self.overrides)
        # CPU timers
        over = cpu_util > c["cpu_limit"]
        self.cpu_hot_since = (self.cpu_hot_since if self.cpu_hot_since is not None else now) if over else None
        cool = cpu_util <= c["cpu_limit"] - c["resume_margin"]
        self.cpu_cool_since = (self.cpu_cool_since if self.cpu_cool_since is not None else now) if cool else None
        # thermal timers (NaN temperature = sensor missing: thermal rules inactive)
        hi, lo = c["center"] + c["band"], c["center"] - c["band"]
        t_ok = temp_c == temp_c
        self.t_hot_since = (self.t_hot_since if self.t_hot_since is not None else now) if t_ok and temp_c >= hi else None
        self.t_cool_since = (self.t_cool_since if self.t_cool_since is not None else now) if t_ok and temp_c <= lo else None
        emergency = t_ok and temp_c >= c["emergency"]
        if not self.thermal_paused and (emergency or (self.t_hot_since is not None
                                                      and now - self.t_hot_since >= c["hold_s"])):
            self.thermal_paused = True
        elif self.thermal_paused and not emergency and self.t_cool_since is not None \
                and now - self.t_cool_since >= c["hold_s"]:
            self.thermal_paused = False
        cpu_pause = self.cpu_hot_since is not None and now - self.cpu_hot_since >= c["cpu_hold_s"]
        can_act = now - self.last_action >= c["step_s"]
        pause_one = can_act and (cpu_pause or emergency)
        resume_one = (not pause_one and can_act and n_paused > 0 and not emergency and not self.thermal_paused
                      and self.cpu_cool_since is not None and now - self.cpu_cool_since >= c["step_s"])
        if pause_one or resume_one:
            self.last_action = now
        allow = (not over) and not self.thermal_paused and not cpu_pause and n_paused == 0
        reason = ("emergency" if emergency else "thermal" if self.thermal_paused else
                  "cpu>limit 2min" if cpu_pause else "cpu>limit" if over else "")
        return Decision(allow, pause_one, resume_one, reason)
