# Parallel exploration while round 1 runs: candidates (V433)

Author, 2026-11-06 15:40: "Can we find some spots where it might be a gap that can be covered in the meantime or improved?"
Limits: no simulation or training until round 1 ends (about 2026-11-07 14:00, V392), few tokens, nothing built before the author's pick (V310).

## Where the evidence stands

```
DRL vs tuned rules (r2m3, X2 at 5,300; V396, V413 F1)
  close-following (TTC < 3 s, read at 1 Hz): 15-25 % fewer, 40 seeds, every CI clear of 0
  delay: tie, every CI includes 0; the 2 % point limit sits inside the noise
  demand step (V410, exploratory): 36-42 % fewer close-following, same delay
  demand peak (V410, exploratory): 69 % more close-following
=> the likely claim is "safer at equal delay", possibly "adapts to a demand step"
   gap A: the safety edge is measured at 1 Hz, the sampling that hid 9 m/s² braking (V367)
   gap B: the delay test fails a true tie about one time in four (F1)
   gap C: adaptation is untested on fresh seeds
```

## Candidates

**E1. Safety at step resolution (gap A).**
- Build now, without running anything: an offline meter for 0.1-s traces (TTC and DRAC per step, braking counts at 3 and 7 m/s²). Unit tests use synthetic traces only.
- After round 1: run it on the round-1 finalists and the tuned rules. Question: does the close-following edge hold at 0.1 s?
- Pros: it protects the only consistent DRL edge, or kills it cheaply before a claim rests on it. No training.
- Cons: tracing can change the run (V386), so the traced counters must equal the untraced ones. The edge may turn out to be a sampling artefact.

**E2. A delay test that a true tie can pass (gap B).**
- Compute now, one process, seconds, from existing paired results: how often round 1's rule fails a true tie at 40 seeds, and how many seeds a non-inferiority margin of 2, 3 or 5 % needs at 80 % power.
- Output: a table from which the author sets the next protocol's margin and seed count. Round 1 stays as approved.
- Pros: it removes the coin flip on delay at no CPU cost.
- Cons: the margin is the author's choice and must be fixed before any data. Used on round 1, it would look like moving the goalposts, so it applies to later rounds only.

**E3. One demand step, evaluation only (gap C).**
- After round 1's test: run the finalists and the tuned rules with one step up at mid-episode (e.g. 5,000 → 5,750, no return), on fresh seeds. No retraining.
- Pros: it is the shortest route to "adaptive" in the title, and V410 points that way.
- Cons: V410's peak profile went the other way, and the rules are state feedback too, so a tie is likely. It needs the author's OK against V408 (here one straight level changes once).

## Recommendation

E1 and E2 now: neither needs CPU to build or compute. E3 designed now and run after round 1's test, using the E1 meter on the same checkpoints.

## Alternatives considered inferior

- **Driver or CAV-share mismatch** (the plant has `sigma_scale`): a useful robustness row, but it is a new variant nobody asked for (V408). Later.
- **3E CMA-ES per-zone rule:** needed before any thesis claim, but it can only lower the odds and costs heavy compute. Tune it on the metric E1 confirms.
- **Methods-paper literature scan:** reading sources costs tokens, and every claim stays [VERIFY]. Low value per token now.
- **Training with varying demand:** the author found it not worth it (V411).
