"""Round 4 T-H stage (docs/lab/round4_harmonisation_protocol.md): harmonisation authority and the classical frontier on
LD3 (3 -> 2 lane drop) with H5 drivers (EIDM SUMO defaults) at a 0.2 s step.

python -m vsl_lab.jobs.round4 th --gate-ok [--workers 16]
python -m vsl_lab.jobs.round4 r2 --gate-ok        # Addendum A tuning (J = delay + 40 s/stop), freezes the baselines
python -m vsl_lab.jobs.round4 screen --gate-ok --run-dir <train run dir>   # P-H screening on the validation specs
python -m vsl_lab.jobs.round4 th --analyse-only --root <batch root>
"""
from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path

import numpy as np

from vsl_lab.config import N_MAX_DEFAULT, REPO_ROOT, RUNS_ROOT
from vsl_lab.eval.stats import paired_median_diff
from vsl_lab.ops import ledger
from vsl_lab.ops.scheduler import Job, run_batch

CELLS = ["3900/0", "4500/0"]
SEEDS = list(range(7160200, 7160230))
HUMAN = ["nc"] + [f"const:{b}" for b in (0.5, 0.6, 0.7, 0.8)] + [f"mtfc:{r}:38:9:0.0015" for r in (20, 25, 32)]
CAV = [("nc", "C"), ("cavconst:0.6", "C"), ("cavpi", "P")]
DETS = ("up3", "up2", "up1", "up0a", "up0b", "down")      # upstream -> downstream
W_STOP = 40.0                                               # s per stop (Addendum A)
R2_SEEDS = list(range(7160300, 7160320))
R2_CTRLS = (["nc"] + [f"const:{b}" for b in (0.75, 0.8, 0.85, 0.9, 0.95)]
            + [f"vslad:{th}:{b}" for th in (50, 70, 90) for b in (0.7, 0.8, 0.9)]
            + [f"mtfc:{r}:38:9:0.0015" for r in (28, 32, 36, 40)] + ["spec", "spec:0.25"])   # Addendum B
VAL_SPECS = [(m, s) for s in (7120300, 7120301, 7120302) for m in (3900, 4500)]
FROZEN = REPO_ROOT / "docs" / "lab" / "round4_baselines_frozen.json"


def job(ctrl, s, cell, root, p=0.0, arm="none", tag="th") -> Job:
    m, r = cell.split("/")
    argv = ["vsl_lab.jobs.mrg3_run", "--ctrl", ctrl, "--seed", str(s), "--main-peak", m, "--ramp-peak", r, "--tag", tag,
            "--out-root", str(root), "--plant", "v3", "--driver", "H5", "--step", "0.2", "--geom", "lanedrop", "--stops"]
    if p > 0:
        argv += ["--cav-share", str(p), "--cav-arm", arm, "--cav-x", "1.0"]
    return Job(jid=f"{tag}_{ctrl.replace(':', '_')}_p{p:g}{arm}_m{m}_s{s}", argv=argv)


def label(o) -> str:
    return o["ctrl"] if not o.get("cav_share") else f"{o['ctrl']}@cav{o['cav_share']:g}{o['cav_arm']}"


def isolated_jam_minutes(run_dir: Path) -> int:
    """SPECIALIST applicability (P1 thresholds): 1-min detector q <= 1500 veh/h/lane and v <= 50 km/h with both neighbour
    detectors at v > 50 km/h."""
    rows = list(csv.DictReader(open(run_dir / "features.csv")))
    n = 0
    for k in range(0, len(rows) - 1, 2):
        q = {}; v = {}
        for e in DETS:
            qs = [float(rows[k + j][f"{e}_q"]) for j in (0, 1)]
            vs = [float(rows[k + j][f"{e}_v"]) for j in (0, 1) if float(rows[k + j][f"{e}_v"]) >= 0]
            q[e], v[e] = float(np.mean(qs)), (float(np.mean(vs)) if vs else None)
        for i, e in enumerate(DETS[1:-1], start=1):
            up, dn = DETS[i - 1], DETS[i + 1]
            if v[e] is not None and v[up] is not None and v[dn] is not None and q[e] <= 1500 and v[e] <= 50 \
                    and v[up] > 50 and v[dn] > 50:
                n += 1
    return n


