"""B training environment (V263): spaces and seeds; the live behaviour is checked by `b_train smoke`."""
import numpy as np
import pytest

from v5b.fleet import b_env as be, b_train as bt


def test_spaces_and_seed_layout():
    env = be.MergeEnv(run_dir="/tmp")
    assert env.action_space.nvec.tolist() == [len(be.OFFSETS_KMH)] * be.K
    assert env.observation_space.shape == (be.R * 3 + be.K * 5 + 4,)
    top = be.SEED0 + 23 * be.SEEDS_PER_WORKER + be.SEEDS_PER_WORKER - 1
    assert top < bt.VAL_SEEDS[0] < 7_420_000


def test_worker_runs_out_of_seeds_instead_of_leaving_its_range():
    env = be.MergeEnv(run_dir="/tmp")
    env.n_ep = be.SEEDS_PER_WORKER
    with pytest.raises(ValueError, match="training seeds"):
        env.reset()


def test_shared_agent_has_one_action_and_starts_on_fresh_seeds():
    c = bt.CFG[2]
    env = be.MergeEnv(run_dir="/tmp", n_ep0=c["nep0"], **c["env"])
    assert env.action_space.n == len(be.SHARED_OFFSETS_KMH)
    assert env.n_ep == c["nep0"]
    assert c["nep0"] + 500 * c["steps"] / 8 / 150 <= be.SEEDS_PER_WORKER


def test_efficiency_reward_rewards_flow_and_speed_and_charges_only_excess_exposure():
    env = be.MergeEnv(run_dir="/tmp", reward="efficiency")
    env.q = 4090.0
    b3, e30, n = be.REF_LEVEL[env.q]
    env.ema_b3, env.ema_e30 = b3, e30
    base = env._efficiency(1, 25.0, int(n), 0, 0)
    env.ema_b3, env.ema_e30 = b3, e30
    assert env._efficiency(2, 25.0, int(n), 0, 0) > base
    env.ema_b3, env.ema_e30 = b3, e30
    assert env._efficiency(1, 27.0, int(n), 0, 0) > base
    env.ema_b3, env.ema_e30 = b3, e30
    assert env._efficiency(1, 25.0, int(n), 60, 0) < base
    env.ema_b3, env.ema_e30 = 0.0, 0.0
    assert env._efficiency(1, 25.0, int(n), 0, 0) == pytest.approx(base)


def test_zone_agent_spaces_and_seeds_stay_outside_training():
    env = be.make(zones=True, run_dir="/tmp", decision=10.0)
    assert env.action_space.nvec.tolist() == [len(be.HEADWAYS_S)] * be.N_ZONES
    assert env.observation_space.shape == (be.R * 3 + be.K * 4 + be.N_ZONES * 4 + 3,)
    assert min(bt.CFG[6]["seeds"]) > 7_419_902 and max(bt.CFG[6]["seeds"]) < 7_420_000
    assert len(bt.ZONE_ARMS) == 12 and (1, 0, 0) in bt.ZONE_ARMS and (3, 3, 3) in bt.ZONE_ARMS


class _T:
    t = 0.0


def _limited_env():
    env = be.make(zones=True, run_dir="/tmp", decision=10.0)
    env.sim = _T()
    env.ep = {"changes": 0, "reversals": 0, "ignored": 0}
    return env


def test_zone_target_moves_one_level_per_hold_and_ignores_the_rest():
    env = _limited_env()
    env._apply((3, 0, 0))
    assert env.target.tolist() == [1, 0, 0]
    for t in (10.0, 50.0):
        env.sim.t = t
        env._apply((3, 0, 0))
    assert env.target.tolist() == [1, 0, 0] and env.ep["ignored"] == 2
    env.sim.t = 60.0
    env._apply((3, 0, 0))
    assert env.target.tolist() == [2, 0, 0] and env.ep["changes"] == 2 and env.ep["reversals"] == 0


def test_up_down_requests_cannot_flip_faster_than_the_hold():
    env = _limited_env()
    seen = []
    for i in range(12):
        env.sim.t = 10.0 * i
        env._apply((3 if i % 2 else 0, 0, 0))
        seen.append(int(env.target[0]))
    assert env.ep["changes"] <= 2
    assert all(abs(a - b) <= 1 for a, b in zip(seen, seen[1:]))


