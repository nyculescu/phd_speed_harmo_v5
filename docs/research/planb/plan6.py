"""Plan B S5/S6 (planb.md §3.2, §7.4, §9): freeze the opponents into one picks file, then build S6's job list and the reading's config.
Per passing cell: v3w's 5 learners, the 15 carried rules, the steady pick, the grid re-picks, 3E-C, 3E-D, ASCH, MPC-F (if its gate
passed) and no control; duplicates (equal controller dicts) run once and count once. In S: v3w, the carried rules, the steady pick, ASCH, MPC-F,
no control, and each cell's re-picks, 3E-C and 3E-D (for the resilience reading). Seeds 7,480,400-639, pack on, read once.

usage: plan6.py freeze --s2 S2.json --repick REPICK.json --cmab DIR --asch ASCH.json --mpcf MPCF.json --out PICKS.json
       plan6.py jobs --picks PICKS.json --out DIR      writes s6_jobs.json and read6_config.json; runs nothing"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pb  # noqa: E402

SEEDS = pb.seeds(7_480_400, 7_480_639)
M = 2     # the approved number of cells, never lowered when a cell drops (planb.md §8.2)


def ctrl_of(cfg: dict) -> dict:
    return {k: v for k, v in cfg.get("ctrl", {}).items() if k != "env"}


def freeze(s2: dict, repick: dict, cmab_dir: Path, asch: dict, mpcf: dict) -> dict:
    cells = [c for c, v in s2["cells"].items() if v["passes"]]
    tuned = {}
    for c in cells:
        for obj, tag in (("ttc", "3E-C"), ("delay", "3E-D")):
            p = json.loads((cmab_dir / f"{c}_{obj}" / "pick.json").read_text())
            inc = p["incumbent"]
            tuned[f"{tag}_{c}"] = {"ctrl": {"zone_own_state": {"zones": inc["params"]}} if inc else None, "label": p["label"],
                                   "generations": p["generations"], "cell": c}
    return {"cells": cells, "m": M, "drain_cap": {c: s2["cells"][c]["drain_cap"] for c in cells},
            "repicks": {c: {r: repick["ctrl"][r] for r in repick["cell_opponents"][c]} for c in cells},
            "steady": {"name": f"steady_{repick['steady_pick']}", "ctrl": repick["steady_ctrl"]}, "tuned": tuned,
            "asch": asch["pick"]["ctrl"] if asch.get("pick") else None,
            "mpcf": {"actions": mpcf["actions"], "model_sha256": mpcf["model_sha256"], "model": mpcf["model"]} if mpcf.get("gate_passed") else None,
            "omitted": {"asch": None if asch.get("pick") else "failed build: no admissible configuration",
                        "mpcf": None if mpcf.get("gate_passed") else "failed its validity gate"}}


def arm_sets(P: dict, model_dir: Path) -> tuple:
    """(cell -> {arm: ctrl}, S arms, cell -> deciding opponent names)."""
    stored = pb.stored_arms()
    base = {n: ctrl_of(stored[n]) for n in pb.CARRIED}
    shared = dict(base) | {P["steady"]["name"]: P["steady"]["ctrl"]}     # the steady pick decides in every cell too (planb.md §3.2)
    if P["asch"]:
        shared["ASCH"] = P["asch"]
    if P["mpcf"]:
        shared["MPC-F"] = {"mpcf": {"actions": P["mpcf"]["actions"], "model": str(model_dir / P["mpcf"]["model"])}}
    cells, deciding = {}, {}
    extra_s = {}
    for c in P["cells"]:
        arms = dict(shared)
        for r, k in P["repicks"][c].items():
            arms[f"grid_{r}"] = k
        for tag in ("3E-C", "3E-D"):
            t = P["tuned"][f"{tag}_{c}"]
            if t["ctrl"]:
                arms[f"{tag}_{c}"] = t["ctrl"]
        seen, uniq = [], {}
        for n, k in arms.items():     # duplicates run once and count once
            if k not in seen:
                seen.append(k)
                uniq[n] = k
        cells[c] = uniq
        deciding[c] = sorted(uniq)
        extra_s |= {n: k for n, k in uniq.items() if n not in shared}
    s_arms = dict(shared) | extra_s
    return cells, s_arms, deciding, stored


def jobs(P: dict, out: Path, model_dir: Path) -> tuple:
    cells, s_arms, deciding, stored = arm_sets(P, model_dir)
    st = str(out / "st")
    J = {}
    for cond, arms in [("S", s_arms)] + list(cells.items()):
        for n in pb.V3W + ("nc",):
            J[f"{cond}|{n}"] = {**pb.with_cond(stored[n], cond), "measure": st}
        for n, k in arms.items():
            J[f"{cond}|{n}"] = {**pb.cfg(k, cond), "measure": st}
    t3e = "3e"
    conf = {"m": P["m"], "cells": P["cells"], "learners": list(pb.V3W), "opponents": deciding, "drain_cap": P["drain_cap"],
            "p333": "p333", "nc": "nc", "t3e": t3e, "e3c": {c: f"3E-C_{c}" for c in P["cells"] if f"3E-C_{c}" in cells[c]},
            "e3d": {c: f"3E-D_{c}" for c in P["cells"] if f"3E-D_{c}" in cells[c]}, "null_swaps": 2000}
    return J, conf


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("step", choices=("freeze", "jobs"))
    ap.add_argument("--s2")
    ap.add_argument("--repick")
    ap.add_argument("--cmab")
    ap.add_argument("--asch")
    ap.add_argument("--mpcf")
    ap.add_argument("--picks")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    if a.step == "freeze":
        P = freeze(pb.load_json(a.s2), pb.load_json(a.repick), Path(a.cmab), pb.load_json(a.asch), pb.load_json(a.mpcf))
        pb.cma2.write_json(Path(a.out), P)
        print("frozen:", P["cells"], "omitted:", {k: v for k, v in P["omitted"].items() if v})
        return 0
    P = pb.load_json(a.picks)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    J, conf = jobs(P, out, Path(a.picks).resolve().parent)
    pb.cma2.write_json(out / "s6_jobs.json", {"seeds": [SEEDS[0], SEEDS[-1]], "q": pb.Q, "arms": J})
    pb.cma2.write_json(out / "read6_config.json", conf)
    print(len(J), "arms x", len(SEEDS), "seeds =", len(J) * len(SEEDS), "runs")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
