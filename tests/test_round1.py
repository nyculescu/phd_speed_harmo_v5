"""Round 1: the new trainer pieces, the event-file checks with planted faults, the collapse rule on baseline-v3's logs, and the readings."""
import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pytest
import torch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "docs/research/round1"))
import common1 as c1  # noqa: E402
import decide1 as dc1  # noqa: E402
import tbcheck1 as tb  # noqa: E402
from v5b.fleet import b_env as be, c_train as ct  # noqa: E402

V3_TRAIN = Path("/home/catalin/work/phd/v5b1_runs/baseline_v3/conf3/train")


def test_combined_advantage():
    ad, adc = torch.tensor([1.0, 2.0, 3.0, 4.0]), torch.tensor([4.0, 1.0, 1.0, 2.0])
    z = lambda x: (x - x.mean()) / (x.std() + 1e-8)
    assert torch.allclose(ct.combined_advantage(ad, None, 5.0), z(ad))
    assert torch.allclose(ct.combined_advantage(ad, adc, 0.0), z(ad))
    assert torch.allclose(ct.combined_advantage(ad, adc, 3.0), (z(ad) - 3.0 * z(adc)) / 4.0)


def test_dual_step():
    cfg = ct.LAGR
    assert ct.dual_step(1.0, [1.0, 1.0], cfg) == pytest.approx((1.03, 1.0))
    assert ct.dual_step(0.01, [0.9], cfg)[0] == 0.0
    assert ct.dual_step(9.99, [2.0], cfg)[0] == cfg["cap"]


def test_residual_start_is_the_rule():
    n_local, n_act = be.cav_sizes(**c1.CANDIDATES["res"])
    assert (n_local, n_act) == (be.CAV_LOCAL + 1, 3)
    net = ct.Net(n_local, n_act)
    ct.init_residual(net)
    p = net.dist(torch.randn(500, n_local) * 3).probs
    assert torch.allclose(p[:, 1], torch.full((500,), 0.9), atol=1e-6)
    assert float(net.actor[-1].bias[1]) == pytest.approx(np.log(18.0))


def test_episode_delay():
    assert ct.episode_delay({"N": 1000.0, "dist_s": 2777.8}) == pytest.approx(1000.0 - 2777.8 / (100 / 3.6))


def test_cost_critic_only_for_lagr():
    assert ct.Net().critic_c is None and ct.Net(cost=True).critic_c is not None
    torch.manual_seed(5)
    a = ct.Net()
    torch.manual_seed(5)
    b = ct.Net(cost=True)
    assert all(torch.equal(x, y) for (k, x), (_, y) in zip(a.state_dict().items(), b.state_dict().items()))     # 2C starts from the same actor and critic


def test_candidate_envs():
    assert c1.env_for("res")["base_rule"] == {"level": 1, "th": 15, "crowd": 10}
    assert c1.env_for("attr")["reward_mode"] == "attr" and c1.env_for("lagr")["reward_mode"] == "lagr"
    for k in c1.CANDIDATES:
        e = c1.env_for(k)
        first = e["seed0"] + c1.FIRST_WORKER * e["seeds_per_worker"]
        last = e["seed0"] + (c1.FIRST_WORKER + c1.LEARNERS * c1.ENVS) * e["seeds_per_worker"] - 1
        assert first == c1.TRAIN_FIRST and last == c1.TRAIN_LAST
        same = lambda d: {x: y for x, y in d.items() if x not in c1.CANDIDATES[k] and x != "seed0"}
        assert same(e) == same(c1.ENV_V3)     # only the candidate's options and the round's seeds differ from baseline-v3


@pytest.mark.skipif(not V3_TRAIN.exists(), reason="baseline-v3 logs not on this machine")
def test_expected_seeds_match_baseline_v3():
    for i in (0, 4):
        for line in open(V3_TRAIN / f"C{i}_episodes.jsonl"):
            e = json.loads(line)
            li = c1.LEVELS.index(e["q"])
            assert e["seed"] == tb.expected_seed(i, li, e["u"], seed0=7_451_320), (i, e["u"], e["q"])


@pytest.mark.skipif(not V3_TRAIN.exists(), reason="baseline-v3 logs not on this machine")
def test_collapse_rule_agrees_with_confirmatory_3_on_baseline_v3():
    sys.path.insert(0, str(ROOT / "docs/research/conf3"))
    import collapse as cl
    for i in range(5):
        rows = [json.loads(x) for x in open(V3_TRAIN / f"C{i}_updates.jsonl")]
        r = np.array([x["r"] for x in rows])
        assert tb.collapse(r, "attr")[3] == (not cl.collapsed(rows)), i


