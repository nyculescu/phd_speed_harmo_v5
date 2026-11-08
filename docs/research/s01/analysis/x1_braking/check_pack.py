"""(1) The pack did not change the runs: every round-2 stored key equal in all 2,800 measured test rows.
(2) What the braking counts measure: event seconds vs b3_step, steps at exactly -4.5 (ALKS decel), peak-bin layout."""
import pickle
from collections import Counter
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parent
T = pickle.load(open(OUT / "test_rows.pkl", "rb"))
S = pickle.load(open(OUT / "r2_rows.pkl", "rb"))
bad = Counter()
nd = 0
for k, s in S.items():
    m = T[k]
    diff = [x for x in s if s[x] != m.get(x)]
    bad.update(diff)
    nd += bool(diff)
print("(1) rows with any stored key different:", nd, "of", len(S), "keys:", dict(bad.most_common(10)))
C = ("car", "alks", "truck")
ev_ok = sum(np.isclose(sum(r[f"m_event_s_{c}"] for c in C), r["b3_step"], rtol=1e-9, atol=1e-6) for r in T.values())
print("(2a) runs with sum(m_event_s_*) == b3_step:", ev_ok, "of", len(T))
# m_ah bins: index int((a + 10) / 0.5); bin 11 = [-4.5, -4.0), bins 0-10 = a < -4.5. b45_step counts a <= -4.5.
ex45 = []
for r in T.values():
    lt45_alks = sum(r["m_ah_alks"][:11])
    le45_alks = r["alks_b45_step"] / 0.1
    lt45_all = sum(sum(r[f"m_ah_{c}"][:11]) for c in C)
    le45_all = r["b45_step"] / 0.1
    ex45.append((le45_alks - lt45_alks, le45_alks, le45_all - lt45_all, le45_all))
ex45 = np.array(ex45)
print("(2b) ALKS steps with a == -4.5 exactly (b45 <= minus ah < -4.5): total", round(ex45[:, 0].sum()), "of ALKS <= -4.5 steps", round(ex45[:, 1].sum()),
      "share", round(ex45[:, 0].sum() / max(ex45[:, 1].sum(), 1), 4))
print("     all classes: steps == -4.5:", round(ex45[:, 2].sum()), "of", round(ex45[:, 3].sum()), "share", round(ex45[:, 2].sum() / ex45[:, 3].sum(), 4))
# class split of steps at exactly -4.5: all minus alks = humans + trucks
print("     human+truck steps == -4.5:", round(ex45[:, 2].sum() - ex45[:, 0].sum()))
# peak bins per class, pooled over all rows of an arm group
def grp(name):
    a = name.split("|")[1]
    if a[0] == "w" and "u" in a: return "v3w"
    if a[0] == "t" and a[1:].isdigit(): return "tail"
    if a[0] == "s" and "u" in a: return "sw"
    if a[0] == "d" and "u" in a: return "bv3"
    return a
for cell in ("X1", "X2"):
    for g in ("nc", "v3w", "3e", "p333"):
        rows = [r for (n, s), r in T.items() if n.startswith(cell + "|") and grp(n) == g]
        for c in C:
            pk = np.sum([r[f"m_peak_{c}"] for r in rows], axis=0) / len(rows)
            print(f"(2c) {cell} {g:5s} {c:5s} mean peak-bin counts per run [-3..-3.5,..,-9..]:", np.round(pk, 1).tolist())
