"""D4.12 follow-up diagnostic (ledger row capacity_forcing_diagnostic, 2026-10-07T19:57, commit a2cfc00+dirty).
RECOVERED, not committed at the time: it ran as an inline heredoc in the Claude session (never a file). This text is
copied verbatim from the session transcript on 2026-10-08 (protocol v5 §B8 step 1). Command prefix as run:
export OMP_NUM_THREADS=1 && timeout 2400 venv314/bin/python - <<'EOF' 2>&1 | grep -v Warn
"""
import math, numpy as np
from vsl_lab.jobs import metanet_calibrate as C, metanet_postcal as Q
from vsl_lab.plants import metanet as M
from vsl_lab.data import metanet_inputs as I
data = C.load_data(); days = [str(d) for d in data["days"]]
net = M.build_network("v4"); cs = Q.part1()["c_s"]
p0 = Q.plant_params()
cap0 = p0["vf3"] * math.exp(-1 / p0["a3"]) * p0["rc3"]
rows = []
for target in (None, 2400.0, 2100.0, 1900.0):
    p = dict(p0)
    if target:
        p["rc3"] = p0["rc3"] * target / cap0                  # G3 capacity/lane -> target (head scaled by theta1 as before)
    x = C.to_norm(p)[None, :]
    J, parts = C.objective(x, data, net, return_parts=True)
    o = M.simulate(net, {k: np.array([v]) for k, v in p.items()}, M.Inputs(data["d0"], data["d_o"], data["beta"]), record_cells=False)
    mp = [Q.model_pairs(d, o.v_st[i], net, cs) for i, d in enumerate(days)]
    b1 = sum(bool(m.get(I.P1)) for m in mp); b2 = sum(bool(m.get(I.P2)) for m in mp)
    pr = parts["parts"][0] if parts["parts"] is not None else None
    terms = [round(float(np.nanmean(pr[:, k])), 3) for k in range(3)] if pr is not None else None
    print(f"G3 cap/lane {target or round(cap0)}: rc3 {p['rc3']:.1f}, J {J[0]:.4f}, terms (q, v, v_cong) {terms}, model B1 days {b1}/22, B2 days {b2}/22 (real 22, 9)")
