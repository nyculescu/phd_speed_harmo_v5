"""Track 1 / R1: run and analyse the BN4 plant checks exactly as in docs/lab/t1_bn4_plant_checks_protocol.md.

python -m vsl_lab.jobs.t1_r1_checks --workers N --gate-ok           # run everything + analyse
python -m vsl_lab.jobs.t1_r1_checks --analyse-only --batch-root DIR  # re-analyse
"""
from __future__ import annotations

import argparse
import json
import random
import statistics as st
import time
from pathlib import Path

import numpy as np

from vsl_lab.config import REPO_ROOT, RUNS_ROOT
from vsl_lab.eval.stats import paired_median_diff
from vsl_lab.ops import ledger
from vsl_lab.ops.scheduler import Job, run_batch

Q_LEVELS = list(range(400, 2600, 100))
SWEEP_SEEDS = list(range(7110010, 7110020))
T0_SEEDS = list(range(7110020, 7110030))
T0_Q = [1200, 2000]
T0_CAPS = [None, 10.0, 5.0]
HIGH_Q = [2200, 2300, 2400, 2500]


def job_nc(tag, q, s, root, lc=False, cap=None, cap_t=None):
    argv = ["vsl_lab.jobs.bn4_nc", "--inflow", str(q), "--seed", str(s), "--tag", tag, "--out-root", str(root)]
    if lc:
        argv.append("--lane-changing")
    if cap is not None:
        argv += ["--av-cap", str(cap), "--av-cap-t", str(cap_t)]
    jid = f"{tag}_q{q}_s{s}_lc{int(lc)}_cap{cap}"
    return Job(jid=jid, argv=argv)


def load_summaries(root: Path, tag: str) -> list:
    out = []
    for p in (root / tag).glob("*/summary.json"):
        try:
            out.append(json.loads(p.read_text()))
        except Exception:
            pass
    return out


def moving_outflow(o: dict, t0: float, t1: float, win: float = 60.0) -> np.ndarray:
    b = o["bin_s"]
    bins = o["arrivals_bins"]
    nb = int(round(t1 / b))
    arr = np.zeros(nb)
    for k, v in bins.items():
        if int(k) < nb:
            arr[int(k)] = v
    w = int(round(win / b))
    mv = np.convolve(arr, np.ones(w), "valid") * 3600.0 / win   # value at index i covers bins i..i+w-1
    start = int(round(t0 / b))
    return mv[start:]


