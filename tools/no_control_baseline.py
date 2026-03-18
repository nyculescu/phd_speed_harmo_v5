#!/usr/bin/env python3
"""
tools/no_control_baseline.py
No-control (open-loop) baseline diagnostic for the ramp_on_v0 topology.

Research question
-----------------
  "At what demand level does the merge at seg_0_after break down,
   and is the breakdown predictable or stochastic?"

Method
------
For each of 5 demand scenarios (mainline / ramp veh/h):
  1. Build a temporary SUMO route file with constant flows.
  2. Run SUMO via TraCI for 3 600 s (warmup: 300 s; observation: 3 300 s).
  3. Every 30 s read all E1 induction-loop detectors (the same loops
     defined in detectors_ramp_on_v0.add.xml).
  4. Detect breakdown: harmonic-mean speed across seg_0_after entry loops
     drops below 60 km/h (≈ 16.67 m/s) for at least one 30-s window.
  5. Write per-scenario CSV  → tools/results/baseline_<main>_<ramp>.csv
  6. Write aggregate summary → tools/results/baseline_summary.csv
  7. Optionally plot speed heat-map per scenario (requires matplotlib).

Usage
-----
  cd /path/to/phd_speed_harmo_v5
  python3 -m tools.no_control_baseline          # all 5 scenarios
  python3 -m tools.no_control_baseline --gui    # with sumo-gui (slow)
  python3 -m tools.no_control_baseline --seed 42

Outputs
-------
  tools/results/baseline_<main>_<ramp>.csv
      columns: t_start, t_end,
               flow_seg0after_entry, speed_seg0after_entry,   # [veh/30s], [m/s]
               flow_seg0after_mid,   speed_seg0after_mid,
               flow_seg0after_exit,  speed_seg0after_exit,
               flow_ramp_merge_exit, speed_ramp_merge_exit,
               flow_seg0before_exit, speed_seg0before_exit,
               breakdown              # 1 if breakdown in this window, else 0

  tools/results/baseline_summary.csv
      columns: main_veh_h, ramp_veh_h, breakdown_occurred,
               breakdown_time_s, mean_speed_seg0after_entry_mps,
               min_speed_seg0after_entry_mps, total_throughput_veh

Notes
-----
* Space-mean speed is estimated as the harmonic mean of per-lane speeds,
  weighted by flow.  When no vehicles are detected the window speed is NaN
  (not counted as breakdown).
* The detector IDs must match detectors_ramp_on_v0.add.xml exactly.
* The network file ramp_on_v0.net.xml must exist (run generate_ramp_network.py
  first, then open in netedit and compute junctions).
"""

from __future__ import annotations

import argparse
import csv
import math
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Tuple

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
_SUMO_DIR = _ROOT / "traffic_environment" / "sumo"
_NET_FILE = _SUMO_DIR / "ramp_on_v0.net.xml"
_ADD_FILE = _SUMO_DIR / "detectors_ramp_on_v0.add.xml"
_RESULTS_DIR = _HERE / "results"
_SUMO_BIN = "sumo"

# ---------------------------------------------------------------------------
# Simulation parameters
# ---------------------------------------------------------------------------
SIM_DURATION_S = 3_600        # total episode length (s)
WARMUP_S = 300                # warmup: no measurements collected
AGG_WINDOW_S = 30             # E1 aggregation window (= detector freq)
SIM_STEP_S = 1.0              # SUMO step length (s)

BREAKDOWN_SPEED_MPS = 60.0 / 3.6   # 60 km/h → m/s
BREAKDOWN_MIN_FLOW = 1              # require ≥1 vehicle to declare breakdown

# ---------------------------------------------------------------------------
# Demand scenarios  (mainline veh/h, ramp veh/h)
# ---------------------------------------------------------------------------
SCENARIOS: List[Tuple[int, int]] = [
    (1_200, 200),
    (1_800, 300),
    (2_400, 400),
    (3_000, 500),
    (3_600, 600),
]

