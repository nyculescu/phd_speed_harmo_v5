"""Demand-sweep report (V406): where may DRL have a purpose. Exploratory, 4 paired seeds per level, so trends across levels carry the information.
Effects: median over seeds of the paired difference over the reference's median, in %, then the median over the 5 policies; positive = DRL has less = better."""
import json
import sys
from collections import defaultdict

import numpy as np

import page
from lib import *
from drl_lib import P, H, PM, cards, lines2

SW = "/home/catalin/work/phd/v5b1_runs/sweep/"
OUT = sys.argv[1]
POL = [f"d{i}" for i in range(5)]
CONDS = [("S", "Steady", "--accent"), ("X1", "X1: slowdown downstream of merge 2", "--sem1"), ("X2", "X2: slowdown between the merges", "--entry")]
T = defaultdict(dict)
for r in map(json.loads, open(SW + "sweep.jsonl")):
    T[(r["name"], r["q"])][r["seed"]] = r
LEVELS = sorted({q for _, q in T})


def eff(c, q, p, ref, key):
    A, B = T[(f"{c}|{p}", q)], T[(f"{c}|{ref}", q)]
    s = sorted(set(A) & set(B))
    b = np.array([B[x][key] for x in s], float)
    a = np.array([A[x][key] for x in s], float)
    return float(np.median((b - a) / max(np.median(b), 1e-9) * 100))


def pol_eff(c, q, ref, key):
    return float(np.median([eff(c, q, p, ref, key) for p in POL]))


