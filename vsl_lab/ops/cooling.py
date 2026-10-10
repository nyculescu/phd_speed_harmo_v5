"""Batch fan controller (author, 2026-10-10): the llano cooling pad and the laptop's fans, following Froonty's Focus.

Design (cooling check 2026-10-10, vsl_lab/ops/cooling_check.py; author decisions the same day):
- acts only under batch load: active once system CPU (60 s mean) >= ACTIVE_UTIL, idle again after IDLE_HOLD_S below
  it; on going idle it puts back what it changed (pad to its state at activation, laptop to the firmware curves);
- Focus ($XDG_STATE_HOME/focus/mode.json, Froonty's Quick Settings toggle; missing = auto) decides the profile:
  Working / Sleeping / Auto -> laptop on its firmware curves; Away -> custom curves, adjusted automatically;
  the pad's noise cap is llano's (noise.py reads the same Focus file: 1000 rpm by day, 600 rpm quiet hours or
  Sleeping, none when Away), so this controller only asks for the speed it wants;
- pad speed: llano's fan_lut.json (the higher of the CPU and GPU rows; built from an 82-minute load x fan sweep),
  on 30 s-smoothed temperatures; rewritten only when the target moves by >= PAD_STEP or Focus changes;
- Away curves: level 0 is the cooling check's custom curve; the level rises by one (temperatures 4 C earlier, mid
  fan +10 points) when the package throttled > THROTTLE_UP of the last 2 min, and falls by one after THROTTLE_DOWN_S
  without throttling; every point is at least the firmware curve's speed at that temperature (never weaker);
- hands off: a pad write by anyone else (llano control.log `by`, e.g. Froonty) or the panic lock, or a laptop
  curve/profile change it did not make, stops it touching that device until the batch ends (idle);
- one instance (flock); a restore file lets `restore` undo a crash.

Run (own systemd scope, outside the editor's cgroup):
  systemd-run --user --unit=vsl-cooling <venv python> -m vsl_lab.ops.cooling run
  python -m vsl_lab.ops.cooling status | restore
"""
from __future__ import annotations

import csv
import datetime
import fcntl
import json
import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

LLANO_DIR = Path("/srv/shared/Workspace/Hobby/Froonty/third_party/llano-v12-linux")
LLANO = LLANO_DIR / "llano.py"
LUT_PATH = LLANO_DIR / "fan_lut.json"
CLIENT = "vsl_lab-cooling"
PROFILE = "Performance"
POLL_S, EMA_S, UTIL_WINDOW_S, GPU_EVERY_S, LAPTOP_EVERY_S = 5.0, 30.0, 60.0, 30.0, 15.0
ACTIVE_UTIL, IDLE_HOLD_S, PAD_STEP = 0.50, 120.0, 5
THROTTLE_WINDOW_S, THROTTLE_UP, THROTTLE_DOWN_S, MAX_LEVEL = 120.0, 0.05, 600.0, 3

# Performance-profile firmware curves (asusctl fan-curve --mod-profile performance, 2026-10-10, before any custom
# curve was stored): (temp C, fan %).
FIRMWARE = {
    "cpu": ((40, 10), (63, 14), (67, 24), (71, 34), (75, 42), (79, 50), (83, 65), (87, 83)),
    "gpu": ((40, 14), (63, 20), (67, 29), (71, 40), (75, 47), (79, 60), (83, 74), (87, 85)),
    "mid": ((40, 5), (63, 20), (67, 20), (71, 34), (75, 40), (79, 42), (83, 42), (87, 42)),
}
# Level 0 of the Away curves: the cooling check's custom curve (2026-10-10: throttling 20 % -> 0 %, one A/B pair).
AWAY_BASE = {
    "cpu": ((40, 20), (55, 30), (65, 45), (72, 60), (78, 75), (83, 90), (87, 100), (90, 100)),
    "gpu": ((40, 20), (55, 30), (65, 45), (72, 60), (78, 75), (83, 90), (87, 100), (90, 100)),
    "mid": ((40, 15), (55, 25), (65, 40), (72, 50), (78, 60), (83, 70), (87, 70), (90, 70)),
}


def _state_root() -> Path:
    return Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local/state")


def interp(points, x: float) -> float:
    """Piecewise-linear through (x, y) points, clamped at both ends."""
    if x <= points[0][0]:
        return points[0][1]
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0) if x1 > x0 else y1
    return points[-1][1]


def lut_target(lut: dict, cpu_c: float, gpu_c: float) -> int:
    """fan_lut.json's speed: the higher of the CPU's and the GPU's rows (a NaN reading is left out)."""
    want = [interp(lut["devices"][d]["rows"], t) for d, t in (("cpu", cpu_c), ("gpu", gpu_c)) if t == t]
    return int(round(max(want))) if want else 0


