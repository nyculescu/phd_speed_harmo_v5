"""E1 controllers (V213 §3, §10.1): meter law and actuator, MTFC, cascade, cap profile, ALKS adapter on a fake libsumo."""
import math
from collections import deque
from types import SimpleNamespace

import pytest

from v5b.fleet import control as ct


def test_alinea_and_pi_laws():
    a = ct.MeterLaw("alinea", setpoint=20.0, k_r=70.0)
    assert a(600.0, 25.0, 25.0, 600.0) == pytest.approx(250.0)
    p = ct.MeterLaw("pi", setpoint=20.0, k_p=100.0, k_i=10.0)
    # occupancy rising by 2 points lowers the rate by K_P x 2; below the setpoint the I term raises it
    assert p(600.0, 18.0, 16.0, 600.0) == pytest.approx(600.0 - 200.0 + 20.0)
    assert p(300.0, 0.0, 0.0, 50.0) == pytest.approx(450.0)         # +400 cap on the measured rate
    assert ct.MeterLaw("fixed", rate=300.0)(900.0, 50.0, 50.0, 0.0) == 300.0


def test_pi_gain_conversion():
    k_p, k_i = ct.pi_gains(100.0, 4.0, 5.2)
    assert k_p == pytest.approx(192.31, abs=0.01) and k_i == pytest.approx(7.692, abs=0.001)


def test_rest_green_without_need():
    m = ct.Meter(ct.MeterLaw("alinea", setpoint=20.0))
    m.update(60.0, 5.0, 0, 300.0)
    assert not m.metering and m.r_law == ct.R_MAX
    assert m.step(61.0, 0, 0, False, 0.0) == "G"


def test_bounds_and_queue_law():
    m = ct.Meter(ct.MeterLaw("alinea", setpoint=10.0))
    m.update(60.0, 80.0, 0, 500.0)
    assert m.r_law == ct.R_MIN
    m.update(120.0, 80.0, 22, 500.0)
    assert m.r_law == pytest.approx(24.0 * 22)
    assert m.saturated


def test_onset_amber_then_red_then_green_per_vehicle():
    m = ct.Meter(ct.MeterLaw("fixed", rate=360.0), overrides=False)
    m.update(0.0, 30.0, 5, 500.0)
    assert m.metering and m.state == "y" and m.amber == ct.AMBER_ONSET
    states = [m.step(float(t), 0, 1, False, 0.0) for t in range(1, 12)]
    assert states[:4] == ["y"] * 4 and states[4] == "r"
    # 360 veh/h owes one vehicle after 10 s; a vehicle waits at the line, so the green starts then
    assert "G" in states[5:] and states.index("G") == 9
    s = [m.step(12.0, 1, 1, False, 0.0), m.step(13.0, 0, 1, False, 0.0)]
    assert s == ["y", "r"] and m.amber == ct.AMBER_CAR
    assert m.n["red_passages"] == 0


def test_red_passage_is_counted():
    m = ct.Meter(ct.MeterLaw("fixed", rate=300.0), overrides=False)
    m.update(0.0, 30.0, 5, 500.0)
    for t in range(1, 7):
        m.step(float(t), 0, 0, False, 0.0)
    assert m.state == "r"
    m.step(7.0, 1, 0, False, 0.0)
    assert m.n["red_passages"] == 1


def test_anti_windup_uses_realised_rate_when_not_metered():
    m = ct.Meter(ct.MeterLaw("alinea", setpoint=20.0, k_r=70.0))
    for t in range(1, 61):
        m.step(float(t), 1 if t % 6 == 0 else 0, 0, False, 0.0)      # 10 releases: 600 veh/h, resting green
    m.update(60.0, 20.0, 0, 600.0)
    assert m.log[-1][2] == pytest.approx(600.0)
    assert m.r_law == pytest.approx(600.0) and not m.metering
    m2 = ct.Meter(ct.MeterLaw("alinea", setpoint=20.0, k_r=70.0))
    for t in range(1, 61):
        m2.step(float(t), 1 if t % 6 == 0 else 0, 0, False, 0.0)
    m2.update(60.0, 22.0, 0, 600.0)
    assert m2.r_law == pytest.approx(600.0 - 140.0) and m2.metering


