"""Results page: confirmatory 3 and 3b, every cell, who wins and by how much. Statistic: the protocol's median of paired differences over the
reference median, positive = the policy has less; 97.5 % percentile bootstrap. Run with PYTHONPATH on the frozen code."""
import json

import numpy as np

import page
from lib import *
from drl_lib import P, H, PM, cards
from common import load, raw, med

C3 = "/home/catalin/work/phd/v5b1_runs/conf3/"
OUT = "/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/reports/2026-11-05_19-22/drl_results_2026-11-05_19-22.html"
POL = [f"d{i}" for i in range(5)]
T = load(C3 + "eval_primary.jsonl", C3 + "eval_map_x.jsonl", C3 + "eval_map.jsonl")
F = load("/home/catalin/work/phd/v5b1_runs/conf3b/eval_x2.jsonl")
O = json.load(open(C3 + "opponents.json"))
COND = {"S": "Steady", "H1": "H1: slow truck every 300 s", "H2": "H2: ramp bursts", "X1": "X1: slowdown downstream of merge 2, 25 km/h, twice", "X2": "X2: slowdown between the merges, 30 km/h, 180 s"}
CELLS = [("S", 4600.0, T, ""), ("S", 5300.0, T, ""), ("H1", 4600.0, T, ""), ("H1", 5300.0, T, ""), ("H2", 4600.0, T, ""), ("H2", 5300.0, T, ""),
         ("X1", 4600.0, T, ""), ("X1", 5300.0, T, "primary"), ("X2", 4600.0, T, ""), ("X2", 5300.0, T, "primary"), ("X2", 5300.0, F, "fresh seeds")]
RULES = {"X1": ["p333"], "X2": ["p333", "r4a1", "lr1000_16_2", "os1_15_10"]}
FRESH_RULES = ["p333", "os1_15_10"]


def A(Tb, c, q, n):
    return Tb.get((f"{c}|{n}", q))


def pe(Tb, c, q, ref, key, sign=-1):
    R = A(Tb, c, q, ref)
    return [raw(A(Tb, c, q, p), R, key, sign) for p in POL]


def lab(c, q, tag):
    return f"{c} {int(q):,}" + (f" ({tag})" if tag else "")


def colour(v, lim=50.0):
    return ("--accent" if v >= 0 else "--sem1"), min(abs(v) / lim, 1.0)


def say(v, good, bad, d=0):
    """A percent in words: v > 0 means the policy has less, which is better."""
    if abs(v) < 0.5:
        return "no difference"
    return f"{abs(v):.{d}f} % {good if v > 0 else bad}"


def grid():
    cols = [("Close-following (TTC)", "vs the 0.8 s rule", "p333", "ttc_net", "fewer", "more"), ("Delay", "vs the 0.8 s rule", "p333", "all_delay", "less", "more"),
            ("Close-following (TTC)", "vs no control", "nc", "ttc_net", "fewer", "more"), ("Delay", "vs no control", "nc", "all_delay", "less", "more")]
    cw, ch, lw, top = 165, 38, 220, 66
    b = ""
    for g, (gt, colr) in enumerate((("Against the 0.8 s rule", "--ptr"), ("Against no control", "--flt"))):
        gx = lw + g * 2 * cw
        b += rect(gx + 2, 2, 2 * cw - 4, 22, fill="--panel", stroke=colr, rx=5, sw=1.5) + text(gx + cw, 17, gt, a="middle", size=12, w=700)
    for j, (t, t2, *_r) in enumerate(cols):
        b += text(lw + j * cw + cw / 2, 42, t, a="middle", size=11, w=600)
    b += text(lw + 2 * cw, top - 6, "Blue: the policies are better.   Orange: the policies are worse.", a="middle", size=9.5, fill="--dim")
    for i, (c, q, Tb, tag) in enumerate(CELLS):
        y = top + i * ch
        b += text(lw - 8, y + ch / 2 + 4, lab(c, q, tag), a="end", size=11.5, w=600 if tag else 400)
        for j, (t, t2, ref, key, good, bad) in enumerate(cols):
            e = pe(Tb, c, q, ref, key)
            m = float(np.median([x[0] for x in e]))
            win, lose = sum(x[1] > 0 for x in e), sum(x[2] < 0 for x in e)
            col, op = colour(m)
            sub = f"{win} of 5 clearly {good}" if win else f"{lose} of 5 clearly {bad}" if lose else "none clear"
            tip = f"{lab(c, q, tag)}, {t} {t2}, by policy: " + "; ".join(f"{p} {say(x[0], good, bad, 1)} (interval {say(x[1], good, bad, 1)} to {say(x[2], good, bad, 1)})" for p, x in zip(POL, e))
            b += rect(lw + j * cw + 2, y + 2, cw - 4, ch - 4, fill=col, stroke=None, op=0.10 + 0.6 * op, rx=4, tip=tip)
            b += text(lw + j * cw + cw / 2, y + ch / 2 + 1, say(m, good, bad), a="middle", size=12, w=600)
            b += text(lw + j * cw + cw / 2, y + ch / 2 + 14, sub, a="middle", size=9, fill="--dim")
    return svg(lw + len(cols) * cw + 10, top + len(CELLS) * ch + 8, b, "Operating map: policies against the 0.8 s rule and no control in every cell", fit=True)