def away_curve(fan: str, level: int) -> tuple:
    """Level `level` of the Away curve for one fan: temperatures 4 C earlier per level, the mid fan +10 points per
    level; each point at least the firmware curve at its temperature; non-decreasing, within 0-100 %."""
    pts, prev = [], 0
    for t, pct in AWAY_BASE[fan]:
        t2 = t - 4 * level
        p = pct + (10 * level if fan == "mid" else 0)
        p = max(p, interp(FIRMWARE[fan], t2), prev)
        prev = min(100, int(round(p)))
        pts.append((t2, prev))
    return tuple(pts)


def curve_arg(points) -> str:
    return ",".join(f"{t}c:{p}%" for t, p in points)


def read_focus() -> str:
    try:
        mode = json.loads((_state_root() / "focus/mode.json").read_text()).get("mode")
    except (OSError, ValueError, AttributeError):
        return "auto"
    return mode if mode in ("working", "sleeping", "away", "auto") else "auto"


@dataclass
class Inputs:
    now: float
    util: float              # system CPU, UTIL_WINDOW_S mean
    cpu_c: float             # package temperature, EMA_S-smoothed
    gpu_c: float             # NaN when not read
    throttle_recent: float   # fraction of the last THROTTLE_WINDOW_S the package throttled
    last_throttle: float     # time of the last throttling seen (-inf: never)
    focus: str
    pad_foreign: bool        # someone else wrote the pad (control.log) or it is locked
    laptop_foreign: bool     # the laptop curves/profile are not what this controller set
    on_performance: bool


@dataclass
class Actions:
    pad: int | None = None         # speed to ask llano for
    pad_restore: bool = False      # put the pad back as it was at activation
    laptop_level: int | None = None  # Away curve level to apply
    laptop_firmware: bool = False  # disable custom curves (only if this controller enabled them)
    events: list = field(default_factory=list)


@dataclass
class Controller:
    lut: dict
    active: bool = False
    idle_since: float | None = None
    pad_yield: bool = False
    laptop_yield: bool = False
    pad_last: int | None = None
    focus_last: str | None = None
    level: int | None = None       # Away curve level in force (None: firmware)
    level_changed: float = -1e18

    def step(self, x: Inputs) -> Actions:
        a = Actions()
        if not self.active:
            if x.util >= ACTIVE_UTIL:
                self.active, self.idle_since = True, None
                self.pad_yield = self.laptop_yield = False
                self.pad_last, self.focus_last = None, None
                a.events.append("active")
            else:
                return a
        self.idle_since = (self.idle_since or x.now) if x.util < ACTIVE_UTIL else None
        if self.idle_since is not None and x.now - self.idle_since >= IDLE_HOLD_S:
            self.active = False
            a.events.append("idle")
            if not self.pad_yield and self.pad_last is not None:
                a.pad_restore = True
            if self.level is not None and not self.laptop_yield:
                a.laptop_firmware = True
            self.level, self.pad_last = None, None
            return a
        # pad
        if x.pad_foreign and not self.pad_yield:
            self.pad_yield = True
            a.events.append("pad: hands off (written by someone else, or locked)")
        if not self.pad_yield:
            want = lut_target(self.lut, x.cpu_c, x.gpu_c)
            if self.pad_last is None or abs(want - self.pad_last) >= PAD_STEP or x.focus != self.focus_last:
                a.pad = want
                self.pad_last = want
        # laptop
        if x.laptop_foreign and not self.laptop_yield and self.level is not None:
            self.laptop_yield, self.level = True, None
            a.events.append("laptop: hands off (curves or profile changed by someone else)")
        if not self.laptop_yield:
            if x.focus == "away" and x.on_performance:
                if self.level is None:
                    lvl = 0
                elif x.throttle_recent > THROTTLE_UP and self.level < MAX_LEVEL \
                        and x.now - self.level_changed >= THROTTLE_WINDOW_S:
                    lvl = self.level + 1
                elif x.now - x.last_throttle >= THROTTLE_DOWN_S and self.level > 0 \
                        and x.now - self.level_changed >= THROTTLE_DOWN_S:
                    lvl = self.level - 1
                else:
                    lvl = self.level
                if lvl != self.level:
                    a.laptop_level, self.level, self.level_changed = lvl, lvl, x.now
                    a.events.append(f"laptop: Away curve level {lvl}")
            elif self.level is not None:
                a.laptop_firmware, self.level = True, None
                a.events.append(f"laptop: firmware curves (Focus {x.focus})")
        self.focus_last = x.focus
        return a


# ---------------------------------------------------------------- hardware (I/O)

def _run(*cmd: str, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=30, env=env)


