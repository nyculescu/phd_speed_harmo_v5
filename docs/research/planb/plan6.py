"""Plan B S5/S6 (planb.md §3.2, §7.4, §9): build the ASCH and MPC-F member files from the picks, freeze the opponents into one picks
file, then build S6's job list and the reading's config.
Per passing cell: v3w's 5 learners, the 15 carried rules, the steady pick, the grid re-picks, 3E-C, 3E-D, ASCH, MPC-F (if its gate
passed) and no control; duplicates (equal controller dicts) run once and count once. In S: v3w, the carried rules, the steady pick, ASCH,
MPC-F, no control, and each cell's re-picks, 3E-C and 3E-D (for the resilience reading), each controller once. Seeds 7,480,400-639,
pack on, read once.

usage: plan6.py inputs --repick REPICK.json --cmab DIR --cells SURGE,TRUCK --out DIR   steady.json, library.json, actions.json
       plan6.py freeze --s2 S2.json --repick REPICK.json --cmab DIR --asch ASCH.json --mpcf MPCF.json --out PICKS.json
       plan6.py jobs --picks PICKS.json --out DIR      writes s6_jobs.json, read6_config.json and the MPC-F model; runs nothing
freeze checks that every stage ran at one clean, detached run commit, that the searches' picks belong to their cells and objectives,
and that ASCH and MPC-F were tuned with exactly the frozen members; the MPC-F model travels inside the picks file (base64), so the
S5-S6 worktree differs from the run commit by the picks file only."""
import argparse
import base64
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pb  # noqa: E402

SEEDS = pb.seeds(7_480_400, 7_480_639)
M = 2     # the approved number of cells, never lowered when a cell drops (planb.md §8.2)
OBJ = (("ttc", "3E-C"), ("delay", "3E-D"))


def ctrl_of(cfg: dict) -> dict:
    return {k: v for k, v in cfg.get("ctrl", {}).items() if k != "env"}


def zone_ctrl(params: list) -> dict:
    return {"zone_own_state": {"zones": params}}


def read_pick(cmab_dir: Path, cell: str, obj: str) -> tuple:
    d = cmab_dir / f"{cell}_{obj}"
    p, meta = json.loads((d / "pick.json").read_text()), json.loads((d / "meta.json").read_text())
    if (p["cell"], p["objective"], meta["cell"], meta["objective"]) != (cell, obj, cell, obj):
        raise SystemExit(f"{d}: pick or meta.json belongs to {p['cell']}/{p['objective']}, not {cell}/{obj}")
    return p, meta


def inputs(repick: dict, cmab_dir: Path, cells: list) -> dict:
    """The members ASCH and MPC-F are tuned with: the steady pick; 3E-T and each cell's 3E-C (planb.md §3.4-§3.5)."""
    e3c = {}
    for c in cells:
        inc = read_pick(cmab_dir, c, "ttc")[0]["incumbent"]
        if inc:
            e3c[f"3E-C_{c}"] = zone_ctrl(inc["params"])
    steady = repick["steady_ctrl"]
    return {"steady": steady, "library": {"3E-T": pb.arm_ctrl("3e")} | e3c,
            "actions": [pb.ref_ctrl("p333"), steady, pb.arm_ctrl("3e")] + list(e3c.values())}


