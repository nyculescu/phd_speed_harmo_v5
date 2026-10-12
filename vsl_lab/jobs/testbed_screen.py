"""Testbed stage-1b metering authority screen, KILL-only (docs/plans/day_pattern_testbed_stage1b_screen.md v1;
D5.11, D5.12). Frozen v5 nominal, closed-loop stepper vsl_lab/plants/metanet_ctrl.py, the 12 train-source days only.

python -m vsl_lab.jobs.testbed_screen inputs                 # demand sources per ramp-day -> testbed_screen_inputs.json
python -m vsl_lab.jobs.testbed_screen smoke --gate-ok        # one train day, timing only (seeds 7,193,000-009)
python -m vsl_lab.jobs.testbed_screen run --gate-ok          # T0/T1/T3, CONST, per-day arms, decision (run once)
python -m vsl_lab.jobs.testbed_screen opt --set 10 --storage x1 --arm TOD-day   # one worker (inside run's batches)
"""
from __future__ import annotations

import argparse
import hashlib
import json
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
OUT = LAB / "testbed_screen.json"
RAW = RUNS_ROOT / "day_pattern" / "testbed_screen"

METERS = {"10": ("E1", "E2", "E3", "E4", "E5", "E6", "E9", "E12", "E13", "E14"), "4": ("E9", "E12", "E13", "E14")}
QDETS = {"E1": ["3685"], "E2": ["3678"], "E4": ["3673", "3674", "3675"], "E5": ["3669"], "E6": ["2000"],
         "E9": ["3663"], "E12": ["7103"], "E13": ["5426"], "E14": ["5431"]}          # E3: replay (3679 has no 2023 data)
STORAGE_FT = {"E1": 326, "E2": 350, "E3": 550, "E4": 660, "E5": 480, "E6": 370, "E9": 300, "E12": 450, "E13": 500, "E14": 420}
S_JAM_M = 8.94                                    # IRIS jam density 180 veh/lane-mile [VERIFY]
R_MIN, R_MAX = 240.0, 1800.0                      # [VERIFY: IRIS density-adaptive range]
B05, B23, NPAD = 12, 228, 24                      # 05:00, 23:00 (model bins of 5 min from 04:00), drain bins
PERIODS = [(12, 72), (72, 132), (132, 180), (180, 228)]   # 05-10, 10-15, 15-19, 19-23
FINE = (96, 192)                                   # 12:00-20:00 (bins)
PERIOD_STEPS = 80                                  # 60 s at T = 0.75 s
ARMS = ("TOD-day", "TOD-fine-day", "ALINEA-day", "ALINEA-B-day")
SEED_ORDER = [(s, a) for s in ("10", "4") for a in ("CONST",) + ARMS]
SEED_BASE, BOOT_SEED, SMOKE_SEED = 7193010, 7193099, 7193000
B1_SENSE, B2_SENSE = [26], [32, 33]
GEN_BLOCK, IMPROVE_TOL, GEN_CAP, RESTARTS = 50, 0.002, 400, 2


# ---------------------------------------------------------------- setup and guards
def train_days() -> list:
    split = json.loads(SPLIT.read_text())
    cal = set(json.loads(FACTS5.read_text())["days"])
    days = list(split["train"])
    assert len(days) == 12 and all(d in cal for d in days), "screen days must be the 12 train-source calibration days"
    assert not (set(days) & (set(split["val"]) | set(split["test"]))), "train/val/test overlap"
    return days


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
    """Replay inputs of the 12 days with the metered ramps' demand rebuilt from Queue arrivals (§3), padded."""
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


def params() -> dict:
    return {k: np.array([v]) for k, v in json.loads(REC5.read_text())["frozen_params"].items()}


def _sub(inp: M.Inputs, rows: list) -> M.Inputs:
    return M.Inputs(inp.d0[rows], inp.d_o[rows], inp.beta[rows])