def test_zone_headway_list_and_change_cost_are_options():
    env = be.make(zones=True, run_dir="/tmp", headways=(1.6, 1.4, 1.2), w_change=0.1, ref_delay=True)
    assert env.action_space.nvec.tolist() == [3] * be.N_ZONES
    assert env.ref is be.REF_DELAY and env.w_change == 0.1


def test_zone_rule_uses_hysteresis_and_leaves_the_other_zones_alone():
    rule = be.ZoneRule(level=2, on=0.6, zones=(be.ZONE_UP, be.ZONE_DOWN))
    o = np.ones(be.R * 3 + be.K * 4 + be.N_ZONES * 4 + 3)
    i = be.R * 3 + be.K * 4 + be.ZONE_MERGE * 4
    assert rule(o).tolist() == [0, 0, 0]
    o[i] = 0.5
    assert rule(o).tolist() == [2, 0, 2]
    o[i] = 0.65
    assert rule(o).tolist() == [2, 0, 2]
    o[i] = 0.75
    assert rule(o).tolist() == [0, 0, 0]


def test_one_contact_counts_once_however_long_it_lasts(monkeypatch):
    env = be.MergeEnv(run_dir="/tmp")

    class Sim:
        def step(self):
            pass

    class C:
        collider, victim = "a", "b"
    env.sim = Sim()
    env.contact = set()
    env.ep = {"collisions": 0, "contact_steps": 0}
    monkeypatch.setattr(be.ls.simulation, "getCollisions", lambda: [C()])
    for _ in range(5):
        env._sim_step()
    assert env.ep == {"collisions": 1, "contact_steps": 5}


def test_a_stopped_queue_is_not_a_short_gap(monkeypatch):
    env = be.MergeEnv(run_dir="/tmp")
    env.ep = {"gap25": 0, "stop_gap": 0}
    speed = {"f": 0.0, "l": 0.0}
    monkeypatch.setattr(be.ls.vehicle, "getIDList", lambda: ["f"])
    monkeypatch.setattr(be.ls.vehicle, "getAcceleration", lambda v: 0.0)
    monkeypatch.setattr(be.ls.vehicle, "getLeader", lambda v, d: ("l", -0.1))
    monkeypatch.setattr(be.ls.vehicle, "getMinGap", lambda v: 2.5)
    monkeypatch.setattr(be.ls.vehicle, "getSpeed", lambda v: speed[v])
    env._net_stats()
    assert env.ep == {"gap25": 0, "stop_gap": 1}
    speed["f"] = 10.0
    env._net_stats()
    assert env.ep == {"gap25": 1, "stop_gap": 1}


def _cav():
    env = be.CavEnv(run_dir="/tmp")
    env.sim = type("S", (), {"t": 400.0})()
    env.ep = {"changes": 0, "reversals": 0, "ignored": 0}
    return env


def test_cav_moves_one_level_and_waits_out_the_hold():
    env = _cav()
    env._apply({"a": 3, "b": 0})
    assert env.lvl == {"a": 1} and env.ep["changes"] == 1
    env.sim.t += env.hold - 5.0
    env._apply({"a": 3})
    assert env.lvl["a"] == 1 and env.ep["ignored"] == 1
    env.sim.t += 5.0
    env._apply({"a": 3})
    assert env.lvl["a"] == 2


def test_cav_counts_a_reversal_and_charges_a_move():
    env = _cav()
    env._apply({"a": 1})
    assert env.acc["a"] == pytest.approx(-be.W_MOVE * env.decision)
    env.sim.t += env.hold
    env._apply({"a": 0})
    assert env.ep["reversals"] == 1 and env.lvl["a"] == 0


def test_gae_matches_hand_values_and_bootstraps():
    from v5b.fleet.c_train import gae
    r, v = np.array([1.0, 1.0]), np.array([0.5, 0.5])
    d1 = 1.0 + 0.9 * 2.0 - 0.5
    d0 = 1.0 + 0.9 * 0.5 - 0.5
    assert gae(r, v, 2.0, 0.9, 0.5).tolist() == pytest.approx([d0 + 0.45 * d1, d1])


def test_cav_rule_reads_zone_from_the_observation():
    lo = np.zeros((5, be.CAV_LOCAL), np.float32)
    lo[:, 0] = [-0.5, -0.05, 0.1, 1.0, -0.02]
    lo[4, 2] = 1.0     # on the ramp, before the 3a start
    a = be.CavRule((3, 0, 2))((list("abcde"), lo, None, None))
    assert a == {"a": 3, "b": 0, "c": 0, "d": 2, "e": 3}