def freeze(s2: dict, repick: dict, cmab_dir: Path, asch: dict, mpcf: dict, mpcf_dir: Path | None = None, strict: bool = True) -> dict:
    if s2.get("null_broken"):
        raise SystemExit("S2's null is broken: the stage stopped, nothing to freeze")
    if set(s2["cells"]) != set(pb.CELLS):
        raise SystemExit(f"s2.json must gate every approved cell {pb.CELLS}")
    if any(v["passes"] is None for v in s2["cells"].values()):
        raise SystemExit("an S2 cell is pending: " + ", ".join(c for c, v in s2["cells"].items() if v["passes"] is None))
    cells = [c for c in pb.CELLS if s2["cells"][c]["passes"]]
    if not cells:
        raise SystemExit("KILL at S2: nothing to freeze")
    conds = ["S"] + cells
    for name, x in (("repick", repick), ("asch", asch), ("mpcf", mpcf)):
        if x["conds"] != conds:
            raise SystemExit(f"{name} ran on {x['conds']}, not {conds}")
    want = inputs(repick, cmab_dir, cells)
    if asch["steady"] != want["steady"] or asch["library"] != want["library"]:
        raise SystemExit("ASCH was tuned with other members than the frozen steady pick, 3E-T and 3E-C")
    if mpcf["actions"] != want["actions"]:
        raise SystemExit("MPC-F was fitted with other actions than p333, the steady pick, 3E-T and the frozen 3E-C")
    tuned, omitted, codes = {}, {}, {"repick": repick["code"], "asch": asch["code"], "mpcf": mpcf["code"]}
    for c in cells:
        for obj, tag in OBJ:
            p, meta = read_pick(cmab_dir, c, obj)
            codes[f"{tag}_{c}"] = meta
            inc = p["incumbent"]
            tuned[f"{tag}_{c}"] = {"ctrl": zone_ctrl(inc["params"]) if inc else None, "label": p["label"], "generations": p["generations"], "cell": c}
            if not inc:
                omitted[f"{tag}_{c}"] = f"no admissible configuration at generation {p['generations']} ({p['label']})"
    commits = {k: v.get("commit") for k, v in codes.items()}
    if strict and (len(set(commits.values())) != 1 or not all(v.get("clean") and v.get("detached") for v in codes.values())):
        raise SystemExit(f"S3a and S4 must run at one clean, detached run commit (planb.md §9): {commits}")
    s2c = s2.get("code") or {}
    if strict and not (s2c.get("clean") and s2c.get("detached") and pb.same_plant(s2c.get("commit") or "", next(iter(commits.values())))):
        raise SystemExit(f"S2 ran at {s2c.get('commit')}, whose plant differs from the run commit's, or from a dirty tree")
    if asch.get("pick"):
        P_asch = asch["pick"]["ctrl"]
    else:
        P_asch, omitted["ASCH"] = None, "failed build: no admissible configuration"
    P_mpcf = None
    if mpcf.get("gate_passed"):
        raw = (mpcf_dir / mpcf["model"]).read_bytes()
        if hashlib.sha256(raw).hexdigest() != mpcf["model_sha256"]:
            raise SystemExit("the MPC-F model differs from its recorded SHA-256")
        P_mpcf = {"actions": mpcf["actions"], "model_sha256": mpcf["model_sha256"], "model_b64": base64.b64encode(raw).decode()}
    else:
        omitted["MPC-F"] = "failed its validity gate"
    return {"cells": cells, "m": M, "run_commit": next(iter(commits.values())), "s2_commit": s2c.get("commit"), "drain_cap": {c: s2["cells"][c]["drain_cap"] for c in cells},
            "repicks": {c: {r: repick["ctrl"][r] for r in repick["cell_opponents"][c]} for c in cells},
            "steady": {"name": f"steady_{repick['steady_pick']}", "ctrl": repick["steady_ctrl"]}, "tuned": tuned, "asch": P_asch, "mpcf": P_mpcf,
            "omitted": omitted}


def write_model(P: dict, out: Path) -> Path | None:
    if not P["mpcf"]:
        return None
    raw = base64.b64decode(P["mpcf"]["model_b64"])
    if hashlib.sha256(raw).hexdigest() != P["mpcf"]["model_sha256"]:
        raise SystemExit("the MPC-F model in the picks file differs from its SHA-256")
    f = out / f"mpcf_{P['mpcf']['model_sha256'][:12]}.pt"
    f.write_bytes(raw)
    return f


def dedup(arms: dict) -> tuple:
    """Equal controller dicts run once: (name -> ctrl with the first name kept, dropped name -> kept name)."""
    uniq, alias = {}, {}
    for n, k in arms.items():
        twin = next((u for u, x in uniq.items() if x == k), None)
        if twin is None:
            uniq[n] = k
        else:
            alias[n] = twin
    return uniq, alias


