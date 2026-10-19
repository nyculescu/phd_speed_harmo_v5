# Screen D2: is there headroom for incident-adaptive ramp metering?

Status: **DRAFT (V91).** The run waits for the author's approval of this page. The outcome is **CONTINUE** or **STOP**; no claim.

**Question.** When an incident hits the bottleneck (a slowdown or a blocked lane), can a controller that adapts to *this particular* incident beat the best simple responses? The particular incident means its own start time and duration. The simple responses are a fixed rate, a tuned feedback meter, and a plan stored per incident **type**.

If even a perfectly informed per-incident response gains less than 10 %, a table by incident type is enough, and direction 2 stops.

**Lesson from D1 (V90).** A screen must first show that control *matters* in the condition being tested. Rule 1 therefore includes T4.

## Plant

- **BN4 as ported in D1** (`v5b/d1/`, commit `a23613b`): constant demand q ∈ {1600, 2000} veh/h.
- **Incidents** are added from the archive's perturbation kinds (`bn4_env.py`, `claude/vsl-lab-core` @ `2a79e5e`):
  - **slow:** the bottleneck speed limit drops to 5 m/s;
  - **block:** one lane is closed on the bottleneck edge. Implemented as a lane closure, not a stopped vehicle, because the archive's stopped vehicle caused teleports.

## Rule 1. Tool checks first

| Check | What it requires | If it fails |
|---|---|---|
| T0 | The best of the arms beats no control (NC) by ≥ 10 % in every incident cell (median paired difference, CI > 0) | STOP |
| T1 | Teleports occur in < 5 % of runs per cell | STOP, or fix the incident code with a test and re-run the checks |
| T3 | The same seed run twice gives identical results | fix, then repeat |
| **T4 (new)** | In incident runs, the hindsight-best fixed controller differs from the no-incident tuned controller by ≥ 10 % in delay (the incident changes what is best) | STOP |

## Rule 2. Incidents (fixed now)

- **Two types:** slow and block.
- **Onset:** uniform in the first third of the 900-s control period.
- **Duration:** uniform 120–480 s.
- Both are seeded per seed, so every arm sees the same incident.
- **The incident and its type are known at onset** (perfect detection), which is conservative for the fallbacks.

## Rule 3. Arms

**Controller family G** (fixed now; 35 controllers):
- the D1 constant-rate grid (19 rates);
- feedback meters with K_F ∈ {10, 20, 40, 70} × n_crit ∈ {6, 8, 10, 12} (16).

| Arm | What it does |
|---|---|
| **N** | The no-incident controller: best of G on no-incident tuning runs. Used by every arm before onset |
| **FX / FB** | Keep N's class: the best single constant rate / best feedback meter, tuned on tuning seeds with incidents mixed in; no switching |
| **IP** | At onset, switch to the best controller of G **for that incident type**, tuned on tuning seeds (a stored plan per type) |
| **OR** | Oracle: at onset, switch to the best controller of G **for this seed's incident** (hindsight; an upper bound, never a method) |
| **NC** | No meter; reference only |

## Rule 4. Metric and statistics

- **Primary:** door-to-door delay including the ramp queue. Served throughput is co-headlined; TTT is reported alongside.
- **Statistics:** paired seeds; median of paired differences; 95 % percentile bootstrap CI, B = 2,000.
- **Cells:** incident type × demand (4 cells), plus a no-incident cell (report only).
- **Invalid runs:** a cell must also pass with seeds that have invalid runs removed (as in D1, A5).

## Rule 5. Decision

- **Headroom:** HD_f = (f − OR) / f, for each fallback f ∈ {FX, FB, IP}.
- **CONTINUE** if HD ≥ 10 % with the CI's lower bound > 0 against **every** fallback in at least 1 cell. **STOP** otherwise.
- The full operating map is always reported.

## Seeds (from the approved v5.B block)

| Use | Seeds |
|---|---|
| Tool checks | 7,400,080–099 |
| Tuning | 7,400,120–139 |
| Evaluation | 7,400,140–189 (50 seeds) |
| Smoke runs during build only | 7,400,000–009 |

## Cost and operation

- **Compute:** about 35 controllers × 50 seeds × 4 cells post-onset, plus tuning. Roughly 10,000 runs at about 1 s each, so minutes to under an hour on 16 workers.
- **Operation:** the CPU guard is on, in its own systemd unit, with the fan controller `vsl-cooling` running (author-authorised, "working" profile).

