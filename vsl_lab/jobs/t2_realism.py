"""Plant-realism gate on MRG3-v3 driver variants H0-H5 (docs/lab/t2_realism_protocol.md, incl. Addendum A).

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

VARIANTS = ["H0", "H1", "H2", "H3", "H4", "H5"]
PREFERENCE = ["H4", "H5", "H2", "H1", "H3", "H0"]   # Addendum A
MAIN = [4200, 4500, 4800, 5100, 5400, 5700, 6000]
RAMP = [600, 900]
CAL_SEEDS = list(range(7120170, 7120180))
CHK_SEEDS = list(range(7120180, 7120200))
STRESS = "6000/900"
SMOKE_SEED = 7120050
STEP = None      # simulation step override (Round 3 Addendum A: 0.2 s re-check); None = plant default 0.5 s
SUFFIX = ""      # output-file suffix for a re-check (e.g. "_step0.2")


def job(tag: str, drv: str, s: int, cell: str, root: Path) -> Job:
    m, r = cell.split("/")
    return Job(jid=f"{tag}_{drv}_m{m}_r{r}_s{s}",
               argv=["vsl_lab.jobs.mrg3_run", "--ctrl", "nc", "--seed", str(s), "--main-peak", m, "--ramp-peak", r,
                     "--tag", f"{tag}_{drv}", "--out-root", str(root), "--plant", "v3", "--driver", drv]
               + (["--step", str(STEP)] if STEP else []))


def load(root: Path, tag: str, drv: str) -> list:
    out = []
    for p in (root / f"{tag}_{drv}").glob("*/summary.json"):
        o = json.loads(p.read_text())
        o["_dir"] = str(p.parent)
        o["_cell"] = f"{int(o['main_peak'])}/{int(o['ramp_peak'])}"
        out.append(o)
    return out


def select_cell(rows: list) -> dict:
    """Addendum A: breakdown = a sustained probe onset exists (R1 capdrop flag reported alongside)."""
    cells = {}
    for o in rows:
        c = cells.setdefault(o["_cell"], {"n": 0, "bd": 0, "bd_capdrop": 0, "tele": 0, "fail": 0})
        c["n"] += 1
        c["bd"] += R.sustained_onset(Path(o["_dir"])) is not None
        c["bd_capdrop"] += bool((o.get("capdrop") or {}).get("breakdown"))
        c["tele"] += o["teleports"]
        c["fail"] += o["health"]["status"] == "FAIL"
    table = {k: {"n": c["n"], "breakdown_share": c["bd"] / max(c["n"], 1),
                 "breakdown_share_capdrop": c["bd_capdrop"] / max(c["n"], 1), "teleports": c["tele"], "fail": c["fail"]}
             for k, c in sorted(cells.items())}
    ok = {k: v for k, v in table.items() if v["teleports"] == 0 and v["fail"] == 0}
    sel = min(ok, key=lambda k: (abs(ok[k]["breakdown_share"] - 0.5), sum(int(x) for x in k.split("/")))) if ok else None
    max_share = max((v["breakdown_share"] for v in table.values()), default=0.0)
    return {"table": table, "selected": sel, "max_share": max_share}


def inert(rows: list, base: list) -> dict:
    h0 = {(o["_cell"], o["seed"]): o["hash"] for o in base}
    pairs = [(o["hash"], h0[(o["_cell"], o["seed"])]) for o in rows if (o["_cell"], o["seed"]) in h0]
    same = sum(a == b for a, b in pairs)
    return {"pairs": len(pairs), "identical": same, "INERT": bool(pairs) and same == len(pairs)}


def _boot_ratio(dis: list, ff: list, n: int = 2000, seed: int = 7120199) -> tuple:
    rng = np.random.default_rng(seed)
    r = [np.median(rng.choice(dis, len(dis))) / np.median(rng.choice(ff, len(ff))) for _ in range(n)]
    return float(np.percentile(r, 2.5)), float(np.percentile(r, 97.5))


def analyse_variant(drv: str, sel: str, chk: list, det: list, xs: dict) -> dict:
    sigs = {(o["_cell"], o["seed"]): (o, R.run_signatures(Path(o["_dir"]), xs)) for o in chk}
    at_sel = [v for k, v in sigs.items() if k[0] == sel]
    # R-a (Addendum A: between-run Q_dis / Q_ff at the selected cell)
    bd = [(o, s) for o, s in at_sel if s["t_b"] is not None]
    nbd = [(o, s) for o, s in at_sel if s["t_b"] is None]
    dis = [s["cap"]["discharge_vphpl"] for _, s in bd if s["cap"]["discharge_vphpl"] is not None]
    ff = [s["plateau_vphpl"] for _, s in nbd if s["plateau_vphpl"] is not None]
    share = len(bd) / max(len(at_sel), 1)
    ok_n = len(dis) >= 3 and len(ff) >= 3
    ratio = float(np.median(dis) / np.median(ff)) if ok_n else None
    med = lambda xs_: float(np.median(xs_)) if xs_ else None
    ra = {"n": len(at_sel), "breakdown_share": share,
          "breakdown_share_capdrop": float(np.mean([bool((o.get("capdrop") or {}).get("breakdown")) for o, _ in at_sel]))
          if at_sel else None,
          "n_discharge": len(dis), "n_free": len(ff), "Q_dis_vphpl": med(dis), "Q_ff_vphpl": med(ff), "ratio": ratio,
          "ratio_ci95": _boot_ratio(dis, ff) if ok_n else None,
          "reported_ratio_within_ramp_corrected": med([s["cap"]["ratio_within_ramp_corrected"] for _, s in bd
                                                       if s["cap"]["ratio_within_ramp_corrected"] is not None]),
          "reported_ratio_original_10min": med([s["cap"]["ratio_original_10min"] for _, s in bd
                                                if s["cap"]["ratio_original_10min"] is not None]),
          "reported_ratio_r1_max_based": med([o["capdrop"]["ratio"] for o, _ in at_sel
                                              if (o.get("capdrop") or {}).get("breakdown")
                                              and o["capdrop"].get("ratio") == o["capdrop"].get("ratio")])}
    ra["PASS"] = bool(share >= 0.3 and ok_n and 0.82 <= ratio <= 0.97)
    # R-b
    waves = [s["wave"] for _, s in sigs.values() if s["wave"]]
    cs = [w["c_kmh"] for w in waves if w["valid"]]
    rb = {"n_runs": len(sigs), "n_windows": len(waves), "n_valid": len(cs), "median_c_kmh": med(cs),
          "pairs_used": {p: sum(w["pair"] == p for w in waves) for p in sorted({w["pair"] for w in waves})}}
    rb["status"] = "n/a" if len(cs) < 5 else ("PASS" if -25.0 <= rb["median_c_kmh"] <= -10.0 else "FAIL")
    # R-c (Addendum A: teleports / FAIL gated at the operating point = selected cell + determinism re-run)
    op = [o for o, _ in at_sel] + det
    stress = [o for (c, _), (o, _) in sigs.items() if c != sel]
    tele_op = sum(o["teleports"] for o in op)
    fail_op = sum(o["health"]["status"] == "FAIL" for o in op)
    tele_st = sum(o["teleports"] for o in stress)
    fail_st = sum(o["health"]["status"] == "FAIL" for o in stress)
    ref = next((o for o, _ in at_sel if o["seed"] == CHK_SEEDS[0]), None)
    det_ok = bool(det) and ref is not None and all(d["hash"] == ref["hash"] for d in det)
    q_ok = bool(dis) and 1600.0 <= float(np.median(dis)) <= 2400.0
    rc = {"teleports_operating": tele_op, "fail_operating": fail_op, "teleports_stress": tele_st, "fail_stress": fail_st,
          "median_discharge_vphpl": med(dis), "determinism": det_ok}
    rc["PASS"] = bool(tele_op == 0 and fail_op == 0 and q_ok and det_ok)
    rc["PASS_original_rule"] = bool(rc["PASS"] and tele_st == 0 and fail_st == 0)
    # R-d
    orig = [s["origin"] for _, s in sigs.values() if s["origin"] is not None]
    down = sum(x in R.DOWNSTREAM_ORIGINS for x in orig)
    rd = {"n_congested_runs": len(orig), "share_bottleneck_origin": down / len(orig) if orig else None,
          "origins": {p: orig.count(p) for p in R.PROBES if p in orig}}
    rd["PASS"] = bool(orig and rd["share_bottleneck_origin"] >= 0.8)
    n_cong = sum(s["n_cong_samples"] for _, s in sigs.values())
    n_stop = sum(s["n_stop_samples"] for _, s in sigs.values())
    rep = {"stopped_share_in_congestion": n_stop / n_cong if n_cong else None, "cells": sorted({k[0] for k in sigs}),
           "median_wall_s": med([o.get("wall_s") for o in chk if o.get("wall_s")])}
    ok = ra["PASS"] and rd["PASS"] and rb["status"] != "FAIL"
    return {"R-a": ra, "R-b": rb, "R-c": rc, "R-d": rd, "reported": rep,
            "verdict": "PASS" if ok and rc["PASS"] else "FAIL",
            "verdict_original_rc_rule": "PASS" if ok and rc["PASS_original_rule"] else "FAIL",
            "flag_wave_na": rb["status"] == "n/a"}


def write_report(res: dict, root: Path) -> None:
    L = ["# Track 2 (MRG3-v3): plant-realism gate, results", "",
         f"*{time.strftime('%Y-%m-%d %H:%M')} · protocol `docs/lab/t2_realism_protocol.md` (incl. Addendum A) · raw `{root}`*",
         "", "| variant | verdict (original R-c rule) | cell | R-a onset share / Q_dis÷Q_ff [95 % CI] | R-b wave km/h "
         "(valid/runs) | R-c tele op / stress · FAIL op · discharge · det | R-d bottleneck origin (n) | stopped share |",
         "|---|---|---|---|---|---|---|---|"]
    for drv in VARIANTS:
        v = res["variants"][drv]
        if v["verdict"] in ("INERT",) or "R-a" not in v:
            L.append(f"| {drv} | **{v['verdict']}** | {v.get('cell')} | {v.get('note', '')} | | | | |")
            continue
        a, b, c, d = v["R-a"], v["R-b"], v["R-c"], v["R-d"]
        fmt = lambda x, f: (f.format(x) if x is not None else "–")
        ci = a["ratio_ci95"]
        L.append(f"| {drv} | **{v['verdict']}**{' (R-b n/a)' if v['flag_wave_na'] else ''} "
                 f"({v['verdict_original_rc_rule']}) | {v['cell']} | "
                 f"{a['breakdown_share']:.2f} / {fmt(a['ratio'], '{:.3f}')}"
                 f"{f' [{ci[0]:.3f}, {ci[1]:.3f}]' if ci else ''} (n={a['n_discharge']}+{a['n_free']}) | "
                 f"{fmt(b['median_c_kmh'], '{:.1f}')} ({b['n_valid']}/{b['n_runs']}) | "
                 f"{c['teleports_operating']} / {c['teleports_stress']} · {c['fail_operating']} · "
                 f"{fmt(c['median_discharge_vphpl'], '{:.0f}')} · {c['determinism']} | "
                 f"{fmt(d['share_bottleneck_origin'], '{:.2f}')} ({d['n_congested_runs']}) | "
                 f"{fmt(v['reported']['stopped_share_in_congestion'], '{:.2f}')} |")
    L += ["", f"Primary plant for DRL (preference H4 > H5 > H2 > H1 > H3 > H0, Addendum A): **{res['primary']}**", "",
          "Calibration tables and per-check details: `docs/lab/t2_realism_verdict.json`."]
    (REPO_ROOT / "docs" / "lab" / f"t2_realism{SUFFIX}.md").write_text("\n".join(L) + "\n")


def analyse(root: Path) -> dict:
    xs = R.probe_x(P.files()["net"], PROBES)
    cal = {d: load(root, "cal", d) for d in VARIANTS}
    res = {"protocol": "docs/lab/t2_realism_protocol.md", "raw": str(root), "variants": {}, "probe_x": xs}
    for drv in VARIANTS:
        sc = select_cell(cal[drv])
        v = {"calibration": sc, "cell": sc["selected"]}
        if drv != "H0" and "H0" in VARIANTS:
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
    res["step"] = STEP or P.STEP_LENGTH
    (REPO_ROOT / "docs" / "lab" / f"t2_realism_verdict{SUFFIX}.json").write_text(json.dumps(res, indent=1, default=str))
    write_report(res, root)
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["smoke", "run", "analyse"])
    ap.add_argument("--workers", type=int, default=N_MAX_DEFAULT)
    ap.add_argument("--gate-ok", action="store_true")
    ap.add_argument("--root", default=None)
    ap.add_argument("--step", type=float, default=None)
    ap.add_argument("--variants", default=None, help="comma list (re-check), e.g. H3,H5")
    ap.add_argument("--cal-seeds", default=None, help="a-b inclusive")
    ap.add_argument("--chk-seeds", default=None, help="a-b inclusive")
    a = ap.parse_args(argv)
    global STEP, SUFFIX, VARIANTS, CAL_SEEDS, CHK_SEEDS
    if a.step:
        STEP, SUFFIX = a.step, f"_step{a.step:g}"
    if a.variants:
        VARIANTS = [v for v in a.variants.split(",") if v]
    rng_ = lambda txt: list(range(int(txt.split("-")[0]), int(txt.split("-")[1]) + 1))
    if a.cal_seeds:
        CAL_SEEDS = rng_(a.cal_seeds)
    if a.chk_seeds:
        CHK_SEEDS = rng_(a.chk_seeds)
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
    root = RUNS_ROOT / "t2" / f"realism{SUFFIX}_{int(time.time())}"
    cells = [f"{m}/{r}" for m in MAIN for r in RAMP]
    jobs = [job("cal", d, s, c, root) for d in VARIANTS for c in cells for s in CAL_SEEDS]
    run_batch(jobs, root / "batch_cal", max_workers=a.workers, gate_ok=a.gate_ok)
    cjobs = []
    for d in VARIANTS:
        rows = load(root, "cal", d)
        sc = select_cell(rows)
        if d != "H0" and "H0" in VARIANTS and inert(rows, load(root, "cal", "H0"))["INERT"]:
            continue
        if sc["selected"] is None or sc["max_share"] < 0.2:
            continue
        for c in sorted({sc["selected"], STRESS}):
            cjobs += [job("chk", d, s, c, root) for s in CHK_SEEDS]
        cjobs.append(job("det", d, CHK_SEEDS[0], sc["selected"], root))
    run_batch(cjobs, root / "batch_chk", max_workers=a.workers, gate_ok=True)
    res = analyse(root)
    n = sum(len(list((root).glob(f"{t}_*/*/summary.json"))) for t in ("cal", "chk", "det"))
    ledger.append("T2", "realism", "S", f"mrg3v3_realism_gate{SUFFIX}", {"variants": VARIANTS, "grid": [MAIN, RAMP],
                                                                     "step": STEP or P.STEP_LENGTH},
                  f"{CAL_SEEDS[0]}-{CAL_SEEDS[-1]} (throw-away), {CHK_SEEDS[0]}-{CHK_SEEDS[-1]}", n,
                  {d: res["variants"][d].get("R-c", {}).get("fail") for d in VARIANTS},
                  {"verdict": res["verdict"], "primary": res["primary"]}, notes=str(root))
    print(json.dumps({"verdict": res["verdict"], "primary": res["primary"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
