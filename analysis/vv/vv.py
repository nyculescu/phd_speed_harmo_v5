"""Merge V&V (docs/local/research/protocols/merge_vv.md on v5b1, V532): seed stages, job files, the smoke, the identity replay and the runner.

Arms are C1 confirmation (CF) E30 arms, built by the same code (c1.stored_cf, c1.arm_cfg), plus the merge V&V fields: lane lengths
(accel_len, accel2_len), the policy remap (x_remap) and the read-only instruments (vv_*, trace_end). Runs use Plan B's runner
(run6.execute) through c1.timed.

usage: vv.py plan STAGE --out JOBS.json
       vv.py run --jobs JOBS.json --out DIR [--workers N] [--cpu CPU]
       vv.py smoke --jobs JOBS.json --out DIR [--workers N] [--cpu CPU]
       vv.py ident ROWS OUT --cpu CPU"""
import argparse
import copy
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "c1"))
import c1  # noqa: E402
from c1 import pb, run6, v5  # noqa: E402

STAGES = {     # VV-D4, inclusive ranges
    "vv_replay": (7_489_160, 7_489_161),     # stored E30 seeds, non-reading: identity and traces against stored rows
    "vv_trace": (7_493_000, 7_493_001),
    "vv_smoke": (7_493_010, 7_493_010),
    "vv_screen": (7_492_000, 7_492_479)}
ARMS = pb.V3W + ("lr400_16_1", "grid_lr400_13_1", "p333", "nc")     # VV-D2
TRACED = ("w1u500", "lr400_16_1", "nc")     # V1: the median learner on E30 close-following, the closest rule, no control
LENGTHS = (300.0, 600.0)     # VV-D3 A: both acceleration lanes
EV = c1.EV
TWIN = v5.TWIN
REPLAY_ROWS = HERE / "data" / "cf_replay_rows.jsonl"     # the stored CF rows of ARMS on the vv_replay seeds
VV_KEYS = ("vv_", "end_trace")     # instrument output, skipped when an instrumented run meets its plain twin
CF_CPU = "AMD EPYC 7B13 64-Core Processor"     # the CF rental (V529): where the stored replay rows were made
OWN_NAME = {"arm", "learner"}     # run6.wrap derives them from the job name, so a "~trace" job carries its own


def vv_key(k: str) -> bool:
    return k.startswith(VV_KEYS)


def seeds(stage: str) -> list:
    a, b = STAGES[stage]
    return list(range(a, b + 1))


def base_arm(r: str, st: Path) -> dict:
    """CF's E30 arm, as cf_screen built it."""
    c = c1.arm_cfg(c1.stored_cf()[r], st, EV)
    if c["ctrl"]["env"]["perturb"] != EV:
        raise SystemExit(f"{r}: perturb differs from E30")
    return c


def at_length(c: dict, L: float) -> dict:
    """VV-D3 A and VV-D7: both lanes at L, with the policy remap on longer lanes (a no-op for rules)."""
    c = copy.deepcopy(c)
    if L != 300.0:
        c |= {"accel_len": L, "accel2_len": L, "x_remap": True}
    return c


def screen_arm(r: str, L: float, out_dir: Path) -> dict:
    """§2 instruments by run set: counts and logs everywhere; the 0.1-s meter at 300 m only."""
    c = at_length(base_arm(r, out_dir / "st"), L) | {"vv_count": True, "vv_log": str(out_dir / "vv")}
    c |= {"vv_meter": True} if L == 300.0 else {"vv_obs": True}
    return c


def traced(c: dict, out_dir: Path) -> dict:
    return c | {"vv_trace": True, "vv_log": str(out_dir / "vv"), "trace_end": True}


def name(L: float, r: str) -> str:
    return f"L{L:g}|{r}"


