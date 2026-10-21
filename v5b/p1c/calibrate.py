"""P1c calibration, stage 1 (gate page §2, approved V138): 54 configurations x 10 throw-away seeds 7,430,000-009,
clean day, no control, ramped demand. Measures breakdown, pre-queue flow, queue discharge flow (QDF) and the drop,
then applies the gate's selection rule on T1a-T1c (drop, QDF, artefacts).

Usage: python -m v5b.p1c.calibrate run  --out DIR [--workers N]
       python -m v5b.p1c.calibrate analyse --out DIR
"""
from __future__ import annotations

import argparse
import itertools
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

from v5b.d1.config import PYTHON_BIN, REPO_ROOT, clean_sumo_env

SEEDS = list(range(7_430_000, 7_430_010))      # BN4 stage 1 (V139); WZ uses --seed0 7430010 (V141)
GRID = {"merge": ["zip20", "zip100", "laneend"], "cf": ["IDM", "EIDM", "Krauss"], "lc_coop": [1.0, 0.5, 0.2],
        "speed_dev": [0.10, 0.05]}
DEFAULTS = {"merge": "zip100", "cf": "IDM", "lc_coop": 1.0, "speed_dev": 0.10}
WARM, RAMP, HOLD = 300.0, 1200.0, 1200.0
RAMPS = {"bn4": (1200.0, 2400.0), "wz": (2400.0, 4800.0)}
BOTT_LANES = {"bn4": 1, "wz": 2}
FREE = 23.0
T1A, T1B = (0.03, 0.20), (1770.0, 2330.0)


def profile(geom: str = "bn4") -> list:
    Q0, Q1 = RAMPS[geom]
    p = [(0.0, WARM, Q0)]
    n = int(RAMP // 60)
    for i in range(n):
        p.append((WARM + 60 * i, WARM + 60 * (i + 1), Q0 + (Q1 - Q0) * (i + 0.5) / n))
    p.append((WARM + RAMP, WARM + RAMP + HOLD, Q1))
    return p


STAGE2 = {"lc_coop_speed": [0.0, 0.5], "decel": [3.0, 4.5]}     # gate §2 stage 2, with step 0.25 s


def configs(geom: str = "bn4", stage: int = 1):
    for v in itertools.product(*GRID.values()):
        base = dict(zip(GRID.keys(), v), step=0.5, geom=geom)
        if stage == 1:
            yield base
        else:
            for w in itertools.product(*STAGE2.values()):
                yield {**base, **dict(zip(STAGE2.keys(), w)), "step": 0.25}


def _cpu_util(dt: float = 3.0) -> float:
    def snap():
        f = [int(x) for x in open("/proc/stat").readline().split()[1:9]]
        return sum(f), f[3] + f[4]
    t1, i1 = snap()
    time.sleep(dt)
    t2, i2 = snap()
    return 100.0 * (1 - (i2 - i1) / max(t2 - t1, 1))


def run(out: Path, workers: int, geom: str = "bn4", seeds=SEEDS, stage: int = 1) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "runs").mkdir(exist_ok=True)
    jobs = []
    for cfg in configs(geom, stage):
        tag = f"{cfg['geom']}_{cfg['merge']}_{cfg['cf']}_lc{cfg['lc_coop']:g}_sd{cfg['speed_dev']:g}"
        if stage == 2:
            tag += f"_st0.25_lcs{cfg['lc_coop_speed']:g}_b{cfg['decel']:g}"
        for s in seeds:
            f = out / "runs" / f"{tag}_s{s}.json"
            if not f.exists():
                jobs.append({"cfg": cfg, "arm": "NC", "incident": "none", "profile": profile(geom), "seed": s,
                             "out": str(f), "series": True})
    print(f"{len(jobs)} jobs, cpu {_cpu_util():.0f} %", flush=True)
    env = clean_sumo_env()

    def one(j):
        while _cpu_util(1.0) > 90.0:          # CLAUDE.md CPU rule: launch only below 90 %
            time.sleep(30)
        r = subprocess.run(["nice", "-n", "10", PYTHON_BIN, "-m", "v5b.p1c.episode", "--job", json.dumps(j),
                            "--run-dir", str(out / "rd")], cwd=REPO_ROOT, env=env, capture_output=True, text=True)
        return j["out"], r.returncode, r.stderr[-300:] if r.returncode else ""

    t0 = time.time()
    with ThreadPoolExecutor(workers) as ex:
        for i, (f, rc, err) in enumerate(ex.map(one, jobs), 1):
            if rc:
                print("FAIL", f, err, flush=True)
            if i % 50 == 0:
                print(f"{i}/{len(jobs)} done, {time.time() - t0:.0f} s", flush=True)
    print(f"all done in {time.time() - t0:.0f} s", flush=True)


