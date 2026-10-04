"""Lead 1 stage H (docs/lab/t1_meter2_protocol.md, Addendum A): headroom gate against tuned non-learning control.

python -m vsl_lab.jobs.t1_meter2_h tune --gate-ok   # H1 evsched2 tuning (7,170,100-119) + MPC-F2 data (7,170,120-219)
python -m vsl_lab.jobs.t1_meter2_h fit              # freeze docs/lab/t1_mpcf2_model.pt
python -m vsl_lab.jobs.t1_meter2_h gate --gate-ok   # H2 on gate seeds 7,170,220-239 (run once)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import numpy as np

from vsl_lab.config import N_MAX_DEFAULT, REPO_ROOT, RUNS_ROOT
from vsl_lab.jobs.t1_meter2_scan import COND as _COND22
from vsl_lab.ops import ledger
from vsl_lab.ops.scheduler import Job, run_batch

Q = 1600
LAB = REPO_ROOT / "docs/lab"
LOOKUP = LAB / "t1_meter2_lookup.json"
LOOKUP_SHA = "abd3b253151a76bd4e8690a88f77ae1551d2daf280b4353377fd766f73d2c440"
COND = {c: pk for c, pk in _COND22.items() if c != "block_d360"}   # Addendum A: teleport artefact condition excluded
TUNE_SEEDS = list(range(7170100, 7170120))
MPCF_SEEDS = (7170120, 7170219)
GATE_SEEDS = list(range(7170220, 7170240))
EV_GRID = [(v, t, f) for v in (5, 7, 9) for t in (10, 20, 40) for f in (1.15, 1.25, 1.35)]
A6_ON = ["10:8", "40:8", "20:12", "5:10", "10:12"]
MPCF2_GRID = ["off"] + A6_ON          # env action order with allow_off: 0 = meter off, k = A6_ON[k-1]
MPCF2_ENV = {"actuator": "meter_sched", "meter_grid": A6_ON, "allow_off": True, "decision_s": 30.0}
MPCF2_MODEL = LAB / "t1_mpcf2_model.pt"
MPCF_OLD_SHA = "415ea0510523c2816718f0123e6a4a3f56a233a50c38639aa7f1658efc0b8224"
SPEC = LAB / "t1_mpcf2_spec.json"
NONLEARN = ["nc", "pooled", "evsched2", "mpcf2", "evsched_old", "mpcf_old"]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def ev_ctrl(v, t, f) -> str:
    return f"evsched:{v}:{t}:{f}:t1_meter2_lookup.json"


def job(jid: str, ctrl: str, seed: int, tag: str, root: Path, ek: dict) -> Job:
    return Job(jid=jid, argv=["vsl_lab.jobs.bn4_eval", "--ctrl", ctrl, "--inflow", str(Q), "--seed", str(seed), "--tag", tag,
                              "--out-root", str(root), "--env-kwargs", json.dumps(ek)])


def write_spec() -> None:
    spec = {"grid": MPCF2_GRID, "conds": COND, "seeds": list(MPCF_SEEDS), "q": float(Q),
            "data_root": str(RUNS_ROOT / "t1" / "mpcf2_data"), "model": str(MPCF2_MODEL.relative_to(REPO_ROOT)),
            "fit_report": "t1_mpcf2_fit.json"}
    SPEC.write_text(json.dumps(spec, indent=1))


def load(root: Path) -> dict:
    """{arm: {cond: {seed: record}}} from tag dirs named '<arm>__<cond>'."""
    d: dict = {}
    for p in root.glob("*__*/*.json"):
        arm, c = p.parent.name.split("__")
        o = json.loads(p.read_text())
        d.setdefault(arm, {}).setdefault(c, {})[o["seed"]] = o
    return d


def tune(a) -> int:
    assert sha(LOOKUP) == LOOKUP_SHA, "frozen lookup changed"
    write_spec()
    root = RUNS_ROOT / "t1" / f"m2h1_{int(time.time())}"
    spec = json.loads(SPEC.read_text())
    jobs = [Job(jid=f"mpcf2_{c}_{s}", argv=["vsl_lab.jobs.mpcf", "gen", "--seed", str(s), "--cond", c, "--reps", "2",
                                            "--spec", str(SPEC)])
            for s in range(MPCF_SEEDS[0], MPCF_SEEDS[1] + 1) for c in spec["conds"]]   # longer jobs first
    for (v, t, f) in EV_GRID:
        arm = f"ev{v}-{t}-{f}"
        for c, pk in COND.items():
            for s in TUNE_SEEDS:
                jobs.append(job(f"h1_{arm}_{c}_s{s}", ev_ctrl(v, t, f), s, f"{arm}__{c}", root, {"perturb": pk} if pk else {}))
    run_batch(jobs, root / "batch", a.workers, gate_ok=a.gate_ok)
    d = load(root)
    score = {}
    for arm, per in d.items():
        if all(len(per.get(c, {})) == len(TUNE_SEEDS) for c in COND):
            score[arm] = float(np.mean([np.median([o["mean_time_in_system_s"] for o in per[c].values()]) for c in COND]))
    best = min(score, key=score.get)
    v, t, f = best[2:].split("-")
    fails = {arm: sum(o.get("health") == "FAIL" for per in d[arm].values() for o in per.values()) for arm in d}
    res = {"chosen": ev_ctrl(v, t, f), "score_mean_of_median_J": score, "complete_arms": len(score), "fails": fails,
           "seeds": f"{TUNE_SEEDS[0]}-{TUNE_SEEDS[-1]}", "raw": str(root), "lookup_sha256": LOOKUP_SHA}
    (LAB / "t1_meter2_evsched2.json").write_text(json.dumps(res, indent=1))
    n_mp = len(list(Path(spec["data_root"]).glob("*.npz")))
    ledger.append("T1", "M2-H1", "S", "t1_meter2_h_tune", {"ev_grid": len(EV_GRID), "conds": len(COND)},
                  f"{TUNE_SEEDS[0]}-{TUNE_SEEDS[-1]} (H1), {MPCF_SEEDS[0]}-{MPCF_SEEDS[1]} (MPC-F2 data)", len(jobs), {},
                  {"evsched2": res["chosen"], "score": round(score[best], 2), "mpcf2_npz": n_mp}, notes=str(root))
    print(json.dumps({"evsched2": res["chosen"], "score": round(score[best], 2), "complete_arms": len(score),
                      "mpcf2_npz": n_mp}))
    return 0


def fit(a) -> int:
    from vsl_lab.jobs import mpcf
    write_spec()
    return mpcf.main(["fit", "--spec", str(SPEC)])


def gate(a) -> int:
    assert sha(LOOKUP) == LOOKUP_SHA, "frozen lookup changed"
    assert sha(LAB / "t1_mpcf_model.pt") == MPCF_OLD_SHA, "R6 MPC-F changed"
    marker = LAB / "t1_meter2_h.json"
    assert not marker.exists(), "stage H gate already ran: it is run once"
    lk = json.loads(LOOKUP.read_text())
    ev2 = json.loads((LAB / "t1_meter2_evsched2.json").read_text())["chosen"]
    mp2_sha = sha(MPCF2_MODEL)
    fam = lk["lookup"][str(Q)]["per_kind"]
    root = RUNS_ROOT / "t1" / f"m2h2_{int(time.time())}"
    jobs = []
    for c, pk in COND.items():
        base = {"perturb": pk} if pk else {}
        arms = [("nc", "nc", base), ("pooled", lk["lookup"][str(Q)]["pooled_best"], base), ("evsched2", ev2, base),
                ("mpcf2", f"mpcf:{MPCF2_MODEL}", dict(base, **MPCF2_ENV)), ("evsched_old", "evsched:7:20:1.15", base),
                ("mpcf_old", "mpcf", base), ("I", lk["lookup_I_per_condition"][c], base),
                ("IA6", lk["lookup_I_A6_per_condition"][c], base), ("family", fam[c.split("_")[0]], base)]
        for s in GATE_SEEDS:
            for arm, ctl, ek in arms:
                jobs.append(job(f"h2_{arm}_{c}_s{s}", ctl, s, f"{arm}__{c}", root, ek))
    run_batch(jobs, root / "batch", a.workers, gate_ok=a.gate_ok)
    d = load(root)
    J = {arm: {s: float(np.mean([per[c][s]["mean_time_in_system_s"] for c in COND]))
               for s in GATE_SEEDS if all(s in per.get(c, {}) for c in COND)} for arm, per in d.items()}
    served = {arm: float(np.median([np.mean([per[c][s]["served_ctrl_end"] for c in COND]) for s in J[arm]]))
              for arm, per in d.items()}
    fails = {arm: sum(o.get("health") == "FAIL" for per in d[arm].values() for o in per.values()) for arm in d}
    rng = np.random.default_rng(7170239)

    def paired(x: dict, y: dict, n=10000):   # x - y; rel to median of x (the non-learning reference)
        ss = sorted(set(x) & set(y))
        diff = np.array([x[s] - y[s] for s in ss])
        b = [np.median(rng.choice(diff, len(diff))) for _ in range(n)]
        return {"median_diff_s": float(np.median(diff)), "ci95": [float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))],
                "rel": float(np.median(diff) / np.median([x[s] for s in ss])), "n": len(ss)}

    med = {arm: float(np.median(list(v.values()))) for arm, v in J.items()}
    B = min(NONLEARN, key=lambda k: med[k])
    H = paired(J[B], J["I"])
    H_A6 = paired(J[B], J["IA6"])
    go = bool(H["rel"] >= 0.10 and H["ci95"][0] > 0)
    per_fam = {}
    for f in ("none", "slow", "block", "surge"):
        cs = [c for c in COND if c.split("_")[0] == f]
        Jf = {arm: {s: float(np.mean([d[arm][c][s]["mean_time_in_system_s"] for c in cs])) for s in J[arm]} for arm in d}
        per_fam[f] = {"best_nonlearning": min(NONLEARN, key=lambda k: np.median(list(Jf[k].values()))),
                      "H_vs_B": paired(Jf[B], Jf["I"], 5000)}
    res = {"lookup_sha256": LOOKUP_SHA, "mpcf2_sha256": mp2_sha, "evsched2": ev2, "median_J": med, "served_median": served,
           "B": B, "H": H, "H_A6_secondary": H_A6, "GO": go, "per_family": per_fam, "fails": fails, "raw": str(root),
           "vs_B_all": {arm: paired(J[B], J[arm]) for arm in J if arm != B}}
    marker.write_text(json.dumps(res, indent=1))
    L = ["# Lead 1 stage H: headroom gate against tuned non-learning control", "",
         f"*{time.strftime('%Y-%m-%d %H:%M')} · protocol `docs/lab/t1_meter2_protocol.md` Addendum A · gate seeds "
         f"{GATE_SEEDS[0]}-{GATE_SEEDS[-1]} × {len(COND)} conditions · q = {Q} · raw `{root}`*", "",
         f"**Pre-registered rule - H = (best non-learning − I) / best non-learning ≥ 10 % with the paired 95 % CI lower bound "
         f"> 0 → DRL stage: {'GO' if go else 'KILL'}**", "",
         f"Best non-learning B = `{B}`. H = {H['rel']:+.1%} (median paired Δ {H['median_diff_s']:+.1f} s, 95 % CI "
         f"[{H['ci95'][0]:+.1f}, {H['ci95'][1]:+.1f}] s). Secondary (oracle restricted to A6): H_A6 = {H_A6['rel']:+.1%} "
         f"[{H_A6['ci95'][0]:+.1f}, {H_A6['ci95'][1]:+.1f}] s.", "",
         "| arm | median J (s) | median served (veh) | FAIL runs | B − arm (s) [95 % CI] |", "|---|---|---|---|---|"]
    for arm in sorted(med, key=med.get):
        v = res["vs_B_all"].get(arm)
        cell = "—" if v is None else f"{v['median_diff_s']:+.1f} [{v['ci95'][0]:+.1f}, {v['ci95'][1]:+.1f}]"
        L.append(f"| {arm} | {med[arm]:.1f} | {served[arm]:.0f} | {fails.get(arm, 0)} | {cell} |")
    L += ["", "Per family (B fixed as above; informative only):", "", "| family | best non-learning in family | H vs B [95 % CI] |",
          "|---|---|---|"]
    for f, v in per_fam.items():
        h = v["H_vs_B"]
        L.append(f"| {f} | {v['best_nonlearning']} | {h['rel']:+.1%} [{h['ci95'][0]:+.1f}, {h['ci95'][1]:+.1f}] s |")
    L += ["", f"evsched2 = `{ev2}` (tuned on {TUNE_SEEDS[0]}-{TUNE_SEEDS[-1]}); MPC-F2 sha256 {mp2_sha[:12]}…; "
          f"lookup sha256 {LOOKUP_SHA[:12]}…"]
    (LAB / "t1_meter2_h.md").write_text("\n".join(L) + "\n")
    ledger.append("T1", "M2-H2", "G", "t1_meter2_h_gate", {"B": B, "evsched2": ev2, "mpcf2_sha256": mp2_sha},
                  f"{GATE_SEEDS[0]}-{GATE_SEEDS[-1]}", len(jobs), fails, {"H": round(H["rel"], 4), "ci95": H["ci95"], "GO": go},
                  notes=str(root))
    print(json.dumps({"GO": go, "B": B, "H": round(H["rel"], 4), "ci95": H["ci95"], "median_J": med}))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["tune", "fit", "gate"])
    ap.add_argument("--workers", type=int, default=N_MAX_DEFAULT)
    ap.add_argument("--gate-ok", action="store_true")
    a = ap.parse_args(argv)
    return {"tune": tune, "fit": fit, "gate": gate}[a.what](a)


if __name__ == "__main__":
    raise SystemExit(main())
