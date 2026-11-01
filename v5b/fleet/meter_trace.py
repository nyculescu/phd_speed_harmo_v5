"""E1 stage-0 diagnostic (V230, throw-away seeds, report-only): per-second trace of the meter for the T0 braking.

Same arguments as `day one`; writes <out>.trace.jsonl next to the day file. Rows, every whole second:
  ["s", t, state, owed, amber length, kinematic ambers so far]: the meter after the step;
  ["v", t, vid, distance to the line, speed, accel, leader, gap]: each vehicle on r_0.
The trace only reads state, so the day file must match the untraced run of the same job."""

import json
import sys
from pathlib import Path

import libsumo as ls

from v5b.fleet import control as ct
from v5b.fleet import day


def main(argv: list) -> int:
    out = Path(argv[argv.index("--out") + 1])
    rows = []
    step = ct.SumoMeter.step

    def traced(self, t: float) -> None:
        step(self, t)
        m = self.m
        rows.append(["s", round(t), m.state, round(m.target - m.released, 3), m.amber, m.n["amber_kin"]])
        for v in ls.lane.getLastStepVehicleIDs(self.lane):
            lead = ls.vehicle.getLeader(v, 200.0)
            rows.append(["v", round(t), v, round(self.len - ls.vehicle.getLanePosition(v), 1),
                         round(ls.vehicle.getSpeed(v), 2), round(ls.vehicle.getAcceleration(v), 2),
                         lead[0] if lead else None, round(lead[1], 1) if lead and lead[0] else None])

    ct.SumoMeter.step = traced
    rc = day.main(["one"] + argv)
    tmp = out.with_suffix(".trace.tmp")
    tmp.write_text("".join(json.dumps(r) + "\n" for r in rows))
    tmp.replace(out.with_suffix(".trace.jsonl"))
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