def analyse(root: Path) -> dict:
    res = {}
    for tag, lc in (("t1_sweep", False), ("t1_sweepL", True)):
        S = load_summaries(root, tag)
        if not S:
            continue
        health = {"PASS": 0, "WARN": 0, "FAIL": 0}
        codes = {}
        tele = 0
        byq = {}
        for o in S:
            health[o["health"]["status"]] += 1
            for c, v in o["health"]["by_code"].items():
                codes[c] = codes.get(c, 0) + 1
            tele += o["teleports"]
            byq.setdefault(int(o["inflow_vph"]), []).append(o["outflow_vph"])
        Q = {q: float(np.median(v)) for q, v in sorted(byq.items())}
        peak_q = max(Q, key=Q.get)
        peak = Q[peak_q]
        high = float(np.mean([Q[q] for q in HIGH_Q if q in Q]))
        res[tag] = {
            "n_runs": len(S), "health": health, "codes_runs": codes, "teleports_total": tele,
            "Q_median_by_q": Q, "Q_min_by_q": {q: float(np.min(v)) for q, v in sorted(byq.items())},
            "Q_max_by_q": {q: float(np.max(v)) for q, v in sorted(byq.items())},
            "peak_q": peak_q, "peak": peak, "high_mean": high, "high_over_peak": round(high / peak, 4),
            "Q_at_2500": Q.get(2500),
            "PASS": bool(high <= 0.95 * peak and health["FAIL"] == 0 and tele == 0) if not lc else None,
        }
    # T0
    S0 = load_summaries(root, "t1_t0")
    if S0:
        cells = {}
        for o in S0:
            key = (int(o["inflow_vph"]), o["av_cap"])
            cells.setdefault(key, {})[o["seed"]] = o
        t0 = {}
        binds = False
        for q in T0_Q:
            base = cells.get((q, None), {})
            for cap in T0_CAPS[1:]:
                arm = cells.get((q, cap), {})
                seeds = sorted(set(base) & set(arm))
                if not seeds:
                    continue
                a = [base[s]["outflow_vph"] for s in seeds]
                b = [arm[s]["outflow_vph"] for s in seeds]
                pm = paired_median_diff(a, b, seed=7110029)
                ref = float(np.median(a))
                lags = []
                for s in seeds:
                    mb = moving_outflow(base[s], 600.0, 1500.0)
                    ma = moving_outflow(arm[s], 600.0, 1500.0)
                    n = min(len(mb), len(ma))
                    rel = np.abs(ma[:n] - mb[:n]) / np.maximum(mb[:n], 1.0)
                    hit = np.nonzero(rel > 0.10)[0]
                    lags.append(float(hit[0] * base[s]["bin_s"]) if len(hit) else float("nan"))
                rel_eff = pm["median_diff"] / ref if ref else float("nan")
                cell_binds = abs(rel_eff) >= 0.05 and pm["excludes_0"]
                binds = binds or cell_binds
                t0[f"q{q}_cap{cap:g}"] = {"none_median": ref, "paired": pm, "rel_effect": round(rel_eff, 4),
                                          "binds": cell_binds,
                                          "lag_s_median": float(np.nanmedian(lags)) if np.isfinite(lags).any() else None,
                                          "lags_s": lags}
        h0 = {"PASS": 0, "WARN": 0, "FAIL": 0}
        for o in S0:
            h0[o["health"]["status"]] += 1
        res["t1_t0"] = {"cells": t0, "PASS": binds, "health": h0, "n_runs": len(S0)}
    # T3
    S3 = load_summaries(root, "t1_t3")
    if S3:
        orig = {(int(o["inflow_vph"]), o["seed"]): o["hash"] for o in load_summaries(root, "t1_sweep")}
        same = [(int(o["inflow_vph"]), o["seed"], o["hash"] == orig.get((int(o["inflow_vph"]), o["seed"])))
                for o in S3]
        res["t1_t3"] = {"pairs": same, "PASS": all(x[2] for x in same) and len(same) == 10}
    return res