def plan(stage: str, out_dir: Path) -> dict:
    st = out_dir / "st"
    if stage == "vv_replay":     # identity at 300 m: CF's configs unchanged; traced versions checked against the same stored rows
        jobs = {f"E30|{r}": base_arm(r, st) for r in ARMS}
        jobs |= {f"E30|{r}~trace": traced(base_arm(r, st), out_dir) for r in TRACED}
    elif stage == "vv_trace":     # V1: traced and untraced twins at both lengths
        jobs = {}
        for L in LENGTHS:
            for r in TRACED:
                plain = at_length(base_arm(r, st), L)
                jobs[name(L, r) + "~trace"] = traced(plain | ({"vv_meter": True} if L == 300.0 else {"vv_obs": True}), out_dir)
                jobs[name(L, r) + TWIN] = plain
    elif stage in ("vv_screen", "vv_smoke"):
        jobs = {name(L, r): screen_arm(r, L, out_dir) for L in LENGTHS for r in ARMS}
        if stage == "vv_smoke":     # instruments against plain twins: a learner, a rule, the uniform rule and no control
            for L, rs in ((300.0, ("w1u500", "lr400_16_1", "p333", "nc")), (600.0, ("w1u500", "nc"))):
                for r in rs:
                    jobs[name(L, r) + TWIN] = at_length(base_arm(r, st), L)
    else:
        raise SystemExit(f"no merge V&V job for stage {stage}")
    lo, hi = STAGES[stage]
    return {"stage": stage, "seed_range": [lo, hi], "q": pb.Q, "arms": jobs}


def twin_diff(a: dict, b: dict) -> list:
    """Traffic keys that differ between an instrumented run and its plain twin (V386; V519 for policy diagnostics)."""
    from read_c1 import key_class
    return [k for k in c1.twin_diff(a, b) if not vv_key(k) and key_class(k) == "traffic"]


def t0_lengths(rows: list, arms: dict) -> list:
    """T0 at 600 m: against the 300-m run of the same arm and seed, only 3a_* and 4a_* lanes differ, each by +300 m (±0.01)."""
    by = {(r["name"], r["seed"]): r for r in rows}
    bad = []
    for (n, s), r in by.items():
        if not n.startswith("L600|") or n.endswith(TWIN):
            continue
        if "vv_lanes" not in r:
            bad.append(f"{n} {s}: no lane read-back")
            continue
        ref = by.get((n.replace("L600|", "L300|"), s))
        if ref is None or "vv_lanes" not in ref:
            bad.append(f"{n} {s}: no 300-m twin")
            continue
        a, b = ref["vv_lanes"], r["vv_lanes"]
        if set(a) != set(b):
            bad.append(f"{n} {s}: lane sets differ")
            continue
        for x in a:
            d = b[x] - a[x]
            want = 300.0 if x.split("_")[0] in ("3a", "4a") else 0.0
            if abs(d - want) > 0.01:
                bad.append(f"{n} {s}: {x} {a[x]:.2f} -> {b[x]:.2f}")
    return bad


def same_demand(rows: list) -> list:
    """The two lengths of an arm and seed insert the same vehicles and automate the same ones (c1_t0), so seeds pair (V3b)."""
    by = {(r["name"], r["seed"]): r.get("c1_t0") for r in rows}
    bad = []
    for (n, s), t in by.items():
        if n.startswith("L600|") and not n.endswith(TWIN):
            u = by.get((n.replace("L600|", "L300|"), s))
            if t is None or u is None or (t["veh_n"], t["alks_sha"]) != (u["veh_n"], u["alks_sha"]):
                bad.append(f"{n} {s}")
    return bad


def obs_checks(rows: list) -> dict:
    """§4 smoke: the remapped position never leaves the training range on 3a and 4a; the share of decisions with column 15 capped."""
    out = {}
    for r in rows:
        if "vv_c15_n" in r:
            out[f"{r['name']} {r['seed']}"] = {"x_out": r.get("vv_x_out", 0.0), "x_acc_n": r.get("vv_x_acc_n", 0.0),
                                               "c15_cap_share": r.get("vv_c15_cap", 0.0) / max(r["vv_c15_n"], 1.0)}
    return out


def meter_ok(r: dict) -> bool:
    """V2 BUG checks: the meter ran (vv_m_time is written whenever it is on), its whole-second count equals ttc_net and its
    half-second count ttc_half."""
    return "vv_m_time" in r and r.get("vv_m_whole", 0.0) == r["ttc_net"] and r.get("vv_m_half", 0.0) == r.get("ttc_half", 0.0)


def meter_bugs(rows: list) -> list:
    """Every instrumented 300-m row must pass meter_ok."""
    return [f"{r['name']} {r['seed']}: time {r.get('vv_m_time')}, whole {r.get('vv_m_whole')} vs ttc_net {r['ttc_net']}, half {r.get('vv_m_half')} vs ttc_half {r.get('ttc_half')}"
            for r in rows if r["name"].startswith("L300|") and not r["name"].endswith(TWIN) and r["cfg"].get("vv_meter") and not meter_ok(r)]


