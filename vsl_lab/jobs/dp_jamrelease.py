"""Day-pattern P3 pre-check: SUMO single-lane queue discharge (docs/lab/day_pattern/p3_precheck_protocol.md).

python -m vsl_lab.jobs.dp_jamrelease one --cand K0 --step 0.5 --seed 7190000 --out-root <dir>
python -m vsl_lab.jobs.dp_jamrelease smoke --gate-ok
python -m vsl_lab.jobs.dp_jamrelease check --gate-ok
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

from vsl_lab.config import NET_CACHE, NETCONVERT_BIN, REPO_ROOT, RUNS_ROOT, SUMO_BIN, clean_sumo_env

V_LIM = 29.0
N_VEH, RATE_S, T_GREEN = 150, 3.0, 700.0   # Addendum A (was 1.2 s, 300 s: insertion backlog)
LOOPS = {"d200": 200.0, "d600": 600.0}
CANDS = ("K0", "K1", "K2", "K3")
STEPS = (0.5, 0.2)
SMOKE_SEED = 7190000
CHK_SEEDS = list(range(7190001, 7190011))
OUT = REPO_ROOT / "docs" / "lab" / "day_pattern"


def build_net() -> Path:
    d = NET_CACHE / "dp_lane_v2"   # Addendum A: up = 3,000 m
    net = d / "lane.net.xml"
    if net.exists() and (d / "lane.det.add.xml").exists():
        return d
    d.mkdir(parents=True, exist_ok=True)
    (d / "n.nod.xml").write_text('<nodes>\n  <node id="n0" x="0" y="0" type="priority"/>\n'
                                 '  <node id="stop" x="3000" y="0" type="traffic_light" tlType="static"/>\n'
                                 '  <node id="n2" x="4000" y="0" type="priority"/>\n</nodes>\n')
    (d / "n.edg.xml").write_text(f'<edges>\n  <edge id="up" from="n0" to="stop" numLanes="1" speed="{V_LIM}"/>\n'
                                 f'  <edge id="down" from="stop" to="n2" numLanes="1" speed="{V_LIM}"/>\n</edges>\n')
    tmp = d / f"lane.net.xml.tmp{os.getpid()}.xml"
    r = subprocess.run([NETCONVERT_BIN, "-n", str(d / "n.nod.xml"), "-e", str(d / "n.edg.xml"), "--no-turnarounds",
                        "true", "-o", str(tmp)], env=clean_sumo_env(), capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-1500:])
    tmp.replace(net)
    add = ["<additional>"] + [f'  <inductionLoop id="{k}" lane="down_0" pos="{x}" period="60" file="NUL"/>'
                              for k, x in LOOPS.items()] + ["</additional>"]
    (d / "lane.det.add.xml").write_text("\n".join(add) + "\n")
    return d


def vtypes(cand: str, seed: int) -> str:
    if cand == "K0":
        return '  <vType id="human" carFollowModel="Krauss"/>'
    if cand == "K1":
        return '  <vType id="human" carFollowModel="EIDM"/>'
    if cand == "K2":
        return '  <vType id="human" carFollowModel="IDM"/>'
    if cand == "K3":   # S1 B3 car classes, no trucks, no AVs
        from vsl_lab.plants.bn4 import B3_CENTRE, b3_vtypes_xml
        pop = dict(B3_CENTRE, truck_share=0.0)
        xml = b3_vtypes_xml(seed, av_share=0.0, pop=pop)
        return "\n".join(ln for ln in xml.splitlines() if 'id="truck_' not in ln and 'id="av"' not in ln)
    raise ValueError(cand)


def run_one(cand: str, step: float, seed: int, out_root: Path) -> dict:
    import libsumo as ls
    t0w = time.time()
    d = build_net()
    run_dir = out_root / f"{cand}_dt{step}_s{seed}_pid{os.getpid()}"
    run_dir.mkdir(parents=True, exist_ok=True)
    rou = run_dir / f"r_{cand}_dt{step}_s{seed}_pid{os.getpid()}.rou.xml"
    veh = [f'  <vehicle id="v{k:03d}" type="human" route="r" depart="{math.ceil(k * RATE_S / step - 1e-9) * step:.2f}" '
           f'departLane="0" departSpeed="max"/>' for k in range(N_VEH)]
    rou.write_text("<routes>\n" + vtypes(cand, seed) + '\n  <route id="r" edges="up down"/>\n' + "\n".join(veh)
                   + "\n</routes>\n")
    ls.start([SUMO_BIN, "-n", str(d / "lane.net.xml"), "-r", str(rou), "-a", str(d / "lane.det.add.xml"),
              "--step-length", str(step), "--seed", str(seed), "--time-to-teleport", "1000",   # Addendum B
              "--collision.action", "warn", "--no-step-log", "true", "--log", str(run_dir / "sumo.log")])
    ls.trafficlight.setRedYellowGreenState("stop", "r")
    seen = {k: {} for k in LOOPS}
    spd200 = {}                                     # review fix #6: speed at first detection on the 200 m loop
    tele = coll = 0
    queued_ok = None
    t = 0.0
    while t < 2000.0:
        ls.simulationStep()
        t = ls.simulation.getTime()
        tele += ls.simulation.getStartingTeleportNumber()
        coll += ls.simulation.getCollidingVehiclesNumber()
        if queued_ok is None and t >= T_GREEN - 1.0 - 1e-9:
            ids = ls.edge.getLastStepVehicleIDs("up")
            queued_ok = len(ids) == N_VEH and all(ls.vehicle.getSpeed(v) < 0.1 for v in ids)
        if abs(t - T_GREEN) < step / 2:
            ls.trafficlight.setRedYellowGreenState("stop", "G")
        for k in LOOPS:
            for v in ls.inductionloop.getLastStepVehicleIDs(k):
                if v not in seen[k]:
                    seen[k][v] = t
                    if k == "d200":
                        spd200[v] = ls.vehicle.getSpeed(v)
        if len(seen["d600"]) == N_VEH:
            break
    ls.close()
    out = {"cand": cand, "step": step, "seed": seed, "teleports": tele, "collisions": coll, "queued_ok": queued_ok,
           "wall_s": round(time.time() - t0w, 2)}
    for k in LOOPS:
        ts = sorted(seen[k].values())
        out[f"n_{k}"] = len(ts)
        out[f"Q_{k}"] = 100 * 3600.0 / (ts[120] - ts[20]) if len(ts) > 120 and ts[120] > ts[20] else None
        out[f"t1_{k}"] = ts[0] - T_GREEN if ts else None
    order200 = sorted(seen["d200"], key=seen["d200"].get)[20:121]       # the same vehicles 21..121 as Q
    out["mean_speed_d200_mps"] = float(np.mean([spd200[v] for v in order200])) if len(order200) == 101 else None
    out["hash"] = hashlib.sha1(json.dumps({k: sorted(seen[k].items()) for k in LOOPS}).encode()).hexdigest()[:16]
    (run_dir / "summary.json").write_text(json.dumps(out, indent=1))
    return out


def _job(tag, cand, step, seed, root):
    from vsl_lab.ops.scheduler import Job
    return Job(jid=f"{tag}_{cand}_dt{step}_s{seed}",
               argv=["vsl_lab.jobs.dp_jamrelease", "one", "--cand", cand, "--step", str(step), "--seed", str(seed),
                     "--out-root", str(root / tag)])


def _load(root: Path, tag: str) -> list:
    return [json.loads(p.read_text()) for p in (root / tag).glob("*/summary.json")]


def analyse(root: Path) -> dict:
    chk, det = _load(root, "chk"), _load(root, "det")
    res = {"protocol": "docs/lab/day_pattern/p3_precheck_protocol.md", "raw": str(root), "cands": {}}
    for c in CANDS:
        rc = {}
        for st in STEPS:
            rows = [o for o in chk if o["cand"] == c and o["step"] == st]
            q = [o["Q_d200"] for o in rows if o["Q_d200"] is not None]
            q6 = [o["Q_d600"] for o in rows if o["Q_d600"] is not None]
            med = float(np.median(q)) if q else None
            ref = next((o for o in rows if o["seed"] == CHK_SEEDS[0]), None)
            dd = [o for o in det if o["cand"] == c and o["step"] == st]
            det_ok = bool(dd) and ref is not None and all(o["hash"] == ref["hash"] for o in dd)
            clean = all(o["teleports"] == 0 and o["collisions"] == 0 for o in rows) and len(rows) == len(CHK_SEEDS)
            queued = all(o["queued_ok"] for o in rows)
            ok = med is not None and 1600.0 <= med <= 2400.0 and clean and det_ok and queued and len(q) == len(CHK_SEEDS)
            rc[str(st)] = {"n": len(rows), "median_Q_d200": med, "min_Q": min(q) if q else None,
                           "max_Q": max(q) if q else None, "median_Q_d600": float(np.median(q6)) if q6 else None,
                           "median_mean_speed_d200_mps": float(np.median([o["mean_speed_d200_mps"] for o in rows
                                                                          if o.get("mean_speed_d200_mps") is not None]))
                           if rows else None,
                           "median_startup_s": float(np.median([o["t1_d200"] for o in rows if o["t1_d200"] is not None]))
                           if rows else None, "teleports": sum(o["teleports"] for o in rows),
                           "collisions": sum(o["collisions"] for o in rows), "queued_ok_all": queued,
                           "determinism": det_ok, "PASS": bool(ok)}
        rc["PASS_any_step"] = [st for st in map(str, STEPS) if rc[st]["PASS"]]
        res["cands"][c] = rc
    res["outcome"] = "P3-ALIVE" if any(res["cands"][c]["PASS_any_step"] for c in CANDS) else "P3-OUT"
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "p3_precheck.json").write_text(json.dumps(res, indent=1))
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["one", "smoke", "check", "analyse"])
    ap.add_argument("--cand", default="K0")
    ap.add_argument("--step", type=float, default=0.5)
    ap.add_argument("--seed", type=int, default=SMOKE_SEED)
    ap.add_argument("--out-root", default=str(RUNS_ROOT / "dp" / "one"))
    ap.add_argument("--root", default=None)
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--gate-ok", action="store_true")
    a = ap.parse_args(argv)
    if a.what == "one":
        try:
            o = run_one(a.cand, a.step, a.seed, Path(a.out_root))
            print(json.dumps({k: o[k] for k in ("cand", "step", "seed", "Q_d200", "teleports", "collisions",
                                                "queued_ok", "wall_s")}))
            return 0
        except Exception as exc:
            import traceback
            print(json.dumps({"error": f"{type(exc).__name__}: {exc}", "traceback": traceback.format_exc()[-1500:]}))
            return 2
    from vsl_lab.ops import ledger
    from vsl_lab.ops.scheduler import run_batch
    if a.what == "analyse":
        print(json.dumps({"outcome": analyse(Path(a.root))["outcome"]}))
        return 0
    build_net()
    root = RUNS_ROOT / "dp" / f"p3_precheck_{a.what}_{int(time.time())}"
    if a.what == "smoke":
        jobs = [_job("smoke", c, 0.5, SMOKE_SEED, root) for c in CANDS]
        rep = run_batch(jobs, root / "batch", max_workers=4, gate_ok=a.gate_ok)
        rows = _load(root, "smoke")
        s = {o["cand"]: {k: o[k] for k in ("Q_d200", "Q_d600", "t1_d200", "teleports", "collisions", "queued_ok")}
             for o in rows}
        (root / "smoke_summary.json").write_text(json.dumps(s, indent=1))
        ledger.append("DP", "P3-pre-smoke", "S", "dp_jamrelease_smoke", {"cands": CANDS}, f"{SMOKE_SEED} (throw-away)",
                      len(jobs), {"proc_failed": rep.n_failed_proc}, {c: v.get("queued_ok") for c, v in s.items()},
                      notes=str(root))
        print(str(root / "smoke_summary.json"))
        return 0
    jobs = [_job("chk", c, st, s, root) for c in CANDS for st in STEPS for s in CHK_SEEDS]
    jobs += [_job("det", c, st, CHK_SEEDS[0], root) for c in CANDS for st in STEPS]
    rep = run_batch(jobs, root / "batch", max_workers=a.workers, gate_ok=a.gate_ok)
    res = analyse(root)
    ledger.append("DP", "P3-pre", "S", "dp_jamrelease_check", {"cands": CANDS, "steps": STEPS},
                  f"{CHK_SEEDS[0]}-{CHK_SEEDS[-1]}", len(jobs), {"proc_failed": rep.n_failed_proc},
                  {"outcome": res["outcome"], **{c: res["cands"][c]["PASS_any_step"] for c in CANDS},
                   "wall_s": rep.wall_s}, notes=str(root))
    print(json.dumps({"outcome": res["outcome"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