def test_override_and_backstop_hysteresis():
    m = ct.Meter(ct.MeterLaw("alinea", setpoint=10.0))
    m.update(60.0, 60.0, 5, 500.0)
    assert m.metering
    m.queue_check(31.0)
    assert m.step(61.0, 0, 1, False, 0.0) == "G" and m.override
    m.queue_check(20.0)
    assert m.override
    m.queue_check(14.0)
    assert not m.override
    m.step(62.0, 0, 1, False, 211.0)
    assert m.backstop and m.r_cmd == ct.R_MAX
    m.step(63.0, 0, 1, False, 160.0)
    assert m.backstop
    m.step(64.0, 0, 1, False, 149.0)
    assert not m.backstop


def _green_at_6():
    m = ct.Meter(ct.MeterLaw("fixed", rate=900.0 - 1), overrides=False)
    m.update(0.0, 30.0, 5, 500.0)
    for t in range(1, 7):
        m.step(float(t), 0, 1, False, 0.0)
    assert m.state == "G" and m.t_state == 6.0
    return m


def test_downstream_limited_second_needs_2_s_without_a_release():
    m = _green_at_6()
    m.step(7.0, 0, 1, True, 0.0)
    assert m.n["dlim_s"] == 0
    m.step(8.0, 0, 1, True, 0.0)
    assert m.n["dlim_s"] == 1 and m.p_dlim
    assert [m.step(float(t), 0, 1, True, 0.0) for t in (9, 10)] == ["G", "y"]     # no hold: G_MAX ends it
    m2 = _green_at_6()
    m2.step(7.0, 1, 1, True, 0.0)                    # the head left in the first green second
    m2.step(8.0, 0, 1, True, 0.0)
    assert m2.n["dlim_s"] == 0


def test_green_extends_on_any_close_vehicle():
    m = _green_at_6()
    assert [m.step(float(t), 0, 0, False, 0.0, n_close=1) for t in (7, 8, 9, 10)] == ["G", "G", "G", "y"]
    m2 = _green_at_6()
    assert [m2.step(float(t), 0, 0, False, 0.0, n_close=0) for t in (7, 8)] == ["G", "y"]


def test_onset_amber_after_an_override():
    m = ct.Meter(ct.MeterLaw("fixed", rate=600.0))
    m.update(60.0, 30.0, 5, 500.0)
    for t in range(61, 70):
        m.step(float(t), 0, 1, False, 0.0)
    m.queue_check(31.0)
    for t in range(70, 190):
        assert m.step(float(t), 0, 1, False, 0.0) == "G"
    m.queue_check(10.0)
    s = [m.step(float(t), 0, 1, False, 0.0) for t in range(190, 197)]
    assert s[:5] == ["y"] * 5 and s[5] == "r" and m.amber == ct.AMBER_ONSET
    m2 = ct.Meter(ct.MeterLaw("fixed", rate=600.0))
    m2.queue_check(31.0)
    m2.update(60.0, 30.0, 5, 500.0)                  # onset during the override
    assert m2.step(60.0, 0, 1, False, 0.0) == "G"
    m2.queue_check(10.0)
    assert m2.step(61.0, 0, 1, False, 0.0) == "y" and m2.amber == ct.AMBER_ONSET