def test_cav_shared_reward_has_no_excess_exposure_term():
    env = _cav()
    env.q, env.flow_ema = 4600.0, 4600.0 / 3600.0
    env.ref = be.REF_DELAY
    env.report_net = True     # no simulation here: skips the per-vehicle pass
    n = int(env.ref[4600.0][2])
    env.ema_b3, env.ema_e30 = 100.0, 100.0
    assert env._efficiency(0, be.fl.LIMIT, n, 50, 50) == pytest.approx(-0.0213, abs=0.05)


def test_zone_shared_reward_has_no_excess_or_gap_term():
    env = be.ZoneEnv(run_dir="/tmp", shared_reward=True, ref_delay=True)
    env.q, env.flow_ema = 4600.0, 4600.0 / 3600.0
    n = int(be.REF_DELAY[4600.0][2])
    env.ema_b3, env.ema_e30 = 1e6, 1e6
    r = env._efficiency(1, 25.0, n, 10**6, 10**6)
    assert r == pytest.approx(env.flow_ema / (4600.0 / 3600.0) - 1.0 + 25.0 / be.fl.LIMIT - 1.0 - (n / be.REF_DELAY[4600.0][2] - 1.0))


def test_cav_sizes_cover_lane_and_residual():
    assert be.cav_sizes() == (be.CAV_LOCAL, 4)
    assert be.cav_sizes(lane_action=True) == (be.CAV_LOCAL + 2, 12)
    assert be.cav_sizes(residual=(3, 0, 3)) == (be.CAV_LOCAL, 3)
    assert be.cav_sizes(lane_action=True, residual=(3, 0, 3), hold=10.0) == (be.CAV_LOCAL + 2, 9)


def test_cav_rule_lane_mode_moves_only_due_mainline_alks_upstream():
    lo = np.zeros((4, be.CAV_LOCAL + 2), dtype=np.float32)
    lo[:, 0] = [-1.0, -1.0, 0.1, -1.0]     # km from the merge start
    lo[:, 3] = [0.0, 1.0 / 3.0, 0.0, 0.0]     # lane index / 3
    lo[3, 2] = 1.0     # on the ramp
    a = be.CavRule((0, 0, 0), lane=1)((["a", "b", "c", "d"], lo, None, np.array([True, True, True, True])))
    assert a == {"a": 4, "b": 0, "c": 0, "d": 0}
    a = be.CavRule((0, 0, 0), lane=1)((["a", "b", "c", "d"], lo, None, np.array([False, True, True, True])))
    assert a["a"] == 0
    a = be.CavRule((0, 0, 0), lane=2)((["a", "b", "c", "d"], lo, None, np.array([True, True, True, True])))
    assert a == {"a": 4, "b": 4, "c": 0, "d": 0}


def test_plant_score_is_paired_clipped_and_counts_collisions():
    from v5b.fleet import plant_sweep as ps
    base = {"passed": 100.0, "N": 100.0, "fuel_km": 100.0, "ttc_net": 100.0, "brake_net": 100.0, "b45_net": 100.0, "collisions": 0}
    rows = [{"name": "base", "q": 1.0, "seed": 1, **base}, {"name": "x", "q": 1.0, "seed": 1, **{**base, "passed": 110.0, "N": 10.0, "collisions": 2}}]
    s = ps.score(rows)["x"]
    assert s["flow"] == pytest.approx(10.0)
    assert s["ttt"] == pytest.approx(90.0)
    assert s["S"] == pytest.approx((10.0 + 30.0) / 6.0)
    assert s["collisions"] == 2


def test_plant_settings_reach_the_right_groups():
    from v5b.fleet import plant_sweep as ps
    p = ps.to_plant({"lcSpeedGain": 5, "limit_kmh": 90, "model": "IDM", "sigma_scale": 0.5, "accel_len": 450})
    assert p["lc"] == {"lcSpeedGain": 5} and p["limit"] == pytest.approx(25.0) and p["hdv"] == {"carFollowModel": "IDM"}
    assert p["truck"] == {"sigma": 0.25} and p["sigma_scale"] == 0.5 and p["accel_len"] == 450
    q = ps.to_plant({"smooth": True, "human_undertake": 0.5})
    assert q["smooth"] and q["alks"] == {"lcOvertakeRight": 1} and q["hdv"]["lcOvertakeRight"] == 0.5 == q["truck"]["lcOvertakeRight"]
