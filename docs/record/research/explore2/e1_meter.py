"""E1 (V434): safety at step resolution, read from the same run at 0.1 s and at 1 Hz.

Per vehicle and step: TTC = gap / (v - v_lead) while closing on a leader within 200 m;
DRAC = (v - v_lead)^2 / (2 gap) while closing. Measures, in vehicle-seconds:
  ttc3      TTC < 3 s (the close-following of the existing metrics)
  drac3/7   DRAC > 3 / 7 m/s^2
  brake3/7  acceleration <= -3 / -7 m/s^2
plus brake events (onsets of brake3/7 per vehicle, at 0.1 s only).
The 1-Hz reading uses only the steps on the whole second, as the existing metrics do.
The meter only reads values handed to it; `read_libsumo` uses getters only, so it cannot change the run.
"""
import math

THRESH = {"ttc3": 3.0, "drac3": 3.0, "drac7": 7.0, "brake3": -3.0, "brake7": -7.0}
LEADER_RANGE = 200.0


def flags(v, a, gap, v_lead):
    """Which measures one vehicle meets in one step; gap/v_lead are None without a leader."""
    out = {"brake3": a <= THRESH["brake3"], "brake7": a <= THRESH["brake7"],
           "ttc3": False, "drac3": False, "drac7": False}
    if gap is not None and v_lead is not None and v > v_lead:
        g = max(gap, 1e-3)
        dv = v - v_lead
        out["ttc3"] = g / dv < THRESH["ttc3"]
        drac = dv * dv / (2 * g)
        out["drac3"] = drac > THRESH["drac3"]
        out["drac7"] = drac > THRESH["drac7"]
    return out


class SafetyMeter:
    def __init__(self, dt=0.1):
        self.dt = dt
        self.per_s = round(1 / dt)
        self.k = 0
        self.fine = dict.fromkeys(THRESH, 0.0)
        self.hz1 = dict.fromkeys(THRESH, 0.0)
        self.events = {"brake3": 0, "brake7": 0}
        self._braking = {"brake3": set(), "brake7": set()}

    def step(self, vehicles):
        """vehicles: iterable of (id, speed, accel, gap or None, leader speed or None) for one step."""
        on_second = self.k % self.per_s == 0
        now = {"brake3": set(), "brake7": set()}
        for vid, v, a, gap, vl in vehicles:
            f = flags(v, a, gap, vl)
            for m, hit in f.items():
                if hit:
                    self.fine[m] += self.dt
                    if on_second:
                        self.hz1[m] += 1.0
            for m in now:
                if f[m]:
                    now[m].add(vid)
        for m in now:
            self.events[m] += len(now[m] - self._braking[m])
        self._braking = now
        self.k += 1

    def result(self):
        missed = {m: (None if self.fine[m] == 0 else 1 - self.hz1[m] / self.fine[m]) for m in THRESH}
        return {"fine_vs": self.fine, "hz1_vs": self.hz1, "missed_share": missed,
                "brake_events": self.events, "steps": self.k}


def read_libsumo(ls):
    """One step's tuples from libsumo, getters only."""
    out = []
    for vid in ls.vehicle.getIDList():
        lead = ls.vehicle.getLeader(vid, LEADER_RANGE)
        if lead and lead[0]:
            gap, vl = lead[1], ls.vehicle.getSpeed(lead[0])
        else:
            gap, vl = None, None
        out.append((vid, ls.vehicle.getSpeed(vid), ls.vehicle.getAcceleration(vid), gap, vl))
    return out


if __name__ == "__main__":
    assert math.isclose(SafetyMeter().dt, 0.1)
