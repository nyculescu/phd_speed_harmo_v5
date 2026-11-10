"""read6 v2 (read6_v2_spec.md, V497): report-only additions on planted rows. Written before the fix; each test but the regression
test fails on v1 (b0c9360)."""
import importlib.util
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import test_planb_read6 as t1  # noqa: E402
from test_planb_read6 import LEARN, N, OPP, cfg, r6, world  # noqa: E402

V1_COMMIT = "b0c9360"
NEW = ("events_ge45", "ttc2", "ttc15", "sev3", "gap25", "delay_ramp", "delay_ramp2", "m_cong_vs", "m_cong_run_s", "m_cong_vs_nc",
       "m_cong_run_s_nc", "contact_steps", "robust_raw", "robust_per_served", "ttc3_lc_share")


def with_report_keys(T: dict) -> dict:
    """Adds the §5 report-only values to planted rows; v3w is 10 % lower on each, gap25 is 0 for every opponent."""
    rng = np.random.default_rng(3)
    for (cond, name), rows in T.items():
        for s, b in rows.items():
            f = 0.9 if name in LEARN else 1.0
            for k in NEW:
                b[k] = 100.0 * f * (1 + rng.normal(0, 0.01))
            b["gap25"] = 0.0 if name not in LEARN else 1.0
    return T


PICKS = {"repicks": {"X": {"lr": {"local_rule": {}}, "p333": {"cav_rule": [3, 3, 3]}}},
         "tuned": {"3E-C_X": {"label": "not converged at 100 generations", "generations": 100, "cell": "X", "ctrl": {}}},
         "steady": {"name": "steady_lr", "ctrl": {}}, "asch": {"local_rule": {}}, "mpcf": None, "omitted": {}}


def conf(**kw):
    return cfg() | {"picks": PICKS} | kw


def test_forms_resolve_to_grid_names_then_carried_twins():
    assert r6.cell_forms(PICKS, ["p333", "lr", "3e"], "X") == ["lr", "p333"]
    assert r6.cell_forms(PICKS, ["p333", "grid_lr", "lr", "3e"], "X") == ["grid_lr", "p333"]
    with pytest.raises(SystemExit):
        r6.cell_forms(PICKS, ["3e"], "X")


def test_counting_filter_applies_round_2s_universe():
    T = with_report_keys(world())
    T[("X", "carried")] = {s: dict(v) for s, v in T[("X", "p333")].items()}
    T[("S", "carried")] = {s: dict(v) for s, v in T[("S", "p333")].items()}
    c = r6.read(T, conf(opponents={"X": OPP + ["carried"]}))["cells"]["X"]
    f = c["t2_counting_filter"]
    assert f["universe"] == ["p333", "lr", "3e"] and "carried" not in f["counted"]
    assert "carried" in f["v1_value"]["counted"]


def test_null_outcome_reports_resilience_report_only():
    c = r6.read(with_report_keys(world(delay=(0.0,) * 5, cf=(0.0,) * 5)), conf())["cells"]["X"]
    assert c["outcome"] == "T"
    for k in ("resilience", "cf_resilience"):
        assert c[k]["status"].startswith("report-only, not read") and set(c[k]["per_opponent"]) == set(OPP)


def test_w_cell_keeps_delay_r_read_and_cf_resilience_report_only():
    loss = lambda name, s: 5000.0 if name in LEARN else 9000.0
    c = r6.read(with_report_keys(world(s_loss=loss)), conf())["cells"]["X"]
    assert c["outcome"] == "W" and c["resilience"]["passes"] and c["resilience"]["status"] == "read"
    assert c["cf_resilience"]["status"].startswith("report-only")


def test_r_value_hidden_when_its_null_fails(monkeypatch):
    calls = []

    def later(*a, **k):
        calls.append(1)
        return 0.0 if len(calls) <= 2 else 0.5
    monkeypatch.setattr(r6, "swap_null", later)
    loss = lambda name, s: 5000.0 if name in LEARN else 9000.0
    c = r6.read(with_report_keys(world(s_loss=loss)), conf())["cells"]["X"]
    assert c["outcome"] == "W"
    assert all(v["R"] == "statistic failed its null" and v["null_false_better"] == 0.5 for v in c["resilience"]["per_opponent"].values())