def test_rest_and_resume_margins():
    m = ct.Meter(ct.MeterLaw("alinea", setpoint=20.0, k_r=70.0))
    m.update(60.0, 10.0, 0, 600.0)
    assert not m.metering
    m.update(120.0, 26.0, 0, 600.0)                  # r = 240 < 0.95 x 600
    assert m.metering and m.r_law == ct.R_MIN
    m.update(180.0, 20.0, 3, 200.0)                  # 240 >= 1.05 x 200, but 3 queued
    assert m.metering
    m.update(240.0, 20.0, 2, 200.0)
    assert not m.metering
    m.update(300.0, 20.0, 0, 250.0)                  # 240 is not below 0.95 x 250
    assert not m.metering
    m.update(360.0, 20.0, 0, 260.0)
    assert m.metering


def _queue_run(hours: float = 2.0, arrivals: float = 523.0):
    """FIFO ramp queue at the meter: deterministic arrivals; the head leaves on green at most every 2 s; ALINEA pinned
    at the lower bound by an occupancy far above its setpoint."""
    m = ct.Meter(ct.MeterLaw("alinea", setpoint=1.0, k_r=70.0))
    q, gap, nxt, last_rel, worst = deque(), 3600.0 / arrivals, 0.0, -10.0, 0.0
    shown = "G"
    for t in range(1, int(hours * 3600) + 1):
        while nxt <= t:
            q.append(nxt)
            nxt += gap
        rel = 0
        if shown == "G" and q and t - q[0] >= 14.1 and t - last_rel >= 2.0:
            q.popleft()
            rel, last_rel = 1, t
        if t % 30 == 0:
            m.queue_check(5.0)
        if t % 60 == 0:
            m.update(float(t), 90.0, len(q), arrivals)
        wait = max(0.0, t - q[0] - 14.1) if q else 0.0
        worst = max(worst, wait) if t > 600 else worst
        near = 1 if q and t - q[0] >= 14.1 else 0
        shown = m.step(float(t), rel, near, False, wait)
    return m, worst


def test_queue_law_keeps_waits_inside_the_backstop():
    m, worst = _queue_run()
    assert m.n["backstop_s"] == 0
    assert worst < ct.WAIT_ON
    assert m.n["red_passages"] == 0


def test_mtfc_saturation_rate_limit_and_hold():
    c = ct.MTFC(setpoint=20.0, k_i=0.02)
    c.update(60.0, 40.0)
    assert c.b == pytest.approx(0.8)       # 0.02 x 20 = 0.4, limited to 0.2
    for k in range(10):
        c.update(120.0 + 60 * k, 60.0)
    assert c.b == ct.B_MIN
    c.update(800.0, 0.0, release=False)
    assert c.b == pytest.approx(ct.B_MIN + 0.2)
    f = ct.MTFC(setpoint=20.0, k_i=0.02, fixed_b=0.5)
    f.update(60.0, 99.0)
    assert f.b == 0.5


def test_cascade_gate():
    g = ct.Cascade()
    assert not g.update(False)
    assert g.update(True)
    for _ in range(4):
        assert g.update(False)
    assert not g.update(False)


def test_cap_profile_and_command():
    lo, hold = ct.ZONES["short"]
    assert hold == 592.0 and lo == pytest.approx(592.0 - 234.1, abs=0.1)
    assert ct.ZONES["long"][1] == pytest.approx(384.1, abs=0.1)
    c = ct.B_MIN * ct.V_ALKS
    assert ct.cap_at(hold, c, hold) == pytest.approx(c)
    assert ct.cap_at(lo, c, hold) == pytest.approx(ct.V_ALKS, abs=1e-6)
    mid = ct.cap_at(hold - 100.0, c, hold)
    assert mid == pytest.approx(math.sqrt(c * c + 300.0))
    assert ct.command(10.0, 27.0, 55.0) == pytest.approx(27.0 - 0.15)
    assert ct.command(20.0, 15.0, 55.0) == 20.0
    assert ct.command(25.0, 15.0, 22.0) == 22.0          # an E2 weather cap is kept


