"""My raw() against the project's conf3/common.raw (imported read-only) on a few arm pairs."""
import sys
import lib
sys.path.insert(0, str(lib.WT / "docs/research/conf3"))
from common import raw as raw_c3  # noqa: E402
T = lib.load()
for cell in ("X1", "X2"):
    nc = T[(f"{cell}|nc", lib.Q)]
    for arm, nm in lib.arms(cell).items():
        A = lib.arm_mean(T, [f"{cell}|{n}" for n in nm])
        for key in ("ttc_net", "all_delay"):
            a, b = lib.raw(A, nc, key), raw_c3(A, nc, key, pct=(2.5, 97.5))
            assert a == b, (cell, arm, key, a, b)
print("raw identical to conf3/common.raw at 95 % on all arms, both cells, ttc_net and all_delay")
