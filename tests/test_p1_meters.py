"""P1 page §2 (PI, AD), §3 TV (posted VSL), §4 (detection / clearance delays, false alarms), §7 (replicate seeds)."""
import numpy as np
import pytest

from v5b.d2.incidents import Incident, incident_window
from v5b.p1 import meters as m


def _seq_reader(vals):
    it = iter(vals)
    return lambda t: next(it)


def test_pi_law():
    states = []
    pi = m.PIMeter(K_P=40.0, K_I=20.0, n_crit=8.0, read=_seq_reader([10, 12, 12, 5]), set_state=states.append)
    pi.step(40.0)                 # control start: no update
    assert pi.q == 1500.0
    pi.step(70.0)                 # first update: n(k-1) := n(k) (no P kick); q = 1500 + 20 (8 - 10)
    assert pi.q == pytest.approx(1460.0)
    pi.step(100.0)                # q = 1460 - 40 (12 - 10) + 20 (8 - 12) = 1300
    assert pi.q == pytest.approx(1300.0)
    pi.step(130.0)                # dn = 0: q = 1300 + 20 (8 - 12) = 1220
    assert pi.q == pytest.approx(1220.0)
    pi.step(160.0)                # q = 1220 - 40 (5 - 12) + 20 (8 - 5) = 1560
    assert pi.q == pytest.approx(1560.0)
    lo = m.PIMeter(K_P=70.0, K_I=120.0, n_crit=2.0, read=_seq_reader([2, 90]), set_state=states.append)
    lo.step(0.0), lo.step(30.0), lo.step(60.0)
    assert lo.q == 200.0          # clipped at q_min as FB
    assert set(states) <= {"GGGG", "rrrr"} and "rrrr" in states


def test_ad_adapts_with_sign_rule_and_clip():
    cum = {"v": 0}
    n_seq = iter([10, 12, 12, 9, 11])
    ad = m.ADMeter(eta=1.0, K_F=20.0, n_crit=8.0, read=lambda t: next(n_seq), cum_out=lambda t: cum["v"],
                   set_state=lambda s: None)
    ad.step(40.0)
    assert ad.nhat_log == [(40.0, 8.0)]
    cum["v"] = 10
    ad.step(70.0)                 # first update: no previous (phi, n): n_hat stays
    assert ad.n_crit == 8.0 and ad.q == pytest.approx(1500 + 20 * (8 - 10))
    cum["v"] = 25                 # phi 15 (up), n 12 (up): + eta
    ad.step(100.0)
    assert ad.n_crit == 9.0
    cum["v"] = 40                 # phi 15 (equal): sgn 0 -> no move
    ad.step(130.0)
    assert ad.n_crit == 9.0
    cum["v"] = 50                 # phi 10 (down), n 9 (down): + eta
    ad.step(160.0)
    assert ad.n_crit == 10.0
    cum["v"] = 55                 # phi 5 (down), n 11 (up): - eta
    ad.step(190.0)
    assert ad.n_crit == 9.0
    assert [v for _, v in ad.nhat_log] == [8.0, 8.0, 9.0, 9.0, 10.0, 9.0]
    hi = m.ADMeter(eta=2.0, K_F=10.0, n_crit=19.0, read=lambda t: 5.0 + t / 30.0, cum_out=lambda t: t * t / 30.0,
                   set_state=lambda s: None)
    for t in np.arange(0.0, 400.0, 30.0):
        hi.step(float(t))
    assert hi.n_crit == 20.0      # flow and count both rising: up, clipped to [4, 20]
    lo = m.ADMeter(eta=2.0, K_F=10.0, n_crit=5.0, read=lambda t: 50.0 - t / 30.0, cum_out=lambda t: t * t / 30.0,
                   set_state=lambda s: None)
    for t in np.arange(0.0, 400.0, 30.0):
        lo.step(float(t))
    assert lo.n_crit == 4.0


def test_ad_max_dev_during_incident():
    log = [(40.0, 8.0), (70.0, 9.0), (100.0, 10.0), (130.0, 6.0), (160.0, 8.0), (190.0, 13.0)]
    assert m.ad_max_dev(log, 105.0, 170.0) == 2.0      # in effect at onset 10 (dev 2), then 6 (dev 2), 8
    assert m.ad_max_dev(log, 165.0, 200.0) == 5.0
    assert m.ad_max_dev(log, 30.0, 60.0) == 0.0
    assert np.isnan(m.ad_max_dev(log, None, None))