def _fake_log(d: Path, kind: str, updates: int = 25, fault: str | None = None) -> None:
    """Event files as the trainer writes them, for learner 0, with one planted fault."""
    from torch.utils.tensorboard import SummaryWriter
    w = SummaryWriter(str(d))
    for u in range(updates):
        if fault == "skip" and u == 7:
            continue
        put = lambda t, x: w.add_scalar(t, np.float32(x), u)
        for t in tb.BASE_TAGS:
            put(t, 0.5 if t != "ppo/scale" else (3.0 if not (fault == "scale" and u > 10) else 3.1))
        if kind == "lagr":
            for t in tb.LAGR_TAGS:
                put(t, 1.0 if not (fault == "freeze" and t == "lagr/lambda" and u == 5) else 1.2)
        for li, q in enumerate(c1.LEVELS):
            for k in (*ct.EP_KEYS, "delay_s"):
                v = tb.expected_seed(0, li, u) if k == "seed" else 1.0
                put(f"ep/q{int(q)}/{k}", v + (1 if fault == "seed" and k == "seed" and u == 3 and li == 1 else 0))
            if kind == "res":
                put(f"ep/q{int(q)}/offset_moves", float("nan") if fault == "nan" and u == 2 else 1.0)
    w.close()


@pytest.mark.parametrize("kind,fault,expect", [("attr", None, None), ("lagr", None, None), ("res", None, None), ("attr", "skip", "once each"), ("attr", "seed", "seeds differ"),
                                               ("attr", "scale", "not constant"), ("res", "nan", "non-finite"), ("lagr", "freeze", "freeze")])
def test_event_file_checks_fire_on_planted_faults(tmp_path, kind, fault, expect):
    _fake_log(tmp_path, kind, fault=fault)
    faults = tb.log_faults(tb.read(tmp_path), kind, 0, updates=25)
    if expect is None:
        assert faults == []
    else:
        assert any(expect in f for f in faults), faults


def test_trainer_scalars_read_back_exactly(tmp_path):
    from torch.utils.tensorboard import SummaryWriter
    rng = np.random.default_rng(1)
    eps = [{**{k: float(rng.integers(1, 10**6)) for k in ct.EP_KEYS}, "q": q, "lv": list(rng.integers(0, 999, 12)), "offset_moves": 7} for q in c1.LEVELS]
    batch = (None,) * 6 + (rng.normal(size=100).astype(np.float32), eps, None, None, rng.normal(size=100).astype(np.float32))
    st = {"entropy": 1.1, "value_loss": 2.2, "kl": 0.003, "clipfrac": 0.01, "ev": 0.6, "n": 76000, "value_loss_c": 0.4, "ev_c": 0.5}
    w = SummaryWriter(str(tmp_path))
    ct.tb_scalars(w, 0, st, batch, 3.3, 12.5, 1.7, 0.98, 0.8)
    w.close()
    S = tb.read(tmp_path)
    assert S["ppo/value_loss"] == [(0, np.float32(2.2))] and S["lagr/lambda"] == [(0, np.float32(1.7))] and S["lagr/J"] == [(0, np.float32(0.98))]
    assert S["ppo/reward_per_decision"][0][1] == np.float32(batch[6].mean())
    for e in eps:
        q = f"ep/q{int(e['q'])}"
        assert all(S[f"{q}/{k}"] == [(0, np.float32(e[k]))] for k in ct.EP_KEYS)
        assert S[f"{q}/delay_s"] == [(0, np.float32(ct.episode_delay(e)))] and S[f"{q}/lv11"] == [(0, np.float32(e["lv"][11]))]


def test_bonferroni():
    assert dc1.bonferroni(2) == pytest.approx((1.25, 98.75)) and dc1.bonferroni(4) == pytest.approx((0.625, 99.375))


def test_tuned_reading_reproduces_confirmatory_3():
    T = c1.load(c1.BASE / "rows/conf3_eval_primary.jsonl.gz")
    sys.path.insert(0, str(ROOT / "docs/research/conf3"))
    import decide3 as d3
    for cell in c1.PRIMARY:
        r = d3.read_cell(T, cell, c1.OPPONENTS)
        m = dc1.tuned(T, cell, c1.OPPONENTS, [f"d{i}" for i in range(5)], (1.25, 98.75))
        assert (m["tuned"], m["counts"]) == (r["tuned"], r["counts"]), cell
    assert dc1.tuned(T, "X2", c1.OPPONENTS, [f"d{i}" for i in range(5)], (1.25, 98.75))["tuned"] == 4     # V395


