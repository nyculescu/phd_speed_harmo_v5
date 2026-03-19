#!/usr/bin/env python3
"""
generate_ramp_network_v2.py
============================
SUMO raw-network generator for the **ramps_v2** topology.

Key change from v1: NO dedicated ramp lane, NO off-ramp.
Ramp vehicles merge directly onto mainline lane 0 (rightmost),
forcing weaving conflict with mainline traffic.

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
from xml.dom import minidom
import argparse
import os

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
    root = ET.Element("net")
    root.set("version", "1.21.0")
    root.set("junctionCornerDetail", "5")
    root.set("limitTurnSpeed", "5.50")
    root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    root.set("xsi:noNamespaceSchemaLocation", "http://sumo.dlr.de/xsd/net_file.xsd")

    loc = ET.SubElement(root, "location")
    loc.set("netOffset", "0.00,0.00")
    loc.set("convBoundary", "-4000.00,0.00,3000.00,100.00")
    loc.set("origBoundary", "-10000000000.00,-10000000000.00,10000000000.00,10000000000.00")
    loc.set("projParameter", "!")

    # --- Junctions (mainline) ---
    junctions = {}
    current_x = -3000.0

    for i in range(len(MAIN_SEGMENTS) + 1):
        j_id = f"J{i}"
        junctions[j_id] = {"x": current_x, "y": Y_BASE, "id": j_id, "type": "priority"}
        if i < len(MAIN_SEGMENTS):
            seg = MAIN_SEGMENTS[i]
            current_x += SEGMENT_LENGTHS[seg] * SHAPE_MULTIPLIERS[seg]

    merge_jid = "J4"  # end of seg_0_before / start of seg_0_after

    # Ramp Y
    ramp_start_y = Y_BASE + RAMP_Y_OFFSET
    main_road_y = Y_BASE + _lane_y_offset(0)  # lane 0 = rightmost

    # --- On-ramp junctions ---
    on_total = (SEGMENT_LENGTHS["ramp_on_approach"]
                + SEGMENT_LENGTHS["ramp_on_transition"]
                + SEGMENT_LENGTHS["ramp_on_merge"])

    on_start_id = "J_ramp_on_start"
    on_mid1_id = "J_ramp_on_mid1"
    on_mid2_id = "J_ramp_on_mid2"

    # Y interpolation: smooth approach from ramp_start_y to main_road_y
    approach_frac = SEGMENT_LENGTHS["ramp_on_approach"] / on_total
    transition_frac = (SEGMENT_LENGTHS["ramp_on_approach"]
                       + SEGMENT_LENGTHS["ramp_on_transition"]) / on_total

    on_mid1_y = ramp_start_y + (main_road_y - ramp_start_y) * approach_frac * RAMP_PROXIMITY_FACTOR
    on_mid2_y = ramp_start_y + (main_road_y - ramp_start_y) * transition_frac * RAMP_PROXIMITY_FACTOR

    junctions[on_start_id] = {
        "x": junctions[merge_jid]["x"] - on_total,
        "y": ramp_start_y,
        "id": on_start_id, "type": "dead_end",
    }
    junctions[on_mid1_id] = {
        "x": junctions[merge_jid]["x"] - SEGMENT_LENGTHS["ramp_on_transition"] - SEGMENT_LENGTHS["ramp_on_merge"],
        "y": on_mid1_y,
        "id": on_mid1_id, "type": "priority",
    }
    junctions[on_mid2_id] = {
        "x": junctions[merge_jid]["x"] - SEGMENT_LENGTHS["ramp_on_merge"],
        "y": on_mid2_y,
        "id": on_mid2_id, "type": "priority",
    }

    # --- Write junction elements ---
    for jd in junctions.values():
        j = ET.SubElement(root, "junction")
        j.set("id", jd["id"])
        j.set("type", jd["type"])
        j.set("x", f"{jd['x']:.2f}")
        j.set("y", f"{jd['y']:.2f}")
        j.set("incLanes", "")
        j.set("intLanes", "")
        j.set("shape", "")

    # --- Main road edges (3 lanes everywhere) ---
    for i, seg in enumerate(MAIN_SEGMENTS):
        edge = ET.SubElement(root, "edge")
        edge.set("id", seg)
        edge.set("from", f"J{i}")
        edge.set("to", f"J{i+1}")
        edge.set("priority", "-1")
        edge.set("length", str(SEGMENT_LENGTHS[seg]))

        j_from = junctions[f"J{i}"]
        j_to = junctions[f"J{i+1}"]

        for lane_idx in range(N_LANES):
            lane = ET.SubElement(edge, "lane")
            lane.set("id", f"{seg}_{lane_idx}")
            lane.set("index", str(lane_idx))
            lane.set("speed", f"{MAINLINE_SPEED:.2f}")
            lane.set("length", str(SEGMENT_LENGTHS[seg]))
            y_off = _lane_y_offset(lane_idx)
            lane.set("shape", f"{j_from['x']:.2f},{j_from['y'] + y_off:.2f} "
                              f"{j_to['x']:.2f},{j_to['y'] + y_off:.2f}")

    # --- On-ramp edges (3 segments) ---
    ramp_edges = [
        ("ramp_on_approach",   on_start_id, on_mid1_id),
        ("ramp_on_transition", on_mid1_id,  on_mid2_id),
        ("ramp_on_merge",      on_mid2_id,  merge_jid),
    ]
    for seg_id, from_id, to_id in ramp_edges:
        edge = ET.SubElement(root, "edge")
        edge.set("id", seg_id)
        edge.set("from", from_id)
        edge.set("to", to_id)
        edge.set("priority", "-1")
        edge.set("length", str(SEGMENT_LENGTHS[seg_id]))

        lane = ET.SubElement(edge, "lane")
        lane.set("id", f"{seg_id}_0")
        lane.set("index", "0")
        lane.set("speed", str(RAMP_SPEED))
        lane.set("length", str(SEGMENT_LENGTHS[seg_id]))

        f = junctions[from_id]
        t = junctions[to_id]
        end_y = main_road_y if seg_id == "ramp_on_merge" else t["y"]
        lane.set("shape", f"{f['x']:.2f},{f['y']:.2f} {t['x']:.2f},{end_y:.2f}")

    # --- Connections: mainline (straight through, same lane count) ---
    for i in range(len(MAIN_SEGMENTS) - 1):
        from_edge = MAIN_SEGMENTS[i]
        to_edge = MAIN_SEGMENTS[i + 1]
        for k in range(N_LANES):
            c = ET.SubElement(root, "connection")
            c.set("from", from_edge); c.set("to", to_edge)
            c.set("fromLane", str(k)); c.set("toLane", str(k))
            c.set("dir", "s"); c.set("state", "M")

    # --- Connections: on-ramp chain ---
    for from_e, to_e in [
        ("ramp_on_approach", "ramp_on_transition"),
        ("ramp_on_transition", "ramp_on_merge"),
    ]:
        c = ET.SubElement(root, "connection")
        c.set("from", from_e); c.set("to", to_e)
        c.set("fromLane", "0"); c.set("toLane", "0")
        c.set("dir", "s"); c.set("state", "M")

    # On-ramp merge → seg_0_after lane 0 (YIELD — creates weaving conflict)
    c = ET.SubElement(root, "connection")
    c.set("from", "ramp_on_merge"); c.set("to", "seg_0_after")
    c.set("fromLane", "0"); c.set("toLane", "0")
    c.set("dir", "s"); c.set("state", "m")

    return root


def prettify_xml(elem):
    rough = ET.tostring(elem, encoding="unicode")
    reparsed = minidom.parseString(rough)
    return reparsed.toprettyxml(indent="    ", encoding="UTF-8")


def main():
    parser = argparse.ArgumentParser(description="Generate ramps_v2.net.xml")
    parser.add_argument("-o", "--output", default="ramps_v2.net.xml")
    args = parser.parse_args()

    root = create_network()
    output_path = os.path.join(os.path.dirname(__file__), args.output)
    with open(output_path, "wb") as f:
        f.write(prettify_xml(root))

    print(f"Network saved to: {args.output}")
    print(f"\nTopology: 3L mainline (4 × 1000m) → 3L merge zone (500m) → 3L downstream (1000m)")
    print(f"On-ramp: 1000m (700 approach + 200 transition + 100 merge) → lane 0 (yield)")
    print(f"No off-ramp.  All vehicles exit via seg_1_after.")
    print(f"Total mainline: ~5.5 km")
    print(f"\nOpen in netedit → Processing → Compute Junctions")


if __name__ == "__main__":
    exit(main())