def smooth(y, k=3):
    return [float(np.median(y[max(0, i - k // 2): i + k // 2 + 1])) for i in range(len(y))]


def med(c, q, n, key):
    if n == "DRL":
        return float(np.median([np.median([r[key] for r in T[(f"{c}|{p}", q)].values()]) for p in POL]))
    return float(np.median([r[key] for r in T[(f"{c}|{n}", q)].values()]))


def effect_chart(ref, key, title, good):
    ser = []
    for c, name, col in CONDS:
        y = [pol_eff(c, q, ref, key) for q in LEVELS]
        ser.append({"x": LEVELS, "y": [round(v, 1) for v in y], "name": f"{c}, each level", "color": col, "sw": 1, "dash": "2 3", "legend": False})
        ser.append({"x": LEVELS, "y": [round(v, 1) for v in smooth(y)], "name": name, "color": col, "sw": 2.6})
    lo = min(min(s["y"]) for s in ser)
    hi = max(max(s["y"]) for s in ser)
    ser.append({"x": [LEVELS[0], LEVELS[-1]], "y": [0, 0], "name": "no difference", "color": "--dim", "sw": 1, "hover": False, "legend": False})
    return lines2(ser, w=560, h=270, title=title, xlabel="Demand, veh/h", ylabel=f"% {good} for DRL  (above 0 = DRL better)", d=1, ylim=(min(lo, -10) - 5, max(hi, 10) + 5))


def level_chart(c, key, title):
    arms = [("nc", "No control", "--sem1"), ("p333", "0.8 s rule", "--ink"), ("os1_15_10", "Best tuned rule", "--c8"), ("DRL", "DRL, median of 5", "--accent")]
    ser = [{"x": LEVELS, "y": [round(med(c, q, n, key) / (1000 if key == "all_delay" else 1), 1) for q in LEVELS], "name": lab, "color": col, "sw": 2.4 if n == "DRL" else 1.6} for n, lab, col in arms]
    return lines2(ser, w=420, h=240, title=title, xlabel="Demand, veh/h", d=0)


def band_table():
    rows = []
    for q in LEVELS:
        r = [f"{int(q):,}"]
        for c, _, _ in CONDS:
            t_rule, d_rule = pol_eff(c, q, "os1_15_10", "ttc_net"), pol_eff(c, q, "os1_15_10", "all_delay")
            t_p, d_p = pol_eff(c, q, "p333", "ttc_net"), pol_eff(c, q, "p333", "all_delay")
            t_nc, d_nc = pol_eff(c, q, "nc", "ttc_net"), pol_eff(c, q, "nc", "all_delay")
            if t_rule >= 10 and d_rule >= -2:
                tag, col = "DRL ahead of the best rule", "--entry"
            elif t_p >= 10 and d_p >= -2:
                tag, col = "DRL ahead of the 0.8 s rule only", "--accent"
            elif abs(t_p) < 10 and abs(d_p) < 2:
                tag, col = "No difference from the rules", "--c8"
            else:
                tag, col = "DRL behind or mixed", "--sem1"
            tip = f"{c} at {int(q)}: vs best rule TTC {t_rule:+.0f} %, delay {d_rule:+.0f} %; vs 0.8 s rule TTC {t_p:+.0f}, delay {d_p:+.0f}; vs no control TTC {t_nc:+.0f}, delay {d_nc:+.0f} (+ = DRL better)"
            r.append(f'<span class="chip" style="--c:var({col})" title="{e(tip)}">{e(tag)}</span>')
        rows.append(r)
    return table(["Demand, veh/h"] + [n for _, n, _ in CONDS], rows)


body = "<h1>Where may DRL have a purpose? A demand sweep</h1>"
body += f'<p class="path">Exploratory, report-only (V406-V407). 16 demand levels drawn at random from 3,800-6,000 veh/h; steady traffic, X1 and X2; the 5 per-CAV PPO policies against no control, the fixed 0.8 s rule (p333), the best tuned rule (os1_15_10) and the single rule; 4 paired seeds per level. The policies were trained at 4,090-5,300; the rules were tuned at 5,300 only.</p>'
body += P("**How to read.** Every chart shows how much better DRL is, in %: **above the zero line, DRL is better; below it, DRL is worse.** For close-following (TTC), better means fewer seconds where a car would reach the one ahead within 3 s; for delay, it means less lost time. Thin dotted lines are single levels (4 seeds, noisy); thick lines are a running median over 3 neighbouring levels.")
body += "<h2 id='s1'>1. Against the fixed 0.8 s rule</h2>" + '<div class="charts"><div>' + effect_chart("p333", "ttc_net", "Close-following: how many % fewer than the 0.8 s rule", "fewer") + "</div><div>" + effect_chart("p333", "all_delay", "Delay: how many % less than the 0.8 s rule", "less") + "</div></div>"
body += "<h2 id='s2'>2. Against the best tuned rule (os1_15_10)</h2>" + '<div class="charts"><div>' + effect_chart("os1_15_10", "ttc_net", "Close-following: how many % fewer than the best rule", "fewer") + "</div><div>" + effect_chart("os1_15_10", "all_delay", "Delay: how many % less than the best rule", "less") + "</div></div>"
body += "<h2 id='s3'>3. Against no control</h2>" + '<div class="charts"><div>' + effect_chart("nc", "ttc_net", "Close-following: how many % fewer than no control", "fewer") + "</div><div>" + effect_chart("nc", "all_delay", "Delay: how many % less than no control", "less") + "</div></div>"
body += "<h2 id='s4'>4. The raw levels: who has fewer and less</h2>"
for c, name, _ in CONDS:
    body += f"<h4>{e(name)}</h4>" + '<div class="charts"><div>' + level_chart(c, "ttc_net", "Close-following seconds (lower is better)") + "</div><div>" + level_chart(c, "all_delay", "Delay, thousand vehicle-seconds (lower is better)") + "</div></div>"
body += "<h2 id='s5'>5. The band, level by level</h2>" + band_table()
body += H("Labels use the median over the 5 policies and 4 seeds, against the thresholds of confirmatory 3: at least 10 % fewer close-following seconds, at most 2 % more delay. Hover a label for all six numbers. With 4 seeds, a single level can flip; look for runs of the same label.")
toc = "".join(f'<a href="#s{i}"><small>{i}</small>{t}</a>' for i, t in enumerate(("vs 0.8 s rule", "vs best rule", "vs no control", "Raw levels", "The band"), 1))
open(OUT, "w").write(page.shell("Demand Sweep", toc, body, "Exploratory; computed from /home/catalin/work/phd/v5b1_runs/sweep/sweep.jsonl."))
print("levels", len(LEVELS), "written", OUT)
