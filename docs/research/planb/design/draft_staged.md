# Plan B protocol, staged kill first (draft)

Draft of 2026-11-08 for V478. Nothing here is approved and nothing has run. Every number marked "planning" comes from stored X1/X2 rows used only as a proxy for size and cost, never as evidence (V478). Planning files: `planb/read_power/` (power, cost), `planb/staged/pilot_oc.py` and `pilot_oc.json` (pilot rule), `planb/staged/stage_cost.py` and `stage_cost.txt` (run counts).

The angle of this draft: find the cheapest honest GO or KILL. Tool checks with fixed criteria come first. Then a pilot on separate seeds that can KILL before the expensive per-cell re-tuning. The confirmatory run comes last and is read once.

```
S0 build + review ─► S1 smoke, T3, identity ─► S2 T0/T1 per cell (no control, p333, placebo; no v3w)
   ─► cells that bind ─► S3a grid re-pick (tuning seeds) ─► S3b pilot (v3w vs 23 opponents, 30 seeds)
   ─► cells with GO ─► S4 CMA-ES re-tuning per cell ─► S5 confirmatory, n = 80, read once
KILL exits: S2 (about 440 runs, laptop 20 min)   S3b (about 7,200 runs, about 3 h rented, under $1)
```

## 0. Status and decisions the author must take

Status: draft. It needs the author's decisions below and a design review (ultracode on, CLAUDE.md phase table) before it is committed. No Plan B seed, code or run exists.

