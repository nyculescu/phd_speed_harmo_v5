"""Diagnostic: package temperature with k BN4 simulations pinned to E-cores (CPUs 16-31) via
sched_setaffinity (a per-process setting of our own jobs; no system setting is changed).
Stops escalating at the first level whose mean exceeds 88 C. Results only inform worker placement."""
from __future__ import annotations

import glob
import json
import os
import statistics as st
import subprocess
import sys
import time

from vsl_lab.config import PYTHON_BIN, RUNS_ROOT, clean_sumo_env

E_CORES = list(range(16, 32))


def pkg_path():
    lab = [h for h in glob.glob("/sys/class/hwmon/hwmon*") if open(h + "/name").read().strip() == "coretemp"][0]
    return lab + "/temp1_input"


def sample(sec: float) -> dict:
    p = pkg_path()
    xs = []
    t0 = time.time()
    while time.time() - t0 < sec:
        xs.append(int(open(p).read()) / 1000.0)
        time.sleep(0.25)
    s = sorted(xs)
    return {"mean": round(st.mean(s), 1), "median": s[len(s) // 2], "p90": s[int(0.9 * len(s))], "max": s[-1],
            "share_ge_90": round(sum(x >= 90 for x in s) / len(s), 2)}


def main() -> int:
    levels = [int(x) for x in sys.argv[1:]] or [1, 8, 16]
    env = clean_sumo_env()
    rows = []
    for k in levels:
        procs = []
        for i in range(k):
            cpu = E_CORES[i % len(E_CORES)]
            pr = subprocess.Popen([PYTHON_BIN, "-m", "vsl_lab.jobs.bn4_nc", "--inflow", "2000", "--seed",
                                   str(7110000 + (i % 10)), "--t-demand", "60000", "--t-max", "60001",
                                   "--tag", f"ecore_probe_k{k}", "--out-root", str(RUNS_ROOT / "ops")],
                                  env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            os.sched_setaffinity(pr.pid, {cpu})
            procs.append(pr)
        time.sleep(5)
        r = sample(30) | {"k": k}
        for pr in procs:
            pr.terminate()
        for pr in procs:
            try:
                pr.wait(timeout=10)
            except subprocess.TimeoutExpired:
                pr.kill()
        rows.append(r)
        print(json.dumps(r), flush=True)
        if r["mean"] > 88.0:
            break
        time.sleep(20)  # cool down between levels
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
