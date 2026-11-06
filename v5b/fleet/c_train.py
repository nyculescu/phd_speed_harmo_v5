"""Per-CAV control (V285): PPO with one policy shared by every ALKS, each acting on its own observation; the critic also
sees network state. SB3 needs fixed agent counts, hence this loop. Each vehicle decides once per hold on its own clock, so
every sample can move its level (V290); its reward is the mean over the interval. A vehicle that leaves is cut off, not
ended: its last value is bootstrapped, so leaving neither earns nor costs anything and the reward can't favour staying on the road.

Usage: python -m v5b.fleet.c_train smoke --out DIR
       python -m v5b.fleet.c_train train --out DIR --learner 0 [--updates 250] [--n-envs 3] [--lagr JSON]
Results come from b_train matrix with model {"pt": FILE} and ENV as its kw.
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import sys
import time
from pathlib import Path

import numpy as np
import torch
from torch import nn

from v5b.fleet import b_env as be

ENV = {"cav": True, "decision": 5.0, "alks_asl": 0.5, "ref_delay": True}
LEVELS = (4090.0, 4600.0, 5300.0)
FIRST_WORKER = 9     # run 5 used workers 0-8
NEP0 = 0
GAMMA, LAM = 0.8, 0.9     # per 30-s decision: a horizon of about 150 s, the time to cross the merge area and feel the result
EPOCHS, BATCH = 10, 4096
LR, CLIP, ENT, VF, GRAD = 3e-4, 0.2, 0.01, 0.5, 0.5
CLIP_INPUT = 5.0
INPUT_NORM = "running mean and SD, updated between updates, clip 5"
NORM_KEYS = {"lo_mean", "lo_var", "gl_mean", "gl_var", "n_seen"}
LAGR = {"start": 1.0, "freeze": 20, "window": 20, "step": 1.0, "cap": 10.0, "target": 0.97}     # 2C, fixed in protocol round_1 before data
RESIDUAL_P0 = 0.9     # 3B: probability of offset 0 at the start, for every input
EP_KEYS = ("seed", "N", "dist_s", "E30", "E15", "brake3", "brake45", "passed", "arrived", "mean_v", "collisions", "contact_steps", "alks_s", "v2v_s",
           "changes", "reversals", "ignored", "steps", "gap25", "stop_gap")


def _mlp(n_in: int, n_out: int) -> nn.Sequential:
    return nn.Sequential(nn.Linear(n_in, 64), nn.Tanh(), nn.Linear(64, 64), nn.Tanh(), nn.Linear(64, n_out))


def act_env(path: str) -> dict:
    """Environment options a stored policy acts through; empty for policies before round 1."""
    return torch.load(path, map_location="cpu").get("act_env", {})


def init_residual(net: "Net", p0: float = RESIDUAL_P0) -> None:
    """3B: the actor's last layer gives offset 0 probability p0 whatever the input, so training starts as the rule."""
    last = net.actor[-1]
    with torch.no_grad():
        last.weight.zero_()
        last.bias.copy_(torch.tensor([0.0, float(np.log(2.0 * p0 / (1.0 - p0))), 0.0]))


def episode_delay(ep: dict) -> float:
    """Training-mode all-vehicle delay: vehicle-seconds in the system or waiting minus 1-s distance over the reference speed."""
    return float(ep["N"] - ep["dist_s"] / be.fl.LIMIT)


def dual_step(lam: float, ratios: list, cfg: dict) -> tuple:
    """2C: one update of the dual variable from the delay ratios of the last window's episodes; returns (new lambda, J)."""
    j = float(np.mean(ratios))
    return float(np.clip(lam + cfg["step"] * (j - cfg["target"]), 0.0, cfg["cap"])), j


