"""Plan B's S6 runner (planb.md §7.4, §8.3): attempts, crash drops, a native crash, the bug stop, resume, file checks, and the chain
plan6 jobs -> run6 rows -> read6 on fake rows. Fake runs are module-level functions so spawned workers can import them."""
import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "docs/research/planb"))
import pb  # noqa: E402
import run6  # noqa: E402


def fake_row(a: tuple) -> dict:
    """A run_one-shaped row with every key read6 needs; values depend on the arm and seed only."""
    name, cfg, q, seed, rd, commit = a
    rng = np.random.default_rng(int(hashlib.sha256(name.encode()).hexdigest()[:8], 16) + seed)
    return {"name": name, "q": q, "seed": seed, "all_delay": 100000.0 * (1 + rng.normal(0, 0.01)), "ttc_net": 1000.0 * (1 + rng.normal(0, 0.02)),
            "passed": 3000.0, "collisions": 0, "alks_full_moving": 0.0, "N": 200000.0, "b3_step": 100.0, "b45_step": 10.0, "end_stop2": 1.0,
            "m_peak_car": [0, 0, 1] + [0] * 6, "m_peak_alks": [0] * 9, "m_peak_truck": [0] * 9, "m_dist_m_car": 1e6, "m_dist_m_alks": 1e6,
            "m_dist_m_truck": 1e5, "m_stuck_n": 0, "m_pending_end": 1, "m_road_vs": {"3": {"rest": 10.0}}, "m_road_dist": {"3": {"rest": 100.0}},
            "m_road_ttc3": {}, "m_robust_road": {}, "pert_log": [],
            **{k: 1.0 for k in ("ttc2", "ttc15", "sev3", "gap25", "delay_ramp", "delay_ramp2", "m_cong_vs", "m_cong_run_s", "m_cong_vs_nc",
                                "m_cong_run_s_nc", "contact_steps")}, "m_ttc3_lc": 0, "m_ttc3_all": 0}     # read6 v2's report fields


def ok(a: tuple) -> dict:
    return run6.wrap(fake_row(a), a)


def raises(a: tuple) -> dict:
    if a[0] == "S|bad":
        raise ValueError("planted crash")
    return ok(a)


def raises_one(a: tuple) -> dict:
    if a[0] == "S|bad" and a[3] == 1:
        raise ValueError("planted crash")
    return ok(a)


def dies(a: tuple) -> dict:
    if a[0] == "S|bad" and a[3] == 1:
        os._exit(1)     # a native crash: the worker process vanishes
    return ok(a)


def flaky(a: tuple) -> dict:
    mark = Path(a[4]).parent / f"tried_{a[0].replace('|', '_')}_{a[3]}"
    if a[0] == "S|bad" and not mark.exists():
        mark.parent.mkdir(parents=True, exist_ok=True)
        mark.touch()
        raise ValueError("first attempt only")
    return ok(a)


def arms(n_extra: int = 4) -> dict:
    out = {"S|bad": {"ctrl": {}}}
    out |= {f"S|a{i}": {"ctrl": {"cav_rule": [i, i, i]}} for i in range(n_extra)}
    out |= {f"SURGE|a{i}": {"ctrl": {"cav_rule": [i, i, i]}} for i in range(n_extra)}
    return out


def rows(out: Path) -> dict:
    return {(r["name"], r["seed"]): r for r in pb.cma2.load(out / "s6_rows.jsonl")}


def test_a_python_crash_on_one_seed_drops_that_seed_after_three_attempts(tmp_path):
    out = tmp_path / "one"
    assert run6.execute(arms(), list(range(6)), out, 4, {"t": 1}, fn=raises_one, strict=False) == {"S": [1]}
    assert json.loads((out / "attempts.json").read_text()) == {"S|bad 1": 3} and len(rows(out)) == 9 * 6 - 1


def test_an_arm_crashing_on_many_seeds_stops_the_run(tmp_path):
    out = tmp_path / "all"
    with pytest.raises(SystemExit):     # a bug to fix (planb.md §11), not seeds to drop
        run6.execute(arms(), list(range(6)), out, 4, {"t": 1}, fn=raises, strict=False)
    att = json.loads((out / "attempts.json").read_text())
    assert all(att[f"S|bad {s}"] == 3 for s in range(6)) and not (out / "drops.json").exists()


def test_a_native_crash_is_charged_to_its_own_run_only(tmp_path):
    out = tmp_path / "dies"
    drops = run6.execute(arms(), list(range(6)), out, 4, {"t": 1}, fn=dies, strict=False)
    assert drops == {"S": [1]}     # only the seed whose own run died, after 3 attempts
    att = json.loads((out / "attempts.json").read_text())
    assert att == {"S|bad 1": 3}
    assert len(rows(out)) == 9 * 6 - 1


