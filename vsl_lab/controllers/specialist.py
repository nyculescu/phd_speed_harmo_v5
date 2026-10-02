"""SPECIALIST dynamic speed-limit algorithm, pure Python (no SUMO dependency).

Sources (both read in full; printed page numbers):
  P1  Hegyi, Hoogendoorn, Schreuder, Stoelhorst, Viti, "SPECIALIST: A dynamic speed limit control algorithm based on
      shock wave theory", IEEE ITSC 2008, pp. 827-832.
  P2  Hegyi, Hoogendoorn, Schreuder, Stoelhorst, "The expected effectivity of the dynamic speed limit algorithm
      SPECIALIST - a field data evaluation method", ECC 2009, pp. 1770-1775.

Units inside: x in km (increasing downstream), t in h, q in veh/h/lane, rho in veh/km/lane, speeds and front speeds in
km/h (negative = upstream). Positions given to the class in metres, times in seconds.

States (P1 pp. 828-829, Figs 2-5; P2 pp. 1771-1772)
  1 downstream free flow (measured)          2 jam = moving shock wave (flow measured, density estimated)
  3 = rho6 at the effective limit V          4 = inflow into the limited stretch: v4 = V, rho4 design (P1 p.831: 33)
  5 = discharge of area 4, design (P1 p.831: rho5 = 26 veh/km/lane, q5 = 6100 veh/h on 3 lanes = 2033.3 veh/h/lane)
  6 upstream free flow (measured)
Front rule (P1 p.828, in words): the front between states a and b moves at  w_ab = (q_a - q_b) / (rho_a - rho_b).

Estimation (printed)
  detection at detector i:  q_i <= q_max and v_i <= v_max                                      (P2 p.1772; P1 p.829-830)
  q1, rho1 = mean(q_i), mean(q_i / v_i) over the free detectors directly downstream; same upstream for 6  (P1 p.830)
  rho2 = rho1 + (q2 - q1) / v12,  v12 = head speed, constant (P1 p.831: -15 km/h; P2 p.1773: "around -18")  (P2 p.1772)
  rho3 = rho6, q3 = V rho6;  q4 = V rho4;  (q5, rho5) design                                    (P1 p.830)
  x_h^ = x_h + m_h;  x_t^ = x_t - m_t  with x_h, x_t the detector locations of head and tail      (P1 p.831)

Estimation (assumptions, not printed)
  q2 = mean of the jam detectors' q (P1 uses "the flow of state 2" without giving the estimator).
  x_t^ = x_t - |m_t|: P1 p.831 prints m_t = -1.5 km with x_t^ = x_t - m_t, which would move the tail 1.5 km
      DOWNSTREAM (shorter jam), against the "on the safe side ... somewhat longer" text of the same page. The magnitude
      is used so the assumed jam is extended upstream. Ambiguity disclosed; m_t is a parameter.
  Detectors with v < 0 (SUMO: no vehicle in the interval) or non-finite values are dropped (neither jam nor free);
      jam clusters are runs of consecutive jam detectors among the remaining ones.
  Optional det_lanes: a detector on a cross-section with l lanes is rescaled to the n_lanes reference cross-section
      as q_ref = q * l / n_lanes (total flow conserved), rho_ref = q_ref / v. Thresholds use the raw per-lane q.
  rho4=None selects P2's choice (p.1774): state 4 at speed V on the line through states 1 and 2,
      rho4 = (q1 - v12 rho1) / (V - v12).

Fronts (derived here from the front rule; P1 p.830 and P2 p.1773 say only "straightforward linear equations")
  w12 = v12                                  jam head (1|2); equals (q1-q2)/(rho1-rho2) by the rho2 estimate
  w62 = (q6-q2)/(rho6-rho2)                  jam tail before activation (used only when delay_s > 0)
  w23 = (q2-q3)/(rho2-rho3)                  jam tail after activation (2|3)
  w34 = (q3-q4)/(rho3-rho4) = V              upstream edge of area 3 (both states drive at V)
  w64 = (q6-q4)/(rho6-rho4)                  upstream edge of area 4 = tail of the speed limits
  w45 = (q4-q5)/(rho4-rho5)                  discharge front of area 4 (after point P)
  w15 = (q1-q5)/(rho1-rho5)                  forward front between 5 and 1 (checked only)
Geometry (activation at t0 with head x_h0 and tail x_t0; s = t - t0)
  x_h(s)  = x_h0 + w12 s;   x_23(s) = x_t0 + w23 s
  area 2 vanishes at   tau2 = (x_h0 - x_t0) / (w23 - w12);   P = (t0 + tau2,  x_P = x_h0 + w12 tau2)
  "the creation of state 3 exactly resolves the shock wave" (P1 p.828): area 3 also vanishes at P, so
      x_c0 = x_P - w34 tau2        (upstream end of the limits at t0; area-3 length x_t0 - x_c0 = (V - w23) tau2)
  x_34(s) = x_c0 + w34 s;   x_64(s) = x_c0 + w64 s;   for s >= tau2:  x_45(s) = x_P + w45 (s - tau2)
  area 4 vanishes where 6|4 meets 4|5:   s4 = tau2 (w34 - w45) / (w64 - w45);   Q = (t0 + s4,  x_c0 + w64 s4)
  limited stretch = areas 2 U 3 U 4 (P1 p.830 III-D; P2 Fig. 2):
      [x_64(s), x_h(s)]  for 0 <= s < tau2;    [x_64(s), x_45(s)]  for tau2 <= s < s4;    none for s >= s4.
  With delay_s = d > 0 (P2 p.1773: schedule the 6->3 change at the expected display moment): measured at t_m,
  t0 = t_m + d, x_h0 = x_h^ + w12 d, x_t0 = x_t^ + w62 d; no limits before t0.

Solvability (P1 p.830; P2 p.1773), checked in this order; the first failing one is the reason:
  no_downstream_free_detector / no_upstream_free_detector   states 1 / 6 cannot be estimated
  state2_invalid        rho2 > max(rho1, rho6) and v2 = q2/rho2 < V (needed for the scheme; implies x_c0 < x_t0)
  v6_not_above_limit    "the speed in area 6 should be higher than the speed limit"                       (P1 p.830)
  state5_not_above_state1   q5 > q1 and rho5 > rho1                                                       (P1 p.830)
  rho4_not_above_rho6   derived: area 4 exists only if rho4 > rho6 (then w64 < V iff v6 > V)
  area2_not_converging  w23 > w12 and tau2 > 0 ("head and tail of area 2 should converge")               (P1 p.830)
  area4_not_converging  w64 > w45 and w45 < w15 ("the same applies for area 4")                          (P1 p.830)
  exceeds_upstream_free_area  min(x_c0, x_Q) >= head detector of the next jam upstream (if any)          (P1 p.830)
  outside_signs         areas 3 and 4, i.e. [min(x_c0, x_Q), max(x_t0, x_P)], within the VSL segments    (P1 p.830)
      (interpretation: the area that the limits must create; area 2 is congested anyway)
Several jam clusters: assessed downstream -> upstream, the first solvable one is activated (states 1/6 from the
free detectors between neighbouring clusters). P1 p.830 assumes no other jams on the stretch.
Termination (P1 p.829-830): while a scheme is active, new measurements are ignored; when areas 2-4 are in the past
(t >= t0 + s4) the limits are released and the measurement of that call is processed as the next one.
P1 recalculates the area locations "e.g., every second" (p.830): step() evaluates them at its own call time only;
call factors_at(t_s) more often for finer application.
"""
from __future__ import annotations

