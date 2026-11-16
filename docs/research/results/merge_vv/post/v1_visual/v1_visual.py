"""V1 visual check (merge_vv.md v1.1 §2 V1): rebuild each of v1.json's 40 sampled samples over +-10 s and plot it.

Read only. Sources per run: the counted-sample trace (vv_trace), the 1-Hz acceleration-lane trace (end_trace: every vehicle on
3a_0 and 4a_0), the merge log (vv/*.json.gz). The trace holds only counted samples, so a vehicle off the acceleration lanes is
seen only in seconds where it, or a vehicle it leads, is below 3 s TTC.
"""
import gzip
import json
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

R = Path("/home/catalin/work/phd/v5b1_runs/vv_remote")
OUT = Path("/home/catalin/work/phd/v5b1_runs/vv_post/v1_visual")
W = 10.0
F_COL, L_COL = "#2a78d6", "#eb6834"
FIELDS = ("t", "v", "w", "fk", "wk", "froad", "flane", "fpos", "flen", "wroad", "wlane", "wpos", "wlen", "gap", "mingap", "s", "sl")

# lane successors of r2m3 (corridor.py connections, 3 main lanes, 4a has 4)
SUCC = {"r_0": ["rj_0"], "rj_0": ["3a_0"], "r2_0": ["rj2_0"], "rj2_0": ["4a_0"]}
for i in range(3):
    SUCC[f"1_{i}"] = [f"2_{i}"]
    SUCC[f"2_{i}"] = [f"3a_{i + 1}"]
    SUCC[f"3a_{i + 1}"] = [f"3_{i}"]
    SUCC[f"3_{i}"] = [f"4a_{i + 1}"]
    SUCC[f"4a_{i + 1}"] = [f"4_{i}"]
    SUCC[f"4_{i}"] = [f"5_{i}"]
NODE_DOWN = {"m": "3a", "ae": "3", "d": "4a", "e2": "4", "b": "5", "n2": "2", "rm": "rj", "rm2": "rj2"}


def road_of(lane):
    return lane.rsplit("_", 1)[0]


def next_lane(fl, wl):
    """wl is reachable from fl within two normal-lane hops (internal lanes accepted at the follower's next node)."""
    if wl.startswith(":"):
        return not fl.startswith(":")
    if fl.startswith(":"):
        return road_of(wl) == NODE_DOWN.get(fl[1:].split("_")[0])
    a = SUCC.get(fl, [])
    return wl in a or any(wl in SUCC.get(x, []) for x in a)


def period(t, onset, dur, taper=20.0):
    if t < onset:
        return "before"
    if t < onset + taper:
        return "taper"
    if t < onset + dur:
        return "hold"
    return "after" if t < onset + dur + 120.0 else "rest"


def load():
    rows = {}
    for d in ("vv_trace", "vv_replay"):
        for line in open(R / d / "s6_rows.jsonl"):
            r = json.loads(line)
            if r["name"].endswith("~trace"):
                r["_dir"] = d
                rows[f"{r['name']} {r['seed']}"] = r
    return rows


