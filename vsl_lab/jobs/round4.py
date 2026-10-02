"""Round 4 T-H stage (docs/lab/round4_harmonisation_protocol.md): harmonisation authority and the classical frontier on
LD3 (3 -> 2 lane drop) with H5 drivers (EIDM SUMO defaults) at a 0.2 s step.

python -m vsl_lab.jobs.round4 th --gate-ok [--workers 16]
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


def job(ctrl, s, cell, root, p=0.0, arm="none") -> Job:
    m, r = cell.split("/")
    argv = ["vsl_lab.jobs.mrg3_run", "--ctrl", ctrl, "--seed", str(s), "--main-peak", m, "--ramp-peak", r, "--tag", "th",
            "--out-root", str(root), "--plant", "v3", "--driver", "H5", "--step", "0.2", "--geom", "lanedrop", "--stops"]
    if p > 0:
        argv += ["--cav-share", str(p), "--cav-arm", arm, "--cav-x", "1.0"]
    return Job(jid=f"th_{ctrl.replace(':', '_')}_p{p:g}{arm}_m{m}_s{s}", argv=argv)


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


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["th"])
    ap.add_argument("--workers", type=int, default=N_MAX_DEFAULT)
    ap.add_argument("--gate-ok", action="store_true")
    ap.add_argument("--analyse-only", action="store_true")
    ap.add_argument("--root", default=None)
    a = ap.parse_args(argv)
    root = Path(a.root) if a.root else RUNS_ROOT / "t2" / f"round4_th_{int(time.time())}"
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