def analyse(root: Path) -> dict:
    rows = []
    for p in (root / "th").glob("*/summary.json"):
        o = json.loads(p.read_text()); o["_dir"] = str(p.parent); rows.append(o)
    by = {}
    for o in rows:
        by.setdefault((f"{int(o['main_peak'])}/{int(o['ramp_peak'])}", label(o)), {})[o["seed"]] = o
    res = {"cells": {}, "n_runs": len(rows), "health": {}}
    for o in rows:
        res["health"][o["health"]["status"]] = res["health"].get(o["health"]["status"], 0) + 1
    for cell in CELLS:
        nch, ncp = by.get((cell, "nc"), {}), by.get((cell, "nc@cav0.25C"), {})
        out = {}
        for (c, lab), d in sorted(by.items()):
            if c != cell or lab in ("nc", "nc@cav0.25C"):
                continue
            ref = ncp if "@cav" in lab else nch
            ss = sorted(set(ref) & set(d))
            if not ss:
                continue
            r = {}
            for k, f in (("delay", lambda o: o["mean_time_in_system_s"]), ("stops", lambda o: o["stops_per_veh"]),
                         ("throughput", lambda o: o.get("arrived", 0))):
                pm = paired_median_diff([f(ref[s]) for s in ss], [f(d[s]) for s in ss], seed=7160229)
                base = float(np.median([f(ref[s]) for s in ss]))
                r[k] = {"rel": pm["median_diff"] / base if base else None, "ci": [pm["ci_lo"], pm["ci_hi"]],
                        "excl0": pm["excludes_0"], "ref_median": base}
            r["eb_events_median"] = float(np.median([(d[s].get("eb_cav") or 0) + (d[s].get("eb_human") or 0) for s in ss]))
            r["harmonises_for_free"] = bool(r["stops"]["rel"] is not None and r["stops"]["rel"] <= -0.10
                                            and r["stops"]["excl0"] and r["delay"]["rel"] <= 0.02)
            r["n"] = len(ss)
            out[lab] = r
        th0 = out.get("const:0.6", {}).get("stops", {})
        spec = [isolated_jam_minutes(Path(o["_dir"])) for o in nch.values()]
        res["cells"][cell] = {
            "per_ctrl": out, "T_H0": bool(th0 and th0["rel"] is not None and th0["rel"] <= -0.10 and th0["excl0"]),
            "nc_human": {"delay": float(np.median([o["mean_time_in_system_s"] for o in nch.values()])) if nch else None,
                         "stops": float(np.median([o["stops_per_veh"] for o in nch.values()])) if nch else None},
            "nc_cav25_vs_human_delay_rel": (float(np.median([ncp[s]["mean_time_in_system_s"] / nch[s]["mean_time_in_system_s"] - 1
                                                             for s in set(ncp) & set(nch)])) if ncp and nch else None),
            "specialist_isolated_jam_minutes_median": float(np.median(spec)) if spec else None}
    res["T_H0_PASS"] = any(c["T_H0"] for c in res["cells"].values())
    res["specialist_applicable"] = any((c["specialist_isolated_jam_minutes_median"] or 0) > 0 for c in res["cells"].values())
    return res