class Run:
    def __init__(self, r):
        self.r = r
        self.lanes = r["vv_lanes"]
        self.off = r["m_offsets"]
        self.tr = [dict(zip(FIELDS, s)) for s in r["vv_trace"]]
        self.st = defaultdict(list)     # vehicle -> (t, lane, pos, speed, source)
        self.pair = defaultdict(dict)   # (v, w) -> t -> record
        for s in self.tr:
            self.st[s["v"]].append((s["t"], s["flane"], s["fpos"], s["s"], "trace-F"))
            self.st[s["w"]].append((s["t"], s["wlane"], s["wpos"], s["sl"], "trace-L"))
            self.pair[(s["v"], s["w"])][s["t"]] = s
        self.end = defaultdict(dict)    # t -> lane -> {v: (pos, speed)}
        for t, ln, L, vs in r["end_trace"]:
            self.end[t][ln] = {v: (p, sp) for v, p, sp in vs}
            for v, p, sp in vs:
                self.st[v].append((t, ln, p, sp, "end"))
        f = R / r["_dir"] / "vv" / r["vv_log_file"]
        self.merges = defaultdict(list)
        for m in json.load(gzip.open(f, "rt"))["merges"]:
            self.merges[m["v"]].append(m)
        self.J = self._junctions()

    def _junctions(self):
        """Internal-lane length per (from road, to road), rebuilt from cross-road samples: SUMO gap + minGap minus the two part gaps."""
        js = defaultdict(list)
        for s in self.tr:
            fl, wl = s["flane"], s["wlane"]
            if fl.startswith(":") or wl.startswith(":") or road_of(fl) == road_of(wl):
                continue
            if wl in SUCC.get(fl, []):
                js[(road_of(fl), road_of(wl))].append(s["gap"] + s["mingap"] - (self.lanes[fl] - s["fpos"]) - (s["wpos"] - s["wlen"]))
        return {k: (min(v), max(v), len(v)) for k, v in js.items()}

    def x(self, lane, pos):
        """Mainline coordinate (m_offsets; junction lengths not included); ramps placed upstream of their acceleration lane."""
        road = road_of(lane)
        if road in self.off:
            return self.off[road] + pos
        if road in ("r", "rj", "r2", "rj2"):
            acc = "3a" if road in ("r", "rj") else "4a"
            rj = "rj" if acc == "3a" else "rj2"
            return self.off[acc] - self.lanes[rj + "_0"] + pos - (self.lanes[road + "_0"] if road in ("r", "r2") else 0.0)
        if road.startswith(":"):
            down = NODE_DOWN.get(road[1:].split("_")[0])
            return self.off.get(down, 0.0) - 3.0 + pos
        return float("nan")

    def states(self, v, t0, t1):
        out = {}
        for t, ln, p, sp, src in self.st[v]:
            if t0 - 1e-6 <= t <= t1 + 1e-6:
                out.setdefault(t, (ln, p, sp, set()))[3].add(src)
        return dict(sorted(out.items()))


