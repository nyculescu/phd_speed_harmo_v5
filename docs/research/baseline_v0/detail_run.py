"""V306: re-runs evaluation rows through the unchanged evaluation path, recording every vehicle and lane.
Reads from SUMO only; every row must equal its stored copy. usage: detail_run.py spec.json stored_rows.jsonl out_dir workers [name q seed]"""
import dataclasses
import gzip
import json
import multiprocessing as mp
import sys
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

EDGES = ("1", "2", "3a", "3", "4", "5", "r", "rj")
BIN_S = 60


def _veh(v):
    d = dataclasses.asdict(v) if dataclasses.is_dataclass(v) else {k: getattr(v, k) for k in dir(v) if not k.startswith("_") and not callable(getattr(v, k))}
    return d


def _instrument(env, sink):
    import libsumo as ls
    step0 = env._sim_step
    close0 = env.close
    trips, lanes, lc = defaultdict(dict), defaultdict(lambda: defaultdict(lambda: [0, 0.0, 0])), defaultdict(int)
    last, k = {}, [0]
    lane_ids = []

    def step():
        step0()
        t = env.sim.t
        for v in ls.simulation.getDepartedIDList():
            trips[v].update(dep=t, delay=ls.vehicle.getDepartDelay(v))
        for v in ls.simulation.getArrivedIDList():
            trips[v]["arr"] = t
        k[0] += 1
        if k[0] % 10:
            return
        if not lane_ids:
            lane_ids.extend(x for x in ls.lane.getIDList() if not x.startswith(":"))
        b = int(t // BIN_S)
        for x in lane_ids:
            c = lanes[x][b]
            n = ls.lane.getLastStepVehicleNumber(x)
            c[0] += n
            c[1] += n * ls.lane.getLastStepMeanSpeed(x)
            c[2] += ls.lane.getLastStepHaltingNumber(x)
        for e in EDGES:
            for v in ls.edge.getLastStepVehicleIDs(e):
                if "e" + e not in trips[v]:
                    trips[v]["e" + e] = [t, ls.vehicle.getLaneIndex(v), round(ls.vehicle.getSpeed(v), 2)]
        for v in ls.vehicle.getIDList():
            x = ls.vehicle.getLaneID(v)
            if x.startswith(":"):
                continue
            p = last.get(v)
            if p and p != x and p.rsplit("_", 1)[0] == x.rsplit("_", 1)[0]:
                lc[f"{x.rsplit('_', 1)[0]}|{'alks' if v in env.alks_all else 'hdv'}|{'left' if int(x.rsplit('_', 1)[1]) > int(p.rsplit('_', 1)[1]) else 'right'}"] += 1
            last[v] = x

    def close():
        planned = [{**_veh(v), "route": r, **trips.get(v.vid, {})} for v, r in zip(env.dem.veh, env.dem.route_of)]
        sink.update(vehicles=planned, lanes={x: {str(b): c for b, c in d.items()} for x, d in lanes.items()}, lc=dict(lc), warm=env.warm, t_end=env.t_end)
        close0()

    env._sim_step = step
    env.close = close


def job(a):
    spec, q, seed, out, rd = a
    from v5b.fleet import b_env as be, b_train as bt
    sink = {}
    make0 = be.make

    def make(*p, **kw):
        env = make0(*p, **kw)
        _instrument(env, sink)
        return env

    be.make = make
    row = bt._matrix_job((spec, q, seed, rd))
    with gzip.open(Path(out) / f"{spec['name']}_{int(q)}_{seed}.json.gz", "wt") as f:
        json.dump({"row": row, **sink}, f, default=float)
    return row


if __name__ == "__main__":
    specs = json.load(open(sys.argv[1]))
    stored = {(r["name"], r["q"], r["seed"]): r for r in map(json.loads, open(sys.argv[2]))}
    out = Path(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    only = (sys.argv[5], float(sys.argv[6]), int(sys.argv[7])) if len(sys.argv) > 5 else None
    jobs = [(s, float(q), seed, str(out), str(out.parent / "rd")) for s in specs for q in s["levels"] for seed in s["seeds"]
            if (only is None or only == (s["name"], float(q), seed)) and not (out / f"{s['name']}_{int(q)}_{seed}.json.gz").exists()]
    print(len(jobs), "jobs", flush=True)
    same = diff = 0
    with ProcessPoolExecutor(int(sys.argv[4]), mp_context=mp.get_context("spawn"), max_tasks_per_child=1) as ex, open(out.parent / "check.jsonl", "a") as w:
        for fut in as_completed([ex.submit(job, j) for j in jobs]):
            r = fut.result()
            s = stored[(r["name"], r["q"], r["seed"])]
            bad = [k for k in s if s[k] != r.get(k)]
            same += not bad
            diff += bool(bad)
            w.write(json.dumps({"name": r["name"], "q": r["q"], "seed": r["seed"], "bad": bad}) + "\n")
            w.flush()
    print("rows equal to stored:", same, "different:", diff, flush=True)
