"""Fig. 2: the information ladder per cell (P1b): strongest L0 arm -> ID -> IP -> ORX_4 -> OR_in, median delay.

Reads only docs/research/results/p1b_result.json (V112/V113, code 93ba655).
Usage: python paper/figures/fig_ladder.py  -> paper/figures/fig_ladder.pdf
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
lad = json.loads((ROOT / "docs/research/results/p1b_result.json").read_text())["eval"]["fig1_ladder"]
cells = [("slow_q1600", "Slowdown, 1600 veh/h"), ("slow_q2000", "Slowdown, 2000 veh/h"),
         ("block_q1600", "Lane crawl, 1600 veh/h"), ("block_q2000", "Lane crawl, 2000 veh/h")]
colour = {"L0": "#4a78b5", "ID": "#8fb1d9", "IP": "#d1802f", "ORX_4": "#bdbdbd", "OR_in": "#e0e0e0"}

fig, axes = plt.subplots(1, 4, figsize=(7.1, 1.9), sharey=False)
for ax, (key, title) in zip(axes, cells):
    rungs = lad[key]["rungs"]
    names, vals, cols = [], [], []
    for i, r in enumerate(rungs):
        name = r["arm"]
        names.append({"ORX_4": "ORX$_4$", "OR_in": "OR$_{in}$"}.get(name, name) if i else f"{name}\n(L0)")
        vals.append(r["median_delay_s"])
        cols.append(colour["L0"] if i == 0 else colour.get(name, "#999999"))
    ax.bar(range(len(vals)), vals, color=cols, edgecolor="black", linewidth=0.3)
    for x, v in enumerate(vals):
        ax.text(x, v + max(vals) * 0.02, f"{v:.0f}", ha="center", fontsize=6)
    ax.set_xticks(range(len(vals)))
    ax.set_xticklabels(names, fontsize=6)
    ax.set_title(title, fontsize=7)
    ax.tick_params(axis="y", labelsize=6)
    ax.set_ylim(0, max(vals) * 1.15)
axes[0].set_ylabel("Median delay (s/veh)", fontsize=7)
fig.tight_layout(w_pad=0.6)
out = Path(__file__).with_suffix(".pdf")
fig.savefig(out)
print("wrote", out)