def smoke(jobs: dict, out: Path, workers: int, cpu: str = "") -> dict:
    """Every arm once, then each distinct config again (T3: rows and side files equal); instrumented runs equal to their plain twins
    on traffic keys (V386); T0 lane lengths at 600 m; the meter's equality checks; the input checks; seconds per run."""
    from read_m2 import npz_equal
    arms = jobs["arms"]
    sd = list(range(jobs["seed_range"][0], jobs["seed_range"][1] + 1))
    run6.check_checkpoints(arms)
    run6.check_files(arms)
    rep = {n: c for n, c in arms.items() if not n.endswith(TWIN)}
    inp = {"stage": jobs["stage"], "seed_range": jobs["seed_range"], "smoke": True, "cpu": cpu}
    da = run6.execute(v5.with_measure(arms, out / "a" / "st"), sd, out / "a", workers, inp, fn=c1.timed)
    db = run6.execute(v5.with_measure(rep, out / "b" / "st"), sd, out / "b", workers, inp, fn=c1.timed)
    A = {(r["name"], r["seed"]): r for r in pb.cma2.load(out / "a" / "s6_rows.jsonl")}
    B = {(r["name"], r["seed"]): r for r in pb.cma2.load(out / "b" / "s6_rows.jsonl")}
    skip = run6.SKIP | {"commit", "m_st_file", "wall_s", "vv_log_file"}
    missing = sorted(f"{k[0]} {k[1]}" for k in B if k not in A)
    differs = {f"{k[0]} {k[1]}": d for k in B if k in A and (d := v5.same_row(A[k], B[k], skip))}
    side = sorted(f"{k[0]} {k[1]}" for k in B if k in A and A[k].get("m_st_file")
                  and not npz_equal(out / "a" / "st" / A[k]["m_st_file"], out / "b" / "st" / B[k]["m_st_file"]))
    twins = {}
    for n in arms:
        if n.endswith(TWIN):
            m = n[: -len(TWIN)]
            for s in sd:
                if (m, s) not in A or (n, s) not in A:
                    twins[f"{m} {s}"] = ["missing row"]
                elif d := twin_diff(A[(m, s)], A[(n, s)]):
                    twins[f"{m} {s}"] = d
    rows = list(A.values())
    t0 = t0_lengths(rows, arms)
    mb = meter_bugs(rows)
    obs = obs_checks(rows)
    x_out = sorted(k for k, v in obs.items() if v["x_out"])
    x_out += sorted(f"{r['name']} {r['seed']}: no position read on 3a/4a" for r in rows if r["name"].startswith("L600|") and r["cfg"].get("vv_obs")
                    and r["name"].split("|", 1)[1].split("~")[0] in pb.V3W and not r.get("vv_x_acc_n"))
    pairs = same_demand(rows)
    wall = {}
    for r in rows:
        wall.setdefault(r["name"].split("~")[0], []).append(r.get("wall_s") or 0.0)
    standing = {f"{r['name']} {r['seed']}": {"end_stop": r.get("end_stop"), "end_stop2": r.get("end_stop2"), "stand_n": r.get("vv_stand_n")}
                for r in rows if r["name"].split("|", 1)[1] in ("nc", "lr400_16_1")}
    res = {"missing_in_a": missing, "replay_differs": differs, "side_files_differ": side, "twin_differs": twins, "t0_lengths": t0,
           "meter_bugs": mb, "x_out": x_out, "obs": obs, "wall_s": {k: round(sum(v) / len(v), 1) for k, v in sorted(wall.items())},
           "standing_for_author": standing, "demand_differs": pairs, "drops": [da, db],
           "pass": not (missing or differs or side or twins or t0 or mb or x_out or pairs or da or db)}
    pb.cma2.write_json(out / "smoke.json", res)
    return res