# ---------------------------------------------------------------- policies (batched over rows)
class Policy:
    """rates(minute) -> (B, nc) commanded rates (np.inf = off); observe/after_period for feedback arms."""
    needs_sense = False

    def rates(self, st, minute):
        raise NotImplementedError

    def observe(self, st):
        pass

    def after_period(self, st):
        pass


class Table(Policy):
    """CONST / TOD / TOD-fine: r (B, nc, n_bins) per 5-min bin, np.inf outside the controlled window."""

    def __init__(self, r_bins):
        self.r = r_bins

    def rates(self, st, minute):
        b = st.k // st.spb
        return self.r[:, :, b]


class Alinea(Policy):
    needs_sense = True

    def __init__(self, K, rho_set, sense: list, active):
        self.K, self.rs, self.sense, self.active = K, rho_set, sense, active   # (B, nc), (B, nc), [cells per ramp], (B, nc) bool
        self.r_prev = np.full(K.shape, R_MAX)
        self.acc = np.zeros(K.shape)
        self.n = 0
        self.rbar = None
        self.r_cmd = np.full(K.shape, np.inf)

    def observe(self, st):
        self.acc += np.stack([st.rho[:, c].max(axis=1) for c in self.sense], axis=1)
        self.n += 1

    def rates(self, st, minute):
        on = (minute >= 60.0) & (minute < 1140.0)
        if not on:
            self.r_prev[:] = R_MAX
            self.r_cmd = np.full(self.K.shape, np.inf)
            return self.r_cmd
        rho = self.acc / max(self.n, 1) if self.n else np.zeros(self.K.shape)
        r = np.clip(self.r_prev + self.K * (self.rs - rho), R_MIN, R_MAX)
        self.r_cmd = np.where(self.active, r, np.inf)
        self._r = r
        return self.r_cmd

    def after_period(self, st):
        self.acc[:] = 0.0
        self.n = 0
        if np.isfinite(self.r_cmd).any():
            bind = st.last_layer | st.last_net
            applied = np.where(np.isfinite(st.last_r_eff), st.last_r_eff, R_MAX)
            self.r_prev = np.where(bind, np.minimum(applied, R_MAX), self._r)


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
        else:
            st.step(n)
        policy.after_period(st)
    return st


def J_of(st) -> np.ndarray:
    a = st.acc
    return (a.tts_cells[:, B05:] + a.tts_queues[:, :, B05:].sum(axis=1) - a.fft[:, B05:]).sum(axis=1)


def left_of(st) -> np.ndarray:
    return (st.rho * st.L * st.lam).sum(axis=1) + st.w.sum(axis=1)


# ---------------------------------------------------------------- decoding of normalised parameters
def ramp_max(inp, rows, meters, net, b0, b1):
    eid = {e["id"]: i for i, e in enumerate(net.entrances)}
    return np.stack([inp.d_o[rows][:, eid[e], b0:b1].max(axis=1) for e in meters], axis=1)    # (len(rows), nc)


def decode(arm: str, u: np.ndarray, ctx: dict) -> Policy:
    """u (B, n) in [0,1] -> policy for B rows of ONE day (ctx: active coordinate maps, boxes)."""
    B, nc, nb = u.shape[0], ctx["nc"], ctx["nb"]
    if arm in ("CONST", "TOD-day", "TOD-fine-day"):
        r = np.full((B, nc, nb), np.inf)
        if arm == "CONST":
            for j, (i, hi) in enumerate(ctx["coords"]):
                r[:, i, B05:B23] = (R_MIN + u[:, j] * (hi - R_MIN))[:, None]
        elif arm == "TOD-day":
            for j, (i, pi, hi) in enumerate(ctx["coords"]):
                b0, b1 = PERIODS[pi]
                r[:, i, b0:b1] = (R_MIN + u[:, j] * (hi - R_MIN))[:, None]
        else:
            for j, (i, hi) in enumerate(ctx["coords"]):
                ton = FINE[0] * 5 + np.round(u[:, 3 * j] * (FINE[1] - FINE[0]) * 5)          # minutes from 04:00
                toff = FINE[0] * 5 + np.round(u[:, 3 * j + 1] * (FINE[1] - FINE[0]) * 5)
                rate = R_MIN + u[:, 3 * j + 2] * (hi - R_MIN)
                for bi in range(FINE[0], FINE[1]):
                    m = bi * 5.0
                    inside = (m >= ton) & (m < toff)
                    r[:, i, bi] = np.where(inside, rate, np.inf)
        return Table(r)
    K = np.full((B, nc), 1.0)
    rs = np.full((B, nc), 1e9)
    act = np.zeros((B, nc), bool)
    for j, (i, rcs) in enumerate(ctx["coords"]):
        K[:, i] = 10 ** (np.log10(5.0) + u[:, 2 * j] * (np.log10(300.0) - np.log10(5.0)))
        rs[:, i] = (0.6 + 0.6 * u[:, 2 * j + 1]) * rcs
        act[:, i] = True
    return Alinea(K, rs, ctx["sense"], act)


