> **STATUS: v1, APPROVED by the author on 2026-10-13 (V66). Binding before seed 7,400,000.** All [AUTHOR] items are answered (V58–V66, §11). Changes need a dated addendum that never relaxes a bound (§9.4).

# Protocol P0–P2 (v5.B.1): plant realism, tool checks T0–T3, inflow band and early KILL

*Revision v1, 2026-10-13: v0 of the same day, amended for V58–V65 (Amendment log). v0 is the synthesis of the drafts "kill", "rigor" and "feasible" (Appendix B), revised after a five-lens review: statistics, honesty, physics, consistency and a bidirectional pass (Appendix C, Review log). **Status: every [AUTHOR] item (§11) was answered on 2026-10-13 (V58–V65). The protocol binds once the author approves it in a commit, before seed 7,400,000.** CLAUDE.md phase table: Extra High effort, ultracode on for the design review.*

*Provenance. No project seed (7,400,000–7,419,999) was used to write it. The only simulations behind it are toy runs on seeds 1–2 on a toy network (`scratchpad/protocol/toy/`, `scratchpad/protocol/review_phys/`), never F3Z. The `v5b1` worktree and the archive checkout were read, never modified. Decisions are cited as V# (`docs/decisions.md` on `v5b1`, V1–V65, the authority; V58–V65 entered in v1). Archive files are on branch `claude/v5b-core`, written ARCH/… (checkout `/srv/shared/Workspace/phd/phd_speed_harmo_v5`, read-only).*

**Labels used throughout**
- **[AUTHOR Ax]**: an open decision, listed in §11 with options, costs, a recommendation and a deadline. The primary design below uses the recommendation; nothing is decided silently.
- **[VERIFY]**: a source not read in full (abstract, secondary source or summarising fetch only).
- **ASSUMPTION**: a threshold with no published source; its rationale is given next to it, and it is listed in [AUTHOR A24].
- **[ADDENDUM X]**: a value fixed in a dated addendum *before* the data it governs (§9.4). An addendum can never relax a bound.
- **"my arithmetic"**: a number computed for this protocol, not taken from a source.
- **FLAG**: recorded, shown in the report and used only by a named rule; never a gate unless a rule says so.

**Conventions.** SI units and euro (V20): m, s, km/h, veh/h/lane, m/s², kWh, €. "Inflow" means vehicles arriving at the network boundary (V9). **λ** is the inflow level: it scales all three streams together, and λ = 1.0 is the nominal peak of B13 (mainline 4,000, on-ramp 1 1,200, on-ramp 2 1,000 veh/h). **B0** = the all-HDV fleet with no commands (the D5.8 no-control baseline, V44). **B1** = the same vehicles with the CAV-flagged cars on plain ACC, no commands (V44). **R1–R4, O** are arms (`system_context.md` §4); **F** is the best fixed tuned rule (§6.6). The on-ramps are called **OR1, OR2** here, so that they cannot be confused with the arms R1–R4 [AUTHOR A13]. **ℓ₁, ℓ₂, ℓ₃** are the three P1 levels (§5.0). A level is **admissible** if it is not plant-invalid under the single admissibility rule of §8.8.

**Design rule.** Every phase is ordered so that the most likely failure is tested first, with the fewest runs and the least code written. v5 never obtained an artefact-free capacity drop in SUMO, and a published benchmark found none at a SUMO merge (Boukhellouf, Buisson & Chiabaut 2023 [VERIFY]). So the first gate is the capacity drop on the all-HDV fleet (B0). It needs only the plant and the metrics: no execution layer, no V2X, no arm. Every KILL in this protocol is conservative: it can stop a claim, never create one.

---

## 0 Purpose and scope

### 0.1 What the three phases decide

| Phase | Question | Possible outcomes |
|---|---|---|
| **P0** plant realism | Does F3Z with the V42 fleet break down at its bottlenecks like a real freeway (drop, discharge, onset location, waves)? Does it receive its inflow without insertion artefacts and run free of simulator artefacts? Are its energy levels plausible? Do uncommanded CAVs (B1) avoid model artefacts? Is the 0.2-s step converged enough? | PASS → P1. FAIL → STOP; pre-registered ladders only: at most two plant-model variants (road or driver model) and at most six setting changes after the original plant (k ≤ 7 counting the original, V59), each on fresh seeds (§9.2), then **P0 KILL**. |
| **P1** tool checks | T0: commands are executed as V26/V36 specify, and they bind on traffic. T1: a drop exists in the experiment scenario on fresh seeds, and control matters. T2 (report-only): best parameters vary with the inflow level. T3: determinism and common random numbers. | PASS → P2. Code FAIL → fix, no seed spent. Actuator FAIL → [AUTHOR A34], decided now. T1a FAIL → P0 FAIL path. T1b FAIL → [AUTHOR A17], decided now. |
| **P2** inflow band | At which inflow levels does the informed oracle O(ℓ) or the best fixed tuned rule F cut the generalised cost by ≥ 10 % vs B0 (V45), within the guards? | Band non-empty → **GO** for the learning phases (band and designated level frozen). Band empty → **KILL**. Two futility KILLs come earlier (§6.5, §6.6). |

**No learning arm (L1, L2) and no VSL reference arm (I1, I2) runs before P2 ends.**

### 0.2 Decision flow

```
 S0 author answers every [AUTHOR] item (§11) ──► Addendum B (VoT, prices, metric constants) committed
   │
 P0-B code acceptance: plant, inflow, health, metrics, stats, seed guard, ops,
      ACC approach pre-screen, energy tests (non-project seeds only)
   │
 P0-S smoke 7,400,000–001 ──► Addendum A (estimator and implementation fixes only)
   │
 P0-C calibration 002–009 (throw-away, disclosed) ──► futility stop F1–F5? ──► P0 FAIL path (§9.2) or STOP; no check seed spent
   │      ladders → λ_c, λ_sub, BN*, λ_a; insertion; ACC ladder; r; T3-early; CPU-time caps
   ▼      calibration report (design quantities and F outcomes only, §4.3) ──► Addendum D (CPU plan)
 P0-G1  drop + discharge, B0 only, plateau probe (010–039)            ◄── most likely FAIL: checked first, alone
   ▼ PASS
 P0-G2  onset location, waves, artefacts, insertion, desired speeds, B0 triangle (040–059)
 P0-G3  uncommanded CAV artefacts, B1 vs the same vehicles in B0 (040–059)
 P0-G4  energy (deterministic)          P0-G5  step 0.1 s vs 0.2 s, paired by seed (040–059)
   │    any FAIL ──► STOP ──► pre-registered ladders on a new seed range (≤ 2 plant variants, ≤ 6 changes after the original, k ≤ 7) ──► P0 KILL
   ▼ PASS     (exec, V2X and R4 are built only now; Addendum C committed before seed 060)
 P1 (060–089): T0a exec · T0b authority (directional) · T0c bottleneck authority · T0d sensing
               T1a drop on fresh seeds · T1b control matters · T3 determinism + CRN
   │    T0b/T0c FAIL ──► [AUTHOR A34] rule ; T1a FAIL ──► P0 FAIL path ; T1b FAIL ──► [AUTHOR A17] rule
   ▼ PASS     R1–R3 built ──► P2-B ──► checkpoint "plant and all opponents done"
 P2 stage 1 (100–107): B0, B1, every candidate, every tuned level ──► headroom ceiling (report-only)
   │    edge-level check and parameter-adequacy check ──► triggered additions on 100–107 (§6.10)
   │    KILL-1: in-sample best gain < t at every tuned level (t calibrated empirically, §6.5)
 P2 stage 2 (108–137): finalists ──► O(ℓ), F chosen on 100–137 with the band's own eligibility
   │    KILL-2: in-sample best gain < 10 % at every tuned level
   ▼    n_eval fixed (σ rule + predicted pass rate of the whole band rule, §6.7)
 P2 held-out (200–239 or 200–259): B0, B1, O(ℓ), F ──► band rule (§6.8)
        band empty ──► KILL-3 ; band non-empty ──► GO: band, map and designated level ℓ* frozen.
        Only now may a learning arm run.
```

### 0.3 Principles that bind inside this protocol
1. **Before data.** Criteria, seeds, sample sizes and statistics are fixed here. Every [AUTHOR] item is answered before seed 7,400,000 (A9 and A30 before seed 7,400,060), before any output it governs exists. Values marked [ADDENDUM] are fixed in a dated addendum before the data they govern. P0 and P1 results may feed only a dated addendum that **tightens** a bound; they never open a decision that this protocol has closed.
2. **KILL first.** The most likely failure is tested first, with the fewest runs and the least code. A KILL rule may only stop a claim.
3. **Intersection-union.** All gated criteria of one check must pass. For an "all must pass" rule no multiplicity correction is needed or taken (an intersection-union test keeps level α without one).
4. **Union claims are corrected.** "At least one level", "at least one rule" or "at least one arm" claims use Bonferroni (α/m), with m stated per family (§8.3).
5. **Nothing is dropped.** Every run goes into the ledger. FAIL, invalid and collapsed runs count against the arm that produced them (V6; ARCH docs/lab/t1_bn4_plant_checks_protocol.md:64). An operations failure (a hung or killed worker, §2.7) is re-run once on the same seed and logged; it is never scored as the arm's failure and never silently dropped.
6. **Bounds are never relaxed after data** (ARCH docs/lab/t2_zipmerge_protocol.md:38; ARCH docs/lab/gate_ctx_r6/s1_protocol.md:164-166).
7. **Not computable = FAIL** for every gated statistic (ARCH docs/lab/t2_realism_protocol.md, Addendum A).
8. **Fresh seeds for every new round** (CLAUDE.md). A seed guard in code refuses any seed outside its role (§7).
9. **Never B0 alone.** From P1 on, every table shows B1 and the tuned rules next to B0 (CLAUDE.md, Metrics).
10. **No continuous model parameter is fitted to pass a realism check.** Calibration fixes design quantities (levels, cells, references) by rules written now. Choosing among **pre-registered discrete candidates** (the insertion configurations, the ACC candidates A0–A3, the step) on the throw-away calibration seeds, and confirming the choice on fresh check seeds, is allowed and disclosed; every look is counted in the settings counter k (§9.2) and reported. V36's "calibrated ACC base model" is read as this selection [AUTHOR A11]. Driver, truck and energy model parameters are never tuned towards a realism band (that would make the check circular).
11. **Counted, not hidden.** Every plant setting tried on check seeds, every ACC candidate screened, and every addendum is listed in the phase report with its seeds and outcome.

### 0.4 Expected outcome, written before data (my judgement, not a measurement)
- **P0-G1 is more likely to FAIL than to PASS**, most probably on the discharge floor or on a drop outside the band. Archive SUMO freeway plants (merges, zippers, lane drops, BN4) discharged 900–1,632 veh/h/lane at their bottlenecks (ARCH docs/lab/STATUS.md:70; t2_zipmerge_protocol.md:31-35; t2_realism_d3.md:7-10; t2_realism_ld3.md:8). A SUMO merge benchmark found no capacity drop (Boukhellouf et al. 2023 [VERIFY]). On paper the first bottleneck is now **BN-LD**, the zipper lane drop at the downstream end of Z3 (V64, §2.1). Archive zipper bottlenecks discharged from stopped queues below the floor (the "metronome", §2.1), so moving the first bottleneck to the zipper does not lower this risk (my judgement).
- **P0-G3 with the SUMO ACC defaults (A0) is expected to FAIL**, and A0 is also expected to fail the ACC approach pre-screen (§2.6 C4). In the toy (not F3Z), a lone ACC CAV at 27.78 m/s approaching a slower leader first braked at a 98.5 m gap, at −6.06, −5.12 and −4.33 m/s², beyond its own 4.5 m/s² decel, with no cut-in; the EIDM HDV's minimum in the same scenario was −1.71 m/s² (toy a_L0_free_slower_leader_cav.csv; whether this is an ACC mode switch near 100 m is [VERIFY]). In mixed toy traffic (3 → 2 lanes, 30 % ACC, 0.2 s) the CAV/HDV ratio of per-step severe deceleration depends on how the 4.5 m/s² decel cap is counted: 3.1–3.7 counting steps at or beyond the cap, 9.1–11.9 counting "a ≤ −4.5 m/s²" (floating-point rounding then decides whether 9–26 % of the at-cap steps count), 11.5–16.6 counting steps strictly beyond the cap (scratchpad review_phys/knife.py, seeds 1–2; my arithmetic). Hence the event definition is [AUTHOR A28]. About 67 % of toy events came within 1 s of a leader change (toy b_diag.py), so about a third were not cut-ins.
- **λ = 1.0 is probably far over capacity and drain-capped** on F3Z (§2.1 desk estimate), so it may be plant-invalid or fail the band guards by construction [AUTHOR A6]. V64 moved the lane drop but kept its two lanes, so this still holds (A26 superseded by V58/V64).
- **If P0 passes, a P2 KILL is more likely than a GO.** The archive found authority only in narrow bands just above critical (ARCH docs/review/design_space/notes_networks.md:392), and published hybrid gains over fixed-parameter controllers are about 1.5–6 % (CLAUDE.md prior).

---

## 1 Decisions implemented

Every V# of `docs/decisions.md` has a row, including the superseded and pending ones.

| V# | What it fixes in this protocol | Where |
|---|---|---|
| V1, V7, V17, V51 | Branches, the trainer and planned profiles: outside P0–P2 | — |
| V2, V56 | Network F3Z, evolved from CORR2X v3; zones Z1 2.0–3.0, Z2 3.5–4.5, Z3 5.0–6.0 km (V64), provisional. A later zone move applies to every arm and re-runs P1 and P2 on fresh seeds; P0 is unaffected (B0 and B1 carry no commands) [AUTHOR A34] | §2.1, §9.5 |
| V3, V26, V36, V47 | Per-CAV ±5 km/h commands every 2 s; `slowDown` over 2 s, then `setSpeed` hold; `setSpeed(−1)` release on zone exit [AUTHOR A10]; target in [50, 100] km/h; entry target = current speed rounded to 5 km/h, reached by a `slowDown` ramp | §2.5, T0a |
| V4, V44 | No control: no speed set for any vehicle, no limit below 100 km/h. B0 and B1 both run and reported; the final candidate must beat both, B1 by at least 5 % (V61) | §2.3, §6.8 |
| V5 | **Superseded by V15** (no lane limits). Its speed-mode finding is kept for reference; speed mode stays 31 | §2.5 |
| V6 | Invalid run = more than 2 collisions or any teleport; it counts as that arm's failure on that seed | §2.7, §8.4 |
| V8, V48 | No pause gate (every commanding arm acts in warm-up, window and drain); no clock in any observation | §2.5, T0d |
| V9 | "Inflow" vocabulary | throughout |
| V10, V23, V24, V53 | Energy per vehicle-km and scenario totals; HDV energy labelled "estimated"; electricity at the battery, no charging loss; **power traces logged for a pre-declared subset of runs** (§10.4) [AUTHOR A35] | §3.1, P0-G4, §6.12, §10.4 |
| V11 | CAV hard braking measured. HDV hard braking is a placeholder (V11): used only as a **plant diagnostic** in P0 (the G3 comparison, P0-R7) and as report-only rows in P2 [AUTHOR A29] | §3.1, P0-G3, §6.12 |
| V11, V25, V36 | CAV hard braking: a stretch with deceleration below −3 m/s², per CAV-km; a constraint vs B1, not a price. Speed condition (B14 "safety counted at speed") [AUTHOR A28] | §3.1, §6.8 |
| V12 | The first plant runs are the P0 smoke on throw-away seeds | §4.2 |
| V13 | **Superseded by V30** | — |
| V14 | Own toolchain (v5b1 venv, SUMO / libsumo 1.27.1) | §2.2 |
| V15, V27 | CAV commands are the only actuator; no meters, no VSL, no loop detectors for arms. Virtual detectors exist only in the metrics and realism code. What zone-spec arms may know about BN-LD, the expected first bottleneck at Z3's downstream end (V64): a V2X summary unit just downstream of the drop ([AUTHOR A30], decided by V65) | §2.1, §3.2, T0d |
| V16, V29 | Headline C = generalised cost in € per vehicle-km over all vehicles, fixed denominator | §3.1 |
| V18 | **Closed** by the V18 update in `decisions.md` ([AUTHOR A35], V65): the §3.1 definitions of cohort, reference time, cut-off, window and stop-and-go | §3.1 |
| V19 | Rule comparators open: R1–R3 parameter spaces fixed in Addendum C before any commanding-arm run | §6.3 |
| V20, V21, V54 | SI and €; Irish retail energy prices (price date recorded in Addendum B); truck VoT = work VTT × 1.03 | §3.1, Addendum B |
| V22 | Network inspired by the M50. The MnDOT shape on an M50-inspired network is a disclosed mismatch (V22 update in `decisions.md`, [AUTHOR A35]); the discharge floor vs Irish data: 1,600 veh/h/lane ([AUTHOR A25], V65) | §2.4, P0-G1 |
| V28, V34 | Truck energy = road-load + Willans in our code (HBEFA4 HDV classes not used); COPERT and the TII OGV fuel function as sensitivity rows, with sign agreement reported | P0-G4, §6.12 |
| V30 | Network maximum 100 km/h (27.78 m/s) | §2.1 |
| V31, V45 | Inflow sweep; band = levels where O or the best non-learning rule cuts C by ≥ 10 % vs B0; rule fixed before the sweep, non-learning arms only | §6 |
| V32, V39, V55 | VSL comparators I1/I2: not in P0–P2 | §12, [AUTHOR A21] |
| V33 | **Superseded by V42** | — |
| V35, V38, V46 | HEV + PHEV = SUMO petrol PHEV pair, one mode per trip, 50 % electric | §2.3 |
| V37 | Delay guard: network delay not worse than B0 by more than 2 %; its test form [AUTHOR A27] | §6.8 |
| V40, V41, V42, V43 | 7.5 % heavy vehicles at 90 km/h; all-HDV first baseline; 2025 new-sales car mix; CAVs = 50 % of electrified + hybrid cars; HDV car desired speeds | §2.3 |
| V49 | Episode: 15 min warm-up, 2.5 h scored window, drain ≤ 30 min | §2.4 |
| V50 | V2V range 300 m; the 5 nearest CAVs ahead, plus count and mean speed of all heard ahead | T0d |
| V52 | Reward and controller type open during exploration: not used in P0–P2 | §12 |
| V57 | External source research (Console) may resolve [VERIFY] items. A value it changes enters only through a dated addendum before the data it governs; Claude Code spot-checks every citation first | §9.4 |
| V58, V64 | Road redesign so that the first jam forms inside the zones: the 3 → 2 lane drop moves to 6,000 m, the downstream end of Z3; merge 2 at 4,500–4,750 m; Z3 5,000–6,000 m. BN-LD is the expected BN*. Supersedes [AUTHOR A26] | §2.1, §3.2, §9.2 |
| V59 | [AUTHOR A1]: at most 2 variants ("road variants" in V59) and 6 setting changes, each on fresh seeds, then P0 KILL; never continue with a disclosed realism FAIL | §9.2 |
| V60 | [AUTHOR A11]: ACC ladder A0–A3, with A3 (IDM-based ACC) allowed | §2.6 C4, §4.6 |
| V61 | [AUTHOR A7]: the band arm must be at least 5 % better than B1 in C | §6.8 (d) |
| V62 | [AUTHOR A16c]: re-round seeds 7,401,000–7,401,999 approved | §7 |
| V63 | [AUTHOR A31]: no non-learning adaptive scheduler in P2, disclosed | §6.11 |
| V65 | Every other [AUTHOR] item takes its recommendation; A6, A13, A26 and A30 are re-read for V64 | §11 |
| B12, B13, B14 (draft inputs, ARCH docs/v5b/design_v0.md §2) | Shape "triangle-ish, fast rise to about 07:50, slower fall"; peaks 4,000 / 1,200 / 1,000 veh/h; safety counted at speed. Not yet V-decisions | §2.4, [AUTHOR A12, A28] |

