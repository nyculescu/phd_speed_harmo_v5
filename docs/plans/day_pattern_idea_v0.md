# Idea note: learning daily demand patterns (M, ^, /, \, free flow, and capacity-clipped peaks) (v0)

*2026-10-04 · recorded by the v6 lead session at the author's request · **kept separate from v6**, which is now about traffic signals · status: idea only, nothing run*

## 1. The idea (author, originally from v4)

Demand over a day, and over days, follows a few recognisable shapes:

| Shape | Typical day |
|---|---|
| **M** | two peaks (morning and evening) |
| **^** | one peak |
| **/** or **\\** | weekend ramps |
| **free flow** | almost no demand |

A controller that learns these patterns could recognise early in the day which kind of day it is, and act ahead of the peaks. The author tried this in v4, narrowed the problem in v5, and then dropped the pattern idea. He does not expect a high success rate, but wants it retried with the methods developed since (pre-registered headroom gates, tuned comparators, realism checks).

## 2. Capacity-clipped peaks (author, same day)

When peak demand exceeds capacity, the measured flow cannot exceed capacity. The peaks of M and ^ are cut flat:

```
 true demand (what people want)            measured flow (what detectors count)

          /\        /\                              _______   _______
         /  \      /  \                            /       \_/       \
        /    \____/    \           ──►            /                   \
  _____/                \_____               ____/                     \____
           M day                              M day, peaks clipped:  /‾\_/‾\

             /\                                       ___________
            /  \                                     /           \
           /    \                    ──►            /             \
  ________/      \________                   ______/               \______
           ^ day                              ^ day, clipped:  /‾‾‾‾\
```

The clipped plateaus are **wider** than the true peaks: they start when demand reaches capacity and last until the queue has drained, after the true peak has passed. On an M day the valley between the peaks shrinks to a short dip (author's correction, 2026-10-04).

Consequences:

1. **The size of an over-capacity peak is invisible in counts.** It shows up only in queues, delays and travel times.
2. **The flat top outlasts the true peak,** because the queue drains at capacity after demand falls. Timing inferred from counts is late.
3. **Time-of-day plans fitted to counted volumes underestimate demand on heavy days.** This is the classic demand-vs-volume distinction [VERIFY in HCM]. It is a structural weakness of the standard comparator, and a possible source of headroom.

## 3. How it maps to the project's lessons

- **The day type is a hidden condition that lasts for hours.** By the "identification lag vs event duration" principle, a good non-learning detector should recognise it quickly, so the expected learning headroom is small. That is probably why v4 found nothing.
- **Headroom is more plausible when:**
  - (a) sensing is weak (sparse probes or CVs), so the demand level is poorly observed; or
  - (b) peaks are clipped, so counts hide the size of the problem while delays reveal it.
- **Comparators that must be in place and tuned:**
  1. time-of-day plans per calendar day type (weekday/weekend), fitted to counted volumes as in practice;
  2. pattern matching (cluster past days; choose a plan from the first hour's observations) [VERIFY literature];
  3. feedback controllers (they react to live demand and need no pattern);
  4. an informed reference that knows the true demand curve of the day.
- **Gate (as in v6):** informed reference vs the best calendar or pattern-matching rule. KILL if the gap is < 10 % (CI). No DRL before it passes.

## 4. Design cautions learned in v6 (2026-10-04)

- **Separate legitimate oversaturation from gridlock.** A heavy day queues vehicles at the network entries (still moving); gridlock means internal teleports and no movement. A stop rule based on the insertion backlog alone would wrongly abort heavy days.
- **Full-day episodes are long** (about 18 h of simulated time). Budget compute and use the thermal-aware runner (v6 `feasibility/cvsig/step2.py`).
- **Pick the plant first.** The v5 bottleneck plants failed the realism gate (queue discharge < 1,600 veh/h/lane). Any freeway or VSL variant of this idea must first pass a realism check, or move to a realistic plant.

## 5. Suggested next step (when the author chooses)

A separate desk research pass on:
- day-type and time-of-day pattern recognition for traffic control;
- demand-vs-volume clipping;
- learning-based anticipation of daily demand patterns.

Then a gate design.
