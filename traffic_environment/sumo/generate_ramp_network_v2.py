#!/usr/bin/env python3
"""
generate_ramp_network_v2.py
============================
SUMO raw-network generator for the **ramps_v2** topology.

Key change from v1: NO dedicated ramp lane, NO off-ramp.
Ramp vehicles merge directly onto mainline lane 0 (rightmost),
forcing weaving conflict with mainline traffic.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WHY 3→3 (NO LANE ADDITION) INSTEAD OF 3→4→3 (DEDICATED RAMP LANE)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The v1 topology used a 4-lane buffer zone (seg_0_after) where lane 0
was a dedicated ramp weaving lane with an off-ramp escape valve at
the downstream end.  A 990-scenario feasibility sweep + per-lane
diagnostic (tests/results/lane_diagnostic/) proved that:

  1. The dedicated lane ISOLATED ramp traffic from mainline.  Ramp
     vehicles merged onto their own lane and either lane-changed into
     lanes 1-3 or exited via the off-ramp — with zero impact on
     mainline flow.

  2. The actual bottleneck was mainline lane 1 saturation (20-30 vehs)
     caused by uneven lane distribution, not merge conflict.  VSL had
     no mechanism to address this.

  3. At every demand level, VSL either did nothing useful (below 6000
     vph) or collapsed throughput without improving harmonization
     (above 6500 vph).  Zero scenarios showed VSL benefit.

The 3→3 design (ramps_v2) forces ramp vehicles to compete for lane 0
with mainline traffic, creating the merge-induced shockwaves that
VSL-based speed harmonization is designed to mitigate.  This matches:

  - Li et al. (2017): QL-VSL at a recurrent merge bottleneck on I-880
    where ramp flow directly disrupts mainline (no dedicated lane).
  - Hua & Fan (2023): DDPG-DSH in a weaving area where ramp vehicles
    interact with mainline on shared lanes (SUMO, PeMS-calibrated).
  - Ko et al. (2020): CAV speed harmonization at a lane closure where
    merging directly disrupts the mainline flow.

The 3→4→3 alternative (with a 4th lane added at merge and dropped
downstream) would be appropriate for studying auxiliary-lane design,
but it does not produce the merge shockwaves that are the target of
this research.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOPOLOGY OVERVIEW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  upstream (3L)                                    merge (3L)     downstream (3L)
  ──────────────────────────────────────────────┬──────────────┬─────────────
  seg_3_before  seg_2_before  seg_1_before  seg_0_before │ seg_0_after │ seg_1_after
  J0──────────J1──────────J2──────────J3──────────J4──────────J5──────────J6
  1000m        1000m        1000m        1000m       500m         1000m

  On-ramp (below mainline, 1000 m total):
    ramp_on_approach (700 m) → ramp_on_transition (200 m)
    → ramp_on_merge (100 m) ──► J4 / seg_0_after LANE 0  (yield)

  NO off-ramp.  All vehicles exit via seg_1_after.

  Merge zone: 500 m (seg_0_after).  3 lanes everywhere — ramp
  vehicles share lane 0 with mainline, creating weaving conflict.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LANE NUMBERING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Lane 0   = rightmost (merge target for ramp vehicles)
  Lane 2   = leftmost  (fast / overtaking lane)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONNECTIONS AT J4 (merge)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  seg_0_before lane k  →  seg_0_after lane k   (k = 0, 1, 2)
  ramp_on_merge lane 0 →  seg_0_after lane 0   (yield / lowercase 'm')

  This creates a CONFLICT: both seg_0_before lane 0 and the ramp
  feed into seg_0_after lane 0.  SUMO resolves this via the yield
  priority (ramp must wait for acceptable gap).
"""

import xml.etree.ElementTree as ET
import argparse
import os
import sys

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

RAMP_Y_OFFSET = -20.0
RAMP_SPEED = 25.0          # 90 kph
RAMP_PROXIMITY_FACTOR = 0.7

SEGMENT_LENGTHS = {
    "seg_3_before": 1000.0,
    "seg_2_before": 1000.0,
    "seg_1_before": 1000.0,
    "seg_0_before": 1000.0,
    "seg_0_after":   500.0,     # merge/weaving zone
    "seg_1_after":  1000.0,
    # On-ramp (1000 m total)
    "ramp_on_approach":   700.0,
    "ramp_on_transition": 200.0,
    "ramp_on_merge":      100.0,
}