## Disclosures

- **The archive's BN4 results were seen.** A learned meter beat the best tuned non-learning arm by 17–28 % under slow and block (D5.10, chapter level, old seeds). This screen asks whether that headroom comes from **per-incident** adaptation or is already captured by a per-type plan.
- **D1's STOP was seen:** on constant demand, a constant rate beats the paper-gain feedback meter.

## Addendum (2026-10-19), pending author approval

Written after a two-lens review (protocol, plant) of the build at commit `bc69707`, before any tool-check, tuning or evaluation seed ran. Each item states what the code runs, adds a check or report, or narrows a conclusion. **None makes CONTINUE easier than the page as written**, except that the meaning of "block" (A2) changes. That effect has no known direction, so the author decides it. Review probes and smoke runs used only seeds 7,400,000–009, and their outcomes were seen (disclosed). The numbers quoted from the review's probes were not re-run by the builder.

- **A1. Cross-fitted oracle (review blocker).**
  - **Problem.** The page's OR is each seed's best of 35 runs, scored on the same run it was picked from. On this plant, run-to-run noise is about as large as the 10 % bar. In a review probe on smoke seeds, the same controller differed by a median 11–24 % between two SUMO-RNG replicates. Because OR ≤ IP on every seed by construction, the CI cannot catch this. In that probe, block_q2000 passed with this OR (HD_IP 14.2 %) but not with a cross-fitted OR (−1.4 %).
  - **Rule.** For every evaluation seed and incident cell, the 35 switch runs are repeated once as a replicate. The replicate keeps the demand file and the incident window and changes only SUMO's `--seed`, to seed + 10,000,000. SUMO then redraws each driver's speedFactor and its `departLane="random"`. These SUMO seeds (17,400,140–189) lie outside every seed block; **approving this addendum approves them.** ORX is the main-run score of the target that does best on the replicate. **A cell passes only if Rule 5 passes, with and without invalid seeds, both with the page's OR and with ORX.** ORX ≥ OR on every seed, so this rule is never easier than Rule 5 alone.
  - **Reading.** A STOP stays valid. A CONTINUE needs ORX. ORX is no longer a per-seed upper bound.
  - **Report only.** Per cell: IP's main-versus-replicate noise, and HD(OR) − HD(ORX) for each fallback.
  - **Cost.** +7,000 runs. The tool checks keep the page's OR (see A4 f).
- **A2. "Block" is a crawl, not a lane closure.**
  - **What runs.** At onset, lane 4_1 (one of the 2 lanes of bottleneck edge 4, 280 m long) gets a speed limit of 1.0 m/s. Each vehicle applies its own speedFactor to that limit; a review probe logged allowed speeds of 0.57–1.54 m/s. The lane still admits traffic. Lane changing is off for every vehicle (BN4), so vehicles arriving on lanes 3_2 and 3_3 must cross the 280 m at that speed.
  - **Why.** A permission closure (`lane.setAllowed`) trapped vehicles in a build probe (smoke seed 7,400,000, q 2000, NC): 54 teleports and an undrained network.
  - **Review evidence.** A near-zero-speed closure (0.01 m/s, with time-to-teleport off or 900 s) gave 0 teleports and drained in 8 of 8 probe runs. On the same seeds, the crawl's delay was 1.3–2.4 × the closure's.
  - **Reading.** This screen's "block" is a severe crawl incident, and its results speak only about that crawl.
  - **Author's choice.** Keep the crawl (as built), or switch to the closure. The closure needs a time-to-teleport above 480 s plus the queue time, a test and a re-review.
- **A3. One switch, at onset only (narrowed conclusion).**
  - **What runs.** IP and OR switch once, at onset, and keep that target until the end of control. Nothing happens at clearance, although perfect detection makes clearance as observable as onset.
  - **Review evidence.** On smoke seeds, the per-type plan "c800 during the incident, then back to N" beat the onset-only OR in both slow cells.
  - **Reading.** A STOP therefore means only this: *no single switch at onset, chosen per incident from G, gains ≥ 10 % over FX, FB and IP*. The page's sentence "if even a perfectly informed per-incident response gains less than 10 %" is read with that restriction. A STOP does not cover responses that also act at clearance.
  - **Author's option.** Add actions at clearance for IP and OR, for example G × {stay, back to N}. This needs its own addendum, and it roughly doubles the switch runs.