class Net(nn.Module):
    def __init__(self, n_local: int = be.CAV_LOCAL, n_act: int = len(be.HEADWAYS_S), cost: bool = False):
        super().__init__()
        self.actor = _mlp(n_local, n_act)
        self.critic = _mlp(n_local + be.CAV_GLOBAL, 1)
        self.critic_c = _mlp(n_local + be.CAV_GLOBAL, 1) if cost else None     # 2C: the cost critic
        # V388: saved with the weights, so that use cannot differ from training. Fixed during a collect and its update, or the probability ratio breaks.
        self.register_buffer("lo_mean", torch.zeros(n_local, dtype=torch.float64))
        self.register_buffer("lo_var", torch.ones(n_local, dtype=torch.float64))
        self.register_buffer("gl_mean", torch.zeros(be.CAV_GLOBAL, dtype=torch.float64))
        self.register_buffer("gl_var", torch.ones(be.CAV_GLOBAL, dtype=torch.float64))
        self.register_buffer("n_seen", torch.zeros(1, dtype=torch.float64))

    def _scaled(self, x: torch.Tensor, mean: torch.Tensor, var: torch.Tensor) -> torch.Tensor:
        if not self.n_seen:     # a policy from before V388 keeps its inputs exactly as it was trained on them
            return x
        z = ((x - mean.float()) / (var.float() + 1e-8).sqrt()).clamp(-CLIP_INPUT, CLIP_INPUT)
        return torch.where(var.float() > 1e-12, z, torch.zeros_like(z))     # never varied in the data, so its weights never trained (V389)

    def logits(self, lo: torch.Tensor) -> torch.Tensor:
        return self.actor(self._scaled(lo, self.lo_mean, self.lo_var))

    def dist(self, lo: torch.Tensor) -> torch.distributions.Categorical:
        return torch.distributions.Categorical(logits=self.logits(lo))

    def value(self, lo: torch.Tensor, gl: torch.Tensor) -> torch.Tensor:
        return self.critic(torch.cat([self._scaled(lo, self.lo_mean, self.lo_var), self._scaled(gl, self.gl_mean, self.gl_var)], 1)).squeeze(1)

    def value_c(self, lo: torch.Tensor, gl: torch.Tensor) -> torch.Tensor:
        return self.critic_c(torch.cat([self._scaled(lo, self.lo_mean, self.lo_var), self._scaled(gl, self.gl_mean, self.gl_var)], 1)).squeeze(1)

    def observe(self, lo: np.ndarray, gl: np.ndarray) -> None:
        """Adds a batch to the input statistics, as if all batches so far were one."""
        n0, n1 = float(self.n_seen), float(len(lo))
        for x, m, v in ((lo, self.lo_mean, self.lo_var), (gl, self.gl_mean, self.gl_var)):
            t = torch.from_numpy(x).double()
            bm, bv = t.mean(0), t.var(0, unbiased=False)
            d = bm - m
            v.copy_((v * n0 + bv * n1 + d * d * n0 * n1 / (n0 + n1)) / (n0 + n1))
            m.copy_(m + d * n1 / (n0 + n1))
        self.n_seen += n1

    def restore(self, sd: dict) -> None:
        own = self.state_dict()
        missing = set(own) - set(sd)
        if missing - NORM_KEYS:
            raise KeyError(f"checkpoint lacks {sorted(missing - NORM_KEYS)}")
        self.load_state_dict({**own, **sd})


class Greedy:
    """The most likely level for each vehicle."""

    def __init__(self, path: str):
        torch.set_num_threads(1)
        ck = torch.load(path, map_location="cpu")
        self.net = Net(ck.get("n_local", be.CAV_LOCAL), ck.get("n_act", len(be.HEADWAYS_S)), any(k.startswith("critic_c.") for k in ck["net"]))
        self.net.restore(ck["net"])

    def __call__(self, o: tuple) -> dict:
        ids, lo, _, due = o
        if not due.any():
            return {}
        with torch.no_grad():
            a = self.net.logits(torch.from_numpy(lo[due])).argmax(1).numpy()
        return dict(zip((v for v, d in zip(ids, due) if d), a.tolist()))


