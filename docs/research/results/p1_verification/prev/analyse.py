import json
import sys

import numpy as np

sys.path.insert(0, "/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/59738c75-cfe8-434e-99ee-b78b7087de37/scratchpad/p1v/prev")
from prev_check import EVAL, TUNE, PIS, fixed, sw, fa, mix, paired  # noqa: E402

D = json.load(open(sys.argv[1]))["res"]
R = json.load(open("/home/catalin/work/phd/v5b1_runs/p1/v99/result.json"))
arms = R["tune"]["arms"]
G, PI_ = R["G"], R["PI"]
L0 = ("N", "FX", "FB", "PI", "AD")


def arr(keys, i=0):
    return np.array([D[k][i] for k in keys], float)


inval = [k for k, v in D.items() if not v[1]]
tele = [k for k, v in D.items() if v[2]]
print("invalid runs among loaded:", len(inval), " teleport runs:", len(tele))

out = {}
for q in ("1600", "2000"):
    a = arms[q]
    N = a["N"]
    print(f"\n================ q {q}  (N={N}, ID={a['ID']}, IP={a['IP']})")
    # ---- re-tune on tuning seeds (fit_prevalence logic re-implemented), incl. pi 0.05 and 1
    fams = {"N": list(G), "FX": [g for g in G if g.startswith("c")], "FB": [g for g in G if g.startswith("f")],
            "PI": list(PI_), "AD": [f"ad{e}_{a['FB']}" for e in ("0p5", "1", "2")]}
    tdel = {}
    for g in set(sum(fams.values(), [])):
        tdel[g] = {c: arr([fixed(g, c, q, s) for s in TUNE]) for c in ("none", "slow", "block")}
    retune = {}
    for pi in PIS:
        retune[pi] = {}
        for arm, cand in fams.items():
            med = {g: float(np.median(mix(tdel[g]["slow"], tdel[g]["block"], tdel[g]["none"], pi))) for g in cand}
            retune[pi][arm] = min(cand, key=lambda g: (med[g], cand.index(g)))
    # pi=0 analogue of N, and the pooled-median main tuning
    pooled = {g: float(np.median(np.concatenate([tdel[g]["slow"], tdel[g]["block"]]))) for g in tdel}
    main_chk = {arm: min(c, key=lambda g: (pooled[g], c.index(g))) for arm, c in fams.items() if arm != "N"}
    main_chk["N"] = min(fams["N"], key=lambda g: (float(np.median(tdel[g]["none"])), fams["N"].index(g)))
    print("main arms re-derived from tuning runs:", main_chk, " stored:", {x: a[x] for x in L0})
    for pi in PIS:
        st = a["prev"].get(str(pi))
        print(f"retune pi={pi}: {retune[pi]}" + (f"  stored: {st}  match={st == retune[pi]}" if st else "  (not in run)"))

    # ---- evaluation arrays
    def E(g, c):
        return arr([fixed(g, c, q, s) for s in EVAL])

    def Esrv(g, c):
        return arr([fixed(g, c, q, s) for s in EVAL], 3)

    ev = {}
    for x in L0:
        ev[x] = {c: E(a[x], c) for c in ("none", "slow", "block")}
    ev["NC"] = {c: E("NC", c) for c in ("none", "slow", "block")}
    for x in ("ID", "IP"):
        ev[x] = {"none": E(N, "none")}
        for inc in ("slow", "block"):
            act = a["ID"] if x == "ID" else a["IP"][inc]
            ev[x][inc] = arr([sw(N, act, inc, q, s) for s in EVAL])
    have = {k.rsplit("_none_", 1)[0] for k in D if f"_none_q{q}_s74005" in k and "-" not in k.split("_none_")[0]}
    for pi in PIS:
        for x in L0:
            g = retune[pi][x]
            if g in have:
                ev[f"{x}_pi{pi}"] = {c: E(g, c) for c in ("none", "slow", "block")}
            else:
                print(f"  NOTE {x}_pi{pi} = {g}: no evaluation runs in the run dir -> not evaluated")
    # clean-day and incident-cell medians
    print("\nmedians (s/veh): arm  clean  slow  block")
    for x in ["NC", "ID", "IP"] + list(L0):
        print(f"  {x:4s} {np.median(ev[x]['none']):7.1f} {np.median(ev[x]['slow']):7.1f} {np.median(ev[x]['block']):7.1f}")
    # the clean-day distribution of N (bimodality)
    n0 = ev["N"]["none"]
    print("  N clean quantiles 10/25/50/75/90:", np.round(np.percentile(n0, [10, 25, 50, 75, 90]), 1))
    for x in ("PI", "FB", "FX"):
        d = ev[x]["none"] - n0
        print(f"  clean {x}-N per seed: median {np.median(d):.1f}, share>0 {np.mean(d > 0):.2f}, "
              f"q10/q90 {np.percentile(d, 10):.1f}/{np.percentile(d, 90):.1f}")
    # ---- prevalence table
    qo = {}
    for pi in PIS:
        rows = {}
        names = ["NC", "ID", "IP"] + list(L0) + [f"{x}_pi{pi}" for x in L0 if f"{x}_pi{pi}" in ev]
        for x in names:
            e = ev[x]
            ps = mix(e["slow"], e["block"], e["none"], pi)
            mm = pi * (np.median(e["slow"]) + np.median(e["block"])) / 2 + (1 - pi) * np.median(e["none"])
            rows[x] = {"per_seed_median": float(np.median(ps)), "mix_of_medians": float(mm), "mean": float(np.mean(ps)), "ps": ps}
        print(f"\n--- pi = {pi}")
        best = sorted(rows, key=lambda x: rows[x]["per_seed_median"])
        print("  ranking (median of per-seed mixture | mixture of medians):")
        for x in best:
            print(f"    {x:10s} {rows[x]['per_seed_median']:7.1f} | {rows[x]['mix_of_medians']:7.1f} | mean {rows[x]['mean']:7.1f}")
        refs = [x for x in names if x not in ("NC", "ID", "IP")]
        st = {}
        for t in ("IP", "ID"):
            for r in refs:
                p = paired(rows[r]["ps"], rows[t]["ps"])
                st[f"{t}_vs_{r}"] = p
                print(f"  {t} vs {r:9s}: rel {100*p['rel']:6.1f} %  CI [{100*p['rel_ci'][0]:6.1f}, {100*p['rel_ci'][1]:6.1f}]"
                      f"  diff {p['diff']:6.1f} [{p['diff_ci'][0]:6.1f}, {p['diff_ci'][1]:6.1f}] s")
        # cross-check vs result.json
        stored = R["eval"]["per_q"][q]["prevalence"].get(str(pi))
        if stored:
            mx = 0.0
            for t in ("IP", "ID"):
                for r in L0:
                    s0 = stored[f"{t}_vs"][r]["all_seeds"]
                    mine = st[f"{t}_vs_{r}_pi{pi}"]
                    mx = max(mx, abs(s0["rel"] - mine["rel"]), abs(s0["diff_ci"][0] - mine["diff_ci"][0]),
                             abs(s0["rel_ci"][1] - mine["rel_ci"][1]))
            print(f"  max |result.json - mine| over rel / diff_ci lo / rel_ci hi: {mx:.2e}")
        qo[str(pi)] = {x: {k: v for k, v in rows[x].items() if k != "ps"} for x in rows}
        qo[str(pi)]["stats"] = st
    out[q] = qo
json.dump(out, open(sys.argv[2], "w"), indent=1)
