"""EV-A's drawn slowdown (v505_ev_informed_rule.md §2): drawn from the seed, inside its ranges, the same for every arm, run as a slowdown."""
from types import SimpleNamespace

from v5b.fleet import perturb as pt

SPEC = {"kind": "slowdown_draw", "edge": "2", "limit_kmh": 20.0, "onset": [450.0, 800.0], "dur": [240.0, 420.0], "taper": 20.0, "salt": 505_001}


def env():
    return SimpleNamespace(warm=300.0, plant={"limit": 100.0 / 3.6})


def test_draw_is_inside_the_ranges_and_ends_before_the_drain_window():
    for seed in range(7_488_220, 7_488_340):
        s = pt.draw_slowdown(SPEC, seed)
        t0, d = s["times"][0], s["dur"]
        assert 450.0 <= t0 < 800.0 and 240.0 <= d < 420.0 and t0 + d < 1_220.0 + 1e-9
        assert s["kind"] == "slowdown" and s["edge"] == "2" and s["limit_kmh"] == 20.0 and s["taper"] == 20.0


def test_same_seed_same_event_for_every_arm_and_seeds_differ():
    a, b = pt.Perturb(env(), dict(SPEC), 7_488_300), pt.Perturb(env(), dict(SPEC), 7_488_300)
    assert a.s == b.s and a.kind == "slowdown"
    assert pt.Perturb(env(), dict(SPEC), 7_488_301).s != a.s


def test_logged_draw_and_period_labels_use_the_drawn_times():
    p = pt.Perturb(env(), dict(SPEC), 7_488_300)
    t0, d = p.s["times"][0], p.s["dur"]
    assert p.log == [("drawn", t0, d)]
    assert pt.event_period(p.s, t0 - 1) == "before" and pt.event_period(p.s, t0 + 5) == "taper"
    assert pt.event_period(p.s, t0 + 30) == "hold" and pt.event_period(p.s, t0 + d + 1) == "after"


def test_salt_separates_the_draw_from_the_training_draw():
    s = pt.draw_slowdown({**SPEC, "salt": 910_000}, 7_488_300)
    assert s != pt.draw_slowdown(SPEC, 7_488_300)