def gae(r: np.ndarray, v: np.ndarray, boot: float, gamma: float = GAMMA, lam: float = LAM) -> np.ndarray:
    adv = np.zeros(len(r), dtype=np.float32)
    last = 0.0
    for t in range(len(r) - 1, -1, -1):
        nxt = v[t + 1] if t + 1 < len(r) else boot
        last = r[t] + gamma * nxt - v[t] + gamma * lam * last
        adv[t] = last
    return adv


def _worker(conn, kw: dict) -> None:
    torch.set_num_threads(1)
    env = be.make(**kw)
    while True:
        cmd, x = conn.recv()
        if cmd == "reset":
            conn.send(env.reset()[0])
        elif cmd == "step":
            conn.send(env.step(x))
        else:
            env.close()
            conn.close()
            return


def _act(net: Net, scale: float, obs: list, scale_c: float = 1.0) -> list:
    """One forward pass over the vehicles due in every env; per env (ids, actions, log-probs, raw values, local, global, raw cost values)."""
    due = [([v for v, d in zip(o[0], o[3]) if d], o[1][o[3]], o[2]) for o in obs]
    lo = np.concatenate([d[1] for d in due])
    gl = np.concatenate([np.repeat(d[2][None], len(d[0]), 0) for d in due])
    with torch.no_grad():
        tl, tg = torch.from_numpy(lo), torch.from_numpy(gl)
        d = net.dist(tl)
        a = d.sample()
        lp, val = d.log_prob(a).numpy(), net.value(tl, tg).numpy() * scale
        valc = net.value_c(tl, tg).numpy() * scale_c if net.critic_c is not None else np.zeros_like(val)
    a = a.numpy()
    out, i = [], 0
    for ids, l, g in due:
        j = i + len(ids)
        out.append((ids, a[i:j], lp[i:j], val[i:j], l, g, valc[i:j]))
        i = j
    return out


def _close(t: dict) -> None:
    if t["k"]:
        t["r"][-1] /= t["k"]
        t["c"][-1] /= t["k"]
    t["k"] = 0


def collect(net: Net, scale: float, conns: list, gamma: float = GAMMA, lam: float = LAM, scale_c: float = 1.0) -> tuple:
    """One episode per env: flat arrays of observations, actions, log-probs, advantages and returns, plus the episode logs.
    With a cost critic (2C) it also returns the cost advantages, cost returns and costs; otherwise those three are None."""
    cost = net.critic_c is not None
    for c in conns:
        c.send(("reset", None))
    obs = [c.recv() for c in conns]
    tr = [{} for _ in conns]
    done, logs = [], [None] * len(conns)
    while logs[0] is None:
        acted = _act(net, scale, obs, scale_c)
        for k, (c, (ids, a, lp, val, lo, gl, valc)) in enumerate(zip(conns, acted)):
            for i, v in enumerate(ids):
                t = tr[k].setdefault(v, {"lo": [], "gl": [], "a": [], "lp": [], "v": [], "r": [], "vc": [], "c": [], "k": 0})
                _close(t)
                for key, x in (("lo", lo[i]), ("gl", gl), ("a", a[i]), ("lp", lp[i]), ("v", val[i]), ("r", 0.0), ("vc", valc[i]), ("c", 0.0)):
                    t[key].append(x)
            c.send(("step", dict(zip(ids, a.tolist()))))
        res = [c.recv() for c in conns]
        obs = [r[0] for r in res]
        for k, (o2, rew, _, trunc, info) in enumerate(res):
            costs = info.get("cost")
            if cost and costs is None:
                raise RuntimeError("a cost critic needs an environment in reward_mode 'lagr'")
            for v, x in rew.items():
                t = tr[k].get(v)
                if t is not None:
                    t["r"][-1] += x
                    if cost:
                        t["c"][-1] += costs[v]
                    t["k"] += 1
            live = set(o2[0])
            for v in [v for v in tr[k] if v not in live]:     # left: the last value stands in for what follows
                t = tr[k].pop(v)
                _close(t)
                done.append((t, t["v"][-1], t["vc"][-1]))
            if trunc:
                logs[k] = info["ep"]
    with torch.no_grad():
        for k, o in enumerate(obs):
            live = list(tr[k])
            if not live:
                continue
            idx = {v: i for i, v in enumerate(o[0])}
            lo = torch.from_numpy(o[1][[idx[v] for v in live]])
            gl = torch.from_numpy(np.repeat(o[2][None], len(live), 0))
            bc = net.value_c(lo, gl).numpy() * scale_c if cost else np.zeros(len(live), dtype=np.float32)
            for v, x, y in zip(live, net.value(lo, gl).numpy() * scale, bc):
                t = tr[k][v]
                _close(t)
                done.append((t, x, y))
    lo, gl, a, lp, adv, ret, r, advc, retc, cc = [], [], [], [], [], [], [], [], [], []
    for t, boot, bootc in done:
        rr, vv = np.array(t["r"], dtype=np.float32), np.array(t["v"], dtype=np.float32)
        x = gae(rr, vv, float(boot), gamma, lam)
        lo += t["lo"]
        gl += t["gl"]
        a += t["a"]
        lp += t["lp"]
        adv.append(x)
        ret.append(x + vv)
        r.append(rr)
        if cost:
            c_, vc = np.array(t["c"], dtype=np.float32), np.array(t["vc"], dtype=np.float32)
            y = gae(c_, vc, float(bootc), gamma, lam)
            advc.append(y)
            retc.append(y + vc)
            cc.append(c_)
    tail = (np.concatenate(advc), np.concatenate(retc), np.concatenate(cc)) if cost else (None, None, None)
    return (np.array(lo, dtype=np.float32), np.array(gl, dtype=np.float32), np.array(a, dtype=np.int64), np.array(lp, dtype=np.float32),
            np.concatenate(adv), np.concatenate(ret), np.concatenate(r), logs, *tail)


