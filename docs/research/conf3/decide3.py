"""The reading of confirmatory 3, as fixed in the protocol. usage: decide3.py out_dir table.csv map.csv"""
import csv
import json
import sys
from pathlib import Path

from common import COND, LEARNERS, PRIMARY, Q, check_rows, collisions, effect, load, med, paired_median, raw, val

P95 = (2.5, 97.5)
TABLE = ("all_delay", "delay", "passed", "N", "ttc_net", "ttc2", "ttc15", "sev3", "b3_step", "b45_step", "b7_step", "alks_b3_step", "alks_b45_step", "alks_b7_step", "free_brake_alks_step", "alks_full_moving", "alks_full_creep",
         "pass_straight", "end_stop", "end_stop2", "delay_ramp", "delay_ramp2", "fuel_step", "dist_step", "jerk_step")
SPLITS = tuple(f"{m}_{x}" for m in ("ttc3", "sev3") for x in ("r_3", "r_4a", "r_ramp2", "r_rest", "s_lo", "s_mid", "s_hi", "p_before", "p_taper", "p_hold", "p_after", "p_rest"))


def limits(P: dict, O: dict) -> dict:
    """The side limits a policy must meet against one opponent."""
    ev = raw(P, O, "alks_full_moving")[0] >= -5.0 or paired_median(P, O, "alks_full_moving") <= 5.0
    return {"delay": raw(P, O, "all_delay")[0] >= -2.0, "flow": raw(P, O, "passed", 1)[0] >= -0.5, "brake": raw(P, O, "b3_step")[0] >= -5.0,
            "events": ev, "coll": collisions(P) <= collisions(O) + 1}


def fails(P: dict, O: dict, margin: float) -> list:
    """What stops a policy against one opponent; empty if it clears."""
    e = raw(P, O, "ttc_net")
    out = [] if e[0] >= margin else ["margin"]
    out += [] if e[1] > 0 else ["ci"]
    out += [] if paired_median(O, P, "ttc_net") >= 20.0 else ["per run"]
    return out + [k for k, ok in limits(P, O).items() if not ok]


def clears(P: dict, O: dict, margin: float) -> bool:
    return not fails(P, O, margin)


def anchored(P: dict, p333: dict) -> bool:
    return raw(P, p333, "all_delay")[0] >= -5.0 and raw(P, p333, "passed", 1)[0] >= -1.0


def delay_clears(P: dict, O: dict) -> bool:
    d = raw(P, O, "all_delay")
    return d[0] >= 5.0 and d[1] > 0 and raw(P, O, "passed", 1)[0] >= -0.5 and raw(P, O, "ttc_net")[0] >= -10.0 and raw(P, O, "b3_step")[0] >= -10.0 and collisions(P) <= collisions(O) + 1


