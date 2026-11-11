p = "part1.md"
t = open(p).read()
R = [
("Stage 0 sizes the delay at the merges; it gives no ceiling.", "Stage 0 only sizes the delay at the merges."),
("1. A new post hoc study (planb.md:576) with cap $3, inside the $40 / 7-day ceiling (Plan B used about $17.50 of it, V494; its own cap does not carry over, V488); one rental (V483); the seeds of section 6.",
 "1. A new post hoc study (planb.md:576) with cap $3, inside the $40 / 7-day ceiling (about $17.50 used by Plan B, V494, whose cap does not carry over, V488); one rental (V483); the seeds of section 6."),
("""Checks, in order:
- Identity and smoke (section 10): a failure stops the screen until fixed.
- T0 (section 10): a failed arm is VOID.
- Lane-end counter trace (PR-24): no control and p333, 2 seeds per cell; traced `end_stop2` samples equal the counter (plant_sweep.py:294), or it is not reported.
- PR-28 stays open (label, section 7). PR-26's drop estimator with a no-drop null (V244) is report-only: it changes no arm, rule or threshold; its hours are outside section 9.""",
"""Checks, in order (criteria in section 10):
- Identity and smoke: a failure stops the screen until fixed. T0: a failed arm is VOID.
- Lane-end counter trace (PR-24): no control and p333, 2 seeds per cell; traced `end_stop2` samples equal the counter (plant_sweep.py:294), or it is not reported.
- PR-28 stays open (label, section 7). PR-26's drop estimator with a no-drop null (V244) is report-only: it changes no arm, rule or threshold; its hours are outside section 9."""),
("""| Report-only | E by merge, slow minutes on 4a, TTT, delay on 4a, ramp 2 and its queue | tied |
| Report-only | close-following, braking at 3 m/s² | reward terms |
| Report-only | braking at 0.1 s (V367), `end_stop2`, fuel per km, jam share | outside |""",
"""| Report-only | E by merge, slow minutes on 4a, TTT, delay on 4a and ramp 2 | tied |
| Report-only | close-following, braking at 3 m/s² | reward terms |
| Report-only | braking at 0.1 s (V367), `end_stop2`, fuel per km, jam share | outside |"""),
("""- 5 %: V354's "coordination matters" rule on r2m3 at 4,600 and 5,300 (5 % against uniform 0.8 s, CI excluding 0, flow at most 0.5 % worse) and V462(1)'s delay tile; about half of E. Lower bound above 0 against each: planb.md:438.
- 3 % is dropped: the drafted "lower bound above 3 %" went with its reference; as a size it came from X1/X2 noise (planb.md:491, :519; paired SD 7-11 %, V435), against 16-17 % in S.
- No 6,000 threshold is on record.
""",
"""- 5 %: V354's "coordination matters" rule on r2m3 at 4,600 and 5,300 (5 % against uniform 0.8 s, CI excluding 0, flow at most 0.5 % worse) and V462(1)'s delay tile; about half of E. No record covers 6,000. Lower bound above 0 against each: planb.md:438.
- 3 % is dropped: the drafted "lower bound above 3 %" went with its reference; as a size it came from X1/X2 noise (planb.md:491, :519; paired SD 7-11 %, V435), against 16-17 % in S.
"""),
("- 6,000: the stored rows are 20 seeds under the training slowdown draw, paired SD 8-11 %, so 60 seeds give about ±3-4 points. Under p333, edge 3 is below 60 km/h for a median 17 of 25 minutes.",
 "- 6,000: the stored rows are 20 seeds under the training slowdown draw, paired SD 8-11 %, so 60 seeds give about ±3-4 points."),
("- 6,000 veh/h is above p333's capacity estimate (5,510-5,614 veh/h, an_delay_floor.md:43); no rule was tuned there.",
 "- 6,000 veh/h is above p333's capacity estimate (5,510-5,614 veh/h, an_delay_floor.md:43): under p333, edge 3 is below 60 km/h for a median 17 of 25 minutes (EXPLORATORY). No rule was tuned there."),
("- V355 and the CAV contract are set aside for this screen.", "- Run with V355 and the CAV contract set aside."),
]
for a, b in R:
    assert a in t, a[:60]
    t = t.replace(a, b)
open(p, "w").write(t)