# ---------------------------------------------------------------------------
# Detector groups to collect
# ---------------------------------------------------------------------------
# Each entry: (csv_prefix, [loop_ids])
# We report harmonic-mean speed and summed flow across the listed loops.
_DETECTOR_GROUPS = [
    ("seg0after_entry", [
        "flow_loop_seg_0_after_0_entry",
        "flow_loop_seg_0_after_1_entry",
        "flow_loop_seg_0_after_2_entry",
    ]),
    ("seg0after_mid", [
        "flow_loop_seg_0_after_0_mid",
        "flow_loop_seg_0_after_1_mid",
        "flow_loop_seg_0_after_2_mid",
    ]),
    ("seg0after_exit", [
        "flow_loop_seg_0_after_0_exit",
        "flow_loop_seg_0_after_1_exit",
        "flow_loop_seg_0_after_2_exit",
    ]),
    ("ramp_merge_exit", [
        "flow_loop_ramp_on_merge_0_exit",
    ]),
    ("seg0before_exit", [
        "flow_loop_seg_0_before_0_exit",
        "flow_loop_seg_0_before_1_exit",
        "flow_loop_seg_0_before_2_exit",
    ]),
]

# ---------------------------------------------------------------------------
# Vehicle types (simplified 2-class fleet for the diagnostic)
# ---------------------------------------------------------------------------
_VTYPES_XML = """
    <vType id="car"   length="4.5"  accel="2.6" decel="4.5" sigma="0.5"
           maxSpeed="36.11" minGap="2.5" tau="1.2" color="1,1,0"/>
    <vType id="truck" length="7.5"  accel="1.8" decel="3.8" sigma="0.4"
           maxSpeed="28.0"  minGap="3.5" tau="1.5" color="0.5,0.5,0.5"
           vClass="truck"/>
"""

# Fraction of trucks in the flow (rest are cars)
TRUCK_FRACTION = 0.15

# Routes
_MAINLINE_EDGES = "seg_2_before seg_1_before seg_0_before seg_0_after seg_1_after"
_RAMP_EDGES = "ramp_on_approach ramp_on_transition ramp_on_merge seg_0_after seg_1_after"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _Window(NamedTuple):
    t_start: float
    t_end: float
    groups: Dict[str, Tuple[float, float]]   # prefix → (flow_veh, speed_mps)
    breakdown: int                            # 0 or 1


def _harmonic_mean_speed(speeds: List[float], flows: List[float]) -> float:
    """Flow-weighted harmonic mean speed (space-mean speed estimator).

    Returns NaN when total flow is zero or any speed is non-positive.
    """
    total_flow = sum(flows)
    if total_flow <= 0:
        return float("nan")
    # Harmonic mean: N / Σ(1/v_i) — here weighted by flow
    inv_sum = 0.0
    for s, f in zip(speeds, flows):
        if s <= 0.0:
            return float("nan")
        inv_sum += f / s
    if inv_sum <= 0.0:
        return float("nan")
    return total_flow / inv_sum


def _build_route_file(main_veh_h: int, ramp_veh_h: int, duration_s: int) -> str:
    """Write a temporary SUMO route file and return its path."""
    car_main  = int(round(main_veh_h * (1.0 - TRUCK_FRACTION)))
    truck_main = main_veh_h - car_main
    car_ramp  = int(round(ramp_veh_h * (1.0 - TRUCK_FRACTION)))
    truck_ramp = ramp_veh_h - car_ramp

    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd">
{_VTYPES_XML}
    <route id="mainline" edges="{_MAINLINE_EDGES}"/>
    <route id="ramp"     edges="{_RAMP_EDGES}"/>

    <!-- Mainline cars -->
    <flow id="fmc" type="car"   route="mainline"
          begin="0" end="{duration_s}" vehsPerHour="{car_main}"
          departLane="best" departSpeed="desired" insertionChecks="none"/>
    <!-- Mainline trucks -->
    <flow id="fmt" type="truck" route="mainline"
          begin="0" end="{duration_s}" vehsPerHour="{truck_main}"
          departLane="best" departSpeed="desired" insertionChecks="none"/>
    <!-- Ramp cars -->
    <flow id="frc" type="car"   route="ramp"
          begin="0" end="{duration_s}" vehsPerHour="{car_ramp}"
          departLane="best" departSpeed="desired" insertionChecks="none"/>
    <!-- Ramp trucks -->
    <flow id="frt" type="truck" route="ramp"
          begin="0" end="{duration_s}" vehsPerHour="{truck_ramp}"
          departLane="best" departSpeed="desired" insertionChecks="none"/>
