"""Testbed stage-1b metering authority screen, KILL-only (docs/plans/day_pattern_testbed_stage1b_screen.md v1 + §11;
D5.11, D5.12). Frozen v5 nominal, closed-loop stepper vsl_lab/plants/metanet_ctrl.py, the 12 train-source days only.

python -m vsl_lab.jobs.testbed_screen inputs                 # demand sources per ramp-day -> testbed_screen_inputs.json
python -m vsl_lab.jobs.testbed_screen smoke --gate-ok        # timing of one full generation of the largest arm
python -m vsl_lab.jobs.testbed_screen run --gate-ok          # checks, CONST, per-day arms, decision (run once)
python -m vsl_lab.jobs.testbed_screen resume --run-id ID --gate-ok   # arms + decision after a load-gate pause
(worker, inside the run's batches only: python -m vsl_lab.jobs.testbed_screen opt --run-id ID --set 10 --storage x1 --arm TOD-day)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

from vsl_lab.config import REPO_ROOT, RUNS_ROOT
from vsl_lab.data import metanet_inputs as I
from vsl_lab.jobs import metanet_calibrate as C
from vsl_lab.plants import metanet as M
from vsl_lab.plants import metanet_ctrl as MC

LAB = REPO_ROOT / "docs/lab/day_pattern"
SPLIT = LAB / "testbed_day_split.json"
FACTS5 = LAB / "metanet_v5_precal_facts.json"
REC5 = LAB / "metanet_v5_calibration.json"
INPUTS_LIST = LAB / "testbed_screen_inputs.json"
PREREG = REPO_ROOT / "docs/plans/day_pattern_testbed_stage1b_screen.md"
OUT = LAB / "testbed_screen.json"
RAW = RUNS_ROOT / "day_pattern" / "testbed_screen"
CODE = [Path(__file__), REPO_ROOT / "vsl_lab/plants/metanet_ctrl.py"]

METERS = {"10": ("E1", "E2", "E3", "E4", "E5", "E6", "E9", "E12", "E13", "E14"), "4": ("E9", "E12", "E13", "E14")}
QDETS = {"E1": ["3685"], "E2": ["3678"], "E4": ["3673", "3674", "3675"], "E5": ["3669"], "E6": ["2000"],
         "E9": ["3663"], "E12": ["7103"], "E13": ["5426"], "E14": ["5431"]}          # E3: replay (3679 has no 2023 data)
STORAGE_FT = {"E1": 326, "E2": 350, "E3": 550, "E4": 660, "E5": 480, "E6": 370, "E9": 300, "E12": 450, "E13": 500, "E14": 420}
S_JAM_M = 8.94                                    # IRIS jam density 180 veh/lane-mile [VERIFY]
R_MIN, R_MAX = 240.0, 1800.0                      # [VERIFY: IRIS density-adaptive range]
B05, B23, NPAD = 12, 228, 24                      # 05:00, 23:00 (5-min model bins from 04:00), drain bins
M05, M23 = 60.0, 1140.0                           # minutes from 04:00
PERIODS = [(12, 72), (72, 132), (132, 180), (180, 228)]   # 05-10, 10-15, 15-19, 19-23
FINE_MIN = (480.0, 960.0)                          # 12:00-20:00 in minutes from 04:00
FINE_BINS = (96, 192)
PERIOD_STEPS = 80                                  # 60 s at T = 0.75 s
ARMS = ("TOD-day", "TOD-fine-day", "ALINEA-day", "ALINEA-B-day")
SEED_ORDER = [(s, a) for s in ("10", "4") for a in ("CONST",) + ARMS]
SEED_BASE, BOOT_SEED, SMOKE_SEED = 7193010, 7193099, 7193000
POOLED_DAY_INDEX = 99
B1_SENSE, B2_SENSE = [26], [32, 33]
GEN_BLOCK, IMPROVE_TOL, GEN_CAP, RESTARTS = 50, 0.002, 400, 2
LOAD_WAIT_S = 1800


# ---------------------------------------------------------------- setup, guards, provenance
def train_days() -> list:
    split = json.loads(SPLIT.read_text())
    cal = set(json.loads(FACTS5.read_text())["days"])
    days = list(split["train"])
    assert len(days) == 12 and all(d in cal for d in days), "screen days must be the 12 train-source calibration days"
    assert not (set(days) & (set(split["val"]) | set(split["test"]))), "train/val/test overlap"
    return days


def provenance_guards(days: list) -> None:
    from vsl_lab.jobs import metanet_gate as G
    facts = json.loads(FACTS5.read_text())
    sha = hashlib.sha256((C.RUNS / "calib_data.npz").read_bytes()).hexdigest()
    assert sha == facts["calib_data_sha256"], "calib_data.npz differs from the committed facts"
    assert not set(days) & set(str(d) for d in G.val_days()), "a screen day is a v5 validation day"


def storage(row: str, meters: tuple) -> tuple:
    out = []
    for e in meters:
        s = STORAGE_FT[e] * 0.3048 / S_JAM_M
        if row == "gen":
            s *= 3.0 if e == "E4" else 1.25
        out.append(s)
    return tuple(out)


def _fill(q: np.ndarray) -> np.ndarray:
    x = q.copy()
    bad = ~np.isfinite(x)
    if bad.any() and (~bad).any():
        x[bad] = np.interp(np.flatnonzero(bad), np.flatnonzero(~bad), x[~bad])
    return x


def build_inputs(days: list) -> tuple:
    """Replay inputs of the days with the metered ramps' demand rebuilt from Queue arrivals (§3), padded with the drain."""
    data = C.load_data()
    cal = [str(d) for d in data["days"]]
    idx = [cal.index(d) for d in days]
    net = M.build_network(C.VARIANT)
    eid = {e["id"]: i for i, e in enumerate(net.entrances)}
    d_o = data["d_o"][idx].copy()
    listing = {}
    for k, day in enumerate(days):
        listing[day] = {}
        for e in METERS["10"]:
            rep = data["d_o"][idx[k], eid[e], :]
            if e not in QDETS:
                listing[day][e] = {"source": "replay", "ratio": None}
                continue
            ls = [I.fit_lane(day, det, "input") for det in QDETS[e]]
            if not all(l["valid"] for l in ls):
                listing[day][e] = {"source": "replay", "ratio": None, "why": "queue lane-day invalid"}
                continue
            arr = _fill(np.sum([l["q"] for l in ls], axis=0))
            ratio = float(arr[B05:B23].sum() / rep[B05:B23].sum())
            if abs(ratio - 1.0) <= 0.05:
                d_o[k, eid[e], :] = arr
                listing[day][e] = {"source": "queue", "ratio": ratio}
            else:
                d_o[k, eid[e], :] = arr / ratio
                listing[day][e] = {"source": "queue_rescaled", "ratio": ratio}
    inp = MC.pad_drain(M.Inputs(data["d0"][idx], d_o, data["beta"][idx]), NPAD)
    return net, inp, listing


