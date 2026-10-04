"""gate_ctx_r6 S1: BN4 driver-variant realism gate with 10-s E1 loops (docs/lab/gate_ctx_r6/s1_protocol.md §4).

python -m vsl_lab.jobs.s1_bn4 one --variant B2 --q 2000 --seed 7180000 --tag smoke --out-root <dir>   # one NC run
python -m vsl_lab.jobs.s1_bn4 smoke --gate-ok        # §4.1: one run per variant at q = 2000, seed 7,180,000
python -m vsl_lab.jobs.s1_bn4 realism --gate-ok      # §4.2-4.3: calibration -> cell selection -> checks -> verdict
python -m vsl_lab.jobs.s1_bn4 analyse --root <dir>   # re-analyse
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

from vsl_lab.config import N_MAX_DEFAULT, REPO_ROOT, RUNS_ROOT

V_CONG = 41.4 / 3.6          # §4.3: t2's 60 / 70 km/h scaled by 82.8 / 120
V_REC = 48.3 / 3.6
V_STOP = 10.0 / 3.6
DT = 10.0
WARMUP, HORIZON = 40.0, 2440.0
ONSET_WIN = (300.0, 2400.0)
GROUPS = ("L1", "L2m", "L2e", "L3e", "L4a", "L4m", "L4e", "L5a", "L5m", "Lx")   # upstream -> downstream
PAIRS = (("L4e", "L4a"), ("L3e", "L2m"), ("L2m", "L1"))
PREFERENCE = ("B0", "B2", "B3")
Q_GRID = list(range(1000, 3001, 200))
CAL_SEEDS = list(range(7180010, 7180020))
CHK_SEEDS = list(range(7180020, 7180040))
SMOKE_SEED = 7180000
STRESS_Q = 3000
OUT = REPO_ROOT / "docs" / "lab" / "gate_ctx_r6"


# ------------------------------------------------------------------------------------------------ one run
def run_one(variant: str, q: float, seed: int, tag: str, out_root: Path) -> dict:
    import libsumo as ls
    from vsl_lab.plants import bn4
    from vsl_lab.sim.runner import SumoSim
    t0 = time.time()
    f = bn4.files()
    loops_add = bn4.net.loops_file(f["dir"])
    dem = bn4.demand_variant(seed, [(0.0, HORIZON, q)], variant)
    run_dir = out_root / tag / f"{variant}_q{int(q)}_s{seed}_pid{os.getpid()}"
    run_dir.mkdir(parents=True, exist_ok=True)
    rou = run_dir / f"routes_{variant}_q{int(q)}_s{seed}_pid{os.getpid()}.rou.xml"
    dem.write(rou)
    sim = SumoSim(f["net"], rou, run_dir, dem, additional=[f["add"], loops_add], step_length=bn4.STEP_LENGTH,
                  checkpoint_s=300.0, seed=seed)
    sim.start()
    bn4.set_all_green()
    sim.asserts.append(bn4.assert_all_green)
    lb = bn4.LoopBank()
    classes: dict = {}
    while sim.t < HORIZON - 1e-9:
        sim.step()
        for vid in ls.simulation.getDepartedIDList():
            c = bn4.type_class(ls.vehicle.getTypeID(vid))
            classes[c] = classes.get(c, 0) + 1
        lb.poll(sim.t, sim.arrived)
    res = sim.close(drained=None)
    lb.write_csv(run_dir / "loops10.csv")
    out = {"job": "s1_bn4_realism", "variant": variant, "q": q, "seed": seed, "teleports": res["teleports"],
           "hash": res["hash"], "health": res["health"], "classes": classes, "generated": len(dem.vehicles),
           "wall_s": round(time.time() - t0, 2)}
    (run_dir / "summary.json").write_text(json.dumps(out, indent=1, default=str))
    return out


# ------------------------------------------------------------------------------------------------ signatures
def load_loops(run_dir: Path) -> dict:
    """group -> (t, section speed, exit-style flow veh/h/lane, mean occupancy) at 10 s."""
    import csv
    with open(run_dir / "loops10.csv") as fh:
        rows = list(csv.DictReader(fh))
    t = np.array([float(r["t"]) for r in rows])
    from vsl_lab.netgen import bn4 as net
    out = {"t": t}
    for g, lids in net.loop_ids().items():
        n = np.array([[float(r[f"{lid}_n"]) for lid, _ in lids] for r in rows])
        o = np.array([[float(r[f"{lid}_occ"]) for lid, _ in lids] for r in rows])
        v = np.array([[float(r[f"{lid}_v"]) for lid, _ in lids] for r in rows])
        cnt = n.sum(1)
        vw = np.where((n > 0) & (v >= 0), n * v, 0.0).sum(1)
        mo = o.mean(1)
        sp = np.where(cnt > 0, vw / np.maximum(cnt, 1), np.where(mo >= 0.5, 0.0, np.nan))
        out[g] = {"v": sp, "q_vphpl": cnt * 3600.0 / DT / len(lids), "occ": mo}
    out["arrived"] = np.array([float(r["arrived"]) if r["arrived"] else np.nan for r in rows])
    return out


def _fwd(x, n):
    out = np.full(len(x), np.nan)
    for i in range(len(x)):
        w = x[i:i + n]
        if len(w) == n and np.isfinite(w).any():
            out[i] = np.nanmean(w)
    return out


def _cen(x, n):
    h = n // 2
    out = np.full(len(x), np.nan)
    for i in range(len(x)):
        w = x[max(0, i - h):i + h + 1]
        if np.isfinite(w).any():
            out[i] = np.nanmean(w)
    return out


def _longest(mask):
    best, start = None, None
    for i, m in enumerate(list(mask) + [False]):
        if m and start is None:
            start = i
        elif not m and start is not None:
            if best is None or i - start > best[1] - best[0]:
                best = (start, i)
            start = None
    return best


def _mean_in(t, x, a, b):
    v = x[(t > a) & (t <= b)]
    return float(np.mean(v)) if len(v) else None


def signatures(run_dir: Path, xs: dict) -> dict:
    L = load_loops(run_dir)
    t = L["t"]
    v4 = L["L4m"]["v"]
    f2, f5 = _fwd(v4, 12), _fwd(v4, 30)
    tb = next((i for i in range(len(t)) if ONSET_WIN[0] <= t[i] <= ONSET_WIN[1] and f2[i] < V_CONG and f5[i] < V_CONG),
              None)
    t_b = float(t[tb]) if tb is not None else None
    t_rec = None
    if tb is not None:
        j = next((j for j in range(tb + 1, len(t)) if f5[j] > V_REC), None)
        t_rec = float(t[j]) if j is not None else None
    qx = L["Lx"]["q_vphpl"]
    cap = None
    if t_b is not None:
        d0, d1 = t_b + 300.0, min(t_b + 1200.0, t_rec if t_rec is not None else np.inf, HORIZON)
        cap = {"discharge_vphpl": _mean_in(t, qx, d0, d1) if d1 - d0 >= 300.0 else None, "window_s": max(0.0, d1 - d0)}
    ff = _mean_in(t, qx, *ONSET_WIN)
    # origin: first group whose forward 2-min mean speed < V_CONG (ties -> most downstream)
    first = {}
    for g in GROUPS:
        idx = np.nonzero(_fwd(L[g]["v"], 12) < V_CONG)[0]
        if len(idx):
            first[g] = float(t[idx[0]])
    origin = [g for g in reversed(GROUPS) if first.get(g) == min(first.values())][0] if first else None
    # wave speed (t2 estimator, section speeds)
    wave = None
    for d, u in PAIRS:
        a, b = L[d]["v"], L[u]["v"]
        ca, cb = _cen(a, 31), _cen(b, 31)
        seg = _longest((ca < V_CONG) & (cb < V_CONG))
        if seg is None or seg[1] - seg[0] < 90:
            continue
        i0, i1 = seg
        ha, hb = np.nan_to_num((a - ca)[i0:i1]), np.nan_to_num((b - cb)[i0:i1])
        k_max = min(60, (i1 - i0) - 60)
        rs = []
        for k in range(0, k_max + 1):
            x, y = ha[:len(ha) - k], hb[k:]
            rs.append(float(np.corrcoef(x, y)[0, 1]) if x.std() > 1e-9 and y.std() > 1e-9 else np.nan)
        if not np.isfinite(rs).any():
            wave = {"pair": f"{d}->{u}", "valid": False, "reason": "flat"}
            break
        k = int(np.nanargmax(rs))
        dx = xs[d] - xs[u]
        valid = rs[k] >= 0.3 and 1 <= k <= k_max - 1
        wave = {"pair": f"{d}->{u}", "seg_s": (i1 - i0) * DT, "lag_s": k * DT, "r": round(rs[k], 3), "dx_m": round(dx, 1),
                "valid": bool(valid), "c_kmh": round(-dx / (k * DT) * 3.6, 2) if valid else None}
        break
    n_cong = n_stop = 0
    for g in GROUPS:
        c = _cen(L[g]["v"], 31)
        m = (c < V_CONG) & np.isfinite(L[g]["v"])
        n_cong += int(m.sum())
        n_stop += int((m & (L[g]["v"] < V_STOP)).sum())
    return {"t_b": t_b, "t_rec": t_rec, "cap": cap, "ff_vphpl": ff, "origin": origin, "wave": wave,
            "n_cong": n_cong, "n_stop": n_stop}


# ------------------------------------------------------------------------------------------------ batch + analysis
def _job(tag, variant, q, seed, root):
    from vsl_lab.ops.scheduler import Job
    return Job(jid=f"{tag}_{variant}_q{q}_s{seed}",
               argv=["vsl_lab.jobs.s1_bn4", "one", "--variant", variant, "--q", str(q), "--seed", str(seed),
                     "--tag", f"{tag}_{variant}", "--out-root", str(root)])


def load(root: Path, tag: str, variant: str) -> list:
    out = []
    for p in (root / f"{tag}_{variant}").glob("*/summary.json"):
        o = json.loads(p.read_text())
        o["_dir"] = str(p.parent)
        out.append(o)
    return out


def select_cell(rows: list) -> dict:
    cells = {}
    for o in rows:
        c = cells.setdefault(int(o["q"]), {"n": 0, "bd": 0, "tele": 0, "fail": 0})
        c["n"] += 1
        c["bd"] += signatures(Path(o["_dir"]), XS)["t_b"] is not None
        c["tele"] += o["teleports"]
        c["fail"] += o["health"]["status"] == "FAIL"
    table = {k: {"n": c["n"], "onset_share": c["bd"] / max(c["n"], 1), "teleports": c["tele"], "fail": c["fail"]}
             for k, c in sorted(cells.items())}
    ok = {k: v for k, v in table.items() if v["teleports"] == 0 and v["fail"] == 0}
    sel = min(ok, key=lambda k: (abs(ok[k]["onset_share"] - 0.5), k)) if ok else None
    return {"table": table, "selected": sel, "max_share": max((v["onset_share"] for v in table.values()), default=0.0)}


def inert(rows: list, base: list) -> dict:
    h0 = {(int(o["q"]), o["seed"]): o["hash"] for o in base}
    pairs = [(o["hash"], h0[(int(o["q"]), o["seed"])]) for o in rows if (int(o["q"]), o["seed"]) in h0]
    same = sum(a == b for a, b in pairs)
    return {"pairs": len(pairs), "identical": same, "INERT": bool(pairs) and same == len(pairs)}


def _boot_ratio(dis, ff, n=2000, seed=7180099):
    rng = np.random.default_rng(seed)
    r = [np.median(rng.choice(dis, len(dis))) / np.median(rng.choice(ff, len(ff))) for _ in range(n)]
    return float(np.percentile(r, 2.5)), float(np.percentile(r, 97.5))


def analyse_variant(sel: int, chk: list, det: list) -> dict:
    sig = {(int(o["q"]), o["seed"]): (o, signatures(Path(o["_dir"]), XS)) for o in chk}
    at_sel = [v for k, v in sig.items() if k[0] == sel]
    med = lambda x: float(np.median(x)) if x else None
    bd = [(o, s) for o, s in at_sel if s["t_b"] is not None]
    nbd = [(o, s) for o, s in at_sel if s["t_b"] is None]
    dis = [s["cap"]["discharge_vphpl"] for _, s in bd if s["cap"]["discharge_vphpl"] is not None]
    ff = [s["ff_vphpl"] for _, s in nbd if s["ff_vphpl"] is not None]
    share = len(bd) / max(len(at_sel), 1)
    ok_n = len(dis) >= 3 and len(ff) >= 3
    ratio = float(np.median(dis) / np.median(ff)) if ok_n else None
    ra = {"n": len(at_sel), "onset_share": share, "n_discharge": len(dis), "n_free": len(ff), "Q_dis_vphpl": med(dis),
          "Q_ff_vphpl": med(ff), "ratio": ratio, "ratio_ci95": _boot_ratio(dis, ff) if ok_n else None}
    ra["PASS"] = bool(share >= 0.3 and ok_n and 0.82 <= ratio <= 0.97)
    waves = [s["wave"] for _, s in sig.values() if s["wave"]]
    cs = [w["c_kmh"] for w in waves if w["valid"]]
    rb = {"n_runs": len(sig), "n_windows": len(waves), "n_valid": len(cs), "median_c_kmh": med(cs),
          "pairs_used": {p: sum(w["pair"] == p for w in waves) for p in sorted({w["pair"] for w in waves})}}
    rb["status"] = "n/a" if len(cs) < 5 else ("PASS" if -25.0 <= rb["median_c_kmh"] <= -10.0 else "FAIL")
    op = [o for o, _ in at_sel] + det
    stress = [o for (q, _), (o, _) in sig.items() if q != sel]
    ref = next((o for o, _ in at_sel if o["seed"] == CHK_SEEDS[0]), None)
    det_ok = bool(det) and ref is not None and all(d["hash"] == ref["hash"] for d in det)
    rc = {"teleports_operating": sum(o["teleports"] for o in op),
          "fail_operating": sum(o["health"]["status"] == "FAIL" for o in op),
          "teleports_stress": sum(o["teleports"] for o in stress),
          "fail_stress": sum(o["health"]["status"] == "FAIL" for o in stress),
          "median_discharge_vphpl": med(dis), "determinism": det_ok}
    q_ok = bool(dis) and 1600.0 <= float(np.median(dis)) <= 2400.0
    rc["PASS"] = bool(rc["teleports_operating"] == 0 and rc["fail_operating"] == 0 and q_ok and det_ok)
    rc["PASS_original_rule"] = bool(rc["PASS"] and rc["teleports_stress"] == 0 and rc["fail_stress"] == 0)
    orig = [s["origin"] for _, s in sig.values() if s["origin"] is not None]
    from vsl_lab.netgen.bn4 import BOTTLENECK_GROUPS
    rd = {"n_congested_runs": len(orig),
          "share_bottleneck_origin": sum(x in BOTTLENECK_GROUPS for x in orig) / len(orig) if orig else None,
          "origins": {g: orig.count(g) for g in GROUPS if g in orig}}
    rd["PASS"] = bool(orig and rd["share_bottleneck_origin"] >= 0.8)
    n_cong = sum(s["n_cong"] for _, s in sig.values())
    n_stop = sum(s["n_stop"] for _, s in sig.values())
    classes = {}
    for o in chk:
        for c, n in o.get("classes", {}).items():
            classes[c] = classes.get(c, 0) + n
    rep = {"stopped_share_in_congestion": n_stop / n_cong if n_cong else None, "spawned_by_class": classes,
           "median_wall_s": med([o["wall_s"] for o in chk]),
           "Q_ff_all_runs_vphpl": med([s["ff_vphpl"] for _, s in at_sel if s["ff_vphpl"] is not None])}
    ok = ra["PASS"] and rd["PASS"] and rb["status"] != "FAIL"
    return {"R-a": ra, "R-b": rb, "R-c": rc, "R-d": rd, "reported": rep,
            "verdict": "PASS" if ok and rc["PASS"] else "FAIL",
            "verdict_original_rc_rule": "PASS" if ok and rc["PASS_original_rule"] else "FAIL",
            "flag_wave_na": rb["status"] == "n/a"}


XS: dict = {}


def analyse(root: Path, variants=PREFERENCE) -> dict:
    global XS
    from vsl_lab.netgen import bn4 as net
    XS = net.loop_x()
    cal = {v: load(root, "cal", v) for v in variants}
    res = {"protocol": "docs/lab/gate_ctx_r6/s1_protocol.md", "raw": str(root), "loop_x": XS, "variants": {}}
    for v in variants:
        sc = select_cell(cal[v])
        r = {"calibration": sc, "cell": sc["selected"], "n_cal_runs": len(cal[v])}
        base = {"B2": "B0", "B3": "B2"}.get(v)
        if base in cal:
            r["R-0"] = inert(cal[v], cal[base])
        if r.get("R-0", {}).get("INERT"):
            r["verdict"] = "INERT"
        elif sc["selected"] is None:
            r.update(verdict="FAIL", note="R-c: no cell with 0 teleports and 0 FAIL")
        elif sc["max_share"] < 0.2:
            r.update(verdict="FAIL", note="R-a: max onset share < 0.2 over the grid")
        else:
            r.update(analyse_variant(sc["selected"], load(root, "chk", v), load(root, "det", v)))
        res["variants"][v] = r
    res["verdict"] = {v: res["variants"][v]["verdict"] for v in variants}
    res["primary"] = next((v for v in PREFERENCE if res["verdict"].get(v) == "PASS"), None)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "s1_realism.json").write_text(json.dumps(res, indent=1, default=str))
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["one", "smoke", "realism", "analyse"])
    ap.add_argument("--variant", default="B0")
    ap.add_argument("--q", type=float, default=2000.0)
    ap.add_argument("--seed", type=int, default=SMOKE_SEED)
    ap.add_argument("--tag", default="one")
    ap.add_argument("--out-root", default=str(RUNS_ROOT / "t1" / "gate_ctx_r6"))
    ap.add_argument("--root", default=None)
    ap.add_argument("--workers", type=int, default=N_MAX_DEFAULT)
    ap.add_argument("--gate-ok", action="store_true")
    a = ap.parse_args(argv)
    if a.what == "one":
        try:
            o = run_one(a.variant, a.q, a.seed, a.tag, Path(a.out_root))
            print(json.dumps({k: o[k] for k in ("variant", "q", "seed", "teleports", "hash", "wall_s")}
                             | {"health": o["health"]["status"]}))
            return 0
        except Exception as exc:
            import traceback
            print(json.dumps({"error": f"{type(exc).__name__}: {exc}", "traceback": traceback.format_exc()[-1500:]}))
            return 2
    from vsl_lab.ops import ledger
    from vsl_lab.ops.scheduler import run_batch
    if a.what == "smoke":
        root = RUNS_ROOT / "t1" / "gate_ctx_r6" / f"s1_smoke_{int(time.time())}"
        run_batch([_job("smoke", v, 2000, SMOKE_SEED, root) for v in PREFERENCE], root / "batch", max_workers=3,
                  gate_ok=a.gate_ok)
        global XS
        from vsl_lab.netgen import bn4 as net
        XS = net.loop_x()
        out = {}
        for v in PREFERENCE:
            rows = load(root, "smoke", v)
            if not rows:
                out[v] = "NO OUTPUT"
                continue
            o = rows[0]
            s = signatures(Path(o["_dir"]), XS)
            out[v] = {"health": o["health"]["status"], "codes": list(o["health"]["by_code"]), "tele": o["teleports"],
                      "hash": o["hash"][:10], "wall": o["wall_s"], "classes": o["classes"], "t_b": s["t_b"],
                      "origin": s["origin"], "wave": s["wave"], "cap": s["cap"], "ff": s["ff_vphpl"]}
        (root / "smoke_summary.json").write_text(json.dumps(out, indent=1, default=str))
        ledger.append("T1", "S1-smoke", "S", "s1_bn4_smoke", {"variants": PREFERENCE, "q": 2000},
                      f"{SMOKE_SEED} (throw-away)", len(PREFERENCE), {}, {v: (o if isinstance(o, str) else
                      {"health": o["health"], "tele": o["tele"]}) for v, o in out.items()}, notes=str(root))
        print(str(root / "smoke_summary.json"))
        return 0
    if a.what == "analyse":
        res = analyse(Path(a.root))
        print(json.dumps({"verdict": res["verdict"], "primary": res["primary"]}))
        return 0
    root = RUNS_ROOT / "t1" / "gate_ctx_r6" / f"s1_realism_{int(time.time())}"
    jobs = [_job("cal", v, q, s, root) for v in PREFERENCE for q in Q_GRID for s in CAL_SEEDS]
    rep_cal = run_batch(jobs, root / "batch_cal", max_workers=a.workers, gate_ok=a.gate_ok)
    XS.update(__import__("vsl_lab.netgen.bn4", fromlist=["x"]).loop_x())
    cjobs = []
    for v in PREFERENCE:
        rows = load(root, "cal", v)
        base = {"B2": "B0", "B3": "B2"}.get(v)
        if base and inert(rows, load(root, "cal", base))["INERT"]:
            continue
        sc = select_cell(rows)
        if sc["selected"] is None or sc["max_share"] < 0.2:
            continue
        for q in sorted({sc["selected"], STRESS_Q}):
            cjobs += [_job("chk", v, q, s, root) for s in CHK_SEEDS]
        cjobs.append(_job("det", v, sc["selected"], CHK_SEEDS[0], root))
    rep_chk = run_batch(cjobs, root / "batch_chk", max_workers=a.workers, gate_ok=True) if cjobs else None
    res = analyse(root)
    n = len(jobs) + len(cjobs)
    ledger.append("T1", "S1-realism", "S", "s1_bn4_realism_gate", {"variants": PREFERENCE, "q_grid": Q_GRID},
                  f"{CAL_SEEDS[0]}-{CAL_SEEDS[-1]} (cal), {CHK_SEEDS[0]}-{CHK_SEEDS[-1]} (checks)", n,
                  {"proc_failed": rep_cal.n_failed_proc + (rep_chk.n_failed_proc if rep_chk else 0)},
                  {"verdict": res["verdict"], "primary": res["primary"],
                   "wall_s": round(rep_cal.wall_s + (rep_chk.wall_s if rep_chk else 0.0), 1)}, notes=str(root))
    print(json.dumps({"verdict": res["verdict"], "primary": res["primary"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
