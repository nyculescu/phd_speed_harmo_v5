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
