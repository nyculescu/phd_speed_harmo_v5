#!/usr/bin/env python3
"""
tools/eval_to_kpi.py — paper-ready KPI extractor for evaluate_models.py outputs.

Pure post-processing of `evaluation_summary.csv` files (one row per
policy × episode). Computes the §8.4 KPI list and the §8.5 reporting-style
breakdowns documented in docs/plans/phd_thesis_plan_v0.md.

Usage:
  # Single experiment — print to stdout
  python tools/eval_to_kpi.py --experiment training_runs/experiment_20260518_133246

  # Multiple experiments — single + cross-experiment comparison
  python tools/eval_to_kpi.py \
      --experiment training_runs/experiment_20260518_133246 \
      --experiment training_runs/experiment_20260518_133504 \
      --experiment training_runs/experiment_20260518_142808 \
      --experiment training_runs/experiment_20260518_144123

  # Write everything to disk under reports/
  python tools/eval_to_kpi.py \
      --experiment training_runs/experiment_20260518_133246 \
      --experiment training_runs/experiment_20260518_133504 \
      --out reports/2026-05-19_ablation/

The cross-experiment comparison ONLY uses reward-independent physical KPIs
(lane_sigma, max_lane_diff, ds_flow, action stats, collisions) and within-
config gap-over-baselines — never raw cross-config reward, per the §8.5.4
cross-config reward-yardstick caveat in the plan.
"""
from __future__ import annotations

import argparse
import csv
import statistics
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


# ---------------------------------------------------------------------------
# IO
# ---------------------------------------------------------------------------

def find_latest_eval_csv(experiment_dir: Path) -> Path:
    """Return the most-recent evaluation_*/evaluation_summary.csv under the dir."""
    candidates = sorted(experiment_dir.glob("evaluation_*/evaluation_summary.csv"))
    if not candidates:
        raise FileNotFoundError(
            f"No evaluation_*/evaluation_summary.csv under {experiment_dir}"
        )
    return candidates[-1]


def load_rows(csv_path: Path) -> List[Dict[str, str]]:
    with csv_path.open() as f:
        return list(csv.DictReader(f))


def find_config_yaml(experiment_dir: Path) -> Optional[Path]:
    """Return the algo/config.yaml snapshot if present (post-2026-05-18 runs)."""
    candidates = list(experiment_dir.glob("*/config.yaml"))
    return candidates[0] if candidates else None


def detect_reward_weights(experiment_dir: Path) -> Optional[Dict[str, float]]:
    cfg = find_config_yaml(experiment_dir)
    if cfg is None:
        return None
    # Parse the reward_weights block without pulling in yaml just for this.
    out: Dict[str, float] = {}
    in_block = False
    for line in cfg.read_text().splitlines():
        s = line.strip()
        if s.startswith("reward_weights"):
            in_block = True
            continue
        if in_block:
            if not s or not s[0].isalpha() and s[0] != "w":
                break
            if ":" in s and s.split(":", 1)[0].strip() in {"w_h", "w_t", "w_q", "w_l", "w_s"}:
                k, v = s.split(":", 1)
                try:
                    out[k.strip()] = float(v.strip())
                except ValueError:
                    pass
            else:
                break
    return out or None


# ---------------------------------------------------------------------------
# Math helpers
# ---------------------------------------------------------------------------

def fmean(values: Iterable[float]) -> float:
    vals = [float(v) for v in values if v not in ("", None)]
    return statistics.fmean(vals) if vals else float("nan")


def fstd(values: Iterable[float]) -> float:
    vals = [float(v) for v in values if v not in ("", None)]
    return statistics.pstdev(vals) if len(vals) > 1 else 0.0


def fmin(values: Iterable[float]) -> float:
    vals = [float(v) for v in values if v not in ("", None)]
    return min(vals) if vals else float("nan")


def fmax(values: Iterable[float]) -> float:
    vals = [float(v) for v in values if v not in ("", None)]
    return max(vals) if vals else float("nan")


def fsum_int(values: Iterable[Any]) -> int:
    """Sum a column as integers (0 for empty / None)."""
    return sum(int(v or 0) for v in values)


