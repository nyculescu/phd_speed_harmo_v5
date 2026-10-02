"""Plant-realism gate on MRG3-v3 driver variants H0-H4 (docs/lab/t2_realism_protocol.md).

python -m vsl_lab.jobs.t2_realism smoke --gate-ok             # tool check: 1 NC run per variant, throw-away seed 7,120,050
python -m vsl_lab.jobs.t2_realism run --gate-ok               # calibration -> cell selection -> checks -> verdict
python -m vsl_lab.jobs.t2_realism analyse --root <batch root> # re-analyse an existing batch
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from vsl_lab.config import N_MAX_DEFAULT, REPO_ROOT, RUNS_ROOT
from vsl_lab.eval import realism as R
from vsl_lab.jobs.mrg3_run import PROBES
from vsl_lab.ops import ledger
from vsl_lab.ops.scheduler import Job, run_batch
from vsl_lab.plants import mrg3 as P

VARIANTS = ["H0", "H1", "H2", "H3", "H4"]
PREFERENCE = ["H4", "H2", "H1", "H3", "H0"]
MAIN = [4200, 4500, 4800, 5100, 5400, 5700, 6000]
RAMP = [600, 900]
CAL_SEEDS = list(range(7120170, 7120180))
CHK_SEEDS = list(range(7120180, 7120200))
STRESS = "6000/900"
SMOKE_SEED = 7120050


def job(tag: str, drv: str, s: int, cell: str, root: Path) -> Job:
    m, r = cell.split("/")
    return Job(jid=f"{tag}_{drv}_m{m}_r{r}_s{s}",
               argv=["vsl_lab.jobs.mrg3_run", "--ctrl", "nc", "--seed", str(s), "--main-peak", m, "--ramp-peak", r,
                     "--tag", f"{tag}_{drv}", "--out-root", str(root), "--plant", "v3", "--driver", drv])


def load(root: Path, tag: str, drv: str) -> list:
    out = []
    for p in (root / f"{tag}_{drv}").glob("*/summary.json"):
        o = json.loads(p.read_text())
        o["_dir"] = str(p.parent)
        o["_cell"] = f"{int(o['main_peak'])}/{int(o['ramp_peak'])}"
        out.append(o)
    return out


def select_cell(rows: list) -> dict:
    cells = {}
    for o in rows:
        c = cells.setdefault(o["_cell"], {"n": 0, "bd": 0, "tele": 0, "fail": 0})
        c["n"] += 1
        c["bd"] += bool((o.get("capdrop") or {}).get("breakdown"))
        c["tele"] += o["teleports"]
        c["fail"] += o["health"]["status"] == "FAIL"
    table = {k: {"n": c["n"], "breakdown_share": c["bd"] / max(c["n"], 1), "teleports": c["tele"], "fail": c["fail"]}
             for k, c in cells.items()}
    ok = {k: v for k, v in table.items() if v["teleports"] == 0 and v["fail"] == 0}
    sel = min(ok, key=lambda k: (abs(ok[k]["breakdown_share"] - 0.5), sum(int(x) for x in k.split("/")))) if ok else None
    max_share = max((v["breakdown_share"] for v in table.values()), default=0.0)
    return {"table": table, "selected": sel, "max_share": max_share}


def inert(rows: list, base: list) -> dict:
    h0 = {(o["_cell"], o["seed"]): o["hash"] for o in base}
    pairs = [(o["hash"], h0[(o["_cell"], o["seed"])]) for o in rows if (o["_cell"], o["seed"]) in h0]
    same = sum(a == b for a, b in pairs)
    return {"pairs": len(pairs), "identical": same, "INERT": bool(pairs) and same == len(pairs)}


def analyse_variant(drv: str, sel: str, chk: list, det: list, xs: dict) -> dict:
    sigs = {(o["_cell"], o["seed"]): (o, R.run_signatures(Path(o["_dir"]), xs)) for o in chk}
    at_sel = [v for k, v in sigs.items() if k[0] == sel]
    cells_used = sorted({k[0] for k in sigs})
    # R-a
    bd = [(o, s) for o, s in at_sel if (o.get("capdrop") or {}).get("breakdown")]
    ratios = [s["cap"]["ratio"] for o, s in bd if s["cap"] and s["cap"]["ratio"] is not None]
    share = len(bd) / max(len(at_sel), 1)
    ra = {"n": len(at_sel), "breakdown_share": share, "n_ratios": len(ratios),
          "median_ratio_mean_based": float(np.median(ratios)) if ratios else None,
          "median_ratio_r1_max_based": float(np.median([o["capdrop"]["ratio"] for o, _ in bd
                                                         if o["capdrop"].get("ratio") == o["capdrop"].get("ratio")]))
          if bd else None}
    ra["PASS"] = bool(share >= 0.3 and len(ratios) >= 5 and 0.82 <= ra["median_ratio_mean_based"] <= 0.97)
    # R-b
    waves = [s["wave"] for _, s in sigs.values() if s["wave"]]
    cs = [w["c_kmh"] for w in waves if w["valid"]]
    rb = {"n_runs": len(sigs), "n_windows": len(waves), "n_valid": len(cs),
          "median_c_kmh": float(np.median(cs)) if cs else None,
          "pairs_used": {p: sum(w["pair"] == p for w in waves) for p in {w["pair"] for w in waves}}}
    rb["status"] = "n/a" if len(cs) < 5 else ("PASS" if -25.0 <= rb["median_c_kmh"] <= -10.0 else "FAIL")
    # R-c
    all_runs = chk + det
    tele = sum(o["teleports"] for o in all_runs)
    fails = sum(o["health"]["status"] == "FAIL" for o in all_runs)
    dis = [s["cap"]["discharge_vphpl"] for o, s in bd if s["cap"] and s["cap"]["discharge_vphpl"] is not None]
    ref = next((o for o in chk if o["_cell"] == sel and o["seed"] == CHK_SEEDS[0]), None)
    det_ok = bool(det) and ref is not None and all(d["hash"] == ref["hash"] for d in det)
    rc = {"teleports": tele, "fail": fails, "median_discharge_vphpl": float(np.median(dis)) if dis else None,
          "determinism": det_ok}
    rc["PASS"] = bool(tele == 0 and fails == 0 and dis and 1600.0 <= rc["median_discharge_vphpl"] <= 2400.0 and det_ok)
    # R-d
    orig = [s["origin"] for _, s in sigs.values() if s["origin"] is not None]
    down = sum(x in R.DOWNSTREAM_ORIGINS for x in orig)
    rd = {"n_congested_runs": len(orig), "share_bottleneck_origin": down / len(orig) if orig else None,
          "origins": {p: orig.count(p) for p in R.PROBES if p in orig}}
    rd["PASS"] = bool(orig and rd["share_bottleneck_origin"] >= 0.8)
    n_cong = sum(s["n_cong_samples"] for _, s in sigs.values())
    n_stop = sum(s["n_stop_samples"] for _, s in sigs.values())
    rep = {"stopped_share_in_congestion": n_stop / n_cong if n_cong else None, "cells": cells_used}
    ok = ra["PASS"] and rc["PASS"] and rd["PASS"] and rb["status"] != "FAIL"
    return {"R-a": ra, "R-b": rb, "R-c": rc, "R-d": rd, "reported": rep, "verdict": "PASS" if ok else "FAIL",
            "flag_wave_na": rb["status"] == "n/a"}


def write_report(res: dict, root: Path) -> None:
    L = ["# Track 2 (MRG3-v3): plant-realism gate, results", "",
         f"*{time.strftime('%Y-%m-%d %H:%M')} · protocol `docs/lab/t2_realism_protocol.md` · raw `{root}`*", "",
         "| variant | verdict | cell | R-a share / ratio (mean-based) | R-b wave km/h (valid) | R-c tele / FAIL / discharge / det | "
         "R-d bottleneck origin | stopped share |", "|---|---|---|---|---|---|---|---|"]
    for drv in VARIANTS:
        v = res["variants"][drv]
        if v["verdict"] in ("INERT",) or "R-a" not in v:
            L.append(f"| {drv} | **{v['verdict']}** | {v.get('cell')} | {v.get('note', '')} | | | | |")
            continue
        a, b, c, d = v["R-a"], v["R-b"], v["R-c"], v["R-d"]
        fmt = lambda x, f: (f.format(x) if x is not None else "–")
        L.append(f"| {drv} | **{v['verdict']}**{' (R-b n/a)' if v['flag_wave_na'] else ''} | {v['cell']} | "
                 f"{a['breakdown_share']:.2f} / {fmt(a['median_ratio_mean_based'], '{:.3f}')} (n={a['n_ratios']}) | "
                 f"{fmt(b['median_c_kmh'], '{:.1f}')} ({b['n_valid']}/{b['n_runs']}) | "
                 f"{c['teleports']} / {c['fail']} / {fmt(c['median_discharge_vphpl'], '{:.0f}')} / {c['determinism']} | "
                 f"{fmt(d['share_bottleneck_origin'], '{:.2f}')} ({d['n_congested_runs']}) | "
                 f"{fmt(v['reported']['stopped_share_in_congestion'], '{:.2f}')} |")
    L += ["", f"Primary plant for DRL (pre-registered preference H4 > H2 > H1 > H3 > H0): **{res['primary']}**", "",
          "Calibration tables and per-check details: `docs/lab/t2_realism_verdict.json`."]
    (REPO_ROOT / "docs" / "lab" / "t2_realism.md").write_text("\n".join(L) + "\n")


def analyse(root: Path) -> dict:
    xs = R.probe_x(P.files()["net"], PROBES)
    cal = {d: load(root, "cal", d) for d in VARIANTS}
    res = {"protocol": "docs/lab/t2_realism_protocol.md", "raw": str(root), "variants": {}, "probe_x": xs}
    for drv in VARIANTS:
        sc = select_cell(cal[drv])
        v = {"calibration": sc, "cell": sc["selected"]}
        if drv != "H0":
            v["R-0"] = inert(cal[drv], cal["H0"])
        if v.get("R-0", {}).get("INERT"):
            v["verdict"] = "INERT"
        elif sc["selected"] is None:
            v.update(verdict="FAIL", note="R-c: no cell with 0 teleports and 0 FAIL")
        elif sc["max_share"] < 0.2:
            v.update(verdict="FAIL", note="R-a: max breakdown share < 0.2 over the grid")
        else:
            chk = load(root, "chk", drv)
            det = load(root, "det", drv)
            v.update(analyse_variant(drv, sc["selected"], chk, det, xs))
        res["variants"][drv] = v
    res["verdict"] = {d: res["variants"][d]["verdict"] for d in VARIANTS}
    res["primary"] = next((d for d in PREFERENCE if res["verdict"][d] == "PASS"), None)
    (REPO_ROOT / "docs" / "lab" / "t2_realism_verdict.json").write_text(json.dumps(res, indent=1, default=str))
    write_report(res, root)
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["smoke", "run", "analyse"])
    ap.add_argument("--workers", type=int, default=N_MAX_DEFAULT)
    ap.add_argument("--gate-ok", action="store_true")
    ap.add_argument("--root", default=None)
    a = ap.parse_args(argv)
    if a.what == "smoke":
        root = RUNS_ROOT / "t2" / f"realism_smoke_{int(time.time())}"
        run_batch([job("smoke", d, SMOKE_SEED, "5400/900", root) for d in VARIANTS], root / "batch", max_workers=5,
                  gate_ok=a.gate_ok)
        xs = R.probe_x(P.files()["net"], PROBES)
        out = {}
        for d in VARIANTS:
            rows = load(root, "smoke", d)
            if not rows:
                out[d] = "NO OUTPUT"
                continue
            o = rows[0]
            s = R.run_signatures(Path(o["_dir"]), xs)
            out[d] = {"health": o["health"]["status"], "codes": list(o["health"]["by_code"]), "tele": o["teleports"],
                      "hash": o["hash"][:10], "t_sys": round(o["mean_time_in_system_s"], 1),
                      "bd": (o.get("capdrop") or {}).get("breakdown"), "wall": o.get("wall_s"),
                      "t_b": s["t_b"], "origin": s["origin"], "wave": s["wave"], "cap": s["cap"]}
        print(json.dumps(out, default=str, indent=1))
        return 0
    if a.what == "analyse":
        res = analyse(Path(a.root))
        print(json.dumps({"verdict": res["verdict"], "primary": res["primary"]}))
        return 0
    root = RUNS_ROOT / "t2" / f"realism_{int(time.time())}"
    cells = [f"{m}/{r}" for m in MAIN for r in RAMP]
    jobs = [job("cal", d, s, c, root) for d in VARIANTS for c in cells for s in CAL_SEEDS]
    run_batch(jobs, root / "batch_cal", max_workers=a.workers, gate_ok=a.gate_ok)
    cjobs = []
    for d in VARIANTS:
        rows = load(root, "cal", d)
        sc = select_cell(rows)
        if d != "H0" and inert(rows, load(root, "cal", "H0"))["INERT"]:
            continue
        if sc["selected"] is None or sc["max_share"] < 0.2:
            continue
        for c in sorted({sc["selected"], STRESS}):
            cjobs += [job("chk", d, s, c, root) for s in CHK_SEEDS]
        cjobs.append(job("det", d, CHK_SEEDS[0], sc["selected"], root))
    run_batch(cjobs, root / "batch_chk", max_workers=a.workers, gate_ok=True)
    res = analyse(root)
    n = sum(len(list((root).glob(f"{t}_*/*/summary.json"))) for t in ("cal", "chk", "det"))
    ledger.append("T2", "realism", "S", "mrg3v3_realism_gate", {"variants": VARIANTS, "grid": [MAIN, RAMP]},
                  f"{CAL_SEEDS[0]}-{CAL_SEEDS[-1]} (throw-away), {CHK_SEEDS[0]}-{CHK_SEEDS[-1]}", n,
                  {d: res["variants"][d].get("R-c", {}).get("fail") for d in VARIANTS},
                  {"verdict": res["verdict"], "primary": res["primary"]}, notes=str(root))
    print(json.dumps({"verdict": res["verdict"], "primary": res["primary"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
