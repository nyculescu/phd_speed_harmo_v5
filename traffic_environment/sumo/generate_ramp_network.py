#!/usr/bin/env python3
"""
generate_ramp_network.py
SUMO network generator for the ramp_on_v0 topology.

Topology (ramp-on only, no off-ramp):
    seg_2_before (3L, 1000m)
    → seg_1_before (3L, 1000m)
    → seg_0_before (3L, 1000m)
    → seg_0_after  (3L,  250m)   ← merge zone; ramp_on_merge enters here at lane 0
    → seg_1_after  (3L, 1000m)

    ramp_on_approach (1L, 300m) → ramp_on_transition (1L, 100m) → ramp_on_merge (1L, 100m)
        merges into seg_0_after lane 0 at J3 (end of seg_0_before).

Usage:
    python generate_ramp_network.py              # writes ramp_on_v0.net.xml
    python generate_ramp_network.py -o foo.net.xml

⚠  After generation, open in netedit and run
   Processing → Compute Junctions to generate internal edges and proper geometry.
"""

import os
import argparse
import xml.etree.ElementTree as ET
from xml.dom import minidom

# ---------------------------------------------------------------------------
# Ramp geometry constants
# ---------------------------------------------------------------------------
RAMP_Y_OFFSET = -20.0        # Y-offset for ramp below main road (m)
RAMP_SPEED = 25.0            # Speed limit on ramp edges (m/s = 90 km/h)
RAMP_PROXIMITY_FACTOR = 0.7  # Controls how close ramp arches toward main road

# ---------------------------------------------------------------------------
# Segment lengths (simulation lengths, not visual lengths)
# ---------------------------------------------------------------------------
SEGMENT_LENGTHS = {
    'seg_2_before':       1000.0,
    'seg_1_before':       1000.0,
    'seg_0_before':       1000.0,
    'seg_0_after':         250.0,
    'seg_1_after':        1000.0,
    'ramp_on_approach':    300.0,
    'ramp_on_transition':  100.0,
    'ramp_on_merge':       100.0,
}

# Visual multipliers (visual_length = actual_length × multiplier)
# Reduces visual crowding for long upstream segments.
SHAPE_MULTIPLIERS = {
    'seg_2_before':       0.5,
    'seg_1_before':       0.5,
    'seg_0_before':       1.0,
    'seg_0_after':        1.0,
    'seg_1_after':        0.5,
    'ramp_on_approach':   1.0,
    'ramp_on_transition': 1.0,
    'ramp_on_merge':      1.0,
}

# Ordered list of main-road edges (upstream → downstream)
MAIN_SEGMENTS = [
    'seg_2_before',
    'seg_1_before',
    'seg_0_before',
    'seg_0_after',
    'seg_1_after',
]

# Junction indices derived from MAIN_SEGMENTS order:
#   J0 = seg_2_before start
#   J1 = seg_1_before start
#   J2 = seg_0_before start
#   J3 = seg_0_after  start  ← merge junction (ramp_on_merge → seg_0_after)
#   J4 = seg_1_after  start
#   J5 = seg_1_after  end
MERGE_JUNCTION_IDX = 3   # index into MAIN_SEGMENTS where seg_0_after begins

LANE_COUNT = 3   # lanes on every main-road edge
LANE_WIDTH = 3.2  # m
MAIN_SPEED = 33.33  # m/s ≈ 120 km/h
Y_BASE = 60.0       # base Y for main road centreline


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _lane_y_offset(lane_idx: int, lane_count: int) -> float:
    """Centre-based y-offset for lane `lane_idx` out of `lane_count`."""
    return (lane_idx - (lane_count - 1) / 2) * LANE_WIDTH