def measure(r: dict) -> dict:
    """Breakdown, pre-queue flow, QDF and drop from the 30-s series (gate §2)."""
    ser = r["series"]                       # (t, exit count, e4 speed, e3 speed, r)
    t = np.array([x[0] for x in ser])
    q = np.array([x[1] for x in ser]) * 120.0                  # veh/h per 30-s interval
    # V143: breakdown from the gate's single location ('up' loops, 6th series field); runs without it (BN4 stage 1,
    # V139) used min(edge-3, edge-4), a disclosed deviation
    v = np.array([x[5] for x in ser]) if len(ser[0]) > 5 else \
        np.minimum(np.array([x[2] for x in ser]), np.array([x[3] for x in ser]))
    slow = v < 0.5 * FREE
    hold_end = WARM + RAMP + HOLD
    tb = None
    for i in range(len(t) - 3):
        if t[i] > WARM and slow[i:i + 4].all():
            tb = t[i]
            break
    out = {"breakdown_s": tb}
    if tb is None:
        out.update(pre=None, qdf=None, drop=None)
        return out
    pre_mask = (t > WARM) & (t <= tb)
    roll = np.convolve(q, np.ones(10) / 10, mode="valid")      # 5-min rolling mean, ends at index i+9
    ends = t[9:]
    cand = roll[(ends > WARM) & (ends <= tb)] if pre_mask.any() else np.array([])
    pre = float(cand.max()) if cand.size else float(q[pre_mask].max()) if pre_mask.any() else None
    m = (t >= tb + 300) & (t <= hold_end)
    qdf = float(q[m].mean()) if m.any() else None
    out.update(pre=pre, qdf=qdf, drop=(1 - qdf / pre) if pre and qdf else None)
    return out


def analyse(out: Path, geom: str = "bn4", stage: int = 1) -> dict:
    rows = {}
    for f in sorted((out / "runs").glob("*.json")):
        r = json.loads(f.read_text())
        c = r["cfg"]
        key = (c["merge"], c["cf"], c["lc_coop"], c["speed_dev"], c.get("lc_coop_speed"), c.get("decel"), c.get("step"))
        m = measure(r)
        rows.setdefault(key, []).append({**m, "valid": r["valid"], "teleports": r["teleports"],
                                         "collisions": r["collisions"], "estops": r["emergency_stops"],
                                         "served": r["served_ctrl_vph"]})
    table = []
    for key, rs in rows.items():
        drops = [x["drop"] for x in rs if x["drop"] is not None]
        qdfs = [x["qdf"] for x in rs if x["qdf"] is not None]
        med_drop = float(np.median(drops)) if drops else None
        in_range = sum(T1A[0] <= d <= T1A[1] for d in drops) / len(rs)
        med_qdf = float(np.median(qdfs)) if qdfs else None
        artefact_free = all(x["valid"] and x["teleports"] == 0 and x["collisions"] == 0 for x in rs)
        t1a = med_drop is not None and T1A[0] <= med_drop <= T1A[1] and in_range >= 0.75
        t1b = med_qdf is not None and T1B[0] <= med_qdf / BOTT_LANES[geom] <= T1B[1]   # per lane (V141)
        nondef = sum(v != DEFAULTS[k] for k, v in zip(DEFAULTS, key)) + sum(x is not None for x in key[4:6]) \
            + (key[6] != 0.5)
        table.append({"merge": key[0], "cf": key[1], "lc_coop": key[2], "speed_dev": key[3], "lc_coop_speed": key[4],
                      "decel": key[5], "step": key[6], "n": len(rs),
                      "n_breakdown": len(drops), "median_drop": med_drop, "share_in_range": in_range,
                      "median_qdf": med_qdf, "median_pre": float(np.median([x["pre"] for x in rs if x["pre"]]))
                      if any(x["pre"] for x in rs) else None,
                      "estops": sum(x["estops"] for x in rs), "artefact_free": artefact_free,
                      "T1a": t1a, "T1b": t1b, "pass": t1a and t1b and artefact_free, "non_default": nondef})
    passing = [r for r in table if r["pass"]]
    chosen = min(passing, key=lambda r: (r["non_default"], abs(r["median_drop"] - 0.07))) if passing else None
    res = {"table": sorted(table, key=lambda r: (not r["pass"], r["non_default"])), "chosen": chosen,
           "n_pass": len(passing)}
    (out / f"calibration_stage{stage}.json").write_text(json.dumps(res, indent=1))
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "analyse"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=24)
    ap.add_argument("--geom", default="bn4")
    ap.add_argument("--seed0", type=int, default=7_430_000)
    ap.add_argument("--stage", type=int, default=1)
    a = ap.parse_args(argv)
    if a.cmd == "run":
        run(Path(a.out), a.workers, a.geom, list(range(a.seed0, a.seed0 + 10)), a.stage)
    res = analyse(Path(a.out), a.geom, a.stage)
    print(json.dumps({"n_pass": res["n_pass"], "chosen": res["chosen"]}, indent=1))
    for r in res["table"]:
        print(f"{r['merge']:8} {r['cf']:6} lc{r['lc_coop']:<4} sd{r['speed_dev']:<5} bd {r['n_breakdown']:2}/{r['n']} "
              f"drop {r['median_drop'] if r['median_drop'] is None else round(100 * r['median_drop'], 1)} "
              f"in {r['share_in_range']:.2f} qdf {r['median_qdf'] if r['median_qdf'] is None else round(r['median_qdf'])} "
              f"pre {r['median_pre'] if r['median_pre'] is None else round(r['median_pre'])} estops {r['estops']} "
              f"ok {int(r['artefact_free'])} PASS {int(r['pass'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
