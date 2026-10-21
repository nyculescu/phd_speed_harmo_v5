"""V109 post-run spill indicator (descriptive, disclosed): a run 'spills' if its queue tail is within 50 m of the
network entry (max_queue_m >= avail_m - 50) OR its mean depart (insertion) delay is > 5 s. Prints the share per arm
and cell from rederive.py's output (Table 1 arms, clean days, runner rows). Usage: spill.py mine.json"""
import json, sys
M = json.load(open(sys.argv[1]))
ARMS = ("NC", "N", "FX", "FB", "PI", "AD", "ID", "IP", "OR_in", "ORX_4")
print("Table 1 arms: spill_new (tail50 | dep5) [old 7 m flag]; median / max depart delay s")
for c, v in M["cells"].items():
    print(c, "  ".join(f"{x} {v['realism'][x]['spill_new']:.2f} ({v['realism'][x]['spill_tail50']:.2f}|"
                       f"{v['realism'][x]['spill_dep5']:.2f}) [{v['realism'][x]['spill_old7']:.2f}] "
                       f"dep {v['realism'][x]['depart_delay_med']:.1f}/{v['realism'][x]['depart_delay_max']:.0f}"
                       for x in ARMS))
print("clean days")
for q, v in M["clean_realism"].items():
    print(q, "  ".join(f"{x} {r['spill_new']:.2f} ({r['spill_tail50']:.2f}|{r['spill_dep5']:.2f}) dep "
                       f"{r['depart_delay_med']:.1f}" for x, r in v.items()))
print("runner rows")
for c, v in M["runner_rows"].items():
    print(c, "  ".join(f"{x} {r['spill_new']:.2f}" for x, r in v["realism"].items()))