def context(arm, net, p, inp, rows, meters, const_rates=None) -> dict:
    """Active coordinates for one day (rows of the same day), boxes and warm start x0 (normalised)."""
    nc, nb = len(meters), inp.d0.shape[1]
    ctx = {"nc": nc, "nb": nb, "coords": []}
    x0 = []
    if arm == "CONST":
        hi = ramp_max(inp, rows, meters, net, B05, B23).max(axis=0)
        for i in range(nc):
            if hi[i] > R_MIN:
                ctx["coords"].append((i, float(hi[i])))
                x0.append(1.0)
    elif arm == "TOD-day":
        for i in range(nc):
            for pi, (b0, b1) in enumerate(PERIODS):
                hi = float(ramp_max(inp, rows[:1], meters, net, b0, b1)[0, i])
                if hi > R_MIN:
                    ctx["coords"].append((i, pi, hi))
                    c = const_rates[i] if const_rates is not None else np.inf
                    x0.append(1.0 if not np.isfinite(c) else float(np.clip((c - R_MIN) / (hi - R_MIN), 0, 1)))
    elif arm == "TOD-fine-day":
        for i in range(nc):
            hi = float(ramp_max(inp, rows[:1], meters, net, *FINE)[0, i])
            if hi > R_MIN:
                ctx["coords"].append((i, hi))
                c = const_rates[i] if const_rates is not None else np.inf
                x0 += [0.0, 1.0, 1.0 if not np.isfinite(c) else float(np.clip((c - R_MIN) / (hi - R_MIN), 0, 1))]
    else:
        st = MC.Stepper(net, p, _sub(inp, rows[:1]), record_cells=False, stations=False)
        rc = st.rc0[0]
        cells = sorted(s["cell"] for s in net.stations)
        eid = {e["id"]: i for i, e in enumerate(net.entrances)}
        sense = []
        for i, e in enumerate(meters):
            if arm == "ALINEA-day":
                sense.append([min(c for c in cells if c > net.entrances[eid[e]]["cell"])])
            else:
                sense.append(B2_SENSE if e == "E14" else B1_SENSE)
        ctx["sense"] = sense
        hi = ramp_max(inp, rows[:1], meters, net, B05, B23)[0]
        for i in range(nc):
            if hi[i] > R_MIN:
                ctx["coords"].append((i, float(rc[sense[i][0]])))
                x0 += [0.5, (1.0 - 0.6) / 0.6]
    ctx["x0"] = np.array(x0, float)
    return ctx


# ---------------------------------------------------------------- evaluation and optimisation
def evaluate(arm, net, p, inp, meters, srow, rows, U, ctxs) -> np.ndarray:
    """J for a batch: rows[k] is the day row of U[k]; ctxs[day_row] the decoding context."""
    return J_of(_rollout_eval(arm, net, p, inp, meters, srow, rows, U, ctxs))


