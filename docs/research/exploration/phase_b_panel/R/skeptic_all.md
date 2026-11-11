# skeptic_all: Screen R (synth.md)

EXPLORATORY = my resampling of the 120 stored X1 seeds (already read for verdicts), n = 160; a "near-tied arm" is a stored rule shifted to the stated true edge. Scripts, outputs: `/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseB/panel/R/skeptic_work/` (sk1, sk2, sk3; `.py`, `.out`). "edge" = `an_x1x2_delay_edge.md`.

**R-all-1, blocker. §8 gives the power of one comparison; K1 is a minimum over 24 deciding arms.**
Pass chance in %, by true edge against each of k near-tied arms (EXPLORATORY, sk1.out B):

| k | 3 % | 3.5 % | 4 % | 5 % |
|---|---|---|---|---|
| 1 | 52 | 79 | 91 | 98 |
| 3 | 23 | 57 | 85 | 99 |
| 5 | 10 | 38 | 71 | 98 |
| 12 | 1 | 12 | 45 | 87 |

- Five arms at p333's stored edge (4.24 %) pass 85 %, twelve 56 %: the screen can KILL in 15-44 % with no opponent gain. A proxy: arms more alike than the stored rules lose less.
- Change: this table replaces §8's. §7: "with 5 to 12 near-tied arms the 3.0 % point bar passes 80 % only from a true edge of about 4.2 to 4.8 %". §13: say how much of the 60 % needs no opponent gain.

**R-all-2, major. The 3 % bar was chosen after the numbers it tests.**
- planb.md:519 is the 80 %-power effect of a bound rule at n = 120, not a point bar. Memo §5.3 gives no source.
- 3 % lies between the stored X1 (+4.2) and X2 (+1.9) points. As stored, the 3 % bar passes 93 %; the recorded 5 % bar (confirmatory_3.md:108), read at arm level, 2 % (EXPLORATORY, sk1.out D).
- Change: both numbers in §2 item 2 and §7; delete the planb.md:519 sentence.

**R-all-3, major. Noise steers the "PR-28-bound" label, and the label gates the protocol.**
- It is read against "the closest arm", picked on verdict rows. As stored, that is p333 in 59 % of studies, lr1000_10_1 in 21 %, os0_10_10 in 20 % (sk1.out C).
- Share on road 4a plus the ramp-2 queue (40 seeds, my proxy of planb.md:143's road set, sk2.out): p333 0.62, lr1000_10_1 0.58, os0_10_10 0.04.
- So chance decides: it fires in about 80 % of studies (INFERENCE, stored rules only). §8 admits it has no null.
- Change: "read against every deciding arm whose point is within 1.5 points of the closest; it fires if it holds against any". Add these numbers to §8.

**R-all-4, major. §1 contradicts §7.** §1: "A pass allows a protocol". §7: a PR-28-bound pass allows none, and §3 expects that label. Change: §1 "Only a pass without 'PR-28-bound' allows a DRL protocol"; §13 gives that probability; §2 adds the author's choice "run the rules-only PR-28 item first" (plant_vv_record_v0.md:96).

**R-all-5, major. Selection on 20 seeds picks by noise, which favours a pass.**
- EXPLORATORY (sk3.out): a candidate truly 2 % below p333 is picked as best of 11 in 28 % (38 % at 40 seeds).
- Record: os0_10_10 reads +1.3 % [−2.5, +4.1] against p333 on confirmatory 3's 20 tuning seeds (`work/cheap_grid_repick.out`) and −2.4 % [−3.7, −0.5] on 120 (edge:44).
- Change: select on 50 seeds (030-049, 170-199); carry the best 3 near-gap settings (1,340 more runs, about $0.1-0.5); give the pick accuracy in §8.

**R-all-6, major. The near-gap arm cannot act as written.**
- A level moves one step per 10-s hold (b_env.py:703-711; conf3/common.py:12, :47). So 0.8 to 1.6 s needs at least 20 s of held trigger, then `tau_rise` (b_env.py:781-782).
- Column 14 pools both acceleration lanes (b_env.py:912-924), so the rule also acts at merge 1.
- Change: binding criterion, fixed now: "the share of triggered decisions that reach the target level; below 50 % the setting 'did not bind' and is not picked".

**R-all-7, major. Window.** The queue never clears (V398); 28 % of the mainline edge against p333 accrues in 1,440-1,800 s (edge:68). The synthesis drops the 3,000-s window. Change: a report-only row: v3w and the three closest arms, seeds 200-239, to 3,000 s (320 runs).

**R-all-8, minor. Build and cost.** Not listed: seed constants (cmab.py:42-43); the near-gap key in `run_one` (plant_sweep.py:86-95); X1's CMA seed (planb.md:225); the 30-minute rate check (planb.md:563). The two-cell alternative totals about $12-16, above the $10 cap.

**R-all-9, minor. Wording.** Define "deciding arm" (24). §3: exploratory rows cannot fire K1; write "X2 stays closed by V466". "Trade-off" should also read the harm rule against each arm (planb.md:437). A pass with "opponent below plateau" is "screen incomplete".

Found right: §8's one-arm row; run counts and $5.8-8.0 (V475, V490, V493); disjoint seeds; closure records named; N stays 91 (cells_tested.md:5); corrections 4 and 7; no barred word.

Would I let this screen run as written: no.
