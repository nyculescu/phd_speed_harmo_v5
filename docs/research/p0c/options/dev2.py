"""Options for undertakes on P0c, used seeds 7,419,640-645, not the check seeds. Nothing here changes the plant."""
import sys
from pathlib import Path
from v5b.fleet import plant_sweep as ps
if __name__ == "__main__":
    E = {"smooth": True, "lcAssertive": 1.4, "ease": True}
    C = {"base": {}, "p0c": E, "need3": {**E, "ease_max": 3.0}, "need44": {**E, "ease_max": 4.4}, "s8": {**E, "smooth_s": 8.0}, "s8need3": {**E, "smooth_s": 8.0, "ease_max": 3.0}, "s8need44": {**E, "smooth_s": 8.0, "ease_max": 4.4}}
    out = Path(sys.argv[1])
    ps.matrix(C, (4600.0, 5300.0), range(7_419_640, 7_419_646), out / "dev2.jsonl", 24, str(out / "rd"))
    print("done", flush=True)
