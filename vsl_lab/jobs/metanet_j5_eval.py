"""METANET v5 J5 evaluator (protocol v5 §B1): simulate a batch of parameter sets on the calibration days and score
J5 with the gate's own event layer (`metanet_postcal.model_day`), the shared per-day items (`metanet_items`) and the
pure J5 items (`metanet_j5`). Real side from the committed v5 facts (hash-checked). Calibration days only.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from vsl_lab.data import metanet_events as V
from vsl_lab.data import metanet_inputs as I
from vsl_lab.jobs import metanet_calibrate as C
from vsl_lab.jobs import metanet_gate as G
from vsl_lab.jobs import metanet_items as IT
from vsl_lab.jobs import metanet_j5 as J
from vsl_lab.jobs import metanet_postcal as Q
from vsl_lab.plants import metanet as M

EV0, NEV = Q.EV0, Q.NEV
J_INADMISSIBLE = 10.0


def real_events(rec: dict) -> dict:
    """The facts' per-day record in metanet_facts.day_events form (censor keys back to int)."""
    ev = {k: rec[k] for k in ("B1", "B2", "B1_long", "B2_long", "first", "heavy_first")}
    ev["censor"] = {int(k): v for k, v in rec["censor"].items()}
    return ev


class J5Eval:
    def __init__(self, facts_path: Path, facts_sha256: str, data: dict, net: M.Net, cs: dict):
        self.f = J.load_facts(facts_path, facts_sha256)
        mpath = Path(facts_path).with_name("metanet_v5_precal_masks.npz")
        import hashlib
        if hashlib.sha256(mpath.read_bytes()).hexdigest() != self.f["masks_npz_sha256"]:
            raise RuntimeError("J5 refuses to run: masks hash differs from the facts")
        z = np.load(mpath)
        self.Fm, self.Pm = z["F"], z["P1c"]
        self.days = self.f["days"]
        if [str(d) for d in data["days"]] != self.days:
            raise RuntimeError("calibration data days differ from the facts")
        self.data, self.net, self.cs = data, net, cs
        self.ev = {d: real_events(self.f["per_day"][d]) for d in self.days}
        self.q = self.f["qualifying"]
        self.rows, self.w = self.f["rows"], self.f["weights"]
        self.sids = [s["id"] for s in net.stations]
        self.scell = {st["id"]: st["cell"] for st in net.stations}

    # ------------------------------------------------------------ one model day
    def day_items(self, i: int, q_st, v_st, x_flow, rho, rc) -> dict:
        d, ev, rec, net, cs = self.days[i], self.ev[self.days[i]], self.f["per_day"][self.days[i]], self.net, self.cs
        md = Q.model_day(d, q_st, v_st, x_flow, net, cs, ev)
        msp, mvl = Q.model_speeds(d, v_st, net, cs)
        cong = rho[:, EV0:EV0 + NEV] > rc[:, EV0:EV0 + NEV]
        it: dict = {r: [] for r in self.rows}
        mm = {}
        for kk, k in ((1, "B1"), (2, "B2")):
            u, dn = Q.PAIR[k]
            with np.errstate(invalid="ignore"):
                cond = np.nan_to_num((msp[u] < 40.0) & ((msp[dn] - msp[u]) >= 20.0)).astype(bool)
            real = [tuple(e) for e in ev[k]]
            model = [tuple(e) for e in md[k]["episodes"]]
            credit = [J.creditable(e, cond, cong, k) for e in model]
            mm[k] = (real, model, credit)
            if k == "B1":
                self._credit_b1 = any(credit)
            # P3-k with shaping
            s = 0.0
            if real and not any(c and J.overlaps(m, r) for m, c in zip(model, credit) for r in real):
                wins = J.windows(real, ev["censor"] if k == "B1" else None, NEV)
                bc = J.BACK_CELLS[k]
                beta = np.min(np.stack([rho[c - 1, EV0:EV0 + NEV] / rc[c - 1, EV0:EV0 + NEV] for c in bc]), axis=0)
                s = J.shaping(J.g_value(J.margins(msp[u], msp[dn]), wins), J.h_value(beta, wins),
                              J.s_override(real, model, credit, wins))
            it[f"P3-{kk}"].append(J.p3_item(real, model, credit, s))
            if f"X-{kk}" in it and not real:
                it[f"X-{kk}"].append(J.x_item(real, model))
            if f"P4-{kk}" in it:
                it[f"P4-{kk}"] += J.p4_items(real, model, credit)
            if d in self.q["heavy"][k]:
                lg = ev[k + "_long"]
                mep = md[k].get("matched")
                ok = mep is not None and credit[model.index(tuple(mep))]
                don = (mep[0] - lg["ep"][0]) * J.BIN if mep is not None else None
                dq = IT.p5a_day(lg, md[k]["c4"]) if ok else None
                it[f"P5a-{kk}"].append(J.taper(J.capped(dq, J.CAP_QDIS), don) if dq is not None else 1.0)
                dm, dr, _ = IT.p7a_day(ev, md[k], k)
                it[f"P7a-{kk}"].append(J.taper(J.capped(dm - dr, J.CAP_DUR), don) if ok else 1.0)
        # system rows (all model episodes, as the gate)
        def don_long(k):
            mep, lg = md[k].get("matched"), ev[k + "_long"]
            return abs(mep[0] - lg["ep"][0]) * J.BIN if mep is not None and lg else 0.0
        if "P5c" in it and d in self.q["both_q"]:
            dc = IT.p5c_day(rec["merge"], [md[k]["merge"] for k in ("B1", "B2")])
            it["P5c"].append(J.taper(J.capped(dc, J.CAP_RATIO), max(don_long("B1"), don_long("B2")))
                             if dc is not None else 1.0)
        if d in self.q["heavy_any"]:
            rsp = {s_: I.event_station(d, s_)["v"] for s_ in I.EVENT_STATIONS}
            rvl = {s_: I.event_station(d, s_)["valid"] for s_ in I.EVENT_STATIONS}
            r7 = IT.p7b_day(ev, md, rsp, rvl, msp, mvl, G.extent, G.UPST)
            dons = [abs(md_e[0] - r_e[0]) * J.BIN for k in ("B1", "B2")
                    for ri, mj in V.match_episodes([tuple(e) for e in ev[k]], md[k]["episodes"]).items()
                    for r_e, md_e in [(tuple(ev[k][ri]), md[k]["episodes"][mj])]] or [0.0]
            it["P7b"].append(J.p7b_item(r7["err"] if r7["matched"] else None, max(dons)))
            it["P7c"].append(J.p7c_item(ev["B1"], ev["B2"], md["B1"]["episodes"], md["B2"]["episodes"]))
        # P8g
        rp = {tuple(k_.split("->")): e for k_, e in rec["pairs"].items()}
        p8 = IT.p8_day(md, ev, rp, Q.spurious, Q.overlaps)
        hitx = any(bool(ev[k]) and md[k]["agree"] and p8["extra"][k] for k in ("B1", "B2"))
        rl = Q.relocation(md["pairs"], rho[:, EV0:], rc[:, EV0:], net.b2_cells[-1] + 1)
        it["P8g"].append(float(bool(p8["spurious"]) or hitx or rl["flag"]))
        # guards and realism
        dq_, dv_ = self.data["q"][i], self.data["v"][i]
        it["P1a_h"].append(J.hinge("P1a", V.nrmse(q_st, dq_, self.data["mq"][i])))
        it["P1b_h"].append(J.hinge("P1b", V.nrmse(v_st, dv_, self.data["mv"][i])))
        it["P1a_ff"].append(J.realism("P1a_ff", V.nrmse(q_st, dq_, self.data["mq"][i] & self.Fm[i])))
        it["P1b_ff"].append(J.realism("P1b_ff", V.nrmse(v_st, dv_, self.data["mv"][i] & self.Fm[i])))
        if d in self.q["P1c_days"]:
            nm = V.nrmse(v_st, dv_, self.Pm[i])
            it["P1c_h"].append(J.p1c_hinge(nm, rec["P1c_null_N1"], rec["P1c_null_N2"]) if nm is not None else None)
        return it

    # ------------------------------------------------------------ batch
    def __call__(self, X: np.ndarray, T_s: float | None = None, return_parts: bool = False):
        """X (P, 17) normalised -> J5 (P,). A3 violators are not simulated (10 + shortfall); clipping > 1 % or a
        non-finite value on any day -> 10."""
        thr = C.a3_thresholds(self.net)
        params_all = C.to_params(X)
        short = C.a3_shortfall(params_all, thr)
        P, D = X.shape[0], len(self.days)
        Jv = 10.0 + short
        parts = [None] * P
        feas = np.flatnonzero(short <= 0.0)
        if feas.size:
            Xf = X[feas]
            o = M.simulate(self.net, C.to_params(Xf), M.Inputs(self.data["d0"], self.data["d_o"], self.data["beta"]),
                           n_param_sets=len(feas), record_cells=True, T_s=T_s or C.T_RUN)
            for a, pidx in enumerate(feas):
                sl = slice(a * D, (a + 1) * D)
                if (o.clipped_share[sl] > 0.01).any() or o.nonfinite[sl].any():
                    Jv[pidx] = J_INADMISSIBLE
                    continue
                rows = {r: [] for r in self.rows}
                per_day, cb1 = [], False
                for i in range(D):
                    b = a * D + i
                    it = self.day_items(i, o.q_st[b], o.v_st[b], o.exit_flow[b], o.rho_cell[b], o.rc_cell[b])
                    for r, v in it.items():
                        rows[r] += v
                    per_day.append(J.j_day(it, self.w))
                    cb1 |= self._credit_b1
                Jv[pidx] = J.j5(rows, self.w)
                if not np.isfinite(Jv[pidx]):
                    Jv[pidx] = J_INADMISSIBLE
                parts[pidx] = {"rows": {r: (float(np.mean([x for x in v if x is not None]))
                                            if any(x is not None for x in v) else None) for r, v in rows.items()},
                               "J_d": per_day, "any_creditable_B1": cb1}
        if return_parts:
            return Jv, parts
        return Jv