def combined_advantage(ad: torch.Tensor, adc: torch.Tensor | None, lam_dual: float) -> torch.Tensor:
    """Each advantage normalised over the minibatch; with a cost (2C) they combine as (A_r - lambda A_c) / (1 + lambda)."""
    ad = (ad - ad.mean()) / (ad.std() + 1e-8)
    if adc is None:
        return ad
    adc = (adc - adc.mean()) / (adc.std() + 1e-8)
    return (ad - lam_dual * adc) / (1.0 + lam_dual)


def update(net: Net, opt, batch: tuple, scale: float, rng: np.random.Generator, lam_dual: float = 0.0, scale_c: float = 1.0) -> dict:
    lo, gl, a, lp, adv, ret = (torch.from_numpy(x) for x in batch[:6])
    ret = ret / scale
    cost = len(batch) > 8 and batch[8] is not None
    if cost:
        advc, retc = torch.from_numpy(batch[8]), torch.from_numpy(batch[9]) / scale_c
    n = len(a)
    ent = vl = vlc = kl = cf = 0.0
    k = 0
    with torch.no_grad():
        ev = 1.0 - float((net.value(lo, gl) - ret).var() / ret.var().clamp_min(1e-8))
        evc = 1.0 - float((net.value_c(lo, gl) - retc).var() / retc.var().clamp_min(1e-8)) if cost else None
    for _ in range(EPOCHS):
        perm = torch.from_numpy(rng.permutation(n))
        for i in range(0, n - BATCH + 1, BATCH):
            b = perm[i:i + BATCH]
            d = net.dist(lo[b])
            ad = combined_advantage(adv[b], advc[b] if cost else None, lam_dual)
            ratio = (d.log_prob(a[b]) - lp[b]).exp()
            pg = -torch.min(ratio * ad, ratio.clamp(1 - CLIP, 1 + CLIP) * ad).mean()
            v = ((net.value(lo[b], gl[b]) - ret[b]) ** 2).mean()
            vc = ((net.value_c(lo[b], gl[b]) - retc[b]) ** 2).mean() if cost else torch.zeros(())
            h = d.entropy().mean()
            loss = pg + VF * (v + vc) - ENT * h
            opt.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(net.parameters(), GRAD)
            opt.step()
            ent += float(h.detach())
            vl += float(v.detach())
            vlc += float(vc.detach())
            with torch.no_grad():
                kl += float((lp[b] - d.log_prob(a[b])).mean())
                cf += float(((ratio - 1.0).abs() > CLIP).float().mean())
            k += 1
    out = {"entropy": ent / max(k, 1), "value_loss": vl / max(k, 1), "n": n, "kl": kl / max(k, 1), "clipfrac": cf / max(k, 1), "ev": ev}
    if cost:
        out |= {"value_loss_c": vlc / max(k, 1), "ev_c": evc}
    return out


