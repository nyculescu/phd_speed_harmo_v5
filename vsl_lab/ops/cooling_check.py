"""Cooling check (author, 2026-10-10): firmware vs custom laptop fan curve under a synthetic CPU load, pad at its cap.

Operations measurement only (no simulations, no seeds). Design, fixed before the run:
- load: N_WORKERS pure-Python busy loops (one thread each); 26 of 32 threads keeps system CPU below the 90 % rule;
- arms: A = firmware curves (asusctl custom curves disabled), B = custom curve CUSTOM on the Performance profile;
  blocks A B A B of BLOCK_S each; the first SETTLE_S of every block are discarded;
- pad: held at 68 % (the daytime noise cap; llano caps every write anyway) in both arms, so only the laptop curve
  differs;
- metrics per block: work rate (loop iterations / s, the throughput proxy), package throttle fraction
  (package_throttle_total_time_ms), mean CPU MHz, package temperature, laptop fan rpm;
- abort (and restore) if system CPU > 90 % for 120 s;
- restore on exit, always: custom curves disabled, pad back to its starting state (`off` if it was off at 0 %).

Run: python vsl_lab/ops/cooling_check.py OUT_DIR
"""
from __future__ import annotations

import csv
import json
import multiprocessing as mp
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

LLANO = "/srv/shared/Workspace/Hobby/Froonty/third_party/llano-v12-linux/llano.py"
PROFILE = "Performance"
CUSTOM = {
    "cpu": "40c:20%,55c:30%,65c:45%,72c:60%,78c:75%,83c:90%,87c:100%,90c:100%",
    "gpu": "40c:20%,55c:30%,65c:45%,72c:60%,78c:75%,83c:90%,87c:100%,90c:100%",
    "mid": "40c:15%,55c:25%,65c:40%,72c:50%,78c:60%,83c:70%,87c:70%,90c:70%",
}
N_WORKERS, BLOCK_S, SETTLE_S, POLL_S, PAD_PCT = 26, 300.0, 90.0, 2.0, 68
ARMS = ("A", "B", "A", "B")
HW = "/sys/class/hwmon"


def _hwmon(name: str) -> Path:
    for h in Path(HW).iterdir():
        if (h / "name").read_text().strip() == name:
            return h
    raise RuntimeError(f"hwmon {name} not found")


def _sh(*cmd: str) -> str:
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)} -> {r.returncode}: {r.stderr.strip()[:300]}")
    return r.stdout


def set_custom(on: bool) -> None:
    _sh("asusctl", "fan-curve", "--mod-profile", PROFILE, "--enable-fan-curves", "true" if on else "false")


def worker(counter, stop) -> None:
    os.nice(0)
    n = 0
    while not stop.value:
        x = 0
        for i in range(20000):
            x += i * i
        n += 1
        if n % 16 == 0:
            with counter.get_lock():
                counter.value += 16


def cpu_times() -> tuple[int, int]:
    with open("/proc/stat") as fh:
        v = [int(x) for x in fh.readline().split()[1:]]
    return sum(v), v[3] + v[4]


def mean_mhz() -> float:
    fs = list(Path("/sys/devices/system/cpu").glob("cpu[0-9]*/cpufreq/scaling_cur_freq"))
    return sum(int(f.read_text()) for f in fs) / len(fs) / 1000.0


def main(out: Path) -> int:
    out.mkdir(parents=True, exist_ok=True)
    if _sh("cat", "/sys/firmware/acpi/platform_profile").strip() != PROFILE.lower():
        print("not on the Performance profile (on battery?): abort", file=sys.stderr)
        return 2
    coretemp, asus = _hwmon("coretemp"), _hwmon("asus")
    thr = Path("/sys/devices/system/cpu/cpu0/thermal_throttle/package_throttle_total_time_ms")
    pad0 = _sh("python3", LLANO, "status").splitlines()[0]
    (out / "pad_start.txt").write_text(pad0 + "\n")
    for fan, data in CUSTOM.items():
        _sh("asusctl", "fan-curve", "--mod-profile", PROFILE, "--fan", fan, "--data", data)
    set_custom(False)
    _sh("python3", LLANO, "speed", str(PAD_PCT))
    counter, stop = mp.Value("q", 0), mp.Value("b", 0)
    procs = [mp.Process(target=worker, args=(counter, stop), daemon=True) for _ in range(N_WORKERS)]
    rows, blocks = [], []
    hot_since = None
    status = 0

    def _term(*_):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, _term)
    try:
        for p in procs:
            p.start()
        t0 = time.time()
        prev_cpu = cpu_times()
        for k, arm in enumerate(ARMS):
            set_custom(arm == "B")
            tb = time.time()
            s0 = None
            while time.time() - tb < BLOCK_S:
                time.sleep(POLL_S)
                now, c = time.time(), cpu_times()
                util = 1.0 - (c[1] - prev_cpu[1]) / max(c[0] - prev_cpu[0], 1)
                prev_cpu = c
                hot_since = (hot_since or now) if util > 0.90 else None
                if hot_since is not None and now - hot_since >= 120:
                    print("CPU > 90 % for 120 s: abort", file=sys.stderr)
                    status = 3
                    raise KeyboardInterrupt
                r = dict(wall_s=round(now - t0, 1), block=k, arm=arm, settled=int(now - tb >= SETTLE_S),
                         util=round(util, 3), temp_c=int((coretemp / "temp1_input").read_text()) / 1000,
                         mhz=round(mean_mhz(), 0), thr_ms=int(thr.read_text()), iters=counter.value,
                         **{f"rpm_{n}": int((asus / f"fan{i}_input").read_text())
                            for i, n in ((1, "cpu"), (2, "gpu"), (3, "mid"))})
                rows.append(r)
                if r["settled"] and s0 is None:
                    s0 = r
            s1 = rows[-1]
            dt = s1["wall_s"] - s0["wall_s"]
            seg = [x for x in rows if x["block"] == k and x["settled"]]
            blocks.append(dict(block=k, arm=arm, seconds=round(dt, 1),
                               iters_per_s=round((s1["iters"] - s0["iters"]) / dt, 1),
                               throttle_frac=round((s1["thr_ms"] - s0["thr_ms"]) / 1000 / dt, 3),
                               **{m: round(sum(x[m] for x in seg) / len(seg), 1)
                                  for m in ("temp_c", "mhz", "util", "rpm_cpu", "rpm_gpu", "rpm_mid")}))
            print(json.dumps(blocks[-1]), flush=True)
    except KeyboardInterrupt:
        status = status or 1
    finally:
        stop.value = 1
        for p in procs:
            p.join(timeout=5)
            if p.is_alive():
                p.kill()
        try:
            set_custom(False)
        finally:
            _sh("python3", LLANO, "off" if pad0.startswith("speed 0%") and "lights off" in pad0 else "release")
        if rows:
            with open(out / "samples.csv", "w", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=list(rows[0]))
                w.writeheader()
                w.writerows(rows)
        (out / "blocks.json").write_text(json.dumps(dict(status=status, custom=CUSTOM, n_workers=N_WORKERS,
                                                         block_s=BLOCK_S, settle_s=SETTLE_S, pad_pct=PAD_PCT,
                                                         blocks=blocks), indent=1))
    return status


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1])))
