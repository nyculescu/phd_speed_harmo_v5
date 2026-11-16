"""Unpaired panel medians, p333 against v3w, from the report_rows_*.txt panels (16 non-decision metrics)."""
import re
from pathlib import Path

D = Path("/home/catalin/work/phd/v5b1_runs/measure_s01_remote")
HIGHER = {"car speed, median", "ALKS speed, median", "car decel, 5th pct"}
SKIP = {"decisions applied (level moved)", "excess level changes per ALKS", "reversals per change", "ALKS at the longest level, V2V on", "policy confidence, median"}
for kind in ("s1", "band", "test"):
    txt = (D / f"report_rows_{kind}.txt").read_text().split("\n\n")
    tally = {}
    for blk in txt:
        lines = blk.strip().splitlines()
        if not lines:
            continue
        m = re.match(r"(\S+) at ([\d,]+) veh/h: (.*), axis", lines[0])
        if not m:
            continue
        cell, q, title = m.group(1), m.group(2), m.group(3)
        if title in SKIP:
            continue
        med = {}
        for ln in lines[1:]:
            lab = ln[:16].strip()
            mm = re.search(r"med (\S+)", ln)
            if mm:
                med[lab] = float(mm.group(1))
        if "p333" not in med or "v3w" not in med:
            continue
        a, b = med["p333"], med["v3w"]
        better = "eq" if a == b else ("p333" if (a > b) == (title in HIGHER) else "v3w")
        t = tally.setdefault(f"{cell} {q}", {"p333": [], "v3w": [], "eq": []})
        t[better].append(title)
    for k, t in tally.items():
        print(k, {x: len(y) for x, y in t.items()}, "| v3w better on:", t["v3w"])