def tb_scalars(w, u: int, st: dict, batch: tuple, scale: float, wall: float, lam_dual: float | None, j: float | None, scale_c: float | None) -> None:
    """V394: one float32 value per tag per update; episodes under ep/q<level>/, one per level and update."""
    put = lambda tag, x: w.add_scalar(tag, np.float32(x), u)
    put("ppo/reward_per_decision", batch[6].mean())
    for k in ("entropy", "value_loss", "kl", "clipfrac", "ev", "n"):
        put(f"ppo/{k}", st[k])
    put("ppo/scale", scale)
    put("ppo/wall_s", wall)
    if lam_dual is not None:
        put("cost/per_decision", batch[10].mean())
        put("cost/value_loss", st["value_loss_c"])
        put("cost/ev", st["ev_c"])
        put("cost/scale", scale_c)
        put("lagr/lambda", lam_dual)
        if j is not None:
            put("lagr/J", j)
    for ep in batch[7]:
        q = f"ep/q{int(ep['q'])}"
        for k in EP_KEYS:
            put(f"{q}/{k}", ep[k])
        put(f"{q}/delay_s", episode_delay(ep))
        for i, x in enumerate(ep["lv"]):
            put(f"{q}/lv{i}", x)
        if "offset_moves" in ep:
            put(f"{q}/offset_moves", ep["offset_moves"])
    w.flush()


