"""Tasks (2), (5) and side checks: S1 grid and seeds, run health per arm and level, configs against round 2's job files,
pairing of the slowdown draw across arms, the draw against its seed, and smoke re-runs against the main rows. Read only."""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

D = Path("/home/catalin/work/phd/v5b1_runs")
M = D / "measure_s01_remote"
OUT = Path(__file__).resolve().parent
S1_SEEDS = set(range(7_440_900, 7_440_920))


def rows(f):
    return [json.loads(x) for x in open(f)]


def strip(c):
    return {k: v for k, v in c.items() if k != "measure"}


def draw(seed):
    """perturb.Perturb's random kind, reimplemented: no slowdown (a third) or one tapered slowdown, from the seed alone."""
    r = np.random.default_rng(seed + 910_000)
    if r.random() >= 1.0 / 3.0:
        return {"edge": str(r.choice(("3", "4", "5"))), "limit_kmh": float(r.uniform(25.0, 60.0)), "dur": float(r.uniform(60.0, 180.0)),
                "t0": float(r.uniform(400.0, 1200.0))}
    return None


def health(R):
    g = defaultdict(list)
    for r in R:
        g[(r["name"], r["q"])].append(r)
    out = {}
    for (n, q), rs in sorted(g.items()):
        fp = np.array([r["finished_pct"] for r in rs])
        out[f"{n}|{q:.0f}"] = {"n": len(rs), "collisions_sum": int(sum(r["collisions"] for r in rs)), "collisions_max": int(max(r["collisions"] for r in rs)),
                               "teleports_sum": float(sum(r["teleports"] for r in rs)), "teleports_max": float(max(r["teleports"] for r in rs)),
                               "contact_steps_sum": int(sum(r["contact_steps"] for r in rs)),
                               "finished_pct_min": float(fp.min()), "finished_pct_med": float(np.median(fp)), "finished_pct_max": float(fp.max()),
                               "passed_med": float(np.median([r["passed"] for r in rs])), "all_delay_med": float(np.median([r["all_delay"] for r in rs])),
                               "steps_set": sorted({r["steps"] for r in rs})}
    return out


def pairing(R):
    """Within a cell, level and seed, every arm must see the same slowdown on/off log."""
    g = defaultdict(dict)
    for r in R:
        g[(r["name"].split("|")[0], r["q"], r["seed"])][r["name"]] = json.dumps(r.get("pert_log"))
    bad = {f"{k}": len(set(v.values())) for k, v in g.items() if len(set(v.values())) > 1}
    return {"groups": len(g), "arms_per_group": sorted({len(v) for v in g.values()}), "groups_with_differing_pert_log": bad}


def draw_vs_log(R):
    """For cell B (random draw), the logged on/off seconds against the draw reconstructed from the seed."""
    res, bad, none = Counter(), [], 0
    seen = {}
    for r in R:
        if not r["name"].startswith("B|"):
            continue
        s = r["seed"]
        if s in seen:
            continue
        d = draw(s)
        log = r.get("pert_log") or []
        seen[s] = (d, log)
        if d is None:
            ok = log == []
            none += 1
        else:
            ok = len(log) == 2 and log[0][1] is True and log[1][1] is False and abs(log[0][0] - d["t0"]) <= 1.0 and abs(log[1][0] - (d["t0"] + d["dur"])) <= 1.0
        res[ok] += 1
        if not ok:
            bad.append({"seed": s, "draw": d, "log": log})
    return {"seeds": len(seen), "match": res[True], "mismatch": res[False], "no_slowdown_seeds": none, "bad": bad[:10],
            "draws": {str(s): v[0] for s, v in sorted(seen.items())}}


