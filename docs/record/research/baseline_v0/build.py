"""V306: builds the baseline tables from the read-only copy. usage: build.py baseline_dir out_dir"""
import csv
import gzip
import json
import shutil
import sys
import tarfile
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

X, T = Path(sys.argv[1]), Path(sys.argv[2])
B = X / "b_train"
LIMIT = 27.78
LEN = {"1": 3000.0, "2": 498.3, "3a": 294.72, "3": 1196.0, "4": 1000.0, "5": 500.0, "r": 391.66, "rj": 28.33}
ROUTE_LEN = {"main": sum(LEN[e] for e in ("1", "2", "3a", "3", "4", "5")), "ramp": sum(LEN[e] for e in ("r", "rj", "3a", "3", "4", "5"))}
MED = ("passed", "arrived", "mean_v", "N", "E15", "E30", "brake3", "brake45", "out_E30", "out_b3", "gap25", "stop_gap", "contact_steps", "commands", "changes", "reversals", "ignored", "alks_s", "v2v_s", "steps")
PAIR = (("flow", "passed", 1), ("speed", "mean_v", 1), ("vehicles", "N", -1), ("ttc", "E30", -1), ("brake", "brake3", -1))


def write(name, rows):
    if not rows:
        return
    keys = list(dict.fromkeys(k for r in rows for k in r))
    opener = gzip.open if name.endswith(".gz") else open
    with opener(T / name, "wt", newline="") as f:
        w = csv.DictWriter(f, keys)
        w.writeheader()
        w.writerows(rows)


def ci(d):
    d = np.array(d, float)
    rng = np.random.default_rng(20261103)
    lo, hi = np.percentile(np.median(d[rng.integers(0, len(d), (20000, len(d)))], axis=1), [2.5, 97.5])
    return float(np.median(d)), float(lo), float(hi)


def paired(A, Bs, key, sign):
    ds = sorted(set(A) & set(Bs))
    base = np.median([Bs[k][key] for k in ds])
    return ci([sign * (A[k][key] - Bs[k][key]) / base * 100 for k in ds]), len(ds)


def base_of(name, T_, q, stem):
    suffix = name.split("_", 1)[1] if "_" in name else ""
    for n in (f"{stem}_{suffix}", stem):
        if (n, q) in T_:
            return T_[(n, q)]
    return None


def summarise(f):
    T_ = defaultdict(dict)
    for line in open(f):
        r = json.loads(line)
        T_[(r["name"], r["q"])][r["seed"]] = r
    out = []
    for (name, q), A in sorted(T_.items(), key=lambda x: (x[0][1], x[0][0])):
        a = list(A.values())
        s = {"src": str(Path(f).parent.relative_to(B)), "name": name, "q": q, "share": a[0].get("share"), "n": len(a), "seed_min": min(A), "seed_max": max(A)}
        for k in MED:
            if k in a[0]:
                s[k] = float(np.median([r[k] for r in a]))
        s["collisions_sum"] = sum(r["collisions"] for r in a)
        steps = s.get("steps") or 1500
        s["served_pct"] = s["passed"] / (q * steps / 3600) * 100
        s["mean_speed_ms"] = s["mean_v"] / steps
        s["mean_vehicles"] = s["N"] / steps
        for stem in ("a000", "p303"):
            b = base_of(name, T_, q, stem)
            if b is None or b is A:
                continue
            for lab, key, sign in PAIR:
                try:
                    (m, lo, hi), n = paired(A, b, key, sign)
                except (KeyError, IndexError, ValueError):
                    continue
                s[f"{lab}_v_{stem}"], s[f"{lab}_v_{stem}_lo"], s[f"{lab}_v_{stem}_hi"] = round(m, 3), round(lo, 3), round(hi, 3)
            s[f"n_paired_{stem}"] = n
        out.append(s)
    return out


def groups(v):
    a = "alks" if v["cls"] == "alks" else "hdv"
    return ("all", v["route"], a, f"{v['route']}_{a}")


