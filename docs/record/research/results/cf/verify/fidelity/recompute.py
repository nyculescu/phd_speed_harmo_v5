import pickle, json, sys
import numpy as np
S = sys.argv[1]
R = pickle.load(open(f"{S}/screen.pkl", "rb"))
scr = json.load(open("/home/catalin/work/phd/v5b1_runs/cf_remote/cf_screen/screen.json"))
seeds = list(range(7489160, 7489640)); n = len(seeds); pos = {s: i for i, s in enumerate(seeds)}
V3W = ("w0u250", "w1u500", "w2u250", "w3u500", "w4u500")
arms = sorted({r["arm"] for r in R}); rules = [a for a in arms if a not in V3W]
def col(key, f=None):
    out = {a: np.full(n, np.nan) for a in arms}
    for r in R: out[r["arm"]][pos[r["seed"]]] = f(r) if f else r[key]
    assert not any(np.isnan(v).any() for v in out.values())
    return out
DEL, TTC, B45 = col("all_delay"), col(None, lambda r: r["E30"] + r["out_E30"]), col("b45_step")
STUCK = col("m_stuck_n"); Q = {k: col(None, lambda r, k=k: r["q"][k]) for k in ("ramp1_queue", "ramp2_queue", "backlog")}
idx = np.random.default_rng(20261108).integers(0, n, (20000, n))
PCT = (1.25, 98.75)
def eff(X, opp):
    O = X[opp]; m = np.median(O)
    D = [-(X[w] - O) / m * 100 for w in V3W]
    pt = np.mean([np.median(d) for d in D]); b = np.mean([np.median(d[idx], axis=1) for d in D], axis=0)
    lo, hi = np.percentile(b, PCT); return pt, lo, hi, b
worst = 0.0
def cmp(tag, mine, theirs):
    global worst
    e = max(abs(a - b) for a, b in zip(mine, theirs)); worst = max(worst, e)
    if e > 1e-9: print("DIFF", tag, mine, theirs)
Dm, Em = {}, {}
for a in rules:
    Dm[a] = eff(DEL, a); Em[a] = eff(TTC, a); Bk = eff(B45, a)
    for k, x in (("D", Dm[a]), ("E", Em[a]), ("brake", Bk)):
        t = scr["readings"][a][k]; cmp(f"{k} {a}", x[:3], (t["pt"], t["lo"], t["hi"]))
print("D, E, brake of 26 arms: largest abs difference from screen.json", worst)
comp = [a for a in rules if Dm[a][1] <= 1.0 or a == "p333"]
print("competitors equal:", sorted(comp) == sorted(scr["competitors"]), len(comp), "| trade points", len(rules) - len(comp))
F = [a for a in rules if Dm[a][1] < 0]; Sl = [a for a in rules if Dm[a][2] > 0]
pairs = {frozenset((q, r)) for q in F for r in Sl if q != r}
print("may-be-faster arms", len(F), "may-be-slower arms", len(Sl), "unordered pairs", len(pairs), "| screen.json chords", len(scr["chords"]), "same set:", pairs == {frozenset((c["q"], c["r"])) for c in scr["chords"]})
print("point-faster arms (D pt < 0):", sorted(a for a in rules if Dm[a][0] < 0))
# chords, my own implementation of §1
def chord(q, r):
    P = [DEL[w] for w in V3W]
    mq = np.mean([np.median(p - DEL[q]) for p in P]); mr = np.mean([np.median(DEL[r] - p) for p in P])
    mqb = np.mean([np.median((p - DEL[q])[idx], axis=1) for p in P], axis=0); mrb = np.mean([np.median((DEL[r] - p)[idx], axis=1) for p in P], axis=0)
    w0 = 0.5 if mq + mr == 0 else min(max(mq / (mq + mr), 0), 1)
    s = mqb + mrb; wb = np.clip(np.where(s == 0, 0.5, mqb / np.where(s == 0, 1, s)), 0, 1)
    cq, cr = np.median(TTC[q]), np.median(TTC[r])
    M0 = (1 - w0) * TTC[q] + w0 * TTC[r]; c0 = (1 - w0) * cq + w0 * cr
    pt = np.mean([np.median(-(TTC[w] - M0) / c0 * 100) for w in V3W])
    Mb = (1 - wb)[:, None] * TTC[q][idx] + wb[:, None] * TTC[r][idx]; cb = ((1 - wb) * cq + wb * cr)[:, None]
    b = np.mean([np.median(-(TTC[w][idx] - Mb) / cb * 100, axis=1) for w in V3W], axis=0)
    lo, hi = np.percentile(b, PCT); return w0, pt, lo, hi
worst = 0.0; interior = 0; los = []
for c in scr["chords"]:
    w0, pt, lo, hi = chord(c["q"], c["r"]); cmp(f"chord {c['q']}~{c['r']}", (w0, pt, lo, hi), (c["w"], c["pt"], c["lo"], c["hi"]))
    interior += 0 < w0 < 1; los.append((lo, hi, c["q"], c["r"], w0))
print("220 chords recomputed: largest abs difference", worst, "| interior (0<w<1):", interior, "| clamped:", len(los) - interior)
print("chords: min lower bound", min(los)[:4], "| min upper bound", min(x[1] for x in los), "| all lo>0:", all(x[0] > 0 for x in los), "| any hi<5:", any(x[1] < 5 for x in los))
print("interior chords: min lower bound", min(x for x in los if 0 < x[4] < 1)[:4])
print("E lower bound > 0 for all 26 arms:", all(Em[a][1] > 0 for a in rules), "| min", min((Em[a][1], a) for a in rules), "| any E hi < 5:", any(Em[a][2] < 5 for a in rules))
# P0
nc = DEL["nc"]; p0 = {}
for a in rules:
    if a == "nc": continue
    d = -(DEL[a] - nc) / np.median(nc) * 100; p0[a] = (np.median(d), np.percentile(np.median(d[idx], axis=1), 2.5))
    t = scr["p0"]["arms"][a]; assert abs(p0[a][0] - t["pt"]) < 1e-9 and abs(p0[a][1] - t["lo95"]) < 1e-9
print("P0 recomputed equal; rules with pt>=10 and lo95>0:", sum(v[0] >= 10 and v[1] > 0 for v in p0.values()), "of", len(p0), "| smallest", min((v[1], v[0], a) for a, v in p0.items()))
# drain
for a in ["v3w"] + rules:
    ex = {k: float(np.mean((np.mean([Q[k][w] for w in V3W], axis=0) if a == "v3w" else Q[k][a]) - Q[k]["p333"])) for k in Q}
    names = V3W if a == "v3w" else (a,)
    share = float(np.mean([np.mean(STUCK[w] > 0) for w in names])); fail = any(v > 2.0 for v in ex.values()) or share > 0.01
    t = scr["drain"][a]; assert fail == t["fail"] and all(abs(ex[k] - t["queue_excess"][k]) < 1e-9 for k in ex), a
print("drain recomputed equal for 27 entries; failing:", sorted(a for a in rules if scr["drain"][a]["fail"]), "| v3w fail:", scr["drain"]["v3w"]["fail"])
# v3w's own stuck and queue numbers
print("v3w stuck rows", {w: int((STUCK[w] > 0).sum()) for w in V3W})
print("delay vs p333", Dm["p333"][:3], "95% hi", np.percentile(Dm["p333"][3], 97.5))
