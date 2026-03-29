#!/usr/bin/env python3
"""
generate_ramp_network_v2.py
============================
SUMO raw-network generator for the **ramps_v2** topology.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOPOLOGY OVERVIEW — EU-standard merge with acceleration lane
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  upstream (3L)                                    merge (4L)     downstream (3L)
  ──────────────────────────────────────────────┬──────────────┬─────────────
  seg_3_before  seg_2_before  seg_1_before  seg_0_before │ seg_0_after │ seg_1_after
  J0──────────J1──────────J2──────────J3──────────J4──────────J5──────────J6
  1000m        1000m        1000m        1000m       250m         1000m

  On-ramp (below mainline, 1000 m total):
    ramp_on_approach (700 m) → ramp_on_transition (200 m)
    → ramp_on_merge (100 m) ──► J4 / seg_0_after LANE 0 (acceleration lane)

  Merge zone: seg_0_after has 4 LANES (250m):
    Lane 0  = acceleration lane (ramp vehicles merge here)
    Lanes 1-3 = mainline through-lanes (from seg_0_before 0/1/2)

  Lane drop at J5: seg_0_after (4L) → seg_1_after (3L).
    seg_0_after lane 0 has NO forward connection — vehicles must
    lane-change from L0 into L1-3 within the 250m acceleration zone.
    seg_0_after lanes 1/2/3 → seg_1_after lanes 0/1/2.

  This is the standard EU motorway merge design (RAA §5.3.3):
    - Ramp vehicles enter a dedicated acceleration lane
    - They have 200-250m to match mainline speed and find a gap
    - The acceleration lane tapers/drops, forcing the merge
    - Mainline traffic is NOT directly disrupted at the merge point
    - Disruption occurs when ramp vehicles lane-change into the
      through lanes — THIS is the shockwave source that VSL mitigates

  NO off-ramp. All vehicles exit via seg_1_after.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LANE NUMBERING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Upstream / downstream (3 lanes):
    Lane 0 = rightmost,  Lane 2 = leftmost (fast)

  Merge zone seg_0_after (4 lanes):
    Lane 0 = acceleration lane (ramp entry, no forward connection)
    Lane 1 = rightmost through-lane (← from seg_0_before L0)
    Lane 2 = middle through-lane   (← from seg_0_before L1)
    Lane 3 = leftmost through-lane (← from seg_0_before L2)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONNECTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  J4 (3L → 4L + ramp):
    seg_0_before:0 → seg_0_after:1
    seg_0_before:1 → seg_0_after:2
    seg_0_before:2 → seg_0_after:3
    ramp_on_merge:0 → seg_0_after:0  (acceleration lane)

  J5 (4L → 3L, lane drop):
    seg_0_after:1 → seg_1_after:0
    seg_0_after:2 → seg_1_after:1
    seg_0_after:3 → seg_1_after:2
    (seg_0_after:0 has NO forward connection — forces lane-change)
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
    "seg_0_after":   250.0,     # acceleration/merge zone (4 lanes)
    "seg_1_after":  1000.0,
    # On-ramp (1000 m total)
    "ramp_on_approach":   700.0,
    "ramp_on_transition": 200.0,
    "ramp_on_merge":      100.0,
}

# Lane counts per segment
LANE_COUNTS = {
    "seg_3_before": 3,
    "seg_2_before": 3,
    "seg_1_before": 3,
    "seg_0_before": 3,
    "seg_0_after":  4,   # 3 through + 1 acceleration lane (L0)
    "seg_1_after":  3,
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
Y_BASE = 60.0


# ---------------------------------------------------------------------------
# Network builder
# ---------------------------------------------------------------------------

def _lane_y_offset(lane_idx: int, n_lanes: int = 3) -> float:
    return (lane_idx - (n_lanes - 1) / 2) * LANE_WIDTH


def create_network():
    """Generate ramps_v2 via plain XML files + netconvert."""
    import subprocess
    import tempfile

    ramp_start_y = Y_BASE + RAMP_Y_OFFSET
    # Ramp targets the rightmost lane of the 4-lane merge zone (lane 0)
    lane_0_y_4L = Y_BASE + _lane_y_offset(0, n_lanes=4)

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

    # The ramp approaches from below and must end at the Y-level of
    # seg_0_after lane 0 (the acceleration lane). We generate the network
    # in two passes: first without the ramp to find the actual lane 0 Y,
    # then with the ramp positioned correctly.
    #
    # For the first pass (or when we know the offset), the acceleration
    # lane sits at approximately:
    #   node_Y - (n_lanes - 1) / 2 * LANE_WIDTH - LANE_WIDTH / 2
    # For 4 lanes: node_Y - 1.5 * LW - LW/2 = node_Y - 2 * LW
    # But we also need to account for SUMO's edge-to-node offset.
    #
    # Empirically from netconvert output: with Y_BASE=60, J4→Y=20,
    # lane 0 center → Y=8.8.  Offset from J4: 20 - 8.8 = 11.2
    # = (4-1)/2 * 3.2 + 3.2/2 = 4.8 + 1.6 = 6.4... not matching.
    # Actually: 4 lanes → edges span 4*3.2=12.8, centered on node.
    # Lane 0 center = node_y - 12.8/2 + 3.2/2 = node_y - 6.4 + 1.6 = node_y - 4.8
    # But 20 - 4.8 = 15.2, not 8.8. netconvert adds extra offset for
    # the junction shape.
    #
    # Simplest fix: place J_ramp_on_mid2 well below J4, and let
    # netconvert's internal edge handle the curve up to lane 0.
    # The ramp_on_merge just needs to approach from below.
    ramp_target_y = Y_BASE - 3.5 * LANE_WIDTH  # well below the 4-lane edge

    approach_frac = SEGMENT_LENGTHS["ramp_on_approach"] / on_total
    on_mid1_y = ramp_start_y + (ramp_target_y - ramp_start_y) * approach_frac * RAMP_PROXIMITY_FACTOR
    on_mid2_y = ramp_target_y

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
        e.set("numLanes", str(LANE_COUNTS.get(seg, 3)))
        e.set("speed", f"{MAINLINE_SPEED:.2f}")
        e.set("length", str(SEGMENT_LENGTHS[seg]))

    # On-ramp segments — ramp_on_merge gets an explicit shape so its
    # endpoint aligns with lane 0 (Y=lane_0_y), not junction center.
    ramp_edge_defs = [
        ("ramp_on_approach",   "J_ramp_on_start", "J_ramp_on_mid1", None),
        ("ramp_on_transition", "J_ramp_on_mid1",  "J_ramp_on_mid2", None),
        ("ramp_on_merge",      "J_ramp_on_mid2",  "J4",             None),
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

    # Mainline straight-through (except at lane-change junctions)
    for i in range(len(MAIN_SEGMENTS) - 1):
        from_edge = MAIN_SEGMENTS[i]
        to_edge = MAIN_SEGMENTS[i + 1]
        from_lanes = LANE_COUNTS.get(from_edge, 3)
        to_lanes = LANE_COUNTS.get(to_edge, 3)

        if from_edge == "seg_0_before" and to_edge == "seg_0_after":
            # 3L → 4L: mainline lanes shift up by 1 (accel lane is L0)
            # seg_0_before:0 → seg_0_after:1
            # seg_0_before:1 → seg_0_after:2
            # seg_0_before:2 → seg_0_after:3
            for k in range(from_lanes):
                c = ET.SubElement(con, "connection")
                c.set("from", from_edge); c.set("to", to_edge)
                c.set("fromLane", str(k)); c.set("toLane", str(k + 1))
        elif from_edge == "seg_0_after" and to_edge == "seg_1_after":
            # 4L → 3L: lane 0 (accel) has NO forward connection (forces merge)
            # seg_0_after:1 → seg_1_after:0
            # seg_0_after:2 → seg_1_after:1
            # seg_0_after:3 → seg_1_after:2
            for k in range(to_lanes):
                c = ET.SubElement(con, "connection")
                c.set("from", from_edge); c.set("to", to_edge)
                c.set("fromLane", str(k + 1)); c.set("toLane", str(k))
        else:
            # Normal same-lane-count connection
            for k in range(min(from_lanes, to_lanes)):
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

    # Ramp merge → acceleration lane (lane 0 of 4-lane seg_0_after)
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
    print(f"\nTopology: 3L upstream (4×1000m) → 4L accel zone (250m) → 3L downstream (1000m)")
    print(f"On-ramp: 1000m (700 approach + 200 transition + 100 merge) → accel lane (L0)")
    print(f"Accel lane (L0) has NO forward connection → forces lane-change within 250m")
    print(f"No off-ramp.  All vehicles exit via seg_1_after.")
    print(f"Generated via netconvert with explicit .con.xml — no netedit recompute needed.")


if __name__ == "__main__":
    exit(main())
