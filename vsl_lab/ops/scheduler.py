"""Thermal-aware batch scheduler (roadmap §5).

Each job is one fresh process (one simulation per process). Concurrency never exceeds max_workers
(<= 100). The package temperature is polled every `poll_s`; at >= TEMP_PAUSE_C (sustained `hold_s`)
the most recently started running job is SIGSTOPped; below TEMP_RESUME_C a paused job is resumed.
At >= TEMP_HARD_C no new job is launched and paused jobs stay paused. Pausing does not change results
(the simulations are not real-time). Every decision is logged in <batch_dir>/thermal.csv.
"""
from __future__ import annotations

import csv
import json
import signal
import statistics
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

import collections
import os

from vsl_lab.config import (WORKER_CPUS, MAX_LAUNCH_PER_S, MAX_WORKERS, PYTHON_BIN, SIM_START_MAX_LOAD, TEMP_HARD_C,
                            TEMP_PAUSE_C, TEMP_RESUME_C, TEMP_SLOW_S, TEMP_SMOOTH_S, TEMP_STEP_S, clean_sumo_env,
                            TARGET_CPU_UTIL, UTIL_SMOOTH_S)
from vsl_lab.ops.thermal import load_fraction, package_temp_c


@dataclass
class Job:
    jid: str
    argv: list            # module + args, run as: python -m <argv...>
    proc: subprocess.Popen | None = None
    t_start: float = 0.0
    t_end: float = 0.0
    paused: bool = False
    result: dict | None = None
    returncode: int | None = None
    log: Path | None = None


@dataclass
class BatchReport:
    n_jobs: int
    n_ok: int
    n_failed_proc: int
    wall_s: float
    max_temp_c: float
    mean_temp_c: float
    n_pauses: int
    results: list = field(default_factory=list)


def sim_start_gate(gate_ok: bool) -> None:
    """Refuse to start unless the caller confirmed v6 is idle, or load is low."""
    if gate_ok:
        return
    lf = load_fraction()
    if lf >= SIM_START_MAX_LOAD:
        raise RuntimeError(f"sim-start gate: load fraction {lf:.2f} >= {SIM_START_MAX_LOAD}; "
                           f"confirm v6 sessions are idle and pass gate_ok=True")


def _cpu_times() -> tuple:
    with open("/proc/stat") as fh:
        v = [int(x) for x in fh.readline().split()[1:]]
    idle = v[3] + (v[4] if len(v) > 4 else 0)
    return sum(v), idle