def evidence(run, smp):
    s = dict(zip(FIELDS, smp[1:]))
    t, v, w = s["t"], s["v"], s["w"]
    r = run.r
    onset, dur = r["pert_log"][0][1], r["pert_log"][0][2]
    e = {"run": smp[0], "t": t, "period": period(t, onset, dur), "v": v, "w": w, "fk": s["fk"], "wk": s["wk"],
         "flane": s["flane"], "fpos": round(s["fpos"], 2), "wlane": s["wlane"], "wpos": round(s["wpos"], 2),
         "s": round(s["s"], 2), "sl": round(s["sl"], 2), "gapmg": round(s["gap"] + s["mingap"], 2),
         "ttc": round((s["gap"] + s["mingap"]) / (s["s"] - s["sl"]), 2), "lane_len": run.lanes.get(s["flane"])}
    if s["flane"] == s["wlane"]:
        e["rel"] = "same lane"
        e["pos_gap_err"] = round(s["wpos"] - s["wlen"] - s["fpos"] - (s["gap"] + s["mingap"]), 4)
    elif next_lane(s["flane"], s["wlane"]):
        e["rel"] = "next lane"
        k = (road_of(s["flane"]), road_of(s["wlane"]))
        e["junction_len_range"] = run.J.get(k)
        if s["wlane"] in SUCC.get(s["flane"], []) and k in run.J:
            jx = s["gap"] + s["mingap"] - (run.lanes[s["flane"]] - s["fpos"]) - (s["wpos"] - s["wlen"])
            e["junction_len_this"] = round(jx, 3)
    else:
        e["rel"] = "OTHER"
    # nearest vehicle ahead on an acceleration lane, from the independent 1-Hz lane trace
    if s["flane"] in ("3a_0", "4a_0"):
        on = run.end.get(t, {}).get(s["flane"], {})
        ahead = sorted((p, u) for u, (p, sp) in on.items() if p > s["fpos"] + 1e-9)
        e["acc_nearest_ahead"] = ahead[0][1] if ahead else None
        e["acc_trace_match"] = (v in on and abs(on[v][0] - s["fpos"]) < 1e-6 and abs(on[v][1] - s["s"]) < 1e-6
                                and (s["wlane"] != s["flane"] or (w in on and abs(on[w][0] - s["wpos"]) < 1e-6 and abs(on[w][1] - s["sl"]) < 1e-6)))
        e["acc_n_on_lane"] = len(on)
    pr = run.pair[(v, w)]
    ts = sorted(pr)
    run_t = [t]
    while run_t[0] - 1.0 in pr:
        run_t.insert(0, run_t[0] - 1.0)
    while run_t[-1] + 1.0 in pr:
        run_t.append(run_t[-1] + 1.0)
    e["encounter"] = [run_t[0], run_t[-1], len(run_t)]
    e["pair_counted_in_window"] = [x for x in ts if abs(x - t) <= W]
    sv, sw = run.states(v, t - W, t + W), run.states(w, t - W, t + W)
    gaps = {}
    for x in sorted(set(sv) & set(sw)):
        lv, pv, spv, _ = sv[x]
        lw, pw, spw, _ = sw[x]
        if lv == lw:
            gaps[x] = (round(pw - s["wlen"] - pv, 3), round(spv - spw, 3), lv)
        else:
            gaps[x] = (None, round(spv - spw, 2), f"{lv}/{lw}")
    e["pair_gaps"] = gaps
    e["f_lanes"] = sorted({(x, st[0]) for x, st in sv.items()})
    e["w_lanes"] = sorted({(x, st[0]) for x, st in sw.items()})
    e["f_lane_changes"] = [(a, la, b, lb) for (a, (la, *_)), (b, (lb, *_)) in zip(sv.items(), list(sv.items())[1:])
                           if la != lb and lb not in SUCC.get(la, []) and not la.startswith(":") and not lb.startswith(":")]
    e["w_lane_changes"] = [(a, la, b, lb) for (a, (la, *_)), (b, (lb, *_)) in zip(sw.items(), list(sw.items())[1:])
                           if la != lb and lb not in SUCC.get(la, []) and not la.startswith(":") and not lb.startswith(":")]
    jumps = []
    for u, su in ((v, sv), (w, sw)):
        it = list(su.items())
        for (a, (la, pa, va, _)), (b, (lb, pb, vb, _)) in zip(it, it[1:]):
            if la == lb and b - a <= 1.0 + 1e-6:
                dx = pb - pa
                if dx < -0.01 or dx > max(va, vb) * (b - a) + 3.0:
                    jumps.append((u, a, b, round(dx, 2)))
    e["jumps"] = jumps
    e["merges"] = [(u, m["t"], m["lane0"], round(m["pos0"], 1), round(m["speed"], 2), m.get("lead", {}).get("v"), m.get("lag", {}).get("v"))
                   for u in (v, w) for m in run.merges.get(u, []) if t - W <= m["t"] <= t + W]
    e["teleports_run"], e["collisions_run"] = r.get("teleports"), r.get("collisions")
    return e, sv, sw