class _Lanes:
    def __init__(self):
        self.v = {f"{e}_{i}": 23.0 for e in ("2", "3") for i in range(4)}

    def set(self, ln, s):
        self.v[ln] = s

    def get(self, ln):
        return self.v[ln]


def test_vsl_rate_limit_onset_to_clearance_and_restore():
    L = _Lanes()
    v = m.PostedVSL(0.4, set_lane=L.set, get_lane=L.get)
    for t in range(100, 110):
        v.tick(float(t), False)
    assert not v.log and L.v["2_0"] == 23.0
    seq = []
    for t in range(110, 300):
        on = t < 200
        v.tick(float(t), on)
        assert v.assert_state(float(t))[0]
        seq.append(v.b)
    bs = [b for _, b in v.log]
    assert bs[:3] == [0.8, 0.6, 0.4] and v.log[0][0] == 110.0          # first update at the onset tick
    assert all(abs(x - y) <= 0.2 + 1e-12 for x, y in zip([1.0] + bs, bs))   # |db| <= 0.2 per 10-s update
    assert bs[-1] == 1.0 and v.done and L.v["3_3"] == 23.0              # ramps back to 23 m/s after clearance
    assert all(b in (0.4, 0.6, 0.8, 1.0) for b in seq)
    w = m.PostedVSL(0.6, set_lane=L.set, get_lane=L.get)
    w.tick(10.0, True)
    assert L.v["2_1"] == pytest.approx(0.8 * 23.0)
    w.restore()
    assert L.v["2_1"] == 23.0
    L.v["3_2"] = 5.0
    assert not w.assert_state(0.0)[0]
    with pytest.raises(ValueError):
        m.PostedVSL(0.1)


def test_ticks_match_incident_tick_rule():
    for s in range(7_400_000, 7_400_400):
        on, dur = incident_window(s, 40.0, 900.0)
        inc = Incident("slow", on, dur, api=None)
        inc._apply = inc._remove = lambda: None
        inc._read = lambda: {}
        ev = {}
        for k in range(900):
            t = 40.0 + k
            e = inc.tick(t)
            if e:
                ev[e] = t
        assert (ev["on"], ev["off"]) == m.incident_ticks(on, dur)
        assert m.switch_schedule(on, dur, back=True) == (ev["on"], ev["off"])


def test_detection_and_clearance_delays():
    on, dur = 100.4, 150.0                      # ticks: on 101, off 251
    assert m.switch_schedule(on, dur) == (101.0, None)
    assert m.switch_schedule(on, dur, d=60.0) == (161.0, None)
    assert m.switch_schedule(on, dur, d=60.0, back=True) == (161.0, 251.0)
    assert m.switch_schedule(on, dur, d=60.0, c=60.0, back=True) == (161.0, 311.0)
    assert m.switch_schedule(on, dur, c=180.0, back=False) == (101.0, None)       # stay plan: c has no effect
    assert m.switch_schedule(on, dur, d=150.0, back=True) == (None, None)        # onset + d >= clearance: IP = N
    assert m.switch_schedule(on, dur, d=240.0) == (None, None)
    assert m.switch_schedule(300.0, 470.0, c=180.0, back=True) == (300.0, None)  # return after control end = stay


def test_false_alarm_window_own_salt():
    for s in range(7_400_000, 7_400_300):
        t, dur = m.fa_window(s)
        assert 40.0 <= t <= 340.0 and dur == 240.0
        sw, bk = m.fa_schedule(s)
        assert sw >= t and bk == sw + 240.0 and bk < 940.0
    assert m.fa_window(7_400_500) != incident_window(7_400_500, 40.0, 900.0)
    assert m.FA_SALT not in (3301, 2027, 4049)


def test_replicate_seeds_redraw_sumo_and_demand_keep_window():
    s = 7_400_517
    assert m.replicate_seeds(s, 0) == {"sumo_seed": s, "demand_seed": s, "window_seed": s}
    for k in (1, 2, 3, 4):
        r = m.replicate_seeds(s, k)
        assert r["sumo_seed"] == r["demand_seed"] == s + k * 10_000_000 and r["window_seed"] == s
    with pytest.raises(ValueError):
        m.replicate_seeds(s, -1)