def _build_junctions() -> dict:
    """Compute X,Y positions of all network junctions."""
    junctions = {}
    x = -3000.0   # start upstream (keeps network coords tidy)

    # Main-road junctions J0 … J5
    for i, seg_id in enumerate(MAIN_SEGMENTS):
        j_id = f'J{i}'
        junctions[j_id] = {'x': x, 'y': Y_BASE, 'type': 'priority'}
        x += SEGMENT_LENGTHS[seg_id] * SHAPE_MULTIPLIERS[seg_id]

    # Final downstream junction
    junctions[f'J{len(MAIN_SEGMENTS)}'] = {'x': x, 'y': Y_BASE, 'type': 'dead_end'}

    # Merge junction reference
    merge_x = junctions[f'J{MERGE_JUNCTION_IDX}']['x']
    merge_y = Y_BASE + _lane_y_offset(0, LANE_COUNT)   # rightmost lane y

    # On-ramp: three junctions placed upstream of the merge point
    total_ramp = (SEGMENT_LENGTHS['ramp_on_approach'] +
                  SEGMENT_LENGTHS['ramp_on_transition'] +
                  SEGMENT_LENGTHS['ramp_on_merge'])
    ramp_start_y = Y_BASE + RAMP_Y_OFFSET

    # Mirror off-ramp geometry to get a smooth arch shape
    # (same logic as in v4 generator, but off-ramp is absent here)
    off_mid1_p = SEGMENT_LENGTHS['ramp_on_merge'] / total_ramp
    off_mid2_p = (SEGMENT_LENGTHS['ramp_on_merge'] +
                  SEGMENT_LENGTHS['ramp_on_transition']) / total_ramp
    off_mid1_y = merge_y + (ramp_start_y - merge_y) * off_mid1_p * RAMP_PROXIMITY_FACTOR
    off_mid2_y = merge_y + (ramp_start_y - merge_y) * off_mid2_p * RAMP_PROXIMITY_FACTOR

    on_mid1_y = off_mid2_y
    on_mid2_y = off_mid1_y

    junctions['J_ramp_on_start'] = {
        'x': merge_x - total_ramp,
        'y': ramp_start_y,
        'type': 'dead_end',
    }
    junctions['J_ramp_on_mid1'] = {
        'x': merge_x - SEGMENT_LENGTHS['ramp_on_transition'] - SEGMENT_LENGTHS['ramp_on_merge'],
        'y': on_mid1_y,
        'type': 'priority',
    }
    junctions['J_ramp_on_mid2'] = {
        'x': merge_x - SEGMENT_LENGTHS['ramp_on_merge'],
        'y': on_mid2_y,
        'type': 'priority',
    }

    return junctions, merge_y


# ---------------------------------------------------------------------------
# Network builder
# ---------------------------------------------------------------------------

