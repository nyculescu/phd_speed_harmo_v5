"""PI with saturation (Stern et al. 2018, arXiv 1705.01693 v1, Sec. 3), step-length aware port of plants/ring.py.

U = mean own speed over `window_s`; v_target = U + v_catch * clip((dx - g_l)/(g_u - g_l), 0, 1); alpha =
clip((dx - dx_s)/gamma, 0, 1) with dx_s = max(2 s * dv, 4 m), dv = v_lead - v; beta = 1 - alpha/2;
v_cmd(j+1) = beta (alpha v_target + (1 - alpha) v_lead) + (1 - beta) v_cmd(j). Constants as in plants/ring.py
(g_l 7 m, g_u 30 m, v_catch 1 m/s, gamma 2 m, window 38 s), checked against the paper for the ring track.
"""
from __future__ import annotations

from collections import deque


class PISaturation:
    def __init__(self, dt: float, window_s: float = 38.0, g_l=7.0, g_u=30.0, v_catch=1.0, gamma=2.0):
        self.hist = deque(maxlen=max(1, int(round(window_s / dt))))
        self.g_l, self.g_u, self.v_catch, self.gamma = g_l, g_u, v_catch, gamma
        self.v_prev = None

    def v_cmd(self, v: float, v_lead: float, gap: float) -> float:
        self.hist.append(v)
        U = sum(self.hist) / len(self.hist)
        v_target = U + self.v_catch * min(max((gap - self.g_l) / (self.g_u - self.g_l), 0.0), 1.0)
        dv = v_lead - v
        dx_s = max(2.0 * dv, 4.0)
        alpha = min(max((gap - dx_s) / self.gamma, 0.0), 1.0)
        beta = 1.0 - 0.5 * alpha
        if self.v_prev is None:
            self.v_prev = v
        vc = beta * (alpha * v_target + (1.0 - alpha) * v_lead) + (1.0 - beta) * self.v_prev
        self.v_prev = vc
        return vc