def ident(rows: list, cpu: str) -> dict:
    """§3 identity at 300 m: the replayed CF arms equal their stored rows on every traffic key (as cf_ident; policy diagnostics printed),
    and the traced versions too (a traced run that differs is a tracer bug; nothing in E30 is re-run)."""
    from read_c1 import key_class, rel_diff
    S = {(r["name"], r["seed"]): r for r in map(json.loads, REPLAY_ROWS.read_text().splitlines())}

    def compare(rs: list) -> dict:
        rule, learner, diag, missing = {}, {}, {}, []
        seen = {(r["name"].split("~")[0], r["seed"]) for r in rs}
        missing = sorted(f"{n} {s}" for n, s in S if (n, s) not in seen)
        for r in rs:
            n = r["name"].split("~")[0]
            ref = S.get((n, r["seed"]))
            if ref is None:
                missing.append(f"{r['name']} {r['seed']} (no stored row)")
                continue
            bad = sorted(k for k in ref if key_class(k) == "traffic" and k not in OWN_NAME
                         and json.dumps(r.get(k), sort_keys=True) != json.dumps(ref[k], sort_keys=True))
            dg = {k: rel_diff(r.get(k), ref[k]) for k in ref if key_class(k) == "diagnostic" and r.get(k) != ref[k]}
            if dg:
                diag[f"{r['name']} {r['seed']}"] = dg
            if bad:
                (learner if n.split("|", 1)[1] in pb.V3W else rule)[f"{r['name']} {r['seed']}"] = bad
        return {"rule_diff": rule, "learner_diff": learner, "diagnostics": diag, "missing": missing}

    plain = compare([r for r in rows if "~" not in r["name"]])
    tr = compare([r for r in rows if r["name"].endswith("~trace")])
    tr["missing"] = [m for m in tr["missing"] if m.split("|", 1)[1].split()[0] in TRACED]
    same_cpu = " ".join(cpu.split()) == CF_CPU
    action = "stop" if plain["rule_diff"] or plain["missing"] or (plain["learner_diff"] and same_cpu) else "go"
    return plain | {"cpu": cpu, "cf_cpu": CF_CPU, "learner_diff_disclosed": bool(plain["learner_diff"] and not same_cpu), "action": action,
                    "traced": tr, "tracer_bug": bool(tr["rule_diff"] or tr["missing"] or (tr["learner_diff"] and same_cpu))}


def run(jobs: dict, out: Path, workers: int, cpu: str = "") -> dict:
    sd = list(range(jobs["seed_range"][0], jobs["seed_range"][1] + 1))
    if [sd[0], sd[-1]] != list(STAGES[jobs["stage"]]):
        raise SystemExit(f"seeds {sd[0]}-{sd[-1]} are not stage {jobs['stage']}'s {STAGES[jobs['stage']]} (VV-D4)")
    run6.check_checkpoints(jobs["arms"])
    run6.check_files(jobs["arms"])
    inp = {"stage": jobs["stage"], "seed_range": jobs["seed_range"], "cpu": cpu}
    return run6.execute(jobs["arms"], sd, out, workers, inp, fn=c1.timed)


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("step", choices=("plan", "run", "smoke", "ident"))
    ap.add_argument("stage", nargs="?")
    ap.add_argument("out2", nargs="?")
    ap.add_argument("--jobs")
    ap.add_argument("--out")
    ap.add_argument("--workers", type=int, default=31)
    ap.add_argument("--cpu", default="")
    x = ap.parse_args(argv)
    if x.step == "plan":
        out = Path(x.out).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        j = plan(x.stage, out.parent)
        pb.cma2.write_json(out, j)
        print(j["stage"], len(j["arms"]), "arms, seeds", j["seed_range"])
        return 0
    if x.step == "ident":
        res = ident([json.loads(l) for l in open(x.stage)], x.cpu)
        pb.cma2.write_json(Path(x.out2), res)
        print("ident", res["action"], "tracer_bug", res["tracer_bug"])
        return 0 if res["action"] == "go" and not res["tracer_bug"] else 1
    pb.reserve(x.workers)
    if x.step == "smoke":
        res = smoke(pb.load_json(x.jobs), Path(x.out).resolve(), x.workers, x.cpu)
        print("smoke", "PASS" if res["pass"] else "FAIL", {k: v for k, v in res.items() if k in ("twin_differs", "t0_lengths", "meter_bugs", "x_out", "replay_differs") and v})
        return 0 if res["pass"] else 1
    drops = run(pb.load_json(x.jobs), Path(x.out).resolve(), x.workers, x.cpu)
    print("rows done;", "crash drops:", drops or "none")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