def _rollout_eval(arm, net, p, inp, meters, srow, rows, U, ctxs) -> MC.Stepper:
    batch = _sub(inp, rows)
    pols = [decode(arm, U[k:k + 1], ctxs[rows[k]]) for k in range(len(rows))]
    if isinstance(pols[0], Table):
        pol = Table(np.concatenate([q.r for q in pols], axis=0))
    else:
        pol = Alinea(np.concatenate([q.K for q in pols]), np.concatenate([q.rs for q in pols]), pols[0].sense,
                     np.concatenate([q.active for q in pols]))
        assert all(q.sense == pols[0].sense for q in pols)
    return rollout(net, p, batch, meters, srow, pol)


def seed_for(set_, arm, day_index, restart) -> int:
    k = SEED_ORDER.index((set_, arm))
    return int(np.random.SeedSequence([SEED_BASE + k, day_index, restart]).generate_state(1)[0] % (2 ** 31 - 2) + 1)


def optimise(arm, set_, srow, net, p, inp, days, J_nc, const_rates=None, cap=GEN_CAP) -> dict:
    """Per-day (or pooled for CONST) CMA-ES with 2 restarts, convergence blocks; all ES advance in one batch."""
    import cma
    meters = METERS[set_]
    D = len(days)
    pooled = arm == "CONST"
    units = [None] if pooled else list(range(D))
    ctxs, es, best, trace, done = {}, {}, {}, {}, {}
    for d in range(D):
        ctxs[d] = context(arm, net, p, inp, [d], meters, const_rates)
    if pooled:
        cpool = context("CONST", net, p, inp, list(range(D)), meters)
        for d in range(D):
            ctxs[d] = cpool
    for u_ in units:
        x0 = ctxs[0 if pooled else u_]["x0"]
        for r in range(RESTARTS):
            key = (u_, r)
            if len(x0) == 0:
                done[key] = True
                best[key] = (0.0 if pooled else float(J_nc[u_]), np.zeros(0))
                trace[key] = []
                continue
            es[key] = cma.CMAEvolutionStrategy(list(x0), 0.3, {"bounds": [0, 1], "verbose": -9,
                                                                 "seed": seed_for(set_, arm, 99 if pooled else u_, r)})
            best[key], trace[key], done[key] = (np.inf, None), [], False
    gen = 0
    while not all(done.values()) and gen < cap:
        asks, rows, U = {}, [], []
        for key, e in es.items():
            if done[key]:
                continue
            X = e.ask()
            asks[key] = X
            for x in X:
                for d in (range(D) if pooled else [key[0]]):
                    rows.append(d)
                    U.append(x)
        J = evaluate(arm, net, p, inp, METERS[set_], srow, rows, np.array(U), ctxs)
        pos = 0
        for key, X in asks.items():
            f = []
            for x in X:
                if pooled:
                    jd = J[pos:pos + D]
                    pos += D
                    f.append(float(np.median((jd - J_nc) / J_nc)))
                else:
                    f.append(float(J[pos]))
                    pos += 1
            es[key].tell(X, f)
            i = int(np.argmin(f))
            if f[i] < best[key][0]:
                best[key] = (f[i], np.array(X[i]))
            trace[key].append(best[key][0])
        gen += 1
        if gen % GEN_BLOCK == 0:
            for key in asks:
                tr = trace[key]
                ref = abs(np.median(J_nc)) if pooled else J_nc[key[0]]
                scale = 1.0 if pooled else ref
                if len(tr) > GEN_BLOCK and (tr[-GEN_BLOCK - 1] - tr[-1]) < IMPROVE_TOL * scale:
                    done[key] = True
    out = {"arm": arm, "set": set_, "storage": srow, "generations": gen, "units": {}}
    for u_ in units:
        rs = [best[(u_, r)] for r in range(RESTARTS)]
        b = min(rs, key=lambda t: t[0])
        out["units"]["pooled" if pooled else days[u_]] = {
            "best": b[0], "x": b[1].tolist(), "restart_values": [t[0] for t in rs],
            "traces": [trace[(u_, r)] for r in range(RESTARTS)], "ctx_coords": [list(c) for c in ctxs[0 if pooled else u_]["coords"]]}
    # final evaluation of each unit's best: per-day J (pooled CONST), queue-layer / hard-net minutes, vehicles left
    rows, U = [], []
    for k, d in enumerate(days):
        unit = out["units"]["pooled" if pooled else d]
        x = np.array(unit["x"], float)
        if x.size == 0:
            x = np.zeros(max(1, len(ctxs[k]["x0"])))
        rows.append(k)
        U.append(x)
    if all(np.array(u).size == len(ctxs[k]["x0"]) for k, u in enumerate(U)) and len(ctxs[0]["x0"]) > 0:
        st = _rollout_eval(arm, net, p, inp, meters, srow, rows, np.array(U), ctxs)
        Jd = J_of(st)
        out["final"] = {"J_d": dict(zip(days, Jd.tolist())),
                        "layer_min": dict(zip(days, (st.acc.layer_steps.sum(axis=(1, 2)) * st.T_s / 60).tolist())),
                        "net_min": dict(zip(days, (st.acc.net_steps.sum(axis=(1, 2)) * st.T_s / 60).tolist())),
                        "left_veh": dict(zip(days, left_of(st).tolist()))}
    else:
        out["final"] = {"J_d": dict(zip(days, [float(x) for x in J_nc])), "note": "no active coordinate: NC"}
    return out


