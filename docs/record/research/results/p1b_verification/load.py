"""Independent loader (P1b): read every per-run JSON of the tuning (7400300-339) and evaluation (7400600-699) seeds,
replicates included; keep a slim record indexed later by the spec fields stored INSIDE the file; check key == filename.
Does not import v5b. Usage: load.py OUT.pkl"""
import json, os, sys, pickle
from multiprocessing import Pool
RUNS = "/home/catalin/work/phd/v5b1_runs/p1b/v108/runs"
F = ("pre", "post", "back", "incident", "q", "seed", "k", "d", "c", "fa", "vsl_b", "rep", "rs", "delay_s", "valid",
     "teleports", "served_ctrl_vph", "ttt_ctrl_vehh", "max_queue", "max_queue_m", "max_queue_halted_veh", "avail_m",
     "depart_delay_s", "hash", "t_on", "t_off", "t_switch", "t_back", "onset_s", "duration_s", "fa_time_s",
     "sumo_seed", "demand_seed", "drained", "generated", "n_trips", "signal", "code_commit", "key",
     "n_runners", "runner_hash", "crossings", "runner_crossings", "red_cross_share", "runner_red_cross_share",
     "discharge_vph", "commanded_mean_vph", "approach_red_mps", "emergency_meter", "emergency_stops", "collisions")


def seed_of(fn):
    for part in fn[:-5].split("_"):
        if part.startswith("s74") and part[1:].isdigit():
            return int(part[1:])
    return None


def want(fn):
    s = seed_of(fn)
    return s is not None and (7400300 <= s <= 7400339 or 7400600 <= s <= 7400699)


def load(fn):
    with open(os.path.join(RUNS, fn)) as f:
        r = json.load(f)
    out = {k: r.get(k) for k in F}
    out["_fn"] = fn[:-5]
    return out


if __name__ == "__main__":
    fns = [f for f in os.listdir(RUNS) if f.endswith(".json")]
    sel = [f for f in fns if want(f)]
    print("files", len(fns), "selected", len(sel), file=sys.stderr)
    with Pool(4) as p:
        recs = p.map(load, sel, chunksize=500)
    bad = [r["_fn"] for r in recs if r["key"] != r["_fn"]]
    print("key!=filename", len(bad), bad[:5], file=sys.stderr)
    pickle.dump(recs, open(sys.argv[1], "wb"))