</routes>
"""
    fd, path = tempfile.mkstemp(suffix=".rou.xml", prefix="baseline_")
    with os.fdopen(fd, "w") as f:
        f.write(content)
    return path


def _build_sumocfg(net_file: str, rou_file: str, add_file: str,
                   step_length: float, seed: int) -> str:
    """Write a temporary sumocfg and return its path."""
    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<configuration>
  <input>
    <net-file value="{net_file}"/>
    <route-files value="{rou_file}"/>
    <additional-files value="{add_file}"/>
  </input>
  <time>
    <step-length value="{step_length}"/>
  </time>
  <processing>
    <collision.action value="warn"/>
    <time-to-teleport value="300"/>
  </processing>
  <random_number>
    <seed value="{seed}"/>
  </random_number>
  <report>
    <no-step-log value="true"/>
    <verbose value="false"/>
  </report>
</configuration>
"""
    fd, path = tempfile.mkstemp(suffix=".sumocfg", prefix="baseline_")
    with os.fdopen(fd, "w") as f:
        f.write(content)
    return path


def _run_scenario(
    main_veh_h: int,
    ramp_veh_h: int,
    seed: int,
    use_gui: bool,
) -> List[_Window]:
    """Run one SUMO scenario and return per-window measurements."""
    import traci

    rou_file = _build_route_file(main_veh_h, ramp_veh_h, SIM_DURATION_S)
    cfg_file = _build_sumocfg(
        str(_NET_FILE), rou_file, str(_ADD_FILE), SIM_STEP_S, seed
    )

    sumo_bin = "sumo-gui" if use_gui else _SUMO_BIN
    traci.start([sumo_bin, "-c", cfg_file])

    windows: List[_Window] = []
    step = 0
    t = 0.0
    steps_per_window = int(AGG_WINDOW_S / SIM_STEP_S)
    total_steps = int(SIM_DURATION_S / SIM_STEP_S)
    warmup_steps = int(WARMUP_S / SIM_STEP_S)

    try:
        while step < total_steps:
            # Advance one aggregation window
            for _ in range(steps_per_window):
                traci.simulationStep()
                step += 1

            t_end = step * SIM_STEP_S
            t_start = t_end - AGG_WINDOW_S

            if step <= warmup_steps:
                continue  # skip warmup windows

            # Read detector data
            groups: Dict[str, Tuple[float, float]] = {}
            for prefix, loop_ids in _DETECTOR_GROUPS:
                speeds = []
                flows = []
                for lid in loop_ids:
                    spd = traci.inductionloop.getLastIntervalMeanSpeed(lid)
                    n   = traci.inductionloop.getLastIntervalVehicleNumber(lid)
                    if spd > 0 and n >= 0:
                        speeds.append(spd)
                        flows.append(float(n))
                    else:
                        speeds.append(float("nan"))
                        flows.append(0.0)
                total_flow = sum(flows)
                hmean = _harmonic_mean_speed(
                    [s for s, f in zip(speeds, flows) if f > 0],
                    [f for f in flows if f > 0],
                ) if any(f > 0 for f in flows) else float("nan")
                groups[prefix] = (total_flow, hmean)

            # Breakdown: speed at seg_0_after entry < threshold AND flow > 0
            entry_flow, entry_speed = groups.get("seg0after_entry", (0.0, float("nan")))
            breakdown = 0
            if (not math.isnan(entry_speed)
                    and entry_flow >= BREAKDOWN_MIN_FLOW
                    and entry_speed < BREAKDOWN_SPEED_MPS):
                breakdown = 1

            windows.append(_Window(t_start=t_start, t_end=t_end,
                                   groups=groups, breakdown=breakdown))

    finally:
        traci.close()
        os.unlink(rou_file)
        os.unlink(cfg_file)

    return windows