def one_run(f):
    d = json.load(gzip.open(f, "rt"))
    r, warm, end = d["row"], d["warm"], d["t_end"]
    key = {"name": r["name"], "q": r["q"], "seed": r["seed"]}
    g = defaultdict(lambda: defaultdict(list))
    times, entry = defaultdict(list), defaultdict(int)
    for v in d["vehicles"]:
        p = v["depart"]
        if warm <= p < end:
            ff = ROUTE_LEN[v["route"]] / (LIMIT * v["sf"])
            arr = v.get("arr")
            done = arr is not None and arr <= end
            dep = v.get("dep")
            for k in groups(v):
                x = g[k]
                x["tis"].append((arr if done else end) - p)
                x["wait"].append(dep - p if dep is not None and dep < end else end - p)
                x["done"].append(done)
                if done:
                    x["delay"].append(arr - p - ff)
        chain = ("e1", "e2", "e3a", "e3", "e4", "e5") if v["route"] == "main" else ("er", "erj", "e3a", "e3", "e4", "e5")
        a = "alks" if v["cls"] == "alks" else "hdv"
        for x, y in zip(chain, chain[1:]):
            if x in v and y in v and warm <= v[x][0] < end:
                times[(v["route"], a, x[1:])].append(v[y][0] - v[x][0])
        for e in ("e2", "e3a", "e3", "e4", "e5"):
            if e in v and warm <= v[e][0] < end:
                entry[(v["route"], a, e[1:], v[e][1])] += 1
    delay = [{**key, "group": k, "n": len(x["tis"]), "finished_pct": 100 * np.mean(x["done"]), "time_in_system_s": float(np.mean(x["tis"])), "insertion_wait_s": float(np.mean(x["wait"])),
              "delay_finished_s": float(np.mean(x["delay"])) if x["delay"] else None, "delay_p50_s": float(np.median(x["delay"])) if x["delay"] else None,
              "delay_p95_s": float(np.percentile(x["delay"], 95)) if x["delay"] else None, "delay_max_s": float(np.max(x["delay"])) if x["delay"] else None} for k, x in g.items()]
    lanes, series = [], []
    b0, b1 = int(warm // 60), int(end // 60)
    for lane, bins in d["lanes"].items():
        L = LEN[lane.rsplit("_", 1)[0]]
        n = nv = h = 0.0
        for b in range(b0, b1):
            c = bins.get(str(b), [0, 0.0, 0])
            n, nv, h = n + c[0], nv + c[1], h + c[2]
            series.append({**key, "lane": lane, "bin_min": b, "density_veh_km": c[0] / 60 / L * 1000, "speed_ms": c[1] / c[0] if c[0] else None, "flow_veh_h": c[1] / 60 / L * 3600, "halting": c[2] / 60})
        secs = (b1 - b0) * 60
        lanes.append({**key, "lane": lane, "density_veh_km": n / secs / L * 1000, "speed_ms": nv / n if n else None, "flow_veh_h": nv / secs / L * 3600, "halting": h / secs})
    return {"delay": delay, "lanes": lanes, "series": series, "lc": [{**key, "edge": k.split("|")[0], "type": k.split("|")[1], "dir": k.split("|")[2], "count": c} for k, c in d["lc"].items()],
            "times": [{**key, "route": k[0], "type": k[1], "edge": k[2], "median_s": float(np.median(v)), "p95_s": float(np.percentile(v, 95))} for k, v in times.items()],
            "entry": [{**key, "route": k[0], "type": k[1], "edge": k[2], "lane": k[3], "count": c} for k, c in entry.items()],
            "demand": d["vehicles"] if r["name"] == "F0" else None}


def med_table(rows, by, vals):
    G = defaultdict(list)
    for r in rows:
        G[tuple(r[k] for k in by)].append(r)
    out = []
    for k, v in sorted(G.items(), key=str):
        s = dict(zip(by, k))
        s["n_runs"] = len(v)
        for x in vals:
            y = [r[x] for r in v if r.get(x) is not None]
            s[x] = float(np.median(y)) if y else None
        out.append(s)
    return out


def main():
    T.mkdir(parents=True, exist_ok=True)
    files = sorted(B.rglob("rows.jsonl"))
    seen = {}
    for f in files:
        for line in open(f):
            r = json.loads(line)
            k = json.dumps(r, sort_keys=True)
            seen.setdefault(k, []).append(str(f.parent.relative_to(B)))
    with gzip.open(T / "rows_all.jsonl.gz", "wt") as w:
        for k, src in seen.items():
            w.write(json.dumps({**json.loads(k), "src": src}) + "\n")
    print("rows", sum(1 for f in files for _ in open(f)), "unique", len(seen), flush=True)
    with ProcessPoolExecutor(8) as ex:
        summ = [s for part in ex.map(summarise, map(str, files)) for s in part]
    write("summary_all.csv", summ)
    arms = []
    for f in sorted(B.rglob("*_spec.json")):
        for s in json.load(open(f)):
            arms.append({"spec": str(f.relative_to(B)), "name": s["name"], "model": json.dumps(s["model"]), "kw": json.dumps(s["kw"]), "share": s.get("share", 0.5), "levels": json.dumps(s["levels"]),
                         "seed_min": min(s["seeds"]), "seed_max": max(s["seeds"]), "n_seeds": len(s["seeds"])})
    write("arms.csv", arms)
    curves = []
    for f in sorted(B.rglob("*_updates.jsonl")):
        u = [json.loads(x) for x in open(f)]
        if not u:
            continue
        fifth = max(len(u) // 5, 1)
        mid = u[len(u) // 2 - fifth // 2:len(u) // 2 + fifth // 2 + 1]
        curves.append({"file": str(f.relative_to(B)), "updates": len(u), "r_first": float(np.mean([x["r"] for x in u[:fifth]])), "r_mid": float(np.mean([x["r"] for x in mid])), "r_last": float(np.mean([x["r"] for x in u[-fifth:]])),
                       "entropy_first": u[0]["entropy"], "entropy_last": u[-1]["entropy"], "value_loss_last": u[-1]["value_loss"], "wall_s": u[-1]["wall"]})
    write("training_updates.csv", curves)
    eps = []
    for f in sorted(B.rglob("*_episodes.jsonl")):
        e = defaultdict(list)
        for x in open(f):
            r = json.loads(x)
            if "q" in r:
                e[r["q"]].append(r)
        for q, v in sorted(e.items()):
            fifth = max(len(v) // 5, 1)
            s = {"file": str(f.relative_to(B)), "q": q, "episodes": len(v), "collisions_sum": sum(r.get("collisions", 0) for r in v)}
            for k in ("passed", "mean_v", "N", "E30", "brake3", "changes", "reversals"):
                if k in v[0]:
                    s[k + "_first"] = float(np.median([r[k] for r in v[:fifth]]))
                    s[k + "_last"] = float(np.median([r[k] for r in v[-fifth:]]))
            eps.append(s)
    write("training_episodes.csv", eps)
    with tarfile.open(T / "logs.tar.gz", "w:gz") as t:
        for pat in ("*_updates.jsonl", "*_episodes.jsonl", "*_config.json", "*.json"):
            for f in sorted(B.rglob(pat)):
                if "code_" not in str(f):
                    t.add(f, arcname=str(f.relative_to(B)))
    with tarfile.open(T / "launchers.tar.gz", "w:gz") as t:
        for f in sorted(B.glob("*.sh")) + sorted(B.rglob("mkeval.py")):
            t.add(f, arcname=str(f.relative_to(B)))
    (T / "policies").mkdir(exist_ok=True)
    for pat in ("*_final.pt", "*_final.zip"):
        for f in sorted((B / "night").rglob(pat)):
            shutil.copy(f, T / "policies" / str(f.relative_to(B / "night")).replace("/", "_"))
    runs = sorted((X / "detail/runs").glob("*.json.gz"))
    print("detail runs", len(runs), flush=True)
    P = defaultdict(list)
    demand = []
    with ProcessPoolExecutor(8) as ex:
        for o, f in zip(ex.map(one_run, map(str, runs), chunksize=8), runs):
            for k in ("delay", "lanes", "series", "lc", "times", "entry"):
                P[k] += o[k]
            if o["demand"]:
                r = o["delay"][0]
                demand.append((r["q"], r["seed"], o["demand"]))
    write("detail_delay_per_run.csv.gz", P["delay"])
    write("detail_lanes_per_run.csv.gz", P["lanes"])
    write("detail_lane_changes_per_run.csv.gz", P["lc"])
    write("detail_edge_times_per_run.csv.gz", P["times"])
    write("detail_entry_lanes_per_run.csv.gz", P["entry"])
    dv = ("n", "finished_pct", "time_in_system_s", "insertion_wait_s", "delay_finished_s", "delay_p50_s", "delay_p95_s", "delay_max_s")
    write("detail_delay.csv", med_table(P["delay"], ("name", "q", "group"), dv))
    write("detail_lanes.csv", med_table(P["lanes"], ("name", "q", "lane"), ("density_veh_km", "speed_ms", "flow_veh_h", "halting")))
    write("detail_lane_timeseries.csv.gz", med_table(P["series"], ("name", "q", "lane", "bin_min"), ("density_veh_km", "speed_ms", "flow_veh_h", "halting")))
    write("detail_lane_changes.csv", med_table(P["lc"], ("name", "q", "edge", "type", "dir"), ("count",)))
    write("detail_edge_times.csv", med_table(P["times"], ("name", "q", "route", "type", "edge"), ("median_s", "p95_s")))
    write("detail_entry_lanes.csv", med_table(P["entry"], ("name", "q", "route", "type", "edge", "lane"), ("count",)))
    D = defaultdict(list)
    for q, s, vs in demand:
        for v in vs:
            D[(q, v["route"], v["cls"])].append(v)
    rows = []
    for (q, route, cls), vs in sorted(D.items()):
        s = {"q": q, "route": route, "cls": cls, "vehicles_per_seed": len(vs) / max(len({x[1] for x in demand if x[0] == q}), 1)}
        for k in ("sf", "tau", "sigma", "length", "asl"):
            y = [v[k] for v in vs if v.get(k) is not None]
            if y:
                s[k + "_p5"], s[k + "_p50"], s[k + "_p95"] = (round(float(x), 3) for x in np.percentile(y, [5, 50, 95]))
        rows.append(s)
    write("detail_demand.csv", rows)
    used = defaultdict(set)
    for k, src in seen.items():
        r = json.loads(k)
        for x in src:
            used[r["seed"]].add(x)
    write("seeds_used.csv", [{"seed": s, "sources": " ".join(sorted(v))} for s, v in sorted(used.items())])
    for f in (X / "plant").iterdir():
        if f.is_file() and f.name != "plant.json" and not f.name.endswith(".rou.xml"):
            shutil.copy(f, T / f.name)
    with open(X / "plant/plant.json", "rb") as a, gzip.open(T / "plant.json.gz", "wb") as b:
        shutil.copyfileobj(a, b)
    with gzip.open(T / "example_routes_7419650_5300.rou.xml.gz", "wb") as b:
        b.write((X / "plant/example_routes_cav_7419650_5300.rou.xml").read_bytes())
    for f in (X / "system").iterdir():
        if f.name != "journal_b_units.txt.gz":
            shutil.copy(f, T / ("system_" + f.name))
    print("sizes MB", sorted(((round(f.stat().st_size / 1e6, 2), f.name) for f in T.iterdir() if f.is_file()), reverse=True)[:5], flush=True)


if __name__ == "__main__":
    main()