class _FakeLS:
    """Just enough libsumo for SumoALKS: vehicles on edge '3' with position, speed and maxSpeed."""

    class TraCIException(Exception):
        pass

    def __init__(self, veh: dict):
        self.veh = veh
        self.edge = SimpleNamespace(getLastStepVehicleIDs=lambda e: [v for v in self.veh if self.veh[v]["live"]])
        self.vehicle = SimpleNamespace(getLanePosition=lambda v: self.veh[v]["x"],
                                       getSpeed=lambda v: self.veh[v]["v"],
                                       getMaxSpeed=lambda v: self.veh[v]["max"],
                                       setMaxSpeed=self._set,
                                       getLeader=lambda v, d: self.veh[v].get("lead", ("", -1.0)),
                                       getDistance=lambda v: self.veh[v].get("d", 0.0),
                                       getAllowedSpeed=lambda v: self.veh[v].get("allowed", min(self.veh[v]["max"], 27.78)))
        self.inductionloop = None

    def _set(self, v, s):
        if not self.veh[v]["live"]:
            raise self.TraCIException(v)
        self.veh[v]["max"] = s


class _Bank:
    def __init__(self, o):
        self.o = o

    def occ60(self, _):
        return self.o


def _alks(monkeypatch, veh, blocked=lambda v: False, b=0.5):
    fake = _FakeLS(veh)
    monkeypatch.setattr(ct, "ls", fake)
    law = ct.MTFC(setpoint=20.0, k_i=0.02, fixed_b=b)
    h = ct.SumoALKS(law, _Bank(30.0), "drop", "short", set(veh), {v: ct.V_ALKS for v in veh}, blocked)
    return fake, h


def test_alks_command_restore_and_blocked(monkeypatch):
    veh = {"a": {"x": 600.0, "v": 27.0, "max": 30.0, "live": True},     # 30.0: a pre-set vType maxSpeed (E2 bound)
           "b": {"x": 600.0, "v": 27.0, "max": 55.5, "live": True},
           "far": {"x": 100.0, "v": 27.0, "max": 55.5, "live": True}}
    fake, h = _alks(monkeypatch, veh, blocked=lambda v: v == "b")
    h.step(0.1)
    assert veh["a"]["max"] == pytest.approx(27.0 - 0.15)
    assert veh["b"]["max"] == 55.5 and veh["far"]["max"] == 55.5      # blocked and outside: untouched
    veh["a"]["x"] = 900.0                                               # leaves the zone
    h.step(0.2)
    assert veh["a"]["max"] == 30.0 and h.n["restores"] == 1 and h.n["restore_mismatch"] == 0


def test_alks_no_command_at_b1(monkeypatch):
    veh = {"a": {"x": 600.0, "v": 27.0, "max": 55.5, "live": True}}
    fake, h = _alks(monkeypatch, veh, b=1.0)
    h.step(0.1)
    assert veh["a"]["max"] == 55.5 and h.n["cmd_steps"] == 0


def test_alks_restore_when_b_returns_to_1(monkeypatch):
    veh = {"a": {"x": 600.0, "v": 13.0, "max": 55.5, "live": True}}
    fake, h = _alks(monkeypatch, veh, b=0.5)
    h.step(0.1)
    assert veh["a"]["max"] == pytest.approx(0.5 * ct.V_ALKS)
    h.law.b = 1.0
    h.step(0.2)
    assert veh["a"]["max"] == 55.5 and not h.own


def test_alks_vehicle_gone_is_not_an_error(monkeypatch):
    veh = {"a": {"x": 600.0, "v": 20.0, "max": 55.5, "live": True}}
    fake, h = _alks(monkeypatch, veh)
    h.step(0.1)
    veh["a"]["live"] = False
    h.step(0.2)
    assert not h.own and h.n["restores"] == 0