SHAPE_MULTIPLIERS = {
    "seg_3_before": 0.5,
    "seg_2_before": 0.5,
    "seg_1_before": 0.5,
    "seg_0_before": 1.0,
    "seg_0_after":  1.0,
    "seg_1_after":  0.5,
    "ramp_on_approach":   1.0,
    "ramp_on_transition": 1.0,
    "ramp_on_merge":      1.0,
}

MAIN_SEGMENTS = [
    "seg_3_before", "seg_2_before", "seg_1_before", "seg_0_before",
    "seg_0_after", "seg_1_after",
]

MAINLINE_SPEED = 33.33  # 120 kph in m/s
LANE_WIDTH = 3.2
N_LANES = 3             # 3 lanes everywhere — no lane addition
Y_BASE = 60.0


# ---------------------------------------------------------------------------
# Network builder
# ---------------------------------------------------------------------------

def _lane_y_offset(lane_idx: int) -> float:
    return (lane_idx - (N_LANES - 1) / 2) * LANE_WIDTH


def create_network():
    """Generate ramps_v2 via plain XML files + netconvert."""
    import subprocess
    import tempfile

    ramp_start_y = Y_BASE + RAMP_Y_OFFSET
    lane_0_y = Y_BASE + _lane_y_offset(0)  # rightmost lane Y

    # --- Compute junction positions ---
    junctions = {}
    current_x = -3000.0
    for i in range(len(MAIN_SEGMENTS) + 1):
        junctions[f"J{i}"] = (current_x, Y_BASE)
        if i < len(MAIN_SEGMENTS):
            current_x += SEGMENT_LENGTHS[MAIN_SEGMENTS[i]] * SHAPE_MULTIPLIERS[MAIN_SEGMENTS[i]]

    merge_x = junctions["J4"][0]

    on_total = (SEGMENT_LENGTHS["ramp_on_approach"]
                + SEGMENT_LENGTHS["ramp_on_transition"]
                + SEGMENT_LENGTHS["ramp_on_merge"])

    # Ramp waypoints — approach lane 0 (Y=56.8), not junction center (Y=60).
    # on_mid2 (start of ramp_on_merge) is placed at lane_0_y so that
    # the 100m merge segment runs parallel to lane 0 before joining it.
    approach_frac = SEGMENT_LENGTHS["ramp_on_approach"] / on_total

    on_mid1_y = ramp_start_y + (lane_0_y - ramp_start_y) * approach_frac * RAMP_PROXIMITY_FACTOR
    # netconvert centers the 3-lane edge on the node Y, placing lane 0
    # at node_y - LANE_WIDTH.  For the 1-lane ramp, the lane IS at node Y.
    # So the ramp must target node_y - LANE_WIDTH = lane_0 absolute Y.
    on_mid2_y = lane_0_y - LANE_WIDTH

    ramp_junctions = {
        "J_ramp_on_start": (merge_x - on_total, ramp_start_y),
        "J_ramp_on_mid1":  (merge_x - SEGMENT_LENGTHS["ramp_on_transition"] - SEGMENT_LENGTHS["ramp_on_merge"], on_mid1_y),
        "J_ramp_on_mid2":  (merge_x - SEGMENT_LENGTHS["ramp_on_merge"], on_mid2_y),
    }

    # --- Write .nod.xml (nodes/junctions) ---
    nod = ET.Element("nodes")
    all_junctions = {**junctions, **ramp_junctions}
    for jid, (x, y) in all_junctions.items():
        jtype = "dead_end" if jid in ("J0", "J6", "J_ramp_on_start") else "priority"
        n = ET.SubElement(nod, "node")
        n.set("id", jid)
        n.set("x", f"{x:.2f}")
        n.set("y", f"{y:.2f}")
        n.set("type", jtype)

    # --- Write .edg.xml (edges) ---
    edg = ET.Element("edges")
    # Mainline edges
    for i, seg in enumerate(MAIN_SEGMENTS):
        e = ET.SubElement(edg, "edge")
        e.set("id", seg)
        e.set("from", f"J{i}")
        e.set("to", f"J{i+1}")
        e.set("numLanes", str(N_LANES))
        e.set("speed", f"{MAINLINE_SPEED:.2f}")
        e.set("length", str(SEGMENT_LENGTHS[seg]))

    # On-ramp segments — ramp_on_merge gets an explicit shape so its
    # endpoint aligns with lane 0 (Y=lane_0_y), not junction center.
    ramp_edge_defs = [
        ("ramp_on_approach",   "J_ramp_on_start", "J_ramp_on_mid1", None),
        ("ramp_on_transition", "J_ramp_on_mid1",  "J_ramp_on_mid2", None),
        ("ramp_on_merge",      "J_ramp_on_mid2",  "J4",
         f"{ramp_junctions['J_ramp_on_mid2'][0]:.2f},{on_mid2_y:.2f} "
         f"{merge_x:.2f},{on_mid2_y:.2f}"),
    ]
    for seg_id, from_id, to_id, shape in ramp_edge_defs:
        e = ET.SubElement(edg, "edge")
        e.set("id", seg_id)
        e.set("from", from_id)
        e.set("to", to_id)
        e.set("numLanes", "1")
        e.set("speed", str(RAMP_SPEED))
        e.set("length", str(SEGMENT_LENGTHS[seg_id]))
        if shape:
            e.set("shape", shape)

    # --- Write .con.xml (explicit connections) ---
    con = ET.Element("connections")
    # Mainline straight-through
    for i in range(len(MAIN_SEGMENTS) - 1):
        from_edge = MAIN_SEGMENTS[i]
        to_edge = MAIN_SEGMENTS[i + 1]
        for k in range(N_LANES):
            c = ET.SubElement(con, "connection")
            c.set("from", from_edge); c.set("to", to_edge)
            c.set("fromLane", str(k)); c.set("toLane", str(k))
    # On-ramp chain
    for from_e, to_e in [
        ("ramp_on_approach", "ramp_on_transition"),
        ("ramp_on_transition", "ramp_on_merge"),
    ]:
        c = ET.SubElement(con, "connection")
        c.set("from", from_e); c.set("to", to_e)
        c.set("fromLane", "0"); c.set("toLane", "0")
    # Ramp merge → lane 0 (explicit)
    c = ET.SubElement(con, "connection")
    c.set("from", "ramp_on_merge"); c.set("to", "seg_0_after")
    c.set("fromLane", "0"); c.set("toLane", "0")

    # --- Write temp files and run netconvert ---
    tmpdir = tempfile.mkdtemp(prefix="ramps_v2_gen_")
    nod_path = os.path.join(tmpdir, "ramps_v2.nod.xml")
    edg_path = os.path.join(tmpdir, "ramps_v2.edg.xml")
    con_path = os.path.join(tmpdir, "ramps_v2.con.xml")

    for path, elem in [(nod_path, nod), (edg_path, edg), (con_path, con)]:
        tree = ET.ElementTree(elem)
        ET.indent(tree, space="  ")
        tree.write(path, encoding="unicode", xml_declaration=True)

    output_path = os.path.join(os.path.dirname(__file__) or ".", "ramps_v2.net.xml")
    result = subprocess.run([
        "netconvert",
        "--node-files", nod_path,
        "--edge-files", edg_path,
        "--connection-files", con_path,
        "--output-file", output_path,
        "--no-internal-links", "false",
        "--junctions.internal-link-detail", "5",
        "--no-turnarounds", "true",
    ], capture_output=True, text=True)

    import shutil
    shutil.rmtree(tmpdir, ignore_errors=True)

    if result.returncode != 0:
        print(f"netconvert STDERR:\n{result.stderr}", file=sys.stderr)
        raise RuntimeError(f"netconvert failed with code {result.returncode}")

    # Read the generated network back as an Element
    return ET.parse(output_path).getroot()


def main():
    create_network()  # writes ramps_v2.net.xml via netconvert

    print(f"Network saved to: ramps_v2.net.xml")
    print(f"\nTopology: 3L mainline (4 × 1000m) → 3L merge zone (500m) → 3L downstream (1000m)")
    print(f"On-ramp: 1000m (700 approach + 200 transition + 100 merge) → lane 0 (yield)")
    print(f"No off-ramp.  All vehicles exit via seg_1_after.")
    print(f"Total mainline: ~5.5 km")
    print(f"Generated via netconvert with explicit .con.xml — no netedit recompute needed.")


if __name__ == "__main__":
    exit(main())
