"""Does B_IN = 4,000 inner resamples change the power or the false-positive rate against round 2's 20,000? Same outer studies."""
import json
import sys
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import power  # noqa: E402

OUT = Path(__file__).resolve().parent
JOBS = [("X1@5300", "obs", 40, 200), ("X2@5300", "obs", 40, 200), ("X2@5300", "null", 40, 200), ("X2@5300", "obs", 80, 100)]

if __name__ == "__main__":
    with Pool(4, initializer=power.init) as pool:
        a = pool.map(power.task, [(c, s, n, r, 4000) for c, s, n, r in JOBS])
        b = pool.map(power.task, [(c, s, n, r, 20000) for c, s, n, r in JOBS])
    (OUT / "check_bin.json").write_text(json.dumps({"b4000": a, "b20000": b}))
    print("done", [round(x["sec"]) for x in a + b])
