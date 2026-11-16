"""(a) Decision metrics of the policy arms per cell and demand level (median over seeds, 95 % bootstrap CI of the median), and
X1 minus X2 paired by seed (same 40 seeds, same demand draw). Rules are listed for the level-choice fields as a reference."""
import json
import sys

from common_dec import GROUPS, RULES, load_table, arm_values, med_ci, paired_diff, fmt, HERE

CELLS = [("test", "X1", 5300.0), ("test", "X2", 5300.0)] + [("band", "B", q) for q in (4500.0, 5000.0, 5250.0, 5500.0, 6000.0)] + \
        [("s1", "B", q) for q in (3500.0, 7000.0)]
FIELDS = ["applied_share", "kept_share", "reversal_share", "excess_per_veh", "changes_per_veh", "asked_per_veh", "share0", "share1", "share2",
          "share3", "gap_on", "want0", "want1", "want2", "want3", "conf_med", "conf_p05", "conf_lt05", "entropy", "v2v_on", "density",
          "lv_3", "lv_4", "lv_4a", "lv_5"]


def main() -> int:
    M = load_table()
    out, n_pair = {}, 0
    arms = {**GROUPS, **{k: v for k, v in RULES.items() if k != "nc"}}
    for g, names in arms.items():
        out[g] = {"cells": {}, "x1_minus_x2": {}}
        for key in CELLS:
            if key not in M or any(n not in M[key] for n in names):
                continue
            lab = f"{key[1]}{key[2]:.0f}"
            out[g]["cells"][lab] = {}
            for f in FIELDS:
                A = arm_values(M, key, names, f)
                if len(A) >= 5:
                    out[g]["cells"][lab][f] = med_ci(A)
        for f in FIELDS:
            A, Bv = arm_values(M, CELLS[0], names, f), arm_values(M, CELLS[1], names, f)
            if len(set(A) & set(Bv)) >= 5:
                out[g]["x1_minus_x2"][f] = paired_diff(A, Bv)
                n_pair += 1
    (HERE / "analysis_a.json").write_text(json.dumps(out, indent=1))
    lines = []
    for g in out:
        lines.append(f"== {g}")
        cells = list(out[g]["cells"])
        for f in FIELDS:
            row = [f"{c}: {out[g]['cells'][c][f][0]:.3f} [{out[g]['cells'][c][f][1]:.3f},{out[g]['cells'][c][f][2]:.3f}]" for c in cells if f in out[g]["cells"][c]]
            if row:
                d = out[g]["x1_minus_x2"].get(f)
                lines.append(f"  {f:<15} " + "  ".join(row) + (f"  | X1-X2 {fmt(d)}" if d else ""))
    lines.append(f"paired X1-X2 comparisons: {n_pair}")
    (HERE / "analysis_a.txt").write_text("\n".join(lines))
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
