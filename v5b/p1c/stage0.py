"""A stage 0 (V251, docs/research/protocols/drafts/bind_A_core_v3.md): is BN4's drop a step artefact, and which
mechanism gives a measurable drop? No control, bn4L, teleporting off.

Phases: smoke (read-back), pre (Q1 from the V139 ramp), main (slow ramp per row and step), null (fixed-rate signal),
fallback (0.1 s, only for rows failing criterion 2 alone), then report: criteria 1-4 and the route.

Usage: python -m v5b.p1c.stage0 {smoke,pre,main,null,fallback,report} --out DIR [--workers N] [--cpu-limit F]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

from v5b.d1.config import PYTHON_BIN, REPO_ROOT, clean_sumo_env
from v5b.p1c import calibrate as cal
from v5b.p1c import plant as pl

S0 = 7_432_000
MAIN = list(range(S0, S0 + 10))
NULL = list(range(S0 + 10, S0 + 30))
PRE = list(range(S0 + 60, S0 + 63))
FALLBACK = list(range(S0 + 63, S0 + 68))
SMOKE = S0 + 90
STEPS = (0.5, 0.25)
BASE = {"geom": "bn4L", "lc_coop": 1.0, "speed_dev": 0.10, "teleport": -1.0}
ROWS = {"zipIDM": {"merge": "zip100", "cf": "IDM", "accel": 1.0},
        "zipKrauss": {"merge": "zip100", "cf": "Krauss"},
        "leIDM1": {"merge": "laneend", "cf": "IDM", "accel": 1.0},
        "leIDM26": {"merge": "laneend", "cf": "IDM", "accel": 2.6},
        "leKrauss": {"merge": "laneend", "cf": "Krauss"}}
ROUTE = (("leIDM1", "leIDM26"), ("zipIDM",), ("leKrauss",))
NULL_RATES = (0.8, 1.0, 1.2)
FREE0, RAMP, HOLD = 600.0, 9600.0, 1800.0
WIN_PQ, WIN_QDF = (-600.0, 0.0), (300.0, 900.0)
SUSTAIN = 1500.0
B = 100_000
CV_MIN, COUNTS_MIN, STEP_FLOW, STEP_DROP = 0.005, 4, 0.05, 0.03
STAND_MAX = 300.0


def cfg(row: str, step: float) -> dict:
    return {**BASE, **ROWS[row], "step": step}


def null_cfg(step: float = 0.5) -> dict:
    return {**BASE, "geom": "bn4L_null", "merge": "laneend", "cf": "IDM", "accel": 1.0, "step": step}


def slow_profile(q1: float) -> list:
    """10 min at 0.6 Q1, linear 0.75 -> 1.15 Q1 over 160 min in 1-min steps, 30-min hold at 1.15 Q1."""
    p = [(0.0, FREE0, 0.6 * q1)]
    n = int(RAMP // 60)
    for i in range(n):
        p.append((FREE0 + 60 * i, FREE0 + 60 * (i + 1), q1 * (0.75 + 0.40 * (i + 0.5) / n)))
    p.append((FREE0 + RAMP, FREE0 + RAMP + HOLD, 1.15 * q1))
    return [(round(a, 1), round(b, 1), round(q, 1)) for a, b, q in p]


def estimate(series: list) -> dict:
    """Activation from excess accumulation between e4 and exit; 10-min means of exit flow before and after (v1 §2.3).
    Free-flow reference from 300-600 s, which skips the network fill of the first 5 minutes."""
    t = np.array([r[0] for r in series])
    ex = np.array([r[1] for r in series], float)
    e4 = np.array([r[6] for r in series], float)
    x = np.cumsum(e4) - np.cumsum(ex)
    ff = (t > 300.0) & (t <= FREE0)
    x = x - np.median(x[ff])
    x_star = max(10.0, 3.0 * float(np.std(x[ff], ddof=1)))
    above = x >= x_star
    t_b = next((t[i] for i in range(len(t) - 3) if above[i:i + 4].all()), None)
    out = {"x_star": x_star, "t_b": None if t_b is None else float(t_b), "sustained": False, "pq": None, "qdf": None,
           "drop": None, "qdf_counts": [], "stand_max": float(max((r[7] for r in series), default=0.0))}
    if t_b is None:
        return out
    out["sustained"] = bool(above[(t >= t_b) & (t <= t_b + SUSTAIN)].all())

    def win(lo, hi):
        m = (t - 30.0 >= t_b + lo - 1e-6) & (t <= t_b + hi + 1e-6)
        return ex[m]
    pre, post = win(*WIN_PQ), win(*WIN_QDF)
    if len(pre) == 20 and len(post) == 20:
        out["pq"], out["qdf"] = 120.0 * float(pre.mean()), 120.0 * float(post.mean())
        out["drop"] = 1.0 - out["qdf"] / out["pq"]
        out["qdf_counts"] = [int(c) for c in post]
        out["step_down_ok"] = bool(np.median(pre[-4:]) >= 0.97 * np.median(pre[:16]))
    return out


def boot_median(x, rng, n: int | None = None) -> np.ndarray:
    x = np.asarray(x, float)
    n = n or len(x)
    return np.median(x[rng.integers(0, len(x), (B, n))], axis=1)


def tau_null(null_drops, n: int, seed: int = 20261101) -> float:
    return float(np.percentile(boot_median(null_drops, np.random.default_rng(seed), n), 95))


def lower95(drops, seed: int = 20261102) -> float:
    return float(np.percentile(boot_median(drops, np.random.default_rng(seed)), 2.5))


def row_stats(runs: list) -> dict:
    """Criteria 1 and 3 on one (row, step): runs = [{"est": estimate(...), "res": episode output}, ...]."""
    est = [r["est"] for r in runs]
    q = [e["qdf"] for e in est if e["qdf"] is not None]
    drops = [e["drop"] for e in est if e["drop"] is not None]
    cv = float(np.std(q, ddof=1) / np.mean(q)) if len(q) > 1 else None
    distinct = sum(len(set(e["qdf_counts"])) >= COUNTS_MIN for e in est)
    c1 = cv is not None and cv >= CV_MIN and distinct >= 8
    sustained = sum(e["sustained"] for e in est)
    stand_ok = sum(e["stand_max"] <= STAND_MAX for e in est)
    coll = sum(r["res"]["collisions"] for r in runs)
    c3 = sustained >= 8 and stand_ok >= 9 and coll == 0
    return {"n": len(runs), "qdf_median": float(np.median(q)) if q else None, "qdf_cv": cv, "distinct_ok": distinct,
            "c1": bool(c1), "drop_median": float(np.median(drops)) if drops else None, "drops": drops,
            "pq_median": float(np.median([e["pq"] for e in est if e["pq"]])) if q else None,
            "sustained": sustained, "stand_ok": stand_ok, "collisions": coll, "c3": bool(c3),
            "step_down_ok": sum(e.get("step_down_ok", False) for e in est)}


def step_stable(a: dict, b: dict) -> bool:
    if None in (a["qdf_median"], b["qdf_median"], a["drop_median"], b["drop_median"]):
        return False
    return (abs(b["qdf_median"] / a["qdf_median"] - 1.0) <= STEP_FLOW
            and abs(b["drop_median"] - a["drop_median"]) <= STEP_DROP)


def route(verdict: dict) -> dict:
    for group in ROUTE:
        for row in group:
            if verdict.get(row, {}).get("pass"):
                return {"route": row, "step": verdict[row]["step"]}
    return {"route": "A-UNTESTABLE(BN4)", "step": None}


def _job(c: dict, seed: int, prof: list, out: Path, arm: str = "NC") -> dict:
    # The series starts after the warm-up, so a 30-s warm-up keeps the free-flow reference window in it.
    end = prof[-1][1]
    return {"cfg": c, "arm": arm, "incident": "none", "profile": prof, "seed": seed, "out": str(out), "series": True,
            "r_min": 600.0, "warmup": 30.0, "control": end - 30.0, "t_cap": end + 3600.0}


def _cpu(dt: float = 1.0) -> float:
    return cal._cpu_util(dt) / 100.0


def run_jobs(jobs: list, out: Path, workers: int, limit: float) -> None:
    (out / "rd").mkdir(parents=True, exist_ok=True)
    jobs = [j for j in jobs if not Path(j["out"]).exists()]
    print(f"{len(jobs)} jobs to run, cpu {_cpu(3.0):.0%}", flush=True)
    env = clean_sumo_env()

    def one(j):
        while _cpu() > limit:
            time.sleep(30)
        Path(j["out"]).parent.mkdir(parents=True, exist_ok=True)
        r = subprocess.run(["nice", "-n", "10", PYTHON_BIN, "-m", "v5b.p1c.episode", "--job", json.dumps(j),
                            "--run-dir", str(out / "rd")], cwd=REPO_ROOT, env=env, capture_output=True, text=True)
        return j["out"], r.returncode, r.stderr[-400:] if r.returncode else ""
    t0, bad = time.time(), 0
    with ThreadPoolExecutor(workers) as ex:
        for i, (f, rc, err) in enumerate(ex.map(one, jobs), 1):
            if rc:
                bad += 1
                print("FAIL", f, err, flush=True)
            if i % 10 == 0:
                print(f"{i}/{len(jobs)} done, {time.time() - t0:.0f} s", flush=True)
    print(f"all done in {time.time() - t0:.0f} s, {bad} failed", flush=True)
    if bad:
        raise SystemExit(f"{bad} jobs failed")


def _load(f: Path) -> dict:
    res = json.loads(f.read_text())
    return {"res": res, "est": estimate(res["series"])}


def q1_table(out: Path) -> dict:
    """Q1 per (row, step): median pre-activation flow of the V139-ramp pre-pass; None if nothing activated."""
    q = {}
    for row in ROWS:
        for st in STEPS:
            pq = [_load(f)["est"]["pq"] for f in sorted((out / "pre").glob(f"{row}_st{st:g}_s*.json"))]
            pq = [x for x in pq if x]
            q[f"{row}_st{st:g}"] = float(np.median(pq)) if pq else None
    return q


def smoke_check(out: Path) -> list:
    """V231: every run echoes its row, step, accel, teleport setting and merge type at both drops."""
    bad = []
    for row in ROWS:
        for st in STEPS:
            f = out / "smoke" / f"{row}_st{st:g}_s{SMOKE}.json"
            if not f.exists():
                bad.append(f"{f.name}: missing")
                continue
            r = json.loads(f.read_text())
            c, p = r["cfg"], r["probe"]
            want = cfg(row, st)
            if {k: c.get(k) for k in want} != want:
                bad.append(f"{f.name}: cfg {c}")
            if abs(p["dt"] - st) > 1e-9 or abs(float(p["ttt"]) - want["teleport"]) > 1e-9:
                bad.append(f"{f.name}: dt {p['dt']} ttt {p['ttt']}")
            acc = want.get("accel") or 2.6
            if abs(p["accel"] - acc) > 1e-9 or abs(p["min_gap"] - (2.0 if want["cf"] == "IDM" else 2.5)) > 1e-9:
                bad.append(f"{f.name}: accel {p['accel']} minGap {p['min_gap']}")
            net = pl.build_net(pl.Config(**want)) / "net.xml"
            types = {j.get("id"): j.get("type") for j in ET.parse(net).getroot().iter("junction")}
            jt = "zipper" if want["merge"].startswith("zip") else "priority"
            if types.get("4") != jt or types.get("5") != jt:
                bad.append(f"{f.name}: junction types {types.get('4')}, {types.get('5')}")
            if not r["series"] or len(r["series"][0]) != 8:
                bad.append(f"{f.name}: series fields")
    for f in sorted((out / "smoke").glob("null_*.json")):
        r = json.loads(f.read_text())
        if r["cfg"]["geom"] != "bn4L_null" or not r["arm"].startswith("c") or r["n_red_onsets"] == 0:
            bad.append(f"{f.name}: null signal not metering")
    return bad


def report(out: Path) -> dict:
    stats, verdict = {}, {}
    for row in ROWS:
        for st in STEPS:
            fs = sorted((out / "main").glob(f"{row}_st{st:g}_s*.json"))
            stats[f"{row}_st{st:g}"] = row_stats([_load(f) for f in fs]) if fs else None
    nulls = {}
    for f in sorted((out / "null").glob("null_r*_s*.json")):
        rate = f.name.split("_")[1][1:]
        nulls.setdefault(rate, []).append(_load(f)["est"]["drop"])
    nulls = {k: [d for d in v if d is not None] for k, v in nulls.items()}
    for row in ROWS:
        a, b = stats.get(f"{row}_st0.5"), stats.get(f"{row}_st0.25")
        if not a or not b:
            continue
        c2 = step_stable(a, b)
        st, s = 0.5, a
        if not c2 and a["c1"] and b["c1"] and a["c3"] and b["c3"]:
            fb = sorted((out / "fallback").glob(f"{row}_st0.1_s*.json"))
            if fb:
                c = row_stats([_load(f) for f in fb])
                c2 = step_stable(b, c)
                st, s = 0.25, b
        v = {"c1": a["c1"] and b["c1"], "c2": c2, "c3": a["c3"] and b["c3"], "step": st}
        if nulls and s["pq_median"]:
            rate = min(nulls, key=lambda k: abs(float(k) - s["pq_median"]))
            v["tau_null"] = tau_null(nulls[rate], s["n"]) if nulls[rate] else None
            v["null_rate"] = float(rate)
            v["lower95"] = lower95(s["drops"]) if s["drops"] else None
            v["c4"] = v["tau_null"] is not None and v["lower95"] is not None and v["lower95"] > v["tau_null"]
        v["pass"] = bool(v["c1"] and v["c2"] and v["c3"] and v.get("c4"))
        v["zero_rung_only"] = bool(v["c1"] and v["c2"] and v["c3"] and not v.get("c4"))
        verdict[row] = v
    return {"stats": stats, "nulls": {k: {"n": len(v), "median": float(np.median(v)) if v else None}
                                      for k, v in nulls.items()}, "verdict": verdict, **route(verdict)}


def main(argv: list) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("phase", choices=("smoke", "pre", "main", "null", "fallback", "report"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=9)
    ap.add_argument("--cpu-limit", type=float, default=0.30)
    a = ap.parse_args(argv)
    out = Path(a.out)
    jobs = []
    if a.phase == "smoke":
        for row in ROWS:
            for st in STEPS:
                jobs.append(_job(cfg(row, st), SMOKE, cal.profile("bn4")[:6], out / "smoke" / f"{row}_st{st:g}_s{SMOKE}.json"))
        jobs.append(_job(null_cfg(), SMOKE, [(0.0, 900.0, 1800.0)], out / "smoke" / f"null_s{SMOKE}.json", "c1500"))
        run_jobs(jobs, out, a.workers, a.cpu_limit)
        bad = smoke_check(out)
        print("smoke:", "ok" if not bad else bad, flush=True)
        return 1 if bad else 0
    if a.phase == "pre":
        jobs = [_job(cfg(row, st), s, cal.profile("bn4"), out / "pre" / f"{row}_st{st:g}_s{s}.json")
                for row in ROWS for st in STEPS for s in PRE]
    elif a.phase == "main":
        q1 = q1_table(out)
        (out / "q1.json").write_text(json.dumps(q1, indent=1))
        miss = [k for k, v in q1.items() if v is None]
        if miss:
            raise SystemExit(f"no activation in the pre-pass: {miss}")
        jobs = [_job(cfg(row, st), s, slow_profile(q1[f"{row}_st{st:g}"]), out / "main" / f"{row}_st{st:g}_s{s}.json")
                for row in ROWS for st in STEPS for s in MAIN]
    elif a.phase == "null":
        rep = report(out)
        ok = [s["pq_median"] for k, s in rep["stats"].items() if s and s["c1"] and s["c3"] and s["pq_median"]]
        if not ok:
            ok = [s["pq_median"] for s in rep["stats"].values() if s and s["pq_median"]]
        base = float(np.median(ok))
        (out / "null_base.json").write_text(json.dumps({"median_pq": base, "rows_meeting_1_3": len(ok)}))
        for f in NULL_RATES:
            r0 = round(f * base)
            jobs += [_job(null_cfg(), s, slow_profile(r0), out / "null" / f"null_r{r0}_s{s}.json", f"c{r0}") for s in NULL]
    elif a.phase == "fallback":
        rep = report(out)
        rows = [r for r, v in rep["verdict"].items() if v["c1"] and v["c3"] and not v["c2"]]
        q1 = json.loads((out / "q1.json").read_text())
        jobs = [_job(cfg(r, 0.1), s, slow_profile(q1[f"{r}_st0.25"]), out / "fallback" / f"{r}_st0.1_s{s}.json")
                for r in rows for s in FALLBACK]
        print("fallback rows:", rows, flush=True)
    else:
        rep = report(out)
        (out / "stage0_report.json").write_text(json.dumps(rep, indent=1))
        print("route:", rep["route"], rep["step"], flush=True)
        return 0
    run_jobs(jobs, out, a.workers, a.cpu_limit)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