def const_rates_from(res: dict, ctx: dict) -> np.ndarray:
    nc = ctx["nc"]
    r = np.full(nc, np.inf)
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
    st = MC.Stepper(net, p, inp, record_cells=True, stations=False)
    st.run_to_end()
    rho = st.rho_rec / st.spb
    rc = st.rc_rec / st.spb
    oc = rho > rc
    return {"B1_cell26_min": (oc[:, 26, B05:B23].sum(axis=1) * 5).tolist(),
            "B2_cells32_33_min": ((oc[:, 32, B05:B23] | oc[:, 33, B05:B23]).sum(axis=1) * 5).tolist()}


# ---------------------------------------------------------------- CLI
def _committed(path: Path) -> bool:
    r = subprocess.run(["git", "-C", str(REPO_ROOT), "ls-files", "--error-unmatch", str(path)], capture_output=True)
    d = subprocess.run(["git", "-C", str(REPO_ROOT), "diff", "--quiet", "HEAD", "--", str(path)])
    return r.returncode == 0 and d.returncode == 0


def cmd_inputs() -> int:
    days = train_days()
    _, _, listing = build_inputs(days)
    INPUTS_LIST.write_text(json.dumps({"days": days, "listing": listing, "rule": "§3 of the screen v1"}, indent=1))
    print(json.dumps({d: {e: v["source"] for e, v in r.items()} for d, r in listing.items()}))
    return 0


def _load_all():
    days = train_days()
    net, inp, listing = build_inputs(days)
    assert json.loads(INPUTS_LIST.read_text())["listing"] == json.loads(json.dumps(listing)), "inputs listing changed"
    return days, net, inp


def cmd_opt(set_, srow, arm) -> int:
    days, net, inp = _load_all()
    p = params()
    J_nc = J_of(nc_run(net, p, inp, METERS[set_], srow))
    const = None
    if arm != "CONST":
        cres = json.loads((RAW / f"opt_{set_}_{srow}_CONST.json").read_text())
        ctx = context("CONST", net, p, inp, list(range(len(days))), METERS[set_])
        const = const_rates_from(cres, ctx)
    res = optimise(arm, set_, srow, net, p, inp, days, J_nc, const)
    res["J_nc"] = J_nc.tolist()
    (RAW / f"opt_{set_}_{srow}_{arm}.json").write_text(json.dumps(res, default=float))
    return 0


