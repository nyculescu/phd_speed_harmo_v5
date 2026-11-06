"""Round 1 pre-run checks (protocol, "Order and checks before the run", items 3-6). Each prints PASS or FAIL lines and exits 1 on a failure.
usage: checks1.py identity|rows|smoke OUT_DIR [OLD_CODE_DIR]
  identity: the old frozen trainer and this one give identical weights after one update in baseline-v3's mode (needs OLD_CODE_DIR)
  rows:     stored rows reproduce on every key (T3), and a zero-offset residual reproduces the stored os1_15_10 row (3B)
  smoke:    two updates of each candidate in training mode on the smoke seed; costs, charges, offsets, TensorBoard read-back"""
import gzip
import json
import os
import shutil
import subprocess
import sys
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import torch

from common1 import BASE, CANDIDATES, ENV_V3, GAMMA, LAM, LEVELS, NET_SEED, OPPONENTS, Q, RULE, ROOT, SEEDS_SMOKE, env_for, incumbent, pt_cfg, rule_cfg
from v5b.fleet import b_env as be, c_train as ct, plant_sweep as ps

PY = sys.executable
SKIP = {"name", "cfg"}     # the arm label and the config, which names a policy path
SHORT = {"episode": 150.0, "warm": 120.0, "seeds": [SEEDS_SMOKE]}


def compare(new: dict, old: dict) -> list:
    """Keys of the stored row whose value differs in the new row, after the JSON round trip the stored rows went through."""
    new = json.loads(json.dumps(new))
    return [k for k in old if k not in SKIP and new.get(k) != old[k]]


def stored(name: str, seed: int, q: float = Q) -> dict:
    for line in gzip.open(BASE / "rows/conf3_eval_primary.jsonl.gz", "rt"):
        r = json.loads(line)
        if r["name"] == name and r["seed"] == seed and r["q"] == q:
            return r
    raise KeyError(name)


def stored_p0d(seed: int = 7_440_045, q: float = 5300.0) -> dict:
    for line in gzip.open(ROOT / "docs/research/p0c/check2_rows.jsonl.gz", "rt"):
        r = json.loads(line)
        if r["name"] == "r2_p0d" and r["seed"] == seed and r["q"] == q:
            return r
    raise KeyError("r2_p0d")


def zero_residual(path: Path) -> Path:
    """A 3B policy whose argmax is offset 0 for every input: what a run must reproduce of the rule's own arm."""
    n_local, n_act = be.cav_sizes(**CANDIDATES["res"])
    net = ct.Net(n_local, n_act)
    ct.init_residual(net)
    torch.save({"net": net.state_dict(), "scale": 1.0, "u": 0, "n_local": n_local, "n_act": n_act, "act_env": {"base_rule": CANDIDATES["res"]["base_rule"]}}, path)
    return path


def rows(out: Path, w: int = 4) -> list:
    out.mkdir(parents=True, exist_ok=True)
    rd, s = str(out / "rd"), 7_440_200
    p0d = stored_p0d()
    jobs = [("X2|os1_15_10", rule_cfg(OPPONENTS["ctrl"][RULE], "X2"), Q, s, rd),
            ("X2|d0", pt_cfg(incumbent(0, "final"), "X2"), Q, s, rd),
            ("X2|res0", pt_cfg(zero_residual(out / "res0.pt"), "X2"), Q, s, rd),
            ("r2_p0d", p0d["cfg"], 5300.0, 7_440_045, rd)]
    with ProcessPoolExecutor(w, mp_context=mp.get_context("spawn"), max_tasks_per_child=1) as ex:
        got = {r["name"]: r for r in ex.map(ps.run_one, jobs)}
    bad = []
    for name, ref in (("X2|os1_15_10", stored("X2|os1_15_10", s)), ("X2|d0", stored("X2|d0", s)), ("X2|res0", stored("X2|os1_15_10", s)), ("r2_p0d", p0d)):
        diff = compare(got[name], ref)
        print(f"{'PASS' if not diff else 'FAIL'} {name} against the stored row: {len(ref) - len(SKIP)} keys, differing {diff[:8]}", flush=True)
        bad += [name] if diff else []
    if got["X2|res0"].get("delay_s") is None:
        bad.append("delay_s missing from the row")
    return bad


