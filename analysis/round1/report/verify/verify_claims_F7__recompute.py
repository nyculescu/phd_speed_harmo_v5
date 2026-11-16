import sys, numpy as np
from pathlib import Path
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator
base = Path("/home/catalin/work/phd/v5b1_runs/round1_remote/out")
for kind in ("attr", "res", "v3w"):
    d = base / f"train_{kind}" / "tb"
    if not d.exists():
        print(kind, "no tb dir"); continue
    for i in range(5):
        acc = EventAccumulator(str(d / f"C{i}"), size_guidance={"scalars": 0}); acc.Reload()
        ev = acc.Scalars("ppo/reward_per_decision")
        steps = [e.step for e in ev]
        r = np.array([e.value for e in ev], float)
        n = len(r)
        # independent phase removal: period 7, offsets over 0-based index >= 100
        ph = np.arange(n) % 7; late = np.arange(n) >= 100
        rr = r - np.array([r[(ph == k) & late].mean() - r[late].mean() for k in range(7)])[ph]
        a = abs(rr[400:500].mean() - rr[300:400].mean()); b = rr[400:500].mean() - rr[:50].mean(); s = rr[100:500].std()
        a0 = abs(r[400:500].mean() - r[300:400].mean()); s0 = r[100:500].std()
        print(f"{kind} C{i}: n={n} steps {min(steps)}-{max(steps)} a={a:.4f} 0.4s={0.4*s:.4f} b={b:+.4f} pass={a<=0.4*s and b>=0} | raw a={a0:.4f} 0.4s_raw={0.4*s0:.4f}")
