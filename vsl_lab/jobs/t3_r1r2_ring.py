"""Track 3 / R1 + R2 on RING22 per docs/lab/t3_ring_r1_r2_protocol.md.

python -m vsl_lab.jobs.t3_r1r2_ring --workers 10 --gate-ok
python -m vsl_lab.jobs.t3_r1r2_ring --analyse-only --batch-root DIR
"""
from __future__ import annotations

import argparse
import json
import random
import time
from pathlib import Path

import numpy as np
from scipy.optimize import brentq

from vsl_lab.config import N_MAX_DEFAULT, REPO_ROOT, RUNS_ROOT
from vsl_lab.eval.stats import paired_median_diff
from vsl_lab.ops import ledger
from vsl_lab.ops.scheduler import Job, run_batch
from vsl_lab.plants.ring import IDM, N_VEH, VEH_LEN

LS = [220, 230, 240, 250, 260, 270]
R1_SEEDS = list(range(7130010, 7130020))
R1_U = [3.0, 3.5, 4.0, 4.5, 5.0, 5.5]
R2_SEEDS = list(range(7130100, 7130120))
R2_U = [round(2.5 + 0.25 * i, 2) for i in range(19)]
R2_PI = [(vc, w) for vc in (0.5, 1.0, 1.5) for w in (20.0, 38.0, 60.0)]


def v_eq(L: float) -> float:
    gap = (L - N_VEH * VEH_LEN) / N_VEH
    f = lambda v: 1 - (v / IDM["v0"]) ** IDM["delta"] - ((IDM["s0"] + v * IDM["T"]) / gap) ** 2
    return brentq(f, 0.0, IDM["v0"])


def job(tag, L, s, ctrl, root, U=None, vc=None, w=None):
    argv = ["vsl_lab.jobs.ring_run", "--L", str(L), "--seed", str(s), "--ctrl", ctrl, "--tag", tag,
            "--out-root", str(root)]
    if U is not None:
        argv += ["--U", str(U)]
    if vc is not None:
        argv += ["--vcatch", str(vc), "--window", str(w)]
    return Job(jid=f"{tag}_L{L}_s{s}_{ctrl}_{U}_{vc}_{w}", argv=argv)


def load(root: Path, tag: str) -> list:
    out = []
    for p in (root / tag).glob("*/summary.json"):
        try:
            out.append(json.loads(p.read_text()))
        except Exception:
            pass
    return out


def key(o):
    if o["ctrl"] == "fs":
        return f"fs:{o['U']:g}"
    if o["ctrl"] == "pi":
        return f"pi:{o['vcatch']:g}:{o['window']:g}"
    return "nc"