def test_alks_hold_speed_counts_free_seconds_only(monkeypatch):
    c = 0.5 * ct.V_ALKS
    veh = {"f": {"x": 700.0, "v": c + 0.4, "max": 55.5, "live": True},
           "q": {"x": 700.0, "v": c - 8.0, "max": 55.5, "live": True, "lead": ("x", 12.0)},
           "g": {"x": 700.0, "v": c - 2.0, "max": 55.5, "live": True, "lead": ("x", 110.0)}}
    fake, h = _alks(monkeypatch, veh)
    for k in range(1, 11):
        h.step(k * 0.1)
    s = h.summary()
    assert s["hold_free_n"] == 1 and s["hold_free_mean"] == pytest.approx(0.4)     # 110 m: ACC still gap-closing
    assert s["hold_free"] == [(1, pytest.approx(0.4))]
    assert s["hold_by_gap"][">100 m"] == (pytest.approx(-2.0), 1)


def test_anti_windup_keeps_the_command_after_an_override_with_red():
    m = ct.Meter(ct.MeterLaw("alinea", setpoint=20.0, k_r=70.0))
    m.update(60.0, 30.0, 5, 500.0)                   # metering at 240
    for t in range(60, 120):
        m.step(float(t), 0, 1, False, 0.0)
    assert m.n["red_phases"] >= 1
    m.p_ovr = True                                   # an override second in the period
    m.update(120.0, 20.0, 5, 500.0)
    assert m.r_law == pytest.approx(240.0)           # r_s = the commanded 240, not the realised 0 (clipped to 240)
    assert m.log[-1][10] == pytest.approx(240.0)     # applied rate logged


def test_saturated_flag_with_an_override():
    m = ct.Meter(ct.MeterLaw("alinea", setpoint=10.0))
    m.update(60.0, 5.0, 0, 500.0)
    assert not m.saturated
    m.p_ovr = True
    m.update(120.0, 5.0, 0, 500.0)
    assert m.saturated


def test_alks_only_alks_on_edge_3_and_the_step_limit(monkeypatch):
    veh = {"a": {"x": 600.0, "v": 27.0, "max": 55.5, "live": True},
           "h": {"x": 600.0, "v": 27.0, "max": 55.5, "live": True}}
    fake = _FakeLS(veh)
    monkeypatch.setattr(ct, "ls", fake)
    law = ct.MTFC(setpoint=20.0, k_i=0.02, fixed_b=0.5)
    h = ct.SumoALKS(law, _Bank(30.0), "drop", "short", {"a"}, {v: ct.V_ALKS for v in veh}, lambda v: False)
    prev = 27.0
    for k in range(1, 30):
        h.step(k * 0.1)
        assert prev - veh["a"]["max"] <= ct.A_CAP * ct.STEP + 1e-9
        prev = veh["a"]["max"]
        veh["a"]["v"] = veh["a"]["max"]
    assert veh["h"]["max"] == 55.5                   # not an ALKS


def test_alks_blocked_after_command_is_not_restored(monkeypatch):
    veh = {"a": {"x": 600.0, "v": 27.0, "max": 55.5, "live": True}}
    state = {"blocked": False}
    fake, h = _alks(monkeypatch, veh, blocked=lambda v: state["blocked"])
    h.step(0.1)
    assert veh["a"]["max"] < 55.5
    state["blocked"] = True
    h.step(0.2)
    assert veh["a"]["max"] < 55.5 and h.n["restores"] == 0


def test_alks_recovery_still_measured_at_b_1(monkeypatch):
    veh = {"a": {"x": 600.0, "v": 27.0, "max": 55.5, "live": True}}
    fake, h = _alks(monkeypatch, veh)
    h.step(0.1)
    h.law.fixed_b = h.law.b = 1.0
    h.step(0.2)                                      # restored, released
    assert h.released
    veh["a"]["d"] = 300.0
    h.step(1.0)
    assert h.recovery and not h.released


