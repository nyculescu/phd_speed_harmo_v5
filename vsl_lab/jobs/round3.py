"""Round 3 tool checks (docs/lab/round3_tm21_protocol.md): TM21 CAV speed commands vs TM20 posted VSL on MRG3-v3
with the realism gate's primary human variant, at its selected cell.

python -m vsl_lab.jobs.round3 tcav0 --gate-ok   # CAV sanity: NC-p at 10/25/50 % (+ ACC at 50 %), seeds 7,150,000-009
python -m vsl_lab.jobs.round3 tx --gate-ok      # step interval X by safety (p = 50 %, stress schedule), seeds 7,150,070-089
python -m vsl_lab.jobs.round3 t0 --gate-ok      # CAV commands / posted VSL with enforcers bind, seeds 7,150,010-039
python -m vsl_lab.jobs.round3 t1c --gate-ok     # control matters (p passing T0-C) + T3 determinism, seeds 7,150,040-069
NC-p = CAVs present, no command (arm C machinery with ctrl nc: CAVs follow the lane limit exactly).
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import time
from pathlib import Path

import numpy as np

from vsl_lab.config import N_MAX_DEFAULT, REPO_ROOT, RUNS_ROOT
from vsl_lab.eval.stats import paired_median_diff
from vsl_lab.ops import ledger
from vsl_lab.ops.scheduler import Job, run_batch

PS = [0.10, 0.25, 0.50]
TCAV0_SEEDS = list(range(7150000, 7150010))
T0_SEEDS = {0.10: list(range(7150010, 7150020)), 0.25: list(range(7150020, 7150030)), 0.50: list(range(7150030, 7150040))}
T1C_SEEDS = list(range(7150040, 7150070))
TX_SEEDS = list(range(7150070, 7150090))
X_GRID = [0.5, 1.0, 2.0]
T1C_CTRLS = ["cavconst:0.6", "cavconst:0.8", "cavmtfc:20:38:9:0.0015", "cavmtfc:25:38:9:0.0015", "cavmtfc:32:38:9:0.0015"]
STATE = REPO_ROOT / "docs" / "lab" / "round3_state.json"
STEP = 0.2       # author decision 2026-10-02 (Round 3 Addendum A)
ROUTE_KM = {"main": 5.25, "ramp": 1.53}          # approx. route lengths (veh-km normalisation)


def plant() -> tuple:
    v = json.loads((REPO_ROOT / f"docs/lab/t2_realism_verdict_step{STEP:g}.json").read_text())
    drv = v["primary"]
    if drv is None:
        raise SystemExit("no realism-gate variant passed: Round 3 does not run (protocol)")
    return drv, v["variants"][drv]["cell"]


def job(tag, ctrl, s, p, arm, drv, cell, root, model="CACC", x=1.0) -> Job:
    m, r = cell.split("/")
    return Job(jid=f"{tag}_{ctrl.replace(':', '_')}_p{p:g}{arm}{model}x{x:g}_s{s}",
               argv=["vsl_lab.jobs.mrg3_run", "--ctrl", ctrl, "--seed", str(s), "--main-peak", m, "--ramp-peak", r,
                     "--tag", tag, "--out-root", str(root), "--plant", "v3", "--driver", drv, "--cav-share", str(p),
                     "--cav-arm", arm, "--cav-model", model, "--cav-x", str(x), "--step", str(STEP)])


def load(root: Path, tag: str) -> list:
    out = []
    for p in (root / tag).glob("*/summary.json"):
        o = json.loads(p.read_text())
        o["_dir"] = str(p.parent)
        out.append(o)
    return out


def key(o) -> tuple:
    return (o["ctrl"], round(o["cav_share"], 2), o["cav_arm"], o["cav_model"], float(o["cav_x"]))


def by_key(rows) -> dict:
    d = {}
    for o in rows:
        d.setdefault(key(o), {})[o["seed"]] = o
    return d


def eb_rate(o) -> float:
    vkm = (o.get("n_main") or 0) * ROUTE_KM["main"] + (o.get("n_ramp") or 0) * ROUTE_KM["ramp"]
    return 1000.0 * float(o.get("emergency_braking") or 0) / max(vkm, 1e-9)


def up0a_q(o) -> float:
    rows = list(csv.DictReader(open(Path(o["_dir"]) / "features.csv")))
    v = [float(r["up0a_q"]) for r in rows if 1500.0 <= float(r["t"]) < 2700.0]
    return float(np.mean(v)) if v else float("nan")


def paired(a: dict, b: dict, f, seed: int) -> dict:
    ss = sorted(set(a) & set(b))
    pm = paired_median_diff([f(a[s]) for s in ss], [f(b[s]) for s in ss], seed=seed)
    pm["rel"] = pm["median_diff"] / float(np.median([f(a[s]) for s in ss])) if ss else None
    pm["n"] = len(ss)
    return pm


def state() -> dict:
    return json.loads(STATE.read_text()) if STATE.exists() else {}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["tcav0", "tx", "t0", "t1c"])
    ap.add_argument("--workers", type=int, default=N_MAX_DEFAULT)
    ap.add_argument("--gate-ok", action="store_true")
    a = ap.parse_args(argv)
    drv, cell = plant()
    st = state()
    root = RUNS_ROOT / "t2" / f"round3_{a.what}_{int(time.time())}"
    res = {"driver": drv, "cell": cell, "raw": str(root)}
    if a.what == "tcav0":
        jobs = [job("tcav0", "nc", s, p, "C", drv, cell, root) for p in PS for s in TCAV0_SEEDS]
        jobs += [job("tcav0", "nc", s, 0.50, "C", drv, cell, root, model="ACC") for s in TCAV0_SEEDS]
        run_batch(jobs, root / "batch", a.workers, gate_ok=a.gate_ok)
        rows = load(root, "tcav0")
        per = {}
        for o in rows:
            k = f"{o['cav_share']:g}_{o['cav_model']}"
            d = per.setdefault(k, {"n": 0, "collisions": 0, "fail": 0, "teleports": 0, "eb_rate": [], "cav": [], "hum": []})
            d["n"] += 1; d["collisions"] += o["collisions"]; d["teleports"] += o["teleports"]
            d["fail"] += o["health"]["status"] == "FAIL"; d["eb_rate"].append(eb_rate(o))
            d["cav"].append(o.get("eb_cav_per_1000vkm") or 0.0); d["hum"].append(o.get("eb_human_per_1000vkm") or 0.0)
        for d in per.values():   # Addendum A: CAV vs human emergency-braking rates (reported)
            d["eb_rate_median"] = float(np.median(d.pop("eb_rate")))
            d["eb_cav_per_1000vkm_median"] = float(np.median(d.pop("cav")))
            d["eb_human_per_1000vkm_median"] = float(np.median(d.pop("hum")))
        bk = by_key(rows)
        cacc, acc = bk.get(("nc", 0.5, "C", "CACC", 1.0), {}), bk.get(("nc", 0.5, "C", "ACC", 1.0), {})
        same = [cacc[s]["hash"] == acc[s]["hash"] for s in set(cacc) & set(acc)]
        res.update(per_p=per, cacc_equals_acc=f"{sum(same)}/{len(same)} identical",
                   PASS=all(d["collisions"] == 0 and d["fail"] == 0 for d in per.values()))
        st["tcav0"] = {"PASS": res["PASS"]}
    elif a.what == "tx":
        if not st.get("tcav0", {}).get("PASS"):
            raise SystemExit("T-CAV0 has not passed: stop and report to the author (protocol)")
        jobs = [job("tx", "nc", s, 0.50, "C", drv, cell, root) for s in TX_SEEDS]
        jobs += [job("tx", "cavstress", s, 0.50, "C", drv, cell, root, x=x) for x in X_GRID for s in TX_SEEDS]
        run_batch(jobs, root / "batch", a.workers, gate_ok=a.gate_ok)
        bk = by_key(load(root, "tx"))
        base = bk.get(("nc", 0.5, "C", "CACC", 1.0), {})
        base_med = float(np.median([eb_rate(o) for o in base.values()])) if base else float("nan")
        per, chosen = {}, None
        for x in X_GRID:
            arm = bk.get(("cavstress", 0.5, "C", "CACC", x), {})
            pm = paired(base, arm, eb_rate, 7150089)
            col = sum(o["collisions"] for o in arm.values()); fail = sum(o["health"]["status"] == "FAIL" for o in arm.values())
            ok = col == 0 and fail == 0 and pm["median_diff"] <= 0.10 * base_med
            per[str(x)] = {"collisions": col, "fail": fail, "eb_paired": pm, "PASS": bool(ok),
                           "cav_steps_median": float(np.median([o["cav_steps"] for o in arm.values()])) if arm else None,
                           "max_excess_ms_median": float(np.median([o["cav_max_excess_ms"] for o in arm.values()])) if arm else None}
            if ok and chosen is None:
                chosen = x
        res.update(nc_eb_rate_median=base_med, per_x=per, X=chosen, PASS=chosen is not None)
        st["X"] = chosen
    elif a.what == "t0":
        x = st.get("X")
        if x is None:
            raise SystemExit("no X selected by T-X: stop and report to the author (protocol)")
        jobs = []
        for p in PS:
            for s in T0_SEEDS[p]:
                jobs += [job("t0", "nc", s, p, "C", drv, cell, root, x=x), job("t0", "cavconst:0.4", s, p, "C", drv, cell, root, x=x),
                         job("t0", "const:0.4", s, p, "B", drv, cell, root, x=x)]
        run_batch(jobs, root / "batch", a.workers, gate_ok=a.gate_ok)
        bk = by_key(load(root, "t0"))
        per = {}
        for p in PS:
            nc = bk.get(("nc", round(p, 2), "C", "CACC", x), {})
            c = paired(nc, bk.get(("cavconst:0.4", round(p, 2), "C", "CACC", x), {}), up0a_q, 7150039)
            b = paired(nc, bk.get(("const:0.4", round(p, 2), "B", "CACC", x), {}), up0a_q, 7150039)
            per[f"{p:g}"] = {"C": c | {"PASS": bool(c["rel"] is not None and c["rel"] <= -0.10 and c["excludes_0"])},
                             "B": b | {"PASS": bool(b["rel"] is not None and b["rel"] <= -0.10 and b["excludes_0"])}}
        res.update(per_p=per)
        st["t0_C_pass"] = [p for p in PS if per[f"{p:g}"]["C"]["PASS"]]
    else:
        x = st.get("X")
        ps = st.get("t0_C_pass", [])
        if x is None or not ps:
            raise SystemExit("no X or no p passed T0-C: arm C is killed at T0 (protocol); nothing to run")
        jobs = [job("t1c", c, s, p, "C", drv, cell, root, x=x) for p in ps for s in T1C_SEEDS for c in ["nc"] + T1C_CTRLS]
        run_batch(jobs, root / "batch", a.workers, gate_ok=a.gate_ok)
        picks = random.Random(7150069).sample(T1C_SEEDS, 5)
        if 0.25 in ps:
            run_batch([job("t3", "nc", s, 0.25, "C", drv, cell, root, x=x) for s in picks], root / "batch_t3", a.workers,
                      gate_ok=True)
        bk = by_key(load(root, "t1c"))
        per = {}
        for p in ps:
            nc = bk.get(("nc", round(p, 2), "C", "CACC", x), {})
            cm = {}
            for c in T1C_CTRLS:
                pm = paired(nc, bk.get((c, round(p, 2), "C", "CACC", x), {}), lambda o: o["mean_time_in_system_s"], 7150069)
                cm[c] = pm | {"ok": bool(pm["rel"] is not None and pm["rel"] <= -0.05 and pm["excludes_0"])}
            per[f"{p:g}"] = {"per_ctrl": cm, "PASS": any(v["ok"] for v in cm.values())}
        t3 = by_key(load(root, "t3")).get(("nc", 0.25, "C", "CACC", x), {})
        nc25 = bk.get(("nc", 0.25, "C", "CACC", x), {})
        res.update(per_p=per, T3={"n": len(t3), "PASS": bool(t3) and all(t3[s]["hash"] == nc25[s]["hash"] for s in t3)})
    STATE.write_text(json.dumps(st, indent=1))
    (root / "analysis.json").write_text(json.dumps(res, indent=1, default=str))
    out_md = REPO_ROOT / "docs" / "lab" / "round3_results.md"
    head = "# Round 3 (TM21 vs TM20): tool-check results\n\nProtocol: `docs/lab/round3_tm21_protocol.md`.\n"
    prev = out_md.read_text() if out_md.exists() else head
    prev += f"\n## {a.what} ({time.strftime('%Y-%m-%d %H:%M')}, variant {drv}, cell {cell})\n\n```json\n" \
            f"{json.dumps({k: v for k, v in res.items() if k != 'raw'}, indent=1, default=str)[:6000]}\n```\n\nRaw: `{root}`\n"
    out_md.write_text(prev)
    ledger.append("T2", f"R3-{a.what}", "S", f"round3_{a.what}", {"driver": drv, "cell": cell}, "see protocol",
                  sum(1 for _ in root.rglob("summary.json")), {}, {k: res.get(k) for k in ("PASS", "X") if k in res},
                  notes=str(root))
    print(json.dumps({k: res.get(k) for k in ("PASS", "X", "cacc_equals_acc") if k in res}, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
