"""Batch fan controller (vsl_lab/ops/cooling.py): the pure parts. No hardware, no llano, no asusctl.

Run: pytest -p no:cacheprovider tests/test_cooling.py -v
"""
from __future__ import annotations

import json

from vsl_lab.ops import cooling as C

LUT = {"devices": {"cpu": {"rows": [[58, 30], [70, 62], [84, 100]]}, "gpu": {"rows": [[42, 30], [47, 60], [64, 60]]}}}
NAN = float("nan")


def inp(now, util=0.9, cpu=90.0, gpu=NAN, thr=0.0, last_thr=-float("inf"), focus="working",
        pad_foreign=False, laptop_foreign=False, perf=True):
    return C.Inputs(now, util, cpu, gpu, thr, last_thr, focus, pad_foreign, laptop_foreign, perf)


def test_lut_takes_the_higher_device_and_skips_nan():
    assert C.lut_target(LUT, 90.0, 40.0) == 100
    assert C.lut_target(LUT, 50.0, 50.0) == 60
    assert C.lut_target(LUT, 64.0, NAN) == 46
    assert C.lut_target(LUT, NAN, NAN) == 0


def test_away_curves_never_weaker_than_firmware_and_monotone():
    for fan in ("cpu", "gpu", "mid"):
        for level in range(C.MAX_LEVEL + 1):
            pts = C.away_curve(fan, level)
            assert len(pts) == 8
            assert all(a[0] <= b[0] and a[1] <= b[1] for a, b in zip(pts, pts[1:]))
            assert all(0 <= p <= 100 and p >= C.interp(C.FIRMWARE[fan], t) - 0.5 for t, p in pts)
    assert C.away_curve("cpu", 2)[0][0] == 32                           # 4 C earlier per level
    assert C.curve_arg(C.away_curve("cpu", 0)).startswith("40c:20%,55c:30%")


def test_idle_does_nothing_and_activation_writes_the_pad():
    c = C.Controller(LUT)
    assert C.Actions() == c.step(inp(0, util=0.2))
    a = c.step(inp(5))
    assert c.active and a.pad == 100 and "active" in a.events and a.laptop_level is None


def test_pad_rewritten_only_on_a_big_move_or_a_focus_change():
    c = C.Controller(LUT)
    c.step(inp(0, cpu=70.0))
    assert c.step(inp(5, cpu=71.0)).pad is None                         # 62 -> 65: < PAD_STEP
    assert c.step(inp(10, cpu=74.0)).pad == 73
    assert c.step(inp(15, cpu=74.0, focus="sleeping")).pad == 73          # llano re-caps on a Focus change


def test_idle_hold_then_restore():
    c = C.Controller(LUT)
    c.step(inp(0))
    assert not c.step(inp(5, util=0.1)).pad_restore
    a = c.step(inp(5 + C.IDLE_HOLD_S, util=0.1))
    assert not c.active and a.pad_restore and "idle" in a.events
    c.step(inp(200))
    c.step(inp(205, util=0.1))
    assert c.step(inp(210, util=0.95)).pad_restore is False             # load back before the hold: stays active
    assert c.active


def test_foreign_pad_write_yields_until_idle():
    c = C.Controller(LUT)
    c.step(inp(0))
    a = c.step(inp(5, cpu=60.0, pad_foreign=True))
    assert a.pad is None and c.pad_yield
    assert c.step(inp(10, cpu=60.0)).pad is None                        # still hands off
    c.step(inp(20, util=0.1))
    a = c.step(inp(20 + C.IDLE_HOLD_S, util=0.1))
    assert not c.active and not a.pad_restore                            # someone else owns it: not put back
    c.step(inp(1000))
    assert not c.pad_yield                                               # a new batch starts fresh


def test_laptop_follows_focus():
    c = C.Controller(LUT)
    assert c.step(inp(0, focus="working")).laptop_level is None
    a = c.step(inp(5, focus="away"))
    assert a.laptop_level == 0
    a = c.step(inp(10, focus="working"))
    assert a.laptop_firmware and c.level is None
    assert c.step(inp(15, focus="away", perf=False)).laptop_level is None  # only on the Performance profile


def test_away_level_rises_on_throttling_and_falls_after_quiet():
    c = C.Controller(LUT)
    c.step(inp(0, focus="away"))
    assert c.step(inp(5, focus="away", thr=0.2, last_thr=5)).laptop_level is None   # within the 2-min window
    assert c.step(inp(125, focus="away", thr=0.2, last_thr=125)).laptop_level == 1
    for k in range(2, C.MAX_LEVEL + 1):
        assert c.step(inp(125 + 120 * (k - 1), focus="away", thr=0.2, last_thr=125 + 120 * (k - 1))).laptop_level == k
    assert c.step(inp(1000, focus="away", thr=0.2, last_thr=1000)).laptop_level is None   # capped at MAX_LEVEL
    t = 1000 + C.THROTTLE_DOWN_S
    assert c.step(inp(t, focus="away", last_thr=1000)).laptop_level == C.MAX_LEVEL - 1


def test_foreign_laptop_change_yields_and_is_not_undone():
    c = C.Controller(LUT)
    c.step(inp(0, focus="away"))
    a = c.step(inp(5, focus="away", laptop_foreign=True))
    assert c.laptop_yield and a.laptop_level is None and not a.laptop_firmware
    assert not c.step(inp(10, focus="working")).laptop_firmware
    c.step(inp(20, util=0.1))
    a = c.step(inp(20 + C.IDLE_HOLD_S, util=0.1))
    assert not c.active and not a.laptop_firmware


def test_restore_cmd_from_status():
    assert C.pad_restore_cmd("speed 0% (software control)  pad off  lights off  raw 80 00 01") == ["off"]
    assert C.pad_restore_cmd("speed 28% (software control)  lights off  raw 80") == ["speed", "28"]
    assert C.pad_restore_cmd("speed 40% (roller)  lights on") == ["release"]
    assert C.pad_restore_cmd("") == ["release"]


def test_focus_file(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    assert C.read_focus() == "auto"
    (tmp_path / "focus").mkdir()
    for text, want in [('{"mode": "away"}', "away"), ('{"mode": "x"}', "auto"), ("nope", "auto"), ("[1]", "auto")]:
        (tmp_path / "focus/mode.json").write_text(text)
        assert C.read_focus() == want
    (tmp_path / "focus/mode.json").write_text(json.dumps({"mode": "sleeping"}))
    assert C.read_focus() == "sleeping"
