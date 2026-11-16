"""Round 2 checks before the run (round_2.md, checks 1-5). Each prints PASS or FAIL lines and exits non-zero on any failure.
usage: check2.py identity|rows|replay|smoke|picks OUT RUN_COMMIT [WORKERS]
  identity: 3E rows from final_runs.jsonl (8 slim keys) and a full row against the swap route; tail and sw identities; v3w's stored rows
  rows:     checks1.py rows inside r2/eval's and every candidate's frozen snapshot (round 1's T3 rows); run again for T3 on this machine
  replay:   decide2 reproduces round 1's T1 and T2 for v3w, and gives res and attr harmed against v3w on round 1's validation rows
  smoke:    smoke2.py inside each snapshot that serves an arm kind (sw, 3E, tail on r2/eval; ahead and 1B on their own)
  picks:    each 3E-X pick, re-run through the plant_sweep key, reproduces its stored final rows on 3 tuning seeds (8 slim keys)"""
import gzip
import inspect
import json
import multiprocessing as mp
import os
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from common2e import (GIT, R1_SUMS, E3T, OPPONENTS, PY, Q, R1, RULE, RUNS, SEEDS_SMOKE, TRAINED, AHEAD_INPUTS, cand_cfg, freeze, policy, pt_cfg, rule_cfg,
                      sw_cfg, tail_cfg, zone_cfg)
import decide2 as dc

HERE = Path(__file__).resolve().parent
SKIP = {"name", "cfg"}
R1OUT = RUNS / "round1_remote/out"
E3DIR = RUNS / "round2_remote/cma3e"
E3KEYS = ("all_delay", "ttc_net", "collisions", "passed", "teleports", "alks_b45_step", "alks_full_events", "finished_pct")


def run1(a):
    from v5b2.freeway import evaluate as ps
    return ps.run_one(a)


def run_swap(a):
    """3E's old worker route: the own_state key with the per-zone class swapped in (cma2.py at d2d0d04, run_cfg)."""
    from v5b2.freeway import environments as be, evaluate as ps
    be.OwnState = be.ZoneOwnState
    return ps.run_one(a)


def diff(new: dict, old: dict, keys=None) -> list:
    new, old = json.loads(json.dumps(new)), json.loads(json.dumps(old))
    return [k for k in (keys or old) if k not in SKIP and new.get(k) != old.get(k)]


def stored(f: Path, name: str, seed: int, q: float = Q) -> dict:
    op = gzip.open if str(f).endswith(".gz") else open
    with op(f, "rt") as h:
        for line in h:
            r = json.loads(line)
            if r["name"] == name and r["seed"] == seed and r["q"] == q:
                return r
    raise KeyError((name, seed, q))


def report(results: list) -> int:
    bad = [r for r in results if not r[1]]
    for name, ok, info in results:
        print(f"{'PASS' if ok else 'FAIL'} {name} {info}", flush=True)
    return 1 if bad else 0


