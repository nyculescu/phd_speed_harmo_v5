#!/usr/bin/env python3
"""
tools/no_control_baseline.py
No-control (open-loop) baseline diagnostic for the ramps_v0 topology.

Research question
-----------------
  "At what demand level does the weaving section at seg_0_after break down,
   and is the breakdown predictable or stochastic?"

Topology (ramps_v0)
-------------------
  3-lane upstream → 4-lane weaving buffer (seg_0_after, 250 m) → 3-lane downstream
  On-ramp:  ramp_on_approach → ramp_on_transition → ramp_on_merge → seg_0_after lane 0
  Off-ramp: seg_0_after lane 0 → ramp_off_diverge → ramp_off_transition → ramp_off_departure

Method
------
For each of 5 demand scenarios (mainline / ramp_on veh/h):
  1. Build a temporary SUMO route file with constant flows.
     Off-ramp: a fixed fraction (15 %) of mainline vehicles take the off-ramp.
  2. Run SUMO via TraCI for 3 600 s (warmup 300 s; observation 3 300 s).
  3. Every 30 s, read all E1 induction-loop detectors.
  4. Detect breakdown: harmonic-mean speed across all seg_0_after entry loops
     drops below 60 km/h (≈ 16.67 m/s) for ≥ 1 window with ≥ 1 detected vehicle.
  5. Write per-scenario CSV  → tools/results/baseline_<main>_<ramp>.csv
  6. Write aggregate summary → tools/results/baseline_summary.csv
  7. Optionally plot speed + flow time-series (requires matplotlib).

Usage
-----
  cd /path/to/phd_speed_harmo_v5
  python3 -m tools.no_control_baseline          # all 5 scenarios
  python3 -m tools.no_control_baseline --gui    # with sumo-gui (interactive)
  python3 -m tools.no_control_baseline --seed 42 --scenarios 2,3

Outputs
-------
  tools/results/baseline_<main>_<ramp>.csv
      columns: t_start_s, t_end_s,
               flow_<group>_veh30s, speed_<group>_mps  (per detector group)
               breakdown              # 1 if breakdown in this window, else 0

  tools/results/baseline_summary.csv
      columns: main_veh_h, ramp_on_veh_h, ramp_off_frac,
               breakdown_occurred, breakdown_time_s,
               mean_speed_seg0after_entry_mps, min_speed_seg0after_entry_mps,
               total_throughput_veh

Notes
-----
* Space-mean speed: harmonic mean of per-lane speeds weighted by flow.
  Windows with zero flow are skipped (not counted as breakdown).
* Detector IDs must match detectors_ramps_v0.add.xml exactly.
* ramps_v0.net.xml must exist (run generate_ramp_network.py, then netedit
  Processing → Compute Junctions).
"""

from __future__ import annotations

import argparse
import csv
import math
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Tuple

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
_SUMO_DIR = _ROOT / "traffic_environment" / "sumo"
_NET_FILE = _SUMO_DIR / "ramps_v0.net.xml"
_ADD_FILE = _SUMO_DIR / "detectors_ramps_v0.add.xml"
_RESULTS_DIR = _HERE / "results"
_SUMO_BIN = "sumo"

# ---------------------------------------------------------------------------
# Simulation parameters
# ---------------------------------------------------------------------------
SIM_DURATION_S    = 3_600
WARMUP_S          = 300
AGG_WINDOW_S      = 30
SIM_STEP_S        = 1.0

BREAKDOWN_SPEED_MPS  = 60.0 / 3.6   # 60 km/h
BREAKDOWN_MIN_FLOW   = 1             # require ≥1 vehicle detected

# ---------------------------------------------------------------------------
# Demand scenarios: (mainline veh/h, ramp-on veh/h)
# Off-ramp volume = mainline × OFF_RAMP_FRACTION
# ---------------------------------------------------------------------------
SCENARIOS: List[Tuple[int, int]] = [
    (1_200, 200),
    (1_800, 300),
    (2_400, 400),
    (3_000, 500),
    (3_600, 600),
]
OFF_RAMP_FRACTION = 0.15   # fraction of mainline traffic taking the off-ramp

