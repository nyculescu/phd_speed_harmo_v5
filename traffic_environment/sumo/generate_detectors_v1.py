#!/usr/bin/env python3
"""
Generate detectors_ramps_v1.add.xml for the ramps_v1 network.

E1 induction loops: entry/mid/exit × all lanes for every segment.
E3 multi-entry-exit zones: one per segment + one corridor-wide.
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
import os

FREQ = "30"  # aggregation period in seconds

# Segment → (length_m, num_lanes)
SEGMENTS = {
    "seg_3_before":        (1000.0, 3),
    "seg_2_before":        (1000.0, 3),
    "seg_1_before":        (1000.0, 3),
    "seg_0_before":        (1000.0, 3),
    "seg_0_after":          (500.0, 4),
    "seg_1_after":         (1000.0, 3),
    "ramp_on_approach":     (700.0, 1),
    "ramp_on_transition":   (200.0, 1),
    "ramp_on_merge":        (100.0, 1),
    "ramp_off_diverge":     (100.0, 1),
    "ramp_off_transition":  (200.0, 1),
    "ramp_off_departure":   (700.0, 1),
}

# Position fractions for entry/mid/exit
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
    # Per-segment E3 detectors
    for seg, (length, n_lanes) in SEGMENTS.items():
        e3_id = f"e3_{seg}"
        e3 = ET.SubElement(root, "entryExitDetector")
        e3.set("id", e3_id)
        e3.set("freq", FREQ)
        e3.set("file", "NUL")
        entry_pos = round(length * 0.02, 2)
        exit_pos = round(length * 0.98, 2)
        for lane_idx in range(n_lanes):
            lane_id = f"{seg}_{lane_idx}"
            det_entry = ET.SubElement(e3, "detEntry")
            det_entry.set("lane", lane_id)
            det_entry.set("pos", str(entry_pos))
            det_exit = ET.SubElement(e3, "detExit")
            det_exit.set("lane", lane_id)
            det_exit.set("pos", str(exit_pos))

    # Corridor E3: entry at seg_3_before + ramp_on_approach,
    #              exit at seg_1_after + ramp_off_departure
    e3_corr = ET.SubElement(root, "entryExitDetector")
    e3_corr.set("id", "e3_corridor")
    e3_corr.set("freq", FREQ)
    e3_corr.set("file", "NUL")

    # Entries
    seg3_len = SEGMENTS["seg_3_before"][0]
    for lane_idx in range(SEGMENTS["seg_3_before"][1]):
        de = ET.SubElement(e3_corr, "detEntry")
        de.set("lane", f"seg_3_before_{lane_idx}")
        de.set("pos", str(round(seg3_len * 0.02, 2)))
    ramp_app_len = SEGMENTS["ramp_on_approach"][0]
    de = ET.SubElement(e3_corr, "detEntry")
    de.set("lane", "ramp_on_approach_0")
    de.set("pos", str(round(ramp_app_len * 0.02, 2)))

    # Exits
    seg1a_len = SEGMENTS["seg_1_after"][0]
    for lane_idx in range(SEGMENTS["seg_1_after"][1]):
        dx = ET.SubElement(e3_corr, "detExit")
        dx.set("lane", f"seg_1_after_{lane_idx}")
        dx.set("pos", str(round(seg1a_len * 0.98, 2)))
    ramp_dep_len = SEGMENTS["ramp_off_departure"][0]
    dx = ET.SubElement(e3_corr, "detExit")
    dx.set("lane", "ramp_off_departure_0")
    dx.set("pos", str(round(ramp_dep_len * 0.98, 2)))

    return root


def main():
    root = generate()
    rough = ET.tostring(root, encoding="unicode")
    reparsed = minidom.parseString(rough)
    pretty = reparsed.toprettyxml(indent="    ", encoding="UTF-8")

    output_path = os.path.join(os.path.dirname(__file__), "detectors_ramps_v1.add.xml")
    with open(output_path, "wb") as f:
        f.write(pretty)

    # Count detectors
    e1_count = len(root.findall("inductionLoop"))
    e3_count = len(root.findall("entryExitDetector"))
    print(f"Detectors saved to: detectors_ramps_v1.add.xml")
    print(f"  E1 induction loops: {e1_count}")
    print(f"  E3 multi-entry-exit: {e3_count}")


if __name__ == "__main__":
    main()