def cmd_smoke(gate_ok) -> int:
    from vsl_lab.ops.scheduler import sim_start_gate
    sim_start_gate(gate_ok)
    days = train_days()[:1]
    net, inp, _ = build_inputs(days)
    p = params()
    t = time.time()
    J_nc = J_of(nc_run(net, p, inp, METERS["10"], "x1"))
    t_nc = time.time() - t
    import cma
    ctx = context("ALINEA-B-day", net, p, inp, [0], METERS["10"])
    e = cma.CMAEvolutionStrategy(list(ctx["x0"]), 0.3, {"bounds": [0, 1], "verbose": -9, "seed": SMOKE_SEED})
    X = e.ask()
    t = time.time()
    evaluate("ALINEA-B-day", net, p, inp, METERS["10"], "x1", [0] * len(X), np.array(X), {0: ctx})
    t_gen = time.time() - t
    print(json.dumps({"nc_run_s": round(t_nc, 1), "alinea_b_generation_s": round(t_gen, 1), "popsize": len(X),
                      "note": "timing only; no J shown (smoke)"}))
    return 0


def cmd_run(gate_ok) -> int:
    from vsl_lab.ops import ledger
    from vsl_lab.ops.scheduler import Job, run_batch, sim_start_gate
    assert not OUT.exists(), "the screen already ran (run once)"
    for f in (SPLIT, INPUTS_LIST, REPO_ROOT / "docs/plans/day_pattern_testbed_stage1b_screen.md"):
        assert _committed(f), f"{f} must be committed and unchanged"
    sim_start_gate(gate_ok)
    days, net, inp = _load_all()
    p = params()
    RAW.mkdir(parents=True, exist_ok=True)
    ledger.append("DP", "testbed-1b", "S", "testbed_screen_started", {"days": days}, "7193010-7193099", 0, {},
                  {"status": "started"}, notes=str(RAW))
    st_nc = nc_run(net, p, inp, METERS["10"], "x1")
    J_nc = J_of(st_nc)
    hin = head_inflow(st_nc, net)
    J_nc2 = J_of(nc_run(net, p, inp, METERS["10"], "x1"))
    checks = {"T3_identical": bool(np.array_equal(J_nc, J_nc2)), "T0": t0(net, p, inp, J_nc, hin), "T1": t1(net, p, inp),
              "left_nc": left_of(st_nc).tolist()}
    assert checks["T3_identical"], "T3 FAIL: stop, fix, re-run"
    py = sys.executable
    mk = lambda s, r, a: Job(jid=f"opt_{s}_{r}_{a}", argv=["vsl_lab.jobs.testbed_screen", "opt", "--set", s, "--storage", r, "--arm", a])
    run_batch([mk(s, r, "CONST") for s in ("10", "4") for r in ("x1", "gen")], RAW / "batch_const", 4, gate_ok=True)
    run_batch([mk(s, r, a) for s in ("10", "4") for r in ("x1", "gen") for a in ARMS], RAW / "batch_arms", 16, gate_ok=True)
    res = decide(days, J_nc, checks)
    OUT.write_text(json.dumps(res, indent=1, default=float))
    report(res)
    ledger.append("DP", "testbed-1b", "S", "testbed_screen", {"days": days}, "7193010-7193099", 0, {},
                  {"outcome": res["outcome"], "median_rel": res["median_rel"]}, notes=str(RAW))
    print(json.dumps({"outcome": res["outcome"], "median_rel": res["median_rel"]}))
    return 0