# ---------------------------------------------------------------------------
# Detector groups: (csv_prefix, [loop_ids])
# Harmonic-mean speed and summed flow are reported per group.
# ---------------------------------------------------------------------------
_DETECTOR_GROUPS = [
    # --- weaving buffer: all 4 lanes ---
    ("seg0after_entry_all", [
        "flow_loop_seg_0_after_0_entry",
        "flow_loop_seg_0_after_1_entry",
        "flow_loop_seg_0_after_2_entry",
        "flow_loop_seg_0_after_3_entry",
    ]),
    # --- weaving buffer: lane 0 only (ramp weaving lane) ---
    ("seg0after_entry_lane0", [
        "flow_loop_seg_0_after_0_entry",
    ]),
    # --- weaving buffer: lanes 1–3 (mainline through-traffic) ---
    ("seg0after_entry_mainline", [
        "flow_loop_seg_0_after_1_entry",
        "flow_loop_seg_0_after_2_entry",
        "flow_loop_seg_0_after_3_entry",
    ]),
    ("seg0after_exit_all", [
        "flow_loop_seg_0_after_0_exit",
        "flow_loop_seg_0_after_1_exit",
        "flow_loop_seg_0_after_2_exit",
        "flow_loop_seg_0_after_3_exit",
    ]),
    # --- upstream ---
    ("seg0before_exit", [
        "flow_loop_seg_0_before_0_exit",
        "flow_loop_seg_0_before_1_exit",
        "flow_loop_seg_0_before_2_exit",
    ]),
    # --- ramp-on merge ---
    ("ramp_on_merge_exit", [
        "flow_loop_ramp_on_merge_0_exit",
    ]),
    # --- ramp-off diverge ---
    ("ramp_off_diverge_entry", [
        "flow_loop_ramp_off_diverge_0_entry",
    ]),
]

# ---------------------------------------------------------------------------
# Vehicle types (simplified 2-class fleet)
# ---------------------------------------------------------------------------
_VTYPES_XML = """
    <vType id="car"   length="4.5"  accel="2.6" decel="4.5" sigma="0.5"
           maxSpeed="36.11" minGap="2.5" tau="1.2" color="1,1,0"/>
    <vType id="truck" length="7.5"  accel="1.8" decel="3.8" sigma="0.4"
           maxSpeed="28.0"  minGap="3.5" tau="1.5" color="0.5,0.5,0.5"
           vClass="truck"/>
"""

TRUCK_FRACTION = 0.15   # fraction of trucks in each flow

# Route edge sequences
_MAINLINE_EDGES   = "seg_2_before seg_1_before seg_0_before seg_0_after seg_1_after"
_RAMP_ON_EDGES    = "ramp_on_approach ramp_on_transition ramp_on_merge seg_0_after seg_1_after"
_RAMP_OFF_EDGES   = ("seg_2_before seg_1_before seg_0_before seg_0_after "
                     "ramp_off_diverge ramp_off_transition ramp_off_departure")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _Window(NamedTuple):
    t_start: float
    t_end: float
    groups: Dict[str, Tuple[float, float]]   # prefix → (flow_veh, speed_mps)
    breakdown: int


def _harmonic_mean_speed(speeds: List[float], flows: List[float]) -> float:
    """Flow-weighted harmonic mean (space-mean speed estimator). Returns NaN if no data."""
    total_flow = sum(flows)
    if total_flow <= 0:
        return float("nan")
    inv_sum = 0.0
    for s, f in zip(speeds, flows):
        if s <= 0.0:
            return float("nan")
        inv_sum += f / s
    return total_flow / inv_sum if inv_sum > 0 else float("nan")