def test_alks_recovery_best_ratio_within_300_m_and_gap_at_release(monkeypatch):
    veh = {"a": {"x": 600.0, "v": 13.9, "max": 55.5, "live": True}}
    fake, h = _alks(monkeypatch, veh)
    h.step(0.1)
    veh["a"]["x"], veh["a"]["lead"] = 900.0, ("x", 150.0)
    h.step(0.2)                                      # released 150 m behind its leader
    veh["a"].pop("lead")
    for k, (d, v) in enumerate([(100.0, 26.0), (200.0, 24.0), (299.0, 25.0), (301.0, 27.7)]):
        veh["a"]["d"], veh["a"]["v"] = d, v
        h.step(float(k + 1))
    assert h.recovery == [(round(27.7 / ct.V_ALKS, 3), 150.0)]
    assert h.n["allowed_mismatch"] == 0


def test_alks_allowed_speed_mismatch_is_counted(monkeypatch):
    veh = {"a": {"x": 600.0, "v": 27.0, "max": 55.5, "live": True, "allowed": 20.0}}
    fake, h = _alks(monkeypatch, veh)
    h.step(0.1)
    veh["a"]["x"] = 900.0
    h.step(0.2)
    assert h.n["restores"] == 1 and h.n["restore_mismatch"] == 0 and h.n["allowed_mismatch"] == 1
    assert h.summary()["allowed_max_dev"] == pytest.approx(ct.V_ALKS - 20.0, abs=1e-4)


def test_kinematic_amber_after_a_green():
    for approach, amber in ((False, ct.AMBER_CAR), (True, ct.AMBER_ONSET)):
        m = ct.Meter(ct.MeterLaw("fixed", rate=360.0), overrides=False)
        m.update(0.0, 30.0, 5, 500.0)
        states = [m.step(float(t), 0, 1, False, 0.0) for t in range(1, 11)]
        assert states[-1] == "G"
        assert m.step(12.0, 1, 0, False, 0.0, 0, approach) == "y" and m.amber == amber
        assert m.n["amber_kin"] == approach


def test_loop_window_and_raw_occupancy_log():
    b = ct.LoopBank({"drop": ["d0"]})
    b.rows = [[30 * k, 0, float(k), None] for k in range(1, 7)]
    assert b.occ60("drop") == pytest.approx(5.5) and b.occ60("drop", 6) == pytest.approx(3.5)
    m = ct.Meter(ct.MeterLaw("pi", setpoint=20.0, k_p=10.0, k_i=1.0))
    m.update(60.0, 3.5, 0, 500.0, 5.5)
    assert m.log[-1][3] == 3.5 and m.log[-1][11] == 5.5
    m.update(120.0, 4.0, 0, 500.0)
    assert m.log[-1][11] == 4.0


def test_fixed_rate_keeps_its_owed_release_across_minutes():
    m = ct.Meter(ct.MeterLaw("fixed", rate=300.0), overrides=False)
    m.update(0.0, 30.0, 5, 500.0)
    shown, rel_t = "y", []
    for t in range(1, 601):
        if t % 60 == 0:
            m.update(float(t), 30.0, 5, 500.0)
        rel = 1 if shown == "G" and (not rel_t or t - rel_t[-1] > 2) else 0
        if rel:
            rel_t.append(t)
        shown = m.step(float(t), rel, 1, False, 0.0)
    assert len(rel_t) >= 49                          # 300 veh/h over 600 s, less the onset
    assert m.amber == ct.AMBER_CAR and m.n["red_phases"] >= 49


def test_supply_limited_seconds_are_flagged():
    m = ct.Meter(ct.MeterLaw("fixed", rate=360.0), overrides=False)
    m.update(0.0, 30.0, 5, 500.0)
    for t in range(1, 21):
        m.step(float(t), 0, 0, False, 0.0)          # owed from t = 10, nobody at the line
    assert m.state == "r" and m.n["starved_s"] >= 10
    m.update(60.0, 30.0, 5, 500.0)
    assert m.log[-1][12] == 1
    m.update(120.0, 30.0, 5, 500.0)
    assert m.log[-1][12] == 0
    assert ct.STOP_DECEL == 3.0
