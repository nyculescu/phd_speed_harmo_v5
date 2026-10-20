"""V100: corrected meter signal on the D1/D2 meter path (opt-in) and the bug re-run mode of the D1/D2 runners."""
import argparse
import hashlib
import json
import types

import numpy as np
import pytest

import v5b.d1.episode as d1e
from v5b import bugrerun
from v5b.d1 import run_screen as rs1
from v5b.d1.meter_signal import SIGNALS, SignalClock
from v5b.d2 import controllers as ctl
from v5b.d2 import run_screen as rs2

GREEN, C_MAX = 6.0, 2.0 * 4 * 3600.0 / 200.0   # c(q_min) = 144 s


@pytest.fixture
def tls(monkeypatch):
    got = []
    monkeypatch.setattr(d1e, "ls", types.SimpleNamespace(
        trafficlight=types.SimpleNamespace(setRedYellowGreenState=lambda tls, s: got.append(s)),
        edge=types.SimpleNamespace(getLastStepVehicleNumber=lambda e: 0)))
    return got


def _drive(got, qs=None, reads=None, signal=None, n=900, t0=40.0, switch=None, K_F=0.0):
    """1-s ticks of the D1 FBMeter; q set to qs[k // 30] every 30 s (K_F = 0), or the feedback law on `reads`."""
    got.clear()
    kw = {} if signal is None else {"signal": signal}
    it = iter(reads) if reads is not None else None
    m = d1e.FBMeter(K_F=K_F, q0=float(qs[0]) if qs is not None else 1500.0,
                    read=(lambda t: float(next(it))) if it else (lambda t: 0.0), **kw)
    for k in range(n):
        if qs is not None and k and k % 30 == 0:
            m.q = float(qs[k // 30])
        if switch and k == switch[0]:
            m.q, m.K_F = switch[1], 0.0
        m.step(t0 + k)
    return list(got)


def _runs(states, val):
    out, cur = [], 0
    for s in states + ["end"]:
        if s == val:
            cur += 1
        elif cur:
            out.append(cur)
            cur = 0
    return out


def _legacy_states(qs, n=900, t0=40.0):
    """The pre-V100 rule written out independently: green iff (t - t_cycle0) mod c(current q) < 6."""
    out = []
    for k in range(n):
        q = float(qs[k // 30])
        c = max(GREEN, 8.0 * 3600.0 / q)
        out.append("GGGG" if (t0 + k - t0) % c < GREEN else "rrrr")
    return out


# ---------------------------------------------------------------- signal rule
def test_signal_clock_validates():
    assert SIGNALS == ("d2", "continuous")
    with pytest.raises(ValueError):
        SignalClock("other")


def test_continuous_red_never_exceeds_cmax_minus_green_under_changing_q(tls):
    rng = np.random.default_rng(100)
    worst = {"d2": 0, "continuous": 0}
    for i in range(60):
        lo, hi = ((200.0, 420.0), (200.0, 4000.0), (200.0, 1200.0))[i % 3]
        qs = rng.uniform(lo, hi, 31)
        for mode in worst:
            s = _drive(tls, qs=qs, signal=mode)
            worst[mode] = max(worst[mode], max(_runs(s, "rrrr")))
            if mode == "continuous":
                assert set(_runs(s, "GGGG")[:-1]) == {6}
    for _ in range(30):   # the feedback law itself moving q (K_F = 70, readings far from n_crit)
        s = _drive(tls, reads=rng.integers(0, 40, 100), signal="continuous", K_F=70.0)
        worst["continuous"] = max(worst["continuous"], max(_runs(s, "rrrr")))
    assert worst["continuous"] <= C_MAX - GREEN
    assert worst["d2"] > C_MAX - GREEN + 50   # the bug the legacy rule has


def test_constant_rate_identical_to_the_old_rule(tls):
    for q in ctl.RATES + (200.0, 4000.0):
        a = _drive(tls, qs=[q] * 31)                       # default (legacy)
        b = _drive(tls, qs=[q] * 31, signal="continuous")
        assert a == b == _legacy_states([q] * 31), q


def test_default_is_the_old_rule_bit_identical(tls):
    rng = np.random.default_rng(7)
    for _ in range(20):
        qs = rng.uniform(200.0, 4000.0, 31)
        assert _drive(tls, qs=qs) == _drive(tls, qs=qs, signal="d2") == _legacy_states(qs)
    m = d1e.FBMeter(read=lambda t: 0.0)
    assert m.signal == "d2"


def test_d1_fx_switch_constant_after_switch(tls):
    """FX after onset holds a constant rate: from the first green after the switch the continuous signal is
    periodic with c(q_fx), greens 6 s."""
    s = _drive(tls, qs=None, reads=[30] * 100, signal="continuous", K_F=20.0, switch=(301, 1200.0))
    tail = s[301:]
    starts = [k for k in range(1, len(tail)) if tail[k] == "GGGG" and tail[k - 1] == "rrrr"]
    assert np.all(np.diff(starts) == 24)   # c(1200) = 24 s
    assert set(_runs(tail, "GGGG")[1:-1]) == {6}


def test_p1_shares_the_clock():
    from v5b.p1 import meters as pm
    mt = pm.FBSignalMeter(K_F=0.0, q0=1600.0, read=lambda t: 0.0, signal="continuous", set_state=lambda s: None)
    assert isinstance(mt._clock, SignalClock) and mt._clock.signal == "continuous"
    assert pm.SIGNALS is SIGNALS


def test_reuse_refuses_other_meter_signal():
    s1 = rs1.spec("O", "none", 2000.0, 7_400_000)
    stored = {k: s1[k] for k in ("arm", "fault", "q", "seed", "q_fx", "ratio", "kf", "ncrit")}
    stored["code_commit"] = "c"
    assert rs1.reuse_mismatch(stored, s1, "c") == []                         # legacy run (no field) = d2
    assert rs1.reuse_mismatch(stored, s1, "c", "continuous") == ["meter_signal"]
    s2 = rs2.spec("c1200", None, "block", 2000.0, 7_400_000)
    st2 = {k: s2[k] for k in rs2.SPEC_FIELDS} | {"code_commit": "c", "meter_signal": "continuous"}
    assert rs2.reuse_mismatch(st2, s2, "c", "continuous") == []
    assert rs2.reuse_mismatch(st2, s2, "c") == ["meter_signal"]


# ---------------------------------------------------------------- bug re-run mode
def _page_sha(mod):
    return hashlib.sha256((mod.REPO_ROOT / mod.PAGE).read_bytes()).hexdigest()


@pytest.fixture
def reg(tmp_path, monkeypatch):
    """A registry whose originals are fake result.json files mirroring the real ones; sentinels in tmp."""
    seeds1 = {k: [v[0], v[-1]] for k, v in rs1.SEEDS.items()}
    seeds2 = {k: [v[0], v[-1]] for k, v in rs2.SEEDS.items()}
    o1, o2 = tmp_path / "d1_orig", tmp_path / "d2_orig"
    o1.mkdir()
    o2.mkdir()
    base = {"out": "x", "workers": 16, "cpu_limit": 0.7, "nice": 19, "smoke": False, "confirm_run_once": True,
            "resume": False}
    c1, c2 = bugrerun.BUG_RERUNS["V100"]["D1"]["original_commit"], bugrerun.BUG_RERUNS["V100"]["D2"]["original_commit"]
    (o1 / "result.json").write_text(json.dumps({
        "code_commit": c1, "decision": "STOP", "args": base | {"literal": False, "kf": 20.0, "ncrit": 8.0},
        "seeds": seeds1, "qs": rs1.QS, "tune": {"grid": rs1.FX_GRID}, "page_sha256": _page_sha(rs1)}))
    (o2 / "result.json").write_text(json.dumps({
        "code_commit": c2, "decision": "STOP", "args": base | {"workers": 32, "cpu_limit": 0.9},
        "seeds": seeds2, "qs": rs2.QS, "G": ctl.G, "page_sha256": _page_sha(rs2)}))
    r = {"V100": dict(bugrerun.BUG_RERUNS["V100"],
                      D1={"original": o1 / "result.json", "original_commit": c1, "sentinel": tmp_path / "D1_BUG.json"},
                      D2={"original": o2 / "result.json", "original_commit": c2, "sentinel": tmp_path / "D2_BUG.json"})}
    monkeypatch.setattr(bugrerun, "BUG_RERUNS", r)
    monkeypatch.setattr(rs1, "ALLOWED_ROOT", tmp_path)
    monkeypatch.setattr(rs2, "ALLOWED_ROOT", tmp_path)
    monkeypatch.setattr(rs1, "SENTINEL", tmp_path / "D1_EVAL_STARTED.json")   # never the real ones
    monkeypatch.setattr(rs2, "SENTINEL", tmp_path / "D2_EVAL_STARTED.json")
    monkeypatch.setattr(rs2, "TCHECK_RECORD", tmp_path / "D2_TCHECK_RECORD.json")
    clean = lambda *a: {"rev-parse": "c" * 40}.get(a[0], "")   # HEAD 'ccc...', clean tree
    monkeypatch.setattr(rs1, "_git", clean)
    monkeypatch.setattr(rs2, "_git", clean)
    return tmp_path


BUG = ["--bug-rerun", "V100", "--meter-signal", "continuous", "--confirm-run-once", "--workers", "32",
       "--cpu-limit", "0.90"]


def _d1_args(*extra):
    ap = argparse.ArgumentParser()
    for f in ("--smoke", "--confirm-run-once", "--literal", "--resume"):
        ap.add_argument(f, action="store_true")
    ap.add_argument("--out")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--cpu-limit", type=float, default=0.9)
    ap.add_argument("--nice", type=int, default=19)
    ap.add_argument("--kf", type=float, default=20.0)
    ap.add_argument("--ncrit", type=float, default=8.0)
    bugrerun.add_args(ap)
    return ap.parse_args(list(extra))


def _id1(o):
    return rs1.identity(o, _page_sha(rs1))


def _id2(o):
    return rs2.identity(o, _page_sha(rs2))


def test_bug_rerun_accepts_only_the_signal_change(reg):
    a = _d1_args("--out", str(reg / "new"), *BUG)
    rec = bugrerun.check(a, "D1", _id1)
    assert rec["original_result"].endswith("d1_orig/result.json") and rec["decision"] == "V100"
    assert rec["meter_signal"] == "continuous" and rec["sentinel"].endswith("D1_BUG.json")
    assert rec["operational_changes"] == {"workers": [16, 32], "cpu_limit": [0.7, 0.9]}
    a2 = rs2.build_parser().parse_args(["--out", str(reg / "new2"), *BUG])
    assert bugrerun.check(a2, "D2", _id2)["original_decision"] == "STOP"


@pytest.mark.parametrize("extra", [["--kf", "25"], ["--ncrit", "10"], ["--literal"]])
def test_bug_rerun_refuses_changed_options(reg, extra):
    with pytest.raises(SystemExit, match="differ"):
        bugrerun.check(_d1_args("--out", str(reg / "new"), *BUG, *extra), "D1", _id1)


def test_bug_rerun_refuses_wrong_signal_missing_confirm_original_out_and_code_drift(reg, monkeypatch):
    bad_sig = [x if x != "continuous" else "d2" for x in BUG]
    with pytest.raises(SystemExit, match="meter-signal"):
        bugrerun.check(_d1_args("--out", str(reg / "new"), *bad_sig), "D1", _id1)
    no_conf = [x for x in BUG if x != "--confirm-run-once"]
    with pytest.raises(SystemExit, match="confirm"):
        bugrerun.check(_d1_args("--out", str(reg / "new"), *no_conf), "D1", _id1)
    with pytest.raises(SystemExit, match="new --out"):
        bugrerun.check(_d1_args("--out", str(reg / "d1_orig"), *BUG), "D1", _id1)
    monkeypatch.setattr(rs1, "FX_GRID", rs1.FX_GRID[:-1])
    with pytest.raises(SystemExit, match="fx_grid"):
        bugrerun.check(_d1_args("--out", str(reg / "new"), *BUG), "D1", _id1)
    monkeypatch.setattr(rs2.ctl, "G", ctl.G[:-1])
    with pytest.raises(SystemExit, match="'G'"):
        bugrerun.check(rs2.build_parser().parse_args(["--out", str(reg / "n2"), *BUG]), "D2", _id2)


def test_bug_rerun_refuses_other_registered_commit(reg):
    p = bugrerun.BUG_RERUNS["V100"]["D2"]["original"]
    d = json.loads(p.read_text())
    p.write_text(json.dumps(d | {"code_commit": "0" * 40}))
    with pytest.raises(SystemExit, match="registered"):
        bugrerun.check(rs2.build_parser().parse_args(["--out", str(reg / "n2"), *BUG]), "D2", _id2)


def test_normal_mode_refuses_continuous_outside_smoke(reg):
    with pytest.raises(SystemExit, match="only with --bug-rerun"):
        bugrerun.check(_d1_args("--out", str(reg / "new"), "--meter-signal", "continuous", "--confirm-run-once"),
                       "D1", _id1)
    assert bugrerun.check(_d1_args("--out", str(reg / "new"), "--smoke", "--meter-signal", "continuous"),
                          "D1", _id1) is None
    assert bugrerun.check(_d1_args("--out", str(reg / "new"), "--confirm-run-once"), "D1", _id1) is None


def test_main_refuses_changed_option_before_any_run(reg):
    with pytest.raises(SystemExit, match="differ"):
        rs1.main(["--out", str(reg / "new"), *BUG, "--kf", "25"])
    assert not (reg / "new").exists() and not (reg / "D1_BUG.json").exists()


@pytest.mark.parametrize("mod,name", [(rs1, "D1"), (rs2, "D2")])
def test_main_refuses_a_second_bug_rerun(reg, mod, name):
    """The bug re-run's own sentinel exists (written by a first bug re-run): a second one with another --out, or the
    same --out without --resume, is refused before any run; the screen's original sentinel is not consulted."""
    sent = reg / f"{name}_BUG.json"
    mod.write_sentinel(reg / "first", "c" * 40, "p", {}, sent)
    for argv in (["--out", str(reg / "second"), *BUG], ["--out", str(reg / "first"), *BUG]):
        with pytest.raises(SystemExit, match="runs once"):
            mod.main(argv)
    assert not (reg / "second").exists()
    mod.check_sentinel(reg / "first", True, "c" * 40, sent)   # --resume of the same --out at the same commit: allowed
    with pytest.raises(SystemExit, match="commit"):
        mod.check_sentinel(reg / "first", True, "d" * 40, sent)


@pytest.mark.parametrize("mod,name", [(rs1, "D1"), (rs2, "D2")])
def test_bug_rerun_bypasses_the_original_sentinel_only_in_bug_mode(reg, mod, name, monkeypatch):
    mod.write_sentinel(reg / "orig_out", "a" * 40, "p", {}, mod.SENTINEL)   # the screen ran once already
    with pytest.raises(SystemExit, match="already started"):
        mod.main(["--out", str(reg / "plain"), "--confirm-run-once"])
    calls = []

    def stop(*a, **k):   # stop right after the bug-rerun sentinel would be written (no SUMO run)
        calls.append(a)
        raise SystemExit("stop-here")

    monkeypatch.setattr(mod.net, "build", stop)
    with pytest.raises(SystemExit, match="stop-here"):
        mod.main(["--out", str(reg / "bug"), *BUG])
    assert calls


def test_old_default_args_unchanged():
    a = rs2.build_parser().parse_args(["--out", "x"])
    assert a.meter_signal == "d2" and a.bug_rerun is None
    assert _d1_args("--out", "x").meter_signal == "d2"
