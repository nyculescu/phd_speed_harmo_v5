#!/usr/bin/env python3
"""
generate_ramp_network.py
========================
SUMO raw-network generator for the **ramps_v0** topology
(3-lane mainline → 4-lane weaving buffer → 3-lane downstream,
 with on-ramp and off-ramp flanking a 250 m weaving section).

Produces ``ramps_v0.net.xml`` by writing SUMO net-XML directly (no netconvert).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOPOLOGY OVERVIEW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  upstream (3L)                  weaving (4L)     downstream (3L)
  ─────────────────────────────┬───────────────┬──────────────────
  seg_2_before  seg_1_before  seg_0_before │ seg_0_after │ seg_1_after
  J0──────────J1──────────J2──────────J3──────────J4──────────J5
  1000m        1000m        1000m     250m         1000m

  On-ramp (below mainline, 500 m total):
    ramp_on_approach (300 m) → ramp_on_transition (100 m)
    → ramp_on_merge (100 m) ──► J3 / seg_0_after LANE 0

  Off-ramp (below mainline, 500 m total):
    J4 / seg_0_after LANE 0 ──► ramp_off_diverge (100 m)
    → ramp_off_transition (100 m) → ramp_off_departure (300 m)

  Weaving zone: 250 m between the merge point (J3) and the diverge
  point (J4).  seg_0_after has 4 lanes; the extra lane 0 (rightmost)
  is the shared on/off ramp weaving lane.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LANE NUMBERING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Lane 0  = rightmost (shoulder / ramp weaving lane)
  Lane N-1 = leftmost (fast / overtaking lane)

  SUMO uses this convention consistently.  All detector IDs and
  TraCI calls use the same numbering.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LANE ADDITION AND LANE DROP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  At J3 (merge junction) — LANE ADDITION:
    seg_0_before lane k  →  seg_0_after lane k+1  (k = 0, 1, 2)
    ramp_on_merge lane 0 →  seg_0_after lane 0   (yield / lowercase 'm')

    The mainline lanes shift UP by one index to free lane 0 for the
    ramp-weaving vehicle.  The Y-coordinates of lanes 1–3 in
    seg_0_after are identical to lanes 0–2 of seg_0_before, so the
    mainline road appears straight through the junction.

  At J4 (diverge junction) — LANE DROP:
    seg_0_after lane k+1 →  seg_1_after lane k   (k = 0, 1, 2)
    seg_0_after lane 0   →  ramp_off_diverge lane 0  (right exit, 'r')

    The weaving lane 0 is consumed by the off-ramp; mainline lanes
    shift DOWN by one index, again preserving Y-alignment.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Y-COORDINATE SYSTEM
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Y_BASE = 60.0 m  — mainline road centreline.
  All mainline junction nodes (J0–J5) sit at Y_BASE.
  Lane Y-offsets are computed relative to the junction node:

    Standard formula (N-lane edge):
      lane k  →  y_offset = (k − (N−1)/2) × LANE_WIDTH

    4-lane buffer (seg_0_after) special formula:
      lane k  →  y_offset = (k − 2) × LANE_WIDTH
      This shifts the anchor such that lanes 1–3 stay at the same
      absolute Y as the upstream 3-lane mainline, while lane 0 sits
      one additional LANE_WIDTH below (= the ramp weaving lane).

  Concrete Y values (LANE_WIDTH = 3.2 m, Y_BASE = 60.0):
    seg_*_before / seg_1_after (3L):   lane 0 → 56.8  lane 1 → 60.0  lane 2 → 63.2
    seg_0_after             (4L):   lane 0 → 53.6  lane 1 → 56.8  lane 2 → 60.0  lane 3 → 63.2
                                                ↑ weaving lane (on+off ramp)

  The ramps run at  y = Y_BASE + RAMP_Y_OFFSET = 40.0 m  during their
  straight approach/departure sections (20 m below the mainline).
  merge_lane0_y = 53.6 m  is where the ramp meets seg_0_after lane 0.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RAMP GEOMETRY AND JUNCTION WAYPOINTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  The ramp is modelled as three edges connected by two intermediate
  junctions (J_ramp_on_mid1, J_ramp_on_mid2).  Each edge's lane
  carries a two-point ``shape`` that SUMO uses for visual rendering;
  netedit's "Compute Junctions" refines internal-edge geometry.

  On-ramp Y profile (left → right, upstream to merge):
    J_ramp_on_start  →  J_ramp_on_mid1  : y = ramp_start_y  (flat approach)
    J_ramp_on_mid1   →  J_ramp_on_mid2  : y rises to ramp_mid_y  (start of curve)
    J_ramp_on_mid2   →  J3 (shape end)  : y rises to merge_lane0_y  (joins mainline)

  Off-ramp Y profile (left → right, diverge to departure):
    J4 (shape start) →  J_ramp_off_mid1 : y drops from diverge_lane0_y to ramp_mid_y
    J_ramp_off_mid1  →  J_ramp_off_mid2 : y drops to ramp_start_y  (end of curve)
    J_ramp_off_mid2  →  J_ramp_off_end  : y = ramp_start_y  (flat departure)

  IMPORTANT — end_y / start_y overrides:
    ramp_on_merge  ends  at merge_lane0_y (not at J3.y = Y_BASE).
    ramp_off_diverge starts at diverge_lane0_y (not at J4.y = Y_BASE).
    These shape overrides are applied inside create_network() via the
    on_ramp_defs / off_ramp_defs tuples.  netedit reads the shape
    attribute and adjusts the junction polygon accordingly.

  Why this profile?
    Earlier attempts used a mirrored off-ramp formula for the on-ramp,
    causing most of the Y rise to happen in the long approach section
    and leaving the short transition+merge nearly flat.  This made the
    ramp visually overlap seg_0_before lane 0 at J3 in netedit.
    The flat-approach + concentrated-curve profile solves this:
    the approach is clearly separate from the mainline, and the curve
    appears only in the last 200 m where it is physically expected.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RAW-NET-XML GENERATION NOTES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  This script writes a SUMO raw net-XML file without running netconvert.
  The raw format includes junctions, edges (with lane shapes), and
  connection elements.  It does NOT include internal edges
  (``<edge function="internal">``) — those are generated by netedit.

  Required post-step:
    Open ramps_v0.net.xml in netedit, then:
    Processing → Compute Junctions  (Ctrl+J)
    File → Save Network  (Ctrl+S)

  After "Compute Junctions":
  • Junction shapes (convex polygons) are calculated from lane endpoints.
  • Internal edges (e.g. ``:J3_0_0``) are inserted for smooth routing.
  • Lane shapes may be slightly trimmed at junction boundaries.

  The resulting net.xml can then be used directly with SUMO/TraCI.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
VISUAL SHAPE MULTIPLIERS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Long upstream/downstream segments (1 km) are visually compressed to
  avoid a very wide network view.  SHAPE_MULTIPLIERS[seg] controls
  visual_length = actual_length × multiplier.  Segments near the
  weaving zone (seg_0_before, seg_0_after) and all ramp segments use
  multiplier = 1.0 so the critical merge area renders at true scale.
  Simulation physics always use the actual lengths in SEGMENT_LENGTHS.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
USAGE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  # From project root:
  python3 traffic_environment/sumo/generate_ramp_network.py
  # → writes traffic_environment/sumo/ramps_v0.net.xml

  python3 traffic_environment/sumo/generate_ramp_network.py -o custom.net.xml

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COMPANION FILES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  detectors_ramps_v0.add.xml   — E1 + E3 detectors (freq = 30 s)
  tools/no_control_baseline.py — no-control diagnostic runner

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXTENDING THIS NETWORK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  To add more upstream segments:
    1. Append segment IDs to MAIN_SEGMENTS before 'seg_0_before'.
    2. Add their lengths to SEGMENT_LENGTHS.
    3. Add shape multipliers to SHAPE_MULTIPLIERS.
    4. Update MERGE_JUNCTION_IDX and DIVERGE_JUNCTION_IDX accordingly
       (= position of seg_0_before's end-junction in the new list).
    5. Update detector IDs in detectors_ramps_v0.add.xml.

  To change lane counts:
    LANES_BEFORE, LANES_BUFFER, LANES_AFTER are the only constants
    to change.  The connection logic in create_network() handles
    lane-addition and lane-drop automatically for any combination
    where LANES_BUFFER == LANES_BEFORE + 1 == LANES_AFTER + 1.
"""

