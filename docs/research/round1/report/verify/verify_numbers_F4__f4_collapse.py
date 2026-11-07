import sys
import numpy as np
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator
base = "/home/catalin/work/phd/v5b1_runs/round1_remote/out/train_attr/tb/"
for i in range(5):
    acc = EventAccumulator(base + f"C{i}", size_guidance={"scalars": 0}); acc.Reload()
    ev = acc.Scalars("ppo/reward_per_decision")
    steps = [e.step for e in ev]
    r = np.array([e.value for e in ev], dtype=float)
    n = len(r)
    # own de-cycling: subtract phase mean (period 7) over updates 101-500 relative to overall late mean
    ph = np.arange(n) % 7
    late = np.arange(n) >= 100
    rr = r.copy()
    for k in range(7):
        rr[ph == k] -= r[(ph == k) & late].mean() - r[late].mean()
    a = abs(rr[400:500].mean() - rr[300:400].mean()); b = rr[400:500].mean() - rr[:50].mean(); s = rr[100:500].std()
    a0 = abs(r[400:500].mean() - r[300:400].mean()); s0 = r[100:500].std()
    print(f"C{i}: n={n} steps {steps[0]}..{steps[-1]} uniq {len(set(steps))}; decycled a={a:.4f} 0.4s={0.4*s:.4f} b={b:+.4f} pass={a<=0.4*s and b>=0}; raw a={a0:.4f} 0.4s={0.4*s0:.4f}")
