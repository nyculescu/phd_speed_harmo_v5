"""W power at n = 240 (double bootstrap from 40 stored seeds: approximate), stored and shifted delay margins."""
import json
from multiprocessing import Pool
import power
import power_shift  # installs the shK scenarios
if __name__ == "__main__":
    jobs = [("X2@5300", "f1", 240, 400, 4000), ("X2@5300", "sh1", 240, 400, 4000), ("X1@5300", "sh3", 240, 400, 4000), ("X1@5300", "sh4", 240, 400, 4000)]
    with Pool(4) as pool:
        out = pool.map(power.task, jobs, chunksize=1)
    json.dump(out, open("power_n240.json", "w"), indent=1)
    for r in out:
        print(json.dumps({k: r[k] for k in ("cell", "sc", "n", "reps", "W", "L")}))
