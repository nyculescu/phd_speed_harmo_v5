"""Raise the llano pad when system CPU is high (author, 2026-11-07, V454): at 90 % or more for 1 minute, 600 rpm (12 %);
still there 5 minutes later, 1000 rpm (28 %); below 80 % for 5 minutes, speed control goes back to the pad.
llano's own noise limit still caps the speed in quiet hours. usage: pad_on_load.py [LOG]"""
import os
import subprocess
import sys
import time

LLANO = "/srv/shared/Workspace/Hobby/llano-v12-linux/llano.py"
HIGH, LOW, STEP = 0.90, 0.80, 10.0
LEVELS = (12, 28)


def cpu_times():
    with open("/proc/stat") as f:
        v = [int(x) for x in f.readline().split()[1:]]
    idle = v[3] + v[4]
    return sum(v), idle


def pad(args, log):
    r = subprocess.run([sys.executable, LLANO, *args], capture_output=True, text=True, env={**os.environ, "LLANO_CLIENT": "r2-pad"})
    log(f"llano {' '.join(args)} -> rc {r.returncode} {r.stdout.strip()[:120]} {r.stderr.strip()[:120]}")


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/work/phd/v5b1_runs/pad_on_load.log")

    def log(m):
        with open(path, "a") as f:
            f.write(f"{time.strftime('%F %T')} {m}\n")

    log("start")
    level, high_since, low_since = -1, None, None
    t0, i0 = cpu_times()
    hist = []
    while True:
        time.sleep(STEP)
        t1, i1 = cpu_times()
        u = 1.0 - (i1 - i0) / max(t1 - t0, 1)
        t0, i0 = t1, i1
        hist = (hist + [u])[-6:]
        avg = sum(hist) / len(hist)
        now = time.time()
        high_since = (high_since or now) if avg >= HIGH else None
        low_since = (low_since or now) if avg < LOW else None
        if level < 0 and high_since and now - high_since >= 60:
            level = 0
            pad(["speed", str(LEVELS[0])], log)
            log(f"cpu {avg:.2f}: 600 rpm")
        elif level == 0 and high_since and now - high_since >= 360:
            level = 1
            pad(["speed", str(LEVELS[1])], log)
            log(f"cpu {avg:.2f}: 1000 rpm")
        elif level >= 0 and low_since and now - low_since >= 300:
            level = -1
            pad(["release"], log)
            log(f"cpu {avg:.2f}: released")


if __name__ == "__main__":
    main()