import math

_EPS = 1e-9


def front_speed(qa: float, rhoa: float, qb: float, rhob: float) -> float:
    """Front rule (P1 p.828): w_ab = (q_a - q_b) / (rho_a - rho_b), km/h. NaN if the densities coincide."""
    d = rhoa - rhob
    if abs(d) < _EPS:
        return math.nan
    return (qa - qb) / d


def scheme_states(q1: float, rho1: float, q2: float, q6: float, rho6: float, *, v_eff: float, v12: float,
                  rho4: float | None, q5: float, rho5: float) -> dict:
    """States 1-6 as (q, rho) and the front speeds w['ab'] of the control scheme (see the module docstring)."""
    rho2 = rho1 + (q2 - q1) / v12
    rho3 = rho6
    q3 = v_eff * rho3
    if rho4 is None:
        rho4 = (q1 - v12 * rho1) / (v_eff - v12)
    q4 = v_eff * rho4
    st = {1: (q1, rho1), 2: (q2, rho2), 3: (q3, rho3), 4: (q4, rho4), 5: (q5, rho5), 6: (q6, rho6)}
    w = {ab: front_speed(*st[int(ab[0])], *st[int(ab[1])]) for ab in ("62", "23", "34", "64", "45", "15")}
    w["12"] = v12
    return {"states": st, "w": w}