import os
import argparse
import xml.etree.ElementTree as ET
from xml.dom import minidom

# ---------------------------------------------------------------------------
# Ramp geometry constants
# ---------------------------------------------------------------------------
RAMP_Y_OFFSET = -20.0
# Y-offset of the ramp approach/departure floor relative to Y_BASE.
# Negative = ramp runs below the mainline.
# Increasing the magnitude (e.g. -30) widens the visual gap between ramp
# and mainline in the approach/departure sections.

RAMP_SPEED = 25.0
# Speed limit on all ramp edges [m/s].  25.0 m/s = 90 km/h.
# Mainline speed (MAIN_SPEED) is set separately for mainline edges.

# ---------------------------------------------------------------------------
# Segment lengths [m]  — used for simulation physics AND visual rendering
# ---------------------------------------------------------------------------
# Mainline segments are numbered from upstream to downstream.
# seg_0_before is the last upstream segment before the merge junction.
# seg_0_after is the 4-lane weaving buffer between merge and diverge.
# seg_1_after is the first downstream segment after the diverge junction.
#
# On-ramp geometry (total 500 m):
#   approach    — straight section where the ramp runs parallel to mainline
#   transition  — transition zone (intended VSL / speed-control zone)
#   merge       — the short curved section where ramp joins mainline lane 0
#
# Off-ramp geometry (total 500 m, symmetric layout):
#   diverge     — short curved section where lane 0 peels away from mainline
#   transition  — transition zone (optional ramp metering / speed control)
#   departure   — straight section running parallel to mainline before exiting
SEGMENT_LENGTHS = {
    'seg_2_before':        1000.0,
    'seg_1_before':        1000.0,
    'seg_0_before':        1000.0,
    'seg_0_after':          250.0,   # weaving buffer; keep short for tight weave model
    'seg_1_after':         1000.0,
    'ramp_on_approach':     300.0,
    'ramp_on_transition':   100.0,
    'ramp_on_merge':        100.0,
    'ramp_off_diverge':     100.0,
    'ramp_off_transition':  100.0,
    'ramp_off_departure':   300.0,
}

