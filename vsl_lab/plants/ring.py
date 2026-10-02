"""RING22 plant (Track 3): Stern et al. (2018) / Flow ring with 21 human drivers and 1 AV.

All vehicles are moved by our own controllers through libsumo each 0.1 s step (as Flow did):
  humans: IDM (Flow defaults v0 30, T 1, a 1, b 1.5, delta 4, s0 2) + Gaussian acceleration noise
          noise="sqrt_dt": a += sqrt(dt) N(0, 0.2)   (Flow master)   | noise="per_step": a += N(0, 0.2) (Flow v0.2.0)
  AV:     one of NC (= IDM human without noise), FollowerStopper(U), PI-with-saturation, or an RL action.
SUMO only integrates kinematics: speedMode 6 (accel/decel limits only). Our own safe-following rule
(Vinitsky 2018: "if a vehicle is about to crash it immediately comes to a full stop") stops a vehicle whose
next-step bumper gap would fall below 0.5 m. Collisions are still counted by SUMO (health H-R4).

Controller equations follow Stern et al. 2018 (arXiv 1705.01693 v1, Sec. 3), checked against the paper:
  FollowerStopper: dx_k = dx0_k + (dv_-)^2 / (2 d_k), dx0 = (4.5, 5.25, 6.0) m, d = (1.5, 1.0, 0.5) m/s^2,
                   dv_- = min(v_lead - v, 0); v = min(max(v_lead, 0), U); 4 regions (Eq. 2, paper form).
  PI with saturation: U = mean AV speed over 38 s; v_target = U + v_catch * clip((dx - g_l)/(g_u - g_l), 0, 1),
                   g_l 7 m, g_u 30 m, v_catch 1 m/s; alpha = clip((dx - dx_s)/gamma, 0, 1), gamma 2 m,
                   dx_s = max(2 s * dv, 4 m) (as printed, dv = v_lead - v); beta = 1 - alpha/2;
                   v_cmd(j+1) = beta (alpha v_target + (1 - alpha) v_lead) + (1 - beta) v_cmd(j).
The AV tracks v_cmd with a = clip((v_cmd - v)/dt, -3, 1.5) m/s^2 (no low-level PID model; Flow did the same
without the clip).
"""
from __future__ import annotations

import math
from collections import deque
from pathlib import Path

import libsumo as ls
import numpy as np

from vsl_lab.netgen import ring as ringnet

DT = 0.1
N_VEH = 22
AV_ID = "av_0"
IDM = dict(v0=30.0, T=1.0, a=1.0, b=1.5, delta=4.0, s0=2.0)
VEH_LEN = 5.0


def idm_accel(v: float, v_lead: float, gap: float, p=IDM) -> float:
    s_star = p["s0"] + max(0.0, v * p["T"] + v * (v - v_lead) / (2.0 * math.sqrt(p["a"] * p["b"])))
    return p["a"] * (1.0 - (v / p["v0"]) ** p["delta"] - (s_star / max(gap, 0.01)) ** 2)


class FollowerStopper:
    DX0 = (4.5, 5.25, 6.0)
    D = (1.5, 1.0, 0.5)

    def __init__(self, U: float):
        self.U = U

    def v_cmd(self, v: float, v_lead: float, gap: float) -> float:
        dvm = min(v_lead - v, 0.0)
        dx = [x0 + dvm * dvm / (2.0 * d) for x0, d in zip(self.DX0, self.D)]
        vv = min(max(v_lead, 0.0), self.U)
        if gap <= dx[0]:
            return 0.0
        if gap <= dx[1]:
            return vv * (gap - dx[0]) / (dx[1] - dx[0])
        if gap <= dx[2]:
            return vv + (self.U - vv) * (gap - dx[1]) / (dx[2] - dx[1])
        return self.U


class PISaturation:
    def __init__(self, window_s: float = 38.0, g_l=7.0, g_u=30.0, v_catch=1.0, gamma=2.0):
        self.hist = deque(maxlen=int(round(window_s / DT)))
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


