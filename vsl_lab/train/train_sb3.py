"""SB3 / sb3-contrib training driver for the lab envs (roadmap §5, §9).

- learner and every env worker pinned to E-cores; torch.set_num_threads(1)
- compute watchdog (author rule 2026-10-05, vsl_lab/ops/guard.py): CPU > 90 % for 2 min or the v6 thermal hysteresis
  SIGSTOPs all env workers (the learner blocks on the pipes) until clear. Pauses do not change results.
- validation on fixed validation seeds every `val_every` updates (deterministic policy); checkpoint
  selection on validation seeds only; the final policy is always saved and evaluated too
- health: every finished training episode reports PASS/WARN/FAIL; FAIL share > 1 % (after 50 episodes) stops
- everything (progress, validation curve, health, config) goes to the run dir; a ledger row at the end

python -m vsl_lab.train.train_sb3 --env bn4 --reward out --algo ppo --updates 500 --n-envs 12 --seed 0 --tag p_bn4_out
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import os
import signal
import statistics
import threading
import time
from pathlib import Path

import numpy as np
import torch

from vsl_lab.config import WORKER_CPUS, RUNS_ROOT, TEMP_SMOOTH_S
from vsl_lab.ops import ledger
from vsl_lab.ops.thermal import package_temp_c


def make_env_fn(env_name: str, env_kwargs: dict, rank: int):
    def _f():
        kw = {k: v for k, v in env_kwargs.items() if k not in ("rank_seed", "val_perturb_cycle")}
        if env_name == "bn4":
            from vsl_lab.envs.bn4_env import BN4Env
            env = BN4Env(**kw)
        elif env_name == "ring":
            from vsl_lab.envs.ring_env import RingEnv
            env = RingEnv(**kw)
        elif env_name == "mrg3":
            from vsl_lab.envs.mrg3_env import MRG3Env
            env = MRG3Env(**kw)
        else:
            raise ValueError(env_name)
        # Episode seeds come from env.np_random, which SB3 seeds per rank via VecEnv.seed(seed + rank).
        return env
    return _f


class Watchdog(threading.Thread):
    """Compute guard for training (author rule 2026-10-05, vsl_lab/ops/guard.py). A learner cannot run on a subset of
    its env workers, so all of them are paused together: when the CPU has been > 90 % for 2 min, or the v6 thermal
    hysteresis is in its paused state (>= 98 C for 150 s, or >= 99 C at once); resumed when neither holds."""

    def __init__(self, pids_fn, poll_s=0.5):
        super().__init__(daemon=True)
        from vsl_lab.config import GUARD_CFG
        from vsl_lab.ops.guard import ComputeGuard
        self.pids_fn = pids_fn
        self.poll_s = poll_s
        self.guard = ComputeGuard(cfg_path=GUARD_CFG)
        self.win = collections.deque(maxlen=int(TEMP_SMOOTH_S / poll_s))
        self.paused = False
        self.n_pauses = 0
        self.max_smoothed = 0.0
        self.paused_s = 0.0
        self.stop_flag = False

    def _signal(self, sig):
        for pid in self.pids_fn():
            try:
                os.kill(pid, sig)
            except OSError:
                pass

    @staticmethod
    def _cpu():
        with open("/proc/stat") as fh:
            v = [int(x) for x in fh.readline().split()[1:]]
        return sum(v), v[3] + (v[4] if len(v) > 4 else 0)

    def run(self):
        prev = self._cpu()
        util_win = collections.deque(maxlen=8)
        while not self.stop_flag:
            t = package_temp_c()
            if t == t:
                self.win.append(t)
            self.max_smoothed = max(self.max_smoothed, sum(self.win) / len(self.win) if self.win else 0.0)
            cur = self._cpu()
            if cur[0] > prev[0]:
                util_win.append(1.0 - (cur[1] - prev[1]) / (cur[0] - prev[0]))
            prev = cur
            util = sum(util_win) / len(util_win) if util_win else 0.0
            now = time.time()
            self.guard.update(now, util, t, n_paused=0)
            g = self.guard
            cpu_hold = g.cpu_hot_since is not None and now - g.cpu_hot_since >= g.cfg["cpu_hold_s"]
            want = g.thermal_paused or cpu_hold
            if want and not self.paused:
                self._signal(signal.SIGSTOP)
                self.paused = True
                self.n_pauses += 1
            elif not want and self.paused and (g.cpu_cool_since is not None
                                               and now - g.cpu_cool_since >= g.cfg["step_s"]):
                self._signal(signal.SIGCONT)
                self.paused = False
            if self.paused:
                self.paused_s += self.poll_s
            time.sleep(self.poll_s)
        if self.paused:
            self._signal(signal.SIGCONT)


def evaluate(model, venv, n_episodes: int, recurrent: bool = False) -> dict:
    obs = venv.reset()
    n = venv.num_envs
    done_metrics, healths = [], []
    state, ep_start = None, np.ones((n,), dtype=bool)
    while len(done_metrics) < n_episodes:
        if recurrent:
            act, state = model.predict(obs, state=state, episode_start=ep_start, deterministic=True)
        else:
            act, _ = model.predict(obs, deterministic=True)
        obs, rew, dones, infos = venv.step(act)
        ep_start = dones
        for d, inf in zip(dones, infos):
            if d and "episode_metrics" in inf:
                done_metrics.append(inf["episode_metrics"])
                healths.append(inf.get("health", "?"))
    done_metrics = done_metrics[:n_episodes]
    keys = done_metrics[0].keys()
    out = {k: float(np.mean([m[k] for m in done_metrics])) for k in keys if isinstance(done_metrics[0][k], (int, float))}
    out["per_episode"] = done_metrics
    out["health"] = {h: healths.count(h) for h in set(healths)}
    return out


class LinearDecay:
    """lr * max(0, 1 - n / updates), with n set by the training loop before each update (model.learn() is called
    once per update, so SB3's own progress_remaining restarts every call). Picklable, so model.save() works."""

    def __init__(self, lr: float, updates: int):
        self.lr, self.updates, self.n = lr, max(int(updates), 1), 0

    def __call__(self, _progress_remaining: float) -> float:
        return self.lr * max(0.0, 1.0 - self.n / self.updates)


def build_model(a, venv, lr):
    """The SB3 model for --algo. `lr` (float or LinearDecay) is passed to EVERY algorithm. Before 2026-10-04,
    RecurrentPPO and TRPO were given the constant a.lr, so --lr-decay was silently ignored for them (P-M3b, PMF,
    P-M4 and the R6 candidate trained at constant 3e-4 although their protocols said "with decay")."""
    policy_kwargs = dict(net_arch=dict(pi=a.net, vf=a.net), activation_fn=torch.nn.Tanh)
    if a.log_std_init != 0.0:
        policy_kwargs["log_std_init"] = a.log_std_init
    if a.algo == "ppo":
        from stable_baselines3 import PPO
        return PPO("MlpPolicy", venv, n_steps=a.n_steps, batch_size=a.batch, n_epochs=a.epochs, learning_rate=lr,
                   gamma=a.gamma, gae_lambda=a.gae, ent_coef=a.ent, policy_kwargs=policy_kwargs, seed=a.seed,
                   verbose=0, device="cpu")
    if a.algo == "recurrentppo":
        from sb3_contrib import RecurrentPPO
        return RecurrentPPO("MlpLstmPolicy", venv, n_steps=a.n_steps, batch_size=a.batch, n_epochs=a.epochs,
                            learning_rate=lr, gamma=a.gamma, gae_lambda=a.gae, ent_coef=a.ent, seed=a.seed,
                            policy_kwargs=dict(net_arch=dict(pi=a.net, vf=a.net), lstm_hidden_size=64,
                                               **({"log_std_init": a.log_std_init} if a.log_std_init != 0.0 else {})),
                            verbose=0, device="cpu")
    if a.algo == "trpo":
        from sb3_contrib import TRPO
        return TRPO("MlpPolicy", venv, n_steps=a.n_steps, batch_size=a.batch, learning_rate=lr, gamma=a.gamma,
                    gae_lambda=a.gae, policy_kwargs=policy_kwargs, seed=a.seed, verbose=0, device="cpu")
    raise NotImplementedError(a.algo)


def _entropy_loss_from_buffer(model):
    """-mean policy entropy over the last rollout's observations, for algorithms that log no train/entropy_loss
    (sb3-contrib TRPO; review fix #9). Same sign convention as SB3's entropy_loss. '' if not computable."""
    try:
        buf = model.rollout_buffer
        obs = buf.observations.reshape(-1, *model.observation_space.shape)
        with torch.no_grad():
            dist = model.policy.get_distribution(torch.as_tensor(obs, dtype=torch.float32))
            return -float(dist.entropy().mean())
    except Exception:
        return ""


def action_dim_of(space):
    """Box -> number of action dimensions (continuous entropy rule), otherwise None."""
    from gymnasium import spaces
    return int(np.prod(space.shape)) if isinstance(space, spaces.Box) else None


def n_actions_of(space):
    """Discrete -> n, MultiDiscrete -> list of n, otherwise None (for the C1f entropy floor)."""
    from gymnasium import spaces
    if isinstance(space, spaces.Discrete):
        return int(space.n)
    if isinstance(space, spaces.MultiDiscrete):
        return [int(n) for n in space.nvec]
    return None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", default="bn4")
    ap.add_argument("--reward", default="out")
    ap.add_argument("--algo", default="ppo", choices=["ppo", "recurrentppo", "sac", "tqc", "trpo"])
    ap.add_argument("--updates", type=int, default=500)
    ap.add_argument("--n-envs", type=int, default=12)
    ap.add_argument("--n-steps", type=int, default=128)
    ap.add_argument("--batch", type=int, default=256)
    ap.add_argument("--epochs", type=int, default=10)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--gamma", type=float, default=0.99)
    ap.add_argument("--gae", type=float, default=0.95)
    ap.add_argument("--ent", type=float, default=0.0)
    ap.add_argument("--net", type=int, nargs="+", default=[128, 128])
    ap.add_argument("--log-std-init", type=float, default=0.0)
    ap.add_argument("--lr-decay", action="store_true", help="linear learning-rate decay to 0 over the run")
    ap.add_argument("--seed", type=int, default=0, help="learner seed index (0-4)")
    ap.add_argument("--max-fail-share", type=float, default=0.01,
                    help="health stop rule: stop when the FAIL share of training episodes exceeds this (after 50)")
    ap.add_argument("--fail-min-episodes", type=int, default=50, help="health stop rule applies after this many episodes")
    ap.add_argument("--val-every", type=int, default=25)
    ap.add_argument("--val-conds", type=float, nargs="+", default=None,
                    help="fixed validation conditions: inflows (bn4) or ring lengths (ring)")
    ap.add_argument("--val-seeds-per", type=int, default=2)
    ap.add_argument("--val-seed0", type=int, default=None)
    ap.add_argument("--val-metric", default=None, help="episode metric to maximise for checkpoint selection")
    ap.add_argument("--env-kwargs", default="{}")
    ap.add_argument("--tag", default="pilot")
    a = ap.parse_args(argv)

    os.sched_setaffinity(0, set(WORKER_CPUS))
    torch.set_num_threads(1)
    from stable_baselines3.common.vec_env import SubprocVecEnv, VecMonitor

    if not 0 <= a.seed <= 4:
        # 2,000 training seeds per learner in a 10,000-seed track pool: seed 5 would draw from the next track's pool
        # (it did, for P-M4 learner 5: 7,220,000-7,221,999 = the T2 DRL range; disclosed 2026-10-04)
        raise SystemExit(f"--seed {a.seed}: learner seed index must be 0-4 (track DRL pool = 5 x 2,000 seeds)")
    env_kwargs = json.loads(a.env_kwargs)
    track = {"bn4": "t1", "ring": "t3", "mrg3": "t2"}[a.env]
    seed_pool = {"t1": (7210000 + a.seed * 2000, 7210000 + a.seed * 2000 + 1999),
                 "t2": (7220000 + a.seed * 2000, 7220000 + a.seed * 2000 + 1999),
                 "t3": (7230000 + a.seed * 2000, 7230000 + a.seed * 2000 + 1999)}[track]
    run_id = f"{a.env}_{a.algo}_{a.reward}_u{a.updates}_e{a.n_envs}_s{a.seed}_{int(time.time())}_pid{os.getpid()}"
    run_dir = RUNS_ROOT / track / "train" / a.tag / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    cfg = vars(a) | {"seed_pool": seed_pool, "run_id": run_id}
    (run_dir / "config.json").write_text(json.dumps(cfg, indent=1))

    train_kwargs = dict(env_kwargs, reward=a.reward, seed_pool=seed_pool, tag=f"{a.tag}_train_s{a.seed}",
                        rank_seed=a.seed)
    conds = a.val_conds or ({"bn4": [1600.0, 2000.0, 2400.0], "ring": [230.0, 260.0], "mrg3": [0.1, 0.3, 0.5]}[a.env])
    seed0 = a.val_seed0 or {"t1": 7110300, "t2": 7120300, "t3": 7130300}[track]
    val_metric = a.val_metric or {"bn4": "outflow_ctrl_vph", "ring": "mean_speed", "mrg3": "tts_ctrl_vehh"}[a.env]
    val_sign = -1.0 if val_metric in ("tts_ctrl_vehh", "mean_time_in_system_s", "score_h", "tts_system_ctrl_vehh") else 1.0
    a.val_n = len(conds) * a.val_seeds_per
    val_specs = [(conds[i % len(conds)], seed0 + i // len(conds)) for i in range(a.val_n)]
    val_seeds = [sd for _, sd in val_specs]
    val_kwargs = dict(env_kwargs, reward=a.reward, tag=f"{a.tag}_val_s{a.seed}", rank_seed=a.seed)
    cfg["val_specs"] = val_specs
    cfg["val_metric"] = val_metric
    (run_dir / "config.json").write_text(json.dumps(cfg, indent=1))

    venv = VecMonitor(SubprocVecEnv([make_env_fn(a.env, train_kwargs, i) for i in range(a.n_envs)],
                                    start_method="forkserver"))

    def val_env_fn(i):
        c, sd = val_specs[i]
        kw = dict(val_kwargs, eval_seeds=[sd])
        if a.env == "bn4":
            kw["inflow"] = (c, c)
            if kw.get("val_perturb_cycle") is not None:   # P-M: validation spec i gets kind cycle[i % len(cycle)]
                cyc = kw["val_perturb_cycle"]
                kw["perturb"], kw["perturb_mix"] = cyc[i % len(cyc)], None
        elif a.env == "ring":
            kw["eval_L"] = c
        else:
            kw["eval_p_nc"] = c
        return make_env_fn(a.env, kw, i)
    vval = SubprocVecEnv([val_env_fn(i) for i in range(a.val_n)], start_method="forkserver")

    def pids():
        out = []
        for v in (venv.venv if hasattr(venv, "venv") else venv, vval):
            out += [p.pid for p in getattr(v, "processes", [])]
        return out
    wd = Watchdog(pids)
    wd.start()

    lr = LinearDecay(a.lr, a.updates) if a.lr_decay else a.lr
    recurrent = a.algo == "recurrentppo"
    model = build_model(a, venv, lr)

    from stable_baselines3.common.callbacks import BaseCallback

    class CB(BaseCallback):
        def __init__(self):
            super().__init__()
            self.n_upd = 0
            self.health = collections.Counter()
            self.best = -np.inf
            self.stop = False
            self.max_fail_share = a.max_fail_share
            self.fail_min_episodes = a.fail_min_episodes
            self.f_prog = open(run_dir / "progress.csv", "w", newline="")
            self.w_prog = csv.writer(self.f_prog)
            self.w_prog.writerow(["update", "timesteps", "wall_s", "ep_rew_mean", "ep_outflow_mean",
                                  "health_pass", "health_warn", "health_fail", "wd_paused", "wd_max_c",
                                  "explained_var", "entropy", "approx_kl"])
            self.f_val = open(run_dir / "val.csv", "w", newline="")
            self.w_val = csv.writer(self.f_val)
            self.w_val.writerow(["update", "timesteps", "val_return", "val_metric", "val_metric_value",
                                 "val_health", "val_per_episode"])
            self.t0 = time.time()
            self.recent = collections.deque(maxlen=50)

        def _on_step(self) -> bool:
            for inf in self.locals.get("infos", []):
                if "health" in inf:
                    self.health[inf["health"]] += 1
                if "episode_metrics" in inf:
                    self.recent.append(inf["episode_metrics"])
            n_ep = sum(self.health.values())
            if n_ep >= self.fail_min_episodes and self.health["FAIL"] / n_ep > self.max_fail_share:
                self.stop = True
                return False
            return True

        def _on_rollout_end(self) -> None:
            self.n_upd += 1

        def _on_training_start(self) -> None:
            pass

        def log_update(self):
            lg = model.logger.name_to_value
            rec = list(self.recent)
            self.w_prog.writerow([self.n_upd, model.num_timesteps, round(time.time() - self.t0, 1),
                                  np.mean([r["return"] for r in rec]) if rec else "",
                                  np.mean([r["outflow_ctrl_vph"] for r in rec]) if rec and "outflow_ctrl_vph" in rec[0] else "",
                                  self.health["PASS"], self.health["WARN"], self.health["FAIL"], wd.n_pauses,
                                  round(wd.max_smoothed, 1), lg.get("train/explained_variance", ""),
                                  lg.get("train/entropy_loss", _entropy_loss_from_buffer(model)),
                                  lg.get("train/approx_kl", "")])
            self.f_prog.flush()

        def validate(self, label):
            ev = evaluate(model, vval, a.val_n, recurrent=recurrent)
            self.w_val.writerow([label, model.num_timesteps, ev.get("return"), val_metric, ev.get(val_metric),
                                 json.dumps(ev["health"]),
                                 json.dumps([round(m.get(val_metric, float("nan")), 3) for m in ev["per_episode"]])])
            self.f_val.flush()
            score = val_sign * ev.get(val_metric, -val_sign * np.inf)
            if label not in ("final", 0) and score > self.best:
                self.best = score
                model.save(run_dir / "best_val_model.zip")
            return ev

    cb = CB()
    steps_per_update = a.n_steps * a.n_envs
    t_start = time.time()
    try:
        ev0 = cb.validate(0)
        for u in range(1, a.updates + 1):
            if a.lr_decay:
                lr.n = u - 1
            model.learn(total_timesteps=steps_per_update, reset_num_timesteps=False, callback=cb,
                        progress_bar=False)
            cb.log_update()
            if cb.stop:
                break
            if u % a.val_every == 0:
                cb.validate(u)
        model.save(run_dir / "final_model.zip")
        ev_final = cb.validate("final")
    finally:
        wd.stop_flag = True
        wd.join(timeout=5)
        cb.f_prog.close()
        cb.f_val.close()
        venv.close()
        vval.close()
    from vsl_lab.train.convergence import check_run_dir
    conv = check_run_dir(run_dir, n_actions=n_actions_of(model.action_space), action_dim=action_dim_of(model.action_space))
    (run_dir / "convergence.json").write_text(json.dumps(conv, indent=1, default=str))
    summary = {"run_id": run_id, "run_dir": str(run_dir), "updates_done": cb.n_upd, "stopped_health": cb.stop,
               "wall_s": round(time.time() - t_start, 1), "health_train": dict(cb.health),
               "val_initial": {k: v for k, v in ev0.items() if k != "per_episode"},
               "val_final": {k: v for k, v in ev_final.items() if k != "per_episode"},
               "best_val_return": cb.best, "watchdog_pauses": wd.n_pauses, "watchdog_max_c": round(wd.max_smoothed, 1),
               "converged_c1": conv["converged"], "c1_pass": conv["pass"]}
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=1, default=str))
    ledger.append(track.upper(), "R3", "P" if a.updates < 500 else "F", f"{a.env}_{a.algo}_{a.reward}",
                  cfg, f"train {seed_pool[0]}-{seed_pool[1]}; val {val_seeds[0]}-{val_seeds[-1]}", cb.n_upd,
                  {"PASS": cb.health["PASS"], "WARN": cb.health["WARN"], "FAIL": cb.health["FAIL"]},
                  {"val_initial_return": summary["val_initial"].get("return"),
                   "val_final_return": summary["val_final"].get("return"),
                   "val_metric": val_metric, "val_initial_metric": summary["val_initial"].get(val_metric),
                   "val_final_metric": summary["val_final"].get(val_metric),
                   "best_val_return": cb.best, "converged_c1": conv["converged"],
                   "c1_final_vs_best": conv["C1a_final_vs_best"]}, notes=str(run_dir))
    print(json.dumps(summary, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
