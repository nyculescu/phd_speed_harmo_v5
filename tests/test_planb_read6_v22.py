"""read6 v2.2 (read6_v2_spec.md amendment 4): fixes from the review of v2.1. Written before the fix; each test fails on 6b5778c,
except the coverage tests marked so, which pin behaviour 6b5778c already has (each one fails on a mutant the review ran)."""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "docs/research/planb"))
sys.path.insert(0, str(ROOT))
import read6_regress  # noqa: E402
import test_planb_read6 as t1  # noqa: E402
from test_planb_read6 import LEARN, N, OPP, cfg, r6, world  # noqa: E402
from test_planb_read6_v2 import PICKS, with_report_keys  # noqa: E402
from test_planb_read6_v21 import universe_world  # noqa: E402
from v5b.fleet import measure  # noqa: E402

JAM = ("jam_share", "congested_share", "jams", "congested_km_mean", "congested_km_max", "osc_kmh")


def field_npz(path: Path, shape=(12, 10)) -> tuple:
    """A space-time field at 100 km/h with a 3 x 3 jam at 20 km/h and a 50 km/h strip, 2 vehicles a cell."""
    kmh = np.full(shape, 100.0)
    kmh[2:5, 3:6] = 20.0
    kmh[7, :] = 50.0
    n = np.full(shape, 2.0, np.float32)
    v = (kmh / 3.6 * n).astype(np.float32)
    np.savez_compressed(path, v=v, n=n, brk_road=np.array(["3", "4a"]))
    return v, n


def st_row(name="X|w0", seed=0, f="k.npz", shape=(12, 10)) -> dict:
    return t1.pack_row(name, seed) | {"m_st_file": f, "m_st_dt": 10.0, "m_st_dx": 50.0, "m_st_shape": list(shape)}


def test_derive_reads_the_jam_metrics_from_the_side_file(tmp_path):
    v, n = field_npz(tmp_path / "k.npz")
    d = r6.derive(st_row(), tmp_path)
    w = measure.waves(v, n, 10.0, 50.0)
    assert {k: d[k] for k in JAM} == {k: w[k] for k in JAM} and d["jam_share"] > 0 and d["jams"] == 1
    assert d["st_file"] == "k.npz" and d["st_sha256"] == hashlib.sha256((tmp_path / "k.npz").read_bytes()).hexdigest()


def test_a_missing_or_misshaped_side_file_stops_the_reading(tmp_path):
    field_npz(tmp_path / "k.npz")
    with pytest.raises(SystemExit):
        r6.derive(st_row(f="absent.npz"), tmp_path)
    with pytest.raises(SystemExit):
        r6.derive(st_row(shape=(12, 11)), tmp_path)


def jam_world(f: float = 0.9) -> dict:
    """with_report_keys plus the jam keys: v3w f times each opponent's value."""
    T = with_report_keys(world())
    rng = np.random.default_rng(5)
    for (cond, name), rows in T.items():
        for b in rows.values():
            for k in JAM:
                b[k] = 100.0 * (f if name in LEARN else 1.0) * (1 + rng.normal(0, 0.01))
    return T


def test_map_report_only_carries_the_jam_metrics():
    res = r6.read(jam_world(), cfg() | {"st_dir": "st"})
    for block in (res["cells"]["X"]["map_report_only"], res["S"]["map_report_only"]):
        for o in OPP + ["nc"]:
            for k in JAM:
                assert block[o][k]["effect"] == pytest.approx(10.0, abs=1.0)


def test_jam_metrics_without_side_files_say_so():
    m = r6.read(with_report_keys(world()), cfg())["cells"]["X"]["map_report_only"]["p333"]
    assert all(m[k]["effect"] is None and m[k]["why"] == r6.NO_ST for k in JAM)


def test_the_output_hashes_the_side_files_it_read():
    T = jam_world()
    for (cond, name), rows in T.items():
        for s, b in rows.items():
            b |= {"st_file": f"{cond}_{name}_{s}.npz", "st_sha256": hashlib.sha256(f"{cond}{name}{s}".encode()).hexdigest()}
    out = r6.read(T, cfg() | {"st_dir": "st"})["space_time"]
    lines = sorted(f"{b['st_file']} {b['st_sha256']}\n" for rows in T.values() for b in rows.values())
    assert out == {"dir": "st", "files": len(lines), "sha256": hashlib.sha256("".join(lines).encode()).hexdigest()}
    assert r6.read(with_report_keys(world()), cfg())["space_time"] == {"dir": None, "files": 0, "sha256": None}