def scatter_cell(Tb, c, q, title, rules):
    names = [n for n in ["nc", "p333", O["single_rule"], "copy"] + list(O["ctrl"]) if A(Tb, c, q, n)]
    names = list(dict.fromkeys(names))
    pts = [(n, med(A(Tb, c, q, n), "all_delay") / 1000.0, med(A(Tb, c, q, n), "ttc_net")) for n in names + POL]
    W, H, ml, mb, mt = 540, 350, 54, 40, 44
    xs, ys = [p[1] for p in pts], [p[2] for p in pts]
    x0, x1, y0, y1 = min(xs) * 0.97, max(xs) * 1.02, 0, max(ys) * 1.08
    pr = 80
    X = lambda v: ml + (v - x0) / (x1 - x0) * (W - ml - pr)
    Y = lambda v: mt + (y1 - v) / (y1 - y0) * (H - mt - mb)
    b = text(0, 14, title, w=600, size=12)
    for t in nice(y0, y1, 5):
        if t <= y1:
            b += line(ml, Y(t), W - 12, Y(t), "--line") + text(ml - 5, Y(t) + 3.5, f"{t:,.0f}", a="end", size=10, fill="--dim")
    for t in nice(x0, x1, 5):
        if x0 <= t <= x1:
            b += text(X(t), H - mb + 14, f"{t:,.0f}", a="middle", size=10, fill="--dim")
    b += text(ml + (W - ml) / 2, H - 6, "All-vehicle delay, thousand vehicle-seconds (left is better)", a="middle", size=10, fill="--dim")
    b += text(4, mt - 12, "Close-following (TTC), vehicle-seconds (lower is better)", size=10, fill="--dim")
    for n, x, y in pts:
        pol, ref = n in POL, n in rules
        colr = "--accent" if pol else "--sem1" if n == "nc" else "--ink" if ref else "--c8"
        r = 6 if pol or ref or n == "nc" else 4
        b += circle(X(x), Y(y), r, fill=colr, stroke="--bg", sw=1.5, tip=f"{n}: delay {x:,.0f}k veh-s, TTC {y:,.0f}" + (" (counting rule)" if ref else ""))
        if pol or ref or n == "nc":
            b += text(X(x) + 8, Y(y) + 4, "no control" if n == "nc" else n, size=10, fill="--ink" if not pol else "--accent", w=600 if pol else 400)
    return svg(W, H, b, title)


