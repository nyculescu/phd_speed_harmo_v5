#!/usr/bin/env python3
"""
generate_ramp_network_v1.py
============================
SUMO raw-network generator for the **ramps_v1** topology.

Compact ramp-on + ramp-off network designed to produce merge congestion
at realistic demand levels (5000–7000 vph combined).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOPOLOGY OVERVIEW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  upstream (3L)                              weaving (4L)   downstream (3L)
  ──────────────────────────────────────────┬──────────────┬─────────────
  seg_3_before  seg_2_before  seg_1_before  seg_0_before │ seg_0_after │ seg_1_after
  J0──────────J1──────────J2──────────J3──────────J4──────────J5──────────J6
  1000m        1000m        1000m        1000m       500m         1000m

  On-ramp (below mainline, 1000 m total):
    ramp_on_approach (700 m) → ramp_on_transition (200 m)
    → ramp_on_merge (100 m) ──► J4 / seg_0_after LANE 0

  Off-ramp (below mainline, 1000 m total):
    J5 / seg_0_after LANE 0 ──► ramp_off_diverge (100 m)
    → ramp_off_transition (200 m) → ramp_off_departure (700 m)

  Weaving zone: 500 m between the merge point (J4) and the diverge
  point (J5).  seg_0_after has 4 lanes; the extra lane 0 (rightmost)
  is the shared on/off ramp weaving lane.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LANE NUMBERING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Lane 0   = rightmost (shoulder / ramp weaving lane)
  Lane N-1 = leftmost  (fast / overtaking lane)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LANE ADDITION AND LANE DROP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  At J4 (merge junction) — LANE ADDITION:
    seg_0_before lane k  →  seg_0_after lane k+1  (k = 0, 1, 2)
    ramp_on_merge lane 0 →  seg_0_after lane 0    (yield / lowercase 'm')

  At J5 (diverge junction) — LANE DROP:
    seg_0_after lane k+1 →  seg_1_after lane k    (k = 0, 1, 2)
    seg_0_after lane 0   →  ramp_off_diverge lane 0 (right turn)
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

# Segment lengths
SEGMENT_LENGTHS = {
    "seg_3_before": 1000.0,
    "seg_2_before": 1000.0,
    "seg_1_before": 1000.0,
    "seg_0_before": 1000.0,
    "seg_0_after":   500.0,     # weaving zone
    "seg_1_after":  1000.0,
    # On-ramp (1000 m total)
    "ramp_on_approach":   700.0,
    "ramp_on_transition": 200.0,
    "ramp_on_merge":      100.0,
    # Off-ramp (1000 m total)
    "ramp_off_diverge":     100.0,
    "ramp_off_transition":  200.0,
    "ramp_off_departure":   700.0,
}

# Shape multipliers (visual compression for SUMO-GUI)
SHAPE_MULTIPLIERS = {
    "seg_3_before": 0.5,
    "seg_2_before": 0.5,
    "seg_1_before": 0.5,
    "seg_0_before": 1.0,    # full size — closest to merge
    "seg_0_after":  1.0,    # full size — weaving zone
    "seg_1_after":  0.5,
    "ramp_on_approach":   1.0,
    "ramp_on_transition": 1.0,
    "ramp_on_merge":      1.0,
    "ramp_off_diverge":   1.0,
    "ramp_off_transition": 1.0,
    "ramp_off_departure": 1.0,
}

MAIN_SEGMENTS = [
    "seg_3_before", "seg_2_before", "seg_1_before", "seg_0_before",
    "seg_0_after", "seg_1_after",
]

MAINLINE_SPEED = 33.33  # 120 kph in m/s
LANE_WIDTH = 3.2
DEFAULT_MAIN_LANES = 3
BUFFER_LANES = 4
Y_BASE = 60.0


# ---------------------------------------------------------------------------
# Network builder
# ---------------------------------------------------------------------------

def _lane_count(seg: str) -> int:
    if seg == "seg_0_after":
        return BUFFER_LANES
    return DEFAULT_MAIN_LANES


def _lane_y_offset(seg: str, lane_idx: int, lane_count: int) -> float:
    if seg == "seg_0_after" and lane_count == BUFFER_LANES:
        return (lane_idx - 2) * LANE_WIDTH
    return (lane_idx - (lane_count - 1) / 2) * LANE_WIDTH


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

    # --- Junctions ---
    junctions = {}
    current_x = -3000.0

    for i in range(len(MAIN_SEGMENTS) + 1):
        j_id = f"J{i}"
        junctions[j_id] = {"x": current_x, "y": Y_BASE, "id": j_id, "type": "priority"}
        if i < len(MAIN_SEGMENTS):
            seg = MAIN_SEGMENTS[i]
            visual_len = SEGMENT_LENGTHS[seg] * SHAPE_MULTIPLIERS[seg]
            current_x += visual_len

    # Merge junction = J4 (end of seg_0_before / start of seg_0_after)
    merge_jid = "J4"
    # Diverge junction = J5 (end of seg_0_after / start of seg_1_after)
    diverge_jid = "J5"

    # Ramp Y coordinates
    ramp_start_y = Y_BASE + RAMP_Y_OFFSET
    main_road_y = Y_BASE + _lane_y_offset("seg_0_after", 0, BUFFER_LANES)

    # --- On-ramp junctions ---
    on_total = (SEGMENT_LENGTHS["ramp_on_approach"]
                + SEGMENT_LENGTHS["ramp_on_transition"]
                + SEGMENT_LENGTHS["ramp_on_merge"])

    on_start_id = "J_ramp_on_start"
    on_mid1_id = "J_ramp_on_mid1"
    on_mid2_id = "J_ramp_on_mid2"

    junctions[on_start_id] = {
        "x": junctions[merge_jid]["x"] - on_total,
        "y": ramp_start_y,
        "id": on_start_id, "type": "dead_end",
    }

    # Y interpolation for on-ramp waypoints
    off_total = (SEGMENT_LENGTHS["ramp_off_diverge"]
                 + SEGMENT_LENGTHS["ramp_off_transition"]
                 + SEGMENT_LENGTHS["ramp_off_departure"])
    off_mid1_progress = SEGMENT_LENGTHS["ramp_off_diverge"] / off_total
    off_mid2_progress = (SEGMENT_LENGTHS["ramp_off_diverge"]
                         + SEGMENT_LENGTHS["ramp_off_transition"]) / off_total
    off_mid1_y = main_road_y + (ramp_start_y - main_road_y) * off_mid1_progress * RAMP_PROXIMITY_FACTOR
    off_mid2_y = main_road_y + (ramp_start_y - main_road_y) * off_mid2_progress * RAMP_PROXIMITY_FACTOR

    # Mirror off-ramp Y for on-ramp
    on_mid1_y = off_mid2_y
    on_mid2_y = off_mid1_y

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

    # --- Off-ramp junctions ---
    off_mid1_id = "J_ramp_off_mid1"
    off_mid2_id = "J_ramp_off_mid2"
    off_end_id = "J_ramp_off_end"

    junctions[off_mid1_id] = {
        "x": junctions[diverge_jid]["x"] + SEGMENT_LENGTHS["ramp_off_diverge"],
        "y": off_mid1_y,
        "id": off_mid1_id, "type": "priority",
    }
    junctions[off_mid2_id] = {
        "x": junctions[diverge_jid]["x"] + SEGMENT_LENGTHS["ramp_off_diverge"] + SEGMENT_LENGTHS["ramp_off_transition"],
        "y": off_mid2_y,
        "id": off_mid2_id, "type": "priority",
    }
    junctions[off_end_id] = {
        "x": junctions[diverge_jid]["x"] + off_total,
        "y": ramp_start_y,
        "id": off_end_id, "type": "dead_end",
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

    # --- Main road edges ---
    for i, seg in enumerate(MAIN_SEGMENTS):
        n_lanes = _lane_count(seg)
        edge = ET.SubElement(root, "edge")
        edge.set("id", seg)
        edge.set("from", f"J{i}")
        edge.set("to", f"J{i+1}")
        edge.set("priority", "-1")
        edge.set("length", str(SEGMENT_LENGTHS[seg]))

        j_from = junctions[f"J{i}"]
        j_to = junctions[f"J{i+1}"]

        for lane_idx in range(n_lanes):
            lane = ET.SubElement(edge, "lane")
            lane.set("id", f"{seg}_{lane_idx}")
            lane.set("index", str(lane_idx))
            lane.set("speed", f"{MAINLINE_SPEED:.2f}")
            lane.set("length", str(SEGMENT_LENGTHS[seg]))
            y_off = _lane_y_offset(seg, lane_idx, n_lanes)
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

    # --- Off-ramp edges (3 segments) ---
    off_edges = [
        ("ramp_off_diverge",    diverge_jid, off_mid1_id),
        ("ramp_off_transition", off_mid1_id, off_mid2_id),
        ("ramp_off_departure",  off_mid2_id, off_end_id),
    ]
    for seg_id, from_id, to_id in off_edges:
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
        start_y = main_road_y if seg_id == "ramp_off_diverge" else f["y"]
        lane.set("shape", f"{f['x']:.2f},{start_y:.2f} {t['x']:.2f},{t['y']:.2f}")

    # --- Connections: mainline ---
    for i in range(len(MAIN_SEGMENTS) - 1):
        from_edge = MAIN_SEGMENTS[i]
        to_edge = MAIN_SEGMENTS[i + 1]
        from_n = _lane_count(from_edge)
        to_n = _lane_count(to_edge)

        # Lane addition at merge (seg_0_before → seg_0_after)
        if from_edge == "seg_0_before" and to_edge == "seg_0_after":
            for k in range(from_n):
                c = ET.SubElement(root, "connection")
                c.set("from", from_edge); c.set("to", to_edge)
                c.set("fromLane", str(k)); c.set("toLane", str(k + 1))
                c.set("dir", "s"); c.set("state", "M")
            continue

        # Lane drop at diverge (seg_0_after → seg_1_after)
        if from_edge == "seg_0_after" and to_edge == "seg_1_after":
            for k in range(to_n):
                c = ET.SubElement(root, "connection")
                c.set("from", from_edge); c.set("to", to_edge)
                c.set("fromLane", str(k + 1)); c.set("toLane", str(k))
                c.set("dir", "s"); c.set("state", "M")
            continue

        # Normal same-lane-count connections
        for k in range(min(from_n, to_n)):
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

    # On-ramp merge → seg_0_after lane 0 (yield)
    c = ET.SubElement(root, "connection")
    c.set("from", "ramp_on_merge"); c.set("to", "seg_0_after")
    c.set("fromLane", "0"); c.set("toLane", "0")
    c.set("dir", "s"); c.set("state", "m")

    # --- Connections: off-ramp ---
    # seg_0_after lane 0 → ramp_off_diverge
    c = ET.SubElement(root, "connection")
    c.set("from", "seg_0_after"); c.set("to", "ramp_off_diverge")
    c.set("fromLane", "0"); c.set("toLane", "0")
    c.set("dir", "r"); c.set("state", "M")

    for from_e, to_e in [
        ("ramp_off_diverge", "ramp_off_transition"),
        ("ramp_off_transition", "ramp_off_departure"),
    ]:
        c = ET.SubElement(root, "connection")
        c.set("from", from_e); c.set("to", to_e)
        c.set("fromLane", "0"); c.set("toLane", "0")
        c.set("dir", "s"); c.set("state", "M")

    return root


def prettify_xml(elem):
    rough = ET.tostring(elem, encoding="unicode")
    reparsed = minidom.parseString(rough)
    return reparsed.toprettyxml(indent="    ", encoding="UTF-8")


def main():
    parser = argparse.ArgumentParser(description="Generate ramps_v1.net.xml")
    parser.add_argument("-o", "--output", default="ramps_v1.net.xml")
    args = parser.parse_args()

    root = create_network()
    output_path = os.path.join(os.path.dirname(__file__), args.output)
    with open(output_path, "wb") as f:
        f.write(prettify_xml(root))

    print(f"Network saved to: {args.output}")
    print(f"\nTopology: 3L mainline (4 × 1000m) → 4L weaving (500m) → 3L downstream (1000m)")
    print(f"On-ramp: 1000m (700 approach + 200 transition + 100 merge)")
    print(f"Off-ramp: 1000m (100 diverge + 200 transition + 700 departure)")
    print(f"Total mainline: ~5.5 km")
    print(f"\nOpen in netedit → Processing → Compute Junctions")


if __name__ == "__main__":
    exit(main())