def train(out: Path, learner: int, updates: int, n_envs: int, env_kw: dict | None = None, resume: str | None = None,
          gamma: float = GAMMA, lam: float = LAM, levels: tuple = LEVELS, net_seed: int = 20261103, lagr: dict | None = None) -> Path:
    """lagr (2C): {"ref": {level: d_ref}} plus optional overrides of LAGR; needs env reward_mode 'lagr'. Logs go to TensorBoard only (V394)."""
    from torch.utils.tensorboard import SummaryWriter
    env_kw = env_kw or {}
    if bool(lagr) != (env_kw.get("reward_mode") == "lagr"):
        raise ValueError("2C needs both the lagr settings and reward_mode 'lagr'")
    if resume and (lagr or env_kw.get("base_rule")):
        raise ValueError("resume is not supported for round-1 candidates")
    torch.set_num_threads(1)
    seed = net_seed + learner
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    out.mkdir(parents=True, exist_ok=True)
    name = f"C{learner}"
    ctx = mp.get_context("spawn")
    conns, procs = [], []
    for i in range(n_envs):
        a, b = ctx.Pipe()
        kw = {**ENV, **env_kw, "share": 0.5, "levels": levels, "worker": FIRST_WORKER + learner * n_envs + i, "n_ep0": NEP0 + i, "run_dir": str(out / "rd")}
        p = ctx.Process(target=_worker, args=(b, kw), daemon=True)
        p.start()
        b.close()     # else a dead worker never gives the parent an EOF
        conns.append(a)
        procs.append(p)
    sizes = be.cav_sizes(**env_kw)
    net = Net(*sizes, cost=bool(lagr))
    if env_kw.get("base_rule"):
        init_residual(net)
    opt = torch.optim.Adam(net.parameters(), lr=LR, eps=1e-5)
    scale = scale_c = 1.0
    cfg_l = {**LAGR, **(lagr or {})}
    d_ref = {float(k): float(v) for k, v in cfg_l.get("ref", {}).items()}
    if lagr and sorted(d_ref) != sorted(float(x) for x in levels):
        raise ValueError(f"2C needs d_ref at every level: {sorted(d_ref)}")
    lam_dual = cfg_l["start"] if lagr else None
    ratios = []     # per update, the delay ratios of its episodes
    meta = {"n_local": sizes[0], "n_act": sizes[1], **({"act_env": {"base_rule": env_kw["base_rule"]}} if env_kw.get("base_rule") else {})}
    if resume:
        ck = torch.load(resume, map_location="cpu")
        net.restore(ck["net"])
        scale = ck["scale"]
    t0 = time.time()
    w = SummaryWriter(str(out / "tb" / name))
    if not resume:     # statistics only: nothing is learned from these episodes
        pilot = collect(net, scale, conns, gamma, lam, scale_c)
        net.observe(pilot[0], pilot[1])
        (out / f"{name}_pilot.json").write_text(json.dumps({"n": len(pilot[0]), "lo_mean": net.lo_mean.tolist(), "lo_var": net.lo_var.tolist(), "gl_mean": net.gl_mean.tolist(), "gl_var": net.gl_var.tolist(), "seeds": [ep["seed"] for ep in pilot[7]]}))
    for u in range(updates):
        batch = collect(net, scale, conns, gamma, lam, scale_c)
        if u == 0 and not resume:     # the critics' units are fixed once, from the first returns
            scale = max(float(batch[5].std()), 1e-3)
            if lagr:
                scale_c = max(float(batch[9].std()), 1e-3)
        st = update(net, opt, batch, scale, rng, lam_dual or 0.0, scale_c)
        if net.n_seen:
            net.observe(batch[0], batch[1])
        lam_used, j = lam_dual, None
        if lagr:
            ratios.append([episode_delay(ep) / d_ref[float(ep["q"])] for ep in batch[7]])
            if u + 1 > cfg_l["freeze"]:
                lam_dual, j = dual_step(lam_dual, [x for r in ratios[-cfg_l["window"]:] for x in r], cfg_l)
        tb_scalars(w, u, st, batch, scale, time.time() - t0, lam_used, j, scale_c if lagr else None)
        if (u + 1) % 50 == 0:
            torch.save({"net": net.state_dict(), "scale": scale, "u": u + 1, **meta, **({"scale_c": scale_c, "lambda": lam_dual} if lagr else {})}, out / f"{name}_u{u + 1}.pt")
    w.close()
    f = out / f"{name}_final.pt"
    torch.save({"net": net.state_dict(), "scale": scale, "u": updates, **meta, **({"scale_c": scale_c, "lambda": lam_dual} if lagr else {})}, f)
    (out / f"{name}_config.json").write_text(json.dumps({"learner": learner, "updates": updates, "n_envs": n_envs, "env": {**ENV, **env_kw}, "gamma": gamma, "lam": lam, "levels": levels, "seed": seed, "inputs": INPUT_NORM,
                                                         "workers": [FIRST_WORKER + learner * n_envs + i for i in range(n_envs)], "lagr": cfg_l if lagr else None, "log": "tensorboard"}))
    for c in conns:
        c.send(("close", None))
    for p in procs:
        p.join(30)
    return f


def _const(env, level: int, track: list | None = None) -> dict:
    o, _ = env.reset()
    while True:
        o, rew, _, tr, inf = env.step({v: level for v in o[0]})
        if track is not None:
            track.append((o, rew))
        if tr:
            return inf["ep"]