def forest(Tb, c, q, rules, title):
    rows = []
    for r in rules:
        for p in POL:
            rows.append((f"{p} vs {r}", raw(A(Tb, c, q, p), A(Tb, c, q, r), "ttc_net"), raw(A(Tb, c, q, p), A(Tb, c, q, r), "all_delay")))
    lw, cw, gap, lh, top = 150, 290, 60, 17, 58
    W = lw + 2 * cw + gap + 40
    b = text(0, 14, title, w=600, size=12)
    panels = [("Close-following (TTC)", "pass: at least 10 % fewer, and surely fewer", 1, (-40, 60), 10.0, "fewer", "more"),
              ("Delay", "pass: at most 2 % more", 2, (-20, 20), -2.0, "less", "more")]
    for k, (t, t2, idx, (lo, hi), th, good, bad) in enumerate(panels):
        x0 = lw + k * (cw + gap)
        X = lambda v, x0=x0, lo=lo, hi=hi: x0 + (max(lo, min(hi, v)) - lo) / (hi - lo) * cw
        b += text(x0 + cw / 2, 30, t, a="middle", size=11, w=600) + text(x0 + cw / 2, 43, t2, a="middle", size=9.5, fill="--dim")
        b += line(X(0), top - 4, X(0), top + len(rows) * lh, "--dim")
        b += line(X(th), top - 4, X(th), top + len(rows) * lh, "--ask", 1.2, dash="4 3")
        for tv in range(lo, hi + 1, 20):
            b += text(X(tv), top + len(rows) * lh + 12, "0" if tv == 0 else f"{abs(tv)} {good if tv > 0 else bad}", a="middle", size=9, fill="--dim")
        b += text(x0, top + len(rows) * lh + 26, "← policy worse", size=9.5, fill="--sem1") + text(x0 + cw, top + len(rows) * lh + 26, "policy better →", a="end", size=9.5, fill="--accent")
        for i, row in enumerate(rows):
            m, l, h = row[idx]
            y = top + i * lh + lh / 2
            ok = (m >= th and l > 0) if idx == 1 else m >= th
            colr = "--accent" if ok else "--sem1"
            b += line(X(l), y, X(h), y, colr, 1.6)
            b += circle(X(m), y, 3.6, fill=colr, tip=f"{row[0]}: {say(m, good, bad, 1)}, interval {say(l, good, bad, 1)} to {say(h, good, bad, 1)}")
    for i, row in enumerate(rows):
        b += text(lw - 8, top + i * lh + lh / 2 + 3.5, row[0], a="end", size=10)
    return svg(W, top + len(rows) * lh + 34, b, title, fit=True)


def controllers():
    rows = [("No control", "Every automated car keeps a 1.6 s gap to the car ahead, always."),
            ("0.8 s rule (p333)", "An automated car following another automated car within 150 m closes to 0.8 s; the same everywhere and always. Behind a human-driven car it stays at 1.6 s."),
            ("Tuned rules (70)", "Variants of the 0.8 s rule that switch to 1.2 or 1.0 s in certain places or conditions, tuned on separate seeds. Strongest in X2: os1_15_10, which uses 0.8 s, but 1.2 s when past the first merge, slower than 15 m/s, with at least 10 cars waiting to merge."),
            ("DRL policies (d0-d4)", "A learned network picks 1.6, 1.2, 1.0 or 0.8 s for each automated car every 10 s, from what that car sees.")]
    return table(["Controller", "What it does (automated cars only; human drivers are never controlled)"], [(f"<b>{e(a)}</b>", e(b)) for a, b in rows])


def scoreboard():
    lines_ = [("No control", T, "nc"), ("0.8 s rule", T, "p333"), ("Best tuned rule (os1_15_10), original seeds", T, "os1_15_10"), ("Best tuned rule (os1_15_10), fresh seeds", F, "os1_15_10")]
    verdict = ["Trade-off: much faster, not safer (in X1 less safe)", "Safer at about the same delay; pre-registered check passed 5 of 5 (original), 3 of 5 (fresh)", "Won: 4 of 5 policies within every limit", "Not confirmed: 1 of 5; delay over the 2 % limit"]
    out = []
    for (name, Tb, ref), v in zip(lines_, verdict):
        cells = []
        for key, good, bad in (("ttc_net", "fewer", "more"), ("all_delay", "less", "more")):
            ee = pe(Tb, "X2", 5300.0, ref, key)
            vals = sorted(x[0] for x in ee)
            m = float(np.median(vals))
            ok = m >= 0.5
            same = abs(m) < 5 and not any(x[1] > 0 or x[2] < 0 for x in ee)
            mark = "about the same" if same else ("✔ " if ok else "✘ ") + f"{abs(vals[0]) if ok else abs(vals[-1]):.0f}-{abs(vals[-1]) if ok else abs(vals[0]):.0f} % {good if ok else bad}" if (vals[0] > 0) == (vals[-1] > 0) else say(m, good, bad) + " (median)"
            cells.append(mark)
        out.append((f"<b>{e(name)}</b>", e(cells[0]), e(cells[1]), f"<b>{e(v)}</b>"))
    return table(["X2 at 5,300: the policies against", "Close-following (TTC)", "Delay", "Verdict"], out)


