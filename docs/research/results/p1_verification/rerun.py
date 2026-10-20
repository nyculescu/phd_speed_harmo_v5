import json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
SRC = "/home/catalin/work/phd/v5b1_runs/p1/v99/runs"
OUT = "/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/59738c75-cfe8-434e-99ee-b78b7087de37/scratchpad/p1v/rerun"
WT = "/home/catalin/work/phd/p1_frozen_85f7d34"
PY = "/home/catalin/work/phd/phd_speed_harmo_v5b1_toolchain/venv/bin/python"
F = ("pre", "post", "back", "incident", "q", "seed", "k", "d", "c", "fa", "vsl_b", "rep")
KEYS = sys.argv[1:]
os.makedirs(OUT + "/runs", exist_ok=True)
env = {k: v for k, v in os.environ.items() if k != "SUMO_HOME"}
env.update(OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=WT)
def one(k):
    st = json.load(open(f"{SRC}/{k}.json"))
    spec = {f: st[f] for f in F}; spec.update(key=k, code_commit=st["code_commit"], signal=st["signal"])
    rd = f"{OUT}/sumo/{k}"; os.makedirs(rd, exist_ok=True)
    out = f"{OUT}/runs/{k}.json"
    p = subprocess.run(["nice", "-n", "19", PY, "-B", "-m", "v5b.p1.episode", "--spec", json.dumps(spec), "--out", out, "--run-dir", rd],
                       cwd=WT, env=env, capture_output=True, text=True)
    if p.returncode:
        return k, "FAIL rc=%d %s" % (p.returncode, p.stderr[-300:])
    new = json.load(open(out))
    fields = ("hash", "delay_s", "served_ctrl_vph", "ttt_ctrl_vehh", "max_queue", "entered_e4_incident", "meter_log", "nhat_log", "t_switch", "t_back", "valid")
    diff = [f for f in fields if new.get(f) != st.get(f)]
    return k, ("IDENTICAL" if not diff else f"DIFF {diff}"), st["hash"], new["hash"], round(st["delay_s"], 3), round(new["delay_s"], 3)
with ThreadPoolExecutor(8) as ex:
    for r in ex.map(one, KEYS):
        print(*r)