# ---------------------------------------------------------------------------
# Visual shape multipliers
# ---------------------------------------------------------------------------
# SUMO uses the lane `shape` attribute only for rendering.  Long upstream/
# downstream segments are compressed visually (multiplier < 1.0) to keep
# the network view manageable.  The weaving zone and all ramp edges use 1.0
# so the critical area renders at true scale.
#
# IMPORTANT: multipliers affect junction X positions (and therefore the
# ramp's horizontal position relative to the mainline) but NOT simulation
# physics — vehicles always travel the distances in SEGMENT_LENGTHS.
SHAPE_MULTIPLIERS = {
    'seg_2_before':        0.5,   # 50% visual compression
    'seg_1_before':        0.5,
    'seg_0_before':        1.0,   # true scale — last segment before merge
    'seg_0_after':         1.0,   # true scale — weaving zone
    'seg_1_after':         0.5,
    'ramp_on_approach':    1.0,
    'ramp_on_transition':  1.0,
    'ramp_on_merge':       1.0,
    'ramp_off_diverge':    1.0,
    'ramp_off_transition': 1.0,
    'ramp_off_departure':  1.0,
}

# ---------------------------------------------------------------------------
# Mainline segment order (upstream → downstream)
# ---------------------------------------------------------------------------
# Junction indices are derived from position in this list:
#   J{i} = start of MAIN_SEGMENTS[i]
#   J{len(MAIN_SEGMENTS)} = end of last segment
MAIN_SEGMENTS = [
    'seg_2_before',    # J0 → J1
    'seg_1_before',    # J1 → J2
    'seg_0_before',    # J2 → J3  ← merge junction (on-ramp joins here)
    'seg_0_after',     # J3 → J4  ← diverge junction (off-ramp leaves here)
    'seg_1_after',     # J4 → J5
]

# Indices into MAIN_SEGMENTS for the special junctions.
# Update these if segments are added/removed.
MERGE_JUNCTION_IDX   = 3   # J3: end of seg_0_before / start of seg_0_after
DIVERGE_JUNCTION_IDX = 4   # J4: end of seg_0_after  / start of seg_1_after

# ---------------------------------------------------------------------------
# Lane counts
# ---------------------------------------------------------------------------
LANES_BEFORE  = 3   # all seg_*_before segments
LANES_BUFFER  = 4   # seg_0_after (one extra ramp weaving lane)
LANES_AFTER   = 3   # seg_1_after
# The relationship LANES_BUFFER == LANES_BEFORE + 1 == LANES_AFTER + 1 is
# required for the lane-shift connection logic to be correct.