def read_cell(T: dict, cell: str, o: dict, n: int = LEARNERS, q: float = Q) -> dict:
    A = lambda name: T[(f"{cell}|{name}", q)]
    pol = [A(f"d{i}") for i in range(n)]
    p333, nc = A("p333"), A("nc")
    c = o["cells"][cell]
    names = list(dict.fromkeys(["p333", *c["forms"].values()]))
    counts = [r for r in names if raw(A(r), p333, "all_delay")[0] >= -2.0]
    blocked = [{r: fails(P, A(r), 10.0) for r in counts if fails(P, A(r), 10.0)} for P in pol]
    tuned = [not b and anchored(P, p333) for b, P in zip(blocked, pol)]
    repl = [clears(P, p333, 30.0) for P in pol]
    dop = min((c["delay_opponent"], "p333"), key=lambda r: med(A(r), "all_delay"))
    delay = [delay_clears(P, A(dop)) for P in pol]
    severe = [all(paired_median(P, A(r), "sev3") <= 0.0 for r in counts) for P in pol]
    single = [clears(P, A(o["single_rule"]), 10.0) and anchored(P, p333) for P in pol]
    copy_arm = (f"{cell}|copy", q) in T
    copy_counts = copy_arm and raw(A("copy"), p333, "all_delay")[0] >= -2.0
    worse_nc = [raw(P, nc, "ttc_net")[2] < 0 for P in pol]
    strongest = min(counts, key=lambda r: med(A(r), "ttc_net"))
    gain = [effect(P, A(strongest), "ttc_net") for P in pol]
    condition_rule = effect(A(strongest), A(o["single_rule"]), "ttc_net")
    drl = sorted(raw(P, A(o["single_rule"]), "ttc_net")[0] for P in pol)[n // 2]
    return {"cell": cell, "counts": counts, "excluded": [r for r in names if r not in counts], "only_p333": counts == ["p333"],
            "tuned": sum(tuned), "tuned_won": sum(tuned) >= 4, "replication": sum(repl), "replication_met": sum(repl) >= 4,
            "delay_opponent": dop, "delay": sum(delay), "delay_won": sum(delay) >= 4, "severe_ok": sum(t and s for t, s in zip(tuned, severe)) >= 4,
            "single": o["single_rule"], "single_cleared": sum(single), "single_won": sum(single) >= 4, "copy_counts": copy_counts,
            "copy_cleared": sum(clears(P, A("copy"), 10.0) for P in pol) if copy_arm else None,
            "worse_than_nc_on_ttc": sum(worse_nc), "nc_delay_more_pct": round(sorted(raw(nc, P, "all_delay", 1)[0] for P in pol)[n // 2], 1),
            "strongest": strongest, "ttc_gain_on_strongest": gain, "blocked": blocked,
            "adaptation": {"per_condition_vs_single": condition_rule, "drl_vs_single_median": round(drl, 1), "share_closed": round(drl / condition_rule[0], 2) if condition_rule[1] > 0 and condition_rule[0] else None}}


def harm(T: dict, o: dict, n: int = LEARNERS) -> list:
    """Map cells where at least 4 of 5 policies are clearly worse than the reference, on delay by over 2 % or TTC by over 10 %."""
    out = []
    for cell in COND:
        for q in (4600.0, Q):
            if cell in PRIMARY and q == Q:
                continue
            A = lambda name: T[(f"{cell}|{name}", q)]
            for ref in dict.fromkeys(("p333", o["single_rule"])):
                k = 0
                for i in range(n):
                    d, t = raw(A(f"d{i}"), A(ref), "all_delay", pct=P95), raw(A(f"d{i}"), A(ref), "ttc_net", pct=P95)
                    k += (d[0] < -2.0 and d[2] < 0) or (t[0] < -10.0 and t[2] < 0)
                if k >= 4:
                    out.append((cell, q, ref, k))
    return out


def blind_spots(T: dict) -> list:
    """Checks every arm before the claim table is read: 1-Hz against step braking, whole against half second TTC."""
    out = []
    for (n, q), A in T.items():
        b, s, t, h = med(A, "brake_net"), med(A, "b3_step"), med(A, "ttc_net"), med(A, "ttc_half")
        if (s >= 50 and abs(b / s - 1.0) > 0.05) or (h >= 50 and abs(t / h - 1.0) > 0.05):
            out.append((n, q, round(b / max(s, 1.0), 3), round(t / max(h, 1.0), 3)))
    return out


def row_of(A: dict, name: str, cell: str, q: float) -> dict:
    r = {"cell": cell, "q": q, "name": name, "collisions_total": collisions(A)}
    r |= {k: round(med(A, k), 1) for k in TABLE}
    return r


if __name__ == "__main__":
    d = Path(sys.argv[1])
    T = load(d / "eval_primary.jsonl", d / "eval_map_x.jsonl", d / "eval_map.jsonl")
    check_rows(T, 20)
    o = json.load(open(d / "opponents.json"))
    print("arms over the 5 % limit, 1-Hz against step or half second:", blind_spots(T), flush=True)
    rows = []
    for cell in PRIMARY:
        r = read_cell(T, cell, o)
        print(json.dumps(r), flush=True)
        for name in sorted({k[0].split("|")[1] for k in T if k[0].startswith(cell + "|") and k[1] == Q}):
            A = T[(f"{cell}|{name}", Q)]
            row = row_of(A, name, cell, Q) | {k: round(med(A, k), 1) for k in SPLITS}
            for ref in r["counts"]:
                for key, sign, lab in (("ttc_net", -1, "ttc"), ("all_delay", -1, "delay"), ("passed", 1, "flow")):
                    e = effect(A, T[(f"{cell}|{ref}", Q)], key, sign)
                    row[f"{lab}_vs_{ref}"] = f"{e[0]} [{e[1]}, {e[2]}]"
            rows.append(row)
    print("harm cells:", harm(T, o), flush=True)
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with open(sys.argv[2], "w", newline="") as f:
        w = csv.DictWriter(f, keys)
        w.writeheader()
        w.writerows(rows)
    m = [row_of(A, k[0].split("|")[1], k[0].split("|")[0], k[1]) for k, A in sorted(T.items())]
    with open(sys.argv[3], "w", newline="") as f:
        w = csv.DictWriter(f, list(m[0]))
        w.writeheader()
        w.writerows(m)
