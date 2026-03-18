#!/usr/bin/env python3
"""
generate_ramp_network.py
SUMO network generator for the ramps_v0 topology.

Topology:
    seg_2_before (3L, 1000m)
    → seg_1_before (3L, 1000m)
    → seg_0_before (3L, 1000m)
    → seg_0_after  (4L,  250m)   ← weaving/merge buffer (extra lane from on-ramp)
    → seg_1_after  (3L, 1000m)

    ramp_on_approach (1L, 300m) → ramp_on_transition (1L, 100m) → ramp_on_merge (1L, 100m)
        merges into seg_0_after LANE 0 at J3.
        seg_0_before lanes 0–2 connect to seg_0_after lanes 1–3.

    seg_0_after LANE 0 → ramp_off_diverge (1L, 100m) → ramp_off_transition (1L, 100m)
        → ramp_off_departure (1L, 300m)
        diverges at J4 (start of seg_1_after).
        seg_0_after lanes 1–3 connect to seg_1_after lanes 0–2.

    Weaving distance (merge → diverge): 250 m (seg_0_after).

Lane numbering convention:
    Lane 0  = rightmost (shoulder) lane
    Lane N-1 = leftmost (fast) lane

Connection logic:
    seg_0_before → seg_0_after : fromLane k → toLane k+1  (shift up; lane 0 freed for ramp weave)
    seg_0_after  → seg_1_after : fromLane k+1 → toLane k  (shift down; lane 0 drops to off-ramp)

Usage:
    python3 generate_ramp_network.py          # writes ramps_v0.net.xml
    python3 generate_ramp_network.py -o foo.net.xml

⚠  After generation, open in netedit → Processing → Compute Junctions.
"""

import os
import argparse
import xml.etree.ElementTree as ET
from xml.dom import minidom

# ---------------------------------------------------------------------------
# Ramp geometry constants
# ---------------------------------------------------------------------------
RAMP_Y_OFFSET = -20.0        # Y-offset for ramps below main road (m)
RAMP_SPEED = 25.0            # m/s = 90 km/h
RAMP_PROXIMITY_FACTOR = 0.7  # controls how close ramp arches toward main road

# ---------------------------------------------------------------------------
# Segment lengths
# ---------------------------------------------------------------------------
SEGMENT_LENGTHS = {
    'seg_2_before':        1000.0,
    'seg_1_before':        1000.0,
    'seg_0_before':        1000.0,
    'seg_0_after':          250.0,
    'seg_1_after':         1000.0,
    'ramp_on_approach':     300.0,
    'ramp_on_transition':   100.0,
    'ramp_on_merge':        100.0,
    'ramp_off_diverge':     100.0,
    'ramp_off_transition':  100.0,
    'ramp_off_departure':   300.0,
}

# Visual shape multipliers (reduce visual crowding for long segments)
SHAPE_MULTIPLIERS = {
    'seg_2_before':        0.5,
    'seg_1_before':        0.5,
    'seg_0_before':        1.0,
    'seg_0_after':         1.0,
    'seg_1_after':         0.5,
    'ramp_on_approach':    1.0,
    'ramp_on_transition':  1.0,
    'ramp_on_merge':       1.0,
    'ramp_off_diverge':    1.0,
    'ramp_off_transition': 1.0,
    'ramp_off_departure':  1.0,
}

MAIN_SEGMENTS = [
    'seg_2_before',    # J0 → J1
    'seg_1_before',    # J1 → J2
    'seg_0_before',    # J2 → J3  (merge junction)
    'seg_0_after',     # J3 → J4  (diverge junction)
    'seg_1_after',     # J4 → J5
]

MERGE_JUNCTION_IDX   = 3   # J3: end of seg_0_before / start of seg_0_after
DIVERGE_JUNCTION_IDX = 4   # J4: end of seg_0_after  / start of seg_1_after

LANES_BEFORE  = 3   # lanes on seg_*_before and seg_1_after
LANES_BUFFER  = 4   # lanes on seg_0_after (extra ramp weaving lane)
LANES_AFTER   = 3   # lanes on seg_1_after
LANE_WIDTH = 3.2    # m
MAIN_SPEED = 33.33  # m/s ≈ 120 km/h
Y_BASE = 60.0       # base Y of main road centreline


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _lane_count(seg_id: str) -> int:
    if seg_id == 'seg_0_after':
        return LANES_BUFFER
    if seg_id == 'seg_1_after':
        return LANES_AFTER
    return LANES_BEFORE


