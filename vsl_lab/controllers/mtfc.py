"""Mainstream traffic flow control (MTFC) via VSL: Carlson, Papamichail, Papageorgiou et al., local feedback cascade.

Implemented from Carlson et al., Transportes 21(3):56-65 (2013), Sec. 3.2 (read in full; equations checked):
  secondary (inner, I):  b(k) = b(k-1) + K_I * e_q(k),              e_q = q_hat_c - q_c   (veh/h/lane)
  primary (outer, PI):   q_hat_c(k) = q_hat_c(k-1) + (K'_P + K'_I) e_rho(k) - K'_P e_rho(k-1),
                         e_rho = rho_hat_out - rho_out(k)   (veh/km/lane; set-point ~ critical density)
  paper values: rho_hat 32 veh/km/lane, K'_P 38 km/h, K'_I 9 km/h, K_I 0.0015 h.lane/veh; T_c = 60 s;
  posted rates discrete b in {0.1, ..., 1.0} (rounded), b_min 0.2, |delta b| <= 0.2 per period and between
  consecutive signs; b = 0.9 in the acceleration (and bottleneck) area while MTFC is active.
Anti-windup (our addition, disclosed): q_hat_c is clamped to [q_min, q_max] and the continuous integrator b to
[b_min, 1]; without it q_hat_c winds up during free flow and reacts late at onset.
"""
from __future__ import annotations

import numpy as np


class MTFC:
    def __init__(self, rho_set: float = 32.0, kp: float = 38.0, ki: float = 9.0, ki2: float = 0.0015,
                 b_min: float = 0.2, acc_b: float = 0.9, q_min: float = 200.0, q_max: float = 2600.0):
        self.rho_set, self.kp, self.ki, self.ki2 = rho_set, kp, ki, ki2
        self.b_min, self.acc_b, self.q_min, self.q_max = b_min, acc_b, q_min, q_max
        self.q_hat = None
        self.e_prev = 0.0
        self.b_cont = 1.0
        self.b_posted = 1.0

    def step(self, rho_out: float, q_c: float) -> tuple[float, float]:
        """One control period. Returns (b for the application area, b for the acceleration area)."""
        e = self.rho_set - rho_out
        if self.q_hat is None:
            self.q_hat = float(np.clip(q_c, self.q_min, self.q_max))
        self.q_hat = float(np.clip(self.q_hat + (self.kp + self.ki) * e - self.kp * self.e_prev, self.q_min, self.q_max))
        self.e_prev = e
        self.b_cont = float(np.clip(self.b_cont + self.ki2 * (self.q_hat - q_c), self.b_min, 1.0))
        target = round(self.b_cont * 10.0) / 10.0
        target = min(max(target, self.b_min), 1.0)
        self.b_posted = float(np.clip(target, self.b_posted - 0.2, self.b_posted + 0.2))
        active = self.b_posted < 1.0 - 1e-9
        return self.b_posted, (self.acc_b if active else 1.0)