def run_batch(jobs: list[Job], batch_dir: Path, max_workers: int, gate_ok: bool = False,
              poll_s: float = 0.5, hold_s: float = 5.0, verbose_every_s: float = 60.0,
              time_budget_s: float | None = None, job_factory=None) -> BatchReport:
    """Run jobs; if job_factory is given, keep generating jobs until time_budget_s (thermal calibration)."""
    max_workers = min(max_workers, MAX_WORKERS)
    sim_start_gate(gate_ok)
    try:  # the scheduler itself (fork/exec, polling) also stays off the P-cores
        os.sched_setaffinity(0, set(WORKER_CPUS))
    except OSError:
        pass
    last_launch = time.time()
    tokens = 1.0
    batch_dir.mkdir(parents=True, exist_ok=True)
    logs = batch_dir / "job_logs"
    logs.mkdir(exist_ok=True)
    env = clean_sumo_env()
    queue = list(jobs)
    running: list[Job] = []
    done: list[Job] = []
    hot_since = None
    n_pauses = 0
    temps = []
    t0 = time.time()
    last_verbose = t0
    tf = open(batch_dir / "thermal.csv", "w", newline="")
    tw = csv.writer(tf)
    tw.writerow(["wall_s", "temp_c", "running", "paused", "done", "queued", "event", "raw_c", "slow_c", "cpu_util"])
    # concurrency follows system CPU utilisation (author, 2026-10-03: "measure the CPU load instead of temp"); the 99 C
    # median guard stays as a safety backstop
    util_win = collections.deque(maxlen=max(int(UTIL_SMOOTH_S / poll_s), 1))
    cpu_prev = _cpu_times()
    util = 0.0
    n_cpu = os.cpu_count() or 32
    recent_launches = collections.deque()   # launches in the last 2 s count as load not yet visible in /proc/stat
    k_factory = 0
    window = collections.deque(maxlen=max(int(TEMP_SMOOTH_S / poll_s), 1))     # fast (10 s)
    slow = collections.deque(maxlen=max(int(TEMP_SLOW_S / poll_s), 1))         # slow (10 min)
    last_thermal_action = 0.0

    def launch(job: Job) -> None:
        job.log = logs / f"{job.jid}.log"
        fh = open(job.log, "w")
        job.proc = subprocess.Popen([PYTHON_BIN, "-m", *job.argv], stdout=fh, stderr=subprocess.STDOUT,
                                    env=env, cwd=str(Path(__file__).resolve().parents[2]))
        try:
            os.sched_setaffinity(job.proc.pid, set(WORKER_CPUS))
        except OSError:
            pass
        job.t_start = time.time()
        running.append(job)

    try:
        while True:
            now = time.time()
            if job_factory is not None and time_budget_s is not None and now - t0 < time_budget_s \
                    and len(queue) < max_workers:
                for _ in range(max_workers):
                    queue.append(job_factory(k_factory))
                    k_factory += 1
            cpu_now = _cpu_times()
            d_tot, d_idle = cpu_now[0] - cpu_prev[0], cpu_now[1] - cpu_prev[1]
            cpu_prev = cpu_now
            if d_tot > 0:
                util_win.append(1.0 - d_idle / d_tot)
            util = sum(util_win) / len(util_win) if util_win else 0.0
            raw = package_temp_c()
            if raw == raw:
                window.append(raw)
                slow.append(raw)
            filled = len(window) == window.maxlen
            # until the 10 s window is filled, single raw spikes (up to ~98 C at idle on this CPU) must not count
            temp = (sum(window) / len(window)) if filled else min(sum(window) / max(len(window), 1), TEMP_HARD_C - 1.5)
            temp_slow = statistics.median(slow) if slow else raw      # slow 5-min MEDIAN (pause / resume)
            if filled:
                temps.append(temp)
            event = ""
            # finished jobs
            for job in list(running):
                rc = job.proc.poll()
                if rc is not None:
                    job.returncode = rc
                    job.t_end = time.time()
                    running.remove(job)
                    job.result = _last_json_line(job.log)
                    done.append(job)
            n_paused = sum(j.paused for j in running)
            # thermal control: slow loop (5-min median, 99 / 96 C, one action per TEMP_STEP_S); the fast cap
            # (TEMP_HARD_C) is effectively off since 2026-10-02
            active = [j for j in running if not j.paused]
            paused_jobs = [j for j in running if j.paused]
            if temp >= TEMP_HARD_C and active:
                j = max(active, key=lambda x: x.t_start)
                j.proc.send_signal(signal.SIGSTOP)
                j.paused = True
                n_pauses += 1
                event = f"cap-pause {j.jid}"
                last_thermal_action = now
            elif now - last_thermal_action >= TEMP_STEP_S:
                if temp_slow >= TEMP_PAUSE_C and active:
                    j = max(active, key=lambda x: x.t_start)
                    j.proc.send_signal(signal.SIGSTOP)
                    j.paused = True
                    n_pauses += 1
                    event = f"pause {j.jid}"
                    last_thermal_action = now
                elif temp_slow < TEMP_RESUME_C and temp < TEMP_HARD_C - 1.0 and paused_jobs:
                    j = min(paused_jobs, key=lambda x: x.t_start)
                    j.proc.send_signal(signal.SIGCONT)
                    j.paused = False
                    event = f"resume {j.jid}"
                    last_thermal_action = now
            # launches (only when cool enough and nothing is paused)
            n_paused = sum(j.paused for j in running)
            stop_launch = time_budget_s is not None and now - t0 >= time_budget_s
            tokens = min(MAX_LAUNCH_PER_S, tokens + (now - last_launch) * MAX_LAUNCH_PER_S)
            last_launch = now
            # launch while the CPU has spare capacity: estimated util = measured util + pending launches (last 2 s)
            while recent_launches and recent_launches[0] < now - 2.0:
                recent_launches.popleft()
            while queue and len(running) < max_workers and temp_slow < TEMP_PAUSE_C and temp < TEMP_HARD_C \
                    and n_paused == 0 and not stop_launch and tokens >= 1.0 \
                    and (len(running) < 2 or util + len(recent_launches) / n_cpu < TARGET_CPU_UTIL):
                launch(queue.pop(0))
                recent_launches.append(now)
                tokens -= 1.0
                event = event or "launch"
            tw.writerow([round(now - t0, 1), round(temp, 2), len(running), n_paused, len(done), len(queue), event, raw,
                         round(temp_slow, 2), round(util, 3)])
            if now - last_verbose >= verbose_every_s:
                tf.flush()
                last_verbose = now
            if not running and (not queue or stop_launch):
                break
            time.sleep(poll_s)
    finally:
        for job in running:
            try:
                if job.paused:
                    job.proc.send_signal(signal.SIGCONT)
                job.proc.terminate()
            except Exception:
                pass
        tf.close()
    valid = [t for t in temps if t == t]
    rep = BatchReport(n_jobs=len(done), n_ok=sum(1 for j in done if j.returncode == 0 and j.result),
                      n_failed_proc=sum(1 for j in done if j.returncode != 0 or not j.result),
                      wall_s=round(time.time() - t0, 1), max_temp_c=max(valid, default=float("nan")),
                      mean_temp_c=round(sum(valid) / max(len(valid), 1), 1), n_pauses=n_pauses,
                      results=[{"jid": j.jid, "rc": j.returncode, "wall": round(j.t_end - j.t_start, 2),
                                "result": j.result} for j in done])
    (batch_dir / "batch_report.json").write_text(json.dumps(rep.__dict__, indent=1))
    return rep


def _last_json_line(log: Path) -> dict | None:
    try:
        lines = [ln for ln in log.read_text(errors="replace").splitlines() if ln.startswith("{")]
        return json.loads(lines[-1]) if lines else None
    except Exception:
        return None