def _build_route_file(main_veh_h: int, ramp_on_veh_h: int, duration_s: int) -> str:
    """Write a temporary SUMO route file and return its path."""
    ramp_off_veh_h = int(round(main_veh_h * OFF_RAMP_FRACTION))
    # Mainline (through) = total mainline minus those taking off-ramp
    through_veh_h  = main_veh_h - ramp_off_veh_h

    def _split(total):
        cars   = int(round(total * (1.0 - TRUCK_FRACTION)))
        trucks = total - cars
        return cars, trucks

    car_thru,  truck_thru  = _split(through_veh_h)
    car_ron,   truck_ron   = _split(ramp_on_veh_h)
    car_roff,  truck_roff  = _split(ramp_off_veh_h)

    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd">
{_VTYPES_XML}
    <!-- Mainline through-traffic (stays on mainline; does NOT take off-ramp) -->
    <route id="mainline" edges="{_MAINLINE_EDGES}"/>
    <!-- On-ramp vehicles -->
    <route id="ramp_on"  edges="{_RAMP_ON_EDGES}"/>
    <!-- Off-ramp vehicles (enter at seg_2_before, exit at ramp_off_departure) -->
    <route id="ramp_off" edges="{_RAMP_OFF_EDGES}"/>

    <!-- Mainline through-traffic -->
    <flow id="fmc" type="car"   route="mainline" begin="0" end="{duration_s}"
          vehsPerHour="{car_thru}"  departLane="best" departSpeed="desired" insertionChecks="none"/>
    <flow id="fmt" type="truck" route="mainline" begin="0" end="{duration_s}"
          vehsPerHour="{truck_thru}" departLane="best" departSpeed="desired" insertionChecks="none"/>

    <!-- On-ramp traffic -->
    <flow id="frc" type="car"   route="ramp_on"  begin="0" end="{duration_s}"
          vehsPerHour="{car_ron}"   departLane="best" departSpeed="desired" insertionChecks="none"/>
    <flow id="frt" type="truck" route="ramp_on"  begin="0" end="{duration_s}"
          vehsPerHour="{truck_ron}"  departLane="best" departSpeed="desired" insertionChecks="none"/>

    <!-- Off-ramp traffic ({int(OFF_RAMP_FRACTION*100)}% of mainline) -->
    <flow id="foc" type="car"   route="ramp_off" begin="0" end="{duration_s}"
          vehsPerHour="{car_roff}"  departLane="best" departSpeed="desired" insertionChecks="none"/>
    <flow id="fot" type="truck" route="ramp_off" begin="0" end="{duration_s}"
          vehsPerHour="{truck_roff}" departLane="best" departSpeed="desired" insertionChecks="none"/>
