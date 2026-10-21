"""Fig. 3: confirmation C1 (lane crawl, 1600 veh/h, 100 fresh seeds): gain of the type plan IP over always-on PI,
rel = median(PI - IP) / median(PI) with 95 % CI, at baseline, with detection delays and with red-light runners.

Reads only docs/research/results/p1b_c1_result.json (V116, code e7dd561).
Usage: python paper/figures/fig_c1_robust.py  -> paper/figures/fig_c1_robust.pdf
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
c1 = json.loads((ROOT / "docs/research/results/p1b_c1_result.json").read_text())["c1"]
desc = c1["descriptive"]
rows = [("Baseline (C1)", c1["C1"]["all_seeds"]),
        ("Detection +30 s", desc["PI_vs_IP_d30"]["all_seeds"]),
        ("Detection +60 s", desc["PI_vs_IP_d60"]["all_seeds"]),
        ("Detection +120 s", desc["PI_vs_IP_d120"]["all_seeds"]),
        ("Runners 10 %", desc["PI_s0.1_vs_IP_s0.1"]["all_seeds"]),
        ("Runners 30 %", desc["PI_s0.3_vs_IP_s0.3"]["all_seeds"])]

fig, ax = plt.subplots(figsize=(3.4, 1.9))
for y, (lab, s) in enumerate(rows):
    m, lo, hi = 100 * s["rel"], 100 * s["rel_ci"][0], 100 * s["rel_ci"][1]
    ax.errorbar(m, y, xerr=[[m - lo], [hi - m]], fmt="o", color="#d1802f" if y == 0 else "#555555",
                ms=3.5, capsize=2, lw=0.9)
    ax.text(hi + 1.0, y, f"{m:.1f}", va="center", fontsize=6)
ax.axvline(0, color="black", lw=0.6)
ax.axvline(10, color="#4a78b5", lw=0.6, ls="--")
ax.set_yticks(range(len(rows)))
ax.set_yticklabels([r[0] for r in rows], fontsize=7)
ax.invert_yaxis()
ax.set_xlabel("Delay reduction of IP vs always-on PI (%)", fontsize=7)
ax.tick_params(axis="x", labelsize=6)
fig.tight_layout()
out = Path(__file__).with_suffix(".pdf")
fig.savefig(out)
print("wrote", out)
