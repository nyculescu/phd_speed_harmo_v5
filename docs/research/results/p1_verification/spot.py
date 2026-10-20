import json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
RUNS = "/home/catalin/work/phd/v5b1_runs/p1/v99/runs"
FROZEN = "/home/catalin/work/phd/p1_frozen_85f7d34"
PY = "/home/catalin/work/phd/phd_speed_harmo_v5b1_toolchain/venv/bin/python"
SC = "/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/59738c75-cfe8-434e-99ee-b78b7087de37/scratchpad/p1v/spot"
keys = sys.argv[1:]
assert len(keys) <= 20
FIELDS = ("pre", "post", "back", "incident", "q", "seed", "k", "d", "c", "fa", "vsl_b", "rep")
env = {k: v for k, v in os.environ.items() if k != "SUMO_HOME"}
env.update(OMP_NUM_THREADS="1", PYTHONDONTWRITEBYTECODE="1")
def one(k):
    r = json.load(open(f"{RUNS}/{k}.json"))
    spec = {f: r[f] for f in FIELDS}
    spec.update(key=k, code_commit=r["code_commit"], signal=r["signal"])
    out = f"{SC}/{k}.json"
    p = subprocess.run(["nice", "-n", "19", PY, "-m", "v5b.p1.episode", "--spec", json.dumps(spec), "--out", out,
                        "--run-dir", f"{SC}/sumo/{k}"], cwd=FROZEN, env=env, capture_output=True, text=True)
    if p.returncode:
        return k, "FAIL " + p.stderr[-300:]
    n = json.load(open(out))
    return k, f"stored {r['delay_s']:.6f} {r['hash']} | rerun {n['delay_s']:.6f} {n['hash']} | same {n['hash']==r['hash'] and n['delay_s']==r['delay_s']}"
os.makedirs(SC, exist_ok=True)
with ThreadPoolExecutor(8) as ex:
    for k, s in ex.map(one, keys):
        print(k, s)
