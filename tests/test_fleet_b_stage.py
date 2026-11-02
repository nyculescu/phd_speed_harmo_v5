"""B bind check rules (V258, bind_B_core_v2 §4) on synthetic inputs."""
import numpy as np

from v5b.fleet import b_merge as bm, b_stage as bs


def _row(t, merges=10, stand=0, sched=10, ma=40, ma0=12):
    return (t, ma, None, 0, 0, 25.0, merges, stand, sched, 25.0, ma0, False, ma)


def test_stuck_episode_needs_10_intervals_and_low_merge_share():
    rows = [_row(600.0 + 30 * i) for i in range(1, 121)]
    assert bs.stuck_episodes({"series": rows}) == 0
    for i in range(20, 30):
        rows[i] = _row(rows[i][0], merges=2, stand=6, sched=10)
    assert bs.stuck_episodes({"series": rows}) == 1
    rows[25] = _row(rows[25][0], merges=2, stand=4, sched=10)
    assert bs.stuck_episodes({"series": rows}) == 0
    for i in range(20, 30):
        rows[i] = _row(rows[i][0], merges=3, stand=6, sched=10)
    assert bs.stuck_episodes({"series": rows}) == 0      # 30 merges > 25 % of 100


def test_loading_check():
    def run(ratio, q_at_merge=True, dead=False):
        sched = np.linspace(2400.0, 4199.0, 1000)
        ma = np.where(np.arange(1000) < ratio * 1000, 3000.0, 5000.0)
        e = [{"t_break": 1000.0, "t_recover": 4300.0, "min": 55.0}] if q_at_merge else []
        return {"deadlock_events": [{"start": 1}] if dead else [], "breakdowns_merge": e}, {"sched": sched, "ma": ma}
    top = [run(0.90) for _ in range(10)]
    assert bs.loading_check(top, low_min=0.99)["pass"]
    assert not bs.loading_check(top, low_min=0.85)["pass"]
    assert not bs.loading_check([run(0.98) for _ in range(10)], 0.99)["pass"]
    assert not bs.loading_check([run(0.9, q_at_merge=i < 7) for i in range(10)], 0.99)["pass"]
    assert not bs.loading_check([run(0.9, dead=i < 3) for i in range(10)], 0.99)["pass"]


def test_tool_artefact_bracket():
    ok = {"deadlock_events": [], "status": "ok", "series": []}
    bad = {"deadlock_events": [{"start": 1}], "status": "ok", "series": []}
    lr = {0.9: [ok] * 10, 0.95: [ok] * 9 + [bad], 1.0: [ok] * 8 + [bad, {**ok, "status": "undrained"}]}
    t = bs.tool_artefact(lr, 0.96 * bm.B0)
    assert t["bracket"] == [0.95, 1.0] and t["artefact_runs"] == 3 and not t["pass"]
    assert bs.tool_artefact(lr, 0.91 * bm.B0)["pass"]
    assert not bs.tool_artefact(lr, 2.0 * bm.B0)["pass"]


def test_c0_tables():
    sh = bm.SHARES
    D = {(s, h): True for s in sh for h in bs.STEPS}
    Lat = dict(D)
    St = {s: True for s in sh}
    assert bs.c0_tables(D, Lat, St)["b_step"] == "0.1"
    St[0.8] = False
    assert bs.c0_tables(D, Lat, St)["b_step"] == "0.05"
    Lat[(0.8, 0.05)] = False
    assert bs.c0_tables(D, Lat, St)["b_step"] == "B-UNTESTABLE(m32, step)"
    D[(0.8, 0.1)] = D[(0.8, 0.05)] = False
    t = bs.c0_tables(D, Lat, {s: True for s in sh})
    assert t["shares"]["0.8"] == {"untestable": "deadlock"} and t["b_step"] == "0.1"
    D = {(s, h): False for s in sh for h in bs.STEPS}
    assert bs.c0_tables(D, Lat, St)["b_step"] == "none left: INCONCLUSIVE"


def test_logistic_levels_and_fallback():
    rng = np.random.default_rng(0)
    f = np.repeat(np.arange(0.6, 1.11, 0.05), 40)
    p = 1 / (1 + np.exp(-(f - 0.9) * 20))
    y = rng.random(f.size) < p
    lv = bs.logistic_levels(list(f * bm.B0), list(y))
    assert lv["method"] == "logistic" and lv["L1"] < lv["L2"]
    assert abs(lv["L2"] / bm.B0 - (0.9 + np.log(0.3 / 0.7) / 20)) < 0.03
    sep = bs.logistic_levels([0.6 * bm.B0] * 10 + [1.0 * bm.B0] * 10, [0] * 10 + [1] * 10)
    assert sep["method"].startswith("interpolation")


def test_lattice_counts():
    assert bs.lattice_ok([3, 4, 5, 6, 4, 5])
    assert not bs.lattice_ok([7, 8] * 10)
    assert not bs.lattice_ok([4] * 6 + [5, 6, 7])


def test_lane0_onset_input_counts_occupied_empty_interval_as_standing():
    assert bm.lane0_speed(3, 20.0, 12.5) == 12.5
    assert bm.lane0_speed(0, 35.0, None) == 0.0
    assert bm.lane0_speed(0, 0.0, None) is None
