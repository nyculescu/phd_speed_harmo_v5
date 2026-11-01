"""E1 stage-0 diagnostic (V232, throw-away seeds): a `day one` run with the meter's approach rule varied.

--approach-speed and --all-close set control.APPROACH_SPEED and SKIP_SERVED = False before the run; everything else
is `day one`. Outputs go to a diagnostic folder only; adopting a variant is the author's decision."""

import sys

from v5b.fleet import control as ct
from v5b.fleet import day


def main(argv: list) -> int:
    if "--approach-speed" in argv:
        i = argv.index("--approach-speed")
        ct.APPROACH_SPEED = float(argv[i + 1])
        argv = argv[:i] + argv[i + 2:]
    if "--all-close" in argv:
        argv.remove("--all-close")
        ct.SKIP_SERVED = False
    return day.main(["one"] + argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
