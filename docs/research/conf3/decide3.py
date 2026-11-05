"""The reading of confirmatory 3, as fixed in the protocol. usage: decide3.py out_dir table.csv"""
import csv
import json
import sys
from pathlib import Path

from common import COND, LEARNERS, PRIMARY, Q, collisions, effect, load, med, paired_median

P95 = (2.5, 97.5)


def limits(P: dict, O: dict) -> dict:
    """The side limits a policy must meet against one opponent."""
    ev = effect(P, O, "alks_full_moving")[0] >= -5.0 or paired_median(P, O, "alks_full_moving") <= 5.0
    return {"delay": effect(P, O, "all_delay")[0] >= -2.0, "flow": effect(P, O, "passed", 1)[0] >= -0.5, "brake": effect(P, O, "b3_step")[0] >= -5.0,
            "events": ev, "coll": collisions(P) <= collisions(O) + 1}


def clears(P: dict, O: dict, margin: float) -> bool:
    e = effect(P, O, "ttc_net")
    return e[0] >= margin and e[1] > 0 and paired_median(O, P, "ttc_net") >= 20.0 and all(limits(P, O).values())


def anchored(P: dict, p333: dict) -> bool:
    return effect(P, p333, "all_delay")[0] >= -5.0 and effect(P, p333, "passed", 1)[0] >= -1.0


def delay_clears(P: dict, O: dict) -> bool:
    d = effect(P, O, "all_delay")
    return d[0] >= 5.0 and d[1] > 0 and effect(P, O, "passed", 1)[0] >= -0.5 and effect(P, O, "ttc_net")[0] >= -10.0 and effect(P, O, "b3_step")[0] >= -10.0 and collisions(P) <= collisions(O) + 1


def read_cell(T: dict, cell: str, o: dict, n: int = LEARNERS, q: float = Q) -> dict:
    A = lambda name: T[(f"{cell}|{name}", q)]
    pol = [A(f"d{i}") for i in range(n)]
    p333 = A("p333")
    c = o["cells"][cell]
    names = list(dict.fromkeys(["p333", *c["forms"].values()]))
    counts = [r for r in names if effect(A(r), p333, "all_delay")[0] >= -2.0]
    tuned = [all(clears(P, A(r), 10.0) for r in counts) and anchored(P, p333) for P in pol]
    repl = [clears(P, p333, 30.0) for P in pol]
    dop = min((c["delay_opponent"], "p333"), key=lambda r: med(A(r), "all_delay"))
    delay = [delay_clears(P, A(dop)) for P in pol]
    severe = [all(paired_median(P, A(r), "sev3") <= 0.0 for r in counts) for P in pol]
    single = [clears(P, A(o["single_rule"]), 10.0) and anchored(P, p333) for P in pol]
    copy_rule = c["forms"].get("copy")
    worse_nc = [effect(P, A("nc"), "ttc_net", pct=P95)[2] < 0 for P in pol]
    return {"cell": cell, "counts": counts, "excluded": [r for r in names if r not in counts], "only_p333": counts == ["p333"],
            "tuned": sum(tuned), "tuned_won": sum(tuned) >= 4, "replication": sum(repl), "replication_met": sum(repl) >= 4,
            "delay_opponent": dop, "delay": sum(delay), "delay_won": sum(delay) >= 4, "severe_ok": sum(severe) >= 4,
            "single": o["single_rule"], "single_cleared": sum(single), "copy_cleared": None if copy_rule not in counts else sum(clears(P, A(copy_rule), 10.0) for P in pol),
            "worse_than_nc_on_ttc": sum(worse_nc)}


def harm(T: dict, o: dict, n: int = LEARNERS) -> list:
    """Map cells where at least 4 of 5 policies are clearly worse than the reference, on delay by over 2 % or TTC by over 10 %."""
    out = []
    for cell in COND:
        for q in (4600.0, Q):
            if cell in PRIMARY and q == Q:
                continue
            A = lambda name: T[(f"{cell}|{name}", q)]
            for ref in ("p333", o["single_rule"]):
                k = 0
                for i in range(n):
                    d, t = effect(A(f"d{i}"), A(ref), "all_delay", pct=P95), effect(A(f"d{i}"), A(ref), "ttc_net", pct=P95)
                    k += (d[0] < -2.0 and d[2] < 0) or (t[0] < -10.0 and t[2] < 0)
                if k >= 4:
                    out.append((cell, q, ref, k))
    return out


def blind_spots(T: dict) -> list:
    """Checks every arm before the claim table is read: 1-Hz against step braking, whole against half second TTC."""
    out = []
    for (n, q), A in T.items():
        b, s = med(A, "brake_net"), max(med(A, "b3_step"), 1.0)
        t, h = med(A, "ttc_net"), max(med(A, "ttc_half"), 1.0)
        if abs(b / s - 1.0) > 0.05 or (h > 50 and abs(t / h - 1.0) > 0.05):
            out.append((n, q, round(b / s, 3), round(t / h, 3)))
    return out


if __name__ == "__main__":
    d = Path(sys.argv[1])
    T = load(d / "eval_primary.jsonl", d / "eval_map_x.jsonl", d / "eval_map.jsonl")
    o = json.load(open(d / "opponents.json"))
    print("arms over the 5 % limit, 1-Hz against step or half second:", blind_spots(T), flush=True)
    rows = []
    for cell in PRIMARY:
        r = read_cell(T, cell, o)
        print(json.dumps(r), flush=True)
        for name in sorted({k[0].split("|")[1] for k in T if k[0].startswith(cell + "|") and k[1] == Q}):
            A = T[(f"{cell}|{name}", Q)]
            row = {"cell": cell, "name": name}
            for key in ("all_delay", "delay", "passed", "N", "ttc_net", "ttc15", "sev3", "b3_step", "b7_step", "alks_full_moving", "alks_full_creep", "collisions", "pass_straight", "end_stop", "end_stop2", "fuel_step"):
                row[key] = round(med(A, key), 1)
            for ref in r["counts"]:
                e = effect(A, T[(f"{cell}|{ref}", Q)], "ttc_net")
                row[f"ttc_vs_{ref}"] = f"{e[0]} [{e[1]}, {e[2]}]"
            rows.append(row)
    print("harm cells:", harm(T, o), flush=True)
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with open(sys.argv[2], "w", newline="") as f:
        w = csv.DictWriter(f, keys)
        w.writeheader()
        w.writerows(rows)
