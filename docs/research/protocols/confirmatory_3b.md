# Confirmatory 3b: fresh-seed replication of X2

Status: draft, awaiting the author's approval of this text and of the seeds (V399).

## Question

Does confirmatory 3's X2 result (V395: won on TTC by the tuned reading, 4 of 5 policies) hold on 20 seeds never used before?

## Fixed, nothing retrained or retuned

- **Code:** frozen `b_train/code_d2b2ecc`, the code confirmatory 3 ran.
- **Plant:** `plant_c3.json` on r2m3, cell X2 at 5,300 veh/h, as in confirmatory 3.
- **Policies:** the 5 final policies `conf3/train/C0-C4_final.pt`.
- **Opponents:** confirmatory 3's final `opponents.json`, unchanged. Every arm it ran in X2 runs here: no control, p333, the copy rule, the single rule, and every rule in its control list.
- **Reading:** `decide3.read_cell` for cell X2, unchanged. The counting set is decided on the new seeds by the same 2 % delay filter, so it may differ from confirmatory 3's.

## Seeds

7,440,220-239, 20 seeds. Never used; inside the confirmation block reserved since V359. They need the author's approval.

## Outcome, fixed now

- **Replicates:** at least 4 of 5 policies clear the tuned reading in X2, as defined in confirmatory 3.
- **Does not replicate:** otherwise.

Either way, confirmatory 3's verdict (V395) stands as recorded, and this result is reported beside it.

- **If it replicates:** "The X2 result held on 20 fresh seeds."
- **If it does not:** "The X2 result did not hold on 20 fresh seeds", with the counts. The X2 claim is then reported as not confirmed.

Report-only, beside the outcome:
- the replication reading against p333, the delay win, severe_ok and the copy rule;
- the counting set and its exclusions;
- a 40-seed pooled reading over both seed blocks, clearly labelled as not the test.

## Stop and bug rules

Every row must be complete, with 20 seeds per arm. Any failure stops the run and goes to the author. A bug found after results is fixed, everything affected is rerun, and both outcomes are logged.

## Disclosures

- Chosen after seeing V395-V398, on the one cell that was won.
- Before data, the seed bootstrap of confirmatory 3 put the chance of "won" on resampled seeds at about 27-30 % (V396). A failure is therefore a likely outcome and is reported as such.
- Only X2 is repeated. X1 stays closed.

## Compute

About 18 arms × 20 seeds = 360 runs, about 15 minutes at 24 workers, with the CPU guard on.
