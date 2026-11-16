"""Trace: per-vehicle decision records of v3w (w0u250) on one seed, X1 and X2: what a 'reversal' and an 'excess change' are made of."""
import numpy as np
D = "/home/catalin/work/phd/v5b1_runs/measure_s01_remote/st/"
for cell in ("X1", "X2"):
    z = np.load(D + f"{cell}__w0u250__5300__7440840.npz")
    d, L = z["dec"], z["dec_level_s"]
    asked, ch, ign, kept, rev, last = d.T
    on = L[:, :4].sum(1)
    print(cell, "ALKS", len(d), "asked=changed+ignored+kept:", bool(np.all(asked == ch + ign + kept)),
          "| changes p50/p90/max", np.percentile(ch, [50, 90]).tolist(), ch.max(), "| reversals p50/p90/max", np.percentile(rev, [50, 90]).tolist(), rev.max(),
          "| share of ALKS with >=4 reversals", round(float((rev >= 4).mean()), 3), "| last level counts", np.bincount(last, minlength=4).tolist())
    i = int(np.argmax(rev))
    print("   most reversals:", z["dec_ids"][i], "asked", asked[i], "changed", ch[i], "kept", kept[i], "reversals", rev[i], "last", last[i],
          "on-seconds per level 1.6/1.2/1.0/0.8 s", L[i, :4].tolist(), "off", L[i, 4])
    # bound: reversals <= changes - 1 for any vehicle with changes
    print("   reversals <= changes-1 where changes>0:", bool(np.all(rev[ch > 0] <= ch[ch > 0] - 1)), "| excess = changes - last >= 0:", bool(np.all(ch - last >= 0)))