def picks_files(tmp_path: Path, commit_r="c0", commit_p="c0", repicks=None, front="lr") -> tuple:
    p = tmp_path / "picks.json"
    p.write_text(json.dumps(PICKS | {"run_commit": commit_p, "repicks": repicks or {"X": {"lr": {}, "p333": {}, "dly": {}}}}))
    f = tmp_path / "repick.json"
    f.write_text(json.dumps({"code": {"commit": commit_r}, "picks": {"X": {"forms": {"uniform": "p333", "local": "lr"}, "delay_opponent": "dly",
                                                                            "front_row": front}}}))
    return str(p), str(f)


def main_world(tmp_path: Path, monkeypatch) -> str:
    T, c = universe_world()
    monkeypatch.setattr(r6, "load_rows", lambda *a, **k: T)
    conf = tmp_path / "c.json"
    conf.write_text(json.dumps({k: v for k, v in c.items() if k not in ("picks", "forms")} | {"run_commit": "c0"}))
    return str(conf)


def test_a_full_run_needs_the_side_files(tmp_path, monkeypatch):
    conf = main_world(tmp_path, monkeypatch)
    p, f = picks_files(tmp_path)
    with pytest.raises(SystemExit, match="--st"):
        r6.main(["rows", conf, str(tmp_path / "o.json"), "--picks", p, "--forms", f])


def test_forms_must_come_from_the_run_commit(tmp_path):
    rep = {"code": {"commit": "c1"}, "picks": {"X": {"forms": {"uniform": "p333", "local": "lr"}, "delay_opponent": "dly", "front_row": "lr"}}}
    picks = {"run_commit": "c0", "repicks": {"X": {"lr": {}, "p333": {}, "dly": {}}}}
    with pytest.raises(SystemExit, match="commit"):
        r6.check_forms(rep, picks, ["X"])
    assert r6.check_forms(rep | {"code": {"commit": "c0"}}, picks, ["X"]) == {"X": ["p333", "lr"]}


def os1_world() -> tuple:
    """universe_world plus os1_15_10, 1 % slower than p333."""
    T, c = universe_world()
    for cond in ("X", "S"):
        T[(cond, "os1_15_10")] = {s: dict(v, all_delay=v["all_delay"] * 1.01) for s, v in T[(cond, "p333")].items()}
    c["opponents"] = {"X": c["opponents"]["X"] + ["os1_15_10"]}
    return T, c


def test_excluded_3e_has_95_percent_intervals_against_both_references():
    T, c = os1_world()
    ex = r6.read(T, c)["cells"]["X"]["t2_counting_filter"]["excluded_3e"]["3e"]
    E, R, P = (np.array([T[("X", n)][s]["all_delay"] for s in range(N)]) for n in ("3e", "os1_15_10", "p333"))
    for got, ref in ((ex["vs_os1_15_10"]["delay"], R), (ex["delay_vs_p333"], P)):
        assert len(got) == 3 and got[1] < got[0] < got[2]
        assert got[0] == pytest.approx(float(np.median(-(E - ref) / np.median(ref) * 100.0)))
    assert ex["vs_os1_15_10"]["delay"][0] == pytest.approx(-100.0 * (1.04 / 1.01 - 1.0), abs=0.3)     # 3e slower: negative
    assert len(ex["cf_vs_p333"]) == 3 and len(ex["vs_os1_15_10"]["cf"]) == 3


def test_transfer_3e_rules_outside_the_universe_are_listed():
    T, c = universe_world()
    for cond in ("X", "S"):
        for n, f in (("3ex1", 1.03), ("3ex2", 1.01)):
            T[(cond, n)] = {s: dict(v, all_delay=v["all_delay"] * f) for s, v in T[(cond, "p333")].items()}
    c["opponents"] = {"X": c["opponents"]["X"] + ["3ex1", "3ex2"]}
    f = r6.read(T, c)["cells"]["X"]["t2_counting_filter"]
    tr = f["transfer_3e"]
    assert "3ex1" not in f["universe"] and tr["names"] == ["3ex1", "3ex2"]
    assert tr["delay_vs_p333"]["3ex1"][0] == pytest.approx(-3.0, abs=0.3) and len(tr["delay_vs_p333"]["3ex2"]) == 3
    assert tr["counted_if_included"] == sorted(f["counted"] + ["3ex2"]) and tr["policies_if_included"] == 5