| # | Decision | Recommendation | Main alternative and why it is weaker |
|---|---|---|---|
| A1 | Seed block | Approve 7,480,000-7,480,999 with the partition in §6 | 7,440,920-999 (80 free seeds in V354's block) is too small for the stages |
| A2 | Cells | B1 moving bottleneck, B2 ramp platoons, B3 demand surge (§4), at 5,300 veh/h | B4 long speed restriction: needs code and sits closest to [A3]'s "these slowdowns" |
| A3 | Intended use | Amend V&V §1 for B1-B3 before S3b, from S1-S2 evidence only | Keep V462(4)'s label: every Plan B sentence then says "outside the plant's stated intended use" |
| A4 | Opponents | 15 stored rules, up to 8 per-cell grid re-picks, a per-cell CMA-ES rule tuned for close-following (3E-C) and one tuned for delay (3E-D) | 3E-C only: halves stage-4 cost, but no opponent is tuned for delay, the metric that binds |
| A5 | MPC or scheduler (V457) | Leave both out, disclosed; the claim then says "rule-based", never "non-learning" | Build the condition-scheduled rule (about a day of build, my estimate) as a 25th opponent |
| A6 | Convergence | Checkpoint every 20 generations, stop when the best admissible rule gains less than δ, cap 100 | Cap 150: about 50 % more stage-4 cost, with no evidence it converges sooner |
| A7 | Claim rule | W in at least 1 of 3 cells, Bonferroni m = 3, arm level, delay and close-following both better than every opponent; braking a stated cost (§8) | "Every cell" (m = 1): power 14-89 % (planning), and one mild cell can sink it |
| A8 | Pilot rule | 30 seeds; GO if delay ≥ +1 % and close-following ≥ 0 % (points) against every pilot opponent | F0 (both ≥ 0): keeps more X2-like cells but kills fewer futile ones (§8.5) |
| A9 | n | 80 evaluation seeds per cell | 60: saves about 0.5 h and $0.15 for 3 cells, and loses 12-16 points of power (planning) |
| A10 | Budget | Ceiling $40 and 6 days of machine time for all stages; stop and ask if S4 would pass it | No ceiling: S4 can grow open-ended if 3E keeps falling |
| A11 | T1 threshold | The perturbation raises no-control delay by ≥ 10 %, with a 2-rung ladder fixed now | 5 %: more cells survive, but a 5 % perturbation makes "resilience" thin |
| A12 | Outline | Log Plan B as a new chapter before "Learning or adaptation?" (V459's chapter 6) | Put it inside chapter 7 "Disturbed plants": no outline change, less visible |
| A13 | Claim review | Log D1 and D8 of `docs/thesis/claim_review_round2.md` before S1 | Leave them open: Plan B runs no X1/X2 row, so they do not block it, but the thesis text needs them |

## 1. Question and claim sentence

**Question.** Under realistic perturbations it was never trained on, does the per-CAV DRL headway policy v3w give less door-to-door delay and less close-following than every tuned rule-based controller, and at what hard-braking cost?

The shape is a conditional advantage (V478, author principle): one policy against controllers tuned for each cell, read cell by cell, with the full map reported.

**Sentence if it passes** (filled from S5 only, read at the deciding level, V467):

> Under [cells won], perturbations it was not trained on [and that lie outside the plant's stated intended use, if A3 is not amended], the per-CAV DRL headway policy v3w (mean of 5 trained policies) had [x] % [CI] less door-to-door delay and [y] % [CI] fewer close-following seconds than every tuned rule-based controller tested ([k] rules, including CMA-ES rules re-tuned for that perturbation on separate seeds, [converged | stopped at 100 generations without converging]). It had [z] % [CI] more hard-braking events per vehicle served (peak ≤ −4.0 m/s²) than [named opponent]. In [other cells] it [tied | lost | was not tested because …]. No MPC or adaptive scheduler was tested.

Clauses added only if their own reading holds (§8.6, §8.7):
- "It also lost less to the perturbation than every such controller" (the word "resilience" is allowed only with this clause).
- Against no control: "… and [d] % less delay than no control, with [not more | more] close-following" (V459's reading, reported in every case).

**Sentence if it fails at S5:**

> Under [cells], perturbations it was not trained on, v3w was not shown to have both less delay and less close-following than every tuned rule-based controller. Outcome per cell: [T | L]. [Where L: it had [x] % more delay than [opponent].]

**Sentence if it stops at S2 or S3b:** see §10. A stop is reported as a null (V243, V456), with its cost.

The sentence never says "proven", "verified and validated", "safe", or names a measure that was not pre-registered (outline_v1.md:55).

## 2. Closures and intended use

### 2.1 X1 and X2

- **X1** closed under [A3] at confirmatory 3 (V395) and was then tested again in rounds 1 and 2 (round_2_result.md:239-246). **Plan B runs no X1 row.** No fourth test.
- **X2** is closed for DRL on this plant (V466; round_2_result.md:432): no further DRL training, tuning, plant change or seed round in X2. **Plan B runs no X2 row and tunes nothing in X2.** [A3]'s "tuning" is not limited to DRL (confirmatory_3.md:132), so no rule is re-tuned there either.
- The stored 3E-X1 (g003i02) and 3E-X2 (g016i21) picks are used unchanged, as transfer opponents in the new cells. Using a stored rule elsewhere is not tuning in X1 or X2.
- The stored X1/X2 rows are not read as evidence. They sized this draft (power, cost, pilot rule), and that use is disclosed.
- **Identity checks** in S1 re-run some stored round-2 rows to prove the code reproduces them, as V475's acceptance did. These are deterministic re-runs of old seeds with only bit-equality read, not a seed round. They are disclosed as such.

### 2.2 What counts as a new cell

The record does not define a cell's boundary (read_record risk 1). This protocol fixes it before data:
- A cell is new if its perturbation kind differs from X1/X2's (a tapered speed-limit drop on one edge).
- A slowdown cell (only B4, if chosen) is new only if it differs from both X1 and X2 in at least two of: edge set, limit, duration, number of events.
- Every cell must also lie outside v3w's training draw (§4.1).

B1, B2 and B3 are different kinds from X1/X2, so none of them is near [A3]'s "these slowdowns".

### 2.3 Plant change

Plan B changes no plant file. `plant_c3.json`, the network, the fleet and the share stay as they are.
- B1 and B2 use existing perturbation kinds (`truck`, `burst`) whose rung-1 specs are confirmatory 3's H1 and H2 (`docs/research/conf3/common.py:16-17`).
- B3 swaps the constant demand for a profile at the runner level, as `docs/research/conf3/demand_osc.py` did without changing frozen code (V407).
- New code (rung-2 specs, B3's profile, 3E-D's objective, the readers) is a code change. S1 proves that stored rows reproduce at the new commit.

### 2.4 Intended use (V462(4))

The V&V record's use is "steady or with tapered slowdowns (X1, X2)" at 4,090-6,000 veh/h with 50 % ALKS (plant_vv_record_v0.md:9). B1, B2 and B3 are outside it as written. V462(4) already labels H1 and H2 outside.

Two ways forward, for the author (A3):
- **Amend §1 before S3b (recommended).** Add the three kinds to the use statement, with requirements, method and evidence per kind. S1-S2 produce the evidence: a spec test like PR-13, T0, T1 "control matters" (PR-25), 1-Hz against step braking (PR-09), drain (PR-17), counter traces (PR-24) and where the effect sits (PR-28). The amendment is logged before any v3w row in a cell. Disclosed: it was made for Plan B, and S2 saw p333 against no control in the cells.
- **Keep the label.** Every Plan B row and sentence carries "outside the plant's stated intended use".

Limits that apply either way:
- B1 depends on overtaking a slow truck, so it rests on lane changing. Lane changing is a limit, not validated (PR-08).
- B2 adds load at the merges. Lane-end behaviour at ramp 2 is a gap (PR-28: 608.5 lane-end stops per run at ramp 2 against 7 at ramp 1). Close-following by road is reported so a merge-only effect is visible. Merge-conflict safety stays "not for".
- The record is still an unreviewed draft (6 met, 13 partial, 7 gap, 2 limit of 28). "Verified and validated" stays out of every sentence (V462(3)).

### 2.5 Other record items

- The outline (V459) names chapter 6 "Learning or adaptation?". Making Plan B a chapter needs a ledger entry (A12).
- Claim review D1-D9 are undecided. D8 is about frozen-policy rows in X1/X2. Plan B makes none, so D8 does not block it (A13).
- No retraining (V478). tail and sw are not run (§3.1).

## 3. Policy under test and opponents

### 3.1 Policy

- **v3w only**: learners w0u250, w1u500, w2u250, w3u500, w4u500 (round 2's checkpoints; job `round2/test/job_6c49e7e.json`). The arm is the per-seed mean over the 5 learners (round_2.md:268).
- The checkpoints were chosen on round 2's X1/X2 validation seeds. No Plan B row selects anything about v3w. Disclosed.
- **tail and sw are not run.** They are the same line of evidence and would add to m. Disclosed.
- **What v3w sees** (b_env.py:896-952): 16 local inputs. It never sees the speed limit, the demand, the time or any event. It meets B1 through the leader's speed difference, B2 and B3 through the accelerating-lane inputs (columns 14-15) and its own bin speed.
- **Fairness, disclosed:** each rule is tuned for its cell and so knows the condition class in advance. LocalRule types read 400-1,000 m of roadside speeds ahead, while v3w sees its own 200-m bin and a leader within 100 m. Both favour the rules.

### 3.2 Opponents per cell (A4, A5)

No counting filter. Every opponent counts, so the claim is harder than round 2's T2 (round_2.md:66-68). The table lists each opponent group.

| Group | Members | How tuned | Seeds | In S3b pilot | In S5 |
|---|---|---|---|---|---|
| Fixed reference | p333 (uniform 0.8 s) | not tuned | none | yes | yes |
| Stored grid rules (11) | z33133, r4a1, lr400_13_2, lr1000_16_2, lr1000_10_1, lr400_16_1, a4400_10_1, os0_10_10, os1_15_10, os1_10_0, copy | picked for X1 or X2 by confirmatory 3's grid; copy traced from baseline-v3, not tuned | 7,440,160-189 (old) | yes | yes |
| Stored CMA-ES rules (3) | 3E-T g032i20, 3E-X1 g003i02, 3E-X2 g016i21 | tuned under T, X1, X2 | 7,440,700-779 (old) | yes | yes |
| Per-cell grid re-picks (up to 8) | per form (uniform, zone, on-4a, local, adaptive-4a, own-state) the lowest close-following admissible rule; the delay opponent; the front row | confirmatory 3's procedure, run in the new cell | 7,480,100-119 | yes | yes |
| 3E-C (per cell) | ZoneOwnState, round 2's objective (close-following, delay hinge +1 % over p333) | CMA-ES, §3.3 | 7,480,120-159 | no | yes |
| 3E-D (per cell, A4) | ZoneOwnState, delay objective | CMA-ES, §3.3 | 7,480,120-159 | no | yes |
| MPC, scheduler (A5) | none by recommendation | disclosed omission | (200-299 kept if built) | no | only if built |

The 15 stored rules are 12 grid-derived rules (p333 and the 11 above) plus 3 CMA-ES rules; sources are `docs/research/baseline_v3/opponents.json` and s01_result.md:431-477. Re-picks that equal a stored rule are run once.

**Grid re-pick** (confirmatory_3.md:48-64, unchanged except the cell): all 69 tunable rules of the 70-rule grid at 5,300 on 20 tuning seeds. Admissible: median paired delay at most 2 % worse than p333 and collisions at most p333's + 1. Per form, the lowest close-following admissible rule goes forward. Also, unlike confirmatory 3, these two decide the claim:
- the **delay opponent**: the lowest median delay among rules with close-following at most 10 % worse than p333;
- the **front row**: the lowest close-following among rules with delay at most 10 % worse than p333.

**Omitting the MPC and scheduler (A5).** This is disclosed with these reasons:
- The 3E rules are already state-feedback per zone, and LocalRule types use look-ahead.
- Each rule is tuned with the condition known, which a scheduler would have to infer.
- An MPC without capacity-drop hysteresis is a straw man (docs/paper1/plan.md:515 [VERIFY the L62 source]), and METANET was stopped (D5.5).

The weak point of this argument: a scheduler can switch within a run between event and non-event periods, and a fixed per-cell rule cannot. So the claim says "every tuned rule-based controller tested", never "every non-learning controller".

### 3.3 CMA-ES re-tuning and convergence (A6)

Kept from round 2 (round_2.md:54-64, cma2.py): ZoneOwnState with 20 parameters, diagonal CMA, sigma 0.25, CMA seed 20261106, population 24, 16 seeds per generation taken in turn from a 40-seed pool. The shortlist is ranked by loss minus the generation median.

- **3E-C objective:** round 2's, unchanged. It is the pooled change in close-following seconds against p333 (%), plus 5 per % of delay above +1 %, plus 5 per collision beyond p333's. It starts from the cell's own-state re-pick. Admissible: delay at most 2 % above p333 on all 40 pool seeds, and collisions at most p333's + 1.
- **3E-D objective (new):** the pooled delay change against p333 (%), plus 5 per collision beyond p333's. It starts from p333 (every zone 0.8 s). Admissible: collisions at most p333's + 1. It has no close-following limit, so it is the strongest delay opponent the family can give.
- **Checkpoints:** at generations 20, 40, 60, 80 and 100, the 10 best distinct configurations since the last checkpoint and the current CMA mean are re-run on all 40 pool seeds. The incumbent is the lowest-loss admissible configuration seen at any checkpoint. This also fixes round 2's X1 problem, where the admissible pick came from generation 3 (V461).
- **Stop:** at the first checkpoint g ≥ 40 where the incumbent's 40-seed loss improved by less than δ since checkpoint g − 20. Proposed δ: 2 loss points for 3E-C and 0.5 for 3E-D. These are my proposals: the only noise figure in the record is a loss SD of about 8.5 points at 16 seeds for one configuration (round_2.md:60), and the paired difference on 40 fixed seeds should be smaller, which I have not measured.
- **Cap:** 100 generations. If the cap stops the search, the pick is labelled "not converged; a lower bound on this family", and the claim sentence says so.
- The generation-median statistic "last 10 against previous 10" is reported, not used to stop: the seed window moved round 2's generation medians by 18-28 points (round_2.md:62).
- 3E-C and 3E-D are tuned only for cells with a pilot GO.

## 4. Perturbation cells

### 4.1 The training draw, which every cell must avoid

v3w trained under kind `random` (perturb.py:35-39): with p = 1/3 no event, otherwise one tapered slowdown (20-s taper) on edge 3, 4 or 5 at 25-60 km/h for 60-180 s, starting at 400-1,200 s, at constant demand 4,500-6,000 veh/h by 250, share 0.5. A cell lies outside it if it is not such a single slowdown at constant demand. Steady traffic at 5,300 (S) is inside the draw and inside the intended use. S is used only as the reference row.

### 4.2 Cells

Every cell runs at 5,300 veh/h (B3: a 5,300 time average), the level of X1/X2 and of the stored opponents. Run 0-1,800 s, warm-up 300 s, on r2m3 with `plant_c3`. Geometry (corridor.py:24-48): edge 1 0-3,000 m, 2 to 3,500, 3a (ramp 1 accelerating lane) to 3,800, 3 to 5,000, 4a (ramp 2) to 5,300, 4 to 6,300, 5 to 6,800.

| Cell | Physical meaning | Rung 1 (fixed) | Rung 2 (only if rung 1 fails T1a) | Training draw | Intended use | Code |
|---|---|---|---|---|---|---|
| B1 moving bottleneck | slow heavy vehicles that others must overtake | `truck`: the first truck on edge 1 within 600 m of the entry capped at 50 km/h, every 300 s from 360 s (= H1) | 40 km/h, every 180 s from 360 s | outside (never trained) | outside (V462(4) labels H1) | none |
| B2 ramp platoons | on-ramps fed in bunches, as behind an upstream signal | `burst`: ramp departures from 300 s moved to a 120-s grid on both ramps (= H2) | 180-s grid | outside | outside (H2 labelled) | none |
| B3 demand surge | a peak arriving on a road already near capacity | profile 4,950 veh/h, 6,000 from 600 to 1,200 s, back to 4,950 (mean 5,300) | 4,600, 6,000 from 600 to 1,500 s, back to 4,600 (mean 5,300) | outside (training demand is constant per episode, V407) | outside as written ("steady"); demand stays within 4,090-6,000 | runner wrapper as demand_osc.py; spec test |

Details that matter for reading:
- **B1:** if no truck is present, the kind retries every second, so event times drift; they are logged (`pert_log`). Up to about 2 capped trucks are on the road at once at rung 1 (6.8 km at 13.9 m/s is about 490 s; my arithmetic). The run equals its unperturbed pair until the first capped truck.
- **B2:** ramp volume is unchanged, only bunched. A held departure's wait is not counted as delay, because the departure time itself moves (perturb.py:48-56). That wait is identical across arms on a seed, so paired differences are unaffected, but B2's T1a understates the platoons' full cost.
- **B3:** route shares stay 70/15/15, so ramp flows rise with the mainline. Within B3 every arm sees the same vehicles. Against S, the seed is shared but the vehicle draws may differ, because the profile changes the draw (I have not checked this). T1a and the resilience reading are therefore seed-paired, not identical until the event.
- **Realism.** Moving bottlenecks are a standard topic in traffic flow theory [VERIFY: e.g. Gazis and Herman 1992; Daganzo and Laval 2005; not read here]. Platoon arrivals at ramps from signalised arterials, and peak onset, are general traffic-engineering knowledge; no source was read [VERIFY].
- **Earlier looks, disclosed.** H1 and H2 rows exist for baseline-v3 and the grid rules (confirmatory 3's map, `baseline_v3/decide3_map.csv`), not for v3w. Unpaired medians there suggest mild effects: no control +8 % delay in both, p333 +4 % (H1) and +14 % (H2) against S. On r1m3, truck and burst formed no wave (V342). V410 ran a 4,200-5,600 step on baseline-v3, not v3w. None of these is evidence here. Each is why B1 and B2 may fail T1a at rung 1.

### 4.3 Alternatives and exclusions

| Kind | Status | Reason |
|---|---|---|
| B4 long speed restriction (edges 3, 4a, 4 at 60 km/h for 600 s, 30-s taper; rung 2 45 km/h) | alternative to any of B1-B3 | needs an edge list in `_slowdown` (a few lines); outside the draw by edge set and duration, but it is a slowdown, the kind nearest [A3]'s scope (§2.2) |
| brake (one human car brakes) | not recommended | no wave and delay within 2 % on r1m3 (V342); likely fails T1a |
| outage (V2V lost) | excluded | "Not for: V2V with latency or loss" (plant_vv_record_v0.md:11), and v3w's commands are void while it lasts (b_env.py:764-786) |
| lane closure or blocked lane | excluded | lateral and merge-conflict safety is "not for"; teleports are off, so a stranded vehicle blocks for the rest of the run; D2's closure trapped vehicles (screen_D2_incidents.md) |
| ALKS share or HDV mix change, weather | excluded | plant changes outside the 50 % ALKS use; the weather factors were calibrated on ld32, not r2m3 (V204, V206) |

## 5. Metrics

Each metric is computed by the code at the run commit. "What it counts" is my reading of that code.

| Role | Metric | What it counts | Source |
|---|---|---|---|
| Primary | door-to-door delay `all_delay` | vehicle-seconds in the system minus distance at 100 km/h; the insertion queue and unfinished vehicles included | plant_sweep.py:336 |
| Co-headline (claim) | close-following `ttc_net` | 1-Hz vehicle samples with TTC below 3 s, inside and after the window (`E30 + out_E30`); only closing pairs have a finite TTC | plant_sweep.py:331 |
| Co-headline (gate) | served flow `passed` | vehicles entering edge 4 | plant_sweep.py:329 |
| Always reported | TTT `N` | vehicle-seconds; it has the same window as delay | plant_sweep.py:29 |
| Gate | collisions | SUMO collision pairs per step. They include minGap intrusions (factor 1.0 for human cars and trucks, 0.1 for IDM/ACC) and the warm-up. `contact_steps` is reported beside | plant_sweep.py:329; read_plant risks |
| Gate | moving full-emergency events `alks_full_moving` | ALKS −9 m/s² events at ≥ 2 m/s; lane-end creep is counted apart (V377) | plant_sweep.py:141 |
| Stated cost | robust hard braking `ev4_all` | braking events (from the first 0.1-s step ≤ −3.0 to the first above it) peaking at ≤ −4.0 m/s² for cars and ALKS, plus ≤ −3.5 for trucks (`m_peak_*` bins), per run and per vehicle served | measure.py:18; s01 common_x.py:33-36 |
| Stated cost | ALKS braking past their limit `ev5_alks` | ALKS events peaking in (−9, −5] | measure.py:18 |
| Reported | `b3_step` | seconds at ≤ −3 m/s², from 0.1-s steps | plant_sweep.py:132 |
| Reported, never in a sentence | `b45_step`, `events_ge45` | speed-selective counts that sit on the −4.5 limit (s01_result.md:287-324) | s01 §4.1 |
| Location | close-following and delay by road (3a, 3, 4a, 4, 5) and by period | where an effect sits; period bins exist only for slowdowns (plant_sweep.py:152), so B1-B3 read by road | plant_sweep.py |
| Drain | `finished_pct`, the insertion queue at the end | whether the network drains; teleports cannot fire (`--time-to-teleport -1`) | plant_sweep.py:333 |

Disclosures:
- **Reward overlap.** The 1-Hz TTC < 3 s flag and braking at 3 m/s² are terms in v3w's reward (claim_review_round2.md:30, :241). A win on them is a win on what it was trained to reduce, and the sentence says so.
- **Exposure.** v3w served about 5 % more vehicles in X1 (s01_result.md §4.2). So braking is read per vehicle served as well as per run.
- **Small counts.** Close-following needs at least 20 per run lower (T2's floor), which guards against percentages on tiny counts (V393, V410).

## 6. Seeds

**Proposed block for approval (A1): 7,480,000-7,480,999.** No keyed seed at or above 7,472,000 exists in the 772,212 stored files under `v5b1_runs`. A strict-boundary git grep over all 35 refs finds no 7,48x,xxx (planb/read_record/seed_scan_summary.txt). Derived streams (kind random's +910,000, CMA seed 20261106, bootstrap 20261104) do not collide with it. Seeds are shared across cells within a stage, as in round 2.

| Range | Stage | Use | Count |
|---|---|---|---|
| 7,480,000-009 | S1 | smoke, T3 determinism, traced-equals-untraced | 10 |
| 7,480,010-029 | S2 | T0/T1 rung 1 (no control, p333, placebo, S) | 20 |
| 7,480,030-049 | S2 | T0/T1 rung 2, only for cells that fail rung 1 | 20 |
| 7,480,050-099 | reserve | S1-S2 re-runs under the bug rule | 50 |
| 7,480,100-119 | S3a | grid re-pick | 20 |
| 7,480,120-159 | S4 | 3E-C and 3E-D pool | 40 |
| 7,480,160-199 | reserve | tuning re-runs under the bug rule | 40 |
| 7,480,200-299 | S4 | MPC or scheduler fitting, only if built (A5) | 100 |
| 7,480,300-329 | S3b | pilot | 30 |
| 7,480,330-399 | reserve | none planned | 70 |
| 7,480,400-479 | S5 | confirmatory evaluation, used once, every arm and S | 80 |
| 7,480,480-999 | reserved | a later study needs its own V# | 520 |

Rules: no seed is used before approval. Pilot seeds are never reused for evidence. A re-run under the bug rule uses the same seeds and is not a new round.

## 7. Tool checks and smoke checks (criteria fixed before they run)

S1 and S2 never run v3w except in S1's determinism and smoke runs, whose outputs are compared for equality only and never read as a comparison.

### 7.1 S0: build and review

- **Code:** rung-2 specs and B3 in `common.COND` and cma2.py's `--cond`; B3's profile as a runner hook, not a plant edit; 3E-D's objective; checkpointed stopping; the S2, S3b and S5 readers. The readers reuse `conf3/common.raw` unchanged.
- **Unit tests on planted rows:** each reader reproduces a hand-computed W, T, L and KILL. The B3 profile test counts generated departures per window: the rate in each window is within 5 % of the plan (no simulation). The B2 test checks that every ramp departure at or after 300 s is a multiple of the cycle.
- **Adversarial code review (ultracode on)** before S1 and again before S3b (CLAUDE.md checkpoint).
- **Branch and worktree** for the approach (`~/work/phd/wt/planb`, from the run commit 79b889b); the stage-5 run goes from a frozen detached worktree.

### 7.2 S1: smoke, determinism, identity (about 100 runs, laptop by day)

| Check | Criterion (pass) | Fail means |
|---|---|---|
| Identity | V475's 7 stored round-2 runs reproduce on every key at the Plan B commit, with the pack on | bug: stop, fix, log |
| T3 determinism | for each cell (both rungs) and S: no control, p333, w0u250 and 3E-T on seed 7,480,000, run twice; every key equal | stop |
| Outputs carry inputs | B1: `pert_log` shows capped trucks at the spec's cap, with drift logged. B2: ramp departures on the grid. B3: per-minute entries follow the profile. Placebo: the brake events logged | stop |
| Traced equals untraced | one traced and one untraced run per cell, equal on every stored key (V386) | stop |
| Pack fields present | `m_peak_car/alks/truck` in every row | stop |
| T3 on the rental | the same identity and T3 subset on the machine of each later stage (V436, V465) | that machine is not used |

### 7.3 S2: T0 and T1 per cell (at most 340 runs, laptop by day)

Arms: no control and p333, each in the cell and in S, on 7,480,010-029, plus the placebo with no control. The placebo is V341's: a human car slows by 5 % for 1 s every 180 s. It uses the existing `brake` kind with factor 0.95 and a 1-s hold; S1 checks that this matches V341's spec.

Statistic: round 2's paired effect, median(X − S) / median(S) × 100, with a 95 % percentile bootstrap (20,000 resamples).

| Check | Criterion (pass) |
|---|---|
| T0 binds as specified | every logged event matches the spec. B1: at least 90 % of nominal events find a truck within 60 s of their time. B2: exact grid. B3: the profile test from S0 |
| T1a it hurts | no control's delay in the cell is at least 10 % above its S run, with the CI lower bound > 0 |
| T1b control matters | p333's delay in the cell is at least 10 % below no control's, with the CI excluding 0 (CLAUDE.md early KILL) |
| Null of T1a | the placebo must fail T1a; if it passes, the gate is broken: stop, fix, log |
| Drain (report) | `finished_pct` and the end queue per arm; a flag if the cell's median `finished_pct` is 5 points or more below S's |
| PR-09 (report, V&V evidence) | 1-Hz braking within 5 % of step braking for both arms |

**Ladder (A11).** If rung 1 fails only T1a, rung 2 runs on 7,480,030-049, with S re-run on those seeds. If rung 2 also fails, the cell drops. A T1b failure drops the cell without rung 2. A T0 failure is a bug, not a rung. The rung choice sees only no control and p333, never v3w or another rule. If rung 1 passes, rung 2 never runs.

**S2 exit.** The cells that pass go on. **If none passes: Plan B KILL at S2** (§10). If cells drop, m stays 3.

### 7.4 Before S3b

- The intended-use amendment, if A3 says so, is logged.
- The code review is done.
- The protocol is still unchanged, or any change is logged as a V# with its reason.

## 8. Statistics and the reading

### 8.1 Effect and CI (round 2's statistic, unchanged)

- e = sign × median(P − O) / median(O) × 100 over paired seeds. Sign −1 for delay, close-following and braking; +1 for flow. Positive means v3w is better.
- Percentile bootstrap of the paired differences: 20,000 resamples, denominator fixed, one index matrix for every comparison, `default_rng(20261104)` (round_2.md:263-268).
- P is the v3w arm: the per-seed mean over the 5 learners.
- Known weakness, disclosed: the median's bootstrap is lumpy when the per-seed differences have a gap. X1 against os0_10_10 had no seed between −1.5 and +1.7 (read_power results §1). It is kept for comparability with rounds 1 and 2 (V408: no new variants).

### 8.2 Level

- **Bonferroni m = 3**, the number of pre-registered cells, fixed now. It is not lowered when cells drop.
- Two-sided CIs at 98.33 %, read at percentiles 0.833 and 99.167.
- Within a cell, "better than every opponent on both metrics" is an intersection-union test, so it needs no correction across opponents or metrics (round_2.md:194).
- Harm is read at 95 %, because a corrected CI would hide harm (round_2.md:172-174).
- Every reading that feeds a sentence is read at 98.33 % (V467), except harm.

### 8.3 Cell outcome at S5 (per cell, against every opponent o in the cell's set)

| Outcome | Rule |
|---|---|
| **L** (harm) | against any o: delay e < −2 with the 95 % CI upper bound < 0, or close-following e < −10 with the 95 % CI upper bound < 0 |
| **W** | against every o, all of: delay lower bound > 0; close-following lower bound > 0, and median(O − P) ≥ 20 per run; flow e ≥ −0.5 (point); collisions median(P) ≤ median(O) + 1; moving full-emergency events median(P − O) ≤ max(5 % of median(O), 5) |
| **W-b** | W, but robust braking per vehicle served is more than 10 % worse (point) than some o. Still a win; the sentence leads with that cost |
| **T** | neither W nor L |

- **Braking is a stated cost, not a gate.** As a gate at a 10 % margin it would pass in only 7-39 % of studies even with X1/X2-sized effects (read_power §2). The sentence always states the largest robust-braking excess over any opponent, with its CI at 98.33 %, and the value against no control.
- **No control is never an opponent in W** (it is not a controller) and never appears alone. Its rows are in every table.

### 8.4 Study outcome

- **PASS:** W or W-b in at least one cell that reached S5. The sentence names every cell's outcome (W, W-b, T, L, dropped at S2, KILL at S3b).
- **NULL:** otherwise, including a stop at S2 or S3b.
- No cell can be added, removed or swapped after S1 starts.

### 8.5 Pilot rule (S3b, A8)

Per cell, on 30 pilot seeds, against every pilot opponent (15 stored rules plus up to 8 re-picks): **GO** if every delay point estimate is at least +1 % and every close-following point estimate is at least 0 %. Otherwise that cell is **KILLed** before any CMA-ES run. The pilot decides nothing else and its rows are never evidence.

**Planning operating characteristic.** Pilot studies were simulated by resampling 30 of the 40 stored X1/X2 seeds against the 14 stored rules, with v3w's delay and close-following effects scaled by f. Percent GO (planb/staged/pilot_oc.json, 4,000 studies each):

| Rule, 30 seeds | X1-like f = 1 | 0.75 | 0.5 | 0.25 | 0 (tie with every rule) | X2-like f = 1 | 0.75 | 0.5 |
|---|---|---|---|---|---|---|---|---|
| F1 (recommended): delay ≥ +1, close-following ≥ 0 | 98 | 92 | 51 | 1 | 0 | 73 | 49 | 15 |
| F0: both ≥ 0 | 99 | 97 | 83 | 16 | 0 | 90 | 76 | 48 |
| F2: delay ≥ +2, close-following ≥ 0 | 96 | 71 | 10 | 0 | 0 | 41 | 18 | 1 |

- The pilot opponents are not yet tuned for the cell, and the S5 opponents will be stronger. That is why F1 keeps a 1-point cushion.
- **Overall power with F1** (pilot GO × S5 power at n = 80, m = 3 from read_power): X1-like about 0.98 × 0.92 ≈ 90 % (92 % without a pilot); X2-like about 0.73 × 0.33 ≈ 24 % (33 %). For a cell at half the X1 effects, the pilot saves stage 4 in about half the cases, where S5 had at most 17 % power.
- F0 keeps more X2-like cells but sends 83 % of half-effect cells into stage 4.
- With 23 opponents instead of 14, GO rates will be lower than in this table.

### 8.6 Resilience reading (decides the word only; V343)

- For each arm a and seed: loss_a = delay in the cell − delay in S.
- R(o) = median(loss_o − loss_v3w) / median(loss_o) × 100, with the same bootstrap and level. Positive means v3w loses less.
- "Resilience" may be written for a cell only if R(o)'s lower bound is > 0 against every o.
- Otherwise the sentence says "under these perturbations", and adds: "its advantage was not shown to be larger than in steady traffic".
- R for close-following and the S-only comparison (v3w against every opponent in S) are reported beside. V395 already saw v3w's edge in steady traffic.

### 8.7 Against no control (V459, reported in every case)

- Delay at least 10 % lower with the 98.33 % CI excluding 0, and close-following not harmed under the harm rule.
- If it fails, the sentence carries the clause, e.g. "with more close-following than no control".
- Planning: this failed in X1-like rows at 3-26 % pass rates (read_power §2), so it is likely to need the clause.

### 8.8 Nulls of the statistics

| Statistic | Null and its value |
|---|---|
| T1a | V341's placebo; it must fail T1a (§7.3) |
| S5 per comparison | label-swap null (per seed, the two runs swap with probability 1/2). At m = 3, n = 40-80: false "better" 0.8-1.0 % against a nominal 0.83 % (read_power §2) |
| S5 rule (W) | 0 % under the global null; at most 1.4 % at m = 3 when only the closest opponent is null (read_power §2) |
| Pilot | GO 0 % when every effect is 0 (§8.5) |
| On S5's own rows | the label-swap null is recomputed before the reading, as a check, and reported |

### 8.9 Power at n = 80 (planning; read_power/power_tables.md, combos.md)

| Scenario | W3 power, m = 3 |
|---|---|
| X1-like effects | 92 % |
| X2-like effects | 33 % |
| X1-like at 0.75 × | 81 % |
| X2-like at 0.75 × | 12 % |
| X1-like at 0.5 × | ≤ 17 % |
| at least one of 3 cells W: all X1-like / half / all X2-like | 100 / 97 / 70 % |
| the same at 0.75 × | 99 / 85 / 31 % |

These are for 14 opponents without the floor, flow and severe gates. With up to 25 opponents, converged CMA-ES rules and cells that may be milder than X1/X2, the true power is lower. The direction is known; the size is not. Delay is the metric that binds (read_power §2).

**Reported beside, not deciding:** per-policy counts (k of 5 learners meeting W alone), round 2's T2 reading with its counting filter (for comparison), a 5 % non-inferiority bound on delay (D11), each re-picked and 3E rule against p333, and the 3E picks' values on their tuning seeds (the overfitting check).

## 9. Stages, run counts, time and cost

**Rates:**
- Rental A (V475): 59 workers, 2,450-3,050 runs/h in the batch, wall time = batch / 0.88, $0.10-0.13 per 1,000 runs.
- Rental B (V461): 244 workers. About 6,400 runs/h, derived from the 3E-X search timing, not measured directly; about $0.13 per 1,000 runs.
- Laptop (V425-V426): 1,330 runs/h, day only (CPU ≤ 40 % from 23:00 to 09:00, V432).

Counts are from `planb/staged/stage_cost.py` (all 3 cells pass every stage).

| Stage | Runs | Where | Time | Cost |
|---|---|---|---|---|
| S1 smoke, T3, identity | about 100 | laptop | about 5 min | 0 |
| S2 T0/T1, both rungs at most | 340 | laptop | about 15 min | 0 |
| S3a grid re-pick, 3 cells × 69 rules × 20 seeds | 4,140 | rental A or laptop | 1.5-1.9 h / 3.1 h | $0.41-0.54 / 0 |
| S3b pilot, 3 × 29 arms × 30 seeds | 2,610 | same machine as S3a | 1.0-1.2 h / 2.0 h | $0.26-0.34 / 0 |
| S4 3E-C + 3E-D, 3 cells, stop at G = 40 | 97,560 | rental B | 15 h | about $13 |
| S4, at the cap G = 100 | 243,720 | rental B | 38 h (rental A 91-113 h) | $24-32 |
| S4, 3E-C only, G = 40 / 100 | 48,840 / 121,920 | rental B | 7.6 / 19 h | $5-6 / $12-16 |
| S5 confirmatory, 3 × 31 arms × 80 + S 51 arms × 80 | 11,520 | rental A, one platform | 4.3-5.3 h | $1.15-1.50 |
| **Total, G = 40 / 100 (3E-C + 3E-D)** | 116,270 / 262,430 | | about 1 / 2-5 days | $12-15 / $26-34 |
| **Total, G = 150** (if A6's alternative) | 385,550 | | 2.5-7.5 days | $39-50 |

- **Kill exits:** KILL at S2 costs about 440 runs (about 20 min on the laptop, $0). KILL at S3b costs about 7,190 runs (2.7-3.3 h rented, under $1, or 5.4 h on the laptop by day). That is under 3 % of the full plan at the cap.
- **S4 sets the budget.** The CMA-ES searches are 85-95 % of all runs. One search's sequential floor is about 437 s per generation on 122 workers (V461), so 100 generations take about 12 h on their own. Six searches together on rental B are throughput-bound (the table).
- **Not costed:** build and author time; the MPC or scheduler if built; setup (about 6 % of wall time, V475); re-runs under the bug rule. Build time for S0 is my estimate of about a day plus two reviews; I have not sized it in detail.
- **Operating rules:**
  - check machine resources before each batch, and that the v6 sessions are idle;
  - the CPU guard;
  - no co-scheduling with training (V392);
  - long runs in their own systemd unit;
  - S5 from a frozen worktree, on one platform with acceptance passed (V436, V465);
  - the stored 3E-X picks and the new 3E picks reproduce on the S5 machine before S5 (round 2's check 1).

## 10. What is reported in every outcome; ledger

Every run goes into the ledger, including failed, dropped and killed ones. Raw runs go under `/home/catalin/work/phd/v5b1_runs/planb/`. Summaries go to `docs/research/results/planb_*.md`. A V# is logged at each stage gate, the same turn.

| Outcome | What is reported | Sentence |
|---|---|---|
| KILL at S2 (no cell binds) | T0/T1 table per cell and rung, placebo result, cost | "As specified, the perturbations did not raise uncontrolled delay by 10 %, so resilience could not be tested on this plant. No DRL claim." Null (V243) |
| Cell dropped at S2 | the same, for that cell | listed in the map as "did not bind at rungs 1-2" |
| KILL at S3b (no cell GO) | pilot effects against every opponent with 95 % CIs (labelled pilot, not evidence), grid re-picks, cost | "In a 30-seed pilot, v3w did not lead every rule by the pre-registered margin in any cell; the study stopped before CMA-ES re-tuning." Null |
| Cell KILLed at S3b | the same, for that cell | in the map |
| NULL at S5 | the full operating map: every cell × metric × opponent, outcome per cell, R, no control, braking, location, convergence status | §1's failure sentence |
| PASS | the same map, plus the filled sentence with every clause | §1's pass sentence |

Every report also states:
- the closures (§2), the intended-use status (amended or labelled), and the fairness notes (§3.1);
- the reward overlap, the omitted MPC and scheduler, and the 3E convergence status;
- that X1/X2 rows were used only for planning;
- the platform per stage;
- that every sentence reads its CI at 98.33 %; only the harm rule reads 95 %.

## 11. Deviations policy

- **Before S1:** changes go into the protocol by a V#, and the review sees them.
- **After S1 starts:** no change to the cells, rungs, opponents, metrics, n, m, the pilot rule or the reading. An unavoidable change is logged as a V# before the affected stage runs, with its reason. If it touches the reading after any S3b row exists, S5 needs a new seed range and a new V#.
- **Bug rule (CLAUDE.md):** a bug found after results is fixed, everything affected is re-run on the same seeds, and both outcomes are logged. A bug re-run is not a new round.
- **Platform:** one platform per stage. If a stage must move machines, it restarts on the new one, or the split is disclosed as in V465.
- **Frozen worktree:** no commit in the S5 run worktree while S5 runs (the P1 lesson).
- **Stops:** a broken null (the placebo passes T1a), an identity failure or a determinism failure stops the stage until it is fixed and logged.
- **Budget:** if S4 would pass the A10 ceiling, it pauses and the author decides.

## 12. Risks and limits

| Risk | Effect | Handling |
|---|---|---|
| B1 and B2 are mild (+8 % unpaired for no control in H1/H2) | they may fail T1a at both rungs | the ladder, then a drop; m stays 3 |
| The pilot opponents are weaker than S5's | GO overstates the S5 chance | F1's 1-point cushion; the power figures are labelled as upper bounds |
| Converged 3E-C and 3E-D are stronger than round 2's picks | at 0.75 × effects, X1-like power falls from 92 to 81 %; at 0.5 ×, to 17 % or less | reported as is; a null is a valid outcome |
| 3E keeps falling at 100 generations | the pick is a lower bound | labelled; the sentence says so; A6 alternative 150 |
| The δ values in the stop rule are not measured | they could stop too early or too late | stated as proposals; the incumbent is re-run on 40 fixed seeds; the cap bounds cost |
| Outside intended use | weakens the contribution if A3 is not amended | A3; the limits PR-08 and PR-28 are carried either way |
| B2 effects sit at the merges | lane-end behaviour at ramp 2 is not validated | close-following by road is reported; merge-conflict safety stays "not for" |
| "Resilience" overclaim | an edge also present in steady traffic would be called resilience | the word only with R > 0 against every opponent (§8.6) |
| Reward overlap | a win on a trained-on measure | disclosed in every sentence |
| The median statistic is lumpy | CI bounds jump between clusters | disclosed; B = 20,000; kept for comparability |
| Collisions include minGap intrusions and warm-up | they overstate contact | `contact_steps` beside; the gate is relative to each opponent |
| B3's vehicle draws may differ from S's | T1a and R are seed-paired, not identical until the event | stated; arms within B3 are identical |
| copy is derived from DRL policies | an examiner may not call it a rule | it is labelled; it stays an opponent (removing it would make the claim easier) |
| No MPC or scheduler | the claim cannot say "every non-learning controller" | wording fixed in §1; A5 alternative |
| Rental B's rate is derived, not measured | S4 time may differ | a rate check after the first 5 generations; the budget pause |
| The S0 build is not sized in detail | calendar time | stated as not costed |
| The H1/H2 specs were seen for other controllers | small selection risk | disclosed (§4.2); no v3w row ever existed there |
| Planning numbers are proxies from X1/X2 at 5,300 | the new cells may behave differently | every planning number is labelled; nothing in them is evidence |

**Limits that every Plan B sentence carries:** a synthetic plant, not calibrated (V245); lane changing is not validated (PR-08); lane-end behaviour at ramp 2 is not validated (PR-28); ideal V2V (PR-16); one demand level (5,300); five learners from one recipe; per-cell rules know the condition; no MPC or scheduler.