def identity(out: Path, old: Path) -> list:
    """One pilot and one update in baseline-v3's mode, old and new code, same seeds: the weights must match exactly."""
    env = json.dumps({**ENV_V3, **SHORT})
    res = {}
    for tag, code in (("old", old), ("new", ROOT)):
        d = out / f"identity_{tag}"
        shutil.rmtree(d, ignore_errors=True)
        cmd = [PY, "-m", "v5b.fleet.c_train", "train", "--out", str(d), "--learner", "0", "--updates", "1", "--n-envs", "1", "--env", env,
               "--levels", json.dumps([Q]), "--gamma", str(GAMMA), "--lam", str(LAM), "--net-seed", str(NET_SEED)]
        subprocess.run(cmd, cwd=code, env={**os.environ, "PYTHONPATH": str(code), "PYTHONDONTWRITEBYTECODE": "1"}, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        res[tag] = torch.load(d / "C0_final.pt", map_location="cpu")
        res[tag + "_pilot"] = json.loads((d / "C0_pilot.json").read_text())
    a, b = res["old"]["net"], res["new"]["net"]
    diff = [k for k in a if not torch.equal(a[k], b[k])] + sorted(set(a) ^ set(b))
    same_scale = res["old"]["scale"] == res["new"]["scale"]
    same_pilot = res["old_pilot"] == res["new_pilot"]
    ok = not diff and same_scale and same_pilot
    print(f"{'PASS' if ok else 'FAIL'} identity: weights differ in {diff}, scale equal {same_scale}, pilot statistics equal {same_pilot}", flush=True)
    return [] if ok else ["identity"]


def tb_read(d: Path) -> dict:
    from tensorboard.backend.event_processing.event_accumulator import EventAccumulator
    acc = EventAccumulator(str(d), size_guidance={"scalars": 0})
    acc.Reload()
    return {t: [(e.step, e.value) for e in acc.Scalars(t)] for t in acc.Tags()["scalars"]}


def smoke(out: Path) -> list:
    bad = []
    for kind in CANDIDATES:
        d = out / f"smoke_{kind}"
        shutil.rmtree(d, ignore_errors=True)
        env = {**env_for(kind, {str(q): [0.2, 0.01, 300.0] for q in LEVELS}), **SHORT}     # placeholder references: the smoke checks wiring, not values
        lagr = {"ref": {str(q): 2.0e4 for q in LEVELS}} if kind == "lagr" else None
        f = ct.train(d, 0, 2, 3, env, None, GAMMA, LAM, LEVELS, NET_SEED, lagr)
        ck = torch.load(f, map_location="cpu")
        S = tb_read(d / "tb" / "C0")
        need = ["ppo/reward_per_decision", "ppo/entropy"] + [f"ep/e{e}/{k}" for e in range(3) for k in ("delay_s", "q", "seed")]
        need += ["lagr/lambda", "cost/per_decision", "cost/value_loss"] if kind == "lagr" else []
        need += [f"ep/e{e}/offset_moves" for e in range(3)] if kind == "res" else []
        miss = [t for t in need if t not in S]
        steps_ok = all([s for s, _ in S[t]] == [0, 1] for t in S)
        finite = all(np.isfinite(v) for t in S for _, v in S[t])
        msg = [f"missing {miss}"] if miss else []
        msg += [] if steps_ok else ["a tag lacks updates 0 and 1 exactly once"]
        msg += [] if finite else ["non-finite value"]
        if kind == "res":
            msg += [] if ck.get("act_env") == {"base_rule": CANDIDATES["res"]["base_rule"]} and ck["n_act"] == 3 and ck["n_local"] == be.CAV_LOCAL + 1 else ["checkpoint lacks its environment"]
            msg += [] if sum(v for t in S if t.endswith("offset_moves") for _, v in S[t]) > 0 else ["no offset ever moved"]
        if kind == "lagr":
            msg += [] if "critic_c.0.weight" in ck["net"] and ck["lambda"] == 1.0 else ["cost critic or lambda missing from the checkpoint"]
            msg += [] if all(v > 0 for _, v in S["cost/per_decision"]) else ["cost not positive"]
        print(f"{'PASS' if not msg else 'FAIL'} smoke {kind}: {msg or 'tags ' + str(len(S))}", flush=True)
        bad += [kind] if msg else []
    bad += smoke_env(out)
    return bad


def smoke_env(out: Path) -> list:
    """In training mode: 1A charges followers and merging vehicles; 2C returns a cost for every rewarded vehicle; v3 has no cost."""
    bad = []
    for kind in ("attr", "lagr", "v3"):
        env = be.make(**{**ct.ENV, **ENV_V3, **(CANDIDATES[kind] if kind != "v3" else {}), **SHORT, "levels": (Q,), "share": 0.5, "run_dir": str(out / "rd")})
        o, _ = env.reset()
        fdel = mdel = 0.0
        costs_ok, rew_var = True, []
        for _ in range(20):
            o, rew, _, tr, info = env.step({v: 3 for v in o[0]})
            fdel += sum(x[7] for x in env.stats.values())
            mdel += sum(x[8] for x in env.stats.values())
            rew_var.append(np.std(list(rew.values())) if rew else 0.0)
            if kind == "lagr":
                costs_ok &= set(info.get("cost", {})) == set(rew) and all(np.isfinite(x) and x >= 0 for x in info["cost"].values())
            elif "cost" in info:
                costs_ok = False
        env.close()
        msg = [] if costs_ok else ["costs wrong"]
        msg += [] if max(rew_var) > 0 else ["reward does not vary"]
        if kind == "attr":
            msg += [] if fdel > 0 and mdel > 0 else [f"charges zero: followers {fdel}, merging {mdel}"]
        print(f"{'PASS' if not msg else 'FAIL'} env {kind}: {msg or f'follower lost {fdel:.1f}, merging lost {mdel:.1f} (last second sums)'}", flush=True)
        bad += [kind] if msg else []
    return bad


if __name__ == "__main__":
    torch.set_num_threads(1)
    mode, out = sys.argv[1], Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    bad = {"identity": lambda: identity(out, Path(sys.argv[3])), "rows": lambda: rows(out), "smoke": lambda: smoke(out)}[mode]()
    print("ALL PASS" if not bad else f"FAILED: {bad}", flush=True)
    sys.exit(1 if bad else 0)