def analyse(root: Path) -> dict:
    res = {"v_eq": {L: round(v_eq(L), 4) for L in LS}}
    S1 = load(root, "r1")
    if S1:
        by = {}
        for o in S1:
            by.setdefault((key(o), int(o["L_target"])), {})[o["seed"]] = o
        nc = [o for o in S1 if o["ctrl"] == "nc"]
        waves = [(o["mean_across_std"] >= 1.0 and o["stop_share"] >= 0.10) for o in nc]
        h = {"PASS": 0, "FAIL": 0}
        for o in S1:
            h[o["health"]] = h.get(o["health"], 0) + 1
        t1 = {"n_nc": len(nc), "share_with_waves": round(float(np.mean(waves)), 3),
              "PASS": bool(np.mean(waves) >= 0.9 and h.get("FAIL", 0) == 0), "health": h}
        cm = {}
        n_ok = 0
        for L in LS:
            base = by.get(("nc", L), {})
            best = None
            for k in [f"fs:{u:g}" for u in R1_U] + ["pi:1:38"]:
                arm = by.get((k, L), {})
                ss = sorted(set(base) & set(arm))
                if not ss:
                    continue
                pm = paired_median_diff([base[s]["mean_speed"] for s in ss], [arm[s]["mean_speed"] for s in ss],
                                        seed=7130019)
                ref = float(np.median([base[s]["mean_speed"] for s in ss]))
                rel = pm["median_diff"] / ref
                if best is None or rel > best["rel"]:
                    best = {"ctrl": k, "rel": round(rel, 4), "paired": pm,
                            "median_speed": float(np.median([arm[s]["mean_speed"] for s in ss])), "nc_median": ref}
            cm[L] = best
            if best and best["rel"] >= 0.05 and best["paired"]["excludes_0"]:
                n_ok += 1
        res["r1"] = {"T1": t1, "control_matters": {"per_L": cm, "n_L_ok": n_ok, "PASS": n_ok >= 4}}
        S3 = load(root, "r1t3")
        if S3:
            orig = {(int(o["L_target"]), o["seed"]): o["hash"] for o in nc}
            same = [o["hash"] == orig.get((int(o["L_target"]), o["seed"])) for o in S3]
            res["r1"]["T3"] = {"n": len(same), "PASS": all(same) and len(same) == 6}
    S2 = load(root, "r2")
    if S2:
        by = {}
        for o in S2:
            by.setdefault(key(o), {}).setdefault(int(o["L_target"]), []).append(o["mean_speed"])
        table = {}
        for k, d in by.items():
            row = {L: float(np.median(v)) for L, v in d.items()}
            row["score"] = float(np.mean([row[L] for L in LS if L in row]))
            row["share_of_v_eq"] = float(np.mean([row[L] / v_eq(L) for L in LS if L in row]))
            table[k] = row
        fams = {"nc": ["nc"], "fs": [k for k in table if k.startswith("fs:")], "pi": [k for k in table if k.startswith("pi:")]}
        tuned = {f: max(ks, key=lambda k: table[k]["score"]) for f, ks in fams.items() if ks}
        per_L_best_fs = {L: max(fams["fs"], key=lambda k: table[k].get(L, -1)) for L in LS} if fams["fs"] else {}
        h2 = {"PASS": 0, "FAIL": 0}
        for o in S2:
            h2[o["health"]] = h2.get(o["health"], 0) + 1
        res["r2"] = {"n_runs": len(S2), "health": h2, "table": table,
                     "tuned": {f: {"ctrl": k, "score": table[k]["score"], "share_of_v_eq": table[k]["share_of_v_eq"]}
                               for f, k in tuned.items()},
                     "per_L_best_fs": per_L_best_fs}
    return res


