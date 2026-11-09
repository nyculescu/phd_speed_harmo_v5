"""Plan B (planb.md §3.5): MPC-F, the fitted-model MPC. Ported from claude/v5b-core:vsl_lab/jobs/mpcf.py (data by held
actions, a 2 x 64 tanh MLP on standardised inputs, receding-horizon choice); the controller is v5b/fleet/planb_ctrl.MpcF.

usage: mpcf.py all --out DIR --actions FILE --conds S,SURGE,TRUCK [--workers N]
  --actions: written by `plan6.py inputs` (p333, the steady pick, 3E-T, each passing cell's 3E-C), so plan6 freeze can check it.
Steps, each resumable from its rows: data (4 schedules per seed on 7,480,270-309 per condition), fixed (every action alone on the
same seeds; the best fixed action = the lowest sum over conditions of per-condition median realised cost), fit (seeds split once:
8 held out, 4 for early stopping, the rest for training; held-out MSE at 50 % and 100 % of the training seeds), gate (MPC-F and
every fixed action on 7,480,310-339; MPC-F passes if its sum over conditions of per-condition median realised cost does not
exceed the best fixed action's). A failed gate makes MPC-F a disclosed failed build."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pb  # noqa: E402

FIT, GATE = pb.seeds(7_480_270, 7_480_309), pb.seeds(7_480_310, 7_480_339)
SCHEDULES = 4
SPLIT_SEED, N_TEST, N_STOP = 20261108, 8, 4
EPOCHS, PATIENCE, BATCH, LR, WD = 400, 30, 256, 1e-3, 1e-5


def run_data(out: Path, actions: list, conds: list, workers: int, runner) -> list:
    """One run per (condition, schedule, seed); the schedule's rng seed is seed x 10 + schedule, as gen_one."""
    rows = []
    for c in conds:
        for r in range(SCHEDULES):
            for s in FIT:
                cfgs = {f"{c}|data{r}|{s}": pb.cfg({"mpcf": {"actions": actions, "data": s * 10 + r}}, c)}
                rows.append(((c, r, s), cfgs))
    cfgs = {k: v for _, d in rows for k, v in d.items()}
    # each config runs on its own seed only
    cache = {(x["name"], x["q"], x["seed"]): x for x in pb.cma2.load(out / "data_runs.jsonl")}
    jobs = {}
    for (c, r, s), d in rows:
        for n, cf in d.items():
            if (n, pb.Q, s) not in cache:
                jobs[n] = (cf, s)
    for attempt in range(pb.cma2.ATTEMPTS):
        todo = [(n, cf, pb.Q, s, str(out / "rd")) for n, (cf, s) in jobs.items() if (n, pb.Q, s) not in cache]
        if not todo:
            break
        try:
            for (n, q, s), m in runner(todo, workers):
                cache[(n, q, s)] = {"name": n, **m}
                pb.cma2.append(out / "data_runs.jsonl", cache[(n, q, s)])
        except (RuntimeError, pb.cma2.BrokenProcessPool) as x:
            print(f"attempt {attempt + 1}: {x}", flush=True)
    missing = [n for (c, r, s), d in rows for n in d if (n, pb.Q, s) not in cache]
    if missing:
        raise SystemExit(f"{len(missing)} data runs missing; start again to continue")
    return [{"cond": c, "seed": s, **smp} for (c, r, s), d in rows for n in d for smp in cache[(n, pb.Q, s)]["ctrl_log"]]


def medians(rows: dict, names: list, conds: list, seed_list: list) -> dict:
    """name -> {cond: median realised cost, "sum": the sum over conditions}."""
    out = {}
    for n in names:
        m = {c: float(np.median([pb.realised_cost(rows[(f"{c}|{n}", s)]) for s in seed_list])) for c in conds}
        out[n] = {**m, "sum": sum(m.values())}
    return out


def split(seed_list: list) -> tuple:
    rng = np.random.default_rng(SPLIT_SEED)
    p = [int(x) for x in rng.permutation(seed_list)]
    return set(p[:N_TEST]), set(p[N_TEST:N_TEST + N_STOP]), [s for s in seed_list if s in set(p[N_TEST + N_STOP:])]


