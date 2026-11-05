"""Report only: the u250 policy against the final one, 5 tuning seeds, X1 and X2. usage: u250.py train_dir out_dir workers"""
import sys
from pathlib import Path

from common import LEARNERS, PRIMARY, Q, SEEDS_TUNE, cfg, effect, load
from v5b.fleet import plant_sweep as ps

if __name__ == "__main__":
    train, out, w = Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3])
    seeds = range(SEEDS_TUNE[0], SEEDS_TUNE[0] + 5)
    c = {f"{x}|{tag}{i}": cfg({"pt": str(train / f"C{i}_{f}.pt")}, x) for i in range(LEARNERS) for x in PRIMARY for tag, f in (("u", "u250"), ("f", "final"))}
    ps.matrix(c, (Q,), seeds, out / "u250.jsonl", w, str(out / "rd"))
    T = load(out / "u250.jsonl")
    for x in PRIMARY:
        for i in range(LEARNERS):
            A, B = T[(f"{x}|f{i}", Q)], T[(f"{x}|u{i}", Q)]
            print(x, f"C{i}", "final against u250: TTC", effect(A, B, "ttc_net", pct=(2.5, 97.5)), "delay", effect(A, B, "all_delay", pct=(2.5, 97.5)), flush=True)