def arm_sets(P: dict, model: Path | None) -> tuple:
    """(cell -> {arm: ctrl}, S arms, cell -> deciding opponent names, stored arms, S alias)."""
    stored = pb.stored_arms()
    base = {n: ctrl_of(stored[n]) for n in pb.CARRIED}
    shared = dict(base) | {P["steady"]["name"]: P["steady"]["ctrl"]}     # the steady pick decides in every cell too (planb.md §3.2)
    if P["asch"]:
        shared["ASCH"] = P["asch"]
    if P["mpcf"]:
        shared["MPC-F"] = {"mpcf": {"actions": P["mpcf"]["actions"], "model": str(model), "model_sha256": P["mpcf"]["model_sha256"]}}
    cells, deciding, alias = {}, {}, {}
    extra_s = {}
    for c in P["cells"]:
        arms = dict(shared)
        for r, k in P["repicks"][c].items():
            arms[f"grid_{r}"] = k
        for tag in ("3E-C", "3E-D"):
            t = P["tuned"][f"{tag}_{c}"]
            if t["ctrl"]:
                arms[f"{tag}_{c}"] = t["ctrl"]
        uniq, _ = dedup(arms)
        cells[c] = uniq
        deciding[c] = sorted(uniq)
        extra_s |= {n: k for n, k in uniq.items() if n not in shared}
    s_arms, alias = dedup(dict(shared) | extra_s)
    return cells, s_arms, deciding, stored, alias


def jobs(P: dict, out: Path) -> tuple:
    model = write_model(P, out)
    cells, s_arms, deciding, stored, alias = arm_sets(P, model)
    st = str(out / "st")
    J = {}
    for cond, arms in [("S", s_arms)] + list(cells.items()):
        for n in pb.V3W + ("nc",):
            J[f"{cond}|{n}"] = {**pb.with_cond(stored[n], cond), "measure": st}
        for n, k in arms.items():
            J[f"{cond}|{n}"] = {**pb.cfg(k, cond), "measure": st}
    conf = {"m": P["m"], "cells": P["cells"], "learners": list(pb.V3W), "opponents": deciding, "drain_cap": P["drain_cap"],
            "seed_range": [SEEDS[0], SEEDS[-1]], "s_alias": alias, "omitted": P["omitted"], "run_commit": P["run_commit"],
            "p333": "p333", "nc": "nc", "t3e": "3e", "e3c": {c: f"3E-C_{c}" for c in P["cells"] if f"3E-C_{c}" in cells[c]},
            "e3d": {c: f"3E-D_{c}" for c in P["cells"] if f"3E-D_{c}" in cells[c]}, "null_swaps": 2000}
    return J, conf


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("step", choices=("inputs", "freeze", "jobs"))
    ap.add_argument("--s2")
    ap.add_argument("--repick")
    ap.add_argument("--cmab")
    ap.add_argument("--cells")
    ap.add_argument("--asch")
    ap.add_argument("--mpcf")
    ap.add_argument("--picks")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    if a.step == "inputs":
        cells = pb.conds_arg("S," + a.cells)[1:]
        x = inputs(pb.load_json(a.repick), Path(a.cmab), cells)
        out = Path(a.out)
        out.mkdir(parents=True, exist_ok=True)
        for k in ("steady", "library", "actions"):
            pb.cma2.write_json(out / f"{k}.json", x[k])
        print("written", [f"{k}.json" for k in x], "library", sorted(x["library"]))
        return 0
    if a.step == "freeze":
        P = freeze(pb.load_json(a.s2), pb.load_json(a.repick), Path(a.cmab), pb.load_json(a.asch), pb.load_json(a.mpcf), Path(a.mpcf).parent)
        pb.cma2.write_json(Path(a.out), P)
        print("frozen:", P["cells"], "run commit", P["run_commit"][:12], "omitted:", P["omitted"])
        return 0
    P = pb.load_json(a.picks)
    out = Path(a.out).resolve()     # the MPC-F model path in every job must open from any working directory
    out.mkdir(parents=True, exist_ok=True)
    J, conf = jobs(P, out)
    pb.cma2.write_json(out / "s6_jobs.json", {"seed_range": [SEEDS[0], SEEDS[-1]], "q": pb.Q, "arms": J})
    pb.cma2.write_json(out / "read6_config.json", conf)
    print(len(J), "arms x", len(SEEDS), "seeds =", len(J) * len(SEEDS), "runs")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
