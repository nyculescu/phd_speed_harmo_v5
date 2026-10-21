"""Fig. 1: schematic of the plant (not to scale): 4 lanes -> 2 -> 1 (lanes per edge 4/4/4/2/1), one mainline signal
across all 4 lanes, and the two incident types (slowdown on the 1-lane bottleneck; crawling lane on the 2-lane edge).
No data are read; the geometry follows v5b/d1/netgen_bn4.py (edge lane counts).
Usage: python paper/figures/fig_plant.py  -> paper/figures/fig_plant.pdf
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

LANE_W = 1.0
edges = [(0, 3, 4), (3, 6, 4), (6, 9, 4), (9, 12, 2), (12, 15, 1)]   # (x0, x1, lanes)

fig, ax = plt.subplots(figsize=(3.4, 1.35))
for x0, x1, n in edges:
    h = n * LANE_W
    ax.add_patch(Rectangle((x0, -h / 2), x1 - x0, h, facecolor="#eeeeee", edgecolor="#555555", lw=0.6))
    for k in range(1, n):
        y = -h / 2 + k * LANE_W
        ax.plot([x0, x1], [y, y], color="#999999", lw=0.4, ls=(0, (3, 3)))
# mainline signal across all 4 lanes at the end of edge 2 (node 3)
ax.plot([6, 6], [-2, 2], color="#c62828", lw=2.2)
ax.text(6, 2.35, "mainline signal\n(G 6 s, amber 3 s, red ≥ 2 s)", ha="center", va="bottom", fontsize=5.5)
# incidents
ax.add_patch(Rectangle((12.4, -0.5), 2.2, 1.0, facecolor="#ffcc80", edgecolor="#ef6c00", lw=0.6))
ax.text(13.5, -1.0, "slowdown\n(5 m/s)", ha="center", va="top", fontsize=5.5)
ax.add_patch(Rectangle((9.4, 0.0), 2.2, 1.0, facecolor="#ffab91", edgecolor="#d84315", lw=0.6))
ax.text(10.5, 1.25, "lane crawl\n(1 m/s)", ha="center", va="bottom", fontsize=5.5)
# demand and queue storage
ax.annotate("", xy=(2.6, 0), xytext=(0.2, 0), arrowprops=dict(arrowstyle="->", lw=0.8))
ax.text(1.4, -2.35, "demand q\n(1600 / 2000 veh/h)", ha="center", va="top", fontsize=5.5)
ax.text(3.0, 2.35, "queue storage", ha="center", va="bottom", fontsize=5.5)
ax.annotate("", xy=(15.6, 0), xytext=(14.8, 0), arrowprops=dict(arrowstyle="->", lw=0.8))
ax.set_xlim(-0.3, 16.0)
ax.set_ylim(-3.6, 3.6)
ax.set_aspect("equal")
ax.axis("off")
fig.tight_layout(pad=0.1)
out = Path(__file__).with_suffix(".pdf")
fig.savefig(out)
print("wrote", out)