LANE_WIDTH = 3.2    # m — standard European motorway lane width
MAIN_SPEED = 33.33  # m/s ≈ 120 km/h — mainline free-flow speed limit
Y_BASE = 60.0       # m — Y coordinate of the mainline road centreline


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _lane_count(seg_id: str) -> int:
    """Return the number of lanes for a given main-road segment ID."""
    if seg_id == 'seg_0_after':
        return LANES_BUFFER
    if seg_id == 'seg_1_after':
        return LANES_AFTER
    return LANES_BEFORE


def _lane_y_offset(seg_id: str, lane_idx: int, lane_count: int) -> float:
    """Return the Y-offset of lane ``lane_idx`` relative to the junction node Y.

    Standard formula centres the road on the junction node:
        offset = (lane_idx − (lane_count − 1) / 2) × LANE_WIDTH

    Special case — seg_0_after (4-lane buffer):
        offset = (lane_idx − 2) × LANE_WIDTH
        This anchors lanes 1–3 at the same absolute Y as the 3-lane mainline,
        so the mainline appears straight through the merge/diverge junction.
        Lane 0 is placed one LANE_WIDTH further right (lower Y), becoming
        the dedicated ramp weaving lane:
            lane 0 → Y_BASE − 2×LANE_WIDTH = 53.6 m  (ramp weaving)
            lane 1 → Y_BASE − 1×LANE_WIDTH = 56.8 m  (former lane 0)
            lane 2 → Y_BASE               = 60.0 m  (former lane 1)
            lane 3 → Y_BASE + 1×LANE_WIDTH = 63.2 m  (former lane 2)
    """
    if seg_id == 'seg_0_after' and lane_count == LANES_BUFFER:
        return (lane_idx - 2) * LANE_WIDTH
    return (lane_idx - (lane_count - 1) / 2) * LANE_WIDTH