def write(res: dict, root: Path) -> None:
    L_ = ["# Track 3 (RING22), R1 plant checks and R2 tuned baselines: results", "",
          f"*{time.strftime('%Y-%m-%d %H:%M')} · protocol `docs/lab/t3_ring_r1_r2_protocol.md` · raw `{root}`*", "",
          f"IDM equilibrium speed v_e(L) (uniform-flow ceiling): {res['v_eq']}", ""]
    if "r1" in res:
        r1 = res["r1"]
        L_ += [f"## R1 T1-ring (waves): **{'PASS' if r1['T1']['PASS'] else 'FAIL'}**: share of NC runs with waves "
               f"{r1['T1']['share_with_waves']} (need >= 0.9); health {r1['T1']['health']}", "",
               f"## R1 control matters: **{'PASS' if r1['control_matters']['PASS'] else 'FAIL'}** "
               f"({r1['control_matters']['n_L_ok']}/6 lengths)", "",
               "| L | NC median speed | best controller | its median speed | rel. gain | 95 % CI (m/s) |",
               "|---|---|---|---|---|---|"]
        for L, b in r1["control_matters"]["per_L"].items():
            if b:
                L_.append(f"| {L} | {b['nc_median']:.3f} | {b['ctrl']} | {b['median_speed']:.3f} | {b['rel']:+.1%} | "
                          f"[{b['paired']['ci_lo']:+.3f}, {b['paired']['ci_hi']:+.3f}] |")
        if "T3" in r1:
            L_ += ["", f"## R1 T3 determinism: **{'PASS' if r1['T3']['PASS'] else 'FAIL'}** ({r1['T3']['n']} re-runs)"]
    if "r2" in res:
        r2 = res["r2"]
        L_ += ["", f"## R2 tuned baselines (frozen) · {r2['n_runs']} runs · health {r2['health']}", ""]
        for f, t in r2["tuned"].items():
            L_.append(f"- **{f}**: `{t['ctrl']}`: score {t['score']:.3f} m/s = {t['share_of_v_eq']:.1%} of v_e")
        L_ += ["", f"- Per-L best FollowerStopper U (informed reference I): {r2['per_L_best_fs']}", "",
               "| controller | " + " | ".join(f"L={L}" for L in LS) + " | score | share of v_e |",
               "|---|" + "---|" * (len(LS) + 2)]
        for k in sorted(r2["table"], key=lambda k: -r2["table"][k]["score"])[:12]:
            r = r2["table"][k]
            L_.append(f"| {k} | " + " | ".join(f"{r.get(L, float('nan')):.3f}" for L in LS) +
                      f" | {r['score']:.3f} | {r['share_of_v_eq']:.1%} |")
        frozen = {"protocol": "docs/lab/t3_ring_r1_r2_protocol.md", "frozen_at": time.strftime("%Y-%m-%d %H:%M"),
                  "tuned": r2["tuned"], "per_L_best_fs": r2["per_L_best_fs"], "v_eq": res["v_eq"], "raw_root": str(root)}
        (REPO_ROOT / "docs" / "lab" / "t3_ring_baselines_frozen.json").write_text(json.dumps(frozen, indent=1))
    (REPO_ROOT / "docs" / "lab" / "t3_ring_r1_r2.md").write_text("\n".join(L_) + "\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=N_MAX_DEFAULT)
    ap.add_argument("--gate-ok", action="store_true")
    ap.add_argument("--analyse-only", action="store_true")
    ap.add_argument("--batch-root", default=None)
    a = ap.parse_args(argv)
    root = Path(a.batch_root) if a.batch_root else RUNS_ROOT / "t3" / f"r1r2_{int(time.time())}"
    if not a.analyse_only:
        jobs = [job("r1", L, s, "nc", root) for L in LS for s in R1_SEEDS]
        jobs += [job("r1", L, s, "fs", root, U=u) for L in LS for s in R1_SEEDS for u in R1_U]
        jobs += [job("r1", L, s, "pi", root, vc=1.0, w=38.0) for L in LS for s in R1_SEEDS]
        jobs += [job("r2", L, s, "nc", root) for L in LS for s in R2_SEEDS]
        jobs += [job("r2", L, s, "fs", root, U=u) for L in LS for s in R2_SEEDS for u in R2_U]
        jobs += [job("r2", L, s, "pi", root, vc=vc, w=w) for L in LS for s in R2_SEEDS for vc, w in R2_PI]
        rep = run_batch(jobs, root / "batch", max_workers=a.workers, gate_ok=a.gate_ok)
        print(json.dumps({k: v for k, v in rep.__dict__.items() if k != "results"}), flush=True)
        picks = random.Random(7130099).sample([(L, s) for L in LS for s in R1_SEEDS], 6)
        rep3 = run_batch([job("r1t3", L, s, "nc", root) for L, s in picks], root / "batch_t3",
                         max_workers=a.workers, gate_ok=True)
    res = analyse(root)
    (root / "analysis.json").write_text(json.dumps(res, indent=1, default=str))
    write(res, root)
    for ph in ("r1", "r2"):
        if ph in res:
            ledger.append("T3", ph.upper(), "S", f"ring_{ph}", {"protocol": "t3_ring_r1_r2_protocol.md"},
                          {"r1": "7130010-7130019", "r2": "7130100-7130119"}[ph],
                          res[ph].get("n_runs", 0) or len(load(root, ph)),
                          res[ph].get("health", res[ph].get("T1", {}).get("health", {})),
                          {k: v for k, v in res[ph].items() if k in ("tuned", "control_matters", "T1", "T3")},
                          notes=str(root))
    print(json.dumps({"r1": {k: res.get("r1", {}).get(k, {}).get("PASS") for k in ("T1", "control_matters", "T3")},
                      "r2_tuned": res.get("r2", {}).get("tuned")}, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
