"""Figure: median delay per arm in the C1 confirmation (block_q1600).

Reads only the committed result file, so every number in the paper traces to the baseline:
docs/research/results/p1b_c1_result.json (V116, code e7dd561).
Usage: python paper/figures/fig_c1_delay.py  -> paper/figures/fig_c1_delay.pdf
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "docs/research/results/p1b_c1_result.json"
OUT = Path(__file__).with_suffix(".pdf")

d = json.loads(RES.read_text())["c1"]
rows = d["rows"]
arms = [("NC", "No meter"), ("N", "Normal plan"), ("PI", "Always-on PI"), ("IP", "Type plan")]
vals = [rows[k]["median_delay_s"] for k, _ in arms]

fig, ax = plt.subplots(figsize=(3.4, 1.9))          # one IEEE column
ax.barh([lab for _, lab in arms], vals, color=["#9e9e9e", "#9e9e9e", "#4a78b5", "#d1802f"])
for y, v in enumerate(vals):
    ax.text(v + 3, y, f"{v:.0f}", va="center", fontsize=7)
c1 = d["C1"]["all_seeds"]
ax.set_xlabel("Median delay per vehicle (s)", fontsize=8)
ax.set_title(f"C1: type plan vs PI {100*c1['rel']:.1f} % "
             f"[{100*c1['rel_ci'][0]:.1f}, {100*c1['rel_ci'][1]:.1f}], n = {c1['n']}", fontsize=8)
ax.tick_params(labelsize=7)
ax.set_xlim(0, max(vals) * 1.15)
fig.tight_layout()
fig.savefig(OUT)
print("wrote", OUT)