def verdict_cards():
    rows = [
        ("X1, slowdown downstream of merge 2", "Not won (V395)", "3 of 5 policies clear. Only the 0.8 s rule counted. 33-46 % fewer TTC seconds than it, but 2 policies had 2.5-3.1 % more delay than allowed.", "--sem1"),
        ("X2, slowdown between the merges", "Won at the minimum (V395)", "4 of 5 clear against 4 rules: 24-30 % fewer TTC seconds than the strongest rule, delay within 2 %. Fragile: about 30 % on resampled seeds.", "--entry"),
        ("X2, 20 fresh seeds", "Not confirmed (V401)", "1 of 5 clear. All 5 still had 14-26 % fewer TTC seconds than the strongest rule, but 4 of 5 had 1.6-10 % more delay.", "--sem1"),
        ("Against no control", "Mixed on TTC, always faster", "In the deciding X1 and X2 cells no TTC gain (X1: 31 % more TTC seconds). In S, H1 and H2 at 5,300: 47-56 % fewer. Delay always 18-37 % lower.", "--flt"),
    ]
    return '<div class="cards">' + "".join(f'<div class="card" style="border-left-color:var({c})"><h4>{e(t)}</h4><p><b>{e(v)}</b></p><p>{e(x)}</p></div>' for t, v, x, c in rows) + "</div>"


