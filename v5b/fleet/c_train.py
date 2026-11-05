"""Per-CAV control (V285): PPO with one policy shared by every ALKS, each acting on its own observation; the critic also
sees network state. SB3 needs fixed agent counts, hence this loop. Each vehicle decides once per hold on its own clock, so
every sample can move its level (V290); its reward is the mean over the interval. A vehicle that leaves is cut off, not
ended: its last value is bootstrapped, so leaving neither earns nor costs anything and the reward can't favour staying on the road.

Usage: python -m v5b.fleet.c_train smoke --out DIR
       python -m v5b.fleet.c_train train --out DIR --learner 0 [--updates 250] [--n-envs 3]
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


def _mlp(n_in: int, n_out: int) -> nn.Sequential:
    return nn.Sequential(nn.Linear(n_in, 64), nn.Tanh(), nn.Linear(64, 64), nn.Tanh(), nn.Linear(64, n_out))


class Net(nn.Module):
    def __init__(self, n_local: int = be.CAV_LOCAL, n_act: int = len(be.HEADWAYS_S)):
        super().__init__()
        self.actor = _mlp(n_local, n_act)
        self.critic = _mlp(n_local + be.CAV_GLOBAL, 1)
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
        self.net = Net(ck.get("n_local", be.CAV_LOCAL), ck.get("n_act", len(be.HEADWAYS_S)))
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


def _act(net: Net, scale: float, obs: list) -> list:
    """One forward pass over the vehicles due in every env; per env (ids, actions, log-probs, raw values, local, global)."""
    due = [([v for v, d in zip(o[0], o[3]) if d], o[1][o[3]], o[2]) for o in obs]
    lo = np.concatenate([d[1] for d in due])
    gl = np.concatenate([np.repeat(d[2][None], len(d[0]), 0) for d in due])
    with torch.no_grad():
        tl, tg = torch.from_numpy(lo), torch.from_numpy(gl)
        d = net.dist(tl)
        a = d.sample()
        lp, val = d.log_prob(a).numpy(), net.value(tl, tg).numpy() * scale
    a = a.numpy()
    out, i = [], 0
    for ids, l, g in due:
        j = i + len(ids)
        out.append((ids, a[i:j], lp[i:j], val[i:j], l, g))
        i = j
    return out


def _close(t: dict) -> None:
    if t["k"]:
        t["r"][-1] /= t["k"]
    t["k"] = 0


def collect(net: Net, scale: float, conns: list, gamma: float = GAMMA, lam: float = LAM) -> tuple:
    """One episode per env: flat arrays of observations, actions, log-probs, advantages and returns, plus the episode logs."""
    for c in conns:
        c.send(("reset", None))
    obs = [c.recv() for c in conns]
    tr = [{} for _ in conns]
    done, logs = [], [None] * len(conns)
    while logs[0] is None:
        acted = _act(net, scale, obs)
        for k, (c, (ids, a, lp, val, lo, gl)) in enumerate(zip(conns, acted)):
            for i, v in enumerate(ids):
                t = tr[k].setdefault(v, {"lo": [], "gl": [], "a": [], "lp": [], "v": [], "r": [], "k": 0})
                _close(t)
                for key, x in (("lo", lo[i]), ("gl", gl), ("a", a[i]), ("lp", lp[i]), ("v", val[i]), ("r", 0.0)):
                    t[key].append(x)
            c.send(("step", dict(zip(ids, a.tolist()))))
        res = [c.recv() for c in conns]
        obs = [r[0] for r in res]
        for k, (o2, rew, _, trunc, info) in enumerate(res):
            for v, x in rew.items():
                t = tr[k].get(v)
                if t is not None:
                    t["r"][-1] += x
                    t["k"] += 1
            live = set(o2[0])
            for v in [v for v in tr[k] if v not in live]:     # left: the last value stands in for what follows
                t = tr[k].pop(v)
                _close(t)
                done.append((t, t["v"][-1]))
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
            for v, x in zip(live, net.value(lo, gl).numpy() * scale):
                t = tr[k][v]
                _close(t)
                done.append((t, x))
    lo, gl, a, lp, adv, ret, r = [], [], [], [], [], [], []
    for t, boot in done:
        rr, vv = np.array(t["r"], dtype=np.float32), np.array(t["v"], dtype=np.float32)
        x = gae(rr, vv, float(boot), gamma, lam)
        lo += t["lo"]
        gl += t["gl"]
        a += t["a"]
        lp += t["lp"]
        adv.append(x)
        ret.append(x + vv)
        r.append(rr)
    return (np.array(lo, dtype=np.float32), np.array(gl, dtype=np.float32), np.array(a, dtype=np.int64), np.array(lp, dtype=np.float32),
            np.concatenate(adv), np.concatenate(ret), np.concatenate(r), logs)


def update(net: Net, opt, batch: tuple, scale: float, rng: np.random.Generator) -> dict:
    lo, gl, a, lp, adv, ret = (torch.from_numpy(x) for x in batch[:6])
    ret = ret / scale
    n = len(a)
    ent = vl = kl = cf = 0.0
    k = 0
    with torch.no_grad():
        ev = 1.0 - float((net.value(lo, gl) - ret).var() / ret.var().clamp_min(1e-8))
    for _ in range(EPOCHS):
        perm = torch.from_numpy(rng.permutation(n))
        for i in range(0, n - BATCH + 1, BATCH):
            b = perm[i:i + BATCH]
            d = net.dist(lo[b])
            ad = adv[b]
            ad = (ad - ad.mean()) / (ad.std() + 1e-8)
            ratio = (d.log_prob(a[b]) - lp[b]).exp()
            pg = -torch.min(ratio * ad, ratio.clamp(1 - CLIP, 1 + CLIP) * ad).mean()
            v = ((net.value(lo[b], gl[b]) - ret[b]) ** 2).mean()
            h = d.entropy().mean()
            loss = pg + VF * v - ENT * h
            opt.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(net.parameters(), GRAD)
            opt.step()
            ent += float(h.detach())
            vl += float(v.detach())
            with torch.no_grad():
                kl += float((lp[b] - d.log_prob(a[b])).mean())
                cf += float(((ratio - 1.0).abs() > CLIP).float().mean())
            k += 1
    return {"entropy": ent / max(k, 1), "value_loss": vl / max(k, 1), "n": n, "kl": kl / max(k, 1), "clipfrac": cf / max(k, 1), "ev": ev}


def train(out: Path, learner: int, updates: int, n_envs: int, env_kw: dict | None = None, resume: str | None = None,
          gamma: float = GAMMA, lam: float = LAM, levels: tuple = LEVELS, net_seed: int = 20261103) -> Path:
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
        kw = {**ENV, **(env_kw or {}), "share": 0.5, "levels": levels, "worker": FIRST_WORKER + learner * n_envs + i, "n_ep0": NEP0 + i, "run_dir": str(out / "rd")}
        p = ctx.Process(target=_worker, args=(b, kw), daemon=True)
        p.start()
        b.close()     # else a dead worker never gives the parent an EOF
        conns.append(a)
        procs.append(p)
    sizes = be.cav_sizes(**(env_kw or {}))
    net = Net(*sizes)
    opt = torch.optim.Adam(net.parameters(), lr=LR, eps=1e-5)
    scale = 1.0
    if resume:
        ck = torch.load(resume, map_location="cpu")
        net.restore(ck["net"])
        scale = ck["scale"]
    t0 = time.time()
    with (out / f"{name}_episodes.jsonl").open("a") as lg, (out / f"{name}_updates.jsonl").open("a") as lu:
        if not resume:     # statistics only: nothing is learned from these episodes
            pilot = collect(net, scale, conns, gamma, lam)
            net.observe(pilot[0], pilot[1])
            (out / f"{name}_pilot.json").write_text(json.dumps({"n": len(pilot[0]), "lo_mean": net.lo_mean.tolist(), "lo_var": net.lo_var.tolist(), "gl_mean": net.gl_mean.tolist(), "gl_var": net.gl_var.tolist(), "seeds": [ep["seed"] for ep in pilot[7]]}))
        for u in range(updates):
            batch = collect(net, scale, conns, gamma, lam)
            if u == 0 and not resume:     # the critic's unit is fixed once, from the first returns
                scale = max(float(batch[5].std()), 1e-3)
            st = update(net, opt, batch, scale, rng)
            if net.n_seen:
                net.observe(batch[0], batch[1])
            for ep in batch[7]:
                lg.write(json.dumps({**ep, "u": u, "wall": round(time.time() - t0, 1)}) + "\n")
            lg.flush()
            lu.write(json.dumps({**st, "u": u, "r": float(batch[6].mean()), "scale": scale, "wall": round(time.time() - t0, 1)}) + "\n")
            lu.flush()
            if (u + 1) % 50 == 0:
                torch.save({"net": net.state_dict(), "scale": scale, "u": u + 1, "n_local": sizes[0], "n_act": sizes[1]}, out / f"{name}_u{u + 1}.pt")
    f = out / f"{name}_final.pt"
    torch.save({"net": net.state_dict(), "scale": scale, "u": updates, "n_local": sizes[0], "n_act": sizes[1]}, f)
    (out / f"{name}_config.json").write_text(json.dumps({"learner": learner, "updates": updates, "n_envs": n_envs, "env": {**ENV, **(env_kw or {})}, "gamma": gamma, "lam": lam, "levels": levels, "seed": seed, "inputs": INPUT_NORM,
                                                         "workers": [FIRST_WORKER + learner * n_envs + i for i in range(n_envs)]}))
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
    a = ap.parse_args(argv)
    out = Path(a.out)
    if a.phase == "smoke":
        out.mkdir(parents=True, exist_ok=True)
        bad = smoke(out)
        print("smoke:", "ok" if not bad else bad, flush=True)
        return 1 if bad else 0
    print("model:", train(out, a.learner, a.updates, a.n_envs, json.loads(a.env), a.resume, a.gamma, a.lam, tuple(json.loads(a.levels)), a.net_seed), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
