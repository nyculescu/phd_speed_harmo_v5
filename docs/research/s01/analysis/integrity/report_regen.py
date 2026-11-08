"""The stored report_rows_*.txt panels regenerated in memory from summary_rows_*.json with measure2's own panel() and METRICS
(no file written to the data folder), compared line by line; plus seeds kept per panel. Read only, run with -I -B."""
import json
import sys
from pathlib import Path

import numpy as np

W = Path("/home/catalin/work/phd/wt/r2-metrics")
sys.path[:0] = [str(W), str(W / "docs/research/round2"), str(W / "docs/research/round1")]
import measure2 as m2  # noqa: E402

RUNS = Path("/home/catalin/work/phd/v5b1_runs")
M = RUNS / "measure_s01_remote"
G = m2.groups(RUNS / "round2")
short = {}
for ph in ("test", "band", "s1"):
    S = json.load(open(M / f"summary_rows_{ph}.json"))
    per = {}
    for k, v in S.items():
        n, q = k.rsplit("|", 1)
        per[(n, float(q))] = {int(s): x for s, x in v.items()}
    cells = sorted({(n.split("|")[0], q) for n, q in per})
    txt = []
    for cell, q in cells:
        arms = {"no control": ["nc"], "p333": ["p333"], "os1_15_10": ["os1_15_10"], "3E-T": ["3e"], "3E-X1": ["3ex1"], "3E-X2": ["3ex2"], **G}
        for title, unit, f in m2.METRICS:
            d = {}
            for lab, names in arms.items():
                runs = [per.get((f"{cell}|{n}", q)) for n in names]
                if any(r is None for r in runs):
                    continue
                seeds = sorted(set.intersection(*[set(r) for r in runs]))
                xs = [np.mean([f(r[s]) for r in runs]) for s in seeds if all(f(r[s]) is not None for r in runs)]
                if xs:
                    d[lab] = xs
                    if len(xs) < len(seeds):
                        short[f"{ph}|{cell}|{q:.0f}|{title}|{lab}"] = f"{len(xs)}/{len(seeds)}"
            if d:
                txt.append(m2.panel(f"{cell} at {q:,.0f} veh/h: {title}", d, unit))
    new = "\n\n".join(txt)
    old = (M / f"report_rows_{ph}.txt").read_text()
    nl, ol = new.splitlines(), old.splitlines()
    diff = [i for i, (a, b) in enumerate(zip(nl, ol)) if a != b]
    print(ph, "lines new/old", len(nl), len(ol), "differing lines", len(diff), "identical text", new == old)
print("panels where seeds were dropped for None (panel|arm: kept/paired):", len(short))
for k, v in list(short.items())[:40]:
    print("  ", k, v)
(Path(__file__).parent / "report_regen.json").write_text(json.dumps(short, indent=1))
