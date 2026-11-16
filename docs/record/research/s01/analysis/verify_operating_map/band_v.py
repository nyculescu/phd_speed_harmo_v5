"""(c) Row identity measured vs round 2 stored rows, and band_table.csv reproduction from both row sets."""
import csv
import json
from pathlib import Path

import numpy as np

D = Path("/home/catalin/work/phd/v5b1_runs/measure_s01_remote")
R2 = Path("/home/catalin/work/phd/v5b1_runs/round2")
CSV = Path("/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/round2/report/band_table.csv")
OUT = Path(__file__).parent
L = []


def rows(p):
    for line in open(p):
        yield json.loads(line)


def norm(v):
    return json.loads(json.dumps(v))


for kind in ("band", "test"):
    meas = {(r["name"], float(r["q"]), int(r["seed"])): r for r in rows(D / f"rows_{kind}.jsonl")}
    r2 = {}
    for r in rows(R2 / kind / "rows_6c49e7e.jsonl"):
        k = (r["name"], float(r["q"]), int(r["seed"]))
        if k in meas:
            r2[k] = r
    missing = [k for k in meas if k not in r2]
    same = diffkeys = 0
    dk = {}
    lacking = set()
    extra = set()
    for k, r in r2.items():
        m = meas[k]
        bad = [x for x in r if x != "cfg" and (x not in m or norm(m[x]) != norm(r[x]))]
        lacking |= {x for x in r if x not in m}
        extra |= {x for x in m if x not in r}
        if bad:
            diffkeys += 1
            for x in bad:
                dk[x] = dk.get(x, 0) + 1
        else:
            same += 1
    L.append(f"{kind}: measured rows {len(meas)}, matched in round 2 {len(r2)}, missing {len(missing)}, identical {same}, differing {diffkeys} {dk}; "
             f"keys only in round 2: {sorted(lacking)}; extra keys in measured: {len(extra)} (m_* {sum(x.startswith('m_') for x in extra)}): {sorted(x for x in extra if not x.startswith('m_'))}")

ARMS = {"tail arm": [f"t{i}" for i in range(5)], "sw arm": [f"s{i}u500" for i in range(5)],
        "v3w arm": ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"], "baseline-v3 arm": [f"d{i}u500" for i in range(5)],
        "nc": ["nc"], "p333": ["p333"], "os1_15_10": ["os1_15_10"], "3e": ["3e"]}


def g(r, k):
    v = r.get(k)
    return 0.0 if v is None else float(v)


def effect(P, O, sign=-1):
    ss = sorted(set(P) & set(O))
    p, o = np.array([P[s] for s in ss]), np.array([O[s] for s in ss])
    ref = max(float(np.median(o)), 1e-9)
    d = sign * (p - o) / ref * 100
    b = np.median(d[np.random.default_rng(20261104).integers(0, len(d), (20000, len(d)))], axis=1)
    lo, hi = np.percentile(b, (2.5, 97.5))
    return f"{round(float(np.median(d)), 1)} [{round(float(lo), 1)}, {round(float(hi), 1)}]"


ref = list(csv.DictReader(open(CSV)))
for src in (D / "rows_band.jsonl", R2 / "band/rows_6c49e7e.jsonl"):
    T = {}
    for r in rows(src):
        T.setdefault((r["name"], float(r["q"])), {})[int(r["seed"])] = r
    ok = bad = 0
    bads = []
    for row in ref:
        q, nm = float(row["q"]), row["name"]
        runs = [T[(f"B|{m}", q)] for m in ARMS[nm]]
        seeds = sorted(set.intersection(*(set(x) for x in runs)))
        A = {k: {s: float(np.mean([g(x[s], k) for x in runs])) for s in seeds} for k in ("all_delay", "passed", "ttc_net", "sev3", "b3_step", "collisions")}
        nc = [T[("B|nc", q)]]
        N = {k: {s: g(nc[0][s], k) for s in nc[0]} for k in ("all_delay", "ttc_net")}
        mine = {"all_delay": f"{np.median(list(A['all_delay'].values())):.1f}", "passed": f"{np.median(list(A['passed'].values())):.1f}",
                "ttc_net": f"{np.median(list(A['ttc_net'].values())):.1f}", "sev3": f"{np.median(list(A['sev3'].values())):.1f}",
                "b3_step": f"{np.median(list(A['b3_step'].values())):.1f}", "collisions_per_learner": f"{sum(A['collisions'].values()):.1f}"}
        if nm != "nc":
            mine["ttc_vs_nc_95"] = effect(A["ttc_net"], N["ttc_net"])
            mine["delay_vs_nc_95"] = effect(A["all_delay"], N["all_delay"])
        for k, v in mine.items():
            if row[k] == "":
                continue
            if row[k] == v or (k not in ("ttc_vs_nc_95", "delay_vs_nc_95") and abs(float(row[k]) - float(v)) < 0.051):
                ok += 1
            else:
                bad += 1
                bads.append((q, nm, k, row[k], v))
    L.append(f"band_table from {src.name} ({src.parent.name}): match {ok}, mismatch {bad}; first mismatches {bads[:8]}")
open(OUT / "band_v.txt", "w").write("\n".join(L))
print("\n".join(L))
