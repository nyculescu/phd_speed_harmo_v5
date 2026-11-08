"""Plan B S3a (planb.md §3.2, V480): confirmatory 3's grid re-pick (confirmatory_3.md:48-64, select_opp.py) in every cell that
passed S2 and in steady traffic S, at 5,300 veh/h on seeds 7,480,100-119. Per cell: the lowest close-following admissible rule of
each form, the delay opponent and the front row. In S: the steady pick, the lowest close-following admissible rule of all. Also
the report-only T2 mechanism G per cell (planb.md §7.3). No counting filter later: every pick is a deciding opponent.

usage: repick.py --out DIR --conds S,SURGE,TRUCK [--workers N]"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pb  # noqa: E402

sys.path.insert(0, str(pb.ROOT / "docs/research/conf3"))
from common import collisions, families, med, raw  # noqa: E402

SEEDS = pb.seeds(7_480_100, 7_480_119)


def choose(T: dict, cond: str, fam: dict) -> dict:
    """select_opp.choose for one condition, on (cond|rule) -> {seed: row}."""
    A = lambda r: T[f"{cond}|{r}"]
    P = A("p333")
    adm = lambda r: raw(A(r), P, "all_delay")[0] >= -2.0 and collisions(A(r)) <= collisions(P) + 1
    every = {r: k for rules in fam.values() for r, k in rules.items()}
    ok = {f: [r for r in rules if adm(r)] for f, rules in fam.items()}
    forms = {f: min(rs, key=lambda r: (med(A(r), "ttc_net"), r)) for f, rs in ok.items() if rs}
    close = [r for r in every if raw(A(r), P, "ttc_net")[0] >= -10.0]
    wide = [r for r in every if raw(A(r), P, "all_delay")[0] >= -10.0]
    allok = [r for rs in ok.values() for r in rs]
    return {"forms": forms, "admissible": {f: len(rs) for f, rs in ok.items()},
            "delay_opponent": min(close, key=lambda r: (med(A(r), "all_delay"), r)),
            "front_row": min(wide, key=lambda r: (med(A(r), "ttc_net"), r)),
            "lowest_cf": min(allok, key=lambda r: (med(A(r), "ttc_net"), r)) if allok else None}


def mechanism(T: dict, cell: str, steady: str, pick: str) -> dict:
    """G = (cost of the steady pick in the cell - cost of the per-cell pick) / cost of the steady pick, on delay and close-following."""
    S, C = T[f"{cell}|{steady}"], T[f"{cell}|{pick}"]
    return {k: 100.0 * (med(S, k) - med(C, k)) / max(med(S, k), 1e-9) for k in ("all_delay", "ttc_net")}


def run(out: Path, conds: list, workers: int, runner=pb.run_jobs) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    fam = families()
    every = {r: k for rules in fam.values() for r, k in rules.items()}
    if len(every) != 69:
        raise SystemExit(f"expected 69 tunable rules, found {len(every)}")
    cfgs = {f"{c}|{r}": pb.cfg(k, c) for c in conds for r, k in every.items()} | {f"{c}|nc": pb.cfg({}, c) for c in conds}
    rows = pb.batch(cfgs, SEEDS, out / "repick_runs.jsonl", out / "rd", workers, runner)
    T = {}
    for (n, s), r in rows.items():
        T.setdefault(n, {})[s] = r
    picks = {c: choose(T, c, fam) for c in conds}
    steady = picks["S"]["lowest_cf"]
    res = {"conds": conds, "seeds": [SEEDS[0], SEEDS[-1]], "picks": picks, "steady_pick": steady,
           "steady_ctrl": every[steady] if steady else None,
           "cell_opponents": {c: sorted(set(p["forms"].values()) | {p["delay_opponent"], p["front_row"]}) for c, p in picks.items() if c != "S"},
           "own_state_repick": {c: every[p["forms"]["own"]]["own_state"] for c, p in picks.items() if c != "S" and "own" in p["forms"]},
           "mechanism_G": {c: {"vs_lowest_cf": mechanism(T, c, steady, picks[c]["lowest_cf"]), "differs": picks[c]["lowest_cf"] != steady}
                           for c in conds if c != "S" and steady and picks[c]["lowest_cf"]},
           "ctrl": every}
    pb.cma2.write_json(out / "repick.json", res)
    return res


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", required=True)
    ap.add_argument("--conds", required=True)
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args(argv)
    conds = a.conds.split(",")
    if conds[0] != "S" or not set(conds[1:]) <= set(pb.CELLS):
        ap.error("--conds is S followed by the cells that passed S2")
    if a.workers > 100:
        ap.error("at most 100 workers (planb.md decision 7)")
    res = run(Path(a.out), conds, a.workers)
    print("steady pick", res["steady_pick"], {c: v for c, v in res["cell_opponents"].items()})
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
