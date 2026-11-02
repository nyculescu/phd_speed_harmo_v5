"""B training environment (V263): spaces and seeds; the live behaviour is checked by `b_train smoke`."""
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
