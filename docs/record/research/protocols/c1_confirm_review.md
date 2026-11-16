# C1 confirmation: review rounds and how the protocol handles them

Each round: a statistics and logic reviewer and a plant, rules and build reviewer, each finding put to a skeptic on the other model (Fable 5.2 and Opus 5.5, high effort). Recomputes were numpy on stored rows only; scripts in the session scratchpads (`frontier/`, `confirm/`).

## Round 0: the frontier-check draft (`c1_frontier.md` v0, 2026-11-14)

| # | Finding | Verdict | Handling |
|---|---|---|---|
| 1 | §2's steady-S figures (MPC-F "dominates" v3w) used the pooled arm that C-D5 rejected; under C1's statistic the stored rows read PASS | confirmed (blocker) | corrected in V526; step 1 folded into this study |
| 2 | Only delay-tuned rules sit within 1 % of v3w's delay, so PASS was near-trivial and the rules that trade delay for close-following were never read | confirmed | chords (CF-D5) |
| 3 | A rule truly 1-2.5 % slower can compete and KILL | confirmed | MATCHED AT A DELAY COST → UNRESOLVED; rate stated |
| 4 | v3w's own delay loss against p333 had no reading | confirmed | C-D6 stated, not gating, labelled (CF-D6) |
| 5 | SE and rate figures were 3E-C_TRUCK's only | confirmed | ranges quoted |
| 6 | PASS's false-rate bound was stated against a zero edge at 1.25 % | confirmed | about 2.5 % (classification plus BEATEN) |
| 7 | Null-failure order undefined | confirmed | round 1 #6 |
| 8 | A second look after UNRESOLVED was uncorrected | confirmed | CF-D7 |
| 9 | MPC-F's model not deployable | confirmed | shipped, path rewritten in every stage |
| 10 | "No rule tuned on close-following" false for five arms | confirmed | §6 rewritten |
| 11 | p000 equals no control's headway; its read-back is vacuous | partly | p000 dropped; level check for p111, p222, p333 |
| 12 | Identity replays only for C1's 8 arms | confirmed | all 29 stored arms (87 runs) |
| 13 | New code not listed | confirmed | build list (§3) and planted rows (§5) |
| 14 | "Two of the three" rules should be "all three" | confirmed | corrected |
| 15 | ASCH and P0 not labelled | partly | labelled; P0 deciding |
| 16 | Wall time of the new arms unmeasured | partly | smoke measures it; cap check before the screen |
| 17 | Twins per controller class | refuted | none |

## Round 1: this study's v0 (2026-11-14)

No blocker. Both chords on record read BEATEN on C1's rows; the whole reading gives PASS on S6's S and TRUCK rows.

| # | Finding | Verdict | v1 handling |
|---|---|---|---|
| 1 | Chords anchored at p333 only can miss a lower line through another fast rule (in S, grid_os1_10_10 with MPC-F) | partly | chords for every pair of a faster and a slower rule (CF-D5) |
| 2 | w's resampled values unclamped; chord null unspecified | partly | full-sample medians, clamped per resample; null on the per-seed chord value with w fixed |
| 3 | Chords rarely KILL; their SEs differ from rules' | partly | §2 says so, with chord SEs |
| 4 | §2's TRUCK figure and chord figures misquoted | partly | corrected |
| 5 | The extension read alone doubles PASS's bound and adds no power | partly | read once on all seeds at 98.75 %; bound about 3.75 % |
| 6 | "MATCHED stands" after a failed null was the fix the round-0 skeptic refuted | confirmed | a failed null makes the test UNRESOLVED whatever it read |
| 7 | The braking co-star had no null and left out 3E-C_TRUCK | confirmed | null on every braking edge; 3E-C_TRUCK's braking stated in every case |
| 8 | The PASS sentence overstated in three places | partly | reworded; a no-chord variant added |
| 9 | Disclosures favouring v3w missing (3E-C not converged, 3E-T/X lower bounds, copy traced from DRL, v3w trained under slowdowns) | confirmed | §6 |
| 10 | grid_os1_10_10 is a delay opponent; os0_10_10's pick unlisted | confirmed | §6 |
| 11 | Build list missed identity's MPC-F path, drain and P0 scope | partly | §3 build list |
| 12 | No seeds for the extension | refuted | its V# names them |
| 13 | Nothing checks that E30 stays C1's E30 | partly | `v5b/` diff and `perturb` equality checks (§3) |

## Final check of v1 (2026-11-14)

One checker (Fable 5.2, high). All round-1 rows fixed; v1's reading recomputed on stored rows gives PASS in S (95 chords) and TRUCK and on C1's E30 halves. No blocker.

| # | Finding | Severity | v1.1 handling |
|---|---|---|---|
| 14 | The extension's null kept the 97.5 % bar, so it checked nothing at 98.75 % | major | bar 0.94 %, 20,000 swaps, 4,000 resamples per swap (CF-D7) |
| 15 | The extension's size and CPU model unfixed | minor | 480 seeds, the screen's CPU model, else VOID |
| 16 | "never KILL" for a slightly slower rule was false | minor | rates stated |
| 17 | §2 described v0's p333-only chords | minor | updated (95 chords in S) |
| 18 | Chord and competitor edges in different units; the pair set unstated | minor | chords in the mix's own median; pairs over all 26 non-learning arms |
| 19 | Many nulls, two sides double the noise; departure from C1 unlabelled | minor | mean of the two sides, one re-estimate at 20,000 swaps; labelled |
| 20 | Pairs chosen by point signs drop out by noise | minor | pairs chosen by intervals |
| 21 | Planted rows missed new paths | minor | added |
