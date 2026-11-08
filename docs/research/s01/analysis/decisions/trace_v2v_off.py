"""What the reversal and excess counts are made of: how many level changes and reversals come from ALKS whose level rarely acted
(V2V on in under 20 % of their seconds), v3w's 5 learners and 3E-T, X1 and X2, all 40 seeds (pooled per cell)."""
import json
import numpy as np
from common_dec import GROUPS, HERE
D = "/home/catalin/work/phd/v5b1_runs/measure_s01_remote/st/"
out = {}
for arm, names in (("v3w", GROUPS["v3w"]), ("3E-T", ["3e"]), ("os1_15_10", ["os1_15_10"])):
    for cell in ("X1", "X2"):
        ch = rv = ch_lo = rv_lo = nveh = nlo = 0
        for s in range(7_440_840, 7_440_880):
            for n in names:
                z = np.load(D + f"{cell}__{n}__5300__{s}.npz")
                d, L = z["dec"], z["dec_level_s"]
                tot = L.sum(1)
                share_on = np.where(tot > 0, L[:, :4].sum(1) / np.maximum(tot, 1), 0.0)
                lo = share_on < 0.2
                ch += d[:, 1].sum(); rv += d[:, 4].sum(); ch_lo += d[lo, 1].sum(); rv_lo += d[lo, 4].sum(); nveh += len(d); nlo += lo.sum()
        out[f"{arm}|{cell}"] = {"share_alks_on_lt_20pct": nlo / nveh, "share_changes_from_them": ch_lo / ch, "share_reversals_from_them": rv_lo / rv}
        print(arm, cell, {k: round(float(v), 3) for k, v in out[f"{arm}|{cell}"].items()})
(HERE / "trace_v2v_off.json").write_text(json.dumps(out, indent=1, default=float))