- **A4. Choices the code keeps, now written out.**
  - a. Before onset, only N, IP and OR follow N's trajectory: they come from the runs "N before onset, g after onset". FX, FB and NC run their own controller from t = 0, with no switching. "Used by every arm before onset" applies to N, IP and OR only. HD_FX and HD_FB therefore include N's advantage before onset; HD_IP does not.
  - b. FX and FB are tuned on the pooled slow and block runs of the tuning seeds only, with no no-incident runs. Each run covers the whole episode.
  - c. N is the best of G per demand, by median delay, on the no-incident tuning runs. IP is the best switch target per (type, demand), by median, on the tuning seeds. Ties go to the earlier controller in G order.
  - d. Switching to a feedback meter keeps the current rate q, and the feedback law continues from there. Switching to a constant sets q. The cycle clock and the 30-s update clock carry over.
  - e. slow: the speed limit of edge 5 (one lane, 5_0) drops to 5 m/s. Slow and block share each seed's onset and duration, drawn from one seeded stream. Every incident ends inside the control period.
  - f. The tool-check arms N_t, FX_t, FB_t, IP_t and OR_t are chosen in hindsight on seeds 7,400,080–099. T0's "best of the arms" is the lowest median among OR (the page's per-seed best), IP, N, FX and FB.
  - g. T1 applies to every (condition × demand) cell, including the no-incident cells.
  - h. The primary metric is the mean, over all generated vehicles, of tripinfo departDelay + timeLoss after the drain (as in D1).
- **A5. T4 must pass in every incident cell.** The page gives no quantifier, so this is the strictest reading, as for T0. The build had coded "at least one cell". On the smoke seeds with the 7-controller subset, T4 passed in 3 of 4 cells. With the full G, the review's probe found it passed in all 4 (16.5–37.4 %).
- **A6. Grid edges are reported, not halted on.** The page states no edge rule. The report now covers N, FX, FB and IP on every grid dimension: rate 600 or 2600, K_F 10 or 70, n_crit 6 or 12. On the smoke seeds, the picks sat at f70_12. On those seeds the review extended K_F up to 250, and IP did not change. The author may turn this into a HALT, as in D1 A1; that would be stricter.
- **A7. Cost.** 29,130 runs, not about 10,000: tool checks 7,130, tuning 7,000, evaluation 15,000 (including the 7,000 A1 replicates). The estimate is 50–80 min at 16 workers; the linear estimate from smoke throughput (5.0 runs/s at 8 workers) is about 48 min.
- **A8. The meter has no amber phase.** Ported unchanged from D1, the meter goes from green straight to red. In the build smoke, 77 % of the 4,138 emergency-braking or stop events were at the meter (edge 2), all in metered runs (the review's count). The H-R4b warning therefore cannot single out incident artefacts. The result now reports, per arm and cell, the median count of these events at the meter (edge 2), on edges 4 and 5, and on edges 4 and 5 while the incident is on. Report only.
- **A9. Tool checks run once.** Every non-smoke tool-check outcome is appended to `/home/catalin/work/phd/v5b1_runs/D2_TCHECK_RECORD.json` (out path, commit, page sha256, the result of each check).
  - After a T0 or T4 failure with T3 passed, the checks are refused for good.
  - After a T1 or T3 failure, the checks may run again only at another commit (the page's "fix, then repeat").
- **A10. Operation.**
  - `--cpu-limit` defaults to 0.70 (V89).
  - HEAD and the work tree (`git status --porcelain` plus `git diff HEAD`) are re-checked after every stage and before `result.json` is written; any change stops the screen with "FIX/rerun".
  - Launch command, after approval and a commit:
    `systemd-run --user --unit d2-screen --working-directory=/srv/shared/Workspace/phd/phd_speed_harmo_v5b1 env -u SUMO_HOME OMP_NUM_THREADS=1 nice -n 19 /home/catalin/work/phd/phd_speed_harmo_v5b1_toolchain/venv/bin/python -m v5b.d2.run_screen --out /home/catalin/work/phd/v5b1_runs/screen_d2/v91 --confirm-run-once --workers 16 --cpu-limit 0.70`
- **A11. Status.** The page stays DRAFT. This addendum is pending author approval, together with the page.