def test_coverage_counting_threshold_and_policies_against_the_counted_set():
    """Coverage: lr at +1.5 % counts, 3e at +2.5 % does not; slow (+3 %, far less close-following) would block every learner."""
    T = with_report_keys(world(opp_delay={"lr": 0.015, "3e": 0.025}))
    for cond in ("X", "S"):
        T[(cond, "slow")] = {s: dict(v, all_delay=v["all_delay"] * 1.03, ttc_net=v["ttc_net"] * 0.7) for s, v in T[(cond, "p333")].items()}
    c = cfg() | {"opponents": {"X": OPP + ["slow"]}, "forms": {"X": ["p333", "lr", "slow"]}}
    f = r6.read(T, c)["cells"]["X"]["t2_counting_filter"]
    assert f["universe"] == ["p333", "lr", "slow", "3e"] and f["counted"] == ["lr", "p333"] and f["policies"] == 5


def test_coverage_braking_clause_names_the_lowest_upper_bound():
    """Coverage: the lowest point, lower bound and upper bound sit on different opponents."""
    comps = {"a": (5.0, 1.0, 20.0), "b": (3.0, -8.0, 10.0), "c": (-2.0, -1.0, 15.0), "d": (1.0, 0.0, 4.0)}
    b = r6.braking_clause({o: {"brake_excess": x} for o, x in comps.items()})
    assert b["largest_point_excess"]["opponent"] == "a" and b["lowest_upper_bound"]["opponent"] == "d"
    one = r6.braking_clause({"a": {"brake_excess": (5.0, 1.0, 2.0)}, "b": {"brake_excess": (1.0, 0.0, 9.0)}})
    assert one["largest_point_excess"]["opponent"] == "a" and one["lowest_upper_bound"] is None


def test_coverage_no_control_null_effect_in_s():
    """Coverage."""
    T = with_report_keys(world())
    for cond in ("X", "S"):
        for n in ("nc", "p333"):
            for v in T[(cond, n)].values():
                v["b45_step"] = 0.0
    S = r6.read(T, cfg())["S"]
    assert S["map_report_only"]["nc"]["b45_step"]["effect"] is None
    assert S["map_report_only"]["p333"]["b45_step"]["effect"] == S["map"]["p333"]["b45_step"]["effect"]


def test_coverage_main_takes_the_universe_from_the_forms_file(tmp_path, monkeypatch):
    """Coverage: main() wires --forms through check_forms; the picks file's delay opponent dly stays out."""
    conf = main_world(tmp_path, monkeypatch)
    p, f = picks_files(tmp_path)
    out = tmp_path / "o.json"
    assert r6.main(["rows", conf, str(out), "--seeds", f"0-{N - 1}", "--picks", p, "--forms", f]) == 0
    assert json.loads(out.read_text())["cells"]["X"]["t2_counting_filter"]["universe"] == ["p333", "lr", "3e", "3E-C_X", "3E-D_X"]


def test_coverage_main_refuses_mismatched_inputs(tmp_path, monkeypatch):
    """Coverage: picks from another run, --forms without --picks, and forms that do not cover the re-picks both ways."""
    conf = main_world(tmp_path, monkeypatch)
    o, sd = str(tmp_path / "o.json"), ["--seeds", f"0-{N - 1}"]
    p, f = picks_files(tmp_path, commit_p="c9")
    with pytest.raises(SystemExit):
        r6.main(["rows", conf, o, *sd, "--picks", p])
    p, f = picks_files(tmp_path)
    with pytest.raises(SystemExit):
        r6.main(["rows", conf, o, *sd, "--forms", f])
    rep = json.loads(Path(f).read_text())
    picks = json.loads(Path(p).read_text())
    with pytest.raises(SystemExit):     # the picks file holds a re-pick the forms file lacks
        r6.check_forms(rep | {"code": {"commit": "c0"}}, picks | {"repicks": {"X": {"lr": {}, "p333": {}, "dly": {}, "extra": {}}}}, ["X"])
    rep["picks"]["X"]["front_row"] = "fr"
    with pytest.raises(SystemExit):     # the front row must be among the re-picks too
        r6.check_forms(rep, picks, ["X"])
    assert r6.check_forms(rep, picks | {"repicks": {"X": {"lr": {}, "p333": {}, "dly": {}, "fr": {}}}}, ["X"]) == {"X": ["p333", "lr"]}