def decide(days, J_nc, checks) -> dict:
    rng = np.random.default_rng(BOOT_SEED)
    out = {"days": days, "J_nc": J_nc.tolist(), "checks": checks, "rows": {}}
    for set_ in ("10", "4"):
        for srow in ("x1", "gen"):
            arms = {a: json.loads((RAW / f"opt_{set_}_{srow}_{a}.json").read_text()) for a in ("CONST",) + ARMS}
            Jc = {a: np.array([arms[a]["final"]["J_d"][d] for d in days]) for a in ("CONST",) + ARMS}
            E = np.min(np.stack([J_nc] + [Jc[a] for a in ("CONST",) + ARMS]), axis=0)
            rel = (E - J_nc) / J_nc
            boot = [np.median(rng.choice(rel, len(rel))) for _ in range(10000)]
            strata = json.loads(SPLIT.read_text())["strata"]
            out["rows"][f"{set_}_{srow}"] = {
                "rel_d": dict(zip(days, rel.tolist())), "median": float(np.median(rel)),
                "ci95": [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))],
                "median_both": float(np.median([r for d, r in zip(days, rel) if d in strata["both"]])),
                "median_B1only": float(np.median([r for d, r in zip(days, rel) if d in strata["B1_only"]])),
                "median_without_20230705": float(np.median([r for d, r in zip(days, rel) if d != "20230705"])),
                "arm_median_rel": {a: float(np.median((Jc[a] - J_nc) / J_nc)) for a in ("CONST",) + ARMS},
                "layer_min_median": {a: float(np.median(list(arms[a]["final"].get("layer_min", {"-": 0}).values()))) for a in ("CONST",) + ARMS},
                "net_min_median": {a: float(np.median(list(arms[a]["final"].get("net_min", {"-": 0}).values()))) for a in ("CONST",) + ARMS},
                "max_left_veh": {a: float(max(arms[a]["final"].get("left_veh", {"-": 0}).values())) for a in ("CONST",) + ARMS},
                "generations": {a: arms[a]["generations"] for a in ("CONST",) + ARMS}}
    m = {r: out["rows"][f"10_{r}"]["median"] for r in ("x1", "gen")}
    best = min(m.values())
    t0_fail_both = not checks["T0"]["B1"]["PASS"] and not checks["T0"]["B2"]["PASS"]
    if t0_fail_both:
        outcome = "KILL (T0: no metering lever at either head)"
    elif best <= -0.10:
        outcome = "GO (licenses protocol v1 only)"
    elif best <= -0.07:
        outcome = "NEAR-MISS (KILL not final: true-model MPC on 20230118, 20230517, 20230816 first)"
    else:
        outcome = "KILL"
    out["median_rel"], out["outcome"] = m, outcome
    return out


def report(res: dict) -> None:
    L = ["# Testbed stage-1b metering authority screen (KILL-only)", "",
         f"*{time.strftime('%Y-%m-%d %H:%M')} · prereg `docs/plans/day_pattern_testbed_stage1b_screen.md` v1 · 12 train-source days · raw `{RAW}`*", "",
         f"**Outcome: {res['outcome']}** · median rel_d (10 meters): S×1 {res['median_rel']['x1']:+.1%}, S_gen {res['median_rel']['gen']:+.1%}", "",
         "| row | median rel_d | 95 % CI | both-heavy | B1-only | without 0705 | arm medians |", "|---|---|---|---|---|---|---|"]
    for k, r in res["rows"].items():
        L.append(f"| {k} | {r['median']:+.1%} | [{r['ci95'][0]:+.1%}, {r['ci95'][1]:+.1%}] | {r['median_both']:+.1%} | "
                 f"{r['median_B1only']:+.1%} | {r['median_without_20230705']:+.1%} | "
                 + ", ".join(f"{a} {v:+.1%}" for a, v in r["arm_median_rel"].items()) + " |")
    c = res["checks"]
    L += ["", f"T0: B1 {'PASS' if c['T0']['B1']['PASS'] else 'FAIL'} ({c['T0']['B1']['days_ok']}/12 days), "
          f"B2 {'PASS' if c['T0']['B2']['PASS'] else 'FAIL'} ({c['T0']['B2']['days_ok']}/12) · T3 identical: {c['T3_identical']}",
          f"T1 NC over-critical minutes, B1 cell 26: {c['T1']['B1_cell26_min']}; B2 cells 32-33: {c['T1']['B2_cells32_33_min']}"]
    (LAB / "testbed_screen.md").write_text("\n".join(L) + "\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["inputs", "smoke", "run", "opt"])
    ap.add_argument("--set", default="10")
    ap.add_argument("--storage", default="x1")
    ap.add_argument("--arm", default="TOD-day")
    ap.add_argument("--gate-ok", action="store_true")
    a = ap.parse_args(argv)
    if a.what == "inputs":
        return cmd_inputs()
    if a.what == "smoke":
        return cmd_smoke(a.gate_ok)
    if a.what == "opt":
        return cmd_opt(a.set, a.storage, a.arm)
    return cmd_run(a.gate_ok)


if __name__ == "__main__":
    sys.exit(main())