def _lane_y_offset(seg_id: str, lane_idx: int, lane_count: int) -> float:
    """Y-offset for lane in segment.

    For seg_0_after (4-lane buffer): keep original 3-lane mainline aligned on
    lanes 1–3 and place the extra weaving lane as lane 0 (rightmost).
    This preserves visual alignment with upstream/downstream 3-lane sections.
    """
    if seg_id == 'seg_0_after' and lane_count == LANES_BUFFER:
        return (lane_idx - 2) * LANE_WIDTH   # lanes 1–3 align with 3-lane mainline
    return (lane_idx - (lane_count - 1) / 2) * LANE_WIDTH


def _build_junctions() -> tuple:
    """Return (junctions dict, merge_lane0_y, diverge_lane0_y)."""
    junctions = {}
    x = -3000.0

    for i, seg_id in enumerate(MAIN_SEGMENTS):
        junctions[f'J{i}'] = {'x': x, 'y': Y_BASE, 'type': 'priority'}
        x += SEGMENT_LENGTHS[seg_id] * SHAPE_MULTIPLIERS[seg_id]
    junctions[f'J{len(MAIN_SEGMENTS)}'] = {'x': x, 'y': Y_BASE, 'type': 'dead_end'}

    # Y position of lane 0 (rightmost) in the 4-lane buffer zone at the merge junction
    merge_lane0_y   = Y_BASE + _lane_y_offset('seg_0_after', 0, LANES_BUFFER)
    diverge_lane0_y = merge_lane0_y   # same geometry

    merge_x   = junctions[f'J{MERGE_JUNCTION_IDX}']['x']
    diverge_x = junctions[f'J{DIVERGE_JUNCTION_IDX}']['x']

    ramp_start_y = Y_BASE + RAMP_Y_OFFSET

    # Off-ramp arch waypoints (computed first; on-ramp mirrors reversed)
    off_total = (SEGMENT_LENGTHS['ramp_off_diverge'] +
                 SEGMENT_LENGTHS['ramp_off_transition'] +
                 SEGMENT_LENGTHS['ramp_off_departure'])
    p1 = SEGMENT_LENGTHS['ramp_off_diverge'] / off_total
    p2 = (SEGMENT_LENGTHS['ramp_off_diverge'] +
          SEGMENT_LENGTHS['ramp_off_transition']) / off_total
    off_mid1_y = diverge_lane0_y + (ramp_start_y - diverge_lane0_y) * p1 * RAMP_PROXIMITY_FACTOR
    off_mid2_y = diverge_lane0_y + (ramp_start_y - diverge_lane0_y) * p2 * RAMP_PROXIMITY_FACTOR

    # On-ramp: mirror off-ramp geometry (reversed along x)
    on_mid1_y = off_mid2_y
    on_mid2_y = off_mid1_y
    total_on_ramp = (SEGMENT_LENGTHS['ramp_on_approach'] +
                     SEGMENT_LENGTHS['ramp_on_transition'] +
                     SEGMENT_LENGTHS['ramp_on_merge'])

    # On-ramp junctions
    junctions['J_ramp_on_start'] = {
        'x': merge_x - total_on_ramp, 'y': ramp_start_y, 'type': 'dead_end',
    }
    junctions['J_ramp_on_mid1'] = {
        'x': merge_x - SEGMENT_LENGTHS['ramp_on_transition'] - SEGMENT_LENGTHS['ramp_on_merge'],
        'y': on_mid1_y, 'type': 'priority',
    }
    junctions['J_ramp_on_mid2'] = {
        'x': merge_x - SEGMENT_LENGTHS['ramp_on_merge'],
        'y': on_mid2_y, 'type': 'priority',
    }

    # Off-ramp junctions
    junctions['J_ramp_off_mid1'] = {
        'x': diverge_x + SEGMENT_LENGTHS['ramp_off_diverge'],
        'y': off_mid1_y, 'type': 'priority',
    }
    junctions['J_ramp_off_mid2'] = {
        'x': diverge_x + SEGMENT_LENGTHS['ramp_off_diverge'] + SEGMENT_LENGTHS['ramp_off_transition'],
        'y': off_mid2_y, 'type': 'priority',
    }
    junctions['J_ramp_off_end'] = {
        'x': diverge_x + off_total, 'y': ramp_start_y, 'type': 'dead_end',
    }

    return junctions, merge_lane0_y, diverge_lane0_y


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
    loc.set('convBoundary', '-3500.00,20.00,2500.00,80.00')
    loc.set('origBoundary', '-10000000000.00,-10000000000.00,10000000000.00,10000000000.00')
    loc.set('projParameter', '!')

    junctions, merge_lane0_y, diverge_lane0_y = _build_junctions()

    # ---- Junctions ----
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
    on_ramp_defs = [
        ('ramp_on_approach',   'J_ramp_on_start', 'J_ramp_on_mid1', None,          None),
        ('ramp_on_transition', 'J_ramp_on_mid1',  'J_ramp_on_mid2', None,          None),
        ('ramp_on_merge',      'J_ramp_on_mid2',  f'J{MERGE_JUNCTION_IDX}',  None, merge_lane0_y),
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
    for i in range(len(MAIN_SEGMENTS) - 1):
        from_seg = MAIN_SEGMENTS[i]
        to_seg   = MAIN_SEGMENTS[i + 1]
        from_cnt = _lane_count(from_seg)
        to_cnt   = _lane_count(to_seg)

        if from_seg == 'seg_0_before' and to_seg == 'seg_0_after':
            # Lane ADDITION at merge: shift mainline lanes up by 1 to free lane 0 for ramp
            # seg_0_before lane k → seg_0_after lane k+1
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
            # Lane DROP at diverge: lanes 1–3 shift back down to 0–2
            # seg_0_after lane k+1 → seg_1_after lane k  (lane 0 goes to off-ramp)
            for k in range(to_cnt):
                conn = ET.SubElement(root, 'connection')
                conn.set('from', from_seg)
                conn.set('to', to_seg)
                conn.set('fromLane', str(k + 1))
                conn.set('toLane', str(k))
                conn.set('dir', 's')
                conn.set('state', 'M')
            continue

        # Standard same-lane-count connection
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

    # ramp_on_merge → seg_0_after lane 0 (yield — merging traffic)
    conn = ET.SubElement(root, 'connection')
    conn.set('from', 'ramp_on_merge')
    conn.set('to', 'seg_0_after')
    conn.set('fromLane', '0')
    conn.set('toLane', '0')
    conn.set('dir', 's')
    conn.set('state', 'm')   # lowercase = yield

    # seg_0_after lane 0 → ramp_off_diverge (right exit)
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
    raw = ET.tostring(elem, encoding='unicode')
    return minidom.parseString(raw).toprettyxml(indent='    ', encoding='UTF-8')


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            'Generate the ramps_v0 SUMO network '
            '(3L mainline → 4L weaving buffer → 3L downstream, on-ramp + off-ramp).'
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
    print(f'  Upstream:  seg_2_before → seg_1_before → seg_0_before  [{LANES_BEFORE} lanes, 1000m each]')
    print(f'  Buffer:    seg_0_after                                   [{LANES_BUFFER} lanes, {int(SEGMENT_LENGTHS["seg_0_after"])}m — weaving zone]')
    print(f'  Downstream:seg_1_after                                   [{LANES_AFTER} lanes, 1000m]')
    print(f'  On-ramp:   approach({int(SEGMENT_LENGTHS["ramp_on_approach"])}m) → transition({int(SEGMENT_LENGTHS["ramp_on_transition"])}m) → merge({int(SEGMENT_LENGTHS["ramp_on_merge"])}m) → seg_0_after lane 0')
    print(f'  Off-ramp:  seg_0_after lane 0 → diverge({int(SEGMENT_LENGTHS["ramp_off_diverge"])}m) → transition({int(SEGMENT_LENGTHS["ramp_off_transition"])}m) → departure({int(SEGMENT_LENGTHS["ramp_off_departure"])}m)')
    print(f'  Lane shift: seg_0_before k → seg_0_after k+1  (lane 0 freed for ramp weave)')
    print(f'  Lane drop:  seg_0_after k+1 → seg_1_after k   (lane 0 absorbed by off-ramp)')
    print()
    print('⚠  Open in netedit → Processing → Compute Junctions before using in simulation.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
