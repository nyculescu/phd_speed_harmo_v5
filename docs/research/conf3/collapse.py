"""The collapse check of the protocol. usage: collapse.py train_dir learners. Exit 1 if more than one learner fails."""
import json
import sys
from pathlib import Path

import numpy as np


def stat(rows: list) -> tuple:
    r = np.array([x["r"] for x in rows])
    return abs(r[400:500].mean() - r[300:400].mean()), r[400:500].mean() - r[:50].mean()


if __name__ == "__main__":
    d, n = Path(sys.argv[1]), int(sys.argv[2])
    bad = []
    for i in range(n):
        rows = [json.loads(x) for x in open(d / f"C{i}_updates.jsonl")]
        a, b = stat(rows)
        ok = len(rows) >= 500 and a <= 0.03 and b >= 0.0
        print(f"C{i}: {len(rows)} updates, last two blocks differ {a:.4f}, gain on the start {b:+.4f}, {'ok' if ok else 'FAILS'}", flush=True)
        bad += [] if ok else [i]
    sys.exit(1 if len(bad) > 1 else 0)