def identity(out: Path, w: int) -> int:
    out.mkdir(parents=True, exist_ok=True)
    rd = str(out / "rd")
    res = []
    import hashlib
    want = dict(reversed(x.split()) for x in R1_SUMS.read_text().splitlines())
    got = {n: hashlib.sha256((R1 / n).read_bytes()).hexdigest() for n in want}
    res.append(("baseline-v4 store matches its SHA256SUMS", got == want and len(want) == 45, f"{len(want)} files"))
    old_src = subprocess.run(["git", "-C", GIT, "show", "d2d0d04:analysis/round2/cma2.py"], capture_output=True,
                             text=True, check=True).stdout
    from v5b2.freeway import environments as be
    body = lambda s: s[s.index("    def __init__(self, zones: list):"):].split("\n\n\n")[0]
    new_body = body(inspect.getsource(be.ZoneOwnState)).replace("zone_of_3e(", "zone_of(").replace("(100.0 / 3.6)", "LIMIT")
    res.append(("3E class moved unchanged", body(old_src[old_src.index("class ZoneOwnState"):]).strip() == new_body.strip(), "method bodies"))
    import cma2
    jobs = [(n, cma2.cfg_for(c, "T"), q, s, rd) for n, c in (("g032i20", cma2.zone_ctrl(E3T)), ("ref", OPPONENTS["ctrl"][RULE]))
            for q in (4500.0, 6000.0) for s in (7_440_700, 7_440_701, 7_440_702)]
    full = ("X2|3e", zone_cfg(E3T, "X2"), Q, 7_440_200, rd)
    swap = ("X2|3e_swap", rule_cfg({"own_state": {"zones": E3T}}, "X2"), Q, 7_440_200, rd)
    v3 = [(f"{c}|w0", pt_cfg(R1 / "C0_u250.pt", c), Q, 7_440_500, rd) for c in ("X1", "X2")]
    tl = [("X2|tail1", {**tail_cfg(0, "X2"), "ctrl": {**tail_cfg(0, "X2")["ctrl"], "pts": [str(R1 / "C0_u500.pt")]}}, Q, 7_440_200, rd),
          ("X2|tail2", {**tail_cfg(0, "X2"), "ctrl": {**tail_cfg(0, "X2")["ctrl"], "pts": [str(R1 / "C0_u500.pt")] * 2}}, Q, 7_440_200, rd),
          ("X2|greedy", pt_cfg(R1 / "C0_u500.pt", "X2"), Q, 7_440_200, rd)]
    sw = [("X2|sw_lo", sw_cfg(0, 250, "X2", x_from=-1e9), Q, 7_440_500, rd), ("X2|sw_hi", sw_cfg(0, 250, "X2", x_from=1e9), Q, 7_440_500, rd)]
    with ProcessPoolExecutor(w, mp_context=mp.get_context("spawn"), max_tasks_per_child=1) as ex:
        new = list(ex.map(run1, [*jobs, full, *v3, *tl, *sw]))
        old_full = ex.submit(run_swap, swap).result()
    k = len(jobs)
    st = {}
    for line in open(E3DIR / "final_runs.jsonl"):
        r = json.loads(line)
        st[(r["name"], r["q"], r["seed"])] = r
    for j, r in zip(jobs, new[:k]):
        s = cma2.slim(r)
        d = [x for x in E3KEYS if s[x] != st[(j[0], j[2], j[3])][x]]
        res.append((f"3E stored row {j[0]} q {j[2]:.0f} seed {j[3]}", not d, f"8 keys, differing {d}"))
    res.append(("3E full row, key against swap route", not diff(new[k], old_full), f"differing {diff(new[k], old_full)[:8]}"))
    test = R1OUT / "test/test.jsonl"
    for r in new[k + 1:k + 3]:
        d = diff(r, stored(test, r["name"], 7_440_500))
        res.append((f"v3w stored row {r['name']} (C0 u250)", not d, f"differing {d[:8]}"))
    t1, t2, g = new[k + 3:k + 6]
    res.append(("TailMean([u500]) = Greedy(u500)", not diff(t1, g), f"differing {diff(t1, g)[:8]}"))
    res.append(("TailMean([u500, u500]) = Greedy(u500)", not diff(t2, g), f"differing {diff(t2, g)[:8]}"))
    lo, hi = new[k + 6:k + 8]
    d1_ = diff(lo, stored(test, "X2|w0", 7_440_500))
    d2_ = diff(hi, stored(test, f"X2|{RULE}", 7_440_500))
    res.append(("ZoneSwitch x_from -1e9 = v3w's stored row", not d1_, f"differing {d1_[:8]}"))
    res.append(("ZoneSwitch x_from +1e9 = os1_15_10's stored row", not d2_, f"differing {d2_[:8]}"))
    return report(res)


def rows(out: Path, run_commit: str) -> int:
    res = []
    for snap in ("eval", *[v[1] for v in TRAINED.values()]):
        code = freeze(snap, run_commit)
        env = {**os.environ, "PYTHONPATH": str(code), "OMP_NUM_THREADS": "1"}
        env.pop("SUMO_HOME", None)
        o = out / f"rows_{code.name}"
        p = subprocess.run([PY, "analysis/round1/checks1.py", "rows", str(o)], cwd=str(code), env=env, capture_output=True, text=True)
        res.append((f"checks1 rows at {code.name}", p.returncode == 0 and "ALL PASS" in p.stdout and sum(x.startswith("PASS ") and "against the stored row" in x for x in p.stdout.splitlines()) == 4, p.stdout.strip()[-400:]))
    return report(res)


