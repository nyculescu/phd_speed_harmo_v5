"""EV readings, part 1 (docs/research/protocols/v505_ev_informed_rule.md v2 §2, V508): the sizing pass on throw-away seeds and the
gate. Event cost = all_delay in the cell minus all_delay in S on the same seed. Read once each, by this committed script. Crash drops
(common §4): the union of the stage's dropped seeds leaves every arm, cell and S alike; more than 3 make the stage VOID.

usage: read_ev.py size ROWS.jsonl OUT.json
       read_ev.py gate ROWS.jsonl OUT.json --size SIZE.json"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "planb"))
sys.path.insert(0, str(HERE))
import drain  # noqa: E402
import read6  # noqa: E402
import v5  # noqa: E402
from read_m2 import arr, drops_of, load, usable  # noqa: E402

SIZE_SHARE = 0.15     # EV §2: no control's median event cost at least 15 % of S's median delay
G1A = 10.0     # EV §2 gate: delay in the cell at least 10 % above S, CI lower bound above 0
DRAIN_VEH = 2.0


def drain_excess(T: dict, cell: str, arm: str, seeds: list) -> dict:
    """V486's form: the mean over seeds of (cell - S) of each queue's mean over 1,500-1,800 s, in vehicles."""
    c = [drain.series_from_row(T[(cell, arm)][s]) for s in seeds]
    s_ = [drain.series_from_row(T[("S", arm)][s]) for s in seeds]
    return {k: float(np.mean([x[k] - y[k] for x, y in zip(c, s_)])) for k in drain.KEYS}


def stuck(T: dict, cell: str, arm: str, seeds: list) -> int:
    return int(sum(T[(cell, arm)][s]["m_stuck_n"] > 0 for s in seeds))


def level_row(T: dict, cell: str, seeds: list) -> dict:
    out = {}
    for arm in ("nc", "p333"):
        cost = arr(T, cell, arm, seeds, "all_delay") - arr(T, "S", arm, seeds, "all_delay")
        s_med = float(np.median(arr(T, "S", arm, seeds, "all_delay")))
        ex = drain_excess(T, cell, arm, seeds)
        out[arm] = {"cost_median": float(np.median(cost)), "S_median": s_med, "share": float(np.median(cost)) / s_med,
                    "drain_excess": ex, "drain_pass": all(v <= DRAIN_VEH for v in ex.values()), "stuck_rows": stuck(T, cell, arm, seeds)}
    return out


def size(T: dict, seeds: list) -> dict:
    """The mildest limit whose no-control event cost is at least 15 % of S's median delay, with drain passed and no stuck row.
    p333 is printed and not used (EV §2, V456(3))."""
    lv = {f"{x:g}": level_row(T, f"EVA{x:g}", seeds) for x in v5.EV_LADDER}
    ok = [x for x in v5.EV_LADDER if (r := lv[f"{x:g}"]["nc"])["share"] >= SIZE_SHARE and r["drain_pass"] and r["stuck_rows"] == 0]
    return {"levels": lv, "limit_kmh": ok[0] if ok else None, "outcome": "sized" if ok else "VOID", "seeds": [seeds[0], seeds[-1]]}


def gate(T: dict, limit: float, seeds: list) -> dict:
    """G1a for no control and p333 at 95 %, drain as V486 and no stuck row; a failure makes EV VOID."""
    cell = f"EVA{limit:g}"
    st = read6.Stat(len(seeds))
    out = {}
    for arm in ("nc", "p333"):
        e, b = st.eff(arr(T, cell, arm, seeds, "all_delay"), arr(T, "S", arm, seeds, "all_delay"), 1)
        lo, hi = read6.ci(b, read6.P95)
        ex = drain_excess(T, cell, arm, seeds)
        out[arm] = {"g1a": (e, lo, hi), "g1a_pass": e >= G1A and lo > 0, "drain_excess": ex, "drain_pass": all(v <= DRAIN_VEH for v in ex.values()),
                    "stuck_rows": stuck(T, cell, arm, seeds)}
    passed = all(r["g1a_pass"] and r["drain_pass"] and r["stuck_rows"] == 0 for r in out.values())
    return {"limit_kmh": limit, "arms": out, "outcome": "pass" if passed else "VOID", "seeds": [seeds[0], seeds[-1]]}


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("step", choices=("size", "gate"))
    ap.add_argument("rows")
    ap.add_argument("out")
    ap.add_argument("--size")
    x = ap.parse_args(argv)
    rows = Path(x.rows)
    T = load(rows)
    dropped = drops_of(rows)
    seeds, void = usable(v5.seeds("ev_size" if x.step == "size" else "ev_gate"), dropped)
    if void:
        res = {"outcome": "VOID", "reason": "more than 3 seeds dropped", "limit_kmh": None}
    elif x.step == "size":
        res = size(T, seeds)
    else:
        lim = json.loads(Path(x.size).read_text())["limit_kmh"]
        if lim is None:
            raise SystemExit("EV is VOID at sizing: no gate")
        res = gate(T, lim, seeds)
    res["dropped"] = dropped
    v5.pb.cma2.write_json(Path(x.out), res)
    print(x.step, res["outcome"], res.get("limit_kmh"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
