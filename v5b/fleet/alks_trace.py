"""E1 stage-0 diagnostic (V224, throw-away seeds, report-only): per-second traces of the T0 ALKS checks (§10.3).

Same arguments as `day one`; writes <out>.trace.jsonl next to the day file. Rows:
  ["h", t, vid, x, lane, speed, accel, maxSpeed, allowed, gap, c]: commanded ALKS in the held stretch, no leader
      within 120 m (gap None = none within 200 m);
  ["r", t, vid, dist, road, lane, speed/desired, accel, gap, gap_at_release]: a released ALKS over the 300 m after
      its release.
The trace only reads vehicle state, so the day file must match the untraced run of the same job."""

import json
import sys
from pathlib import Path

import libsumo as ls

from v5b.fleet import control as ct
from v5b.fleet import day

SPAN = 300.0


def _gap(v: str) -> float | None:
    lead = ls.vehicle.getLeader(v, 200.0)
    return round(lead[1], 1) if lead and lead[0] else None


def main(argv: list) -> int:
    out = Path(argv[argv.index("--out") + 1])
    rows, rel = [], {}
    step = ct.SumoALKS.step

    def traced(self, t: float) -> None:
        own0 = set(self.own)
        step(self, t)
        for v in own0 - set(self.own):
            if v in self.desired and not self.blocked(v):
                try:
                    rel[v] = (ls.vehicle.getDistance(v), _gap(v))
                except ls.TraCIException:
                    pass
        if abs(t - round(t)) > 1e-6:
            return
        c = round(self.law.b * ct.V_ALKS, 3)
        for v in self.own:
            x = ls.vehicle.getLanePosition(v)
            g = _gap(v)
            if x < self.x_hold or (g is not None and g <= ct.FREE_GAP):
                continue
            rows.append(["h", round(t), v, round(x, 1), ls.vehicle.getLaneIndex(v), round(ls.vehicle.getSpeed(v), 3),
                         round(ls.vehicle.getAcceleration(v), 3), round(ls.vehicle.getMaxSpeed(v), 3),
                         round(ls.vehicle.getAllowedSpeed(v), 3), g, c])
        for v, (d0, g0) in list(rel.items()):
            try:
                d = ls.vehicle.getDistance(v) - d0
                if d > SPAN:
                    rel.pop(v)
                    continue
                rows.append(["r", round(t), v, round(d, 1), ls.vehicle.getRoadID(v), ls.vehicle.getLaneIndex(v),
                             round(ls.vehicle.getSpeed(v) / self.desired[v], 3),
                             round(ls.vehicle.getAcceleration(v), 3), _gap(v), g0])
            except ls.TraCIException:
                rel.pop(v)

    ct.SumoALKS.step = traced
    rc = day.main(["one"] + argv)
    tmp = out.with_suffix(".trace.tmp")
    tmp.write_text("".join(json.dumps(r) + "\n" for r in rows))
    tmp.replace(out.with_suffix(".trace.jsonl"))
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
