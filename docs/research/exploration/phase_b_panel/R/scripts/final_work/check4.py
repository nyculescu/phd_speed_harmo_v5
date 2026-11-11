# EXPLORATORY: the same pass chance at n = 160, 240, 320 (resampled from 120 stored seeds), k near-tied arms.
import numpy as np
import check1 as c
for n in (160, 240, 320):
    for k in (1, 3, 5, 12):
        js = c.order[:k]
        print(f"n={n} k={k}: " + " | ".join(f"e={e}: {c.study(c.shift(js, e), n, R=4000)[0][3]:.3f}" for e in (2, 3, 3.5, 4, 4.24, 5)), flush=True)
    print(f"n={n} as stored: {c.study(c.O, n, R=4000)[0][3]:.3f}")
