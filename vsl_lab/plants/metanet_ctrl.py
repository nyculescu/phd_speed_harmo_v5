"""Closed-loop METANET stepper for the day-pattern corridor testbed (D5.6, D5.11; testbed protocol v0/v1 §2).

A state-in/state-out, batched (B = n_param_sets x D) re-implementation of `metanet.simulate` with three additions:
  * a meter-rate input on the controlled entrances (E9, E12, E13, E14 by default): q_o = min(d + w/T, Q_O, supply, r_eff);
  * the common queue-protection layer (identical for every arm, learning or not; D5.11 / review fix "queue layer"):
        r_wait = w / max_wait                       (veh/h; serves the current queue within max_wait)
        r_stor = d_hat + (w - f_hi S) / t_stor       when w > f_hi S (d_hat = mean arrivals over the last t_stor)
        r_eff  = min(r_max, max(r_cmd, r_wait, r_stor)); hard net: w >= S -> r_max until w <= f_lo S
  * per-bin delay accounting: vehicle-hours in the cells and in every origin queue, and the free-flow-time term.

The dynamics are the frozen plant's own arithmetic in the same order (`metanet.simulate`, v4 variant, T = 0.75 s), so
in replay (no control) every SimOut field equals simulate() bit for bit; tests/test_metanet_ctrl.py checks this
(M-EQ). This file is NOT in the v5 CODE_PATHS: the frozen plant code is imported, never edited.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from vsl_lab.plants import metanet as M
from vsl_lab.plants.metanet import (Q_O, RHO_MAX, V_CAP_FACTOR, V_MIN, Inputs, Net, SimOut, assert_numerics,
                                    free_flow_state)

CONTROLLED = ("E9", "E12", "E13", "E14")


@dataclass
class QueueLayer:
    """Common ramp-queue protection (all arms). storage_veh: per controlled ramp, vehicles (S_i)."""
    storage_veh: tuple
    r_min: float = 240.0
    r_max: float = 1800.0
    max_wait_s: float = 240.0
    f_hi: float = 0.75
    f_lo: float = 0.5
    t_stor_s: float = 60.0


@dataclass
class Acc:
    tts_cells: np.ndarray            # (B, bins) veh-h in the cells per bin
    tts_queues: np.ndarray           # (B, n_origins, bins) veh-h in each origin queue per bin
    fft: np.ndarray                  # (B, bins) free-flow-time veh-h of the flow in the cells per bin
    r_eff: np.ndarray                # (B, n_ctrl, bins) bin-mean effective meter rate (veh/h; inf = unmetered)
    layer_steps: np.ndarray          # (B, n_ctrl, bins) steps with r_eff > r_cmd (queue layer active)
    net_steps: np.ndarray            # (B, n_ctrl, bins) steps with the hard net active
    q_cell: np.ndarray = None        # (B, N, bins) bin-mean cell outflow q_i (veh/h; flow from cell i into i+1)


def pad_drain(inp: Inputs, n_bins: int = 24) -> Inputs:
    """Append n_bins of zero demand at every origin, with the split ratios held at the last bin (the drain)."""
    D = inp.d0.shape[0]
    d0 = np.concatenate([inp.d0, np.zeros((D, n_bins))], axis=1)
    d_o = np.concatenate([inp.d_o, np.zeros(inp.d_o.shape[:2] + (n_bins,))], axis=2)
    beta = np.concatenate([inp.beta, np.repeat(inp.beta[:, :, -1:], n_bins, axis=2)], axis=2)
    return Inputs(d0, d_o, beta)


class Stepper:
    """Batched closed-loop METANET (same setup and step as metanet.simulate)."""

    def __init__(self, net: Net, params: dict, inp: Inputs, n_param_sets: int = 1, c1=1.0, c2=1.0,
                 f1: dict | None = None, T_s: float | None = None, controlled: tuple = CONTROLLED,
                 queue: QueueLayer | None = None, record_cells: bool | tuple = True, stations: bool = True):
        if T_s is None:
            T_s = M.T_S_V4 if net.variant.startswith("v4") else M.T_S
        assert_numerics(net, params, T_s)
        self.net, self.T_s, self.f1 = net, T_s, f1
        D = inp.d0.shape[0]
        P = n_param_sets
        B = P * D
        N = net.N
        self.B, self.N, self.P, self.D = B, N, P, D
        self.T = T = T_s / 3600.0
        self.spb = int(round(300.0 / T_s))
        self.nb = inp.d0.shape[1]

        def per_b(name):
            x = np.asarray(params[name], dtype=float)
            x = np.broadcast_to(x, (P,))
            return np.repeat(x, D)[:, None]
        g = net.group
        vf_g = np.concatenate([per_b("vf1"), per_b("vf2"), per_b("vf3"), per_b("vf3")], axis=1)
        rc_g = np.concatenate([per_b("rc1"), per_b("rc2"), per_b("rc3"),
                               per_b("rc4") if "rc4" in params else per_b("rc3")], axis=1)
        a_g = np.concatenate([per_b("a1"), per_b("a2"), per_b("a3"), per_b("a4") if "a4" in params else per_b("a3")], axis=1)
        self.vf = vf_g[:, g]
        rc0 = rc_g[:, g].copy()
        self.acell = a_g[:, g]
        c1b = np.repeat(np.broadcast_to(np.asarray(c1, float), (P,)), D)[:, None] if np.ndim(c1) <= 1 else np.asarray(c1)[:, None]
        c2b = np.repeat(np.broadcast_to(np.asarray(c2, float), (P,)), D)[:, None] if np.ndim(c2) <= 1 else np.asarray(c2)[:, None]
        if net.b1_cells:
            rc0[:, net.b1_cells] *= c1b
            rc0[:, net.head1] *= per_b("theta1")[:, 0]
        if net.b2_cells:
            rc0[:, net.b2_cells] *= c2b
        self.rc0 = rc0
        self.tau = per_b("tau") / 3600.0
        self.nu, self.kappa, self.dm, self.phi = per_b("nu"), per_b("kappa"), per_b("delta_m"), per_b("phi")
        self.L, self.lam = net.L[None, :], net.lam[None, :]
        self.vcap = V_CAP_FACTOR * self.vf
        self.f1_cells = np.array(sorted(set(net.b1_cells) | set(net.b2_cells)), dtype=int)
        if f1 is not None:
            self.Dlt = np.repeat(np.broadcast_to(np.asarray(f1["Delta"], float), (P,)), D)[:, None]
            self.eta = np.repeat(np.broadcast_to(np.asarray(f1["eta"], float), (P,)), D)[:, None]
            self.mem = np.zeros((B, len(self.f1_cells)), dtype=bool)
        ne, nx = len(net.entrances), len(net.exits)
        self.ne, self.nx = ne, nx
        self.e_cell = np.array([e["cell"] for e in net.entrances], dtype=int)
        self.e_merge = np.array([e["merging"] for e in net.entrances], dtype=bool)
        self.x_cell = np.array([x["cell"] for x in net.exits], dtype=int)
        self.d0 = np.tile(inp.d0, (P, 1))
        self.d_o = np.tile(inp.d_o, (P, 1, 1))
        self.beta = np.tile(inp.beta, (P, 1, 1))
        order = []
        for i, e in enumerate(net.entrances):
            order.append((e["cell"], e["km"], 0, i))
        for j, x in enumerate(net.exits):
            order.append((x["cell"], x["km"], 1, j))
        order.sort()
        self.order = order
        # controlled entrances
        eid = {e["id"]: i for i, e in enumerate(net.entrances)}
        self.ctrl_idx = np.array([eid[c] for c in controlled], dtype=int)
        self.controlled = tuple(controlled)
        self.queue = queue
        self.stations = stations          # False: skip the station aggregation (output-only; the state is unchanged)
        self.last_r_eff = np.full((B, len(controlled)), np.inf)
        self.last_layer = np.zeros((B, len(controlled)), dtype=bool)
        self.last_net = np.zeros((B, len(controlled)), dtype=bool)
        if queue is not None:
            assert len(queue.storage_veh) == len(controlled)
            self.S = np.asarray(queue.storage_veh, float)[None, :]
            self.net_on = np.zeros((B, len(controlled)), dtype=bool)
            n_hist = max(1, int(round(queue.t_stor_s / T_s)))
            self.arr_hist = np.zeros((n_hist, B, len(controlled)))
            self._h = 0
        # initial state (§2.6), as simulate()
        rho = np.zeros((B, N))
        qprop = np.zeros((B, N))
        run = self.d0[:, 0].copy()
        ptr = 0
        for i in range(N):
            while ptr < len(order) and order[ptr][0] == i:
                _, _, kind, idx = order[ptr]
                if kind == 0:
                    run = run + self.d_o[:, idx, 0]
                else:
                    run = run - self.beta[:, idx, 0] * run
                ptr += 1
            qprop[:, i] = run
        rho, _over = free_flow_state(net, self.vf, rc0, self.acell, qprop)
        self.rho = rho
        self.v = self.vf * np.exp(-(1.0 / self.acell) * (rho / rc0) ** self.acell)
        self.w = np.zeros((B, 1 + ne))
        self.veh0 = (rho * self.L * self.lam).sum(axis=1)
        # accumulators (same as simulate)
        nb = self.nb
        self.clip_n = np.zeros(B)
        self.fl_nj, self.fl_j = np.zeros(B), np.zeros(B)
        self.nonfin = np.zeros(B, dtype=bool)
        self.st_cells = np.array([s["cell"] for s in net.stations], dtype=int)
        xid = {x["id"]: j for j, x in enumerate(net.exits)}
        self.corr = [([eid[e] for e in s["corr_entr"]], [xid[x] for x in s["corr_exit"]]) for s in net.stations]
        ns = len(net.stations)
        self.q_st = np.zeros((B, ns, nb))
        self.vden = np.zeros((B, ns, nb))
        part = isinstance(record_cells, tuple)
        self.part, self.record_cells = part, record_cells
        self.c_lo, self.c_hi = record_cells if part else (0, N)
        self.rho_rec = np.zeros((B, N, nb)) if record_cells else np.zeros((B, 1, 1))
        self.v_rec = np.zeros((B, N, nb)) if record_cells and not part else np.zeros((B, 1, 1))
        self.rc_rec = np.zeros((B, N, nb)) if record_cells else None
        self.w0_rec = np.zeros((B, nb))
        self.w0_cnt = np.zeros((B, nb))
        self.phimax = np.zeros(B)
        self.eflow = np.zeros((B, ne, nb))
        self.xflow = np.zeros((B, nx, nb))
        self.oflow = np.zeros((B, nb))
        self.qclip = np.zeros((B, 1 + ne))
        self.wrun = np.zeros((B, 1 + ne))
        self.wlong = np.zeros((B, 1 + ne))
        nc = len(controlled)
        self.acc = Acc(np.zeros((B, nb)), np.zeros((B, 1 + ne, nb)), np.zeros((B, nb)), np.zeros((B, nc, nb)),
                       np.zeros((B, nc, nb)), np.zeros((B, nc, nb)), np.zeros((B, N, nb)))
        self.k = 0                     # global step index (bin = k // spb)
        self.r_cmd = np.full((B, nc), np.inf)

    # ------------------------------------------------------------------ control
    def set_rates(self, r_cmd) -> None:
        """Commanded meter rates (B, n_ctrl) in veh/h; np.inf = meter off. Clipped to [r_min, r_max] when a queue
        layer is configured (every arm uses the same range)."""
        r = np.broadcast_to(np.asarray(r_cmd, float), (self.B, len(self.controlled))).copy()
        if self.queue is not None:
            fin = np.isfinite(r)
            r[fin] = np.clip(r[fin], self.queue.r_min, self.queue.r_max)
        self.r_cmd = r

    def _r_eff(self, dctrl: np.ndarray) -> tuple:
        """Queue layer at the current step (uses the queue before this step's update)."""
        r = self.r_cmd
        if self.queue is None:
            return r, None, None
        qp = self.queue
        wq = self.w[:, 1:][:, self.ctrl_idx]
        r_wait = wq / (qp.max_wait_s / 3600.0)
        d_hat = self.arr_hist.mean(axis=0)
        r_stor = np.where(wq > qp.f_hi * self.S, d_hat + (wq - qp.f_hi * self.S) / (qp.t_stor_s / 3600.0), 0.0)
        self.net_on = (wq >= self.S) | (self.net_on & (wq > qp.f_lo * self.S))
        metered = np.isfinite(r)
        r_e = np.minimum(qp.r_max, np.maximum(np.maximum(r, r_wait), r_stor))
        r_e = np.where(self.net_on, qp.r_max, r_e)
        r_e = np.where(metered, r_e, np.inf)
        layer = metered & (r_e > r + 1e-9)
        return r_e, layer, self.net_on & metered

    # ------------------------------------------------------------------ dynamics
    def step(self, n: int = 1) -> None:
        """Advance n steps of T (inputs held per 5-min bin, as simulate())."""
        net, T, T_s = self.net, self.T, self.T_s
        L, lam, L_, lam_ = self.L, self.lam, self.L, self.lam
        vf, acell, rc0 = self.vf, self.acell, self.rc0
        tau, nu, kappa, dm, phi = self.tau, self.nu, self.kappa, self.dm, self.phi
        B, N, ne, nx = self.B, self.N, self.ne, self.nx
        e_cell, x_cell, e_merge, order = self.e_cell, self.x_cell, self.e_merge, self.order
        for _ in range(n):
            b = self.k // self.spb
            if b >= self.nb:
                raise RuntimeError("past the last input bin")
            db0 = self.d0[:, b]
            dbo = self.d_o[:, :, b]
            bb = self.beta[:, :, b]
            rho, v, w = self.rho, self.v, self.w
            if self.f1 is not None:
                rc = rc0.copy()
                rc[:, self.f1_cells] = np.where(self.mem, (1.0 - self.Dlt) * rc0[:, self.f1_cells], rc0[:, self.f1_cells])
            else:
                rc = rc0
            q = rho * v * lam
            Vc1 = vf[:, 0] * np.exp(-1.0 / acell[:, 0])
            with np.errstate(invalid="ignore", divide="ignore"):
                rho_at_v = rc[:, 0] * (-acell[:, 0] * np.log(np.clip(v[:, 0] / vf[:, 0], 1e-12, 1.0))) ** (1.0 / acell[:, 0])
            qcap1 = lam[0, 0] * rc[:, 0] * Vc1
            qlim = np.where(v[:, 0] < Vc1, lam[0, 0] * v[:, 0] * rho_at_v, qcap1)
            q0 = np.minimum(db0 + w[:, 0] / T, qlim)
            sup = Q_O * (RHO_MAX - rho[:, e_cell]) / (RHO_MAX - rc[:, e_cell])
            qo = np.minimum(np.minimum(dbo + w[:, 1:] / T, Q_O), np.maximum(sup, 0.0))
            # meters (testbed addition): only where a finite rate is commanded, so replay is untouched
            r_e, layer, neton = self._r_eff(dbo[:, self.ctrl_idx])
            if np.isfinite(r_e).any():
                qc = qo[:, self.ctrl_idx]
                qo[:, self.ctrl_idx] = np.where(np.isfinite(r_e), np.minimum(qc, r_e), qc)
            qin = np.concatenate([q0[:, None], q[:, :-1]], axis=1)
            run = {}
            sx = np.zeros((B, nx))
            for (ci, _km, kind, idx) in order:
                r = run.get(ci, qin[:, ci])
                if kind == 0:
                    r = r + qo[:, idx]
                else:
                    s_e = bb[:, idx] * r
                    sx[:, idx] = s_e
                    r = r - s_e
                run[ci] = r
            r_cell = np.zeros((B, N))
            for i_e in range(ne):
                r_cell[:, e_cell[i_e]] += qo[:, i_e]
            rm_cell = np.zeros((B, N))
            for i_e in np.flatnonzero(e_merge):
                rm_cell[:, e_cell[i_e]] += qo[:, i_e]
            s_cell = np.zeros((B, N))
            for j in range(nx):
                s_cell[:, x_cell[j]] += sx[:, j]
            rho_n = rho + T / (L * lam) * (qin - q + r_cell - s_cell)
            Vr = vf * np.exp(-(1.0 / acell) * (rho / rc) ** acell)
            v_up = np.concatenate([v[:, :1], v[:, :-1]], axis=1)
            rho_dn = np.concatenate([rho[:, 1:], np.minimum(rho[:, -1:], rc[:, -1:])], axis=1)
            v_n = (v + (T / tau) * (Vr - v) + (T / L) * v * (v_up - v)
                   - (nu * T) / (tau * L) * (rho_dn - rho) / (rho + kappa)
                   - dm * T * rm_cell * v / (L * lam * (rho + kappa)))
            if net.phi_cell >= 0:
                i = net.phi_cell
                v_n[:, i] -= phi[:, 0] * T * 1.0 * rho[:, i] * v[:, i] ** 2 / (L[0, i] * lam[0, i] * rc[:, i])
                self.phimax = np.maximum(self.phimax, 2.0 * phi[:, 0] * T * rho[:, i] * v[:, i] / (L[0, i] * lam[0, i] * rc[:, i]))
            rho_c = np.clip(rho_n, 0.0, RHO_MAX)
            vclip_hi = v_n > self.vcap
            vfloor = v_n < V_MIN
            v_c = np.clip(v_n, V_MIN, self.vcap)
            clipped = (rho_c != rho_n) | vclip_hi | (vfloor & (rho_c < rc))
            self.clip_n += clipped.sum(axis=1)
            self.fl_nj += (vfloor & (rho_c < rc)).sum(axis=1)
            self.fl_j += (vfloor & (rho_c >= rc)).sum(axis=1)
            fin = np.isfinite(rho_c).all(axis=1) & np.isfinite(v_c).all(axis=1)
            self.nonfin |= ~fin
            rho_next, v_next = np.nan_to_num(rho_c), np.nan_to_num(v_c, nan=V_MIN)
            dall = np.concatenate([db0[:, None], dbo], axis=1)
            qall = np.concatenate([q0[:, None], qo], axis=1)
            self.qclip += T * np.maximum(dall - qall, 0.0)
            w = np.maximum(w + T * (dall - qall), 0.0)
            pos = w > 1e-9
            self.wrun = np.where(pos, self.wrun + T_s / 60.0, 0.0)
            self.wlong = np.maximum(self.wlong, self.wrun)
            for si in (range(len(self.st_cells)) if self.stations else ()):
                c = self.st_cells[si]
                cr = self.corr[si]
                qs = q[:, c] - sum(qo[:, k] for k in cr[0]) + sum(sx[:, k] for k in cr[1]) if (cr[0] or cr[1]) else q[:, c]
                self.q_st[:, si, b] += qs
                self.vden[:, si, b] += qs / v[:, c]
            if self.part:
                self.rho_rec[:, self.c_lo:self.c_hi, b] += rho[:, self.c_lo:self.c_hi]
                self.rc_rec[:, self.c_lo:self.c_hi, b] += rc[:, self.c_lo:self.c_hi]
            elif self.record_cells:
                self.rho_rec[:, :, b] += rho
                self.v_rec[:, :, b] += v
                self.rc_rec[:, :, b] += rc
            self.eflow[:, :, b] += qo
            self.w0_rec[:, b] += w[:, 0]
            self.w0_cnt[:, b] += w[:, 0] > 1e-9
            self.xflow[:, :, b] += sx
            self.oflow[:, b] += q[:, -1]
            # testbed accounting (veh-h per step, from the state at the start of the step, as the station aggregates)
            self.acc.tts_cells[:, b] += T * (rho * L_ * lam_).sum(axis=1)
            self.acc.tts_queues[:, :, b] += T * self.w
            self.acc.fft[:, b] += T * (q * L / vf).sum(axis=1)
            self.acc.r_eff[:, :, b] += np.where(np.isfinite(r_e), r_e, 0.0)
            self.acc.q_cell[:, :, b] += q
            self.last_r_eff = r_e
            if layer is not None:
                self.last_layer, self.last_net = layer, neton
            if layer is not None:
                self.acc.layer_steps[:, :, b] += layer
                self.acc.net_steps[:, :, b] += neton
                self.arr_hist[self._h % len(self.arr_hist)] = dbo[:, self.ctrl_idx]
                self._h += 1
            self.rho, self.v, self.w = rho_next, v_next, w
            if self.f1 is not None:
                rcf = rc0[:, self.f1_cells]
                self.mem = (self.rho[:, self.f1_cells] > rcf) | (self.mem & (self.rho[:, self.f1_cells] > self.eta * rcf))
            self.k += 1

    def q_cell_bins(self) -> np.ndarray:
        """Bin-mean cell outflows (veh/h) for the bins stepped so far."""
        return self.acc.q_cell / self.spb

    def run_to_end(self) -> None:
        self.step(self.nb * self.spb - self.k)

    # ------------------------------------------------------------------ outputs
    def simout(self) -> SimOut:
        """The simulate()-compatible output (valid once the whole day has been stepped)."""
        assert self.k == self.nb * self.spb, "simout() needs the whole day"
        spb, N, nb = self.spb, self.N, self.nb
        q_st = self.q_st / spb
        with np.errstate(invalid="ignore", divide="ignore"):
            v_st = np.where(self.vden > 0, q_st * spb / self.vden, np.nan)
        rho_rec, v_rec, rc_rec = self.rho_rec, self.v_rec, self.rc_rec
        if self.record_cells:
            rho_rec = rho_rec / spb
            if not self.part:
                v_rec = v_rec / spb
            rc_rec = rc_rec / spb
        return SimOut(q_st, v_st, rho_rec, v_rec, self.clip_n / (N * nb * spb), self.qclip, self.w, self.wlong, self.nonfin,
                      self.eflow / spb, self.xflow / spb, self.oflow / spb, self.veh0,
                      (self.rho * self.L * self.lam).sum(axis=1), self.rho, self.v, self.fl_nj / (N * nb * spb),
                      self.fl_j / (N * nb * spb), rc_rec, self.w0_rec / spb, self.w0_cnt, self.phimax)