def _build_junctions() -> tuple:
    """Compute all junction positions and return (junctions, merge_lane0_y, diverge_lane0_y).

    junctions : dict[str, dict]
        Keys are junction IDs; values are dicts with 'x', 'y', 'type'.

    merge_lane0_y : float
        Absolute Y position of seg_0_after lane 0 at junction J3.
        This is the Y at which the on-ramp's final lane shape endpoint
        must arrive (= the ramp merge point).

    diverge_lane0_y : float
        Absolute Y position of seg_0_after lane 0 at junction J4.
        This is the Y from which the off-ramp's first lane shape starts
        (= the ramp diverge point).  Numerically equal to merge_lane0_y
        because seg_0_after has uniform lane geometry throughout.
    """
    junctions = {}
    x = -3000.0   # X coordinate of J0 (leftmost junction)

    # Main-road junctions J0 … J{len(MAIN_SEGMENTS)}
    for i, seg_id in enumerate(MAIN_SEGMENTS):
        junctions[f'J{i}'] = {'x': x, 'y': Y_BASE, 'type': 'priority'}
        x += SEGMENT_LENGTHS[seg_id] * SHAPE_MULTIPLIERS[seg_id]
    junctions[f'J{len(MAIN_SEGMENTS)}'] = {'x': x, 'y': Y_BASE, 'type': 'dead_end'}

    # Absolute Y of the ramp weaving lane (seg_0_after lane 0) at both ramp junctions
    merge_lane0_y   = Y_BASE + _lane_y_offset('seg_0_after', 0, LANES_BUFFER)
    diverge_lane0_y = merge_lane0_y   # same lane, same geometry

    merge_x   = junctions[f'J{MERGE_JUNCTION_IDX}']['x']
    diverge_x = junctions[f'J{DIVERGE_JUNCTION_IDX}']['x']

    # Y of the ramp floor (flat approach/departure sections)
    ramp_start_y = Y_BASE + RAMP_Y_OFFSET
    # Y halfway between ramp floor and the merge lane (used as mid-curve waypoint)
    ramp_mid_y   = (ramp_start_y + merge_lane0_y) / 2.0

    # Total ramp lengths (for X positioning of start/end junctions)
    total_on_ramp = (SEGMENT_LENGTHS['ramp_on_approach'] +
                     SEGMENT_LENGTHS['ramp_on_transition'] +
                     SEGMENT_LENGTHS['ramp_on_merge'])
    off_total     = (SEGMENT_LENGTHS['ramp_off_diverge'] +
                     SEGMENT_LENGTHS['ramp_off_transition'] +
                     SEGMENT_LENGTHS['ramp_off_departure'])

    # ------------------------------------------------------------------
    # Ramp waypoint strategy — Y profile
    # ------------------------------------------------------------------
    # On-ramp (left → right, upstream to merge junction J3):
    #
    #   approach section  (300 m): ramp stays FLAT at ramp_start_y
    #                              → clearly below and separate from mainline
    #   transition section (100 m): Y rises from ramp_start_y to ramp_mid_y
    #                              → start of the visible "ramp curves up" arc
    #   merge section      (100 m): Y rises from ramp_mid_y to merge_lane0_y
    #                              → ramp joins seg_0_after lane 0 at J3
    #
    # Off-ramp (left → right, diverge junction J4 to departure):
    #
    #   diverge section    (100 m): Y drops from diverge_lane0_y to ramp_mid_y
    #   transition section (100 m): Y drops from ramp_mid_y to ramp_start_y
    #   departure section  (300 m): ramp stays FLAT at ramp_start_y
    #
    # Rationale:
    #   Concentrating the curve in the short merge/diverge segments (100 m
    #   each) rather than spreading it across the long approach/departure
    #   (300 m) ensures the ramp is visually well-separated from the mainline
    #   for most of its length.  Previous mirrored-off-ramp logic produced
    #   the opposite profile (ramp nearly horizontal at J3), causing the
    #   ramp_on_merge lane to visually overlap seg_0_before lane 0 in netedit.
    # ------------------------------------------------------------------

    # On-ramp junction positions
    junctions['J_ramp_on_start'] = {
        'x': merge_x - total_on_ramp,
        'y': ramp_start_y,       # flat start — well below mainline
        'type': 'dead_end',
    }
    junctions['J_ramp_on_mid1'] = {
        'x': merge_x - SEGMENT_LENGTHS['ramp_on_transition'] - SEGMENT_LENGTHS['ramp_on_merge'],
        'y': ramp_start_y,       # end of flat approach = start of climb
        'type': 'priority',
    }
    junctions['J_ramp_on_mid2'] = {
        'x': merge_x - SEGMENT_LENGTHS['ramp_on_merge'],
        'y': ramp_mid_y,         # midpoint of the climb curve
        'type': 'priority',
    }
    # Note: ramp_on_merge's lane shape endpoint is overridden to merge_lane0_y
    # (not J3.y = Y_BASE) inside create_network() — see on_ramp_defs.

    # Off-ramp junction positions
    junctions['J_ramp_off_mid1'] = {
        'x': diverge_x + SEGMENT_LENGTHS['ramp_off_diverge'],
        'y': ramp_mid_y,         # midpoint of the descent curve
        'type': 'priority',
    }
    junctions['J_ramp_off_mid2'] = {
        'x': diverge_x + SEGMENT_LENGTHS['ramp_off_diverge'] + SEGMENT_LENGTHS['ramp_off_transition'],
        'y': ramp_start_y,       # end of descent = start of flat departure
        'type': 'priority',
    }
    junctions['J_ramp_off_end'] = {
        'x': diverge_x + off_total,
        'y': ramp_start_y,       # flat end
        'type': 'dead_end',
    }
    # Note: ramp_off_diverge's lane shape start is overridden to diverge_lane0_y
    # (not J4.y = Y_BASE) inside create_network() — see off_ramp_defs.

    return junctions, merge_lane0_y, diverge_lane0_y


# ---------------------------------------------------------------------------
# Network builder
# ---------------------------------------------------------------------------