def _finite(*xs: float) -> bool:
    return all(math.isfinite(x) for x in xs)


class Specialist:
    """SPECIALIST (P1, P2). Call step() every measurement period with 1-min detector data."""

    def __init__(self, det_x: list[float], seg_bounds: list[tuple[float, float]], n_lanes: int = 3,
                 v_limit_kmh: float = 60.0, q_max: float = 1500.0, v_max: float = 50.0, v12_kmh: float = -15.0,
                 rho4: float | None = 33.0, rho5: float = 26.0, q5: float = 2033.3, m_h_km: float = 0.0,
                 m_t_km: float = 1.5, v_free_kmh: float = 120.0, *, v_eff_kmh: float | None = None,
                 det_lanes: list[int] | None = None, delay_s: float = 0.0):
        if len(det_x) < 3:
            raise ValueError("need at least 3 detectors (upstream free, jam, downstream free)")
        if any(b <= a for a, b in zip(det_x, det_x[1:])):
            raise ValueError("det_x must be strictly increasing (upstream -> downstream)")
        if not seg_bounds or any(b <= a for a, b in seg_bounds):
            raise ValueError("seg_bounds must be non-empty (start, end) pairs with end > start")
        if not 0.0 < v_limit_kmh <= v_free_kmh:
            raise ValueError("need 0 < v_limit_kmh <= v_free_kmh")
        if v12_kmh >= 0.0:
            raise ValueError("v12_kmh is the head speed of an upstream-moving jam and must be negative")
        if n_lanes <= 0 or delay_s < 0.0:
            raise ValueError("need n_lanes > 0 and delay_s >= 0")
        if det_lanes is not None and len(det_lanes) != len(det_x):
            raise ValueError("det_lanes must have one entry per detector")
        self.x = [xi / 1000.0 for xi in det_x]
        self.segs = [(a / 1000.0, b / 1000.0) for a, b in seg_bounds]
        self.sign_lo = min(a for a, _ in self.segs)
        self.sign_hi = max(b for _, b in self.segs)
        self.lane_scale = [1.0] * len(det_x) if det_lanes is None else [l / n_lanes for l in det_lanes]
        self.n_lanes = n_lanes
        self.v_limit, self.v_free = float(v_limit_kmh), float(v_free_kmh)
        self.v_eff = float(v_limit_kmh if v_eff_kmh is None else v_eff_kmh)
        self.b_lim = self.v_limit / self.v_free
        self.q_max, self.v_max, self.v12 = float(q_max), float(v_max), float(v12_kmh)
        self.rho4, self.rho5, self.q5 = rho4, float(rho5), float(q5)
        self.m_h, self.m_t = float(m_h_km), abs(float(m_t_km))
        self.delay_h = float(delay_s) / 3600.0
        self.reset()

    def reset(self) -> None:
        self.scheme: dict | None = None
        self.last_scheme: dict | None = None
        self.last_eval: dict | None = None
        self.active = False
        self.n_detected = self.n_solvable = self.n_unsolvable = self.n_finished = 0
        self.last_reason = "init"

    # ---------------------------------------------------------------- application
    def interval_km(self, t_s: float) -> tuple[float, float] | None:
        """Speed-limited stretch (areas 2 U 3 U 4) of the active scheme at time t_s, in km; None if there is none."""
        sc = self.scheme
        if sc is None:
            return None
        s = t_s / 3600.0 - sc["t0_h"]
        if s < -_EPS or s >= sc["s4_h"]:
            return None
        s = max(s, 0.0)
        w = sc["w"]
        lo = sc["x_c0"] + w["64"] * s
        hi = sc["x_h0"] + w["12"] * s if s < sc["tau2_h"] else sc["x_P"] + w["45"] * (s - sc["tau2_h"])
        return (lo, hi) if hi > lo else None

    def factors_at(self, t_s: float) -> list[float]:
        """b = v_limit / v_free on segments overlapping the limited stretch at t_s, else 1.0 (no state change)."""
        iv = self.interval_km(t_s)
        if iv is None:
            return [1.0] * len(self.segs)
        lo, hi = iv
        return [self.b_lim if (a < hi and b > lo) else 1.0 for a, b in self.segs]

    # ---------------------------------------------------------------- algorithm
    def step(self, t_s: float, q: list[float], v: list[float]) -> list[float]:
        """Called every 60 s with 1-min per-detector flow (veh/h/lane) and speed (km/h), detectors ordered upstream ->
        downstream at positions det_x (m). Returns one speed-limit factor b in (0, 1] per VSL segment (seg_bounds,
        metres, upstream -> downstream), where b = v_limit/v_free on segments overlapping areas 2, 3 or 4 of the
        active scheme at time t_s, else 1.0."""
        n = len(self.x)
        if len(q) != n or len(v) != n:
            raise ValueError(f"expected {n} detector values, got q={len(q)}, v={len(v)}")
        if self.scheme is not None:
            if t_s / 3600.0 < self.scheme["t_end_h"] - _EPS:
                self.active = True
                return self.factors_at(t_s)              # measurements ignored while a scheme runs (P1 p.830)
            self.scheme, self.active = None, False
            self.n_finished += 1
        q = [float(a) for a in q]
        v = [float(a) for a in v]
        valid = [_finite(q[i], v[i]) and q[i] >= 0.0 and v[i] >= 0.0 for i in range(n)]
        jam = [valid[i] and q[i] <= self.q_max and v[i] <= self.v_max for i in range(n)]
        clusters: list[list[int]] = []
        cur: list[int] = []
        for i in range(n):
            if not valid[i]:
                continue
            if jam[i]:
                cur.append(i)
            elif cur:
                clusters.append(cur)
                cur = []
        if cur:
            clusters.append(cur)
        if not clusters:
            self.last_reason = "no_shock_wave"
            return [1.0] * len(self.segs)
        self.n_detected += 1
        qref = [q[i] * self.lane_scale[i] for i in range(n)]
        reasons = []
        for k in range(len(clusters) - 1, -1, -1):
            sc, why = self._assess(k, clusters, valid, qref, v, t_s / 3600.0)
            if sc is not None:
                self.scheme = self.last_scheme = sc
                self.active = True
                self.n_solvable += 1
                self.last_reason = (f"activated: jam {sc['x_t0']:.3f}-{sc['x_h0']:.3f} km, limits from "
                                    f"{sc['x_c0']:.3f} km, end in {(sc['t_end_h'] * 3600.0 - t_s):.0f} s")
                return self.factors_at(t_s)
            reasons.append(f"jam@{self.x[clusters[k][-1]]:.3f}km:{why}")
        self.n_unsolvable += 1
        self.last_reason = "unsolvable: " + "; ".join(reasons)
        return [1.0] * len(self.segs)

    def _assess(self, k: int, clusters: list[list[int]], valid: list[bool], qref: list[float], v: list[float],
                t_m: float) -> tuple[dict | None, str]:
        c = clusters[k]
        n = len(self.x)
        dn_end = clusters[k + 1][0] if k + 1 < len(clusters) else n
        up_start = clusters[k - 1][-1] if k > 0 else -1
        dn = [i for i in range(c[-1] + 1, dn_end) if valid[i] and v[i] > 0.0]
        up = [i for i in range(up_start + 1, c[0]) if valid[i] and v[i] > 0.0]
        ev: dict = {"cluster": list(c), "down": dn, "up": up}
        self.last_eval = ev
        if not dn:
            return self._fail(ev, "no_downstream_free_detector")
        if not up:
            return self._fail(ev, "no_upstream_free_detector")
        q1 = sum(qref[i] for i in dn) / len(dn)
        rho1 = sum(qref[i] / v[i] for i in dn) / len(dn)
        q6 = sum(qref[i] for i in up) / len(up)
        rho6 = sum(qref[i] / v[i] for i in up) / len(up)
        q2 = sum(qref[i] for i in c) / len(c)
        sw = scheme_states(q1, rho1, q2, q6, rho6, v_eff=self.v_eff, v12=self.v12, rho4=self.rho4, q5=self.q5,
                           rho5=self.rho5)
        st, w = sw["states"], sw["w"]
        ev.update(states=st, w=w)
        V = self.v_eff
        rho2, rho4 = st[2][1], st[4][1]
        if not (_finite(rho2) and rho2 > max(rho1, rho6) and q2 / rho2 < V):
            return self._fail(ev, "state2_invalid")
        if not q6 / rho6 > V:
            return self._fail(ev, "v6_not_above_limit")
        if not (self.q5 > q1 and self.rho5 > rho1):
            return self._fail(ev, "state5_not_above_state1")
        if not (_finite(rho4) and rho4 > rho6):
            return self._fail(ev, "rho4_not_above_rho6")
        # head/tail with margins (P1 p.831), optionally propagated over the actuation delay (P2 p.1773)
        d = self.delay_h
        x_h0 = self.x[c[-1]] + self.m_h + w["12"] * d
        x_t0 = self.x[c[0]] - self.m_t + (w["62"] * d if d > 0.0 else 0.0)
        t0 = t_m + d
        if not (_finite(x_t0) and x_h0 > x_t0):
            return self._fail(ev, "no_jam_length_at_activation")
        dw2 = w["23"] - w["12"]
        if not (_finite(dw2) and dw2 > _EPS):
            return self._fail(ev, "area2_not_converging")
        tau2 = (x_h0 - x_t0) / dw2
        x_P = x_h0 + w["12"] * tau2
        x_c0 = x_P - w["34"] * tau2
        dw4 = w["64"] - w["45"]
        if not (_finite(dw4, w["15"]) and dw4 > _EPS and w["45"] < w["15"]):
            return self._fail(ev, "area4_not_converging")
        s4 = (x_P - x_c0 - w["45"] * tau2) / dw4
        x_Q = x_c0 + w["64"] * s4
        x_up_min = min(x_c0, x_Q)
        x_dn_max = max(x_t0, x_P)
        ev.update(x_h0=x_h0, x_t0=x_t0, tau2_h=tau2, x_P=x_P, x_c0=x_c0, s4_h=s4, x_Q=x_Q)
        if k > 0 and x_up_min < self.x[up_start]:
            return self._fail(ev, "exceeds_upstream_free_area")
        if x_up_min < self.sign_lo - _EPS or x_dn_max > self.sign_hi + _EPS:
            return self._fail(ev, "outside_signs")
        sc = dict(ev, t_meas_h=t_m, t0_h=t0, t_end_h=t0 + s4, x_up_min=x_up_min, x_dn_max=x_dn_max,
                  reason="solvable")
        self.last_eval = sc
        return sc, "solvable"

    def _fail(self, ev: dict, why: str) -> tuple[None, str]:
        ev["reason"] = why
        return None, why