def create_network() -> ET.Element:
    root = ET.Element('net')
    root.set('version', '1.21.0')
    root.set('junctionCornerDetail', '5')
    root.set('limitTurnSpeed', '5.50')
    root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
    root.set('xsi:noNamespaceSchemaLocation',
             'http://sumo.dlr.de/xsd/net_file.xsd')

    loc = ET.SubElement(root, 'location')
    loc.set('netOffset', '0.00,0.00')
    loc.set('convBoundary', '-3500.00,30.00,2000.00,80.00')
    loc.set('origBoundary', '-10000000000.00,-10000000000.00,10000000000.00,10000000000.00')
    loc.set('projParameter', '!')

    junctions, merge_lane0_y = _build_junctions()

    # ------------------------------------------------------------------
    # Junction elements
    # ------------------------------------------------------------------
    for j_id, j in junctions.items():
        el = ET.SubElement(root, 'junction')
        el.set('id', j_id)
        el.set('type', j['type'])
        el.set('x', f"{j['x']:.2f}")
        el.set('y', f"{j['y']:.2f}")
        el.set('incLanes', '')
        el.set('intLanes', '')
        el.set('shape', '')

    # ------------------------------------------------------------------
    # Main-road edges
    # ------------------------------------------------------------------
    for i, seg_id in enumerate(MAIN_SEGMENTS):
        from_j = junctions[f'J{i}']
        to_j = junctions[f'J{i + 1}']

        edge = ET.SubElement(root, 'edge')
        edge.set('id', seg_id)
        edge.set('from', f'J{i}')
        edge.set('to', f'J{i + 1}')
        edge.set('priority', '-1')
        edge.set('length', str(SEGMENT_LENGTHS[seg_id]))

        for lane_idx in range(LANE_COUNT):
            y_off = _lane_y_offset(lane_idx, LANE_COUNT)
            lane = ET.SubElement(edge, 'lane')
            lane.set('id', f'{seg_id}_{lane_idx}')
            lane.set('index', str(lane_idx))
            lane.set('speed', str(MAIN_SPEED))
            lane.set('length', str(SEGMENT_LENGTHS[seg_id]))
            lane.set('shape', (
                f"{from_j['x']:.2f},{from_j['y'] + y_off:.2f} "
                f"{to_j['x']:.2f},{to_j['y'] + y_off:.2f}"
            ))

    # ------------------------------------------------------------------
    # On-ramp edges
    # ------------------------------------------------------------------
    ramp_edges = [
        ('ramp_on_approach',   'J_ramp_on_start', 'J_ramp_on_mid1'),
        ('ramp_on_transition', 'J_ramp_on_mid1',  'J_ramp_on_mid2'),
        ('ramp_on_merge',      'J_ramp_on_mid2',  f'J{MERGE_JUNCTION_IDX}'),
    ]
    for edge_id, from_id, to_id in ramp_edges:
        from_j = junctions[from_id]
        to_j = junctions[to_id]
        # For ramp_on_merge, the lane endpoint touches the mainline lane-0 y
        end_y = merge_lane0_y if edge_id == 'ramp_on_merge' else to_j['y']

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
        lane.set('shape', (
            f"{from_j['x']:.2f},{from_j['y']:.2f} "
            f"{to_j['x']:.2f},{end_y:.2f}"
        ))

    # ------------------------------------------------------------------
    # Connections — main road
    # ------------------------------------------------------------------
    for i in range(len(MAIN_SEGMENTS) - 1):
        from_edge = MAIN_SEGMENTS[i]
        to_edge = MAIN_SEGMENTS[i + 1]
        for lane_idx in range(LANE_COUNT):
            conn = ET.SubElement(root, 'connection')
            conn.set('from', from_edge)
            conn.set('to', to_edge)
            conn.set('fromLane', str(lane_idx))
            conn.set('toLane', str(lane_idx))
            conn.set('dir', 's')
            conn.set('state', 'M')

    # Connections — on-ramp internal
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

    # Connection — ramp merge into seg_0_after lane 0 (yielding)
    conn = ET.SubElement(root, 'connection')
    conn.set('from', 'ramp_on_merge')
    conn.set('to', 'seg_0_after')
    conn.set('fromLane', '0')
    conn.set('toLane', '0')
    conn.set('dir', 's')
    conn.set('state', 'm')   # lowercase = yield

    return root


# ---------------------------------------------------------------------------
# XML formatting
# ---------------------------------------------------------------------------

def prettify_xml(elem: ET.Element) -> bytes:
    raw = ET.tostring(elem, encoding='unicode')
    return minidom.parseString(raw).toprettyxml(indent='    ', encoding='UTF-8')


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description='Generate the ramp_on_v0 SUMO network (3-lane mainline + on-ramp, no off-ramp).'
    )
    parser.add_argument(
        '-o', '--output',
        default='ramp_on_v0.net.xml',
        help='Output file name (default: ramp_on_v0.net.xml)',
    )
    args = parser.parse_args()

    root = create_network()

    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), args.output)
    with open(output_path, 'wb') as f:
        f.write(prettify_xml(root))

    print(f'Network written to: {output_path}')
    print()
    print('Topology:')
    for seg_id in MAIN_SEGMENTS:
        print(f'  {seg_id}: {int(SEGMENT_LENGTHS[seg_id])}m, {LANE_COUNT} lanes')
    print('  ramp_on_approach → ramp_on_transition → ramp_on_merge → seg_0_after lane 0')
    print()
    print('⚠  Open in netedit and run Processing → Compute Junctions before using in simulation.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