def create_network() -> ET.Element:
    """Build and return the root <net> XML element for ramps_v0.

    Element order in the output follows the SUMO raw-net-XML convention:
        1. <location>
        2. <junction> elements (all)
        3. <edge> elements — mainline, then on-ramp, then off-ramp
        4. <connection> elements — mainline, then ramp internal, then ramp merge/diverge

    The output is intentionally minimal: no internal edges, no tlLogics,
    no roundabouts.  netedit's "Compute Junctions" fills in the rest.
    """
    root = ET.Element('net')
    root.set('version', '1.21.0')
    root.set('junctionCornerDetail', '5')
    root.set('limitTurnSpeed', '5.50')
    root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
    root.set('xsi:noNamespaceSchemaLocation',
             'http://sumo.dlr.de/xsd/net_file.xsd')

    loc = ET.SubElement(root, 'location')
    loc.set('netOffset', '0.00,0.00')
    loc.set('convBoundary', '-3500.00,20.00,2500.00,80.00')
    loc.set('origBoundary', '-10000000000.00,-10000000000.00,10000000000.00,10000000000.00')
    loc.set('projParameter', '!')

    junctions, merge_lane0_y, diverge_lane0_y = _build_junctions()

    # ---- Junction elements ----
    # incLanes / intLanes / shape are left empty; netedit computes them.
    for j_id, j in junctions.items():
        el = ET.SubElement(root, 'junction')
        el.set('id', j_id)
        el.set('type', j['type'])
        el.set('x', f"{j['x']:.2f}")
        el.set('y', f"{j['y']:.2f}")
        el.set('incLanes', '')
        el.set('intLanes', '')
        el.set('shape', '')

    # ---- Main-road edges ----
    # Each lane gets a two-point shape: (from_junction_x, lane_y) → (to_junction_x, lane_y).
    # Lanes are horizontal (constant Y) for all mainline segments; the junction
    # node Y never differs between J0–J5 (all at Y_BASE).
    for i, seg_id in enumerate(MAIN_SEGMENTS):
        from_j = junctions[f'J{i}']
        to_j   = junctions[f'J{i + 1}']
        lcount = _lane_count(seg_id)

        edge = ET.SubElement(root, 'edge')
        edge.set('id', seg_id)
        edge.set('from', f'J{i}')
        edge.set('to', f'J{i + 1}')
        edge.set('priority', '-1')
        edge.set('length', str(SEGMENT_LENGTHS[seg_id]))

        for lane_idx in range(lcount):
            y_off = _lane_y_offset(seg_id, lane_idx, lcount)
            lane = ET.SubElement(edge, 'lane')
            lane.set('id', f'{seg_id}_{lane_idx}')
            lane.set('index', str(lane_idx))
            lane.set('speed', str(MAIN_SPEED))
            lane.set('length', str(SEGMENT_LENGTHS[seg_id]))
            lane.set('shape', (
                f"{from_j['x']:.2f},{from_j['y'] + y_off:.2f} "
                f"{to_j['x']:.2f},{to_j['y'] + y_off:.2f}"
            ))

    # ---- On-ramp edges ----
    # Each tuple: (edge_id, from_junction, to_junction, start_y_override, end_y_override)
    # None → use junction['y']; a float → use that Y for the lane shape endpoint.
    #
    # end_y_override for ramp_on_merge:
    #   The lane shape must end at merge_lane0_y (= Y of seg_0_after lane 0),
    #   NOT at J3.y (= Y_BASE = 60.0).  J3 is the mainline centreline junction,
    #   but the ramp physically joins one lane width below it.  Setting the
    #   shape endpoint correctly allows netedit to compute the junction polygon
    #   with the ramp entering from the correct Y position.
    on_ramp_defs = [
        ('ramp_on_approach',   'J_ramp_on_start', 'J_ramp_on_mid1', None,          None),
        ('ramp_on_transition', 'J_ramp_on_mid1',  'J_ramp_on_mid2', None,          None),
        ('ramp_on_merge',      'J_ramp_on_mid2',  f'J{MERGE_JUNCTION_IDX}', None,  merge_lane0_y),
    ]
    for edge_id, from_id, to_id, start_y_ov, end_y_ov in on_ramp_defs:
        from_j = junctions[from_id]
        to_j   = junctions[to_id]
        sx = from_j['x']
        sy = start_y_ov if start_y_ov is not None else from_j['y']
        ex = to_j['x']
        ey = end_y_ov   if end_y_ov   is not None else to_j['y']

        edge = ET.SubElement(root, 'edge')
        edge.set('id', edge_id)
        edge.set('from', from_id)
        edge.set('to', to_id)
        edge.set('priority', '-1')
        edge.set('length', str(SEGMENT_LENGTHS[edge_id]))

        lane = ET.SubElement(edge, 'lane')
        lane.set('id', f'{edge_id}_0')
        lane.set('index', '0')
        lane.set('speed', str(RAMP_SPEED))
        lane.set('length', str(SEGMENT_LENGTHS[edge_id]))
        lane.set('shape', f"{sx:.2f},{sy:.2f} {ex:.2f},{ey:.2f}")

    # ---- Off-ramp edges ----
    # start_y_override for ramp_off_diverge:
    #   Mirrors the ramp_on_merge logic above; the diverge lane shape must START
    #   at diverge_lane0_y, not at J4.y = Y_BASE.
    off_ramp_defs = [
        ('ramp_off_diverge',    f'J{DIVERGE_JUNCTION_IDX}', 'J_ramp_off_mid1', diverge_lane0_y, None),
        ('ramp_off_transition', 'J_ramp_off_mid1',           'J_ramp_off_mid2', None,            None),
        ('ramp_off_departure',  'J_ramp_off_mid2',            'J_ramp_off_end',  None,            None),
    ]
    for edge_id, from_id, to_id, start_y_ov, end_y_ov in off_ramp_defs:
        from_j = junctions[from_id]
        to_j   = junctions[to_id]
        sx = from_j['x']
        sy = start_y_ov if start_y_ov is not None else from_j['y']
        ex = to_j['x']
        ey = end_y_ov   if end_y_ov   is not None else to_j['y']

        edge = ET.SubElement(root, 'edge')
        edge.set('id', edge_id)
        edge.set('from', from_id)
        edge.set('to', to_id)
        edge.set('priority', '-1')
        edge.set('length', str(SEGMENT_LENGTHS[edge_id]))

        lane = ET.SubElement(edge, 'lane')
        lane.set('id', f'{edge_id}_0')
        lane.set('index', '0')
        lane.set('speed', str(RAMP_SPEED))
        lane.set('length', str(SEGMENT_LENGTHS[edge_id]))
        lane.set('shape', f"{sx:.2f},{sy:.2f} {ex:.2f},{ey:.2f}")

    # ---- Main-road connections ----
    # Special cases handle the lane-addition at J3 and lane-drop at J4.
    # All other consecutive-segment pairs use a 1-to-1 lane mapping.
    for i in range(len(MAIN_SEGMENTS) - 1):
        from_seg = MAIN_SEGMENTS[i]
        to_seg   = MAIN_SEGMENTS[i + 1]
        from_cnt = _lane_count(from_seg)
        to_cnt   = _lane_count(to_seg)

        if from_seg == 'seg_0_before' and to_seg == 'seg_0_after':
            # LANE ADDITION at J3:
            # The on-ramp occupies seg_0_after lane 0, so mainline lanes must
            # shift up by 1 to accommodate it.
            #   seg_0_before lane 0 → seg_0_after lane 1
            #   seg_0_before lane 1 → seg_0_after lane 2
            #   seg_0_before lane 2 → seg_0_after lane 3
            # The ramp connection (ramp_on_merge_0 → seg_0_after_0) is added
            # separately below.
            for k in range(from_cnt):
                conn = ET.SubElement(root, 'connection')
                conn.set('from', from_seg)
                conn.set('to', to_seg)
                conn.set('fromLane', str(k))
                conn.set('toLane', str(k + 1))
                conn.set('dir', 's')
                conn.set('state', 'M')
            continue

        if from_seg == 'seg_0_after' and to_seg == 'seg_1_after':
            # LANE DROP at J4:
            # Lane 0 of seg_0_after exits via the off-ramp; the remaining
            # three lanes shift back down by 1.
            #   seg_0_after lane 1 → seg_1_after lane 0
            #   seg_0_after lane 2 → seg_1_after lane 1
            #   seg_0_after lane 3 → seg_1_after lane 2
            # The off-ramp connection (seg_0_after_0 → ramp_off_diverge_0) is
            # added separately below.
            for k in range(to_cnt):
                conn = ET.SubElement(root, 'connection')
                conn.set('from', from_seg)
                conn.set('to', to_seg)
                conn.set('fromLane', str(k + 1))
                conn.set('toLane', str(k))
                conn.set('dir', 's')
                conn.set('state', 'M')
            continue

        # Standard 1-to-1 lane mapping (same lane count on both sides)
        for k in range(min(from_cnt, to_cnt)):
            conn = ET.SubElement(root, 'connection')
            conn.set('from', from_seg)
            conn.set('to', to_seg)
            conn.set('fromLane', str(k))
            conn.set('toLane', str(k))
            conn.set('dir', 's')
            conn.set('state', 'M')

    # ---- On-ramp internal connections ----
    for from_e, to_e in [
        ('ramp_on_approach',   'ramp_on_transition'),
        ('ramp_on_transition', 'ramp_on_merge'),
    ]:
        conn = ET.SubElement(root, 'connection')
        conn.set('from', from_e)
        conn.set('to', to_e)
        conn.set('fromLane', '0')
        conn.set('toLane', '0')
        conn.set('dir', 's')
        conn.set('state', 'M')

    # On-ramp merge into mainline weaving lane (ramp yields to mainline)
    # state='m' (lowercase) = yield / give-way at the junction.
    conn = ET.SubElement(root, 'connection')
    conn.set('from', 'ramp_on_merge')
    conn.set('to', 'seg_0_after')
    conn.set('fromLane', '0')
    conn.set('toLane', '0')
    conn.set('dir', 's')
    conn.set('state', 'm')   # yield — ramp gives way to mainline traffic

    # Off-ramp exit from weaving lane (mainline lane 0 → ramp diverge)
    # dir='r' = right turn (the ramp curves away to the right / lower Y).
    conn = ET.SubElement(root, 'connection')
    conn.set('from', 'seg_0_after')
    conn.set('to', 'ramp_off_diverge')
    conn.set('fromLane', '0')
    conn.set('toLane', '0')
    conn.set('dir', 'r')
    conn.set('state', 'M')

    # ---- Off-ramp internal connections ----
    for from_e, to_e in [
        ('ramp_off_diverge',    'ramp_off_transition'),
        ('ramp_off_transition', 'ramp_off_departure'),
    ]:
        conn = ET.SubElement(root, 'connection')
        conn.set('from', from_e)
        conn.set('to', to_e)
        conn.set('fromLane', '0')
        conn.set('toLane', '0')
        conn.set('dir', 's')
        conn.set('state', 'M')

    return root


