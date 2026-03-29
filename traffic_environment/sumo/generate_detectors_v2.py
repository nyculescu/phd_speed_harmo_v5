#!/usr/bin/env python3
"""
Generate detectors_ramps_v2.add.xml for the ramps_v2 network.

E1 induction loops: entry/mid/exit × all lanes for every segment.
E3 multi-entry-exit zones: one per segment + one corridor-wide.

Changes from v1:
  - seg_0_after: 4 lanes (3 through + 1 acceleration lane)
  - No off-ramp segments
  - Corridor E3 exits only at seg_1_after (no ramp_off_departure)
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
import os

FREQ = "30"

SEGMENTS = {
    "seg_3_before":        (1000.0, 3),
    "seg_2_before":        (1000.0, 3),
    "seg_1_before":        (1000.0, 3),
    "seg_0_before":        (1000.0, 3),
    "seg_0_after":          (250.0, 4),   # 3 through + 1 accel lane (L0)
    "seg_1_after":         (1000.0, 3),
    "ramp_on_approach":     (700.0, 1),
    "ramp_on_transition":   (200.0, 1),
    "ramp_on_merge":        (100.0, 1),
    # No ramp_off_* segments
}

POS_FRACS = {"entry": 0.05, "mid": 0.50, "exit": 0.95}


def generate():
    root = ET.Element("additional")

    # --- E1 induction loops ---
    for seg, (length, n_lanes) in SEGMENTS.items():
        for pos_name, frac in POS_FRACS.items():
            pos = round(length * frac, 2)
            for lane_idx in range(n_lanes):
                det_id = f"flow_loop_{seg}_{lane_idx}_{pos_name}"
                lane_id = f"{seg}_{lane_idx}"
                e1 = ET.SubElement(root, "inductionLoop")
                e1.set("id", det_id)
                e1.set("lane", lane_id)
                e1.set("pos", str(pos))
                e1.set("freq", FREQ)
                e1.set("file", "NUL")

    # --- E3 multi-entry-exit zones ---
    for seg, (length, n_lanes) in SEGMENTS.items():
        e3 = ET.SubElement(root, "entryExitDetector")
        e3.set("id", f"e3_{seg}")
        e3.set("freq", FREQ)
        e3.set("file", "NUL")
        entry_pos = round(length * 0.02, 2)
        exit_pos = round(length * 0.98, 2)
        for lane_idx in range(n_lanes):
            lane_id = f"{seg}_{lane_idx}"
            de = ET.SubElement(e3, "detEntry")
            de.set("lane", lane_id)
            de.set("pos", str(entry_pos))
            dx = ET.SubElement(e3, "detExit")
            dx.set("lane", lane_id)
            dx.set("pos", str(exit_pos))

    # Corridor E3
    e3_corr = ET.SubElement(root, "entryExitDetector")
    e3_corr.set("id", "e3_corridor")
    e3_corr.set("freq", FREQ)
    e3_corr.set("file", "NUL")

    seg3_len = SEGMENTS["seg_3_before"][0]
    for lane_idx in range(SEGMENTS["seg_3_before"][1]):
        de = ET.SubElement(e3_corr, "detEntry")
        de.set("lane", f"seg_3_before_{lane_idx}")
        de.set("pos", str(round(seg3_len * 0.02, 2)))
    de = ET.SubElement(e3_corr, "detEntry")
    de.set("lane", "ramp_on_approach_0")
    de.set("pos", str(round(SEGMENTS["ramp_on_approach"][0] * 0.02, 2)))

    seg1a_len = SEGMENTS["seg_1_after"][0]
    for lane_idx in range(SEGMENTS["seg_1_after"][1]):
        dx = ET.SubElement(e3_corr, "detExit")
        dx.set("lane", f"seg_1_after_{lane_idx}")
        dx.set("pos", str(round(seg1a_len * 0.98, 2)))

    return root


def main():
    root = generate()
    rough = ET.tostring(root, encoding="unicode")
    reparsed = minidom.parseString(rough)
    pretty = reparsed.toprettyxml(indent="    ", encoding="UTF-8")

    output_path = os.path.join(os.path.dirname(__file__), "detectors_ramps_v2.add.xml")
    with open(output_path, "wb") as f:
        f.write(pretty)

    e1_count = len(root.findall("inductionLoop"))
    e3_count = len(root.findall("entryExitDetector"))
    print(f"Detectors saved to: detectors_ramps_v2.add.xml")
    print(f"  E1 induction loops: {e1_count}")
    print(f"  E3 multi-entry-exit: {e3_count}")


if __name__ == "__main__":
    main()