def _write_csv(windows: List[_Window], path: Path) -> None:
    """Write per-window measurements to a CSV file."""
    fieldnames = ["t_start_s", "t_end_s"]
    for prefix, _ in _DETECTOR_GROUPS:
        fieldnames += [f"flow_{prefix}_veh30s", f"speed_{prefix}_mps"]
    fieldnames.append("breakdown")

    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for w in windows:
            row: Dict = {"t_start_s": w.t_start, "t_end_s": w.t_end,
                         "breakdown": w.breakdown}
            for prefix, _ in _DETECTOR_GROUPS:
                flow, speed = w.groups.get(prefix, (float("nan"), float("nan")))
                row[f"flow_{prefix}_veh30s"] = f"{flow:.1f}"
                row[f"speed_{prefix}_mps"] = f"{speed:.3f}" if not math.isnan(speed) else "nan"
            writer.writerow(row)


def _scenario_summary(
    main_veh_h: int,
    ramp_veh_h: int,
    windows: List[_Window],
) -> Dict:
    """Compute summary statistics for one scenario."""
    entry_speeds = [
        w.groups["seg0after_entry"][1]
        for w in windows
        if not math.isnan(w.groups.get("seg0after_entry", (0, float("nan")))[1])
    ]
    total_flow = sum(
        w.groups.get("seg0after_exit", (0.0, float("nan")))[0]
        for w in windows
    )
    breakdown_windows = [w for w in windows if w.breakdown == 1]
    breakdown_occurred = 1 if breakdown_windows else 0
    breakdown_time = breakdown_windows[0].t_start if breakdown_windows else float("nan")

    return {
        "main_veh_h": main_veh_h,
        "ramp_veh_h": ramp_veh_h,
        "breakdown_occurred": breakdown_occurred,
        "breakdown_time_s": f"{breakdown_time:.0f}" if not math.isnan(breakdown_time) else "nan",
        "mean_speed_seg0after_entry_mps": (
            f"{sum(entry_speeds)/len(entry_speeds):.3f}" if entry_speeds else "nan"
        ),
        "min_speed_seg0after_entry_mps": (
            f"{min(entry_speeds):.3f}" if entry_speeds else "nan"
        ),
        "total_throughput_veh": f"{total_flow:.0f}",
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="No-control baseline diagnostic for ramp_on_v0."
    )
    parser.add_argument(
        "--gui", action="store_true",
        help="Use sumo-gui instead of sumo (interactive, slow).",
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="SUMO random seed (default: 42).",
    )
    parser.add_argument(
        "--scenarios", type=str, default=None,
        help="Comma-separated list of scenario indices to run (0-4). Default: all.",
    )
    parser.add_argument(
        "--no-plot", dest="plot", action="store_false", default=True,
        help="Skip matplotlib plots.",
    )
    args = parser.parse_args()

    # Verify prerequisites
    if not _NET_FILE.exists():
        print(
            f"ERROR: {_NET_FILE} not found.\n"
            "Run traffic_environment/sumo/generate_ramp_network.py first,\n"
            "then open in netedit and compute junctions.",
            file=sys.stderr,
        )
        return 1
    if not _ADD_FILE.exists():
        print(f"ERROR: {_ADD_FILE} not found.", file=sys.stderr)
        return 1

    # Filter scenarios
    if args.scenarios:
        indices = [int(x.strip()) for x in args.scenarios.split(",")]
        scenarios = [SCENARIOS[i] for i in indices]
    else:
        scenarios = list(SCENARIOS)

    _RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    summaries = []

    for main_veh_h, ramp_veh_h in scenarios:
        label = f"{main_veh_h}_{ramp_veh_h}"
        print(
            f"\n{'='*60}\n"
            f"Scenario: mainline={main_veh_h} veh/h  ramp={ramp_veh_h} veh/h\n"
            f"{'='*60}"
        )

        windows = _run_scenario(main_veh_h, ramp_veh_h, args.seed, args.gui)

        # Per-scenario CSV
        csv_path = _RESULTS_DIR / f"baseline_{label}.csv"
        _write_csv(windows, csv_path)
        print(f"  Per-window data → {csv_path}")

        # Summary
        summary = _scenario_summary(main_veh_h, ramp_veh_h, windows)
        summaries.append(summary)
        bd = "YES" if summary["breakdown_occurred"] else "NO"
        print(
            f"  Breakdown: {bd}"
            + (f"  at t={summary['breakdown_time_s']} s" if bd == "YES" else "")
        )
        print(f"  Mean speed @ seg_0_after entry: {summary['mean_speed_seg0after_entry_mps']} m/s")
        print(f"  Min  speed @ seg_0_after entry: {summary['min_speed_seg0after_entry_mps']} m/s")
        print(f"  Total throughput (exit):         {summary['total_throughput_veh']} veh")

        # Optional plot
        if args.plot:
            _plot_scenario(main_veh_h, ramp_veh_h, windows)

    # Summary CSV
    summary_path = _RESULTS_DIR / "baseline_summary.csv"
    with open(summary_path, "w", newline="") as f:
        if summaries:
            writer = csv.DictWriter(f, fieldnames=list(summaries[0].keys()))
            writer.writeheader()
            writer.writerows(summaries)
    print(f"\nSummary → {summary_path}")
    return 0