def replay() -> int:
    from common1 import load
    res = []
    T = load(R1OUT / "test/test.jsonl")
    st = json.load(open(R1OUT / "test/test_result.json"))
    pct = dc.bonferroni(2)
    w, d = [f"w{i}" for i in range(5)], [f"d{i}" for i in range(5)]
    for c in ("X1", "X2"):
        r = dc.t1(T, c, w, d, pct)
        s = st["finalists"]["v3w"][c]["T1"]
        res.append((f"T1 replay {c}", r["a"] == s["better"] and list(r["delay"]) == s["delay_vs_incumbent"] and list(r["ttc"]) == s["ttc_vs_incumbent"],
                    f"delay {r['delay']}, path a {r['a']}"))
        t2 = dc.d1.tuned(T, c, OPPONENTS, w, pct)
        s2 = st["finalists"]["v3w"][c]["T2"]
        res.append((f"T2 replay {c}", t2["tuned"] == s2["tuned"] and t2["counts"] == s2["counts"], f"tuned {t2['tuned']} counts {t2['counts']}"))
    V = load(R1OUT / "val/validation.jsonl")
    v = json.load(open(R1OUT / "val/validation.json"))
    nm = lambda k, p: [f"{p}{i}u{v['chosen'][k][str(i)]}" for i in range(5)]
    for k, p in (("res", "r"), ("attr", "a")):
        harmed = [c for c in ("X1", "X2") if dc.paths(dc.arm(V, c, nm(k, p)), dc.arm(V, c, nm("v3w", "w")), dc.P95)["harm"]]
        res.append((f"harm replay {k} against v3w", harmed == ["X1", "X2"], f"harmed in {harmed}"))
    return report(res)


def smoke(out: Path, run_commit: str, w: int) -> int:
    out.mkdir(parents=True, exist_ok=True)
    q = Q
    jobs = {"eval": [{"kind": "sw", "name": "X2|s0u250", "cfg": sw_cfg(0, 250, "X2"), "q": q, "seed": SEEDS_SMOKE,
                      "extra": {"own_state": dict(OPPONENTS["ctrl"][RULE]["own_state"]), "pt": str(R1 / "C0_u250.pt")}},
                     {"kind": "3e", "name": "X2|3e", "cfg": zone_cfg(E3T, "X2"), "q": q, "seed": SEEDS_SMOKE, "extra": {"zones": E3T}},
                     {"kind": "tail", "name": "X2|t0", "cfg": tail_cfg(0, "X2"), "q": q, "seed": SEEDS_SMOKE,
                      "extra": {"u500": str(R1 / "C0_u500.pt"), "obs_out": str(out / "tail_obs.npy")}}],
            TRAINED["ahead"][1]: [{"kind": "ahead", "name": "X2|h0u500", "cfg": cand_cfg("ahead", 0, 500, "X2"), "q": q, "seed": SEEDS_SMOKE,
                                   "extra": {"cols": list(AHEAD_INPUTS)}}],
            TRAINED["1b"][1]: [{"kind": "1b", "name": "X2|g0u500", "cfg": cand_cfg("1b", 0, 500, "X2"), "q": q, "seed": SEEDS_SMOKE}],
            **{TRAINED[k][1]: [{"kind": k, "name": f"X2|{TRAINED[k][0]}0u500", "cfg": cand_cfg(k, 0, 500, "X2"), "q": q, "seed": SEEDS_SMOKE}]
               for k in ("2b", "1d", "rep")}}
    res, summ = [], {}
    for snap, runs in jobs.items():
        code = freeze(snap, run_commit)
        jf, of = out / f"smoke_{code.name}.json", out / f"smoke_{code.name}_out.json"
        jf.write_text(json.dumps({"runs": runs, "rd": str(out / "rd")}))
        of.unlink(missing_ok=True)
        env = {**os.environ, "PYTHONPATH": str(code), "OMP_NUM_THREADS": "1"}
        env.pop("SUMO_HOME", None)
        p = subprocess.run([PY, str(HERE / "smoke2.py"), str(jf), str(of), str(w)], cwd=str(code), env=env, capture_output=True, text=True)
        if p.returncode not in (0, 2) or not of.exists():
            res.append((f"smoke at {code.name}", False, p.stderr[-400:]))
            continue
        summ |= json.load(open(of))
    for n, s in summ.items():
        res.append((f"traced = untraced {n}", s["traced_equals_untraced"], f"differing {s['differing']}"))
    t = lambda n: summ.get(n, {}).get("trace", {})
    sw = t("X2|s0u250")
    res.append(("sw: both sides served, each by its own controller", all(sw.get("side", {}).get(x, 0) > 0 for x in ("up", "down"))
                and all(sw.get(f"from_own_{x}", {}).get("0", 0) == 0 for x in ("up", "down")), sw))
    e3 = t("X2|3e")
    res.append(("3E: every zone with decisions gives its own level or free value", e3.get("own_value", {}).get("0", 0) == 0 and len(e3.get("zone", {})) >= 3, e3))
    tl = t("X2|t0")
    res.append(("tail: share of decisions differing from Greedy(u500) reported", "differs_from_u500" in tl, tl.get("differs_from_u500")))
    ah = t("X2|h0u500")
    res.append(("ahead: 18 inputs, both look-ahead inputs vary", ah.get("n_inputs") == 18 and all(x > 0 for x in ah.get("ahead_sd", [0])), ah))
    b = t("X2|g0u500")
    res.append(("1B: the gate hold drops decisions", b.get("masked", {}).get("n", 0) > 0,
                f"masked {b.get('masked')}, decisions {b.get('decisions')}"))
    return report(res)


