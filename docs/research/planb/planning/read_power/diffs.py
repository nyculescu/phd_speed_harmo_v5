"""Part 1: per-seed paired differences of the v3w arm against every opponent, per cell and level.
d_i = sign * (P_i - O_i) / median(O) * 100 (positive = v3w better); effect = median(d) with round 2's 95 % percentile bootstrap
(20,000 resamples, default_rng(20261104), denominator fixed), as conf3/common.raw."""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from load_arms import METRICS, load  # noqa: E402

OUT = Path(__file__).resolve().parent
SHOW = ("all_delay", "ttc_net", "ev4_ca", "ev5_alks", "b45_step")


def rel(P, O, sign):
    ref = max(float(np.median(O)), 1e-9)
    return sign * (P - O) / ref * 100.0, ref


def raw_ci(d, pct=(2.5, 97.5)):
    rng = np.random.default_rng(20261104)
    lo, hi = np.percentile(np.median(d[rng.integers(0, len(d), (20000, len(d)))], axis=1), pct)
    return float(np.median(d)), float(lo), float(hi)


def main():
    cells = load()
    res = {}
    lines = []
    for cell, C in cells.items():
        A = C["arms"]
        opps = C["rules"] + (["nc"] if C["has_nc"] else [])
        res[cell] = {}
        dag = "" if cell.startswith("X") else " (outside the plant's stated intended use, V462(4))"
        lines.append(f"\n## {cell}{dag}: n = {len(C['seeds'])} seeds, v3w medians: "
                     + ", ".join(f"{k} {np.median(A['v3w'][k]):.1f}" for k in SHOW))
        lines.append("| opponent | metric | O median | v3w median | effect % [95 % CI] | SD(d) % | IQR(d) % | SD abs |")
        lines.append("|---|---|---|---|---|---|---|---|")
        for o in opps:
            res[cell][o] = {}
            for k in SHOW:
                s = METRICS[k]
                d, ref = rel(A["v3w"][k], A[o][k], s)
                pt, lo, hi = raw_ci(d)
                sd = float(np.std(d, ddof=1))
                iqr = float(np.subtract(*np.percentile(d, [75, 25])))
                sda = float(np.std(A["v3w"][k] - A[o][k], ddof=1))
                res[cell][o][k] = {"O_med": ref, "P_med": float(np.median(A["v3w"][k])), "pt": pt, "lo": lo, "hi": hi,
                                   "sd": sd, "iqr": iqr, "sd_abs": sda}
                lines.append(f"| {o} | {k} | {ref:.1f} | {np.median(A['v3w'][k]):.1f} | {pt:+.1f} [{lo:+.1f}, {hi:+.1f}] | "
                             f"{sd:.1f} | {iqr:.1f} | {sda:.1f} |")
    (OUT / "diffs.json").write_text(json.dumps(res, indent=1))
    (OUT / "diffs_table.md").write_text("\n".join(lines) + "\n")
    # Compact summary: per cell and metric, the smallest effect over rules, and the SD range over rules
    summ = ["| cell | metric | min effect over rules (opponent) | SD(d) range over rules % | vs nc |", "|---|---|---|---|---|"]
    for cell, R in res.items():
        rules = [o for o in R if o != "nc"]
        for k in SHOW:
            mn = min(rules, key=lambda o: R[o][k]["pt"])
            sds = [R[o][k]["sd"] for o in rules]
            nc = R.get("nc", {}).get(k)
            ncs = f"{nc['pt']:+.1f} [{nc['lo']:+.1f}, {nc['hi']:+.1f}] SD {nc['sd']:.1f}" if nc else "-"
            summ.append(f"| {cell} | {k} | {R[mn][k]['pt']:+.1f} [{R[mn][k]['lo']:+.1f}, {R[mn][k]['hi']:+.1f}] ({mn}) | "
                        f"{min(sds):.1f}-{max(sds):.1f} | {ncs} |")
    (OUT / "diffs_summary.md").write_text("\n".join(summ) + "\n")
    print("\n".join(summ))


if __name__ == "__main__":
    main()
