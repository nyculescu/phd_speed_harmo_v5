"""Meter signal clock shared by the D1/D2 FBMeter (v5b/d1/episode.py) and the P1 meters (v5b/p1/meters.py).

Two rules (P1 addendum 2026-10-19 R3; bug found V100):
  'd2'         (legacy; D1 a23613b and D2 72ba8f2 ran with it) green iff (t - t_cycle0) mod c(q) < green with the
               CURRENT cycle c. When q changes the phase jumps, so greens can be skipped and a red can exceed
               c(q_min) - green (P1 smoke: 322 s).
  'continuous' green iff (t - g) mod c(q) < green, where g, the anchor, is the start of the last green: when c changes,
               the time since that green start carries over (a new green starts at once if it already reaches the
               new c). With a constant c both rules give the same signal; a red is at most c(q_min) - green.
"""
from __future__ import annotations

SIGNALS = ("d2", "continuous")
LEGACY = "d2"


class SignalClock:
    def __init__(self, signal: str):
        if signal not in SIGNALS:
            raise ValueError(f"meter signal must be one of {SIGNALS}: {signal!r}")
        self.signal = signal
        self.anchor = self.anchor_c = None

    def phase(self, t: float, t_cycle0: float, c: float) -> float:
        """Time into the current cycle at t (green iff < green)."""
        if self.signal == "d2":
            return (t - t_cycle0) % c
        if self.anchor is None:
            self.anchor, self.anchor_c = t_cycle0, c
        elif c != self.anchor_c:
            since = (t - self.anchor) % self.anchor_c      # time since the last green start
            self.anchor = t - since if since < c - 1e-9 else t
            self.anchor_c = c
        return (t - self.anchor) % c