body = "<h1>DRL against rules: where, who wins, by how much</h1>"
body += '<p class="path">Confirmatory 3, revision 4 (V395-V398), and its fresh-seed replication, confirmatory 3b (V401). r2m3, plant_c3, 50 % ALKS. 5 per-CAV PPO policies (d0-d4) against no control, the fixed 0.8 s rule (p333) and tuned rules. 20 paired seeds per cell. Companion pages: <a href="../../extracts/2026-11-05_09-18/2026-11-05_09-18_extract.html">handoff</a>, <a href="../../extracts/2026-11-05_09-18/2026-11-05_09-18_drl_extract.html">DRL course</a>.</p>'
body += "<h2 id='s0'>0. In one picture</h2>" + P("**The four controllers.** All of them act only on the automated cars (half of the traffic); human drivers drive on their own.") + controllers()
body += P("**The scoreboard in X2**, the deciding scenario. Against each simple baseline the policies win on one measure only: against no control on delay, against the 0.8 s rule on close-following. Neither is a win on both. The real test was the best tuned rule: always safer, but on fresh seeds a few per cent slower than the 2 % the protocol allowed.") + scoreboard()
body += "<h2 id='s1'>1. The verdicts</h2>" + verdict_cards()
body += P("**How to read every number here.** For both measures, less is better. **'fewer'** close-following seconds and **'less'** delay mean the policy is better; **'more'** means it is worse. Blue marks the policy better, orange marks it worse. **Close-following (TTC)** counts vehicle-seconds where a vehicle would hit the one ahead within 3 s at current speeds. It is a safety surrogate and is also in the policies' reward. **Delay** counts all vehicles' lost time. Percentages are the protocol's statistic: the median over the 20 seeds of the paired difference, relative to the other controller. 'Clearly' means the 97.5 % interval lies entirely on that side.")
body += "<h2 id='s2'>2. Where: every scenario</h2>" + grid()
body += H("Each box is the median over the 5 policies; hover for each policy with its interval. 'Better' or 'worse' means the interval excludes 0 that way. The map rows (not primary) compare with the 0.8 s rule and no control only; the tuned rules ran only in the primary rows at 5,300. Blue: policies better. Orange: policies worse.")
body += PM("**Pattern.** Against the fixed 0.8 s rule, the policies clearly cut TTC seconds only in the slowdown cells at 5,300: 38-42 %, all 5 policies, at about equal delay. Elsewhere the medians favour them (14-39 % fewer) but at most 3 of 5 are clearly fewer, and in steady traffic at 4,600 there is no difference. Against no control the picture splits. At 5,300 in steady traffic, H1 and H2, and in X1 at 4,600, the policies have 47-56 % fewer TTC seconds, because no control queues. In X1 at 5,300 they have 31 % more, and in S at 4,600 about twice as many, on tiny counts. In X2 they are about equal. They always have 18-37 % less delay than no control.")
body += "<h2 id='s3'>3. Who wins in the deciding cells: delay against TTC</h2>"
sc = [scatter_cell(T, "X1", 5300.0, "X1 at 5,300, original seeds", RULES["X1"]), scatter_cell(T, "X2", 5300.0, "X2 at 5,300, original seeds", RULES["X2"]), scatter_cell(F, "X2", 5300.0, "X2 at 5,300, fresh seeds", FRESH_RULES)]
body += '<div class="charts">' + "".join(f"<div>{x}</div>" for x in sc) + "</div>"
body += H("Each dot is one controller's median over the 20 seeds. Blue: the 5 policies. Black: rules that counted in that cell. Grey: other rules. Orange: no control. Best is bottom left. Medians only; the verdict uses paired differences.")
body += PM("**Reading.** The policies sit lowest on TTC among everything except no control, in all three panels. On delay they sit among the rules. In X2 on the original seeds they are as fast as the rules that counted. On the fresh seeds, os1_15_10 is faster than most policies, and that is the delay limit the replication failed.")
body += "<h2 id='s4'>4. By how much: each policy against each counting rule</h2>"
body += forest(T, "X2", 5300.0, RULES["X2"], "X2, original seeds: WON, 4 of 5 (d2 fails)")
body += forest(F, "X2", 5300.0, FRESH_RULES, "X2, fresh seeds: NOT CONFIRMED, 1 of 5 (delay)")
body += forest(T, "X1", 5300.0, RULES["X1"], "X1, original seeds: NOT WON, 3 of 5 (delay)")
body += H("Dot: median; line: 97.5 % interval. Blue: the policy passes that condition; orange: it fails. Dashed red: the pass line; right of it passes. A cell is won when at least 4 of 5 policies meet every condition against every counting rule, plus flow, braking and collision limits not drawn here.")
body += "<h2 id='s5'>5. What it adds up to</h2>"
body += cards([
    ("Holds in every test", "Fewer seconds at TTC below 3 s than every tuned headway rule in X2, on both seed blocks: 8.5-30 % (original), 14-26 % (fresh), and 29-45 % fewer than the 0.8 s rule. Human drivers benefit too (V398).", "--entry"),
    ("Does not hold", "A clean win: on fresh seeds the policies needed 1.6-10 % more delay than the best delay-efficient rule. X1 failed on delay too. In the deciding cells they do not beat no control on TTC.", "--ask"),
    ("Where it comes from", "The queue left after a slowdown at the near-saturated second merge. Not during the slowdown itself, and not clearly in steady traffic (V396).", "--ptr"),
    ("Honest one-line summary", "Per-CAV PPO headway control traded a little delay for fewer close-following seconds than tuned rules after a slowdown on this uncalibrated two-merge model; the pre-registered win did not replicate.", "--accent"),
])
toc = "".join(f'<a href="#s{i}"><small>{i}</small>{t}</a>' for i, t in enumerate(("In one picture", "Verdicts", "Every scenario", "Delay against TTC", "Each policy, each rule", "What it adds up to")))
html_ = page.shell("DRL Results Map", toc, body, "Self-contained. Computed from conf3 and conf3b evaluation rows with the protocol's statistic.")
open(OUT, "w").write(html_)
print(len(html_) / 1e6, "MB")
