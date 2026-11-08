"""Part 3: run counts, hours and dollars for a Plan B round with 2, 3 or 4 new cells (planning only, no runs).

Sources of the rates:
- rental A (V475): EPYC 7702, 59 workers, $0.312/h; 2,600-3,050 runs/h on the S0/S1 mix. From the stored file times
  (measure_s01_remote/st/*.npz mtimes) the X1/X2 rows at 5,300 with the pack ran at about 2,450 runs/h, band rows at about 2,960,
  so 2,450-3,050 is used here. Batch was 88 % of wall time (V475), so wall = batch / 0.88.
- rental B (V461): two 3E-X searches, 122 workers each, $0.81/h; 2 x 15,680 runs in about 4.85-4.9 h, about 6,400 runs/h.
- laptop (V425, V426): 31 workers, 1,330 runs/h by day; night 23:00-09:00 is capped at 40 % CPU (author rule), assumed about
  530 runs/h (40/97 of the day rate: an assumption, not measured).
- 3E per-cell search (round 2, cma3e_x1/meta.json, runs.jsonl): population 24 x 16 seeds per generation, 40 reference runs, final
  7 configurations x 40 tuning seeds; 40 generations = 15,680 runs. 100 = the original 3E pre-registration (V441/V443); 150 is a
  guess at what a convergence rule might need (not measured)."""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
RATE_A = (2450.0, 3050.0)     # runs/h, 59 workers
USD_PER_H_A = 0.312
RATE_B = 6400.0     # runs/h, 244 workers in total
USD_PER_H_B = 0.81
LAPTOP_DAY, LAPTOP_NIGHT = 1330.0, 530.0
BATCH_SHARE = 0.88


def cma_runs(gens: int) -> int:
    return gens * 24 * 16 + 40 + 7 * 40


def per_cell(n: int, gens: int, opp: int, checks: int = 300, pilot_seeds: int = 10, grid: bool = False) -> dict:
    arms = opp + 5 + 1     # opponents + v3w's 5 learners + no control
    return {"eval": arms * n, "cma": cma_runs(gens), "checks": checks, "pilot": arms * pilot_seeds,
            "grid": 69 * 20 if grid else 0}


def laptop_days(runs: float) -> float:
    per_day = 14 * LAPTOP_DAY + 10 * LAPTOP_NIGHT
    return runs / per_day


def row(cells: int, n: int, gens: int, opp: int, grid: bool = False) -> dict:
    c = per_cell(n, gens, opp, grid=grid)
    total = cells * sum(c.values())
    hA = [total / r / BATCH_SHARE for r in RATE_A]
    usdA = [total / r * USD_PER_H_A / BATCH_SHARE for r in RATE_A]
    hB = total / RATE_B / BATCH_SHARE
    usdB = hB * USD_PER_H_B
    return {"cells": cells, "n": n, "gens": gens, "opponents": opp, "grid": grid, "per_cell": c, "total": total,
            "eval_total": cells * c["eval"], "cma_total": cells * c["cma"],
            "rentalA_h": hA, "rentalA_usd": usdA, "rentalB_h": hB, "rentalB_usd": usdB,
            "laptop_day_h": total / LAPTOP_DAY, "laptop_days": laptop_days(total),
            "eval_only_rentalA_h": [cells * c["eval"] / r / BATCH_SHARE for r in RATE_A]}


def main():
    rows = []
    for cells in (2, 3, 4):
        for n in (40, 60, 80):
            for gens in (40, 100, 150):
                rows.append(row(cells, n, gens, 15))
    rows.append(row(3, 60, 100, 15, grid=True))
    for opp in (14, 18):
        rows.append(row(3, 60, 100, opp))
    (OUT / "cost.json").write_text(json.dumps(rows, indent=1))
    L = ["| cells | n | 3E gens | runs: eval / 3E / checks+pilot | total runs | rental A h (59 w) | rental A $ | rental B h (244 w) | "
         "rental B $ | laptop days (day+night) |", "|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        c = r["per_cell"]
        cp = r["cells"] * (c["checks"] + c["pilot"] + c["grid"])
        tag = f" (opp {r['opponents']}{', grid re-pick' if r['grid'] else ''})" if r["opponents"] != 15 or r["grid"] else ""
        L.append(f"| {r['cells']}{tag} | {r['n']} | {r['gens']} | {r['eval_total']:,} / {r['cma_total']:,} / {cp:,} | {r['total']:,} | "
                 f"{r['rentalA_h'][1]:.1f}-{r['rentalA_h'][0]:.1f} | {r['rentalA_usd'][1]:.2f}-{r['rentalA_usd'][0]:.2f} | "
                 f"{r['rentalB_h']:.1f} | {r['rentalB_usd']:.2f} | {r['laptop_days']:.1f} |")
    L.append("")
    L.append("Evaluation only (no 3E search), rental A hours: "
             + "; ".join(f"{r['cells']} cells n {r['n']}: {r['eval_total']:,} runs, {r['eval_only_rentalA_h'][1]:.2f}-"
                         f"{r['eval_only_rentalA_h'][0]:.2f} h" for r in rows if r["gens"] == 40 and r["opponents"] == 15
                         and not r["grid"]))
    # sequential floor of one 3E search: generations x waves x run time
    for w, run_s in ((59, 59 * 3600 / RATE_A[0]), (122, 127.0)):
        waves = -(-384 // w)
        L.append(f"One 3E search alone on {w} workers: {waves} waves per generation x about {run_s:.0f} s = about "
                 f"{waves * run_s / 60:.0f} min per generation; 100 generations about {100 * waves * run_s / 3600:.0f} h "
                 f"(V461 measured 437 s per generation on 122 workers).")
    (OUT / "cost_table.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