def report(res: dict, root: Path) -> None:
    L = ["# Round 4 T-H (harmonisation on LD3, H5, 0.2 s): results", "",
         f"*{time.strftime('%Y-%m-%d %H:%M')} · protocol `docs/lab/round4_harmonisation_protocol.md` · {res['n_runs']} runs · "
         f"health {res['health']} · raw `{root}`*", "",
         f"**T-H0 (posted VSL has authority over stops): {'PASS' if res['T_H0_PASS'] else 'FAIL'}** · "
         f"SPECIALIST applicable: {res['specialist_applicable']}", ""]
    for cell, c in res["cells"].items():
        L += [f"## Cell {cell}", "",
              f"NC-human median: delay {c['nc_human']['delay']:.1f} s, stops {c['nc_human']['stops']:.2f} per vehicle; "
              f"NC with 25 % CACC vs NC-human delay: {c['nc_cav25_vs_human_delay_rel']:+.1%}; SPECIALIST isolated-jam minutes "
              f"(median per run): {c['specialist_isolated_jam_minutes_median']}", "",
              "| controller (vs its NC) | Δ delay | 95 % CI (s) | Δ stops | 95 % CI (stops/veh) | Δ arrived | harmonises for free |",
              "|---|---|---|---|---|---|---|"]
        for lab, r in sorted(c["per_ctrl"].items(), key=lambda kv: kv[1]["stops"]["rel"] or 0):
            L.append(f"| {lab} | {r['delay']['rel']:+.1%} | [{r['delay']['ci'][0]:+.1f}, {r['delay']['ci'][1]:+.1f}] | "
                     f"{r['stops']['rel']:+.1%} | [{r['stops']['ci'][0]:+.2f}, {r['stops']['ci'][1]:+.2f}] | "
                     f"{r['throughput']['rel']:+.1%} | {'yes' if r['harmonises_for_free'] else 'no'} |")
        L.append("")
    (REPO_ROOT / "docs" / "lab" / "round4_th.md").write_text("\n".join(L) + "\n")


def J(o) -> float:
    return o["mean_time_in_system_s"] + W_STOP * o["stops_per_veh"]


def r2(root: Path, workers: int, gate_ok: bool, analyse_only: bool, only: list | None = None, skip: list | None = None) -> dict:
    if not analyse_only:
        ctrls = [c for c in R2_CTRLS if (not only or c in only) and c not in (skip or [])]
        jobs = [job(c, s, cell, root, tag="r2") for cell in CELLS for s in R2_SEEDS for c in ctrls]
        run_batch(jobs, root / "batch", workers, gate_ok=gate_ok)
    by = {}
    for p in (root / "r2").glob("*/summary.json"):
        o = json.loads(p.read_text())
        by.setdefault(o["ctrl"], {}).setdefault(f"{int(o['main_peak'])}/{int(o['ramp_peak'])}", []).append(o)
    table = {}
    for c, cells in by.items():
        if all(cell in cells for cell in CELLS):
            row = {cell: {"J": float(np.median([J(o) for o in cells[cell]])),
                          "delay": float(np.median([o["mean_time_in_system_s"] for o in cells[cell]])),
                          "stops": float(np.median([o["stops_per_veh"] for o in cells[cell]])), "n": len(cells[cell]),
                          "fail": sum(o["health"]["status"] == "FAIL" for o in cells[cell])} for cell in CELLS}
            row["score"] = float(np.mean([row[cell]["J"] for cell in CELLS]))
            table[c] = row
    fam = lambda c: c.split(":")[0]
    best = {f: min((c for c in table if fam(c) == f), key=lambda c: table[c]["score"]) for f in {fam(c) for c in table}}
    learnfree = [c for c in table if c != "nc"]
    tuned = min(learnfree, key=lambda c: table[c]["score"]) if learnfree else None
    out = {"protocol": "docs/lab/round4_harmonisation_protocol.md (Addendum A)", "w_stop": W_STOP, "table": table,
           "family_best": best, "tuned_classical": tuned, "raw": str(root), "frozen_at": time.strftime("%Y-%m-%d %H:%M")}
    FROZEN.write_text(json.dumps(out, indent=1))
    L = ["# Round 4 R2-H (tuning, J = delay + 40 s per stop): results", "",
         f"*{out['frozen_at']} · raw `{root}`* · tuned classical: **{tuned}** · family bests: {best}", "",
         "| controller | J 3900 | delay 3900 | stops 3900 | J 4500 | delay 4500 | stops 4500 | score | FAIL |",
         "|---|---|---|---|---|---|---|---|---|"]
    for c in sorted(table, key=lambda c: table[c]["score"]):
        r = table[c]
        L.append(f"| {c} | {r['3900/0']['J']:.1f} | {r['3900/0']['delay']:.1f} | {r['3900/0']['stops']:.2f} | "
                 f"{r['4500/0']['J']:.1f} | {r['4500/0']['delay']:.1f} | {r['4500/0']['stops']:.2f} | {r['score']:.1f} | "
                 f"{r['3900/0']['fail'] + r['4500/0']['fail']} |")
    (REPO_ROOT / "docs" / "lab" / "round4_r2.md").write_text("\n".join(L) + "\n")
    ledger.append("T2", "R4-R2", "S", "round4_r2", {"ctrls": R2_CTRLS, "w_stop": W_STOP}, f"{R2_SEEDS[0]}-{R2_SEEDS[-1]}",
                  sum(len(v) for c in by.values() for v in c.values()), {}, {"tuned": tuned, "family_best": best},
                  notes=str(root))
    return out