# ---------------------------------------------------------------------------
# XML formatting
# ---------------------------------------------------------------------------

def prettify_xml(elem: ET.Element) -> bytes:
    """Serialize ``elem`` to indented UTF-8 XML bytes."""
    raw = ET.tostring(elem, encoding='unicode')
    return minidom.parseString(raw).toprettyxml(indent='    ', encoding='UTF-8')


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            'Generate the ramps_v0 SUMO network '
            '(3L mainline → 4L weaving buffer → 3L downstream, on-ramp + off-ramp). '
            'Run netedit → Processing → Compute Junctions after generation.'
        )
    )
    parser.add_argument('-o', '--output', default='ramps_v0.net.xml',
                        help='Output file name (default: ramps_v0.net.xml)')
    args = parser.parse_args()

    root = create_network()

    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), args.output)
    with open(output_path, 'wb') as f:
        f.write(prettify_xml(root))

    print(f'Network written to: {output_path}')
    print()
    print('Topology:')
    print(f'  Upstream:   seg_2_before → seg_1_before → seg_0_before  [{LANES_BEFORE}L, 1000 m each]')
    print(f'  Buffer:     seg_0_after                                   [{LANES_BUFFER}L, {int(SEGMENT_LENGTHS["seg_0_after"])} m — weaving zone]')
    print(f'  Downstream: seg_1_after                                   [{LANES_AFTER}L, 1000 m]')
    print(f'  On-ramp:    approach({int(SEGMENT_LENGTHS["ramp_on_approach"])} m, flat)'
          f' → transition({int(SEGMENT_LENGTHS["ramp_on_transition"])} m, curve)'
          f' → merge({int(SEGMENT_LENGTHS["ramp_on_merge"])} m) → seg_0_after lane 0')
    print(f'  Off-ramp:   seg_0_after lane 0 → diverge({int(SEGMENT_LENGTHS["ramp_off_diverge"])} m)'
          f' → transition({int(SEGMENT_LENGTHS["ramp_off_transition"])} m, curve)'
          f' → departure({int(SEGMENT_LENGTHS["ramp_off_departure"])} m, flat)')
    print()
    print('Lane logic:')
    print('  At J3 (merge):   seg_0_before lane k → seg_0_after lane k+1  (shift up)')
    print('                   ramp_on_merge lane 0 → seg_0_after lane 0   (yield)')
    print('  At J4 (diverge): seg_0_after lane k+1 → seg_1_after lane k   (shift down)')
    print('                   seg_0_after lane 0   → ramp_off_diverge lane 0')
    print()
    print('⚠  Open in netedit → Processing → Compute Junctions (Ctrl+J) → Save (Ctrl+S)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