def test_checkpoint_choice_and_advance():
    rng = np.random.default_rng(3)
    T = {}
    for c in c1.PRIMARY:
        base = {s: {"seed": s, "all_delay": 1000.0 + rng.normal(0, 5), "ttc_net": 1000.0 + rng.normal(0, 5)} for s in range(40)}
        T[(f"{c}|{c1.RULE}", c1.Q)] = base
        T[(f"{c}|p333", c1.Q)] = {s: {**r, "ttc_net": r["ttc_net"] * 1.3} for s, r in base.items()}
        T[(f"{c}|nc", c1.Q)] = {s: {**r, "all_delay": r["all_delay"] * 1.2} for s, r in base.items()}
        for i in range(5):
            for ck, dly, ttc in ((250, 1.05, 0.7), (500, 1.00, 0.75)):
                T[(f"{c}|d{i}u{ck}", c1.Q)] = {s: {**r, "all_delay": r["all_delay"] * dly, "ttc_net": r["ttc_net"] * ttc} for s, r in base.items()}
                T[(f"{c}|a{i}u{ck}", c1.Q)] = {s: {**r, "all_delay": r["all_delay"] * 0.95, "ttc_net": r["ttc_net"] * ttc} for s, r in base.items()}
    assert dc1.choose(T, "d", 0) == 500     # u250 is over the 2 % delay limit in both cells
    assert dc1.choose(T, "a", 0) == 250     # both within the limit: fewer TTC seconds wins
    inc = {i: dc1.choose(T, "d", i) for i in range(5)}
    res = dc1.advance(T, "a", {i: dc1.choose(T, "a", i) for i in range(5)}, inc)
    assert res["advances"] and not res["floor_kill"] and not res["harm"]
    assert res["cells"]["X2"]["delay_vs_incumbent"][0] == pytest.approx(5.0, abs=0.01)
    assert dc1.finalists({"x": res, "y": {**res, "advances": False}}) == ["x"]


def _rows(rng, n, scale_delay=1.0, scale_ttc=1.0):
    out = {}
    for s in range(n):
        base = 1.0 + rng.normal(0, 0.01)
        out[s] = {"seed": s, "all_delay": 2.0e5 * base * scale_delay, "ttc_net": 2000.0 * base * scale_ttc, "passed": 7000.0, "b3_step": 100.0, "alks_full_moving": 1.0,
                  "collisions": 0, "sev3": 50.0 * scale_ttc, "dist_step": 1.0e7, "ttc_half": 2000.0 * base * scale_ttc, "delay_s": 2.0e5 * base * scale_delay, "N": 6.0e5}
    return out


def test_readers_run_end_to_end_on_synthetic_rows():
    import stage0 as s0
    import validate1 as v1
    import test1 as t1
    rng = np.random.default_rng(7)
    q = c1.Q
    A = {(n, q): _rows(rng, 20, 1.0, 0.8 if "|d" in n else 1.0) for n in s0.arms_0a()}
    a = s0.read_0a(A)
    assert set(a["chosen"]) == {f"d{i}" for i in range(5)} and set(a["rank_vs_u500"]) == set(c1.PRIMARY)
    B = {(n, lv): _rows(rng, 30, 0.95 if n.startswith("T|d") else (1.0 if "p333" in n else 1.02)) for n in s0.arms_0b() for lv in c1.LEVELS}
    b = s0.read_0b(B)
    assert all(b["lower_rule"][str(lv)] == "p333" for lv in c1.LEVELS) and b["stop_2c"]
    trained = {"res": "/x/res", "attr": "/x/attr"}
    V = {(n, q): _rows(rng, 40, 0.95 if "|a" in n else 1.0, 0.75 if ("|a" in n or "|r" in n or "|d" in n) else 1.0) for n in v1.arms(trained)}
    v = json.loads(json.dumps(v1.read(V, trained)))
    assert v["finalists"] == ["attr"] and v["results"]["res"]["advances"] is False
    Tt = {(n, q): _rows(rng, 40, 0.95 if "|a" in n else 1.0, 0.75 if n.split("|")[1][0] in "adf" and n.split("|")[1] not in c1.OPPONENTS["ctrl"] else 1.0) for n in t1.arms(trained, v)}
    r = t1.read(Tt, v)
    assert r["pct"] == pytest.approx((1.25, 98.75)) and set(r["finalists"]["attr"]) == set(c1.PRIMARY)
    assert all(r["finalists"]["attr"][c]["T1"]["better"] for c in c1.PRIMARY)