def plot(i, run, smp, e, sv, sw):
    s = dict(zip(FIELDS, smp[1:]))
    t = s["t"]
    fig, ax = plt.subplots(3, 1, figsize=(7.2, 7.6), sharex=True, gridspec_kw={"height_ratios": [3, 2, 1.6]})
    for u, su, col, ls, mk, lab, L in ((s["v"], sv, F_COL, "-", "o", "follower", 0.0), (s["w"], sw, L_COL, "--", "s", "leader", s["wlen"])):
        tt = list(su)
        xs = [run.x(su[x][0], su[x][1]) for x in tt]
        sp = [su[x][2] for x in tt]
        acc = [su[x][0] in ("3a_0", "4a_0") or road_of(su[x][0]) in ("r", "rj", "r2", "rj2") for x in tt]
        ax[0].plot(tt, xs, ls, color=col, lw=2, label=f"{lab} {u} ({s['fk'] if lab == 'follower' else s['wk']}) front")
        if L:
            ax[0].plot(tt, [a - L for a in xs], ":", color=col, lw=1.5, marker="_", ms=10, label="leader rear")
        ax[0].scatter([a for a, q in zip(tt, acc) if q], [b for b, q in zip(xs, acc) if q], marker=mk, s=40, facecolors="white", edgecolors=col, zorder=3)
        ax[0].scatter([a for a, q in zip(tt, acc) if not q], [b for b, q in zip(xs, acc) if not q], marker=mk, s=40, color=col, zorder=3)
        prev = None
        for a, b in zip(tt, xs):
            if su[a][0] != prev:
                ax[0].annotate(su[a][0], (a, b), textcoords="offset points", xytext=(4, 6 if lab == "follower" else -12), fontsize=7, color="#52514e")
                prev = su[a][0]
        ax[1].plot(tt, sp, ls, color=col, lw=2, marker=mk, ms=5, label=lab)
    for m in e["merges"]:
        for a in ax:
            a.axvline(m[1], color="#6250d6", lw=1, ls="-.")
        ax[1].annotate(f"merge {m[0].split('.')[-1]}", (m[1], 0), textcoords="offset points", xytext=(2, 2), fontsize=7, color="#6250d6")
    for lane in ("3a_0", "4a_0"):
        if lane in (s["flane"], s["wlane"]):
            xe = run.x(lane, run.lanes[lane])
            lo, hi = ax[0].get_ylim()
            if xe > hi + 40.0:     # far above the pair: drawing it would squash the plot
                continue
            ax[0].axhline(xe, color="#52514e", lw=0.8)
            ax[0].annotate(f"{lane} end", (t - W, xe), textcoords="offset points", xytext=(2, 2), fontsize=7, color="#52514e")
    pg = [(x, g[0]) for x, g in e["pair_gaps"].items() if g[0] is not None]
    pr = run.pair[(s["v"], s["w"])]
    ax[2].plot([x for x, _ in pg], [g for _, g in pg], "-", color="#52514e", lw=1.5, marker="o", ms=3, label="net gap from positions (m)")
    ax[2].scatter([x for x in pr if abs(x - t) <= W], [pr[x]["gap"] + pr[x]["mingap"] for x in pr if abs(x - t) <= W], marker="x", s=40,
                  color="#0b0b0b", zorder=3, label="counted: SUMO gap + minGap")
    ax[2].axhline(s["mingap"], color="#52514e", lw=0.8, ls="--", label="follower minGap (SUMO gap 0)")
    ax[2].set_ylim(bottom=0)
    ax[2].ticklabel_format(useOffset=False)
    for a in ax:
        a.axvline(t, color="#d03b3b", lw=1)
        a.grid(color="#e6e6e3", lw=0.6)
        a.spines[["top", "right"]].set_visible(False)
    ax[0].set_ylabel("position (m, mainline)")
    ax[1].set_ylabel("speed (m/s)")
    ax[2].set_ylabel("gap (m)")
    ax[2].set_xlabel("simulation time (s)")
    ax[0].legend(fontsize=7, loc="upper left", frameon=False)
    ax[1].legend(fontsize=7, loc="upper left", frameon=False)
    ax[2].legend(fontsize=7, loc="upper left", frameon=False)
    ax[2].set_xlim(t - W - 0.5, t + W + 0.5)
    ax[0].set_title(f"S{i:02d} {smp[0]}  t={t:.0f} ({e['period']})  {e['rel']}  TTC {e['ttc']:.2f} s\n"
                    f"open marker = acceleration lane or ramp; red line = counted second; violet = merge", fontsize=8.5)
    fig.tight_layout()
    f = OUT / f"s{i:02d}.png"
    fig.savefig(f, dpi=80)
    plt.close(fig)
    return f.name


def main():
    rows = load()
    sample = json.load(open(R / "vv_trace" / "v1.json"))["sample"]
    runs = {}
    out = []
    for i, smp in enumerate(sample):
        run = runs.get(smp[0]) or runs.setdefault(smp[0], Run(rows[smp[0]]))
        e, sv, sw = evidence(run, smp)
        e["i"], e["png"] = i, plot(i, run, smp, e, sv, sw)
        out.append(e)
    jl = {k: run.J for k, run in runs.items()}
    (OUT / "evidence.json").write_text(json.dumps({"samples": out, "junction_len": {k: {f"{a}->{b}": v for (a, b), v in j.items()} for k, j in jl.items()}},
                                                  indent=1, default=str))
    print("wrote", len(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