def screen(root: Path, run_dir: Path, workers: int, gate_ok: bool, mode: str = "direct_fine") -> dict:
    fz = json.loads(FROZEN.read_text())
    refs = sorted({fz["tuned_classical"], *fz["family_best"].values(), "nc"})
    jobs = [job(c, s, f"{m}/0", root, tag="val") for m, s in VAL_SPECS for c in refs]
    models = {"final": run_dir / "final_model.zip", "best": run_dir / "best_val_model.zip"}
    for lab, mp in models.items():
        if mp.exists():
            jobs += [Job(jid=f"val_rl{lab}_m{m}_s{s}", argv=["vsl_lab.jobs.r4_eval_rl", "--model", str(mp), "--main-peak", str(m),
                                                            "--seed", str(s), "--out-root", str(root), "--tag", f"rl_{lab}",
                                                            "--mode", mode])
                     for m, s in VAL_SPECS]
    run_batch(jobs, root / "batch", workers, gate_ok=gate_ok)
    res = {}
    for p in (root / "val").glob("*/summary.json"):
        o = json.loads(p.read_text()); res.setdefault(o["ctrl"], []).append(o)
    for lab in models:
        for p in (root / f"rl_{lab}").glob("*.json"):
            res.setdefault(f"rl_{lab}", []).append(json.loads(p.read_text()))
    summ = {c: {"J": float(np.mean([J(o) for o in v])), "delay": float(np.mean([o["mean_time_in_system_s"] for o in v])),
                "stops": float(np.mean([o["stops_per_veh"] for o in v])), "n": len(v),
                "fail": sum((o.get("health") if isinstance(o.get("health"), str) else o["health"]["status"]) == "FAIL" for o in v)}
            for c, v in res.items()}
    t = summ.get(fz["tuned_classical"])
    crit = {}
    for lab in ("rl_final", "rl_best"):
        d = summ.get(lab)
        if d and t:
            crit[lab] = {"C_H1": d["J"] <= 0.95 * t["J"], "C_H2": d["delay"] <= 1.02 * t["delay"] and d["stops"] <= 1.02 * t["stops"],
                         "C_H3": d["fail"] == 0}
            crit[lab]["PASS"] = all(crit[lab].values())
    out = {"tuned_classical": fz["tuned_classical"], "summary": summ, "criteria": crit, "raw": str(root), "run_dir": str(run_dir)}
    (root / "screen.json").write_text(json.dumps(out, indent=1))
    L = [f"## P-H screening ({time.strftime('%Y-%m-%d %H:%M')}) · run `{run_dir}`", "",
         "| controller | J (mean, s) | delay (s) | stops/veh | n | FAIL |", "|---|---|---|---|---|---|"]
    for c in sorted(summ, key=lambda c: summ[c]["J"]):
        r = summ[c]
        L.append(f"| {c} | {r['J']:.1f} | {r['delay']:.1f} | {r['stops']:.2f} | {r['n']} | {r['fail']} |")
    L += ["", f"Criteria vs tuned classical `{fz['tuned_classical']}`: {json.dumps(crit)}", ""]
    rp = REPO_ROOT / "docs" / "lab" / "round4_pilots.md"
    rp.write_text((rp.read_text() if rp.exists() else "# Round 4 DRL pilots: screening (exploratory)\n\n") + "\n".join(L) + "\n")
    ledger.append("T2", "R4-P", "S", "round4_screen", {"run_dir": str(run_dir)}, "7120300-7120302", sum(v["n"] for v in summ.values()),
                  {}, crit, notes=str(root))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["th", "r2", "screen", "r5refs"])
    ap.add_argument("--mode", default="direct_fine", help="policy action mode for screen (P-H3: residual_c)")
    ap.add_argument("--run-dir", default=None)
    ap.add_argument("--only", default=None, help="comma list of controllers (r2)")
    ap.add_argument("--skip", default=None, help="comma list of controllers (r2)")
    ap.add_argument("--workers", type=int, default=N_MAX_DEFAULT)
    ap.add_argument("--gate-ok", action="store_true")
    ap.add_argument("--analyse-only", action="store_true")
    ap.add_argument("--root", default=None)
    a = ap.parse_args(argv)
    root = Path(a.root) if a.root else RUNS_ROOT / "t2" / f"round4_{a.what}_{int(time.time())}"
    if a.what == "r2":
        out = r2(root, a.workers, a.gate_ok, a.analyse_only, only=a.only.split(",") if a.only else None,
                 skip=a.skip.split(",") if a.skip else None)
        print(json.dumps({"tuned": out["tuned_classical"], "family_best": out["family_best"]}))
        return 0
    if a.what == "r5refs":   # Addendum D: classical arms of R5-H on the shared T2 test seeds, pre-computed
        fz = json.loads(FROZEN.read_text())
        refs = sorted({fz["tuned_classical"], *fz["family_best"].values(), "nc"})
        jobs = [job(c, s, cell, root, tag="r5refs") for cell in CELLS for s in range(7120500, 7120530) for c in refs]
        run_batch(jobs, root / "batch", a.workers, gate_ok=a.gate_ok)
        ledger.append("T2", "R4-R5refs", "S", "round4_r5refs", {"refs": refs}, "7120500-7120529", len(jobs), {}, {},
                      notes=str(root))
        return 0
    if a.what == "screen":
        out = screen(root, Path(a.run_dir), a.workers, a.gate_ok, mode=a.mode)
        print(json.dumps(out["criteria"]))
        return 0
    if not a.analyse_only:
        jobs = [job(c, s, cell, root) for cell in CELLS for s in SEEDS for c in HUMAN]
        jobs += [job(c, s, cell, root, p=0.25, arm=arm) for cell in CELLS for s in SEEDS for c, arm in CAV]
        run_batch(jobs, root / "batch", a.workers, gate_ok=a.gate_ok)
    res = analyse(root)
    (root / "analysis.json").write_text(json.dumps(res, indent=1, default=str))
    (REPO_ROOT / "docs" / "lab" / "round4_th.json").write_text(json.dumps(res, indent=1, default=str))
    report(res, root)
    ledger.append("T2", "R4-TH", "S", "round4_th", {"cells": CELLS, "ctrls": HUMAN + [f"{c}@{arm}" for c, arm in CAV]},
                  f"{SEEDS[0]}-{SEEDS[-1]}", res["n_runs"], res["health"],
                  {"T_H0": res["T_H0_PASS"], "specialist_applicable": res["specialist_applicable"]}, notes=str(root))
    print(json.dumps({"T_H0": res["T_H0_PASS"], "specialist_applicable": res["specialist_applicable"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
