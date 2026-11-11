"""EXPLORATORY: my own recomputation from the stored S6 rows (240 seeds, already read for a verdict). No simulation."""
import numpy as np
Z = np.load("f_scalars.npz")
KEYS = list(Z["keys"]); N0 = len(Z["seeds"])
arms = [f for f in Z.files if f not in ("keys", "seeds")]
print(len(arms), "arms", sorted(arms)[:70])
print("keys", KEYS)