def fit(samples: list, n_act: int, train_seeds: list, stop_seeds: set, test_seeds: set) -> dict:
    import torch
    from v5b.fleet.planb_ctrl import Net, onehot_features
    torch.manual_seed(SPLIT_SEED)
    torch.set_num_threads(1)
    X = np.stack([onehot_features(np.asarray(x["x"], np.float32), x["a"], n_act) for x in samples]).astype(np.float32)
    Y = np.array([x["y"] for x in samples], np.float32)
    sd_of = np.array([x["seed"] for x in samples])
    tr, st, te = np.isin(sd_of, train_seeds), np.isin(sd_of, list(stop_seeds)), np.isin(sd_of, list(test_seeds))
    mu, sd = X[tr].mean(0), X[tr].std(0) + 1e-6
    ymu, ysd = float(Y[tr].mean()), float(Y[tr].std() + 1e-6)
    Xt, Yt = torch.from_numpy((X - mu) / sd), torch.from_numpy((Y - ymu) / ysd).reshape(-1, 1)
    net = Net(X.shape[1]).m
    opt = torch.optim.Adam(net.parameters(), lr=LR, weight_decay=WD)
    rng = np.random.default_rng(SPLIT_SEED)
    idx_tr, idx_st, idx_te = (np.nonzero(m)[0] for m in (tr, st, te))
    best, best_state, bad, ep = np.inf, None, 0, 0
    for ep in range(EPOCHS):
        net.train()
        perm = rng.permutation(idx_tr)
        for i in range(0, len(perm), BATCH):
            b = perm[i:i + BATCH]
            opt.zero_grad()
            torch.nn.functional.mse_loss(net(Xt[b]), Yt[b]).backward()
            opt.step()
        net.eval()
        with torch.no_grad():
            vl = float(torch.nn.functional.mse_loss(net(Xt[idx_st]), Yt[idx_st]))
        if vl < best - 1e-5:
            best, best_state, bad = vl, {k: v.clone() for k, v in net.state_dict().items()}, 0
        else:
            bad += 1
            if bad >= PATIENCE:
                break
    net.load_state_dict(best_state)
    with torch.no_grad():
        pv = net(Xt[idx_te]).numpy().reshape(-1) * ysd + ymu
    yv = Y[idx_te]
    mse = float(np.mean((pv - yv) ** 2))
    return {"state": net.state_dict(), "mu": mu, "sd": sd, "ymu": ymu, "ysd": ysd, "n_act": n_act,
            "report": {"n_train": int(tr.sum()), "n_stop": int(st.sum()), "n_test": int(te.sum()), "test_mse": mse,
                       "test_r2": 1.0 - mse / float(np.var(yv)) if len(yv) > 1 and np.var(yv) > 0 else None, "epochs": ep + 1}}


def all_steps(out: Path, actions: list, conds: list, workers: int, runner=pb.run_jobs) -> dict:
    """Fit once: a stored fit record and its model are reused (their SHA-256 checked), never refitted, and gate rows are keyed by
    the model's SHA, so a resumed gate cannot mix models (review F8)."""
    import torch
    names = [f"a{i}" for i in range(len(actions))]
    fixed_cfgs = {f"{c}|{n}": pb.cfg(actions[i], c) for c in conds for i, n in enumerate(names)}
    meta = pb.guard(out, {"actions": actions, "conds": conds}, fixed_cfgs, strict=runner is pb.run_jobs)
    samples = run_data(out, actions, conds, workers, runner)
    fx = pb.batch(fixed_cfgs, FIT, out / "fixed_runs.jsonl", out / "rd", workers, runner)
    fixed = medians(fx, names, conds, FIT)
    best_fixed = min(names, key=lambda n: (fixed[n]["sum"], n))
    model, fitf = out / "mpcf_model.pt", out / "fit.json"     # the model predicts standardised cost; the argmin does not depend on the scale
    if fitf.exists():
        fr = json.loads(fitf.read_text())
        if not model.exists() or hashlib.sha256(model.read_bytes()).hexdigest() != fr["model_sha256"]:
            raise SystemExit(f"{model} differs from {fitf}; use a new folder")
    else:
        if model.exists():
            raise SystemExit(f"{model} has no fit record; use a new folder")
        test, stop, train = split(FIT)
        half = sorted(train)[:len(train) // 2]
        m_half = fit(samples, len(actions), half, stop, test)
        m_full = fit(samples, len(actions), train, stop, test)
        torch.save({k: v for k, v in m_full.items() if k != "report"}, model)
        fr = {"model_sha256": hashlib.sha256(model.read_bytes()).hexdigest(), "split": {"test": sorted(test), "stop": sorted(stop), "train": train},
              "fit_half": m_half["report"], "fit_full": m_full["report"]}
        pb.cma2.write_json(fitf, fr)
    sha = fr["model_sha256"]
    tag = f"mpcf_{sha[:12]}"
    gate_cfgs = {f"{c}|{tag}": pb.cfg({"mpcf": {"actions": actions, "model": str(model), "model_sha256": sha}}, c) for c in conds} | fixed_cfgs
    gr = pb.batch(gate_cfgs, GATE, out / "gate_runs.jsonl", out / "rd", workers, runner)
    gm = medians(gr, [tag] + names, conds, GATE)
    gm["mpcf"] = gm.pop(tag)
    passed = gm["mpcf"]["sum"] <= gm[best_fixed]["sum"]
    res = {"conds": conds, "actions": actions, "code": meta["code"], "n_samples": len(samples), "fixed_on_fit_seeds": fixed, "best_fixed": best_fixed,
           "split": fr["split"], "fit_half": fr["fit_half"], "fit_full": fr["fit_full"], "model": model.name, "model_sha256": sha, "gate": gm,
           "gate_passed": bool(passed)}
    pb.cma2.write_json(out / "mpcf.json", res)
    return res


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("step", choices=("all",))
    ap.add_argument("--out", required=True)
    ap.add_argument("--actions", required=True)
    ap.add_argument("--conds", required=True)
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args(argv)
    conds = a.conds.split(",")
    if conds[0] != "S" or len(conds) < 2 or len(set(conds)) != len(conds) or not set(conds[1:]) <= set(pb.CELLS):
        ap.error("--conds is S followed by the cells that passed S2, each once")
    pb.reserve(a.workers)
    res = all_steps(Path(a.out), json.loads(Path(a.actions).read_text()), conds, a.workers)
    print("MPC-F gate", "passed" if res["gate_passed"] else "FAILED (disclosed failed build)", "model", res["model_sha256"][:12])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