def fraction(rows: List[Dict[str, str]], predicate) -> float:
    if not rows:
        return float("nan")
    return sum(1 for r in rows if predicate(r)) / len(rows)


# ---------------------------------------------------------------------------
# Per-policy aggregation
# ---------------------------------------------------------------------------

POLICY_ORDER = [
    "NC", "M110_uniform", "diff_mild",
    "M60_active", "M70_active", "M80_active", "M90_active", "M100_active", "M110_active",
    "diff_mild_active", "diff_aggressive_active",
]


def group_by_policy(rows: List[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
    out: Dict[str, List[Dict[str, str]]] = {}
    for r in rows:
        out.setdefault(r["policy"], []).append(r)
    return out


def trained_seed_keys(by_policy: Dict[str, List[Dict[str, str]]]) -> List[str]:
    return sorted(p for p in by_policy if "_seed" in p)


def policy_kpis(prs: List[Dict[str, str]]) -> Dict[str, float]:
    """Compute the §8.4 KPIs for a single policy across its 30-ish episodes."""
    return {
        "n_eps":              len(prs),
        # KPI 1
        "reward_mean":        fmean(r["total_reward"] for r in prs),
        "reward_std":         fstd(r["total_reward"] for r in prs),
        "reward_best":        fmax(r["total_reward"] for r in prs),
        "reward_worst":       fmin(r["total_reward"] for r in prs),
        # KPI 2
        "ds_flow_vph":        fmean(r["avg_ds_flow_vph"] for r in prs),
        # KPI 3
        "lane_sigma":         fmean(r["avg_rc_lane_sigma"] for r in prs),
        # KPI 4
        "max_lane_diff_kph":  fmean(r["avg_rc_max_lane_diff_kph"] for r in prs),
        # KPI 5
        "merge_speed_kph":    fmean(r["avg_merge_speed_kph"] for r in prs),
        # KPI 6
        "action_L0_std":      fmean(r["action_L0_std"] for r in prs),
        "action_L1_std":      fmean(r["action_L1_std"] for r in prs),
        "action_L2_std":      fmean(r["action_L2_std"] for r in prs),
        "action_ramp_std":    fmean(r["action_ramp_std"] for r in prs),
        # KPI 7
        "per_lane_util_frac": fraction(prs, lambda r: abs(float(r["action_L0_L2_mean_diff"])) > 10.0),
        "action_L0_L2_diff":  fmean(r["action_L0_L2_mean_diff"] for r in prs),
        # KPI 9 — safety-by-construction evidence
        "collisions_total":   fsum_int(r.get("episode_collision_count") for r in prs),
        # KPI 10 — reward-component decomposition
        "rc_harmo":           fmean(r["avg_rc_harmonization"] for r in prs),
        "rc_temporal":        fmean(r["avg_rc_temporal"] for r in prs),
        "rc_throughput":      fmean(r["avg_rc_throughput"] for r in prs),
        "rc_lane_eq":         fmean(r["avg_rc_lane_equalisation"] for r in prs),
        "rc_smoothness":      fmean(r["avg_rc_smoothness"] for r in prs),
        # Tier-A safety / system performance (already computed by EvalMetricsCollector)
        "hard_brake_count":   fmean(r.get("hard_brake_count", 0) or 0 for r in prs),
        "min_ttc_s":          fmin(r["min_ttc_s"] for r in prs if r.get("min_ttc_s")),
        "mean_ttc_s":         fmean(r["mean_ttc_s"] for r in prs if r.get("mean_ttc_s")),
        "n_ttc_critical":     fmean(r.get("n_ttc_critical", 0) or 0 for r in prs),
        "lc_per_veh_per_km":  fmean(r.get("lc_per_veh_per_km", 0) or 0 for r in prs),
        "mean_travel_time_s": fmean(r.get("mean_travel_time_s", 0) or 0 for r in prs),
        "p95_travel_time_s":  fmean(r.get("p95_travel_time_s", 0) or 0 for r in prs),
        "total_tts_veh_h":    fmean(r.get("total_tts_veh_h", 0) or 0 for r in prs),
        "regime_metastable":  fmean(r.get("regime_metastable_pct", 0) or 0 for r in prs),
        "regime_congested":   fmean(r.get("regime_congested_pct", 0) or 0 for r in prs),
    }


def trained_seeds_aggregate(by_policy: Dict[str, List[Dict[str, str]]]) -> Dict[str, float]:
    """Aggregate KPIs across all trained-seed policies in one experiment.

    The mean is taken across SEEDS (each seed's per-seed mean weighted equally)
    so a 3-seed and 5-seed run are comparable on the same axis. The spread
    captures cross-seed variance, not within-seed (episode) variance.
    """
    seeds = trained_seed_keys(by_policy)
    if not seeds:
        return {}
    per_seed_kpis = {s: policy_kpis(by_policy[s]) for s in seeds}
    out: Dict[str, float] = {"n_seeds": len(seeds)}
    # Cross-seed aggregates for reward
    seed_means = [k["reward_mean"] for k in per_seed_kpis.values()]
    out["reward_mean_across_seeds"] = fmean(seed_means)
    out["reward_spread_seed"]       = fmax(seed_means) - fmin(seed_means)
    out["reward_best_seed"]         = fmax(seed_means)
    out["reward_worst_seed"]        = fmin(seed_means)
    # Physical KPI means (cross-seed)
    for k in ("ds_flow_vph", "lane_sigma", "max_lane_diff_kph", "merge_speed_kph",
              "action_L0_std", "action_L0_L2_diff", "per_lane_util_frac",
              "rc_harmo", "rc_temporal", "rc_throughput", "rc_lane_eq", "rc_smoothness",
              "hard_brake_count", "min_ttc_s", "mean_ttc_s", "n_ttc_critical",
              "lc_per_veh_per_km", "mean_travel_time_s", "p95_travel_time_s",
              "total_tts_veh_h", "regime_metastable", "regime_congested"):
        out[k] = fmean(k_dict[k] for k_dict in per_seed_kpis.values() if k in k_dict)
    out["collisions_total"] = sum(k["collisions_total"] for k in per_seed_kpis.values())
    return out


# ---------------------------------------------------------------------------
# Anomaly + ramp-fraction breakdowns
# ---------------------------------------------------------------------------

def anomaly_breakdown(by_policy: Dict[str, List[Dict[str, str]]]) -> List[Dict[str, Any]]:
    """For each policy, mean reward in {normal, anomaly} episodes + delta."""
    out = []
    for pol in policy_order_for(by_policy):
        prs = by_policy[pol]
        normal = [r for r in prs if (r.get("anomaly_type") or "none") == "none"]
        anom   = [r for r in prs if (r.get("anomaly_type") or "none") != "none"]
        r_n = fmean(r["total_reward"] for r in normal) if normal else float("nan")
        r_a = fmean(r["total_reward"] for r in anom)   if anom else float("nan")
        out.append({
            "policy":         pol,
            "n_normal":       len(normal),
            "n_anomaly":      len(anom),
            "reward_normal":  r_n,
            "reward_anomaly": r_a,
            "delta":          r_a - r_n if normal and anom else float("nan"),
        })
    return out


def ramp_quartile_breakdown(prs: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """Bin a policy's episodes by ramp_fraction quartile and return per-quartile reward.

    Quartiles are computed within the policy's own ramp_fraction distribution
    (so they're robust to whatever the eval pool sampled).
    """
    vals = sorted(float(r["ramp_fraction"]) for r in prs)
    if len(vals) < 4:
        return []
    q1, q2, q3 = (
        statistics.quantiles(vals, n=4, method="inclusive")
        if hasattr(statistics, "quantiles") else
        (vals[len(vals)//4], vals[len(vals)//2], vals[3*len(vals)//4])
    )
    bins = {"Q1 (≤{:.2f})".format(q1): [], f"Q2 (≤{q2:.2f})": [],
            f"Q3 (≤{q3:.2f})": [],     f"Q4 (>{q3:.2f})": []}
    for r in prs:
        rf = float(r["ramp_fraction"])
        if rf <= q1: bins[list(bins)[0]].append(r)
        elif rf <= q2: bins[list(bins)[1]].append(r)
        elif rf <= q3: bins[list(bins)[2]].append(r)
        else: bins[list(bins)[3]].append(r)
    return [{
        "quartile":    q,
        "n":           len(rs),
        "ramp_frac":   f"[{fmin(r['ramp_fraction'] for r in rs):.2f}, {fmax(r['ramp_fraction'] for r in rs):.2f}]" if rs else "—",
        "reward_mean": fmean(r["total_reward"] for r in rs),
        "reward_std":  fstd(r["total_reward"] for r in rs),
    } for q, rs in bins.items()]


def policy_order_for(by_policy: Dict[str, List[Dict[str, str]]]) -> List[str]:
    """Canonical ordering: NC first, then baselines, then trained seeds, then unknown."""
    seen = set(by_policy.keys())
    out  = [p for p in POLICY_ORDER if p in seen]
    out += sorted(p for p in seen if p not in POLICY_ORDER and "_seed" in p)
    out += sorted(p for p in seen if p not in POLICY_ORDER and "_seed" not in p)
    return out


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------

def fmt(v: Any, spec: str = ".2f") -> str:
    if v is None:
        return "—"
    try:
        if isinstance(v, float):
            if v != v:  # NaN
                return "—"
            return format(v, spec)
        return str(v)
    except Exception:
        return str(v)


def render_per_experiment(exp_dir: Path, csv_path: Path,
                          weights: Optional[Dict[str, float]],
                          by_policy: Dict[str, List[Dict[str, str]]]) -> str:
    out = []
    out.append(f"# KPI report — `{exp_dir.name}`\n")
    out.append(f"Source: `{csv_path.relative_to(exp_dir.parents[1])}`")
    if weights:
        wstr = ", ".join(f"{k}={v}" for k, v in sorted(weights.items()))
        out.append(f"Reward weights: `{wstr}`\n")
    else:
        out.append("Reward weights: (config.yaml not found — pre-2026-05-18 run?)\n")

    nc_reward = fmean(r["total_reward"] for r in by_policy["NC"]) if "NC" in by_policy else float("nan")
    m110_reward = fmean(r["total_reward"] for r in by_policy.get("M110_uniform", []))
    m60_reward  = fmean(r["total_reward"] for r in by_policy.get("M60_active", []))

    # ── Table 1: Per-policy headline KPIs ─────────────────────────────────
    out.append("\n## Per-policy headline (KPI 1, 2, 3, 4, 5, 9)")
    out.append("\n| Policy | n | reward μ±σ | best ep | worst ep | Δ vs NC | ds_flow_vph | lane_sigma | max_ldiff_kph | merge_kph | collisions |")
    out.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for pol in policy_order_for(by_policy):
        k = policy_kpis(by_policy[pol])
        d = k["reward_mean"] - nc_reward if nc_reward == nc_reward else float("nan")
        out.append("| {pol} | {n} | {rm}±{rs} | {b} | {w} | {d:+.1f} | {flow:.0f} | {ls:.2f} | {mld:.2f} | {mk:.1f} | {coll} |".format(
            pol=pol, n=k["n_eps"], rm=fmt(k["reward_mean"], ".1f"), rs=fmt(k["reward_std"], ".1f"),
            b=fmt(k["reward_best"], ".1f"), w=fmt(k["reward_worst"], ".1f"),
            d=d, flow=k["ds_flow_vph"], ls=k["lane_sigma"], mld=k["max_lane_diff_kph"],
            mk=k["merge_speed_kph"], coll=k["collisions_total"],
        ))

    # ── Table 2: Anomaly vs Normal (KPI 8) ─────────────────────────────────
    out.append("\n## Anomaly vs Normal (KPI 8 — anomaly robustness)")
    out.append("\n| Policy | n_normal | n_anomaly | reward(normal) | reward(anomaly) | Δ |")
    out.append("|---|---:|---:|---:|---:|---:|")
    for row in anomaly_breakdown(by_policy):
        out.append("| {pol} | {nn} | {na} | {rn} | {ra} | {d} |".format(
            pol=row["policy"], nn=row["n_normal"], na=row["n_anomaly"],
            rn=fmt(row["reward_normal"], ".1f"), ra=fmt(row["reward_anomaly"], ".1f"),
            d=fmt(row["delta"], "+.1f"),
        ))

    # ── Table 3: Action statistics (KPI 6, 7) ─────────────────────────────
    out.append("\n## Action statistics (KPI 6 — control authority, KPI 7 — per-lane utilization)")
    out.append("\n| Policy | L0_std | L1_std | L2_std | ramp_std | L0-L2 mean diff | per-lane utilization (|L0-L2|>10) |")
    out.append("|---|---:|---:|---:|---:|---:|---:|")
    for pol in policy_order_for(by_policy):
        if not any(s in pol for s in ("_seed", "_active")):
            # skip pure-static policies for action stats (they're 0 by definition)
            pass
        k = policy_kpis(by_policy[pol])
        out.append("| {pol} | {l0:.2f} | {l1:.2f} | {l2:.2f} | {r:.2f} | {d:+.2f} | {pl:.0%} |".format(
            pol=pol, l0=k["action_L0_std"], l1=k["action_L1_std"], l2=k["action_L2_std"],
            r=k["action_ramp_std"], d=k["action_L0_L2_diff"], pl=k["per_lane_util_frac"],
        ))

    # ── Table 4: Reward-component decomposition (KPI 10) ───────────────────
    out.append("\n## Reward-component decomposition (KPI 10)\n")
    out.append("Per-step averages of each `RewardSignal.components` term. Rewards are scaled by `reward_scale=5` in the env total; values here are pre-scale.\n")
    out.append("| Policy | r_harmo | r_temporal | r_throughput | r_lane_eq | r_smoothness |")
    out.append("|---|---:|---:|---:|---:|---:|")
    for pol in policy_order_for(by_policy):
        k = policy_kpis(by_policy[pol])
        out.append("| {pol} | {h:.3f} | {t:.3f} | {q:.3f} | {l:.3f} | {s:.3f} |".format(
            pol=pol, h=k["rc_harmo"], t=k["rc_temporal"], q=k["rc_throughput"],
            l=k["rc_lane_eq"], s=k["rc_smoothness"],
        ))

    # ── Table 5: Tier-A safety + system-perf (eval-only metrics) ──────────
    out.append("\n## Tier-A safety + system performance (from EvalMetricsCollector)")
    out.append("\n| Policy | min TTC s | mean TTC s | n_TTC<1 | hard_brakes/ep | LC/veh/km | mean_TT s | p95_TT s | TTS veh·h | metastable % | congested % |")
    out.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for pol in policy_order_for(by_policy):
        k = policy_kpis(by_policy[pol])
        out.append("| {pol} | {min_t:.2f} | {mean_t:.2f} | {n_t:.1f} | {hb:.1f} | {lc:.2f} | {tt:.1f} | {p95:.1f} | {tts:.1f} | {mst:.1f} | {cng:.1f} |".format(
            pol=pol, min_t=k["min_ttc_s"], mean_t=k["mean_ttc_s"], n_t=k["n_ttc_critical"],
            hb=k["hard_brake_count"], lc=k["lc_per_veh_per_km"],
            tt=k["mean_travel_time_s"], p95=k["p95_travel_time_s"], tts=k["total_tts_veh_h"],
            mst=k["regime_metastable"], cng=k["regime_congested"],
        ))

    # ── Table 6: Per-quartile ramp_fraction (trained seeds only, §8.4 reporting style) ──
    out.append("\n## Ramp-fraction quartile breakdown (trained seeds only)\n")
    out.append("Per ADR-013 the pool sweeps `ramp_fraction ∈ [0.20, 0.30]`. Per-quartile reward shows whether the policy degrades across the operational regime.\n")
    for pol in trained_seed_keys(by_policy):
        qbins = ramp_quartile_breakdown(by_policy[pol])
        if not qbins: continue
        out.append(f"\n### {pol}\n")
        out.append("| Quartile | n | ramp_frac range | reward μ±σ |")
        out.append("|---|---:|---|---:|")
        for q in qbins:
            out.append("| {q} | {n} | {rng} | {rm}±{rs} |".format(
                q=q["quartile"], n=q["n"], rng=q["ramp_frac"],
                rm=fmt(q["reward_mean"], ".1f"), rs=fmt(q["reward_std"], ".1f"),
            ))

    return "\n".join(out) + "\n"


def render_cross_experiment(experiments: List[Tuple[Path, Dict[str, List[Dict[str, str]]],
                                                     Optional[Dict[str, float]]]]) -> str:
    """Render the §8.5.1 physical-KPI + §8.5.2 within-config-gap cross-experiment tables.

    `experiments` is a list of (exp_dir, by_policy, weights) tuples.
    """
    out = ["# Cross-experiment comparison\n"]
    out.append("> ⚠ **Cross-config reward-yardstick caveat** (plan §8.5.4): when reward weights differ between configs, absolute reward numbers are not comparable. The within-config gap-over-baselines table below IS comparable (each gap is measured under the corresponding config's own yardstick).\n")

    # ── §8.5.1 physical KPIs (reward-independent) ─────────────────────────
    out.append("\n## Physical KPIs — reward-independent (apples-to-apples)\n")
    out.append("| Experiment | lane_sigma | max_ldiff_kph | ds_flow_vph | action_L0_std | L0-L2 diff | collisions | n_seeds |")
    out.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for exp_dir, by_pol, _ in experiments:
        agg = trained_seeds_aggregate(by_pol)
        if not agg:
            out.append(f"| {exp_dir.name} | (no trained seeds) | | | | | | 0 |")
            continue
        out.append("| {n} | {ls:.2f} | {ml:.2f} | {df:.0f} | {l0s:.2f} | {l0l2:+.2f} | {coll} | {ns} |".format(
            n=exp_dir.name, ls=agg["lane_sigma"], ml=agg["max_lane_diff_kph"],
            df=agg["ds_flow_vph"], l0s=agg["action_L0_std"], l0l2=agg["action_L0_L2_diff"],
            coll=agg["collisions_total"], ns=int(agg["n_seeds"]),
        ))

    # ── §8.5.2 within-config gap-over-baselines ────────────────────────────
    out.append("\n## Within-config gap over baselines (each row uses its own config's reward yardstick)\n")
    out.append("| Experiment | DRL μ | DRL best | DRL worst | seed spread | vs NC | vs M110_uniform | vs M60_active |")
    out.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for exp_dir, by_pol, _ in experiments:
        agg = trained_seeds_aggregate(by_pol)
        if not agg: continue
        nc   = fmean(r["total_reward"] for r in by_pol.get("NC", []))
        m110 = fmean(r["total_reward"] for r in by_pol.get("M110_uniform", []))
        m60  = fmean(r["total_reward"] for r in by_pol.get("M60_active", []))
        m    = agg["reward_mean_across_seeds"]
        out.append("| {n} | {m:.1f} | {b:.1f} | {w:.1f} | {sp:.1f} | {nc:+.1f} | {m110:+.1f} | {m60:+.1f} |".format(
            n=exp_dir.name, m=m,
            b=agg["reward_best_seed"], w=agg["reward_worst_seed"], sp=agg["reward_spread_seed"],
            nc=m-nc, m110=m-m110, m60=m-m60,
        ))

    # ── safety summary ─────────────────────────────────────────────────────
    out.append("\n## Safety-by-construction evidence (ADR-010)\n")
    total_ep = 0; total_coll = 0
    for exp_dir, by_pol, _ in experiments:
        ep   = sum(len(rs) for rs in by_pol.values())
        coll = sum(int(r.get("episode_collision_count") or 0) for rs in by_pol.values() for r in rs)
        total_ep += ep; total_coll += coll
        out.append(f"- `{exp_dir.name}`: **{coll} collisions / {ep} episodes**")
    out.append(f"\n**Total: {total_coll} collisions / {total_ep} evaluation episodes** across all listed experiments.")

    return "\n".join(out) + "\n"


# ---------------------------------------------------------------------------
# CSV export
# ---------------------------------------------------------------------------

def export_csv(out_path: Path, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        return
    fields = list({k for r in rows for k in r.keys()})
    # stable ordering: keep insertion order from the first row
    fields = list(rows[0].keys()) + [f for f in fields if f not in rows[0]]
    with out_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--experiment", action="append", required=True, type=Path,
                   help="Path to a training_runs/experiment_<TS>/ dir. Repeatable.")
    p.add_argument("--out", type=Path, default=None,
                   help="If given, write per-experiment .md + cross-experiment.md + .csv files into this dir.")
    args = p.parse_args()

    loaded: List[Tuple[Path, Path, Dict[str, List[Dict[str, str]]], Optional[Dict[str, float]]]] = []
    for exp_dir in args.experiment:
        if not exp_dir.is_dir():
            print(f"ERROR: not a directory: {exp_dir}", file=sys.stderr)
            return 2
        csv_path = find_latest_eval_csv(exp_dir)
        rows = load_rows(csv_path)
        by_policy = group_by_policy(rows)
        weights = detect_reward_weights(exp_dir)
        loaded.append((exp_dir, csv_path, by_policy, weights))
        print(f"[loaded] {exp_dir.name} — {len(rows)} rows, {len(by_policy)} policies", file=sys.stderr)

    # Build per-experiment markdowns
    per_exp_md: List[Tuple[Path, str]] = []
    for exp_dir, csv_path, by_pol, weights in loaded:
        md = render_per_experiment(exp_dir, csv_path, weights, by_pol)
        per_exp_md.append((exp_dir, md))

    cross_md = None
    if len(loaded) >= 2:
        cross_md = render_cross_experiment([(d, b, w) for d, _, b, w in loaded])

    if args.out is None:
        # stdout
        for exp_dir, md in per_exp_md:
            print(md)
            print("\n---\n")
        if cross_md:
            print(cross_md)
        return 0

    # write to disk
    args.out.mkdir(parents=True, exist_ok=True)
    for exp_dir, md in per_exp_md:
        (args.out / f"{exp_dir.name}_kpi.md").write_text(md)
    if cross_md:
        (args.out / "cross_experiment_comparison.md").write_text(cross_md)

    # machine-readable CSV: one row per (experiment, policy) with all the KPIs
    flat: List[Dict[str, Any]] = []
    for exp_dir, _csv, by_pol, weights in loaded:
        for pol, prs in by_pol.items():
            k = policy_kpis(prs)
            flat.append({
                "experiment": exp_dir.name,
                "policy":     pol,
                **{f"w_{wk[2:]}": wv for wk, wv in (weights or {}).items()},
                **k,
            })
    export_csv(args.out / "per_policy_kpis.csv", flat)
    # cross-experiment summary CSV
    cross_rows: List[Dict[str, Any]] = []
    for exp_dir, _, by_pol, weights in loaded:
        agg = trained_seeds_aggregate(by_pol)
        if not agg: continue
        nc   = fmean(r["total_reward"] for r in by_pol.get("NC", []))
        m110 = fmean(r["total_reward"] for r in by_pol.get("M110_uniform", []))
        m60  = fmean(r["total_reward"] for r in by_pol.get("M60_active", []))
        cross_rows.append({
            "experiment":   exp_dir.name,
            **{f"w_{wk[2:]}": wv for wk, wv in (weights or {}).items()},
            **agg,
            "vs_NC":        agg["reward_mean_across_seeds"] - nc,
            "vs_M110":      agg["reward_mean_across_seeds"] - m110,
            "vs_M60_active": agg["reward_mean_across_seeds"] - m60,
        })
    export_csv(args.out / "cross_experiment_summary.csv", cross_rows)

    print(f"\nWrote {len(per_exp_md)} per-experiment .md + cross .md + 2 .csv files under {args.out}/", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