def v1_clean() -> tuple:
    """A v1-shaped output with no NaN, and its v2 copy."""
    a = {"study": "NULL", "cells": {"X": {"outcome": "W", "harm": {"delay": []}, "learner_signs": {"w0": True}, "pr28": None,
                                          "t2_counting_filter": {"counted": ["p333"], "policies": 5},
                                          "resilience": {"per_opponent": {"p333": {"R": [1.0, 0.5, 2.0], "pct_of_nc_loss": 44.0,
                                                                                   "null_false_better": 0.01, "null_ok": 1.0}}},
                                          "map": {"p333": {m: {"effect": 1.0, "ci95": [0.0, 2.0], "ci_m": [-0.5, 2.5]} for m in read6_regress.V1_MEASURES}},
                                          "z": 0.0}},
         "S": {"map": {}}}
    b = json.loads(json.dumps(a))
    b["cells"]["X"] |= {"t2_counting_filter": {"universe": ["p333"], "counted": ["p333"], "policies": 5, "v1_value": {"counted": ["p333"], "policies": 5}},
                        "map_report_only": json.loads(json.dumps(a["cells"]["X"]["map"])), "closest": {}, "pr28": {"share": 0.1}}
    b["S"]["map_report_only"] = {}
    return a, b


def gate(edit) -> list:
    a, b = v1_clean()
    edit(a, b)
    return read6_regress.diff(a, b)


X = lambda b: b["cells"]["X"]
P333 = lambda b: X(b)["resilience"]["per_opponent"]["p333"]


def test_gate_pr28_none_in_v1_must_still_be_present():
    d = gate(lambda a, b: X(b).pop("pr28"))
    assert d == ["cells.X.pr28: missing in v2"]


def test_gate_a_hidden_r_must_carry_the_label():
    def hide(r, pct):
        def edit(a, b):
            P333(a)["null_ok"] = P333(b)["null_ok"] = 0.0
            P333(b)["pct_of_nc_loss"] = pct
            if r is ...:
                P333(b).pop("R")
            else:
                P333(b)["R"] = r
        return edit
    assert gate(hide(read6_regress.FAILED, None)) == []
    assert [x.split(":")[0] for x in gate(hide(None, None))] == ["cells.X.resilience.per_opponent.p333.R"]
    assert [x.split(":")[0] for x in gate(hide(..., None))] == ["cells.X.resilience.per_opponent.p333.R"]
    assert [x.split(":")[0] for x in gate(hide(read6_regress.FAILED, 12.0))] == ["cells.X.resilience.per_opponent.p333.pct_of_nc_loss"]


def test_gate_map_repeats_follows_the_float_rules():
    def put(m, r):
        def edit(a, b):
            X(a)["map"]["p333"]["delay"]["effect"] = X(b)["map"]["p333"]["delay"]["effect"] = m
            X(b)["map_report_only"]["p333"]["delay"]["effect"] = r
        return edit
    assert gate(put(float("nan"), float("nan"))) == []
    assert [x.split(":")[0] for x in gate(put(-0.0, 0.0))] == ["cells.X.map_report_only.p333.delay.effect"]


def test_gate_map_repeats_reports_a_missing_entry():
    def edit(a, b):
        for m in read6_regress.V1_MEASURES:
            X(a)["map"]["p333"][m] = X(b)["map"]["p333"][m] = {"effect": None, "ci95": None, "ci_m": None}
        X(b)["map_report_only"].pop("p333")
    assert [x.split(":")[0] for x in gate(edit)] == [f"cells.X.map_report_only.p333.{m}" for m in read6_regress.V1_MEASURES]


def test_gate_unread_blocks_carry_no_verdict():
    def edit(a, b):
        X(b)["cf_resilience"] = {"per_opponent": {}, "status": "report-only, not read", "passes": True}
    assert [x.split(":")[0] for x in gate(edit)] == ["cells.X.cf_resilience.passes"]
    assert gate(lambda a, b: X(b).update(cf_resilience={"per_opponent": {}, "status": "report-only, not read"})) == []