def _plot_scenario(main_veh_h: int, ramp_veh_h: int, windows: List[_Window]) -> None:
    """Plot speed time-series and flow for one scenario (matplotlib)."""
    try:
        import matplotlib.pyplot as plt  # type: ignore
    except ImportError:
        return

    t_mid = [(w.t_start + w.t_end) / 2.0 for w in windows]

    fig, axes = plt.subplots(2, 1, figsize=(12, 6), sharex=True)

    # Speed plot
    ax = axes[0]
    for prefix, _ in _DETECTOR_GROUPS:
        speeds_ms = [
            w.groups[prefix][1] if not math.isnan(w.groups.get(prefix, (0, float("nan")))[1])
            else float("nan")
            for w in windows
        ]
        speeds_kph = [s * 3.6 if not math.isnan(s) else float("nan") for s in speeds_ms]
        ax.plot(t_mid, speeds_kph, label=prefix, linewidth=1.2)

    ax.axhline(60.0, color="red", linestyle="--", linewidth=1.0, label="Breakdown threshold (60 kph)")
    ax.axvline(WARMUP_S, color="grey", linestyle=":", linewidth=0.8, label="Warmup end")
    ax.set_ylabel("Speed (km/h)")
    ax.set_title(f"No-control baseline: mainline={main_veh_h} veh/h, ramp={ramp_veh_h} veh/h")
    ax.legend(fontsize=7, ncol=2)
    ax.set_ylim(0, 150)

    # Flow plot
    ax2 = axes[1]
    for prefix, _ in _DETECTOR_GROUPS:
        flows = [w.groups.get(prefix, (float("nan"), 0))[0] for w in windows]
        ax2.plot(t_mid, flows, label=prefix, linewidth=1.2)

    ax2.set_xlabel("Simulation time (s)")
    ax2.set_ylabel("Flow (veh / 30 s)")
    ax2.legend(fontsize=7, ncol=2)

    fig.tight_layout()
    label = f"{main_veh_h}_{ramp_veh_h}"
    plot_path = _RESULTS_DIR / f"baseline_{label}.png"
    fig.savefig(plot_path, dpi=150)
    plt.close(fig)
    print(f"  Plot → {plot_path}")


if __name__ == "__main__":
    raise SystemExit(main())