def test_resume_reruns_nothing_and_a_transient_failure_recovers(tmp_path):
    out = tmp_path / "flaky"
    assert run6.execute(arms(2), [0, 1], out, 2, {"t": 1}, fn=flaky, strict=False) == {}
    n = len(pb.cma2.load(out / "s6_rows.jsonl"))
    assert n == 5 * 2 and json.loads((out / "attempts.json").read_text()) == {"S|bad 0": 1, "S|bad 1": 1}
    assert run6.execute(arms(2), [0, 1], out, 2, {"t": 1}, fn=raises, strict=False) == {}     # nothing left to run
    assert len(pb.cma2.load(out / "s6_rows.jsonl")) == n
    with pytest.raises(SystemExit):
        run6.execute(arms(3), [0, 1], out, 2, {"t": 1}, fn=ok, strict=False)     # other jobs: refused


def test_rows_carry_identity_and_the_cell_spec(tmp_path):
    a = ("TRUCK|w0u250", {"ctrl": {"pt": str(tmp_path / "p.pt"), "env": {"perturb": {"kind": "truck_fixed"}}}, "measure": "/x"}, 5300.0, 7, "/rd", "c0")
    (tmp_path / "p.pt").write_bytes(b"w")
    r = ok(a)
    assert r["cell"] == "TRUCK" and r["arm"] == r["learner"] == "w0u250" and r["commit"] == "c0" and r["cell_spec"] == {"kind": "truck_fixed"}
    assert "measure" not in r["cfg"] and r["ctrl_sha256"] == pb.sha(r["cfg"]) and r["files"] == {str(tmp_path / "p.pt"): hashlib.sha256(b"w").hexdigest()}


def test_checkpoints_and_files_are_checked_before_any_run(tmp_path, monkeypatch):
    pt = tmp_path / "C0_u250.pt"
    pt.write_bytes(b"policy")
    sums = tmp_path / "SHA256SUMS"
    sums.write_text(f"{hashlib.sha256(b'policy').hexdigest()}  C0_u250.pt\n")
    monkeypatch.setattr(run6, "SUMS", sums)
    A = {"S|w0u250": {"ctrl": {"pt": str(pt)}}}
    assert run6.check_checkpoints(A) == {str(pt): hashlib.sha256(b"policy").hexdigest()}
    sums.write_text("0" * 64 + "  C0_u250.pt\n")
    with pytest.raises(SystemExit):
        run6.check_checkpoints(A)
    model = tmp_path / "m.pt"
    model.write_bytes(b"model")
    good = {"S|MPC-F": {"ctrl": {"mpcf": {"actions": [], "model": str(model), "model_sha256": hashlib.sha256(b"model").hexdigest()}}}}
    run6.check_files(good)
    with pytest.raises(SystemExit):
        run6.check_files({"S|MPC-F": {"ctrl": {"mpcf": {"actions": [], "model": str(model), "model_sha256": "0" * 64}}}})
    with pytest.raises(SystemExit):
        run6.check_files({"S|x": {"ctrl": {"pt": str(tmp_path / "missing.pt")}}})


@pytest.mark.skipif(not pb.JOB.exists(), reason="round 2's job file is not on this machine")
def test_plan6_jobs_to_run6_rows_to_read6(tmp_path):
    import read6
    from test_planb_opp import plan6_world
    plan6, s2, repick, asch_res, mpcf_res = plan6_world(tmp_path)
    P = plan6.freeze(s2, repick, tmp_path, asch_res, mpcf_res, tmp_path, strict=False)
    out = tmp_path / "jobs"
    out.mkdir()
    J, conf = plan6.jobs(P, out)
    conf["null_swaps"] = 20
    f = tmp_path / "rows.jsonl"
    with f.open("w") as w:
        for n, c in J.items():
            for s in run6.SMOKE:
                w.write(json.dumps(ok((n, c, pb.Q, s, "/rd", "c0"))) + "\n")
    res = read6.read(read6.load_rows(f, conf, run6.SMOKE), conf, {}, run6.SMOKE)
    assert set(res["cells"]) == {"SURGE", "TRUCK"} and all(c["n_seeds"] == 3 for c in res["cells"].values())
    assert "G4(ii)" in res["must_carry"] and res["must_carry"] == conf["must_carry"]     # the reading cannot lose the deviation
    assert set(res["S"]["map"]) == set(read6.expected(conf)["S"]) - set(pb.V3W) - {"nc"}