def test_gate_allows_the_space_time_record():
    assert gate(lambda a, b: b.update(space_time={"dir": "st", "files": 2, "sha256": "x"})) == []


def test_coverage_gate_reports_each_kind_of_change():
    """Coverage: each planted change is reported once, at its own path, on a fixture with no NaN (the v2.1 test's NaN hid these
    from its fails-on-f84c9dc log)."""
    cases = {
        "cells.X.outcome": lambda a, b: X(b).pop("outcome"),
        "cells.X.harm": lambda a, b: X(b).update(harm=1),
        "cells.X.learner_signs.w0": lambda a, b: X(b)["learner_signs"].update(w0=1.0),
        "cells.X.z": lambda a, b: X(b).update(z=0),
        "cells.X.harm.delay": lambda a, b: X(b)["harm"].update(delay=["x"]),
        "cells.X.t2_counting_filter.v1_value": lambda a, b: X(b)["t2_counting_filter"].pop("v1_value"),
        "cells.X.pr28.share": lambda a, b: (X(a).update(pr28={"share": 0.1}), X(b).update(pr28={"share": 0.2})),
        "cells.X.harm.new": lambda a, b: X(b)["harm"].update(new=1),
        "cells.X.closest_x": lambda a, b: X(b).update(closest_x=1),
        "cells.X.resilience.per_opponent.p333.null_ok": lambda a, b: (P333(b).update(null_ok=0.0, R=read6_regress.FAILED, pct_of_nc_loss=None)),
        "cells.X.resilience.per_opponent.p333.R": lambda a, b: P333(b).update(R=read6_regress.FAILED),     # hidden while its null passed
        "cells.X.map_report_only.p333.flow.effect": lambda a, b: X(b)["map_report_only"]["p333"]["flow"].update(effect=1.5),
        "cells.X.harm.extra": lambda a, b: X(b)["harm"].update(extra=["delay"]),
        "cells.X.learner_signs.w9": lambda a, b: X(b)["learner_signs"].update(w9=False),
        "cells.X.k_policies": lambda a, b: X(b).update(k_policies=5),
        "cells.X.t2_counting_filter.v1_value.policies": lambda a, b: X(b)["t2_counting_filter"]["v1_value"].update(policies=4),
        "cells.X.z ": lambda a, b: X(b).update(z=-0.0),
        "extra": lambda a, b: b.update(extra=1),
    }
    assert gate(lambda a, b: None) == []
    for path, edit in cases.items():
        d = gate(edit)
        assert len(d) == 1 and d[0].split(":")[0] == path.strip(), (path, d)
    d = gate(lambda a, b: (P333(a).update(null_ok=0.0), P333(b).update(null_ok=0.0, R=[1.0, 0.4, 2.0])))
    assert [x.split(":")[0] for x in d] == ["cells.X.resilience.per_opponent.p333.R[1]"]     # both nulls failed: a changed number is reported


def test_an_empty_side_file_reads_as_none_and_is_listed(tmp_path):
    """Amendment 4a: the S6 host's outage left the last 14 TRUCK side files empty (V494). Written before the fix; fails on d14307f."""
    (tmp_path / "e.npz").write_bytes(b"")
    d = r6.derive(st_row(f="e.npz"), tmp_path)
    assert all(d[k] is None for k in JAM) and d["st_empty"] and d["st_sha256"] == hashlib.sha256(b"").hexdigest()
    (tmp_path / "bad.npz").write_bytes(b"PK\x03\x04 truncated")
    with pytest.raises(Exception):     # anything but an empty file still stops the reading
        r6.derive(st_row(f="bad.npz"), tmp_path)
    T = jam_world()
    for s in (0, 1, 2):
        T[("X", "lr")][s] |= {k: None for k in JAM} | {"st_empty": True, "st_file": f"lr{s}.npz", "st_sha256": "0"}
    res = r6.read(T, cfg() | {"st_dir": "st"})
    e = res["cells"]["X"]["map_report_only"]["lr"]["jam_share"]
    assert e["effect"] is None and e["none_seeds"] == 3 and e["why"] == r6.EMPTY_ST
    assert res["cells"]["X"]["map_report_only"]["p333"]["jam_share"]["effect"] == pytest.approx(10.0, abs=1.0)
    assert res["space_time"]["empty_files"] == ["lr0.npz", "lr1.npz", "lr2.npz"]