def tailobs(out: Path) -> int:
    """TailMean against the explicit mean of the six members' softmax, each with its own input statistics, on up to 1,000 recorded
    observations of the smoke run; and TailMean([u500, u500]) against Greedy(u500)."""
    import numpy as np
    import torch
    from v5b2.freeway.train_per_cav import Greedy, TailMean
    from common2e import TAIL_CKS
    X = np.load(out / "tail_obs.npy")
    ids = [f"v{i}" for i in range(len(X))]
    o = (ids, X, None, np.ones(len(X), bool))
    paths = [str(R1 / f"C0_u{c}.pt") for c in TAIL_CKS]
    with torch.no_grad():
        p = np.mean([torch.softmax(Greedy(f).net.logits(torch.from_numpy(X)), 1).numpy() for f in paths], axis=0)
    t = TailMean(paths)(o)
    g, t2 = Greedy(paths[-1])(o), TailMean([paths[-1]] * 2)(o)
    res = [("TailMean = argmax of the explicit mean softmax", [t[v] for v in ids] == p.argmax(1).tolist(), f"{len(X)} observations"),
           ("TailMean([u500, u500]) = Greedy(u500)", t2 == g, f"{len(X)} observations")]
    return report(res)


def picks(out: Path, w: int) -> int:
    import cma2
    from common2e import OUT
    res, jobs, want = [], [], {}
    for cell in ("X1", "X2"):
        d = OUT / f"cma3e_{cell.lower()}"
        fin = json.load(open(d / "final.json"))
        if fin["pick"] is None:
            res.append((f"3E-{cell} pick", True, "no configuration within the cap: nothing to check"))
            continue
        st = {(r["name"], r["seed"]): r for r in map(json.loads, open(d / "final_runs.jsonl"))}
        for s in (7_440_740, 7_440_741, 7_440_742):
            n = fin["pick"]["name"]
            jobs.append((f"{cell}|{n}", cma2.cfg_for(cma2.zone_ctrl(fin["pick"]["params"]), cell), Q, s, str(out / "rd")))
            want[(f"{cell}|{n}", s)] = st[(n, s)]
    with ProcessPoolExecutor(w, mp_context=mp.get_context("spawn"), max_tasks_per_child=1) as ex:
        new = list(ex.map(run1, jobs))
    for j, r in zip(jobs, new):
        s = cma2.slim(r)
        d = [x for x in E3KEYS if s[x] != want[(j[0], j[3])][x]]
        res.append((f"3E pick {j[0]} seed {j[3]}", not d, f"8 keys, differing {d}"))
    return report(res)


if __name__ == "__main__":
    mode, out, rc = sys.argv[1], Path(sys.argv[2]), sys.argv[3] if len(sys.argv) > 3 else None
    w = int(sys.argv[4]) if len(sys.argv) > 4 else 8
    sys.exit({"identity": lambda: identity(out, w), "rows": lambda: rows(out, rc), "replay": replay, "smoke": lambda: smoke(out, rc, w), "picks": lambda: picks(out, w), "tailobs": lambda: tailobs(out)}[mode]())
