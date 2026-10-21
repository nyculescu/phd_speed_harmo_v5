"""Spot re-runs (T3-style determinism check) of stored P1b runs with the frozen code, into a scratch dir (never the run
dir). Compares hash, delay and the P1b reporting fields. Usage: rerun.py KEY [KEY ...] (at most 6; 4 in parallel)."""
import json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
SRC = "/home/catalin/work/phd/v5b1_runs/p1b/v108/runs"
OUT = "/home/catalin/work/phd/v5b1_runs/jobs/p1b_verify/scratch"
WT = "/home/catalin/work/phd/p1b_frozen_93ba655"
PY = "/home/catalin/work/phd/phd_speed_harmo_v5b1_toolchain/venv/bin/python"
F = ("pre", "post", "back", "incident", "q", "seed", "k", "d", "c", "fa", "vsl_b", "rep", "rs")
CMP = ("hash", "delay_s", "depart_delay_s", "served_ctrl_vph", "ttt_ctrl_vehh", "max_queue", "max_queue_m",
       "meter_log", "t_switch", "t_back", "valid", "crossings", "runner_crossings", "runner_hash", "emergency_meter",
       "approach_red_mps", "collisions")
KEYS = sys.argv[1:]
assert 0 < len(KEYS) <= 6
os.makedirs(OUT + "/runs", exist_ok=True)
env = {k: v for k, v in os.environ.items() if k not in ("SUMO_HOME", "V5B1_RUNS")}
env.update(OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=WT)


def one(k):
    st = json.load(open(f"{SRC}/{k}.json"))
    spec = {f: st[f] for f in F}
    spec.update(key=k, code_commit=st["code_commit"], signal=st["signal"])
    rd = f"{OUT}/sumo/{k}"
    os.makedirs(rd, exist_ok=True)
    out = f"{OUT}/runs/{k}.json"
    p = subprocess.run(["nice", "-n", "19", PY, "-B", "-m", "v5b.p1b.episode", "--spec", json.dumps(spec), "--out", out,
                        "--run-dir", rd], cwd=WT, env=env, capture_output=True, text=True)
    if p.returncode:
        return k, "FAIL rc=%d %s" % (p.returncode, p.stderr[-300:])
    new = json.load(open(out))
    diff = [f for f in CMP if new.get(f) != st.get(f)]
    return k, ("IDENTICAL" if not diff else f"DIFF {diff}"), st["hash"], new["hash"], round(st["delay_s"], 3), \
        round(new["delay_s"], 3)


with ThreadPoolExecutor(4) as ex:
    for r in ex.map(one, KEYS):
        print(*r)