def test_map_report_only_has_no_control_and_section_5():
    T = with_report_keys(world())
    T[("X", "w0")][4]["delay_ramp"] = None
    res = r6.read(T, conf())
    c = res["cells"]["X"]
    m = c["map_report_only"]
    assert set(m) == set(OPP) | {"nc"}
    assert set(m["nc"]) >= set(NEW) | {"delay", "cf", "flow", "robust_braking", "collisions", "alks_full_moving"}
    for o in OPP:
        for meas in ("delay", "cf", "flow", "robust_braking", "alks_past_limit", "b45_step", "b3_step", "ttt"):
            assert m[o][meas]["effect"] == c["map"][o][meas]["effect"] and list(m[o][meas]["ci95"]) == list(c["map"][o][meas]["ci95"])
    assert m["p333"]["ttc2"]["effect"] == pytest.approx(10.0, abs=1.0)
    assert m["p333"]["gap25"]["effect"] is None and m["p333"]["gap25"]["mean_diff"][0] == pytest.approx(1.0)
    assert m["p333"]["delay_ramp"]["effect"] is None and m["p333"]["delay_ramp"]["none_seeds"] == 1
    assert set(res["S"]["map_report_only"]) == set(OPP) | {"nc"}


def test_null_sentence_fields_in_every_outcome():
    c = r6.read(with_report_keys(world(delay=(0.0,) * 5, cf=(0.0,) * 5)), conf())["cells"]["X"]
    assert set(c["closest"]) == {"delay", "cf", "flow"} and set(c["d4"]) == {"delay", "cf"}
    assert c["braking_clause"]["largest_point_excess"]["opponent"] in OPP and c["pr28"]["opponent"] == c["closest"]["delay"]
    assert "k_policies" not in c


def test_provenance_from_the_picks():
    res = r6.read(with_report_keys(world()), conf())
    p = res["provenance"]
    assert p["plateau"]["3E-C_X"] == {"label": "not converged at 100 generations", "generations": 100}
    assert p["breakdown"]["X"]["fixed"] == ["p333"] and p["breakdown"]["X"]["distilled"] == []
    assert p["breakdown"]["X"]["repick_equal_to_carried"] == ["lr", "p333"]


def test_derive_adds_report_keys_strictly():
    row = t1.pack_row("X|w0", 0) | {k: 1.0 for k in ("ttc2", "ttc15", "sev3", "gap25", "delay_ramp", "delay_ramp2", "m_cong_vs", "m_cong_run_s",
                                                     "m_cong_vs_nc", "m_cong_run_s_nc", "contact_steps")} | {"m_ttc3_lc": 3, "m_ttc3_all": 12}
    d = r6.derive(row)
    assert d["events_ge45"] == 2 + 1 + 0 + (0 + 2 + 1 + 0 + 1 + 5) + 0
    assert d["robust_raw"] == 6 + 10 + 3 and d["robust_per_served"] == pytest.approx(19 / 3.0) and d["ttc3_lc_share"] == 0.25
    del row["delay_ramp"]     # not a counter field: absent stops the reading
    with pytest.raises((KeyError, SystemExit)):
        r6.derive(row)


def test_counter_fields_absent_read_as_zero():
    """plant_sweep's defaultdict S writes ttc2, ttc15 and sev3 only on their first hit (plant_sweep.py:111, :194-198, :341)."""
    row = t1.pack_row("X|w0", 0)
    for k in ("ttc2", "ttc15", "sev3"):
        del row[k]
    d = r6.derive(row)
    assert d["ttc2"] == d["ttc15"] == d["sev3"] == 0.0 and d["absent_zero"] == ["ttc2", "ttc15", "sev3"]
    assert r6.derive(t1.pack_row("X|w0", 0))["absent_zero"] == []


def test_defaults_hit_are_counted(tmp_path):
    row = t1.pack_row("X|w0", 0) | {k: 1.0 for k in ("ttc2", "ttc15", "sev3", "gap25", "delay_ramp", "delay_ramp2", "m_cong_vs", "m_cong_run_s",
                                                     "m_cong_vs_nc", "m_cong_run_s_nc", "contact_steps")} | {"m_ttc3_lc": 3, "m_ttc3_all": 12}
    del row["alks_full_moving"]
    assert r6.derive(row)["defaults"] == ["alks_full_moving"]


def v1_module(tmp_path):
    root = HERE.parent
    try:
        src = subprocess.run(["git", "-C", str(root), "show", f"{V1_COMMIT}:docs/research/planb/read6.py"], capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("v1 source not available")
    p = tmp_path / "read6_v1.py"
    p.write_text(src)
    spec = importlib.util.spec_from_file_location("read6_v1", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize("kw", [{}, {"delay": (0.0,) * 5, "cf": (0.0,) * 5}, {"delay": (0.05,) * 5, "cf": (0.0,) * 5}])
def test_v1_fields_unchanged(tmp_path, kw):
    v1 = v1_module(tmp_path)
    T = with_report_keys(world(**kw))
    a, b = v1.read(T, cfg()), r6.read(T, conf())
    sys.path.insert(0, str(HERE.parent / "docs/research/planb"))
    import read6_regress
    assert read6_regress.diff(a, b) == []