def main():
    rep = {}
    T, B, S1 = rows(M / "rows_test.jsonl"), rows(M / "rows_band.jsonl"), rows(M / "rows_s1.jsonl")

    # (2) S1 grid
    keys = Counter((r["name"], r["q"], r["seed"]) for r in S1)
    names = sorted({r["name"] for r in S1})
    levels = sorted({r["q"] for r in S1})
    seeds = {r["seed"] for r in S1}
    full = {(n, q, s) for n in names for q in levels for s in S1_SEEDS}
    other_seeds = {r["seed"] for r in T} | {r["seed"] for r in B}
    rep["s1_grid"] = {"rows": len(S1), "names": names, "n_names": len(names), "levels": levels, "seeds_min": min(seeds), "seeds_max": max(seeds),
                      "seeds_equal_7440900_919": seeds == S1_SEEDS, "duplicate_keys": sum(1 for v in keys.values() if v > 1),
                      "missing_grid_cells": len(full - set(keys)), "extra_keys": len(set(keys) - full),
                      "s1_seeds_in_test_or_band": sorted(seeds & other_seeds),
                      "test_seeds": [min(r["seed"] for r in T), max(r["seed"] for r in T), len({r["seed"] for r in T})],
                      "band_seeds": [min(r["seed"] for r in B), max(r["seed"] for r in B), len({r["seed"] for r in B})]}
    print("S1 grid:", {k: v for k, v in rep["s1_grid"].items() if k != "names"})
    print("S1 names:", names)

    # health per arm and level (S1 in full; test and band summarised)
    rep["health_s1"] = health(S1)
    rep["health_test"] = health(T)
    rep["health_band"] = health(B)
    print("\nS1 health per arm and level (collisions sum/max, teleports sum/max, contact_steps sum, finished_pct min/med/max, passed med, all_delay med):")
    for k, h in rep["health_s1"].items():
        print(f"  {k:<22} n={h['n']} coll {h['collisions_sum']}/{h['collisions_max']} tele {h['teleports_sum']:.0f}/{h['teleports_max']:.0f} "
              f"contact {h['contact_steps_sum']} fin {h['finished_pct_min']:.1f}/{h['finished_pct_med']:.1f}/{h['finished_pct_max']:.1f} "
              f"passed {h['passed_med']:.0f} delay {h['all_delay_med']:.0f} steps {h['steps_set']}")
    for ph in ("test", "band"):
        H = rep[f"health_{ph}"]
        print(f"\n{ph}: arm-levels {len(H)}; collisions total {sum(h['collisions_sum'] for h in H.values())}, "
              f"teleports total {sum(h['teleports_sum'] for h in H.values()):.0f}, contact_steps total {sum(h['contact_steps_sum'] for h in H.values())}, "
              f"finished_pct min {min(h['finished_pct_min'] for h in H.values()):.2f}, steps values {sorted({s for h in H.values() for s in h['steps_set']})}")
        low = {k: round(h["finished_pct_min"], 1) for k, h in H.items() if h["finished_pct_min"] < 95.0}
        print("  arm-levels with a run below 95 % finished:", len(low), dict(list(low.items())[:12]))
        coll = {k: h["collisions_sum"] for k, h in H.items() if h["collisions_sum"]}
        print("  arm-levels with collisions:", coll)

    # (5) configs against round 2's job files
    jt, jb, js = (json.load(open(M / f"job_{p}.json")) for p in ("test", "band", "s1"))
    rt, rb = json.load(open(D / "round2/test/job_6c49e7e.json")), json.load(open(D / "round2/band/job_6c49e7e.json"))
    cfg = {}
    for lab, new, old in (("test", jt, rt), ("band", jb, rb), ("s1_vs_round2_band", js, rb)):
        names_n, names_o = set(new["arms"]), set(old["arms"])
        diff = [n for n in names_n & names_o if strip(new["arms"][n]) != old["arms"][n]]
        meas = Counter(new["arms"][n].get("measure") for n in names_n)
        cfg[lab] = {"arms_new": len(names_n), "arms_old": len(names_o), "only_new": sorted(names_n - names_o), "only_old_count": len(names_o - names_n),
                    "cfg_differs_apart_from_measure": diff, "measure_values": dict(meas),
                    "levels_equal": new["levels"] == old["levels"] if lab != "s1_vs_round2_band" else None,
                    "seeds_equal": new["seeds"] == old["seeds"] if lab != "s1_vs_round2_band" else None,
                    "old_extra_keys": sorted(set(old) - {"arms", "levels", "seeds"})}
    # rows carry their job's cfg
    for lab, R, J in (("test", T, jt), ("band", B, jb), ("s1", S1, js)):
        cfg[lab + "_rows_cfg_eq_job"] = sum(r["cfg"] == J["arms"][r["name"]] for r in R), len(R)
    rep["configs"] = cfg
    print("\nconfigs:", json.dumps(cfg, default=str)[:3000])

    # pairing and the draw
    rep["pairing"] = {"test": pairing(T), "band": pairing(B), "s1": pairing(S1)}
    print("\npairing:", {k: {kk: (vv if kk != "groups_with_differing_pert_log" else len(vv)) for kk, vv in v.items()} for k, v in rep["pairing"].items()})
    rep["draw_band"] = draw_vs_log(B)
    rep["draw_s1"] = draw_vs_log(S1)
    for k in ("draw_band", "draw_s1"):
        x = rep[k]
        print(k, {kk: vv for kk, vv in x.items() if kk not in ("draws",)})
    for k in ("draw_s1",):
        ds = rep[k]["draws"]
        e = Counter(d["edge"] if d else "none" for d in ds.values())
        print("  S1 draws by edge:", dict(e))
        print("  S1 draws:", {s: (None if d is None else (d["edge"], round(d["limit_kmh"]), round(d["dur"]), round(d["t0"]))) for s, d in ds.items()})
    eb = Counter(d["edge"] if d else "none" for d in rep["draw_band"]["draws"].values())
    print("  band draws by edge:", dict(eb))
    print("  band draws:", {s: (None if d is None else (d["edge"], round(d["limit_kmh"]), round(d["dur"]), round(d["t0"]))) for s, d in rep["draw_band"]["draws"].items()})

    # smoke re-runs (same code, run again) against the main rows: determinism on the host and across machines
    idx = {(r["name"], r["q"], r["seed"]): r for r in T + B + S1}
    sm = {}
    for f in (M / "smoke/smoke_rows.jsonl", M / "smoke1/smoke1_rows.jsonl", D / "s01_smoke1/smoke1_rows.jsonl", D / "s01_smoke2/smoke1_rows.jsonl",
              D / "round2_measure_smoke_2354/smoke_rows.jsonl"):
        if not f.exists():
            continue
        res = []
        for r in rows(f):
            k = (r["name"], r["q"], r["seed"])
            m = idx.get(k)
            if m is None:
                res.append({"key": list(k), "found": False})
                continue
            fields = (set(r) | set(m)) - {"cfg", "m_st_file"}
            bad = sorted(x for x in fields if r.get(x) != m.get(x))
            res.append({"key": list(k), "found": True, "fields": len(fields), "differ": bad[:10], "n_differ": len(bad),
                        "cfg_eq_apart_from_measure": strip(r["cfg"]) == strip(m["cfg"])})
        sm[str(f.relative_to(D))] = res
    rep["smoke_vs_main"] = sm
    print("\nsmoke rows vs main rows (all keys incl. m_*, except cfg and m_st_file):")
    for f, res in sm.items():
        print(" ", f, [(r["key"][0], r["key"][1], r["n_differ"] if r["found"] else "not found", r.get("differ", [])[:4]) for r in res])

    (OUT / "checks.json").write_text(json.dumps(rep, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