</routes>
"""
    fd, path = tempfile.mkstemp(suffix=".rou.xml", prefix="baseline_")
    with os.fdopen(fd, "w") as f:
        f.write(content)
    return path


def _build_sumocfg(net_file: str, rou_file: str, add_file: str,
                   step_length: float, seed: int) -> str:
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
    ramp_on_veh_h: int,
    seed: int,
    use_gui: bool,
) -> List[_Window]:
    """Run one SUMO scenario and return per-window measurements."""
    import traci  # type: ignore

    rou_file = _build_route_file(main_veh_h, ramp_on_veh_h, SIM_DURATION_S)
    cfg_file = _build_sumocfg(str(_NET_FILE), rou_file, str(_ADD_FILE), SIM_STEP_S, seed)

    sumo_bin = "sumo-gui" if use_gui else _SUMO_BIN
    traci.start([sumo_bin, "-c", cfg_file])

    windows: List[_Window] = []
    step = 0
    steps_per_window = int(AGG_WINDOW_S / SIM_STEP_S)
    total_steps      = int(SIM_DURATION_S / SIM_STEP_S)
    warmup_steps     = int(WARMUP_S / SIM_STEP_S)

    try:
        while step < total_steps:
            for _ in range(steps_per_window):
                traci.simulationStep()
                step += 1

            t_end   = step * SIM_STEP_S
            t_start = t_end - AGG_WINDOW_S

            if step <= warmup_steps:
                continue

            # Read detector data
            groups: Dict[str, Tuple[float, float]] = {}
            for prefix, loop_ids in _DETECTOR_GROUPS:
                speeds, flows = [], []
                for lid in loop_ids:
                    spd = traci.inductionloop.getLastIntervalMeanSpeed(lid)
                    n   = traci.inductionloop.getLastIntervalVehicleNumber(lid)
                    if n > 0 and spd > 0:
                        speeds.append(spd)
                        flows.append(float(n))
                total_flow = sum(flows)
                hmean = _harmonic_mean_speed(speeds, flows) if flows else float("nan")
                groups[prefix] = (total_flow, hmean)

            # Breakdown: speed across ALL 4 seg_0_after entry lanes < threshold
            entry_flow, entry_speed = groups.get("seg0after_entry_all", (0.0, float("nan")))
            breakdown = int(
                not math.isnan(entry_speed)
                and entry_flow >= BREAKDOWN_MIN_FLOW
                and entry_speed < BREAKDOWN_SPEED_MPS
            )
            windows.append(_Window(t_start=t_start, t_end=t_end,
                                   groups=groups, breakdown=breakdown))

    finally:
        traci.close()
        os.unlink(rou_file)
        os.unlink(cfg_file)

    return windows


def _write_csv(windows: List[_Window], path: Path) -> None:
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
                row[f"speed_{prefix}_mps"]   = (
                    f"{speed:.3f}" if not math.isnan(speed) else "nan"
                )
            writer.writerow(row)


def _scenario_summary(main_veh_h: int, ramp_on_veh_h: int,
                      windows: List[_Window]) -> Dict:
    entry_speeds = [
        w.groups["seg0after_entry_all"][1]
        for w in windows
        if not math.isnan(w.groups.get("seg0after_entry_all", (0, float("nan")))[1])
    ]
    total_thru = sum(
        w.groups.get("seg0after_exit_all", (0.0, float("nan")))[0]
        for w in windows
    )
    bd_windows = [w for w in windows if w.breakdown]
    bd_occurred = 1 if bd_windows else 0
    bd_time = bd_windows[0].t_start if bd_windows else float("nan")

    return {
        "main_veh_h":       main_veh_h,
        "ramp_on_veh_h":    ramp_on_veh_h,
        "ramp_off_frac":    OFF_RAMP_FRACTION,
        "breakdown_occurred": bd_occurred,
        "breakdown_time_s": f"{bd_time:.0f}" if not math.isnan(bd_time) else "nan",
        "mean_speed_seg0after_entry_mps": (
            f"{sum(entry_speeds)/len(entry_speeds):.3f}" if entry_speeds else "nan"
        ),
        "min_speed_seg0after_entry_mps": (
            f"{min(entry_speeds):.3f}" if entry_speeds else "nan"
        ),
        "total_throughput_veh": f"{total_thru:.0f}",
    }


def _plot_scenario(main_veh_h: int, ramp_on_veh_h: int,
                   windows: List[_Window]) -> None:
    try:
        import matplotlib.pyplot as plt  # type: ignore
    except ImportError:
        return

    t_mid = [(w.t_start + w.t_end) / 2.0 for w in windows]

    fig, axes = plt.subplots(2, 1, figsize=(13, 6), sharex=True)

    ax = axes[0]
    for prefix, _ in _DETECTOR_GROUPS:
        speeds_kph = [
            w.groups.get(prefix, (0, float("nan")))[1] * 3.6
            if not math.isnan(w.groups.get(prefix, (0, float("nan")))[1])
            else float("nan")
            for w in windows
        ]
        ax.plot(t_mid, speeds_kph, label=prefix, linewidth=1.2)

    ax.axhline(60.0, color="red", linestyle="--", linewidth=1.0, label="Breakdown (60 kph)")
    ax.axvline(WARMUP_S, color="grey", linestyle=":", linewidth=0.8, label="Warmup end")
    ax.set_ylabel("Speed (km/h)")
    ax.set_title(
        f"No-control baseline: mainline={main_veh_h} veh/h  "
        f"ramp-on={ramp_on_veh_h} veh/h  "
        f"ramp-off={int(main_veh_h * OFF_RAMP_FRACTION)} veh/h"
    )
    ax.legend(fontsize=7, ncol=2)
    ax.set_ylim(0, 150)

    ax2 = axes[1]
    for prefix, _ in _DETECTOR_GROUPS:
        flows = [w.groups.get(prefix, (float("nan"), 0))[0] for w in windows]
        ax2.plot(t_mid, flows, label=prefix, linewidth=1.2)
    ax2.set_xlabel("Simulation time (s)")
    ax2.set_ylabel("Flow (veh / 30 s)")
    ax2.legend(fontsize=7, ncol=2)

    fig.tight_layout()
    label = f"{main_veh_h}_{ramp_on_veh_h}"
    plot_path = _RESULTS_DIR / f"baseline_{label}.png"
    fig.savefig(plot_path, dpi=150)
    plt.close(fig)
    print(f"  Plot → {plot_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="No-control baseline diagnostic for ramps_v0 (on-ramp + off-ramp)."
    )
    parser.add_argument("--gui", action="store_true",
                        help="Use sumo-gui (interactive, slow).")
    parser.add_argument("--seed", type=int, default=42,
                        help="SUMO random seed (default: 42).")
    parser.add_argument("--scenarios", type=str, default=None,
                        help="Comma-separated scenario indices 0–4. Default: all.")
    parser.add_argument("--no-plot", dest="plot", action="store_false", default=True,
                        help="Skip matplotlib plots.")
    args = parser.parse_args()

    if not _NET_FILE.exists():
        print(
            f"ERROR: {_NET_FILE} not found.\n"
            "Run traffic_environment/sumo/generate_ramp_network.py first,\n"
            "then open in netedit → Processing → Compute Junctions.",
            file=sys.stderr,
        )
        return 1
    if not _ADD_FILE.exists():
        print(f"ERROR: {_ADD_FILE} not found.", file=sys.stderr)
        return 1

    if args.scenarios:
        indices   = [int(x.strip()) for x in args.scenarios.split(",")]
        scenarios = [SCENARIOS[i] for i in indices]
    else:
        scenarios = list(SCENARIOS)

    _RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    summaries = []

    for main_veh_h, ramp_on_veh_h in scenarios:
        ramp_off_veh_h = int(round(main_veh_h * OFF_RAMP_FRACTION))
        label = f"{main_veh_h}_{ramp_on_veh_h}"
        print(
            f"\n{'='*65}\n"
            f"Scenario: mainline={main_veh_h}  ramp-on={ramp_on_veh_h}  "
            f"ramp-off={ramp_off_veh_h}  (veh/h)\n"
            f"{'='*65}"
        )

        windows  = _run_scenario(main_veh_h, ramp_on_veh_h, args.seed, args.gui)

        csv_path = _RESULTS_DIR / f"baseline_{label}.csv"
        _write_csv(windows, csv_path)
        print(f"  Per-window data → {csv_path}")

        summary = _scenario_summary(main_veh_h, ramp_on_veh_h, windows)
        summaries.append(summary)

        bd = "YES" if summary["breakdown_occurred"] else "NO"
        print(f"  Breakdown: {bd}"
              + (f"  at t={summary['breakdown_time_s']} s" if bd == "YES" else ""))
        print(f"  Mean speed @ seg_0_after entry (all lanes): "
              f"{summary['mean_speed_seg0after_entry_mps']} m/s")
        print(f"  Min  speed @ seg_0_after entry (all lanes): "
              f"{summary['min_speed_seg0after_entry_mps']} m/s")
        print(f"  Total throughput (seg_0_after exit): "
              f"{summary['total_throughput_veh']} veh")

        if args.plot:
            _plot_scenario(main_veh_h, ramp_on_veh_h, windows)

    summary_path = _RESULTS_DIR / "baseline_summary.csv"
    with open(summary_path, "w", newline="") as f:
        if summaries:
            writer = csv.DictWriter(f, fieldnames=list(summaries[0].keys()))
            writer.writeheader()
            writer.writerows(summaries)
    print(f"\nSummary → {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
