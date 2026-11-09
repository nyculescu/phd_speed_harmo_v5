"""Plan B S1 (planb.md §7.2, V480): smoke, identity and determinism, criteria fixed before they run. Laptop, by day. It prints pass or
fail per check and never a performance field.

C1   V475's 7 stored acceptance rows reproduce on every round 2 key at this commit (measure2.py smoke).
C1b  S on 7,480,000-002 for no control, p333, lr400_13_2, a4400_10_1, z33133, copy, os1_15_10, 3E-T and one v3w learner, plus the
     placebo with no control on 7,480,000: run at the base commit (79b889b, unchanged) and at this commit; every key equal.
C2   T3: in S, SURGE and TRUCK, no control, p333, one learner, 3E-T, ASCH and MPC-F on 7,480,000, twice, pack on; every key equal.
     ASCH and MPC-F are not tuned yet, so placeholders run here (ASCH: steady p333, R_dist 3E-T, 55 km/h, 30 s, 15 km/h; MPC-F:
     data mode over p333 and 3E-T, and control mode with a fixed random model, the path S6 runs with the pack on); the tuned ones
     repeat this in S5 on the S6 machine.
C3   TRUCK: the capped truck ids and departure times are identical across arms on each seed (7,480,000-002), and no capped truck
     exceeds 40 km/h. Every row: no planned vehicle dropped (PR-03, `m_dropped` = 0), and the period labels of plant_sweep's
     ttc3_p_* keys are the cell's own (S: rest; SURGE: before, surge, post; TRUCK: before, trucks).
C4   Per-minute series equal S on the same seed and arm: SURGE until 600 s, TRUCK until the first capped truck departs.
C5   Pack-on rows equal pack-off rows on every non-pack key (SURGE and TRUCK; no control, p333, one learner); no counter calls
     CavEnv._x; the pack's own sums agree (close-following by road = its total; braking events in the side file = the events count);
     PR-24: traced runs (pr24.py) of no control, p333 and one learner in S, SURGE and TRUCK on 7,480,000 recount equal to their rows
     and equal the untraced C2 rows on every key (V386).

Run from a clean, detached worktree at the run commit into a new, empty --out; s1.json records the commit.
usage: s1.py --out DIR --base ROOT_AT_79b889b [--workers N]"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pb  # noqa: E402

HERE = Path(__file__).resolve().parent
PY = sys.executable
BASE_COMMIT = "79b889b"
SMOKE = pb.seeds(7_480_000, 7_480_002)
C1B_ARMS = ("nc", "p333", "lr400_13_2", "a4400_10_1", "z33133", "copy", "os1_15_10", "3e", "w0u250")
CAP = 40.0 / 3.6
SKIP = {"cfg", "m_st_file"}


def placeholder_model(path: Path) -> str:
    """A fixed random MPC-F model over two actions, so C2 runs control mode; returns its SHA-256."""
    import hashlib
    import torch
    from v5b.fleet.planb_ctrl import N_FEAT, Net
    torch.manual_seed(20261108)
    net = Net(N_FEAT + 2).m
    torch.save({"state": net.state_dict(), "mu": np.zeros(N_FEAT + 2, np.float32), "sd": np.full(N_FEAT + 2, 10.0, np.float32), "n_act": 2}, path)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def arms_for_c2(arms: dict, model: Path | None = None) -> dict:
    out = {a: arms[a] for a in ("nc", "p333", "w0u250", "3e")}
    p333, e3 = pb.ref_ctrl("p333"), {k: v for k, v in arms["3e"]["ctrl"].items() if k != "env"}
    out["asch_ph"] = pb.rule_cfg({"asch": {"steady": p333, "dist": e3, "theta_kmh": 55, "tau_s": 30, "h_kmh": 15}}, "S")
    out["mpcf_ph"] = pb.rule_cfg({"mpcf": {"actions": [p333, e3], "data": 74_800_000}}, "S")
    if model is not None:
        out["mpcf_ctl_ph"] = pb.rule_cfg({"mpcf": {"actions": [p333, e3], "model": str(model), "model_sha256": placeholder_model(model)}}, "S")
    return out


def run(root: Path, jobs: list, out: Path, workers: int) -> dict:
    f = out.with_suffix(".jobs.json")
    f.write_text(json.dumps(jobs))
    subprocess.run([PY, str(HERE / "run_rows.py"), str(root), str(f), str(out), str(workers)], check=True)
    return {(r["name"], r["seed"]): r for r in map(json.loads, out.open())}


def diff(a: dict, b: dict, skip=SKIP, only=None) -> list:
    a, b = json.loads(json.dumps(a)), json.loads(json.dumps(b))
    keys = (set(a) | set(b)) - skip
    if only:
        keys = {k for k in keys if only(k)}
    return sorted(k for k in keys if a.get(k) != b.get(k))


def minutes_equal(c: dict, s: dict, onset: float) -> list:
    """Series that differ before the onset: flow_min and v20_min (absolute minutes from 300 s), the pack's minute series."""
    bad = []
    n_abs = int(onset // 60) - 5
    for k in ("flow_min", "v20_min"):
        if c[k][:n_abs] != s[k][:n_abs]:
            bad.append(k)
    n_rel = int((onset - 300.0) // 60)
    for k, x in c["m_minute"].items():
        if x[:n_rel] != s["m_minute"][k][:n_rel]:
            bad.append("m_minute." + k)
    return bad


def check(out: Path, base: Path, workers: int) -> dict:
    if out.exists() and any(out.iterdir()):
        raise SystemExit(f"{out} is not empty: S1 never reuses rows, so a re-run after a fix runs everything again (review F6)")
    code = pb.code_state()
    if not (code["clean"] and code["detached"]):
        raise SystemExit(f"run S1 from a clean, detached worktree at the run commit (found clean={code['clean']}, detached={code['detached']})")
    out.mkdir(parents=True, exist_ok=True)
    head = subprocess.run(["git", "-C", str(base), "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    if not head.startswith(BASE_COMMIT) or subprocess.run(["git", "-C", str(base), "status", "--porcelain"], capture_output=True, text=True).stdout.strip():
        raise SystemExit(f"--base must be a clean checkout of {BASE_COMMIT}, found {head}")
    res = {"code": code}
    r = subprocess.run([PY, str(pb.ROOT / "docs/research/round2/measure2.py"), "smoke", "/home/catalin/work/phd/v5b1_runs/round2", str(out / "c1"),
                        str(min(workers, 7))], capture_output=True, text=True)
    res["C1"] = {"pass": "SMOKE PASS" in r.stdout, "tail": [x for x in r.stdout.splitlines() if "differs" in x and "differs: []" not in x][:5]}

    arms = pb.stored_arms()
    jobs = [[f"S|{a}", pb.with_cond(arms[a], "S"), pb.Q, s] for a in C1B_ARMS for s in SMOKE]
    jobs.append(["PLACEBO|nc", pb.with_cond(arms["nc"], "S", pb.PLACEBO), pb.Q, SMOKE[0]])
    rb, rp = run(base, jobs, out / "c1b_base.jsonl", workers), run(pb.ROOT, jobs, out / "c1b_planb.jsonl", workers)
    bad = {f"{k[0]} {k[1]}": d for k in rb if (d := diff(rb[k], rp[k]))}
    res["C1b"] = {"pass": not bad and len(rb) == len(rp) == len(jobs), "differs": bad}

    c2 = arms_for_c2(arms, out / "mpcf_ctl_ph.pt")
    st = str(out / "st")
    jobs2 = []
    for cond in ("S", "SURGE", "TRUCK"):
        for a, cfg in c2.items():
            jobs2.append([f"{cond}|{a}", {**pb.with_cond(cfg, cond), "measure": st}, pb.Q, SMOKE[0]])
    r1, r2 = run(pb.ROOT, jobs2, out / "c2_a.jsonl", workers), run(pb.ROOT, jobs2, out / "c2_b.jsonl", workers)
    bad = {f"{k[0]}": d for k in r1 if (d := diff(r1[k], r2[k]))}
    res["C2"] = {"pass": not bad and len(r1) == len(jobs2), "differs": bad}

    jobs3 = [[f"TRUCK|{a}", {**pb.with_cond(arms[a], "TRUCK"), "measure": st}, pb.Q, s] for a in ("nc", "p333", "w0u250") for s in SMOKE[1:]]
    r3 = run(pb.ROOT, jobs3, out / "c3.jsonl", workers) | r1
    by_seed = {}
    for (n, s), row in r3.items():
        if n.startswith("TRUCK|"):
            by_seed.setdefault(s, []).append([tuple(x) for x in row["pert_log"]])
    same = all(all(x == v[0] for x in v) for v in by_seed.values())
    vmax = max(row["m_capped_vmax"] for (n, s), row in r3.items() if n.startswith("TRUCK|"))
    dropped = {f"{n} {s}": row["m_dropped"] for (n, s), row in r3.items() if row.get("m_dropped")}
    ten = all(len(v[0]) == 10 for v in by_seed.values())
    labels = {"S": {"rest"}, "SURGE": {"before", "surge", "post"}, "TRUCK": {"before", "trucks"}}     # plant_sweep.period()'s dispatch
    bad_labels = {f"{n} {s}": sorted(got - labels[n.split("|")[0]]) for (n, s), row in r3.items()
                  if (got := {k.split("_p_", 1)[1] for k in row if k.startswith("ttc3_p_")}) - labels[n.split("|")[0]]}
    res["C3"] = {"pass": same and ten and vmax <= CAP + 1e-6 and not dropped and not bad_labels, "same_trucks_across_arms": same, "ten_trucks": ten,
                 "capped_vmax_kmh": round(vmax * 3.6, 3), "dropped": dropped, "period_labels": bad_labels}

    bad = {}
    for a in c2:
        s = r1[(f"S|{a}", SMOKE[0])]
        sg = r1[(f"SURGE|{a}", SMOKE[0])]
        tr = r1[(f"TRUCK|{a}", SMOKE[0])]
        first = min(x[2] for x in tr["pert_log"])
        for name, row, onset in (("SURGE", sg, 600.0), ("TRUCK", tr, first)):
            d = minutes_equal(row, s, onset)
            if d:
                bad[f"{name}|{a}"] = d
    res["C4"] = {"pass": not bad, "differs": bad}

    jobs5 = [[f"{c}|{a}", pb.with_cond(arms[a], c), pb.Q, SMOKE[0]] for c in ("SURGE", "TRUCK") for a in ("nc", "p333", "w0u250")]
    r5 = run(pb.ROOT, jobs5, out / "c5_off.jsonl", workers)
    bad = {k[0]: d for k in r5 if (d := diff(r5[k], r1[k], only=lambda x: not x.startswith("m_") and x not in SKIP))}
    calls = [f for f in ("v5b/fleet/measure.py", "v5b/fleet/planb_ctrl.py") if re.search(r"\._x\(", (pb.ROOT / f).read_text())]
    sums = {}
    for k, row in r1.items():
        tot = sum(sum(x.values()) for x in row["m_road_ttc3"].values())
        ev = sum(row[f"m_events_{c}"] for c in ("car", "alks", "truck"))
        z = np.load(out / "st" / row["m_st_file"])
        n_brk = len(z["brk"]) if "brk" in z else 0
        if tot != row["m_ttc3_all"] or n_brk != ev:
            sums[k[0]] = {"ttc3": (tot, row["m_ttc3_all"]), "events": (n_brk, ev)}
    import pr24
    jobs_t = [[f"{c}|{a}", {**pb.with_cond(arms[a], c), "measure": str(out / "trace_st")}, pb.Q, SMOKE[0]] for c in ("S", "SURGE", "TRUCK") for a in ("nc", "p333", "w0u250")]
    rt = pr24.run(jobs_t, workers, out / "c5_trace")
    traced = {f"{n} {s}": {"recount_differs": bad, "row_differs": pr24.row_differs(row, r1[(n, s)])} for (n, s), (row, _, bad) in rt.items()}
    traced_ok = len(rt) == len(jobs_t) and all(not v["recount_differs"] and not v["row_differs"] for v in traced.values())
    res["C5"] = {"pass": not bad and not calls and not sums and traced_ok, "pack_on_off_differs": bad, "calls_x": calls, "sums": sums,
                 "traced": {k: v for k, v in traced.items() if v["recount_differs"] or v["row_differs"]}}
    res["all_pass"] = all(v["pass"] for k, v in res.items() if k != "code")
    pb.cma2.write_json(out / "s1.json", res)
    return res


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", required=True)
    ap.add_argument("--base", required=True)
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args(argv)
    pb.reserve(a.workers)
    res = check(Path(a.out), Path(a.base), a.workers)
    print("commit", res["code"]["commit"])
    for k, v in res.items():
        if k not in ("all_pass", "code"):
            print(k, "PASS" if v["pass"] else "FAIL", {x: y for x, y in v.items() if x != "pass" and y})
    print("S1", "PASS" if res["all_pass"] else "FAIL")
    return 0 if res["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
