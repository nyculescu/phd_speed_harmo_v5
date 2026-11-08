"""Run counts and cost per stage for the staged Plan B draft (planning; rates from V475, V461, V425-V426)."""
CELLS = 3
def search(g):  # one CMA-ES search: 24 x 16 per generation + a checkpoint every 20 generations (and at the cap): 10 best + CMA mean on 40 seeds
    checks = len(set(list(range(20, g + 1, 20)) + [g]))
    return g * 384 + checks * 11 * 40
st = {}
st["1 smoke/T3/identity"] = 100
st["2 T0/T1 (both rungs)"] = 3 * 40 + 40 + 20 + 3 * 40 + 40
st["3a grid re-pick"] = CELLS * 69 * 20
st["3b pilot n=30"] = CELLS * (5 + 1 + 15 + 8) * 30
for g in (40, 100, 150):
    st[f"4 3E C+D, G={g}"] = CELLS * (2 * search(g) + 40)
    st[f"4 3E C only, G={g}"] = CELLS * (search(g) + 40)
st["5 confirm n=80"] = CELLS * (5 + 1 + 15 + 8 + 2) * 80 + (5 + 1 + 15 + 10 * CELLS) * 80
def rate(n):
    a_lo, a_hi = n / 3050 / 0.88, n / 2450 / 0.88
    return f"{a_lo:.1f}-{a_hi:.1f}", f"{n*0.10/1000:.2f}-{n*0.13/1000:.2f}", f"{n/6400:.1f}", f"{n/1330:.1f}"
print("| stage | runs | rental A wall h | $ | rental B h | laptop day h |")
for k, n in st.items():
    print(f"| {k} | {n:,} |", " | ".join(rate(n)), "|")
pre = st["1 smoke/T3/identity"] + st["2 T0/T1 (both rungs)"]
p3 = pre + st["3a grid re-pick"] + st["3b pilot n=30"]
for g in (40, 100, 150):
    for v in ("C+D", "C only"):
        tot = p3 + st[f"4 3E {v}, G={g}"] + st["5 confirm n=80"]
        print("total", g, v, f"{tot:,}", rate(tot))
print("kill at 2:", pre, rate(pre)); print("kill at 3:", p3, rate(p3))
print("per search G=40/100/150:", search(40), search(100), search(150))