### 1.1 Conflicts and gaps in the binding inputs (each recorded as a decision before the data it governs)
*v1: every [AUTHOR] item named below was answered on 2026-10-13 (V58–V65; §11, Decision column).*
1. **Hold mechanism.** V36 (decided) says "`slowDown` over 2 s, then `setSpeed` to hold". `interfaces.md` §3 still says "re-issuing `slowDown(target, 2.0)` holds it", and its Entry row does not say how the rounded target is reached. Both holds are exact in the toy (max deviation 0.000000 km/h; toy summ_a.py A2, A3). This protocol implements and tests V36, with the entry target reached by a `slowDown` ramp (§2.5). [AUTHOR A9]: correct `interfaces.md` §3 (done in v1, V65).
2. **Reference-time class.** `interfaces.md` §5.2 defines r(route, class) but not "class". If it means the driver class, the same vehicle has different references in B0 (HDV) and B1 (CAV), which biases C across arms. [AUTHOR A8]: (a), `interfaces.md` §5.2 amended in v1 (V65).
3. **V42 arithmetic.** The five sales shares sum to 98.39 %. Renormalised, HDV cars are 60.0 % ICE (my arithmetic); V42 says "about 59 %", which matches keeping the 1.61 % residual inside the HDV cars (58.7 %). [AUTHOR A13]: renormalise (V65); V42's wording in `decisions.md` is not amended by this protocol.
4. **Desired speed of CAVs in B1** is not specified anywhere, and it changes B1 − B0 and every commanding arm's delay vs B0 (§2.3). [AUTHOR A13].
5. **"The realistic level"** (D5.8; CLAUDE.md early KILL) is undefined under the V31 sweep, and on paper λ = 1.0 exceeds F3Z's capacity (§2.1; still true under V64, whose drop keeps two lanes). [AUTHOR A6]: the designated level ℓ* (V65); A26 superseded by V58/V64.
6. **VoT in 2026 €** is still [TBD] (`interfaces.md` §5.4). The PAG category is already fixed there (cars: commuting €8.90 per person-hour × 1.23 occupancy; trucks: work VTT × 1.03, V54); only the uplift to 2026 € is open. It needs no data, so it is frozen in Addendum B **before seed 7,400,000**. [AUTHOR A18].
7. **Archive runner defaults** that would silently change results: step 0.5 s default, `collision.check-junctions false`, collisions counted per vehicle-step and FAIL on any collision (against V6's > 2), a determinism hash over aggregates only (port_map_v0.md runner traps 5, 7; corr_run traps (a)–(c)). §2.2 and §2.7 fix each.
8. **Truck fuel price.** V21 prices are retail incl. taxes; TAF §8.11.3 treats work fuel net of VAT (irish_parameters_v0.md §2). [AUTHOR A18] (report-only sensitivity row).
9. **Invalid runs beyond V6.** V6 lists collisions and teleports only. This protocol also counts the other §2.7 health FAILs as invalid runs of their arm, and separates operations failures (re-run once) from plant collapse (arm FAIL). [AUTHOR A19].
10. **Per-episode inflow noise.** `interfaces.md` §4 [PROPOSAL] includes it; this protocol switches it off in P0–P2. [AUTHOR A12].
11. **B12/B13/B14** are draft inputs, not V-decisions (decisions.md header). [AUTHOR A12, A28].
12. **ACC base model.** `system_context.md` §3 says "SUMO ACC, calibrated"; ladder candidate A3 (§2.6) departs from it, and "calibrated" names no target. [AUTHOR A11].
13. **Truck length.** The archive `_IDM_TRK` uses 12 m; V40 describes a 40 t articulated vehicle. [AUTHOR A13].
14. ARCH design_v0.md §3 lists "trucks 10 %"; V40 (7.5 %) supersedes it and is used here.
15. **Headline vs co-headline.** v5b1 CLAUDE.md (Metrics) makes door-to-door delay including origin queues the primary metric, co-headlined with served throughput; V29 (decided, more specific and newer) makes the generalised cost C the headline. This protocol follows V29 for the band rule, and shows network delay Dl, origin-queue time and **served throughput with its CI** in every band table (§6.8, §6.12). Recorded, not an [AUTHOR] item, because V29 is decided.
16. **Hard-brake speed condition.** V36 fixes 3 m/s² with no speed condition; draft input B14 says safety is counted at speed (zipper-queue creeping is not a safety event). [AUTHOR A28].
17. **V18 (pending) and V22 (open item).** The metric definitions of §3 close V18 only if the author says so; V22's open question (does the MnDOT shape fit an M50-inspired network) is not answered by any decision. [AUTHOR A35].
18. **Release on zone exit.** V36 and `interfaces.md` §1/§3/§9 release CAVs with `setSpeed(−1)` at zone exit. A gentler release would be a command outside a zone and would amend them. [AUTHOR A10].
19. **Non-learning adaptive scheduler.** CLAUDE.md (Method, headroom) includes one in "best non-learning" and makes only the MPC optional. None is built here. [AUTHOR A31]: dropped from P2, disclosed (V63).
20. **Geometry vs nominal inflow.** In v0 the first bottleneck on paper lay downstream of every zone (the two lanes after merge 2). V58 asked for a road redesign so that the first jam forms inside the zones, and V64 moved the 3 → 2 lane drop to 6,000 m, the downstream end of Z3 (§2.1). The B13 nominal inflow still exceeds the lane-count capacity of the two lanes after the drop by about 32–65 % (§2.1). [AUTHOR A26] is superseded by V58/V64.

---

## 2 Plant and fleet as built

*Nothing is built yet on `v5b1`. This section is the specification the port must meet. P0-B checks the built artefacts against it, and the P0 report replaces "as specified" with the built values and hashes. If a value changes after a check has run, that check is re-run on fresh seeds.*

### 2.1 Network F3Z (V2, V30)
Ported from ARCH vsl_lab/netgen/corr2.py `SPEC_AUX` (CORR2X v3) and trimmed per `port_map_v0.md`: v_main changed from 33.33 to **27.78 m/s** (V30); TLS meter nodes, the all-green program, ALINEA loops and the O1 branch removed (V15); the spec passed explicitly; a mandatory spec hash (port_map corr2 traps 1–4); every edge given an explicit nominal length (ARCH notes_networks.md L1: MRG3 edges drifted to 465.6 m instead of 500 m without explicit lengths). **Layout per V64** (the road redesign of V58, 2026-10-13): the 3 → 2 lane drop moved from 4,500 m (between Z2 and Z3 in v0) to 6,000 m, the downstream end of Z3; merge 2 moved from 5,750–6,000 m to 4,500–4,750 m and has four lanes (auxiliary lane + 3); the mainline has three lanes from 0 to 6,000 m and two from 6,000 to 9,250 m. Edge ids and split points inside a section of constant lane count are provisional and fixed at the port; the x ranges, lane counts and zones are V64's.

| Edge | x from–to (m) | Lanes | Role |
|---|---|---|---|
| m0, m1, m2 | 0–1,500–2,500–3,000 | 3 | entry; **Z1 = 2,000–3,000** |
| merge1 | 3,000–3,250 | 4 (aux lane 0 + 3) | **BN-M1**: OR1 joins; aux lane 0 continues as off-ramp X1 |
| m3 | 3,250–4,500 | 3 | **Z2 = 3,500–4,500** |
| merge2 | 4,500–4,750 | 4 (aux lane 0 + 3) | **BN-M2**: OR2 joins; aux lane 0 continues as off-ramp X2 |
| m4, m5 | 4,750–5,000–6,000 | 3 | **Z3 = 5,000–6,000** |
| zipper node | 6,000 | 3 → 2 | **BN-LD**: lanes 0, 1 → 0; lane 2 → 1 |
| m6, down | 6,000–7,250–9,250 | 2 | exit |
| OR1o → OR1, OR2o → OR2 | 200 m + 400 m | 1 | on-ramps, 25 m/s (archive spec; re-confirm at the port); no traffic light (V15) |

- **Routes** (ARCH vsl_lab/plants/corr2.py:49-53): 10 % of mainline-origin vehicles leave at X1, 10 % at X2; 10 % of OR1 vehicles leave at X2; OR2 vehicles all continue [AUTHOR A13].
- **Zones** are defined by the mainline position x of the vehicle front, not by edge id (zones split edges; review_v0 EX-C6).
- **Bottleneck reference points** x_k, taken from the built net and recorded with the network hash before calibration: BN-M1 = end of the merge1 auxiliary section (nominal 3,250 m); BN-M2 = end of the merge2 auxiliary section (4,750 m); BN-LD = zipper node (6,000 m). **Bottleneck groups** for onset location: [x_k − 750, x_k + 250] m, i.e. [2,500, 3,500], [4,000, 5,000] and [5,250, 6,250] m (non-overlapping). **Entry group**: [0, 1,000] m.
- **Desk estimate per section, not measured** (my arithmetic from the route shares above; lane-count capacity only, with c = 1,600–2,000 veh/h/lane; weaving and uneven lane use lower these values; ARCH design_v0.md §3 gives 3,800–4,000 veh/h for two lanes, i.e. c = 1,900–2,000):

  | Section | x (m) | Lanes | Flow at λ (veh/h) | Per lane | λ at which flow reaches lane-count capacity |
  |---|---|---|---|---|---|
  | m0–m2 (entry) | 0–3,000 | 3 | 4,000λ | 1,333λ | 1.20–1.50 |
  | merge1 weave (BN-M1) | 3,000–3,250 | 4 | 5,200λ in; 1,200λ move left (OR1), 400λ move right (to X1) | 1,300λ | 1.23–1.54 before the weave penalty |
  | m3 | 3,250–4,500 | 3 | 4,800λ | 1,600λ | 1.00–1.25 |
  | merge2 weave (BN-M2) | 4,500–4,750 | 4 | 5,800λ in; 1,000λ move left (OR2), 520λ move right (to X2) | 1,450λ | 1.10–1.38 before the weave penalty |
  | m4–m5, after merge 2 (Z3) | 4,750–6,000 | 3 | 5,280λ | 1,760λ | 0.91–1.14 |
  | **m6 and down, after the lane drop (BN-LD)** | 6,000–9,250 | 2 | **5,280λ** | **2,640λ** | **0.61–0.76** (0.72–0.76 at design_v0's c) |

  Consequences, all labelled as desk expectations:
  - **BN-LD binds first on paper**, at the downstream end of Z3, as V58 intended. BN* (chosen from data in C2) is therefore expected to be BN-LD, and under the §9.2 order rule V-2 would come first after a G1 or T1a FAIL.
  - The next tightest section, the three lanes after merge 2 (m4–m5; Z3 lies on m5), reaches its lane-count capacity only near λ ≈ 0.91–1.14; m3 and the two weaves come later still. Below λ ≈ 0.91 the bottlenecks therefore do not interact much: on paper BN-M1 and BN-M2 cannot starve BN-LD. Once BN-LD is active, its queue grows upstream through Z3 towards merge 2 (the end of the merge2 auxiliary section lies 1,250 m upstream of the drop) and beyond; a queue spilled back into merge 2 is not an active onset at BN-M2 (§3.2, downstream-probe test). The drop estimators still exclude upstream starvation (§3.2), which matters near and above λ ≈ 0.91.
  - λ = 1.0 puts 1.32–1.65 times BN-LD's lane-count capacity on m6, while the three lanes after merge 2 carry 0.88–1.10 times their own. A point-queue model of the drop on the §2.4 triangle (desk estimate: one queue, no spatial storage, travel times ignored; scratchpad protocol_v1/desk_v64.py) leaves about 1,400 / 2,010 / 2,670 vehicles queued when inflow stops at 9,900 s, at a discharge of 1,900 / 1,750 / 1,600 veh/h/lane; they need about 22 / 34 / 50 min to drain, against the 30-min cap (V49). The three lanes from the end of merge 2 to the drop hold only about 500 vehicles at a jam spacing of 7.5 m (SUMO's default car length 5 m plus minGap 2.5 m; ASSUMPTION, trucks ignored), so at λ = 1.0 the queue would reach back through merge 2, Z2 and merge 1 (V64), at the lowest discharge possibly to the entry. **λ = 1.0 is therefore likely drain-capped, with spillback far upstream** [AUTHOR A6; A26 superseded by V58/V64].
  - λ_c may lie near or below 0.6, the lowest rung of the C1 ladder, so C1 has a downward extension and a rule for an undefined λ_c (§2.6).
  - This is why the P2 grid is anchored on the measured critical level, with λ = 1.0 always kept as a reported row (§6.2). Both stay under V58/V64 (A26 superseded).
- **The lane drop is a SUMO zipper node** (ARCH vsl_lab/netgen/corr2.py:63, :123), kept at its new position (V64; a drop without the zipper is not a pre-registered variant, §9.2). Archive zipper bottlenecks discharged from stopped queues at near-fixed headways below the floor (BN4 "a metronome… releasing vehicles one at a time from a stopped zipper queue", ARCH docs/lab/gate_ctx_r6/report_S1_20261004-1508.md:57-59; ZM3 1,528 veh/h/lane, ARCH STATUS.md:57), and most raw SUMO emergency-braking warnings in the CORR2X replay were zipper-queue creeping (B14, ARCH design_v0.md:43). Hence the per-lane discharge FLAG at BN-LD, now the expected primary bottleneck (§3.2), and the location and speed attribution of braking events (§2.7, [AUTHOR A28]).
- **Stranding.** Lane 0 of merge1 continues to X1, so for OR1 vehicles bound for m3 the auxiliary lane still ends on their route: stranding at the end of the merge area stays possible, and its detector stays (§2.7). Dead-end acceleration lanes are never reintroduced (port_map trap 12; ARCH STATUS #15).

### 2.2 SUMO configuration (every option explicit; never changed to pass a check, except through the pre-registered discrete ladders of §2.6 and §9.2, each change counted in k)

| Option | Value | Reason |
|---|---|---|
| version | SUMO / libsumo 1.27.1, `toolchain/requirements_lock.txt` (V14) | determinism scope (T3) |
| `--step-length` | **0.2 s** | ACC/CACC emergency-braking artefacts at 0.5 s (ARCH STATUS #14); EIDM docs give 0.05–0.5 s [VERIFY]. A realism verdict is step-specific: a step change re-runs P0 on fresh seeds (ARCH t2_realism_protocol.md:175-199) |
| `--time-to-teleport` | 300 s (default, set explicitly); never raised | raising it only hides artefacts (ARCH round2_protocol.md:129) |
| `--collision.action` | `warn` | the default `teleport` turns every collision into a teleport (toy c_collide.py), which would merge V6's two counts; `none` does not count it |
| `--collision.check-junctions` | `true` | F3Z has merges and a zipper; with `false` a merge collision is detected only later, downstream (toy c_junction.py) |
| `--collision.mingap-factor` | `0` | a "collision" means physical overlap whatever the car-following model (toy c_mingap2.py: the default registers Krauss at a 2.4 m gap) |
| `--xml-validation`, `--xml-validation.routes` | `always` | a misspelt vType attribute is otherwise silently ignored (toy b_mixed.py: same hash as the defaults) |
| `--seed` | the run seed, from the seed guard | the SUMO default (23423) is never used |
| `--max-depart-delay` | not set | no vehicle is ever discarded; insertion queues count in door-to-door time |
| outputs | statistic-output, tripinfo-output (departDelay), log with errors captured; per-vehicle per-edge traversal times; power traces (V10) only for the pre-declared subset of §10.4, written from our own per-step read | no fcd or emission files in production runs (toy e_cost.py: 6.3× the step cost, 652 MB per 30 min) |
| lane-change model | LC2013 defaults, written explicitly, enabled for every vehicle (CAVs under command included); **no `lcAssertive`** | lcAssertive moved onsets to the network entry (ARCH STATUS.md:74) |
| insertion | chosen in calibration (C3) from this fixed order: (`departLane="random"`, `departSpeed="avg"`), (random, desired), (free, avg), (free, desired) on the mainline; ramps lane 0, `"avg"` | `"best"` moved the bottleneck to the insertion point (toy b_mixed.py: departDelay 201 s vs 0.03 s); `"max"` caused insertion failures (ARCH STATUS #9). Checked by P0-G2(d) |
| emergency-braking warning threshold | default | diagnostic only; braking is measured from trace accelerations (toy: 101 warnings vs 216 episodes of a < −4.5 m/s²) |
| collision count | statistic-output `safety/collisions` (pairs), cross-checked against distinct (collider, victim) pairs from `getCollisions()` | never the per-step sum of `getCollisions()` (toy: 2,137 entries for 2 collisions) |
| ground-truth read | one plain-getter read per vehicle and step (position, lane, speed, acceleration, fuel, electricity), shared by every consumer | no subscriptions (toy e_cost.py: slower overall) |
| process | `unset SUMO_HOME; OMP_NUM_THREADS=1`; one simulation per process; file names include every varying parameter and the PID | CLAUDE.md toolchain |

### 2.3 Fleet (V40–V43, V35, V38, V46)

| Group | Share | Model |
|---|---|---|
| Heavy vehicles | 7.5 % of all vehicles (V40) | 40 t articulated; EIDM truck parameters (archive `_IDM_TRK` with the H5 EIDM layer); vType maxSpeed 25 m/s (90 km/h); length 16.5 m [VERIFY] ([AUTHOR A13], V65); energy by road-load + Willans (V34); never CAVs |
| Cars | 92.5 % of all vehicles | sales mix renormalised over the five V42 classes (my arithmetic, [AUTHOR A13]): petrol 25.52 %, diesel 17.37 %, HEV 22.85 %, PHEV 15.06 %, BEV 19.20 % |
| CAVs | 50 % of electrified + hybrid cars = **28.55 % of cars, 26.41 % of all vehicles** | SUMO ACC, candidate chosen in calibration (C4, [AUTHOR A11]); `speedDev=0`; desired speed 100 km/h, speed factor 1.0 [AUTHOR A13 (iii)]: the 44.7 % of CAVs whose B0 speed factor exceeds 1.0 therefore drive slower in B1 and in every commanding arm than in B0, a built-in delay increase and energy saving vs B0 that P0-R2 measures and every band table shows (B1 − B0); powertrains BEV 33.6 %, PHEV pair 66.4 % |
| HDV cars (B1 and commanding arms) | 71.45 % of cars | EIDM, archive driver H5 (every EIDM-specific parameter, error terms included, at the SUMO default; ARCH t2_realism_protocol.md H4 collapse); petrol 35.7 %, diesel 24.3 %, PHEV pair 26.5 %, BEV 13.4 % |
| PHEV pair (HEV + PHEV) | — | `HBEFA4/PC_PHEV_petrol_Euro-6d_(P)` or `_(El)`, one mode per trip, 50 % electric (V46) |
| ICE and BEV classes | — | `HBEFA4/PC_petrol_Euro-6d`, `HBEFA4/PC_diesel_Euro-6d`, `HBEFA4/PC_BEV` (all load in 1.27.1; toy f_emission.py) |

- **HDV car desired speeds** (V43, labelled assumptions): speed factor 1.0 (55 %), uniform in (1.0, 1.2] (44.7 %), uniform in (1.2, 1.5] (0.3 %) on the 100 km/h network. "Uniform within each range" is an ASSUMPTION (V43 gives only the ranges). `speedDev=0` in the HDV vTypes, because the factor is drawn per vehicle. Note: in the toy, EIDM HDVs with sigma = 0 still exceeded the lane maximum by up to 2.1 km/h, probably through EIDM's own error processes [VERIFY]; P0-G2(e) measures compliance.
- **B0** drives every car, CAV-flagged or not, as an EIDM HDV with its manifest speed factor. **B1** and every commanding arm drive the CAV-flagged cars with the chosen ACC.
- **Attribute manifest (common random numbers).** Route, desired departure, category, powertrain, emission class, PHEV mode, speed factor and CAV flag are drawn once per seed, before any arm is known, from NumPy generators keyed by (seed, stream): one stream per route for arrivals and one per attribute, so that changing one route's rate no longer shifts every later route's arrivals (port_map plant trap 3). They are written per vehicle in the route file. vTypes are assigned per vehicle by id; `vTypeDistribution` is not used, because SUMO would draw types from its own RNG (port_map mrg3 trap (b)). CAVs are tracked by id, never by type id (ARCH STATUS #5, `av@<id>` rename). The per-vehicle speed factor read back from SUMO must equal the manifest (P0-B7) [VERIFY the per-vehicle attribute in 1.27.1; fallback: generated vTypes, because SUMO 1.27 rejects distribution strings for accel, ARCH STATUS.md:89].
- **Disclosed limit of common random numbers.** Inflow and attributes are identical across arms (T3b). SUMO's own random draws (EIDM driver noise, lane-change randomness, and the lane picked at insertion under `departLane="random"`) are not in the manifest; they diverge as soon as arms behave differently. This is unavoidable here and is why sample sizes rest on paired variances (§8.7).
- **Every vType attribute is set explicitly** (toy b_params.py: the ACC defaults read back include `speedDev` 0.1 and `HBEFA4/PC_petrol_Euro-4`; libsumo cannot read model gains back), including mass (the HBEFA4 fuel cut-off depends on it, literature_v0.md, and the P0-G4 acceleration floor uses it). The full vType XML and its hash go into each run record.

### 2.4 Inflow family and episode ([AUTHOR A12]; proposal with labelled assumptions)
- **Episode (V49).** Warm-up [0, 900) s at the base level q₀; scored window [900, 9,900) s; **inflow stops at 9,900 s** (the reading of V49 and `interfaces.md` §4/§5.1: the drain adds no new arrivals); drain until every cohort vehicle has arrived or t = 11,700 s (58,500 steps of 0.2 s). Cohort = vehicles whose desired departure lies in [900, 9,900) s. Control stays active in warm-up, window and drain (V8; `interfaces.md` §5.1). Edge effect, identical across arms: the last cohort vehicles drive on an emptying road.
- **Shape, per stream** (a triangle approximation of the fitted US-169 SB S460 morning peak, B12): q₀ = 0.5·q̂ during warm-up and at window start; linear rise to q̂ at **t_pk = 5,160 s** from episode start (71 min into the window); linear fall to **q₁ = 0.7·q̂** at 9,900 s. Anchors (port_map m_day verifier, upheld): within 06:00–10:00 the fitted curve starts at 0.47 of its AM peak, peaks at 07:54, and is still at 0.70 at 10:00. Mapping 06:00–10:00 linearly onto the 2.5-h window puts the peak 114/240 × 9,000 s ≈ 4,275 s into the window, rounded to 4,260 s (my arithmetic). Rise 71 min, fall 79 min ("rise faster than fall", `interfaces.md` §4). The fitted curve is not a triangle (its plateau term holds about 0.65 all day): the triangle is a labelled simplification. Mapping the 4-h morning onto the 2.5-h window makes the rise and the fall 1.6 times faster than on the real road (240 / 150 min; my arithmetic), which changes queue sizes at a given λ; disclosed in [AUTHOR A12].
- **Level.** q̂ = λ × (4,000; 1,200; 1,000) veh/h for (mainline; OR1; OR2) (B13 draft input).
- **Per-episode noise: off in P0–P2** (Poisson arrivals only). The archive magnitudes are invented (port_map trap 9; m_day trap 1), and noise on the peak level would blur what "level λ" means for the band and inflate the paired variance. Noise enters later as a pre-registered robustness row (§12).
- **Arrivals.** Non-homogeneous Poisson per route; explicit vehicles snapped to the 0.2-s grid; exact due(t) counting with depart < t; no per-second or per-route cap. v5 capped every route at 3,600 veh/h and B0 never broke down (ARCH notes_networks.md V1); a SUMO flow probability is capped at one vehicle per second per flow (toy b_mixed.py).
- **Expected size at λ = 1.0** (my arithmetic): about 13,200 vehicles per episode, 12,440 of them in the cohort.
- **Plateau probe (P0-G1 and calibration only).** Warm-up 900 s at 0.5·q̂_a; rise over 900 s to q̂_a; plateau [1,800, 5,400) s; fall over 900 s to 0.5·q̂_a; inflow stops at 6,300 s; drain ≤ 1,800 s (end ≤ 8,100 s). Same fleet and ramp ratios (OR1 = 0.30, OR2 = 0.25 of the mainline). It exists because a triangle confounds any within-run pre/post drop estimate by construction (ARCH t2_realism_protocol.md Addendum A; STATUS #13: every smoke breakdown began when the peak arrived, and the ratios came out at 1.2–1.5).

### 2.5 Execution layer as tested (V26, V36, V47; `interfaces.md` §3 except the hold and the entry ramp, §1.1 item 1)
- **Zone entry:** at the first 2-s boundary after a CAV's front enters a zone, target = its current speed rounded to the nearest 5 km/h, clipped to [50, 100] km/h. The target is always reached with `slowDown(id, target, 2.0)` from the current speed, never with a `setSpeed` step (a `setSpeed` from 97.4 to 95 km/h brakes at −3.333 m/s² for one 0.2-s step, a V36 hard brake manufactured by `exec`; scratchpad review_phys/hold_recover.py). If the arm also commands u = ±1 at that boundary, the same single call ramps from the current speed to the rounded target ± 5 km/h: at most 7.5 km/h over 2 s, i.e. ≤ **1.04 m/s²** (my arithmetic; the only ramp allowed to exceed 0.694 m/s², T0a).
- **At each later 2-s boundary**, u ∈ {−1, 0, +1}: target ← clip(target + 5u, 50, 100). If the target changed: `slowDown(id, target, 2.0)`. If it is unchanged and the previous ramp has ended: `setSpeed(id, target)` (hold, V36). Exactly one call per CAV per boundary, and only from `exec` (toy A2b: re-issuing `slowDown` every step never reaches the target).
- **Zone exit:** release per [AUTHOR A10]. Recommended and as decided (a): `setSpeed(id, −1)` at the first boundary after exit (V36, `interfaces.md` §3, §9); the ACC then accelerates at its own 2.6 m/s² towards its desired speed (toy A3, A6), which is the ACC's own behaviour, not a command. Option (b), a ramp of +5 km/h per 2 s with `slowDown` before `setSpeed(−1)`, would amend V36 and `interfaces.md` §1/§3/§9 (it commands outside zones); if chosen, zone entry cancels an active release ramp and sets target = current speed rounded (precedence rule), and release-ramp calls are logged as their own command type.
- **Lane changes** stay enabled under every command (LC2013, §2.2); a CAV changing lanes during a ramp or a hold keeps its target (T0a tests it).
- **Speed mode 31** (default): car-following safety overrides every target (toy L1/L2: a CAV commanded to 90 km/h follows a 60 km/h leader with a 21.5 m minimum gap, no collision).
- **Commanded stops are impossible** by construction (v_min = 50 km/h), so a hold cannot manufacture a standstill longer than the 300-s teleport time (ARCH STATUS #18: 360-s blockages teleported in 209 of 220 runs).
- **No large target jumps** come from `exec`; T0a gates on 0 exec-induced steps below −3 m/s².

### 2.6 Calibration on the throw-away seeds 7,400,000–009 (disclosed)
Calibration fixes only the design quantities below, by rules written now (principle 10). **Nothing is calibrated on 7,400,010 or later.** A calibration report (§4.3) is committed before seed 7,400,010 is used.

| Id | Seeds | What is set | Rule (fixed now) |
|---|---|---|---|
| C0 smoke (P0-S) | 000–001 | nothing; golden B0 trace hash (seed 000, triangle λ = 1.0); CPU time | §4.2 |
| C1 triangle ladder | 002–009 | λ_c, λ_sub | B0 triangle at λ ∈ {0.6, 0.7, …, 1.2} × 8 seeds. **λ_c** = the level at which the share of runs with an active sustained onset at any bottleneck (§3.2) reaches 0.5, linearly interpolated between ladder points, rounded to 0.01. **Downward extension, once:** if the share at 0.6 is already ≥ 0.5, B0 is also run at {0.4, 0.5} on the same seeds. If the share is still ≥ 0.5 at 0.4, λ_c is undefined: futility stop **F5**. **λ_sub** = the highest ladder level with no sustained onset in any of its 8 runs; if none qualifies, λ_c − 0.2 |
| C2 plateau ladder | 002–009 | BN*, λ_a | B0 plateau probe at λ ∈ {0.60, 0.65, …, 0.95} × 8 seeds. **BN*** = the bottleneck with the most active sustained onsets pooled over the ladder. **λ_a** = among levels with 0 teleports and 0 health FAIL, the level whose BN* onset share is closest to 0.5; ties go to the lower level (archive cell rule, ARCH t2_realism_protocol.md:42-48). Extensions, at most one: if the maximum share is < 0.2, extend to {1.00, 1.10, 1.20}; if the share at 0.60 is > 0.8, extend to {0.50, 0.55} |
| C3 insertion | C1/C2 runs | `departLane` / `departSpeed` | the first configuration of the §2.2 order that meets P0-G2(d) on the calibration runs |
| C4 ACC ladder | non-project seed 1, then 002–009 | ACC candidate ([AUTHOR A11]) | **Pre-screen (deterministic, non-project seed 1, before any calibration seed is spent on the ladder):** (i) the platoon test (one lane, 10 followers, leader 100 → 60 km/h at −3 m/s²: peak deceleration of follower 10 ≤ the leader's; toy b_string.py: the defaults attenuate, 2.90 → 1.19 m/s²); (ii) the **approach test**: a lone CAV at 100 km/h approaching, from 300 m, a leader at 60 km/h and a stopped leader: peak deceleration ≤ 4.5 m/s² and 0 steps beyond the vType decel + 0.01 m/s² (ASSUMPTION; the EIDM HDV's peak in the same scenario is reported). A candidate failing the pre-screen is dropped (logged). **Calibration:** B1 for each surviving candidate in order, paired with B0, at **λ_c and λ_c + 0.1** (the G3 levels, §4.6; both below the plant-invalid line by construction); B0 at these two levels is run once on 002–009 (16 runs). R is the G3(b) statistic (pooled rate ratio of severe events, definition [AUTHOR A28]), computed only over seeds where B0 is valid with 0 health FAIL. **Selection:** the first candidate with G3(a) met and R ≤ **0.85** at both levels (a margin, ASSUMPTION, so that the fresh-seed check is not a coin flip); if none reaches 0.85, the candidate with the lowest max-over-levels R among those with R ≤ 1.25 at both levels goes to G3, flagged. Candidates in order: **A0** SUMO ACC defaults (explicit); **A1** A0 with tau 1.2 s; **A2** A0 with decel 3.5 m/s²; **A3** an IDM-based ACC without driver noise (Kesting et al. 2008 [VERIFY]; departs from "SUMO ACC" in `system_context.md` §3; allowed by V60). Excluded a priori: SUMO CACC (uncommanded CACC at 25 % made delay +46 to +93 % worse, ARCH round4_th.md); the ACC "original-model" gain set (toy: 4,552 collision log lines at 100 % ACC); tau 1.5 s (toy: 6.03 vs about 1.5 hard brakes per 1,000 vehicle-steps at 100 % ACC) |
| C5 reference times | 002–009 | r(route, cat) | B0 triangle at λ = 0.05 on all 8 calibration seeds; median trip time (insertion to arrival) per route and cat ∈ {car, truck} [AUTHOR A8], over all 8 runs pooled. **Minimum count:** ≥ 20 vehicles per (route, cat) cell (ASSUMPTION). **Fallback** for a sparse cell: the category's median free-flow pace (s/km, pooled over all routes of that category) × the route length; the cells that use it are recorded. **Sanity row:** r vs route length ÷ the category's desired speed (100 or 90 km/h), FLAG outside ±10 % (ASSUMPTION). Stored with the network hash and its own hash (T3c); **identical for every arm**. (Expected sparse cell, my arithmetic: OR1 → X2 trucks ≈ 0.96 per seed at λ = 0.05) |
| C6 travel-time offsets | from C5 | tt_k | reference travel time from the mainline origin to each measurement section (§3.2) |
| C7 T3-early | 3 runs of C1 | — | each re-run in a fresh process; bitwise-identical per-step trace hash, else STOP (protects pairing before any check seed is spent) |
| C8 CPU-time caps | all | per-run CPU-time cap per arm family | median **process CPU time** per episode (SIGSTOP intervals excluded by construction), measured at production concurrency in the C1/C2 batches; cap = 4 × that median at the nearest level, applied from seed 010 on. During P0-S and P0-C a provisional cap of 8 × the P0-S median CPU time applies (ASSUMPTION: generous, because the smoke runs at low concurrency and low levels); a calibration run over it is a collapse for F3. Commanding arms: B1's cap × their CPU overhead ratio over B1, measured in the P1-B (R4) and P2-B (R1–R3) timing tests (§5.0, §6.3). A run over its cap is a **collapse**: killed and counted as a FAIL of its arm on that seed, never excluded (§2.7) |

**Any later change of insertion configuration, step or HDV model re-runs C1–C8 on 002–009 before its fresh-seed re-check** ([AUTHOR A16d]); a new ACC candidate re-runs only C4.

**Calibration futility stops ([AUTHOR A4]; STOP direction only, disclosed).** If any holds, no check seed is spent; F1–F3 lead to the plant FAIL path (§9.2):
- **F1** no sustained onset at any λ ≤ 1.2 in either ladder (no breakdown to measure);
- **F2** in every calibration run with an active onset at BN*, the per-run discharge at BN*'s section (§3.2) is < 90 % of the discharge floor ([AUTHOR A25]; 1,440 veh/h/lane under the recommended floor of 1,600; ASSUMPTION: a margin wide enough that the check seeds could not plausibly reach the floor);
- **F3** a ladder level ≤ λ_c + 0.1 COLLAPSED: in at least half its runs, a run exceeds the CPU-time cap, or B0 is not drained at the cap (archive H4 precedent: discharge 185 veh/h/lane, runs about 12 times longer; ARCH t2_realism_protocol.md:127-135). Non-drain at higher levels is over-saturation, not collapse: it is reported (P0-R6) and never a stop;
- **F4** every ACC candidate failed the pre-screen, or every surviving candidate has calibration R > 1.25 at some G3 level or fails G3(a): P0-G3 is not run on check seeds, and [AUTHOR A11] applies: P0 KILL, or a new CAV base model under a new protocol. The plant-variant ladder (§9.2) does not apply to F4, because it changes the HDV plant, not the CAV model;
- **F5** λ_c undefined (onset share ≥ 0.5 already at λ = 0.4): the plant breaks down far below the nominal inflow; STOP (a re-designed plant or inflow needs a new protocol; [AUTHOR A26] is superseded by V58/V64, which redesigned the road before any data). Not a realism FAIL and not a variant.

### 2.7 Health layer: every known artefact has a detector
Ported from ARCH vsl_lab/sim/runner.py:7-17,179-263, with the gaps between the runner and the roadmap closed (runner H-R2 and H-R5 only WARNed; H-R8 existed only for BN4; no golden hash existed). "FAIL" = the run is invalid for its arm ([AUTHOR A19]); "FLAG" = recorded and used by a named rule; "OPS" = an operations failure, re-run once on the same seed.

| Artefact (archive or toy evidence) | Detector | Action |
|---|---|---|
| Teleport (V6; H-R3) | SUMO teleport count | FAIL |
| Collision (V6; runner trap 5) | statistic-output pairs, cross-checked against distinct pairs; junctions checked; mingap-factor 0 | > 2 in a run: FAIL; every one counted (gates in §4) |
| SUMO error, assert, traceback (H-E4, H-R7; STATUS #11 quiet stderr) | log scan; non-zero exit | FAIL. A crash is re-run once on the same seed; a second crash stays FAIL (`interfaces.md` §9) |
| Loaded ≠ generated (H-S2) | counters vs manifest | FAIL |
| Conservation at the end, per route (H-E2 adapted to censoring) | generated = arrived + running + pending at the end | FAIL |
| Conservation every step (H-R1; STATUS #3 off-by-one) | generated = inserted + pending; inserted = arrived + running (+ teleported) | FAIL; unit-tested in P0-B4 |
| Statistic-output mismatch (H-E3) | SUMO statistics vs own counters | FAIL |
| Insertion backlog on a free entry (H-R2, tightened from WARN) | departDelay of vehicles inserted while the first 500 m of their entry edge has a 1-min speed ≥ 70 km/h | any > 60 s: FAIL; median > 1 s: FLAG (P0-G2(d)) |
| Stranded vehicle at a lane end (H-R5 tightened; STATUS #15) | speed < 0.1 m/s within 50 m of the zipper or an auxiliary-lane end | > 120 s continuously: FAIL; > 60 s: FLAG |
| Severe, at-cap and extreme deceleration (STATUS #4, #14; toy b_mixed.py; review_phys/knife.py) | per-step acceleration from the trace; definitions by [AUTHOR A28] (recommended: **severe** = contiguous stretch with a < −(4.5 + 0.01) m/s², i.e. strictly beyond 4.5 m/s², the decel of the HDV car and of ACC candidates A0 and A1 (A2 uses 3.5; A3's value is stated in its vType), with speed at onset ≥ 10 m/s; **at-cap** = \|a + decel_vType\| ≤ 0.01 m/s²; **extreme** = a ≤ −8.9 m/s² at v ≥ 10 m/s). Every event stores its onset speed and location; events within 150 m upstream of the zipper node or an auxiliary-lane end are attributed "lane end" | counted per km of the relevant vehicles (P0-G3, P0-R7, §6.12). The threshold must differ by ≥ 0.01 m/s² from every decel in the vType manifest (P0-B3). SUMO emergency-braking warnings are a diagnostic only |
| Zipper metronome (ARCH report_S1:57-59) | per-lane 10-s counts at the BN-LD section (6,100 m) during active discharge minutes; CV of lane 0's counts | FLAG if CV < 0.2 (ASSUMPTION; a Poisson stream at 1,600 veh/h has CV ≈ 0.47 over 10 s, my arithmetic) or if lane 0's discharge is below the floor while the section mean is in band (P0-R9) |
| NaN or ±∞ energy | metrics check | FAIL (`interfaces.md` §9) |
| Not drained at the cap (H-E1) | cohort vehicles not arrived at 11,700 s | FLAG; censored count per arm reported and guarded (§6.8(g)) |
| Queue reaching the network entry | 1-min speed < 60 km/h at the 250 m probe; origin-queue vehicle-hours | FLAG; reported and guarded (§6.8(g)) |
| Plant collapse (ARCH t2_realism_protocol.md:127-135) | process CPU time > the C8 cap of its arm family | killed; FAIL for that arm on that seed, never excluded |
| Worker hang (`interfaces.md` §9) | CPU time grows by < 1 s over 10 min of wall time while the guard has not paused the job (the guard logs every SIGSTOP and SIGCONT) | OPS: killed and re-run once on the same seed, logged; a second hang is a FAIL of that arm and reported. A kill that overlaps a guard pause is OPS, never FAIL |
| Unknown or inert vType attribute (STATUS #10) | XML validation `always` + R-0 hash test | build FAIL (P0-B3) |
| Silent code change in the plant | golden B0 trace hash (seed 7,400,000, λ = 1.0) | an unexplained hash change: STOP |

### 2.8 Code needed per stage (from `port_map_v0.md`; every check runs on planned code)

| Stage | Modules | Source | Acceptance tests |
|---|---|---|---|
| Before P0-S | `ops/` (config, CPU guard with pause log, scheduler with shuffled job order, ledger, run dirs); `plant/` (F3Z build, inflow generator, vTypes, runner + health); `metrics/` (headline + realism estimators, truck model, power traces); `exp/` (stats, seed guard) | netgen/corr2.py TRIM; the archive seeded Poisson generator (vsl_lab/sim/, PORT, renamed `inflow`); plants/m_day.py TRIM (reshaped, §2.4); plants/mrg3.py vType layer TRIM; sim/runner.py TRIM with the trap fixes; eval/realism.py REFERENCE; eval/stats.py PORT; guard/scheduler/ledger PORT/TRIM; seed guard new | P0-B |
| After P0 PASS | `exec/`, minimal `v2x/` (zone summaries, V2V lists, radar), `arms/` R4, command log | new (references: cav_staircase.py, mrg3_run.py) | P1-B (§5.0) |
| After P1 PASS | `arms/` R1 (plants/ring.py PI with saturation, REFERENCE), R2 and R3 (new), O lookup, tuning machinery; headroom ceiling (new, report-only) | port_map; literature_v0.md F1, F2, F4 | P2-B (§6.3) |

---

## 3 Metrics used per check

### 3.1 Headline, guards and reported metrics (`interfaces.md` §5)
All are computed in `metrics/` from the per-step ground-truth trace, the inflow manifest and the command log, by one implementation for every arm. Per-vehicle summaries are stored, so a price or weight sensitivity row is a re-scoring without new simulation.

| Symbol | Definition |
|---|---|
| Cohort | vehicles whose desired departure lies in the scored window [900, 9,900) s; all categories |
| τ_v | door-to-door time = arrival − desired departure (insertion queue included, from the manifest); censored at 11,700 s and the run flagged |
| r(route, cat) | median trip time (insertion to arrival) in B0 at λ = 0.05 on seeds 7,400,002–009 (C5, with its minimum count and fallback), cat ∈ {car, truck}; stored with the network hash and its own hash; **identical for every arm** [AUTHOR A8] |
| d_v, Dl | delay d_v = τ_v − r; network delay Dl = Σ d_v (veh·h). R_tot = Σ_v r_v (veh·h), the cohort's total reference time, used by the delay-guard floor (§6.8(e)) |
| D | fixed denominator: Σ over the cohort of the planned route length (km); identical across arms on a seed |
| E_v | energy over the vehicle's whole trip: HBEFA4 fuel (mg/s) or electricity (Wh/s) × 0.2 s for cars; road-load + Willans for trucks; electricity net of regeneration, at the battery (V53). kWh via E10 41.5 MJ/kg, 748 kg/m³ and B7 42.7 MJ/kg, 836 kg/m³ (JEC WTW v5; the Irish blend is [VERIFY]). Vehicles in the origin queue use no energy in SUMO (an imputation row exists, §6.12) |
| € energy | petrol €1.98/L, diesel €2.15/L, electricity €0.4042/kWh (V21; price date in Addendum B) |
| **C** | **[Σ_v VoT_cat · d_v + Σ_v € energy_v] / D**, € per vehicle-km; VoT_car and VoT_truck frozen in Addendum B before seed 7,400,000 (V29, V54) |
| h | CAV hard-brake events (contiguous stretches with a < −3 m/s², V36) per CAV-km, CAV-km = the planned km of cohort CAVs (fixed). Speed condition [AUTHOR A28] (recommended: all speeds as decided in V36; the split at onset speed ≥ 10 m/s reported) |
| h_HDV | the same definition on HDV cars and trucks per HDV-km, and the severe-event rate per HDV-km; report-only [AUTHOR A29] |
| Validity | V6 + §2.7 FAIL rows [AUTHOR A19]; OPS failures are re-run, not scored |
| TTT | ∫ over [900, 11,700) s of the number of vehicles that have reached their desired departure time and not yet arrived, in the network **or in the origin queue** (veh·h); unfinished vehicles counted to the cap (CLAUDE.md; the archive's "TTS gaming via insertion blocking" trap, ARCH docs/lessons_metric_gameability.md §5) |
| Served throughput | cohort vehicles arrived by the cap, and vehicles per hour at the exits over the window; reported with a CI wherever C is |
| Reported | stop-and-go cycles per vehicle-km on the mainline (a speed below 20 km/h, later above 50 km/h, per vehicle; ASSUMPTION, the `interfaces.md` §5.6 proposal, rationale in A24); per-zone travel time; CAV mean speed vs B1 (speed give-up); kWh per vehicle-km per category and powertrain; scenario totals in kWh and € (V24); share of CAV-boundaries with the target at 50 or 100 km/h (V47); origin-queue vehicle-hours per arm; censored count per arm |

### 3.2 Plant diagnostics (P0, P1; never in any arm's observation, V27)
- **Speed probes.** Space-mean speed of the vehicles on the **through lanes** within ±50 m of x (vehicle-weighted: the mean over vehicles, not a mean of lane means), sampled every 10 s, at x = 250·i m (i = 1…36) (the archive probes10 method). The auxiliary lanes of merge1 and merge2 are excluded; their speeds and waiting counts are reported separately. A 1-min speed is the mean of its six 10-s samples; empty samples are excluded, and a minute with no vehicle counts as uncongested.
- **Flow counters (virtual detectors).** Front crossings per lane at every probe and section, in 10-s and 60-s bins. P0-B6 shows they equal SUMO E1 counts (toy e_detect.py: 1,427 = 1,427 = 1,427; at most 1 vehicle apart per interval at bin edges). Timestamps are interval **ends** (ARCH report_S1 onset-label bug). Any E1 read uses `getLast*` (CLAUDE.md).
- **Congested probe-minute:** 1-min speed < **60 km/h**. **Sustained onset** at a probe: ≥ 5 consecutive congested minutes; t_b = its first minute. Source: the TII lane-capacity note (NRA/TII, "A Study of Lane Capacity in the Greater Dublin Area", Feb 2012, §5.4, read in full) finds a speed boundary of about 60 km/h between congested and uncongested conditions on the M50/M1/N11 sites and adopts Lorenz & Elefteriadou's criterion, speeds below 60 km/h for five minutes or more (original [VERIFY]). **Recovery** t_rec: the first of ≥ 5 consecutive minutes ≥ 70 km/h (ASSUMPTION: a 10-km/h hysteresis, the archive realism.py pair 60/70).
- **Measurement sections** (per lane, just downstream of each bottleneck, so that a lane-local drop is not diluted; ARCH notes_networks.md L9): BN-M1 at 3,400 m (3 lanes, m3); BN-M2 at 4,900 m (3 lanes, m4); BN-LD at 6,100 m (2 lanes, m6) (V64 layout; v0 had BN-LD at 4,600 m and BN-M2 at 6,100 m); positions taken from the built net. At BN-LD, lane 0 (the zipper output) is also reported on its own, with the metronome FLAG (§2.7).
- **Active bottleneck.** A discharge minute at section k counts only if the 1-min speed at the probe 200 m further downstream is ≥ 70 km/h, so that the bottleneck is discharging freely and not inside a queue spilled back from downstream (the usual meaning of an active bottleneck; the 200 m and 70 km/h implementation is an ASSUMPTION). An onset is **at bottleneck k** (an active onset) if it is a sustained onset at k's head probe (the probe nearest x_k − 250 m) while that downstream probe is ≥ 70 km/h at t_b. **Upstream bottlenecks** of k: BN-M1 and BN-M2 for BN-LD; BN-M1 for BN-M2; none for BN-M1 (an entry-group onset counts as upstream of every bottleneck). An upstream bottleneck j is **active** from its active onset t_b,j until its recovery t_rec,j.
- **Between-run drop estimator** (ARCH t2_realism_protocol.md:139-152, Addendum A), on plateau runs at λ_a:
  - Q_ff(k) = median, over runs **without** an active onset at k **and without** any upstream bottleneck active during [2,400 + tt_k, 5,400 + tt_k) s, of the mean per-lane flow at section k over that interval, active minutes only;
  - Q_dis(k) = median, over runs **with** an active onset at k, of the per-run mean per-lane flow over [t_b + 300, min(t_b + 1,200, t_rec, 5,400 + tt_k + 600)) s, active minutes only, **excluding minutes in which an upstream bottleneck of k is active** (upstream starvation); a run needs ≥ 5 such minutes, else it is not valid for Q_dis;
  - ρ = Q_dis / Q_ff. The bottleneck carried Q_ff without breaking down, so Q_ff is a lower bound on capacity and ρ **understates** the drop (the archive's argument);
  - the runs and minutes excluded for upstream activity are counted and reported.
- **Triangle discharge** (P0-G2, G5, T1a): per run with an active onset at k, the mean per-lane flow over [t_b + 300, min(t_b + 1,200, t_rec, 9,900 + tt_k)) s, active minutes only, excluding minutes with an upstream bottleneck active, ≥ 5 such minutes.
- **v_cong:** mean 1-min speed of the probes in [x_k − 800, x_k − 300] m over the Q_dis window (Yuan, Knoop & Hoogendoorn 2015 poster: queue discharge rises with the speed in the queue).
- **Origin of congestion:** per run, the probe with the earliest sustained onset (ties → the most downstream; archive realism.py), assigned to a bottleneck group (§2.1), the entry group, or "open road".
- **Wave speed c** (archive estimator, ARCH vsl_lab/eval/realism.py `wave_speed`): 10-s probe speeds; high-pass = series minus its centred 5-min mean; on the longest jointly congested segment (centred 5-min means < 60 km/h) of ≥ 15 min; lag of the cross-correlation peak searched in 10-s steps from 0 to min(600 s, segment − 600 s); valid if the peak correlation is ≥ 0.3 (ASSUMPTION, archive value) and the lag is interior (not at either end); c = −Δx / lag. Here up to four probe pairs 500 m apart, going upstream from the active bottleneck's head probe; the run estimate is the median over valid pairs. Resolution: 10-s lags at 500 m resolve c to about 1.5 km/h near −15 km/h, whereas a 1-min series could give only −15 or −10 km/h at lags of 2 or 3 min.
- **Wave period τ:** first autocorrelation peak of the high-passed 10-s series at the probe 1 km upstream of the active bottleneck, over the congested segment (Treiber & Kesting 2010 method, arXiv 1008.1639, sections read; venue [VERIFY]). Report-only.
- **Free-flow speed:** speed of vehicles on m0–m2 with no leader within 150 m.
- **Pre-breakdown flow** (report-only): the highest 1-min per-lane flow at the section in the 5 min before t_b. Within-run and confounded by the inflow ramp; shown only next to the TII 2012 breakdown flows for context.

### 3.3 Which metrics each check uses

| Check | Metrics |
|---|---|
| P0-G1 | Q_ff, Q_dis, ρ, v_cong, onset counts and valid Q_dis runs at BN*; upstream exclusions; per-lane discharge at BN-LD; health |
| P0-G2 | origin, c, τ (report); insertion GEH, departDelay, lane split; health; free-flow speeds; manifest vs SUMO speed factors |
| P0-G3 | CAV severe-event rates (B1 vs the same vehicles in B0, definition per A28) with the cut-in, location and speed splits; the −3 m/s² ratio; CAV collisions; CAV free-flow speed; Dl, C, energy (flag) |
| P0-G4 | single-vehicle energy per km per class at 0–120 km/h; idle; acceleration and braking cycle; truck model and its sensitivity models; regeneration sign and bound |
| P0-G5 | per-run mean door-to-door time; triangle discharge (paired by seed); onset and origin shares, censored share (report) |
| T0a | per-step speed and acceleration; the `exec` call log |
| T0b, T0c | zone space-mean speed, zone density, section throughput, Dl |
| T0d | zone summaries, V2V lists, radar gap vs trace; command log |
| T1a | onsets, triangle discharge, ρ_T1, health |
| T1b, T1c | C, Dl, h, energy, TTT, throughput, validity |
| T3 | per-step trace hash, manifest hashes, record fields |
| P2 | C, Dl, h, h_HDV, validity, censored count, origin-queue time, served throughput, all §3.1 reported metrics |

### 3.4 Gameability guards (ARCH docs/lessons_metric_gameability.md §4–§5)

| Route to game the headline | Guard |
|---|---|
| Serve fewer km to improve a per-km ratio | fixed denominator D (planned km), the same for every arm |
| Push delay into the origin queue | τ and TTT from the desired departure (manifest); origin-queue vehicle-hours reported per arm |
| Vehicles waiting off-network use no energy in SUMO | band guard (g2) on pooled origin-queue vehicle-hours with a sign count (§6.8); an idle-energy imputation row (§6.12) [AUTHOR A23] |
| Push vehicles past the cap (censoring) | band guard (g1) on pooled censored counts with a sign count (§6.8); a row with censored trips completed by imputation (§6.12) |
| Slow CAVs to save energy ("crawl") | delay guard V37 in the band rule; CAV speed give-up reported; R4 includes the 50 km/h floor, so the constant-policy and extreme tests are in the data |
| Move harm onto HDVs | C counts the **delay and energy** of all vehicles, not their braking. HDV hard-brake and severe rates per HDV-km are reported for every arm and level, with a FLAG when A/B1 > 1 + y [AUTHOR A29]; per-category C reported |
| Avoid CAV braking by opening huge gaps | hard braking is a constraint vs B1, not a price (V25) |
| Credit automation as control | B1 row everywhere; the band requires A to be at least 5 % cheaper than B1 (d; V61), which **narrows but does not close** this route: when B1 is already much cheaper than B0, most of a level's gain can still come from automation. The decomposition (C_B0 − C_B1) and (C_B1 − C_A) with CIs is printed at every level, and "≥ 10 % vs no control" is never written without the B1 share next to it [AUTHOR A7] (V61). If uncommanded ACC inflates B1's hard braking, (f′) adds a braking guard vs B0 (§6.8, [AUTHOR A14]) |
| Structural zeros (a model that cannot crash) | P0 reports whether any collision or extreme deceleration occurs at all; a metric that is always 0 is declared uninformative |
| Raw counts grow with time in the network | every rate per vehicle-km or CAV-km of the fixed denominator |

---

## 4 P0 checks (plant realism)

### 4.0 Order of execution
S0 ([AUTHOR] answers, Addendum B) → P0-B (with the ACC pre-screen and P0-G4, which need no project seed) → P0-S → Addendum A → P0-C (calibration report, futility stops) → Addendum D → **P0-G1 alone** → P0-G2, G3, G5 (one batch on 040–059, job order shuffled across arms) → verdict. G1 and G2 need only the plant and the metrics; G3 and G5 need the CAV vType, which is part of the plant, but no `exec`. The execution layer, V2X and the arms are built only after P0 PASS. Every run passes the health layer (§2.7); FAIL runs are counted, never dropped.

### 4.1 P0-B: build and code acceptance (no project seeds; all must pass before seed 7,400,000 is used)
Each item is a unit or micro-scenario test in the repo, run on non-project seeds 1–999 [AUTHOR A16a], observing no F3Z plant outcome. Each test includes a **negative control** that shows the code can produce the FAIL it is meant to catch. PASS = 100 % of tests pass. FAIL = fix the code; no seed is consumed and no deviation note is needed (logged in the commit).

| Id | Test |
|---|---|
| B1 | Built net: every edge length within ±0.5 m of the spec; lane counts; zipper connections 0, 1 → 0 and 2 → 1; auxiliary lanes continue to X1/X2; zones and bottleneck groups map to x ranges; probe and section positions read from the built net; through lanes and auxiliary lanes labelled per probe; spec hash recorded and mandatory |
| B2 | Config table §2.2 applied; a run with a misspelt vType attribute stops with an XML error (negative control) |
| B3 | R-0 inertness: in a 20-vehicle single-lane micro-scenario, perturbing each non-default attribute of every vType (HDV car, truck, each ACC candidate) by ±20 % changes the per-step trace hash; 0 inert attributes (ARCH STATUS #10). Every vType states its mass, and the severe-event threshold of [AUTHOR A28] differs by ≥ 0.01 m/s² from every decel in the manifest |
| B4 | Conservation identities exact on synthetic manifests, including departures exactly on a step boundary (STATUS #3); each FAIL code of §2.7 fires on an injected fault (unbounded backlog at constant sub-capacity inflow, a stopped vehicle at a lane end, an injected collision, a SUMO error) |
| B5 | The collision counter counts pairs, not vehicle-steps; a merge collision is detected on the junction lane (toy c_collide.py, c_junction.py) |
| B6 | Virtual detectors = E1 counts per interval (±1 at bin edges), totals equal; timestamps are interval ends; reads use `getLast*` (toy e_detect.py: `getInterval*` returns the new interval) |
| B7 | Generator on seeds 1–999: per route and 15-min bin, the exact two-sided Poisson test of the realised count against the nominal integral rejects at α = 0.01 in 0.5–1.5 % of bins; mean count within ±0.5 % of nominal; a 5,000 veh/h route is not capped; changing one route's rate leaves the other routes' arrival times identical; attribute shares within ±0.5 percentage points of §2.3; the per-vehicle speed factor read back from SUMO equals the manifest for 100 % of vehicles |
| B8 | `stats`: paired median and percentile bootstrap (numerator and denominator resampled) reproduce a hand-computed case; the invalid-run encodings of §8.4 (effect and guard forms); the continuity-corrected rate ratio of §8.5; the empirical KILL-1 calibration of §6.5; bad input raises, never `assert` (port_map stats trap 1) |
| B9 | Seed guard: refuses any seed outside the role declared for the job (negative control) and appends to a burned-seed ledger |
| B10 | Metrics identities on synthetic traces with hand-computed values: cohort, τ, censoring, fixed D identical across arms, delay, R_tot, kWh conversion, € cost, C, hard-brake events (CAV and HDV), stop-and-go, TTT from the desired departure (origin queue included), served throughput, exact to 10⁻⁹ relative; no negative censored times (runner trap 6); arrivals after the cap are censored; the power-trace writer fires only for the pre-declared subset (§10.4) |
| B11 | Realism estimators on synthetic speed and flow series with a known onset, recovery, drop, active/inactive minutes and wave: t_b, t_rec, origin, ρ, c and τ recovered within one aggregation interval or 1 %. Added cases: (i) an upstream breakdown that starves bottleneck k: those runs and minutes are excluded from Q_ff(k) and Q_dis(k); (ii) one stopped auxiliary-lane vehicle with free through lanes: no onset; (iii) acceleration values at exactly −4.5 m/s² and at −4.5 ± 10⁻⁹ m/s²: the event counts follow the [AUTHOR A28] definition and do not depend on floating-point rounding; (iv) a metronome series (fixed headways) raises the zipper FLAG |
| B12 | `ops`: the CPU-guard tests pass (launch only below 90 % utilisation; SIGSTOP to the process group; resume one per 30 s; every pause logged); the CPU-time cap: a job SIGSTOPped for longer than the cap in wall time is **not** killed or marked invalid (negative control), a CPU-bound runaway job is killed as a collapse, a job with no CPU progress while not paused is an OPS hang and re-run once; job order is shuffled across arms within each batch by a seeded permutation; a ledger row for every job, failed ones included; health columns filled by code from run summaries (ARCH ledger: 89 of 221 run rows had 0/0/0 health counts); a resume after a kill skips finished (arm, config, level, seed) tuples without duplicate rows |
| B13 | Determinism-lite: a 600-s B0 run on non-project seed 1 at low inflow, run twice in fresh processes, gives an identical per-step trace hash (no metric is read) |

### 4.2 P0-S: smoke (seeds 7,400,000–001; throw-away)
- **Runs:** B0 and B1 on the triangle at λ ∈ {0.7, 1.0} and on the plateau probe at λ = 0.8, both seeds: 12 episodes. The B0 triangle run at λ = 1.0 on seed 7,400,000 records the **golden B0 trace hash**.
- **Purpose:** the pipeline runs end to end; every §3 estimator returns a number; CPU time, wall time, memory and trace volume are measured. **No criterion is evaluated on smoke data**, and no smoke value is tabulated except costs and pipeline errors. Addendum B (VoT, prices, metric constants) is already committed (§9.4).
- **On a defect:** an estimator or implementation fix goes into a dated **Addendum A** before any calibration run (ARCH t2_realism_protocol.md:119-166: the smoke test found the estimator defect and the H4 collapse). Addendum A may not change any bound.

### 4.3 P0-C: calibration (seeds 7,400,002–009) and Addendum D
Calibration follows §2.6 exactly, including the ACC pre-screen and the futility stops F1–F5. The **calibration report** shows only what C1–C8 need: λ_c, λ_sub, BN*, λ_a, the insertion configuration, the ACC pre-screen outcomes and the chosen candidate with the margin case it fell into (R ≤ 0.85, or the flagged 0.85–1.25 case), r with its fallback cells and sanity FLAGs, the T3-early result, the CPU-time caps, and which futility stops fired. ρ, Q_dis, discharge values, C, delay, energy and the per-candidate R values are stored in the ledger but are not tabulated or read until the P0 report. **Addendum D** (informational) re-issues the CPU plan from C8 if the measured cost differs from §10 by more than 25 %.

### 4.4 P0-G1 Capacity drop and discharge at the primary bottleneck (the first gate)

| Field | Content |
|---|---|
| Question | Does B0 break down at BN* with a realistic drop and a plausible per-lane discharge, without artefacts? |
| Measurement | B0, plateau probe at λ_a. Between-run estimator at BN*'s section (§3.2), with the upstream-starvation exclusions; Q_dis also at every other bottleneck with ≥ 5 valid Q_dis runs |
| Statistic | medians over runs; 95 % percentile bootstrap CI of ρ (runs resampled within the two groups, 20,000 resamples), reported, not gated |
| PASS (all) | (a) ≥ 5 runs **with** and ≥ 5 runs **without** an active onset at BN* (the latter also free of upstream activity, §3.2), **and ≥ 5 runs valid for Q_dis at BN*** (fewer: not computable → FAIL, principle 7); (b) **ρ ∈ [0.82, 0.97]** (a 3–18 % drop); (c) **Q_dis(BN*) ∈ [floor, 2,300] veh/h/lane**, floor per [AUTHOR A25] (recommended 1,600), and every other bottleneck with ≥ 5 valid Q_dis runs also in that band; (d) **over the original 30 runs (010–039)**: 0 teleports, 0 invalid runs, 0 health FAIL, and ≤ 2 collisions in total. Artefacts in extension runs are reported prominently, and such runs are invalid for the estimator, but they cannot turn (d) into a FAIL |
| Sources | (b) Yuan, Knoop & Hoogendoorn 2017, *Transportation Science* 51(3):852-862 (accepted manuscript read in full) review reported drops of 3–18 %; the originals they cite [VERIFY each]. About 10 %: Cassidy & Bertini 1999 [VERIFY, abstract only]. About 15–16.5 % at the US-169 NB Plymouth Ave merge: Geroliminis, Srivastava & Michalopoulos 2011, UMN CTS 11-05 (read in full). HCM default 7 % [VERIFY, via the McTrans page]. Band choice: [AUTHOR A2]. (c) ASSUMPTION built from sources, not a published band: Dutch 3-lane A4/A12 queue discharge observed at 5,220–6,840 veh/h, i.e. 1,740–2,280 veh/h/lane, over v_cong 6–60 km/h (Yuan et al. 2015, TRB poster 15-4064, read; their fit Q = 29·v + 5,000 veh/h for 3 lanes gives 1,725–2,247 veh/h/lane over that range, my arithmetic); 1,866–2,031 at a 100 km/h 4-lane site (Han et al., arXiv 2602.22019, read); M50 lane means 1,580–1,960 veh/h (TII 2012, read; pre-breakdown flows, not discharge); HCM-based ≈ 1,990–2,030 (my arithmetic, with an assumed truck PCE of 2.0 [VERIFY HCM]). The archive band [1,600, 2,400] had no source (ARCH t2_realism_protocol.md:88). Upper bound: [AUTHOR A3]; floor: [AUTHOR A25]. Neither is changed after data (archive ZM3 at 1,528 stayed FAIL) |
| Computability | With n = 30, P(the onset split of (a) fails) = 0.03 at a true onset share of 0.3 or 0.7, 0.10 at 0.25 or 0.75, 0.26 at 0.2 or 0.8 (binomial; my arithmetic). These figures bound only the onset split, **not** Q_dis validity: short breakdowns (the archive's EIDM failure mode: "EIDM's breakdowns at the 50 %-share cell are too short to measure a drop", ARCH STATUS.md:73; H5 Q_dis not computable at n = 1+15, ARCH t2_realism_step0.2.md:9) can make (a) fail with many onsets. **Pre-registered extension, once:** if (a) fails only by group size or by valid Q_dis runs, B0 is run at λ_a on seeds 090–099 and pooled (n = 40: 0.016 at 0.25/0.75, 0.076 at 0.2/0.8). Bounds unchanged; (d) stays on the original 30. The archive's onset-share gate (≥ 0.3) is not used: the share is a property of the cell choice, not of realism, and its drift between calibration and check seeds made R-a "not computable" in 9 of 15 archive gate runs (ARCH notes_networks.md L5). The share is reported |
| Known risks | **The most likely P0 FAIL** (§0.4). Also: a plant with a high queue speed v_cong can show ρ ≈ 1 and FAIL (b)'s 0.97 bound for a realistic reason: Yuan et al. 2015 observed discharge above the 6,300 veh/h three-lane pre-queue capacity when the speed in congestion was high. And BN* is expected to be BN-LD, a zipper node (V64, §2.1), the bottleneck type whose archive analogues discharged as a metronome below the floor; the metronome FLAG (§2.7) and P0-R9 watch it |
| Reported | v_cong next to ρ (Yuan et al. 2015 relation, my arithmetic: against their pre-queue capacity of 6,300 veh/h, 0 % drop at v_cong ≥ 44.8 km/h, 17.9 % at 6 km/h, ρ = 0.79 at v = 0; against their maximum observed discharge of 6,840 veh/h: 63.4 km/h, 24.4 %, 0.73); ρ and Q_dis at the other bottlenecks; the onset share; runs and minutes excluded for upstream activity; per-lane discharge at BN-LD with the metronome FLAG (P0-R9); the within-run "pre-breakdown flow" ratio (confounded; values only); 5-min discharge CV (Cassidy & Bertini 1999 report near-stationary discharge [VERIFY]); pre-breakdown flows vs TII 2012 (P0-R5); lane flow shares at breakdown |
| Seeds, n | 7,400,010–039, n = 30 (+ 090–099 if extended) |
| On FAIL | **STOP P0** → §9.2. [AUTHOR A2], [AUTHOR A3] and [AUTHOR A25] concern the bounds themselves and are settled before seed 7,400,000 |

### 4.5 P0-G2 Onset location, waves, artefacts, insertion and desired speeds in the experiment scenario

| Field | Content |
|---|---|
| Question | In the triangle scenario, does congestion start at the bottlenecks, do waves travel upstream at a plausible speed, does the plant receive the inflow it is given, are the runs artefact-free, and are desired speeds implemented? |
| Levels | **λ_c**, and a second level **λ_2** = 1.0 if 1.0 ≥ λ_c + 0.05, else λ_c + 0.2 |
| Measurement | B0 triangle at both levels. Origin per run; c per run; insertion (per entry and hour bin: M = vehicles inserted, S = vehicles scheduled; departDelay; lane split at insertion); health; free-flow speeds; manifest vs SUMO speed factors |
| PASS (all) | **(a) Onset location (R-d):** pooled over all B0 runs of G1 and G2 with any sustained onset, ≥ **80 %** have their origin in a bottleneck group and ≤ **5 %** in the entry group; ≥ 20 such runs, else not computable → FAIL. **(b) Wave speed (R-b):** median c over runs with a valid estimate ∈ **[−25, −10] km/h**, with ≥ 5 valid run estimates; fewer → not computable → FAIL. **(c) Artefacts.** *Realism gate* at λ_c, and at λ_2 if λ_2 ≤ λ_c + 0.1: 0 teleports, 0 invalid runs, 0 health FAIL and ≤ 2 collisions in total over the 20 runs. *Admissibility* at λ_2 > λ_c + 0.1: the single admissibility rule of §8.8 (B0 invalid share ≤ 5 %, i.e. ≤ 1 of 20); artefact counts reported. **(d) Insertion fidelity**, on uncongested entry intervals (the first 500 m of the entry edge at a 1-min speed ≥ 70 km/h on the mainline, ≥ 0.7 × the ramp limit on ramps), at both levels: GEH = √(2(M − S)² / (M + S)) **< 5 in 100 %** of uncongested entry-hours; median departDelay ≤ 1 s, 99th percentile ≤ 10 s, maximum ≤ 60 s; each mainline lane receives ≥ 20 % of mainline insertions; 0 vehicles discarded. **(e) Desired speeds:** the manifest speed factor equals SUMO's per-vehicle value for 100 % of vehicles; median free-flow speed of the 100 km/h class ∈ [97, 103] km/h, of the (100, 120] class ∈ [107, 113] km/h, of trucks ∈ [87, 92] km/h |
| Sources | (a) 80 %: archive R-d, which discriminated (MRG3 d3 scored 0.15 and 0.00; ARCH t2_realism_d3.md:7-10); about 400 A5 breakdowns, all at bottlenecks (Treiber, Kesting & Helbing 2010, arXiv 1004.5545, §2 read; venue [VERIFY]). 5 %: ASSUMPTION (an entry onset is an insertion or lane-choice artefact). (b) −15 ± 5 km/h (Schönhof & Helbing 2007, *Transportation Science* 41(2):135-166, relevant sections read; their cited originals [VERIFY]); −20 to −15 km/h (Treiber, Kesting & Helbing 2010); UK M4 about −14 and US 19–20 km/h upstream (Zielke, Bertini & Treiber 2008 [VERIFY, abstract level]); 22–24 km/h (Mauch & Cassidy 2002 [VERIFY]). The band keeps the archive's [−25, −10]. Not computable = FAIL: stop-and-go oscillation inside congestion is a stylised fact (Treiber et al. 2010), and wave-damping comparators have nothing to act on without it. (d) GEH form and the < 5 criterion: TII PAG Unit 5.1 (PE-PAG-02015, Dec 2023, §3.2, Table 5.1.2, read; > 85 % of cases there), tightened to 100 % because a synthetic plant has no counting error, so any miss is an insertion artefact. 1 s, 10 s, 60 s and 20 %: ASSUMPTION (toy: random lanes gave 0.03 s mean departDelay and 32–35 % per lane; `"best"` gave 201 s and 0 % on one lane). (e) ASSUMPTION tolerances (toy: EIDM exceeded the lane maximum by up to 2.1 km/h with sigma = 0) |
| Caveat | R-b did not discriminate in the archive (IDM, EIDM and W99 all gave waves of −14 to −19 km/h; ARCH STATUS.md:69). It is necessary, never presented as evidence of realism |
| Reported | wave period τ (4–20 min for wide jams, Schönhof & Helbing 2007 [VERIFY]; IDM-family periods come out too short, Treiber & Kesting 2010); stop-and-go cycles per vehicle-km; spillback to the entry (share of runs, origin-queue vehicle-hours); censored share; HDV extreme-deceleration rate per 10⁴ vehicle-km (P0-R7); lane 1 vs outer-lane flows; auxiliary-lane speeds and waiting counts |
| Seeds, n | 7,400,040–059, n = 20 per level |
| On FAIL | (a), (b), or (c) at λ_c: **STOP P0** → §9.2. (c) at λ_2 ≤ λ_c + 0.1: a P0 FAIL. (c) at λ_2 > λ_c + 0.1: λ_2 and every grid level ≥ λ_2 are **plant-invalid** (kept in the operating map with their B0 and B1 rows, never tuned, never in the band; stated prominently when λ_2 = 1.0); P0 does not FAIL on it. (d): the next insertion configuration of the §2.2 order (not a plant-model variant; it counts in k); C1–C8 re-run on 002–009 ([AUTHOR A16d]), then G1 and G2 re-run on fresh seeds, because insertion changes the realised inflow. (e): vType code fix; G2 re-run on fresh seeds |

### 4.6 P0-G3 Uncommanded CAV artefacts (B1 vs the same vehicles in B0)

| Field | Content |
|---|---|
| Question | Do uncommanded CAVs (B1) drive without simulation artefacts, judged against the same vehicles driven by humans in B0? |
| Levels | **λ_c and λ_c + 0.1** (gated; both below the plant-invalid line by construction, and the levels of C4). λ_2 is run and reported: its B1 runs also serve G5 and P0-R2 |
| Measurement | B1 vs B0 on the same seeds and inflow files. For the CAV-flagged vehicles (same ids in both arms): severe-deceleration events, at-cap stretches and extreme events (definitions [AUTHOR A28], §2.7), and hard-brake events at −3 m/s² (V36), each per 1,000 km of those vehicles (planned km), with onset speed and location; teleports; collisions involving a CAV; CAV free-flow speed |
| Statistic | pooled rate ratio R = (Σ events in B1 / Σ km) / (Σ events of the same vehicles in B0 / Σ km), over the seeds of that level **on which the B0 run is valid with 0 health FAIL**, per level; 95 % percentile bootstrap CI over those seeds (§8.5) |
| PASS (all) | (a) on every seed whose B0 run is clean: the B1 run is valid with 0 health FAIL and 0 collisions involving a CAV (a B1 failure on a seed where B0 also failed is a plant artefact: reported, not counted against the CAV model); (b) at both gated levels: **R ≤ 1.0** (point estimate) **and** its 95 % bootstrap upper bound ≤ **1.2** (ASSUMPTION margin; a point rule alone passes a model with true R slightly above 1 on noise, especially after sequential looks); (c) CAV median free-flow speed within ±1 km/h of 100 km/h |
| Rationale | ASSUMPTION: an uncommanded automated vehicle should not brake harder than the human it replaces. Otherwise the V25 constraint (measured vs B1) and the energy result would rest on a model artefact (ARCH STATUS #14; round3_tm21_protocol.md). Production ACC standards bound automatic deceleration (ISO 15622 [VERIFY]; not read, no value cited) |
| Expected | **A0 is expected to FAIL** the pre-screen or (b) (§0.4). The ladder A0–A3 and the ACC futility stop F4 (§2.6) exist for this reason |
| Reported | R₃ = the same ratio for −3 m/s² hard-brake events (the V36 threshold): **if R₃ > 1 + y at either gated level, band criterion (f′) is activated** (§6.8, [AUTHOR A14]); extreme events; at-cap stretches; the lane-end and speed-at-onset splits; share of severe events within 1 s of a leader change (cut-in attribution; toy b_diag.py: 67 %); median CAV time headway in steady following; the platoon and approach tests of the chosen candidate; B1 vs B0 relative ΔDl, ΔC and Δenergy with CIs; the number of ACC candidates screened and checked |
| Flag (not a gate) | \|ΔDl(B1 vs B0)\| > 20 % at either level: shown to the author before P1 (archive: uncommanded CACC at 25 % gave +46 to +93 % delay, ARCH round4_th.md). It can trigger nothing except a dated deviation note with a fresh-seed G3 re-run ([AUTHOR A16c]). Never credited to control (ARCH round3_tm21_protocol.md:59) |
| Seeds, n | 7,400,040–059, n = 20 per level (B0 at λ_c shared with G2; B0 and B1 at λ_c + 0.1 are 40 extra runs) |
| On FAIL | the next surviving ACC candidate of the C4 order (pre-screen passed, calibration R ≤ 1.25 at both levels), on fresh seeds (new range, [AUTHOR A16c]); only G3 and G5 are re-run, because G1 and G2 are B0-only. Each such look counts in k (§9.2). Candidates exhausted → [AUTHOR A11]: P0 KILL, or a new CAV base model under a new protocol (the plant-variant ladder changes the HDV plant, not the CAV model) |

### 4.7 P0-G4 Energy plausibility (deterministic)

| Field | Content |
|---|---|
| Question | Are energy levels, their speed trend, and their idle, acceleration and braking behaviour plausible per powertrain? |
| Measurement | One vehicle per class, alone on a flat 10-km test edge (no inflow; non-project seed 1): (i) cruise at v ∈ {10, 20, …, 120} km/h (trucks 10–90): mean over 120 s after 120 s of settling; (ii) idle at v = 0 for 120 s; (iii) 0 → 100 km/h at +1 m/s² (trucks 0 → 90); (iv) 100 → 0 km/h at −1 m/s², and the 100 → 50 km/h braking test. Tank- or battery-to-wheel kWh (§3.1 conversion). Code checks: Σ getter × 0.2 s equals the tripinfo totals within 0.1 % (toy f_emission.py: equal) |
| PASS (all) | (1) At 80, 90 and 100 km/h: petrol, diesel and PHEV (P) in **[40, 70] kWh/100 km**; BEV and PHEV (El) in **[11, 21] kWh/100 km**. (2) Every car class: energy per km at 100 km/h > at 80 km/h. (3) Idle: a finite rate, ≥ 0, for every class. (4) Cruise at 10–40 km/h: finite and > 0 per km. (5) **Acceleration floor** (non-circular physics, ASSUMPTION road-load values stated in Addendum B): energy over the 0 → 100 km/h ramp ≥ ½·m·v² + the road-load work over the ramp, with m from the vType XML; gated for petrol, diesel, PHEV (P) and trucks; for BEV and PHEV (El) per [AUTHOR A33] (recommended: report-only, because HBEFA4 PC_BEV is known to under-charge acceleration: 184.8 Wh for 0 → 30 m/s against about 225 Wh of kinetic energy for an assumed 1.8 t car, literature_v0.md:336-342). (6) Braking: BEV electricity < 0 while braking (net of regeneration, V53), and the energy recovered over (iv) ≤ the kinetic energy at the start of braking. (7) Truck model: reproduces `truck_energy_check_v0.md` (40 t road-load + Willans: 221 / 238 / 254 g/km at 60 / 80 / 90 km/h) within ±1 % (a code-vs-specification check; its offset was calibrated to one measured point), rises from 60 to 90 km/h, and gives 0 fuel when P < 0 through cycle (iii)–(iv). The truck sensitivity models reproduce their sources within ±1 %: COPERT 215 / 216 / 248* g/km at 60 / 80 / 90 km/h (`truck_energy_check_v0.md`:13; * extrapolated above its 80 km/h validity) and the TII OGV2 fuel function L = a/v + b + c·v + d·v² (TII PAG Unit 6.11, Tables 6.11.13–14, read: a = 5.0715, b = 0.34664, c = −0.0027069, d = 0.000014479; L in litre/km, v in km/h) = 268 / 239 / 231 g/km at 60 / 80 / 90 km/h (my arithmetic, diesel 836 kg/m³; that OGV2 is the class of a 40 t articulated vehicle is [VERIFY]). (8) 0 NaN or ±∞ in any P0 run |
| Sources | ASSUMPTION bands anchored on: the Irish fuel function (TII PAG Unit 6.11 / DoT TAF Module 8 Table 10, read): petrol 45.5–49.2, diesel 52.0–55.7 kWh/100 km at 80–100 km/h (my arithmetic, RED energy contents; an average-speed function, not steady cruise); BEV 17.5–21.1 kWh/100 km at 110 km/h from manufacturer highway data (Behrisch, Flötteröd & Wagner 2024, SUMO Conf. Proc. 5, read; data origin [VERIFY]); road-load physics ≈ 12–15 kWh/100 km at 80–100 km/h (my arithmetic, assumed parameters). [AUTHOR A24] |
| Disclosure | The cruise bands (1) were proposed **after** SUMO's own cruise values had been seen (literature_v0.md F7; toy f_emission.py at 100 km/h: petrol ≈ 53, diesel ≈ 66, PHEV (P) ≈ 55, BEV 14.8, PHEV (El) 18.9 kWh/100 km, my arithmetic). They therefore catch gross errors (units, class strings, conversions), not model bias. HBEFA4 diesel near the top of the band is a known model trait (literature_v0.md F7), not a plant bug. Rows (3)–(6) were written before any run on the built vTypes; the HBEFA4 BEV acceleration figure was already known (literature_v0.md F7) and is the reason for [AUTHOR A33] |
| Disclosed model property | PHEV (El) recovers nothing while braking in HBEFA4, BEV does (toy f_emission.py). Smoothing therefore saves more for PHEV (El) and ICE than for BEVs: a model property, not a controller effect. Energy is reported per powertrain |
| Output | the table e_class(u) at 10–120 km/h (10-km/h steps, linear interpolation between them), used by the report-only ceiling (§6.4); the idle rate per class, used by the origin-queue imputation row (§6.12) |
| Seeds, n | none (deterministic) |
| On FAIL | a disclosed model or parameter fix, never a silent rescale (for BEV and PHEV (El), per [AUTHOR A33]); G4 re-run only (no other P0 gate depends on energy) |

### 4.8 P0-G5 Step-size sensitivity (paired by seed)

| Field | Content |
|---|---|
| Question | Is the 0.2-s plant converged enough that conclusions do not hinge on the step? |
| Measurement | B0 and B1 triangle at **λ_c and λ_2** at **0.1 s** on seeds 040–059, paired by seed with the 0.2-s runs of G2/G3. Both steps use the same inflow and attribute manifests (arrivals on the 0.2-s grid are valid at 0.1 s). SUMO's own random draws differ between steps, as they differ between arms (§2.3); pairing removes the inflow variance only |
| Statistic | J1 = per-run mean door-to-door time of the cohort; J2 = triangle discharge at BN*, on the seeds with an active onset at BN* in both runs (≥ 5 such seeds at a level, else J2 is not computable there). ΔJ = median_s(J_0.1,s − J_0.2,s) / median_s(J_0.2,s), with a 95 % percentile bootstrap CI |
| PASS | form per [AUTHOR A20] (recommended: point estimate, consistent with §8.6): \|ΔJ\| ≤ **5 %** for J1 and J2, in both arms, at λ_c, and at λ_2 if λ_2 is admissible (a plant-invalid λ_2 is reported only); J2 computable at ≥ 1 gated level. A CI reaching beyond ±5 % is a FLAG, disclosed in every report |
| Source | lab convention (ARCH day_pattern_metanet_protocol_v3.md:439), no published source. The SUMO ACC docs recommend steps below 1 s, e.g. 0.1 s [VERIFY, summarising fetch]. The archive found IDM door-to-door times of 356 / 392 / 403 s at 0.5 / 0.2 / 0.1 s (ARCH round3_tm21_protocol.md:121-135): a true step effect of about 3 % between 0.2 and 0.1 s, inside the tolerance; a realism verdict is step-specific |
| Reported | censored share at each step (censoring at 11,700 s compresses J1 differences at over-saturated levels); onset and origin shares at both steps (the METANET step check FAILed on event classification although J moved 0.23 %; ARCH day_pattern_decisions_v0.md:53); CAV severe-event ratio; wave speed; the paired SD of ΔJ |
| Seeds, n | 7,400,040–059, n = 20 per arm and level (80 runs at about twice the cost) |
| On FAIL | as decided **now** in [AUTHOR A20]: (a, recommended) move to 0.1 s: C1–C8 re-run on 002–009 at 0.1 s ([AUTHOR A16d]), a new golden hash, then all of P0 on fresh seeds ([AUTHOR A16c]); no further step check at 0.1 s (disclosed); about twice the CPU for everything after; (b) keep 0.2 s with the FAIL disclosed in every report. Either way it counts in k |

### 4.9 Report-only rows (do not block P0)
- **P0-R1 Stop-and-go presence:** share of B0 runs per level with ≥ 1 stop-and-go cycle per 10 vehicle-km on the mainline. Wave-damping rules need waves; the band rule decides whether control is worth it.
- **P0-R2 Automation effect (B1 vs B0):** paired median relative difference of Dl, C and energy at λ_c, λ_c + 0.1 and λ_2, with 95 % CIs; never credited to control. It is also the first measurement of the speed-compliance effect of [AUTHOR A13] (CAVs at 100 km/h vs their B0 speed factors), disclosed before seed 7,400,100. The G3 flag applies.
- **P0-R3 ACC behaviour:** median time headway of CAVs in steady car-following; the platoon and approach tests of every screened candidate; CAV free-flow speed.
- **P0-R4 Wave period** τ per level.
- **P0-R5 Irish context:** pre-breakdown flows per lane vs the TII 2012 values (lane means 1,580 / 1,660 / 1,960 veh/h for lanes 1 / 2 / 3; per-site range 1,400–2,300 veh/h; practical capacity of an unmanaged lane "measured to be between 1,700 PCU’s per hour to 1,800 PCU’s per hour" in §7.1 and 1,715 / 1,862 / 1,824 pcu/h for lanes 1 / 2 / 3 in Table 5.2; read in full). Lane 1 is expected lowest. Context only: the TII values are breakdown flows from 2012, before the eMOS VSL, not queue discharge.
- **P0-R6 Drain and spillback:** censored share and origin-queue vehicle-hours per level (G2, later P2 stage 1). They feed the band guards (§6.8(g)), not P0.
- **P0-R7 HDV extreme deceleration** (a plant diagnostic, not the V11 metric): rate per 10⁴ vehicle-km in B0; a flag to the author if > 1 (ASSUMPTION: braking at about 0.9 g at speed is a near-crash).
- **P0-R8 Plant energy:** B0 kWh per vehicle-km per category and powertrain at λ_c and λ_2; share of vehicle-steps with \|a\| > 0.6 m/s² per arm (the HBEFA slope-derived range, unverified for HBEFA4; literature_v0.md critic C).
- **P0-R9 Zipper and lane ends:** per-lane discharge at the BN-LD section with the metronome FLAG (§2.7); lane 0's discharge against the floor; auxiliary-lane speeds and waiting counts at merge1 and merge2.

### 4.10 P0 verdict
**P0 PASS** iff P0-B and G1–G5 all PASS (intersection-union), with G1 evaluated first and alone. The P0 report lists every calibration choice with its seeds, every run in the ledger, the values against each criterion, the burned seeds, every deviation, both outcomes of any re-analysis, and the expected outcome of §0.4 next to the result. **Its verdict sentence states k**, the number of plant settings tried on check seeds (§9.2), and the thesis text repeats it.

---

## 5 P1 tool checks T0–T3 (seeds 7,400,060–089, n = 30, fresh)

### 5.0 What is built, levels and arms
- **Built only after P0 PASS:** `exec`, a minimal `v2x` (zone summaries, V2V lists, radar gap and closing speed), R4, the command log.
- **P1-B acceptance tests** (non-project seeds, no plant outcome; all must pass before seed 060): `exec` ramp, hold, one call per boundary, clip, entry rounding reached by a `slowDown` ramp (never a `setSpeed` step), release; **negative control:** a once-only `slowDown` variant must FAIL the hold test; `v2x` outputs equal values recomputed from the trace; an empty lane gives n = 0 plus a fallback flag; **contract test:** an injected HDV-only field and a clock field never reach an arm (V27, V48; `interfaces.md` §7); R4 logic; the command log enters the trace hash; **timing test:** R4's process CPU time per episode relative to B1 on a fixed micro-batch, which sets R4's CPU-time cap (§2.6 C8).
- **Levels** (from P0-C and P0-G2, calibration and check seeds only): **λ_sub** for T0b. **ℓ₁** = λ_c; **ℓ₂** and **ℓ₃** = the P2 grid points nearest λ_c + 0.1 and λ_c + 0.2. A P1 level that is plant-invalid under P0-G2(c) is replaced by the highest admissible grid point below it that is not already a P1 level (in practice ℓ₃ → λ_c + 0.05). All three are P2 grid points (§6.2). Every level ≤ λ_c + 0.1 is admissible by construction (a G2(c) failure at or below λ_c + 0.1 is a P0 FAIL); a P1 level above λ_c + 0.1 has its admissibility re-checked in T1a.
- **Arms:** B0, B1, R4(70) and R4(80): R4(c) is a constant CAV target c, with u = sign(c − target) at each boundary. Commands act from the first second of the episode, before any onset: the archive's first BN4 T0 applied control after breakdown and tested the wrong thing (ARCH t1_bn4_plant_checks_protocol.md:76-98).
- Addendum B (VoT) is frozen before seed 7,400,000, so T1b's C is fixed before any data. **Addendum C** (R1–R3 parameter spaces and the observation specs, §6.3) is committed before seed 060, before any commanding arm runs on a project seed.
- Every P1 batch shuffles its job order across arms (P0-B12), so CPU-guard pauses cannot follow arm order.

### T0a Command execution (gated; deterministic micro-scenarios on the built F3Z, no inflow, non-project seed 1)

| Field | Content |
|---|---|
| Question | Are commands carried out exactly as V26/V36 specify, with F3Z's chosen ACC and EIDM vTypes? Does SUMO release the vehicle between boundaries? |
| Scenarios | (1) a lone CAV in Z1 given −1, +1, then 0 for ≥ 10 boundaries; (2) a CAV behind a scripted HDV leader at 60 km/h, commanded to 90 km/h; (3) a CAV crossing Z1 → gap → Z2 (release, re-entry rounding), and a CAV leaving Z2 at 50 km/h and entering Z3 through the 500-m gap that contains merge 2 (V64; release still in progress at re-entry); (4) commands beyond [50, 100] km/h; (5) a new command during a hold; (6) zone entries at speeds 0.1, 1.2, 2.4, 2.6, 3.9 and 4.9 km/h above a multiple of 5 km/h, each with u = −1, 0 and +1 at the first boundary; (7) a CAV changing lanes, with lane changes enabled, during a ramp and during a hold; (8) negative control: once-only `slowDown` |
| PASS (all) | (1) ramp acceleration **±0.694 ± 0.005 m/s²** at every ramp step of a ±5 km/h command when unconstrained (5 km/h over 2 s = 0.6944 m/s²; toy A1, A5), except the first post-entry ramp, which is \|Δv\| / 2 s ± 0.005 m/s² with \|Δv\| ≤ 7.5 km/h (≤ 1.04 m/s²); (2) \|v − target\| ≤ 0.01 km/h at boundary + 2.0 s (± one step); (3) **hold:** unconstrained, ≥ 20 s, max \|v − target\| ≤ **0.01 km/h** and no step with a > +0.01 m/s² (no release between boundaries; toy A3: 0.000000 km/h); (4) a new command during a hold replaces it with a ramp (toy A7); (5) exactly one `exec` call per CAV per boundary and none between boundaries (toy A2b), including at a zone entry while a release is in progress; (6) entry target = current speed rounded to 5 km/h and clipped, reached by a `slowDown` ramp; no target outside [50, 100]; every clip logged; (7) behind the slower leader: 0 collisions, the gap never below the car-following minimum, the command acts only as an upper bound (toy L1/L2); (8) unconstrained exec-induced deceleration never below −0.70 m/s² (−1.05 m/s² on the first post-entry ramp); (9) release issued ≤ 2 s after zone exit; under [AUTHOR A10] (a) the release acceleration is logged; under (b) it is ≤ 0.70 m/s², and zone entry cancels an active release ramp (§2.5); (10) **0 exec-induced steps below −3 m/s²** in every scenario (a V36 hard brake must never come from `exec`); (11) during a lane change the target is kept and (2)/(3) hold on the new lane; (12) the negative control FAILs criterion (3) (toy a_A1_once_cav.csv: after the once-only call, the first acceleration is logged 2.4 s after the call, 0.4 s after the ramp ends, back towards 100 km/h at +2.6 m/s²) |
| On FAIL | code fix; no project seed consumed. Not a KILL |

### T0b Authority on speed and density (gated, directional)

| Field | Content |
|---|---|
| Question | Do CAV commands change the speed and density of **all** traffic in each zone, in the pre-registered direction? |
| Arms, level | B1 vs R4(70) at λ_sub (sub-critical: flow is conserved, so a lower cap must lower speed and raise density) |
| Measurement | per zone over the scored window: space-mean speed of all vehicles = Σ distance / Σ time in the zone; density = Σ time in the zone / (T · L_Z · lanes) (veh/km/lane) |
| Statistic | paired median relative difference vs B1, 95 % percentile bootstrap CI |
| PASS | in **each** of Z1, Z2, Z3 (intersection-union): speed Δ ≤ **−5 %** with CI upper bound < 0, **and** density Δ ≥ **+5 %** with CI lower bound > 0 |
| Rationale | 5 %: archive convention (ARCH t1_bn4_plant_checks_protocol.md:54-55), no published source. Directional, because a sign-agnostic T0 once passed a harmful actuator (ARCH t1_bn4_plant_checks.md:59-68). Sub-critical, because a cap applied inside a queue does not bind. Size check (my arithmetic, not a prediction): if HDVs were unaffected, 26 % of vehicles at 70 instead of about 100 km/h would cut the space-mean speed by about 10 % |
| Seeds, n | 060–089, n = 30 (half-width ≈ 4.5 % at σ = 0.10; §8.7) |

### T0c Authority at the bottleneck (gated, two-sided)

| Field | Content |
|---|---|
| Question | Can commands change outcomes where the breakdown happens (either sign)? |
| Arms, level | B1 vs R4(70) at the highest P1 level that is admissible after T1a (normally ℓ₃; all P1 levels are run for T1b) |
| Statistic | paired median relative difference of (i) Dl and (ii) served throughput in the peak hour at BN*'s section; Bonferroni over the two (α = 0.025 each) |
| PASS | (i) \|ΔDl\| ≥ 5 % with its 97.5 % CI excluding 0, **or** (ii) \|Δ throughput\| ≥ 3 % with its 97.5 % CI excluding 0 (3 %: ASSUMPTION; throughput moves less than delay) |
| Seeds, n | 060–089, n = 30 |

### T0d Sensing and command integrity (gated, exact, on every P1 run)
Zone summaries and V2V lists (the 5 nearest CAVs ahead within 300 m, plus the count and mean speed of all heard ahead; V50) equal the values recomputed from the trace; radar gap and closing speed equal the trace values; the contract-test log shows no field outside the observation spec; **0** hold violations (v > target + 0.1 km/h at a hold step, ramps and leader-constrained steps excluded); no target below 50 km/h. Reported: share of CAV-boundaries at 50 and at 100 km/h per arm (V47); share of commanded CAV-steps more than 5 km/h below target (leader-constrained).

**On T0b or T0c FAIL:** the actuator does not bind on F3Z. The consequence is decided now in [AUTHOR A34] (recommended: one disclosed zone move under V56, re-run on fresh seeds from [AUTHOR A16c], then a KILL of the CAV-only actuator on F3Z if T0b or T0c FAILs again; the alternative is an immediate KILL, the archive testbed precedent D5.14). A fix found after the look cannot turn this FAIL into a PASS without a fresh-seed re-run (§9.3). **On T0d FAIL:** code fix, re-verified on replicates of 5 P1 seeds; the P1 effect results stand, because R4 reads no V2X field.

### T1a Drop and artefacts in the experiment scenario, on fresh seeds (gated)

| Field | Content |
|---|---|
| Question | Does the triangle scenario break down at BN*, with a drop and a discharge consistent with P0, without artefacts, on seeds that P0 never saw? (Archive: onset shares drifted between calibration and check seeds) |
| Measurement | B0 at ℓ₁, ℓ₂ and ℓ₃. BN* is the bottleneck fixed in calibration; the other bottlenecks are reported separately |
| PASS (all) | (i) **realism artefact gate** at the P1 levels ≤ λ_c + 0.1 (normally ℓ₁ and ℓ₂): 0 teleports, 0 invalid B0 runs and ≤ 2 collisions in total over their runs; (ii) **admissibility** at the P1 levels above λ_c + 0.1 (normally ℓ₃; §8.8: B0 invalid share ≤ 5 %, i.e. ≤ 1 of 30): a level that fails it, and every grid level above it, become plant-invalid (this is not a T1a FAIL), and its artefact counts are reported; (iii) active-onset share at BN* ≥ 0.2 at ≥ 1 admissible P1 level; (iv) at the admissible P1 level with the most active onsets at BN*: the median triangle discharge at BN* ∈ **[floor, 2,300] veh/h/lane** (floor per [AUTHOR A25]) **and** ρ_T1 = that median ÷ Q_ff(BN*) from P0-G1 ≤ **0.97** (same section, estimator conventions and upstream exclusions; a cross-scenario replication of the drop, with no lower bound because the triangle confounds within-run levels); not computable → FAIL. A peak-relative drop alone is not enough: BN4's T1 passed at 0.862, then the plant failed realism at 900 veh/h/lane (ARCH t1_bn4_plant_checks.md:5-8) |
| Seeds, n | 060–089, n = 30 per level (shared with T1b) |
| On FAIL | treated as a P0 FAIL (§9.2) |

### T1b Control matters (gated)

| Field | Content |
|---|---|
| Question | Can a simple, pre-specified command rule improve the headline over the same fleet without commands? |
| Arms | R4(70) and R4(80) vs B1 at ℓ₁, ℓ₂ and ℓ₃: 6 pre-specified tests, no selection. If a P1 level becomes plant-invalid in T1a, its two tests are reported and dropped from the union, with m kept at 6 (conservative) |
| Statistic | r = median_s(C_R4 − C_B1) / median_s(C_B1); percentile bootstrap CI at 1 − 0.05/6 |
| PASS | at least one test with r ≤ **−5 %** and its Bonferroni CI upper bound < 0 |
| Power | z = 2.638 (α = 0.05/6, two-sided); with n = 30, 80 % power needs a true effect ≈ 0.80 σ: about 4 % at σ = 0.05 and 8 % at σ = 0.10 (σ = SD of the per-seed relative difference; my arithmetic, §8.7) |
| Rationale | archive T1c template (≥ 5 %, CI excluding 0; ARCH t2_mrg3_r1_protocol.md:49-54). Directional: authority is not usefulness (ARCH t1_bn4_plant_checks.md:59-68) |
| On FAIL | [AUTHOR A17], recommended (a): proceed to P2, whose first binding KILL is the stage-1 futility rule. An untuned R4 is a weak rule (the archive's untuned per-CAV PI gave +119 to +180 % delay), and the CLAUDE.md early KILL needs a tuned proven controller or the oracle; a FAIL here predicts but does not prove a P2 KILL |

### T1c Attribution (report-only)
B1 vs B0, and each R4 vs B0 and vs B1, in C, Dl, h, h_HDV, energy, TTT and served throughput at the three levels, signed, with 95 % CIs. The automation effect (B1 − B0) is never credited to control.

### T2 Mechanism (report-only)
Computed in P2 from the tuning and held-out runs, with no extra simulation (§6.11). Prior: inflow scheduling gave G of 2–4 % in the archive (ARCH notes_networks.md:392; CORR2 ALINEA over 4 inflow conditions 0.4 %). T2 never gates (CLAUDE.md; D5.1).

### T3 Determinism and common random numbers (gated)

| Part | Content |
|---|---|
| T3-early | calibration C7 (§2.6) |
| T3a | 10 runs drawn uniformly from the P1 run list (`numpy.random.default_rng(0)`), each re-run (i) in a fresh process on another worker inside a mixed 32-worker batch and (ii) as the second episode of one process after an in-process close/start (as RL resets will do); 2 of the 10 are also (iii) SIGSTOPped by the CPU guard for ≥ 60 s mid-run and resumed (they must not be killed by the CPU-time cap). Hash = per-step trace (all vehicles: id, x, lane, speed, acceleration to 12 decimals) + command log + per-vehicle energy, delay and hard brakes. PASS: **22 / 22 bitwise identical** |
| T3b | for every seed used in P0 and P1: inflow-manifest and attribute-manifest hashes identical across all arms. PASS 100 % |
| T3c | every ledger row holds config hash, code commit + dirty flag read at start **and** end, network spec hash, inflow hash, vType XML hash, observation-spec hash (per rule), **r-table hash, Addendum B constants hash** (VoT, prices and their date, LHV and density, road-load values), seed and role, validity, OPS re-run flag, metric summary, trace hash, SUMO version and build. PASS 100 % |
| Scope | one machine and one toolchain lock. Cross-machine determinism is not established (the EIDM docs warn that results may differ by compiler, processor or OS [VERIFY]); hashes are never compared across machines |
| Evidence | toy d_determinism.py: identical hashes over 4 concurrent processes × 2 in-process restarts; the archive found no determinism FAIL, but its hash covered aggregates only (port_map runner trap 7) |
| On FAIL | STOP; find the cause, fix, re-run every affected comparison (both outcomes logged); no P2 without a T3 PASS |

**P1 verdict.** PASS iff T0a–T0d, T1a and T3 PASS, and T1b PASSes or the [AUTHOR A17] rule says proceed.

**Planning variance for P2.** σ_plan,1 = 1.136 × the largest SD, over the admissible (cap, level) pairs among the six, of the per-seed relative difference R4 vs B0 on 060–089 (the 80 % upper confidence limit of an SD with df = 29; §8.7). It is reported, and the admissible (cap, level) samples of paired values feed the empirical calibration of the stage-1 futility threshold t (§6.5). Neither covers λ_c − 0.2, λ_c − 0.1, λ_c − 0.05 or the levels above ℓ₃ (stated in the P2 report).

---

## 6 P2: inflow band sweep, tuning of R1–R4, O and F, band rule, early KILL

### 6.1 Arms
- **B0, B1** at every level (the references).
- **R1** PI with saturation (Stern et al. 2018), re-parametrised for 100 km/h; `local` observation spec. The sign of its dx_s term is [VERIFY] before use.
- **R2** an explicit MicroAccel-family controller (Hayat et al.), local + planner mode; `zone` spec. Its parameters are unpublished, so they are tuned; its Eq. 14 is implemented as the clip the text describes (disclosed; literature_v0.md). Leader acceleration is not an onboard signal under V36, so it is a finite difference of the radar-derived leader speed over 2 s (a disclosed adaptation).
- **R3** CAV speed harmonisation upstream of each merge (FHWA-HRT-21-008 linear transition; its Eq. 12 [VERIFY]), with the loop inputs replaced by V2X zone means (a disclosed adaptation); `zone` spec.
- What R2's planner and R3 know about BN-LD, the expected first bottleneck at Z3's downstream end (6,000 m, V64), is fixed in Addendum C by [AUTHOR A30], decided (b) by V65 and re-read for V64: a V2X probe-summary unit on [6,000, 7,000) m, just downstream of the drop, with no commands there, is Z3's "next downstream zone" for every zone-spec arm (R2, R3, and later L2). R3 harmonises upstream of merges (FHWA-HRT-21-008); whether its transition is also applied upstream of BN-LD, a lane drop, is fixed in Addendum C [VERIFY that the FHWA method covers lane drops].
- **R4** a constant CAV target, one parameter in {50, 55, …, 100} km/h (11 values).
- **O(ℓ)** the informed oracle: the best (rule, candidate) looked up per level, tuned on tuning seeds only (`system_context.md` §4). **F** the best fixed (rule, candidate) at every level ("the best of R1–R4", V45). Both are chosen in §6.6.
- All commanding arms use the same `exec` layer at 2 s (`system_context.md` §4). Sources: literature_v0.md F1, F2, F4 (Stern 2018 and Hayat 2023 read in full; the FHWA report in the relevant chapters). VSL arms I1/I2 are not in the band rule [AUTHOR A21]. Native-rate (unquantised) rule versions are not run in P0–P2 [AUTHOR A22].

### 6.2 Level grid (rule fixed now, applied to λ_c from P0-C)
- **L = 8 levels:** {λ_c − 0.20, λ_c − 0.10, λ_c − 0.05, λ_c, λ_c + 0.05, λ_c + 0.10, λ_c + 0.20, 1.0}, rounded to 0.01. If 1.0 lies within 0.025 of another grid point, that other point is replaced by λ_c + 0.35; the P1 level that would have been the replaced point is then 1.0, its nearest grid point (§5.0).
- The grid is densest near critical, where the archive found authority (ARCH notes_networks.md:392). **λ = 1.0 is always in the operating map.** ℓ₁, ℓ₂ and ℓ₃ are the P1 levels.
- Levels marked **plant-invalid** by P0-G2(c) or T1a(ii) are not tuned; they keep their B0 and B1 rows in the map. The tuned levels are the others; L in every formula below counts tuned levels, including an edge level added under §6.10.

### 6.3 Addendum C and P2-B
- **Addendum C** is committed **before seed 7,400,060**, before any commanding arm runs on a project seed, so that no P1 contrast can shape it. Per rule it fixes: the parameter list and its dimension d; each parameter's **inner range** (sampled in stage 1) and **outer range** (the inner range widened by 25 % of its width on each side, clipped to physically admissible values; used only by the refinement of §6.10); its scale; the published default point mapped to 100 km/h (mapping disclosed); the Latin-hypercube sampler (`scipy.stats.qmc.LatinHypercube`, seed 0) and its 19 sampled points; the refinement sampler (seed 1). It also fixes the R4 grid and **freezes the observation specs** `local` and `zone` (`interfaces.md` §7 [PROPOSAL]): field list, normalisation constants, Z3's "next downstream zone" field, i.e. the V2X summary unit on [6,000, 7,000) m just downstream of the drop (BN-LD) of [AUTHOR A30] (V64 layout); the spec hash is recorded per rule. Any later spec change that touches a field a rule reads re-runs that rule's P2 on fresh seeds. The author approves Addendum C before seed 060; the checkpoint "plant and all opponents done" (High effort, ultracode on for the adversarial code review) reviews the code against it.
- **P2-B acceptance tests** (non-project seeds): each rule reproduces a hand-computed command sequence on a scripted scenario; each reads only its declared observation spec (contract test); the O lookup and the ledger resume work; per rule, a timing test (CPU overhead ratio over B1) sets its CPU-time cap (§2.6 C8).
- R1 and R4 may start stage 1 before R2 and R3 exist, on the same seeds. No futility, selection or band decision is taken until all four rules have finished the stage concerned.

### 6.4 Baselines and the headroom ceiling (report-only, [AUTHOR A5])
- B0 and B1 run on every seed and level that any tuned arm uses (stage 1, stage 2, held-out).
- **Ceiling.** After stage 1, for each level ℓ, an approximate upper bound on what any CAV-command arm could gain over B0 on the same inflow files (from the kill draft): G_max(ℓ) = 1 − median_s C_floor,s / median_s C_B0,s, with C_floor,s = [Σ_v VoT_v · w_v + Σ_v f_v] / D, where
  - w_v = queue-delay floor: the largest, over the bottleneck sections on v's route, of v's delay in a fluid first-in-first-out point queue at section k, with arrivals = desired departure + reference travel time to k and service rate Q_cap,k = 1.10 × the largest 5-min flow observed at section k over all B0 and B1 runs at all levels on 100–107 (10 % margin: ASSUMPTION);
  - f_v = the minimum over cruise speeds u ∈ [50, min(v_des, 100)] km/h of [VoT_v · L_v · (1/u − 1/u_ref,v) + p_v · e_class(u) · L_v], with e_class(u) from P0-G4 (interpolated) and u_ref,v the speed implied by r.
- **Labelled approximation, not a theorem:** it assumes first-in-first-out queues, no throughput above Q_cap, and no trajectory beating steady cruise on energy (pulse-and-glide could, under HBEFA4). It is reported per level with a 95 % bootstrap CI over seeds, next to the operating map, and it **never prunes a level or KILLs** in the primary design.

### 6.5 Stage 1: screen (seeds 7,400,100–107, n₁ = 8), additions and KILL-1
- **Runs:** every candidate at every tuned level, paired with B0 and B1: R1, R2, R3 with 20 candidates each (the published default + 19 LHS points; equal budget across R1–R3, [AUTHOR A15]), R4 with 11; **the same candidate set at every level**, so that the pooled objective and T2 come at no extra cost. 73 episodes per level and seed.
- **Objective** for a candidate at level ℓ: J = median_s(C_cfg − C_B0) / median_s(C_B0) (lower is better); gain g = −J. The **pooled objective** of a candidate is defined in §6.6.
- **Eligibility to advance** (a screen; in-sample point estimates, per candidate and level): the delay guard Δ_D ≤ +0.02 (§6.8(e) definition); the continuity-corrected hard-brake ratio vs B1 ≤ 1 + y (§8.5, [AUTHOR A14]); **at most 1 invalid run among the 8** (with 0 of 8, a candidate with a 2 % per-run invalid rate would be screened out with probability ≈ 0.15 per level; with ≤ 1 of 8, ≈ 0.01; my arithmetic). If fewer than 2 candidates of a rule qualify at a level, the lowest-J others fill the slots, flagged.
- **Metric screen** (ARCH lessons_metric_gameability.md §4, on stage-1 data, before stage 2): (1) constant policy: the R4 values are constant policies, and their C is reported; (2) extremes: if the best R4 value at any level is 50 km/h, the report shows the delay guard and the CAV speed give-up there; (3) decoupling: any arm with lower C but higher Dl than B0 beyond the guard is reported; (4) tautology: whether collisions or extreme decelerations ever occur; (5) exposure: all rates per fixed km; (6) harm moved onto HDVs: h_HDV of the best candidates vs B1 [AUTHOR A29]. It informs the report and never changes the band rule.
- **Additions** (§6.10): the edge-level check and the parameter-adequacy check run on stage-1 data; any triggered addition runs on 100–107 and joins stage 1 **before** KILL-1 is evaluated.
- **KILL-1 (stage-1 futility).** If, at **every** tuned level (an added edge level included), the best candidate over all rules (guards ignored, in-sample, refinement candidates included) has g < t, the claim on this plant is **KILLed**. The threshold t is calibrated **empirically** from P1 data and recorded in the P1 report, before seed 100:
  - for each admissible P1 (cap, level) sample of 30 paired values (C_R4,s, C_B0,s) on 060–089, a constant is added to every C_R4,s so that median_s(C_R4 − C_B0) / median_s(C_B0) = −0.10 exactly;
  - 10⁴ resamples of 8 seeds are drawn with replacement (`numpy.random.default_rng(20261013)`), and g* = −J* is computed in each;
  - **t = min(0.05, the smallest 1 % quantile of g* over these samples).**

  So a candidate whose true gain is 10 % falls below t with probability ≤ 1 % at a level whose paired-difference distribution resembles a P1 sample, without assuming normality or a median SE formula. The normal-approximation value t_N = min(0.05, 0.10 − 2.326 × 1.2533 × σ_plan,1 / √8) = min(0.05, 0.10 − 1.031 σ_plan,1) is reported alongside (σ_plan,1 = 0.05 → 0.048; 0.07 → 0.028; 0.10 → −0.003; my arithmetic). Selecting the best of 73 or more candidates only raises the in-sample estimate, so the real false-KILL rate is lower still. The calibration covers only the P1 levels (§5). If t ≤ 0, KILL-1 fires only if no candidate improves on B0 at all, and the realistic early KILL is KILL-2 (§10.3).

### 6.6 Stage 2: selection (seeds 7,400,108–137, n₂ = 30, fresh), O and F, KILL-2
- **Finalists per tuned level:** per rule, the 2 eligible candidates with the best stage-1 J at that level, plus per rule the 2 eligible candidates with the best stage-1 pooled objective, deduplicated (refinement candidates count as candidates of their rule); plus B0 and B1. At most 18 arms per level and seed.
- **Selection eligibility** mirrors the band rule: on all 38 selection seeds 100–137, a finalist is eligible at level ℓ if it meets band criteria (d)–(h) (§6.8) computed in-sample with the band's own statistics and the forms chosen in [AUTHOR A7] (V61: at least 5 % better than B1) and [AUTHOR A27] (point form, V65); (h) is an invalid share ≤ 5 % (≤ 1 of 38).
- **Selection** uses stages 1 and 2 together (n = 38) and the **paired** statistic, never the median level (ARCH STATUS #19: choosing by level picked an arm paired-worse than 4 of 5 rivals):
  - **O(ℓ)** = the eligible finalist with the lowest J at level ℓ (a per-level lookup tuned on tuning seeds only, never per evaluation seed); if none is eligible at ℓ, the finalist with the lowest J among those meeting (h), flagged;
  - **F** = among pooled finalists meeting (h) at every tuned level, the one with the lowest **pooled objective** J̄ = mean over tuned levels of J_ℓ, where J_ℓ is set to 0 (no gain) at every level at which the finalist is not eligible (fixed parameters at every level); ties are broken by the unpenalised mean J;
  - each rule's per-level and pooled bests are kept for the map (in-sample rows, labelled).
  O and F are chosen with the same effort on the same seeds. The lowest J stays the objective (the CLAUDE.md oracle is a lookup tuned on tuning seeds); the predicted pass rate of §6.7 is reported for the chosen arm and the two runners-up at each level.
- **KILL-2 (in-sample futility).** If, at **every** tuned level, the lowest J over all finalists (guards ignored) is > −0.10, no configuration reaches a 10 % median reduction even in-sample: the claim is **KILLed** and the held-out stage is not run. The in-sample minimum over the finalists is biased towards larger reductions, so this is conservative relative to band criterion (b).
- **σ_plan,2** = 1.136 × the largest SD over tuned levels of the per-seed relative difference O(ℓ) vs B0 on 108–137 (80 % upper confidence limit, df = 29). The SDs of the guard quantities (Δ_D, the hard-brake ratio, origin-queue time) on 108–137 are reported with it.

### 6.7 Held-out sample size (fixed after stage 2, before any held-out run)
- **(i) σ rule:** the smaller of {40, 60} for which z_m × 1.2533 × σ_plan,2 / √n ≤ 0.05, with m = 2L and z_m = Φ⁻¹(1 − 0.05/(2m)). For L = 8 (m = 16, z = 2.955): n = 40 if σ_plan,2 ≤ 0.085, n = 60 if ≤ 0.105 (my arithmetic; for L = 9: 0.084 and 0.103). Rationale: a true 10 % reduction then has its Bonferroni CI upper bound near −5 %.
- **(ii) Whole-rule check:** for every tuned level ℓ and A ∈ {O(ℓ), F} with in-sample r_A ≤ −0.10 on 100–137, 2,000 bootstrap resamples of n = 40 and of n = 60 seeds are drawn from the 38 selection seeds (rows of B0, B1 and A paired by seed); the full band rule (b)–(h) is applied to each, giving the pass shares P40 and P60.
- **n_eval = 60** if the σ rule requires it, or if P60 − P40 ≥ 0.10 for any such (ℓ, A) (ASSUMPTION); otherwise 40. If neither n satisfies the σ rule, n_eval = 60 and the achieved half-width is reported as a limitation.
- P40, P60, the expected bounds of the guards (e)–(g) and the binding criterion per (ℓ, A) go into the P2 report **before** the held-out stage. They are in-sample predictions, optimistic by construction (winner's curse).
- Seeds 200–239 or 200–259. Arms at every tuned level: B0, B1, O(ℓ), F (if O(ℓ) = F, one set of runs serves both); B0 and B1 also at untuned levels.

### 6.8 The band rule (fixed now; non-learning arms only)
For a tuned level ℓ and an arm A ∈ {O(ℓ), F}, on the held-out seeds. The effect criteria (b)–(d) use intervals at the Bonferroni level 1 − 0.05/m, m = 2L (a one-sided bound is the corresponding end of that two-sided interval, which is conservative). The guards (e)–(g) use the form chosen in **[AUTHOR A27]** (recommended: the point estimate within the margin, with the Bonferroni interval reported).

| # | Criterion | Rule |
|---|---|---|
| (a) | Admissible level | ℓ is not plant-invalid (P0-G2(c), T1a(ii)), and the single admissibility rule of §8.8 holds on the held-out B0 runs (B0 invalid share ≤ 5 %, n ≥ 40) |
| (b) | Effect | r_A = median_s(C_A − C_B0) / median_s(C_B0) **≤ −0.10** (V45: g = 10 %) |
| (c) | Significance | the CI upper bound of r_A is **< 0** |
| (d) | Beats B1 by at least 5 % ([AUTHOR A7], decided by V61) | r_A,B1 = median_s(C_A − C_B1) / median_s(C_B1) **≤ −0.05** **and** its CI upper bound **< 0** (A7 option (b); the same point-plus-CI structure as (b) and (c) vs B0). v0 recommended only the CI condition (option (a)) |
| (e) | Delay guard (V37) | Δ_D = median_s(Dl_A − Dl_B0) / max(median_s(Dl_B0), 0.05 · median_s(R_tot)) **≤ +0.02**. The floor in the denominator (ASSUMPTION) keeps the guard continuous where B0's delay is near or below 0; there the margin is 0.1 % of the cohort's total reference time |
| (f) | Hard braking (V25) | the pooled CAV hard-brake rate ratio A / B1, continuity-corrected (§8.5), ≤ **1 + y** [AUTHOR A14]; its bootstrap and exact conditional intervals are reported. No event-count switch (the synthesis's "fewer than 20 events" fallback is removed) |
| (f′) | Hard braking vs B0 (only if activated) | activated, by a rule fixed now, if P0-G3's R₃ (B1 vs the same vehicles in B0 at −3 m/s²) exceeds 1 + y at either gated level: the same as (f) with the same vehicles in B0 as the reference |
| (g) | Gameability guards ([AUTHOR A23]) | pooled totals over seeds: (g1) Σ_s censored_A,s ≤ Σ_s censored_B0,s; (g2) Σ_s origin-queue veh·h_A,s ≤ 1.02 × Σ_s origin-queue veh·h_B0,s (1.02 mirrors V37; ASSUMPTION); and for each of the two quantities, the number of seeds with A > B0 does not exceed the number with B0 > A (sign count) |
| (h) | Validity | A's invalid share ≤ 5 %; invalid runs enter (b)–(g) as in §8.4 |

- **Level ℓ is in the band** iff (a) holds and, for A = O(ℓ) or A = F, all of (b)–(h) hold, and (f′) if activated. The **band** is the set of such levels. It need not be contiguous; there is no interpolation or smoothing; its hull is reported but not used.
- **Band table** at every tuned level, in or out of the band: r_A vs B0 and vs B1 with CIs; the **decomposition** (C_B0 − C_B1) / C_B0 (automation share) and (C_B1 − C_A) / C_B0 (control share) with CIs; Δ_D; **served throughput with its CI**; TTT; h and h_HDV (with the [AUTHOR A29] FLAG when A/B1 > 1 + y); censored counts; origin-queue time; validity; and which criterion binds. The words "≥ 10 % vs no control" are never written without the automation share next to them ([AUTHOR A7]).
- **Error control, stated exactly.** The family-wise error of "some level is in the band" is ≤ 0.05 **under the null of no gain** (θ ≥ 0 for every (ℓ, A)): (c) is tested at α/m and the union over the m = 2L claims is Bonferroni-corrected; the guards and (d) only make entry harder. The 10 % threshold (b) is a point criterion with no error control, consistent with D5.8's bar (a median of 10 % with the CI excluding 0), so a level whose true gain is below 10 % can enter. **Operating characteristic** (normal planning approximation, n = 40, σ_plan,2 = 0.085, SE ≈ 0.0168, guards and (d) ignored; my arithmetic): P(a (ℓ, A) pair enters) = 0.04 at a true 7 % gain, 0.12 at 8 %, 0.28 at 9 %, 0.50 at 10 %, 0.88 at 12 %. Seeds 200–259 decide **band membership only**; any effect size quoted for a band level or regime is re-estimated on fresh seeds (300+) in the learning-phase protocol (§12).
- **Why both O and F.** V45 says "the best non-learning arm or the informed oracle". O(ℓ) is the oracle; F is the best fixed tuned rule. Testing both, each at α/m, keeps the family at 2L pre-chosen tests.

### 6.9 GO, or KILL-3
- **KILL-3:** band empty → **KILL** of the claim on F3Z with this fleet (CLAUDE.md, Method): no tuned proven controller (tuned within the Addendum C ranges and the pre-registered refinement of §6.10) or informed oracle beats no control by ≥ 10 % at any admissible level. No bound is revisited; a re-designed plant needs a new protocol. All three KILLs are logged with every level's numbers, and the full operating map is still reported.
- **GO:** band non-empty. The band and the map are frozen in the P2 report and become the pre-registered regime set for the learning phases (§12). The **designated level ℓ*** is fixed at the same time by the rule of [AUTHOR A6] (recommended (c): λ = 1.0 if it is in the band, else the band level closest to 1.0, ties to the higher), before any learner data; the later D5.8 test "≥ 10 % vs no control at the realistic level" is made at ℓ* only, so it needs no multiplicity correction across band levels.
- **Wording** ([AUTHOR A6]): no band level is called "realistic" unless it is λ = 1.0; ℓ* is called "the designated level". λ = 1.0's row is always shown, in or out of the band, with the §2.1 statement that the nominal inflow exceeds F3Z's capacity on paper.

### 6.10 Additions after stage 1 (pre-registered, once each)
- **Order, fixed now:** stage 1 → (i) edge-level check and (ii) parameter-adequacy check, both on stage-1 data → triggered additions run on 100–107 → KILL-1 on the extended set → stage 2 on the extended set → KILL-2 → n_eval → held-out. Nothing is added after stage 2, so no addition can be prompted by stage-2 data or rescue a KILL-2.
- **(i) Edge level.** If the level with the lowest stage-1 J (the best candidate over all rules) is the lowest or the highest tuned level, one level beyond it (λ_c − 0.30, or the highest tuned level + 0.15) is added: B0, B1 and all candidates on 100–107, then stage 2. L and m grow by one and two, and F's pooled objective covers it. Cost ≈ 584 episodes in stage 1 and ≤ 540 in stage 2 at L = 8 (my arithmetic). The archive found authority only in narrow bands just above critical (ARCH notes_networks.md:392), so an optimum at the grid edge warns that the grid missed it.
- **(ii) Parameter adequacy.** If, at any tuned level, the best stage-1 candidate of R1, R2 or R3 lies within 10 % of the normalised inner-range width of a range bound, or is the published default, one refinement batch runs for **all three** rules (equal budget): per rule, 10 LHS points (refinement sampler) in a box of half-width 25 % of each parameter's inner range around that rule's best pooled stage-1 candidate, clipped to the outer range; at every tuned level, on 100–107. R4 is not refined: its grid already spans the V47 bounds. Cost ≈ 10 × 3 × L × 8 = 1,920 episodes at L = 8, about 10 h (my arithmetic). Per rule, the spread of J across candidates and the gap between the best and the default are reported. Reason: a false KILL from under-tuning is the most expensive error for the thesis, and the archived PI with ring constants gave +119 to +180 % delay untuned (literature_v0.md:757).

### 6.11 T2, G and headroom H (report-only)
- **G(ℓ)** = median_s(C_F − C_O(ℓ)) / median_s(C_F) on the held-out seeds (paired), with a 95 % CI: the adaptation room between the fixed and the per-level tuned rule. Because O(ℓ) may switch rules across levels, it is labelled "G (oracle with rule switching)".
- **Per rule, in-sample** on 100–137: the pooled best vs the per-level best, labelled "biased upwards" (selection on the same seeds); whether the per-level optimal parameters differ across levels; the cost of using a neighbouring level's optimum; and the same-rule lookup I_F (F's rule with its per-level best parameters), the CLAUDE.md "I" in its narrow sense.
- **Headroom H** per [AUTHOR A31], decided (b) (V63): no non-learning adaptive scheduler and no MPC arm run in P2 (MPC dropped and disclosed, `system_context.md` §4, allowed under D5.8; the scheduler drop disclosed as a deviation from CLAUDE.md, Method). The quantity reported is labelled "G, i.e. H without the adaptive scheduler", never "H". Prior: archive inflow scheduling gave G of 2–4 %.
- Never gated.

### 6.12 Operating map (every level, every arm)
One table per level, tuned, untuned or plant-invalid, with B0 always next to B1 and the tuned rules (each rule's pooled and per-level best, in-sample and labelled; O(ℓ) and F, held out): C (€/vehicle-km); Dl; energy in kWh per vehicle-km by category and powertrain (HDV energy labelled "estimated", V23); h; h_HDV and the HDV severe-event rate ([AUTHOR A29]); stop-and-go; TTT; served throughput with its CI; per-zone travel time; CAV speed give-up; target floor and ceiling occupancy (V47); origin-queue vehicle-hours; censored count; scenario totals in kWh and € (V24); validity counts; r vs B0 and vs B1 with CIs; the automation/control decomposition; the guards; band membership; G; the ceiling; the metronome and lane-end FLAGs.

**Sensitivity rows** come from the same runs by re-scoring (no new simulation). They are never used for the band, but **band membership under each row is reported**, and a level whose membership changes under a row is labelled (e.g. "price-dependent"):
- the V21 lower-price / resource-cost row, and truck fuel net of VAT [AUTHOR A18], with values and sources fixed in Addendum B;
- truck energy by COPERT and by the TII OGV2 fuel function (V34), both average-speed functions evaluated on each vehicle's **per-edge** average speed (edge length ÷ edge traversal time; ASSUMPTION), with COPERT's extrapolation above 80 km/h disclosed; report-only: whether the sign of r_A vs B0 agrees across the three truck models at every band level (pre-registered as in `truck_energy_check_v0.md`);
- BEV energy by a road-load physics model in our code, if [AUTHOR A33] (b) is chosen;
- C with censored trips completed by imputation (each censored vehicle's remaining planned km at its category's reference pace, plus cruise energy at 100 km/h for cars and 90 km/h for trucks from e_class) and C with origin-queue idle energy (origin-queue time × the class idle rate from P0-G4) [AUTHOR A23];
- the guards with a reference-only failure encoded as 0 instead of the arm's worst case (§8.4).

---

## 7 Seed allocation

The seed guard (P0-B9) enforces this table in code, and the burned seeds are written to a ledger after each check (as in ARCH report_S1:82-88). An exploratory test once consumed 90 reserved confirmatory seeds in the archive (ARCH t1_meter_gscan_protocol.md:240-243); the guard exists to prevent that.

| Seeds (7,400,…) | n | Approved role | Used by | Arms × scenario | Episodes (≈) |
|---|---|---|---|---|---|
| 000–001 | 2 | calibration | P0-S smoke; golden B0 hash (000) | B0, B1 × triangle 0.7 and 1.0, plateau 0.8 | 12 |
| 002–009 | 8 | calibration | P0-C, C1–C8 (C4 after its non-project pre-screen) | §2.6: C1 56, C2 64, C4 16 B0 + ≤ 64 B1, C5 8 | ≈ 210 (+ 16 if C1 extends down; + 16 or 24 if C2 extends) |
| 010–039 | 30 | plant and tool checks | P0-G1 | B0 plateau at λ_a | 30 |
| 040–059 | 20 | plant and tool checks | P0-G2, G3, G5 | B0, B1 triangle at λ_c, λ_c + 0.1 and λ_2; B0, B1 at λ_c and λ_2 at 0.1 s | 120 + 80 at 0.1 s |
| 060–089 | 30 | plant and tool checks | P1: T0b–T0d, T1a–T1c; T3 replicates | B1, R4(70) at λ_sub; B0, B1, R4(70), R4(80) at ℓ₁, ℓ₂, ℓ₃ | 420 (+ 22 replicates) |
| 090–099 | 10 | plant and tool checks | reserve: the P0-G1 computability extension only | B0 plateau at λ_a | ≤ 10 |
| 100–107 | 8 | tuning | P2 stage 1 (with B0, B1), and the §6.10 additions | 73 × L (+ 73 × 8 per edge level; + 30 × L × 8 for a refinement) | ≈ 4,672 at L = 8 (+ ≈ 584; + ≈ 1,920) |
| 108–137 | 30 | tuning | P2 stage 2 (with B0, B1) | ≤ 18 × L | ≤ 4,320 |
| 138–199 | 62 | tuning | reserve: re-runs after a bug fix (§9.3), only through a dated addendum | — | 0 planned |
| 200–239 (–259) | 40 (60) | tuning, held out from all selection | P2 band evaluation | B0, B1, O(ℓ), F × L | 1,280 (1,920) |
| 260–299 | 40 | tuning | reserve; a candidate for the D5.8 re-tuning of the rules (§12, [AUTHOR A32]) | — | 0 planned |
| 300–499, 500–699, 700–999 | — | validation, test, reserved confirmatory | **not used** in P0–P2 | — | 0 |
| 7,410,000–7,419,999 | — | DRL training | **not used** | — | 0 |
| 7,401,000–7,401,999 | — | **approved 2026-10-13** (V62; [AUTHOR A16c]) | re-rounds after a plant variant, an insertion, ACC or step change, a zone move ([AUTHOR A34]), or a fresh-seed re-check under §9.3 or after a G3 flag deviation | as the round replaced | as needed |
| 1–999 (non-project) | — | **approved 2026-10-13** ([AUTHOR A16a], V65) | P0-B (incl. the ACC pre-screen), P1-B, P2-B, P0-G4, T0a | no F3Z plant outcome is observed | — |

- A seed means one inflow realisation plus one attribute manifest; every arm, level and step on that seed is paired with it. Using the same seed number at several levels inside one round is common random numbers across levels, not reuse across rounds.
- **No P0 seed is reused in P1**, and no selection seed in the band evaluation.
- Calibration seeds 002–009 may be reused for re-calibration after a plant variant, an insertion change, a step change or a new ACC candidate, because they never feed a PASS, only a STOP or a design quantity [AUTHOR A16d].
- The archived ranges 7,100,000–7,399,999 are never used.
- If a needed round does not fit in the approved or the requested ranges, the protocol stops until the author approves seeds.

---

## 8 Statistics

### 8.1 Unit and convention
The unit of replication is the seed. Every comparison is paired on seeds. The binding statistic is the **median of paired differences** θ = median_s(Y_arm,s − Y_ref,s). Relative effects are r = θ / median_s(Y_ref,s), the denominator over valid reference runs (CLAUDE.md, Statistics; ARCH vsl_lab/eval/stats.py `rel`). The sign is arm − reference throughout (negative = the arm costs less); a gain is g = −r. The median of per-seed relative differences is reported alongside as a sensitivity row and never decides. P0-G5 pairs the two steps on the same seed in the same way.

### 8.2 Confidence intervals
Percentile bootstrap over seeds: seed indices are resampled with replacement, and the numerator and denominator medians are both recomputed in every resample. B = 20,000 resamples, generator `numpy.random.default_rng(20261013)` (a fixed analysis seed outside every project block; it seeds only the resampling, never a simulation), recorded per table. Two-sided 95 % unless stated; Bonferroni intervals at 1 − 0.05/m; a one-sided bound is the corresponding end of the two-sided interval at the stated level. Shares: Clopper–Pearson. Event rates per exposure: exact Poisson (Garwood); rate ratios also get the exact conditional (binomial) interval as a reported row. Between-run estimators (P0-G1): bootstrap within the onset and no-onset groups.

### 8.3 Multiplicity

| Family | Structure | Correction |
|---|---|---|
| Criteria inside one check (e.g. G1 (a)–(d); T0b over three zones and two quantities; G3 over two levels; the band criteria (a)–(h) for one (level, arm)) | all must pass (intersection-union) | none needed |
| T0c: Dl or throughput | union of 2 | Bonferroni, α = 0.025 each |
| T1b: 2 caps × 3 levels | union of 6 (tests at a level found plant-invalid are dropped, m stays 6) | Bonferroni, α = 0.05/6 |
| P2 band: (level, arm) claims for L tuned levels and A ∈ {O(ℓ), F} | union of m = 2L, each an intersection | Bonferroni, α = 0.05/m for the effect components (c), (d); the guards in the form of [AUTHOR A27] |
| KILL-1, KILL-2 | in-sample futility rules; can only stop | none (conservative by construction) |
| T2, G, H, the ceiling, the operating map, sensitivity rows, P0 report rows | report-only | none; labelled descriptive |

The band's family-wise error statement holds under the null of no gain only (§6.8); the 10 % threshold is a point criterion.

### 8.4 Invalid and collapsed runs (V6, [AUTHOR A19])
An invalid or collapsed run is that arm's failure on that seed; an OPS failure is re-run once and is not scored (§2.7). Encoding before any statistic:
- the failed arm-run's C, Dl and delay-type values are set to **+∞**;
- **effect criteria** (b)–(d) and the selection objective: if only the reference (B0 or B1) failed on a seed, the paired difference on that seed is **0** (no credit for a baseline artefact; conservative for claims);
- **guards** (e)–(g): if only the reference failed on a seed, the arm's paired guard difference on that seed is set to the **largest (worst) value of that arm's paired guard differences over the valid seeds** at that level, so that a baseline failure cannot make an arm look harmless; the 0 encoding is reported as a sensitivity row (§6.12);
- if both failed, the arm's failure counts: **+∞**.
Medians and percentile bootstraps are well defined with +∞ as long as fewer than half of the seeds fail; if half or more fail, the statistic is +∞ and the criterion FAILs. Pooled event rates keep the events and exposure an invalid run recorded (runs continue to the end, `interfaces.md` §9). Failed runs are reported per arm and level and never dropped.

### 8.5 Rare events
CAV hard braking (V25), CAV severe deceleration (P0-G3) and the HDV rates use the **pooled rate ratio**: (Σ events / Σ exposure km) of the arm over that of the reference, over the seeds of the comparison, with a percentile bootstrap over seeds. This deviates from the single convention, because many seeds can have zero events and the median of paired differences then degenerates. The deviation is disclosed in every table that uses it. Wherever a ratio is gated in P2, it is **continuity-corrected**: R̃ = ((k_A + 0.5) / E_A) / ((k_ref + 0.5) / E_ref), with k the pooled counts and E the pooled exposures (ASSUMPTION: a standard 0.5 correction). R̃ is continuous in the counts and defined at zero events, so no event-count switch is needed; with zero events in both arms and equal exposure, R̃ = 1. P0-G3 uses the uncorrected R, because its counts are large (§0.4).

### 8.6 Point-estimate gates vs CI gates
Plant-plausibility checks (P0-G1, G2, G4, G5) gate on point estimates lying in literature-anchored or labelled bands, with CIs reported: they are plausibility checks, not effect claims, and a CI inside a 3–18 % band would need far more runs than the seed block holds. P0-G3(b) gates on a point estimate **and** an upper confidence bound (≤ 1.2), because sequential candidate looks would otherwise let a ratio slightly above 1 pass on noise. Effect claims (T0b, T0c, T1b, band (c) and (d)) gate on CIs. The band guards follow [AUTHOR A27].

### 8.7 Sample sizes
- **Planning approximation** (labelled as such): for normal paired differences, SE(median) ≈ 1.2533 σ/√n, so the half-width of a CI at Bonferroni level z is z × 1.2533 σ/√n. It is used for planning only; KILL-1's threshold is calibrated empirically instead (§6.5), and the held-out n also uses a resampling check of the whole band rule (§6.7).
- **Planning σ** is the 80 % upper confidence limit of the SD from planning data: factor √(df / χ²₀.₂₀(df)) = 1.351 for the 8 calibration seeds (df = 7) and 1.136 for 30 seeds (df = 29).

| Check | n | Justification (my arithmetic) |
|---|---|---|
| P0-G1 | 30 (+10) | P(onset split not computable) ≤ 0.03 for a true onset share in [0.3, 0.7]; the extension gives ≤ 0.016 at 0.25/0.75. Q_dis validity is gated separately (≥ 5 valid runs) |
| P0-G2, G3, G5 | 20 per level and arm | R-d needs ≥ 20 onset runs pooled with G1; wave speed needs ≥ 5 valid estimates; artefact and insertion gates are exact counts; G5 compares paired medians at a 5 % tolerance (archive across-seed CV of the mean time in system 0.030–0.062 for no control, computed in the review from `/home/catalin/work/phd/vsl_lab_runs/t4/gscan_1791047971`, 10 seeds per cell; the paired step SD is unmeasured and reported) |
| T0b, T0c | 30 | a 5 % effect is resolved when σ ≤ 0.10 (95 % half-width 4.5 %) |
| T1b | 30 | MDE at 80 % power ≈ 0.80 σ (about 4 % at σ = 0.05, 8 % at σ = 0.10) |
| P2 stage 1 | 8 | t calibrated so that a true 10 % candidate is falsely screened out with probability ≤ 1 % per level at the P1 levels (§6.5); not calibrated at other levels |
| P2 stage 2 | 30 (selection on 38) | 95 % half-width ≈ 0.40 σ on the 38 selection seeds (≈ 0.45 σ on the 30 stage-2 seeds alone) |
| P2 held-out | 40 or 60 | §6.7: Bonferroni half-width ≤ 0.05 when σ_plan,2 ≤ 0.085 (n = 40) or ≤ 0.105 (n = 60), m = 16; and the predicted pass rate of the whole rule |
| Band guard (e), for orientation | 40 | under a **non-inferiority** form at α/m, an arm with a true Δ_D = 0 passes with probability 0.17 / 0.026 / 0.007 at σ_D = 0.05 / 0.10 / 0.20; under the recommended point form, 0.98 / 0.84 / 0.69; an arm with a true +5 % passes the point form with probability 0.001 / 0.065 at σ_D = 0.05 / 0.10 (normal approximation; [AUTHOR A27]) |
| Band guard (f), for orientation | — | a non-inferiority bound exp(z·√(2/N)) at z = 2.955 and equal true rates is about 1.52 / 1.21 / 1.14 at N = 100 / 500 / 1,000 events per arm; about 1,920 events per arm are needed to reach 1.10 (Poisson, no overdispersion; my arithmetic) |

The archive's failures of habit are the reason for this table: a 10-seed screen had CI widths of about ±40 s against a 10 s target, and in R5-M2 a 3–5 % effect was below what 100 seeds resolved per learner (ARCH t1_meter_gscan_protocol.md:126,238).

### 8.8 Share and count gates, and the single admissibility rule
Every share-based gate states its minimum n and tolerance (the archive stopped learners spuriously at 1 of 96 > 1 % and 4 of 64 > 5 %; ARCH t1_meter_gscan_protocol.md:112-118). Two roles are kept apart:
- **Realism artefact gates** (P0-G1(d) on its original 30 runs; P0-G2(c) at λ_c and at a λ_2 ≤ λ_c + 0.1; P0-G3(a); T1a(i) at the P1 levels ≤ λ_c + 0.1): exact counts with **zero tolerance** for teleports, invalid runs and health FAILs, and ≤ 2 collisions in total, over the stated runs. Near critical the plant must be clean; these are realism properties of the plant, as the brief requires a drop "without artefacts". Whether to split them into code-integrity FAILs (zero tolerance) and rate-based traffic-artefact gates is an option in [AUTHOR A24].
- **Admissibility of a level** (one rule everywhere it is used: P0-G2(c) at λ_2 > λ_c + 0.1, T1a(ii) at the P1 levels above λ_c + 0.1, band (a)): the B0 invalid share at that level ≤ **5 %** over the runs of that check (≤ 1 of 20, ≤ 1 of 30, ≤ 2 of 40, ≤ 3 of 60). A level that fails it, and every grid level above it, is plant-invalid: kept in the map, never tuned, never in the band.
- **Arm validity:** stage-1 advancement ≤ 1 invalid run of 8 (a screen, with a flagged fill-in rule, §6.5); selection eligibility and band (h) ≤ 5 % (≤ 1 of 38; ≤ 2 of 40; ≤ 3 of 60).

---

## 9 FAIL handling and deviations

### 9.1 Kinds of FAIL

| Kind | Checks | Consequence |
|---|---|---|
| Code | P0-B, P1-B, P2-B, T0a, T0d, T3 | fix; no project seed consumed for unit tests; plant runs affected by the bug are re-run (§9.3); logged in the commit and the ledger |
| Operations | a hung or killed worker (§2.7) | re-run once on the same seed, logged; a second hang is a FAIL of that arm, reported |
| Calibration futility | F1–F3 | P0 FAIL path (§9.2) without spending a check seed |
| Calibration futility | F4 | [AUTHOR A11]: P0 KILL, or a new CAV base model under a new protocol |
| Calibration futility | F5 | STOP; a re-designed plant or inflow needs a new protocol ([AUTHOR A26] superseded by V58/V64) |
| Plant | P0-G1, G2 (a)–(c), T1a | STOP; the plant-variant ladder (§9.2), with author approval |
| Insertion | P0-G2 (d) | the next insertion configuration of the §2.2 order; C1–C8 re-run on 002–009, then G1 and G2 on fresh seeds; not a plant-model variant; counts in k |
| ACC base model | P0-G3 | the next surviving ACC candidate (§2.6 C4) on fresh seeds; G3 and G5 re-run; counts in k; exhausted → [AUTHOR A11] |
| Step | P0-G5 | as decided in [AUTHOR A20]; counts in k |
| Energy | P0-G4 | disclosed model or parameter fix; G4 re-run (BEV per [AUTHOR A33]) |
| Actuator | T0b, T0c | as decided in [AUTHOR A34] |
| Usefulness | T1b | as decided in [AUTHOR A17] (recommended: proceed to P2) |
| Claim | P2 | KILL-1, KILL-2, KILL-3, or GO; no plant variant inside P2 |

### 9.2 Plant-variant ladder and the settings counter (fixed now; each use needs the author's approval and a dated deviation note)
- **At most two plant-model variants after the specified plant (V0).** Each variant re-runs calibration C1–C8 on 002–009 ([AUTHOR A16d]) and **all** of P0 on fresh seeds from the requested range ([AUTHOR A16c]), then P1.
- **Settings counter k.** k counts every plant setting whose check ran on check seeds: the first plant counts 1, and every later insertion configuration, ACC candidate checked on fresh seeds, step change and plant-model variant adds 1. **k ≤ 7**: the original plus at most six changes (V59, author 2026-10-13); an eighth would be a **P0 KILL**. Candidates rejected in calibration only (the ACC pre-screen, C3, C4) do not count in k but are listed in the P0 report. k appears in every P0 verdict sentence and in the thesis text (principle 11).
- **Order rule (fixed now, not chosen after seeing the failure):** if the failing check is G1 or T1a and BN* is a merge (BN-M1 or BN-M2), V-1 comes first; otherwise (BN* is the lane drop, or a G2 failure) V-2 comes first. The other variant is second. On paper BN* is expected to be BN-LD, the lane drop at the end of Z3 (V64, §2.1), so V-2 is the likely first variant (v0 expected BN-M2 and V-1).
- **V-1: zipper-type junctions at the OR1 and OR2 merges.** Archive ZM3 produced the only measurable merge drop (ρ = 0.967), but its discharge (1,528 veh/h/lane) failed the floor (ARCH t2_zipmerge_protocol.md:31-38). Expected effect on F3Z: unknown.
- **V-2: HDV cars on SUMO IDM defaults.** In the archive P3 pre-check, IDM at its defaults discharged a standing single-lane queue at 2,323–2,335 veh/h/lane with 0 teleports (ARCH docs/lab/day_pattern/p3_precheck.md:9-18). This shows that IDM's car-following does not by itself hold discharge below the floor. It is not a merge discharge: every archive merge plant discharged less, and 2,323–2,335 lies above this protocol's 2,300 bound, so whether F3Z passes with IDM is exactly what V-2 tests. IDM stranded ramp vehicles at a dead-end acceleration lane in MRG3 (ARCH round2_protocol.md:119-123); F3Z has no dead-end acceleration lane, but stranding remains possible (§2.1) and the detector stays.
- **Not a variant: a lane drop without the zipper node.** The archive's non-zipper lane drop LD3 (priority nodes, ARCH vsl_lab/netgen/mrg3.py:29, :54) also failed realism: H5 Q_dis not computable (n = 0+8), H3 ρ = 1.037 (ARCH docs/lab/t2_realism_ld3.md). So replacing the zipper is not expected to help and is not pre-registered; the zipper's own behaviour is watched through the metronome FLAG and the lane-end attribution (§2.7). Under V64 this concerns the expected BN*; the zipper node is kept.
- **Never used as a fix:** `lcAssertive` (it moved onsets to the entry), driver error terms above the SUMO defaults (the H4 collapse), a higher time-to-teleport, any bound change.
- **Not plant-model variants** (they do not count towards the two, but they count in k): the insertion configuration (G2(d)), ACC candidates (G3), the step (G5).
- **Hard stop:** after the second variant fails, or when k would exceed 6, **P0 KILL**: "no realistic, artefact-free F3Z plant with this fleet in SUMO 1.27.1 at the chosen step, after k plant settings". A headline on a plant with a disclosed realism FAIL is ruled out ([AUTHOR A1], V59). A re-designed plant needs a new protocol.

### 9.3 Bugs found after results
Fix, re-run everything affected, log both outcomes (CLAUDE.md). **Asymmetry** (archive decision W13, ARCH day_pattern_decisions_v0.md:67): a fix that turns a PASS into a FAIL counts at once; a fix that turns a FAIL into a PASS on the *same* seeds does not count. The check is re-run on fresh seeds (the 138–199 reserve in P2, the requested range in P0–P1), and only that run can PASS.

### 9.4 Addenda (dated, committed before the data they govern; never relax a bound)
- **B** before seed 7,400,000 (no data needed): VoT_car and VoT_truck in 2026 € with every step written out (`interfaces.md` §5.4, V54; only the uplift is open); the V21 prices with their date; the sensitivity-row prices and their sources; the energy constants (LHV, density); the road-load values used by the G4 acceleration floor and, if chosen, the BEV physics row ([AUTHOR A33]); the hash of these constants (T3c).
- **A** after P0-S: estimator or implementation fixes found by the smoke test.
- **D** (informational, not a deviation) after P0-C and whenever needed: CPU plan updates.
- **C** before seed 7,400,060, before any commanding arm runs on a project seed: R1–R3 parameter spaces (inner and outer ranges, defaults, dimensions, the samplers and the sampled points), the R4 grid, and the frozen observation specs (§6.3, [AUTHOR A30]).
- A value resolved by external source research (V57) enters only through one of these addenda, before the data it governs, after Claude Code has spot-checked its citation.

### 9.5 Deviations
Any departure from this protocol is a dated deviation note in the phase report: what changed, why, which result prompted it, the author's approval, and the outcome under the original rule next to the new one. **Zone moves** (V56) follow [AUTHOR A34]: a move applies to every arm, uses fresh seeds from [AUTHOR A16c], re-runs P1 and, if P2 has started, P2 (P0 is not re-run, because B0 and B1 carry no commands), and has its own cost row (§10.2). After a move, the band and the regime set are re-fixed by the unchanged band rule in a dated addendum before any validation-seed evaluation of a learning arm, and they are frozen with the zones before the confirmatory run (V56).

### 9.6 Records
- **Every run goes into the ledger**, including FAIL, invalid, OPS, crashed and abandoned ones, with the T3c fields. Health columns are filled by job code from the run summaries, never by hand.
- **SUMO crash:** the same seed is re-run once; a second crash keeps the run failed and reported (`interfaces.md` §9). **Hung worker:** killed, marked OPS and re-run once (§2.7). **Collapse:** killed at the CPU-time cap and marked failed for its arm.
- Raw runs go under `/home/catalin/work/phd/` (ext4), in a v5.B.1-only run root (not the archive's); the repo holds summaries only (< 5 MB per file).
- One report per phase, with the verdict, the values against each criterion, the burned seeds, k, and the deviations.

---

## 10 CPU budget and schedule

### 10.1 Per-episode cost (ASSUMPTION, to be measured in P0-S and P0-C)
- **Measured anchor:** archive CORR2 G-scan runs (3 lanes, 9.5 km, EIDM, 0.2 s): median 112 s wall per run (range 87–161 s) for about 6,674 vehicles and 5,475 s simulated, under concurrent load; 360 runs took 1,937 s of batch wall time, i.e. about 21 effective parallel runs on 32 workers (local count over `/home/catalin/work/phd/vsl_lab_runs/t4/gscan_1791047971`; that batch never ran more than 24 jobs at once and recorded 0 guard pauses).
- **F3Z scaling:** at λ = 1.0, about 13,200 vehicles over up to 11,700 s simulated (§2.4). With assumed mean trip times, this is about 2.5–3 times the anchor's vehicle-seconds (my arithmetic), i.e. about 280–330 s, plus the ground-truth reads (toy: 1.34 µs per vehicle-step for six getters, unloaded; about 32 million vehicle-steps → about 45 s) and the Python work at each boundary. **Planning value: 350 s per episode at λ = 1.0 (range 250–500 s); throughput about 200 episodes per hour** at 21 effective parallel runs. Lower levels are cheaper, plateau runs cost about 0.7 times, and 0.1-s runs about twice as much, so the totals below are conservative for the sweep.

### 10.2 Budget per phase (episodes; 0.1-s runs counted twice)

| Phase | Episodes (≈) | Wall at 200 per hour | Code needed first |
|---|---|---|---|
| P0-B | micro-scenarios only (incl. ACC pre-screen, P0-G4) | < 0.5 h | plant, inflow, health, metrics, stats, seeds, ops |
| P0-S | 12 | < 0.1 h | — |
| P0-C | 210 (+ 16 to 40 if ladders extend) | ≈ 1.1 h | CAV vType (B1) |
| P0-G1 | 30 (+ 10) | ≈ 0.1 h | — |
| P0-G2, G3 | 120 | ≈ 0.6 h | — |
| P0-G5 | 80 at 0.1 s ≈ 160 | ≈ 0.8 h | — |
| P1 | 420 + 22 replicates | ≈ 2.2 h | exec, v2x, R4, command log |
| P2 stage 1 (L = 8) | 4,672 | ≈ 23 h | R1–R3, O, tuning code (after Addendum C) |
| P2 stage 2 | 3,360–4,320 | ≈ 17–22 h | — |
| P2 held-out | 1,280 (1,920) | ≈ 6.4 h (9.6 h) | — |
| **Total, unconditional** | **≈ 10,300–11,900** | **≈ 51–59 h** | ≈ 1,000–1,160 core-hours at 350 s |
| Conditional | G1 extension 10; C1/C2 extensions 16–40; edge level ≈ 584 + ≤ 540 + held-out ≈ 160–240 (≈ 6–7 h); parameter refinement ≈ 1,920 (≈ 10 h); per plant variant ≈ 520 eq (C1–C8 and P0) + a P1 repeat (≈ 5 h); per ACC re-check ≈ 280 eq (G3 and G5 on fresh seeds, ≈ 1.4 h); a move to 0.1 s ≈ doubles P1 and P2 (≈ +50 h); per zone move ≈ 2 h for P1 plus ≈ 46–55 h for P2 if P2 has started | | |

At the range ends (250–500 s per episode) the unconditional total is about 37–85 h (my arithmetic). If Addendum D's re-stated projection for P2 exceeds 72 h, the author is asked before P2 (accept, or an addendum reducing the candidate counts, written before any P2 data).

### 10.3 Where each KILL path stops (cumulative batch time, planning value)
Calibration futility ≈ 1.2 h; P0-G1 FAIL ≈ 1.3 h; P0-G2/G3/G5 FAIL ≈ 2.5 h; P1 actuator FAIL ≈ 5 h; KILL-1 ≈ 28 h, or ≈ 31–41 h when an edge level or the parameter refinement is triggered; KILL-2 ≈ 45–50 h, up to ≈ 65 h with both additions (saves the held-out stage, ≈ 6–10 h). **KILL-1's saving of about 23–31 h is real only when the calibrated t is clearly positive** (under the normal approximation, σ_plan,1 ≲ 0.07); when t is near or below 0, KILL-1 rarely fires and KILL-2 is the realistic early KILL. Raising n₁ from 8 to 12 would lift t to about 0.016 at σ = 0.10 for about +2,336 episodes (≈ +12 h; my arithmetic); it is not adopted, and the trade-off is recorded in [AUTHOR A15].

### 10.4 Operating rules (CLAUDE.md, binding)
32 workers on all hardware threads, ≤ 100 processes; the CPU guard ported and unit-tested before the first batch (launch only below 90 %; after 2 min above 90 % pause the newest job, then one more every 30 s; resume one per 30 s after 30 s at ≤ 87 %), with every pause logged; job order shuffled across arms within each batch; a resource check before every batch; no overlap with v6 runs (v6 sessions confirmed idle, else CPU load < 15 %); every batch in its own `systemd-run --user` unit, resumable from the ledger; background jobs only, logs tailed at most every 10 min; package temperature logged per batch; fans never driven by batch code; per-run CPU-time cap (C8) and hang detection (§2.7). **Power traces (V10)** are written only for a pre-declared subset: the golden run, the T3a replicates, the P0-G4 tests, the P0-G3 runs on seed 7,400,040, and in the P2 held-out stage the lowest seed per (level, arm) [AUTHOR A35]. **Disk (ASSUMPTION):** per-vehicle summaries (including per-edge traversal times for the truck sensitivity rows) of about 0.5–2 MB per run; 10-s probe and section series only for P0, P1 and held-out runs (about 5 MB each); power traces about 0.2 GB per traced run (float32, compressed), about 12 GB for about 60 traced runs; about 25–35 GB in all, free space checked before each batch.

### 10.5 Schedule (order and gates; effort and ultracode per the CLAUDE.md phase table)

| Step | Content | Gate | Effort, ultracode |
|---|---|---|---|
| S0 | Author review of this protocol; every [AUTHOR] item answered (done 2026-10-13, V58–V65); Addendum B; protocol approved in a commit | approval | Extra High, on |
| S1 | Port `ops`, plant, inflow, runner, metrics, stats, seed guard; P0-B green (incl. ACC pre-screen, P0-G4) | all P0-B green | High, off |
| S2 | P0-S → Addendum A → P0-C → calibration report → Addendum D | futility stops not triggered | High, off |
| S3 | P0-G1, then P0-G2, G3, G5 → P0 report | §4.10 | Extra High, on (interpreting a gate) |
| S4 | Addendum C (content, before seed 060); `exec`, `v2x`, R4; P1-B green → P1 → P1 report (incl. the calibrated t) | §5 verdict | High, off to build; Extra High, on to interpret |
| S5 | R1–R3, O, tuning machinery, ceiling; P2-B green | checkpoint "plant and all opponents done" | High, on |
| S6 | Stage 1 → §6.10 additions → KILL-1 → stage 2 → KILL-2 → n_eval → held-out → band → P2 report | §6.8–6.9 | High, off to run; Extra High, on to interpret |

The critical path is engineering (S1, S4, S5), not CPU. R1 and R4 stage-1 runs can overlap the building of R2 and R3 (§6.3).

---

## 11 [AUTHOR] decisions needed (each before any data it governs)

**All items were answered on 2026-10-13 (V58–V65); the last column records each answer.** Items written for the v0 layout (A6, A10, A13, A26, A30) are re-read for V64 there. Every item was due **before seed 7,400,000**, except A9 and A30 (before seed 7,400,060, before any commanding arm runs on a project seed). None needs data. A deadline after the data an item governs would let the choice be made after seeing the contrast it decides (principle 1); the synthesis had such deadlines for A1–A8, A11, A14, A15, A18 and A21–A23, which this revision moves (Appendix C, GH-1, GH-2); A10, A17 and A20 are moved to seed 000 as well, for one simple gate.

| Id | Decision | Options | Cost / consequence | Recommendation | Needed before | Author answer (2026-10-13) |
|---|---|---|---|---|---|---|
| A1 | What a P0 FAIL means | (i) KILL F3Z at the first FAIL; (ii) ≤ 2 pre-registered plant-model variants and ≤ 6 plant settings in all (§9.2), each a full calibration + P0 on fresh seeds, then KILL; (iii) continue as a "SUMO plant, realism FAIL disclosed" claim | (i) cheapest, but the thesis then needs another plant; (ii) ≈ 5 h CPU per variant and a new seed range; (iii) weak for a thesis and a hidden-variant risk | **(ii), then KILL; never (iii)** for the headline | seed 000 | **(ii), then KILL; never (iii)** (V59: at most 2 variants and 6 setting changes in all, each on fresh seeds, then P0 KILL) |
| A2 | Drop band | (a) [0.82, 0.97]; (b) lower bound 0.79 when the median v_cong < 10 km/h (the Yuan et al. 2015 relation against their pre-queue capacity of 6,300 veh/h; 0.73 against their maximum observed 6,840 veh/h); (c) upper bound moved towards the real US-169 SB ρ ≈ 0.98 (archive D3.1 waived ≥ 3 % there; I-394 ≈ 0.968) | (a) strictest, highest FAIL risk; a plant with a high queue speed can show ρ ≈ 1 for a realistic reason (§4.4); (b) one more estimator, admits deep-queue drops, and its value depends on the capacity reference; (c) admits a plant with almost no drop, which removes the mechanism the controllers target | **(a)**, with v_cong and (b) reported as rows only | seed 000 | (a) (V65) |
| A3 | Queue-discharge upper bound | 2,300 or 2,400 veh/h/lane | 2,400 admits flows above the highest Dutch observation (2,280) and the HCM-derived ≈ 2,000 | **2,300** | seed 000 | 2,300 veh/h/lane (V65) |
| A4 | Calibration futility stops F1–F5 | yes / no | yes saves up to 60 check seeds and ≈ 1 h; the verdict then rests on throw-away seeds, but only ever for a STOP. F3 is restricted to levels ≤ λ_c + 0.1, so over-saturation alone cannot stop P0; F5 stops a plant that breaks down below 40 % of the nominal inflow | **yes** | seed 000 | yes (V65) |
| A5 | Role of the headroom ceiling | (a) report-only; (b) binding: levels with G_max < 5 % not tuned, KILL if all are below 5 % (kill draft); (c) not computed | (b) saves up to ≈ 23 h when every level is below 5 %, but the ceiling is not a proven bound (pulse-and-glide; throughput above anything observed) and its false-KILL risk is unquantified; (c) saves one small module | **(a)** | seed 000 | (a) report-only (V65) |
| A6 | Meaning of "the realistic level" (D5.8; CLAUDE.md early KILL) under V31/V45 | (a) any admissible band level; λ = 1.0 always reported; no band level called "realistic" unless it is λ = 1.0; (b) λ = 1.0 must be in the band; (c) a **designated level ℓ*** fixed by a rule written now and applied at GO, before any learner data: λ = 1.0 if it is in the band, else the band level closest to 1.0 (ties to the higher); the later D5.8 "≥ 10 % vs no control" is tested at ℓ* only | (a) leaves the later D5.8 claim with an open multiplicity question across band levels; (b) is close to a guaranteed KILL: on paper λ = 1.0 is 1.32–1.65 times the first bottleneck's capacity (BN-LD under V64, BN-M2 in v0) and likely drain-capped (§2.1); (c) no multiplicity cost and no data-dependent choice, but ℓ* may lie well below the nominal inflow, which the thesis must say | **(c)**, called "the designated level", with the A26 statement on λ = 1.0 | seed 000 | (c), "the designated level" ℓ* (V65). Re-read for V64: λ = 1.0 is still 1.32–1.65 times the first bottleneck's lane-count capacity, now BN-LD; unchanged |
| A7 | How the band must beat B1 (V44) | (a) the CI upper bound of r vs B1 < 0 at α/m (V44's operative clause, as in the synthesis); (b) r vs B1 ≤ −5 % with its CI at α/m; (c) control share (C_B1 − C_A) / (C_B0 − C_A) ≥ 0.5 as a point estimate, CI reported; (d) no B1 requirement. Under (a)–(c) the decomposition rows and the wording rule of §6.8 are mandatory | (a) a level can enter with, e.g., 9 % from automation and 1 % from control, which V44's rationale ("control, not automation, must carry the gain") does not want; the decomposition discloses it; (b), (c) close that route but go beyond the literal V44/V45 text and may shrink the band; (d) contradicts V44 | **(a)** with the decomposition and the wording rule; **(b)** if the author reads V44's rationale as binding | seed 000 | **At least 5 % better than B1** (V61), i.e. option (b): band (d) = r vs B1 ≤ −5 % with its CI upper bound < 0 at α/m (§6.8). Decomposition rows and the wording rule kept |
| A8 | Delay reference index | (a) r(route, car/truck), measured in B0 and identical in every arm (C5 on 8 seeds, minimum count and fallback); (b) r(route, driver class); (c) each vehicle's own B0 trip time | (b) biases C across arms; (c) needs a matched B0 run for every arm and seed | **(a)**; amend `interfaces.md` §5.2 | seed 000 | (a) (V65); `interfaces.md` §5.2 amended in v1 |
| A9 | Hold mechanism and entry ramp | V36 (`slowDown`, then `setSpeed`) is decided; `interfaces.md` §3 still describes re-issued `slowDown` and does not say how the rounded entry target is reached | none: both holds are exact in the toy; T0a tests V36 and the entry ramp; a `setSpeed` entry step would manufacture a hard brake (§2.5) | **amend `interfaces.md` §3 to V36**, with the entry target reached by `slowDown(target, 2.0)` from the current speed and the first post-entry ramp ≤ 1.04 m/s² | seed 060 | amend `interfaces.md` §3 as recommended (V65); done in v1 |
| A10 | Release at zone exit | (a) `setSpeed(−1)` at the first boundary after exit, as decided (V36; `interfaces.md` §1, §3, §9); (b) a ramp of +5 km/h per 2 s with `slowDown` to the desired speed, then release | (a) the ACC accelerates at its own 2.6 m/s² towards its desired speed: the model's own behaviour, the same in every commanding arm and charged to the arms in energy; (b) amends a decided item and `interfaces.md` §1/§3/§9 (commands outside zones), needs a precedence rule at Z3 entry (the Z2 → Z3 gap was 250 m in v0 and is 500 m under V64, while a release ramp from 50 to 100 km/h takes about 417 m; my arithmetic), and shapes traffic inside BN-M1 and BN-M2 in every commanding arm | **(a)** (changed from the synthesis, which recommended (b)) | seed 000 | (a) (V65); `interfaces.md` §3 states it in v1 |
| A11 | ACC base model (V36 "calibrated") and its ladder | the ladder A0 → A1 → A2 → A3 of §2.6 C4 with the deterministic pre-screen (platoon and approach tests), the calibration margins (select at R ≤ 0.85; stay on the ladder at R ≤ 1.25; F4 otherwise) and G3(b) on a point estimate plus an upper bound ≤ 1.2; CACC excluded; "calibrated" read as this pre-registered discrete selection (principle 10). Alternatives: (i) calibrate the ACC to a stated empirical target (e.g. a measured ACC time-headway or deceleration distribution; no source read yet [VERIFY]); (ii) test A3 first | A0 is expected to fail the pre-screen (toy approach braking −6.06 m/s² with no cut-in) and (b); A3 departs from "SUMO ACC" (`system_context.md` §3) and needs explicit consent; the margins make the fresh-seed check less of a coin flip but raise the chance of exhausting the ladder (F4 → P0 KILL or a new CAV protocol); (i) needs a source and a fitting rule, i.e. a new design step; if F4 fires: P0 KILL, or a new CAV base model under a new protocol | **approve the ladder including A3, the pre-screen, the margins and the CI-based G3(b)** | seed 000 | the ladder **including A3** (V60), with the pre-screen, the margins and the CI-based G3(b) (V65) |
| A12 | Inflow family | as §2.4: q₀ = 0.5 q̂, t_pk = 5,160 s, q₁ = 0.7 q̂ (mapped from the fitted curve), λ scaling all streams, inflow stopping at the window end, per-episode noise off in P0–P2, the plateau probe for G1. Alternatives: noise on (the `interfaces.md` §4 proposal); inflow continuing at q₁ during the drain; end levels 0.5 or 0.6 | noise on blurs the level and inflates the paired variance; inflow during the drain adds about 14 % vehicles and departs from the V49 reading; 0.5/0.6 have no anchor in the fitted curve. Disclosed: mapping 06:00–10:00 onto the 2.5-h window compresses the rise and fall by a factor of 1.6 (240 / 150 min; my arithmetic), which changes queue sizes at a given λ | **approve as proposed**, with the compression disclosed; noise later as a pre-registered robustness row | seed 000 | approved as proposed (V65) |
| A13 | Small plant items, incl. the CAV desired speed | renormalise the V42 shares (HDV cars 60.0 % ICE; amend V42's "about 59 %"); X1/X2 shares 10 %; truck length 12 m (archive) or 16.5 m (commonly given as the EU maximum for an articulated vehicle [VERIFY]); on-ramp ids OR1/OR2. **CAV desired speed** (§1.1 item 4): (i) CAVs keep their manifest speed factor outside zones, 100 km/h caps only zone targets; (ii) 100 km/h, with the delay guard's automation part attributed to B1 (changes V37's reference, NC); (iii) 100 km/h, with the handicap accepted and stated | CAV speed under (ii)/(iii): the 44.7 % of CAVs whose B0 speed factor exceeds 1.0 drive slower than in B0, so B1 and every commanding arm carry a built-in delay increase vs B0 (upper estimate about 12 veh·h per episode at λ = 1.0: 3,285 cohort CAVs × 0.447 × about 30 s; my arithmetic) and a built-in energy saving; at sub-critical levels where B0's delay is near 0, the delay guard (e) then fails commanding arms by construction; P0-R2 measures the effect before seed 100. (i) has automated cars exceed the 100 km/h network maximum (V30), which is implausible. Truck length: a longer truck lowers capacity and discharge, which raises the G1 FAIL risk against the floor (A25). The others are bookkeeping | **approve all; CAV desired speed (iii)**, with B1 − B0 reported next to (b) and (e) at every level; **truck length 16.5 m [VERIFY]** | seed 000 | approve all; CAV desired speed (iii); truck length 16.5 m [VERIFY] (V65). Re-read for V64: unaffected (routes unchanged). V42's "about 59 %" in `decisions.md` is not amended here |
| A14 | Hard-braking tolerance y (V25), its statistic, and the guard vs B0 | y ∈ {0 %, 10 %, 25 %}; the pooled rate ratio with a 0.5 continuity correction (§8.5), or the median of paired differences; the conditional guard (f′) vs the same vehicles in B0, activated if P0-G3's R₃ > 1 + y | 0 % is very strict for rare events; 25 % tolerates a quarter more hard brakes; the median degenerates with zero-event seeds. Without (f′), ACC artefact braking between −3 and −4.5 m/s² in B1 would loosen (f), and merely holding CAVs could look like a braking win | **y = 10 %, continuity-corrected pooled ratio, (f′) as pre-registered** | seed 000 | y = 10 %, continuity-corrected pooled ratio, (f′) as pre-registered (V65) |
| A15 | Tuning budget | 20 candidates per rule (default + 19 LHS), R4 11, stage 1 n₁ = 8, stage 2 n = 30 with 2 + 2 finalists per rule, plus the parameter-adequacy refinement (§6.10); or 24 per rule (≈ +3 h); or 16 (≈ −3 h); or max(20, 10 × d) per rule with equal budget across R1–R3 (cost depends on the dimensions d of Addendum C); stage 1 with n₁ = 12 (≈ +12 h; t ≈ 0.016 instead of ≈ 0 at σ = 0.10) | equal budget across R1–R3 is the fairness rule; a weakly tuned rule risks a false KILL; the refinement costs ≈ 10 h when triggered | **20 per rule + the refinement; n₁ = 8** | seed 000 | 20 per rule + the refinement; n₁ = 8 (V65) |
| A16 | Seeds | (a) unit and micro-scenario tests on non-project seeds 1–999; (b) the roles of §7 inside 010–099 and 100–299 (selection 100–137, held-out 200–259); (c) a new range 7,401,000–7,401,999 for re-rounds (plant variants; insertion, ACC or step changes; zone moves; §9.3 re-checks; G3 flag deviations); (d) calibration seeds 002–009 reusable for re-calibration after a plant variant or an insertion, step or ACC change | without (c), any re-round stops the protocol until seeds are approved; without (d), a re-calibration has no seeds | **approve (a)–(d)** | seed 000 | (a)–(d) approved: (c) 7,401,000–7,401,999 by V62; (a), (b), (d) by V65 |
| A17 | Consequence of a T1b FAIL | (a) proceed to P2 (the first binding KILL is KILL-1); (b) KILL on the untuned R4 | (a) ≈ 23 h more CPU (stage 1) to reach KILL-1; (b) goes beyond the CLAUDE.md early-KILL definition (a tuned proven controller or the oracle) | **(a)**, with the expected outcome written down first | seed 000 | (a) (V65) |
| A18 | VoT freeze and sensitivity rows | Addendum B before seed 000: VoT_car (commuting €8.90 × 1.23, `interfaces.md` §5.4) and VoT_truck (work VTT × 1.03, V54) uplifted to 2026 € step by step (TII growth, CSO price index; values [VERIFY]); the V21 price date; the V21 lower-price row; truck fuel net of VAT as a report-only row | blocks seed 000 until done (no data needed); the PAG categories are already fixed, only the uplift is open | **required as proposed** | seed 000 | required as proposed (V65) |
| A19 | Invalid-run scope and operations failures | V6 only, or V6 plus the §2.7 FAIL rows; plant collapse (CPU-time cap, arm FAIL) kept apart from operations failures (hang, re-run once) | V6 alone would let a run with a SUMO error, a conservation breach or a stranded vehicle count as valid; a wall-time cap would score CPU-guard pauses and machine contention as controller failures | **V6 + §2.7, with the collapse/OPS split**, recorded as a decision | seed 000 | V6 + §2.7, with the collapse/OPS split (V65) |
| A20 | P0-G5: test form and FAIL consequence | form: (i) the paired point estimate within ±5 %, CI reported (§8.6); (ii) two one-sided tests: the 90 % CI inside ±5 %, one pre-registered extension on fresh seeds if inconclusive, then FAIL. Consequence: (a) move to 0.1 s: C1–C8 re-run at 0.1 s on 002–009, a new golden hash, all of P0 on fresh seeds, no further step check at 0.1 s (disclosed); (b) keep 0.2 s and disclose | (ii) is stricter: with a true step effect of about 3 % (archive IDM 392 vs 403 s) and an unmeasured paired SD, it may FAIL a plant that is converged enough; (i) passes a 3 % effect and lets a borderline one through with a FLAG. (a) about doubles P1 and P2 CPU (≈ +50 h); (b) conclusions may hinge on the step | **form (i); consequence (a)** | seed 000 | form (i); consequence (a) (V65) |
| A21 | VSL arms in the band rule | include I1/I2, or exclude | I1/I2 are non-learning but not our actuator (V15); their compliance values are open (V32) | **exclude**; run them later as references inside the band | seed 000 | exclude (V65) |
| A22 | Native-rate rule versions | (a) not in P0–P2: a KILL stays a KILL, and any later native-rate check is a new protocol on fresh seeds; (b) a report-only row on the held-out seeds at every level, whatever the outcome; (c) only on the KILL path (feasible draft) | (b) ≈ 960–1,440 episodes and a new `exec` variant; (c) an asymmetric forking path, against `system_context.md` §4 ("a sensitivity row only") | **(a)** | seed 000 | (a) (V65) |
| A23 | Drain-limited and boundary-limited levels | (a) eligible, with the pooled-total censoring and origin-queue guards and sign counts of §6.8(g); (b) excluded from the band (rigor draft); (c) as (a), with origin-queue idle energy imputed into C for the band (idle rate from P0-G4) | (b) probably removes λ ≥ 1.0 from the band, although B0's censoring already understates B0 cost; (c) changes the headline definition (V29) | **(a)**, with the imputation rows reported (§6.12) and levels whose membership changes under them labelled | seed 000 | (a) (V65) |
| A24 | Thresholds without a published source | collisions ≤ 2 per check; departDelay 1 s / 10 s / 60 s; lane share ≥ 20 %; entry onsets ≤ 5 %; 70 km/h recovery and active-bottleneck speed; wave correlation 0.3; desired-speed tolerances; the 20 % B1 flag; the extreme-deceleration flag; the energy bands and the road-load values of the G4 floor; the 5 % T0 effect and the 3 % throughput effect; the 90 % futility margin of F2; the 10 % Q_cap margin; the stop-and-go thresholds 20 / 50 km/h (the `interfaces.md` §5.6 proposal; they bracket the 60 km/h congestion boundary of §3.2 with hysteresis); the ≥ 20-vehicle r cell and its ±10 % sanity FLAG; the C4 margins 0.85 / 1.25; the G3 upper bound 1.2; the CPU-time caps (4 × the calibration median; a provisional 8 × the smoke median during P0-C) and the 10-min hang rule; the approach-test criterion; the metronome CV 0.2; k ≤ 6; the delay-guard floor of 5 % of R_tot; the origin-queue factor 1.02; the 0.5 continuity correction; the P60 − P40 ≥ 0.10 rule; the 25 % outer range and the 10 % edge proximity of the refinement; the per-edge averaging of the truck sensitivity rows. Option: split the zero-tolerance realism gates into code-integrity FAILs (zero tolerance) and traffic artefacts gated on rates with exact bounds | wrong values either pass artefacts or FAIL a usable plant; the split would loosen the brief's "without artefacts" | **approve as labelled assumptions; no split** | seed 000 | approved as labelled assumptions; no split (V65) |
| A25 | Discharge floor (G1(c), T1a, F2) | (a) 1,600 veh/h/lane (Dutch and HCM anchors; archive ZM3 at 1,528 stayed FAIL); (b) an Irish-derived floor: 1,440 (1,600 × 0.90) or 1,405 (TII 2012 Table 5.2, "Lower 85 Percentile" of lane 1); these are breakdown flows, not discharge; (c) gate the drop on ρ only, with a gross-artefact floor (e.g. 1,200; the archive's BN4 discharged 900) | (a) the most likely P0 FAIL (§0.4); an M50-like plant may FAIL it: the TII 2012 M50 three-lane sites average 1,600–1,733 veh/h per lane (my arithmetic over Table 5.2), and queue discharge lies below pre-breakdown flow by the drop; (b) would pass archive-like plants (ZM3's 1,528 passes 1,440) and needs a stated derivation; (c) tests no discharge realism beyond gross artefacts. F2 is 90 % of the chosen floor | **(a)**, with a reported row "would pass under (b)" | seed 000 | (a) 1,600 veh/h/lane (V65) |
| A26 | Geometry–inflow consistency (V2, B13), and the response to F5 | (a) keep F3Z and the B13 peaks; the grid is anchored on λ_c; λ = 1.0 is reported as over capacity on paper; ℓ* by A6(c); (b) define the realistic level by the real site's peak-to-capacity ratio instead of B13's absolute flows (needs a sourced ratio; none read [VERIFY]); (c) reconcile geometry and inflow before any run: three lanes after merge 2, or a lower OR2 peak (a V2/B13 decision) | (a) honest and cheap, but the nominal level is not an operating point of this geometry; (b) needs data we do not have; (c) changes the plant before seed 000 (no data cost), moves the bottleneck structure the zones were placed for (V56), and re-opens B13 | **(a)** now; (c) only if the author wants λ = 1.0 to be an operating point | seed 000 | **Superseded by V58/V64**: the road was redesigned before any data (lane drop at 6,000 m, the end of Z3). The grid stays anchored on the measured critical level λ_c; λ = 1.0 stays a reported row; after F5, a further redesign needs a new protocol |
| A27 | Burden of proof for the band guards (e), (f), (f′), (g) | (a) non-inferiority at α/m (the synthesis): the Bonferroni upper bound must lie within the margin; (b) non-inferiority at one-sided 95 %, unadjusted, the error accounting disclosed; (c) point estimate within the margin, Bonferroni interval reported (as in P0 and the stage-1 screen); (d) harm must be shown: FAIL only if the Bonferroni interval lies entirely beyond the margin | pass probability at n = 40 for an arm with a true Δ_D = 0, at σ_D = 0.05 / 0.10 (normal approximation, my arithmetic): (a) 0.17 / 0.026, (b) 0.65 / 0.26, (c) 0.98 / 0.84, (d) ≈ 1 / ≈ 1; for an arm with a true +5 % (a real violation): (a) 0.000 / 0.000, (b) 0.000 / 0.001, (c) 0.001 / 0.065, (d) 0.47 / 0.93. (a) structurally excludes gains carried by energy with neutral delay (against V10, V16) and, for (f) at a true ratio of 1, needs about 1,920 events per arm; (d) barely protects commuters | **(c)**: V37 states a tolerance, not a burden of proof; the band is a screen for where learners are trained, and the D5.8 evaluation later applies its own "not significantly worse" guard on fresh seeds | seed 000 | (c) (V65) |
| A28 | Braking event definitions (G3 and h) | severe event for G3: (i) strictly beyond the shared 4.5 m/s² decel cap (a < −4.51 m/s²), at-cap stretches reported; (ii) a physical threshold equal to no decel in the manifest, e.g. a < −4.0 m/s²; (iii) per vType, beyond its own cap (a < −decel_vType − 0.01 m/s²). Speed condition for G3: (α) onset speed ≥ 10 m/s (B14), all speeds reported; (β) all speeds. For h (V25, band (f)): (α′) all speeds as decided in V36, the at-speed split reported; (β′) at speed only (B14) | the synthesis's "a ≤ −4.5" counted 9–26 % of the at-cap steps through floating-point rounding (toy knife.py), and A2 (decel 3.5) could pass by re-parametrisation alone; (ii) is still exposed to that (A2's at-cap steps lie below 4.0, the HDVs' above); (iii) is stricter for A2. (β) lets zipper-creep braking at about 0 m/s push R towards 1 and hide CAV artefacts; (β′) departs from a decided item | **(i) with (α) for G3; (α′) for h** | seed 000 | (i) with (α) for G3; (α′) for h (V65) |
| A29 | HDV braking (revisits V11) | (a) report-only HDV hard-brake (< −3 m/s²) and severe rates per HDV-km for every arm and level, with a FLAG when A/B1 > 1 + y at a band level; (b) (a) plus a band guard "HDV rate ratio A/B1 ≤ 1 + y"; (c) none (V11 literally: not measured) | V11's reason concerns what the system can observe, not what metrics may measure (`system_context.md` §2, the honesty line); (b) adds one intersection component and lowers the pass probability; (c) leaves "move harm onto HDVs" open (§3.4) | **(a)** | seed 000 | (a) (V65) |
| A30 | Observation specs, and what zone-spec arms know about the bottleneck downstream of Z3 (BN-M2 in v0; BN-LD under V64) | freeze `local` and `zone` in Addendum C. Z3's "next downstream zone": (a) a defined fallback value with n = 0 and a flag (a disclosed blind spot at the first bottleneck); (b) an extra V2X probe-summary unit downstream of Z3, on [6,000, 7,000) m under V64 ([5,750, 6,750) m in v0), with no commands there (amends `interfaces.md` §6/§7); (c) move Z3 (V56) | (a) R2's planner and R3, which harmonise upstream of merges, see nothing at the expected first bottleneck: a weak-baseline risk (it applies equally to L2); (b) a few lines in `v2x`, the same information for every zone-spec arm; (c) re-opens the zone layout | **(b)** | seed 060 | (b) (V65), re-read for V64: the unit lies on [6,000, 7,000) m, just downstream of the lane drop (BN-LD) at Z3's downstream end; fixed in Addendum C before seed 7,400,060 |
| A31 | Non-learning adaptive scheduler and H | (a) build one: F's rule with parameters switched by a V2X-measured state (e.g. zone mean speed), thresholds tuned on 100–137, run as a report-only arm in stage 2 and on the held-out seeds at every tuned level; (b) drop it in P2, disclosed as a deviation from CLAUDE.md (Method), and label the reported quantity "G, i.e. H without the adaptive scheduler"; the D5.8 protocol decides before any learner data | (a) new code and ≈ 320–480 held-out episodes plus stage-2 runs (≈ 3–4 h); (b) the band is unaffected (the scheduler would be report-only either way), but a learner's later "adaptation" advantage might be one that a simple within-episode scheduler also gets, and H would not show it | **(b)** | seed 000 | (b): scheduler dropped from P2, disclosed (V63) |
| A32 | Tuning parity for the D5.8 comparator | adopt the binding clause of §12: P2 tuning serves the band and the KILLs only; before any learner comparison, R1–R4 are re-tuned on the frozen band levels, on tuning seeds not used in P2, with a budget at least equal to the learners' total tuning budget, counted in (a) simulated episodes, (b) simulated vehicle-hours, or (c) CPU-hours; LHS size ≥ max(20, 10 × d); P2's F and O(ℓ) never serve as the D5.8 comparator without it | without it, P2's 20-candidate tuning could become the D5.8 baseline (CLAUDE.md: no weak baselines); 260–299 may not hold enough seeds, so a new range may be needed; cost unknown until the learner budget is fixed | **adopt, unit (a)** | seed 000 | adopt, unit (a) (V65) |
| A33 | BEV and PHEV (El) energy under acceleration | (a) keep HBEFA4 PC_BEV, with the G4 acceleration floor report-only for BEV and PHEV (El) and the known under-charge disclosed; (b) (a) plus a per-step road-load BEV energy model in our code (as for trucks) as a sensitivity row, parameters in Addendum B from a named source [VERIFY]; (c) switch BEVs to SUMO's Energy model (EVM) as the main model (the alternative recorded in literature_v0.md, with its reported highway error) | (a) BEV transients are mis-priced, in an unknown direction for arms that add or remove accelerations; (b) cheap (re-scoring); (c) changes V10's model choice and needs new G4 checks | **(b)** | seed 000 | (b) (V65) |
| A34 | Actuator FAIL (T0b/T0c) and zone moves (V56) | on a T0b/T0c FAIL: (a) KILL of the CAV-only actuator on F3Z (archive testbed precedent D5.14); (b) one disclosed zone move, chosen by the author, re-run on fresh seeds (A16c), then KILL if T0b or T0c FAILs again. Any zone move (also after GO, V56): applies to every arm, uses fresh seeds from A16c, re-runs P1 and, if started, P2, has its own cost row, and the band and regime set are re-fixed by the unchanged band rule in a dated addendum before any validation-seed evaluation of a learning arm | (a) cheapest; may KILL a plant whose zones were placed before its bottleneck structure was known (§2.1); (b) ≈ 2 h for P1 (+ ≈ 46–55 h if P2 is re-run); the new zones are chosen after seeing a FAIL, but only a fresh-seed re-run can PASS | **(b)** | seed 000 | (b) (V65) |
| A35 | Bookkeeping decisions | (a) close V18 with the §3 definitions (cohort, r, the cut-off at 11,700 s, the window, stop-and-go 20/50 km/h); (b) answer V22's open item: the US-169 shape on an M50-inspired network is a disclosed mismatch, not a calibration; (c) V10 power traces for the pre-declared subset of §10.4 | (c) costs about 12 GB of disk; without (a), V18 stays formally pending while the protocol uses its definitions | **approve (a)–(c)** | seed 000 | approve (a)–(c) (V65; V18 and V22 updates in `decisions.md`) |

---

## 12 What this protocol does not cover, and what it binds for later

### 12.1 Not covered
- Learning arms L1 and L2: the PettingZoo environment, the reward (open, V52), the trainer ladder (ADR-001 §4; its steps that use no F3Z and no project seed may proceed in parallel), the training budget and validation-only checkpoint choice. All after a GO.
- The D5.8 evaluation itself: the best tuned rule chosen on validation seeds (300–499), the test seeds (500–699), the confirmatory run (700–999), and the pre-registration of regimes, the adaptation gain and robustness rows (taken from the P2 map, evaluated on fresh seeds). P2 only fixes the band and the designated level ℓ*.
- The VSL comparators I1/I2 (V32, V39, V55) and their compliance values.
- Regime axes other than the inflow level: CAV share, ramp-to-mainline ratio, per-episode inflow noise, communication delay and loss, adaptive drivers, weather and incidents.
- Native-rate comparator rows ([AUTHOR A22]). If the band is empty, whether the 2-s quantised interface rather than the plant limited the rules (literature_v0.md verifier weakness 4) can only be examined in a new protocol on fresh seeds; it never changes the P2 verdict.
- A second plant variant for band robustness (archive D4.7, ARCH day_pattern_decisions_v0.md:59).
- Ramp meters (dropped by V15) and MPC (dropped and disclosed).
- Cross-machine determinism.
- Charging losses (V53), cold start, HVAC and auxiliary loads; a MOVES or VECTO cross-check; the validity of the HBEFA4 acceleration term beyond the G4 floor ([AUTHOR A33]).
- Validation against Irish data: no measured capacity drop, wave speed or queue discharge was found for any Irish motorway (TII open per-vehicle files returned 403 for every date tested from 2021-06 to 2026-10; irish_parameters_v0.md §4). The realism bands are international, apart from the 2012 M50 breakdown flows; Irish-specific realism is [VERIFY].

### 12.2 Binding commitments for the learning-phase protocol (fixed now, so that they cannot be chosen after P2 results)
- **Tuning parity ([AUTHOR A32]).** P2's tuning serves the band and the KILL decisions only. Before any learner comparison under D5.8, R1–R4 are re-tuned on the frozen band levels, on tuning seeds not used in P2 (260–299, or a newly approved range), with a budget at least equal to the learners' total tuning budget counted in the unit chosen in A32, and with an LHS of at least max(20, 10 × d) points per rule (d from Addendum C). P2's F and O(ℓ) are never used as "the best tuned proven controller" without this re-tuning.
- **Effect sizes.** Seeds 200–259 decide band membership only. Every effect size quoted for a band level or regime is re-estimated on fresh seeds (300+).
- **Designated level.** The D5.8 "≥ 10 % vs no control at the realistic level" is tested at ℓ* only ([AUTHOR A6]).
- **Adaptive scheduler.** Whether a non-learning adaptive scheduler enters "best non-learning" for the adaptation gain is decided before any learner data ([AUTHOR A31]; V63 dropped it from P2).
- **Zone moves.** After a zone move, the band and the regime set are re-fixed by the unchanged band rule in a dated addendum before any validation-seed evaluation of a learning arm ([AUTHOR A34]).

---

## Appendix A: sources and read status
- Yuan, Knoop & Hoogendoorn (2017), *Transportation Science* 51(3):852-862: accepted manuscript read in full (TU Delft repository). The originals cited in its review: [VERIFY].
- Yuan, Knoop & Hoogendoorn (2015), TRB 94th Annual Meeting poster 15-4064: read in full (pre-queue capacity 6,300 veh/h; observed discharge 5,220–6,840 veh/h; fit Q = 29·v + 5,000). The TRR 2491 paper: not read.
- Cassidy & Bertini (1999), TR-B 33(1):25-42: abstract only [VERIFY].
- Chung, Rudjanakanoknad & Cassidy (2007), TR-B 41(1):82-95: abstract only [VERIFY]; secondary numbers disagree (3–18 % vs 5–18 %).
- Geroliminis, Srivastava & Michalopoulos (2011), UMN CTS 11-05: read in full. Srivastava & Geroliminis 2013 (TR-C 30): not read [VERIFY].
- Han, Liu, Liu & Leclercq, arXiv 2602.22019v2 (2026): read in full.
- NRA/TII, "A Study of Lane Capacity in the Greater Dublin Area" (Feb 2012, AECOM): read in full, including §5.4 (the 60 km/h boundary), Table 5.2 and §7.1. Lorenz & Elefteriadou, the breakdown criterion it adopts: not read [VERIFY].
- HCM 7th ed.: via the McTrans page and the TxDOT manual Table 3-1 only [VERIFY].
- Boukhellouf, Buisson & Chiabaut (2023), ETRR, DOI 10.1186/s12544-023-00586-1: summarising fetch only [VERIFY the table values].
- Schönhof & Helbing (2007), *Transportation Science* 41(2):135-166 (arXiv cond-mat/0408138): relevant sections read [VERIFY cited originals].
- Treiber, Kesting & Helbing (2010), arXiv 1004.5545: §2 read [VERIFY venue]. Treiber & Kesting (2010), arXiv 1008.1639: §2.4–2.6, 3, 4 read [VERIFY venue].
- Zielke, Bertini & Treiber (2008), TRR 2088; Mauch & Cassidy (2002): abstract level [VERIFY].
- TII PAG Unit 5.1 (PE-PAG-02015, Dec 2023): §3.2 and Table 5.1.2 read; the GEH formula checked on the rendered page. UK TAG M3.1: §3.3.10-3.3.16 read.
- TII PAG Unit 6.11 (PE-PAG-02030, Sept 2026) and DoT TAF Module 8 (July 2026): the relevant tables read, including Tables 6.11.13–14 (fuel consumption function and parameters; the OGV2 row used in P0-G4). Whether OGV2 is the class of a 40 t articulated vehicle: [VERIFY].
- Behrisch, Flötteröd & Wagner (2024), SUMO Conf. Proc. 5: read in full (the origin of the manufacturer data [VERIFY]).
- FHWA Traffic Analysis Toolbox Vol. III (2019): summarising fetch [VERIFY]. Wang, de Souza & Karbowski, arXiv 2409.19090: read in parts.
- SUMO documentation (RoadCapacity, VehicleInsertion, ACC, EIDM, vType pages): summarising fetches [VERIFY]. SUMO 1.27.1 behaviour: local toy runs, `scratchpad/protocol/toy/` and `scratchpad/protocol/review_phys/` (knife.py: per-step deceleration counts at the decel cap; hold_recover.py: entry `setSpeed` step and hold recovery).
- Stern et al. (2018), TR-C 89:205-221; Hayat et al., arXiv 2310.18151; FHWA-HRT-21-008: as recorded in `docs/research/literature_v0.md`.
- Kesting et al. (2008), the IDM-based ACC named in candidate A3: not read [VERIFY].
- ISO 15622 (ACC): not read; named only as [VERIFY], no value cited.
- `docs/research/truck_energy_check_v0.md` (v5b1): read (40 t road-load + Willans: 221 / 238 / 254 / 273 g/km at 60 / 80 / 90 / 100 km/h; COPERT 215 / 216 / 248* / 300* g/km, * extrapolated).
- `docs/research/literature_v0.md` (v5b1): F7 (HBEFA4 BEV acceleration 184.8 Wh for 0 → 30 m/s vs about 225 Wh kinetic for an assumed 1.8 t) read.
- Archive documents (branch `claude/v5b-core`): cited inline by path and line; ARCH vsl_lab/netgen/mrg3.py:29, :54 read for the LD3 node types.
- Review arithmetic: `scratchpad/protocol/rev_bidir_desk.py` (point-queue drain times, desk critical levels, guard pass probabilities, G5 noise, t vs n₁). v1: `scratchpad/protocol_v1/desk_v64.py` (the V64 per-section table and the single-queue drain at the lane drop).

---

## Appendix B: Synthesis notes

*Kept as written for the synthesis, before the review. Where it conflicts with the body or with Appendix C (for example on the guard test level, the release recommendation, the ACC selection rule, the wall-time cap or the [AUTHOR] deadlines), the body and Appendix C govern.*

### B.1 Base draft and scores
Totals over the three judges (sum of six criteria each): **draft_kill 143**, draft_rigor 142, draft_feasible 120 (my arithmetic). Judges 1 and 2 named rigor the winner (judge 1 called the totals a tie); judge 3 named kill. Following the rule "start from the highest total", **kill is the base**: its skeleton (KILL-first staging with a B0-only first gate, calibration futility stops, the plateau probe, the P2 selection and held-out confirmation of both O and F, the plant-variant ladder) is kept. Rigor supplies most of the measurement, statistics and health machinery; feasible supplies the implementation-acceptance tests, the operational T3 cases and the Irish breakdown threshold.

### B.2 Ideas taken, by source draft
- **From draft_kill:** the design rule "most likely failure first" and the B0-only P0-G1 before `exec`, V2X or any arm is built; the calibration futility stops F1–F3 (extended here by F4 for the ACC ladder); the plateau probe as the instrument for the between-run drop estimator; the expected outcome written before data; one independent RNG stream per route keyed by (seed, route); r indexed by (route, car/truck) and shared by every arm; the level grid anchored on λ_c with λ = 1.0 always in the map; one candidate set reused at every level, making the pooled optimum and T2 free; O and F both selected on the same tuning seeds and both confirmed on held-out seeds 200+; the delay guard at the same Bonferroni level as the effect test; the pooled rate ratio for rare events; the headroom ceiling (kept as report-only); stage-1 futility; the fixed plant-variant ladder V-1 / V-2 with "realism FAIL disclosed" ruled out; "no band level is called realistic unless λ = 1.0"; the SUMO option table; the CPU anchor and the KILL-path savings; the archive wave estimator (10-s series, high-pass, ≥ 15-min segment, correlation ≥ 0.3, interior lag).
- **From draft_rigor:** the intersection-union principle and the named Bonferroni families; the conflicts-and-gaps list (§1.1); measurement sections just downstream of each bottleneck with an active-bottleneck test; the computability probabilities for G1 and the pre-registered extension to n = 40; the wave-speed resolution argument; T0b directional at a sub-critical level, T0c two-sided at the bottleneck, T0d sensing integrity; T1a on fresh seeds with a discharge band; the held-out n rule from a planning σ; the relative-CI bootstrap that resamples numerator and denominator; the invalid-run encoding (+∞ for the arm, 0 when only the reference failed); the gameability table and the five-test metric screen; the health layer with a detector for every known artefact and the golden B0 hash; the step-size check; the W13 asymmetry; Addenda A/B/C; VoT frozen before the first check seed; the grid-edge extension; selection by the paired statistic; KILL-2 (in-sample futility after stage 2); the sensitivity rows by re-scoring; the read-status appendix.
- **From draft_feasible:** acceptance tests that prove the code can FAIL (negative controls, including the once-only `slowDown` that must FAIL the hold test); the module-by-stage mapping to `port_map_v0.md`; T3 with an in-process close/start and a run SIGSTOPped and resumed by the CPU guard; a resumable ledger with health columns filled by code; σ for the held-out n taken from the stage-2 SDs before the held-out stage; the TII 2012 60 km/h / 5-min breakdown threshold and the 60/70 km/h hysteresis; the TII breakdown flows as Irish context (report-only here); the post-hoc disclosure of the energy bands; renaming the on-ramps OR1/OR2; the truck-length question; the λ = 1.0 ≈ 2,400 veh/h/lane arithmetic; the R2 leader-acceleration finite difference and the R1 dx_s [VERIFY]; R1/R4 may start stage 1 early without any decision being taken early; the "critical path is engineering" view; the 72-h projection checkpoint.
- **New in the synthesis** (in none of the drafts): the stage-1 futility threshold t that adapts to σ_plan,1, with a stated ≤ 1 % false-screen probability; the censoring and origin-queue guards in the band rule instead of excluding drain- or boundary-limited levels; the pre-registered order rule for the two plant variants (merge-type BN* → V-1 first, otherwise V-2 first); q₁ = 0.70 and t_pk = 5,160 s from mapping the fitted US-169 curve onto the window; dropping the archive onset-share gate from G1 with the binomial reasoning; G3 on the pooled rate ratio; plant-invalid levels above λ_c + 0.1 instead of a plant FAIL when artefacts appear only far over capacity; the ACC ladder A0–A3 with CACC and tau 1.5 s excluded on archive and toy evidence; P0 seeds rearranged so that P1 has its own fresh block; an exhausted ACC ladder routed to [AUTHOR A11] (KILL or a new CAV model) instead of to the HDV plant-variant ladder, which cannot fix a CAV model; the deadline column in §11.

### B.3 Judge defects and how they were handled

| Draft | Defect (judges) | Handling |
|---|---|---|
| kill | T1-a = P0-G1: the drop never replicated on fresh seeds in the triangle | fixed: T1a on P1 seeds 060–089, three levels, discharge band |
| kill | P1 reuses P0 seeds 035–054 whose B0/B1 outcomes were already seen | fixed: P1 has its own fresh block 060–089 (§7) |
| kill | G1 needs only ≥ 3 runs per group | fixed: ≥ 5 per group, n = 30, binomial computability, +10 extension |
| kill | No active-bottleneck condition on Q_dis; D1 only 750 m upstream of the lane drop | fixed: sections just downstream + downstream probe ≥ 70 km/h (§3.2) |
| kill | G_max not a proven upper bound, used to prune and KILL, no uncertainty, e_class only at 80/90/100 km/h, unplanned code | fixed: report-only by default (A5) with a bootstrap CI; e_class measured at 50–120 km/h with interpolation; the module listed as new code (§2.8) |
| kill | KILL on an untuned R4 at T1-b goes beyond CLAUDE.md | fixed: A17 recommends proceeding to P2 |
| kill | No observation-spec or V2X integrity check | fixed: T0d and the P1-B contract test |
| kill | Wave speed with < 5 estimates = n/a | fixed: not computable = FAIL (G2(b)) |
| kill | No gated step check; no origin-queue energy guard | fixed: P0-G5 gated; origin-queue guard in §6.8(g) |
| kill | End level 0.5 unsupported (fitted curve 0.70 at 10:00) | fixed: q₁ = 0.70 from the fitted curve (A12) |
| kill | `departLane="random"` uses SUMO's RNG, not in the manifest, divergence undisclosed | fixed: disclosed as a CRN limit (§2.3) |
| kill | 12 m truck length unquestioned | fixed: A13 |
| kill | Relative CI does not resample the denominator | fixed: §8.2 resamples both |
| kill | T0-b sign-agnostic at λ = 1.0 (over capacity), n = 15 with m = 12 | fixed: T0b directional at λ_sub, n = 30, intersection-union; T0c at λ_c + 0.2 with m = 2 |
| kill | One invalid B0 run makes a level plant-invalid (false-KILL source) | fixed: admissibility at B0 invalid share ≤ 5 % (n ≥ 40); a reference-only failure gives a paired difference of 0 |
| kill | m = 2 × levels in §6.5 vs "+ levels if A7" in §8 | fixed: m = 2L for every component (§6.8, §8.3) |
| kill | G3(b) probable FAIL not stated; CACC as A1 without consent flag; A2 departs from V36 | fixed: expected FAIL stated (§0.4, G3); CACC excluded; the IDM-based ACC (now A3) flagged for explicit consent (A11) |
| kill | V-2 rationale cites 2,323–2,335 > 2,300; V-1 ZM3 failed at 1,528 | fixed: both rationales rewritten with their limits; expected effects stated as unknown (§9.2) |
| kill | Vague sample-size top-up; no power for held-out n = 50 | fixed: σ-based rules for stage 1 (§6.5) and the held-out n (§6.7) |
| kill | Energy bands anchored on toy values without disclosure | fixed: disclosed (P0-G4) |
| rigor | ~11 gated P0 checks with source-less thresholds; only 2 variants | partly fixed: the collision-rate-per-10⁶-veh-km and HDV extreme-deceleration gates removed (collisions ≤ 2 per check; extreme deceleration a flag); R7–R9 report-only; artefacts only far over capacity make levels plant-invalid instead of failing the plant; the remaining source-less thresholds are listed in A24. **Not changed:** the limit of two plant-model variants, because CLAUDE.md asks for an early and cheap KILL; a third variant needs a new protocol |
| rigor | Per-episode noise on with invented magnitudes; inflow during the drain; CPU omits those vehicles | fixed: noise off, inflow stops at the window end (A12) |
| rigor | Drain- and boundary-limited levels excluded (likely s ≥ 1.0) yet still tuned | fixed: guards instead of exclusion (A23); only plant-invalid levels are untuned |
| rigor | Only O_k tested, narrower than V45 | fixed: O(ℓ) and F both tested (§6.8) |
| rigor | KILL comes late; P0 needs `exec`, R4 and V2X before its verdict | fixed: B0-only G1 first; `exec`/V2X built after P0; planning variance from P1; KILL-1 after stage 1 |
| rigor | Inconsistencies: non-project seeds 0–999 vs 0–9,999; golden run on 7,400,000 inside P0-B; t_pk ambiguity | fixed: seeds 1–999 (A16a); golden hash in P0-S; t_pk stated from episode start |
| rigor | "s ≈ 0.8" attributed to design_v0 | fixed: labelled my arithmetic from design_v0's desk numbers |
| rigor | Re-assigning tuning seeds 148–199 as a P0/P1 reserve | fixed: a new range is requested instead (A16c); approved roles unchanged |
| rigor | Highest CPU budget | reduced: ≈ 51–59 h planning (rigor 62–69 h); 0.1-s check only at λ_2 |
| rigor | ACC headway band [1.0, 2.0] s without a source; P0-A1 likely FAIL not stated | fixed: headway report-only; expected FAIL stated |
| rigor | Guards at one-sided 95 %, uncorrected across K levels | fixed: every component at α/m |
| rigor | Pooled arms chosen on stage 1 only (unequal selection effort) | fixed: O and F selected on the same 38 seeds |
| rigor | 0 invalid runs required at every level ≤ 1.0, including over-saturated 1.0 | fixed: the P0 artefact gate applies at λ_c (and at λ_2 only if λ_2 ≤ λ_c + 0.1) |
| rigor | ACC candidates (tau, decel) unlikely to remove cut-in braking | fixed: tau 1.5 s dropped (toy: worse); IDM-based ACC added (A3, consent); ACC futility stop F4 |
| rigor | V2 rationale overstated (aux lanes "remove" stranding) | fixed (§2.1, §9.2) |
| rigor | Median paired difference of rare hard brakes degenerate; 0.001 fallback unsourced | fixed: pooled rate ratio; the fallback is a labelled assumption in A24 |
| rigor | Fixed grid not anchored on λ_c | fixed: anchored grid (§6.2) |
| rigor | r(route, car/truck) decided in the text; non-project seeds without an [AUTHOR] item | fixed: A8, A16a |
| rigor | Step check doubles cost on FAIL | kept gated (judge 1 valued it); its consequence is decided now (A20); scope reduced to one level |
| feasible | HDV tau calibrated to the discharge-band centre (circular) | not adopted: principle 10 forbids fitting a model to a realism band |
| feasible | 1-min wave-speed series (resolution) | fixed: 10-s series |
| feasible | Within-run Q_bd/Q_dis on a rising triangle; no active-bottleneck condition | not adopted: between-run plateau estimator with the active test |
| feasible | +∞ gain when only the reference failed | fixed: paired difference 0 |
| feasible | Gain = median of per-seed ratios | fixed: median paired difference over the reference median; per-seed ratios as a sensitivity row only |
| feasible | Native-rate KILL insurance on the KILL path only | not adopted (A22) |
| feasible | Hard braking not in the band; delay guard optional | fixed: both in the band rule |
| feasible | Author menu after seeing a V-1 FAIL | fixed: a fixed ladder with a pre-registered order rule |
| feasible | r(route, class) undefined | fixed: A8 |
| feasible | Thin samples (n = 20; stage 1 n = 6); no MDE for T0-b/T1-b | fixed: n = 30 in G1 and P1; stage 1 n = 8 with an adaptive futility threshold; MDE table §8.7 |
| feasible | A zone change re-runs P0 | fixed: it re-runs P1 and P2 only |
| feasible | B12 vs B13 citation; "6 getters × 1.34 µs" wording | fixed |
| feasible | T2 G_k from unpaired ratios of medians | fixed: paired form (§6.11) |
| feasible | Breakdown-flow band built from single-lane extremes | changed to report-only Irish context (P0-R5) |
| feasible | "0.2 s cuts ACC emergency events by ~40 %" generalised from 100 % ACC | not repeated |
| feasible | CAV braking artefact only an alarm | fixed: P0-G3 gated |

### B.4 Arithmetic re-checked for the synthesis (python3, this session)
Binomial computability for G1 (n = 30 and 40); Bonferroni z for m = 2, 6, 16, 18; the σ thresholds of the held-out n rule; the stage-1 futility thresholds and false-screen probabilities; the χ² factors 1.351 and 1.136; the renormalised fleet shares (CAVs 28.555 % of cars, 26.413 % of all vehicles, BEV share 33.62 %; HDV cars 60.03 % ICE); the vehicle count at λ = 1.0 (775 + 5,502 + 6,939 ≈ 13,216); the toy braking ratios from b_grid2.txt; the truck energy table from `truck_energy_check_v0.md`; the TII §5.4 breakdown criterion from the downloaded note. Judge totals: 49 + 48 + 46 = 143 (kill), 49 + 46.5 + 46.5 = 142 (rigor), 41 + 39.5 + 39.5 = 120 (feasible).

---

## Appendix C: Review log

The synthesis (`protocol_v0_synth.md`) was reviewed through five lenses: statistics (S), honesty (GH), physics (PHYS), consistency with the binding inputs (C) and a bidirectional pass (BDP: down from the thesis claim, up from each threshold). Each finding was then verified against the text and, where possible, recomputed. "Severity" shows the lens's rating → the rating after verification. Findings that the verifier marked as needing the author became [AUTHOR] items with options, costs and a recommendation (§11) instead of silent choices.

| Finding | Lens | Severity | Verdict | What changed (or why not) |
|---|---|---|---|---|
| S1 | stats | blocker → blocker | confirmed | P1 levels ℓ₁–ℓ₃ redefined as grid points, ℓ₃ replaced by λ_c + 0.05 when plant-invalid (§5.0); T1a gates artefacts with zero tolerance only at ℓ₁, ℓ₂ and applies the admissibility rule at ℓ₃; σ_plan,1 and the KILL-1 calibration use admissible levels only; the §6.2 replacement rule maps P1 levels to their nearest grid point; one admissibility rule (B0 invalid share ≤ 5 %) for G2(c) above λ_c + 0.1, T1a(ii) and band (a) (§8.8); T0c falls back to ℓ₂ |
| S2 | stats | major → minor | plausible | n_eval also uses a bootstrap of the whole band rule on the 38 selection seeds at n = 40 and 60, for O(ℓ) and F (§6.7); the guards' test level went to the author ([AUTHOR A27]); the 20-event fallback of (f) was replaced by a continuity-corrected ratio with no switch (§6.8, §8.5); a reference-only failure is encoded as the arm's worst case in the guards, with the 0 encoding as a sensitivity row (§8.4) |
| S3 | stats | major → minor | plausible | Selection eligibility is re-evaluated on all 38 seeds with the band's own criteria (d)–(h) and tolerances (§6.6); F's pooled objective gives no credit at levels where it is ineligible; stage-1 advancement allows ≤ 1 invalid run of 8 (false screen-out ≈ 0.01 instead of 0.15 at a 2 % invalid rate). Not changed: the selection objective stays the lowest J (the CLAUDE.md lookup definition); the predicted pass rate is reported, not used to select |
| S4 | stats | major → major | confirmed | P0-G5 is paired by seed on the shared manifests, with the paired median relative difference and its CI; J2 on seeds with onsets in both runs (≥ 5); the test form (point estimate vs TOST) went to the author in [AUTHOR A20] (recommended: point estimate, consistent with §8.6) (§4.8) |
| S5 | stats | major → minor | plausible | The error claim is restated (FWER ≤ 0.05 under the null of no gain; 10 % is a point criterion), with an operating-characteristic table; seeds 200–259 decide membership only, and effect sizes are re-estimated on 300+ (§6.8, §12.2); [AUTHOR A6] option (c), a designated level fixed by a rule written now, added and recommended |
| S6 | stats | major → minor | plausible | G1(d) is evaluated on the original 30 runs only, so the extension cannot add FAIL risk (§4.4); the code-integrity vs traffic-artefact split is offered in [AUTHOR A24] (recommended: no split). Not changed: zero tolerance near critical, which the brief requires; §8.8 now states the two roles explicitly |
| S7 | stats | minor → minor | plausible | The KILL-1 threshold t is calibrated empirically by resampling the P1 paired samples shifted to a 10 % gain; the normal formula is reported alongside; coverage limited to the P1 levels is stated (§6.5) |
| S8 | stats | minor → minor | confirmed | C5 runs on all 8 calibration seeds, with ≥ 20 vehicles per cell, a pooled-pace fallback, a sanity FLAG, and the fallback cells recorded (§2.6, §3.1) |
| S9 | stats | minor → minor | confirmed | Order fixed: the edge check runs after stage 1 and before KILL-1; nothing is added after stage 2; F's pooled objective covers an added level (§6.10, §0.2) |
| S10 | stats | minor → minor | plausible | C4 selects at R ≤ 0.85, keeps candidates up to 1.25 for G3, and runs at the G3 levels (λ_c, λ_c + 0.1); the margin trade-off (ladder exhaustion) is shown in [AUTHOR A11]; the reported R is labelled conditional on selection (§2.6, §4.6) |
| GH-1 | honesty | blocker → blocker | confirmed | Every [AUTHOR] item is due before seed 7,400,000 (A9, A30 before 060); Addendum B (VoT, prices, constants) is committed before seed 000; the calibration report shows design quantities and futility outcomes only, and ρ, Q_dis, C and R values are not tabulated until the P0 report (§4.3, §9.4, §11). A18 records that only the VoT uplift is open |
| GH-2 | honesty | blocker → blocker | confirmed | A5, A6, A7, A14, A15, A21, A22 and A23 are due before seed 000; principle 1 now says P0/P1 results can only feed a tightening addendum; Addendum C moved before seed 060 (§0.3, §6.3, §11) |
| GH-3 | honesty | major → major | confirmed | Guard (g) uses pooled totals, an origin-queue factor of 1.02 and sign counts (§6.8); imputation rows for censored trips and origin-queue idle energy (§6.12); TTT counted from the desired departure (§3.1); the CLAUDE.md co-headline vs V29 recorded in §1.1 item 15; served throughput with its CI in the band table |
| GH-4 | honesty | major → major | plausible | A binding parity clause for the D5.8 comparator (§12.2, [AUTHOR A32]); Addendum C states each rule's dimension; a parameter-adequacy refinement inside P2 (§6.10) |
| GH-5 | honesty | major → major | confirmed | Principle 10 reworded (pre-registered discrete selection allowed, counted and disclosed); a settings counter k ≤ 6 in every P0 verdict (§9.2, §4.10); G3(b) gated on a point estimate ≤ 1.0 and an upper bound ≤ 1.2; the ΔDl flag can trigger only a dated deviation with a fresh-seed G3 re-run (§4.6); the §2.2 header names the ladders as the only route to a changed setting |
| GH-6 | honesty | major → major | confirmed | [AUTHOR A7] options extended (r vs B1 ≤ −5 %; control share ≥ 0.5); decomposition rows and the wording rule are mandatory (§6.8); the §3.4 row corrected ("narrows but does not close"); G3 reports R₃ at −3 m/s² and activates the conditional guard (f′) vs B0 when R₃ > 1 + y (§4.6, §6.8, [AUTHOR A14]) |
| GH-7 | honesty | major → major | confirmed | HDV hard-brake and severe rates reported for every arm and level, in the metric screen and the map, with a FLAG (§3.1, §6.5, §6.12); the §3.4 row corrected; [AUTHOR A29] (recommended: report-only with the FLAG) |
| GH-8 | honesty | minor → minor | confirmed | Merged with C1: a CPU-time cap per arm family, hangs as OPS failures re-run once, a P0-B12 negative control (§2.6 C8, §2.7, §4.1) |
| GH-9 | honesty | minor → minor | confirmed | Band membership is reported under every sensitivity row, with a "price-dependent" label (§6.12) |
| GH-10 | honesty | minor → minor | confirmed in part | Wave speeds corrected to −14 to −19 km/h (§4.5). The TII 1,700–1,800 figure was not a misquote (§7.1, now quoted exactly); Table 5.2 values added (P0-R5). Of "check every other inline number", only a spot-check was done in this revision (see the note below the table) |
| PHYS-01 | physics | major → major | confirmed | §2.1 desk estimate replaced by a per-section table (BN-M2 binds first on paper, λ ≈ 0.61–0.76); Q_ff and Q_dis exclude upstream starvation, with counts reported (§3.2); a P0-B11 synthetic case; the §9.2 order-rule consequence stated |
| PHYS-02 | physics | major → major | confirmed | G1(a) requires ≥ 5 runs valid for Q_dis at BN*, also with the extension; the computability row states that the binomial bounds only the onset split (§4.4) |
| PHYS-03 | physics | major → major | confirmed | The event definitions went to the author ([AUTHOR A28]; recommended: strictly beyond the shared cap, at speed, for G3); the threshold must differ from every vType decel (P0-B3); an exact-cap case in P0-B11; the §0.4 toy figures restated under each definition |
| PHYS-04 | physics | major → major | confirmed | A deterministic approach test joins the C4 pre-screen on a non-project seed, before any calibration seed is spent; failing candidates are dropped, so A3 is reached early if A0–A2 fail; §0.4 states the toy approach braking. The ACC mode switch near 100 m stays [VERIFY] |
| PHYS-05 | physics | major → major | confirmed | Per-lane discharge at BN-LD with a metronome FLAG (§2.7, §3.2, P0-R9); events attributed by location and onset speed; the speed condition went to the author ([AUTHOR A28]); a non-zipper lane drop is stated as excluded because archive LD3 also failed (§9.2) |
| PHYS-06 | physics | major → major | confirmed | Merged with S4 and BDP-5: G5 paired, run at λ_c (gated) and λ_2 (gated if admissible), censored share reported (§4.8). Not adopted: sizing n from the calibration SD, because calibration has no 0.1-s runs; the paired SD is reported instead |
| PHYS-07 | physics | major → major | confirmed | The entry target is reached by a `slowDown` ramp; the first post-entry ramp is bounded at 1.04 m/s² and exempted in T0a (1)/(8); T0a adds the speed-remainder cases, lane changes, the Z2 → Z3 crossing and a gate of 0 exec-induced steps below −3 m/s² (§2.5, T0a); carried into [AUTHOR A9] |
| PHYS-08 | physics | major → minor | confirmed | T1a adds ρ_T1 = triangle discharge ÷ the P0-G1 Q_ff ≤ 0.97 at the calibrated BN*, with other bottlenecks reported separately (§5 T1a) |
| PHYS-09 | physics | minor → minor | plausible | Probes and the active test use through lanes only, vehicle-weighted; auxiliary lanes reported separately; a P0-B11 synthetic case (§3.2, §4.1) |
| PHYS-10 | physics | minor → minor | confirmed | 1,740–2,280 cited as the observed range, with the fit's 1,725–2,247; the v_cong relation recomputed against 6,300 and 6,840 veh/h; A2(b) restated; a high-v_cong false-FAIL risk added to G1; the toy release time restated (first acceleration logged 2.4 s after the call) |
| C1 | consistency | major → major | plausible | As GH-8, plus caps measured at production concurrency (C1/C2) and from timing tests per arm family, and job order shuffled across arms (§2.6, §2.7, §4.1, §10.4) |
| C2 | consistency | major → major | confirmed | Merged with BDP-1 and S2: [AUTHOR A27] with four burden-of-proof options and their pass probabilities; the expected guard bounds computed after stage 2 feed the n_eval rule (§6.7, §8.7) |
| C3 | consistency | major → major | confirmed | [AUTHOR A13] extended with the CAV desired-speed options and their consequence (measured in P0-R2 before seed 100); B1 − B0 reported next to (b) and (e); the delay-guard floor keeps (e) continuous near zero B0 delay (§6.8) |
| C4 | consistency | major → major | confirmed | Any insertion, step or HDV-model change re-runs C1–C8 ([AUTHOR A16d] extended; §2.6, §4.5, §4.8); the r rule fixed (as S8); the r-table and Addendum B constant hashes added to T3c |
| C5 | consistency | major → minor | confirmed | COPERT and TII OGV2 truck rows added to §6.12 (per-edge averaging, extrapolation disclosed, sign agreement reported); P0-G4 code checks for both, with the OGV2 coefficients from PAG 6.11 Table 6.11.14 |
| C6 | consistency | major → major | confirmed | [AUTHOR A10] now states that (b) amends V36 and `interfaces.md` §1/§3/§9 and needs a precedence rule; the recommendation changed to (a), the decided release; T0a covers the Z2 → Z3 crossing |
| C7 | consistency | major → minor | confirmed | Principle 10 reworded; [AUTHOR A11] adds the empirical-target option; every look is counted in k and reported |
| C8 | consistency | major → minor | confirmed | Observation specs frozen in Addendum C before seed 060, Z3's downstream field defined, the spec hash recorded per rule, a re-run rule on spec change (§6.3); [AUTHOR A30] on BN-M2 information |
| C9 | consistency | major → major | confirmed | P0-G4 adds idle, 10–40 km/h cruise, an acceleration floor, a regeneration bound and the truck cycle; the known HBEFA4 BEV under-charge led to [AUTHOR A33] |
| C10 | consistency | minor → minor | confirmed | [AUTHOR A31]; the reported quantity relabelled "G, i.e. H without the adaptive scheduler"; G labelled "oracle with rule switching"; the same-rule lookup I_F reported in-sample (§6.11) |
| C11 | consistency | minor → minor | confirmed | §1 lists every V# (V5, V13, V33 superseded; V18 pending; V22 open); V10 power traces for a pre-declared subset (§10.4); [AUTHOR A35] for V18, V22 and the trace subset; stop-and-go thresholds in A24; the V21 price date in Addendum B; HDV braking in G3 and P0-R7 labelled a plant diagnostic |
| BDP-1 | bidir | blocker → major | confirmed | As C2: [AUTHOR A27]; guard pass probabilities in §8.7; stage-2 eligibility uses the band's guard form (§6.6); the delay-guard denominator floor (§6.8(e)); the 20-event discontinuity removed (§8.5) |
| BDP-2 | bidir | major → major | confirmed | [AUTHOR A25] for the floor (due before seed 000), with the TII M50 arithmetic; A1 moved to seed 000; F2 tied to the chosen floor; A13 states the truck-length interplay |
| BDP-3 | bidir | major → major | confirmed | §2.1 per-section table and drain arithmetic; [AUTHOR A6] option (c) and [AUTHOR A26]; a C1 downward extension and F5 for an undefined λ_c; F3 restricted to levels ≤ λ_c + 0.1, so over-saturation alone cannot stop P0; the time compression disclosed in A12 |
| BDP-4 | bidir | major → minor | plausible | Folded into [AUTHOR A7] (options (b), (c)) with the decomposition rows; the claim that the speed-compliance effect is "kept away from control credit" was removed from A13 and §3.4 corrected |
| BDP-5 | bidir | major → major | confirmed | As S4 and PHYS-06; G5 exempts a plant-invalid λ_2; A20 states what a move to 0.1 s re-runs and that 0.1 s gets no further step check; A16d covers the re-calibration |
| BDP-6 | bidir | major → major | confirmed | G3 and C4 run at λ_c and λ_c + 0.1, never at a plant-invalid level; G3(a) counts only seeds with a clean B0; F4 has a 1.25 margin; G3(b) also needs an upper bound ≤ 1.2 |
| BDP-7 | bidir | major → major | confirmed | A parameter-adequacy refinement (§6.10(ii)) with inner and outer ranges in Addendum C, ordered before KILL-1; KILL-3 worded "tuned within the Addendum C ranges and the refinement"; the spread and the default gap reported; a cost row |
| BDP-8 | bidir | major → minor | plausible | A zone-move cost row (§10.2); the re-fix rule after a move (§9.5, §12.2); [AUTHOR A34] decides the T0b/T0c consequence now. Not adopted: a cap on moves, which would contradict V56 |
| BDP-9 | bidir | minor → minor | confirmed | §10.3 states that KILL-1's saving holds only when t is clearly positive; the empirical t (S7) and its coverage statement; n₁ = 12 offered in [AUTHOR A15] |
| BDP-10 | bidir | minor → minor | confirmed | As C10 ([AUTHOR A31]) |

**Note (v1, 2026-10-13).** The log above describes v0 and is kept as written. Under the V64 layout some of its statements no longer hold: PHYS-01 and BDP-3 ("BN-M2 binds first on paper"): BN-LD now binds first (§2.1); PHYS-05 (per-lane discharge and metronome at BN-LD): that bottleneck is now the expected primary one; C8 ([AUTHOR A30] on BN-M2 information): A30 now concerns a unit downstream of BN-LD; C6 and PHYS-07 (the Z2 → Z3 crossing): the gap is now 500 m and contains merge 2, not the zipper. Appendix B is likewise v0 history.

**Spot-check of cited numbers done in this revision** (GH-10 asked for all of them): TII 2012 §7.1 and Table 5.2; ARCH STATUS.md:57, :69, :73; ARCH design_v0.md:43 (B14); ARCH lessons_metric_gameability.md §5; ARCH vsl_lab/netgen/mrg3.py:29, :54 and ARCH t2_realism_ld3.md; `truck_energy_check_v0.md` (the 40 t and COPERT rows); literature_v0.md F7 (lines 336–342) and line 757; PAG 6.11 Tables 6.11.13–14; the Yuan et al. 2015 poster text; `decisions.md` V1–V57; `interfaces.md` §1–§10. All other inline numbers carried over from the synthesis were not re-checked against their cited lines and should be before approval.

**Choices the reviser made that the findings left open** (each is either an [AUTHOR] recommendation or an ASSUMPTION listed in A24, so the author can reverse it):
- recommendations changed from the synthesis: A10 now recommends the decided release (a), not the ramp (b); A6 recommends the designated level (c); A27 recommends point-estimate guards (c); A13 recommends keeping CAVs at 100 km/h with the handicap stated (iii);
- G3 and C4 gate at λ_c and λ_c + 0.1 (both admissible by construction) rather than at λ_2, at a cost of 40 extra runs; G5 runs at λ_c and λ_2;
- the edge-level check moved from after stage 2 to after stage 1 (S9 allowed either order); the parameter refinement placed at the same point, before KILL-1;
- stage-1 advancement relaxed from 0 to ≤ 1 invalid run of 8; selection eligibility and band validity at ≤ 5 %;
- the delay guard uses one continuous formula with a denominator floor of 5 % of R_tot instead of a separate "B0 delay ≤ 0" branch;
- the hard-brake guard uses a 0.5 continuity correction instead of an exact conditional test with a minimum count;
- the KILL-1 threshold is calibrated by resampling the P1 samples (the S7 proposal) rather than by a studentised per-level t (the BDP-9 alternative);
- a provisional CPU-time cap of 8 × the smoke median during calibration, the final 4 × cap from seed 010;
- F's pooled objective scores an ineligible level as J = 0, with ties broken by the unpenalised mean;
- the zone-move rule keeps V56's freedom (no cap on moves) and adds only a cost row and the re-fix rule.

---

## Amendment log

### v1, 2026-10-13 (author decisions V58–V65)
- **Status.** DRAFT v0 → v1: every [AUTHOR] item answered (§11, last column); binding after the author's approval commit, before seed 7,400,000. No project seed was used for v1.
- **V58, V64: road redesign, option 1.** The 3 → 2 lane drop (zipper node, BN-LD) moved from 4,500 m to 6,000 m, the downstream end of Z3; merge 2 (BN-M2) moved from 5,750–6,000 m to 4,500–4,750 m with four lanes (auxiliary lane + 3); Z3 moved from 4,750–5,750 m to 5,000–6,000 m; three lanes from 0 to 6,000 m, two from 6,000 to 9,250 m; routes unchanged. Updated: the status lines, §0.4, §1 (V2/V56, V15/V27 rows, new rows V58–V65), §1.1 items 5 and 20, §2.1 (edge table, reference points, bottleneck groups, the per-section desk estimate with the same method and c = 1,600–2,000 veh/h/lane, its consequences, and the point-queue drain re-computed for the single drop: about 1,400 / 2,010 / 2,670 vehicles queued at 9,900 s, 22 / 34 / 50 min to drain), the zipper bullet, §2.7 (metronome section at 6,100 m), §3.2 (sections at 3,400 / 4,900 / 6,100 m; upstream order BN-M1 → BN-M2 → BN-LD), §4.4 known risks, T0a scenario (3), §6.1 and §6.3 (A30 unit on [6,000, 7,000) m; R3 at a lane drop [VERIFY]), §9.2 (V-2 now the likely first variant), §11 rows A6, A10 and A30, and a note under Appendix C. BN* is expected to be BN-LD.
- **V59 (A1).** At most 2 variants and 6 setting changes, each on fresh seeds, then P0 KILL; never a disclosed realism FAIL (§9.2, §11).
- **V60 (A11).** A3 allowed (§2.6 C4, §11).
- **V61 (A7).** Band criterion (d) is now r vs B1 ≤ −5 % with its CI upper bound < 0 (§6.8); §1 (V44 row), §3.4 and §6.6 follow it; the decomposition rows and the wording rule stay.
- **V62 (A16c).** Seeds 7,401,000–7,401,999 approved for re-rounds (§7).
- **V63 (A31).** No non-learning adaptive scheduler in P2, disclosed (§1.1 item 19, §6.11, §12.2).
- **V65.** Every other item takes its recommendation (§11, last column); the non-project seeds 1–999 approved (§7, A16a); truck length 16.5 m [VERIFY] (§2.3, A13); the §1 rows for V18 and V22 follow the updates in `decisions.md`; A26 superseded by V58/V64.
- **Companion edits, same date, outside this file:** `docs/architecture/interfaces.md` §2, §3 (A9, A10), §4 pointer (A12), §5 (A8, A14, A19, A27, A29, A35), §6 and §7 (A30 under V64); `docs/architecture/system_context.md` §3 (V64, V60), §4 (V61, V63), §8.
- **Not changed:** bounds, seed roles, statistics and sample sizes.

### Amendment 2026-10-13 (approval, V66)
- **A7 / V61 reading (a):** the candidate passes the B1 criterion when its paired median gain vs B1 is ≥ 5 % **and** the 95 % CI of the gain excludes 0 (as written in §6.8 (d)).
- **V59 reading:** six setting changes after the original plant (k ≤ 7 counting the original); a plant-model variant may be a road variant or a driver-model variant.
- **Approved:** the author approved v1 on 2026-10-13. The protocol is binding from this commit.

### Addendum G1 (2026-10-13, before any project seed): geometry V68
The author lengthened the plain sections (V68). Order, lane counts, routes and flows are unchanged, so the §2.1 per-section desk table, the critical levels and every PASS rule stay as written. **Every position in this protocol is read through this table** (old V64 position → new V68 position):

| Item | V64 (m) | V68 (m) |
|---|---|---|
| Entry, Z1 | 0–3,000; Z1 2,000–3,000 | unchanged |
| Merge 1 (BN-M1), X1 diverge | 3,000–3,250 | unchanged |
| Plain section after merge 1 | 3,250–3,500 | 3,250–8,000 |
| Z2 | 3,500–4,500 | 8,000–9,000 |
| Merge 2 (BN-M2), X2 diverge | 4,500–4,750 | 9,000–9,250 |
| Plain section after merge 2 | 4,750–5,000 | 9,250–14,000 |
| Z3 | 5,000–6,000 | 14,000–15,000 |
| Lane drop (BN-LD) | 6,000 | 15,000 |
| 2-lane exit section | 6,000–9,250 | 15,000–18,250 |
| Measurement sections (§3.2) | 3,400 / 4,900 / 6,100 | 3,400 / 9,400 / 15,100 |
| Metronome probe (§2.7) | 6,100 | 15,100 |
| A30 downstream V2X unit | 6,000–7,000 | 15,000–16,000 |
| Bottleneck groups [x_k − 750, x_k + 250] | around 3,250 / 4,750 / 6,000 | around 3,250 / 9,250 / 15,000 |

**Consequences:**
- The distance from the drop back to merge 2 grows from 1,250 m to 5,750 m. Queue spillback to merge 2 needs a much longer queue, so BN-M2 interaction appears later and at higher inflow.
- Free-flow trip times roughly double, so the reference times r(route, class) are re-measured on this network (as §5.2 requires anyway).
- The CPU estimate per episode (§10.1) grows with vehicle-km and is re-measured in P0-S.
- The 30-min drain cap (V49) is kept; the drain arithmetic of §2.1 is unchanged, because it depends on flows, not lengths.