def inputs_sha(inp: M.Inputs) -> str:
    h = hashlib.sha256()
    for a in (inp.d0, inp.d_o, inp.beta):
        h.update(np.ascontiguousarray(a, dtype=np.float64).tobytes())
    return h.hexdigest()


def params() -> dict:
    return {k: np.array([v]) for k, v in json.loads(REC5.read_text())["frozen_params"].items()}


def _sub(inp: M.Inputs, rows: list) -> M.Inputs:
    return M.Inputs(inp.d0[rows], inp.d_o[rows], inp.beta[rows])


# ---------------------------------------------------------------- policies (batched over rows)
class Policy:
    needs_sense = False

    def rates(self, st, minute):
        raise NotImplementedError

    def observe(self, st):
        pass

    def post_step(self, st):
        pass

    def after_period(self, st):
        pass


class Table(Policy):
    """CONST / TOD-day: r (B, nc, n_bins) per 5-min bin (their windows are bin-aligned); np.inf = off."""

    def __init__(self, r_bins):
        self.r = r_bins

    def rates(self, st, minute):
        return self.r[:, :, st.k // st.spb]


class Window(Policy):
    """TOD-fine-day: per row and meter, rate inside [t_on, t_off) (minutes from 04:00, 60-s resolution), NC outside."""

    def __init__(self, ton, toff, rate):
        self.ton, self.toff, self.rate = ton, toff, rate                    # (B, nc) each; inactive meters: ton = toff

    def rates(self, st, minute):
        return np.where((minute >= self.ton) & (minute < self.toff), self.rate, np.inf)


class Alinea(Policy):
    """Density ALINEA (§4): r <- clip(r_prev + K (rho* - rho_bar), 240, 1800) every 60 s; rho_bar = the 60-s mean of the
    sensed cell (a ramp with several sensed cells uses the max of the cells' 60-s means); anti-windup: if the queue
    layer or the hard net bound at any step of the period, r_prev <- the last bound applied r_eff (§11)."""
    needs_sense = True

    def __init__(self, K, rho_set, sense: list, active):
        self.K, self.rs, self.sense, self.active = K, rho_set, sense, active
        self.cells = sorted({c for cs in sense for c in cs})
        self.col = {c: j for j, c in enumerate(self.cells)}
        B, nc = K.shape
        self.acc = np.zeros((B, len(self.cells)))
        self.n = 0
        self.rbar = None
        self.r_prev = np.full((B, nc), R_MAX)
        self.r_cmd = np.full((B, nc), np.inf)
        self._r = np.full((B, nc), R_MAX)
        self.bound = np.zeros((B, nc), bool)
        self.bound_r = np.full((B, nc), R_MAX)

    def observe(self, st):
        self.acc += st.rho[:, self.cells]
        self.n += 1

    def post_step(self, st):
        b = (st.last_layer | st.last_net) & np.isfinite(self.r_cmd)
        self.bound_r = np.where(b, np.minimum(st.last_r_eff, R_MAX), self.bound_r)
        self.bound |= b

    def rates(self, st, minute):
        if not (M05 <= minute < M23):
            self.r_prev[:] = R_MAX
            self.r_cmd = np.full(self.K.shape, np.inf)
            return self.r_cmd
        rho = self.rbar if self.rbar is not None else np.zeros(self.K.shape)
        self._r = np.clip(self.r_prev + self.K * (self.rs - rho), R_MIN, R_MAX)
        self.r_cmd = np.where(self.active, self._r, np.inf)
        return self.r_cmd

    def after_period(self, st):
        means = self.acc / max(self.n, 1)
        self.rbar = np.stack([means[:, [self.col[c] for c in cs]].max(axis=1) for cs in self.sense], axis=1)
        self.acc[:] = 0.0
        self.n = 0
        if np.isfinite(self.r_cmd).any():
            self.r_prev = np.where(self.bound, self.bound_r, self._r)
        self.bound[:] = False


def rollout(net, p, inp, meters, srow, policy: Policy) -> MC.Stepper:
    st = MC.Stepper(net, p, inp, controlled=meters, queue=MC.QueueLayer(storage_veh=storage(srow, meters), r_min=R_MIN,
                    r_max=R_MAX), record_cells=False, stations=False)
    total = st.nb * st.spb
    while st.k < total:
        minute = st.k * st.T_s / 60.0
        st.set_rates(policy.rates(st, minute))
        n = min(PERIOD_STEPS, total - st.k)
        if policy.needs_sense:
            for _ in range(n):
                policy.observe(st)
                st.step(1)
                policy.post_step(st)
        else:
            st.step(n)
        policy.after_period(st)
    return st


def J_of(st) -> np.ndarray:
    a = st.acc
    return (a.tts_cells[:, B05:] + a.tts_queues[:, :, B05:].sum(axis=1) - a.fft[:, B05:]).sum(axis=1)


def left_of(st) -> np.ndarray:
    return (st.rho * st.L * st.lam).sum(axis=1) + st.w.sum(axis=1)


# ---------------------------------------------------------------- decoding of normalised parameters (§4, §11)
def ramp_max(inp, rows, meters, net, b0, b1):
    eid = {e["id"]: i for i, e in enumerate(net.entrances)}
    return np.stack([inp.d_o[rows][:, eid[e], b0:b1].max(axis=1) for e in meters], axis=1)    # (len(rows), nc)


def decode(arm: str, u: np.ndarray, ctx: dict) -> Policy:
    """u (B, W) in [0,1] (only the first len(ctx coords) columns are read) -> policy for B rows of ONE day."""
    B, nc, nb = u.shape[0], ctx["nc"], ctx["nb"]
    if arm == "CONST":
        r = np.full((B, nc, nb), np.inf)
        for j, (i, hi) in enumerate(ctx["coords"]):
            r[:, i, B05:B23] = (R_MIN + u[:, j] * (hi - R_MIN))[:, None]
        return Table(r)
    if arm == "TOD-day":
        r = np.full((B, nc, nb), np.inf)
        for j, (i, pi, hi) in enumerate(ctx["coords"]):
            b0, b1 = PERIODS[pi]
            r[:, i, b0:b1] = (R_MIN + u[:, j] * (hi - R_MIN))[:, None]
        return Table(r)
    if arm == "TOD-fine-day":
        ton = np.zeros((B, nc))
        toff = np.zeros((B, nc))
        rate = np.full((B, nc), np.inf)
        span = FINE_MIN[1] - FINE_MIN[0]
        for j, (i, hi) in enumerate(ctx["coords"]):
            ton[:, i] = FINE_MIN[0] + np.round(u[:, 3 * j] * span)
            toff[:, i] = FINE_MIN[0] + np.round(u[:, 3 * j + 1] * span)
            rate[:, i] = R_MIN + u[:, 3 * j + 2] * (hi - R_MIN)
        return Window(ton, toff, rate)
    K = np.full((B, nc), 1.0)
    rs = np.full((B, nc), 1e9)
    act = np.zeros((B, nc), bool)
    for j, (i, rcs) in enumerate(ctx["coords"]):
        K[:, i] = 10 ** (np.log10(5.0) + u[:, 2 * j] * (np.log10(300.0) - np.log10(5.0)))
        rs[:, i] = (0.6 + 0.6 * u[:, 2 * j + 1]) * rcs
        act[:, i] = True
    return Alinea(K, rs, ctx["sense"], act)


def sense_lists(arm, net, meters) -> list:
    cells = sorted(s["cell"] for s in net.stations)
    eid = {e["id"]: i for i, e in enumerate(net.entrances)}
    out = []
    for e in meters:
        if arm == "ALINEA-day":
            out.append([min(c for c in cells if c > net.entrances[eid[e]]["cell"])])
        else:
            out.append(B2_SENSE if e == "E14" else B1_SENSE)
    return out


def context(arm, net, p, inp, rows, meters, const_rates=None) -> dict:
    """Active coordinates for one day (or the pooled days for CONST), boxes and the warm start x0 (§11)."""
    nc, nb = len(meters), inp.d0.shape[1]
    ctx = {"nc": nc, "nb": nb, "coords": []}
    x0 = []
    if arm == "CONST":
        hi = ramp_max(inp, rows, meters, net, B05, B23).max(axis=0)          # box top: max over the 12 days (§11)
        for i in range(nc):
            if hi[i] > R_MIN:
                ctx["coords"].append((i, float(hi[i])))
                x0.append(1.0)
    elif arm in ("TOD-day", "TOD-fine-day"):
        top = ramp_max(inp, rows[:1], meters, net, B05, B23)[0]                # box top: the ramp-day 05-23 max (§4)
        for i in range(nc):
            c = const_rates[i] if const_rates is not None else np.inf
            c0 = 1.0 if not np.isfinite(c) else float(np.clip((c - R_MIN) / (top[i] - R_MIN), 0, 1)) if top[i] > R_MIN else 1.0
            if arm == "TOD-day":
                for pi, (b0, b1) in enumerate(PERIODS):
                    if ramp_max(inp, rows[:1], meters, net, b0, b1)[0, i] > R_MIN:   # drop rule: the window max
                        ctx["coords"].append((i, pi, float(top[i])))
                        x0.append(c0)
            elif ramp_max(inp, rows[:1], meters, net, *FINE_BINS)[0, i] > R_MIN:
                ctx["coords"].append((i, float(top[i])))
                x0 += [0.0, 1.0, c0]
    else:
        st = MC.Stepper(net, p, _sub(inp, rows[:1]), record_cells=False, stations=False)
        rc = st.rc0[0]
        ctx["sense"] = sense_lists(arm, net, meters)
        hi = ramp_max(inp, rows[:1], meters, net, B05, B23)[0]
        for i in range(nc):
            if hi[i] > R_MIN:
                ctx["coords"].append((i, float(rc[ctx["sense"][i][0]])))
                x0 += [0.5, (1.0 - 0.6) / 0.6]
    ctx["x0"] = np.array(x0, float)
    return ctx


# ---------------------------------------------------------------- evaluation and optimisation
def _pad(U: list) -> np.ndarray:
    W = max([len(x) for x in U] + [1])
    out = np.zeros((len(U), W))
    for k, x in enumerate(U):
        out[k, :len(x)] = x
    return out


def _rollout_eval(arm, net, p, inp, meters, srow, rows, U, ctxs) -> MC.Stepper:
    batch = _sub(inp, rows)
    Up = _pad(list(U))
    pols = [decode(arm, Up[k:k + 1], ctxs[rows[k]]) for k in range(len(rows))]
    if isinstance(pols[0], Table):
        pol = Table(np.concatenate([q.r for q in pols], axis=0))
    elif isinstance(pols[0], Window):
        pol = Window(*(np.concatenate([getattr(q, a) for q in pols]) for a in ("ton", "toff", "rate")))
    else:
        assert all(q.sense == pols[0].sense for q in pols)
        pol = Alinea(np.concatenate([q.K for q in pols]), np.concatenate([q.rs for q in pols]), pols[0].sense,
                     np.concatenate([q.active for q in pols]))
    return rollout(net, p, batch, meters, srow, pol)


def evaluate(arm, net, p, inp, meters, srow, rows, U, ctxs) -> np.ndarray:
    return J_of(_rollout_eval(arm, net, p, inp, meters, srow, rows, U, ctxs))


def seed_for(set_, arm, day_index, restart) -> int:
    k = SEED_ORDER.index((set_, arm))
    return int(np.random.SeedSequence([SEED_BASE + k, day_index, restart]).generate_state(1)[0] % (2 ** 31 - 2) + 1)


def make_es(x0, seed):
    import cma
    g = np.random.default_rng(seed)
    return cma.CMAEvolutionStrategy(list(x0), 0.3, {"bounds": [0, 1], "verbose": -9, "seed": np.nan,
                                                    "randn": (lambda *s, g=g: g.standard_normal(s))})


def optimise(arm, set_, srow, net, p, inp, days, J_nc, const_rates=None, cap=GEN_CAP, evaluate_fn=None) -> dict:
    """Per-day (pooled for CONST) CMA-ES, 2 restarts; x0 is evaluated at generation 0 (§11); 50-generation
    convergence blocks; all ES advance in one padded batch; per-ES RNG from the pre-registered seed map."""
    ev = evaluate_fn or evaluate
    meters = METERS[set_]
    D = len(days)
    pooled = arm == "CONST"
    units = [POOLED_DAY_INDEX] if pooled else list(range(D))
    if pooled:
        cpool = context("CONST", net, p, inp, list(range(D)), meters)
        ctxs = {d: cpool for d in range(D)}
    else:
        ctxs = {d: context(arm, net, p, inp, [d], meters, const_rates) for d in range(D)}
    es, best, trace, done = {}, {}, {}, {}
    for u_ in units:
        x0 = ctxs[0 if pooled else u_]["x0"]
        for r in range(RESTARTS):
            key = (u_, r)
            trace[key] = []
            if len(x0) == 0:
                done[key] = True
                best[key] = (0.0 if pooled else float(J_nc[u_]), np.zeros(0))
                continue
            es[key] = make_es(x0, seed_for(set_, arm, u_, r))
            best[key], done[key] = (np.inf, None), False

    def score(J, keys_X):
        pos, out = 0, {}
        for key, X in keys_X:
            f = []
            for _ in X:
                if pooled:
                    jd = J[pos:pos + D]
                    pos += D
                    f.append(float(np.median((jd - J_nc) / J_nc)))
                else:
                    f.append(float(J[pos]))
                    pos += 1
            out[key] = f
        return out

    def batch(keys_X):
        rows, U = [], []
        for key, X in keys_X:
            for x in X:
                for d in (range(D) if pooled else [key[0]]):
                    rows.append(d)
                    U.append(np.asarray(x, float))
        return rows, U

    # generation 0: the warm start of every active key
    k0 = [(key, [ctxs[0 if pooled else key[0]]["x0"]]) for key in es]
    if k0:
        rows, U = batch(k0)
        f0 = score(ev(arm, net, p, inp, meters, srow, rows, U, ctxs), k0)
        for key, _ in k0:
            best[key] = (f0[key][0], np.array(ctxs[0 if pooled else key[0]]["x0"]))
            trace[key].append(best[key][0])
    gen = 0
    while not all(done.values()) and gen < cap:
        asks = [(key, e.ask()) for key, e in es.items() if not done[key]]
        rows, U = batch(asks)
        f = score(ev(arm, net, p, inp, meters, srow, rows, U, ctxs), asks)
        for key, X in asks:
            es[key].tell(X, f[key])
            i = int(np.argmin(f[key]))
            if f[key][i] < best[key][0]:
                best[key] = (f[key][i], np.array(X[i]))
            trace[key].append(best[key][0])
        gen += 1
        if gen % GEN_BLOCK == 0:
            for key, _ in asks:
                tr = trace[key]
                scale = 1.0 if pooled else float(J_nc[key[0]])
                if len(tr) > GEN_BLOCK and (tr[-GEN_BLOCK - 1] - tr[-1]) < IMPROVE_TOL * scale:
                    done[key] = True
    out = {"arm": arm, "set": set_, "storage": srow, "generations": gen, "units": {}}
    for u_ in units:
        rs = [best[(u_, r)] for r in range(RESTARTS)]
        b = min(rs, key=lambda t: t[0])
        name = "pooled" if pooled else days[u_]
        out["units"][name] = {"best": b[0], "x": np.asarray(b[1]).tolist(), "restart_values": [t[0] for t in rs],
                              "restart_spread": float(max(t[0] for t in rs) - min(t[0] for t in rs)),
                              "traces": [trace[(u_, r)] for r in range(RESTARTS)],
                              "ctx_coords": [list(c) for c in ctxs[0 if pooled else u_]["coords"]]}
    # final evaluation of each day's best: per-day J (pooled CONST), queue-layer / hard-net minutes, vehicles left
    rows, U, idle = [], [], []
    for k, d in enumerate(days):
        x = np.array(out["units"]["pooled" if pooled else d]["x"], float)
        if x.size == 0:
            idle.append(k)
            continue
        rows.append(k)
        U.append(x)
    fin = {"J_d": {}, "layer_min": {}, "net_min": {}, "left_veh": {}}
    for k in idle:                                          # no active coordinate on that day: the arm is NC there
        d = days[k]
        fin["J_d"][d], fin["layer_min"][d], fin["net_min"][d], fin["left_veh"][d] = float(J_nc[k]), 0.0, 0.0, None
    if rows:
        st = _rollout_eval(arm, net, p, inp, meters, srow, rows, U, ctxs)
        Jd = J_of(st)
        for j, k in enumerate(rows):
            d = days[k]
            fin["J_d"][d] = float(Jd[j])
            fin["layer_min"][d] = float(st.acc.layer_steps[j].sum() * st.T_s / 60)
            fin["net_min"][d] = float(st.acc.net_steps[j].sum() * st.T_s / 60)
            fin["left_veh"][d] = float(left_of(st)[j])
            if not pooled:
                assert fin["J_d"][d] == out["units"][d]["best"], f"re-evaluation of the best differs on {d} (T3)"
    out["final"] = fin
    return out


def const_rates_from(res: dict, ctx: dict) -> np.ndarray:
    r = np.full(ctx["nc"], np.inf)
    x = np.array(res["units"]["pooled"]["x"])
    for j, (i, hi) in enumerate(ctx["coords"]):
        r[i] = R_MIN + x[j] * (hi - R_MIN)
    return r


# ---------------------------------------------------------------- checks
def nc_run(net, p, inp, meters, srow) -> MC.Stepper:
    return rollout(net, p, inp, meters, srow, Table(np.full((inp.d0.shape[0], len(meters), inp.d0.shape[1]), np.inf)))


def head_inflow(st, net) -> dict:
    eid = {e["id"]: i for i, e in enumerate(net.entrances)}
    q = st.q_cell_bins()
    ef = st.eflow / st.spb
    b1 = q[:, 26, 132:180] + ef[:, eid["E13"], 132:180]
    b2 = q[:, 31, 132:180] + ef[:, eid["E14"], 132:180]
    return {"B1": b1.mean(axis=1), "B2": b2.mean(axis=1)}


def t0(net, p, inp, J_nc, hin_nc) -> dict:
    out = {}
    D = inp.d0.shape[0]
    for head, meters in (("B1", ("E1", "E2", "E3", "E4", "E5", "E6", "E9", "E12", "E13")), ("B2", ("E14",))):
        r = np.full((D, len(meters), inp.d0.shape[1]), np.inf)
        r[:, :, B05:B23] = R_MIN
        st = rollout(net, p, inp, meters, "x1", Table(r))
        J = J_of(st)
        hin = head_inflow(st, net)[head]
        ok = (hin < hin_nc[head]) & (np.abs(J - J_nc) / J_nc > 0.01)
        out[head] = {"days_ok": int(ok.sum()), "PASS": bool(ok.sum() >= 3), "dJ_rel": ((J - J_nc) / J_nc).tolist(),
                     "inflow_nc": hin_nc[head].tolist(), "inflow_240": hin.tolist()}
    return out


def t1(net, p, inp) -> dict:
    """NC over-critical minutes 05-23 h, counted per step (rho > rho_cr) at cell 26 and at cells 32-33."""
    st = MC.Stepper(net, p, inp, record_cells=False, stations=False)
    c26, c32 = np.zeros(st.B), np.zeros(st.B)
    for _ in range(B23 * st.spb):
        if st.k >= B05 * st.spb:
            c26 += st.rho[:, 26] > st.rc0[:, 26]
            c32 += (st.rho[:, 32] > st.rc0[:, 32]) | (st.rho[:, 33] > st.rc0[:, 33])
        st.step(1)
    return {"B1_cell26_min": (c26 * st.T_s / 60).tolist(), "B2_cells32_33_min": (c32 * st.T_s / 60).tolist()}


def t3(net, p, inp, J_nc, J_nc2) -> dict:
    """Determinism: NC twice, and fixed CONST / TOD-fine / ALINEA-B candidates alone vs inside a mixed padded batch."""
    meters = METERS["10"]
    ok = bool(np.array_equal(J_nc, J_nc2))
    ctxs = {d: context("CONST", net, p, inp, list(range(inp.d0.shape[0])), meters) for d in range(inp.d0.shape[0])}
    detail = {"nc": ok}
    for arm, cx in (("CONST", ctxs), ("TOD-fine-day", {0: context("TOD-fine-day", net, p, inp, [0], meters)}),
                    ("ALINEA-B-day", {0: context("ALINEA-B-day", net, p, inp, [0], meters)})):
        x = np.full(len(cx[0]["x0"]), 0.4)
        a = evaluate(arm, net, p, inp, meters, "x1", [0], [x], cx)
        b = evaluate(arm, net, p, inp, meters, "x1", [0, 0, 0], [x, np.full(len(x), 0.9), x], cx)
        same = bool(a[0] == b[0] == b[2])
        detail[arm] = same
        ok &= same
    return {"PASS": ok, "detail": detail}


# ---------------------------------------------------------------- CLI
def _committed(path: Path) -> bool:
    r = subprocess.run(["git", "-C", str(REPO_ROOT), "ls-files", "--error-unmatch", str(path)], capture_output=True)
    d = subprocess.run(["git", "-C", str(REPO_ROOT), "diff", "--quiet", "HEAD", "--", str(path)])
    return r.returncode == 0 and d.returncode == 0


def _head() -> str:
    return subprocess.run(["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()


def cmd_inputs() -> int:
    days = train_days()
    _, inp, listing = build_inputs(days)
    INPUTS_LIST.write_text(json.dumps({"days": days, "listing": listing, "inputs_sha256": inputs_sha(inp),
                                       "rule": "§3 of the screen v1"}, indent=1))
    print(json.dumps({d: {e: v["source"] for e, v in r.items()} for d, r in listing.items()}))
    return 0


def _load_all():
    days = train_days()
    provenance_guards(days)
    net, inp, listing = build_inputs(days)
    rec = json.loads(INPUTS_LIST.read_text())
    assert rec["listing"] == json.loads(json.dumps(listing)), "inputs listing changed"
    assert rec["inputs_sha256"] == inputs_sha(inp), "padded inputs differ from the committed listing's hash"
    return days, net, inp


def _run_dir(run_id: str) -> Path:
    return RAW / f"run_{run_id}"


def cmd_opt(set_, srow, arm, run_id) -> int:
    assert run_id, "opt runs only inside a screen run (--run-id)"
    rd = _run_dir(run_id)
    assert (rd / "stamp.json").exists(), "unknown run id"
    stamp = json.loads((rd / "stamp.json").read_text())
    days, net, inp = _load_all()
    p = params()
    J_nc = J_of(nc_run(net, p, inp, METERS[set_], srow))
    assert J_nc.tolist() == stamp["J_nc"], "NC J differs from the run's own"
    const = None
    if arm != "CONST":
        cres = json.loads((rd / f"opt_{set_}_{srow}_CONST.json").read_text())
        assert cres["run_id"] == run_id
        const = const_rates_from(cres, context("CONST", net, p, inp, list(range(len(days))), METERS[set_]))
    res = optimise(arm, set_, srow, net, p, inp, days, J_nc, const)
    res |= {"run_id": run_id, "head": _head(), "J_nc": J_nc.tolist()}
    (rd / f"opt_{set_}_{srow}_{arm}.json").write_text(json.dumps(res, default=float))
    print(json.dumps({"ok": True, "arm": arm, "set": set_, "storage": srow, "generations": res["generations"]}))
    return 0


def cmd_smoke(gate_ok) -> int:
    from vsl_lab.ops.scheduler import sim_start_gate
    sim_start_gate(gate_ok)
    days, net, inp = _load_all()
    p = params()
    meters = METERS["10"]
    t = time.time()
    nc_run(net, p, inp, meters, "x1")
    t_nc = time.time() - t
    ctxs = {d: context("TOD-day", net, p, inp, [d], meters) for d in range(len(days))}
    rows, U = [], []
    for d in range(len(days)):
        for r in range(RESTARTS):
            es = make_es(ctxs[d]["x0"], SMOKE_SEED + 2 * d + r)
            for x in es.ask():
                rows.append(d)
                U.append(np.asarray(x))
    t = time.time()
    evaluate("TOD-day", net, p, inp, meters, "x1", rows, U, ctxs)
    t_gen = time.time() - t
    print(json.dumps({"nc_12days_s": round(t_nc, 1), "tod_day_full_generation_s": round(t_gen, 1), "batch_rows": len(rows),
                      "hours_at_cap_per_arm_job": round(t_gen * GEN_CAP / 3600, 1), "note": "timing only; no J shown"}))
    return 0


def _wait_load() -> bool:
    from vsl_lab.ops.thermal import load_fraction
    from vsl_lab.config import SIM_START_MAX_LOAD
    t0_ = time.time()
    while time.time() - t0_ < LOAD_WAIT_S:
        if load_fraction() < SIM_START_MAX_LOAD:
            return True
        time.sleep(30)
    return False


def _batch(jobs, bdir, workers) -> None:
    from vsl_lab.ops.scheduler import run_batch
    rep = run_batch(jobs, bdir, workers, gate_ok=True)
    assert rep.n_ok == rep.n_jobs, f"{rep.n_jobs - rep.n_ok} worker(s) failed: see {bdir}"


def _jobs(run_id, arms):
    from vsl_lab.ops.scheduler import Job
    return [Job(jid=f"opt_{s}_{r}_{a}", argv=["vsl_lab.jobs.testbed_screen", "opt", "--run-id", run_id, "--set", s,
                                              "--storage", r, "--arm", a]) for s in ("10", "4") for r in ("x1", "gen") for a in arms]


def cmd_run(gate_ok, resume_id=None) -> int:
    from vsl_lab.ops import ledger
    from vsl_lab.ops.scheduler import sim_start_gate
    assert not OUT.exists(), "the screen already ran (run once)"
    for f in [SPLIT, INPUTS_LIST, PREREG] + CODE:
        assert _committed(f), f"{f} must be committed and unchanged"
    sim_start_gate(gate_ok)
    days, net, inp = _load_all()
    p = params()
    run_id = resume_id or time.strftime("%Y%m%d-%H%M%S")
    rd = _run_dir(run_id)
    try:
        if resume_id is None:
            assert not rd.exists(), "run directory exists"
            rd.mkdir(parents=True)
            ledger.append("DP", "testbed-1b", "S", "testbed_screen_started", {"days": days, "run_id": run_id, "head": _head()},
                          "7193010-7193099", 0, {}, {"status": "started"}, notes=str(rd))
            st_nc = nc_run(net, p, inp, METERS["10"], "x1")
            J_nc = J_of(st_nc)
            J_nc2 = J_of(nc_run(net, p, inp, METERS["10"], "x1"))
            checks = {"T3": t3(net, p, inp, J_nc, J_nc2), "T0": t0(net, p, inp, J_nc, head_inflow(st_nc, net)),
                      "T1": t1(net, p, inp), "left_nc": left_of(st_nc).tolist()}
            (rd / "stamp.json").write_text(json.dumps({"run_id": run_id, "head": _head(), "J_nc": J_nc.tolist()}))
            (rd / "checks.json").write_text(json.dumps(checks, default=float))
            if not checks["T3"]["PASS"]:
                ledger.append("DP", "testbed-1b", "S", "testbed_screen_T3_fail", {"run_id": run_id}, "-", 0, {},
                              checks["T3"], notes=str(rd))
                raise SystemExit("T3 FAIL: stop, fix, re-run everything affected, log both")
            _batch(_jobs(run_id, ("CONST",)), rd / "batch_const", 4)
        else:
            checks = json.loads((rd / "checks.json").read_text())
            J_nc = np.array(json.loads((rd / "stamp.json").read_text())["J_nc"])
        if not (rd / "arms_done").exists():
            if not _wait_load():
                ledger.append("DP", "testbed-1b", "S", "testbed_screen_paused", {"run_id": run_id}, "-", 0, {},
                              {"status": "load gate before the arms batch; resume with: resume --run-id " + run_id}, notes=str(rd))
                raise SystemExit("load gate: resume later with --run-id " + run_id)
            _batch(_jobs(run_id, ARMS), rd / "batch_arms", 16)
            (rd / "arms_done").write_text("ok")
        res = decide(days, J_nc, checks, rd, run_id)
        OUT.write_text(json.dumps(res, indent=1, default=float))
        report(res, rd)
        ledger.append("DP", "testbed-1b", "S", "testbed_screen", {"days": days, "run_id": run_id}, "7193010-7193099", 0, {},
                      {"outcome": res["outcome"], "median_rel": res["median_rel"]}, notes=str(rd))
        print(json.dumps({"outcome": res["outcome"], "median_rel": res["median_rel"]}))
        return 0
    except SystemExit:
        raise
    except Exception as exc:
        ledger.append("DP", "testbed-1b", "S", "testbed_screen_failed", {"run_id": run_id}, "-", 0, {},
                      {"error": f"{type(exc).__name__}: {exc}"}, notes=str(rd))
        raise


def decide(days, J_nc, checks, rd: Path, run_id: str) -> dict:
    rng = np.random.default_rng(BOOT_SEED)
    out = {"days": days, "run_id": run_id, "J_nc": list(map(float, J_nc)), "checks": checks, "rows": {}}
    strata = json.loads(SPLIT.read_text())["strata"]
    for set_ in ("10", "4"):
        for srow in ("x1", "gen"):
            arms = {a: json.loads((rd / f"opt_{set_}_{srow}_{a}.json").read_text()) for a in ("CONST",) + ARMS}
            for a, r in arms.items():
                assert r["run_id"] == run_id and r["J_nc"] == list(map(float, J_nc)), f"stale or foreign result: {a}"
            Jc = {a: np.array([arms[a]["final"]["J_d"][d] for d in days]) for a in ("CONST",) + ARMS}
            E = np.min(np.stack([J_nc] + [Jc[a] for a in ("CONST",) + ARMS]), axis=0)
            rel = (E - J_nc) / J_nc
            boot = [np.median(rng.choice(rel, len(rel))) for _ in range(10000)]
            fin = {a: arms[a]["final"] for a in arms}
            out["rows"][f"{set_}_{srow}"] = {
                "rel_d": dict(zip(days, rel.tolist())), "median": float(np.median(rel)),
                "ci95": [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))],
                "median_both": float(np.median([r for d, r in zip(days, rel) if d in strata["both"]])),
                "median_B1only": float(np.median([r for d, r in zip(days, rel) if d in strata["B1_only"]])),
                "median_without_20230705": float(np.median([r for d, r in zip(days, rel) if d != "20230705"])),
                "arm_median_rel": {a: float(np.median((Jc[a] - J_nc) / J_nc)) for a in ("CONST",) + ARMS},
                "layer_min_median": {a: float(np.median(list(fin[a]["layer_min"].values()))) for a in fin},
                "net_min_median": {a: float(np.median(list(fin[a]["net_min"].values()))) for a in fin},
                "max_left_veh": {a: max([v for v in fin[a]["left_veh"].values() if v is not None] + [0.0]) for a in fin},
                "generations": {a: arms[a]["generations"] for a in arms},
                "restart_spread_median": {a: float(np.median([u["restart_spread"] for u in arms[a]["units"].values()])) for a in arms}}
    m = {r: out["rows"][f"10_{r}"]["median"] for r in ("x1", "gen")}
    best = min(m.values())
    if not checks["T0"]["B1"]["PASS"] and not checks["T0"]["B2"]["PASS"]:
        outcome = "KILL (T0: no metering lever at either head)"
    elif best <= -0.10:
        outcome = "GO (licenses protocol v1 only)"
    elif best <= -0.07:
        outcome = "NEAR-MISS (KILL not final: true-model MPC on 20230118, 20230517, 20230816 first)"
    else:
        outcome = "KILL"
    out["median_rel"], out["outcome"] = m, outcome
    return out


def report(res: dict, rd: Path) -> None:
    L = ["# Testbed stage-1b metering authority screen (KILL-only)", "",
         f"*{time.strftime('%Y-%m-%d %H:%M')} · prereg `docs/plans/day_pattern_testbed_stage1b_screen.md` v1 + §11 · 12 train-source days · run {res['run_id']} · raw `{rd}`*", "",
         f"**Outcome: {res['outcome']}** · median rel_d (10 meters): S×1 {res['median_rel']['x1']:+.1%}, S_gen {res['median_rel']['gen']:+.1%}", "",
         "| row | median rel_d | 95 % CI | both-heavy | B1-only | without 0705 |", "|---|---|---|---|---|---|"]
    for k, r in res["rows"].items():
        L.append(f"| {k} | {r['median']:+.1%} | [{r['ci95'][0]:+.1%}, {r['ci95'][1]:+.1%}] | {r['median_both']:+.1%} | "
                 f"{r['median_B1only']:+.1%} | {r['median_without_20230705']:+.1%} |")
    L += ["", "| row | arm | median rel_d | layer min | net min | max veh left | generations | restart spread |",
          "|---|---|---|---|---|---|---|---|"]
    for k, r in res["rows"].items():
        for a in ("CONST",) + ARMS:
            L.append(f"| {k} | {a} | {r['arm_median_rel'][a]:+.1%} | {r['layer_min_median'][a]:.0f} | {r['net_min_median'][a]:.0f} | "
                     f"{r['max_left_veh'][a]:.1f} | {r['generations'][a]} | {r['restart_spread_median'][a]:.3g} |")
    c = res["checks"]
    L += ["", f"T0: B1 {'PASS' if c['T0']['B1']['PASS'] else 'FAIL'} ({c['T0']['B1']['days_ok']}/12 days), "
          f"B2 {'PASS' if c['T0']['B2']['PASS'] else 'FAIL'} ({c['T0']['B2']['days_ok']}/12) · T3: {c['T3']}",
          f"T1 NC over-critical minutes (05-23 h), B1 cell 26: {[round(x) for x in c['T1']['B1_cell26_min']]}; "
          f"B2 cells 32-33: {[round(x) for x in c['T1']['B2_cells32_33_min']]}"]
    (LAB / "testbed_screen.md").write_text("\n".join(L) + "\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["inputs", "smoke", "run", "resume", "opt"])
    ap.add_argument("--set", default="10")
    ap.add_argument("--storage", default="x1")
    ap.add_argument("--arm", default="TOD-day")
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--gate-ok", action="store_true")
    a = ap.parse_args(argv)
    if a.what == "inputs":
        return cmd_inputs()
    if a.what == "smoke":
        return cmd_smoke(a.gate_ok)
    if a.what == "opt":
        return cmd_opt(a.set, a.storage, a.arm, a.run_id)
    if a.what == "resume":
        assert a.run_id, "--run-id required"
        return cmd_run(a.gate_ok, a.run_id)
    return cmd_run(a.gate_ok)


if __name__ == "__main__":
    sys.exit(main())
