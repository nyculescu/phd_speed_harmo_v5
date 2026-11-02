"""B bind check stages S, C0 and the ladder (V258, bind_B_core_v2.md §4, §7, §10): jobs, the batch runner and the
pre-registered rules. Stages from the C nulls on need the control arms and come with stage T.

Usage: python -m v5b.fleet.b_stage {smoke,c0,ladder} --out DIR [--workers N] [--cpu-limit F]
  smoke   the §10 checks for this batch (NC, NC 0.05 s, NCμ per share; the unset-vType run and both deadlock-detector
          controls at 50 %); exit 1 on any failure
  c0      C0 at 1.10 × B0 (and 1.25 × B0 when fewer than 9/10 NC runs break down); writes c0_report.json; exit 3 when
          B does not continue at 0.1 s, so the launch script stops for the author
  ladder  the NC ladder with its extensions, the loading, stuck and tool-artefact checks and L1/L2; ladder_report.json
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

from v5b.d1.config import PYTHON_BIN, REPO_ROOT, clean_sumo_env
from v5b.fleet import b_merge as bm, corridor, fleet as fl
from v5b.p1c.calibrate import _cpu_util

SEED_SMOKE = 7_431_110
SEEDS_C = list(range(7_431_111, 7_431_121))
LADDER = [round(0.60 + 0.05 * i, 2) for i in range(11)]
EXT_HIGH = [1.15, 1.20, 1.25, 1.30]
EXT_LOW = [0.40, 0.45, 0.50, 0.55]
C0_LEVEL, C0_HIGH = 1.10, 1.25
STEPS = (0.1, 0.05)
B = 100_000
RAMP32_NET = "ramp32_131a87b358"
LOAD_T0, LOAD_T1 = 2400.0, 4200.0


def job(stage: str, share: float, f: float, step: float, arm: str, seed: int, out: Path, **kw) -> dict:
    p = out / stage / f"s{share:g}" / f"q{f:g}" / f"st{step:g}" / f"{arm}{kw.pop('tag', '')}_s{seed}.json"
    return {"seed": seed, "share": share, "q": round(f * bm.B0, 1), "f": f, "step": step, "arm": arm, "out": str(p),
            **kw}


def run_jobs(jobs: list, workers: int, limit: float) -> None:
    jobs = [j for j in jobs if not Path(j["out"]).exists()]
    print(f"{len(jobs)} jobs to run, cpu {_cpu_util(3.0):.0f} %", flush=True)
    env = clean_sumo_env()

    def one(j):
        while _cpu_util(1.0) > 100 * limit:
            time.sleep(30)
        Path(j["out"]).parent.mkdir(parents=True, exist_ok=True)
        r = subprocess.run(["nice", "-n", "10", PYTHON_BIN, "-m", "v5b.fleet.b_merge", "--job", json.dumps(j)],
                           cwd=REPO_ROOT, env=env, capture_output=True, text=True)
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


def load(j: dict) -> dict:
    return json.loads(Path(j["out"]).read_text())


def arrays(j: dict) -> dict:
    with np.load(Path(j["out"]).with_suffix(".npz")) as z:
        return {k: z[k] for k in z.files}


def onset(r: dict) -> dict | None:
    """The first merge breakdown with its onset in the window."""
    return next((e for e in r["breakdowns_merge"] if bm.WARM <= e["t_break"] < bm.WINDOW_END), None)


def queued(r: dict) -> list:
    """30-s rows from onset + 5 min to recovery of every merge breakdown episode (the QDF span)."""
    rows = []
    for e in r["breakdowns_merge"]:
        rows += [x for x in r["series"] if e["t_break"] + 300.0 <= x[0] <= e["t_recover"]]
    return rows


def lattice_ok(counts: list) -> bool:
    if not counts:
        return False
    vals, n = np.unique(counts, return_counts=True)
    return len(vals) >= 4 and n.max() <= 0.5 * len(counts)


def run_lattice(r: dict, a: dict) -> dict:
    """C0.2 per run: evaluable with >= 10 queued intervals and no deadlock event."""
    q = queued(r)
    ev = len(q) >= 10 and not r["deadlock_events"]
    if not ev:
        return {"evaluable": False}
    m = np.sort(a["merge"][a["ramp"] & ~np.isnan(a["merge"])])
    spans = [(e["t_break"] + 300.0, e["t_recover"]) for e in r["breakdowns_merge"]]
    inq = np.array([any(lo <= x <= hi for lo, hi in spans) for x in m[1:]], bool) if m.size > 1 else np.array([])
    gaps = np.round(np.diff(m), 1)[inq] if m.size > 1 else np.array([])
    _, gn = np.unique(gaps, return_counts=True) if gaps.size else (None, np.array([0]))
    ok = (lattice_ok([x[10] for x in q]) and lattice_ok([x[6] for x in q])
          and gaps.size > 0 and gn.max() <= 0.2 * gaps.size)
    return {"evaluable": True, "pass": bool(ok), "qdf": 120.0 * float(np.mean([x[1] for x in q]))}


def qdf(r: dict) -> float | None:
    """C0.3: mean 30-s MA-end crossing flow over the QDF span; None without an onset or with a deadlock event."""
    q = queued(r)
    return 120.0 * float(np.mean([x[1] for x in q])) if q and onset(r) and not r["deadlock_events"] else None


def boot_median(x, rng) -> np.ndarray:
    x = np.asarray(x, float)
    return np.median(x[rng.integers(0, len(x), (B, len(x)))], axis=1)


def c0_tables(D: dict, Lat: dict, St: dict) -> dict:
    """§4 C0 outcome. D, Lat: {(share, step): bool}; St: {share: bool}."""
    state = {}
    for s in bm.SHARES:
        if not D[(s, 0.1)] and not D[(s, 0.05)]:
            state[s] = {"untestable": "deadlock"}
            continue
        state[s] = {"ok01": bool(D[(s, 0.1)] and Lat[(s, 0.1)] and St[s]),
                    "ok005": bool(D[(s, 0.05)] and Lat[(s, 0.05)])}
    left = [s for s in bm.SHARES if "untestable" not in state[s]]
    if not left:
        b = "none left: INCONCLUSIVE"
    elif all(state[s]["ok01"] for s in left):
        b = "0.1"
    elif all(state[s]["ok005"] for s in left):
        b = "0.05"
    else:
        b = "B-UNTESTABLE(m32, step)"
    return {"shares": {f"{s:g}": v for s, v in state.items()}, "b_step": b}


def stuck_episodes(r: dict) -> int:
    """§4: 10 consecutive 30-s intervals in [600, 4,200) s with >= 5 standing ramp vehicles at every interval end and
    merges <= 25 % of the ramp vehicles scheduled in the same 5 min; overlapping windows form one episode."""
    rows = [x for x in r["series"] if bm.WARM < x[0] <= bm.WINDOW_END]
    hit = []
    for i in range(len(rows) - 9):
        w = rows[i:i + 10]
        hit.append(all(x[7] >= 5 for x in w) and sum(x[6] for x in w) <= 0.25 * sum(x[8] for x in w))
    n, prev = 0, False
    for h in hit:
        n += h and not prev
        prev = h
    return n


def load_ratio(a: dict) -> float:
    s = a["sched"]
    dep = ((s >= LOAD_T0) & (s < LOAD_T1)).sum()
    cross = ((a["ma"] >= LOAD_T0) & (a["ma"] < LOAD_T1)).sum()
    return float(cross / dep) if dep else float("nan")


def queue_at_merge(r: dict) -> bool:
    for e in r["breakdowns_merge"]:
        if e["t_break"] < bm.WINDOW_END and e["t_recover"] > bm.WARM:
            if e["t_recover"] >= bm.WINDOW_END or (e["t_break"] >= bm.WARM and e["min"] >= 15.0):
                return True
    return False


def loading_check(top: list, low_min: float) -> dict:
    """§4 loading check at the highest level run: top = [(result, arrays)] at that level; low_min = the smallest
    per-run ratio at the lowest level run (the free-flow null)."""
    ok = [(r, a) for r, a in top if not r["deadlock_events"]]
    if len(ok) < 8:
        return {"pass": False, "n": len(ok), "why": "fewer than 8 deadlock-free runs"}
    ratios = [load_ratio(a) for _, a in ok]
    med = float(np.median(ratios))
    share_q = float(np.mean([queue_at_merge(r) for r, _ in ok]))
    return {"pass": bool(med <= 0.97 and med < low_min and share_q >= 0.8), "n": len(ok), "median_ratio": med,
            "low_min": low_min, "queue_at_merge": share_q}


def logistic_levels(q: list, y: list) -> dict:
    """L1, L2 = Q at P(onset) 0.1 and 0.3 from a logistic fit; linear interpolation of the empirical P if the fit
    fails (separation, non-monotone)."""
    x, y = np.asarray(q, float) / bm.B0, np.asarray(y, float)
    out = {"method": "logistic"}
    try:
        if y.min() == y.max():
            raise ValueError("no variation")
        b = np.zeros(2)
        for _ in range(100):
            p = 1 / (1 + np.exp(-(b[0] + b[1] * x)))
            g = np.array([np.sum(y - p), np.sum((y - p) * x)])
            w = p * (1 - p)
            h = np.array([[w.sum(), (w * x).sum()], [(w * x).sum(), (w * x * x).sum()]])
            step = np.linalg.solve(h, g)
            b += step
            if np.abs(step).max() < 1e-9:
                break
        if not np.isfinite(b).all() or b[1] <= 0 or abs(b[1]) > 500:
            raise ValueError("separation or non-monotone")
        lev = {k: (math.log(p / (1 - p)) - b[0]) / b[1] * bm.B0 for k, p in (("L1", 0.1), ("L2", 0.3))}
        out |= {"b": b.tolist(), **lev}
    except (ValueError, np.linalg.LinAlgError) as e:
        lv = sorted(set(q))
        pe = [float(np.mean([yy for qq, yy in zip(q, y) if qq == v])) for v in lv]
        out = {"method": f"interpolation ({e})"}
        for k, p in (("L1", 0.1), ("L2", 0.3)):
            out[k] = next((lv[i] + (p - pe[i]) / (pe[i + 1] - pe[i]) * (lv[i + 1] - lv[i])
                           for i in range(len(lv) - 1) if pe[i] <= p <= pe[i + 1] and pe[i + 1] > pe[i]), None)
    for k in ("L1", "L2"):
        if out.get(k) is not None:
            out[k] = round(out[k] / 10.0) * 10.0
    return out


def tool_artefact(level_runs: dict, lv: float) -> dict:
    """§4: the bracket [Q_lo, Q_hi) around a level holds 20 NC runs; > 2 with a deadlock event, undrained or a stuck
    episode -> tool-UNTESTABLE. level_runs: {f: [result]}."""
    fs = sorted(level_runs)
    lo = max((f for f in fs if f * bm.B0 <= lv), default=None)
    hi = min((f for f in fs if f * bm.B0 > lv), default=None)
    if lo is None or hi is None:
        return {"bracket": None, "pass": False}
    runs = level_runs[lo] + level_runs[hi]
    dl = sum(bool(r["deadlock_events"]) or r["status"] == "deadlocked" for r in runs)
    ud = sum(r["status"] == "undrained" for r in runs)
    st = sum(stuck_episodes(r) > 0 for r in runs)
    bad = sum(bool(r["deadlock_events"]) or r["status"] != "ok" or stuck_episodes(r) > 0 for r in runs)
    return {"bracket": [lo, hi], "n": len(runs), "deadlock": dl, "undrained": ud, "stuck": st, "artefact_runs": bad,
            "pass": bad <= 2}


def binom_ok(k: int, n: int, p: float, z: float = 3.29) -> bool:
    return abs(k - n * p) <= z * math.sqrt(n * p * (1 - p)) + 0.5


def smoke_jobs(out: Path) -> list:
    js, f, s0 = [], C0_LEVEL, SEED_SMOKE
    for s in bm.SHARES:
        js += [job("smoke", s, f, 0.1, "NC", s0, out, t_end=1200.0), job("smoke", s, f, 0.05, "NC", s0, out, t_end=1200.0),
               job("smoke", s, f, 0.1, "NCmu", s0, out, t_end=1200.0)]
    js += [job("smoke", 0.5, f, 0.1, "NC", s0, out, t_end=1200.0, explicit=False, tag="_unset"),
           job("smoke", 0.5, f, 0.1, "NC", s0, out, t_end=1200.0, tag="_hold1",
               hold={"lane": bm.ROAD0, "t": 700.0, "dur": 200.0, "tail": 10.0}),
           job("smoke", 0.5, f, 0.1, "NC", s0, out, t_end=1200.0, tag="_hold2",
               hold={"lane": bm.MERGE_LANE, "t": 700.0, "dur": 200.0, "tail": 25.0})]
    return js


def smoke_check(js: list) -> list:
    bad = []
    rs = {Path(j["out"]).name + str(j["share"]) + str(j["step"]): load(j) for j in js}
    nc = {}
    for j in js:
        r = rs[Path(j["out"]).name + str(j["share"]) + str(j["step"])]
        a = arrays(j)
        n = f"{Path(j['out']).parent.relative_to(Path(j['out']).parents[4])}/{Path(j['out']).name}"
        for k in ("arm", "share", "q", "step", "seed"):
            if r[k] != j[k]:
                bad.append(f"{n}: echo {k} {r[k]} != {j[k]}")
        if r["plant"] != "m32" or set(r["tls_rm"]) != {"G"}:
            bad.append(f"{n}: plant {r['plant']} tls {r['tls_rm']}")
        if not (r["inserted"] == r["generated"] == r["trips"] == r["ma_crossings"]):
            bad.append(f"{n}: counts generated {r['generated']} inserted {r['inserted']} trips {r['trips']} "
                       f"ma {r['ma_crossings']}")
        if not (r["merges"] == r["ramp_trips"] == r["ramp_generated"]):
            bad.append(f"{n}: merges {r['merges']} ramp trips {r['ramp_trips']} of {r['ramp_generated']}")
        mt = a["merge"][a["ramp"]]
        if np.isnan(mt).any() or np.all(np.abs(mt - np.round(mt)) < 1e-6):
            bad.append(f"{n}: merge times missing or on whole seconds")
        g = r["generated"]
        for k, p in (("alks_generated", j["share"]), ("truck_generated", fl.B_TRUCK_SHARE),
                     ("ramp_generated", corridor.RAMP_SHARE)):
            if not binom_ok(r[k], g, p):
                bad.append(f"{n}: {k} {r[k]} of {g} outside the 99.9 % interval of {p}")
        if not r["drained"] or r["status"] != "ok" or r["contacts"] or r["teleports"]:
            bad.append(f"{n}: drained {r['drained']} status {r['status']} contacts {r['contacts']}")
        if r["alks_readback_dev"] > 1e-6:
            bad.append(f"{n}: ALKS read-back deviates by {r['alks_readback_dev']}")
        log = r["nc_mu"]["log"]
        if j["arm"] == "NCmu" and (len(log) != 1 or not log[0]["binding"] or not r["nc_mu"].get("restore_ok")):
            bad.append(f"{n}: NCmu log {log}")
        if j["arm"] == "NC" and log:
            bad.append(f"{n}: NC has commands")
        if j.get("hold"):
            want = 1 if j["hold"]["lane"] == bm.ROAD0 else 0
            if r["held"]["vid"] is None or len(r["deadlock_events"]) != want:
                bad.append(f"{n}: hold on {j['hold']['lane']} held {r['held']} events {r['deadlock_events']}")
        elif r["deadlock_events"]:
            bad.append(f"{n}: unexpected deadlock events {r['deadlock_events']}")
        if j["arm"] == "NC" and not j.get("hold") and j.get("explicit", True):
            nc[(j["share"], j["step"])] = r["trip_hash"]
    for j in js:
        r = rs[Path(j["out"]).name + str(j["share"]) + str(j["step"])]
        if j["arm"] == "NCmu" and r["trip_hash"] == nc.get((j["share"], j["step"])):
            bad.append(f"NCmu s{j['share']:g}: trip hash equals NC")
        if j.get("explicit") is False and r["trip_hash"] != nc.get((j["share"], j["step"])):
            bad.append("unset vType: trip hash differs from the explicit build")
    d = fl.build_net(bm.setup(0.5, 0.1))
    root = ET.parse(d / "net.xml").getroot()
    lanes = {x.get("id") for x in root.iter("lane") if not x.get("id").startswith(":")}
    cons = {(c.get("from"), c.get("fromLane"), c.get("to")) for c in root.iter("connection")
            if not c.get("from").startswith(":")}
    if not {f"{e}_{i}" for e in "45" for i in range(3)} <= lanes:
        bad.append("m32: edges 4 and 5 lack 3 lanes")
    if any(("3", str(i), "4") not in cons or ("4", str(i), "5") not in cons for i in range(3)):
        bad.append("m32: 3->4 or 4->5 not on all 3 lanes")
    succ = {(c[0], c[1]) for c in cons}
    if [ln for ln in sorted(lanes) if ln.rsplit("_", 1)[0] != "5" and tuple(ln.rsplit("_", 1)) not in succ] != ["3a_0"]:
        bad.append("m32: 3a_0 is not the only lane without a successor")
    n_add = sum(1 for _ in ET.parse(d / "add.xml").getroot().iter("inductionLoop"))
    if n_add != sum(len(v) for v in corridor.loop_ids("m32").values()):
        bad.append("m32: add.xml loop count")
    if corridor.build(fl.LIMIT).name != RAMP32_NET or sum(len(v) for v in corridor.loop_ids().values()) != 21:
        bad.append("ramp32 net or loops changed")
    return bad


def c0_jobs(out: Path, f: float) -> list:
    return [job("c", s, f, st, arm, seed, out) for s in bm.SHARES for seed in SEEDS_C
            for st, arm in ((0.1, "NC"), (0.05, "NC"), (0.1, "NCmu"))]


def c0_report(out: Path) -> dict:
    D, Lat, St, rows, levels = {}, {}, {}, {}, {}
    rng = np.random.default_rng(20261102)
    for s in bm.SHARES:
        # a C0 level was run for a share when its NC 0.05-s runs exist (the ladder also writes NC 0.1 s at 1.25)
        lv = [f for f in (C0_LEVEL, C0_HIGH) if Path(job("c", s, f, 0.05, "NC", SEEDS_C[0], out)["out"]).exists()]
        levels[f"{s:g}"] = lv
        pairs, mu_r = [], []
        for st in STEPS:
            ok_d, lat, qdfs_by = True, [], {}
            for f in lv:
                js = [job("c", s, f, st, "NC", seed, out) for seed in SEEDS_C]
                rs = [load(j) for j in js]
                ok_d &= sum(bool(r["deadlock_events"]) for r in rs) <= 1
                for j, r in zip(js, rs):
                    lt = run_lattice(r, arrays(j))
                    lat.append(lt)
                    if lt["evaluable"]:
                        qdfs_by.setdefault(f, []).append(lt["qdf"])
            ev = [x for x in lat if x["evaluable"]]
            cv_ok = all(len(v) < 2 or np.std(v, ddof=1) / np.mean(v) >= 0.005 for v in qdfs_by.values())
            D[(s, st)] = ok_d
            Lat[(s, st)] = bool(len(ev) >= 8 and np.mean([x["pass"] for x in ev]) >= 0.8 and cv_ok)
            rows[f"s{s:g}_st{st:g}"] = {"deadlock_ok": ok_d, "evaluable": len(ev),
                                        "lattice_pass": sum(x["pass"] for x in ev), "qdf_cv_ok": cv_ok,
                                        "qdf": {f"{k:g}": [round(x) for x in v] for k, v in qdfs_by.items()}}
        for f in lv:
            for seed in SEEDS_C:
                a, b, m = (job("c", s, f, 0.1, "NC", seed, out), job("c", s, f, 0.05, "NC", seed, out),
                           job("c", s, f, 0.1, "NCmu", seed, out))
                qa, qb, qm = qdf(load(a)), qdf(load(b)), qdf(load(m))
                if qa and qb:
                    pairs.append(qb / qa)
                if qa and qm:
                    mu_r.append(qm / qa - 1.0)
        thr = max(0.02, float(np.percentile(np.abs(boot_median(mu_r, rng)), 95))) if len(mu_r) >= 2 else None
        med = float(np.median(pairs)) if pairs else None
        St[s] = bool(len(pairs) >= 8 and thr is not None and abs(med - 1.0) <= thr)
        rows[f"s{s:g}_step"] = {"pairs": len(pairs), "median_ratio": med, "threshold": thr, "pass": St[s]}
    return {"levels": levels, "rows": rows, **c0_tables(D, Lat, St)}


def ladder(out: Path, workers: int, limit: float) -> dict:
    """Runs the NC ladder per share with its extensions and returns the ladder report (§4)."""
    rep = {}
    for s in bm.SHARES:
        rep[f"{s:g}"] = {}
    levels = {s: list(LADDER) for s in bm.SHARES}
    run_jobs([job("c", s, f, 0.1, "NC", seed, out) for s in bm.SHARES for f in levels[s] for seed in SEEDS_C],
             workers, limit)

    def res(s, f):
        js = [job("c", s, f, 0.1, "NC", seed, out) for seed in SEEDS_C]
        return [(load(j), arrays(j)) for j in js]

    def p_on(s, f):
        return float(np.mean([onset(r) is not None for r, _ in res(s, f)]))
    ext = []
    for s in bm.SHARES:
        if p_on(s, 1.10) < 0.3:
            ext += [(s, f) for f in EXT_HIGH]
        if p_on(s, 0.60) >= 0.1:
            ext += [(s, f) for f in EXT_LOW]
    run_jobs([job("c", s, f, 0.1, "NC", seed, out) for s, f in ext for seed in SEEDS_C], workers, limit)
    for s, f in ext:
        levels[s].append(f)
    for s in bm.SHARES:
        lv = sorted(levels[s])
        low_min = min(load_ratio(a) for _, a in res(s, lv[0]))
        load_c = loading_check(res(s, lv[-1]), low_min)
        if not load_c["pass"] and lv[-1] <= 1.10:
            run_jobs([job("c", s, f, 0.1, "NC", seed, out) for f in EXT_HIGH for seed in SEEDS_C], workers, limit)
            lv = sorted(set(lv) | set(EXT_HIGH))
            load_c = loading_check(res(s, lv[-1]), low_min)
        levels[s] = lv
        qs = [f * bm.B0 for f in lv for _ in SEEDS_C]
        ys = [onset(r) is not None for f in lv for r, _ in res(s, f)]
        fit = logistic_levels(qs, ys)
        st = {"levels": lv, "p_onset": {f"{f:g}": p_on(s, f) for f in lv}, "fit": fit, "loading": load_c}
        st["p_sustained"] = {f"{f:g}": float(np.mean([bool(onset(r)) and onset(r)["min"] >= 15.0
                                                      for r, _ in res(s, f)])) for f in lv}
        st["p_onset_lane0"] = {f"{f:g}": float(np.mean([any(bm.WARM <= e["t_break"] < bm.WINDOW_END
                                                            for e in r["breakdowns_lane0"]) for r, _ in res(s, f)]))
                               for f in lv}
        st["report"] = {f"{f:g}": {"deadlock_runs": sum(bool(r["deadlock_events"]) for r, _ in res(s, f)),
                                   "undrained": sum(r["status"] == "undrained" for r, _ in res(s, f)),
                                   "stuck_runs": sum(stuck_episodes(r) > 0 for r, _ in res(s, f)),
                                   "empty_occ_intervals": sum(sum(1 for x in r["series"] if x[11]) for r, _ in res(s, f)),
                                   "loop_minus_id_ma": sum(sum(x[12] - x[1] for x in r["series"]) for r, _ in res(s, f)),
                                   "max_pending_med": float(np.median([r["max_pending"] for r, _ in res(s, f)]))}
                        for f in lv}
        if max(st["p_onset"].values()) < 0.3 or fit.get("L2") is None:
            st["state"] = 'plant-UNTESTABLE "not critical"'
        elif not load_c["pass"]:
            st["state"] = 'plant-UNTESTABLE "merge not loaded"'
        else:
            lr = {f: [r for r, _ in res(s, f)] for f in lv}
            t1, t2 = tool_artefact(lr, fit["L1"]) if fit.get("L1") else {"pass": False}, tool_artefact(lr, fit["L2"])
            st["tool"] = {"L1": t1, "L2": t2}
            st["state"] = "ok" if t1["pass"] and t2["pass"] else "tool-UNTESTABLE"
        rep[f"{s:g}"] = st
    return rep


def main(argv: list) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("phase", choices=("smoke", "c0", "ladder"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=9)
    ap.add_argument("--cpu-limit", type=float, default=0.30)
    a = ap.parse_args(argv)
    out = Path(a.out)
    if a.phase == "smoke":
        js = smoke_jobs(out)
        run_jobs(js, a.workers, a.cpu_limit)
        bad = smoke_check(js)
        walls = [load(j)["wall_s"] / load(j)["sim_s"] for j in js]
        print(f"wall-s per sim-s: median {np.median(walls):.4f}, max {max(walls):.4f}", flush=True)
        print("smoke:", "ok" if not bad else bad, flush=True)
        return 1 if bad else 0
    if a.phase == "c0":
        run_jobs(c0_jobs(out, C0_LEVEL), a.workers, a.cpu_limit)
        hi = [s for s in bm.SHARES if np.mean([onset(load(job("c", s, C0_LEVEL, 0.1, "NC", seed, out))) is not None
                                               for seed in SEEDS_C]) < 0.9]
        if hi:
            run_jobs([j for j in c0_jobs(out, C0_HIGH) if j["share"] in hi], a.workers, a.cpu_limit)
        rep = c0_report(out)
        (out / "c0_report.json").write_text(json.dumps(rep, indent=1))
        print("C0:", rep["b_step"], {k: v for k, v in rep["shares"].items()}, flush=True)
        return 0 if rep["b_step"] == "0.1" else 3
    rep = ladder(out, a.workers, a.cpu_limit)
    (out / "ladder_report.json").write_text(json.dumps(rep, indent=1))
    print("ladder:", {k: v["state"] for k, v in rep.items()}, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