def write_report(res: dict, root: Path, n_max: int) -> Path:
    p = REPO_ROOT / "docs" / "lab" / "t1_bn4_plant_checks.md"
    sw = res.get("t1_sweep", {})
    swl = res.get("t1_sweepL", {})
    t0 = res.get("t1_t0", {})
    t3 = res.get("t1_t3", {})
    L = ["# Track 1 (BN4), R1 plant checks: results", "",
         f"*{time.strftime('%Y-%m-%d %H:%M')} · protocol `docs/lab/t1_bn4_plant_checks_protocol.md` · "
         f"raw runs `{root}` · workers {n_max}*", ""]
    if sw:
        L += [f"## T1 capacity drop (lane changing off): **{'PASS' if sw['PASS'] else 'FAIL'}**", "",
              f"- {sw['n_runs']} runs; health {sw['health']}; runs with codes {sw['codes_runs']}; "
              f"teleports {sw['teleports_total']}.",
              f"- Peak median outflow **{sw['peak']:.0f} veh/h** at q = {sw['peak_q']}; mean median outflow at "
              f"q = 2,200–2,500 **{sw['high_mean']:.0f} veh/h**; ratio **{sw['high_over_peak']:.3f}** (PASS needs ≤ 0.95).",
              "", "| q (veh/h) | median outflow | min | max |", "|---|---|---|---|"]
        for q in sw["Q_median_by_q"]:
            L.append(f"| {q} | {sw['Q_median_by_q'][q]:.0f} | {sw['Q_min_by_q'][q]:.0f} | {sw['Q_max_by_q'][q]:.0f} |")
        L.append("")
    if swl:
        L += ["## T1-L (lane changing on; exploratory)", "",
              f"- {swl['n_runs']} runs; health {swl['health']}; teleports {swl['teleports_total']}; peak "
              f"{swl['peak']:.0f} veh/h at q = {swl['peak_q']}; high mean {swl['high_mean']:.0f}; ratio "
              f"{swl['high_over_peak']:.3f}.", ""]
    if t0:
        L += [f"## T0 actuator (AV cap): **{'PASS' if t0['PASS'] else 'FAIL'}**", "",
              f"- {t0['n_runs']} runs; health {t0['health']}.", "",
              "| cell | none median | median Δ (cap − none) | 95 % CI | rel. | binds | median lag (s) |",
              "|---|---|---|---|---|---|---|"]
        for k, c in t0["cells"].items():
            pm = c["paired"]
            L.append(f"| {k} | {c['none_median']:.0f} | {pm['median_diff']:+.0f} | [{pm['ci_lo']:+.0f}, "
                     f"{pm['ci_hi']:+.0f}] | {c['rel_effect']:+.1%} | {c['binds']} | {c['lag_s_median']} |")
        L.append("")
    if t3:
        L += [f"## T3 determinism: **{'PASS' if t3['PASS'] else 'FAIL'}**", "",
              f"- {sum(x[2] for x in t3['pairs'])}/{len(t3['pairs'])} identical hashes.", ""]
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(L) + "\n")
    return p


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--gate-ok", action="store_true")
    ap.add_argument("--analyse-only", action="store_true")
    ap.add_argument("--batch-root", default=None)
    a = ap.parse_args(argv)
    root = Path(a.batch_root) if a.batch_root else RUNS_ROOT / "t1" / f"r1_{int(time.time())}"
    if not a.analyse_only:
        jobs = [job_nc("t1_sweep", q, s, root) for q in Q_LEVELS for s in SWEEP_SEEDS]
        jobs += [job_nc("t1_sweepL", q, s, root, lc=True) for q in Q_LEVELS for s in SWEEP_SEEDS]
        jobs += [job_nc("t1_t0", q, s, root, cap=c, cap_t=600) for q in T0_Q for s in T0_SEEDS for c in T0_CAPS]
        rep = run_batch(jobs, root / "batch_main", max_workers=a.workers, gate_ok=a.gate_ok)
        print(json.dumps({k: v for k, v in rep.__dict__.items() if k != "results"}), flush=True)
        rng = random.Random(7110099)
        picks = rng.sample([(q, s) for q in Q_LEVELS for s in SWEEP_SEEDS], 10)
        rep3 = run_batch([job_nc("t1_t3", q, s, root) for q, s in picks], root / "batch_t3",
                         max_workers=a.workers, gate_ok=True)
        print(json.dumps({k: v for k, v in rep3.__dict__.items() if k != "results"}), flush=True)
    res = analyse(root)
    (root / "r1_analysis.json").write_text(json.dumps(res, indent=1, default=str))
    rp = write_report(res, root, a.workers)
    for tag in ("t1_sweep", "t1_sweepL", "t1_t0", "t1_t3"):
        if tag in res:
            r = res[tag]
            h = r.get("health", {"PASS": len(r.get("pairs", [])) if r.get("PASS") else 0})
            ledger.append("T1", "R1", "S", tag, {"protocol": "t1_bn4_plant_checks_protocol.md"},
                          {"t1_sweep": "7110010-7110019", "t1_sweepL": "7110010-7110019",
                           "t1_t0": "7110020-7110029", "t1_t3": "subset of 7110010-7110019"}[tag],
                          r.get("n_runs", len(r.get("pairs", []))), h,
                          {k: r[k] for k in ("PASS", "peak", "peak_q", "high_over_peak") if k in r},
                          notes=str(root))
    print(json.dumps({"report": str(rp), "T1": res.get("t1_sweep", {}).get("PASS"),
                      "T0": res.get("t1_t0", {}).get("PASS"), "T3": res.get("t1_t3", {}).get("PASS")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
