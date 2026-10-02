"""Pilot / training-run report against the pre-registered screening criteria (docs/lab/r3_pilots_protocol.md).

python -m vsl_lab.eval.pilot_report --tag p1_bn4 --track t1 --run-dirs DIR [DIR ...] --refs docs/lab/t1_val_refs.json \
       --nc-key nc --const-key cap:3 --classical-key meter:10:6
Writes docs/lab/figs/<tag>.png (validation metric vs PPO update, one line per learner seed, reference
controllers as labelled dashed lines) and appends a section to docs/lab/r3_pilots.md; one ledger row.
"""
from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path

import numpy as np

from vsl_lab.config import REPO_ROOT
from vsl_lab.ops import ledger

# Reference palette (dataviz skill, light mode): fixed categorical order, never cycled.
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e7e6e2"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]   # first three slots validate all-pairs in both modes


def read_val(run_dir: Path) -> list:
    rows = []
    with open(run_dir / "val.csv") as f:
        for r in csv.DictReader(f):
            v = r.get("val_metric_value")
            if v in (None, "", "None"):
                continue
            rows.append((r["update"], float(v)))
    return rows


def read_progress(run_dir: Path) -> list:
    with open(run_dir / "progress.csv") as f:
        return [r for r in csv.DictReader(f)]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--track", required=True)
    ap.add_argument("--run-dirs", nargs="+", required=True)
    ap.add_argument("--refs", required=True)
    ap.add_argument("--nc-key", required=True)
    ap.add_argument("--const-key", default=None)
    ap.add_argument("--classical-key", default=None)
    ap.add_argument("--higher-better", action="store_true")
    ap.add_argument("--metric-label", default="validation metric")
    ap.add_argument("--min-gain", type=float, default=0.05)
    a = ap.parse_args(argv)
    refs = json.loads(Path(a.refs).read_text())["refs"]
    rk = next(iter(refs[a.nc_key]))            # 'mean_val_outflow' or 'mean_val_speed' or similar
    ref = lambda k: refs[k][rk] if k and k in refs else None
    nc, const, cls = ref(a.nc_key), ref(a.const_key), ref(a.classical_key)
    sign = 1.0 if a.higher_better else -1.0
    better = lambda x, y: sign * (x - y)
    results = []
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7.2, 4.0), dpi=150)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    for i, d in enumerate(a.run_dirs):
        d = Path(d)
        val = read_val(d)
        prog = read_progress(d)
        summ = json.loads((d / "summary.json").read_text()) if (d / "summary.json").exists() else {}
        cfg = json.loads((d / "config.json").read_text())
        pts = [(int(u), v) for u, v in val if u not in ("final",)]
        final = [v for u, v in val if u == "final"]
        init = [v for u, v in pts if u == 0]
        mids = [(u, v) for u, v in pts if u != 0]
        best = max(mids, key=lambda x: sign * x[1]) if mids else (None, None)
        rew = [float(r["ep_rew_mean"]) for r in prog if r.get("ep_rew_mean") not in ("", None)]
        c1_val = bool(final and init and better(final[0], init[0]) > 0)
        c1_rew = bool(len(rew) >= 50 and np.mean(rew[-25:]) > np.mean(rew[:25]))
        cand = [x for x in (final[0] if final else None, best[1]) if x is not None]
        top = max(cand, key=lambda x: sign * x) if cand else None
        c3 = bool(top is not None and nc and better(top, nc) >= a.min_gain * abs(nc))
        c2 = bool(top is not None and const is not None and better(top, const) > 0)
        fails = int((summ.get("health_train") or {}).get("FAIL", 0))
        res = {"run_dir": str(d), "seed": cfg.get("seed"), "updates": summ.get("updates_done"),
               "initial": init[0] if init else None, "final": final[0] if final else None, "best_val": best,
               "C1_val": c1_val, "C1_reward": c1_rew, "C3_vs_nc": c3, "C2_vs_const": c2, "health_fail": fails,
               "beats_classical": bool(top is not None and cls is not None and better(top, cls) > 0),
               "pass": c1_val and c1_rew and c3 and c2 and fails == 0, "wall_s": summ.get("wall_s"),
               "watchdog_max_c": summ.get("watchdog_max_c")}
        results.append(res)
        xs = [u for u, _ in pts] + ([summ.get("updates_done")] if final and summ.get("updates_done") else [])
        ys = [v for _, v in pts] + ([final[0]] if final and summ.get("updates_done") else [])
        ax.plot(xs, ys, color=SERIES[i % 3], lw=2, marker="o", ms=4, label=f"learner seed {cfg.get('seed')}")
    xmax = ax.get_xlim()[1]
    for name, v in (("no control", nc), ("best constant", const), ("tuned classical", cls)):
        if v is not None:
            ax.axhline(v, color=INK2, lw=1, ls="--", zorder=0)
            ax.text(xmax, v, f" {name} {v:.3g}", color=INK2, fontsize=8, va="center", ha="left", clip_on=False)
    ax.set_xlabel("PPO update", color=INK2, fontsize=9)
    ax.set_ylabel(a.metric_label, color=INK2, fontsize=9)
    ax.set_title(f"{a.tag}: validation {a.metric_label}", color=INK, fontsize=10, loc="left")
    ax.grid(True, color=GRID, lw=0.6)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.tick_params(colors=INK2, labelsize=8)
    if len(a.run_dirs) >= 2:
        ax.legend(frameon=False, fontsize=8, labelcolor=INK2)
    figdir = REPO_ROOT / "docs" / "lab" / "figs"
    figdir.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(figdir / f"{a.tag}.png", facecolor=SURFACE)
    L = ["", f"## {a.tag} ({a.track}) · {time.strftime('%Y-%m-%d %H:%M')}", "",
         f"References on the same validation seeds ({rk}): no control {nc}, best constant {const}, tuned classical {cls}.",
         "", f"![{a.tag}](figs/{a.tag}.png)", "",
         "| seed | updates | initial | final | best val (update) | C1 val | C1 reward | C3 ≥ NC+{:.0%} | C2 > const | beats tuned classical | health FAIL | screening |".format(a.min_gain),
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in results:
        b = r["best_val"]
        L.append(f"| {r['seed']} | {r['updates']} | {r['initial']} | {r['final']} | {b[1]} ({b[0]}) | {r['C1_val']} | "
                 f"{r['C1_reward']} | {r['C3_vs_nc']} | {r['C2_vs_const']} | {r['beats_classical']} | {r['health_fail']} | "
                 f"**{'PASS' if r['pass'] else 'FAIL'}** |")
    rp = REPO_ROOT / "docs" / "lab" / "r3_pilots.md"
    if not rp.exists():
        rp.write_text("# R3 pilots: results\n\nProtocol: `docs/lab/r3_pilots_protocol.md`. Exploratory; nothing here is a claim.\n")
    rp.write_text(rp.read_text() + "\n".join(L) + "\n")
    ledger.append(a.track.upper(), "R3", "P", a.tag, {"run_dirs": a.run_dirs}, "see run configs", len(results),
                  {"FAIL": sum(r["health_fail"] for r in results)},
                  {"refs": {"nc": nc, "const": const, "classical": cls},
                   "runs": [{k: r[k] for k in ("seed", "final", "best_val", "pass", "beats_classical")} for r in results]},
                  notes=";".join(a.run_dirs))
    print(json.dumps(results, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
