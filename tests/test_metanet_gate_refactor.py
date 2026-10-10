"""Protocol v5 test 30(a): the refactored gate reproduces the gate at tag `metanet-v4-stop` bit for bit.

Both versions of `metanet_gate.deterministic()` run in the same synthetic world: every data and simulation
dependency (validation inputs, real events, model day outputs, station series, freeze record, F11 facts) is stubbed
with random but structured synthetic values. No real day is read and nothing is simulated.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import types
from pathlib import Path

import numpy as np
import pytest

from vsl_lab.data import metanet_events as V
from vsl_lab.data import metanet_facts as F
from vsl_lab.data import metanet_inputs as I
from vsl_lab.jobs import metanet_calibrate as C
from vsl_lab.jobs import metanet_postcal as Q
from vsl_lab.plants import metanet as M

REPO = Path(__file__).resolve().parents[1]
TAG = "metanet-v4-stop"
EV0, NEV, NB = Q.EV0, Q.NEV, M.N_BINS


def tag_module():
    try:
        src = subprocess.run(["git", "-C", str(REPO), "show", f"{TAG}:vsl_lab/jobs/metanet_gate.py"],
                             capture_output=True, text=True, check=True).stdout
    except Exception:
        pytest.skip(f"tag {TAG} not available")
    mod = types.ModuleType("metanet_gate_tag")
    mod.__file__ = str(REPO / "vsl_lab/jobs/metanet_gate.py")
    sys.modules["metanet_gate_tag"] = mod
    exec(compile(src, "metanet_gate@" + TAG, "exec"), mod.__dict__)
    return mod


def current_module():
    spec = importlib.util.spec_from_file_location("metanet_gate_cur", REPO / "vsl_lab/jobs/metanet_gate.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["metanet_gate_cur"] = mod
    spec.loader.exec_module(mod)
    return mod


def _eps(rng, n_max, lo=40, hi=200):
    out = []
    for _ in range(int(rng.integers(0, n_max + 1))):
        s = int(rng.integers(lo, hi))
        out.append([s, s + int(rng.integers(2, 30))])
    out.sort()
    merged = []
    for s, e in out:                                   # episodes of one pair never overlap
        if merged and s <= merged[-1][1] + 6:
            continue
        merged.append([s, e])
    return merged


class World:
    """One synthetic validation set (deterministic in its rng seed; non-protocol synthetic seeds)."""

    def __init__(self, seed: int, n_days: int = 14):
        rng = np.random.default_rng(seed)
        self.rng = rng
        self.net = M.build_network(C.VARIANT)
        self.sids = [s["id"] for s in self.net.stations]
        ns, ne = len(self.sids), len(self.net.entrances)
        self.days = [f"SYN{seed}_{i:02d}" for i in range(n_days)]
        n = n_days
        v = rng.uniform(20, 70, (n, ns, NB)) * 1.609344
        q = rng.uniform(800, 2200, (n, ns, NB))
        self.data = {"days": np.array(self.days), "d0": rng.uniform(2000, 5000, (n, NB)),
                     "d_o": rng.uniform(0, 900, (n, ne, NB)), "beta": rng.uniform(0, 0.3, (n, 5, NB)),
                     "x_q": rng.uniform(0, 500, (n, 5, NB)), "q": q, "mq": rng.random((n, ns, NB)) > 0.1,
                     "v": v, "mv": rng.random((n, ns, NB)) > 0.1}
        self.o = types.SimpleNamespace(
            q_st=q * rng.uniform(0.9, 1.1, q.shape), v_st=v * rng.uniform(0.8, 1.2, v.shape),
            exit_flow=rng.uniform(0, 500, (n, 5, NB)), clipped_share=rng.uniform(0, 0.005, n),
            nonfinite=np.zeros(n, bool), rho_cell=np.zeros((n, 1, 1)), rc_cell=np.zeros((n, 1, 1)))
        self.real, self.model, self.ststa, self.pairs_real, self.msp, self.merge = {}, {}, {}, {}, {}, {}
        others = [p for p in [(a, b) for a, b in zip(I.EVENT_STATIONS, I.EVENT_STATIONS[1:])] if p not in (I.P1, I.P2)]
        for d in self.days:
            b1, b2 = _eps(rng, 2, 60, 150), _eps(rng, 1, 70, 160)
            if not b1 and rng.random() < 0.8:
                b1 = [[100, 120]]
            cens = V.censor_time([tuple(x) for x in b1], [tuple(x) for x in b2])
            ev = {"B1": b1, "B2": b2, "censor": cens}
            for k, eps in (("B1", b1), ("B2", b2)):
                if eps:
                    i = max(range(len(eps)), key=lambda j: (eps[j][1] - eps[j][0], -eps[j][0]))
                    tc = cens.get(i) if k == "B1" else None
                    ev[k + "_long"] = {"heavy": bool(rng.random() < 0.8), "ep": list(eps[i]),
                                       "c4": {"Q_dis": float(rng.uniform(1500, 2000)), "r": float(rng.uniform(0.0, 0.2))},
                                       "dur_min": V.censored_duration(tuple(eps[i]), tc)}
                else:
                    ev[k + "_long"] = None
            firsts = [(e[0], k) for k in ("B1", "B2") for e in ev[k]]
            ev["first"] = min(firsts)[1] if firsts else "B1"
            ev["heavy_first"] = bool(firsts and ev[ev["first"] + "_long"] and ev[ev["first"] + "_long"]["heavy"])
            self.real[d] = ev
            md = {"pairs": {}}
            for k, eps in (("B1", b1), ("B2", b2)):
                me = [[s + int(rng.integers(-15, 16)), e + int(rng.integers(-15, 16))] for s, e in eps if rng.random() < 0.75]
                me = [[s, max(s + 1, e)] for s, e in me]
                if rng.random() < 0.25:
                    s = int(rng.integers(30, 190))
                    me.append([s, s + int(rng.integers(2, 20))])
                me.sort()
                me = [tuple(x) for x in me]
                lg = ev[k + "_long"]
                mt = V.match_episodes([tuple(x) for x in eps], me)
                matched = me[mt[eps.index(lg["ep"])]] if lg and eps.index(lg["ep"]) in mt else None
                active = bool(me)
                agree = (bool(eps) and active and Q.overlaps(me, [tuple(x) for x in eps])) or (not eps and not active)
                md[k] = {"episodes": me, "active": active, "agree": bool(agree), "matched": matched,
                         "c4": ({"Q_dis": float(rng.uniform(1400, 2100)), "r": float(rng.uniform(0, 0.2))}
                                if matched else None),
                         "merge": float(rng.uniform(1500, 2100)) if rng.random() < 0.8 else None}
                md["pairs"][Q.PAIR[k]] = me
            for p in others:
                if rng.random() < 0.08:
                    s = int(rng.integers(30, 190))
                    md["pairs"][p] = [(s, s + 5)]
            self.model[d] = md
            self.pairs_real[d] = {p: ([[50, 60]] if rng.random() < 0.1 else []) for p in others} | {
                I.P1: b1, I.P2: b2}
            self.ststa[d] = {s: {"v": rng.uniform(15, 70, NEV), "valid": bool(rng.random() > 0.05),
                                 "q": rng.uniform(800, 2200, NEV)} for s in I.EVENT_STATIONS}
            self.msp[d] = ({s: rng.uniform(15, 70, NEV) for s in I.EVENT_STATIONS},
                           {s: bool(rng.random() > 0.05) for s in I.EVENT_STATIONS})
            self.merge[d] = [({"discharge": float(rng.uniform(1500, 2100))} if rng.random() < 0.85 else None)
                             for _ in range(2)]
        n1 = rng.uniform(90, 110, ns)
        self.nulls = {"N1": n1, "N2": rng.uniform(40, 110, (ns, NB))}
        self.arr = {d: rng.uniform(1400, 2600, NB // 3) for d in self.days}

    def install(self, mp, gate, tmp: Path):
        facts = tmp / "facts.json"
        facts.write_text(json.dumps({"F11": {"P8_tolerance": 3, "flow_null_N2_q": {"median_nrmse_q": 0.21},
                                             "floors": {"B1": {"L_r": 0.03}, "B2": {"L_r": 0.03}}}}))
        mp.setattr(C, "FACTS", facts)
        mp.setattr(Q, "part1", lambda: {"c_s": {}})
        mp.setattr(Q, "simf", lambda *a, **k: self.o)
        mp.setattr(F, "day_events", lambda d: self.real[d])
        mp.setattr(Q, "model_day", lambda d, *a, **k: self.model[d])
        mp.setattr(F, "merge_section", lambda d, k, ev: self.merge[d][0 if k == "B1" else 1])
        mp.setattr(I, "event_station", lambda d, s: self.ststa[d][s])
        mp.setattr(I, "event_pairs", lambda d: self.pairs_real[d])
        mp.setattr(Q, "model_speeds", lambda d, *a, **k: self.msp[d])
        mp.setattr(Q, "p11_day", lambda d, *a, **k: d)
        mp.setattr(Q, "p11_verdict", lambda res: {"tolerance": 2, **{k: {
            "n_unbacked": 1, "unbacked_days": [], "pooled_backed_share": 0.8, "most_downstream_congested_cell": 31,
            "PASS": True} for k in ("B1", "B2")}})
        mp.setattr(gate, "plant", lambda seed: (7191013, {"vf1": 100.0}))
        mp.setattr(gate, "load_val", lambda: self.data)
        mp.setattr(gate, "freeze", lambda: {"stephalving": {"PASS": True}, "nominal_seed": 7191013})
        mp.setattr(gate, "nulls", lambda: self.nulls)
        mp.setattr(gate, "arrivals", lambda d0, d_o, x_q, net, p, b: self.arr[self.days[[
            i for i in range(len(self.days)) if self.data["d0"][i] is d0 or np.shares_memory(self.data["d0"][i], d0)][0]]])
        mp.setattr(gate, "RUNS", tmp)


def run_gate(gate, world, mp, tmp):
    world.install(mp, gate, tmp)
    return json.loads(json.dumps(gate.deterministic(None), default=float))


def test30a_gate_refactor_bit_for_bit(monkeypatch, tmp_path):
    """Synthetic worlds 101-130 (non-protocol seeds). On every world the tag can run, the refactored gate gives the
    identical result (≥ 3 required). Worlds where the tag raises (P9's empty S1 window, a latent crash fixed in the
    refactor) must run under the refactored gate."""
    tag, cur = tag_module(), current_module()
    same, crash = 0, 0
    for seed in range(101, 131):
        w = World(seed)
        try:
            old = run_gate(tag, w, monkeypatch, tmp_path)
        except ValueError:
            old = None
        monkeypatch.undo()
        new = run_gate(cur, w, monkeypatch, tmp_path)
        monkeypatch.undo()
        if old is None:
            crash += 1
            continue
        assert old == new, f"world {seed}"
        assert len(old["rows"]) >= 20
        same += 1
    print(f"\ntest30a: {same} worlds identical, {crash} tag crashes (refactor runs)")
    assert same >= 3, (same, crash)


def test_s1_empty_window_returns_none():
    from vsl_lab.jobs import metanet_items as IT
    q = np.arange(50, dtype=float)
    assert IT.s1_ratio(q, 40, 45, 10.0, cut=20) is None          # window [28, 19] is empty
    assert IT.s1_ratio(q, 10, 12, 10.0, cut=None) == pytest.approx(np.convolve(q[0:13], np.ones(3) / 3, "valid").max() / 10)


def test34_screen_ctx_path(monkeypatch, tmp_path):
    """v5 §B5 screen path of the gate: substitutes applied, no F11/freeze/val file read, per-day nulls, own boot seed."""
    gate = current_module()
    w = World(101)
    w.install(monkeypatch, gate, tmp_path)
    monkeypatch.setattr(C, "FACTS", tmp_path / "absent.json")          # any F11 read would raise
    monkeypatch.setattr(gate, "freeze", lambda: (_ for _ in ()).throw(AssertionError("freeze read")))
    monkeypatch.setattr(gate, "load_val", lambda: (_ for _ in ()).throw(AssertionError("val read")))
    calls = []
    ctx = {"seed": None, "p": {"vf1": 100.0}, "data": w.data, "stephalving_PASS": True, "boot_seed": 7192099,
           "f11": {"P8_tolerance": 3, "floors": {"B1": {"L_r": 0.777}, "B2": {"L_r": 0.888}},
                   "flow_null_N2_q": {"median_nrmse_q": None}},
           "nulls_for": lambda i: calls.append(i) or w.nulls, "write": False}
    res = gate.deterministic(None, ctx=ctx)
    assert res["rows"]["P5b-1"]["L_r"] == 0.777 and res["rows"]["P5b-2"]["L_r"] == 0.888
    assert res["rows"]["P8"]["tolerance"] == 3
    assert calls and len(set(calls)) == len(calls)                    # nulls fetched per real-active day
    assert gate.SEED_BOOT == 7191300                                  # restored after the screen
    ctx2 = dict(ctx, boot_seed=1)
    r2 = gate.deterministic(None, ctx=ctx2)["rows"]
    assert any(r2[k]["ci"] != res["rows"][k]["ci"] for k in ("P1a", "P1b"))   # the boot seed is used (continuous rows)
    assert not list(tmp_path.glob("gate_det_*.json"))                 # write=False


def test_v5_gate_wiring(monkeypatch, tmp_path):
    """v5 gate: start record before any validation read, output only in the v5 raw dir, v4 RUNS restored (test 22)."""
    from vsl_lab.jobs import metanet_gate as G
    from vsl_lab.jobs import metanet_v5_calibrate as V5
    from vsl_lab.jobs import metanet_v5_gate as VG
    w = World(101)
    w.install(monkeypatch, G, tmp_path)
    v5dir, v4dir = tmp_path / "v5", tmp_path / "v4"
    v5dir.mkdir(); v4dir.mkdir()
    monkeypatch.setattr(V5, "RUNS5", v5dir)
    monkeypatch.setattr(G, "RUNS", v4dir)
    order = []
    rec = {"nominal": 7192013, "frozen_params": {"vf1": 100.0}, "stops": {"step-halving": "PASS"}}
    monkeypatch.setattr(VG, "check", lambda s: (7192013, rec, {}, {"code": "c", "freeze_blob": "b"}))
    from vsl_lab.ops import ledger as _ledger
    monkeypatch.setattr(_ledger, "append", lambda *a, **k: order.append("ledger"))
    real_start = VG.start_record
    monkeypatch.setattr(VG, "start_record", lambda *a: order.append("start") or real_start(*a))
    with pytest.raises(SystemExit):                                   # missing prep output: refused, no lock left
        VG.deterministic(None)
    assert not (v5dir / VG.LOCKF).exists() and order == []
    (v5dir / "val_data.npz").write_bytes(b"placeholder")              # load_val itself is stubbed by the world
    lv = G.load_val
    monkeypatch.setattr(G, "load_val", lambda: order.append("val") or lv())
    r = VG.deterministic(None)
    assert order[:3] == ["start", "ledger", "val"]
    assert (v5dir / "gate_det_7192013.json").exists() and not list(v4dir.glob("*"))
    assert G.RUNS == v4dir and r["plant_seed"] == 7192013


def test30b_j5_items_map_to_gate_statistics():
    """On the synthetic worlds, with every episode creditable and no taper, J5's items are the capped gate per-day
    statistics (same shared functions): P4 |Δonset|, P7a |Δdur|, P5a D, P7c |Δdur_sys|, P8 extra flags."""
    from vsl_lab.jobs import metanet_items as IT
    from vsl_lab.jobs import metanet_j5 as J
    n = 0
    for seed in (101, 202, 303):
        w = World(seed)
        for d in w.days:
            ev, md = w.real[d], w.model[d]
            for k in ("B1", "B2"):
                real, model = [tuple(e) for e in ev[k]], md[k]["episodes"]
                cr = [True] * len(model)
                exp = [J.capped(dt, J.CAP_ONSET) if dt is not None else 1.0 for dt, _ in IT.p4_day(real, model)]
                assert J.p4_items(real, model, cr) == exp
                lg = ev[k + "_long"]
                if lg and md[k].get("matched") is not None:
                    dm, dr, _ = IT.p7a_day(ev, md[k], k)
                    don = (md[k]["matched"][0] - lg["ep"][0]) * J.BIN
                    if abs(don) <= J.TAPER_A:
                        assert J.taper(J.capped(dm - dr, J.CAP_DUR), don) == J.capped(dm - dr, J.CAP_DUR)
                        n += 1
            dr_, dm_ = IT.p7c_day(ev, md)
            it = J.p7c_item(ev["B1"], ev["B2"], md["B1"]["episodes"], md["B2"]["episodes"])
            if it is not None and dm_ > 0:
                assert it >= J.capped(dm_ - dr_, J.CAP_DUR) - 1e-12      # taper can only raise it
    assert n > 0


def test_v5_gate_check_real(monkeypatch, tmp_path):
    """check() itself (not stubbed): dirty code refuses before any lock; a ledger start record with a missing or
    different raw-dir lock refuses; a consistent record at unchanged hashes passes."""
    import json as _j
    from vsl_lab.jobs import metanet_gate as G
    from vsl_lab.jobs import metanet_v5_calibrate as V5
    from vsl_lab.jobs import metanet_v5_gate as VG
    rec = {"protocol": VG.PROTOCOL, "stage": "freeze", "route": "continue", "nominal": 7192013, "members": []}
    f = tmp_path / "rec.json"; f.write_text(_j.dumps(rec))
    monkeypatch.setattr(VG, "FREEZE5", C.REPO / "docs" / "x.json")
    monkeypatch.setattr(VG, "AUDIT5", C.REPO / "docs" / "a.json")
    monkeypatch.setattr(VG.Path, "read_text", lambda self, *a, **k: _j.dumps(rec) if self.name == "x.json"
                        else open(self).read(), raising=False)
    monkeypatch.setattr(V5, "RUNS5", tmp_path)
    git = {"ls-files": "x", "status": "", "log": "abc", "hash-object": "blob1"}
    monkeypatch.setattr(VG, "_git", lambda *a: git[a[0]])
    monkeypatch.setattr(VG, "FIXES5", tmp_path / "nofixes")
    monkeypatch.setattr(V5, "code_commit", lambda: (_ for _ in ()).throw(SystemExit("dirty")))
    monkeypatch.setattr(VG, "ledger_starts", lambda: {})
    with pytest.raises(SystemExit):
        VG.check(None)
    assert not (tmp_path / VG.LOCKF).exists()
    monkeypatch.setattr(V5, "code_commit", lambda: "c1")
    assert VG.check(None)[0] == 7192013
    monkeypatch.setattr(VG, "ledger_starts", lambda: {"7192013": {"code": "c1", "freeze_blob": "blob1"}})
    with pytest.raises(SystemExit):                                   # ledger says started, lock file deleted
        VG.check(None)
    (tmp_path / VG.LOCKF).write_text(_j.dumps({"7192013": {"code": "c1", "freeze_blob": "blob1"}}))
    assert VG.check(None)[0] == 7192013                               # plain re-run at unchanged hashes
    monkeypatch.setattr(V5, "code_commit", lambda: "c2")               # code changed since the start record
    with pytest.raises(SystemExit):
        VG.check(None)



def test_v5_gate_lock_two_way(monkeypatch, tmp_path):
    """A lock entry with no ledger row (ledger reverted) is refused."""
    import json as _j
    from vsl_lab.jobs import metanet_v5_calibrate as V5
    from vsl_lab.jobs import metanet_v5_gate as VG
    rec = {"protocol": VG.PROTOCOL, "stage": "freeze", "route": "continue", "nominal": 7192013, "members": []}
    monkeypatch.setattr(VG, "FREEZE5", C.REPO / "docs" / "x.json")
    monkeypatch.setattr(VG, "AUDIT5", C.REPO / "docs" / "a.json")
    monkeypatch.setattr(VG.Path, "read_text", lambda self, *a, **k: _j.dumps(rec) if self.name == "x.json"
                        else open(self).read(), raising=False)
    monkeypatch.setattr(V5, "RUNS5", tmp_path)
    git = {"ls-files": "x", "status": "", "log": "abc", "hash-object": "blob1"}
    monkeypatch.setattr(VG, "_git", lambda *a: git[a[0]])
    monkeypatch.setattr(VG, "FIXES5", tmp_path / "nofixes")
    monkeypatch.setattr(V5, "code_commit", lambda: "c1")
    monkeypatch.setattr(VG, "ledger_starts", lambda: {})
    (tmp_path / VG.LOCKF).write_text(_j.dumps({"7192013": {"code": "c1", "freeze_blob": "blob1"}}))
    with pytest.raises(SystemExit):
        VG.check(None)


def test_code_commit_and_fix_rerun_in_a_real_repo(monkeypatch, tmp_path):
    """Ledger appends never block (no deadlock); a code change does; a committed fix record is accepted only if its
    fix commit is an ancestor of HEAD with no later vsl_lab code change."""
    import subprocess as sp
    from vsl_lab.jobs import metanet_v5_calibrate as V5
    from vsl_lab.jobs import metanet_v5_gate as VG
    r = tmp_path / "repo"
    (r / "vsl_lab" / "runs").mkdir(parents=True)
    g = lambda *a: sp.run(["git", "-C", str(r), *a], capture_output=True, text=True, check=True).stdout.strip()
    g("init", "-q"); g("config", "user.email", "t@t"); g("config", "user.name", "t")
    (r / "vsl_lab" / "x.py").write_text("a = 1\n"); (r / "vsl_lab" / "runs" / "ledger.csv").write_text("h\n")
    g("add", "-A"); g("commit", "-qm", "base")
    monkeypatch.setattr(C, "REPO", r)
    head0 = V5.code_commit()
    (r / "vsl_lab" / "runs" / "ledger.csv").write_text("h\nstart row\n")       # a start record was appended
    assert V5.code_commit() == head0
    (r / "vsl_lab" / "x.py").write_text("a = 2\n")
    with pytest.raises(SystemExit):
        V5.code_commit()
    g("add", "vsl_lab/x.py"); g("commit", "-qm", "fix"); fix = g("rev-parse", "HEAD")
    (r / "docs").mkdir(); (r / "docs" / "fix.json").write_text("{}")
    g("add", "-A"); g("commit", "-qm", "fix record + ledger"); head = g("rev-parse", "HEAD")
    assert VG.fix_rerun_ok({"rerun_seed": 1, "fix_commit": fix}, 1, head)
    assert not VG.fix_rerun_ok({"rerun_seed": 2, "fix_commit": fix}, 1, head)
    (r / "vsl_lab" / "x.py").write_text("a = 3\n"); g("commit", "-qam", "later code"); head2 = g("rev-parse", "HEAD")
    assert not VG.fix_rerun_ok({"rerun_seed": 1, "fix_commit": fix}, 1, head2)   # code changed after the fix
    g("checkout", "-q", "-b", "other", head0); (r / "y").write_text("y"); g("add", "-A"); g("commit", "-qm", "o")
    assert not VG.fix_rerun_ok({"rerun_seed": 1, "fix_commit": g("rev-parse", "HEAD")}, 1, head)  # not an ancestor
