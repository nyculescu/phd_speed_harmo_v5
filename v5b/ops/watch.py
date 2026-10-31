"""External CPU guard (CLAUDE.md "Limits") for batches that only gate launches.

Pauses (SIGSTOP) and resumes (SIGCONT) the running processes whose command line matches a pattern, with the
ComputeGuard state machine: the newest job is paused first, the earliest paused is resumed first. It stops once the
watched systemd unit is inactive and no job is left, and resumes anything it paused when it exits.
"""
from __future__ import annotations

import argparse
import os
import signal
import subprocess
import time

from v5b.ops.guard import ComputeGuard


def cpu_util(dt: float = 5.0) -> float:
    def read():
        with open("/proc/stat") as f:
            x = list(map(int, f.readline().split()[1:]))
        return x[3] + x[4], sum(x)
    i0, t0 = read()
    time.sleep(dt)
    i1, t1 = read()
    return 1.0 - (i1 - i0) / max(1, t1 - t0)


def jobs(pattern: str) -> list:
    """Matching pids, oldest first."""
    out = subprocess.run(["pgrep", "-f", pattern], capture_output=True, text=True).stdout.split()
    started = {}
    for p in map(int, out):
        if p == os.getpid():
            continue
        try:
            with open(f"/proc/{p}/stat") as f:
                started[p] = int(f.read().rsplit(")", 1)[1].split()[19])
        except (OSError, IndexError, ValueError):
            pass
    return sorted(started, key=started.get)


def unit_active(unit: str) -> bool:
    return subprocess.run(["systemctl", "--user", "is-active", "-q", unit]).returncode == 0


def _stop(*_):
    raise KeyboardInterrupt


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pattern", required=True)
    ap.add_argument("--unit", required=True)
    ap.add_argument("--cpu-limit", type=float, help="lower than the 0.90 default, e.g. for quiet nights")
    a = ap.parse_args(argv)
    g = ComputeGuard(overrides={"cpu_limit": a.cpu_limit} if a.cpu_limit else None)
    paused = []
    signal.signal(signal.SIGTERM, _stop)
    try:
        while True:
            util = cpu_util()
            live = jobs(a.pattern)
            paused = [p for p in paused if p in live]
            running = [p for p in live if p not in paused]
            d = g.update(time.time(), util, float("nan"), len(paused))
            if d.pause_one and running:
                os.kill(running[-1], signal.SIGSTOP)
                paused.append(running[-1])
                print(f"{time.strftime('%H:%M:%S')} cpu {util:.2f} paused {running[-1]} ({len(paused)} paused)", flush=True)
            elif d.resume_one and paused:
                p = paused.pop(0)
                os.kill(p, signal.SIGCONT)
                print(f"{time.strftime('%H:%M:%S')} cpu {util:.2f} resumed {p} ({len(paused)} paused)", flush=True)
            if not live and not unit_active(a.unit):
                return 0
    except KeyboardInterrupt:
        return 0
    finally:
        for p in paused:
            try:
                os.kill(p, signal.SIGCONT)
            except OSError:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