def smoke(out: Path) -> list:
    """V231: level 0 reproduces the zone env exactly; a level reaches SUMO; levels move at the allowed rate; rewards and
    observations are finite and sized; a short PPO run saves a model that drives an evaluation row."""
    import libsumo as ls
    from v5b.fleet import b_train as bt
    bad = []
    s = 7_419_899
    base = {"episode": 200.0, "warm": 120.0, "run_dir": str(out / "rd"), "seeds": [s], "levels": (4600.0,), "share": 0.5, "alks_asl": 0.5, "ref_delay": True, "report_net": True}
    keys = ("N", "E30", "brake3", "passed", "arrived", "mean_v", "commands", "out_E30", "out_b3", "stop_gap")
    z = be.ZoneEnv(decision=10.0, **base)
    z.reset()
    while True:
        *_, tr, inf = z.step(np.zeros(3, int))
        if tr:
            break
    z.close()
    env = be.CavEnv(**base)
    track = []
    a = _const(env, 0, track)
    if any(a[k] != inf["ep"][k] for k in keys):
        bad.append(f"level 0 differs from the zone env: { {k: (a[k], inf['ep'][k]) for k in keys} }")
    for o, rew in track:
        if o[1].shape != (len(o[0]), be.CAV_LOCAL) or o[2].shape != (be.CAV_GLOBAL,) or not np.isfinite(o[1]).all() or not np.isfinite(o[2]).all():
            bad.append("bad observation")
            break
        if not all(np.isfinite(x) for x in rew.values()):
            bad.append("bad reward")
            break
    if not a["alks_s"] or a["changes"]:
        bad.append(f"level 0: {a}")
    o, _ = env.reset()
    seen, moves = set(), {}
    while True:
        o, rew, _, tr, inf = env.step({v: 3 for v in o[0]})
        if o[3].any() and not all(env.asked[v] == env.sim.t for v, d in zip(o[0], o[3]) if d):
            bad.append("a due vehicle was not stamped")
        for v, m in env.moved.items():
            moves.setdefault(v, set()).add(m)
        for v in o[0]:
            if env.v2v_cur.get(v, be.ALKS_TAU0) != be.ALKS_TAU0:
                seen.add(round(ls.vehicle.getTau(v), 2))
        if tr:
            break
    c = inf["ep"]
    if not {1.2}.issubset(seen) or not c["changes"] or not c["ignored"]:
        bad.append(f"level 3 did not reach SUMO: {seen} {c['changes']} {c['ignored']}")
    gaps = [b - a for m in moves.values() for a, b in zip(sorted(m), sorted(m)[1:])]
    if gaps and min(gaps) < env.hold - 1e-6:
        bad.append(f"a vehicle moved faster than the hold: {min(gaps)}")
    if c["N"] == a["N"]:
        bad.append("level 3 changed nothing")
    env.close()
    t = be.CavEnv(**{**base, "report_net": False})     # the mode training runs in
    o, _ = t.reset()
    for _ in range(5):
        o, rew, *_ = t.step({})
    if np.std(list(rew.values())) <= 0 or not t.stats:
        bad.append("per-vehicle reward is absent in training mode")
    t.close()
    f = train(out / "ppo", 0, 2, 2, {"episode": 100.0, "warm": 120.0})
    row = bt._eval_one(({"pt": str(f)}, 0.5, 4600.0, s, str(out / "rd"), {**ENV, "episode": 100.0, "warm": 120.0}, True))
    if not row["alks_s"]:
        bad.append("evaluation row empty")
    return bad


def main(argv: list) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("phase", choices=("smoke", "train"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--learner", type=int, default=0)
    ap.add_argument("--updates", type=int, default=250)
    ap.add_argument("--n-envs", type=int, default=3)
    ap.add_argument("--resume")
    ap.add_argument("--env", default="{}", help="JSON options for CavEnv")
    ap.add_argument("--gamma", type=float, default=GAMMA)
    ap.add_argument("--lam", type=float, default=LAM)
    ap.add_argument("--levels", default=json.dumps(LEVELS))
    ap.add_argument("--net-seed", type=int, default=20261103, help="network seed of learner 0")
    ap.add_argument("--lagr", default="", help="2C: JSON with ref per level, overrides of LAGR")
    a = ap.parse_args(argv)
    out = Path(a.out)
    if a.phase == "smoke":
        out.mkdir(parents=True, exist_ok=True)
        bad = smoke(out)
        print("smoke:", "ok" if not bad else bad, flush=True)
        return 1 if bad else 0
    print("model:", train(out, a.learner, a.updates, a.n_envs, json.loads(a.env), a.resume, a.gamma, a.lam, tuple(json.loads(a.levels)), a.net_seed, json.loads(a.lagr) if a.lagr else None), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