def llano(*args: str) -> subprocess.CompletedProcess:
    return _run("/usr/bin/python3", str(LLANO), *args,
                env={**os.environ, "LLANO_CLIENT": CLIENT})


def pad_status() -> str:
    r = llano("status")
    return r.stdout.splitlines()[0] if r.returncode == 0 and r.stdout else ""


def pad_restore_cmd(status: str) -> list[str]:
    """llano.py arguments that put the pad back to `status` (its first status line)."""
    if "pad off" in status:
        return ["off"]
    if "(software control)" in status and status.startswith("speed "):
        return ["speed", status.split()[1].rstrip("%")]
    return ["release"]


def last_control() -> dict | None:
    try:
        return json.loads((_state_root() / "llano/control.log").read_text().splitlines()[-1])
    except (OSError, ValueError, IndexError):
        return None


def pad_locked() -> bool:
    return (_state_root() / "llano/lock").exists()


def custom_enabled() -> dict:
    """{'cpu': bool, ...} from asusctl fan-curve --get-enabled (the active profile)."""
    r = _run("asusctl", "fan-curve", "--get-enabled")
    out = {}
    for line in r.stdout.splitlines():
        if ":" in line and "enabled:" in line:
            out[line.split(":")[0].strip().lower()] = "enabled: true" in line
    return out


def apply_level(level: int) -> None:
    for fan in ("cpu", "gpu", "mid"):
        r = _run("asusctl", "fan-curve", "--mod-profile", PROFILE, "--fan", fan, "--data", curve_arg(away_curve(fan, level)))
        if r.returncode:
            raise RuntimeError(f"asusctl --data {fan}: {r.stderr.strip()[:200]}")
    r = _run("asusctl", "fan-curve", "--mod-profile", PROFILE, "--enable-fan-curves", "true")
    if r.returncode:
        raise RuntimeError(f"asusctl enable: {r.stderr.strip()[:200]}")


def firmware_curves() -> None:
    _run("asusctl", "fan-curve", "--mod-profile", PROFILE, "--enable-fan-curves", "false")


def platform_profile() -> str:
    try:
        return Path("/sys/firmware/acpi/platform_profile").read_text().strip()
    except OSError:
        return ""


def pkg_temp_c() -> float:
    for h in Path("/sys/class/hwmon").iterdir():
        try:
            if (h / "name").read_text().strip() == "coretemp":
                return int((h / "temp1_input").read_text()) / 1000.0
        except OSError:
            continue
    return float("nan")


def gpu_temp_c() -> float:
    try:
        r = _run("nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader,nounits")
        return float(r.stdout.split()[0]) if r.returncode == 0 else float("nan")
    except (OSError, ValueError, IndexError, subprocess.TimeoutExpired):
        return float("nan")


def throttle_ms() -> int:
    try:
        return int(Path("/sys/devices/system/cpu/cpu0/thermal_throttle/package_throttle_total_time_ms").read_text())
    except (OSError, ValueError):
        return 0


def cpu_times() -> tuple[int, int]:
    with open("/proc/stat") as fh:
        v = [int(x) for x in fh.readline().split()[1:]]
    return sum(v), v[3] + v[4]


# ---------------------------------------------------------------- service

def ops_dir() -> Path:
    from vsl_lab.config import RUNS_ROOT
    d = RUNS_ROOT / "ops"
    d.mkdir(parents=True, exist_ok=True)
    return d


def restore(state_path: Path) -> list[str]:
    """Undo what the restore file says this controller changed; returns what was done."""
    try:
        st = json.loads(state_path.read_text())
    except (OSError, ValueError):
        return []
    done = []
    if st.get("pad_restore"):
        llano(*st["pad_restore"])
        done.append("pad " + " ".join(st["pad_restore"]))
    if st.get("laptop_custom"):
        firmware_curves()
        done.append("laptop firmware curves")
    state_path.unlink(missing_ok=True)
    return done


