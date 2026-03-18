#!/usr/bin/env python3
"""
Reward landscape verification for r44_reward_v2.

Reads the existing fixed-VSL sweep data (summary.csv) and computes what
the v2 reward function WOULD return for each scenario.  This validates
that the reward landscape has the correct gradient:

  - At free-flow (5000 vph): no-control > any VSL  (don't restrict)
  - At congestion (7000 vph): moderate VSL > no-control  (restrict)
  - Throughput penalty activates only below 85% of ref_flow

No SUMO needed — this is a pure offline computation from existing data.

Usage:
    python3 tests/run_reward_landscape_check.py
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np

# Add project root to path
_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from sar_components.discovery import discover_components
from core import create_reward_function, TrafficMetrics, RewardSignal

discover_components()

# --- Config matching _common_config.yaml ---
_SAR_CONFIG = {
    "ref_flow_vph": 6000.0,
    "speed_floor_kph": 50.0,
    "harmo_spatial_blend": 0.5,
    "throughput_threshold": 0.85,
    "reward_weights": {"w_h": 0.55, "w_q": 0.30, "w_a": 0.15},
}

# --- Locate the sweep data ---
_SWEEP_CSV = (
    _ROOT / "tests" / "results"
    / "fixed_vsl_sweep_v2_18-03-2026_17-09-52" / "summary.csv"
)


def _compute_reward_for_row(
    row: dict,
    reward_func,
    prev_ds_speed_kph: float = None,
) -> dict:
    """
    Build a TrafficMetrics from the sweep CSV row and compute reward.

    The sweep CSV has per-scenario averages; we use them as a single
    representative step to check the reward landscape shape.
    """
    m = TrafficMetrics()

    # Upstream speeds — the CSV has avg_upstream_speed_kph (corridor mean)
    # and avg_sigma_upstream.  We don't have per-segment speeds directly,
    # so we reconstruct plausible per-segment speeds from the mean and sigma.
    avg_speed = float(row["avg_upstream_speed_kph"])
    sigma = float(row["avg_sigma_upstream"])

    # Simple reconstruction: s2 = mean + sigma, s1 = mean, s0 = mean - sigma
    # This gives std(s2,s1,s0) = sigma and max_gradient = sigma (approx).
    s2_kph = avg_speed + sigma
    s1_kph = avg_speed
    s0_kph = max(avg_speed - sigma, 0.0)

    m.seg_2_before_speed_ms = s2_kph / 3.6
    m.seg_1_before_speed_ms = s1_kph / 3.6
    m.seg_0_before_speed_ms = s0_kph / 3.6

    # Downstream flow
    m.seg_1_after_flow_vph = float(row["avg_ds_flow_vph"])

    # Downstream speed: approximate from corridor speed (seg_0_after stays
    # higher than upstream, use a rough estimate)
    ds_speed_kph = min(avg_speed + 15.0, 120.0)
    m.seg_0_after_speed_ms = ds_speed_kph / 3.6

    # No action delta for this static check (smoothness = 0)
    m.action = np.array([90.0, 65.0], dtype=np.float32)
    m.prev_action = np.array([90.0, 65.0], dtype=np.float32)

    signal: RewardSignal = reward_func.calculate(m)
    return {
        "total": signal.total,
        **signal.components,
        "s2_kph": s2_kph,
        "s1_kph": s1_kph,
        "s0_kph": s0_kph,
        "max_gradient": max(abs(s2_kph - s1_kph), abs(s1_kph - s0_kph)),
        "ds_flow": m.seg_1_after_flow_vph,
        "flow_ratio": m.seg_1_after_flow_vph / 6000.0,
    }


def main():
    if not _SWEEP_CSV.exists():
        print(f"Sweep CSV not found: {_SWEEP_CSV}")
        print("Run tests/run_fixed_vsl_sweep_v2.py first.")
        return 1

    reward_func = create_reward_function("r44_reward_v2", _SAR_CONFIG)

    with open(_SWEEP_CSV) as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Header
    print(f"{'demand':>7s} {'vsl':>12s} │ {'r_spatial':>9s} {'r_temporal':>10s} "
          f"{'r_harmo':>8s} {'r_q':>7s} {'r_a':>7s} │ {'total':>7s} │ "
          f"{'max_grad':>9s} {'flow_ratio':>10s} {'avg|a|':>7s}")
    print("─" * 120)

    # Group by demand
    demands = sorted(set(r["demand_vph"] for r in rows))

    for demand in demands:
        demand_rows = [r for r in rows if r["demand_vph"] == demand]
        # Sort: no_control first, then by VSL level
        demand_rows.sort(key=lambda r: (r["vsl_kph"] == "no_control", r["vsl_kph"]))

        # Reset reward func for each demand group (fresh temporal state)
        reward_func.reset()

        best_total = -999
        best_vsl = ""

        for row in demand_rows:
            result = _compute_reward_for_row(row, reward_func)

            vsl_label = row["vsl_kph"]
            avg_abs_accel = row.get("up_mean_abs_accel_ms2", "N/A")

            if result["total"] > best_total:
                best_total = result["total"]
                best_vsl = vsl_label

            print(
                f"{demand:>7s} {vsl_label:>12s} │ "
                f"{result['spatial']:>+9.4f} {result['temporal']:>+10.4f} "
                f"{result['harmonization']:>+8.4f} "
                f"{result['throughput']:>+7.4f} {result['smoothness']:>+7.4f} │ "
                f"{result['total']:>+7.4f} │ "
                f"{result['max_gradient']:>9.1f} "
                f"{result['flow_ratio']:>10.3f} "
                f"{avg_abs_accel:>7s}"
            )

            # Reset temporal state between scenarios (they're independent)
            reward_func.reset()

        print(f"         {'>>> BEST: ' + best_vsl:>12s} │{'':>29s}│ {best_total:>+7.4f} │")
        print("─" * 120)

    # --- Key checks ---
    print("\n=== Reward Landscape Checks ===\n")

    nc_5000 = next((r for r in rows if r["demand_vph"] == "5000"
                     and r["vsl_kph"] == "no_control"), None)
    vsl90_5000 = next((r for r in rows if r["demand_vph"] == "5000"
                        and r["vsl_kph"] == "90kph"), None)
    nc_7000 = next((r for r in rows if r["demand_vph"] == "7000"
                     and r["vsl_kph"] == "no_control"), None)
    vsl90_7000 = next((r for r in rows if r["demand_vph"] == "7000"
                        and r["vsl_kph"] == "90kph"), None)

    if nc_5000 and vsl90_5000:
        reward_func.reset()
        r_nc = _compute_reward_for_row(nc_5000, reward_func)
        reward_func.reset()
        r_vsl = _compute_reward_for_row(vsl90_5000, reward_func)
        gap = r_nc["total"] - r_vsl["total"]
        status = "PASS" if gap > 0 else "FAIL"
        print(f"  [{status}] 5000 vph: no-control ({r_nc['total']:+.4f}) vs "
              f"90kph ({r_vsl['total']:+.4f}), gap = {gap:+.4f} "
              f"(expect positive = don't restrict at free-flow)")

    if nc_7000 and vsl90_7000:
        reward_func.reset()
        r_nc = _compute_reward_for_row(nc_7000, reward_func)
        reward_func.reset()
        r_vsl = _compute_reward_for_row(vsl90_7000, reward_func)
        gap = r_vsl["total"] - r_nc["total"]
        status = "PASS" if gap > 0 else "FAIL"
        print(f"  [{status}] 7000 vph: 90kph ({r_vsl['total']:+.4f}) vs "
              f"no-control ({r_nc['total']:+.4f}), gap = {gap:+.4f} "
              f"(expect positive = restrict at congestion)")

    # Throughput threshold check
    print()
    for row in rows:
        ds_flow = float(row["avg_ds_flow_vph"])
        ratio = ds_flow / 6000.0
        if ratio < 0.85:
            reward_func.reset()
            result = _compute_reward_for_row(row, reward_func)
            if abs(result["throughput"]) < 0.001:
                print(f"  [FAIL] {row['demand_vph']} vph / {row['vsl_kph']}: "
                      f"flow ratio = {ratio:.3f} < 0.85 but r_q = 0 "
                      f"(throughput penalty should activate)")
                break
    else:
        print("  [PASS] Throughput penalty activates correctly for all "
              "sub-threshold scenarios")

    return 0


if __name__ == "__main__":
    sys.exit(main())
