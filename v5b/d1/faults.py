"""Screen D1 Rule 2 (fault layer) and the RF fill-in math. Pure Python, no SUMO.

The faulty detector is the meter's mainline reading: the archived FBMeter reads n_hat = vehicles on edge 4
(the 2-lane section between the first zipper merge and the second), every T = 30 s. The RF arm's healthy
upstream reading is the vehicle count on edge 3 (4 lanes, between the meter at node 3 and edge 4).
"""
from __future__ import annotations

import numpy as np

FAULTS = ("stuck_off", "stuck_on", "noisy", "dropout")
ANY = "any"            # a detected fault whose reading is never used (arms O, FX, RF, NC): read() refuses
NOISE_SIGMA = 0.5      # Rule 2: multiplicative noise, sigma = 50 %
ONSET_SALT = 2027      # onset stream rng(seed + 2027); independent of SUMO and the demand stream rng(seed)
NOISE_SALT = 4049      # noise stream rng(seed + 4049)
L_JAM_M = 7.0          # jam spacing per vehicle (5 m length + 2 m minGap), the archive's piece-capacity convention


def onset_time(seed: int, t_ctrl0: float, control_s: float) -> float:
    """Rule 2: onset ~ U(t_ctrl0, t_ctrl0 + control_s / 3) from its own seeded stream. It depends on the seed only,
    so every arm and fault type of a seed shares the onset (paired)."""
    return float(np.random.default_rng(seed + ONSET_SALT).uniform(t_ctrl0, t_ctrl0 + control_s / 3.0))


def saturated_count(lane_len: dict, edge: str = "4", l_jam: float = L_JAM_M) -> float:
    """'Reads saturated' = the jam count of the detected section: sum over its lanes of length / 7 m."""
    return float(sum(L / l_jam for lid, L in lane_len.items() if lid.rsplit("_", 1)[0] == edge))


class DetectorFault:
    """kind in FAULTS, 'none' or ANY; active from `onset` to the end of the episode. Detection is perfect and
    instant: active(t) is what the FX and RF arms use to switch."""

    def __init__(self, kind: str, onset: float, saturated: float, seed: int):
        if kind not in FAULTS + ("none", ANY):
            raise ValueError(kind)
        self.kind, self.onset, self.saturated = kind, float(onset), float(saturated)
        self.rng = np.random.default_rng(seed + NOISE_SALT)

    def active(self, t: float) -> bool:
        return self.kind != "none" and t >= self.onset - 1e-9

    def read(self, t: float, true_value: float):
        """Observed reading at time t; None = no data (dropout)."""
        if not self.active(t):
            return float(true_value)
        if self.kind == ANY:
            raise RuntimeError("fault type 'any': this arm must not use the faulty reading")
        if self.kind == "stuck_off":
            return 0.0
        if self.kind == "stuck_on":
            return self.saturated
        if self.kind == "noisy":   # counts cannot be negative: the factor is truncated at 0
            return float(true_value) * max(0.0, 1.0 + NOISE_SIGMA * float(self.rng.standard_normal()))
        return None                # dropout


def ratio_fit(n_up, n_down) -> float:
    """RF ratio learned on tuning seeds: ratio-of-sums estimator sum(n_down) / sum(n_up) over the healthy meter's
    readings (edge 4 = down, edge 3 = up)."""
    su, sd = float(np.sum(n_up)), float(np.sum(n_down))
    if su <= 0.0:
        raise ValueError("no upstream vehicles in the fit data")
    return sd / su


def rf_fill(ratio: float, n_up: float) -> float:
    """RF fill-in of the faulty reading from the healthy upstream count."""
    return float(ratio) * float(n_up)