def run() -> int:
    ops = ops_dir()
    lock = open(ops / "cooling.lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("another cooling controller is running", file=sys.stderr)
        return 2
    state_path = ops / "cooling_state.json"
    for what in restore(state_path):
        print(f"restored after a crash: {what}", flush=True)
    ctl = Controller(lut=json.loads(LUT_PATH.read_text()))
    st = {"pad_restore": None, "laptop_custom": False}
    save = lambda: state_path.write_text(json.dumps(st))  # noqa: E731
    stop = []
    signal.signal(signal.SIGTERM, lambda *_: stop.append(1))
    signal.signal(signal.SIGINT, lambda *_: stop.append(1))

    util_win, temp_ema, gpu_c, gpu_t, laptop_t = [], float("nan"), float("nan"), -1e18, -1e18
    thr_win, last_thr, prev_cpu, prev_thr = [], -float("inf"), cpu_times(), throttle_ms()
    our_pad_time, expect_custom, laptop_foreign = 0.0, False, False
    log_path = ops / "cooling" / f"{datetime.date.today():%Y%m%d}.csv"
    log_path.parent.mkdir(exist_ok=True)
    new = not log_path.exists()
    logf = open(log_path, "a", newline="")
    log = csv.writer(logf)
    if new:
        log.writerow(["time", "focus", "active", "util", "cpu_c", "gpu_c", "throttle", "pad", "level", "event"])
    try:
        while not stop:
            time.sleep(POLL_S)
            now = time.time()
            c, t_ms = cpu_times(), throttle_ms()
            util_win.append((now, 1.0 - (c[1] - prev_cpu[1]) / max(c[0] - prev_cpu[0], 1)))
            thr_win.append((now, (t_ms - prev_thr) / 1000.0 / POLL_S))
            if t_ms > prev_thr:
                last_thr = now
            prev_cpu, prev_thr = c, t_ms
            util_win = [u for u in util_win if now - u[0] <= UTIL_WINDOW_S]
            thr_win = [u for u in thr_win if now - u[0] <= THROTTLE_WINDOW_S]
            raw = pkg_temp_c()
            if raw == raw:
                k = POLL_S / EMA_S
                temp_ema = raw if temp_ema != temp_ema else temp_ema + k * (raw - temp_ema)
            if ctl.active and now - gpu_t >= GPU_EVERY_S:   # nvidia-smi only under load (it wakes the GPU)
                gpu_c, gpu_t = gpu_temp_c(), now
            if ctl.level is not None and now - laptop_t >= LAPTOP_EVERY_S:
                laptop_t = now
                en = custom_enabled()
                laptop_foreign = (en.get("cpu") is not expect_custom) or platform_profile() != PROFILE.lower()
            entry = last_control()
            pad_foreign = pad_locked() or bool(entry and entry.get("by") != CLIENT
                                               and entry.get("time", 0) > our_pad_time and our_pad_time > 0)
            x = Inputs(now, sum(u for _, u in util_win) / len(util_win), temp_ema, gpu_c,
                       min(1.0, sum(u for _, u in thr_win) / max(len(thr_win), 1)), last_thr, read_focus(),
                       pad_foreign, laptop_foreign, platform_profile() == PROFILE.lower())
            was_active = ctl.active
            a = ctl.step(x)
            if ctl.active and not was_active:
                st["pad_restore"] = pad_restore_cmd(pad_status())
                our_pad_time, laptop_foreign = 0.0, False
                save()
            if a.pad is not None:
                r = llano("speed", str(a.pad))
                our_pad_time = time.time()
                if r.returncode:
                    a.events.append(f"pad write failed: {r.stderr.strip()[:120]}")
            if a.laptop_level is not None:
                try:
                    apply_level(a.laptop_level)
                    expect_custom, st["laptop_custom"] = True, True
                except RuntimeError as e:
                    a.events.append(str(e))
                save()
            if a.laptop_firmware:
                firmware_curves()
                expect_custom, st["laptop_custom"] = False, False
                save()
            if a.pad_restore and st["pad_restore"]:
                llano(*st["pad_restore"])
            if not ctl.active and not was_active and not a.events:
                continue
            if not ctl.active:
                st = {"pad_restore": None, "laptop_custom": False}
                state_path.unlink(missing_ok=True)
            log.writerow([round(now, 1), x.focus, int(ctl.active), round(x.util, 3), round(x.cpu_c, 1),
                          round(x.gpu_c, 1) if x.gpu_c == x.gpu_c else "", round(x.throttle_recent, 3),
                          ctl.pad_last if ctl.pad_last is not None else "", "" if ctl.level is None else ctl.level,
                          "; ".join(a.events)])
            logf.flush()
            for e in a.events:
                print(f"{datetime.datetime.now():%H:%M:%S} {e}", flush=True)
    finally:
        if ctl.active:
            if st.get("pad_restore") and not ctl.pad_yield:
                llano(*st["pad_restore"])
            if st.get("laptop_custom") and not ctl.laptop_yield:
                firmware_curves()
        state_path.unlink(missing_ok=True)
        logf.close()
    return 0


def main(argv: list[str]) -> int:
    cmd = argv[1] if len(argv) > 1 else "status"
    if cmd == "run":
        return run()
    if cmd == "restore":
        print("\n".join(restore(ops_dir() / "cooling_state.json")) or "nothing to restore")
        return 0
    print(json.dumps({"focus": read_focus(), "pad": pad_status(), "custom_curves": custom_enabled(),
                      "profile": platform_profile(), "cpu_c": pkg_temp_c()}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