class RingPlant:
    """One ring episode. Call start(), then step_all(av_accel or None) per 0.1 s step."""

    def __init__(self, L: float, seed: int, noise: str = "sqrt_dt", noise_std: float = 0.2, jitter_m: float = 1.0,
                 run_dir: Path | None = None):
        self.L_target = L
        self.seed = seed
        self.noise, self.noise_std = noise, noise_std
        self.rng = np.random.default_rng(seed)
        self.jitter_m = jitter_m
        self.dir = ringnet.build(L)
        self.net = self.dir / "ring.net.xml"
        self.elen = ringnet.edge_lengths(self.net)
        self.L = sum(self.elen.values())
        self.run_dir = run_dir
        self.t = 0.0
        self.collisions = 0
        self.teleports = 0
        self.estops = 0
        self.safe_stops = 0
        self.ids = []

    def _route_file(self) -> Path:
        order = list(ringnet.EDGES)
        lines = ['<?xml version="1.0" encoding="UTF-8"?>', "<routes>",
                 '  <vType id="human" length="5" minGap="0" accel="5" decel="9" emergencyDecel="9" sigma="0" '
                 'speedFactor="1" speedDev="0" maxSpeed="30"/>',
                 '  <vType id="av" length="5" minGap="0" accel="5" decel="9" emergencyDecel="9" sigma="0" '
                 'speedFactor="1" speedDev="0" maxSpeed="30" color="1,0,0"/>']
        spacing = self.L / N_VEH
        cum = np.cumsum([0.0] + [self.elen[e] for e in order])
        for i in range(N_VEH):
            s = (i * spacing + self.rng.uniform(-self.jitter_m, self.jitter_m)) % self.L
            k = int(np.searchsorted(cum, s, side="right") - 1)
            k = min(k, 3)
            pos = max(0.0, min(s - cum[k], self.elen[order[k]] - 0.01))
            route = " ".join(order[(k + j) % 4] for j in range(4 * 400))
            vid = AV_ID if i == 0 else f"h_{i}"
            vt = "av" if i == 0 else "human"
            # Front bumper position. SUMO accepts departPos < vehicle length (the back hangs over the previous
            # edge); the earlier clamp to >= 5.01 m pushed cars onto their neighbours on short rings and SUMO then
            # refused to insert one of them (21 vehicles; caught by health H-R1 in ring R1/R2 v1).
            dpos = min(max(pos, 0.01), self.elen[order[k]] - 0.01)
            lines.append(f'  <vehicle id="{vid}" type="{vt}" depart="0" departPos="{dpos:.3f}" '
                         f'departSpeed="0">\n    <route edges="{route}"/>\n  </vehicle>')
        lines.append("</routes>")
        p = (self.run_dir or self.dir) / f"ring_L{int(self.L_target)}_s{self.seed}_{id(self)}.rou.xml"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("\n".join(lines) + "\n")
        return p

    def start(self) -> None:
        self.rou = self._route_file()
        log = (self.run_dir or self.dir) / f"sumo_ring_{id(self)}.log"
        from vsl_lab.config import SUMO_BIN
        ls.start([SUMO_BIN, "-n", str(self.net), "-r", str(self.rou), "--step-length", str(DT),
                  "--seed", str(self.seed), "--no-step-log", "true", "--duration-log.disable", "true",
                  "--time-to-teleport", "300", "--collision.action", "warn", "--collision.check-junctions", "false",
                  "--log", str(log)])
        self.log = log
        ls.simulationStep()          # insert all vehicles
        self.t = ls.simulation.getTime()
        self.ids = sorted(ls.vehicle.getIDList())
        for vid in self.ids:
            ls.vehicle.setSpeedMode(vid, 6)
            ls.vehicle.setLaneChangeMode(vid, 0)

    def state(self):
        """Return dict vid -> (v, v_lead, gap) using SUMO's leader search along the looped route."""
        out = {}
        for vid in self.ids:
            v = ls.vehicle.getSpeed(vid)
            lead = ls.vehicle.getLeader(vid, 300.0)
            if lead is None or lead[0] == "":
                out[vid] = (v, v, 300.0)
            else:
                out[vid] = (v, ls.vehicle.getSpeed(lead[0]), max(lead[1], 0.0))
        return out

    def step_all(self, av_accel: float | None, st: dict | None = None) -> dict:
        st = st or self.state()
        for vid in self.ids:
            v, vl, gap = st[vid]
            if vid == AV_ID and av_accel is not None:
                a = av_accel
            else:   # humans, and the AV under no-control (an all-human ring, as Flow's baseline)
                a = idm_accel(v, vl, gap)
                eps = self.rng.normal(0.0, self.noise_std)
                a += math.sqrt(DT) * eps if self.noise == "sqrt_dt" else eps
            v_next = max(0.0, v + a * DT)
            # safe-following rule: predicted next-step gap must stay >= 0.5 m
            if gap + (vl - v_next) * DT < 0.5:
                v_next = 0.0
                self.safe_stops += 1
            ls.vehicle.setSpeed(vid, v_next)
        ls.simulationStep()
        self.t = ls.simulation.getTime()
        self.collisions += ls.simulation.getCollidingVehiclesNumber()
        self.teleports += ls.simulation.getStartingTeleportNumber()
        self.estops += ls.simulation.getEmergencyStoppingVehiclesNumber()
        return st

    def speeds(self) -> np.ndarray:
        return np.array([ls.vehicle.getSpeed(v) for v in self.ids])

    def close(self) -> dict:
        n_now = ls.vehicle.getIDCount()
        ls.close()
        n_err = 0
        try:
            n_err = sum(1 for ln in self.log.read_text(errors="replace").splitlines() if ln.startswith("Error"))
        except Exception:
            pass
        try:
            self.rou.unlink()
        except OSError:
            pass
        issues = []
        if n_now != N_VEH:
            issues.append(("FAIL", "H-R1", f"vehicles in ring {n_now} != {N_VEH}"))
        if self.collisions:
            issues.append(("FAIL", "H-R4", f"collisions {self.collisions}"))
        if self.teleports:
            issues.append(("FAIL", "H-R3", f"teleports {self.teleports}"))
        if n_err:
            issues.append(("FAIL", "H-E4", f"{n_err} SUMO errors"))
        status = "FAIL" if any(i[0] == "FAIL" for i in issues) else "PASS"
        return {"status": status, "issues": issues, "safe_stops": self.safe_stops, "estops": self.estops}
