# Appendix B: finding details and verifier reasoning to the paper_1 forensic audit

Main report: `REPORT_paper1_forensic_audit.md` (same folder). The text below is the agents' own output, reconciled as described in §0.2 of the main report. Paths of the form `/tmp/claude-1000/.../scratchpad/audit/<dir>/...` refer to the session scratch folder; the same files are now in `~/work/phd/v5b1_runs/audit_paper1_2026-10-21/<dir>/...` (caches over 10 MB excluded, see `EXCLUDED_CACHES.txt`).

### B1. [critical] PROV-F1: 'Pre-registered before any data' is false: D2->P1->P1b->C1 sequence and post-hoc choices undisclosed

Raised as critical; verification: reproduce: CONFIRMED/critical, defend: CONFIRMED/critical, impact: CONFIRMED/critical.

#### PROV-F1 (R1 PROV, critical, disclosure): 'Pre-registered before any data' is false as written: the sequence D2 -> P1 -> P1b -> C1 is undisclosed

- **Description.** Lines 69 and 145 say that all statements, the protocol and the seeds were fixed before any data. In fact, P1's statements were designed after the D1/D2 screen data on the same plant and cells (disclosed only inside the P1 protocol). P1b's design changes (amber, PI-law plans in A, the rate clip, runner rows) were made after P1's results and in response to them. C1's cell, arms and comparator were chosen after seeing P1b's evaluation data. Each study's own statements did come before that study's data (page hashes match), so the headline numbers stand. But the paper's central integrity claim is false as worded, and this rubric counts a false statement about pre-registration as critical.
- **Evidence.**
  - p1_incident_information.md@0e8d49b:133-134
  - p1b_addendum.md@75bcd2b:5-9
  - p1b_confirm_c1.md@7c6acc8:5,36
  - git: fac8789 11:38 (D2) < 14d8866 13:38 (P1 draft); c2d11c2 03:19 (P1 result) < a0144e3 09:42 (P1b draft); 95f1f33 20:31 (P1b result) < a4e3e6d 21:09 (C1 draft)
  - scratch page_sha.sh output
- **Failure scenario.** A reviewer reads 'pre-registered before any data' and treats S1b/C1 as untouched confirmatory tests. Later they learn that the C1 cell was chosen from P1b data, and that P1b's action set was redesigned after P1 showed no type-plan gain over PI in that very cell. The integrity claim then collapses.
- **How to test.** git log --date=iso on docs/research/protocols/*, compared with ~/work/phd/v5b1_runs/*_STARTED.json times and run.log first lines.
- **Related claims.** C11, C53, C60

#### TEXT-F1 (R1 TEXT, critical, disclosure): False statements that all statements were pre-registered before any data

- **Description.** Line 69 says 'All statements were pre-registered before any data were produced'. Line 145 says 'The protocol, its statements and the seed ranges were fixed and approved before any data were produced'. Both are false as written. Screens D1 and D2 on the same plant had been seen (P1 page §8). P1 had been run, and P1b was redesigned after its results (V103, V105). The C1 cell and arms were chosen after the P1b data. The paper also contains post-data descriptive statements, marked (D) in p1b_result.md: the spill share (V109), the emergency-stop share across studies, and others. Pre-registration does hold for each study separately.
- **Evidence.**
  - paper.qmd:69, :145
  - docs/research/protocols/p1_incident_information.md:133-134 (screens D1, D2 and probes seen)
  - docs/research/protocols/p1b_addendum.md:5-10 (P1 is the earlier run; P1b motivated by V103/V105)
  - docs/research/protocols/p1b_confirm_c1.md:36 (cell and arms chosen after P1b data)
  - git log: P1 page 7da4ab4 / 0e8d49b (2026-10-19 14:12 / 16:32) before P1 eval 21:13; P1b 75bcd2b (10-20 09:51) before 13:07; C1 7c6acc8 (21:11) before 21:27; sha256 fed27bf6 / 2b3d3ccb / 8b6005aa match the sentinels
- **Failure scenario.** A reviewer takes C1 for a hypothesis fixed before any data. In fact it came from the second full round on this plant, after a redesign and a post-hoc choice of cell. Discovery would damage credibility even though C1's fresh-seed test is valid.
- **How to test.** Compare the protocol commit times with the run sentinels (done). Rewrite: 'Each study's statements and seeds were fixed and committed before that study's data; earlier screens and a first round (P1) on the same plant were seen; the C1 cell was chosen after P1b.'
- **Related claims.** C13, C85

#### REPRO-F4 (R1 REPRO, critical, disclosure): C1 cell and reference were chosen after the P1b data; the paper says all statements were pre-registered before any data

- **Description.** The C1 protocol states: 'the cell and the arms were chosen after seeing P1b's evaluation data'. It was drafted 21:09 and approved 21:11, after the P1b results commit at 20:31. Paper line 69 ('All statements were pre-registered before any data were produced') and line 145 ('fixed and approved before any data were produced') are false as written for C1, and the paper does not disclose the post-hoc choice of cell and reference. Severity is critical only under the task's literal definition (a false statement about pre-registration). The C1 numbers themselves reproduce exactly, and C1 is a valid single test on fresh seeds. The fix is wording and disclosure.
- **Evidence.**
  - docs/research/protocols/p1b_confirm_c1.md 'Integrity' section (Disclosure line)
  - git log: 95f1f33 20:31:19 P1b results; a4e3e6d 21:09:49 C1 draft; 7c6acc8 21:11:24 approved; e7dd561 21:16:00 code
  - paper.qmd:69, :145, :187
- **Failure scenario.** A reviewer reads 'all statements pre-registered before any data', then finds in the repository that the C1 cell and reference arm were selected from P1b results. This undermines trust in the pre-registration claims overall.
- **How to test.** Compare commit times of the C1 protocol with P1b results, and read the protocol's disclosure line.
- **Related claims.** C75

#### C1-F1 (R1 C1, major, disclosure): Post-hoc choice of the C1 cell and arms not disclosed in the paper

- **Description.** The C1 protocol says the cell (block_q1600) and the arms were chosen after seeing P1b's evaluation data, and that this must be disclosed. The paper does not say this. Line 145 says the protocol, statements and seed ranges 'were fixed and approved before any data were produced'. For C1 that is true only for C1's own data: the statement was written after P1b's report-only row IP vs PI 18.0 % had been seen. Fresh seeds deal with the selection effect for the test itself, but readers need to know that the cell was picked because it looked best (1 of 4 cells, and 1 of several report-only rows). The V116 caveat ('the rel CI includes values below 10 %') is also missing. The Discussion section is empty (line 199).
- **Evidence.**
  - docs/research/protocols/p1b_confirm_c1.md, Integrity: 'Disclosure: the cell and the arms were chosen after seeing P1b's evaluation data'
  - papers/paper_1/paper.qmd:145, 177 (report-only row 18.0 %), 187, 199 (empty Discussion)
  - docs/decisions.md:135 (V116 caveat)
- **Failure scenario.** A reviewer reads C1 as an independent pre-registered confirmation of a hypothesis fixed in advance, when it was chosen after looking at the P1b results.
- **How to test.** grep the paper for 'after seeing' / 'chosen'; compare with the protocol Integrity section.
- **Related claims.** C71

#### CTRL-F7 (R1 CTRL, major, disclosure): P1b's action set (G_PI) and meter were redesigned after P1's evaluation results were seen; the paper does not mention P1

- **Description.** The paper says the protocol was 'fixed and approved before any data were produced'. That is true per study: the P1b addendum was committed 09:51, the run started 10:38, and the evaluation sentinel was written 13:07 on 2026-10-20. But P1b's PI-law plans (V103 'controller-family confound') and amber (V105) were chosen after P1's evaluation on seeds 500-599. The paper never mentions P1 (grep finds nothing). No P1b evaluation or C1 seed touched any selection.
- **Evidence.**
  - docs/decisions.md V103, V105, V108; git 75bcd2b 2026-10-20 09:51; run.log tune-B finished 13:07:52
  - papers/paper_1/paper.qmd:145
  - /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/CTRL/out/seed_audit.json (disjoint seeds, single commit per study)
- **Failure scenario.** A reviewer finds the earlier round in the record and reads the omission as hidden flexibility.
- **How to test.** Add one sentence: the main study is a second round after an earlier run without amber and without PI-law plans; give the verdicts of both.
- **Related claims.** C46, C47

#### Verifier R1 reproduce: CONFIRMED / critical

Meaning: the paper says, twice, that everything was fixed before any data existed. In fact the work happened in a chain on the same plant and the same 4 cells. Screens D1 and D2 came first (and the archived BN4 results before them). Then P1 was run without amber and without PI-law plans. P1b was redesigned after P1's results. C1 then tested the one cell and comparison that P1b's report-only row made look best. Each study's own protocol and seeds were committed before that study's own runs, so the numbers are untouched. But the absolute wording ("before any data") is false, and the paper does not disclose the chain.

I re-derived the core facts myself from primary evidence.
(1) Paper text: paper.qmd:69 reads "All statements were pre-registered before any data were produced." paper.qmd:145 reads "The protocol, its statements and the seed ranges were fixed and approved before any data were produced." Both sentences are in the rendered paper.pdf (pdftotext). paper.qmd never names P1, D1, D2, a screen or an earlier round. No sentence says how the C1 cell or comparator was chosen (line 187). The Discussion is empty (line 199 is followed directly by the Conclusion).
(2) Timeline. Author dates equal committer dates and agree with the run mtimes and log lines:
- D2 runs from 10:45; D2 result fac8789 11:38; P1 draft 14d8866 13:38; P1 approved 7da4ab4 14:12; last P1 page edit 0e8d49b 16:32 (all 10-19).
- P1 runs 18:42:22 to 03:18:42; P1 result c2d11c2 03:19 (10-20).
- V103, which lists the "controller-family confound (A had no PI-law plans)" and "no amber" as P1 limits: e24c02a 06:44. V105: f8c701a 06:58.
- P1b draft a0144e3 09:42; approved 75bcd2b 09:51; P1b runs 10:38:07 to 20:30:10; P1b result 95f1f33 20:31; p1b_result.md with the 18.0 % row: 4f91777 21:03.
- C1 draft a4e3e6d 21:09:49; approved 7c6acc8 21:11:24; code e7dd561 21:16; C1 runs 21:27:50.
(3) Protocol text at the cited commits:
- p1_incident_information.md@0e8d49b:133 says "screens D1 and D2 and their numbers were seen"; line 134 says D2's evaluation runs were re-analysed and probes run.
- p1b_addendum.md@75bcd2b:5 says "P1 stays in the record as the earlier run"; lines 7-10 give the reasons (V105 amber, V103 PI-law plans, runners). The finding cites 5-9; the list actually ends at line 10.
- p1b_confirm_c1.md@7c6acc8:5 cites P1b's report-only row of 18.0 % as the reason for C1. Line 36 reads "the cell and the arms were chosen *after* seeing P1b's evaluation data".
- screen_D2_incidents.md:78 also says the archived BN4 results for slow and block had been seen.
(4) The D2 cells are the same 4 cells (slow/block x q1600/q2000) on BN4.
(5) Page hashes: fed27bf6, 2b3d3ccb and 8b6005aa equal sha256 of the pages at 0e8d49b, 75bcd2b and 7c6acc8, and match the P1, P1b and C1 sentinels. The protocols are therefore intact for each study.
(6) My own recomputation from raw runs shows the post-hoc path behind C1. IP vs PI in block_q1600 is rel -0.7 % in P1 (IP = c2000-f40_14, n = 100). In P1b it is +18.0 % (IP = c1800-p20_20_16_e4, a PI-law plan that exists only because of the post-P1 V103/V108 change). C1 tests exactly this cell, plan and comparator.
(7) paper.qmd:197 quotes "87 % (no amber)", which is a P1 number. My count gives 43,370 of 50,061 P1 non-replicate evaluation runs = 86.6 %. So the paper uses P1 data without naming P1.

Small corrections to member wording:
- CTRL-F7's "the paper never mentions P1" is true only for the token "P1". The paper labels Table II "(P1b)" (line 165) without explaining it, and it uses P1 data at line 197.
- The P1b statements S1a/S1b/S2/S3 were not rewritten after P1 (addendum line 4: "exactly as" P1). What changed after P1 data was the design under which they were tested: amber, G_PI, the rate clip and the runner rows. So for P1b, line 69 is literally true relative to P1's data; it is false relative to D1/D2. For C1 it is false outright, and line 145 is false for both the P1b addendum and the C1 protocol.

Severity: critical under the task's literal rule (a false statement about pre-registration). The headline numbers are not affected; C1 is a valid single test on fresh seeds. The fix is wording and disclosure: say that each study was fixed before its own data, name D1/D2 and P1, and state that the C1 cell and comparator were chosen from P1b.

Failure points:
- A reader could take "before any data" to mean "before that study's data". That softens it to major, but the text says "any".
- If uncommitted protocol drafts existed earlier, the per-study claim would still hold. I could not check this beyond git and file mtimes.

Checks: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/PROV-F1-reproduce/page_sha.sh: hashes every committed version of the 3 protocol pages and compares them with the sentinel page_sha256 (all match per study); /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/PROV-F1-reproduce/timeline.sh: sorted merge of git commit times, sentinel mtimes and run.log first and last lines; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/PROV-F1-reproduce/p1_ip_vs_pi.py: own numpy recomputation of IP vs PI in block_q1600 for P1 (-0.7 %) and P1b (+18.0 %); /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/PROV-F1-reproduce/p1_estop_share.py: share of P1 evaluation runs with an emergency stop (86.6 %), confirming that paper line 197 uses P1 data; git show of the protocols at 0e8d49b, 75bcd2b and 7c6acc8 with grep -n for exact line numbers; git log --follow per protocol file; git log -S to find the first commit of decision rows V94-V116; grep of paper.qmd and pdftotext of paper.pdf for pre-registration wording and for any mention of P1, the screens, an earlier round or the cell choice; Comparison of author and committer dates on all key commits (identical); ancestry checks with git merge-base --is-ancestor

#### Verifier R1 defend: CONFIRMED / critical

Meaning: the paper says, with no qualification, that every statement, the protocol and the seed ranges were fixed "before any data were produced" (paper.qmd:69, :145; the rendered PDF says the same). The natural reading is that no outcome on this plant had been seen. The defence holds only if the sentence is read per study ("before that study's own data"), and nothing in the text signals that reading.

Best defence, checked against primary evidence:
(1) Each study was pre-registered on its own terms. The sha256 of each protocol at its approval commit matches its run sentinel: P1 fed27bf6cb2f@0e8d49b (approved 10-19 16:32, run 21:13), P1b 2b3d3ccb957a@75bcd2b (09:51, run 13:07), C1 8b6005aa49a4@7c6acc8 (21:11, run 21:27:50). No protocol file was committed after the last run started.
(2) The wording of S1a/S1b/S2/S3 is carried over unchanged from the P1 page (p1b_addendum.md@75bcd2b:4). So the S1–S3 text predates both the P1 and the P1b data.
(3) The C1 rule reuses the pre-registered R(a) thresholds (10 %, CI lower bound > 0). It runs on fresh seeds, and its protocol discloses the post-hoc choice.
(4) The paper is an unfinished draft: Discussion has 0 lines, and the Conclusion and Abstract are not written. Disclosure could still be added.
(5) The cell block_q1600 was already flagged by the D2 bug re-run (e973f6e, 10-19 18:43) before P1 ran. So the choice did not rest only on P1b.

Why the problem survives:
(a) Line 69 says "All statements", which includes C1. The C1 statement, cell and comparator were fixed at 21:09/21:11, after the P1b evaluation (sentinel 13:07; result note 4f91777 at 21:03). Those P1b data appear in the same paper: Table II and the 18.0 % report-only row at line 155. The C1 page says so itself: "the cell and the arms were chosen after seeing P1b's evaluation data".
(b) The S1–S3 text was written after the D2 screen. D2 used the same plant (BN4), the same q values {1600, 2000} and the same incident types, and the same IP-vs-N comparison (screen_D2_incidents.md:13-29). D2 data were produced 10-19 10:45 and committed 11:38. The P1 draft came at 13:38. This is disclosed only in p1_incident_information.md@0e8d49b §8, not in the paper.
(c) The P1b protocol and seed ranges were fixed after the P1 data. The changes respond to P1's verified limits: V103 lists the controller-family confound and the missing amber phase.
(d) The redesign matters for C1. C1's tested IP plan, p20_20_16_e4, is a PI law from G_PI. G_PI exists only because of the post-P1 change B3. So C1 tests a hypothesis shaped by two earlier rounds on this plant.
(e) The draft also departs from the P1b addendum's own promise, "P1 stays in the record as the earlier run ... Both are reported". The paper never names P1. It still uses a P1 number: "87 % (no amber)" at :193, from p1_result.md:81. The only trace of P1 is the "(P1b)" label in the Table II caption.

Severity: the rubric counts a false statement about pre-registration as critical, so it stays critical. Substantively, no headline number changes: per-study pre-registration and C1's fresh-seed test are valid. The fix is to reword lines 69 and 145, and to disclose D1/D2, P1, the post-P1 redesign and the post-P1b choice of the C1 cell. The finding group's facts hold. One small timing detail: the C1 draft commit a4e3e6d (21:09) also comes after the P1b result note 4f91777 (21:03).

Checks: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/PROV-F1-defend/timeline.sh (output timeline.out): git commit times of every D2/P1/P1b/C1 protocol version, sha256 of each version via git show, matched to page_sha256 and time in ~/work/phd/v5b1_runs/*_STARTED.json; result-note commit times; protocol commits after the last run start (none); /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/PROV-F1-defend/paper_disclosure_grep.sh (output paper_disclosure_grep.out): searched paper.qmd and pdftotext of paper.pdf for any disclosure of P1, D1/D2, earlier rounds or the post-hoc C1 choice; counted Discussion lines (0); Read paper.qmd:1-80 and :120-203 (the plan comment, Introduction, Protocol, Results); Read p1b_confirm_c1.md (whole), p1b_addendum.md (whole), p1_incident_information.md §7-8, screen_D2_incidents.md design lines; grep docs/decisions.md for V90-V129; read V102, V103, V105, V112, V114, V116, V122, V124 in full; git show 93ba655:v5b/p1b/family.py and 85f7d34:v5b/p1/family.py: confirmed p20_20_16_e4 is a PI-law id, available only through G_PI; grep of the result notes for the source of the 87 % figure (p1_result.md:81); Read the P1b result-note limits section and BASELINE_2026-10-20.md (evolution diagram and traceability table)

#### Verifier R1 impact: CONFIRMED / critical

Meaning: the paper says, at line 69 and again at line 145, that every statement was fixed before any data existed. The record shows four rounds on the same plant (BN4), the same two demands and the same two incident types: screen D2, then P1, then P1b, then C1. Each round's protocol was written after the previous round's results had been seen. Each round's own protocol was committed before that round's own data. So the claim holds for each study on its own, but it is false as the paper words it.

Impact. Nothing in the headline changes.
- S1a and S1b: P1 and P1b give the same verdicts (S1a FAIL; S1b PASS in the same two cells, slow_q2000 and block_q1600). Read this way, the P1 round is a replication that helps the paper.
- Table II: no number changes.
- C1: the test stays valid. Its 100 seeds are fresh, and its statement was approved at 21:11, before the run started at 21:27:50.

What must change in the paper:
1. Line 69, last sentence, and line 145, first sentence: rewrite them to say the statements were fixed per study. Name the D1/D2 screens and the P1 round.
2. Lines 145 and 187: say that the C1 cell and comparator were chosen after the P1b evaluation, because it was the only one of 4 cells where IP beat PI with an interval above zero (Table II, report-only row). C1's own protocol (line 36) requires this disclosure.
3. Disclose P1. The P1b addendum (line 9) says "Both are reported", and the paper never mentions P1, so the paper breaks its own protocol. The impact lens found two facts a reader needs:
   - In P1 (no amber, no PI-law plans), IP vs PI in this same cell was -0.7 % [-11.4, 12.9], while slow_q2000 was 6.9 % [2.3, 10.7]. The cell with a significant IP-vs-PI lead moved between the two rounds.
   - The plan that C1 confirms, p20_20_16_e4, belongs to G_PI. That is the set of PI-law plans added in P1b in response to P1's data (V103/V108), and it is absent from P1's action set. So the C1 win depends on a design change made after P1 was seen. C1 is a valid test of a hypothesis generated from the data, not a test of an a priori hypothesis.
4. P1 numbers appear in the paper without attribution:
   - Line 193 says the upper bounds ran "from 13.3 %". 13.3 is P1's slow_q2000 upper bound. P1b's range is 19.3-47.9 %, which matches the paper's own Table II, so line 193 contradicts Table II.
   - Line 197 says the emergency-stop share fell "from 87 % (no amber)". The 87 % is P1's share, from other seeds (500-599) and another action set, presented as if it were a within-study effect of amber.
5. The Discussion (line 199) is empty, so none of these caveats appears anywhere.

Severity. The rubric counts a false statement about pre-registration as critical, and the sentence is false as written: the C1 statement was written after the P1b data existed. The rendered PDF carries both sentences. I keep critical on that basis. In terms of numbers, this is a wording and disclosure fix (one paragraph, plus correcting line 193); no verdict and no Table II value moves. If the author rewords line 69 and line 145 to the per-study form, the remaining items (the P1 round, the post-hoc choice of the C1 cell, the P1 numbers) are major.

Failure points of this assessment:
- A charitable reader could take "the protocol" at line 145 to mean the protocol of each study. That reading does not rescue line 69 ("All statements"), which includes C1.
- I took "statements" to mean the formal S1/S2/S3/C1 statements. The descriptive (D) rows add a minor issue, not a critical one.

Checks: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/PROV-F1-impact/timeline.sh: protocol commits, result commits and run sentinels in time order. Output is timeline.txt in the same folder. Each protocol comes before its own run and after the previous round's result.; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/PROV-F1-impact/compare_p1_p1b.py: compares the S1 verdicts and the report-only IP-vs-PI rows of P1 and P1b. Verdicts are identical; the IP-vs-PI row moved from slow_q2000 (P1) to block_q1600 (P1b).; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/PROV-F1-impact/c1_plan_origin.py: the C1 IP plan p20_20_16_e4 is in P1b G_PI and is absent from P1's action set.; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/PROV-F1-impact/find_value.py: traced 13.3 % and 87 % to P1, not P1b (P1b S2 has no 13.3).; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/PROV-F1-impact/keys.py: structure-only summary of the result JSONs (no raw JSON printed).; pdftotext of papers/paper_1/paper.pdf into /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/PROV-F1-impact/paper.txt: the rendered PDF contains both false sentences and the 13.3 % and 87 % numbers.; grep of paper.qmd for P1, screen, D1/D2, 'chosen', 'after seeing': no disclosure found. grep of the protocols for the disclosure lines (p1b_confirm_c1.md:36, p1b_addendum.md:5-9, p1_incident_information.md:133-134). grep of docs/decisions.md for V103/V105/V108/V114-V116.

### B2. [major] COMETRIC: Pre-registered co-metrics (served throughput, TTT) missing; on fixed-window TTT S1b has no passing cell

Raised as major; verification: reproduce: CONFIRMED/major, defend: CONFIRMED/major, impact: CONFIRMED/major.

#### FU1-F2 (R1 FU1, major, missing-evidence): Pre-registered co-metrics (served throughput, TTT) are missing; on fixed-window TTT S1b has no passing cell

- **Description.** The protocol says 'Served throughput is co-headlined; TTT and the max queue are reported alongside' (p1_incident_information.md:85). CLAUDE.md defines TTT as fixed-window with unfinished vehicles counted to the window end, which is ttt_ctrl_vehh. The paper reports neither metric, and p1b_result.json has only per-arm medians, no paired comparisons. On fixed-window TTT at level 0.99375: S1b IP vs ID is 7.4 / 1.7 / 9.9 / 0.0 %, so no cell reaches 10 % and S1b FAILs. S1a also fails, with no a-cell for any L0 arm. C1 holds: 11.7 % [6.9, 14.0]. Paired in-window throughput favours IP: +48 [24, 84] veh/h (slow_q2000), +102 [56, 144] (block_q1600), +52 [12, 100] (C1). Reporting it would support the claim.
- **Evidence.**
  - docs/research/protocols/p1_incident_information.md:85
  - CLAUDE.md Method/Metrics: 'TTT always reported alongside (fixed window; unfinished vehicles counted to the window end)'
  - papers/paper_1/paper.qmd: no TTT or throughput anywhere (grep)
  - docs/research/results/p1b_result.json: only eval/table1_operating_map/*/arms/*/median_ttt_* and median_served_vph
  - FU1/drain_audit.out S1 verdicts per metric; FU1/served_check.out
- **Failure scenario.** A reviewer or examiner checks the pre-registration and finds that the co-headlined and alongside metrics are missing. On the project's own TTT definition, the S1b pass is not reproduced, so the S1b headline looks metric-selected even though the decision metric was fixed in advance.
- **How to test.** Re-run FU1/drain_audit.py and FU1/served_check.py. Add a Table II row for window TTT (and full TTT) and for paired served throughput, with an explicit note that only delay is decision-bearing.
- **Related claims.** FU1-C3, FU1-C7

#### FU1-F8 (R1 FU1, info, discrepancy): Unpaired median throughput in the notes points the wrong way

- **Description.** p1b_summary.md Table 1 (slow_q2000) lists served throughput of 1204 veh/h for ID and 1196 for IP. Read alone, IP looks worse. The paired median difference is +48 [24, 84] veh/h in IP's favour. If the paper adds throughput, it should report paired differences.
- **Evidence.**
  - docs/research/results/p1b_summary.md:63 (slow_q2000 row)
  - FU1/served_check.out
- **Failure scenario.** A reader takes the median rows at face value and concludes that IP reduces throughput.
- **How to test.** Re-run FU1/served_check.py.
- **Related claims.** 

#### FU1-F9 (R1 FU1, info, statistics): S1-level CI ends depend on the bootstrap draw

- **Description.** At level 0.99375 the CI ends are extreme percentiles, and they move with the bootstrap seed. The lower bound of the median paired delay difference ranged from 16.7 to 21.4 s across 3 seeds for block_q1600 IP vs ID; the official value is 21.40. My ratio-bootstrap rel CIs differ from the paper's by up to 1.3 points ([7.5, 31.3] vs [8.8, 31.4]). This could be method or RNG; I did not check v5b/d1/stats.py. No verdict changes, since all lower bounds stay well above 0.
- **Evidence.**
  - FU1/lcb_debug.py output
  - p1b_result.json eval/S1/per_cell_stats/block_q1600/IP_vs_ID diff_ci [21.40, 84.84]
- **Failure scenario.** The third digit of the CIs in Table II and in the text cannot be reproduced exactly by an independent bootstrap.
- **How to test.** Re-run FU1/lcb_debug.py with more seeds, or raise B.
- **Related claims.** FU1-C3

#### Verifier R2 reproduce: CONFIRMED / major

I rebuilt the core facts myself from the protocol, the paper, the run code and the raw run JSONs. I wrote my own run keys and my own bootstrap and did not import the repo's v5b package. The arms are right: my delay values match the paper exactly (ID vs PI -17.9/-1.8/-0.7/-2.1; IP vs ID 16.2/11.8/22.0/0.0; IP vs PI 4.5/7.4/18.0/-2.1; C1 16.2 % [7.3, 23.7], 41.4 s).

(1) Protocol p1_incident_information.md:85 says "Served throughput is co-headlined; TTT and the max queue are reported alongside". The run's base_page_sha256 (fed27bf6...) matches this file. Neither p1b_addendum.md nor p1b_confirm_c1.md overrides §5. (2) paper.qmd has no TTT and no throughput anywhere. It names delay as the only objective (line 93) and says the protocol was fixed in advance (line 145). The omission is not disclosed. (3) The repo JSON p1b_result.json holds served/TTT only as per-arm medians (median_served_vph, median_ttt_ctrl_vehh, median_ttt_full_vehh under table1_operating_map, per_q and runner_rows). It has no paired statistics for them. (4) ttt_ctrl_vehh is tts_system at the end of the control window, taken from sim start and including the origin queue (v5b/p1b/episode.py@93ba655:239). This matches the CLAUDE.md:69 definition.

(5) On window TTT at level 0.99375, IP vs ID is 7.4 / 1.7 / 9.9 / 0.0 %, exactly as the finding says. No cell reaches 10 %, so rule (a) fails and S1b does not pass. For S1a, no L0 arm has any a-cell. (6) C1 window TTT is 11.7 % [6.9, 14.0] (bootstrap seed 2; seeds 1 and 3 give [6.8, 14.1]). (7) Paired served throughput, IP minus reference, at 95 %: +48 [24, 84] (slow_q2000), +102 [56, 144] (block_q1600), +52 [12, 100] (C1). All reproduced exactly. At the S1 level the first two are [8, 100] and [36, 154]. (8) p1b_summary.md:63 lists the unpaired medians as ID 1204, IP 1196, the opposite sign to the paired difference. Confirmed. (9) F9: with BOOT_SEED 20261019 (v5b/p1/stats.py@93ba655:15) I get the official numbers exactly: block_q1600 diff_ci [21.40, 84.84], rel_ci [8.84, 31.38]; slow_q2000 rel_ci [5.84, 16.74]. Across 40 other bootstrap seeds, block_q1600 diff_lo ranges 16.68 to 21.40 (the official value is the maximum) and rel_lo 7.12 to 8.98. All lower bounds stay above 0, so no verdict changes.

Caveats the finding does not state, which lower the weight of 'S1b fails on TTT':
- block_q1600 window-TTT rel is 9.87 %, only 0.13 points under the bar.
- On full TTT, S1b passes: 10.3 % in slow_q2000 and 18.6 % in block_q1600.
- The protocol fixes delay as the only decision metric and says only 'reported alongside' for TTT. Applying the 10 % rule to TTT is therefore a post-hoc sensitivity check, not a pre-registered failure.
- Window TTT includes warm-up time, pre-incident time and free-flow time that all arms share, so its rel is diluted compared with delay.

The headline on delay is unchanged. The missing co-headlined and alongside metrics are a real, undisclosed deviation from protocol §5. Severity: major.

Checks: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/COMETRIC-reproduce/cometric.py (output cometric.out): own key construction and own bootstrap; S1a/S1b rule (a)/(b) on delay, window TTT and full TTT; paired served throughput; C1 recomputation; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/COMETRIC-reproduce/ci_seed_spread.py (output ci_seed_spread.out): official BOOT_SEED reproduction plus 40-seed spread of the CI ends; git archive 93ba655 and e7dd561 into the scratch dir; read episode.py metric code, analysis.py evaluate/cell_runs, p1/stats.py paired/rule_R; sha256 check of the protocol against result.json base_page_sha256; grep of the addendum and C1 protocol for metric overrides; grep of paper.qmd for TTT/throughput/served/queue/pre-registration wording; key-path scan of docs/research/results/p1b_result.json and p1b_c1_result.json for served/TTT fields; read p1b_summary.md:60-63

#### Verifier R2 defend: CONFIRMED / major

I tried to defend the paper as its author would. The main problem still stands. The approved P1 protocol (commit 7da4ab4, 2026-10-19, before any data; sha256 fed27bf... matches the base_page_sha256 that the P1b run recorded) says at line 85: "Served throughput is co-headlined; TTT and the max queue are reported alongside." The P1b addendum does not change this. In the paper, served throughput and TTT do not appear anywhere. The max queue appears only as one qualitative sentence (paper.qmd:197). The paper plan comment (paper.qmd:31-59, V121) has no row for either metric. The P1b source notes do not report TTT at all (p1b_result.md and p1b_summary.md: 0 hits). The paper does not disclose this deviation.

Context I found that limits the finding:
(1) The draft is incomplete: Abstract, Discussion and Conclusion are empty, and the venue limit is 6 pages. A disclosure could still be added, but none is planned.
(2) The C1 protocol (p1b_confirm_c1.md:15, 29-31) names delay as the only metric. Its descriptive list does not include throughput or TTT. So for C1 nothing was omitted.
(3) "On fixed-window TTT S1b has no passing cell" is numerically correct: 7.4 / 1.7 / 9.9 / 0.0 %. But it is not a pre-registered test, because the protocol applies the S1 rule only to delay. The window TTT also cuts off the drain after the control period, and most of the IP-ID difference lies there: at window end, ID has a median of 12-25.5 more vehicles in the system. Full TTT is the complete integral, equal to delay plus about 48-52 s of free-flow time per vehicle. On full TTT, S1b passes in the same two cells: slow_q2000 10.3 % [5.1, 14.4] and block_q1600 18.6 % [6.0, 25.5]. Note that slow_q2000 is only just above 10 %.
(4) Paired served throughput favours IP: +48 [24, 84] veh/h (slow_q2000), +102 [56, 144] (block_q1600), +52 [12, 100] (C1). C1 also holds on window TTT: 11.7 % [6.8, 14.1].

So the failure scenario "S1b looks metric-selected" is overstated. Delay was fixed as the decision metric before any data, and the complete co-metrics support the headline. The headline survives, so the severity is not critical. It stays major: the deviation from the pre-registered reporting plan is undisclosed, and a reviewer holding the protocol would ask for it to be fixed. The project's own TTT convention (CLAUDE.md; also the window TTT used in p1_result.md Table 1) does not reproduce the S1b pass, so the paper should report both TTT variants and state that only delay decides.

F8 (info) is confirmed. The unpaired medians in p1b_summary.md:62 are ID 1204 and IP 1196 veh/h, while the paired difference is +48 [24, 84]. This affects only the notes, not the paper.

F9 (info) is mostly refuted as a reproducibility problem. The official bootstrap uses a fixed seed (BOOT_SEED = 20261019, v5b/p1/stats.py@93ba655:15) and a ratio method that the code documents (stats.py@93ba655:4-5). My own reimplementation with that seed reproduces the official numbers exactly: diff CI [21.40, 84.84] and rel CI [8.8, 31.4] for block_q1600, and [5.8, 16.7] for slow_q2000. With another seed I get a lower bound of 17.0 s instead of 21.4 s, i.e. rel [7.4, 31.3]. This is ordinary Monte Carlo error at the 0.3125 % tail; no verdict changes. Also, FU1 named the wrong file: P1b uses v5b/p1/stats.py, not v5b/d1/stats.py.

Checks: Read the COMETRIC group from round2_input.json; Read protocol section 5 and 6 text; git show 7da4ab4 to confirm line 85 predates the data; sha256 of the protocol matches result.json base_page_sha256; Grepped paper.qmd, p1b_result.md, p1b_summary.md, p1b_c1_summary.md, p1_result.md, docs/decisions.md and the protocols for TTT, throughput and served; Read the whole paper.qmd draft, including the plan comment and the empty sections; git archive of 93ba655 and e7dd561 into /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/COMETRIC-defend/code_93ba655 and code_e7dd561; read v5b/p1b/episode.py metric code, v5b/p1b/analysis.py S1 code, v5b/p1/stats.py bootstrap; Wrote and ran my own recomputation from the raw run JSONs (v108 eval seeds 7400600-699, v114 C1 seeds 7400700-799): /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/COMETRIC-defend/cometric_check.py; output in /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/COMETRIC-defend/cometric_check.out and cometric_check.json; Checked that the arm-key mapping is right: my code with the official bootstrap seed reproduces the result.json S1b delay statistics exactly; Read the p1b_summary.md Table 1 rows (lines 60-64) to check F8

#### Verifier R2 impact: CONFIRMED / major

The core fact holds. Protocol §5 (p1_incident_information.md:85) says: "Served throughput is co-headlined; TTT and the max queue are reported alongside." The P1b addendum keeps that section unchanged, and no V# decision in docs/decisions.md removes it. The paper never mentions served throughput or TTT (grep of paper.qmd). The results notes do report both, as unpaired medians, so the gap is between the notes and the paper. Because the paper says it follows a pre-registered protocol (paper.qmd:145), leaving out a co-headlined metric without saying so is an undisclosed deviation that a reviewer would ask to fix. That is major.

What does NOT change: the pre-registered verdicts and the Table II numbers. The S1 rules and C1 are fixed on door-to-door delay: "Primary: door-to-door delay" (p1_incident_information.md:85) and "Metric: door-to-door delay" (p1b_confirm_c1.md:15). The paper also names delay as the objective (paper.qmd:93). My own recomputation on delay reproduces S1a FAIL, S1b PASS (11.8 % and 22.0 %) and C1 16.2 % [7.3, 23.6]. On full TTT, which per seed is almost an affine function of delay because every arm generates the same vehicles, S1b also PASSes (10.3 % [5.1, 14.4], 18.6 % [6.0, 25.5]). Applying the S1 rule to window TTT is post hoc, on a metric that does not decide anything. So the FU1 phrase "S1b FAILs" describes a sensitivity result, not a pre-registered verdict, and it is not critical.

What DOES change:
1. Table II or the text needs rows for paired served throughput and for TTT, plus one sentence saying that only delay decides the verdicts.
2. On fixed-window TTT [0, 940 s], which includes the origin queue (d1/sumo_runner.py@93ba655:142; p1b/episode.py@93ba655:239), IP vs ID is 7.4 / 1.7 / 9.9 / 0.0 %. No cell reaches 10 %, so the S1b-style rule would not pass. The crawl 1600 cell (9.9 %) misses by a hair.
3. In the two passing S1b cells, about 67 % (crawl 1600) and 83 % (slow 2000) of the mean paired full-TTT gain comes after the control window. In that drain phase the incident is cleared and the meter is all-green (p1b/episode.py@93ba655:238-248). The gain comes from IP leaving fewer vehicles in the system at the window end (paired 12 and 25.5 fewer) and from higher served throughput (+48 and +102 veh/h). The paper only says the run "continues until the network is empty" (paper.qmd:110). It never says that the drain is uncontrolled or that most of the S1b gain accrues there.
4. Reporting throughput as paired differences helps the claim, but unpaired medians would mislead (slow 2000: ID 1204 vs IP 1196 veh/h).

So the headline survives, and the omission plus the weaker window-TTT result change the interpretation and the completeness of the paper. That is major, not critical. Member F9 is confirmed as RNG-only: the run's bootstrap seed 20261019 reproduces [21.40, 84.84] and [8.8, 31.4] exactly. Other seeds give rel lower bounds of 7.3–8.7 %, and no verdict changes, so info is correct.

Checks: Read round2_input.json group COMETRIC (members FU1-F2, F8, F9; claims FU1-C3, FU1-C7); Read protocol §5-§6 (p1_incident_information.md), the full p1b_addendum.md, and the metric line in p1b_confirm_c1.md; Grep of paper.qmd for TTT, throughput, served and queue; read paper.qmd lines 85-203; Grep of docs/decisions.md and the results notes for co-metric decisions and reporting; git show 93ba655:v5b/p1b/episode.py, v5b/p1/episode.py, v5b/d1/sumo_runner.py and v5b/p1/stats.py (metric definitions, drain, bootstrap convention); /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/COMETRIC-impact/cometric_impact.py -> cometric_impact.out (own bootstrap: S1a, S1b, IP vs PI and C1 on delay, window TTT, full TTT, served, n_system_ctrl_end; both views); /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/COMETRIC-impact/drain_share.py -> drain_share.out (window and post-window split of the paired TTT gain); /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/COMETRIC-impact/boot_seed_check.py -> boot_seed_check.out (CI sensitivity to the bootstrap RNG seed)

### B3. [major] CTRL-F1: S1b magnitudes depend on a fragile/dominated ID plan chosen by the pooled-median rule

Raised as critical; verification: reproduce: CONFIRMED/major, defend: CONFIRMED/major, impact: CONFIRMED/major.

#### CTRL-F1 (R1 CTRL, critical, invalid-comparison): S1b's block_q1600 pass (Table II 22.0 %) depends on a Pareto-dominated ID chosen by the pooled-median rule

- **Description.** At q1600, the pre-registered pooled (slow+block) median picks ID = f40_10. On the tuning seeds this plan ranks 10th in slow and 7th in block, and it is beaten in both per-type medians by p70_40_10_e4 and p20_20_12_e4, and in both per-type means by 3 actions. The median of a two-mode pooled sample lands between the modes. With two equally plausible pooling rules computed on the tuning seeds only, the evaluation result changes. Pooled mean: S1b FAILS (no cell meets (a)). Mean of per-type medians: ID = p20_20_14_e4, S1b passes only via slow_q2000, IP vs ID in block_q1600 falls to 2.8 %, and ID beats always-on PI there by 16.3 %. That would turn the crawl-1600 story from 'type pays' into 'presence pays'. Against each plan that dominates f40_10, the block_q1600 (a) test fails (12.5 % with CI including 0; 8.6 %). The verdict as computed under the protocol is correct; my own code reproduces S1a FAIL, S1b PASS and every Table II S1 number. The headline is fragile to a weak ID baseline.
- **Evidence.**
  - v5b/p1b/analysis.py@93ba655:139-140 pooled = per['slow'] + per['block']; ID = best_by_median(pooled, A_)
  - /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/CTRL/out/pareto_id.txt (f40_10 slow 204.5 / block 244.7; p70_40_10_e4 203.4 / 239.4; p20_20_14_e4 205.7 / 224.9)
  - /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/CTRL/out/s1_sensitivity.json
  - /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/CTRL/out/id_alt_eval.txt
- **Failure scenario.** A reviewer tunes ID by mean delay, or by the average of the per-type medians, and finds the 'type adds 22 %' crawl-1600 result shrinks to about 3 %, and that S1b fails or rests on one cell.
- **How to test.** Re-run /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/CTRL/scripts/s1_sensitivity.py. Report S1 under the alternative pooling rules as a disclosed sensitivity row, and state that the pooled-median ID is Pareto-dominated on the tuning seeds.
- **Related claims.** C27, C46, C47

#### HEADLINE-F1 (R1 HEADLINE, major, unsupported-interpretation): S1b magnitudes depend on which near-tied presence-only plan (ID) won tuning; the CIs cover only evaluation-seed noise

- **Description.** Meaning: S1b says that knowing the incident type adds 11.8 % (slow_q2000) and 22.0 % (block_q1600) over knowing only presence. Both numbers compare two specific plans that were each picked as a minimum over 120 actions on 40 tuning seeds, so they inherit selection noise. Verification (derived, descriptive, not a protocol statistic): I resampled the tuning seeds 1,000 times, re-selected IP and ID over the fixed A(q), and scored the result on the 100 evaluation seeds. The tuned (IP, ID) pair came back in only 15-23 % of resamples per cell. The median re-selected IP-vs-ID rel is 4.4 % in slow_q2000 (5-95 %: -3.9 to 11.8; the reported 11.8 % sits at the 95th percentile) and 12.5 % in block_q1600 (-2.9 to 23.1). The tuning runner-up for ID gives much smaller gains: in slow_q2000, ID = p70_40_10_e4 (384.6 s vs 381.3 s in tuning) gives 3.4 % [-0.3, 7.2]; in block_q1600, ID = p20_20_14_e4 gives 2.8 % [0.0, 5.9]. The pre-registered S1b verdict is computed correctly and still passes in about 74 % of resamples (point rule plus diff CI), so the verdict is moderately robust. The magnitudes and the identity of the passing cells are not. The paper reports the intervals as if they described the value of type information in general, but they describe only these tuned plans.
- **Evidence.**
  - paper.qmd:155 'knowing the type added 11.8 % [5.8, 16.7] ... and 22.0 % [8.8, 31.4]'
  - tuning medians: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/HEADLINE/tune_out.json (top3_ID, top3_IP)
  - /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/HEADLINE/selection_bootstrap_out.json
  - /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/HEADLINE/selection_sensitivity.py output
  - selection rule: v5b/p1b/analysis.py:134-140@93ba655 (fit_switch, best_by_median)
- **Failure scenario.** A reader takes 'type pays 12-22 %' as the value of type information. A re-tune on other 40 seeds, which is equally valid under the protocol, would likely report about 4 % in slow_q2000, and S1b would fail in about 1 resample in 4.
- **How to test.** Run selection_bootstrap.py (M = 1000) and selection_sensitivity.py. To make this stronger, re-select G_PI and N inside each resample too (this needs switch runs from other N, which do not exist). Report the selection-stability result, or state in the paper that the CIs are conditional on the tuned plans.
- **Related claims.** paper.qmd:155 S1b passes, paper.qmd:175 Table II IP vs ID

#### FU2-1-F1 (R2 FU2, major, unsupported-interpretation): S1b sentence credits 'type knowledge' with gains that depend on the undisclosed ID tuning rule and on the drain convention

- **Description.** S1b PASS reproduces exactly under the pre-registered pooled-median ID rule. The magnitudes in the sentence are not information effects as written.

Crawl-1600 (22.0 %): the reference ID f40_10 is beaten on both per-type tuning medians by two plans. Type-blind alternatives fitted on the tuning seeds only give:
- 2.8 % for p20_20_14_e4 (pooled-mean and mean-of-medians rules);
- 0.0 % for p20_20_16_e4 (minimax rule).

Slow-2000 (11.8 %):
- the arm medians differ by only 6.0 %;
- on window TTT the gain is 1.7 %;
- 83 % of the TTT gain accrues after 940 s, and 43 % of that is arm-specific.

S1b by alternative rule:
- pooled mean: FAIL;
- mean of type medians: PASS via slow_q2000 only, which is the drain-dependent cell;
- minimax: PASS via slow_q1600 and slow_q2000.

This consolidates CTRL-F1, DRAIN, COMETRIC and HEADLINE-F6. The ID rule followed the protocol, so this is not a deviation.
- **Evidence.**
  - FU2-1/id_rule_sens.out
  - FU2-1/s1_indep.out
  - FU2-1/drain_nleft.out
  - v5b/p1b/analysis.py@93ba655:136-141,354
  - docs/research/protocols/p1_incident_information.md:36,43
  - paper.qmd:118,155
- **Failure scenario.** A reviewer chooses the type-blind plan by mean delay. The crawl-1600 'type adds 22 %' becomes about 3 %, and S1b fails or rests only on the drain-dependent slow-2000 cell.
- **How to test.** Re-run FU2-1/id_rule_sens.py and s1_indep.py. Fix in the paper: state the ID rule, add a sensitivity row for the alternative rules, and report window TTT, served throughput and the release convention.
- **Related claims.** C66, FU1-C3, C69

#### FU2-1-F2 (R2 FU2, major, unsupported-interpretation): S1a clause 'no detected gain of 10 % or more' holds only for the pooled-median ID; the FAIL itself is robust

- **Description.** With an ID chosen type-blind on the tuning seeds by pooled mean or by mean of per-type medians (p20_20_14_e4), presence alone beats FB by 13.7 % and PI by 16.3 % in crawl-1600. With minimax (p20_20_16_e4) the gains are 15.9 % and 18.0 %. In both cases the diff LCB is above 0 at level 0.99375, and (a) holds against every L0 arm in both views. S1a still fails, but only through (b) in slow_q1600 (ID vs PI -16.2 % / -29.9 %). The pre-registered ID is the always-on law itself (FB at q1600, PI at q2000), so it differs from those arms only before onset. In crawl-1600, the choice of rule moves the gain between 'presence pays' and 'type pays'. The paper discloses neither point.
- **Evidence.**
  - FU2-1/id_rule_sens.out (block_q1600 and slow_q1600 rows per rule)
  - FU2-1/s1_indep.out (S1a FAIL on delay, window TTT, full TTT)
  - result.json tune.arms 1600 ID f40_10 = FB, 2000 ID p20_20_14_e4 = PI
  - protocol p1_incident_information.md:101
- **Failure scenario.** A reader concludes that presence information is worthless against strong control. A type-blind plan tuned with a different but reasonable rule gets a detected gain of about 16 % over PI in the lane-crawl 1600 cell.
- **How to test.** Run FU2-1/id_rule_sens.py and read the block_q1600 'ID vs L0' lines. In the paper, state that S1a fails through (b) as well as through (a), and give the ID-rule sensitivity.
- **Related claims.** C64, FU1-C4

#### Verifier R1 reproduce: CONFIRMED / major

Meaning: in P1b, ID ("presence only") is the one action from the set A(q) of 120 actions that has the lowest median delay over the slow and crawl (block) tuning runs together. At 1600 veh/h this rule picks f40_10, which switches from N = c1800 to the feedback plan f40_10 at onset. f40_10 is not the best plan for either incident type taken alone: other plans beat it on both per-type medians. So the 22.0 % "type pays" figure in crawl 1600 compares IP with a weak presence baseline.

I re-derived everything from the raw run files with my own code, without importing v5b. The re-derived N(q), G_PI(q), |A| = 120, IP and ID all match result.json, and no tuning runs are missing. I also reproduced the S1b and Table II numbers exactly: slow_q1600 16.2 %, slow_q2000 11.8 % [5.8, 16.7], block_q1600 22.0 % [8.8, 31.4], block_q2000 0.0 %, and the ID vs PI row -17.9 / -1.8 / -0.7 / -2.1. Every fact the finding cites holds as stated:
- f40_10 ranks 10th in slow and 7th in block by per-type median.
- It is dominated on both per-type medians by p70_40_10_e4 and p20_20_12_e4, and on both per-type means by those two plus p20_20_14_e4.
- With ID chosen by pooled mean, S1b FAILS: no cell meets (a). This rule also changes ID at q2000, to p70_40_10_e4, which is near-tied with the current ID on pooled mean (397.43 vs 397.80).
- With ID chosen by the mean of the per-type medians (p20_20_14_e4 at q1600), S1b passes only through slow_q2000. IP vs ID in block_q1600 drops to 2.8 %, and ID vs always-on PI there is 16.3 %.
- With ID set to either dominating plan, block_q1600 fails (a): 12.5 % with the diff CI covering 0, and 8.6 % (below 10 %).

For HEADLINE-F1, my own resampling of the tuning seeds (M = 1000) gives:
- S1b passes in 74.0 % of resamples, the same as reported;
- the tuned (ID, IP) pair comes back in 13-22 % of resamples (reported 15-23 %);
- the 5-95 % range of the re-selected rel is [-3.9, 11.8] in slow_q2000 (identical to the report) and [-3.5, 23.1] in block_q1600 (reported [-2.9, 23.1]). The medians are 3.5 % and 10.4 %, against the reported 4.4 % and 12.5 %; the difference is resampling noise.

One small mismatch: the 2.8 % row has a CI of [-0.1, 5.9] at the S1 level, against the reported [0.0, 5.9].

Why major, not critical. The pooling rule is pre-registered: protocol p1_incident_information.md lines 36 and 43, present at the run commit 93ba655 and approved 2026-10-19, before the P1b evaluation. The verdict is computed correctly under that rule. C1 tests IP vs PI and does not involve ID, so it is unaffected. S1a still fails under the alternative ID. Under that ID, block_q1600 meets (a) against every L0 arm, but slow_q1600 ID vs PI is -16.2 %, which breaks (b). So the "presence pays" reading holds for one cell only and is not an S1a pass. S1b passes under 2 of the 3 rules and in 74 % of resamples. What does not hold is the size of the effect and which cells pass: the 22.0 % crawl-1600 number depends on a dominated ID. The paper does not disclose the ID tuning rule, any sensitivity row, or that its CIs are conditional on the tuned plans (paper.qmd lines 118, 145, 155, 175). A reviewer would ask for that disclosure; the pre-registered headline still stands.

Checks: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/CTRL-F1-reproduce/s1b_id_check.py: re-derives N, G_PI, A(q), IP and ID from the raw tuning runs in v108/runs, plus ranks, dominators and S1b under the protocol, pooled-mean, mean-of-type-medians and dominator ID rules (both views, B=20000, level 0.99375). Output: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/CTRL-F1-reproduce/out/s1b_id_check.txt and /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/CTRL-F1-reproduce/out/s1b_id_check.json; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/CTRL-F1-reproduce/selection_bootstrap_check.py (M=1000): re-selects ID and IP on resampled tuning seeds and scores them on the evaluation seeds. Output: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/CTRL-F1-reproduce/out/selection_bootstrap_check.txt; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/CTRL-F1-reproduce/alt_id_s1a_check.py: ID (f40_10 or p20_20_14_e4) vs each L0 arm in the q1600 cells. Output: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/CTRL-F1-reproduce/out/alt_id_s1a_check.txt; git archive 93ba655 into /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/CTRL-F1-reproduce/code_93ba655; read analysis.py fit_switch, cell_runs, evaluate, s1_decision; p1/stats.py paired, rule_cell, rule_R; p1/family.py best_by_median; p1b/episode.py run_key; git diff 93ba655 HEAD and the working tree for analysis.py, family.py, stats.py: empty; grep of the protocols p1_incident_information.md (also at 93ba655) and p1b_confirm_c1.md for the ID rule and C1's comparison; jq on v108/result.json: code_commit 93ba655 with code_dirty false, tune.arms, A_size, eval.cells n_seeds = 100; paper.qmd lines 118, 145, 155 and 164-182 (Table II)

#### Verifier R1 defend: CONFIRMED / major

Meaning: ID is the controller that knows when an incident is on but not its type. Because it does not know the type, the protocol tunes it once on all incident runs pooled together (slow and block, 80 runs per action) and picks the action with the lowest median of that pooled sample. S1b ("the type pays") then compares the per-type plan IP with this ID, one cell at a time. The finding says the plan this rule picks at q=1600 (f40_10) is worse than two other actions in both incident types, so the 22.0 % "type gain" in crawl-1600 is mostly measured against a weak baseline.

Best defence and what is left of it:
(1) The rule was pre-registered and was run as written. It is in protocol p1_incident_information.md:36 and :43, approved V99 at 7da4ab4 (2026-10-19). The page hash fed27bf6cb2f at 93ba655 matches result.json base_page_sha256. The rule is implemented in v5b/p1b/analysis.py@93ba655:134-140, and that file has no diff to HEAD. The same rule tunes every arm that does not know the type (FX, FB, PI, AD, ID). My own code reproduces ID, IP, S1b PASS and 22.0 % / 11.8 %. So the verdict as computed is correct. This defence holds.
(2) The S1b verdict is fairly robust. I computed three other selection rules on the tuning seeds only. S1b still passes under the average of the two per-type medians (pass via slow_q2000), under the worse of the two per-type medians (via slow_q1600 and slow_q2000), and under the mean when it is used for both ID and IP (via slow_q1600, 26.4 %). The tracer's "pooled mean: S1b FAILS" mixes a mean-tuned ID with a median-tuned IP, so that part is overstated. In 1,000 resamples of the tuning seeds, S1b passes in 76 %. S1a still FAILS under every alternative ID rule with the pre-registered L0 arms: (a) now holds in block_q1600, but (b) fails, because ID loses to PI by 16.2 % in slow_q1600. So the tracer's "presence pays" overstates the effect on the verdict. C1 (IP vs PI) does not involve ID at all.
(3) Defences that fail. The pooled mean also uses no type labels, yet it does not pick f40_10. Being dominated in both per-type medians can be seen on tuning data without knowing the type at deployment, so a controller blind to the type could have chosen a dominating plan. The pooled-median objective does not match the per-cell median that the evaluation scores. The tuned f40_10 ranks 10th (slow) and 7th (block) by per-type median. It is dominated by p70_40_10_e4 (slow 203.4 / block 239.4 s) and by p20_20_12_e4 (202.5 / 242.3 s). Their pooled medians (226.3 and 219.8) are higher than f40_10's 211.6. This happens because the pooled median sits in the overlap of the two type samples: 62 % of the slow runs and 38 % of the block runs lie below it.

Consequences:
- Under every alternative rule, IP vs ID in block_q1600 falls from 22.0 % to 0.0-2.8 %.
- Against the two dominating plans, block_q1600 fails (a): 12.5 % with a diff CI of [-7.9, 56.4] s, and 8.6 %.
- The paper's sentence "Against always-on PI, ID was never better (-17.9 to -0.7 %)" (line 155) becomes +16.3 % in crawl-1600 under the alternative ID (p20_20_14_e4).
- The paper does not state the selection rule (line 118 says only "All arms are tuned on 40 tuning seeds"). It does not disclose this sensitivity, and its Discussion/Limitations section is empty.

Severity: the problem survives, so CONFIRMED. I rate it major, not critical, because the pre-registered numbers are correct and the S1a, S1b and C1 verdicts survive. What does not survive is the magnitudes, which cells pass, and the crawl-1600 reading that type, not presence, pays.

HEADLINE-F1: reproduced. In my resamples the tuned (IP, ID) pair comes back in only 14-20 % of cases. The median re-selected rel is 12.5 % in block_q1600 and 3.4 % in slow_q2000. One caveat: picking the best plan on bootstrap resamples (about 25 unique seeds out of 40) somewhat overstates how unstable the choice is, so treat this as descriptive. The CIs are conditional on the tuned plans, as is usual for tune-then-test designs, and the paper's wording ("knowing the type added...") generalises beyond those plans.

Further finding (new, not tested on outcomes): the same pooled-median problem affects the C1 comparator. On the tuning seeds, PI at q1600 (p70_120_8_e4: slow 189.4 / block 293.4 s) has six PI plans that beat it in both per-type medians, for example p40_40_10_e4 at 186.6 / 250.3 s. Those plans have no always-on evaluation runs, so I could not measure the effect on C1.

Checks: git log/show of docs/research/protocols/p1_incident_information.md (7da4ab4, 0e8d49b, 93ba655) and its sha256 against result.json; git diff 93ba655 HEAD on v5b/p1b/analysis.py and v5b/p1/family.py; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/CTRL-F1-defend/id_defend.py: own json+numpy re-selection of ID/IP over the 120 actions on the tuning seeds 7400300-339; per-type ranks, dominators, 4 selection rules; S1b on eval seeds 7400600-699 at level 0.99375, B=20000, both views; output in out/id_defend.txt and out/id_defend.json; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/CTRL-F1-defend/s1a_alt.py: S1a under the alternative ID rules, with the pre-registered L0 arms and with re-tuned L0 arms (arms without evaluation runs are excluded and flagged); output in out/s1a_alt.txt; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/CTRL-F1-defend/sel_boot.py: M=1000 resamples of the tuning seeds, re-selecting ID and IP and scoring them on the eval seeds; S1b pass share; output in out/sel_boot.txt; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/CTRL-F1-defend/l0_dominance.py: per-type-median dominance of the tuned FX/FB/PI on the tuning seeds; output in out/l0_dominance.txt; grep of paper.qmd, p1b_addendum.md, p1b_confirm_c1.md, decisions.md and the p1b results notes for any disclosure of the pooled rule, dominance or sensitivity (none found)

#### Verifier R1 impact: CONFIRMED / major

Meaning. ID is the meter that knows an incident is on but not its type. It must use one plan for both incident types. The protocol picks that plan, and every always-on arm (FX, FB, PI, AD), by the lowest median delay over the slow and block tuning runs taken together. IP picks one plan per type. At q1600 the pooled median picks f40_10, a plan that is worse in both types than other type-blind plans. So part of the 22.0 % "type pays" gain in crawl 1600 is really the cost of this tuning rule, not the value of knowing the type.

Core fact. I checked it with my own code from the raw v108 runs (code 93ba655 on every run; analysis.py and family.py are unchanged at HEAD). With the protocol's bootstrap seed 20261019 my recomputation gives every arm exactly and reproduces the Table II S1 rows: IP vs ID 16.2 / 11.8 [5.8, 16.7] / 22.0 [8.8, 31.4] / 0.0, ID vs PI -17.9 / -1.8 / -0.7 / -2.1, IP vs PI 18.0 in crawl 1600. On the tuning seeds f40_10 ranks 10th in slow and 7th in block. Two plans have lower medians in both types: p20_20_12_e4 (202.5/242.3 s) and p70_40_10_e4 (203.4/239.4 s), against 204.5/244.7 s for f40_10. Selection noise does not explain this, because the weakness holds on the 100 evaluation seeds too. Medians in slow/block: f40_10 202.9/257.9 s; p20_20_12_e4 198.6/230.7; p70_40_10_e4 183.5/229.6; p20_20_14_e4 199.6/212.8. The rule itself drives the choice: in tuning resamples the pooled median still prefers f40_10 over each better plan 63-80 % of the time.

What changes in the paper.
(1) Table II, row IP vs ID, crawl 1600: the bold 22.0 becomes 2.8 [-0.1, 5.9] with ID chosen by the mean of per-type medians, 8.6 [5.1, 13.7] with ID = p20_20_12_e4, and 12.5 [-3.9, 22.8] with ID = p70_40_10_e4. Under none of these rules is the entry bold. Slow 1600 changes from 16.2 to 11.5 / 12.7 / 1.2, still never significant.
(2) Table II, row ID vs PI, crawl 1600: -0.7 becomes +16.3 [4.8, 26.9] with the mean-of-medians ID. That ID then meets condition (a) against all five always-on arms in that cell (N 29.5, FX 27.6, FB 13.7, PI 16.3, AD 20.4).
(3) paper.qmd:155. "S1a fails: knowing only that an incident is on gave no detected gain of 10 % or more" and "ID was never better [than PI] (-17.9 to -0.7 %)" are true only for the pre-registered ID. The S1a verdict still FAILS under the alternative, but for a different reason: condition (b) fails in slow 1600 (ID vs PI -16.2 % [-29.3, -5.9]). "Type added ... 22.0 %" does not hold under any alternative I tested.
(4) Fig. 2: the ID bars at q1600 depend on the rule.

What does not change.
- The pre-registered verdicts S1a FAIL and S1b PASS.
- Every Table II number as computed under the protocol.
- C1 (paper.qmd:187). C1 is IP vs PI, and its cell was chosen from the IP vs PI row (p1b_confirm_c1.md:5), not from S1b.
- The S1b PASS verdict is fairly robust when an alternative rule is applied consistently. It still passes through slow 2000 (11.8 %) under the mean of per-type medians and with either better ID plan. With mean tuning for both ID and IP it passes through slow 1600 (26.4 % [14.2, 34.6]).

Correction to the tracer: "pooled mean: S1b FAILS" holds only when ID is tuned by mean while IP stays tuned by median.

Severity. No pre-registered verdict or protocol-computed number is wrong, and the rule was pre-registered (p1_incident_information.md:36,43 at ee3ce1e, 2026-10-19, before the P1b runs). So this is not critical. It is major because:
- the crawl-1600 "type pays 22 %" and the S1a wording do not survive any reasonable alternative rule;
- in that cell a presence-only plan gets about as much over PI (16.3 %) as IP does (18.0 %);
- the paper never discloses the pooled-median tuning rule ("pool" does not appear in paper.qmd).
A reviewer would ask for a disclosed sensitivity row and reworded text.

Further finding (info). The same mechanism affects always-on PI at q1600. p70_120_8_e4 is beaten in both types on the tuning seeds by 6 PI plans; the best of them, p70_70_10_e4, has 172.6/255.1 s against 189.4/293.4 s. No always-on evaluation or C1 runs exist for those plans. As a stand-in I used the switch runs that apply the PI plan from onset; their medians match always-on within 0.4 s, but single seeds differ by about 30 s. With that stand-in, IP vs p70_70_10_e4 in crawl 1600 is 21.3 % [7.4, 27.1], so the PI-side concern does not appear to threaten IP vs PI or C1 (not proven).

Checks: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/CTRL-F1-impact/load.py (raw runs -> cache.json; key==filename and no k/d/c/fa/rep/rs/vsl filters); /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/CTRL-F1-impact/impact.py -> impact_out.json (re-tune all arms under 3 pooling rules; S1a/S1b both views; Pareto dominators); /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/CTRL-F1-impact/key_rows.py -> key_rows_out.txt (protocol bootstrap seed 20261019, level 1-0.05/8); /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/CTRL-F1-impact/extra.py -> extra_out.txt (eval medians of ID candidates; tuning bootstrap of rule stability); /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/CTRL-F1-impact/mean_consistent.py -> mean_consistent_out.txt; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/CTRL-F1-impact/pi_check.py, pi_tune_rel.py, pi_proxy.py -> pi_*_out.txt; git blame/log of docs/research/protocols/p1_incident_information.md lines 36,43; git diff 93ba655 HEAD on v5b/p1b/analysis.py, family.py (empty); grep of paper.qmd for S1/pool/type statements; read p1b_confirm_c1.md rationale; listed C1 v114 run controllers

### B4. [major] CTRL-F2: C1 reference PI is Pareto-dominated and on grid edges; tuned arms on grid edges undisclosed

Raised as major; verification: reproduce: CONFIRMED/major, defend: CONFIRMED/minor.

#### CTRL-F2 (R1 CTRL, major, hidden-assumption): The C1 comparator (always-on PI at q1600) is Pareto-dominated on the tuning seeds and sits on two upper grid edges

- **Description.** PI = p70_120_8_e4 has per-type tuning medians of slow 189.4 and block 293.4. Six PI laws are lower in both: p70_70_10_e4 has 172.6 / 255.1, and the pooled mean and the mean of per-type medians both pick it. The chosen point is at K_P = 70 (max) and K_I = 120 (max), and the surface is still decreasing at that corner. Papageorgiou 2008's count-based merge control (§3) reports K_R >= 300 h^-1 as virtually equivalent, while the grid tops at 120 (plant scales differ; indicative only). On P1b evaluation seeds, IP still beats the available alternatives: 14.4 % [6.6, 25.3] against always-on p70_70_8_e4, and 15-21 % against N->p70_70_10_e4 / p20_40_10_e4 (proxies with N before onset). C1 probably survives in sign, but 'tuned always-on PI-ALINEA' overstates how strong the comparator is.
- **Evidence.**
  - /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/CTRL/out/pareto_all.txt
  - /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/CTRL/out/pi_surface.txt
  - /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/CTRL/out/pi_objective.txt
  - /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/CTRL/out/c1_comparator.txt; out/pi_dominators.txt
  - result.json tune.grid_edges_report_only['1600'].PI = ['K_P=70','K_I=120']; protocol §2 'No HALT and no further extension'
- **Failure scenario.** A stronger always-on PI (non-dominated, or tuned on an extended grid) narrows C1's 16.2 % margin, possibly below the 10 % bar.
- **How to test.** Run always-on p70_70_10_e4 and an extended-gain PI grid on fresh seeds in block_q1600. Meanwhile, disclose the grid-edge and Pareto status in the paper.
- **Related claims.** C44, C26

#### TEXT-F11 (R1 TEXT, major, hidden-assumption): Tuned arms sit on grid edges, including the always-on PI used as the C1 reference; the paper calls the set 'full' and 'strong'

- **Description.** In P1b at q1600, PI = p70_120_8_e4 sits at both the maximum K_P and the maximum K_I. This PI is the frozen reference in C1. FX = c2600, the maximum rate (almost no metering). The IP block plan is on the K_P = 20 and n_crit = 16 edges. At q2000, N is on the K_F = 10 edge. The protocol reports grid edges and forbids extending the grid; the paper says nothing about them.
- **Evidence.**
  - p1b_result.json tune.grid_edges_report_only
  - p1b_confirm_c1.md:12
  - p1_incident_information.md:45
  - paper.qmd:67, :73, :155
- **Failure scenario.** A stronger PI beyond the grid could reduce IP's lead in C1, which weakens 'beyond strong always-on feedback'.
- **How to test.** Report the grid edges; optionally tune PI on an extended grid using the tuning seeds only.
- **Related claims.** C12, C08

#### Verifier R1 reproduce: CONFIRMED / major

I reproduced the core facts from the raw tuning runs with my own code, without importing v5b.

(1) The rule at 93ba655 picks the PI with the lowest median delay over the 80 pooled slow + block tuning runs: v5b/p1b/analysis.py@93ba655:119-131, fit_fixed, which calls fam.best_by_median. The protocol pre-registers this rule (p1_incident_information.md:34 'Tuned like FX', :31, :41). The rule gives p70_120_8_e4 with a pooled median of 210.05, a slow median of 189.4 and a block median of 293.4.

(2) Exactly 6 PI laws are strictly lower in both medians. p70_70_10_e4 has 172.6 / 255.1. Both the pooled mean (224.7) and the mean of the two per-type medians (213.9) pick p70_70_10_e4.

(3) The PI grid is K_P {20,40,70} x K_I {10,20,40,70,120} (v5b/p1/family.py@93ba655:22,30-31). The chosen point sits at both upper edges. result.json tune.grid_edges_report_only['1600'].PI = ['K_P=70','K_I=120']. The protocol forbids extending the grid (p1_incident_information.md:45). The C1 protocol fixes this PI (p1b_confirm_c1.md:12).

(4) The dominance also holds out of sample. On the P1b evaluation seeds, always-on p70_70_8_e4 has 168.6 / 233.6 against 174.8 / 252.1 for the frozen PI.

(5) IP still beats the alternatives on the P1b evaluation seeds. It beats the frozen PI by 18.0 % and always-on p70_70_8_e4 by 14.4 %, 95 % CI [6.7, 25.3]. The tracer's [6.6, 25.3] differs only in the bootstrap random seed. It beats N->p70_70_10_e4 by 21.3 % and N->p20_40_10_e4 by 19.9 %. I also reproduced C1 at 16.2 % [7.3, 23.6].

(6) Papageorgiou 2008 §3 (toll plaza, Fig. 7) says: 'virtually identical for K_R >= 300'.

(7) The paper is silent on grid edges and on the tuning objective. It only says 'All arms are tuned on 40 tuning seeds' (:118), and it uses 'full set of tuned' (:73) and 'strong always-on' (:67, :155).

Caveats that refine the finding but do not refute it:
(a) Nothing is wrong in the code. The dominated pick follows from the pre-registered pooled-median objective applied to a two-peaked mix of slow and block runs. The pooled median of 80 values falls in the overlap between the upper slow tail and the lower block tail: 13 slow runs lie above it and 13 block runs below it.
(b) 'Surface still decreasing at the corner' is true only for the pooled-median objective: 227.1 -> 214.4 -> 210.1 along K_I at K_P=70, and 234.1 -> 222.8 -> 210.1 along K_P at K_I=120. The per-type medians rise from K_I=70 to K_I=120 (slow 180.6 -> 189.4, block 251.6 -> 293.4). So the evidence points to a better interior-K_I point, p70_70_10_e4, which is still on the K_P=70 edge. It does not point to a stronger PI beyond the grid.
(c) The '15-21 %' range mixes proxies. The two named proxies give 19.9 and 21.3 %; the 15 % is N->p70_70_8_e4 (15.4 %).
(d) Papageorgiou also says K_R = 100-200 is 'virtually equally efficient' when the transient is short. The 120 grid cap is therefore not evidence of too-low gains; it is indicative only, as the tracer said.
(e) The phrase 'tuned always-on PI-ALINEA' appears in decisions.md V116, not in the paper.

The headline survives. Against the non-dominated always-on alternative that exists on the evaluation seeds, IP still meets rel >= 10 % with the 95 % CI lower bound > 0. So this is not critical. It is an undisclosed weakness of the comparator and of the tuning objective that a reviewer would ask to see disclosed, so major stands.

Checks: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/CTRL-F2-reproduce/pi_tune.py (output out_pi_tune_q1600.txt): recompute pooled-median pick, per-type medians, Pareto dominators, alternative aggregators and K_P x K_I surface from 14,400 raw tuning runs, with a field check on every file; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/CTRL-F2-reproduce/ip_vs_alt.py (output out_ip_vs_alt.txt): paired bootstrap B=20,000 of IP vs frozen PI, always-on p70_70_8_e4 and N->PI proxies on the P1b evaluation seeds, plus C1 v114; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/CTRL-F2-reproduce/eval_pertype.py (output out_eval_pertype.txt): out-of-sample per-type medians of the always-on PI laws; git show 93ba655:v5b/p1b/analysis.py, v5b/p1b/run.py, v5b/p1/family.py, v5b/p1b/family.py: selection rule and grid; git diff 93ba655 HEAD on these files is empty; pdftotext of papers/refs_papers/1-s2.0-S0968090X07000873-main.pdf to papageorgiou2008.txt in the scratch dir; grep of the K_R sensitivity text (§3, Fig. 7); grep/sed of the protocols p1_incident_information.md:31-45, p1b_addendum.md:63, p1b_confirm_c1.md:12; paper.qmd:67,73,118,145,155,187; decisions.md V114/V116; p1b_summary.md:22

#### Verifier R1 defend: CONFIRMED / minor

Defence result: the facts in the finding hold, but the defence removes most of what was said to follow from them. What is left is a disclosure gap in the paper, not a weaker comparator.

(1) Tuning rule. The C1 PI was tuned by the pre-registered rule: lowest median delay over the pooled slow + block runs on the 40 tuning seeds (protocol p1 §2 'Tuning'). The code at 93ba655 implements exactly this (v5b/p1b/analysis.py:119-131 fit_fixed -> v5b/p1/family.py:110-117 best_by_median; the working tree is unchanged for v5b/p1 and v5b/p1b). My own recomputation from the raw runs gives p70_120_8_e4 as the argmin: pooled median 210.1, against 212.1, 212.3 and 214.4 for the next three. G_PI(1600) also matches result.json. So 'tuned' is accurate as defined.

(2) Pareto claim. The 'Pareto-dominated' statement is true at point-estimate level: six laws have lower per-type medians, and p70_70_10_e4 gives 172.6 / 255.1. But per-type medians, pooled mean and the mean of per-type medians were not the pre-registered objective. The median of a mixture is not monotone in the medians of its parts. All of these differences are inside the noise:
- corner versus p70_70_8_e4: difference of medians 4.3 s, CI [-32, 26]; paired median difference -6.3 s, CI [-21, 5];
- corner versus p70_70_10_e4: paired median difference -9.3 s, CI [-28, 5].

(3) 'Surface still decreasing at the corner'. The last steps into the corner are within noise: K_I 70 to 120 gives 4.3 s, CI [-32, 26]; K_P 40 to 70 gives 12.8 s, CI [-21, 32]. So this is not evidence that better gains lie beyond the grid. The Papageorgiou 2008 analogy cuts both ways. §3 says results are 'virtually identical for KR >= 300', and also that 100 or 200 are 'virtually equally efficient' when transients are short. §4 shows performance getting worse above KR 200. The units differ from this plant.

(4) Evaluation data. On the P1b evaluation seeds, the best in-grid alternative that was run always-on (p70_70_8_e4) is not detectably stronger than the chosen PI in the paper's paired convention: block 2.2 % [-2.9, 7.4]; slow -1.4 %, which favours the chosen PI. IP still beats p70_70_8_e4 by 14.4 % [6.7, 25.3] (95 %), and beats every N->PI proxy by 15-24 %, all CIs above 0. C1 reproduces at 16.2 % [7.3, 23.6]. Within the pre-registered grid, I found no evidence that the C1 comparator is weaker than any available always-on PI.

(5) Grid edges. Not extending the grid was pre-registered (p1 protocol:45 and A5; inherited by the P1b addendum). The edges are reported in result.json and summary.md. FX at c2600 is at the physical rate cap of 2618 veh/h, so that edge is not a tuning gap. The IP edges (K_P = 20, n_crit = 16) could only make IP stronger if extended.

What survives:
- The paper never mentions that the C1 comparator sits at the K_P = 70 / K_I = 120 corner of its grid.
- The paper never states the tuning objective. Line 118 says only 'tuned on 40 tuning seeds'.
- Lines 67, 73 and 155 call the comparator set 'strong' and 'full'.
- The protocol requires grid edges to be 'reported for every arm and grid dimension'. Only the auto-generated summary.md does this; p1b_result.md does not.
- The paper's Discussion and Limitations section is empty (it is a draft), so this is an omission, not a false statement.
- Whether a stronger PI exists beyond the grid is untested. Nothing I found suggests one does.

Headline risk is low. I rate this minor (a missing detail the protocol requires) rather than major. It would become major only if an extended-grid check showed a detectably stronger PI.

Checks: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/CTRL-F2-defend/pi_tune.py -> out/pi_tune.txt, out/pi_tune.json: full PI surface from raw tuning runs (pooled median, per-type medians, means, argmins, Pareto set, neighbourhood), both q; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/CTRL-F2-defend/corner_noise.py -> out/corner_noise.txt: bootstrap (B=20000) of the corner's lead over grid neighbours and Pareto dominators on tuning seeds; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/CTRL-F2-defend/eval_alt_pi.py -> out/eval_alt_pi.txt: IP vs every always-on PI and N->PI proxy on P1b eval seeds; C1 re-computation on v114; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/CTRL-F2-defend/eval_pi_vs_pi.py -> out/eval_pi_vs_pi.txt: p70_70_8_e4 vs chosen PI on eval seeds, paired convention; git show 93ba655:v5b/p1b/analysis.py, v5b/p1b/run.py, v5b/p1/family.py; git diff --stat 93ba655 HEAD -- v5b/p1 v5b/p1b; Read protocols p1_incident_information.md §2, p1b_addendum.md B1/B3, p1b_confirm_c1.md; grep paper.qmd for grid/edge/tuned/strong/limitations; grep decisions.md V114/V116; pdftotext of papers/refs_papers/1-s2.0-S0968090X07000873-main.pdf -> out/pap2008.txt; read §3.2 and §4.2 KR sensitivity passages

### B5. [major] CTRL-F3: ID equals the always-on law with N before onset (and IP=ID in block_q2000); comparisons measure only pre-onset effect

Raised as major; verification: reproduce: CONFIRMED/major, defend: CONFIRMED/minor.

#### CTRL-F3 (R1 CTRL, major, invalid-comparison): ID and IP run N before onset; this pre-onset choice alone costs 1.5-6.4 % against the same law run from t=0

- **Description.** For the L0 laws that are also plans in A, evaluation seeds give fixed(x) vs sw(N, x), i.e. N before onset and x after. Results: PI slow_q1600 -6.4 % [-12.7, -0.2]; PI block_q2000 -2.1 % [-5.6, -0.1]; FB block_q2000 -4.8 %; FX -1.1 to -4.2 %. ID's chosen plan is FB's own law at q1600 and PI's own law at q2000. ID vs FB (q1600) and ID vs PI (q2000) therefore measure only this pre-onset effect: Table II's -1.8 and -2.1 equal the sw(N, PI) vs fixed(PI) numbers. The S1a failure against PI is partly built into the design. V103's 'controller-family confound' was fixed only on the action-set side in P1b. The paper mentions this for crawl 2000 only (line 197).
- **Evidence.**
  - /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/CTRL/out/confound.json eval_fixed_vs_N_then_x
  - analysis.py@93ba655:71-73 sw(N, a); result.json tune.arms ID
  - oracles.json: always-on PI beats OR_in on 8/5/10/16 seeds
- **Failure scenario.** A reader concludes 'presence information has no value', when an ID that keeps the L0 law before onset would weakly dominate it.
- **How to test.** Add an ID variant that runs the always-on L0 law before onset (stay-PI is in A). At minimum, report the sw(N, x) vs fixed(x) rows and disclose that ID's plan equals the FB or PI law.
- **Related claims.** C27, C29, C46

#### S1-F3 (R1 S1, major, unsupported-interpretation): S1a nearly fails by construction: ID's plan is the binding always-on controller

- **Description.** ID's tuned plan is f40_10, the same controller as the FB arm at q1600, and p20_20_14_e4, the same controller as the PI arm at q2000. ID therefore differs from those arms only in running N before onset. At q2000, 7/100 seeds give hash-identical ID and PI runs. Both kinds of arm are tuned on incident runs only, so the best post-onset plan tends to coincide with the best always-on controller. Against those arms, S1a can only detect pre-onset effects. The paper does not state this. It reads S1a as 'knowing only that an incident is on gave no detected gain'.
- **Evidence.**
  - result.json tune.arms (re-derived from 60,480 tuning files by tune_check.py: all agree)
  - zero_diffs.py: ID vs PI at q2000, 7 identical hashes per cell; ID vs FB at q1600, same controller with N c1800 pre-onset
  - v5b/p1b/analysis.py@93ba655:119-142 fit_fixed/fit_switch (both tuned on pooled incident runs)
- **Failure scenario.** A reviewer asks whether S1a could ever have passed. On incident days, the answer is essentially only if switching at onset, or running N before onset, beats running the incident-optimal controller all along. This is a narrow test of 'presence information'.
- **How to test.** Report ID's chosen controller next to the L0 controllers. Add one sentence saying that ID equals FB or PI started at onset, and that presence information pays only through clean days (see S1-F2).
- **Related claims.** C64, C65

#### HEADLINE-F7 (R1 HEADLINE, info, hidden-assumption): In q2000 the presence plan ID is PI's own controller, and in block_q2000 IP is the same run as ID

- **Description.** Meaning: In both q2000 cells, ID = 'N (f10_8) until onset, then p20_20_14_e4', which is the always-on PI arm's controller. So ID vs PI there measures only whether running N before onset costs anything (-1.8 %, -2.1 %). In block_q2000, IP = ID (the same run key for all 100 seeds), so IP vs ID = 0.0 holds by construction. In q1600, ID = f40_10, which is FB's controller. This is consistent with the paper's statement that the lane-crawl 2000 plan was 'PI's own law' (paper.qmd:197). It also means S1a's failure in q2000 is structural, not evidence about presence information as such.
- **Evidence.**
  - /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/HEADLINE/tune_out.json
  - headline_out.json block_q2000 IP_vs_ID ties = 100
- **Failure scenario.** S1a 'presence did not pay' is read as a general result, when at q2000 ID could not differ from PI after onset.
- **How to test.** Inspect tune_out.json; mention in the discussion that ID coincided with an L0 controller in 3 of 4 cells.
- **Related claims.** paper.qmd:155 S1a fails, paper.qmd:174

#### CTRL-F8 (R1 CTRL, minor, disclosure): ID equals IP by construction in crawl 2000 (rel 0.0); both equal 'N then PI's law'

- **Description.** At q2000, the pooled best action and the block-type best action are the same: p20_20_14_e4 stay. The run keys are identical and all 100 delays are equal. The table's 0.0 and 'never ahead' follow mechanically.
- **Evidence.**
  - result.json tune.arms['2000']; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/CTRL/out/confound.json eval_IP_minus_ID_all_zero
- **Failure scenario.** A reader reads 0.0 as a measured null effect.
- **How to test.** Footnote the identical plans in Table II.
- **Related claims.** C27, C28

#### Verifier R1 reproduce: CONFIRMED / major

I reproduced the core fact from primary evidence: the raw v108 run files and the code at run commit 93ba655. I did not import anything from the v5b package. The working tree's v5b/p1b/analysis.py and meters.py are the same as at 93ba655; the only change since then is the added confirm_c1.py.

What ID is. ID's run is sw(N, a): the always-on law N runs until onset, then the chosen action a takes over (analysis.py@93ba655:71-73; fit_switch at 134-142 tunes ID on these runs). The raw ID runs confirm this: the fields are pre=N, post=plan, back=False, with t_switch == t_on in 100/100 runs per cell.

ID's plan is an L0 law in all four cells. I re-tuned every arm from the 40 tuning seeds (7400300-339) and all choices match result.json tune.arms.
- q1600: ID = f40_10, which is FB's law. Tuning medians: 211.6 for ID against 217.6 for the runner-up.
- q2000: ID = p20_20_14_e4, which is PI's law. Tuning medians: 381.3 against 384.6.
- q2000: IP(block) = p20_20_14_e4 = ID.

So in Table II, ID vs PI at q2000 compares sw(N, PI) with fixed(PI) and nothing else. My values are -1.83 % (slow) and -2.07 % (crawl); the table prints -1.8 and -2.1. IP vs ID in block_q2000 compares a run with itself: all 100 delays are identical, giving 0.0. The other Table II values also reproduce: ID vs PI -17.91 and -0.71; IP vs ID 16.16, 21.99 and 11.83.

Numbers the tracers cited, all reproduced:
- sw(N, x) vs fixed(x), percentile bootstrap with B = 20,000:
  - PI slow_q1600: -6.43 % [-12.73, -0.24]
  - PI block_q2000: -2.07 % [-5.67, -0.11]
  - FB block_q2000: -4.82 %
  - FX: -1.11 to -4.15 %
- ID and PI runs have identical hashes on 7 of 100 seeds in each q2000 cell.
- Always-on PI beats OR_in on 8, 5, 10 and 16 seeds (slow_q1600, block_q1600, slow_q2000, block_q2000).

Why this matters for S1a. S1a needs condition (a) to hold in the same cell against every L0 arm (paper.qmd:145). With the tuned plans, ID vs FB at q1600 and ID vs PI at q2000 differ only before onset. My values there are -1.6, -2.6, -1.8 and -2.1 %. So the common-cell (a) condition could be met only if running N before onset gained 10 % or more. This follows from how the tuning came out; the design does not force it in advance.

The paper does disclose the design: "Both run N before the incident" (paper.qmd:118). It does not say that ID's plan is FB's law at q1600 and PI's law at q2000. The only such mention is "PI's own law", for the crawl-2000 type plan (paper.qmd:197). Line 155, "knowing only that an incident is on gave no detected gain", therefore mixes the value of presence information with the cost of running N before onset.

The headline survives. S1a also fails condition (b) against PI in slow_q1600 (-17.9 %), and that comparison is genuine: two different laws. A variant of ID that runs the L0 law before onset would at best tie FB or PI in those cells, so S1a would still fail. That is why I keep the severity at major, not critical.

Where the tracers' wording is off:
1. CTRL-F3's title, "costs 1.5-6.4 %", overstates the cost. Across the 12 combinations of law and cell, the point estimates run from +0.94 % (PI, block_q1600: running N first slightly helps, CI [-2.1, 6.8]) down to -6.4 %. The CI lies below zero in only 6 of the 12; slow_q2000 PI has its upper bound at exactly 0.0. FB at q1600 is not significant in either cell. On the tuning seeds at q1600, sw(N, f40_10) even beat fixed FB (211.6 against 223.4).
2. "Pre-onset alone" is approximately right. Strictly, the switch also keeps N's rate until the next update on the shared 30-s grid (up to 30 s after onset), and a switch to PI resets n_prev, so the first update has no P term (meters.py@93ba655:18-20, 72-81, 117-125).
3. HEADLINE-F7 says ID matched an L0 controller "in 3 of 4 cells". It is 4 of 4. It is IP that matches an L0 law in 1 of 4.
4. "IP = ID by construction" in CTRL-F8 is loose. The two arms coincide because of how the tuning came out (the pooled best and the block best happen to be the same). Once they are the same action, the 0.0 follows mechanically.
5. V103's confound was fixed only by enlarging the action set (p1b_addendum.md:9, 35). The asymmetry that only ID and IP run N before onset was never addressed.

Checks: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/CTRL-F3-reproduce/reproduce.py -> out_reproduce.json (same dir): re-tunes N/FX/FB/PI/ID/IP from the raw tuning runs; on the evaluation seeds computes Table II rows and sw(N, x) vs fixed(x) with bootstrap B = 20,000; hash and delay identity counts; pre/post/t_switch checks.; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/CTRL-F3-reproduce/oracle_vs_fixed.py -> out_oracle.json: OR_in over the 120 actions (A taken from the main switch runs of a tuning seed) against the fixed L0 arms. A first version wrongly included delay-variant keys; it was fixed before the result was used.; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/CTRL-F3-reproduce/id_vs_fb.py -> out_id_vs_fb.txt: ID vs FB per cell.; git show 93ba655:v5b/p1b/analysis.py, meters.py and episode.py (sw, fit_fixed, fit_switch, set_law, step, switch handling); git diff --stat 93ba655 HEAD -- v5b/p1b/ (only confirm_c1.py added).; Read result.json tune.arms and eval.S1 (S1a per-reference a/b flags) with small Python snippets.; grep of paper.qmd (lines 118, 145, 155, 174-175, 197) and of the protocols p1_incident_information.md:36 and p1b_addendum.md:9, 35, 63-64; decisions.md V103.

#### Verifier R1 defend: CONFIRMED / minor

Meaning. ID (presence) runs the clean-day controller N until the incident starts, then switches to one plan picked from the set A. After tuning, that plan turned out to be FB's own law at q1600 (f40_10, stay) and PI's own law at q2000 (p20_20_14_e4, stay). So ID vs FB at q1600, and ID vs PI at q2000, differ only in what runs before onset (N, or the law itself) and in what that changes later. At block_q2000, IP is the same run as ID, so IP vs ID = 0.0 is an identity, not a measured null effect. The paper's Table II gives -1.8 and -2.1 (ID vs PI, q2000). These are exactly the "start PI's law at onset instead of at t=0" cost.

What survives my defence (CONFIRMED). (1) The plans do coincide. My own re-tune from the 40 tuning seeds (0 missing runs) reproduces ID = f40_10 = FB at q1600 and ID = p20_20_14_e4 = PI at q2000. It also reproduces IP block_q2000 = ID, with 100/100 identical hashes. (2) The paper never says that ID's plan equals an L0 law. It covers only the lane-crawl 2000 cell (paper.qmd:197). Nothing in Table II marks the 0.0 as an identity, and the Discussion section is empty.

What my defence removes, which is why I lower the severity from major to minor:
(a) The design is not a deviation. It was pre-registered: protocol p1_incident_information.md:36 (the ID row: "At onset ..."), :173 (I9: L0 arms are fixed runs from t=0) and :149 (A4(a): S1 is conditional on an incident; the clean-day cost is printed). The asymmetry was even written out earlier, in screen_D2_incidents.md:103 (A4a: "HD_FX and HD_FB therefore include N's advantage before onset"). The paper states it at paper.qmd:118 ("Both run N before the incident") and :104 (the comparison is conditional on an incident, and L0 arms tuned on incident runs may pay a clean-day cost). This matches the usual incident-responsive set-up: run the normal controller, then switch when an incident occurs.
(b) "By construction" overstates it. ID chose among 120 actions, and the coincidence came out of tuning. The tuning runner-up was 2.8 % (q1600) and 0.9 % (q2000) behind in median. IP's plan differs from every L0 law in 3 of 4 cells. IP beat ID significantly in two cells, so the design could detect information value when it existed.
(c) The headline cannot flip. I tested the alternative the finding proposes: an ID that keeps the L0 law before onset, which here is simply the fixed FB run at q1600 or the fixed PI run at q2000. It still fails S1a(a) in every cell. At q1600 it gives 0.0 vs FB and -18.5 % / -4.2 % vs PI. At q2000 it gives 0.0 vs PI and +7.2 % / +8.3 % vs FB (Bonferroni lower bounds 4.4 / 5.7, below the 10 % bar). S1a also fails against FB in all four cells, including the q2000 cells where ID is not FB's law. The pre-onset cost works against ID, so it cannot produce a false PASS.
(d) "Costs 1.5-6.4 %" cherry-picks. Across the 12 law x cell pairs, the sw(N,x) vs fixed(x) effect runs from -6.4 % to +0.9 % (PI block_q1600 +0.9). For the four pairs that the finding says matter, the S1-level CIs all include 0: q1600 FB [-4.4, 4.9] and [-8.1, 3.8]; q2000 PI [-5.2, 0.0] and [-6.5, 0.0]. Also, ID vs PI -17.9 % at slow_q1600 is not a pre-onset effect: ID's plan there is FB's law, and FB itself vs PI is -18.5 %.
(e) The author's own record already says this: p1b_result.md:48 ("best plan is PI's own law; starting it at onset costs 2.1 %") and :58 ("Controller-family confound: reduced, not removed ... plans still start from N, not PI"). The paper simply does not carry it yet.

So no paper sentence is false: "no detected gain of >= 10 %" and "never better (-17.9 to -0.7)" both check out. What remains is a missing disclosure or footnote. It would become major only if the Discussion or Abstract later generalised this into "presence information has no value". That reading would also leave out the clean-day costs, which ID avoids (q1600: N 45.4 s vs PI 81.1 s; p1b_summary.md:52, a note, not checked by me).

Failure points / tests. Report ID's and IP's chosen plans next to the L0 laws in Table II or a footnote. State that IP=ID=PI's law in block_q2000, that the q2000 ID-vs-PI rows are pre-onset costs, and that ID=FB's law at q1600. Re-run defend_check.py if the tuning runs or result.json change.

Checks: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/CTRL-F3-defend/defend_check.py (own numpy/json re-tune of ID/IP from tuning runs; sw(N,x) vs fixed(x) on eval seeds with B=20,000 bootstrap at 95 % and 0.99375; hash identity counts; onset times) -> output defend_out.json in the same dir; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/CTRL-F3-defend/hypo_id_prime.py (counterfactual ID' = L0 law kept before onset vs every L0 arm, Bonferroni lower bounds) -> hypo_id_prime.out; git show 93ba655:v5b/p1b/analysis.py and v5b/p1b/episode.py, v5b/p1/episode.py (run_key), v5b/p1b/family.py (A order, best_by_median); git diff 93ba655 HEAD -- v5b/p1b/analysis.py (no change); Read result.json eval.S1 (S1a per-arm a/b flags, per_cell_stats ID_vs) via small python summaries; grep/sed of protocols (p1_incident_information.md, p1b_addendum.md, screen_D2_incidents.md), docs/decisions.md V103, p1b_result.md, p1b_summary.md, paper.qmd lines 100-203

### B6. [major] CTRL-F4: IP gain comes from type-specific parameters, not timing; controller-family confound undisclosed

Raised as major; verification: reproduce: CONFIRMED/major, defend: CONFIRMED/major.

#### CTRL-F4 (R1 CTRL, major, unsupported-interpretation): A per-type always-on law, with no onset information, matches or beats IP out of sample; the type gain comes from parameters, not timing

- **Description.** I split the 40 tuning seeds in two (select on 20, score on the other 20). The best always-on law of G u PI tuned on each cell beats IP in 8/8 fold-cells (-0.7 to -22.2 %). In block_q1600 it beats pooled PI by 15-18 %, against IP's 19 %. In-sample, an always-on law beats IP in every cell (for example block_q1600: p40_20_14_e4 210.2 vs IP 224.7; IP's own law run from t=0 gives 222.0). So the C1 and S1b gains reflect type-specific tuning against an L0 arm tuned on a 50/50 mix (a hidden assumption), not the value of switching at onset. A 'type-tuned always-on' comparator is not realisable unless one type dominates, but its absence should be disclosed.
- **Evidence.**
  - /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/CTRL/out/split_type_tuned.json
  - /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/CTRL/out/confound.json (tune_best_alwayson_per_cell)
- **Failure scenario.** The paper's ladder reads as 'incident-type-aware switching pays'. A reviewer shows that the same gain comes from an always-on PI tuned for crawls, so the gain depends on the assumed incident-type prevalence used to tune L0.
- **How to test.** Evaluate always-on type-tuned laws on evaluation or fresh seeds. Report L0 tuning sensitivity to the type mix (prevalence-retuned PI rows already exist).
- **Related claims.** C28, C44, C26

#### C1-F5 (R1 C1, minor, unsupported-interpretation): C1 gain comes from type-specific PI tuning, not timely switching; the reference PI was tuned on pooled incidents

- **Description.** IP is c1800 until onset and then the PI law p20_20_16_e4 (set point 16) until the end of control. The reference is p70_120_8_e4 (set point 8), tuned on slow and block pooled. Three observations point the same way. (1) Detection delays of up to 120 s change IP by -1.5 % to +0.2 % (CIs include 0). (2) In the median seed 52 % of control lies after clearance. (3) On the P1b tuning seeds (block, q1600, 40 seeds), always-on p20_20_16_e4 had a median of 222.0 s against IP's 224.7 s; the best block-only always-on PI (p40_20_14_e4) had 210.2 s; the pooled-tuned PI had 293.4 s. So the C1 lead measures the value of tuning the PI gains for the incident type, not of switching at onset. The paper does not say this. Its framing ('type plan', 'lead held with detection delays') can be read as evidence for timely switching.
- **Evidence.**
  - result.json IP_vs_IP_d30/60/120 rel -0.7/+0.2/-1.5 %
  - raw C1 runs: duration 120-479 s, onset 40-336 s
  - tune_block_only.py on P1b raw tuning runs (seeds 7,400,300-339)
- **Failure scenario.** The paper or thesis claims that detection timing or online switching drives the gain, when an always-on block-tuned PI would likely do as well (not tested on C1 seeds).
- **How to test.** tune_block_only.py (descriptive, tuning seeds only); a proper test would need new runs of always-on p20_20_16_e4 on fresh seeds.
- **Related claims.** C71, C73

#### TEXT-F10 (R1 TEXT, major, invalid-comparison): The controller-family confound is not disclosed

- **Description.** IP and ID run N before onset (c1800 at q1600) and switch at onset. Always-on PI runs its incident-tuned law from t = 0. So IP vs PI mixes three effects: type information, running N before onset, and the plan family. p1b_result.md marks the confound 'reduced, not removed'. The fix it proposes as step 2 ('PI by default + type plan') was not run. Since ID vs PI is only -0.7 % in this cell, the type effect is probably real, but its size against PI is not isolated.
- **Evidence.**
  - p1b_result.md:58, :91
  - paper.qmd:118, :187
  - clean_day_paired.out: PI vs N on clean days at q1600 +12.0 s [-0.5, 19.8]
- **Failure scenario.** A reviewer asks whether the 16.2 % gain over PI would survive against an arm that runs PI by default and switches to the type plan at onset.
- **How to test.** Run the 'PI default + type plan' arm (p1b_result.md §8 step 2, about 22k runs; needs author approval), or disclose the confound in the limitations.
- **Related claims.** C12

#### Verifier R1 reproduce: CONFIRMED / major

I recomputed everything myself from the raw run JSONs, using my own numpy code and no v5b imports. Every number the finding cites reproduces exactly.

In-sample check (40 tuning seeds, block_q1600):
- IP = c1800, then the PI law p20_20_16_e4 from onset (stay plan): median 224.7.
- The same law always on from t = 0: 222.0. Paired rel 0.0 % [-5.9, 2.8]; IP is better on 20 of 40 seeds. So switching at onset adds nothing on incident days.
- The best always-on law in G u PI is p40_20_14_e4: 210.2. The pooled-tuned PI p70_120_8_e4: 293.4.
- An always-on law has a lower median than IP in all 4 cells.

Out-of-sample split (select on 20 seeds, score on the other 20):
- IP vs the type-tuned always-on law: -4.3, -22.2, -2.0, -1.4, -4.4, -0.7, -5.4, -4.1 %. These match the tracer's values.
- block_q1600: the always-on law beats pooled PI by 17.7 % and 15.2 %; IP beats it by 19.1 % and 19.4 %.

C1 and design facts:
- Detection delays change IP by -0.7 % (d30), +0.2 % (d60) and -1.5 % (d120). All three CIs include 0.
- In the median seed, 52.4 % of control comes after clearance.
- L0 is tuned on slow + block pooled in equal shares. This is pre-registered in the protocol (p1_incident_information.md:43), but the paper never says it.
- The 'PI by default + type plan' arm was never run: there are 0 such runs, and the code at the run commit refuses them.
- The paper (line 118) says IP and ID run N before onset, but it does not discuss the confound. Its Discussion section is empty.

So the core claim stands. The IP-vs-PI gain (C1, 16.2 %) comes almost entirely from the incident-tuned PI gains, not from when the switch happens. How big the gain is depends on the undisclosed 50/50 type mix used to tune L0. A reviewer would ask for this to be disclosed. The headline numbers themselves stay correct, so the severity is major.

Corrections to the finding:
1. 'Beats IP in 8/8 fold-cells' is a point-estimate statement only. All 8 paired 95 % CIs include 0 (20 seeds each), and IP is better on 7-10 of 20 seeds.
2. The comparison is uneven. The always-on comparator searched 230 laws, while IP could choose from only 10 PI laws (G_PI). With the always-on set limited to IP's own laws (G u G_PI), IP leads in the C1 cell in both folds: +2.3 % [-2.6, 7.4] and +17.9 % [-0.7, 24.4]. Across all 8 fold-cells it is 4 for always-on, 2 about equal, 2 for IP. So 'matches or beats out of sample' does not hold up in the C1 cell. The cleanest evidence for 'not timing' is the same-law check (0.0 %), together with the detection-delay results.
3. 'Not timing' holds only on incident days. Running a crawl-tuned law always on costs 65.8-83.5 s/veh more than N on clean days, and is 16.6-50.8 % worse than PI on slowdowns. Onset and type information is what lets the meter use that law without these costs.
4. S1b compares IP with ID. ID also switches at onset and is not an L0 arm, so type-specific plan choice is exactly what S1b is meant to measure; it is not a confound there. The confound applies to IP vs PI (C1 and the Table II row).
5. The 'prevalence-retuned PI rows' do not vary the type mix. They mix pi·(slow + block)/2 + (1 - pi)·clean, so slow and block are always 50/50. No check of the type mix exists.
6. Calling the 50/50 mix 'hidden' is wrong for the protocol, which pre-registers it. It is true for the paper, which does not state it.
7. The paper discloses a similar point for one cell only: line 197 says that for the crawl at 2000 veh/h, starting PI's own law at onset never beat always-on PI.

Checks: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/CTRL-F4-reproduce/load_tune.py: cache of all 75,120 tuning-seed runs (matches tune.n_runs), output tune_cache.json; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/CTRL-F4-reproduce/type_tuned.py: re-derives the arms, in-sample medians and split-half selections, output type_tuned.json; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/CTRL-F4-reproduce/split_ci.py: paired bootstrap CIs (B=20,000) for the 8 fold-cells, plus the costs of crawl-tuned laws on clean and slowdown days, output split_ci.out; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/CTRL-F4-reproduce/same_set.py: always-on limited to G u G_PI vs IP, output same_set.out; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/CTRL-F4-reproduce/iplaw_alwayson.py: IP vs the same law always on, output iplaw_alwayson.out; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/CTRL-F4-reproduce/c1_timing.py: C1 detection-delay rows, onset and duration ranges, post-clearance share, output c1_timing.out; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/CTRL-F4-reproduce/clean_day.py: clean-day PI vs N on eval seeds, output clean_day.out; Read code at 93ba655 and e7dd561 via git archive into the scratch dir: p1b/run.py stage_tune, p1b/analysis.py fit_fixed / fit_switch / fit_prevalence, p1b/family.py, p1b/episode.py:77-79, d2/incidents.py incident_window; Listed and counted run files for switch runs that start from a PI law in p1b/v108 and p1b_c1/v114 (0 found); Read paper.qmd:100-101, 118, 145, 165-197, 199; p1b_result.md:58, 91; p1_incident_information.md:32, 36, 43; git diff --stat 93ba655 HEAD and e7dd561 HEAD on v5b/p1b and v5b/p1

#### Verifier R1 defend: CONFIRMED / major

Defence result: the core problem survives. Part of the group is overstated, and one new fact makes the core worse.

What the defence removes or reduces:
(1) "The gain comes from parameters, not timing" does not contradict any claim in the paper. S1a (presence and timing alone) fails in every cell, and the paper says so (paper.qmd:155). IP is defined as "switches to a plan for that type" (paper.qmd:101). The paper never says that onset timing drives the gain. Choosing type-specific parameters is exactly what type information buys.
(2) An always-on law tuned per type is not an L0 arm, because it needs to know the type in advance. The protocol says L0 is tuned on the pooled mix "so they get no type information" (p1_incident_information.md:43).
(3) The family part of TEXT-F10 is largely moot for the C1 cell:
- IP's crawl plan p20_20_16_e4 is itself a PI law from G_PI (the P1b B3/R1 fix).
- The text discloses that IP and ID run N before onset (paper.qmd:118), and line 197 says onset-starting cost the PI law at crawl 2000.
- On the tuning seeds, the same law run from t=0 gives 222.0 s against IP's 224.7 s. So the N-before-onset component is about 1 % and works against IP.
(4) The tracer's out-of-sample claim is overstated for the C1 cell. Over 500 random 20/20 splits, with IP also re-selected on the selection half, the type-tuned always-on PI beats IP by median in only 40 % of splits in block_q1600. The paired rel IP vs AO has median +3.9 % (5-95 %: -4.5 to 11.9). It is roughly a tie there, not a clear win. In the other cells AO wins in 65-86 % of splits.
(5) The Discussion and Limitations section is empty (paper.qmd:199), so part of the non-disclosure is a draft-stage gap.

What survives:
- The paper never says that L0 and ID were tuned on a pooled 50/50 slow+crawl mix by the median of the pooled runs. Pre-registration was not hidden (protocol :32, :43); the paper itself does not say it.
- New, stronger evidence: the C1-cell gain depends on a near-tie inside that pre-registered pooled-median rule.
  - The top 5 PI laws score 210.1-214.8 s on the pooled median, but their crawl-cell medians span 251.6-293.4 s. The rule picks the law that is worst on crawl.
  - In a bootstrap of the tuning seeds, p70_120_8_e4 wins only 29 % of draws. The winner's crawl median ranges from 222.5 to 293.4 s (5-95 %).
  - With the same 50/50 mix but a per-seed-mixture median (the protocol's own prevalence form), the choice becomes p20_20_14_e4. In-sample, IP vs PI then drops from 22.3 % to 1.8 % in block_q1600 and rises to 20.4 % in slow_q1600. With a pooled mean, the gains are 9.3 % and 1.2 %.
- On the evaluation seeds, IP still leads the 4th-ranked near-tie law p70_70_8_e4 by 14.4 % [6.8, 25.4] in block_q1600. So some gain over always-on PI survives, but its size is set by the choice of L0 rule.
- S1b is an at-least-one-cell statement (protocol :100, R5). Under every objective, one cell at q1600 shows an 18-22 % type gain, so the S1b pass is robust. Which cell shows it is an artefact of where the L0 compromise falls.
- Paper.qmd:155 says IP beat PI "only for the lane crawl at 1600" and C1 confirms that cell. Readers will take this as specific to crawl. Neither point is disclosed.

Severity: major. No headline is overturned. C71 is literally true against the frozen, pre-registered arms, and S1b stands. But the paper does not state the L0 tuning mix and rule, and the cell location and size of the IP-vs-PI gain depend on them. A reviewer would require this to be disclosed. Treat TEXT-F10's family-confound part on its own as minor.

Checks: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/CTRL-F4-defend/extract_tuning.py: reads the raw P1b tuning-seed runs (7,400,300-339) into tuning_table.json (75,120 rows, all from 93ba655); /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/CTRL-F4-defend/defend_check.py (output defend_check.out/.json): reproduces the PI/IP/ID choices; per-cell type-tuned always-on vs IP; 500 random 20/20 split-sample re-selections; type-mix sweep w_block 0-1; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/CTRL-F4-defend/objective_sensitivity.py (output .out/.json): the L0 PI choice under pooled median (pre-registered), pooled mean and per-seed mixture median/mean at a 50/50 mix; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/CTRL-F4-defend/id_objective_sensitivity.py (output .out/.json): ID choice and IP vs ID under the alternative objectives; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/CTRL-F4-defend/eval_alt_pi.py (output .out/.json): eval-seed IP vs the three always-on PI laws run there (paired bootstrap B=20,000); bootstrap stability of the pooled-median PI winner on the tuning seeds; Read paper.qmd:60-203; p1_incident_information.md (grep pooled/prevalence/S1); p1b_addendum.md:1-80; p1b_result.md:50-100; decisions.md grep confound/prevalence (V103, V129); git show 93ba655:v5b/p1b/analysis.py (fit_fixed, fit_switch), 93ba655:v5b/p1/family.py best_by_median, 93ba655:v5b/p1/stats.py (rel convention); git diff --stat 93ba655 HEAD on those files (no drift); Directory listings of the arms on eval seed 7,400,650 (block_q1600) and in the C1 runs (p1b_c1/v114/runs), to confirm that no type-tuned always-on law was evaluated

### B7. [major] DRAIN: End-of-horizon convention (all-green, demand-free drain after 940 s) carries most of every headline gain

Raised as major; verification: reproduce: CONFIRMED/major, defend: CONFIRMED/major, impact: CONFIRMED/major.

#### FU1-F1 (R1 FU1, major, disclosure): Undisclosed end-of-horizon convention carries most of every headline gain

- **Description.** At 940 s demand stops, the meter switches to all-green, and the network drains with no control. The paper metric (delay after the drain) includes this phase, but the paper says only 'continues until the network is empty'. Across all P1b and C1 comparisons with a real gain, 55-106 % of the mean paired full-TTT difference accrues after 940 s. For S1b it is 0.83 (slow_q2000) and 0.67 (block_q1600); for C1 IP vs PI 0.55; for C1 IP vs NC 0.86. Per-seed median shares are 0.87, 0.69 and 0.57. The critic's numbers reproduce exactly.
- **Evidence.**
  - v5b/p1b/episode.py@93ba655:133,239-251 (same at e7dd561 and in the working tree)
  - v5b/d1/sumo_runner.py@93ba655:142
  - paper.qmd:110
  - FU1/drain_audit.out (all cells, all L0 arms)
  - FU1/rerun_drain_decomp.out identical to critic/drain_decomp.out
- **Failure scenario.** A reviewer reads the 11.8 %, 22.0 % and 16.2 % as savings made while the meter is operating. In fact more than half of each is realised in an uncontrolled, demand-free drain whose cost per leftover vehicle depends on the release convention.
- **How to test.** Add one sentence on the release convention and a window-TTT/served-throughput row. A decisive test needs new runs with the meter kept on during the drain, or a longer demand horizon (author decision; outside this audit).
- **Related claims.** FU1-C2, FU1-C3, FU1-C7, C57, C66, C69, C71, C34, C24, C12, C85

#### FU1-F3 (R1 FU1, major, unsupported-interpretation): The S1b slowdown-2000 gain depends on arm-specific behaviour in the uncontrolled drain

- **Description.** For slow_q2000 IP vs ID, 83 % of the mean paired TTT gain accrues after control ends, and the window-TTT rel is 1.7 %. A two-arm model (post_s = a n + b n² + c·arm) assigns 44 % of the post-control difference to an arm effect at equal leftover n. Possible cause, not verified: IP ends in p70_40_8_e4 and ID in p20_20_14_e4, and the queue states these leave drain differently once released. With the leftover vehicles priced by a common pooled function of n_left, the rel is 6.0 %, against 10.3 % on full TTT. For block_q1600 the arm-specific share is only 8 % and the neutral-price rel is 19.0 % (LCB 2.95 > 0). So the S1b verdict survives through block_q1600, but the 11.8 % slowdown number is not an information effect produced during control.
- **Evidence.**
  - FU1/metric_ideal.out part (2)
  - FU1/drain_dynamics.out slow_q2000 per-arm residuals: ID +1.48, IP -1.37 veh.h at similar n_left (230 vs 220)
  - FU1/drain_audit.out slow_q2000 IP vs ID: medians dW 0.58, dpost 4.83 veh.h
  - paper.qmd:155,175
- **Failure scenario.** If the meter stayed on during the drain, or the horizon were longer, the slowdown-2000 type gain could fall below 10 %, and the second S1b cell named in the text would no longer pass.
- **How to test.** Re-run FU1/metric_ideal.py and FU1/drain_dynamics.py. Decisive test: new runs with control kept active until empty (author decision).
- **Related claims.** FU1-C3

#### FU1-F4 (R1 FU1, minor, hidden-assumption): The all-green drain discharges at roughly the uncontrolled rate, which prices leftover queues convexly and favours the arm that serves more

- **Description.** Quadratic fits of post-control TTT on n_left give an implied drain discharge of about 806-858 veh/h pooled and 790-1,000 veh/h per arm. During the control window, metered arms serve 1,050-1,220 veh/h and NC serves 920-970. This is model-based: the fitted linear term is negative and not physical, so I treat the rates as rough. Leftover queues are therefore priced at the uncontrolled bottleneck rate, which grows roughly with n_left². This is why always-on PI beats NC on delay in C1 (+13.5 %) but loses on window TTT (-5.7 % [-12.6, -0.4]); PI vs NC has a post share of 1.12. In P1b block_q1600 the same pair is +14.9 % on delay and -4.4 % [-10.9, 5.7] on window TTT. NC is a report-only reference, so no claim fails. The cost of a leftover vehicle under this convention is a modelling choice the paper should state.
- **Evidence.**
  - FU1/drain_dynamics.out
  - FU1/drain_audit.out C1 PI vs NC; P1b block_q1600 PI vs NC
  - FU1/rerun_c1_vs_nocontrol.out
- **Failure scenario.** A reader takes always-on PI to be a strong baseline that beats no control. On in-window TTT it does not in the crawl-1600 cell. Its advantage on delay comes from the cheaper drain of its smaller leftover queue.
- **How to test.** Re-run FU1/drain_dynamics.py. Compare against runs with the meter kept on during the drain.
- **Related claims.** FU1-C7, FU1-C6

#### FU1-F5 (R1 FU1, info, unsupported-interpretation): C1 and the crawl-1600 rows are robust: their post-control share reflects throughput won during control

- **Description.** The critic's wording 'most of the difference is decided by how a leftover queue drains' overstates the case for C1 and block_q1600. Per seed, served_ctrl x 0.25 h + n_left is exactly constant across arms (residual 0.00). IP leaves 13-26 fewer vehicles at 940 s because it serves more during control. At equal n_left, the arm-specific drain part is -4 % (C1) and 8-11 % (block_q1600). C1 holds on every metric: delay 16.2, window TTT 11.7, full TTT 13.8, neutral price 14.9, faster-drain price (k = 0.6) 14.5. Window TTT, for its part, ignores the cost of the leftover vehicles, so it is not a neutral metric either.
- **Evidence.**
  - FU1/served_check.out (identity resid max 0.00)
  - FU1/metric_ideal.out part (2)
  - FU1/drain_dynamics.out C1 rows
- **Failure scenario.** Over-correcting: declaring C1 an artefact of the drain would be wrong.
- **How to test.** Re-run FU1/served_check.py and FU1/drain_dynamics.py.
- **Related claims.** FU1-C7, FU1-C6

#### FU1-F7 (R1 FU1, info, hidden-assumption): The project's own architecture review rejected the release-at-end convention that P1/P1b kept

- **Description.** docs/architecture/review_v0.md:392 says: 'Releasing control during the drain also biases ramp-queue delay across arms'. The F3Z contract (docs/architecture/interfaces.md:52) says: 'Control stays active during the drain; there is no release at the end of the inflow.' The BN4 P1/P1b plant kept the D1/D2 release, which is pre-registered only by reference: D2-A4 h, 'after the drain', screen_D2_incidents.md:110. The words 'all-green' and 'release' appear in no P1/P1b protocol text.
- **Evidence.**
  - docs/architecture/review_v0.md:390-392
  - docs/architecture/interfaces.md:52
  - docs/research/protocols/screen_D2_incidents.md:110
  - docs/research/protocols/p1_incident_information.md:85 (refers to D2-A4 h)
- **Failure scenario.** An examiner cites the author's own review against the P1b metric.
- **How to test.** grep -n -i 'all.green\|release' docs/research/protocols/p1*.md
- **Related claims.** FU1-C2

#### Verifier R2 reproduce: CONFIRMED / major

I reproduced the core fact from the code at the run commits and from the raw runs, using my own code.

(1) Code (direct observation). Demand is a Poisson stream on [0, 940) s only: v5b/p1b/episode.py@93ba655:133 and v5b/d1/demand.py@93ba655 generate(), which breaks at t >= t1. At the end of control, episode.py@93ba655:237-251 does four things: it clears any incident, records ttt_ctrl_vehh, sets the TLS to the 'allgreen' program and drops the meter, then calls sim.drain(7200) until the network is empty. TTT counts both running and pending (origin) vehicles: v5b/d1/sumo_runner.py@93ba655:142. episode.py, sumo_runner.py and plant.py are byte-identical at e7dd561 (C1) and at HEAD. No compared run had the incident still on at 940 s (onset <= 340 s, duration <= 480 s). All compared runs are drained and valid.

(2) Paper (direct observation). paper.qmd:110 says only "continues until the network is empty". No line mentions the demand stop, the all-green release, TTT or served throughput (grep). Yet protocol p1_incident_information.md:85 says served throughput is co-headlined and TTT is reported alongside.

(3) Numbers (derived, own scripts). Paired TTT split at 940 s, as post share = mean(dPost)/mean(dFull):
- slow_q2000 IP vs ID: 0.826
- block_q1600 IP vs ID: 0.667
- C1 IP vs PI: 0.552
- C1 IP vs NC: 0.860
- P1b block_q1600 IP vs PI: 0.570
- P1b block_q1600 PI vs NC: 1.063
- C1 PI vs NC: 1.115

For slow_q2000, window-TTT rel is 1.68 %, full-TTT rel 10.27 %, median dW 0.576 and median dPost 4.833 veh.h. The TTT split carries over to the paper's delay metric: per seed, dDelay x generated / 3600 equals dTTT_full (corr 1.000; medians 6.42 vs 6.40, 6.62 vs 6.62, 4.85 vs 4.81 veh.h). So more than half of each headline delay gain (11.8, 22.0, 16.2 %) accrues after 940 s.

(4) Model-based parts of F3, F4 and F5 also reproduce (derived; the fits are descriptive):
- The two-arm arm effect at equal n_left is 0.44 for slow_q2000. It is stable across three specifications (0.43-0.44). It is 0.08 for block_q1600 IP vs ID, 0.11 for block_q1600 IP vs PI, and -0.04 for C1.
- The neutral pooled-price rel is 6.0 % (slow_q2000), 19.0 % (block_q1600) and 14.9 % (C1).
- The implied pooled discharge is 806-858 veh/h.
- The throughput identity residual (served_ctrl x 0.25 h + n_left, compared across arms) is 0.000.
- C1 PI vs NC: delay +13.46 %, window TTT -5.68 % [-12.6, -0.4].

Small deviations, none of which changes the finding:
- Per-seed median shares are 0.871 / 0.682 / 0.561 over all seeds. FU1's 0.69 and 0.57 came from a |dF| > 0.5 filter.
- The stated range '55-106 %' leaves out C1 PI vs NC (1.12), which F4 itself cites.
- F4's 'metered arms serve 1,050-1,220 veh/h' does not hold for every metered arm: N serves 860 in slow_q2000, FX 938-990, and AD 950 in block_q1600.
- The block_q1600 neutral-price LCB of 2.95 depends on the bootstrap RNG (2.53-3.08 over 20 seeds), but it stays above 0.
- In slow_q2000, the residuals of the pooled quadratic fit alternate in sign by arm (about +/-1.1 to 1.6 veh.h), and their cause is unexplained. So the 44 % is a model-based figure, not a mechanism.

Severity stays major. The Table II and C1 numbers are correct as computed. S1b survives through block_q1600 (window rel 9.9 %, neutral 19.0 %), and C1 holds on every variant. But the paper does not disclose the end-of-horizon convention, and the slowdown-2000 gain is mostly realised in the uncontrolled drain (window rel 1.7 %, neutral 6.0 %). A reviewer would require both to be disclosed. A change to the S1b verdict is not shown, so this is not critical.

Checks: git show 93ba655:v5b/p1b/episode.py, v5b/d1/sumo_runner.py, v5b/d1/plant.py, v5b/d1/demand.py, v5b/d2/incidents.py; sha1 comparison with e7dd561 and HEAD; grep of papers/paper_1/paper.qmd for drain / horizon / all-green / TTT / throughput / served disclosure; check of cited lines 110, 155, 174-176, 187; grep of the protocols p1_incident_information.md, p1b_addendum.md, p1b_confirm_c1.md for drain / TTT / served; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/DRAIN-reproduce/drain_split.py (output drain_split.out, drain_split.json): paired window / post / full TTT split, rels, own bootstrap CIs, n_left, throughput identity, flags, for 11 comparisons in P1b v108 and C1 v114; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/DRAIN-reproduce/drain_models.py (output drain_models.out): two-arm arm-effect fits in 3 specifications, pooled 8-arm neutral-price metric with and without intercept, implied discharge, served in window per arm; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/DRAIN-reproduce/proxy_check.py (output proxy_check.out): delay-diff against TTT-diff proxy; RNG sensitivity of the neutral-price LCB; Read FU1/drain_dynamics.py, metric_ideal.py, drain_audit.py (definitions only) and rerun_drain_decomp.out, to explain the small differences (|dF|>0.5 filter, RNG)

#### Verifier R2 defend: CONFIRMED / major

I argued the author's side and found five defences. Each is real, but none removes the problem.

(1) The convention was fixed before data, so it is not a deviation. The metric is "delay ... after the drain" (screen_D2_incidents.md:110 A4 h, taken over by p1_incident_information.md:85). The code docstring states the uncontrolled all-green drain (v5b/p1/episode.py@93ba655:4). The P1b code does exactly this: demand runs only over 0-940 s (v5b/p1b/episode.py@93ba655:133), then the meter goes all-green (:242-243) and the network drains (:249). Every arm is treated the same way. This answers any charge of a post-hoc choice, but the group does not make that charge.

(2) The paper hints at the convention ("900-s control period, and continues until the network is empty", paper.qmd:110). It never says that demand stops at 940 s or that the meter is released to all-green while 130-230 vehicles are still in the system. Discussion/Limitations is still empty (paper.qmd:199-201), so the disclosure can still be added. The defence fails against the current text, and it fails against the protocol too: p1_incident_information.md:85 requires served throughput to be co-headlined and TTT to be reported alongside. The results notes do this (p1b_summary.md:60-65, p1b_c1_summary.md:39), but the paper reports neither. That is an omission against the protocol's reporting rule.

(3) Field convention. The cited Papageorgiou 2008 also counts the dissipation phase: demand falls to zero "in order to have an empty system again" (PDF text lines 429-433, 636-638). There the regulator stays active and releases on its own as the queue clears (lines 515-520). Counting the drain is therefore standard. Switching the meter off while a large queue still stands is not what the cited source does.

(4) Causation. The share of the gain that comes after 940 s is accounting, not proof of an artefact. Per seed, the delay difference correlates at 0.96-0.98 with the difference in leftover vehicles, which is throughput won during control. For block_q1600 and C1, re-pricing the drain on the paper's own metric leaves the results unchanged:
- block_q1600 IP vs ID: 19.8-22.4 %, rule (a) passes under every pricing;
- C1: 16.2-18.0 %, passes under every pricing;
- block_q1600 IP vs PI: 16.6-18.0 %.

So the S1b verdict (it passes through block_q1600) and C1 survive. The title's word "carries" is too strong for these rows, which FU1-F5 itself concedes.

(5) slow_q2000. Part of the arm effect at equal leftover count comes from a state that the control itself produced. ID's set point leaves 19.5 vehicles on edge 4, against 7.9 for IP. Adding that count to the pooled drain model shrinks the arm-specific share from 43 % to 28 % of the post-940 difference. Even so, on the delay metric this cell's 11.8 % falls below the rule (a) bar under 3 of 4 alternative drain pricings (6.8 %, 9.3 %, 9.9 %) and passes only at k = 0.75 (10.6 %). Window TTT gives 1.7 %.

So the problem survives. The paper's numbers are correct on the pre-registered metric, but the end-of-horizon convention and the pre-registered throughput/TTT co-headline are missing from the paper. The second S1b cell named in the text (slowdown at 2000 veh/h) also depends on how the uncontrolled drain is priced. The headline verdicts survive, so the severity is major, not critical.

FU1-F4's implied drain rates (806-858 veh/h) depend on the fit. My quadratic terms give about 833-858 veh/h, but the fitted linear term is negative and not physical, so I treat those rates as unverified.

Checks: Read v5b/p1b/episode.py, v5b/d1/sumo_runner.py and v5b/d1/plant.py at 93ba655; grepped v5b/d1/episode.py and v5b/p1/episode.py at 93ba655 for the drain convention; git diff 93ba655..e7dd561 on these files (empty); Grepped all protocols, results notes and decisions.md for drain, all-green, TTT and throughput; Read paper.qmd:85-203; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/DRAIN-defend/drain_defend.py (output drain_defend.out): delay/window/full rels, post-940 share, n_left, pooled drain model with and without the downstream-state term, P1b v108 and C1 v114 raw runs; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/DRAIN-defend/delay_reprice.py (output delay_reprice.out): drain re-pricing on the paper's delay metric with rule (a) at the S1 or C1 level, B=20000; pdftotext of papers/refs_papers/1-s2.0-S0968090X07000873-main.pdf into /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/DRAIN-defend/pap/pap2008.txt; read the simulation-scenario passages only, not the full paper

#### Verifier R2 impact: CONFIRMED / major

I took the core fact as true and checked it myself from the code that ran and the raw runs. At v5b/p1b/episode.py@93ba655 the demand exists only for 0-940 s (plant.demand(..., [(0, warmup_s+control_s, q)])). After the control loop the code calls inc.clear(), then plant.set_all_green(), then sim.drain(7200). The run metrics delay_s and ttt_full_vehh are taken after this drain. In P1b, at 940 s about 30-45 % of the generated vehicles are still in the system (median n_left 118-236).

What changes in the paper:
(1) Table II and every headline number stay the same. They are computed on the pre-registered metric. D2 A4 h says 'departDelay + timeLoss after the drain', and P1 §5 line 85 adopts it. So this is not a protocol deviation, and the paper's pre-registration statement is not falsified. The meter release to all-green is not written explicitly in any protocol, though. It is only in the frozen code, and P1 protocol line 168 implies that the drain is uncontrolled ('restored before the drain').
(2) The pre-registered verdicts do not change. I re-ran S1a, S1b and C1 on four metric variants: the paper metric; a 'window floor' where the post-940-s difference is equalised; a common meter-on drain price n·60 s + n²/(2μ) with μ = 1000-1300 veh/h (an assumption); and the drain difference scaled by k. S1a fails on every variant. S1b passes on the paper metric and on every μ variant through block_q1600 (19.2-22.1 %, LCB > 0). S1b keeps (a) in block_q1600 down to k = 0.15. Only the zero-price window floor makes S1b fail, and that floor is too pessimistic because it gives no cost to extra leftover vehicles. C1 stays at or above 16.5 % under every μ and holds down to k = 0.05. It drops to 9.5 % only at k = 0.
(3) The slowdown-2000 S1b number is fragile. Its (a) condition fails once the drain-phase difference shrinks by 20 % (k = 0.80 gives 9.8 %). Under a common meter-on price it is 5.7-6.5 %, and the window part alone is 1.0 %. So the sentence at paper.qmd:155, which names slow_q2000 (11.8 %) as one of two S1b cells, would need a caveat. Table II's bold on that cell is correct for the metric as defined, but it depends on the release convention. With this check the defect is a real disclosure gap. The sentence at line 110 is true but incomplete: it does not say that demand stops at 940 s or that the meter goes to all-green. The interpretation of the slowdown-2000 gain as an information effect is also unsupported.

Severity: major fits, not critical. A reviewer would require the convention to be stated and the slowdown-2000 claim to be qualified, but S1a, S1b and C1 survive. Two things reduce the practical impact: the Discussion/Limitations section is still empty, so the disclosure can be added, and NC is not in the paper text, so FU1-F4 (PI vs NC on the window: −3.1 % in block_q1600) affects only the words 'strong always-on control'. My proxy prices are modelling assumptions. The decisive test needs new runs with the meter kept on during the drain, which I did not run (no SUMO).

Checks: Read paper.qmd lines 1-203 (method line 110, results lines 155, 165-176, C1 line 186, empty Discussion); git show 93ba655:v5b/p1b/episode.py (run_episode: demand horizon, set_all_green, inc.clear, drain, metric fields); git show 93ba655:v5b/d1/sumo_runner.py (tts_system accumulation incl. pending vehicles; drain); grep of protocols p1_incident_information.md, p1b_addendum.md, p1b_confirm_c1.md, screen_D2_incidents.md, screen_D1_detector_faults.md for drain / all-green / metric definition; grep of docs/decisions.md and results notes for drain convention (only V49, an unrelated earlier episode decision); Read frozen arms from ~/work/phd/v5b1_runs/p1b/v108/result.json (tune.arms); /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/DRAIN-impact/impact.py -> impact.out: own bootstrap (B = 20,000) on raw P1b v108 and C1 v114 runs; rel and LCB on paper metric, window floor and meter-on proxies; S1a/S1b re-evaluated per variant; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/DRAIN-impact/kscale.py -> kscale.out: break-even k for the drain-difference scaling (slow_q2000, block_q1600, C1)

### B8. [major] G2-F2: C1/crawl gains come from L0/ID laws over-holding all four lanes (the crawl lane inflates the edge-4 count; no lane changes); untested with lane changing

Raised as major; verification: reproduce: CONFIRMED/major, defend: CONFIRMED/minor.

#### G2-F2 (R2 G2, major, unsupported-interpretation): The IP-vs-PI and IP-vs-ID gains in the crawl cell come from L0/ID laws over-holding all four lanes, triggered by the crawl lane inflating the edge-4 detector

- **Description.** All meter arms switch the four lanes with one signal state (GGGG/yyyy/rrrr). The laws read the vehicle count on both lanes of edge 4. During the crawl, vehicles stored on 4_1 push that count from about 8 to 20-26 under every arm. PI (n_crit 8, K_I 120) reaches the 200 veh/h floor about 120 s after onset and stays there until clearance. ID and FB (f40_10, n_crit 10) and AD also reach 200. IP's law (n_crit 16, K_I 20) keeps q at about 1800-2000 for the first 3 minutes. Vehicles entering edge 4 during the incident (P1b median): PI 46, FB 63, AD 63, ID 66, IP 84.5, NC 83.5. C1: PI 45, IP 85, NC 85. IP lets more in than PI in 100/100 (P1b) and 99/100 (C1) seeds. Spearman(d delay, d entries) is 0.73 (P1b IP-PI), 0.67 (C1) and 0.80 (IP-ID). In the 2 spot seeds, PI cut free-path exits during the incident from 724 to 424 and from 548 to 213 veh/h, and 61 % and 90 % of IP's time-loss lead fell on vehicles bound for the free lane 4_0. On tuning seeds, an always-on gentle law (p20_20_16_e4) matches the IP plan in the crawl cell (222.0 vs 224.7, PI 293.4) but loses in the slowdown cell (226.7 vs PI 189.4). So the type is used to avoid a detector-driven over-hold. The paper does not describe this mechanism.
- **Evidence.**
  - G2/g2_mechanism.out
  - G2/g2_actions_traj.out (trajectories of q and n)
  - G2/g2_spot_lanes.out
  - v5b/p1b/meters.py@93ba655:34, 72-79, 104-112
  - v5b/p1/family.py@93ba655:11-13, 33
  - docs/research/results/p1b_result.json tune.arms['1600']
- **Failure scenario.** The paper reads C1 and S1b block_q1600 as evidence that type information generally pays for mainline metering. The measured effect is that a pooled-tuned law with a low set point on an edge-4 count chokes a free lane, which the plant's lane split leaves unaffected by the crawl.
- **How to test.** Re-run G2/g2_mechanism.py and G2/g2_actions_traj.py. With SUMO (the author's call): run IP and PI with a detector on lane 4_0 only, or with the edge-4 count excluding 4_1, and check whether the IP-PI gap closes.
- **Related claims.** C71, C37

#### G2-F4 (R2 G2, major, hidden-assumption): Whether the gain survives a blockage with lane changing is untested, and the mechanism suggests it may not

- **Description.** Speculation, labelled as such: the gain relies on three plant features. (i) With lane changing off, the crawl path and the free path are separate pipes, so holding at the meter cannot raise crawl throughput and can only starve 4_0. (ii) The edge-4 detector counts the stored crawl lane as congestion. (iii) After clearance, the stored lanes-2/3 platoon breaks down the 2->1 zipper unless it is held back (N/FX: the edge-4 count reaches 60 in 95-97 % of runs). With lane changing, blocked-lane vehicles would merge into 4_0. Edge 4 would then act as one lane in front of an already one-lane edge 5, and holding during the incident could protect that merge, as in the slowdown cell, where the strong law wins. The relative ranking of the gentle and strong laws, and so the value of the type, could shrink or flip. No run tests this.
- **Evidence.**
  - G2/g2_none_check.out (N c1800 block: max edge-4 count 60 in 95 % of runs; FX 97 %; feedback arms 0 %)
  - G2/g2_mechanism.out (tuning: gentle vs strong law, block vs slow)
  - v5b/d1/plant.py@93ba655:8 (BN4-L variant exists: lane_changing=True)
  - docs/decisions.md V129 (roadmap: 'second geometry with real lane closure')
- **Failure scenario.** C1 is replicated on a plant with lane changing, or in the field, and the type-plan advantage disappears because the incident becomes a capacity reduction in which strong holding is best.
- **How to test.** The author decides whether to spend SUMO time: a small spot set on BN4-L (plant.vtypes_xml(lane_changing=True)) in the block cell at q=1600 with IP, PI, ID and NC; compare entered_e4_incident, the edge-4 count trajectory and the delays. Until then, state the dependence as a limitation.
- **Related claims.** C71, C36

#### G2-F1 (R2 G2, major, hidden-assumption): The crawl acts on the upstream 2-lane edge and forces about half the inflow through one lane; the paper does not say this

- **Description.** Paper line 114 says both incidents 'act on the bottleneck'. Line 110 says only that a blockage 'is represented by a crawling lane'. In the code, the crawl sets the whole 240-m lane 4_1 (the left lane of the 2-lane edge 4) to 1 m/s; the slowdown is the one on the 1-lane edge 5. Lanes 3_2 and 3_3 connect only to 4_1, and lane changing is off. So every vehicle that departs on lanes 1_2 or 1_3 (0.49-0.52 of vehicles) must cross the crawl lane. During the incident that lane releases only 0-122 veh/h. The D2 protocol disclosed this crawl as more severe than a closure (1.3-2.4 times the delay), with 'results speak only about that crawl'. That caveat is not in the paper.
- **Evidence.**
  - G2/net_read.out (connections and lane lengths from the cached net)
  - v5b/d2/incidents.py@93ba655:28-29, 64-69
  - v5b/d1/plant.py@93ba655:25-29, 34
  - docs/research/protocols/screen_D2_incidents.md:91-96
  - G2/g2_spot_lanes.out
  - paper.qmd:110, 114
- **Failure scenario.** A reader or reviewer pictures a local blockage that drivers can avoid by changing lanes, and generalises the crawl-cell results (S1b 22.0 %, C1 16.2 %) to real lane blockages. The simulated incident is a forced, walking-pace pipe for half the demand.
- **How to test.** Read incidents.py and the net connections. Count depart lanes 1_2/1_3 in any tripinfo file. Then fix the text: name edge 4 / lane 4_1 and the 240 m, state the 3_2/3_3->4_1 split, and carry over the D2-A2 caveat.
- **Related claims.** C37, C36

#### Verifier R3 reproduce: CONFIRMED / major

I recomputed every number in G2-F2 with my own code from the raw P1b runs (v108, evaluation seeds 7400600-699, k=0), the C1 runs (v114, seeds 7400700-799), the cached net, and the spot tripinfo files (hashes equal to the raw C1 runs). All the cited numbers reproduce exactly or within rounding:
- entries onto edge 4 during the incident;
- the 100/100 and 99/100 seed counts;
- the Spearman values 0.727 / 0.668 / 0.796;
- PI reaching the 200 veh/h floor about 126 s after onset;
- IP's q at 1800-2050 in the first 180 s;
- free-path exits 724->424 and 548->213 veh/h, with free-lane shares of IP's lead 61.4 % and 89.8 %;
- the tuning medians 222.0 / 224.7 / 293.4 (crawl) and 226.7 vs 189.4 (slowdown).

The code facts also hold:
- the signal state is one 4-character string for all lanes (meters.py@93ba655:34);
- every law reads ls.edge.getLastStepVehicleNumber on edge '4', which counts both lanes (episode.py@93ba655:147-150, meters.py@93ba655:75-84, 104-112);
- the net connects 3_2/3_3 only to 4_1;
- lane changing is off (lcStrategic=-1 and the other lc* parameters set to 0 in both vTypes).

The paper does not give the mechanism. Its Discussion section is empty. Line 118 says only 'downstream vehicle count'; it does not say this is the edge-4 count that includes the crawl lane. The headline numbers are unchanged, so major (not critical) fits.

Small corrections to the finding's wording:
1. Before onset the edge-4 count is about 6-7 (median), not 8. About 9-10 is the first minute after onset. It reaches 20-26 only after about 4-5 minutes. Under PI it peaks near 20-21.
2. 'Stays at 200 until clearance' holds in 83/97 (P1b) and 90/96 (C1) of the PI runs that reach the floor.
3. ID, FB and AD reach 200 in only 65-69 % of runs, and later (median about 234 s after onset).

Weaker than presented:
4. Incident duration drives both the delay gain and the extra entries. With duration held fixed (partial rank correlation), the link drops from 0.73 to 0.44 (P1b IP-PI), from 0.80 to 0.41 (IP-ID) and from 0.67 to 0.17 (C1). So the Spearman figures add little to the causal story.
5. In a third spot seed (7400750, from G3, 151-s incident), PI also cut free-path exits (763 -> 429 veh/h), but PI won on delay (168.6 vs 188.7 s/veh). Starving the free lane is therefore not the whole story; duration and what happens after clearance matter too.
6. That the count rise comes from vehicles stored on 4_1 is inferred, not measured: no per-lane log exists. Under N the median count reaches 31-44 late in long incidents. Lane 4_1 holds at most about 34 vehicles (240 m / 7 m spacing), so 4_0 must then hold queued vehicles too.

The core fact is reproduced: PI and the ID/FB/AD laws throttle all four lanes because the edge-4 count rises during the crawl, while IP's gentle law lets about 85 vehicles in versus PI's 45. 'The gain comes from over-holding' remains a well-supported interpretation, but it is not proven. Proving it needs the counterfactual SUMO run the finding proposes.

Checks: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify3/G2-F2-reproduce/mech.py -> mech.out (entries, paired counts, Spearman, q/n trajectories, C1 rel, tuning medians, from raw JSONs); /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify3/G2-F2-reproduce/lanes.py -> lanes.out (net lanes and connections, vType lc parameters, per-lane-group exits and time loss in the REPRO and G3 spot tripinfo files, hash check against the raw C1 runs); /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify3/G2-F2-reproduce/partial.py -> partial.out (partial rank correlation with duration held fixed; edge-4 count profile per arm); git show 93ba655:v5b/p1b/meters.py, v5b/p1b/episode.py, v5b/p1/family.py, v5b/d1/plant.py (read only); grep of bn4.net.xml for tlLogic and the tl connections; grep and read of paper.qmd lines 60-203 for any mechanism or detector description; Read the tuned arms in docs/research/results/p1b_result.json and the tuning rule in p1_incident_information.md:31-43

#### Verifier R3 defend: CONFIRMED / minor

Verdict: the facts in the finding hold up, but my best defence removes the "major / unsupported interpretation" charge. What is left is a minor gap: the paper does not explain the mechanism and leaves out some scope notes. The draft's Discussion and Limitations section is still empty, which is where these notes belong.

The defence works on four points:
(1) The paper makes no claim of generality. Line 69 limits it to "one microsimulated bottleneck". The C1 sentence (line 187) states exactly the narrow question of the C1 protocol: does IP beat always-on PI in block_q1600? So the failure scenario ("the paper reads C1 as type info generally pays") attacks a statement the paper does not make.
(2) The mechanism the auditor found is what the pre-registered design means by "type value". All L0 arms and ID are tuned per q on the pooled incident mix, with no type information (p1_incident_information.md:43). The auditor's own tuning numbers show the trade-off: the strong law wins the slowdown, the gentle law wins the crawl, and only the type lets a meter use both. Saying "type is used to avoid an over-hold" describes how type information pays. It does not show an artefact.
(3) The "detector inflation" framing is incomplete. The pre-registered L0 grid already held 90 PI laws on the edge-5 count, which the vehicles stored on 4_1 do not inflate. In the crawl cell on tuning seeds every one of them did badly (best 307.2 s, against 224.7 s for the IP plan and 313 s for no metering). The winning crawl law still reads edge 4: it needs that count to hold traffic after clearance (IP beats NC in 97/100 C1 seeds; its peak edge-4 count after clearance is 32.5, against 60 under N). So the gain comes from a type-specific set point, not from ignoring edge 4. The test the auditor proposes, a detector on lane 4_0 only, would build in knowledge of which lane is blocked, and that is incident information.
(4) Some of the auditor's support for the mechanism is confounded by incident duration. Duration is fixed before treatment and drives both d(delay) and d(entries). In C1 the Spearman 0.67 falls to a partial 0.17 once duration is controlled for; in P1b, 0.73 falls to 0.44 (IP-PI) and 0.80 to 0.41 (IP-ID). The direct observations from the meter logs still stand: under PI, q sits at the 200 veh/h floor during the crawl, and edge-4 entries are 45 for PI against 85 for IP.

Disclosure already in place: line 110 states that lane changing is off. Fig. 1 (fig_plant.py:29-30) draws the crawl on one lane of the 2-lane edge. Line 93 defines the bottleneck as the whole 4-to-1 zone, so "act on the bottleneck" is defensible. The results note p1b_result.md:80 already says "one plant; the block incident is a substitute (1 m/s lane crawl, no lane changes)", and :75 says it "cannot say ... generality".

What survives the defence:
- The paper text never says that, with lane changing off, lanes 3_2 and 3_3 feed only 4_1, so about half the inflow must pass the crawl lane.
- The paper does not carry over the D2-A2 caveat (screen_D2_incidents.md:91-96): the crawl is 1.3-2.4 times as severe as a closure, and "results speak only about that crawl".
- The paper does not explain why IP wins in the crawl cell.
- Whether the result holds with lane changing on is untested. This belongs in the Limitations section.
None of these is a false statement or an undisclosed deviation, so the right level is minor (a missing detail).

Two related observations (info, outside this group):
- With an equal-weight criterion (the mean of the two per-type medians), the always-on law p20_20_14_e4 would have been chosen as the L0 PI arm (216.0 s, against 241.4 s for p70_120_8_e4). On tuning seeds it is within 1 % of IP in the crawl cell (222.5 against 224.7). So the cell where type information pays depends on the pooled tuning rule. Under the pre-registered pooled median, the comparison is valid as it stands.
- IP loses to PI for short incidents: 6/33 wins in C1 and 8/33 in P1b in the shortest duration third. This is a post-hoc subgroup, but it is consistent across both data sets.

Checks: Read the G2-F2 group (round3_input.json) and the auditor outputs G2/g2_mechanism.out and g2_mechanism.py; Read paper.qmd in full (203 lines) at HEAD (last change 4de404a); Read v5b/p1b/meters.py@93ba655, v5b/p1/family.py@93ba655, v5b/d2/incidents.py@93ba655:1-30, v5b/d1/plant.py@93ba655:1-40; Read p1_incident_information.md (tuning rules), p1b_confirm_c1.md, screen_D2_incidents.md:85-100, p1b_result.md:70-95, fig_plant.py; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify3/G2-F2-defend/d1_tuning_tables.py (ranks e4 against e5 PI laws in the committed P1b tuning tables) -> d1_tuning_tables.out; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify3/G2-F2-defend/d2_c1_mechanism.py (own recomputation from the C1 raw runs: medians, edge-4 counts, q floor, duration-confound partial Spearman, IP vs NC) -> d2_c1_mechanism.out; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify3/G2-F2-defend/d3_e5_per_type.py (per-type tuning-seed delays of all 90 e5 PI laws and 4 e4 laws from the P1b v108 raw runs) -> d3_e5_per_type.out; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify3/G2-F2-defend/d4_p1b_partial.py (P1b eval block_q1600: Spearman(d delay, d entries) controlled for incident duration, and per-duration-third results) -> d4_p1b_partial.out

### B9. [major] G2-F3: Exploratory: the type-plan gain over PI/ID reverses for incidents shorter than about 230 s and grows with duration (replicated on P1b and C1 seeds)

Raised as major; verification: reproduce: CONFIRMED/major, defend: CONFIRMED/major.

#### G2-F3 (R2 G2, major, unsupported-interpretation): Exploratory: the type-plan gain over PI/ID reverses for short incidents and grows with duration

- **Description.** This split was not pre-registered; I fixed the 300-s midpoint before looking. C1 IP vs PI: incidents of 120-240 s give rel -19.2 % [-45.5, -6.5]; 240-360 s give +23.7 %; 360-480 s give +33.8 %; Spearman(duration, d delay) = 0.78. P1b block_q1600 IP vs PI: -30.4 % [-43.6, -12.0] for 120-240 s, +32.5 % for 360-480 s. IP vs ID: -10.2 % [-16.8, -3.2] for 120-240 s, +30.6 % for 360-480 s. IP vs NC is flat across durations (about 26-34 %). The headline 16.2 % is thus an average over U(120, 480) s that mixes a loss on short incidents with a large gain on long ones. This fits the over-hold mechanism in G2-F2: PI's choke lasts until clearance.
- **Evidence.**
  - G2/g2_duration_split.out
  - G2/g2_c1_recheck.out
- **Failure scenario.** For a different incident-duration mix (for example, mostly short crawls), the type plan would be worse than always-on PI. The paper's C1 sentence and Fig. c1 imply a uniform lead.
- **How to test.** Re-run G2/g2_duration_split.py. Report it as exploratory, and state that the result depends on the duration distribution.
- **Related claims.** C71

#### Verifier R3 reproduce: CONFIRMED / major

I reproduced the core fact with my own code, working from the raw runs. In the lane-crawl cell at 1600 veh/h, the gain of the type plan IP (c1800-p20_20_16_e4) over always-on PI (p70_120_8_e4) depends strongly on incident duration. IP loses for short incidents and gains a lot for long ones. This holds in both P1b (seeds 7,400,600-699) and C1 (seeds 7,400,700-799).

All of the finding's numbers hold, up to bootstrap noise of about 0.2 points:
- C1, IP vs PI: -19.2 % [-45.6, -6.5] for 120-240 s, +23.7 % for 240-360 s, +33.8 % for 360-480 s. Spearman(duration, delay difference) = 0.78.
- P1b, IP vs PI: -30.4 % [-43.6, -11.8] for 120-240 s, +32.5 % for 360-480 s.
- P1b, IP vs ID: -10.2 % [-16.8, -3.2] for 120-240 s, +30.6 % for 360-480 s.
- IP vs NC stays at 26-34 % in every bin.
- My overall values match the run outputs and the paper: 18.0 % (IP vs PI, P1b), 22.0 % (IP vs ID, P1b), 16.2 % [7.3, 23.7] (C1). So I selected the same arms and the same data.

The pattern does not depend on the chosen bin edges:
- With 60-s bins, C1 IP vs PI rises from -63.7 % (120-180 s) to -0.5 %, 18.7 %, 28.8 %, 31.3 % and 33.7 % (420-480 s).
- In the C1 120-240 s bin, IP is better than PI in only 22 % of the seeds. In the 360-480 s bin it is better in 100 %.

Pairing and data integrity are fine:
- Each seed has the same duration in every arm.
- The duration_s values match exactly my own regeneration of the seeded draw, default_rng(seed+3301), second U(120, 480) draw (v5b/d2/incidents.py@93ba655:30-39).
- No run is invalid in any arm used here.
- The incident code did not change between 93ba655 and e7dd561.

Neither the protocols nor the paper pre-register or mention a split by duration:
- The only duration text in the protocols is the U(120-480) definition at p1_incident_information.md:23.
- The paper gives only the distribution (paper.qmd:114), and its Discussion section is empty.
- So the C1 sentence (paper.qmd:187) gives one number and does not say that the lead reverses for short incidents.

Severity stays major, not critical. The C1 verdict as pre-registered (average over U(120, 480)) is computed correctly, so the headline survives. But the paper's framing that the type plan leads PI is unsupported for short crawls, and a reviewer would require this to be disclosed.

Caveats:
1. The split is post hoc and covers several subsets and comparisons. The auditor's statement that the 300-s midpoint was fixed "before looking" cannot be verified. The continuous Spearman result and the 60-s bins make this less important.
2. Wording: the 16.2 % is a ratio of medians of paired differences, not an average. Calling it "an average that mixes" short and long incidents is loose but fair in substance.
3. Durations below 120 s were never simulated, so "mostly short crawls" is supported only inside 120-240 s.
4. I did not re-check the over-hold mechanism (G2-F2) under this lens.

Checks: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify3/G2-F3-reproduce/dur_split_check.py (output: same dir, dur_split_check.out): own loader, paired bootstrap with a different RNG seed and B, scipy Spearman, three duration sources, 60-s bins, validity check; Compared my overall rels with ~/work/phd/v5b1_runs/p1b/v108/result.json (eval.S1.per_cell_stats) and p1b_c1/v114/result.json (c1.C1); Read v5b/d2/incidents.py@93ba655:1-80 and v5b/p1b/episode.py@93ba655:140,266; git diff 93ba655 e7dd561 on the incident and episode code (no change); grep for duration or subgroup text in the three protocol files and in papers/paper_1/paper.qmd; Read G2/g2_duration_split.py and its .out for comparison only; it was not reused

#### Verifier R3 defend: CONFIRMED / major

I tried the usual defences. Almost none of them remove the problem.

(1) Selection on a post-treatment variable: does not apply. The duration is drawn from rng(seed + 3301) (v5b/d2/incidents.py@93ba655:34-39). It is the same in every arm. I checked this in the raw JSONs: duration, onset, crawl lane, t_on and t_off are identical across arms for all 100 seeds, in both P1b and C1.

(2) Small subgroups, multiple testing, choice of bins: the pattern replicates on two independent seed sets (P1b eval 7,400,600-699 and C1 7,400,700-799).
- Spearman(duration, PI-IP) is 0.74 and 0.78, permutation p < 1e-4.
- An OLS crossover, which does not depend on bins, falls at 231 s [204, 252] and at 233 s [212, 249]. About 31 % of U(120, 480) lies below it.
- For the 120-240 s bin, the 99 % CI excludes 0 in both seed sets.
- In C1, for incidents of 120-180 s, IP is worse than PI in 18 of 18 seeds.

(3) Confounds: the crawl lane is always 4_1. Onset is not correlated with duration (Spearman 0.07-0.09). No pair contains an invalid run.

(4) A disclosure elsewhere: none. The paper, the results notes, the protocols and decisions.md never mention a dependence on duration.

What the defence does establish:
(a) The C1 sentence is true as a statement about the median over the duration law U(120, 480). The paper discloses this law in line 114, and the protocol pre-registered it. No sentence in the paper claims a lead at every duration. Fig. c1 covers detection delay and runners, not duration. The Discussion section is still empty. So the auditor's phrase "C1 sentence and Fig. c1 imply a uniform lead" is overstated. The issue is an omission, not a false statement.
(b) The frozen IP plan was tuned for this duration mix. For a mix of mostly short incidents, the plan would be retuned. The failure scenario therefore applies to this frozen plan, not to type information in general.
(c) The reversal of IP vs ID is weaker than the auditor states. It rests on P1b only, because C1 has no ID arm. The 99 % CI for 120-240 s is [-19.8, 0.7], and the CI for the pre-fixed 120-300 s split is [-9.3, 4.9]. Also, with the pre-fixed 300-s split, the P1b IP-vs-PI short bin is not significant ([-29.2, 2.7]). The strong numbers in the finding come from the three-bin split. The continuous crossover analysis does support them.

Net result: the headline C1 median of 16.2 % stands. The type plan's lead over always-on PI is a long-incident effect, and it reverses for incidents below about 230 s. A reviewer would require this to be reported, because it qualifies the paper's answer to "does knowing the type pay". It should go in the Discussion as an exploratory, not pre-registered, result. Severity stays major, as an undisclosed result property; the headline survives.

Checks: Read groups['G2-F3'] from round3_input.json, plus G2/g2_duration_split.py and its .out file; Read paper.qmd lines 1-203: intro, design (line 114), results (lines 155, 187-197); the Discussion is empty; git show 93ba655:v5b/d2/incidents.py and v5b/p1b/episode.py: the incident draw depends on the seed only; git show e7dd561:v5b/p1b/confirm_c1.py: definition of the C1 statistic; grep for duration, subgroup and exploratory in the protocols (p1, p1b_addendum, p1b_confirm_c1), docs/research/results/*.md and docs/decisions.md; Own script /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify3/G2-F3-defend/dur_defend.py (output in dur_defend.out in the same dir). It checks the per-seed identity of the incident across arms, recomputes bins at 95 % and 99 % with the invalid-run view, runs a Spearman permutation test, a bootstrap of the OLS crossover, and onset and lane confound checks, for P1b (PI, ID, NC) and C1 (PI, NC)

### B10. [major] G3R-F1: The 200 veh/h floor (135-s reds on all four lanes) has no stated reason, is far below the paper's own cited source, binds in every C1 PI run and alone sets PI's rate there; the paper does not disclose this

Raised as major; verification: not adversarially verified.

#### G3R-F1 (R3 G3R, major, methodology-disclosure): The 200 veh/h floor (135-s reds on all four lanes) has no stated reason, is far below the paper's own cited source, binds in every C1 PI run and alone sets PI's rate there; the paper does not disclose this

- **Description.** Q_MIN = 200 gives c(200) = 144 s, so red lasts 144 - 6 - 3 = 135 s, on all four mainline lanes at once (one state for all lanes). The value is a code default inherited from the archive BN4 FBMeter. The protocols leave q_min as a symbol and no decision record sets or justifies 200. It binds in almost every feedback arm and cell. In the confirmatory cell it, not the PI law, sets PI's rate for about 29 % of updates. The per-seed C1 gain rises with PI's time at the floor. The paper's own source for mainline/work-zone metering, Papageorgiou et al. 2008, uses floors of about 43 % of capacity, which give reds of about 18-20 s, with lane groups offset to avoid releasing all lanes at once. Here 200 veh/h is about 14 % of the metered clean-day served flow. Paper line 110 states the bounds [200, 2618] and c(q), but never says that this allows 135-s reds, how often arms sit there, or why 200 was chosen. A higher floor would cap PI's over-holding during the crawl, so the C1 gain (16.2 %) and the 22.0 % S1b entry would probably shrink; the size is unknown without SUMO. This is pre-registered by the frozen code, and the S1b verdict also passes on slow_q2000, which does not depend on the floor, so the verdicts as run stand.
- **Evidence.**
  - v5b/p1b/meters.py@93ba655:31 'Q_MIN, Q_CAP = 200.0, 2618.0'; :37-38 cycle_s = max(11, 2*M*3600/q); :41-42 G<6, y<9, else r; :34 STATES 'rrrr' (all four lanes); :87-88 clip
  - Origin: same default q_min=200.0 in v5b/d1/episode.py@93ba655:46 (D1 FBMeter), ported from claude/vsl-lab-core@2a79e5e:vsl_lab/envs/bn4_env.py:42 (q_min=200.0, q_max=4000.0)
  - Protocols: p1b_addendum.md:68 'every law clips q to [q_min, 2,618] veh/h' (no value); decisions.md:127 (V108) decides only the 2,618 cap; p1_incident_information.md:187 'a red never exceeds c(q_min) - green = 138 s' (implies 200, gives no reason); docs/architecture/port_map_v0.md:365 calls the archive clamps (q_min 200) 'a lab addition, not in the paper'
  - Floor use, C1 (G3R/g3r_floor.out): PI 100/100 runs, median 8 of 29 updates (240 s), max 14, median longest stretch 210 s; IP 87/100, median 3. In P1b block_q1600: PI 100/100 (median 8), ID 97 (6), FB 97 (5), AD 97 (5.5), IP 84 (3). slow_q1600: FB/PI/AD/ID 95-98/100; slow_q2000: N(f10_8) 85, FB 99, PI 63, AD 100, ID 25, IP 42; block_q2000: 78-97 for the law arms
  - Where (G3R/g3r_floor_when.out): PI floor time C1 69 % during the incident, 30 % after clearance; IP 9 % during, 91 % after clearance (P1b: 19 % / 81 %)
  - Unclipped command (G3R/g3r_unclipped.out, exact re-computation of meters.py@93ba655:110-111): C1 PI at the floor in 792/2700 updates; the unclipped q there is < 0 in 90 % (median -830 veh/h); P1b 813/2700, 91 %
  - Per-seed C1 gain IP vs PI: Spearman with PI floor updates 0.84; with duration 0.78; PI floor vs duration 0.92; partial(gain, floor | duration) 0.48; partial(gain, duration | floor) 0.05; inside duration terciles 0.73/0.64/0.41. 10 seeds with <= 3 floor updates: median gain -89.6 s/veh, rel -90.9 % (median duration 147 s). P1b block_q1600: IP vs PI 0.82 (partial 0.54), IP vs ID 0.86 (partial 0.58). slow_q2000 IP vs ID: 0.02
  - Papageorgiou et al., TR-C 16 (2008) 535-553 (paper ref Papageorgiou2008; local PDF papers/refs_papers/1-s2.0-S0968090X07000873-main.pdf, text via pdftotext into G3R/refpdf/ref.txt): toll plaza 'T = 30 s ... qmin = 4500 veh/h and qmax = 13,000 veh/h' with qcap about 10,500 (15 lanes, red at qmin about 20 s) and lane groups offset 'to avoid bursty entering flows'; work zone 3->1 lanes 'qmin = 1000 veh/h, qmax = 3000 veh/h' with qcap about 2300 (red at qmin about 17.6 s)
  - Plant flow (G3R/g3r_capacity.out): N c1800 clean-day served median 1444 veh/h (max 1640); NC edge-4 entry during crawl 1024 veh/h; 200/1444 = 14 %
  - Paper line 110: 'the commanded rate is limited to [200, 2618] veh/h' and 'at least 2 s red' (no maximum); line 149: runners ignore only amber and the first 1.5 s of red
- **Failure scenario.** A reviewer asks whether a mainline meter would ever hold all four freeway lanes on red for 135 s, several cycles in a row, and why the floor is about one third of the cited source's ratio. With a realistic floor (for example 400-600 veh/h) or a maximum red, PI can no longer over-hold during the crawl. The C1 gain and the 22.0 % block_q1600 S1b entry could fall, possibly below the 10 % bar; this is not measured.
- **How to test.** Without SUMO: run G3R/g3r_floor.py, g3r_floor_when.py and g3r_unclipped.py (outputs .out next to them). Decisive, and the author's call: a SUMO spot set for C1 (PI, IP) and P1b block_q1600 (PI, ID, IP) with Q_MIN at 400 and 600 veh/h, or a maximum red of about 20-60 s, with PI re-tuned under the new floor. Report the gain under both floors. In the paper, add one sentence giving the red at the floor, how often each arm reaches it, and why the floor was chosen.
- **Related claims.** C71, C66, C35, C85, C72

#### G3R-F5 (R3 G3R, info, audit-correction): Correction to the critic: IP does reach the floor in block_q1600, mostly after clearance; 'min q 970' is the median minimum during the incident only

- **Description.** CG2-2 says that in P1b block_q1600 'IP's minimum is 970' (G2/g2_mechanism.out qmin_inc). That figure is the median, over seeds, of the minimum q during the incident only. Over the whole run, IP reaches 200 in 84/100 P1b seeds and 87/100 C1 seeds; 81 % (P1b) and 91 % (C1) of its floor time comes after clearance. So a higher floor would also constrain IP, mainly in the post-clearance phase, and the direction of the effect on the gain is less certain than CG2-2 suggests. PI's floor time (69-73 % during the incident) would be constrained more.
- **Evidence.**
  - G3R/g3r_floor.out: P1b block_q1600 IP '>=1' 84, qmin=200 in 84 runs; C1 IP 87
  - G3R/g3r_floor_when.out: IP floor time before / during / after = 0 / 19 / 81 % (P1b), 0 / 9 / 91 % (C1); PI 1 / 73 / 26 % (P1b), 1 / 69 / 30 % (C1)
  - G2/g2_mechanism.out: IP qmin_inc 970.0 (incident window only)
- **Failure scenario.** A floor-sensitivity run designed on the belief that IP never reaches the floor would read IP's post-clearance change as unexpected.
- **How to test.** Run G3R/g3r_floor_when.py.
- **Related claims.** C71, C72

### B11. [major] G5-F1: Pre-registered S3 rows omitted: p*, f* (paper outputs under A10) and the combined row; under d=60, c=60, p=0.2 IP has no CI above zero vs the strongest L0 arm in any cell

Raised as major; verification: reproduce: CONFIRMED/major, defend: CONFIRMED/major.

#### G5-F1 (R2 G5, major, missing-evidence): Pre-registered combined row omitted: under d=60, c=60, p=0.2, IP is not ahead of the strongest always-on arm in any cell

- **Description.** The combined row is a pre-registered S3 output (protocol §4, §6). It is computed and stored as vs_L0 and vs_IP (analysis.py@93ba655:558-562) but appears nowhere in the paper. Compared with the strongest L0 arm it gives:
- slow_q1600: -52.0 % [-65.4, -40.1] vs PI
- slow_q2000: +2.7 % [-1.5, 8.0] vs PI
- block_q1600: +0.5 % [-6.1, 7.8] vs FB and +5.9 % [-0.9, 16.8] vs PI
- block_q2000: -7.0 % [-10.2, -3.4] vs PI
One imperfection at a time in block_q1600 (the C1 cell): d60 alone gives vs FB +11.9 [4.8, 18.8]; c has no effect (stay plan); p=0.2 alone gives vs FB +0.5 [-5.3, 7.3] and vs PI +6.1 [-2.1, 17.5]. The wrong-type plan c1000+back has a median of 379.3 s against IP's 210.8 s and is worse in 100/100 seeds. The paper's robustness text (lines 75, 85, 187, 197, Fig. 3) shows only onset delay and runners, so it reads as more robust than the pre-registered rows show. S1a/S1b, C1 and Table II are unchanged, because S3 is descriptive.
- **Evidence.**
  - v5b/p1b/analysis.py@93ba655:45 (COMBINED d=60, c=60, p=0.2), 225, 544, 558-562
  - p1b_result.json eval.S3.*.combined_row.vs_L0
  - own recompute g5_recompute.py (seeds 20261019 and 777): identical to the JSON
  - paper.qmd:75, 85, 187, 197 (no combined row)
- **Failure scenario.** A reader or reviewer concludes from line 187 and Fig. 3 that the type plan's lead in the C1 cell is robust to imperfect detection. With a 60-s onset delay plus 20 % type errors (the pre-registered realistic setting), the lead over FB is 0.5 % and the lead over PI is not significant.
- **How to test.** Run /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/G5/g5_recompute.py and read the 'combined' and 'p0.2_only' lines per cell.
- **Related claims.** C14, C18, C73, C79, C80

#### G5-F2 (R2 G5, major, disclosure): S3 reporting deviates from the pre-registered paper outputs (A10), and line 145 narrows S3 to detection delays

- **Description.** Protocol A10 fixed 'one break-even table (d*, p*, f*); the clearance delay in the text', and S3 = d*, c*, p*, f*(pi) and the combined row with 95 % CIs. The P1b addendum keeps this ('everything not changed'). The paper's table has only d* and no CIs. It has no clearance delay in the text. Line 145 describes S3 as 'break-even detection delays (descriptive)', and the change is not disclosed. This adds to round-1 C18 and TEXT-F7 (p* and f* missing) and S23-F2 (c* missing). Borderline critical, because line 145 describes the pre-registered content incompletely right after the claim that the protocol was fixed in advance.
- **Evidence.**
  - p1_incident_information.md@93ba655:112, 116 (A10)
  - p1b_addendum.md:4
  - paper.qmd:145, 179
- **Failure scenario.** A reviewer who checks the protocol finds pre-registered robustness outputs replaced by a subset with no disclosure. The subset is the favourable one.
- **How to test.** Compare protocol line 116 with paper.qmd lines 145 and 179.
- **Related claims.** C18, C14

#### G5-F3 (R2 G5, minor, unsupported-interpretation): Results note reports the combined row only against perfect IP; the four negative values do not mean IP loses to always-on control

- **Description.** In p1b_result.md Table 1, the row 'Combined row vs IP' (-20.5, -1.6, -16.5, -3.4 %) is rel(IP, combined): the cost of adding the imperfections to perfect IP. A negative value is expected and says nothing about always-on control. The decision-relevant comparison against L0 is only in the JSON, and its results are mixed: +2.7 % (n.s.) and +0.5 % (n.s.) in two cells, and significantly worse than PI in two cells (-52.0 %, -7.0 %). In the C1 cell, the -16.5 % comes almost entirely from misclassification: delays alone cost 2.6 %.
- **Evidence.**
  - docs/research/results/p1b_result.md:27
  - analysis.py@93ba655:562 (vs_IP = _two(D['IP'], comb))
  - g5_recompute_20261019.log (combined_p0_vs_IP block_q1600 -2.6 %)
- **Failure scenario.** The author or a later auditor reads 'negative in all cells' as 'IP loses to always-on control under realistic detection'. The vs-L0 numbers say instead: no significant lead in any cell, and a loss in two.
- **How to test.** Compare the md row with eval.S3.*.combined_row.vs_L0 in p1b_result.json.
- **Related claims.** C14

#### Verifier R3 reproduce: CONFIRMED / major

I reproduced the core fact from the raw runs with my own code. I built the run keys and the canonicalisation myself and did not import v5b. Every number in G5-F1 holds, and the pre-registration and omission claims also hold.

1. The combined row (d=60, c=60, p=0.2) against the strongest L0 arm, per cell, 100 seeds, all of them valid:
- slow_q1600: -52.0 % [-65.4, -40.1] vs PI;
- slow_q2000: +2.7 % [-1.5, 8.0] vs PI;
- block_q1600: +0.5 % [-6.1, 7.8] vs FB, and +5.9 % [-0.9, 16.8] vs PI;
- block_q2000: -7.0 % [-10.2, -3.4] vs PI.

The rel values, the diffs and the CIs equal p1b_result.json exactly (0 mismatches with boot seed 20261019). With boot seed 777 the CI bounds move by 0.1 at most.

2. One imperfection at a time in block_q1600:
- d60 only: +11.9 % [4.8, 18.8] vs FB.
- c60 only: identical to perfect IP. p20_20_16_e4 is a stay plan, so the clearance delay cannot act.
- p=0.2 only: +0.5 % [-5.3, 7.3] vs FB and +6.1 % [-2.1, 17.5] vs PI.
- The wrong-type plan c1000+back has a median of 379.3 s, against 210.8 s for IP, and is worse in 100/100 seeds.
- p* in the JSON is 0.21 (vs FB), which agrees with this.

3. All 900 d=60 runs on the eval seeds switch at exactly t_on+60. Back plans return at t_off+c. No seed falls back to the N run.

4. Pre-registration:
- Protocol §4 (p1_incident_information.md:74) lists 'Combined row | d = 60 s, c = 60 s, p = 0.2'.
- §6 (line 112) defines S3 as 'd*, c*, p*, f*(π) and the combined row, with 95 % CIs'.
- The protocol is unchanged since 93ba655, and the addendum keeps S3 ('everything not changed').

5. The cited code lines match: analysis.py@93ba655:45, 225, 544 and 558-562.

6. The paper (papers/paper_1/paper.qmd) never mentions a combined row or misclassification results. Lines 75, 187, 197 and Fig. 3 show only the onset delay and runners. Line 85 even promises to report 'how often the type may be wrong or a false alarm occur'. Line 145 narrows S3 to 'break-even detection delays'.

7. S3 is descriptive ('No significance claim'), so S1a/S1b, C1 and Table II are unchanged. The severity is major, not critical.

Small corrections to the finding's wording (they do not change the outcome):
(a) The title says 'not ahead ... in any cell'. This is too strong as written: the point estimates are positive in 2 cells (+2.7 %, +0.5 %). Accurate wording: 'no lead with a CI that excludes 0 in any cell; significantly behind the strongest arm in 2 cells'.
(b) 'The pre-registered realistic setting': the protocol does not call the combined row realistic.
(c) Protocol A10 (line 116) lists the paper outputs as 'one break-even table (d*, p*, f*); the clearance delay in the text'. It does not name the combined row as a paper output. The omission is a deviation from the S3 statement, not from A10.
(d) Two cells add no new information:
- slow_q1600: perfect IP was already not significantly ahead of PI (+4.5 % [-24.4, 12.8]).
- block_q2000: perfect IP was already behind PI (-2.1 % [-5.6, -0.1]).
The combined row matters mainly for block_q1600 and slow_q2000. In block_q1600 the loss comes almost entirely from p=0.2, not from the delays.
(e) The combined row uses the P1b eval seeds (7400600-699), not the fresh C1 seeds. The C1 protocol pre-registered only the d and runner rows, so Fig. 3 itself follows its own protocol. The link the failure scenario draws to line 187 and Fig. 3 crosses two data sets. It is still fair as a point about how robust the paper makes IP look.

Checks: Read groups['G5-F1'] from /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/round3_input.json; Read v5b/p1b/analysis.py@93ba655 (COMBINED, canon_sw, eval_specs, imperfection_cell, _two), v5b/p1/stats.py@93ba655 (paired, mixture, boot_idx), v5b/p1b/episode.py@93ba655 (run_key), v5b/p1/meters.py@93ba655:203-217 (switch_schedule); /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify3/G5-F1-reproduce/recompute_combined.py: own key building, canonicalisation and paired bootstrap from raw runs in ~/work/phd/v5b1_runs/p1b/v108/runs; compares to result.json (log recompute_20261019.log); Same script with boot seed 777 (recompute_777.log); /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify3/G5-F1-reproduce/check_schedules.py: realised switch/return ticks of all 900 eval-seed d=60 runs (check_schedules.log); p_star summary from result.json (pstar_json.log in the same scratch dir); grep of protocol §4/§6/A10 and addendum; diff of the protocol at 93ba655 vs the working tree (unchanged); grep of papers/paper_1 for combined/misclassification; read paper.qmd lines 70-90, 140-150, 170-203

#### Verifier R3 defend: CONFIRMED / major

The core problem survives my best defence, but in a narrower form than the group title states.

Defence points that hold (they narrow G5-F1):
1. The combined row is a pre-registered S3 study output (protocol:74, :112). It is NOT a pre-registered paper output. A10 option (a), which was chosen, fixes the paper outputs (protocol:116, :155): Fig. 1, Table 1, the S2 inset, "one break-even table (d*, p*, f*); the clearance delay in the text". The combined row is not on that list, and option (b) "every row in the main text" was rejected. So leaving the combined row out of the paper is within the pre-registered scope. It should not be called a pre-registration deviation. The results note does report it (p1b_result.md:27).
2. "IP is not ahead of the strongest always-on arm in any cell" is true only in the sense "no 95 % CI above zero". The point estimates are positive in two cells: +2.7 % vs PI (slow_q2000) and +0.5 % vs FB (block_q1600). S3 is descriptive by protocol ("no significance claim"), and the paper's own d* uses the point median.
3. In two cells nothing new is shown. slow_q1600 (lead lost within 3 s) and block_q2000 (IP never ahead) are already disclosed at line 197 and in Table II.
4. The protocol never calls d=60, c=60, p=0.2 "realistic". That word comes from the auditor.
5. Line 187 and Fig. 3 are accurate. They match the C1 protocol's descriptive rows exactly: d in {30, 60, 120} and runners. The C1 protocol has no misclassification row.
6. The paper is a draft. Discussion and Limitations is empty, and the plan comment says Table II will hold an "S1/S2/S3 summary with CIs".

What survives:
- In the C1 cell (block_q1600), type errors remove IP's lead over the binding always-on arm FB. The pre-registered break-even p* = 0.21 [0.12, 0.33] vs FB, and p = 0.2 alone gives +0.5 %.
- p* is an A10 paper output, and the paper leaves it out.
- Line 85 says "We therefore report how long detection may take, and how often the type may be wrong or a false alarm occur, before the gain disappears". The Results report only onset delay (d*) and runners. No p*, f* or clearance delay appears anywhere.
- So a statement in the paper is unsupported as written, and the missing evidence is the unfavourable part. A reviewer would require it.

The combined row itself adds nothing beyond p*: in block_q1600, d60 alone keeps +11.9 % vs FB, and the stay plan makes c irrelevant. The finding is therefore really the p*/f*/c* omission (G5-F2, round-1 C18/TEXT-F7), and the group partly double-counts with it. S1a/S1b, C1 and the Table II numbers are unchanged, so the severity stays major, not critical.

Members:
- G5-F2 confirmed. A10 lists p*, f* and the clearance delay; the paper has only d*, without CIs. Line 145 describes S3 as "break-even detection delays" only.
- G5-F3 is minor. The md label "Combined row vs IP" is accurate, so this is a risk of misreading, not an error.

My own recompute from raw runs matches the JSON and the earlier auditor on every point estimate.

Checks: Read the group G5-F1 from round3_input.json; Read paper.qmd lines 25-90 and 140-203 (contributions, line 85, protocol paragraph, Results, Table II, empty Discussion); Read p1_incident_information.md §4, §6 and the A10 row at 93ba655; git diff 93ba655..HEAD on the protocols (no change); grep for 'realistic' (none); Read p1b_addendum.md and p1b_confirm_c1.md (descriptive rows of C1); Read analysis.py@93ba655 (COMBINED constant, eval_specs, imperfection_cell); /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify3/G5-F1-defend/s3_summary.py: the combined row vs each L0 arm and vs IP for all 4 cells, from p1b_result.json; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify3/G5-F1-defend/s3_stars.py: d*, c*, p* with binding arms and CIs per cell; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify3/G5-F1-defend/find_ipvs.py: perfect-information IP vs each L0 arm (99.375 %); /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify3/G5-F1-defend/block1600_decomp.py (output block1600_decomp.log): own recompute from raw v108 runs, with no v5b import, of IP, d60-only, p0.2-only, combined and wrong-type rows vs FB, PI, N and AD, for block_q1600 and slow_q2000; all 100 seeds present, run keys checked

### B12. [major] HEADLINE-F2: C1 tests IP only against PI; FB was the strongest always-on arm in that cell

Raised as major; verification: reproduce: CONFIRMED/major, defend: CONFIRMED/minor.

#### HEADLINE-F2 (R1 HEADLINE, major, invalid-comparison): C1 confirms IP only against PI; in block_q1600 the strongest always-on arm was FB, which C1 did not run

- **Description.** Meaning: C1 is the only confirmatory claim, and it compares the type plan with always-on PI. On the P1b evaluation seeds in block_q1600, the lowest-median L0 arm (the Fig. 1 'strongest L0' rule) is FB f40_10 at 247.9 s, ahead of PI at 252.1 s. FB is also the binding arm in the intersection-union sense: IP vs FB is 15.9 % (diff-CI lower bound 17.8 s), against 18.0 % for IP vs PI. The comparator PI was chosen after the P1b data were seen (protocol p1b_confirm_c1.md:5 and :36, disclosed there). C1 ran only IP, PI, N and NC. So C1 does not confirm that the type plan beats the strongest always-on control in that cell. The paper's wording 'relative to always-on PI' is accurate. However, the paper does not say that PI was not the strongest L0 arm there, and the introduction frames the question as 'beyond strong always-on feedback'.
- **Evidence.**
  - paper.qmd:155, :187; paper.qmd:67 'beyond strong always-on feedback'
  - /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/HEADLINE/l0_medians.py: block_q1600 FB 247.9, PI 252.1, AD 287.4, FX 310.3, N 314.6
  - /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/HEADLINE/s1a_all_l0.py: block_q1600 IP vs FB 15.9 % (lo 17.8 s), vs PI 18.0 % (lo 20.5 s)
  - v5b/p1b/confirm_c1.py:87@e7dd561 ARMS = (IP, PI, N, NC)
  - docs/research/protocols/p1_incident_information.md:44 (statements against L0 must hold against each L0 arm; binding arm reported)
- **Failure scenario.** A reviewer reads C1 as 'the type plan beats tuned always-on control on fresh seeds'. That holds only against PI. The stronger FB baseline in the same cell is untested on fresh seeds, which looks like the 'weak baseline' pattern.
- **How to test.** Disclose in the paper that FB was the strongest L0 arm in block_q1600 (P1b: IP vs FB 15.9 %). Any new FB run on 7,400,700-799 would be a new, non-pre-registered row, so it needs an author decision and must be reported as descriptive.
- **Related claims.** paper.qmd:187 C1 is confirmed, paper.qmd:155 IP vs PI 18.0 % [8.9, 31.6]

#### PROV-F3 (R1 PROV, major, invalid-comparison): C1's comparator (always-on PI) was chosen after the data and was not the strongest always-on arm in that cell; FB was not run in C1

- **Description.** In P1b block_q1600, FB (f40_10) had the lowest median delay among the L0 arms (247.9 s, against PI 252.1 s). IP's paired gain over FB (15.9 %, diff 39.4 s [20.1, 55.3]) was smaller than over PI (18.0 %, 45.3 s [25.2, 77.3]). C1 tested only IP vs PI, so it does not confirm a gain over the best always-on controller in that cell. This matters because the paper frames its contribution against 'a full set of tuned always-on controllers' and S1 compares against every L0 arm. The P1b evidence suggests that FB would probably also pass, but this was not confirmed on fresh seeds.
- **Evidence.**
  - scratch c1_opponent.py output
  - p1b_summary.md:64 (block_q1600 medians)
  - p1b_result.md:47 ('Only in block_q1600 does IP beat every L0 arm')
  - C1 arms in p1b_c1/v114/runs: NC, c1800, IP (+d/rs rows), PI (+rs rows); no FB
- **Failure scenario.** A reviewer asks whether the type plan beats the best always-on law in the confirmed cell. The fresh-seed evidence covers only PI, which in P1b was the second-best L0 arm there by median.
- **How to test.** Run scratch c1_opponent.py. A fresh-seed check would need FB runs on 7,400,700-799, which this audit did not do (no simulations).
- **Related claims.** C60, C70

#### REPRO-F9 (R1 REPRO, minor, invalid-comparison): C1 reference is PI while Fig. 2 shows FB as the strongest L0 in the same cell

- **Description.** In block_q1600 the lowest marginal median among the L0 arms is FB (247.87 s vs PI 252.14 s), and Fig. 2 shows FB as L0. C1 confirms IP only against PI. P1b gives IP vs FB 15.9 % [7.8, 22.9] at the S1 level, but this comparison was not confirmed on fresh seeds. The text frames C1 correctly as 'vs always-on PI', yet a reader of Fig. 2 could assume that C1 used the strongest always-on arm.
- **Evidence.**
  - p1b_result.json eval.fig1_ladder.block_q1600.strongest_L0 = 'FB'; eval.cells.block_q1600.IP_vs_L0.FB rel 0.159
  - confirm_c1.py@e7dd561:51
- **Failure scenario.** A reviewer asks why the confirmation is not against the cell's strongest always-on controller.
- **How to test.** Compare fig1_ladder strongest_L0 with the C1 frozen arms.
- **Related claims.** C68, C75

#### Verifier R1 reproduce: CONFIRMED / major

I reproduced the core fact from the raw data. On the P1b evaluation seeds in block_q1600, the always-on arm with the lowest median delay is FB (f40_10), not PI. The C1 confirmation ran only IP, PI, N and NC, so FB was never tested on the fresh seeds.

What this means: C1 confirms that the type plan (IP) beats always-on PI. It does not confirm that IP beats the strongest always-on arm in that cell. The paper's own Fig. 2 rule (L0 = the lowest marginal median) picks FB, and Fig. 2 labels that bar 'FB (L0)' at 248 s in the lane-crawl 1600 panel.

The paper's wording ('relative to always-on PI', paper.qmd:155 and :187) is accurate. What the paper leaves out:
- PI was not the strongest L0 arm in this cell.
- The cell and the comparator were chosen after the P1b data were seen. The C1 protocol discloses this at :5 and :36, but the paper text does not; a grep for 'after seeing' and 'post hoc' found nothing.

Two points temper the finding:
- FB and PI cannot be told apart in this cell. FB is better than PI by a median paired difference of 10.7 s (rel -4.2 % for FB vs PI), with a 95 % CI of [-21.0, 5.7] s, which includes zero.
- In P1b, IP vs FB already passes at the S1 level: rel 15.9 %, CI [7.8, 22.9] %, diff-CI lower bound 18.0 s. So IP would probably also beat FB on fresh seeds, but this is my speculation and was not tested.

The headline survives. The issue is an undisclosed choice of comparator, made after the P1b data were seen, which a reviewer would ask about. That fits the definition of 'major'.

Small errors in the tracers' cited numbers:
- HEADLINE-F2 gives the S1-level lower bound of IP vs FB as 17.8 s. The stored JSON, which uses the repo's random-number recipe, says 18.0 s. 17.8 s is what an independent random seed gives; my own seed also gave 17.8 s.
- PROV-F3 gives the 95 % CI of IP vs PI as [25.2, 77.3]. With the repo's recipe it is [25.2, 77.1]; with an independent seed it is [25.2, 77.3]. The difference is resampling noise.
- All other cited values match exactly. These are the medians FB 247.87, PI 252.14, AD 287.37, FX 310.30 and N 314.57 s, and IP vs PI 18.0 % [8.9, 31.6] with diff-CI lower bound 20.5 s.

Further findings:
1. The tuned picks re-derive from the raw tuning runs (seeds 7,400,300-339, slow and block runs pooled).
   - FB: f40_10 is the lowest of 30 feedback candidates (223.4 s vs f40_12 234.4 s).
   - PI: p70_120_8_e4 is the lowest of 90 PI candidates (210.1 s, with p20_40_10_e4 at 212.1 s).
   - FX: c2600 is the lowest of 20 constant rates.
   The arm set is therefore correct as it ran. The 'strongest L0 = FB' result comes from the evaluation seeds, not from the tuning.
2. Table II shows only rows against PI. IP vs FB, the binding arm in the intersection-union sense, appears nowhere in the paper. Yet p1_incident_information.md:44 requires that 'the binding arm is reported'.
3. paper.qmd:145 says 'the protocol, its statements and the seed ranges were fixed and approved before any data were produced'. For C1 this holds only relative to the C1 data: the C1 statement was written after P1b's evaluation data had been seen (protocol committed 7c6acc8 at 21:11:24; P1b data existed since 13:07).

Checks: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/HEADLINE-F2-reproduce/f2_recompute.py: my own numpy/json code with no v5b imports (run with python -I). It loads the 700 raw P1b files for block_q1600 (7 arms x 100 eval seeds) and checks key, seed, incident, q, validity and code_commit. It then recomputes the medians, the strongest-L0 and binding-arm choices, and the paired IP vs each L0 arm at the 95 % and S1 levels, with both the repo's random-number recipe and an independent seed. It also recomputes FB vs PI paired, re-derives the FB/PI/FX tuning picks from the raw tuning runs, lists the C1 run labels, and searches for f40_10 files on C1 seeds.; Output: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/HEADLINE-F2-reproduce/f2_recompute.log and /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/HEADLINE-F2-reproduce/f2_recompute_out.json; Extracted the analysis code at the run commit to /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/HEADLINE-F2-reproduce/analysis_93ba655.py (git show 93ba655:v5b/p1b/analysis.py) and read cell_runs, evaluate, fit_fixed and _two. Read run_key/make_spec in v5b/p1b/episode.py@93ba655 and paired in v5b/p1/stats.py@93ba655.; git show e7dd561:v5b/p1b/confirm_c1.py lines 30-110; git diff --stat e7dd561 HEAD and 93ba655 HEAD for v5b/p1b, v5b/p1 and the protocol: no change except that confirm_c1.py was added after 93ba655.; git log and git show for docs/research/protocols/p1b_confirm_c1.md (a4e3e6d 21:09:49, 7c6acc8 21:11:24); diffed against HEAD: identical.; jq on docs/research/results/p1b_result.json: eval.fig1_ladder.block_q1600, eval.cells.block_q1600.IP_vs_L0.{FB,PI}.all_seeds, table1_operating_map medians, tune.arms.; ls and uniq on ~/work/phd/v5b1_runs/p1b_c1/v114/runs (labels and seed range), plus a filesystem walk for f40_10*_s74007xx.; pdftotext -layout papers/paper_1/figures/fig_ladder.pdf to read the panel labels.; grep in papers/paper_1/paper.qmd (lines 67, 73, 145, 155, 160, 187, abstract), docs/decisions.md (V114, V115), docs/research/protocols/p1_incident_information.md:44, docs/research/results/p1b_result.md:47 and p1b_summary.md:64.

#### Verifier R1 defend: CONFIRMED / minor

Meaning: C1 is the paper's only confirmation on fresh seeds. It tested one thing: the type plan IP against always-on PI in the lane-crawl cell at 1600 veh/h. The finding says that FB, another always-on arm, was at least as strong there, that FB was not run in C1, and that the paper does not explain this.

The defence works on several points.
(1) The paper's wording is accurate. paper.qmd:187 says "relative to always-on PI", the Fig. 3 caption says "over always-on PI", and the C1 protocol title asks "does the type plan beat always-on PI". Nothing in the paper says C1 beat the strongest always-on arm.
(2) The claim "the paper does not say FB was the strongest" is wrong. Fig. 2 (caption: "strongest always-on arm (L0)") labels the crawl-1600 bar as "FB (L0)" in the rendered PDF.
(3) "PI is a weaker baseline" holds only for marginal medians: FB 247.9 s, PI 252.1 s. By the paper's own paired statistic, PI is ahead: median(PI-FB) = -10.7 s [-21.0, 5.7]. PI also has the lower delay on 56 % of seeds and the lower mean (263.7 s vs 267.7 s). The two arms are statistically indistinguishable, so this is not a weak-baseline pick.
(4) There is a reason to pick PI. The P1b addendum exists to remove the controller-family confound (V103), and IP's block plan is itself a PI-law plan (p20_20_16_e4). So IP vs PI isolates the value of information with the control law held fixed.

What survives the defence:
(a) Under the pre-registered intersection-union rule (p1_incident_information.md:44 and section 5), FB is the binding arm in P1b. IP's gain is smaller against FB: 15.9 % with diff-CI lower bound 17.8-18.0 s at the S1 level, against 18.0 % with lower bound 20.7 s for PI. C1 has no fresh-seed evidence against FB: confirm_c1.py@e7dd561:87 has ARMS = (IP, PI, N, NC), and v114/runs holds no f40_10 files.
(b) The protocol (line 101 of p1_incident_information.md) says "IP vs each L0 arm is reported". Table II reports only IP vs PI, so IP vs FB = 15.9 % is not in the paper.
(c) The paper does not say why PI was chosen, nor that the cell and the comparator were chosen after the P1b data. The C1 protocol discloses this at :36; the paper does not.
(d) The framing at paper.qmd:67 ("beyond strong always-on feedback") and :73 ("against a full set of tuned always-on controllers ... and a confirmation on fresh seeds") lets a reader take C1 as a confirmation against always-on control in general.

The headline is unaffected. In P1b, IP also passes the C1-type rule against FB. In C1, the IP and PI medians reproduce P1b well: IP 210.6 vs 210.8 s, PI 254.7 vs 252.1 s. That makes it plausible, but not shown, that FB would also pass. What remains is a missing disclosure plus one omitted pre-registered descriptive row, so I rate it minor. It would be major if the abstract or conclusion (not written yet) claimed that C1 confirms a gain over always-on control without naming PI.

Related, outside this group: paper.qmd:69 says "All statements were pre-registered before any data were produced". C1's statement was fixed after the P1b data existed, though before the C1 data. This is a separate pre-registration wording issue.

Failure points: an FB arm run on 7,400,700-799 could fail the rule. That would be a new row that was not pre-registered, so it needs an author decision and would be reported as descriptive. The ranking of FB and PI depends on the convention (marginal median, paired median or mean), so any sentence calling one of them "the strongest" must name the convention.

Checks: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/HEADLINE-F2-defend/l0_vs_ip_block1600.py (output in l0_vs_ip_block1600.out in the same dir): reads 700 raw P1b runs with my own numpy code; per-arm medians; IP vs each L0 arm at 95 % and 0.99375 in both views; paired FB vs PI; lists the C1 run keys.; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/HEADLINE-F2-defend/c1_vs_p1b_medians.py (output c1_vs_p1b_medians.out): C1 vs P1b medians and means for the arms common to both.; git show e7dd561:v5b/p1b/confirm_c1.py (grep ARMS/arms); git diff --stat e7dd561 HEAD on confirm_c1.py and p1b_confirm_c1.md (no change).; git show 93ba655:v5b/d1/stats.py: the rel CI is a bootstrap of the ratio median(d*)/median(b*). This explains why my rel CIs differ slightly from the JSON while the diff CIs agree.; jq on p1b/v108/result.json .tune.arms (tuned arm names at q1600) and on docs/research/results/p1b_result.json eval.cells.block_q1600.IP_vs_L0.FB and eval.fig1_ladder.block_q1600.; pdftotext on papers/paper_1/paper.pdf to check the Fig. 2 panel labels; read fig_ladder.py labelling (lines 14-30).; Read the paper text (qmd lines 55-203); the P1 protocol lines 1-110 (sections 2, 5 and 6, A-table); the P1b addendum; the C1 protocol; decisions.md V108-V116 and V122.

### B13. [major] LIT-F1: AD-ALINEA cited to wrong Smaragdis paper/year; AD arm weak

Raised as major; verification: reproduce: CONFIRMED/major, defend: CONFIRMED/major.

#### LIT-F1 (R1 LIT, major, citation): AD-ALINEA and set-point adaptation are cited to the wrong Smaragdis paper

- **Description.** Paper lines 65, 81 and 118 cite Smaragdis & Papageorgiou 2003 (TRR 1856) for set-point adaptation and AD-ALINEA. That paper's abstract presents FL-, UP-, UF-ALINEA and X-ALINEA/Q only. AD-ALINEA is introduced in Smaragdis, Papageorgiou & Kosmatopoulos 2004, TR-B 38(3):251-270, doi:10.1016/S0191-2615(03)00012-2. The repo's own protocol cites 2004, but the V128 review note wrongly says AD-ALINEA is 'already cited via' 2003.
- **Evidence.**
  - Smaragdis2003 abstract (/tmp/.../LIT/dl_meta/Smaragdis2003.json)
  - IDEAS abstract of the 2004 paper (/tmp/.../LIT/dl_misc/ideas_smaragdis2004.html): 'The developed AD-ALINEA strategy ...'
  - Papageorgiou 2008 §2.7.1 p. 541: attributes online critical-occupancy estimation to Smaragdis et al. (2004) and Kosmatopoulos et al. (2006), and FL-ALINEA to Smaragdis and Papageorgiou (2003)
  - docs/research/protocols/p1_incident_information.md:35 (cites 2004)
  - docs/colab_with_other_llm/argon_v1_review.md:5 (the wrong statement)
- **Failure scenario.** A reviewer who knows the ALINEA family sees a named baseline credited to the wrong paper and doubts how carefully the related work was prepared.
- **How to test.** Read section headings of the Smaragdis 2003 full text. Replace the citation with Smaragdis2004 (plus Kosmatopoulos2006, doi:10.1177/0361198106195900108) and re-render.
- **Related claims.** C06, C17

#### CTRL-F10 (R1 CTRL, minor, citation): AD is dominated by FB, uses a different estimator from AD-ALINEA, and its citation year is inconsistent

- **Description.** Tuned eta = 0.5 is the lowest grid value at both q. AD's tuning median is worse than FB's (251 vs 223; 412 vs 396). The rule is a sign-based hill-climb ('not its estimator', protocol §2). The protocol cites Smaragdis et al. 2004, the paper cites Smaragdis2003 (TRR 1856, 'Series of new local ramp metering strategies').
- **Evidence.**
  - /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/CTRL/out/retune.json AD_gap
  - docs/research/protocols/p1_incident_information.md:35; papers/paper_1/references.bib:137-148
- **Failure scenario.** The citation does not support the AD-ALINEA attribution.
- **How to test.** The literature agent should check the original AD-ALINEA source. The paper should state the estimator difference.
- **Related claims.** C45

#### G8-F4 (R2 G8, major, citation): LIT-F1 confirmed: set-point adaptation / AD-ALINEA cited to Smaragdis & Papageorgiou 2003 at lines 65, 81 and 118

- **Description.** Neither Smaragdis paper is legally reachable in full (SAGE closed; ScienceDirect subscribers only; TUC repository behind an Anubis bot check). The best legal texts are both abstracts plus Papageorgiou 2008 in full. The 2003 abstract lists only FL-, UP-, UF-ALINEA and X-ALINEA/Q. The 2004 TR-B abstract introduces AD-ALINEA for 'automatic tracking of the critical occupancy'. Papageorgiou 2008 credits the online estimator to Smaragdis et al. (2004) and Kosmatopoulos et al. (2006), and FL-ALINEA to the 2003 paper.
- **Evidence.**
  - LIT/dl_meta/Smaragdis2003.json
  - LIT/dl_misc/ideas_smaragdis2004.html
  - LIT/papageorgiou2008.txt:333-334, :356
  - paper.qmd:65, :81, :118
- **Failure scenario.** A reviewer sees a named baseline (AD) credited to the wrong paper.
- **How to test.** Replace with Smaragdis, Papageorgiou & Kosmatopoulos 2004 (doi:10.1016/S0191-2615(03)00012-2), optionally plus Kosmatopoulos 2006. Before keeping 2003, check its section headings in a library copy.
- **Related claims.** C06, C17

#### Verifier R2 reproduce: CONFIRMED / major

I reproduced the core fact. The paper cites Smaragdis & Papageorgiou 2003 (TRR 1856) in three places: for set-point adaptation (line 65), for online set-point estimation (line 81) and for AD-ALINEA (line 118).

- **The 2003 paper.** Its Crossref/OpenAlex abstract presents only FL-, UP-, UF-ALINEA and X-ALINEA/Q.
- **The 2004 paper.** It is TR-B 38(3):251-270 by Smaragdis, Papageorgiou & Kosmatopoulos. Its IDEAS abstract says "The developed AD-ALINEA strategy" and describes automatic tracking of the critical occupancy.
- **The local full text of Papageorgiou et al. 2008 (a primary source written by the same group).** On p. 541 it gives the real-time critical-occupancy estimator to Smaragdis et al. (2004) and Kosmatopoulos et al. (2006), and FL-ALINEA to Smaragdis and Papageorgiou (2003). The string "AD-ALINEA" does not appear in the 2008 text.
- **The repo's own records.** The protocol (p1_incident_information.md:35) cites 2004. The V128 review note (argon_v1_review.md:5) wrongly says that AD-ALINEA is "already cited via" 2003. The error started in Argon v0, which added the 2003 paper "to verify AD-ALINEA".
- **The bib file.** references.bib:137-148 has only Smaragdis2003. There is no 2004 entry and no Kosmatopoulos 2006 entry.

The idea in C06/C17 (a set point that is estimated online and tracks slow changes) matches the 2004 abstract. So the defect is the wrong source, not a wrong idea.

**CTRL-F10 parts.** I reproduced these from the code that ran and from the raw runs.
- AD is a sign-rule hill-climb: n_crit += eta*sgn(dphi)*sgn(dn), clipped to [4, 20]. This is not AD-ALINEA's estimator, and the paper does not say so.
- With eta = 0, AD reduces to FB.
- The tuned eta = 0.5 is the lowest grid value at both q.
- On the tuning seeds, AD is worse than FB at both q: 251.25 vs 223.44 s, and 411.65 vs 395.71 s.
- On the 100 eval seeds, AD is worse than FB in 3 of 4 cells and ties in slow_q1600.
- FB is itself an L0 opponent, so a weak AD does not inflate the S1 headline.

**Severity.** I keep major: as written, the citation does not support the statement. The headline results are not affected, and the fix is easy (cite Smaragdis2004, and optionally Kosmatopoulos2006; say that the AD rule is a sign-based heuristic).

**Limits.** I did not read the 2003 full text (it is paywalled and I had no web access). So the claim that "AD-ALINEA is absent from 2003" rests on the 2003 abstract and on the 2008 attribution, not on the full text. The 2003 abstract came from metadata that the round-1 script downloaded from api.crossref.org and api.openalex.org. I did not query them again.

Checks: grep for Smaragdis/AD-ALINEA/Kosmatopoulos in paper.qmd, references.bib, docs/ (and git show HEAD:papers/paper_1/paper.qmd to confirm the line numbers); sed of docs/research/protocols/p1_incident_information.md:30-40 and docs/colab_with_other_llm/argon_v1_review.md:1-12; pdftotext -layout of the local Papageorgiou 2008 PDF -> /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/LIT-F1-reproduce/pap2008.txt, then grep and read section 2.7.1; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/LIT-F1-reproduce/page_of_lines.py (output page_of_lines_output.txt): maps the cited lines to journal page 541; Read LIT/dl_meta/Smaragdis2003.json abstract fields with python -I, and checked LIT/scripts/fetch_meta.py to see where the metadata came from; Parsed LIT/dl_misc/ideas_smaragdis2004.html with python -I (abstract plus citation_* meta tags); git show 93ba655:v5b/p1b/meters.py (AD law, lines 72-112, 130-133) and 93ba655:v5b/p1/family.py (ETA_GRID, clip bounds); Read result.json tune.arms / tune.tables / grid_edges_report_only in ~/work/phd/v5b1_runs/p1b/v108 (summarised, not printed raw); /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/LIT-F1-reproduce/recompute_ad_fb_tune.py (output recompute_ad_fb_tune_output.txt): independent tuning medians from 80 raw runs per arm; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/LIT-F1-reproduce/eval_ad_vs_fb.py (output eval_ad_vs_fb_output.txt): AD vs FB on the 100 eval seeds per cell, from raw runs

#### Verifier R2 defend: CONFIRMED / major

I tried to defend the paper and could not; the citation problem stands. The AD-weakness part of the group is real, but it does not affect any result. Three sentences cite Smaragdis & Papageorgiou 2003 (TRR 1856) for set-point adaptation and for AD-ALINEA: papers/paper_1/paper.qmd:65, :81 and :118 (HEAD 1e5e8d7, no uncommitted changes). Primary evidence against this citation (basis: direct observation): (1) The local full text of Papageorgiou et al. 2008, whose senior author also wrote both Smaragdis papers, gives real-time critical-occupancy estimation to "Smaragdis et al. (2004) and Kosmatopoulos et al. (2006)" (p. 541). It gives only FL-ALINEA to Smaragdis and Papageorgiou (2003). (2) The 2003 abstract (saved by round 1 from Crossref/OpenAlex and TRID) lists the new strategies: FL-, UP-, UF-ALINEA and X-ALINEA/Q. AD-ALINEA is not among them. (3) The 2004 TR-B abstract says "The developed AD-ALINEA strategy ...". (4) The approved protocol p1_incident_information.md:35 itself cites Smaragdis et al. 2004 [VERIFY]. So the paper does not follow its own protocol's source. Defences I tried: (a) 'in the spirit of' is a hedge. It hedges how close our rule is to AD-ALINEA, not which paper the reference names. (b) The 2003 full text might mention adaptation. Nobody has read it (paywalled), so this is a small residual uncertainty. But the 2004 paper is the one that 'developed' AD-ALINEA, so it is the correct source in any case. (c) A later fix or a disclosure elsewhere. There is none: references.bib has no Smaragdis2004 entry, and git log -S finds no 2004 key ever in papers/. Where the error came from (direct observation): the external LLM draft (Argon v0) added Smaragdis 2003 as the AD-ALINEA source. That draft itself asked which of the two papers was meant (Argon v0 line 317). The V128 review then wrongly kept 2003 (argon_v1_review.md:5). One point is overstated: claim C06 was rated CONTRADICTED. The content of the sentence (set-point adaptation tracks slow changes without an incident detector) is supported by the 2004 abstract; only the attribution is wrong. Fixing it means changing the citation in three places, not the wording. The AD arm (CTRL-F10), recomputed from raw v108 runs with my own code: the tuning medians on the pooled slow+block seeds 7,400,300-339 are FB 223.4 s versus AD 251.3/300.0/303.6 s (eta 0.5/1/2) at q=1600, and FB 395.7 s versus AD 411.7/439.9/478.1 s at q=2000. AD gets worse as eta grows, and the chosen eta=0.5 is at the edge of the grid. So AD is dominated by its eta->0 limit, which is FB. The rule is a sign-based hill-climb (v5b/p1/meters.py@93ba655:125-126, v5b/p1b/meters.py@93ba655:98-99), which matches the protocol, and the protocol says 'not its estimator'. The paper does not describe the rule, the fact that it differs from AD-ALINEA's estimator, or the grid-edge result. That is a minor disclosure gap. It is moot for the headline: the rule is intersection-union, and the S1a binding arm is FB in both the all-seeds and valid-only views (result.json eval.S1), so a weak AD arm cannot make any statement easier to pass. Severity: by the task's definition, 'a paper statement unsupported as written' is major. The citation part stays major (the fix is easy, and the headline survives). The AD-weakness part alone would be minor.

Checks: Read the LIT-F1 group from round2_input.json; grep of Smaragdis/AD-ALINEA/set point in paper.qmd, references.bib, protocols, decisions.md, docs/colab_with_other_llm (read-only); git diff HEAD on paper.qmd/references.bib (clean); git log -S for Smaragdis2003, Smaragdis2004 and AD-ALINEA in papers/; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/LIT-F1-defend/pap2008_grep.sh: pdftotext of the local Papageorgiou 2008 PDF plus a grep of its attributions (output pap2008_grep.out, full text pap2008.txt); Parsed the saved abstracts (round-1 LIT dl_meta/Smaragdis2003.json, dl_misc/trid_686972.html, dl_misc/ideas_smaragdis2004.html) with my own regex extraction (python -I); git grep at 93ba655 for the AD controller (v5b/p1/meters.py, v5b/p1b/meters.py, v5b/p1/family.py) and compared it with protocol section 2; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/LIT-F1-defend/ad_vs_fb.py: own recomputation of the AD-versus-FB tuning medians from raw v108 run files (output ad_vs_fb.out); Read result.json tune.arms, grid_edges_report_only and eval.S1 binding arm (summarised by script, not printed raw)

### B14. [major] LIT-F3: Plant geometry and FB baseline from Flow / Vinitsky et al. 2018 not cited

Raised as major; verification: reproduce: CONFIRMED/major, defend: CONFIRMED/major.

#### LIT-F3 (R1 LIT, major, citation): The plant geometry and FB baseline come from Flow / Vinitsky et al. 2018 but are not credited

- **Description.** The code states that the BN4 network geometry is copied from the public Flow bottleneck. It also states that the FB law and its default values (T = 30 s, K_F = 20, n_crit = 8, 6-s green, c = 2M·3600/q) come from 'Vinitsky et al. (2018) Sec. III-E'. The paper describes the plant (lines 93, 110) and the FB arm (line 118) without citing either source. The likely paper is Vinitsky, Parvate, Kreidieh, Wu & Bayen, 'Lagrangian Control through Deep-RL: Applications to Bottleneck Decongestion', ITSC 2018, pp. 759-765, doi:10.1109/itsc.2018.8569615 (metadata verified on OpenAlex; content not read). The CoRL 2018 benchmark paper (PMLR 87:399-409, read) contains no feedback ramp-meter baseline.
- **Evidence.**
  - v5b/d1/netgen_bn4.py@93ba655:1-11
  - v5b/d1/episode.py@93ba655:37-44 (FBMeter docstring)
  - /tmp/.../LIT/vinitsky2018.txt (CoRL text: no ALINEA or feedback meter found by grep)
- **Failure scenario.** A reviewer who knows the Flow bottleneck benchmark recognises the 4/4/4/2/1 zipper geometry and sees reuse without credit.
- **How to test.** Read Vinitsky ITSC 2018 §III-E to confirm the section and values. Add the citation to the plant description and the FB arm.
- **Related claims.** C04, C16

#### PLANT-F11 (R1 PLANT, minor, citation): Plant geometry and the base feedback meter come from Flow / Vinitsky et al. (2018) but are not cited

- **Description.** The code docstrings state that BN4's geometry, vehicle parameters and the FBMeter law (6-s green, c = 2M*3600/q, K_F, n_crit on the edge-4 count) are ported from Flow / Vinitsky et al. (2018). The paper cites only SUMO, and calls FB 'ALINEA style' [Papageorgiou1991]. I did not verify the Vinitsky reference myself.
- **Evidence.**
  - v5b/d1/netgen_bn4.py@93ba655:2-10
  - v5b/d1/plant.py@93ba655:2-8
  - v5b/d1/episode.py@93ba655:38-44
- **Failure scenario.** Missing attribution for a reused benchmark plant.
- **How to test.** Add the Flow / Vinitsky citation after checking it against the primary source.
- **Related claims.** C09

#### Verifier R1 reproduce: CONFIRMED / major

Meaning: the simulated bottleneck and the feedback (FB) meter in the paper are not original designs. They are the Flow bottleneck benchmark and the feedback ramp-meter baseline of Vinitsky et al. (ITSC 2018), and the code says so. The paper describes the plant (lines 93, 110) and the FB arm (line 118) with no credit to Flow or Vinitsky.

What I checked directly:
(1) The code that ran credits the source. netgen_bn4.py@93ba655:2-9 says "BN4: the Flow / Vinitsky et al. (2018) two-stage zipper bottleneck ... Geometry is copied from the public Flow code (flow/networks/bottleneck.py)". plant.py@93ba655:2-7 says "Vinitsky et al. (2018) bottleneck", with Flow's IDM defaults and lane changing disabled "as in the paper". The FBMeter docstring at d1/episode.py@93ba655:38-44 says "Vinitsky et al. (2018) Sec. III-E" and gives T=30, K_F=20, n_crit=8, a fixed 6-s green, c = 2M·3600/q, and 140 m before the bottleneck. These files are identical at e7dd561 and at HEAD (git diff --stat is empty). P1b reaches this code through p1b/episode.py@93ba655:32 (`from v5b.d1 import plant`, which builds the net with netgen_bn4). p1b/meters.py@93ba655:6,12 reuses the FB law q(k)=q(k-1)+K_F(n_crit-n) on the edge-4 count, and c = 2M·3600/q.
(2) The primary source matches exactly. I found a local full text of Vinitsky, Parvate, Kreidieh, Wu, Bayen, "Lagrangian Control through Deep-RL: Applications to Bottleneck Decongestion", ITSC 2018, pp. 759-765. It is under the other worktree's knowledge base, and I only read it. Section III-E "Feedback ramp metering" (p. 763) has eq. (6) q(k+1)=q(k)+K_f(n_crit−n̂), with n̂ = the vehicles in segment 4, a fixed 6-s green plus a variable red, 2 vehicles per lane per green, and eq. (7) c=2M·3600/q. It says "We used T = 30, KF = 20, ncrit = 8 ... there may be better values" and that the meter "sits 140 meters before the bottleneck". In the code, node 3 is at x=410 and node 4 at x=550, which is 140 m. Section III-A describes the two-stage zipper (four lanes to two to one) and says lane changing is disabled. Section III-F gives the 40-s uncontrolled warm-up and 10% AVs. The PDF metadata holds IEEE Article ID 8569615, which fits the tracer's DOI 10.1109/itsc.2018.8569615. I inferred that DOI from IEEE's usual pattern; it is not printed in the paper.
(3) The paper gives no credit. paper.qmd (unchanged since 4de404a; the working tree is clean for it) and references.bib contain no Vinitsky, Kreidieh, Bayen, Parvate or Flow-software citation. The only "Flow" hits are in the titles "Traffic Flow Control". The text of the rendered paper.pdf has 0 matches. Line 110 cites only SUMO [Lopez2018]. Line 118 calls FB "in the style of ALINEA [Papageorgiou1991]", but it also reuses Vinitsky's 40-s warm-up, 4/4/4/2/1 lanes, 28,800/q cycle and disabled lane changing.

Nuances:
- The P1b FB arm is tuned over K_F and n_crit and adds 3-s amber and a minimum red. So the law form and the signal structure come from Vinitsky, but the paper does not use his values 20/8. Wording that cites the source should say "adapted from".
- Vinitsky cites Spiliopoulou et al. (toll-plaza control, his ref. [31]) for his feedback controller. The paper cites Spiliopoulou2010 only in the introduction.
- I could not check the exact node positions (0/100/410/550/830/985 m) against the Flow code: there is no local copy and no web access. The ITSC text confirms the topology and the 140-m meter position, but not every coordinate.

Severity: major, not critical. No headline number changes. But a reviewer would require credit for a reused benchmark plant and baseline controller, and reuse without credit is a research-integrity concern.

Further findings:
(a) Undisclosed plant detail, minor, taken from Vinitsky. plant.py@93ba655:25-29 and p1b/episode.py@93ba655:125,133 give every P1b/C1 run av_share=0.1. These "av" vehicles have speedFactor 1 and speedDev 0 and are not controlled; humans have speedFactor normc(1,0.2,0.2,2.0). Other settings are IDM a=1, b=1.5, tau=1, minGap=2, delta=4, and a 0.5-s step. Nothing overrides av_share: run_episode is called only at p1b/episode.py:312, without it. The run JSONs do not record av_share; 200 sampled P1b files and 100 sampled C1 files show only code_commit and signal='amber'. The paper does not mention the vehicle mix or the car-following model, which a reader needs to reproduce the runs.
(b) Info, not checked by me. docs/architecture/port_map_v0.md@93ba655:373 records that the BN4 plant "failed the realism gate (discharge 900 veh/h/lane, capacity-drop ratio 0.77)". The paper does not mention any realism limit of the plant. The plant tracer should follow this up.

Checks: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/LIT-F3-reproduce/verify_litf3.sh: prints the code attributions at 93ba655, the diffs against e7dd561 and HEAD, the geometry SPEC, a grep of paper.qmd and references.bib for any Vinitsky/Flow citation, the extraction of Vinitsky §III-E/§III-A/§III-F text and the PDF article ID; pdftotext of the local Vinitsky ITSC 2018 PDF -> .../LIT-F3-reproduce/src/vinitsky_itsc2018.txt; read §III-A, §III-E, §III-F and the references [22] and [31]; pdftotext of papers/paper_1/paper.pdf -> .../LIT-F3-reproduce/src/paper_pdf.txt; grep: 0 Vinitsky/Kreidieh/Bayen matches; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/LIT-F3-reproduce/check_run_meta.py on 200 sampled P1b v108 run JSONs and 100 sampled C1 v114 run JSONs: code_commit 93ba655 / e7dd561, signal 'amber', no av_share key; git grep 'run_episode(' at 93ba655 and e7dd561 in v5b/p1b: only call site p1b/episode.py:312, no av_share override; find over / for local Vinitsky or Flow sources: Flow's bottleneck.py is not available locally, so the exact node x positions copied from the Flow code are UNVERIFIED

#### Verifier R1 defend: CONFIRMED / major

Meaning: The simulated road and the feedback meter in the paper were not designed from scratch. Both were taken from a published deep-RL benchmark, the Flow bottleneck of Vinitsky, Parvate, Kreidieh, Wu and Bayen (ITSC 2018). The paper describes both in detail but cites only SUMO for the plant, and only ALINEA for the feedback law. A reader cannot tell that the plant and the meter's signal design come from earlier work.

My best defence, point by point:
(1) The draft is unfinished (abstract, discussion and conclusion are not written; V124 says an author review comes at the end). This does not make the finding moot. The plant section is drafted, and the BL-2 open-items list (docs/baseline/BASELINE_2_2026-10-20.md:74-77) names only the [CITE] markers. Nothing flags this gap, and there is no \citeneeded marker at line 110 or 118.
(2) The lineage of the feedback law is credited. Line 118 says FB is 'in the style of ALINEA [Papageorgiou1991]', which is accurate: Vinitsky's eq. (6) is an integral law on a vehicle count. Vinitsky cites Spiliopoulou et al. (toll-plaza merging) as [31] for the controller, and the paper cites that work as Spiliopoulou2010 at line 63. So the claim that 'the FB law is uncredited' is overstated.
(3) The tracer's point about 'default values T=30, K_F=20, n_crit=8' is also overstated. The paper never states these values. P1b tunes K_F in {10,...,120} and n_crit in {6,...,16} on a grid (v5b/p1/family.py@93ba655:5), and the update period T is not in the paper.

What survives this defence: the paper states the plant and signal details that are verbatim Vinitsky ITSC 2018, with no credit:
- the 4->2->1 two-stage zipper bottleneck (abstract and Sec. III-A);
- lane changing disabled (Sec. III-A);
- a 6-s fixed green with 2 vehicles per lane per green, and c = 2M·3600/q, which the paper writes as 28,800/q (Sec. III-E, eq. 7);
- a 40-s uncontrolled warm-up (Sec. III-F).
The code at the run commit says outright that the geometry was copied from flow/networks/bottleneck.py and that the meter is 'Vinitsky et al. (2018) Sec. III-E'. The plant has node x = 410 -> 550, so the meter sits 140 m upstream, exactly as in Sec. III-E. The paper (qmd, bib, tex and PDF) contains no Vinitsky or Flow reference.

The omission looks inadvertent, not hidden: the archive notes say the paper was read in full, and V90 mentions the 'paper gains K_F 20, n_crit 8'. No result depends on it (S1a/S1b/C1 and Table II are untouched). It is still uncredited reuse of a known public benchmark plant and of its baseline's signal design, which a reviewer who knows Flow would require the authors to fix. I keep the severity at major, at the low end (the fix is one citation in Sec. IV-A and one at line 118). PLANT-F11's 'minor' understates the integrity aspect.

Defence failure points: if the Flow code's node coordinates differed from the docstring, the geometry claim would weaken. That is not checkable offline (no web), but the 4/4/4/2/1 lane counts and the 140-m meter position independently match the ITSC text.

Further finding (minor): the paper never names the car-following model. The plant uses IDM with Flow's default values and speedFactor N(1, 0.2) (plant.py@93ba655:5-6). Citing Vinitsky/Flow would also settle part of this reproducibility gap. The related claims C04/C09/C16 stay VERIFIED and are unaffected.

Checks: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/LIT-F3-defend/check_lit_f3.sh: shows the code provenance docstrings at 93ba655, extracts the local Vinitsky ITSC 2018 full text and greps the key passages, greps the paper/bib/tex/pdf for Vinitsky/Flow, and lists the paper statements that match Vinitsky; Copied and extracted the full text to /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/LIT-F3-defend/src/vinitsky_itsc2018.txt (pdftotext -layout); the sha256 of the copy matches the original; git show 93ba655: v5b/d1/netgen_bn4.py, plant.py, episode.py, v5b/p1b/meters.py, v5b/p1b/episode.py, v5b/p1/family.py; git diff 93ba655 HEAD and the working tree for these files: no changes; Read paper.qmd lines 1-203 (plant section 110, arms 118, background 63-65); grep references.bib for every key; git grep on the archive branches claude/vsl-lab-core and claude/day-pattern-core for 'III-E', 'Lagrangian control' and the ITSC DOI, to find where the reference came from; grep docs/decisions.md and docs/baseline/BASELINE_2_2026-10-20.md for planned plant citations or open items

### B15. [major] PLANT-F1: q2000 oversaturated without incident; uncontrolled plant loses ~40 % capacity

Raised as major; verification: reproduce: CONFIRMED/major, defend: CONFIRMED/major.

#### PLANT-F1 (R1 PLANT, major, hidden-assumption): q2000 is oversaturated without any incident, and the uncontrolled plant loses about 40 % of capacity

- **Description.** With no incident, the best metered arms serve about 1,450-1,610 veh/h (median during control; single-run maximum 1,724 at q1600 and 1,856 at q2000). Without control, throughput is about 1,006 veh/h at q1600 and 964 veh/h at q2000. At q2000 demand exceeds the metered capacity even on clean days: vehicles in the system at control end have median 223 (minimum 39). FB/PI/AD flag spill in 81-95 % of clean-day runs. The theoretical single-lane IDM capacity is about 1,900-2,400 veh/h. The breakdown discharge of about 1,000 veh/h implies a capacity drop of about 40 %, which looks far above typical empirical values (my general knowledge, not checked against a source). It probably comes from the zipper merges without lane changing (emergency braking at the merges in most runs, PLANT-F5). The paper presents q2000 as an incident cell and does not say that the plant is overloaded there regardless.
- **Evidence.**
  - analyze_plant.out section 'clean-day (none) and NC behaviour' and 'clean q2000: ... n_system at control end min 39, median 223'
  - spill_rows.json none_q2000: N served 1606, NC 964; none_q1600: N 1444, NC 1006
  - idm_capacity.out: 1,894-2,397 veh/h for speedFactor 0.6-1.2
- **Failure scenario.** A reader takes the q2000 gains as incident response. In fact they mix recurrent oversaturation, unlimited virtual storage and incident response. Absolute metering gains are inflated by an unrealistically large capacity drop.
- **How to test.** Report clean-day served flow and end-of-control backlog per q in the paper. Run a capacity tool check: slowly increasing demand, NC versus best meter, discharge after breakdown. Compare the capacity drop with field values from a sourced reference.
- **Related claims.** C22, C33, C84

#### Verifier R2 reproduce: CONFIRMED / major

I reproduced the core fact with my own code on the raw v108 run JSONs from code 93ba655. On incident-free days the plant is oversaturated at q2000 under every controller. Without control it discharges about 1,000 veh/h, which is a capacity drop of 30-48 %. The paper presents q2000 only as a demand level for incident cells and never reports clean-day served flow, backlog or capacity.

The served numbers match the finding exactly:
- Best clean-day medians (eval seeds 7400600-699): q1600 N=c1800 1444 veh/h; q2000 N=f10_8 1606 veh/h.
- NC medians: 1006 veh/h (q1600) and 964 veh/h (q2000).
- Single-run maxima over all 11,540 clean main runs per q: 1724 (q1600) and 1856 (q2000).
- n_system at control end over all 11,540 clean q2000 runs: median 223, minimum 39.
- Static IDM capacity for speedFactor 0.6-1.2: 1894-2397 veh/h.

Stronger proof of oversaturation: in 0 of 11,540 clean q2000 runs did served flow reach the realised demand, and only 2 reached 95 % of it. The served count is biased low by about 5 % because of the 45-s travel time.

Corrections to the finding's wording:
1. The 81-95 % spill share is for q2000 only (FB 0.95, PI 0.81, AD 0.95). It uses the post-run V109 indicator: queue tail within 50 m of the entry, OR mean insertion (depart) delay above 5 s. The B4 flag the code actually shipped (7 m) is 0.00 for every clean-day arm, because queues stop at about 368 of 410 m. At q1600 the V109 share is 0-2 %. At q2000 it is 23 % for N, 9 % for NC and 1 % for FX.
2. Median 223 and minimum 39 are pooled over all controllers and all stages (tool check, tuning, eval). For the best arm (f10_8) the median is 130.5, against a free-flow occupancy of about 25 vehicles, so about 106 vehicles are left over.
3. q1600 is also near or above the metered capacity. The best arm serves a median of 1444 veh/h against a realised demand of about 1616. Only 24 of 100 eval runs reach 95 % of demand, and the median excess backlog is about 27 vehicles.
4. The finding called the 40 % drop "far above typical" from general knowledge. The local full text of Papageorgiou et al. 2008 (TR-C 16, p. 538) supports this: it reports field congestion-discharge rates "lower than qcap by some 5–20%". Their own work-zone simulation drops from about 2300 to about 1800 veh/h. The plant's drop is 1 - 964/1606 = 40 % (q2000), 1 - 1006/1444 = 30 % (q1600), or 48 % against the 1856 maximum. All three are lower bounds, because the metered served rate is only a lower bound on qcap.
5. The suggested cause, "emergency braking at the merges in most runs (PLANT-F5)", does not hold for clean-day NC runs. SUMO statistics show emergencyBraking > 0 in only 3 of 100 (q1600) and 1 of 100 (q2000) clean NC eval runs. Braking on merge edges 4/5 appears in at most 1 run. So the clean-day breakdown happens without emergency braking, and its cause is still speculation.

Effect on the paper (derived): the q2000 gains mix recurrent oversaturation with incident response. On the clean day at q2000, PI already gains 205 s/veh over NC (506.1 vs 301.1), which is more than its gain in the slow_q2000 cell (520.5 vs 359.0, 161.5 s). The headline S1a/S1b verdicts compare metered arms with each other, so they likely survive. That keeps this major, not critical. A reviewer would still require disclosure plus a capacity / capacity-drop check.

Side note, outside this finding: paper L118 calls N "the best constant rate on incident-free days". At q2000, N = f10_8 is a feedback law; the family G includes 30 feedback laws (v5b/p1/family.py@93ba655:4-5).

Checks: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/PLANT-F1-reproduce/clean_day.py -> clean_day.out (per-arm clean-day served, n_system, spill, eval seeds, own code); /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/PLANT-F1-reproduce/clean_all.py -> clean_all.out (all 11,540 clean main runs per q: max served, n_system min/median); /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/PLANT-F1-reproduce/served_vs_demand.py -> served_vs_demand.out (served vs realised demand, all clean runs); /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/PLANT-F1-reproduce/best_arm_saturation.py -> best_arm_saturation.out; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/PLANT-F1-reproduce/clean_spill.py -> clean_spill.out (V109 and B4 spill indicators, free-flow occupancy excess); /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/PLANT-F1-reproduce/idm_cap.py -> idm_cap.out (static IDM capacity, own implementation); /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/PLANT-F1-reproduce/nc_emerg.py -> nc_emerg.out and clean_ebrake_stats.py -> clean_ebrake_stats.out (emergency braking in clean runs from run JSON and raw SUMO stats/logs); Code read at 93ba655 (git archive into /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/PLANT-F1-reproduce/code_93ba655): v5b/p1b/episode.py, v5b/p1b/analysis.py, v5b/d1/plant.py, v5b/d1/netgen_bn4.py, v5b/p1/family.py; pdftotext of papers/refs_papers/1-s2.0-S0968090X07000873-main.pdf -> /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/PLANT-F1-reproduce/pdf/pap2008.txt; read the capacity-drop passages; Read paper.qmd L93, L110, L114, L118, L155, L197, L199-203; docs/decisions.md V109, V113; v108 summary.md tuning lines 20-21

#### Verifier R2 defend: CONFIRMED / major

The core problem survives my best defence. Two parts of the finding are overstated.

What I checked myself. I recomputed all of this from the P1b v108 raw runs (eval seeds 7,400,600-699), with my own code.
- At q2000 with no incident, even the best always-on arm cannot serve the demand. N (f10_8) serves a median 1,606 veh/h during control, against 2,007 veh/h generated. Every one of the 100 seeds still has a backlog at control end: n_system median 130, minimum 66.
- The other arms do worse: PI 1,270 veh/h, FB 1,178, AD 1,152, FX 1,094, NC 964. FB/PI/AD reach the spill flag in 95/81/95 % of clean-day runs.
- NC serves 1,006 veh/h at q1600 and 964 at q2000.
- So the q2000 cells are overloaded whatever the incident. For the always-on arms, 79-92 % of their incident-cell median delay at q2000 is already there on clean days. For PI: 301 of 359 s (slow) and 301 of 373 s (block).
- Added check, derived. On the 40 clean tuning seeds at q2000, IP's slowdown plan (p70_40_8_e4) beats ID's plan (p20_20_14_e4 = PI) by a paired 30.4 % (93 s/veh). ID and IP both run N before onset and keep the plan to the end. So part of the S1b gain at slow_q2000 (11.8 %) may come from better control of the recurring queue after the incident has cleared, not from knowing the incident type.

Defences I tried:
1. Overloading is a normal design choice, not a bug:
   - The cited Papageorgiou et al. 2008 work-zone example uses 2,500 veh/h demand against 2,300 veh/h capacity.
   - The protocol says "No storage limit is imposed" (p1_incident_information.md:46).
   - The paper discloses unlimited storage at 2000 veh/h (paper.qmd:197).
   - This defence holds for the experiment design. It fails for the paper text: no line says that q2000 is above the metered capacity without any incident, or reports the clean-day throughput or backlog.
2. The paper promises to report clean-day costs "separately" (paper.qmd:103), but the draft does not. The protocol makes it worse for the defence: A10 asks for Table 1 = operating map with a clean-day column, and line 102 asks for clean-day delays printed next to S1. Table II has neither. The data exist in internal notes (p1b_summary.md:52; my medians match exactly).
3. "Absolute metering gains are inflated": this hits no number in the paper. The paper reports no comparison with NC; all headline comparisons are between metered arms. Also, recurring delay enlarges the denominator of rel, so it shrinks relative gains rather than inflating them. Here the finding is overstated.
4. "About 40 % capacity drop": this depends on the definition.
   - By Papageorgiou's definition it is 30-48 %. That definition compares the flow a controller can hold at the bottleneck (median 1,444-1,606 veh/h; single-run maximum 1,856) with the uncontrolled discharge (964-1,006 veh/h).
   - By the classical definition, comparing the uncontrolled peak with the uncontrolled discharge, an archive document gives only 14 %: 1,044 to 900 veh/h (claude/vsl-lab-core:docs/lab/t1_bn4_plant_checks.md). Its raw runs are no longer on disk, so I could not verify that figure.
   - The plant is the Flow/Vinitsky bottleneck (code docstring), so this behaviour comes with that benchmark.
   - Even so, Papageorgiou 2008, which the paper cites, gives field drops of "some 5-20 %" (PDF p. 538). Its own microsimulation examples show about 10 % and about 22 %. It also says that throughput gains from merge control depend on the capacity drop.
   - In this plant, metering raises throughput by about 60 % over NC, roughly two to three times what real bottlenecks would allow. The paper says none of this: it gives no capacity, no NC flow and no capacity drop, and the intro still has \citeneeded for the capacity drop.

Severity: major. The headline survives:
- S1b also passes in block_q1600 alone.
- C1 is at q1600, where the clean-day backlog with N is small (median 47).
- But a reviewer would ask for the clean-day throughput and backlog per q, the plant's metering gain or capacity drop compared with sourced field values, and a reading of the q2000 cells as recurring overload plus incident.

Checks: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/PLANT-F1-defend/clean_day_check.py (output clean_day_check.out, clean_day_check.json): per-arm served flow, backlog, delay and spill on 100 eval seeds for none/slow/block at q1600/q2000, from raw run JSON scalars; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/PLANT-F1-defend/clean_plan_compare.py (output clean_plan_compare.out): paired clean-day comparison at q2000 of the IP slow plan vs the ID/PI law vs N; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/PLANT-F1-defend/idm_eq.py (output idm_eq.out): IDM equilibrium capacity with the plant parameters; pdftotext of papers/refs_papers/1-s2.0-S0968090X07000873-main.pdf into /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/PLANT-F1-defend/papageorgiou2008.txt; read pp. 538-539 and 547-549; Code at the run commit extracted to /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/PLANT-F1-defend/code_93ba655; read v5b/d1/netgen_bn4.py and v5b/d1/plant.py; Read paper.qmd lines 55-203; grepped protocols p1_incident_information.md, p1b_addendum.md, p1b_confirm_c1.md, screen_D1/D2, decisions.md, p1b_result.md and p1b_summary.md for capacity, clean-day and storage text; git show claude/vsl-lab-core:docs/lab/t1_bn4_plant_checks.md and t1_bn4_plant_checks_protocol.md (archive BN4 capacity-drop check; raw runs missing)

### B16. [major] PLANT-F2: Meter off and demand stops after 900 s; large delay share in uncontrolled drain

Raised as major; verification: reproduce: CONFIRMED/major, defend: CONFIRMED/major.

#### PLANT-F2 (R1 PLANT, major, disclosure): After 900 s the meter is switched off and demand stops; 22-56 % of the delay accrues in this uncontrolled drain

- **Description.** p1b/episode.py sets the signal to all-green at control end and drains until empty, with no new arrivals after 940 s. Per arm and cell, the median share of total time in system accrued after control end is 7-43 % at q1600 and 27-56 % at q2000 (incident cells 42-56 %). At q2000, 42-59 % of vehicles are still in the system when the meter goes off. In the drain the plant behaves like no control, so the bottleneck can break down. An arm's delay therefore depends on how it hands over the queue at 900 s. The paper says only 'continues until the network is empty'.
- **Evidence.**
  - v5b/p1b/episode.py@93ba655:133 (demand to 940 s), :242-249 (set_all_green, drain)
  - drain_share.out
- **Failure scenario.** An arm that ends control with a large meter queue is penalised by an all-green release that triggers a breakdown. The ranking of arms could then reflect the end-of-control rule rather than incident handling.
- **How to test.** Disclose the rule. As a sensitivity, keep each arm's law active during the drain, or score delay only for vehicles that depart before 940 s with a fixed horizon, then recompute S1, S2 and C1.
- **Related claims.** C34, C24

#### Verifier R2 reproduce: CONFIRMED / major

I reproduced the core facts myself, from the code at the run commit and from the raw evaluation runs.

(1) The code does what the finding says. At 93ba655, v5b/p1b/episode.py:133 generates demand only in [0, 940) s, with departure times rounded up to the 0.5-s step grid, so no desired departure is later than 940.0 s (v5b/d1/demand.py, the generate loop). At control end, :238 clears the incident, :243 sets the signal to all green, :246 restores the VSL and :249 drains for up to 7,200 s. In the drain the plant is therefore in the NC state. The primary metric, delay_s (:253-254, :271), is the mean over all trips of tripinfo departDelay + timeLoss, so all delay that accrues in the drain counts. The cited lines are correct (:133; :242-249). C1 (e7dd561) changes only confirm_c1.py, so it uses the same episode.

(2) The numbers match. My script over 4,400 evaluation runs (seeds 600-699, main runs, all valid and drained) gives these ranges of per-arm medians for the share of total time in system after control end: 7-43 % at q1600, 27-56 % at q2000, and 42-56 % in the q2000 incident cells. Over the incident cells at both q the range is 22-56 %. All of these match the finding.

(3) The paper text is as quoted. paper.qmd:110 says only 'continues until the network is empty', and lines 93 and 110 call the demand 'constant'. Neither line says that demand stops at 940 s or that the meter is all green in the drain.

Small inexactnesses (they do not change the core fact):
- 'At q2000, 42-59 % of vehicles still in the system' holds only for the incident cells. In the no-incident cell at q2000, N is at 25 % and PI at 39 %.
- The title says 'of the delay', but the measured quantity is the share of time in system. My approximate bounds on the delay share in the incident cells (21-56 % lower, 29-61 % upper) are consistent with it.

Mechanism (derived, rough): with a FIFO constant-rate approximation, the implied drain discharge is about 900-1,400 veh/h. Under metering in the clean cells the exit flow is higher: N served 1,606 veh/h at q2000 and 1,444 at q1600. In the drain it is about 1,080-1,390 veh/h. This is consistent with lower discharge once the meter is off, but it does not prove a breakdown. The claim that the ranking of arms depends on the end-of-control rule is still untested: no sensitivity run exists.

Pre-registration: the all-green drain is inherited from the D1 and D2 episodes (v5b/d1/episode.py:143, v5b/d2/episode.py:137). The P1 protocol fixes the plant 'as ported for D1/D2' and mentions 'the drain' (I4). So this is a disclosure gap in the paper, not an undisclosed deviation from the protocol. The headline is not shown to change, so the severity stays major.

Checks: git show 93ba655:v5b/p1b/episode.py, v5b/p1/episode.py, v5b/d1/plant.py, v5b/d1/demand.py, v5b/d1/sumo_runner.py (drain, tts_system), v5b/d1/episode.py, v5b/d2/episode.py: code read; git diff --stat 93ba655 e7dd561 -- v5b/ and grep of e7dd561:v5b/p1b/confirm_c1.py (C1 uses the same episode); /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/PLANT-F2-reproduce/drain_check.py -> drain_check.out (own recomputation from ~/work/phd/v5b1_runs/p1b/v108/runs, 4,400 evaluation runs; arms from v108/result.json, byte-identical to docs/research/results/p1b_result.json); /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/PLANT-F2-reproduce/demand_window_check.py -> demand_window_check.out (generated counts vs 940-s window; exit flow during control per arm); grep of papers/paper_1/paper.qmd for drain, empty, demand and control-period wording (lines 93, 110, 114); grep of protocols p1_incident_information.md, p1b_addendum.md, p1b_confirm_c1.md, protocol_p0p2_v2.md and docs/decisions.md for drain and all-green rules; Compared with round-1 PLANT/drain_share.out: identical numbers

#### Verifier R2 defend: CONFIRMED / major

I argued the author's side, and part of the finding does not hold up. Three points are wrong or overstated. (1) This is not a deviation from the protocol. The meter-off drain is in the frozen code of every study: v5b/d1/episode.py@93ba655:6,142-146 ('uncontrolled drain: all-green, meter off, run until empty', ported from the archive bn4_eval drain_after=True) and v5b/p1/episode.py@93ba655:4,210-217. The rule is the same at e7dd561 (C1). The protocols fix the metric 'after the drain' (screen_D2 A4 h, which P1 §5 uses), and P1 I4 says control (VSL) is 'restored before the drain'. So the rule was not chosen after seeing data. (2) The paper does imply that demand stops. A network can only become empty if inflow ends, and Papageorgiou et al. 2008 (local PDF) also lets demand fall to zero and runs 'in order to have an empty system again'. That passage does not say whether control is switched off. (3) In all 3,200 S1-arm runs the incident had already cleared before control ended. All runs are valid and drained, and 'generated' is the same across arms for each seed. So the drain never overlaps the incident itself.

The core problem still stands. (a) The paper says only 'continues until the network is empty'. It never says that the meter switches to all-green, i.e. no control, for the whole drain. The Discussion and Limitations section is still empty. (b) A large share of the S1 gains accrues after the meter is off. I recomputed this from the raw v108 runs. The mean paired gain of IP over ID is 6.0 s/veh in the control window plus 28.8 s/veh in the drain for slow_q2000 (83 % in the drain). For block_q1600 it is 17.0 + 33.6 (66 %); for C1 it is 18.1 + 22.2 (55 %). (c) In slow_q2000 the drain gain does not come from a smaller leftover queue. ID and IP leave the same median number of vehicles in the system (230 vs 220). But they hand over different states. ID/PI run the n_crit = 14 law and end with about 15 vehicles on edge 4 at q ≈ 1,905 veh/h. IP ends with about 7 vehicles at q ≈ 1,650. The residual queue then drains faster under IP: about 1,150 vs 1,010 veh/h. This rate is a rough point-queue estimate, close to NC's breakdown level of about 980. The finding's failure scenario is therefore plausible for this cell. (d) I ran a what-if; it is an assumption, not a simulation. I kept each run's control-window TTT and drained its leftover vehicles at a common rate C* in {1200, 1500, 1800} veh/h. Under this what-if, IP vs ID in slow_q2000 falls from 11.8 % to about 5 % (CI still above 0, but below the 10 % bar). With control-window TTT the same cell falls to 1.7 %. The S1a FAIL is unchanged. S1b still PASSES, but only in block_q1600 (15-16 %). C1 survives both checks: 13.5-13.7 % in the what-if, 11.6 % on control-window TTT, CI above 0 in both. (e) The project's own architecture review says 'Releasing control during the drain also biases ramp-queue delay across arms' (docs/architecture/review_v0.md:392). The v5.B design keeps control on during the drain (docs/architecture/interfaces.md:52). The defence 'this is the field convention' is therefore weak.

My verdict on the severity: major, not critical. The headline verdicts survive my rough what-ifs. Only a re-run with the control law kept on during the drain can show whether the bold slow_q2000 S1b entry (11.8 %) holds. One small wording error: the member title says '22-56 % of the delay', but the quantity measured is the share of time in system (TTT), not the share of delay. The numbers themselves (shares in system at control end, shares after control end) match my recomputation. C34 is true as written but leaves out the meter-off rule, so PARTIALLY SUPPORTED is right.

Checks: git show 93ba655:v5b/p1b/episode.py, v5b/p1/episode.py, v5b/d1/episode.py, v5b/d1/plant.py, v5b/d1/sumo_runner.py (drain, all-green, demand, tts_system includes the origin queue); git diff 93ba655 e7dd561 on the episode, sim and plant files (empty: same rule for C1); grep of paper.qmd and the protocols (p1, p1b, c1, screen_D1, screen_D2) and docs/ for drain/release/all-green; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/PLANT-F2-defend/drain_defend.py -> drain_defend.out (sanity checks, drain shares, Table II reproduction, control-window TTT rel, split of the gains, S1 verdicts); /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/PLANT-F2-defend/s1_whatif.py -> s1_whatif.out (S1 under a common drain rate, point-queue assumption); /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/PLANT-F2-defend/c1_drain.py -> c1_drain.out (C1 split and what-if); /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/PLANT-F2-defend/handover_state.py -> handover_state.out (meter state at control end per arm); pdftotext of papers/refs_papers/1-s2.0-S0968090X07000873-main.pdf (demand-end and empty-system convention); Read the round-1 PLANT drain_share.out (numbers agree with my own medians)

### B17. [major] PLANT-F3: No-red-crossing enforced by physically impossible SUMO emergency stops

Raised as major; verification: reproduce: CONFIRMED/major, defend: CONFIRMED/major.

#### PLANT-F3 (R1 PLANT, major, unsupported-interpretation): 'No vehicle crossed on red' is enforced by SUMO's instant emergency stops, physically impossible stops at about 26 m/s2

- **Description.** In SUMO 1.27.1 a non-runner cannot pass a red link. If it cannot stop, it overshoots the line, is moved back to the lane end and given speed 0 ('performs emergency stop at the end of lane ... because of a red traffic light'). In P1b there are 44,816 such events in 40,803 runs (11.8 %), all on edge 2, with implied deceleration median 26.4 m/s2 (max 32) and overshoot median 6.0 m (max 11.0 m). In C1 there are 154 events in 144 runs (14.4 %). These are the same 'emergency stops' the paper cites (12.8 %). The zero red crossings is therefore true by construction of the simulator, not evidence of compliance or safety.
- **Evidence.**
  - SUMO v1_27_1 MSVehicle.cpp:4520-4524, 4780-4786
  - estop_times.out (P1b, P1, C1)
  - p1b/episode.py@93ba655:180-183 (crossing = leaving edge 2)
- **Failure scenario.** A reviewer reads 'no collisions, no red crossings' as evidence that the amber design is safe. In reality, 12-14 % of runs contain events that would be red crossings or rear-end conflicts.
- **How to test.** Report these events as 'forced stops / would-be red crossings' with their deceleration. Optionally set a non-zero jmDriveAfterRedTime for all drivers, or add a longer amber, to see how many would cross.
- **Related claims.** C83, C61

#### G3-F2 (R2 G3, minor, unsupported-interpretation): Zero red crossings and zero collisions are partly guaranteed by SUMO, not measured outcomes

- **Description.** In SUMO 1.27.1, a non-runner that cannot stop before a red link is put back at the lane end with speed 0 and logged as an 'emergency stop' (MSVehicle.cpp:4776-4787). So it can never cross on red or crash into the stop line. All 120,045 P1b and 254 C1 emergency stops are at the end of meter-approach lanes 2_x. The car-following model avoids rear-end collisions by braking up to emergencyDecel 9 m/s2. Line 197 presents both zeros as realism results. Their real content is the emergency-stop share, which the paper reports in the same sentence, and the hard-braking counts, which it does not report.
- **Evidence.**
  - SUMO MSVehicle.cpp:4776-4787
  - G3/p1b_log_emerg_lanes.out: emergency stops only at 'end of lane 2_0..2_3' (22,806 + 8,797 + 6,754 + 6,459 lines)
  - G3/c1_log_lanes.out: C1 emergency stops only on 2_x (154 lines)
  - G3/scan_red_cross.out: emergency-stop runs P1b 40,803 / 344,852; C1 144 / 1,100
- **Failure scenario.** A reader takes 'no vehicle crossed on red' as evidence that drivers complied with the meter. In the model, an overshoot (round-1 PLANT: up to about 11 m, about 26 m/s2 implied) is turned into an impossible stop instead.
- **How to test.** Reword, e.g.: 'SUMO prevents red crossings by non-runners; vehicles that could not stop were stopped at the line (emergency stops, reported above). No same-lane collisions were recorded.'
- **Related claims.** C83

#### G4-F1 (R2 G4, major, disclosure): Non-physical forced stops and 9-m/s2 emergency braking at the meter are not disclosed, although they were a pre-registered reported item

- **Description.** Non-runner vehicles that cannot stop at 3.0 m/s2 drive on through amber. If they have not crossed by red onset, SUMO brakes them at the 9 m/s2 emergency limit, and when that is not enough it sets them back to the stop line with speed 0. This happened 44,816 times in P1b (154 in C1). In addition, P1b logs 95,215 meter-edge braking warnings, all at decel = 9.00, and 54,353 of them are not at a forced stop (C1: 554). 44 % of the P1b forced stops (19,898) happen at the very first amber (t = 46-49 s), right after the all-green warm-up. The paper's sentence 'Drivers obey the amber unless they cannot stop comfortably' hides this behaviour. The addendum (p1b_addendum.md:20) lists emergency stops at the meter as a reported item per arm, and the paper reports none.
- **Evidence.**
  - SUMO v1_27_1 MSVehicle.cpp:4520-4523, :4776-4786 (forced stop: position set to the lane end, speed 0), :4975-4983 (warning only when decel >= 9)
  - G4/p1b_emerg_lines.txt (own grep of all 344,852 P1b logs), G4/pair_check_p1b.out, G4/by_type_p1b.out, G4/by_type_c1.out
  - grep -n emergency papers/paper_1/paper.qmd: no matches; docs/research/protocols/p1b_addendum.md:19-20
- **Failure scenario.** A reviewer reads line 149 as a physical gap-acceptance rule. In fact about 0.13 vehicles per metered run are teleported to a halt at the line, and many more brake at 9 m/s2. Arms that discharge more vehicles at speed during amber get more of these events. The size of the effect on delay is not measured.
- **How to test.** Add one sentence plus counts per arm and cell (forced stops and 9-m/s2 brakings at the meter) from the run JSON field emergency_meter or from the logs. Optionally re-run one cell with --tls.yellow.min-decel and emergency-decel settings changed, or with a longer amber, to show that the headline does not move.
- **Related claims.** C61, C20

#### G4-F6 (R2 G4, info, missing-evidence): Event split by type: AV type under-represented in forced stops, runners over-represented in 9-m/s2 braking; runner crossings by type not recoverable

- **Description.** Forced stops in P1b: 1,642 AV against 43,174 human (AV share 3.7 % against 9.8 % of vehicles; 2.4 % at the first amber). C1: 2 AV and 152 human. 9-m/s2 brakings at the meter: AV share 7.5 %. In runner runs, runners have 0 of 940 forced stops but 3,051 of 4,806 brakings at 9 m/s2, while they are 20 % of vehicles. Runner crossings by vehicle type cannot be computed: runner_crossings is stored only by signal state, and the route and tripinfo files are deleted after each run.
- **Evidence.**
  - G4/by_type.py (own demand rebuild, 0 mismatches against generated and n_runners), G4/by_type_p1b.out, G4/by_type_c1.out
  - episode.py@93ba655:175-180 (files deleted), :159 (runner_crossings by state)
- **Failure scenario.** None for the headline. The 'realism rows' produce harsh-braking side effects that are not reported.
- **How to test.** Reported counts as above; to split crossings by type, keep the tripinfo files or log the vType at each crossing in a re-run (needs approval).
- **Related claims.** C62, C61

#### G4-F7 (R2 G4, info, wording): Round-1 evidence misreads SUMO's printed forced-stop 'decel' as a deceleration

- **Description.** SUMO prints decel = myAcceleration - mySpeed (MSVehicle.cpp:4780-4782), which mixes m/s2 and m/s. Most forced stops come right after a 9-m/s2 braking in the same step (40,862 of 44,816), so the printed value is about 9 plus the speed after braking. PLANT's 'implied decel median 26.4 m/s2' is therefore not a deceleration. The real event is a reset from about 17-20 m/s to 0 within one 0.5-s step, with a position set back by a median of about 6 m (max 11 m). The printed values are: AV median 26.0, human median 26.5, p90 28.8.
- **Evidence.**
  - SUMO MSVehicle.cpp:4776-4786
  - G4/estop_speed.py, G4/estop_speed_p1b.out, G4/pair_check_p1b.out
  - PLANT estop_times.out (round-1 wording)
- **Failure scenario.** A deceleration of '26 m/s2' quoted in a reply to a reviewer would be wrong in its units.
- **How to test.** Describe the event as 'speed reset to 0 and position set back to the stop line'.
- **Related claims.** C61

#### G4-F8 (R2 G4, info, hidden-assumption): Idealised kinematics overpredict forced stops 4-6x: the zone shares are upper bounds

- **Description.** My free-road model (no car-following interactions, constant speed in the zone) predicts 0.215 and 0.268 forced stops per run at the first amber (q1600 / q2000), with an AV share of 9.7 %. Observed values are 0.058 and 0.045 per run, with an AV share of 2.4 %. Actual approach speeds or SUMO details therefore differ from my model. The approach-speed distribution at amber onset is not logged.
- **Evidence.**
  - G4/dilemma_pred.py, G4/dilemma_pred.out
  - G4/by_type_p1b.out (first-cycle counts over 146,646 metered s = 0, k = 0 runs)
- **Failure scenario.** Quoting the 40/8/52 % split from G4-F2 as a measured fraction would overstate the dilemma-zone share.
- **How to test.** Log speed and distance-to-line for all vehicles on edge 2 at each amber onset in a small re-run (needs approval).
- **Related claims.** C61

#### Verifier R2 reproduce: CONFIRMED / major

I reproduced the core fact from primary evidence: the SUMO 1.27.1 source, the run code at 93ba655, and my own scan of every raw SUMO log, stats file and run JSON.

How the model works (direct observation):
- At amber, SUMO lets a vehicle brake only if it can stop with its comfortable deceleration. Here that deceleration is 1.5 m/s2, so many approaching vehicles keep going.
- At red, a vehicle without a red-running parameter can never pass the stop line.
- If such a vehicle cannot stop before the line, SUMO lets it overshoot, puts it back at the lane end and sets its speed to 0. This is the 'emergency stop because of a red traffic light'.
- So 'no vehicle crossed on red without runners' (paper.qmd:197) is guaranteed by the simulator. It is not a measured sign of compliance.
- 'Drivers obey the amber unless they cannot stop comfortably' (paper.qmd:149) leaves out the next step: a driver who cannot stop at amber and does not clear the line in 3 s is stopped instantly at red.

All numbers in the finding reproduce exactly:
- P1b: 44,816 events in 40,803 runs (11.8 %), all on edge 2, all caused by red.
- Printed decel: median 26.4, max 32.0. Overshoot: median 5.97 m, max 11.03 m.
- C1: 154 events in 144 runs.
- The paper's 12.8 % uses the same counter.

Small corrections:
1. C1 14.4 % is a share of the 1,000 metered runs. Of all 1,100 runs it is 13.1 %.
2. The printed SUMO 'decel' is not a physical deceleration. With a 0.5-s step it equals v_next - 2 v_old, which understates the average deceleration over the step. A lower bound for that average is about 38 m/s2 (median). The stops are physically impossible either way.
3. The 12.8 % denominator includes 600 no-control runs; metered runs alone give 12.9 %. The 87 % is computed the same way, so the comparison is consistent.

Basis:
- Core facts: direct observation.
- 'Would-be red crossings': derived. The vehicles were moving at at least about 12 m/s when they reached the line, and at about 19 m/s or more just before.
- 'Rear-end conflicts': speculation, not checked.

Why major and not critical:
- The headline results do not depend on these events. In C1 the shares are similar between arms: IP 14 of 100 runs, PI 21 of 100.
- The paper does give the 12.8 % share.
- But it does not explain that these events are instant, impossible stops at the meter line, and it presents zero red crossings as a result. A reviewer would ask for this to be disclosed or fixed.

Extra observation: the runs used --collision.check-junctions false, so 'no collisions' does not cover collisions on the junction lanes.

Checks: Read MSVehicle.cpp (v1_27_1) lines 2775-2800, 2925-2945, 3760-3800, 4495-4535, 4760-4800, 4955-4985, 7585-7625, and the SPEED2ACCEL macro in SUMOTime.h; Extracted the v5b code at 93ba655 and e7dd561 with git archive into /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/PLANT-F3-reproduce/code_93ba655 and code_e7dd561; read p1b/episode.py, p1b/runners.py, d1/plant.py and the relevant parts of d1/sumo_runner.py; grepped for setSpeedMode, jm* and speed settings; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/PLANT-F3-reproduce/scan_estops.py (own parser of all SUMO logs, stats xml and run JSON; outputs p1b_scan.jsonl and c1_scan.jsonl); /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/PLANT-F3-reproduce/tally.py -> tally.out; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/PLANT-F3-reproduce/subset_12p8.py -> subset_12p8.out; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/PLANT-F3-reproduce/denominators.py -> denominators.out (P1b 12.8 % and P1 87 % denominators, from the P1 v99 run JSON); /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/PLANT-F3-reproduce/by_arm.py -> by_arm_c1.out, by_arm_c1_all.out, by_arm_p1b_tail.out; grep -n in paper.qmd for red, emergency and amber (lines 149, 197); read docs/research/results/p1b_result.md:56 and p1_result.md:81 only to find which numbers to check

#### Verifier R2 defend: CONFIRMED / major

I tried five defences. None removes the problem.

(1) Disclosure. The paper does give the count. The 12.8 % at paper.qmd:197 is exactly these events: it is SUMO's emergency-stop counter, and I reproduced it as 7,396 / 57,782 runs (s = 0, evaluation seeds, k = 0). But the paper never says what an "emergency stop" is. Each one is a vehicle whose step position was 0-11 m past the stop line during red. SUMO moved it back to the lane end and set its speed to 0 within one 0.5-s step. The project's own log reads them as braking: V112 says "Amber cut meter emergency braking sharply". So the misreading is likely, not hypothetical.

(2) No explicit safety claim. True. But the sentence stands under "Robustness and realism", next to "no collisions". Line 85 presents the amber model as a realism step ("We model the amber phase explicitly"). So the sentence works as evidence of compliance.

(3) Pre-registration. p1b_addendum.md R4/R6 required reporting the red-crossing share. Reporting it complies with the protocol, but that does not make it informative.

(4) SUMO convention. A reader who knows SUMO knows that default drivers never enter a red link. This helps only that reader, and the paper does not say it.

(5) Limitations section. Discussion and Limitations (lines 199-201) is empty, so nothing in the paper discloses the artefact yet.

Mechanism, from the SUMO 1.27.1 source:
- A vehicle plans to stop at amber or red only if it can stop at 3 m/s² or less. 3 m/s² is the default tls.yellow.min-decel. It is above the vType decel of 1.5, and the run options do not override it.
- Otherwise the vehicle does not brake at all. If it reaches the line on red, SUMO stops it instantly.
- So, for non-runners, "no red crossing" is true by construction. With the 3-s amber at about 26 m/s, the dilemma zone is roughly 78-113 m from the line at amber onset (derived).

Correction to the finding. The "26.4 m/s²" is SUMO's printed "decel". SUMO prints myAcceleration − mySpeed, with myAcceleration = (vNext − vOld)/TS. At TS = 0.5 s this value is about −v, the speed in m/s, not a deceleration. The physical deceleration needed to stop within one step is about v/0.5 ≈ 50 m/s² (derived). So the finding understates the effect; its conclusion still holds.

Severity. The headline is unaffected: 44,816 events among 103.2 M stop-line crossings (0.04 %), about 1.1 per affected run, so S1a/S1b, C1 and the Table II numbers stand. The fix is text only. The severity sits at the low edge of major: both sentences are literally true, but the paper presents a built-in property of the simulator as an observed result, and the nature of the 12.8 % stops is not disclosed.

Checks: Read finding group PLANT-F3 from round2_input.json; Read paper.qmd:81-201 (method, realism rows, results, empty discussion); Read p1b_addendum.md (B1, B2, R4, R6) and the emergency/crossing references in the protocols; Extracted run code 93ba655 and e7dd561 with git archive into /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/PLANT-F3-defend/code_93ba655 and code_e7dd561; read p1b/episode.py, d1/sumo_runner.py, d1/plant.py, d1/netgen_bn4.py, p1b/runners.py; Read SUMO 1.27.1 source (/home/catalin/work/phd/phd_speed_harmo_v6_toolchain/sumo-src, tag v1_27_1): MSVehicle.cpp planMoveInternal (2781-2830, 2924-2945), executeMove (3760-3800), processLaneAdvances (4500-4535), estop warning (4760-4800), updateState (4967), ignoreRed (7585-7625); MSFrame.cpp:513; Own log parser /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/PLANT-F3-defend/estop_scan.py run on P1b v108 and C1 v114, giving p1b_estops.jsonl and c1_estops.jsonl; Aggregation /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/PLANT-F3-defend/estop_agg.py, output in /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/PLANT-F3-defend/estop_agg.out (reasons, edges, decel/offset, JSON-vs-log match, red crossings by runner/non-runner, collisions, denominator search for 12.8 %); P1 no-amber scan /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/PLANT-F3-defend/estop_scan_light.py, output in /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/PLANT-F3-defend/p1_estops_light.out; C1 per-arm breakdown (inline script over c1_estops.jsonl); grep of docs/decisions.md and the results notes for emergency-stop wording (V103, V112; p1b_result.md:56,62)

### B18. [major] PLANT-F4: Crawl lane forces half the inflow through 1 m/s lane with no lane change; not disclosed

Raised as major; verification: reproduce: CONFIRMED/major, defend: CONFIRMED/major, impact: CONFIRMED/major.

#### PLANT-F4 (R1 PLANT, major, hidden-assumption): The 'lane crawl' forces about half the vehicles through a 240-m lane at about 1 m/s with no way out

- **Description.** The depart lane is random and lane changing is off. Lanes 3_2 and 3_3 connect only to 4_1. So every vehicle that entered on lanes 2-3 must cross the 240-m crawl lane at 1 m/s x speedFactor (about 4 min; IDM capacity there about 280-390 veh/h). A real lane blockage lets drivers merge into the open lane. The D2 review found the crawl 1.3-2.4 times more severe than a closure. C1 and the S1b block_q1600 result are measured in this cell.
- **Evidence.**
  - bn4.net.xml connections 3_2/3_3 -> 4_1
  - v5b/d1/plant.py@93ba655:25-29, 34-35
  - docs/research/protocols/screen_D2_incidents.md:92-94
  - idm_capacity.out (1 m/s rows)
- **Failure scenario.** The type-plan advantage over PI in block_q1600 (C1: 16.2 %) may depend on this forced-split artefact and not carry over to blockages with lane changing.
- **How to test.** Disclose it. Run a sensitivity with lane changing on in the 4-lane section (BN4-L), or with a closure plus a long teleport timeout, and re-test IP versus PI in the block cell.
- **Related claims.** C36, C37, C22

#### REPRO-F6 (R1 REPRO, minor, hidden-assumption): Fig. 1 incident extents and the no-lane-change feed of the crawl lane are not shown

- **Description.** The code slows the whole of edge 5 (135 m) and the whole of lane 4_1 (240 m). The figure draws short zones. More importantly, with lane changing disabled, lanes 3_2 and 3_3 feed only 4_1, so about half of the inflow must cross the 1 m/s lane. The incidents.py docstring calls the crawl 'more severe than a closure'. Line 110 says only that 'a lane blockage is represented by a crawling lane'.
- **Evidence.**
  - v5b/d2/incidents.py@e7dd561:5-14, :28-29
  - netgen_bn4.py@e7dd561:62 (lane i -> i//2)
  - fig_plant.py@HEAD:27-30
- **Failure scenario.** Readers picture a local, partial blockage that drivers can avoid, while the simulated incident forces half of the flow through a walking-pace lane. This affects how the lane-crawl results generalise.
- **How to test.** Read the incident and network code; count vehicles whose departLane is 1_2 or 1_3 (they must use 4_1).
- **Related claims.** C25

#### Verifier R2 reproduce: CONFIRMED / major

I reproduced the core fact from primary evidence. In the network the runs used, lanes 3_2 and 3_3 connect only to lane 4_1 (240 m long). Lane changing is off for all vehicles, and the depart lane is drawn uniformly at random. When the crawl is on, 4_1 gets a speed limit of 1.0 m/s. So vehicles that enter on lanes 2-3 cannot avoid the crawl lane. The insertion queue never reached the network entry in the block_q1600 runs. Because of that, the random lane draw is not distorted, and about half of the inflow goes to lanes 2-3 (basis: derived). The raw data agree with this forced split. With no control at q=1600, the flow into edge 4 during the crawl was a median of 1074 veh/h (C1) and 1012 veh/h (P1b), against 1382 veh/h during the slowdown. This fits about 800 veh/h on the free lanes 0-1 plus about 210-275 veh/h through the crawl lane. My own IDM equilibrium calculation gives a crawl-lane capacity of 276 / 336 / 393 veh/h at speedFactor 0.8 / 1.0 / 1.2, which matches the cited 280-390 range. The paper discloses only that lane changing is disabled and that a blockage 'is represented by a crawling lane' (lines 110, 114). It does not say which lane, how long it is, that two of the four upstream lanes feed it exclusively, or that the crawl is more severe than a closure. Line 93 says the queue is stored upstream 'on four lanes'. The Discussion and Limitations section (line 199) is empty. C1 and the S1b crawl result are both measured in this cell. Minor inaccuracies in the finding: (a) 'every vehicle must cross at 1 m/s (about 4 min)' holds only for vehicles on 4_1 while the incident is on; incidents last 120-480 s, so many vehicles crawl over only part of the lane. The crossing time is 240/speedFactor s. (b) The D2 protocol says the crawl's delay was 1.3-2.4 × the closure's, which is a ratio, not '1.3-2.4 times more severe'. Also, the closure in that comparison (0.01 m/s) still had lane changing off, so it was not a closure that drivers could merge around. (c) The protocol line 92 gives 280 m, but the lane in the net is 240 m. The failure scenario, that the type plan's lead over PI depends on this artefact, is untested speculation. It has partial support: in the C1 runs, PI lets only a median of 593 veh/h into edge 4 during the crawl, against 1029 veh/h for the type plan IP. This suggests that PI throttles all four lanes, including the two lanes whose path is free (basis: derived, not proven causal). Severity stays major, not critical: the headline numbers are computed correctly within this model. The problem is undisclosed modelling that limits how far the lane-crawl results generalise, and a reviewer would require it to be disclosed. The Fig. 1 part (REPRO-F6) is minor: the boxes cover about 73 % of each edge, the caption says 'not to scale', and the figure does not show which lanes feed the crawl lane.

Checks: git archive 93ba655 and e7dd561 -> /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/PLANT-F4-reproduce/code_<commit>; read v5b/d1/plant.py, netgen_bn4.py, demand.py, v5b/d2/incidents.py, v5b/p1b/episode.py; diff d1/d2 between commits (identical); /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/PLANT-F4-reproduce/net_conn.py on the cached net -> net_conn.out (lane lengths, connections); /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/PLANT-F4-reproduce/idm_cap.py -> idm_cap.out (own IDM capacity at 1 m/s); /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/PLANT-F4-reproduce/queue_entry.py on v108 and v114 block_q1600 runs -> queue_entry_p1b.out, queue_entry_c1.out (queue reach, depart delay, 4_1 speeds); /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/PLANT-F4-reproduce/e4_rate.py on v114 and v108 NC runs -> e4_rate_c1.out, e4_rate_p1b_nc.out (edge-4 inflow during incidents); /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/PLANT-F4-reproduce/run_keys.py (key structure of one C1 raw run JSON; confirmed no per-lane or tripinfo data kept, so depart lanes cannot be counted directly); Read SUMO 1.27.1 source MSEdge.cpp (getDepartLane RANDOM, insertVehicle) and MSLCM_LC2013.cpp (lcStrategic<0, speedGain<=0 guards); Read paper.qmd lines 93-125, 155, 187-200; fig_plant.py; screen_D2_incidents.md:85-96; p1_incident_information.md:22; grep docs/decisions.md and results notes for crawl/closure/lane change; Compared with round-1 idm_capacity.out (PLANT): values match my own computation

#### Verifier R2 defend: CONFIRMED / major

I argued the author's side and the problem still stands. Two of the finding's points are overstated, but neither removes it.

The best defence has four parts:
(a) The modelling choice was pre-registered and disclosed in the protocols. P1 §1 says "lane 4_1 crawls at 1.0 m/s; lane changing is off (disclosed)", and §8 lists "the block substitute". D2 Addendum A2 states plainly that vehicles on 3_2/3_3 must cross the crawl lane, that the crawl was 1.3–2.4 times more severe than a closure, and that the results "speak only about that crawl". So there is no pre-registration or data-integrity problem.
(b) The paper does state that lane changing is disabled and that the incident is "one lane at 1 m/s" (line 110, line 114). The results always call the cell a "lane crawl", never a "lane blockage".
(c) C1 is a paired comparison inside one plant: IP and PI face the same crawl on the same seeds. Internal validity and the headline numbers are not affected.
(d) The Discussion and Limitations section is still empty in this draft. Fig. 1 is labelled "not to scale", so REPRO-F6's point about the drawn incident extents is weak.

What survives:
- The paper never says the following. With lane changing off (lcStrategic=-1) and departLane="random", every vehicle that enters on the two left lanes stays in its lane. Lanes 3_2 and 3_3 connect only to 4_1. So about half the demand cannot avoid a 240-m lane at about 1 m/s (about 4 min to cross).
- Line 110 says "a lane blockage is represented by a crawling lane", and line 63 uses "lane blockages" as motivation. Together they invite readers to generalise to real blockages, where drivers can merge. The protocol's own "Reading" (D2-A2) forbids that generalisation.

The raw data support the severity and its link to the C1 mechanism (derived, not proven):
- During the crawl at q = 1600 with no control (NC), the median entry rate into edge 4 is only about 1010–1070 veh/h. In the slowdown cell it is about 1380.
- Assuming lanes 0–1 pass q/2, the crawl lane carries roughly 210–270 veh/h. A textbook IDM gives about 280–390 veh/h at a desired speed of 0.8–1.2 m/s.
- PI's measurement counts all vehicles on edge 4, including the packed crawl lane. Always-on PI admits a median of about 593 veh/h into edge 4 during the incident; the IP plan admits about 1029.
- So C1's 16.2 % plausibly depends on the lane-locked split. A blockage that drivers can merge around may not reproduce it. This is untested: I did not run a sensitivity case with lane changing on.

The "about half" share is derived from the code and the network, not observed. Raw runs keep no counts per lane. The median depart delay is about 0.1 s, so insertion was almost never blocked, and a uniform random lane choice then gives about 50 %. This is my understanding of how SUMO handles departLane="random", not something I checked in the SUMO source.

Severity stays major: a paper statement is unsupported as written, a reviewer would require the disclosure, and the headline survives. The title "not disclosed" is partly overstated. The paper does disclose that lane changing is off and that the incident is a crawl. It does not disclose the forced split, how severe the crawl is, or the generalisation limit stated in the protocol.

Checks: Read the PLANT-F4 group from round2_input.json.; git show 93ba655 of v5b/d1/plant.py, v5b/d1/netgen_bn4.py, v5b/d1/demand.py, v5b/d2/incidents.py and v5b/d2/episode.py; git diff 93ba655 e7dd561 on the plant, network and incident files (no changes).; git grep at 93ba655 and at e7dd561 for lane_changing, setLaneChangeMode, departLane, lcStrategic and time-to-teleport.; Parsed the network the runs used: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/PLANT-F4-defend/net_check.py, output in net_check.out in the same folder.; Edge-4 entry rate per C1 arm during the incident: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/PLANT-F4-defend/e4_rate.py, output in e4_rate_c1.out in the same folder.; Edge-4 entry rate for the P1b NC runs: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/PLANT-F4-defend/e4_rate_nc_p1b.py, output in e4_rate_nc_p1b.out in the same folder.; Textbook IDM capacity at crawl speeds: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/PLANT-F4-defend/idm_eq.py, output in idm_eq.out in the same folder.; Searched paper.qmd for crawl, lane-change, blockage, depart-lane, Vinitsky/Flow and limitations text; read lines 93-118 and 195-203.; Searched screen_D2_incidents.md (A2), p1_incident_information.md (sections 1 and 8), p1b_addendum.md, p1b_confirm_c1.md and docs/decisions.md (V101, V129) for crawl and closure disclosures.; Read papers/paper_1/figures/fig_plant.py.; No SUMO simulation was run. Raw runs keep no per-lane counts, so the lane split was derived, not measured.

#### Verifier R2 impact: CONFIRMED / major

I checked the core fact myself and it holds. In the cached net that the runs used (~/work/phd/v5b1_runs/_netcache/bn4_e578788201/bn4.net.xml), lanes 3_2 and 3_3 connect only to 4_1. Edge 4 is 240 m long. The protocol addendum D2-A2 says 280 m, which is a small error in the protocol, not in the paper. Lane changing is off for all vehicles (v5b/d1/plant.py@93ba655:25-29) and the depart lane is random (:34-35). So during the incident, about half of the inflow must cross the 1 m/s lane. At q = 1600 the meter queue never reached the entry, so the share should be close to half; I could not count it per vehicle because no tripinfo was kept.

What changes in the paper:
(1) No number changes. Table II, Fig. 2, C1 (16.2 % [7.3, 23.7]) and Fig. 3 are correct for the plant as built.
(2) No pre-registered verdict changes. S1a fails in every cell against PI, even without the crawl cells. S1b part (a) also passes in slow_q2000 (11.8 %), so S1b passes even if both crawl cells are set aside (p1b_result.json S1b_cells_both_views = [slow_q2000, block_q1600]). C1 is a pre-registered statement about this exact cell, so it stays valid inside its scope.
(3) Pre-registration integrity is fine. P1 protocol line 22 says "lane changing is off (disclosed)". D2-A2 says the block "is NOT a closure" and that the results "speak only about that crawl".
(4) The paper does not carry that limit. Line 110 ("so a lane blockage is represented by a crawling lane") and line 114 ("one lane at 1 m/s") do not say that half the flow cannot avoid the lane, or that the crawl is not a closure. Line 63 uses lane blockages as the motivation. These sentences are incomplete in a way that misleads; they are not false. They need a disclosure. The future Discussion and Abstract must not generalise C1 to lane blockages.

Why it matters more than wording: the crawl 1600 cell is the paper's only place where type information beats the strongest always-on arm, both in the report-only row (18.0 %) and in C1. All C1 robustness rows, the positive S2 lower bounds and the d* entries for the crawl columns also come only from these cells. In the raw runs, the advantage seems tied to how this incident works:
- During the crawl, always-on PI (p70_120_8_e4, set point 8 on the edge-4 count) sees about 14-18 vehicles on edge 4. It throttles all four lanes: median rate 849 veh/h, at the 200 veh/h floor in 55 % of updates, so the free lanes 0-1 are held too.
- The type plan (set point 16) barely acts during the crawl (1768 veh/h). It throttles after clearance (751 versus 1300 veh/h), when the queued lanes 2-3 empty into edge 4. C1 shows the same pattern: PI at 868 veh/h with 52 % at the floor; IP at 1835 veh/h.
- Another point: the final bottleneck (edge 5) already has one lane. So a real blockage of one lane on edge 4, with merging allowed, might cut capacity much less than this crawl. That is my inference, not tested.

Whether IP still beats PI with lane changing on (BN4-L) or with a closure is unknown without new simulations, which I did not run. Because no headline number or verdict is overturned, critical is not justified. Because the plant cannot be described honestly without this fact, and a reviewer would require it disclosed and probably a sensitivity run, the stated severity of major is right.

Checks: Read groups['PLANT-F4'] from round2_input.json; git show 93ba655:v5b/d1/plant.py, v5b/d2/incidents.py, v5b/d1/netgen_bn4.py, v5b/p1b/family.py, v5b/p1b/meters.py (PI law and edge-4 count); Parsed the cached net with /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/PLANT-F4-impact/net.py (output net.out); Read paper.qmd lines 60-203 and grepped it for crawl, blockage and lane-change wording; Read protocol text: p1_incident_information.md:22,136; screen_D2_incidents.md addendum A2; p1b_confirm_c1.md; Read p1b_result.json: tuned arms, S1 pass flags, S1b cells, block_q1600 ID_vs stats; Raw P1b eval and C1 runs (own code): /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/PLANT-F4-impact/mech.py (output mech.out): delay, rate and edge-4 count during the incident per arm; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/PLANT-F4-impact/phase.py (output phase.out): rate and count before, during and after the incident; no-incident delays; No SUMO simulations run; I did not test whether IP still beats PI with lane changing on

### B19. [major] PROV-F2: Earlier P1 round omitted despite addendum promise; its results differ

Raised as major; verification: reproduce: CONFIRMED/major, defend: CONFIRMED/major.

#### PROV-F2 (R1 PROV, major, disclosure): The earlier full run P1 is not reported, although the P1b addendum promised it; its results differ in the C1 cell, S2 and S3

- **Description.** P1 (296,527 runs; the same statements S1-S3 and cells; no amber; A without PI-law plans) is absent from the paper. p1b_addendum.md:5 says 'Both are reported.' P1's results differ materially. In the C1 cell block_q1600, IP vs always-on PI was -0.7 % (diff -1.7 s, 95 % CI [-15.8, 21.2]), against +18.0 % in P1b. The S2 lower bound for block_q2000 was -1.8 % in P1, against +3.5 % in P1b; the paper says the lower bounds were 'positive in the two lane-crawl cells'. The S3 break-even for slow_q2000 was 26 s in P1, against 120 s in P1b; the paper says 'about 120 s'. For block_q2000 it was 210 s in P1, while in P1b IP was never ahead. The C1 effect therefore appeared only after the post-P1 design change (a PI-law type plan, p20_20_16_e4). The paper uses one P1 number (87 %) without naming P1.
- **Evidence.**
  - p1b_addendum.md@75bcd2b:5
  - ~/work/phd/v5b1_runs/p1/v99/run.log final 'done:' line (S2 brackets)
  - scratch p1_block1600.py: P1 IP(c2000-f40_14) vs PI(p40_40_10_e4) rel -0.7 %
  - scratch p1_vs_p1b.py: S3 d_star P1 slow_q2000 25.8, block_q1600 0.0 'IP never ahead', block_q2000 210.1; P1b 120.4, 240 '> max', 0.0
  - paper.qmd:193, 197
- **Failure scenario.** A reader assumes the reported P1b result is the only run of these hypotheses. In fact, an earlier run with the same statements gave no type-plan advantage over PI in the confirmed cell, and different S2/S3 readings.
- **How to test.** Re-run scratch p1_block1600.py and p1_vs_p1b.py. Compare the result.json decision fields of p1/v99 and p1b/v108.
- **Related claims.** C11, C53, C54, C60

#### TEXT-F2 (R1 TEXT, major, disclosure): The earlier P1 round is omitted although the addendum says both are reported; P1 numbers leak in

- **Description.** The paper never mentions P1 (no amber; A without PI plans; seeds 500-599; resumed once). Yet it uses P1 data: '87 % (no amber)' (line 197) and '13.3 %' (line 193). The Table II caption says '(P1b)', a label the paper never defines. In P1 the C1 cell showed IP vs PI at -0.7 % and d* 'IP never ahead PI'. The confirmed effect appeared only after the P1b redesign (amber plus PI-law plans).
- **Evidence.**
  - p1b_addendum.md:5 ('P1 stays in the record ... Both are reported')
  - paper.qmd:165, :193, :197
  - docs/research/results/p1b_result.md:52-58
  - docs/research/results/p1b_verification/out/p1_vs_p1b.log (P1 block_q1600: IP vs PI -0.7; d* never ahead PI)
  - /home/catalin/work/phd/v5b1_runs/P1_EVAL_STARTED.json ('resume': true)
  - CLAUDE.md: every run reported; no hidden variants
- **Failure scenario.** A reader cannot see that the headline cell was null in the first round, or that the protocol changed between rounds. That is a forking-paths concern a reviewer would require to be disclosed.
- **How to test.** Add a short 'study history' paragraph with P1's S1/S2 verdicts and the P1 to P1b changes (p1b_result.md §4).
- **Related claims.** C13, C85

#### Verifier R1 reproduce: CONFIRMED / major

I reproduced the core fact from primary evidence. The P1b addendum says both rounds are reported, the paper does not mention P1 anywhere, and P1's results differ from P1b's in the C1 cell, in S2 and in S3. I recomputed every cited number from the raw run JSONs with my own numpy code, and the bootstrap intervals match to within about 0.4 points.

Meaning: the same statements (S1a, S1b, S2, S3) were tested twice on the same plant and the same four cells. The first round (P1) had no amber phase, and its type-plan set A had no PI-law plans. The paper shows only the second round (P1b) and its confirmation C1. It never says that an earlier full round existed, or that the round changed the design. Two P1 numbers still appear in the text.

Facts that hold:
(1) The addendum (p1b_addendum.md@75bcd2b:5, same as the working tree) says: "P1 stays in the record as the earlier run. P1b becomes the paper's main result. Both are reported." Line 4 says the arms, statements and statistics are unchanged from P1.
(2) paper.qmd at HEAD (the PDF has the same text) has no P1 and no earlier-round disclosure. The only traces are the caption "(P1b)" at line 165 and "87 % (no amber)" at line 197. Line 145 says "every study was run once". The Discussion section is empty and the Conclusion says "To be written".
(3) P1 ran code 85f7d34 with a clean tree. It has 296,527 run files: 14,546 tool checks, 71,920 tuning and 210,061 evaluation runs, per run.log. All 49,461 metered evaluation runs have signal 'continuous'. A has 100 actions and no PI-law plans (family.py@85f7d34:7, "A = G x {stay, back}"). In P1b the signal is 'amber' and A has 120 actions, 20 of them PI-law plans.
(4) C1 cell, P1, IP c2000-f40_14 against PI p40_40_10_e4: rel −0.70 %, diff −1.69 s, 95 % CI [−15.8, 21.1]. At the S1 level 0.99375 the CI is [−24.7, 33.6]; the JSON has [−24.65, 33.24]. P1b: +17.98 %, CI [9.2, 31.3] at 0.99375; the JSON has [8.9, 31.6].
(5) S2 brackets in P1: [−7.4, 39.9], [−9.1, 13.3], [3.3, 26.7], [−1.8, 19.8]; the JSON has [−7.1, 39.7], [−9.1, 13.3], [3.4, 26.6], [−1.8, 19.8]. In P1 only one lane-crawl cell had a positive lower bound. P1b reproduces to its Table II: [−0.4, 47.9], [−2.4, 19.3], [0.4, 25.4], [3.5, 22.4].
(6) S3 detection break-even d*, recomputed exactly, cells in the order slow 1600, slow 2000, crawl 1600, crawl 2000. P1: 45.3; 25.8; 0.0 ('IP never ahead'); 210.1 (binding arm FB). P1b: 2.6; 120.4; 240 ('> max', binding arm N); 0.0 ('IP never ahead').
(7) The paper's "87 %" is a P1 number: 43,370 of 50,061 non-replicate P1 evaluation runs had at least one emergency stop (86.6 %). The P1b figure is 7,396 of 57,782 (12.8 %).
(8) The paper's "13.3 %" at line 193 is P1's slow_q2000 upper bound. The P1b upper bounds in Table II run from 19.3 to 47.9 %, so line 193 contradicts the paper's own table.

Corrections to the finding:
(a) The tracers' sentence "The C1 effect therefore appeared only after ... a PI-law type plan, p20_20_16_e4" is not supported as a cause. I restricted P1b's A to P1's plan set (G only) and refit IP on the P1b tuning seeds. The best plan, c1800-f40_16, still beats PI on the P1b evaluation seeds by 17.5 % [6.5, 23.6]. So the C1-cell effect in P1b does not depend on the PI-law plans. The P1-to-P1b swing comes from the other changes: the amber plant, the re-tuned arms (PI p40_40_10_e4 became p70_120_8_e4), and the new seeds.
(b) The headline verdicts are the same in both rounds: S1a FAIL, and S1b PASS in slow_q2000 and block_q1600. C1 was confirmed on fresh seeds. The headline therefore survives, and severity stays major (disclosure, forking paths, one wrong number) rather than critical.
(c) P1's resume ('resume': true in P1_EVAL_STARTED.json) reused only the 6,146 tcheck-A runs (run.log line 14). The evaluation line says "0 reused", so the evaluation data are not affected.
(d) "Both are reported" could be read as "both are in the record", and P1 is reported in p1_result.md. But the sentence sits next to "P1b becomes the paper's main result", and the paper's own plan comment lists p1_result.md as a source of truth (paper.qmd:33). So the omission from the paper stands.

Checks: git show/diff of p1b_addendum.md at 75bcd2b vs HEAD (no diff); sed of lines 1-15; grep of paper.qmd and pdftotext of paper.pdf for P1/earlier/87/13.3/120 s/pre-registered/once; Read of the result.json decision, S1, S3 and table1 controllers in p1/v99 and p1b/v108 (small python summaries); /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/PROV-F2-reproduce/ip_vs_pi_raw.py (+ .log): IP vs PI per cell from raw runs, paired bootstrap B=20,000 at 95 % and 0.99375; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/PROV-F2-reproduce/s2_bracket_raw.py (+ .log): S2 OR_in/ORX_4 bracket from raw runs at level 1-0.05/4; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/PROV-F2-reproduce/s3_dstar_raw.py (+ .log): S3 detection-delay break-even from raw runs with canonical no-switch fallback; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/PROV-F2-reproduce/estop_share.py (+ .log): emergency-stop share, P1 vs P1b non-replicate eval runs; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/PROV-F2-reproduce/p1b_gonly_counterfactual.py (+ .log): P1b IP restricted to P1's plan set, tuned on P1b tuning seeds, vs PI on eval seeds; git show 85f7d34:v5b/p1/{stats.py,analysis.py,family.py} and 93ba655:v5b/p1b/{family.py,analysis.py}: definitions of rel, S2 x/y, d* crossing, canon_sw and A; run.log grep for 'runs to do' and 'reused' (resume scope); P1_EVAL_STARTED.json args; grep of docs/decisions.md V108-V129 for any decision to drop P1 from the paper (none found)

#### Verifier R1 defend: CONFIRMED / major

Meaning: P1 was a complete first evaluation of the same pre-registered statements S1a/S1b/S2/S3 in the same four cells. It had no amber phase, and the incident action set A had no PI-law plans. P1b re-ran everything with amber, PI-law plans in A, a rate clip and fresh seeds. The P1b page itself says P1 "stays in the record as the earlier run ... Both are reported". The paper never mentions P1, but it still uses P1 numbers without saying where they come from.

Best defence, and what each point is worth:
(1) The paper is a draft. The Abstract, Discussion/Limitations and Conclusion are empty (paper.qmd:58, 199-203), so the disclosure could still be added. But the BL-2 open-items list (docs/baseline/BASELINE_2_2026-10-20.md:74-82) has no plan to report P1. And the sections already written say things that only hold without the P1 history: "All statements were pre-registered before any data were produced" (paper.qmd:69) and "every study was run once" (paper.qmd:145).
(2) P1's differences come from the design change. P1 is not a failed replication of the same controller. In P1, IP's crawl plan was integral feedback f40_14 against PI p40_40_10_e4. In P1b it is the PI law p20_20_16_e4 against a retuned PI p70_120_8_e4, on a plant that now has amber. The redesign reason (the controller-family confound, V103; amber is necessary, V105) was recorded, and the addendum was approved and hashed before P1b ran. This reduces the forking-paths concern but does not remove it. The change was decided after seeing P1, where IP vs PI in the C1 cell was null, and it plausibly helps IP against PI.
(3) The pre-registered S1 verdicts were the same in both rounds (S1a FAIL, S1b PASS in the same two cells). C1 confirmed the P1b effect on fresh seeds. So the headline survives: severity stays major, not critical.
(4) "Both are reported" could be read as "in the record" only. That reading is weak. The same line calls P1b "the paper's main result", and the roadmap maps paper_1 to "P1, P1b, C1" (docs/roadmap/thesis_roadmap_v0.md:30).

The problem survives on two counts: the promise in the pre-registered page is not kept, and P1 data appear in the paper without attribution. The '13.3 %' at paper.qmd:193 is P1's slow_q2000 upper bound. P1b's smallest upper bound is 19.3 %, and the paper's own Table II shows 19.3, so the sentence is wrong as written. The '87 % (no amber)' at paper.qmd:197 is also P1. It compares two different studies (different seeds, action set A, PI tuning and rate clip), so it is not a clean ablation of amber alone.

Failure points / tests: if the Discussion adds a study-history paragraph (P1's verdicts, the P1→P1b changes and why, IP vs PI −0.7 % in P1) and line 193 is corrected to 19.3 %, the finding is resolved. Re-run my scripts to check the numbers.

Checks: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/PROV-F2-defend/p1_vs_p1b_ipvspi.py: recomputes IP vs PI in block_q1600 from raw run JSONs for P1 and P1b, with an own numpy bootstrap (B=20,000); output in p1_vs_p1b_ipvspi.out in the same folder; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/PROV-F2-defend/s3_compare.py: S3 d* and S1 decisions from both result JSONs; output in s3_compare.out; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/PROV-F2-defend/estop_share.py: emergency-stop shares from raw runs (P1 86.6 %, P1b 12.8 %); output in estop_share.out; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/PROV-F2-defend/find_number.py: locates which JSON keys equal 13.3 / 87 / 12.8 (13.3 is the P1 S2 upper bound only); Python one-liners: S2 x/y brackets and the tune.arms plans from both result JSONs; sha256sum of the raw and committed result JSONs; git show 93ba655 of p1b_addendum.md, sha256 compared with P1B_EVAL_STARTED page_sha256; Read paper.qmd in full (203 lines); pdftotext of paper.pdf to confirm the same text is rendered; grep of docs/decisions.md V96-V129, BASELINE_2 open items, the roadmap, and the p1b notes for any plan to report or disclose P1

### B20. [major] REPRO-F3: CRN claim overstated and unsupported by reported experiment or citation

Raised as major; verification: reproduce: CONFIRMED/major, defend: CONFIRMED/major.

#### REPRO-F3 (R1 REPRO, major, unsupported-interpretation): CRN statement (line 141) is too general: CRN held exactly until insertion timing diverged

- **Description.** The paper says that a change of controller changes later random draws, so equal seeds do not give CRN. Two seed pairs were re-simulated. In seed 7400700 (no spill to the entry), IP and PI had identical departLane, speedFactor and departure for all 403 vehicles, although the controllers differed from t = 40 s. In seed 7400760 the streams split exactly at the first insertion delay caused by PI's queue (475 vs 476 s); after that, the lane draws of vehicles inserted on time also differ (21/23). The source of the claim is a reading of the SUMO source code (prior_art_P1_P2.md:34), not a measurement, so 'We found' overstates it. The headline results do not depend on it: the comparisons are still validly paired, only with less variance reduction.
- **Evidence.**
  - scratch/crn_check.py and scratch/crn_check2.py outputs
  - docs/research/prior_art_P1_P2.md:34
  - plant.py@e7dd561:32-38 (departLane='random')
- **Failure scenario.** A reviewer reproduces paired runs, observes identical vehicle streams in non-spill seeds, and doubts the stated mechanism behind the honest-bounds argument.
- **How to test.** Re-run more seed pairs with --keep-files (scratch/spot_run.sh), compare tripinfo, and relate divergence to depart delays and spill.
- **Related claims.** C52

#### TEXT-F16 (R1 TEXT, minor, citation): 'We found' the CRN effect in SUMO: no experiment is reported and prior work is not cited

- **Description.** Line 141 says 'We found that in SUMO a change of controller also changes later random draws'. The only record is an agent's reading of the SUMO source (MSBaseVehicle::getRNG). Klein et al. 2024 (CRN broken in agent-based models) [VERIFY] appears in the prior-art note but is not cited. The claim that paired runs 'do not share common random numbers' is also overstated: demand (route file) and the incident window are common to all arms.
- **Evidence.**
  - paper.qmd:141
  - docs/research/prior_art_P1_P2.md:31, :34
- **Failure scenario.** A reviewer asks for the evidence behind the claim.
- **How to test.** Cite the source mechanism, or show a two-run divergence test; say what pairing does preserve.
- **Related claims.** C13

#### Verifier R2 reproduce: CONFIRMED / major

I reproduced the core facts of REPRO-F3 from primary data: the per-vehicle tripinfo and route files kept by the round-1 spot re-runs, the production C1 run JSONs in v114, and the code at e7dd561. I did not run SUMO myself. To show that the kept files stand for the runs that actually produced C1, I compared all 4 spot JSONs with the production JSONs: every field is equal (wall times excluded), including the result hash.

Seed 7400700 (IP = c1800-p20_20_16_e4, PI = p70_120_8_e4):
- The route files are identical between the two arms (403 vehicles, 37 AV).
- departLane, speedFactor, depart and departDelay are equal for 403/403 vehicles.
- The controllers did differ from the start of control: the control loop starts after the 40 s warm-up, with initial q 1800 vs 1500.
- The traffic itself differed: trip duration differs for 394/403 vehicles.
- So the SUMO draws that tripinfo records stayed common even though the controller changed the traffic.

Seed 7400760:
- The departure draws are equal for every vehicle planned before 475 s (194 vehicles inserted on time in both arms, 0 lane differences).
- The first divergence is main.226, planned at 475 s: IP inserts it at 475.00 s (lane 1_3), PI at 476.00 s (departDelay 1.0, lane 1_0).
- After that, 21 of the 23 vehicles inserted on time in both arms have a different departLane. This matches the finding exactly.

Two small imprecisions in the finding:
- The 475 s delay is not the first insertion delay. Both arms had identical earlier delays from t = 20 s (in seed 7400760: IP 68 vehicles with delay > 0, max 1.5 s). The split happens at the first insertion delay that differs between the arms.
- "Caused by PI's queue" is an inference. It is supported by PI's max_queue (218 vs 165) and mean depart delay (20.45 s vs 0.11 s), but not observed directly.
- One more draw differs late in the run: main.391 has a different speedFactor (0.95 vs 0.72) after a 36 s insertion delay in PI.

plant.py@e7dd561:34 sets depart_lane="random" (inside lines 32-38). Lane changing is disabled (plant.py:26). The source of the claim, prior_art_P1_P2.md:34, says literally "agent read the source" (MSBaseVehicle::getRNG).

Searching the repo turned up no experiment that measures this effect on the paper's BN4 plant. The P1 protocol's T3 is a determinism check (same seed twice), not a cross-arm CRN test. protocol_p0p2_v2.md:318 also asserts that the draws diverge, but that note is about a different plant and is not a measurement either. Klein et al. 2024 is listed in the prior-art note but is not in paper.qmd or references.bib.

How general is the paper's sentence? I used a proxy over the C1 v114 JSONs: if two arms have exactly the same mean depart delay on a seed, their insertion timing was most likely identical. IP vs PI have exactly equal mean depart delay in 56/100 seeds, IP vs NC in 88/100. So in a large share of seeds the insertion-level random stream very likely stayed common. This is derived evidence, not a direct observation of the draws.

Conclusion: the sentence at paper.qmd:141 is too general as written ("a change of controller also changes later random draws ... do not share common random numbers"). It is also not backed by any reported measurement ("We found"). Demand, the incident window and, in many seeds, all insertion draws are in fact shared.

Severity: major under the given definition (a paper statement unsupported and partly false as written), not critical. The paired-seed analysis (median of paired differences, bootstrap) does not assume CRN, so the S1/C1/Table II numbers are not affected. That last point is my assessment, not a recomputation.

Uncertainty: I did not check the SUMO source mechanism (getRNG lane pool). I am also not certain whether SUMO's IDM uses any random draw that tripinfo does not show. So "CRN held exactly" in seed 7400700 is proven only for the attributes tripinfo records.

Checks: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/REPRO-F3-reproduce/crn_verify.py (output crn_verify.out in same dir): spot vs production JSON equality, route-file equality, per-vehicle draw comparison, first divergence, on-time lane differences, meter_log, duration divergence; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/REPRO-F3-reproduce/c1_insertion_proxy.py (output c1_insertion_proxy.out): equal mean depart delay across 100 C1 seeds per arm pair; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/REPRO-F3-reproduce/sf_diff.py: the one differing speedFactor in s7400760; git archive e7dd561 and 93ba655 into /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/REPRO-F3-reproduce/code_*; diff -rq vs round-1 code_e7dd561 (identical except __pycache__); Read v5b/p1b/episode.py@e7dd561 (warm-up, seeds, incident window, control loop), v5b/p1/meters.py replicate_seeds, v5b/p1b/meters.py step/update, v5b/d1/plant.py; grep paper.qmd:141, prior_art_P1_P2.md:31-34, protocols p1/p1b/c1 and protocol_p0p2_v2.md for CRN text; grep decisions.md; grep Klein in paper and bib; git log -S for the sentence's origin

#### Verifier R2 defend: CONFIRMED / major

Defence attempted. The best points for the author: (1) The mechanism is real. In the faithful spot re-run of seed 7400760 (its hashes match the v114 records), the IP and PI vehicle streams are identical until the first insertion delay that differs between the arms (main.226, wanted 475 s; IP delay 0 s, PI delay 1 s). After that, 21 of the 23 vehicles inserted on time in both arms got a different random lane, and one speedFactor also differs. In C1, 44 of 100 IP-PI seed pairs have different mean departDelay, a proxy for this loss of synchronisation. (2) The error goes in the conservative direction: it understates how well the runs are paired, so it inflates no number. Paired-by-seed differences and the bootstrap stay valid. The in-sample oracle is optimistic even under full CRN. (3) The Discussion section is still empty, so a fuller disclosure may be planned.

None of this saves the sentence as written. (a) 'paired runs with equal seeds do not share common random numbers' is false in its absolute form. Arrivals, vehicle types and runner flags come from NumPy keyed on the seed: the route files are identical across arms, and generated counts are equal in all C1 pairs. The incident window is also common, and the paper itself says so at line 114. SUMO's own lane draws are common until insertions diverge. In seed 7400700 all 403 vehicles had the same departLane, speedFactor and departDelay under IP and PI. By the same proxy, 56/100 C1 IP-PI pairs and 100/100 N-vs-NC pairs keep identical insertion timing. So the general clause 'a change of controller also changes later random draws' is also wrong as a universal rule. It holds only when the controllers delay insertions differently (queue spill to the entry). (b) 'We found' has no experiment behind it in the repo. The only record is docs/research/prior_art_P1_P2.md:34 ('agent read the source'), written at commit 8e96f1d. The P1/P1b/C1 protocols do not mention CRN. The paper gives no citation; Klein et al. 2024 is listed in the note but not cited. The precise disclosure that exists (protocol_p0p2_v2.md:318) belongs to a different study line and is not in the paper. Result: the statement is false and unsupported as written, but no headline (S1a/S1b, C1, Table II) depends on it. That is major under the given definitions, at its low end, and one sentence can fix it. Suggested wording: 'Demand and incidents are common across arms; SUMO's own draws (here the insertion lane under departLane=random) lose synchronisation once controllers delay insertions differently, so pairing reduces variance only partly.' Uncertainty: I did not read the SUMO C++ source (it is under the v6 toolchain, a boundary). So the getRNG/lane-RNG-pool mechanism is inferred from the observed behaviour and from my general knowledge of SUMO, not verified in code. The 56/44 split uses mean departDelay as a proxy; I checked per vehicle only on the two spot seeds.

Checks: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/REPRO-F3-defend/crn_own.py: spot vs raw v114 hash and delay; route-file equality; per-vehicle speedFactor/departLane/departDelay comparison for seeds 7400700 and 7400760; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/REPRO-F3-defend/crn_own2.py: first vehicle with a different departDelay; first lane difference; the speedFactor difference; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/REPRO-F3-defend/crn_timeline.py: 100-s timeline of lane and departDelay differences, seed 7400760; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/REPRO-F3-defend/crn_after475.py: recount of REPRO's 21/23; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/REPRO-F3-defend/desync_share.py: C1 v114, 100 seeds, equal-mean-departDelay proxy for IP/PI/N/NC pairs; git show e7dd561/93ba655 of v5b/d1/plant.py, v5b/d1/demand.py, v5b/p1b/episode.py, v5b/p1/meters.py, v5b/p1b/runners.py; grep of the P1/P1b/C1 protocols, decisions.md, results notes and git log for CRN/RNG; read paper.qmd:93-145 and 199; sumo --help (option list only, no simulation): --thread-rngs exists (pre-allocated RNG pool); Not done: reading the SUMO C++ source (it is under the v6 toolchain, a boundary); no new SUMO runs

### B21. [major] S1-F1: Table II caption inverts the sign convention

Raised as major; verification: reproduce: CONFIRMED/major, defend: CONFIRMED/major.

#### S1-F1 (R1 S1, major, wording): Table II caption inverts the sign convention

- **Description.** The caption says 'Rel in %, positive favours the second arm'. In every row ('ID vs PI', 'IP vs ID', 'IP vs PI'), rel = median(r − t)/median(r), with t the first-named arm. A positive value favours the first-named arm. For example, 'IP vs ID 22.0' means IP is better.
- **Evidence.**
  - papers/paper_1/paper.qmd:165; paper.pdf Table II caption (pdftotext line 117)
  - paper.qmd:145 'positive values favour arm t over reference r'
  - v5b/p1/stats.py@93ba655:52-63
- **Failure scenario.** A reader of the table alone takes 'ID vs PI −17.9' to mean ID beats PI by 17.9 %, which is the opposite of the result.
- **How to test.** Read the caption against the text at line 155 ('ID was never better ... −17.9 %'). The fix is 'positive favours the first-named arm'.
- **Related claims.** C69, C56

#### TEXT-F4 (R1 TEXT, major, discrepancy): The Table II caption inverts the sign convention

- **Description.** The caption says 'positive favours the second arm'. By line 145, rel = median(r - t)/median(r) favours t, and t is the first-named arm. For example, 'ID vs PI -17.9' means ID is worse; line 155 reads it that way ('never better').
- **Evidence.**
  - paper.qmd:165 vs :145, :155, :174
  - p1b_result.md:3, :69
- **Failure scenario.** A reader of the table alone reverses every conclusion (for example, that PI beats IP in block_q1600).
- **How to test.** Change the caption to 'positive favours the first-named arm'.
- **Related claims.** C12

#### FU2-1-F3 (R2 FU2, major, wording): Table II caption sign convention inverted (re-confirmed from the code that ran)

- **Description.** This duplicates S1-F1, and I confirm it independently. analysis.py@93ba655:353-355 calls paired(r = second-named arm, t = first-named arm). With rel = median(r - t)/median(r), positive favours the first-named arm, but the caption says 'the second arm'. All 12 values and the bold pattern are correct.
- **Evidence.**
  - v5b/p1b/analysis.py@93ba655:353-355
  - v5b/p1/stats.py@93ba655:52,63
  - paper.qmd:145,165; paper.pdf Table II caption
  - FU2-1/s1_indep.out
- **Failure scenario.** A reader of the table alone takes 'ID vs PI -17.9' to mean ID beats PI.
- **How to test.** Compare the caption with paper.qmd:145 and :155. Fix: 'positive favours the first-named arm'.
- **Related claims.** C69

#### Verifier R1 reproduce: CONFIRMED / major

Meaning: each row of Table II compares two arms by rel = median(r − t)/median(r), where delay is the cost (lower is better). A positive rel means arm t had the lower delay. In the code, t is always the first-named arm in the row label. So a positive value favours the first-named arm. The caption says the opposite ("positive favours the second arm").

I checked this myself from primary evidence. (1) v5b/p1/stats.py@93ba655:52,59,63 sets d = r - t and rel = median(d)/median(r). The working tree is identical to 93ba655 for stats.py and p1b/analysis.py (git diff is empty). (2) v5b/p1b/analysis.py@93ba655 builds the three rows this way: line 353 `_two(D[r], D["ID"], ...)` for r in L0 gives "ID vs PI", with r = PI and t = ID. Line 354 `_two(D["ID"], D["IP"], ...)` gives "IP vs ID", with r = ID and t = IP. Line 355 `_two(D[r], D["IP"], ...)` gives "IP vs PI", with r = PI and t = IP. The first-named arm is t in every row. (3) I recomputed all 12 values in rows 1-3 from the 1,200 raw run files in ~/work/phd/v5b1_runs/p1b/v108/runs, with my own code (no v5b import, my own bootstrap seed). All 12 match result.json and the table to 0.01 %. In every case the sign tracks the first-named arm. ID vs PI is negative in all four cells, and median(ID) > median(PI) in all four (for example slow_q1600: 202.9 vs 174.8 s, rel −17.91 %). So ID is worse, as the text at paper.qmd:155 says ("ID was never better"). IP vs ID block_q1600 is +21.99 %, with median(IP) 210.8 < median(ID) 257.9, so IP is better. My own Bonferroni-level bootstrap gives the same bold pattern (11.8, 22.0, 18.0). (4) The caption text is at paper.qmd:165 (git blame: commit f53b9c33) and in the PDF (pdftotext -layout line 117). It contradicts paper.qmd:145 ("positive values favour arm t") and p1b_result.md:3 ("positive = t better"). Every cited location is correct: qmd 145, 155, 165 and 174, PDF line 117, stats.py lines 52-63, and p1b_result.md lines 3 and 69.

Severity: major, not critical. The data, the body text and the S1a/S1b verdicts are correct. Only the caption is false as written, but a reader of the table alone would reverse every row.

Nuance (info): "favours" refers to the median of the paired differences, not to the difference of the two medians. In slow_q1600 "IP vs PI" rel is +4.47 %, yet median(IP) = 175.2 s is slightly above median(PI) = 174.8 s. A caption that says "positive = first-named arm has lower delay" would not hold exactly for that cell. A safer fix is "Rel = median(r − t)/median(r) in %, t = first-named arm; positive favours the first-named arm".

Failure points: none for the core fact. It would only be wrong if the table were built from rows with r and t the other way round, and the 12 values matching exactly to 0.01 % rules that out.

Checks: sed -n 140,180p papers/paper_1/paper.qmd (caption at 165, convention at 145, text at 155, rows 174-176); pdftotext -layout papers/paper_1/paper.pdf | grep caption (line 117); git show 93ba655:v5b/p1/stats.py lines 1-90; git diff 93ba655 -- v5b/p1/stats.py v5b/p1b/analysis.py (empty); git show 93ba655:v5b/p1b/analysis.py (row construction lines 353-355, key builders 67-118, cell_runs 236-256); git show 93ba655:v5b/p1b/episode.py run_key/make_spec (run file naming); cmp docs/research/results/p1b_result.json ~/work/phd/v5b1_runs/p1b/v108/result.json (identical); /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/S1-F1-reproduce/sign_check.py: independent numpy recompute of Table II rows 1-3 from 1,200 raw run files, with medians per arm and own bootstrap; output in /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/S1-F1-reproduce/sign_check.out; sed -n '3p;69p' docs/research/results/p1b_result.md; git blame -L 165,165 papers/paper_1/paper.qmd

#### Verifier R1 defend: CONFIRMED / major

Meaning: Table II gives, for each pair of controllers, the relative gain rel = median(r - t)/median(r). A positive value means arm t has the lower paired delay, so t is better. Each row is labelled "X vs Y". The question is whether X is t (the caption is then wrong) or Y is t (the caption is then right).

Best defence tried, and it fails on every point.
(1) Row-label convention. The paper (qmd:145) and the protocol (p1_incident_information.md:94-100) both write the rule as R(t, r). S1a is R(ID, r) and S1b is R(IP, ID). The row labels "ID vs PI (S1a)" and "IP vs ID (S1b)" follow that order, so the first-named arm is t.
(2) Code that ran. In v5b/p1b/analysis.py@93ba655:353-355 the calls are s1_stats = _two(D[r], D["ID"]) with r = PI, s1b = _two(D["ID"], D["IP"]) and ip_vs_l0 = _two(D[r], D["IP"]). These call v5b/p1/stats.py@93ba655 paired(r, t), which computes d = r - t and rel = median(d)/median(r). In all three rows t is the first-named arm.
(3) Raw data. My own numpy script reads the delay_s fields of the 100 evaluation seeds (7400600-699) in v108/runs, using the arms from result.json tune.arms. It reproduces all 12 numbers with t = first-named arm. The direction is clear in the data: for slow_q1600 ID vs PI, the median delay of ID is 202.9 and of PI is 174.8, and rel = -17.9 %, so PI is better and the negative value counts against the first-named arm. For block_q1600 IP vs ID, the median delay of IP is 210.8 and of ID is 257.9, and rel = +22.0 %, so IP is better and the positive value favours the first-named arm.
(4) Disclosure or later fix. The body text gives the correct reading: qmd:145 says "positive values favour arm t", qmd:155 says "ID was never better (rel between -17.9 % and -0.7 %)", and p1b_result.md:3 says "positive = t better". The caption contradicts all three. `git log -S` shows the caption came in with f53b9c3 (V122) and was never corrected. The working tree matches HEAD for paper.qmd, and the rendered PDF (Table II, pdftotext line 117) has the same wording. No context removes the error.

Severity: the numbers and the S1a/S1b verdicts are not affected, so this is not critical. It is still a false statement in the caption of the main results table, and a reader of the table alone would reverse every row. Under the given definitions that is major. It sits at the major/minor border, because the body text gives the right reading and the fix is one word: "positive favours the first-named arm".

Further finding (minor/info): rel is a median of paired differences, not a difference of medians. A positive value can therefore appear even when t has the higher median delay. In slow_q1600 IP vs PI, rel = +4.5 %, yet the median delay of IP (175.2) is above that of PI (174.8). Fig. 2 plots medians, so a reader comparing Fig. 2 with Table II sees PI slightly lower while the table favours IP. The corrected caption should say "positive: the first-named arm has the lower median paired delay". Also, block_q2000 IP vs ID = 0.0 by construction: ID and IP-block are the same plan (p20_20_14_e4). The results note says this ("same plan"), but the paper table does not.

Checks: Read paper.qmd:139-185 (rel definition, Results text, Table II source) and pdftotext of paper.pdf around Table II; git log --oneline -S 'positive favours the second arm' (caption origin f53b9c3); git diff HEAD --stat on paper.qmd (no working-tree change); git show 93ba655:v5b/p1/stats.py (paired definition) and git show 93ba655:v5b/p1b/analysis.py | grep paired/_two (argument order for the S1a, S1b and IP-vs-L0 rows); grep of p1b_result.md and protocol p1_incident_information.md for the R(t, r) convention and row labels; Independent recomputation from raw runs with my own numpy code, no v5b imports: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/S1-F1-defend/sign_check.py; output /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/S1-F1-defend/sign_check.out (run with PYTHONDONTWRITEBYTECODE=1 venv python -I)

### B22. [major] S23-F1: Stale P1 value 13.3 % in S2 upper-bound range (should be 19.3-47.9 %)

Raised as major; verification: reproduce: CONFIRMED/major, defend: CONFIRMED/major.

#### CTRL-F5 (R1 CTRL, major, discrepancy): Results text gives S2 upper bounds 'from 13.3 % to 47.9 %'; P1b's are 19.3-47.9 % (13.3 is P1's number)

- **Description.** Paper line 193 says the upper bounds range from 13.3 % to 47.9 %. result.json and Table II give x = 47.9 / 19.3 / 25.4 / 22.4. The value 13.3 matches P1's slow_q2000 upper bound in docs/research/results/p1_result.md:48, the earlier round without amber.
- **Evidence.**
  - papers/paper_1/paper.qmd:193 vs :181 (Table II S2 row)
  - result.json eval.S2.*.statements.x; my recomputation /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/CTRL/out/oracles.json
  - docs/research/results/p1_result.md:48 '[-9.1, 13.3]'
- **Failure scenario.** The text contradicts its own table and mixes in numbers from another study.
- **How to test.** Replace with 19.3 % and check every number in the text against p1b_result.json.
- **Related claims.** C49

#### S23-F1 (R1 S23, major, discrepancy): Stale P1 number in the Results text: 'upper bounds ranged from 13.3 %'

- **Description.** Paper line 193 gives the S2 upper bounds as 13.3-47.9 %. P1b's upper bounds are 47.9, 19.3, 25.4 and 22.4 (Table II, result.json), so the range is 19.3-47.9. The 13.3 is the slow_q2000 upper bound of P1, the earlier round without amber.
- **Evidence.**
  - docs/research/results/p1_result.json /eval/S2/slow_q2000 adds_at_most_pct 13.31
  - ~/work/phd/v5b1_runs/p1b/v108/result.json eval.S2.slow_q2000.statements.x = 0.1930
  - paper.qmd:177 vs :193; paper.pdf text lines 262-263; git blame f53b9c3
- **Failure scenario.** A reader or reviewer sees the text contradict Table II; the number also mixes two studies.
- **How to test.** grep 13.3 in docs/research/results/*.json; compare with Table II row 'S2 bracket'.
- **Related claims.** C77

#### REPRO-F1 (R1 REPRO, major, discrepancy): Line 193 upper-bound range uses a stale P1 number (13.3 %)

- **Description.** Paper line 193 says 'the upper bounds ranged from 13.3 % to 47.9 %'. In P1b the S2 upper bounds are 47.9, 19.3, 25.4 and 22.4 (Table II shows 19.3), so the range is 19.3-47.9 %. The 13.3 % comes from the earlier P1 round without amber: slow_q2000 bracket [-9.1, 13.3].
- **Evidence.**
  - paper.qmd:177 (Table II S2 bracket slow 2000 [-2.4, 19.3]) vs paper.qmd:193 ('13.3 % to 47.9 %')
  - p1b_result.json eval.S2.slow_q2000.statements.x = 0.19300 (both views)
  - docs/research/results/p1_result.md:48 and p1_summary.md:39: P1 slow_q2000 'bracket [-9.1, 13.3]'
- **Failure scenario.** A reader or reviewer checks the text against Table II and finds a number from an older, superseded study inside the P1b results paragraph.
- **How to test.** grep 13.3 in p1b_result.json/md (absent) and in p1_result.md (present); recompute min over cells of eval.S2[*].statements.x = 19.3.
- **Related claims.** C68

#### TEXT-F3 (R1 TEXT, major, discrepancy): Line 193 gives the S2 upper-bound range as 13.3-47.9 %; the P1b data give 19.3-47.9 %

- **Description.** In P1b, the S2 upper bounds x are 47.9, 19.3, 25.4 and 22.4 %. The value 13.3 % is P1's slow_q2000 upper bound. The text contradicts Table II.
- **Evidence.**
  - paper.qmd:193 vs :177
  - p1b_result.json eval.S2.slow_q2000.statements.x = 0.1930
  - docs/research/results/p1_summary.md:39 ('adds at most 13.3 %')
  - /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/TEXT/check_paper_numbers.out
- **Failure scenario.** A reviewer finds the text and the table inconsistent, and the number comes from an unreported study.
- **How to test.** Rerun check_paper_numbers.py, then replace with '19.3 % to 47.9 %'.
- **Related claims.** C13

#### Verifier R1 reproduce: CONFIRMED / major

I reproduced the core fact from the code that ran and from the raw data. The paper text gives the S2 upper bounds as 13.3-47.9 % (paper.qmd:193, rendered PDF too). P1b's upper bounds are 47.9, 19.3, 25.4 and 22.4 %, so the range is 19.3-47.9 %. No S2 value in P1b rounds to 13.3 %. The number 13.3 % is exactly P1's slow_q2000 upper bound (x = 0.13309). P1 is the earlier round without amber (code 85f7d34).

How I checked:
1. Read the S2 statements in both copies of the P1b result file. They are byte-identical (sha256 prefix 1caf4c6f39264e40) and were made by code 93ba655 with code_dirty False.
2. Recomputed x for every cell with my own numpy code, without importing v5b. The inputs were the raw runs: 100 eval seeds (7400600-699) and 120 switch actions per seed. Every run file records code_commit 93ba655. The point estimate rel matches the JSON exactly. The upper bounds differ by at most 0.0012, which is bootstrap-RNG noise.
3. Searched the whole P1b JSON for any number that rounds to 13.3 %. There were 17 hits, all in per_q, S3 and runner_rows, and none in S2. 13.3 also does not appear in p1b_result.md or p1b_summary.md. It does appear in p1_result.md:48 and p1_summary.md:39.
4. The bad sentence came in with commit f53b9c3. That same commit already had Table II with 19.3, so the text and the table disagreed from the first draft.

The headline survives: Table II and the JSON are correct, and only the Results sentence is wrong. That makes this major, not critical. The rest of the sentence holds: the lower bounds 0.4 % and 3.5 % match y in the JSON, and the placebo 13.6-37.7 % matches eval.TP rel 0.1358 and 0.3765. Note that I did not recompute y from the raw runs myself.

One caveat: my own bootstrap gives the slow_q2000 upper bound as 19.2 %, not 19.3 %. The last digit depends on the bootstrap seed, but 13.3 % is far outside that noise. A small correction to the tracers: the PDF lines are 170-172 under pdftotext -layout. The tracer's 262-263 probably came from a different extraction mode. Either way, the PDF has the same wrong text.

Checks: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/S23-F1-reproduce/s2_bounds.py (output s2_bounds.out): S2 x and y per cell from the P1b and P1 result files, raw and docs copies, with sha256, commit and dirty flag; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/S23-F1-reproduce/s2_views.py (output s2_views.out): x equals OR_in.median.rel_ci[1] in both views; placebo TP rel values; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/S23-F1-reproduce/find_133.py (outputs find_133.out, find_133_paths.out): walks the P1b JSON for any value rounding to 13.3 %; 17 hits, 0 in S2; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/S23-F1-reproduce/recompute_x.py (outputs recompute_x.out, recompute_x.json): independent numpy recomputation of x from the raw runs in ~/work/phd/v5b1_runs/p1b/v108/runs; B=20,000, level 0.9875, joint seed resampling. A first version omitted the c/fa/vsl_b/rep filter and mixed in c60/c180 variant runs; debug_slow1600.py found this, and the filter was fixed and the script re-run with a duplicate assert; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/S23-F1-reproduce/json_s2_detail.py: JSON OR_in median and mean statistics for slow_q1600 and slow_q2000; pdftotext -layout paper.pdf > /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/S23-F1-reproduce/paper_pdf.txt; rg for 13.3, 19.3 and 47.9; git -C repo blame -L 193,193 papers/paper_1/paper.qmd; git show f53b9c3 (introducing commit and its Table II row); git diff HEAD on paper.qmd (clean); git show 93ba655:v5b/p1b/analysis.py and 93ba655:v5b/p1/stats.py (definitions of OR_in, x and LEVEL_S2); rg 13.3 in docs/research/results/p1b_*.md, p1_*.md and docs/decisions.md

#### Verifier R1 defend: CONFIRMED / major

Meaning: in the S2 paragraph (paper.qmd:193, PDF lines 170-172), the paper sums up Table II's S2 row by saying the upper bounds on per-incident hindsight "ranged from 13.3 % to 47.9 %". The upper bound x is the upper end of the 1-0.05/4 CI for the median relative gain of OR_in over IP (v5b/p1b/analysis.py@93ba655:478, `x = OR_in.median.rel_ci[1]`). In P1b these x values are 47.9, 19.3, 25.4 and 22.4 %, so the true range is 19.3-47.9 %.

My best defence failed. (1) No P1b quantity rounds to 13.3: the bracket ends, the y_hat, the OR_in median and mean estimates with their CIs, and the valid_only view all differ from 13.3, and the valid_only values equal the all_seeds values in every cell. The only 13.3 values in the P1b result.json belong to S3, per_q and runner_rows fields, none of which is an upper bound. (2) The number matches P1, the earlier round without amber: its slow_q2000 x = 13.3087, with bracket [-9.1, 13.3]. The same sentence uses P1b lower bounds (0.4 and 3.5; P1 has 3.4 and -1.8) and the P1b maximum (47.9; P1's is 39.7). So the sentence mixes the minimum from one study with the maximum from another. It is not a consistent report of P1. (3) The paper never presents P1's S2 results. The only reference to the no-amber round is the emergency-stop share at line 197. The protocol, the baseline traceability record BL-2 and later commits contain no disclosure or erratum. Line 193 has been unchanged since f53b9c3. (4) The rendered PDF has the same error.

Severity: under the given rubric this stays major, because a paper statement is false as written and carries a number from another study. The headline survives: Table II at line 177 is correct and matches the raw result.json, and the conclusion of the paragraph (the bracket did not converge, and the placebo inflates hindsight gains) still holds with 19.3. A case for minor (a one-number text-versus-table slip) is defensible, but the mixing of two studies is why I keep major. Fix: change the text to "19.3 % to 47.9 %".

Checks: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/S23-F1-defend/find_133.py: walks every numeric leaf of the P1b raw and repo result.json, the C1 JSONs and the P1 JSON for values in [13.25, 13.35) or [0.1325, 0.1335). P1b has 17 hits, none in S2. P1 has hits at S2.slow_q2000.x and statements.adds_at_most_pct. Output in find_133.out in the same folder.; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/S23-F1-defend/s2_dump.py: prints the S2 statements, x, y, y_hat and the OR_in median/mean estimates with CIs per cell and per view for P1b and P1. Output in s2_dump.out. No P1b S2 alternative definition gives 13.3.; md5sum of the raw v108 result.json against docs/research/results/p1b_result.json: identical; code_commit = 93ba655; git show 93ba655:v5b/p1b/analysis.py: confirmed the definition of x and y (lines 456-484); pdftotext of papers/paper_1/paper.pdf into the scratch folder (paper.txt): the rendered text carries the same error; git blame and git log for paper.qmd: line 193 unchanged since f53b9c3; no later fix; grep of p1b_summary.md, p1b_result.md, p1b_c1_summary.md, the BASELINE_2 traceability record and decisions.md V122 for 13.3 or a P1 disclosure: none found; Not done: re-deriving x from the 344,852 raw run files with my own OR_in builder. I relied on the run's own output JSON at 93ba655, which is primary output of the code that ran. Even if that JSON were wrong, the text would still contradict Table II.

### B23. [major] S23-F2: Pre-registered outputs missing: clean-day cost, prevalence, p*, f*, c*, false-alarm cost, combined row

Raised as major; verification: reproduce: CONFIRMED/major, defend: CONFIRMED/major.

#### S23-F2 (R1 S23, major, disclosure): Pre-registered 'always reported' outputs are missing from the paper (clean-day cost, false-alarm cost, p*, f*, c*, combined row)

- **Description.** Paper line 104 says the cost of always-on control on incident-free days is reported separately, and line 85 promises how often the type may be wrong or a false alarm occur before the gain disappears. Neither appears in the paper. The protocol requires them: clean-day delay of every arm printed next to S1 (:102, A4(a)); false-alarm cost 'always reported' (:81); S3 = d*, c*, p*, f*, combined row (:112); paper outputs = one break-even table (d*, p*, f*) (:116). The data exist, and they matter:
- clean days at q1600: medians N 45.4, PI 81.1, FB 154.3 s/veh;
- clean days at q2000: N 151.6, PI 301.1, FB 340.9 s/veh;
- PI vs N paired median: -12.0 s/veh at q1600, -151.6 s/veh at q2000;
- false-alarm cost: 39.5 [22.0, 69.6] and 120.4 [89.7, 147.5] s/veh;
- p* = 0.13 / 0.53 / 0.21 / never ahead;
- combined row in the C1 cell (block_q1600): vs FB +0.5 % [-6.1, 7.8], vs PI +5.9 % [-0.9, 16.8].
- **Evidence.**
  - result.json eval.per_q.{1600,2000}.clean_day, false_alarm_cost, prevalence.*.f_star; eval.S3.*.{c_star,p_star,combined_row}
  - docs/research/results/p1b_summary.md:45-58
  - protocol p1_incident_information.md:81,102,112,116,149
  - own recompute s23_extra.log (clean days, c*, p* match)
- **Failure scenario.** Selective reporting of pre-registered rows. The always-on arms look strong 'given an incident' while their large incident-free-day cost goes unreported, and the robustness section omits the type-error and combined-imperfection results that weaken the C1 cell.
- **How to test.** Diff the protocol §6/A10 output list against the paper's tables and text; print result.json eval.per_q and eval.S3 combined_row.
- **Related claims.** C59

#### S1-F2 (R1 S1, major, disclosure): Pre-registered clean-day cost not reported next to S1 (and promised but absent)

- **Description.** Protocol §6 requires that 'the clean-day delay of every arm is printed next to S1, because the L0 arms are tuned on incident runs only', and the paper says at line 104 that the cost is reported separately. The draft never reports it. The cost is large. On clean days ID and IP run N, while always-on PI gives 81.1 vs 45.4 s/veh (q1600) and 301.1 vs 151.6 s/veh (q2000). In the report-only prevalence line in result.json (which I did not recompute), ID beats the π-retuned PI at q2000, for example 11.0 % [9.1, 13.0] at π = 0.1.
- **Evidence.**
  - docs/research/protocols/p1_incident_information.md:102
  - paper.qmd:104 and the absence of any later clean-day number (grep)
  - clean_day.py output (raw runs <ctrl>_none_q<q>_s74006xx), equal to result.json eval.per_q.<q>.clean_day
  - result.json eval.per_q.<q>.prevalence.<pi>.ID_vs (assumption, not recomputed)
- **Failure scenario.** Readers take S1a FAIL to mean 'presence information has no value'. Unconditionally it can have large value, because the always-on arms that win on incident days lose heavily on clean days.
- **How to test.** Add the clean-day row (and the prevalence line) next to Table II. Recompute the prevalence mixture from raw runs.
- **Related claims.** C64

#### TEXT-F8 (R1 TEXT, major, missing-evidence): The clean-day cost and the prevalence line are promised (line 104) and pre-registered, but not reported, and they change the reading of S1a

- **Description.** The protocol requires the clean-day delay of every arm next to S1, and a report-only prevalence line. Neither is in the paper.
- Paired clean-day costs vs N (my own recomputation): q2000 PI +151.6 s/veh [135.3, 163.3], FB +194.9, AD +200.4, FX +174.9; q1600 PI +12.0 [-0.5, 19.8], FB +85.3.
- Prevalence line (report-only, 95 %): at q2000, ID beats every pi-retuned L0 arm at pi = 0.1 and 0.25, all CIs above 0 (vs PI 11.0 % and 13.6 %), but not by 10 % against FX (4.9 %, 9.1 %).
So 'presence does not pay' holds only conditional on an incident.
Note that p1b_result.md:76 says the paper 'cannot say anything about prevalence'. That conflicts with the pre-registered report-only output and should be resolved.
- **Evidence.**
  - paper.qmd:104, :155
  - p1_incident_information.md:102-103, :149 (A4(a))
  - p1b_result.json eval.per_q.*.clean_day, prevalence.*.ID_vs
  - /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/TEXT/clean_day_paired.out
  - /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/TEXT/check_paper_numbers.out
- **Failure scenario.** The S1a headline is read as 'presence information is useless'. Once incident-free days count, presence-aware switching beats every re-tuned always-on arm at q2000 (descriptive).
- **How to test.** Rerun clean_day_paired.py. Report the clean-day row and the prevalence line, both marked report-only.
- **Related claims.** C31, C08

#### CTRL-F11 (R1 CTRL, minor, missing-evidence): The paper promises p*, f* and clean-day costs but reports none

- **Description.** Line 85 promises 'how often the type may be wrong or a false alarm occur', and line 104 says clean-day costs are 'report[ed] separately'. Only d* appears in the paper. The data exist: p* = 0.13/0.53/0.21/0.0 (result.json eval.S3). Clean-day medians: N 45.4 vs PI 81.1 s/veh at q1600, and 151.6 vs 301.1 at q2000. These are relevant context for C1, since IP runs N on clean days.
- **Evidence.**
  - papers/paper_1/paper.qmd:85,104,179; result.json eval.per_q.*.clean_day, eval.S3.*.p_star
- **Failure scenario.** Promised results are missing, and the clean-day advantage of the incident-aware arms goes unreported.
- **How to test.** Add the p*, f* and clean-day rows.
- **Related claims.** C30

#### TEXT-F7 (R1 TEXT, major, missing-evidence): Pre-registered S3 outputs promised in line 85 are missing; robustness is reported selectively

- **Description.** S3 in the protocol covers d*, c*, p*, f*(pi) and the combined row, each with a 95 % CI. The paper reports d* only, without CIs. The omitted values are unfavourable to IP:
- block_q1600 (the C1 cell): p* = 0.21 [0.12, 0.33] (binding FB); the combined row (d = 60, c = 60, p = 0.2) is -16.5 % [-18.5, -11.4] vs IP;
- slow_q1600: p* = 0.13, combined row -20.5 %;
- f*(pi) is 0.10-0.44;
- the false-alarm cost is +39.5 s/veh (q1600) and +120.4 s/veh (q2000).
Line 187's 'the lead held' covers only the delay and runner rows, which favour IP.
- **Evidence.**
  - paper.qmd:85, :145, :179, :187
  - p1_incident_information.md:63-81, :112
  - p1b_result.md:24-27
  - p1b_result.json eval.S3.*.{p_star,c_star,combined_row}; eval.per_q.*.{false_alarm_cost, prevalence.*.f_star}
  - /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/TEXT/check_paper_numbers.out
- **Failure scenario.** Readers conclude that the type plan is robust in the C1 cell. In fact a 21 % misclassification rate, or the combined imperfection row, removes most of the lead.
- **How to test.** Add an S3 table with d*, c*, p*, f* and the combined row with CIs (all are already in p1b_result.json).
- **Related claims.** C18, C14

#### Verifier R1 reproduce: CONFIRMED / major

I reproduced the core fact. The protocol pre-registers these outputs, and the result data contain them:
- clean-day delay per arm;
- cost of one false alarm;
- c*, p*, f*(pi);
- the combined row;
- the prevalence line.

None of them is in paper.qmd or in the rendered paper.pdf. The paper only promises them: line 85 ("how often the type may be wrong or a false alarm occur") and line 104 ("which we report separately"). Decision V128 rewrote the Background on purpose to say that misclassification and false alarms "are reported". Table II (paper.qmd:179) gives d* only, as point values without the pre-registered CIs.

**Protocol versions.** The protocol pages did not change between run commit 93ba655 and HEAD. Their sha256 values match page_sha256 and base_page_sha256 in result.json. Protocol lines 81, 102, 112, 116 and 149 say exactly what the finding cites.

**Own recompute.** I recomputed every cited number from the raw runs in ~/work/phd/v5b1_runs/p1b/v108/runs (100 evaluation seeds, 0 invalid) with my own numpy code. Every value matches result.json exactly:
- clean-day medians: N 45.4 / PI 81.1 / FB 154.3 at q1600; N 151.6 / PI 301.1 / FB 340.9 at q2000;
- cost of one false alarm: 39.5 [22.0, 69.6] and 120.4 [89.7, 147.4] s/veh;
- p*: 0.13 / 0.53 / 0.21 [0.12, 0.33] (binding arm FB) / never ahead;
- f*(pi) from 0.10 to 0.44;
- combined row in block_q1600: vs FB +0.5 % [-6.1, 7.8], vs PI +5.9 % [-0.9, 16.8], vs IP -16.5 % [-18.5, -11.4];
- slow_q1600: combined row vs IP -20.5 %;
- prevalence line, q2000: ID vs PI 11.0 % [9.1, 13.0] at pi = 0.1 and 13.6 % at pi = 0.25.

The repo copy of p1b_result.json is byte-identical to the raw run's result.json. The two member findings quote different "combined row" numbers (+0.5 % vs FB, -16.5 % vs IP). They do not conflict: they are the vs_L0 and vs_IP keys of the same row.

The finding holds, and major severity fits. Caveats that narrow the members' interpretations:
1. **Clean-day PI cost at q1600 is small, and its CI includes 0.** The paired median(PI - N) is +12.0 [-0.5, 19.8], the mean is -4.0, and PI is worse on only 59 % of seeds. The gap between the two medians (81.1 vs 45.4) overstates it. The large clean-day costs are at q2000 (PI +151.6 [135.3, 164.8]) and for FB, AD and FX at both demands.
2. **TEXT-F8's CI is slightly off.** It gives the q2000 PI cost's CI upper bound as 163.3; I get 164.8 to 164.9 with three bootstrap seeds. S23-F2's 147.5 is a rounding of 147.446.
3. **The prevalence line does not reach the 10 % bar.** It is report-only and uses 95 % CIs without correction. At q2000, ID's lower CI bound is above 0 against every re-tuned L0 arm at pi = 0.1 and 0.25, but rel stays below 10 %:
   - against N and FB, 7.8 % at pi = 0.1;
   - against FX, 4.9 % at pi = 0.1 and 9.1 % at pi = 0.25.

   At q1600, ID vs PI has a CI that includes 0 at every pi (-2.7 % at pi = 0.5). So the claim that "presence-aware switching beats every re-tuned arm" holds only in the CI-above-0 sense, at q2000, and as a descriptive result.
4. **Line 187 is not itself selective.** TEXT-F7 says "the lead held" covers only the delay and runner rows. Those are exactly the descriptive rows that the C1 protocol pre-registers; C1 never ran p, f or a combined row. The omission is of the P1b S3 rows: the block_q1600 combined row comes from P1b evaluation seeds 7,400,600–699, not from the C1 seeds.
5. **The paper is a draft.** Discussion is empty and the Conclusion reads "To be written", so the authors may still add these outputs. As written, lines 85 and 104 are unfulfilled.

**Other missing pre-registered outputs (my own checks):**
- the A10 Table 1 "operating map (every arm, every cell, clean day)";
- S1a against every L0 arm: Table II shows only ID vs PI;
- c* "in the text", required by A10.

The arm names come from result.json tune.arms. I did not re-check the tuning itself.

Checks: Read protocol lines 55-125 and 140-160 and the P1b and C1 protocols; ran git diff 93ba655 HEAD on the protocol pages (no change) and compared their sha256 with result.json page hashes; Read paper.qmd lines 85, 104, 145, 150-203; grep for clean/false alarm/misclass/prevalence/combined/operating; pdftotext of paper.pdf to /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/S23-F2-reproduce/paper_pdf.txt and grep; grep of figures/*.py; Read v5b/p1b/analysis.py@93ba655 (imperfection_cell, clean_and_prevalence, canon_sw, fa_spec), v5b/p1/stats.py@93ba655 (paired, mixture, prevalence_mix, breakeven) and v5b/p1/meters.py@93ba655 (switch_schedule) to define the quantities; did not import any of them; Independent recompute with own numpy code, no v5b imports, B = 20,000: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/S23-F2-reproduce/recompute_s3_clean.py -> recompute_s3_clean.out (clean-day medians and paired costs, false-alarm cost, p* with CIs, combined row vs L0 and vs IP, prevalence ID_vs, f*(pi)); Comparison with result.json: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/S23-F2-reproduce/compare.py -> compare.out (every value matches); Bootstrap-seed sensitivity and distribution of the clean-day PI-N difference: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/S23-F2-reproduce/clean_pi_n_seedcheck.py -> clean_pi_n_seedcheck.out; Grep of docs/decisions.md for A10/output-scope decisions (V128 found; no decision to drop these outputs from the paper); read p1b_summary.md:45-58 and p1b_result.md:22-28, 66-76; cmp of the repo p1b_result.json against the raw v108 result.json (identical)

#### Verifier R1 defend: CONFIRMED / major

Meaning: the protocol required some outputs to be reported, and the paper says it reports them. These are the delay of every arm on incident-free ("clean") days, the cost of one false alarm, how much misclassification (p*) and false-alarm rate (f*) the type plan can tolerate, the clearance break-even delay (c*) and a combined-imperfection row. The paper shows none of them. Its only robustness number is d*, the break-even detection delay, and Table II gives d* without CIs.

My best defence, point by point:
(1) The paper is an unfinished draft. The abstract, Discussion and Conclusion are empty. V124 says "author review of the full draft at the end". The paper plan comment (paper.qmd:54) promises "Table II S1/S2/S3 summary per cell with CIs". So the authors may still intend to add these outputs. Why the defence fails: the Results section and Table II are already written. paper.qmd:145 describes S3 as "break-even detection delays" only. Lines 85 and 104 promise outputs that the draft does not contain. The paper's declared source of truth, p1b_result.md, also leaves out the clean-day row and the prevalence line, and at :76 it says the paper "cannot say anything about prevalence". So the gap comes from the source note, not only from unfinished text.
(2) A10(a) (protocol :116, :155; V99) limits what goes in the main text. The combined row and the prevalence-line rel rows are not on that cut list, and c* goes "in the text" only. This narrows the finding: the combined-row part is overstated as a main-text requirement. But A10 still requires Table 1 to be the operating map (every arm, every cell, clean day) and "one break-even table (d*, p*, f*)". A4(a) (:149) and §6 (:102) require the clean-day delay "printed next to S1". The paper has none of these, and it points to no supplement or repository.
(3) The C1 text at :187 ("the lead held" under detection delay and runners) reports exactly the descriptive rows pre-registered for C1 (p1b_confirm_c1.md:27-31). p* and the combined row were never C1 rows, so TEXT-F7's charge of selective reporting within C1 is moot. However, in the same cell, P1b's p* = 0.21 [0.12, 0.33] (binding arm FB). The combined row there is +0.5 % [-5.8, 8.1] vs FB and +5.9 % [-0.9, 18.5] vs PI. Both qualify the robustness reading, and they are pre-registered S3 outputs.
(4) The headlines survive. S1a, S1b and C1 are defined "given that an incident occurs" (A4(a)), and the paper says so at :104, so clean-day costs do not change any verdict. That is why the severity is major, not critical.

What survives: the paper statements at :85 and :104 are unsupported as written. :145 understates the scope of the pre-registered S3. And the outputs that A10 and A4(a) require are absent, even though they are computed in result.json and in the auto-generated p1b_summary.md.

The omitted data matter. I recomputed them from the raw runs with my own code. At q2000, always-on PI costs +151.6 s/veh [135.5, 164.9] on clean days. Under the report-only prevalence line at q2000, ID beats every π-retuned L0 arm at π = 0.1 and 0.25 with CI above 0 (vs PI +11.0 %, vs FX +4.9 %). So "presence does not pay" holds only conditional on an incident.

Two corrections to the tracers: PI's clean-day cost at q1600 is not resolved (+12.0 [-0.5, 19.8]), so "large" applies to q2000 PI and to FB, FX and AD only. And CTRL-F11's p* "0.0" for block_q2000 is actually the "IP never ahead" flag.

Further findings in this domain:
(a) paper.qmd:118 calls N "the best constant rate on incident-free days". At q2000, N is f10_8, an integral feedback law (tune.arms.2000.N; meter_log shows the rate moving 1500→1580→1600). So ID and IP run a feedback law before onset at q2000. Severity minor to major; the headline is unaffected.
(b) Table II's row "ID vs PI (S1a)" is not the binding S1a arm in Crawl 1600: ID vs FB is -2.6 %, against -0.7 % vs PI (eval.S1.per_cell_stats.block_q1600). This is a minor consequence of the missing operating map.

Checks: Read the paper.qmd text in full; grepped paper.qmd and the pdftotext output of paper.pdf for clean / incident-free / false alarm / misclass / prevalence / combined / clearance / p* / f*; Read the protocol p1_incident_information.md (§4, §6, A4, A10, addendum), p1b_addendum.md and p1b_confirm_c1.md in full; Grepped docs/decisions.md for A10 / prevalence / clean / false alarm / misclass; read V99-V129; git log --all -- papers/paper_1/paper.qmd paper/paper.qmd; git status papers/; git diff --stat 93ba655 HEAD -- v5b/p1 v5b/p1b; sha256 of the committed p1b_result.json vs raw v108/result.json (identical); code_commit and code_dirty checked; git show 93ba655:v5b/p1b/analysis.py and v5b/p1/analysis.py (clean_and_prevalence, imperfection_cell); /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/S23-F2-defend/recompute_s3_clean.py --boot (own numpy code from raw runs; B = 20,000): clean-day medians and paired cost vs N, FA cost, p* per cell plus the bootstrap CI for block_q1600, combined row, prevalence ID vs retuned L0 at pi 0.1 and 0.25; output in recompute_s3_clean.out in the same directory; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/S23-F2-defend/recompute_fstar.py (own f*(pi) point recompute vs JSON; output in recompute_fstar.out); Printed result.json tune.arms and eval.S1.per_cell_stats ID_vs per arm (small python one-liners); checked the N controller type at q2000 from a raw run's meter_log

### B24. [major] TEXT-F12: Plant details needed for reproduction missing from the paper

Raised as major; verification: reproduce: CONFIRMED/major, defend: CONFIRMED/major.

#### TEXT-F12 (R1 TEXT, major, reproducibility): Plant under-described: origin, vehicle mix, crawl severity and the 50/50 type mix are not stated

- **Description.** Facts in the code that the paper does not state:
- The plant is the Vinitsky et al. 2018 bottleneck [VERIFY citation]; it is not cited.
- 10 % of vehicles are an 'av' vType with speedFactor 1 and speedDev 0 (av_share = 0.1, the default at the run commit).
- Car following is IDM with a = 1, b = 1.5, T = 1 s, s0 = 2 m; desired speed is N(1, 0.2); the step is 0.5 s; the departure lane is random; the drain is capped at 7200 s.
- The lane crawl is on the 2-lane edge 4, not on the 1-lane edge 5. With lane changing off, vehicles on the lanes feeding 4_1 must cross it at 1 m/s. The code calls this 'more severe than a closure'.
- ID, the L0 arms and the false-alarm cost assume a 50/50 slow/block mix. Line 93 instead says 'an incident of random type'.
- **Evidence.**
  - git show 93ba655:v5b/d1/plant.py lines 2-8, 25-29
  - 93ba655:v5b/p1b/episode.py:125 (av_share=0.1), :312 (default used)
  - 93ba655:v5b/d2/incidents.py:4-13, 28-29
  - p1_incident_information.md:36, :43, :73
  - paper.qmd:93, :110, :114
- **Failure scenario.** The plant cannot be reproduced from the paper. The S1b gain (IP vs ID) depends on the unstated type mix, and the confirmed cell rests on an incident model that is harsher than a real lane closure.
- **How to test.** Add the plant parameters and the citation; state the 50/50 pooling. Optionally re-tune ID under other mixes using the stored tuning runs.
- **Related claims.** C85, C12

#### PLANT-F12 (R1 PLANT, minor, reproducibility): Plant details needed for reproduction are missing from the paper

- **Description.** The paper does not state: IDM (a=1, b=1.5, T=1, s0=2, delta=4, length 5); speedFactor normc(1, 0.2, 0.2, 2) and a 10 % 'av' vType with speedFactor 1; Poisson arrivals on [0, 940) s; random depart lane at 10 m/s; step 0.5 s; time-to-teleport 300 s; all-green warm-up; feedback laws starting from q0=1500; drain cap 7200 s; the meter switched off in the drain; edge and lane lengths (100/310/120/240/135 m); incident locations (edge 5, lane 4_1); the 30-s update grid and edge-4 detector. SUMO also redraws speed factors for slow vehicles to match the 10 m/s departure speed ('Choosing new speed factor' warnings).
- **Evidence.**
  - v5b/d1/plant.py@93ba655:22-38
  - v5b/d1/sumo_runner.py@93ba655:102-107
  - v5b/p1b/meters.py@93ba655:32
  - log_sample_emerg sampling: 18 'Choosing new speed factor' warnings in 862 logs
- **Failure scenario.** Others cannot rebuild the plant from the paper.
- **How to test.** Add a plant parameter table.
- **Related claims.** C32, C33, C34, C37

#### G4-F4 (R2 G4, minor, reproducibility): Vehicle population and driver model not described; 10 % 'av' vType and human desired speeds above the limit

- **Description.** Every run has about 10 % vehicles of type 'av'. This type is not automated: it is the same IDM as the humans, with speedFactor 1.0 and speedDev 0. Realised shares are 9.84 % (P1b sample of 3.6 M vehicles) and 10.14 % (C1). Humans have speedFactor normc(1, 0.2, 0.2, 2.0), so desired speeds reach up to 46 m/s on a 23 m/s road. Observed approach speeds of lane leaders at red onset reach 27.5 m/s, and 6.7-17 % of those that then stopped were approaching at 10 m/s or more. Other settings: IDM a 1, b 1.5, tau 1, minGap 2, delta 4, length 5; depart speed 10 m/s on a random lane; lane changing off; step 0.5 s, Euler; emergencyDecel 9; no driver imperfection. The paper (lines 110, 149) mentions none of these and says only 'drivers'. Runners are drawn from both types, so about 10 % of runners are 'av'.
- **Evidence.**
  - plant.py@93ba655:25-38; demand.py@93ba655:38-57; p1b/episode.py@93ba655:125 (av_share 0.1), :133-134, :138
  - runners.py@93ba655:20-30
  - G4/by_type_p1b.out, G4/by_type_c1.out, G4/approach_cross_p1b.out
  - grep of paper.qmd for IDM/AV/speed factor/depart: no matches
- **Failure scenario.** A reviewer cannot rebuild the plant from the paper. If the type were disclosed as 'AV', readers would expect automated or controlled vehicles, which do not exist in this plant.
- **How to test.** Add one sentence with these parameters, or a footnote naming the vType 'av' as 'speed factor 1, no variance'.
- **Related claims.** C61, C62, C09

#### Verifier R2 reproduce: CONFIRMED / major

I reproduced the core fact: the paper text does not give the plant details that the code at the run commit uses, and it does not state that ID and the L0 arms were tuned on an equal (50/50) slow/block mix. The code files are identical at 93ba655 and HEAD. The protocol sha256 matches base_page_sha256 in result.json. The cached net hash (e578788201) matches the SPEC at 93ba655.

Each cited fact, checked against primary evidence:
(1) Origin. plant.py@93ba655:2 and netgen_bn4.py@93ba655:2 say the plant is the Flow / Vinitsky et al. (2018) bottleneck. references.bib (21 entries) has no Vinitsky or Flow entry, and paper.qmd never mentions it. I did not check the bibliographic details of Vinitsky 2018 (no web access).
(2) AV share. p1b/episode.py@93ba655:125 sets av_share=0.1. The batch path (run.py:71 runs `-m v5b.p1b.episode`, then main at :312) uses that default. demand.py:53 draws each vehicle's type independently, so the AV share is 10 % in expectation, not exactly 10 %. The 'av' vType has speedFactor 1 and speedDev 0 (plant.py:29). The paper never mentions AVs or vehicle types.
(3) Car following and run settings. IDM with a 1.0, b 1.5, tau 1.0, minGap 2.0, delta 4, length 5 (plant.py:27). Human speedFactor is normc(1,0.2,0.2,2.0): a normal distribution truncated to [0.2, 2], for human vehicles only (the finding writes N(1,0.2)). Step 0.5 s (:22). Random depart lane, depart speed 10 m/s (:34-35). Drain runs until the absolute simulation time reaches 7200 s (episode.py:125, sumo_runner.py:224-232). None of these is in the paper.
(4) Crawl. incidents.py:28-29: the slowdown is on edge 5 (5 m/s) and the crawl on lane 4_1 (1 m/s). In the cached net, lanes 3_2 and 3_3 feed 4_1. With lane changing off and a random depart lane, about half of the traffic must cross the crawling lane. The phrase 'more severe than a closure' is at incidents.py:13. The code attributes it to review probes; screen_D2_incidents.md:94 gives 1.3-2.4x the closure's delay in 8 probe runs, and I did not check that probe data. Two corrections to the finding: the paper text does say that lane changing is disabled and that the crawl stands in for a blockage (line 110), and Fig. 1 (I rendered fig_plant.pdf) draws the crawl on one lane of the 2-lane section and the slowdown on the 1-lane section. So the location is shown in the figure but not stated in the text.
(5) 50/50 mix. analysis.py@93ba655:122 and :139 build the tuning sample by concatenating the slow and block runs over the same 40 seeds (40+40 runs), so FX, FB, PI, AD and ID are tuned on an equal mix. :605 computes the false-alarm cost as (slow + block)/2. The protocol says the same (p1_incident_information.md:32, 36, 43, 73). paper.qmd:93 says 'an incident of random type'; nowhere does the paper state the pooling. The false-alarm cost is not reported in the paper yet (lines 85 and 104 only promise it), so that part has no effect on the current text.

Failure scenario. My own code recomputed ID and IP from the raw tuning runs; both match result.json at both demands. At 50/50 my S1b values match Table II exactly (16.2 / 11.8 / 22.0 / 0.0). I then re-chose ID under other slow shares w (weighted median). The ID choice and the per-cell IP-vs-ID numbers change a lot: at crawl q1600 the gain is 0.0 % at w=0, 2.8 % at w=0.1-0.25, 22.0 % at w=0.4-0.6 and 42.1 % at w=1. However, the S1b verdict holds at every w I tested: at least one cell has rel ≥ 10 % with the Bonferroni lower bound > 0, and the worst cell is -3.9 %, above the -5 % limit. At w=0.1-0.25 it rests on one cell only (slowdown q2000). So the claim 'the S1b gain depends on the mix' is true for the cell values, not for the verdict. I did not re-tune the L0 arms; the PI arm used as C1's reference is also tuned on the 50/50 mix.

Severity: major, not critical. The headline survives. But a reviewer would require the citation of the plant's origin, the 10 % 'av' vehicles, the plant parameters, and the 50/50 tuning mix.

Checks: git show 93ba655 of v5b/d1/plant.py, v5b/d1/demand.py, v5b/d1/netgen_bn4.py, v5b/d1/sumo_runner.py, v5b/d2/incidents.py, v5b/p1b/episode.py, v5b/p1b/meters.py, v5b/p1b/run.py, v5b/p1/family.py; git diff 93ba655 HEAD on those files (no changes); Saved copy of analysis.py@93ba655: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/TEXT-F12-reproduce/analysis_93ba655.py (read fit_fixed, fit_switch, clean_and_prevalence); grep of paper.qmd and references.bib for plant terms (Vinitsky, IDM, AV, step, depart, 7200, pooled, mix, random type, false alarm); Rendered papers/paper_1/figures/fig_plant.pdf to /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/TEXT-F12-reproduce/fig_plant-1.png and read fig_plant.py; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/TEXT-F12-reproduce/net_check.py (cached net lanes, lengths, edge 3 -> 4 connections) and an ast-based SPEC hash check of netgen_bn4.py@93ba655; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/TEXT-F12-reproduce/mix_sensitivity.py (output mix_sensitivity.out): own recomputation of ID/IP from raw tuning runs, S1b at 50/50 versus Table II, re-selection of ID under slow shares 0-1 with bootstrap B=20000 at level 0.99375; Protocol p1_incident_information.md lines 32/36/43/73 read; sha256 compared with result.json base_page_sha256; screen_D2_incidents.md:91-96 read for the crawl-versus-closure claim; Sample of 3000 SUMO run dirs (6000 logs) grepped for 'Choosing new speed factor' (list in log_sample_dirs.txt in the same scratch dir)

#### Verifier R2 defend: CONFIRMED / major

I tried to defend the paper. Some parts of the finding are overstated, but its core survives: the plant as it ran cannot be identified or rebuilt from the paper text, and the paper does not cite the benchmark whose geometry the code says it copied.

What the defence removes or narrows:
(1) Crawl location. The paper text does not give it, but Fig. 1 (figures/fig_plant.py:2,27-30; I rendered the PDF) shows the slowdown on the 1-lane edge and the lane crawl on one lane of the 2-lane edge. The text also says that lane changing is off and that a lane blockage is represented by a crawling lane (paper.qmd:110). So "the crawl is not on edge 5 / not stated" is mostly disclosed already.
(2) "Harsher than a real lane closure" is overstated. The evidence is 8 probe runs against a simulated near-stop closure with lane changing off in this same plant, not against a real closure. In those probes the crawl gave 1.3-2.4 times the closure's delay (screen_D2_incidents.md:91-95).
(3) The 50/50 type mix is not a deviation. The protocol pre-registered tuning of L0 and ID on the pooled slow + block runs (p1_incident_information.md §2), and the code does exactly this: 40 slow + 40 block runs per arm, median of the pooled list (p1b/analysis.py@93ba655:122,139,151). The 50/50 false-alarm cost is moot for the current text, because the paper reports no false-alarm row (f*).
(4) Small precision point: the desired-speed factor is a truncated normal, normc(1, 0.2, 0.2, 2.0), not a plain N(1, 0.2).
(5) No headline number depends on these omissions. All arms share the plant, and evaluation is per type cell.
(6) The draft is unfinished: the abstract, Discussion/Limitations and Conclusion are empty, and the format has a 6-page budget.

What survives:
(a) The car-following model and its parameters are absent. The paper never names IDM (a=1, b=1.5, T=1 s, s0=2 m, delta=4, length 5 m).
(b) There is an undisclosed vehicle population: 10% of vehicles are an 'av' vType with speedFactor 1 and speedDev 0. The default av_share=0.1 is used in both P1b (93ba655) and C1 (e7dd561), because episode main() passes no override and the runner launches episodes with --spec only. Neither the paper nor the P1 protocols mention this population.
(c) Step 0.5 s, time-to-teleport 300 s, Poisson arrivals, random departure lane at 10 m/s, the 7200-s drain cap, the meter switched to all-green before the drain, edge lengths and the edge-4 detector are all absent from the paper.
(d) The geometry is "copied from the public Flow code" (netgen_bn4.py@93ba655:2-4), but references.bib has no Vinitsky/Flow entry. (My script's three "Flow" hits at paper.qmd:63, 65 and 110 are false positives: they match the ordinary word "flow".) I could not check the Vinitsky et al. 2018 paper itself: no web access. [VERIFY]
(e) The type-mix weights behind ID and the L0 arms are not stated. Line 93 says only "random type". This matters when reading S1b, because the gain of type knowledge over presence depends on that prior.
(f) There is no code or data availability statement.

None of these is a false statement, and the fixes are cheap: a parameter table, the citation, one sentence on pooling, and a code release. Even so, the uncited reuse of the benchmark geometry and the undisclosed 10% vehicle type are items a reviewer would require fixed. I therefore keep the severity at major, at its lower edge.

Checks: git archive 93ba655 and e7dd561 (v5b, docs) into /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/TEXT-F12-defend/code_93ba655 and code_e7dd561; read plant.py, netgen_bn4.py, demand.py, sumo_runner.py, incidents.py, p1b/episode.py, p1b/meters.py, p1/analysis.py, p1b/analysis.py, p1b/run.py, p1/run.py; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/TEXT-F12-defend/check_plant_disclosure.py (output: check_plant_disclosure.out in the same dir): code facts at both run commits vs regex search of paper.qmd, fig_plant.py and references.bib; Rendered papers/paper_1/figures/fig_plant.pdf to /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/TEXT-F12-defend/fig_plant-1.png and inspected incident placement; diff of v5b/d1/plant.py between 93ba655 and e7dd561 (identical); Read paper.qmd in full (lines 1-203), p1_incident_information.md lines 15-80, screen_D2_incidents.md lines 86-100; grep of docs/ for av_share / speedFactor / severity / code-availability statements (none disclose the 10% av type); Checked raw run dirs ~/work/phd/v5b1_runs/p1b/v108 and p1b_c1/v114 for kept route files (none kept; av share confirmed from code path only)

### B25. [major] TEXT-F13: Spill share uses an undisclosed post-run proxy and excludes FX

Raised as major; verification: reproduce: CONFIRMED/major, defend: CONFIRMED/major.

#### TEXT-F13 (R1 TEXT, major, discrepancy): The spill sentence uses an undisclosed post-data indicator and is wrong for FX

- **Description.** Line 197 says that at 2000 veh/h the meter queue 'reached the upstream entry in 85-100 % of metered runs'. The measure is the indicator defined after the data (V109): the tail within 50 m of the entry, or a mean depart delay above 5 s. The paper does not define it or say that it came after the data. FX, which is metered, has 0.07 (slow) and 0.42 (block), and NC has 0.11 and 0.34. No run's tail came within 7 m of the entry (the pre-registered B4 flag never fired).
- **Evidence.**
  - paper.qmd:197
  - p1b_result.md:64, :82
  - docs/decisions.md:128 (V109)
  - /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/TEXT/spill_q2000.out
- **Failure scenario.** The sentence misdescribes both the evidence and the arms it covers. The underlying point, that q2000 assumes unlimited upstream storage, still stands.
- **How to test.** Rerun spill_q2000.py. Rephrase: 'for N, FB, PI, AD, ID and IP, a post-run indicator (definition) flags 85-100 % of runs'.
- **Related claims.** C85

#### PLANT-F6 (R1 PLANT, minor, wording): The C84 range excludes FX and uses a post-run proxy in place of the pre-registered spill flag

- **Description.** At q2000 the V109 spill share is 0.85-1.00 for N, FB, PI, AD, ID and IP, but 0.07 (slow) and 0.42 (block) for FX. The paper says '85-100 % of metered runs'. The queue tail never passes 368.7 of 410 m. 'Reached the upstream entry' is the V109 proxy (tail within 50 m, or mean depart delay above 5 s), which replaced the pre-registered B4 flag (7 m). B4 never fired. The replacement is recorded in V109/V113 but not in the paper.
- **Evidence.**
  - spill_rows.json; analyze_plant.out spill section
  - v5b/p1b/analysis.py@93ba655:50,284-285; confirm_c1.py@e7dd561:59,140-141; docs/decisions.md:128,132
- **Failure scenario.** A reader assumes every metered arm spilled. A reviewer checking against the protocol finds that the pre-registered flag never fired.
- **How to test.** Reword to 'in 85-100 % of runs of N, FB, PI, AD, ID and IP (FX 7 % and 42 %)', and state that the spill indicator was defined after the run.
- **Related claims.** C84

#### PROV-F7 (R1 PROV, minor, disclosure): The spill share in the paper comes from a post-run recomputation of the queue flag

- **Description.** The pre-registered B4 flag never fired because of a 7 m tolerance bug. The '85-100 % of metered runs' at 2000 veh/h on paper line 197 comes from an indicator recomputed after the run (V109; the decision was recorded at 10:38:01, before the P1b launch at 10:38:06, but implemented afterwards). The paper does not say this.
- **Evidence.**
  - decisions.md V109 (8e10812 10-20 10:38:01)
  - p1b_result.md:64
  - paper.qmd:197
- **Failure scenario.** A reader takes the spill share for a pre-registered output.
- **How to test.** Compare the B4 flag in p1b result.json with p1b_verification's recomputed spill.
- **Related claims.** C53

#### Verifier R1 reproduce: CONFIRMED / major

Meaning: paper.qmd:197 (identical at HEAD 1e5e8d7 and at the last paper commit 4de404a) says: "At 2000 veh/h the meter queue reached the upstream entry in 85-100 % of metered runs, so these cells assume unlimited upstream storage." The claim is meant to say that the stored queue fills the whole 410 m approach. I re-derived the evidence from the raw run JSONs with my own code, and every core fact in the finding holds.

(1) No queue tail reached the entry. The pre-registered B4 flag (p1b_addendum.md:41, "exceeds the available length in more than 5 % of runs") is coded as max_queue_m >= avail_m - 7 (v5b/p1b/analysis.py@93ba655:50,284-285). It fired in 0 of 344,852 P1b runs and 0 of 1,100 C1 runs. The closest tail was 369.6 m of 410 m, so 40.4 m short of the entry. In the main-table q2000 rows the maximum is 368.66 m. queue_limit_flags in result.json is [].

(2) The 85-100 % comes from the V109 proxy (tail within 50 m of the entry, OR mean depart delay > 5 s). V109 itself (commit 8e10812, 10:38:01, before the first tool-check run.log line at 10:38:07) only says the flag will be "recomputed after the run ... (max_queue_m + depart delay)", with no thresholds. The 50 m and 5 s thresholds first appear in the verifier prompt jobs_prompts/p1b_verify.md (mtime 20:31:20). That is after the P1b evaluation finished (run.log "done" 20:30:10). They reach the repo at 4f91777 (21:03) and confirm_c1.py@e7dd561:59,140-141. So the indicator's definition came after the data.

(3) The paper defines neither the indicator nor the deviation. A grep of paper.qmd for 50 m, depart, post-run, indicator, insertion or 410 finds nothing.

(4) FX is a metered L0 arm (paper.qmd:118,130), but its V109 shares are 0.07 (slow_q2000) and 0.42 (block_q2000). NC (no meter) has 0.11 and 0.34. The 0.85-1.00 range holds only for N, FB, PI, AD, ID and IP. Even pooled over all seven metered arms, slow_q2000 gives 0.82, below 85 %.

The headline results (S1a/S1b, Table II, C1) are not affected, because delay includes the origin wait. The underlying point (q2000 relies on unlimited storage, with median depart delays of 2-44 s for those arms) still stands. But the sentence is false as written in two ways: no queue physically reached the entry, and FX is excluded from 'metered runs'. It also hides a replacement of a pre-registered flag with a post-data one. That fits 'major' as defined.

Small corrections to the tracers:
- PROV-F7 gives the launch as 10:38:06; run.log first shows 10:38:07.
- PLANT-F6's 368.7 m maximum holds for the main-table rows only. Over all runs it is 369.6 m, as p1b_result.md:64 says.
- Calling the 7 m tolerance a 'bug' is an interpretation. The tail metric counts only halted vehicles (speed < 0.1 m/s) on edges 1-2 (episode.py@93ba655:111-121), and in these runs it never came closer than about 40 m to the entry, so the 7 m criterion did not fire in any run.

Further findings:
(a) paper.qmd:118 calls N 'the best constant rate on incident-free days'. But fit_fixed (analysis.py@93ba655:119-126) picks N over G = CONST + FEEDBACK, and at q2000 N = f10_8, an integral-feedback law (v5b/p1/family.py@93ba655:25). The arm description is wrong at 2000 veh/h, where N is also the arm that spills most (1.00, median depart delay 33-44 s).
(b) The caveat is limited to 2000 veh/h, yet in the C1 cell (block_q1600) the C1 rival PI (p70_120_8_e4) meets the V109 indicator in 0.32 of P1b runs and 0.32 of C1 runs (0.38-0.39 with runners), against 0.05 for IP. The storage assumption therefore also touches the confirmed C1 comparison. The effect on that comparison has not been tested.
(c) In block_q2000, ID and IP are the same runs (same plan p20_20_14_e4), so the IP 0.96 is not an independent observation.

Checks: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/TEXT-F13-reproduce/spill_check.py (rebuilds the run keys of the main-table arms from result.json controllers, asserts each loaded run's spec fields, and computes the B4, tail50, dep5 and V109 shares per arm and cell; output spill_check.out and spill_rows.json); /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/TEXT-F13-reproduce/scan_all.py on p1b/v108 and p1b_c1/v114 (all runs: max tail, gap to entry, B4 fire count; output scan_all.out); /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/TEXT-F13-reproduce/c1_spill.py (C1 spill shares per run group; output c1_spill.out); git show 93ba655:v5b/p1b/analysis.py, episode.py, family.py; git show e7dd561:v5b/p1b/confirm_c1.py; git show 93ba655:v5b/p1/family.py (CONST/FEEDBACK); git diff --stat e7dd561 HEAD and HEAD -- v5b/p1b/ (no drift); git log -S'B4 spill flag never fires' / -S'within 50 m' / -S'depart delay > 5' for decision and threshold timing; run.log head and tail timestamps; stat mtimes of jobs_prompts/p1b_verify.md and jobs/*/prompt.md; grep of paper.qmd for spill, storage, entry, 50 m, depart, indicator, post-run, FX, N and metered definitions; sed of p1b_addendum.md B4, decisions.md V109/V113/V116 and p1b_result.md:60-66,80-84; Compared against docs/research/results/p1b_verification/out/spill.log (all values match)

#### Verifier R1 defend: CONFIRMED / major

The finding survives my best defence of the paper. Two points help the author, but neither removes the problem.

What helps the author:
(1) The recompute was decided before any data. V109 (commit 8e10812, 10:38:01) says to recompute the flag from max_queue_m and depart delay after the run and to disclose it. The tool-check record is dated 11:03:09 and the evaluation started at 13:07:53.
(2) The results note p1b_result.md §7 plans that disclosure, and the paper's Discussion and Limitations section is still empty. So the gap may be a draft omission, not hiding.
(3) The indicator is report-only. Delay includes the insertion wait, so S1-S3, C1 and Table II are not affected.
(4) The conclusion of the sentence holds: the q2000 cells do rely on SUMO's unlimited insertion queue. For N the median depart delay is up to 43.7 s and the maximum 118 s (AD, block).

Why the problem survives:
(a) FX is a metered arm. At q2000 its plan is c2000, a constant 2000 veh/h. The signal cycles every 14.4 s (6 s green, 3 s amber, 5.4 s red; meters.py@93ba655:29-38). Its spill share is 0.07 (slow) and 0.42 (block). The OR bounds give 0.70-0.87. So '85-100 % of metered runs' is false as written. The arm-by-arm list in p1b_result.md:64 was cut to 'metered' in the 4f91777 commit message and in V113, and the paper copied that.
(b) The 50 m and 5 s thresholds first appear in 4f91777 (21:03:05), after the evaluation. V109 names the ingredients but not the thresholds.
(c) 'Reached the upstream entry' is literally false. The furthest queue tail in any run is 368.7 m of 410 m, and the pre-registered 7 m B4 flag fired in 0 runs. The 85-100 % comes entirely from the 'tail within 50 m' part: the depart-delay test adds 0 extra runs. Insertion blocking, the physical sign that the queue reached the entry, gives a lower range for N, FB, PI, AD, ID and IP: 32-100 % with depart delay over 5 s, and 57-100 % with depart delay over 1 s.
(d) The paper's Protocol paragraph (line 145) presents everything as fixed beforehand and has no caveat.

By the audit definitions this is a false statement as written while the headline survives, so the severity is major, at its low end. It is fixed by rewording, for example: 'For N, FB, PI, AD, ID and IP, a post-run indicator (queue tail within 50 m of the entry, or mean insertion delay above 5 s) flagged 85-100 % of runs (FX 7 % and 42 %).'

Two side findings in this area. First, paper line 118 calls N 'the best constant rate on incident-free days'. The protocol (p1_incident_information.md:30) defines N as the best of G, and at q2000 N is f10_8, a feedback law with a mean command of 889-947 veh/h. That arm drives the 100 % spill share. Second, the working tree has the same analysis.py and episode.py as 93ba655.

Checks: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/TEXT-F13-defend/spill_defend.py: own json/numpy code, no v5b import. It reads 100 raw run JSONs per arm and cell from ~/work/phd/v5b1_runs/p1b/v108/runs, with the arm-to-action map from p1b_result.json tune.arms, and computes old7, tail50, dep5, the union, dep>1, max tail, depart delay and commanded rate. Output: spill_defend.out and spill_defend.json in the same dir.; Read the paper text (paper.qmd:93,118,145,197) and confirmed via pdftotext that the rendered PDF has the same sentence; grepped the paper for any post-run, descriptive or definition disclosure: none.; git show 93ba655: v5b/p1b/analysis.py:40-60,275-313 (B4 flag), v5b/p1b/episode.py:15-17,108-121,195-215,255-275 (how max_queue_m and depart_delay_s are measured), v5b/p1b/meters.py:5-42 (FX c2000 cycles red). git diff 93ba655 HEAD for these files: no change.; Timeline: git log of docs/decisions.md V109 row (8e10812 10:38:01, only commit touching it), p1b_addendum.md (75bcd2b 09:51:10), and p1b_verification rederive.py/spill.py (first in 4f91777 21:03:05); P1B_TCHECK_RECORD.json 11:03:09; P1B_EVAL_STARTED.json 13:07:53.; Read protocol B4 (p1b_addendum.md:38-41), the C1 descriptive list (p1b_confirm_c1.md:25-31) and the N definition (p1_incident_information.md:28-34).; Compared against docs/research/results/p1b_verification/out/spill.log and p1b_result.md:64, §7: numbers identical to my recomputation.

### B26. [major] TEXT-F5: N described as constant rate but is a feedback law at q2000

Raised as major; verification: reproduce: CONFIRMED/major, defend: CONFIRMED/major.

#### S1-F7 (R1 S1, major, discrepancy): N is not a constant rate at 2000 veh/h

- **Description.** Line 118 describes N as 'the best constant rate on incident-free days'. The protocol defines N as the best member of G (constants and feedback laws). At q2000 the tuned N is f10_8, an integral feedback law. ID and IP therefore run a feedback law before onset at q2000. This is a false statement as written, although it does not change any number.
- **Evidence.**
  - result.json tune.arms['2000'].N = 'f10_8'; tune_check.py re-derivation agrees
  - protocol p1_incident_information.md §2 table 'N: Best of G on no-incident tuning runs'
  - paper.qmd:118
- **Failure scenario.** A reader assumes the S1 comparisons start from a constant-rate baseline at q2000.
- **How to test.** Change line 118 to 'the best controller of the family on incident-free days (N)'.
- **Related claims.** C64

#### TEXT-F5 (R1 TEXT, major, discrepancy): N is described as a constant rate, but at q2000 it is a feedback law

- **Description.** Line 118 defines N as 'the best constant rate on incident-free days'. The protocol defines N as the best member of G, which contains both constant-rate and feedback controllers. At q2000 the tuned N is f10_8, an integral-feedback law on the K_F grid edge. So at q2000, ID and IP run a feedback law before onset.
- **Evidence.**
  - paper.qmd:118
  - p1_incident_information.md:31
  - p1b_result.json tune.arms['2000'].N = 'f10_8'; tune.grid_edges_report_only['2000'].N = ['K_F=10']
- **Failure scenario.** Readers misread the pre-onset controller and the controller family behind the q2000 results.
- **How to test.** Rerun check_paper_numbers.py (section 'Line 118'), then rephrase to 'the best controller of G on incident-free days'.
- **Related claims.** C12

#### Verifier R1 reproduce: CONFIRMED / major

Meaning: paper.qmd:118 says arm N is "the best constant rate on incident-free days". The pre-registered protocol defines N as the best member of the whole family G, and G holds both constant rates and integral-feedback laws. At 2000 veh/h the tuned N is f10_8, a feedback law, so the sentence is false for that demand level. It is true at 1600 veh/h.

Core fact reproduced from primary evidence:
(1) Protocol p1_incident_information.md:31 defines N as "Best of G on no-incident tuning runs, per q". Family G (lines 42ff) contains constants plus K_F x n_crit feedback laws.
(2) The code that ran builds N over all of G. v5b/p1b/analysis.py@93ba655:124 has `"N": fam.best_by_median(none, G_)`, while FX is restricted to fam.CONST (line 167). The working tree does not differ from 93ba655 for v5b/p1b/analysis.py, run.py or v5b/p1/family.py; only confirm_c1.py was added later. In v5b/p1/family.py@93ba655:5, 'f<K_F>_<n_crit>' is D1's FBMeter integral law with T = 30 s and q0 = 1500.
(3) My own re-derivation from the 40 raw no-incident tuning runs per controller (seeds 7400300-7400339, all present and valid; rule: lowest median delay, ties by G order) gives N = f10_8 at q2000 (median 144.67 s). The best constant there is c1700 (146.91 s, 1.5 % worse). At q1600 it gives N = c1800 (44.74 s). Both match p1b_result.json tune.arms. grid_edges_report_only['2000'].N = ['K_F=10'] also holds: 10 is the lowest value of KF_GRID.
(4) f10_8 really does vary its rate, so it is not a near-constant in disguise. Within one run the commanded rate takes 12-18 distinct values. Per-run minimum is 200-1500 veh/h and per-run maximum 1530-1980 veh/h. The run mean ranges 879-1803 veh/h across seeds.
(5) The raw evaluation file names confirm that ID and IP at q2000 start with N. Examples: 'f10_8-c1800_slow_q2000_...' and 'f10_8-f10_8+back_block_q2000_...'. So at q2000 both run a feedback law before onset, and the '+back' plans release back to that feedback law.

Likely cause: the wording seems to have been carried over from P1, the round without amber. There N was constant at both demands (p1_result.json tune.arms N: 1600 = c2000, 2000 = c1800). The amber change in P1b made the q2000 N a feedback law. 'git log -S' points to commit f53b9c3 (V122) as the first appearance of the phrase.

Scope and severity: no number changes. The S1 numbers already use the actual N. C1 is not affected: its cell is block_q1600, where N = c1800 is a constant (p1b_c1_result.json frozen_arms). It stays major under the audit definition, because a paper statement is false as written, but the headline survives.

Suggested fix: "the best controller of G (a constant rate or an integral-feedback law) on incident-free days (N: c1800 at 1600 veh/h, f10_8 at 2000 veh/h)".

Correction to the tracer evidence: S1-F7 says "tune_check.py agrees". I did not run that script. My own independent script agrees.

Checks: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/TEXT-F5-reproduce/rederive_N.py: rebuilds G (50 controllers) from the protocol and re-derives N per q from the raw no-incident tuning runs, using numpy/json only. Result: q1600 N = c1800, q2000 N = f10_8; best constant at q2000 = c1700.; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/TEXT-F5-reproduce/within_run_range.py: range of f10_8's commanded rate within each run at q2000. Not constant (12-18 distinct values per run).; grep -n on paper.qmd and the protocol to confirm line numbers 118 and 31; pdftotext of paper.pdf confirms the same sentence.; git show 93ba655:v5b/p1b/analysis.py, v5b/p1/family.py, v5b/p1b/run.py; git diff --stat 93ba655 HEAD -- v5b/p1b/ v5b/p1/family.py (only confirm_c1.py added).; Python summary of p1b_result.json (tune.arms, grid_edges_report_only, seeds, code_commit), p1_result.json tune.arms N and p1b_c1_result.json cell/frozen_arms.; git log -S 'best constant rate on incident-free' to locate the commit that introduced the wording (f53b9c3).

#### Verifier R1 defend: CONFIRMED / major

Meaning: N is the controller that runs on incident-free days. ID and IP also run N before the incident starts, and the "back" actions return to N after the incident clears. Paper line 118 calls N "the best constant rate on incident-free days". The protocol and the code define N as the best member of the whole family G, and G holds both constant rates and integral-feedback laws.

Defence attempted:
(1) A definition elsewhere. Every protocol defines N as "best of G": screen_D2_incidents.md:43 and p1_incident_information.md:31. None says "constant". Paper line 99 says L0 laws may be "a constant rate or feedback", but that sentence covers L0 in general. Line 118 names N specifically as a constant. No other paper line (grep of paper.qmd, and the rendered PDF, which has the same wording) says that N is f10_8 at q2000.
(2) A different code path or a later commit. fit_fixed at 93ba655 sets N = best_by_median over all of G on no-incident runs, and the working tree has the same code. So the code follows the protocol and the paper text is what is wrong.
(3) "f10_8 is nearly constant." This defence fails. In the raw no-incident runs its commanded rate climbs from 1500 to about 1845 veh/h (median std over seeds about 106 veh/h), so it really is a feedback law. Onset falls in the first 300 s, when the rate is still ramping up from 1500.
(4) "True at q1600." It is: there N is c1800. So the statement is false only at q2000, which is half of the evaluation cells.

The finding survives my defence. It does not change any number: S1a, S1b and Table II stay as they are, and the binding arms are FB and PI. But under the given rubric it is a method statement that is false as written, so it stays major. It is borderline minor, and the fix is one phrase: "the best controller of G (constant or feedback) on incident-free days".

Checks: grep and sed of paper.qmd lines 93-135 and every N mention; pdftotext of paper.pdf for the 'best constant' wording; Read the protocol N and G definitions: p1_incident_information.md:31,45; screen_D2_incidents.md:43; grep of docs/decisions.md; git show 93ba655:v5b/p1b/analysis.py (fit_fixed) and run.py (stage_tune); git diff --stat 93ba655 HEAD on the relevant files (no change); /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/TEXT-F5-defend/n_identity.py: independent median-delay ranking of all 50 G members on raw no-incident tuning runs per q (output n_identity.out); /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/TEXT-F5-defend/f10_8_behaviour.py: f10_8 commanded-rate trajectory from raw meter_log (output f10_8_behaviour.out)

### B27. [major] TEXT-F9: C1 reporting gaps (rule, CI, post-hoc, PI only, metric name)

Raised as major; verification: reproduce: CONFIRMED/major, defend: CONFIRMED/major.

#### TEXT-F9 (R1 TEXT, major, disclosure): C1 reporting gaps: rule not stated, CI below 10 %, post-hoc choice, only PI tested, metric misnamed

- **Description.** Five problems:
(a) The C1 rule (point rel >= 10 % and diff-CI lower bound > 0) is not stated, and the rel CI [7.3, 23.7] includes values below 10 % (V116 caveat).
(b) The cell and arms were chosen after the P1b data; the C1 page requires this disclosure.
(c) C1 tests PI only. In P1b's block_q1600, FB was the strongest L0 arm (247.9 vs PI 252.1 s/veh), and IP vs FB was 15.9 % [7.8, 22.9]. C1 does not confirm 'beyond every always-on arm'.
(d) 'Reduced median delay ... by 16.2 %' misnames the metric: 16.2 % is median(PI - IP)/median(PI). The median delay itself fell by 17.3 % (254.7 to 210.6 s/veh).
(e) 'The same result when seeds with invalid runs are excluded' is vacuous: no run was invalid.
- **Evidence.**
  - paper.qmd:145, :187
  - p1b_confirm_c1.md:17-25, :36
  - docs/decisions.md:135 (V116 caveat)
  - p1b_c1_result.json c1.C1.all_seeds (rel 0.1625, rel_ci [0.073, 0.237]); c1.rows medians IP 210.57, PI 254.68
  - p1b_result.json eval.table1_operating_map.block_q1600 (FB 247.9, PI 252.1)
- **Failure scenario.** Readers infer that a gain of at least 10 % over the best always-on control was confirmed. What was confirmed is a point estimate of at least 10 % with a positive lower bound, against PI only.
- **How to test.** State the C1 rule and the CI in the text; add 'chosen after P1b'; say that FB was not tested; rephrase the metric.
- **Related claims.** C13, C12

#### Verifier R2 reproduce: CONFIRMED / major

I reproduced all five sub-facts from the raw runs, the code at the run commits, the protocol and the paper text. I did not rely on the results notes.

(a) The paper does not state the C1 rule. Line 145 says only "a single pre-fixed statement at the 95 % level". The approved rule (p1b_confirm_c1.md:21-22) is: point rel >= 10 % AND lower bound of the 95 % CI of median(PI-IP) > 0, in both views. My own bootstrap gives rel 16.25 %, rel CI [7.31, 23.68] %, diff CI [16.61, 65.69] s/veh. So the rel CI includes values below 10 %: about 10 % of bootstrap replicates have rel < 10 %. C1 still passes as pre-registered, because the rule uses the point rel and the diff CI, not the rel CI.

(b) The paper never says that the cell and the arms were chosen after the P1b data. The approved protocol says so at line 36 (the sha256 matches the run's page_sha256). Lines 69 and 145 say statements were fixed "before any data were produced". For C1 this is true only relative to C1's own data. Nuance: the protocol carries the disclosure itself; it does not literally instruct the paper to repeat it.

(c) C1 ran only IP, PI, N and NC (11 run variants, no f40_10/FB). In P1b block_q1600, FB had the lowest L0 median: 247.87 vs PI 252.14 s/veh. p1b_result.json labels FB strongest_L0 for this cell, and the paper's Fig. 1 shows that arm. IP vs FB is 15.89 % [7.79, 22.93] at level 0.99375, reproduced exactly. The quoted phrase "beyond every always-on arm" is not in the paper. Line 187 correctly says "relative to always-on PI". So this is an omission, not a false statement. In P1b data IP also meets rule (a) against FB (diff CI lower bound 18.0 > 0), but that was never re-tested on fresh seeds.

(d) 16.2 % is median(PI-IP)/median(PI). The median delay itself fell from 254.68 to 210.57 s/veh, which is 17.32 % or 44.11 s. The 41.4 s/veh is the median paired difference, not the change in median delay. rel is defined at line 145, and the error goes in the conservative direction, so this sub-item alone is minor.

(e) 0 of 1,100 C1 runs are invalid (also 0 teleports, all drained, 0 collisions), and n_invalid_seeds = 0. The valid-only view is therefore identical to the all-seeds view, so the sentence is true but uninformative.

No headline number is wrong, and C1 passes its pre-registered rule. Together, (a)-(c) are disclosure gaps a reviewer would ask to have fixed. Severity: major.

Checks: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/TEXT-F9-reproduce/recompute_c1_f9.py (own bootstrap and medians from raw C1 and P1b run JSONs; commit and spec asserts; output in recompute_c1_f9.out in the same dir); /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/TEXT-F9-reproduce/text_checks.sh (paper lines 145/187/189, disclosure grep, protocol lines and sha256, C1 run variants; output in text_checks.out); git show e7dd561:v5b/p1b/confirm_c1.py, v5b/p1/stats.py (paired: rel = median(d)/median(r); rel_ci from per-replicate ratio), v5b/p1b/analysis.py (_d = delay_s, _v = valid); p1b_result.json: tune.arms.1600, eval.table1_operating_map.block_q1600, eval.cells.block_q1600.IP_vs_L0, eval.fig1_ladder.block_q1600; p1b_c1_result.json c1.C1 summary; docs/decisions.md:128-136

#### Verifier R2 defend: CONFIRMED / major

My best defence removes some of the finding, but its core holds. Sub-part (c) is overstated. Sub-parts (a), (d) and (e) are real but minor. Sub-part (b) holds at major.

(a) Rule not stated. VERIFIED, minor (basis: direct observation). Paper line 145 only says C1 had "a single pre-fixed statement at the 95 % level". Defence: the same paragraph states the S1 rule R(a): rel >= 10 % and the lower CI bound of median(r - t) > 0. C1 is exactly that rule for one cell (p1b_confirm_c1.md:19-22). The rel CI [7.3, 23.7] is printed at line 187. Fig. 3 plots this CI next to a dashed 10 % line, so the reader can see it cross 10 %. What remains: the paper never says that C1 used R(a), and it gives no caveat (V116 has one). My own bootstrap gives P(boot rel < 10 %) of about 0.10. The two-sided 80 % lower bound is about 10.0 %.

(b) Post-hoc choice not disclosed. VERIFIED, major (basis: direct observation plus derived). Git timing: the P1b results were committed at 20:31 (95f1f33) and verified at 21:03 (4f91777). The C1 page was drafted at 21:09 (a4e3e6d) and approved at 21:11 (7c6acc8). The page's sha256 (8b6005aa...) matches result.json and the sentinel, and the sentinel was written at 21:27:50. So the C1 statement was fixed before C1's own data, but after P1b's data. The page itself has a "Disclosure" item saying exactly this (p1b_confirm_c1.md:36). The paper does not say it. Instead it says "All statements were pre-registered before any data were produced" (line 69) and "The protocol, its statements and the seed ranges were fixed and approved before any data were produced" (line 145). Defences: the narrative implies the selection (line 155 ends with the report-only row, and C1 then tests that cell), and the per-study reading of "before any data" is true. Neither defence is explicit, and the global reading is false for C1. The fresh-seed test itself is valid: the seeds 7,400,700-799 do not appear in the P1 or P1b run files. So the headline survives, and this is not critical.

(c) PI only. Overstated, minor (basis: direct observation). The quoted phrase "beyond every always-on arm" does not appear in paper.qmd. Every C1 sentence says "relative to always-on PI" (lines 187, 189). Fig. 2 labels FB as the L0 arm for the lane crawl at 1600 veh/h, so FB being the strongest arm there is visible. My recomputation from the P1b raw runs confirms the finding's numbers:
- median delay: FB 247.87 s/veh, PI 252.14 s/veh;
- IP vs FB: 15.9 % [7.6, 23.1] at level 0.99375;
- IP beat all five L0 arms in P1b (report-only), each with diff lower bound > 0.

What remains: C1 ran no FB arm, so no fresh-seed evidence exists against the strongest arm (by median delay) in that cell. The paper does not say why PI was chosen, although the P1 protocol's intersection-union rule (p1_incident_information.md:89) defines "beats L0" as against every arm.

(d) Metric name. VERIFIED, minor (basis: derived). The 16.2 % is median(PI - IP)/median(PI). The medians themselves fell from 254.68 to 210.57 s/veh, which is 17.3 %. Defence: rel is defined at line 145, and the wording understates the gain rather than inflating it. Still, "reduced median delay by 16.2 %" is imprecise as written. The same applies to "41.4 s/veh": the difference of the medians is 44.1 s/veh. The Fig. 3 axis label uses the same loose wording.

(e) Invalid-runs view. VERIFIED, minor (basis: direct observation). 0 of the 400 IP/PI/N/NC runs are invalid (also 0 teleports, 0 collisions, all drained). JSON n_invalid_seeds = 0, so the two views are identical. The sentence is true and reports the pre-registered two-view check, but it implies that some seeds were excluded. It should add "(no run was invalid)".

Overall: the group's problems survive as disclosure and wording gaps. None of them changes the C1 verdict, and C1 is CONFIRMED under its own pre-registered rule. Major is justified mainly by (b). The rest is minor.

Checks: Read round2_input.json groups['TEXT-F9']; Read paper.qmd:55-80 and :140-203 (protocol, results, C1, figure captions); grep for every/strongest/beyond/pre-registered/invalid; Read docs/research/protocols/p1b_confirm_c1.md in full; grep p1_incident_information.md and p1b_addendum.md for the IP-vs-L0 rows and the intersection-union rule; Read docs/decisions.md V106-V126 (V112-V116 timing and the V116 caveat); git log/show timing and sha256 of p1b_confirm_c1.md at a4e3e6d and 7c6acc8 vs result JSON and sentinel; git show e7dd561:v5b/p1b/confirm_c1.py (statement code); /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/TEXT-F9-defend/c1_recompute.py (output c1_recompute.out): independent C1 medians, rel, bootstrap CIs, invalid counts from raw runs; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/TEXT-F9-defend/p1b_ip_vs_l0.py (output p1b_ip_vs_l0.out): P1b block_q1600 IP vs each L0 arm from raw runs at 0.95 and 0.99375; Read papers/paper_1/figures/fig_ladder.py and fig_c1_robust.py; p1b_result.json fig1_ladder and table1_operating_map for block_q1600; Filename scan of p1b/v108 and p1/v99 runs for C1 seeds 7,400,700-799

### B28. [minor] C1-F3: Decision rule tests >=10 % on point estimate only; CIs include gains below 10 %

Raised as minor; verification: not adversarially verified.

#### C1-F3 (R1 C1, minor, statistics): Confirmed statement does not establish a gain of 10 % or more

- **Description.** C1's rule needs only the point estimate to be >= 10 % plus a median difference > 0. The rel CI [7.3, 23.7] includes gains below 10 %. The d = 30 and d = 120 rows (CI lower bounds 7.9 % and 5.7 %) also cross the dashed 10 % line in Fig. 3. The text should not suggest that a gain of at least 10 % was confirmed.
- **Evidence.**
  - result.json c1.C1.all_seeds rel_ci [0.0731, 0.2368]
  - fig_c1_robust.py draws the 10 % line; descriptive rel CIs: d30 [7.9, 21.7], d120 [5.7, 25.0]
- **Failure scenario.** Readers take 'C1 confirmed' plus the 10 % line as evidence of a gain of at least 10 %.
- **How to test.** Read the rel_ci values in p1b_c1_result.json.
- **Related claims.** C71, C73

#### REPRO-F11 (R1 REPRO, info, statistics): Fig. 3 CI crosses the 10 % line; the paper text does not state the caveat

- **Description.** C1 passes on point rel 16.2 % >= 10 % and diff-CI lower bound > 0. The rel CI [7.3, 23.7] includes values below 10 %. Decision record V116 notes this caveat; the paper does not. The 'Detection +120 s' row also reaches 5.75 %. The CI is computed correctly as specified.
- **Evidence.**
  - docs/decisions.md V116 caveat
  - p1b_c1_result.json c1.C1.all_seeds.rel_ci = [0.0731, 0.2368]
- **Failure scenario.** A reader takes the dashed line as the confirmed lower limit of the gain.
- **How to test.** Read rel_ci in the JSON.
- **Related claims.** C75

#### S1-F4 (R1 S1, minor, wording): 'No detected gain of 10 % or more' does not describe what rule (a) tests

- **Description.** Rule (a) needs a point rel of at least 10 % and a CI of median(r − t) above zero. It tests 'gain > 0' at the CI level and '≥ 10 %' only on the point estimate. So a pass does not establish a gain of 10 % or more: S1b's lower bounds are 5.8 % and 8.8 %. A fail is not merely 'not detected' either: against PI, the 99.375 % upper bounds are −6.7, 0.0, 6.7 and 0.0 %, so a 10 % gain is excluded in every cell. In slow_q1600, IP vs ID is 16.2 % [−16.7, 27.4]: neither 0 nor 10 % is excluded (inconclusive).
- **Evidence.**
  - v5b/p1/stats.py@93ba655:79-80
  - s1_recompute.py rows ID_vs_PI and IP_vs_ID
- **Failure scenario.** Readers think S1b showed the type adds at least 10 %, and think S1a is merely underpowered. In fact the CIs exclude a gain of 10 % or more over PI.
- **How to test.** Rephrase. For example: 'S1a fails: in no cell did ID reach a point gain of 10 % or more with an interval above zero against every always-on arm; against PI the intervals exclude gains above 7 %'. Also say that the S1b lower bounds are below 10 %.
- **Related claims.** C64, C66

### B29. [minor] C1-F7: Emergency-stop population and braking warnings not stated

Raised as minor; verification: not adversarially verified.

#### C1-F7 (R1 C1, minor, missing-evidence): Emergency-stop population and braking warnings not stated

- **Description.** The 12.8 % is over all k=0, s=0 evaluation runs. 83 % of these are runs of every action of A (for the oracle), not the deployed arms. Per arm the share differs: in C1, PI 21/100 and IP 14/100 runs; in P1b block_q1600, FX 47/100. Other choices give 11.8-13.0 %. SUMO emergency-braking warnings at the meter still occur in 22.0 % of P1b runs. The paper reports neither the population nor the warnings. 'Emergency stop' is SUMO's counter (getEmergencyStoppingVehiclesNumber). I am not fully certain of its exact SUMO semantics; verify against the SUMO documentation before defining it in the paper.
- **Evidence.**
  - estops.py / estops2.py output
  - docs/research/results/p1b_verification/out/p1_vs_p1b.log:24-30
  - c1_recompute.py safety block
- **Failure scenario.** Readers assume that 12.8 % applies to the deployed controllers, or that amber removed hard braking at the meter.
- **How to test.** estops.py composition lines; per-arm counts in c1_recompute.py.
- **Related claims.** C82

### B30. [minor] C1-F8: C1 descriptive rows not labelled descriptive

Raised as minor; verification: not adversarially verified.

#### C1-F8 (R1 C1, minor, disclosure): C1 descriptive rows not labelled descriptive; PI self-comparison not in the protocol text

- **Description.** The protocol lists the detection-delay and runner IP-vs-PI rows as 'descriptive (no claims)'. The paper presents them at line 187 without that label. The 'PI itself degraded' rows (PI vs PI_s) are computed by code committed before data, but they are not listed in the protocol.
- **Evidence.**
  - p1b_confirm_c1.md 'Reported, descriptive (no claims)'
  - confirm_c1.py@e7dd561:184-186
  - paper.qmd:187
- **Failure scenario.** The rows are read as confirmatory results.
- **How to test.** Compare protocol text with paper line 187.
- **Related claims.** C73, C74

### B31. [minor] CTRL-F12: Wrong-type p* is a per-seed exact mixture, not simulated misclassification

Raised as minor; verification: not adversarially verified.

#### CTRL-F12 (R1 CTRL, minor, hidden-assumption): Wrong-type p* is a per-seed exact mixture, not a simulated misclassification

- **Description.** stats.mixture gives (1-p)D(IP) + pD(other plan) on every seed, and M(p) is the median over seeds of this mixture. For median statistics this differs from misclassifying a random share p of incidents. Detection delay (all 1,986 d runs), clearance delay (400 runs) and false alarms (402 runs) are implemented as specified (s3_tp.json).
- **Evidence.**
  - v5b/p1/stats.py@93ba655:153-155; analysis.py@93ba655:548
  - /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/CTRL/out/s3_tp.json counts
- **Failure scenario.** If p* is reported, it is read as 'share of misclassified incidents'.
- **How to test.** Describe it as expected delay per incident, or compute it by random assignment per seed.
- **Related claims.** C47

### B32. [minor] CTRL-F6: TP placebo is not a like-for-like measure of OR_in noise inflation

Raised as major; verification: reproduce: CONFIRMED/minor, defend: CONFIRMED/minor.

#### CTRL-F6 (R1 CTRL, major, unsupported-interpretation): The TP placebo exploits demand-draw luck, so it does not measure the simulation-noise inflation of OR_in

- **Description.** TP takes min(IP main, 4 replicates). The replicates use new demand seeds, and the run TP picks has fewer generated vehicles than the main run (median 7.5-15.5 fewer). OR_in selects among 120 runs that share one demand file. Line 193 ('shows how strongly in-sample selection on simulation noise inflates hindsight gains') and line 141 ('pure-noise gains') overstate what TP measures. TP is also best-of-5 while OR_in is best-of-120.
- **Evidence.**
  - p1/stats.py@93ba655:145-149; p1/meters.py:233-239
  - /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/CTRL/out/s3_tp.json tp_demand_luck
- **Failure scenario.** A reviewer argues that the placebo inflation (13.6-37.7 %) is mostly arrival-count luck and cannot calibrate OR_in.
- **How to test.** Build a same-demand placebo: replicate only the SUMO seed with the same route file. Alternatively, describe TP as demand-plus-simulation noise.
- **Related claims.** C51, C49

#### S23-F5 (R1 S23, minor, invalid-comparison): Placebo TP is not a like-for-like illustration of OR_in's noise inflation

- **Description.** Both TP and OR_in select in-sample (minimum over candidates, scored on the selected run), but they differ in two ways:
- TP has 5 candidates of one plan with demand and SUMO seeds redrawn; OR_in has 120 actions sharing the main run's demand and pre-onset trajectory.
- TP exceeds OR_in in slow_q1600 (37.7 % vs 15.1 % median; 92.7 vs 77.9 s/veh mean), and in mean s/veh also in slow_q2000.
An OR_in limited to the 5 best tuning actions gains only 2.5-10.3 %, below TP. TP mainly measures demand-realisation variability, which no plan choice can exploit. The sentence also compares TP point estimates with bracket ends that are CI bounds.
- **Evidence.**
  - v5b/p1/stats.py@93ba655:145-149; v5b/p1/meters.py@93ba655:233-239
  - s23_recompute_20261019.log (TP vs OR_in, mean gains); s23_extra.log (OR_in over the top-5 tuning actions)
- **Failure scenario.** Readers take 13.6-37.7 % as the noise share of the upper bounds; in slow_q1600 that would leave OR_in negative.
- **How to test.** Build a placebo that holds demand fixed (SUMO seed only) with 120 copies of IP, or report TP strictly as a pure-noise illustration.
- **Related claims.** C78

#### Verifier R1 reproduce: CONFIRMED / minor

I reproduced every core fact of the finding from the code that ran and from the raw P1b v108 runs, using my own scripts.

1. What TP is, in code: TP = rel(IP_main, min(IP_main, IP_k1..k4)), so it is the best of 5 runs. Each replicate k redraws both the SUMO seed and the demand seed (seed + k*1e7). The incident window still comes from the base seed. All four replicates are used (rmax=4).
2. What OR_in is: the minimum over the 120 k=0 runs N->x. Those runs share one demand seed, one SUMO seed and one generated-vehicle count (true in 100/100 seeds in every cell).
3. The run TP picks has fewer generated vehicles than the main run. The median difference is -7.5, -10.5, -10.5 and -15.5 vehicles (slow_q1600, block_q1600, slow_q2000, block_q2000). This matches the tracer exactly.
4. My TP values match the reported 13.6-37.7 %. The 13.3-47.9 % 'upper bounds' in the paper are the upper ends of Bonferroni CIs (level 0.9875) on OR_in, while the TP figures are point estimates.
5. TP is larger than OR_in in slow_q1600 (median 37.7 % vs 15.1 %; mean 92.7 vs 77.9 s/veh). It is also larger in slow_q2000, by median (16.8 % vs 14.8 %, which S23 left out) and by mean (71.1 vs 59.7 s/veh).
6. The working tree is identical to 93ba655 for these files.

Where the tracers go too far: CTRL's failure scenario says the placebo inflation is 'mostly arrival-count luck'. My data do not show that. In a within-seed linear adjustment, the generated count explains only part of TP: TP falls from 37.7 to 31.0 %, 13.6 to 11.7 %, 16.8 to 12.4 % and 15.7 to 8.7 %. That is about 18-45 % of TP. Count is only one part of demand luck, though; arrival timing also matters. So the true demand share is probably larger, but I have not measured it.

Line 141 ('pure-noise gains') is accurate in a narrow sense: TP compares one plan with itself, so its gain is pure noise. Line 193 ('in-sample selection on simulation noise') loosely suggests TP measures OR_in's inflation. It does not, because the noise includes the demand draw, TP selects from 5 candidates instead of 120, and the comparison puts point estimates next to CI ends. The paper never subtracts TP from OR_in, so the S2 bracket and the headline results are not affected. That makes this an interpretation and wording issue, so I rate it minor rather than major. A reviewer could still ask for a same-demand placebo or for wording such as 'demand plus simulation noise'. I did not reproduce S23's 'OR_in over the top-5 tuning actions gains 2.5-10.3 %' figure: how the top 5 actions are defined is ambiguous, and I did not have it.

Checks: git show 93ba655:v5b/p1/stats.py, v5b/p1/meters.py, v5b/p1b/analysis.py, v5b/p1b/episode.py, v5b/p1b/family.py (read-only); git diff --stat 93ba655 -- (the 4 files): empty, so the working tree equals the run commit; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/CTRL-F6-reproduce/tp_vs_orin.py (output tp_vs_orin.json): recomputes TP and OR_in from raw runs with my own percentile bootstrap (B=20,000, 95 %); picked-k counts; generated difference picked vs main; candidate count and shared demand/SUMO seed/generated across the 120 OR_in runs; asserts the replicate seed arithmetic; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/CTRL-F6-reproduce/tp_count_adjust.py (output tp_count_adjust.json): within-seed OLS of delay on generated, count-adjusted TP, incident window identical across the 5 IP runs (100/100); grep -n placebo papers/paper_1/paper.qmd (lines 141, 193); result.json eval.S2[cell].all_seeds.OR_in.median and statements, to confirm the upper bounds are CI ends

#### Verifier R1 defend: CONFIRMED / minor

My best defence takes away some of the problem, but not all of it.

What the defence does establish:
(1) TP was pre-registered as a report-only illustration of "pure-noise inflation" that "is never subtracted from anything" (p1_incident_information.md:110).
(2) Author decision A3(a) deliberately makes replicates redraw both the demand seed and the SUMO seed. So in this design "noise" means everything except the incident (protocol:125, :148).
(3) Paper line 141 discloses this: replicates use "new demand and simulator seeds". Read with that, the line-141 phrase "shows the size of pure-noise gains" is accurate. TP compares IP with IP, so all of its gain is demand plus simulator noise.
(4) No inference uses TP. The S2 bracket comes only from OR_in and ORX, so no headline number changes.

What survives the defence:
- I checked the raw P1b runs. All 120 OR_in candidates on a seed share the same demand seed and have the same `generated` count. OR_in therefore cannot profit from arrival-count luck, but TP can and does. When TP picks a replicate, that run has a median of 13 to 24 fewer generated vehicles than the main run (7.5 to 15.5 fewer over all seeds).
- TP is larger than OR_in's whole gain over IP in two cells:
  - slow_q1600: median 37.7 % vs 15.1 %, mean 46.3 % vs 38.9 %;
  - slow_q2000: median 16.8 % vs 14.8 %, mean 20.3 % vs 17.1 %.
  OR_in includes IP's own plan, so its gain over IP is never negative on any seed. TP therefore cannot be the size of OR_in's selection-on-noise inflation.
- Line 193 says the placebo "shows how strongly in-sample selection on simulation noise inflates hindsight gains". It puts the TP range right next to the bounds on hindsight gains. That invites a magnitude comparison the design does not support.
- Calling this noise "simulation noise" (and "SUMO noise" in the results note, "noise floor" in decision V102) hides the fact that most of TP's noise is redrawn demand, which no oracle on the main run can use.

I rate it minor, not major. The problem is the interpretation and wording of one report-only sentence (line 193). The design behind it is disclosed and pre-registered, and no headline result depends on it. The fix is to reword line 193, for example: "TP shows how large best-of-runs gains from demand and simulator noise alone can be. It does not estimate OR_in's inflation." A demand-fixed placebo would be the alternative fix.

Separate finding in the same sentence: line 193 (and the PDF) says "the upper bounds ranged from 13.3 % to 47.9 %". result.json gives x = 47.9, 19.3, 25.4 and 22.4, so the range is 19.3 to 47.9 %. The "13.3" looks like a typo. It makes the TP range 13.6–37.7 % look as if it covers almost the whole range of upper bounds, which strengthens the misleading comparison.

Checks: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/CTRL-F6-defend/tp_vs_orin.py: own numpy/json code (no v5b imports) over v108 raw runs. Per cell it computes TP and OR_in (median and mean), checks shared demand_seed and generated count across A, the k of the run TP picks, its generated difference, and a demand-count-adjusted TP. Output in tp_vs_orin.json and tp_vs_orin.log in the same directory.; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify/CTRL-F6-defend/tp_gen_allseeds.py: median generated difference over all 100 seeds (log tp_gen_allseeds.log). It reproduces the tracer's 7.5-15.5.; git show 93ba655:v5b/p1/stats.py, 93ba655:v5b/p1/meters.py, and 93ba655:v5b/p1b/analysis.py (lines 236-372) for how OR_in and TP are built.; Read the protocol TP, A3 and seed sections (p1_incident_information.md:100-152) and p1b_addendum.md B3.; jq on v108/result.json: eval.TP, eval.S2.*.all_seeds.OR_in, eval.S2.*.statements, tune.arms IP plans, tcheck.T3.; grep of paper.qmd and pdftotext of paper.pdf for placebo, replicate and range wording; grep of decisions.md and p1b_result.md for TP interpretations.

### B33. [minor] CTRL-F9: Fig. 2 strongest always-on arm chosen per cell on evaluation seeds

Raised as minor; verification: not adversarially verified.

#### CTRL-F9 (R1 CTRL, minor, disclosure): Fig. 2's 'strongest always-on arm' is chosen per cell in hindsight on the evaluation seeds

- **Description.** analysis.py:376 picks the L0 arm with the lowest evaluation-seed median per cell. This is conservative, since it favours L0, but it is a selection on evaluation data and should be named in the caption. The d* binding arm is also the minimum over the L0 arms, which is conservative.
- **Evidence.**
  - v5b/p1b/analysis.py@93ba655:376-381
- **Failure scenario.** A reader assumes the L0 rung is a single pre-specified arm.
- **How to test.** Caption: 'strongest L0 arm per cell (chosen on the evaluation seeds)'.
- **Related claims.** C48

### B34. [minor] G2-F5: The gain over no control comes from avoiding a post-clearance zipper breakdown; the paper does not explain this

Raised as minor; verification: not adversarially verified.

#### G2-F5 (R2 G2, minor, missing-evidence): The gain over no control comes from avoiding a post-clearance zipper breakdown; the paper does not explain this

- **Description.** IP beats NC by about 28-30 %, and the gain is flat across incident durations. IP lets as many vehicles onto edge 4 during the incident as NC (84.5 vs 83.5). Its advantage comes after clearance: it holds q at about 480-890 veh/h for about 200 s, and the edge-4 count peaks at about 25. Arms that do not hold (N c1800, FX c2600) see edge 4 fill completely (count 60) and serve only 922-938 veh/h, against 1124 for IP. Even without an incident, NC at q=1600 breaks down (delay 258.5 s, served 1006 veh/h vs N's 45.4 s and 1444 veh/h). The plant's 1-lane zipper bottleneck is therefore near breakdown at the demand used. This is context the paper does not give.
- **Evidence.**
  - G2/g2_actions_traj.out
  - G2/g2_none_check.out
  - Critic/drain_decomp.out (IP vs NC: post-clearance share of dTTT 0.86)
- **Failure scenario.** Readers may attribute IP's gain over no control to incident handling during the incident, while it comes from managing the recovery at a merge that is near breakdown.
- **How to test.** Re-run G2/g2_none_check.py and G2/g2_actions_traj.py.
- **Related claims.** C71

### B35. [minor] G3R-F2: Long-wait warnings (H-R5, a vehicle waiting > 120 s) appear only in arms that reach the floor and are not reported; the results survive excluding them

Raised as minor; verification: not adversarially verified.

#### G3R-F2 (R3 G3R, minor, realism-disclosure): Long-wait warnings (H-R5, a vehicle waiting > 120 s) appear only in arms that reach the floor and are not reported; the results survive excluding them

- **Description.** H-R5 fires when, at a 300-s checkpoint, some vehicle has been waiting more than 120 s. In C1 it fires in 11 PI runs and 4 IP runs (14 seeds in either arm). In P1b block_q1600 it fires in 13 PI, 12 ID, 6 FB, 6 AD and 3 IP runs. It never fires in NC or N runs (no floor), and every H-R5 run reached the floor. This is consistent with the 135-s reds, but the checkpoint does not record which vehicle waited, so it is not proof. The paper only says that excluding invalid runs gives the same result; H-R5 is a warning, not an invalid flag, so it is not covered by that sentence. Exclusion sensitivity (post hoc): C1 13.5 % [3.3, 20.5], diff [7.1, 53.9], which still meets the C1 rule (rel >= 10 %, lower bound > 0). P1b block_q1600 IP vs ID 19.5 % [4.2, 30.3] at level 0.99375 (against 22.0 %), and IP vs PI 16.5 % [8.2, 29.8]. slow_q2000 has no H-R5 runs in IP or ID.
- **Evidence.**
  - v5b/d1/sumo_runner.py@93ba655:63 stuck_wait_s=120.0; :209-212 count of vehicles with getWaitingTime > stuck_wait_s -> WARN H-R5
  - G3R/g3r_floor.out: C1 'rel excl. 14 seeds with H-R5 in either arm: 13.5 % [3.3, 20.5]; diff 33.2 [7.1, 53.9]'; P1b block_q1600 IP vs ID 'excl. 14 seeds: 19.5 % [4.2, 30.3]', IP vs PI 'excl. 16 seeds: 16.5 % [8.2, 29.8]'
  - G3R/g3r_floor_when.out: H-R5 runs NC 0, N 0 (C1 and P1b block_q1600); PI 11 / IP 4 (C1); FB 6, PI 13, AD 6, ID 12, IP 3 (P1b)
  - docs/research/protocols/p1b_confirm_c1.md:21 C1 rule
  - Critic check reproduced: critic2/c1_hr5_sens.out 13.5 % [3.4, 20.5] (bootstrap seed differs)
- **Failure scenario.** A reader assumes that no vehicle waits unusually long. In fact 11 % of PI runs and 4 % of IP runs in C1 hold some vehicle more than 2 minutes at a freeway red. This is a compliance and realism flag that the runner rows (amber plus the first 1.5 s of red) do not model.
- **How to test.** Run G3R/g3r_floor.py and g3r_floor_when.py. Report the H-R5 counts per arm and the exclusion row in a footnote.
- **Related claims.** C71, C72

### B36. [minor] G3R-F3: Actuation lag of switched law plans: real and pre-registered, with no measurable bias; the critic's proposed mechanism is not supported; the 30-s update period and the R3 'no P kick' rule are missing from the paper

Raised as minor; verification: not adversarially verified.

#### G3R-F3 (R3 G3R, minor, methodology-disclosure): Actuation lag of switched law plans: real and pre-registered, with no measurable bias; the critic's proposed mechanism is not supported; the 30-s update period and the R3 'no P kick' rule are missing from the paper

- **Description.** Constant-rate plans set q at the switch tick. Law plans keep the previous rate until the next tick of the 30-s grid anchored at t = 40 s. The PI P term is set to zero at a switched plan's first update and first acts at the second. Measured lag L (switch to first update): uniform 1-29 s, median 15 s, mean 15.7 s in P1b (every cell and arm), mean 14.4 s in C1. For q2000 the 'previous rate' is N = f10_8's current rate (median 1625 veh/h), not 1800. Every always-on law (FB, PI, AD, and N at 2000) updates on the same grid, so the lag exists only relative to constant-rate plans, not relative to the L0 law arms. Bias test: law plans' first rate cut below the pre-switch rate comes a median 40-190 s after the switch, and at the last pre-switch update n < n_crit in 89-92 % of seeds (62 % for p70_40_8_e4). An immediate update would therefore mostly have raised q. The response is limited by what the detector sees, not by the grid. Per-seed gains do not depend on L in any consistent way (Spearman -0.22 to +0.27). N, which never switches, itself shows +0.14 to +0.25, so L only tracks noise in how the incident unfolds. The R3 suppression matters most for slow_q2000's IP (K_P = 70). There the suppressed P term is a median -140 veh/h, and with it the first update would be a net cut in 62/93 seeds; this works against IP (conservative for S1b). Critic's hypothesis: every delay level d in {30, 60, 120, 240} is a multiple of 30 s, so the law's first update moves by exactly d in 100 % of switched seeds in all four cells. The lag cannot absorb detection delay. d* by plan family: constant (slow_q1600) 2.6 s (an interpolation, see S23-F3); PI laws 120.4 s (slow_q2000), > 240 s (block_q1600), never ahead (block_q2000). There is only one constant plan, so family and cell cannot be separated.
- **Evidence.**
  - v5b/p1b/meters.py@93ba655:74-75 (const sets q at once), :76-80 (fb/pi keep q; pi n_prev = None), :110 (dn = 0 at first update), :119-126 (30-s grid from first control tick); v5b/p1b/episode.py@93ba655:194-200 set_law before meter.step at the same tick; p1b_addendum.md:71 (R3: grid carries over, n(k-1) = n(k))
  - G3R/g3r_lag.out: L median 15.0 mean 15.7 min 1 max 29 for every switched arm and d; formula check True; 'exact shift in 100, not in 0' (71 at d = 240) for all four cells
  - G3R/g3r_lag2.out: first cut after switch, median: ID slow1600 74 s, ID block1600 86 s, IP block1600 182 s (C1 189 s), ID slow2000 78 s, IP slow2000 40 s, block2000 119 s; n < n_crit at the last pre-switch update 89/100, 89/100, 92/100, 91/100, 62/100, 91/100
  - G3R/g3r_pkick.out: suppressed P term median -40 veh/h (K_P = 20), -140 veh/h for p70_40_8_e4 (net cut in 62/93 seeds with it)
  - G3R/g3r_lag.out per-seed Spearman(L, gain): IP vs PI -0.06 / -0.05 / +0.04 / -0.22; ID vs N -0.01 / +0.06 / -0.04 / +0.27; N delay +0.15 / +0.14 / +0.14 / +0.25
  - p1b_result.json eval.S3.*.d_star (grid [0, 30, 60, 120, 240]; slow_q1600 M_PI 7.81 -> -81.93); tune.arms (IP slow1600 c1000+back; others PI laws; N q2000 = f10_8)
  - paper.qmd:110,118: no update period, no R3 rule; line 118 'detection is perfect in the main rows'
- **Failure scenario.** A reader takes 'detection is perfect' to mean the switched law acts at onset; in fact it acts 1-29 s later, and its P term 31-59 s later. A reader might also accept the critic's story that the lag explains why law plans tolerate delay. The data show neither a bias nor that mechanism.
- **How to test.** Run G3R/g3r_lag.py, g3r_lag2.py and g3r_pkick.py. In the paper, add a half-sentence: 'all laws update every 30 s on a grid fixed at control start; a switched law keeps the current rate until its next update, and a switched PI law starts without a proportional kick (pre-registered)'.
- **Related claims.** C47, C73, C79, C80, C81, C86, C14

### B37. [minor] G3R-F4: C1's tolerance of detection delay comes from a slow-acting plan, not from robust use of type information

Raised as minor; verification: not adversarially verified.

#### G3R-F4 (R3 G3R, minor, interpretation): C1's tolerance of detection delay comes from a slow-acting plan, not from robust use of type information

- **Description.** In block_q1600, the IP law (n_crit 16, K_I 20) first raises q above N's 1800 in 96-98 % of seeds. It cuts the rate below the pre-switch rate only a median 182-189 s after onset, and in 21-24 % of seeds not before clearance. A later switch makes it cut sooner: the first cut after onset is a median 189 / 160 / 144 / 146 s at d = 0 / 30 / 60 / 120 s in C1, and 182 / 149 / 135 / 146 s in P1b. The traffic state, not the switch time, sets the plan's action. So a switch up to about 2 minutes late changes nothing measurable (C1 IP(d) vs IP(0): -0.7 % [-2.4, 0.7], +0.2 % [-1.2, 1.8], -1.5 % [-3.7, 0.5]). Contrast slow_q2000 (p70_40_8_e4): its first cut moves with d (40 / 50 / 76 / 135 s), and d* is 120 s. The slow_q1600 constant plan fails by tipping: at d = 30 / 60 / 120 s, 36 / 72 / 90 of 100 seeds end within 0.5 s/veh of N. Line 187 ('the lead held with detection delays of 30-120 s') is true. But a reader may take it as evidence that incident-type information tolerates late detection. Here it reflects a plan whose gain comes from not over-holding during the crawl, in line with the round-2 mechanism finding.
- **Evidence.**
  - G3R/g3r_cut_vs_d.out (first cut after onset by d, P1b and C1)
  - G3R/g3r_lag.out: 'first IP update raises q above 1800 in 96/100 seeds' (C1); P1b block_q1600 d = 0 '1st update q up 98 / down 2'; C1 d-row rel values
  - G3R/g3r_lag2.out: 'cut before clearance in 76/100' (P1b), '79/100' (C1)
  - G3R/g3r_slow1600_d.out: |N - IP| < 0.5 s/veh in 7 / 36 / 72 / 90 seeds at d = 0 / 30 / 60 / 120
  - paper.qmd:187, :197
- **Failure scenario.** A reader generalises 'C1 is robust to 30-120 s detection delay' to incident-aware metering. The result holds because this plan does almost nothing in the first ~3 minutes; a faster plan, like the one in slow_q2000, loses its lead with delay.
- **How to test.** Run G3R/g3r_cut_vs_d.py. Add one clause at line 187: 'because the type plan's feedback cuts the rate only about 3 min after onset, a switch up to 2 min late changes little'.
- **Related claims.** C73, C79, C80, C86

### B38. [minor] G4-F5: Cycle formula written with the demand q; the code uses the commanded rate

Raised as minor; verification: not adversarially verified.

#### G4-F5 (R2 G4, minor, discrepancy): Cycle formula written with the demand q; the code uses the commanded rate

- **Description.** Line 110 writes c(q) = max(11, 28,800/q), where q is the demand defined in the same paragraph and at line 93. The code computes cycle_s(self.q), where self.q is the commanded rate of the law, clipped to [200, 2618]. 'Two vehicles per lane per green' is the nominal design: 3.5-7.8 % of crossings happen in amber, and realised discharge is below the commanded rate.
- **Evidence.**
  - meters.py@93ba655:37-38, :114-115, :57, :75, :87-88
  - paper.qmd:93, :110
  - G4/clock_check.out, G4/approach_cross_p1b.out
- **Failure scenario.** A reader rebuilds a signal whose cycle follows the demand (18 s at 1600 veh/h, 14.4 s at 2000 veh/h) for every arm. No feedback law could then change the release rate.
- **How to test.** Rename the variable to the commanded rate r: c(r) = max(11, 28,800/r).
- **Related claims.** C35, C22

### B39. [minor] G5-F4: c* '> 180' in three cells is vacuous: the stay plans cannot be affected by a clearance delay

Raised as minor; verification: not adversarially verified.

#### G5-F4 (R2 G5, minor, wording): c* '> 180' in three cells is vacuous: the stay plans cannot be affected by a clearance delay

- **Description.** In slow_q2000, block_q1600 and block_q2000, IP is a stay plan. canon_sw maps the c=60 and c=180 runs to the c=0 run: 0/100 distinct keys, and M is flat across c. clearance_delay_applies is False in the JSON. p1b_result.md shows '> 180' (which reads as a tolerance) and 'never ahead (PI)'. The P1 note wrote 'n/a (stay plan)'.
- **Evidence.**
  - analysis.py@93ba655:76-89, 567
  - p1b_result.md:25
  - p1_result.md:52
  - g5_recompute_20261019.log (c-rows distinct from IP run: 0)
- **Failure scenario.** '> 180 s' is cited as evidence of robustness to late clearance detection, but no clearance-delayed run exists in those cells.
- **How to test.** Read clearance_delay_applies and c_star.per_arm.M in the JSON (M is constant across c).
- **Related claims.** C79

### B40. [minor] G5-F5: 'Detection delay' means onset delay only; Table I overstates which information the tuned plans use

Raised as minor; verification: not adversarially verified.

#### G5-F5 (R2 G5, minor, wording): 'Detection delay' means onset delay only; Table I overstates which information the tuned plans use

- **Description.** In every d row, clearance is detected exactly: the slow_q1600 back plan returns at t_off in 100/100 runs for d <= 120. Only 1 of 4 IP plans (slow_q1600) and none of the ID plans (f40_10 and p20_20_14_e4, both stay plans) ever use clearance, and the C1 plan never returns. Table I says IP uses 'onset, clearance and type' and ID uses 'onset (and clearance)'. That describes what is available, not what the tuned plans use. Lines 75, 85, 197 and Fig. 3 should say 'onset detection delay'. They could also state that 3 of 4 IP plans need no clearance detection at all, which is a real robustness property.
- **Evidence.**
  - meters.py@93ba655:203-217
  - p1b_result.json tune.arms (ID, IP)
  - g5_schedules.log
  - paper.qmd:100-101, 131-132, 75, 85, 197; fig_c1_robust.py rows 'Detection +d s'
- **Failure scenario.** A reader assumes the d rows also delay clearance detection, or that the tuned plans depend on clearance detection.
- **How to test.** Read t_back in the raw d-row runs; read tune.arms in the JSON.
- **Related claims.** C14, C80, C73

### B41. [minor] G8-F6: 'Feedback laws ... apply directly' sits beside a source that reports calibration and auto-tuning were needed

Raised as minor; verification: not adversarially verified.

#### G8-F6 (R2 G8, minor, wording): 'Feedback laws ... apply directly' sits beside a source that reports calibration and auto-tuning were needed

- **Description.** The Tympakianaki 2014 abstract says 'some calibration of the regulator's parameters may be necessary' and uses a learning/adaptive fine-tuning algorithm. It also uses green-red signals, not green-amber-red. Spiliopoulou 2010 (toll plaza) reports low tuning needs. 'Apply directly' is thus fair for transferring the law structure, but not for its parameters. This overlaps LIT-F4/C15.
- **Evidence.**
  - G8/dl_tymp/wzs_47333.html (abstract)
  - Spiliopoulou2010 abstract: 'little sensitive to various settings'
  - paper.qmd:81
- **Failure scenario.** Readers infer that ramp-metering gains transfer unchanged to mainline signals.
- **How to test.** Reword, e.g.: 'transfer with retuning [Tympakianaki2014]'.
- **Related claims.** C15, C44

### B42. [minor] HEADLINE-F3: Printed S1 intervals are rel CIs, not the decision-rule diff CIs

Raised as minor; verification: not adversarially verified.

#### HEADLINE-F3 (R1 HEADLINE, minor, wording): The intervals printed for S1 are rel CIs, but the protocol and the decision rule use the CI of median(r - t); the paper does not say which is shown

- **Description.** Meaning: Protocol §5 (p1_incident_information.md:86) defines the CI as the percentile bootstrap of median(r - t), and S1(a) is decided on its lower bound (stats.py:79 rule_cell uses diff_ci). The brackets printed at paper.qmd:155 ([5.8, 16.7], [8.8, 31.4], [8.9, 31.6]) are the rel_ci: percentiles of median(d*)/median(r*) (stats.py:48-64). For C1 the paper gives both, which is clear. For S1 the reader cannot tell. The two differ, e.g. block_q1600 IP vs ID: rel CI [8.8, 31.4] against the diff CI scaled by median(ID), [8.3, 32.9]. Verdicts are unaffected, because both lower bounds are > 0 wherever the text says the interval is above zero.
- **Evidence.**
  - docs/research/protocols/p1_incident_information.md:86, :176 (I12)
  - v5b/p1/stats.py:48-64, :79@93ba655
  - paper.qmd:145, :155
- **Failure scenario.** A reader converts [8.8, 31.4] % back to s/veh and expects it to match the decision CI. It does not match exactly.
- **How to test.** Compare relCI_pct and scaledCI_pct in /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/HEADLINE/headline_out.json. Fix: add one sentence, e.g. 'brackets: percentile CI of rel; decisions use the CI of median(r - t)'.
- **Related claims.** paper.qmd:145, paper.qmd:155

### B43. [minor] HEADLINE-F4: Bootstrap Monte Carlo error of 0.99375 bounds exceeds printed precision

Raised as minor; verification: not adversarially verified.

#### HEADLINE-F4 (R1 HEADLINE, minor, statistics): Bootstrap Monte Carlo noise of the 0.99375 bounds is about ±1 point at B = 20,000, so one-decimal precision is overstated

- **Description.** Meaning: At level 0.99375 each tail holds only about 62 of the 20,000 draws, so the bounds move when the bootstrap seed changes. Across 50 independent bootstrap seeds, the block_q1600 IP-vs-ID lower bound ranges 7.1-9.0 (median 8.5). The reported 8.8 comes from the fixed repo seed 20261019, which my own code reproduces exactly, and lies near the top of that range. The IP-vs-PI bounds range 8.9-9.3 and 31.1-31.6, and the C1 diff-CI upper bound ranges 63.3-66.1 s. No verdict depends on this: every diff-CI lower bound stays clearly above 0 (S1b block_q1600 ≥ 16.7 s, C1 ≥ 16.5 s). The seed was fixed before data (P1b: v5b/p1/stats.py:15; C1: confirm_c1.py:56@e7dd561, committed 21:16, 11 min before the C1 sentinel).
- **Evidence.**
  - /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/HEADLINE/boot_sensitivity.py output
  - /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/HEADLINE/repo_seed_replay.py output (exact match to the reported values)
- **Failure scenario.** An independent re-analysis with another bootstrap seed reports 22.0 % [7.6, 31.3] and appears to contradict the paper.
- **How to test.** Re-run boot_sensitivity.py. Either state the bootstrap seed, or round the S1 bounds to integers, or use B = 200,000 for the Bonferroni-level intervals.
- **Related claims.** paper.qmd:155, paper.qmd:187

#### S1-F5 (R1 S1, minor, statistics): Monte Carlo error of 0.99375-level bounds exceeds the printed precision

- **Description.** With B = 20,000, each tail at the 0.99375 level holds about 62 draws. Over 20 bootstrap RNG seeds, the block_q1600 IP vs ID lower bound ranges from 7.3 to 8.9 % (the paper prints 8.8), and slow_q2000 IP vs PI ranges from −4.0 to −2.6. No verdict changes: every decisive bound keeps its sign in all 20 seeds, and the diff lower bounds stay at or above 17 s/veh.
- **Evidence.**
  - robustness.py section (1)
  - s1_recompute.py alt seeds 1, 777, 424242
- **Failure scenario.** Someone re-running with another RNG seed reports 'different' CIs and questions reproducibility.
- **How to test.** Report the bootstrap seed and the Monte Carlo spread, or use B ≥ 200,000 for the S1-level rows.
- **Related claims.** C66, C67, C56

### B44. [minor] HEADLINE-F5: 'Same result excluding invalid runs' is vacuous: zero invalid runs

Raised as minor; verification: not adversarially verified.

#### HEADLINE-F5 (R1 HEADLINE, minor, wording): 'Same result when seeds with invalid runs are excluded' suggests exclusions, but there were none; 'valid' ignores emergency-braking and stuck-vehicle warnings

- **Description.** Meaning: A run is invalid only if it did not drain, if n_trips != generated, or if health == FAIL (v5b/p1b/episode.py:255@93ba655). All 255,182 P1b evaluation runs and all 1,100 C1 runs are valid, so the valid-only view is identical to the all-seeds view by construction. The sentence at paper.qmd:187 implies that some seeds were dropped. The 'valid' flag also passes runs with health WARN codes. Among the headline rows (P1b, 4 cells), H-R4b (emergency-braking warnings) appears in 1,082 of 1,100 runs, H-R5 (vehicles waiting long) in 40, and H-R2 (old pending vehicle) in 162. Per row, emergency_warnings > 0 occurs in 95-100 % of runs, emergency_stops > 0 in 9-21 %, and emergency_meter > 0 in 16-28 % (headline IP and PI rows, P1b and C1).
- **Evidence.**
  - v5b/p1b/episode.py:254-255, :271@93ba655
  - /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/HEADLINE/pairing_check.py output (health codes per cell)
  - /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/HEADLINE/eb_check.py output
  - run record ~/work/phd/v5b1_runs/p1b/v108/result.json eval.invalid_runs = 0; p1b_c1/v114/result.json invalid_runs = 0
- **Failure scenario.** A reader believes that the robustness to invalid runs was actually tested, when the second view is a copy of the first.
- **How to test.** Reword as 'no run was invalid (drained, all trips completed, no FAIL), so both views coincide'. The safety auditor should check how the paper's 87 % -> 12.8 % emergency-stop figure is defined against these fields.
- **Related claims.** paper.qmd:187

#### C1-F4 (R1 C1, minor, wording): Invalid-run exclusion view is vacuous (0 invalid runs)

- **Description.** All 1,100 C1 runs are valid (drained, all trips recorded, health not FAIL), with 0 teleports. The 'valid only' view equals the 'all seeds' view by construction. The paper's wording suggests that an exclusion was made.
- **Evidence.**
  - result.json invalid_runs 0, c1.C1.n_invalid_seeds 0
  - c1_recompute.py integrity block: invalid=0 in all 11 rows
- **Failure scenario.** Reader infers that some C1 runs failed and that the result survived their removal.
- **How to test.** Count valid flags in the raw runs (c1_recompute.py).
- **Related claims.** C72

#### PROV-F10 (R1 PROV, info, wording): 'Same result when seeds with invalid runs are excluded' is trivial: C1 had 0 invalid runs

- **Description.** C1 recorded invalid_runs=0 (and P1b had 0 invalid among 344,852 runs), so both views are identical by construction. The sentence suggests a robustness check that removed seeds.
- **Evidence.**
  - p1b_c1/v114/result.json invalid_runs 0
  - scratch scan_runs.py bad={} for p1b/v108 and p1b_c1/v114
- **Failure scenario.** A reader over-weights a check that removed nothing.
- **How to test.** jq .invalid_runs on the C1 result.json
- **Related claims.** C70

#### REPRO-F8 (R1 REPRO, minor, wording): 'Same result when seeds with invalid runs are excluded' (line 187) holds trivially

- **Description.** C1 had 0 invalid runs (n_invalid_seeds = 0), so the valid-only view is the same data. The sentence suggests that some seeds were excluded.
- **Evidence.**
  - p1b_c1_result.json c1.C1.n_invalid_seeds = 0; invalid_runs = 0
  - scratch/fig3_recompute.py (all 1,200 files valid)
- **Failure scenario.** Readers infer that some runs were invalid.
- **How to test.** jq .c1.C1.n_invalid_seeds on the result JSON.
- **Related claims.** C75

### B45. [minor] HEADLINE-F6: 'Reduced median delay by 16.2 %' is not the change in the median

Raised as minor; verification: not adversarially verified.

#### HEADLINE-F6 (R1 HEADLINE, minor, wording): 'Reduced median delay by 16.2 %' is not literally the change in median delay; for S1b slow_q2000 the arm medians differ by only 6.0 %

- **Description.** Meaning: rel = median of the paired differences / median of the reference. This is not the relative change of the arm's median delay. C1: the median delay goes from 254.7 to 210.6 s, a 17.3 % cut, while rel = 16.2 %. The gap is larger in S1b slow_q2000: the paired rel is 11.8 %, but the arm medians differ by only 6.0 % (375.7 vs 353.2 s), and the mean version is 9.1 %, below the 10 % threshold. The pre-registered metric is the paired median, and paper.qmd:145 defines it, but the sentence at :187 ('reduced median delay ... by 16.2 %') describes it wrongly.
- **Evidence.**
  - /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/HEADLINE/pairing_check.py output (paired-median rel, mean rel, arm-median rel)
  - paper.qmd:187
- **Failure scenario.** A reader computes the gain from the figure's arm medians (Fig. 1 plots median delay per arm) and finds 6 % for slow_q2000, not 11.8 %.
- **How to test.** Reword as 'the median paired delay difference was 16.2 % of PI's median delay', or report both numbers.
- **Related claims.** paper.qmd:187, paper.qmd:155, paper.qmd:160 Fig. 1 caption

#### C1-F2 (R1 C1, minor, wording): 'Reduced median delay by 16.2 %' is not the reduction of the median

- **Description.** The 16.2 % (41.4 s/veh) is the median of the per-seed differences divided by PI's median. The reduction of the median delay itself is (254.7 - 210.6)/254.7 = 17.3 % (44.1 s/veh). The definition is at line 145, but the sentence at line 187 describes a different quantity.
- **Evidence.**
  - c1_recompute.py output: rel of medians 0.1732; median(PI) 254.68, median(IP) 210.57; median paired diff 41.37
  - papers/paper_1/paper.qmd:145, 187
- **Failure scenario.** A reader recomputes the change of medians from reported arm medians and gets 17.3 %, a mismatch.
- **How to test.** Run c1_recompute.py and read the 'rel of medians' line.
- **Related claims.** C71

#### FU2-1-F4 (R2 FU2, minor, wording): C1 sentence calls the paired statistic a 'reduction of median delay' (16.2 % / 41.4 s vs 17.3 % / 44.1 s)

- **Description.** This duplicates HEADLINE-F6 / C1-F2, and I confirm it. The PI median is 254.68 and the IP median 210.57, a change of 17.32 % (44.11 s/veh). The 16.25 % and 41.37 s/veh are the median of paired differences, divided by PI's median for the percentage. The mismatch understates the gain, and C1 also holds on window TTT (11.7 %, LCB 1.58 veh.h) and full TTT (13.9 %).
- **Evidence.**
  - FU2-1/c1_indep.out
  - paper.qmd:145,187
- **Failure scenario.** A reader checks the arm medians and finds 17.3 %, not 16.2 %. It looks like an error, although the paper's number is correct for its own definition.
- **How to test.** Run FU2-1/c1_indep.py. Rewording: 'the median paired delay difference was 16.2 % of PI's median (41.4 s/veh)'.
- **Related claims.** C71, FU1-C7

### B46. [minor] LIT-F10: Bias results concern expectations; paper reports medians

Raised as minor; verification: not adversarially verified.

#### LIT-F10 (R1 LIT, minor, statistics): The bias results cited for the bracket concern expectations; the paper reports medians

- **Description.** OR_in takes the best action on each run, so it is never worse than the truly best action scored on that same run. That ordering survives medians. ORX_R is low only in expectation for each seed (van Hasselt's lemma; Smith & Winkler): E[D(a*)] >= min_a E[D(a)]. It is not ordered run by run, so the median of ORX gains is not guaranteed to be a lower bound on the median per-incident gain. Line 141's 'low in expectation' is accurate per seed, but the S2 brackets in Table II are on the scale rel = median(r - t)/median(r).
- **Evidence.**
  - van Hasselt 2010 §2 (/tmp/.../LIT/vanhasselt2010.txt lines 320-336)
  - paper.qmd:141 and :145
- **Failure scenario.** If the ORX gain distribution is skewed, its median can exceed the median of the true per-incident gain, and the 'lower bound' wording fails.
- **How to test.** Recompute the S2 brackets on the mean scale from the raw per-seed delays and check that ORX(mean) <= OR_in(mean) and that the ordering matches the median scale. Or add a sentence that the bounds hold in expectation.
- **Related claims.** C10, C21

#### G8-F8 (R2 G8, info, statistics): Smith & Winkler 2006 read in full: the curse is a statement about expectations

- **Description.** The author-hosted full text supports lines 69, 89 and 141. Its abstract says the chosen alternative's value is expected to be below its estimate 'even if the value estimates are unbiased'. Proposition 1 states E[mu_i* - V_i*] <= 0 under conditional unbiasedness, which is an expectation statement and supports the LIT-F10 caveat about medians. A 2007 author correction changes the Fig. 3 values only; the paper uses none of them.
- **Evidence.**
  - G8/smith2006.txt:21, :325-334
  - G8/smith2006_correction.txt
- **Failure scenario.** None for the citation. The median-versus-expectation gap (LIT-F10) remains.
- **How to test.** Optionally add 'in expectation' where the bracket is described.
- **Related claims.** C10, C21

### B47. [minor] LIT-F11: Cited mainline metering engages only in near-stopped traffic

Raised as minor; verification: not adversarially verified.

#### LIT-F11 (R1 LIT, minor, hidden-assumption): The cited mainline-metering practice engages only in near-stopped traffic; the paper meters free-flowing traffic

- **Description.** Ghiasi 2018 activates the mainline signal only once traffic on all lanes has almost stopped, 'for safety reasons'. Hale 2020 calls mainline metering 'challenging to implement'. The paper's meter cycles on traffic at 23 m/s from the start of control, reduced by amber only to a 12.8 % share of runs with an emergency stop. The Discussion section is empty, so this realism gap is not stated anywhere.
- **Evidence.**
  - Ghiasi 2018 abstract
  - FHWA-HRT-20-008 landing page
  - paper.qmd:175, :194
- **Failure scenario.** A reviewer asks whether such a meter is deployable and the paper has no answer.
- **How to test.** State it in Discussion/Limitations. A sensitivity run that activates the meter only below a speed threshold would show its effect.
- **Related claims.** C03, C15

### B48. [minor] LIT-F12: C01 opening sentence uncited

Raised as minor; verification: not adversarially verified.

#### LIT-F12 (R1 LIT, minor, missing-evidence): C01 still has no source; two verified candidates exist

- **Description.** The first sentence of the Introduction is uncited. Candidates with verified metadata and abstracts: Knoop, Hoogendoorn & van Zuylen 2008, TRR 2071:19-25, doi:10.3141/2071-03 (remaining-lane capacity about 50 % lower at incidents); Skabardonis, Varaiya & Petty 2003, TRR 1856:118-124, doi:10.3141/1856-12 (incident delay 13-30 % of peak congestion delay).
- **Evidence.**
  - /tmp/.../LIT/crossref_candidates_output.txt
  - OpenAlex abstracts
- **Failure scenario.** The draft is submitted with an unsourced motivating claim.
- **How to test.** Read both full texts and cite.
- **Related claims.** C01

### B49. [minor] LIT-F13: C07 wording mismatches cited methods

Raised as minor; verification: not adversarially verified.

#### LIT-F13 (R1 LIT, minor, wording): The C07 wording does not match how two of the three cited methods work, and its baseline clause is unverified

- **Description.** Sheu 2007 (GSPRT) and Wu 2014 (adaptive neural network) detect incidents themselves rather than act 'when an incident is reported'. 'Usually compared with no control or with a fixed-parameter controller' could not be checked from the abstracts: Dabiri says 'other existing approach', Wu gives about 25 % against an unnamed baseline, and Sheu reports 'feasibility'.
- **Evidence.**
  - Sheu2007, Wu2014 and Dabiri2014 abstracts (/tmp/.../LIT/dl_meta, dl_misc/chalmers_211200.html)
- **Failure scenario.** An author of one of these works objects that its baselines are misdescribed.
- **How to test.** Read the evaluation sections of the three papers, or soften the clause.
- **Related claims.** C07

#### G8-F2 (R2 G8, minor, citation): Dabiri 2014 is continuous gain scheduling on estimated incident magnitudes, not switching on an incident flag

- **Description.** Line 81 says incident-scheduled controllers 'switch plans or parameters when an incident flag arrives [Dabiri2014]'. In the full text, the state-feedback gain is a function of the real-valued incident parameters alpha and beta. These are assumed 'real-time measured (or estimated)', and there is no plan library. The controller needs the incident's magnitude, which is more than presence or type. It behaves like a switch only because the case study steps alpha and beta at t = 35 min. Its results are shown only as figures, against no control, a nominal (fixed-gain) LQR and a scheduled LQR.
- **Evidence.**
  - G8/dabiri2014.txt:23 (p. 11338), :168-170 (p. 11340), :275-281 Remark 3, :349-353 and :382-397 (pp. 11341-11342)
- **Failure scenario.** A reviewer familiar with LPV/gain-scheduled control says the work is mis-described, and that it uses more incident information than the paper's IP rung.
- **How to test.** Reword, e.g.: 'gain-scheduled controllers adapt their gains to estimated incident parameters [Dabiri2014]'.
- **Related claims.** C17, C07

#### G8-F3 (R2 G8, minor, wording): Sheu 2007 detects incidents itself; the baseline clause now holds for 2 of the 3 cited works

- **Description.** Line 65 says incident-responsive ramp metering acts 'when an incident is reported'. In the Sheu full text, the method identifies incident-induced congestion patterns itself by M-GSPRT, so nothing is reported to it; Wu's abstract describes an adaptive neural network that recognises the incident. The baseline clause ('usually compared with no control or with a fixed-parameter controller') is supported in full text for Sheu (pretimed and no control, plus its own isolated variant; it explicitly excludes published ramp-control models) and for Dabiri (no control and nominal LQR). Wu's baseline stays unknown. This updates LIT-F13.
- **Evidence.**
  - G8/sheu2007.txt:61-63, :87 (pp. 359-360), :1357-1374 (p. 366)
  - G8/dabiri2014.txt:382-397, :432
  - LIT/dl_meta/Wu2014.json abstract
- **Failure scenario.** An author of Sheu 2007 objects that the method needs no incident report.
- **How to test.** Reword as 'responds to detected or reported incidents'. Keep the baseline clause, citing Sheu and Dabiri for it, or say 'often'.
- **Related claims.** C07

### B50. [minor] LIT-F2: Carlson2010 is optimal control, not the same feedback laws

Raised as major; verification: reproduce: CONFIRMED/minor, defend: CONFIRMED/minor.

#### LIT-F2 (R1 LIT, major, citation): Carlson2010 is an optimal-control paper, not 'the same laws'

- **Description.** Line 65 says ALINEA and PI-ALINEA-type laws 'drive mainstream traffic flow control with variable speed limits [Carlson2010; Carlson2011]'. Carlson et al. 2010 applies a model-based optimal-control tool. The feedback MTFC that is combined with PI-ALINEA, and used as the benchmark by Frejo 2021b, is Carlson, Papamichail & Papageorgiou 2014, TR-C 46:209-221, doi:10.1016/j.trc.2014.05.017. Carlson2011's abstract says only 'simple local MTFC feedback controller'.
- **Evidence.**
  - EPFL Infoscience record 154946 (Carlson 2010 abstract)
  - Frejo 2021b AAM, refs [2] and [5] and §III.A (/tmp/.../LIT/frejo2021b_raw.txt)
  - Crossref record of the 2014 paper (/tmp/.../LIT/crossref_candidates_output.txt)
- **Failure scenario.** A reviewer checks Carlson2010 and finds optimal control, so the 'same laws' sentence reads as a mis-citation.
- **How to test.** Read the Carlson 2011 and 2014 controller sections. Cite 2014 (and 2011 if its law is PI-type) for the feedback MTFC, and drop 2010 or move it to an 'optimal control' clause.
- **Related claims.** C05

#### G8-F5 (R2 G8, major, citation): LIT-F2 confirmed: Carlson2010 is optimal control; the feedback benchmark is Carlson 2014, which the paper does not cite

- **Description.** Carlson 2010's full abstract (EPFL REST) applies 'a ... software tool for optimal integrated motorway network traffic control'. Frejo 2021a, in full text, files it under 'Optimization-based controllers'. Carlson 2011 is a feedback MTFC (its abstract; Frejo 2021a describes feedback on downstream flow and bottleneck density), a PI-type controller, not ALINEA itself. The 'strong benchmark' in Frejo 2021b is MTFC + PI-ALINEA from Carlson, Papamichail & Papageorgiou 2014 (TR-C 46:209-221), which is absent from the bib. The full texts of Carlson 2011 and 2014 were not reachable.
- **Evidence.**
  - G8/dl_epfl/item_1db1e590-9717-4f8e-a196-e355142df3c2.json (Carlson 2010 abstract)
  - LIT/frejo2021a_raw.txt:104-108, :145-155
  - LIT/frejo2021b_raw.txt:128, :1252, :1921
- **Failure scenario.** A reviewer opens Carlson2010, finds optimal control, and reads 'the same laws' as a mis-citation.
- **How to test.** Cite Carlson 2011 and 2014 for feedback MTFC, and drop Carlson 2010 or move it to an optimal-control clause. Say 'PI-type feedback laws' rather than 'the same laws'.
- **Related claims.** C05

#### Verifier R2 reproduce: CONFIRMED / minor

I confirmed the core fact from primary evidence. The paper (paper.qmd:65 at HEAD 1e5e8d7, file clean) says "The same laws [ALINEA, PI-ALINEA] drive mainstream traffic flow control with variable speed limits [@Carlson2010; @Carlson2011]". The bib entry Carlson2010 is TR-C 18(2):193-212, "Optimal Mainstream Traffic Flow Control of Large-Scale Motorway Networks". It is an optimal-control paper, not a feedback law (basis: direct observation of the title and Crossref record; derived from the Carlson 2011 abstract). The Carlson 2011 abstract (OpenAlex text, stored locally) describes the earlier MTFC work as "sophisticated optimal control methods". It says this paper designs only "a simple local MTFC feedback controller", and it does not say the law is integral or PI. That quote reproduces exactly. Frejo 2021b (AAM, my own pdftotext extraction) cites the MTFC + PI-ALINEA benchmark as ref [2]. Ref [2] is Carlson, Papamichail & Papageorgiou 2014, TR-C 46:209-221. Frejo 2021b also says MTFC+PI-ALINEA "is based on a PI structure". The paper's bib does not contain the 2014 paper (0 matches for trc.2014.05.017). Frejo 2021a lists MTFC [6] = Carlson 2011 as a feedback VSL strategy. It lists Carlson's other 2010 paper ([9], Transp. Sci.) among "optimization-based controllers". The mis-citation comes from the Argon v1 literature draft ("These local feedback laws have been successfully applied ... MTFC via variable speed limits [6], [7], [19]", where [6] = Carlson 2010 TR-C).

Small corrections to the finding's evidence. (1) Frejo 2021b ref [5] is a different 2010 Carlson paper (Transportation Science 44(2):238-253), not the TR-C paper in the bib. It shows only that Carlson's 2010 line is optimal control; it is not a direct statement about the cited paper. (2) The EPFL Infoscience abstract of Carlson 2010 is not stored locally (Crossref and OpenAlex abstracts are empty), and web access was not allowed. So I could not reproduce that one evidence item. The title and the 2011 abstract are enough for the core fact. (3) I could not check locally whether the Carlson 2011 law is integral/PI-type. My belief that it is PI-type is an assumption, not verified.

Severity: I lowered it to minor. The sentence as a whole is broadly supported: Carlson2011 supports feedback MTFC with VSL, and Frejo2021b in the same sentence supports a PI-based MTFC+PI-ALINEA benchmark. The defect is one wrong reference in a background sentence. The fix is a citation swap: drop Carlson2010 or move it to an "optimal control" clause, and add Carlson 2014. No result or headline is affected. If a strict reading is used ("statement unsupported as written for one of its two citations"), major is also defensible.

Checks: Read round2_input.json groups['LIT-F2'] (finding and claim C05); /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/LIT-F2-reproduce/check_litf2.sh (output check_litf2_output.txt in the same dir): paper line 65, bib titles, Carlson 2014 absence, Carlson 2010/2011 abstracts, Frejo 2021a/b citations, Argon origin; Own pdftotext extraction of the Frejo 2021a/2021b AAM PDFs (sha256 b5ac30e5..., 8627e807...) to frejo2021a_own.txt and frejo2021b_own.txt in my scratch dir; read §II.A.1, the optimal-control paragraph, the PI-structure sentence and the reference lists; pdftotext of papers/refs_papers/1-s2.0-S0968090X07000873-main.pdf (Papageorgiou 2008): no Carlson mention (not relevant to this finding); grep -rn carlson over the repo docs (prior_art_P1_P2.md:58, Argon v0/v1, port_map_v0.md:364) to trace where the sentence came from; Not done: no web access, so the Carlson 2010 abstract/full text and the Carlson 2011 controller equations (PI vs I type) were not checked

#### Verifier R2 defend: CONFIRMED / minor

The problem survives my best defence: the citation is wrong. My defence does lower the severity.

What I tried, and what I found:

1. Can Carlson2010 be read as a citation for the MTFC idea only? No, not as the sentence is written. Line 65 says "The same laws drive mainstream traffic flow control with variable speed limits [@Carlson2010; @Carlson2011]". Its subject is the laws: ALINEA and PI-ALINEA. Carlson2010 in references.bib is "Optimal Mainstream Traffic Flow Control of Large-Scale Motorway Networks" (TR-C 18(2)). The title alone shows it is an optimal-control paper, not a feedback law. No other place in the paper cites Carlson, and no other text discloses or qualifies this. So the mis-citation stands.

2. Is the substance of the sentence true? Yes, in the literature it is true (basis: direct observation of the sources).
- Carlson2011's abstract (OpenAlex record) says: "A simple local MTFC feedback controller is designed... relies only on readily available real-time measurements".
- Frejo 2021a (my own pdftotext extraction) describes the MTFC of [6] = Carlson 2011 as "a local VSL controller with feedback of the flow downstream of the VSL application area and of the density at the bottleneck area".
- Frejo 2021b is cited in the same sentence. It says "MTFC+PI-ALINEA is based on a PI structure". Its eq. (4) is the PI velocity-form law on the bottleneck density error, q̂t(k)=q̂t(k-1)+(KP+KI)eρ(k)-KP·eρ(k-1). That is the same form as PI-ALINEA. It attributes this law to its ref [2], which is Carlson, Papamichail & Papageorgiou 2014, TR-C 46:209-221. The paper does not cite this 2014 paper.
- Papageorgiou 2008 (local full text, §2.5) also lists variable speed limits as a device for the same feedback merging control. It calls this "on-going research", and the paper does not cite it at this sentence.

So the claim is not false. One of its two citations does not support it, and the main source for the MTFC benchmark (Carlson 2014) is missing.

3. Severity. No headline result, pre-registration statement or data statement depends on this Introduction sentence. The fix is a citation change: move Carlson2010 to an "optimal-control MTFC" clause, and add Carlson 2014 (plus Carlson 2011 if its law is PI-type) for the feedback law. This is closer to "wording, small inconsistency" than to "statement unsupported as written". So I lower it from major to minor. A reviewer who opens Carlson2010 would still ask for the fix. This is near the major/minor boundary.

Limits of my check:
- I could not read the full text of Carlson 2011 (no web access, no local PDF). So "same law" (PI-type, as in PI-ALINEA) is confirmed for Carlson 2011 only at the level "local feedback controller" (from its abstract and Frejo 2021a), not in its exact form.
- My statement that Carlson2010 uses no ALINEA-type feedback law rests on its title and the round-1 report of its abstract, not on its full text.

Process note (info only): the project rule says literature not read in full must be marked [VERIFY]. The Argon v1 table shows Carlson 2010 and 2011 were checked only by "Abstract & bibliographic record", and line 65 has no [VERIFY] marker.

Checks: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/LIT-F2-defend/check_defend.sh (output: check_defend_output.txt in the same dir). Checks: paper line 65, bib titles, count of Carlson citations in the paper, Frejo refs [2]/[5] and PI-structure lines, Frejo 2021a on Carlson 2011, Argon reading depth, Papageorgiou 2008 VSL passage.; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/LIT-F2-defend/abstracts.py (output: abstracts_output.txt in the same dir). Rebuilds the Carlson2010/2011 abstracts from the stored OpenAlex/Crossref metadata; Carlson2010 has no abstract stored.; Own pdftotext re-extraction of the Frejo 2021a/b PDFs (round-1 dl_frejo) into frejo2021a_own.txt and frejo2021b_own.txt in my scratch dir; grep for 'PI-ALINEA [2]', 'based on a PI', eq. (4) and ref list.; Own pdftotext of papers/refs_papers/1-s2.0-S0968090X07000873-main.pdf into pap2008.txt in my scratch dir; grep for VSL/MTFC/Carlson.; grep of the repo docs for Carlson (prior_art_P1_P2.md, Argon v0/v1 tables, gemini prompt, BASELINE_2), and git log -S for the sentence (introduced in 0d9b386, V124). No disclosure or qualification of Carlson2010 was found anywhere.

### B51. [minor] LIT-F4: Amber presented beside sources using green-red signals

Raised as minor; verification: not adversarially verified.

#### LIT-F4 (R1 LIT, minor, wording): 'Green, amber and red' is set beside sources that use green-red signals

- **Description.** Line 81 presents an amber phase as part of how a mainline meter works, in a sentence that cites Papageorgiou 2008 and Tympakianaki 2014. Both use green-red signals: 4-s green, red of at least 2 s, no amber. The 6 G + 3 A + >= 2 R cycle is the paper's own P1b choice (v5b/p1b/meters.py@93ba655:29-42).
- **Evidence.**
  - Papageorgiou 2008 §3.1 p. 543 and §4.1 p. 548
  - Tympakianaki 2014 abstract
  - v5b/p1b/meters.py@93ba655:29-42
- **Failure scenario.** A reader assumes the cited works modelled amber and that P1b's amber design follows them.
- **How to test.** Reword as 'Our meter uses ...', or cite a source that uses amber (for example Sun 2013, three-section heads, abstract verified).
- **Related claims.** C15

### B52. [minor] LIT-F5: Feedback laws use 0.5-s count snapshot, undisclosed

Raised as minor; verification: not adversarially verified.

#### LIT-F5 (R1 LIT, minor, hidden-assumption): FB, PI and AD use a 0.5-s snapshot of the vehicle count, not a period-averaged measurement (not disclosed)

- **Description.** Every law reads ls.edge.getLastStepVehicleNumber once per 30-s update, i.e. one 0.5-s simulation step (STEP_LENGTH = 0.5). ALINEA as published uses occupancy averaged over the ending control period; Papageorgiou 2008 also allows 'the latest measurements or estimates' of the vehicle number N. PI's proportional term differences two such snapshots. This is defensible, but line 118 says only 'downstream vehicle count'. It may add noise to the strongest baseline, PI, which is the reference arm of C1.
- **Evidence.**
  - v5b/p1b/episode.py@93ba655:147-150 read()
  - v5b/p1b/meters.py@93ba655:90-112
  - v5b/d1/plant.py@93ba655:22 STEP_LENGTH = 0.5
  - Papageorgiou 2008 §2.7.1 p. 540
- **Failure scenario.** If a 30-s-averaged count makes PI stronger, the C1 margin of IP over PI (16.2 %) shrinks.
- **How to test.** Re-tune PI (and FB) on the tuning seeds with the count averaged over the 60 half-second steps of each period. Compare tuned PI delay in block_q1600 with the snapshot version. This needs simulations, so it is out of scope for this audit.
- **Related claims.** C04, C16

### B53. [minor] LIT-F6: AD arm is the paper's own sign rule, not stated

Raised as minor; verification: not adversarially verified.

#### LIT-F6 (R1 LIT, minor, disclosure): The AD arm is the paper's own sign rule; the paper names AD-ALINEA but does not state the rule

- **Description.** AD runs n_hat <- clip(n_hat + eta * sgn(d phi) * sgn(d n), 4, 20) every 30 s, with eta in {0.5, 1, 2}, phi = network exits in the last 30 s and n = the edge-4 snapshot. This is a hill-climbing rule; the protocol says it is 'not its [AD-ALINEA's] estimator'. The paper says only 'in the spirit of AD-ALINEA', so readers cannot tell how simple this adaptive baseline is. The rule also combines an interval count (phi) with snapshot differences (n), so with noisy signs the set point may drift randomly. The T-AD tool check (median set-point movement 2-4 vehicles) shows only that it moves, not that it tracks capacity.
- **Evidence.**
  - v5b/p1b/meters.py@93ba655:91-103
  - v5b/p1/meters.py@93ba655:113-131 (identical at 85f7d34, 93ba655 and e7dd561; md5 bbb19039...)
  - docs/research/protocols/p1_incident_information.md:35
  - docs/research/results/p1b_summary.md:7-12 (T-AD med)
- **Failure scenario.** A reviewer assumes AD is AD-ALINEA, and the 'full set of tuned always-on controllers' claim overstates the adaptive baseline.
- **How to test.** State the rule in the Design section. From the raw runs' nhat_log, test whether n_hat moves in the direction of the incident's capacity change more often than chance.
- **Related claims.** C06, C17

### B54. [minor] LIT-F7: Runner shares not compared with field numbers

Raised as minor; verification: not adversarially verified.

#### LIT-F7 (R1 LIT, minor, unsupported-interpretation): The runner shares are not compared with the actual field numbers

- **Description.** The only verified field rates (TOPS 2005) are 0.9-9.0 % red-light violations in SOV lanes. The HOV figure of up to 34.3 % includes occupancy violations. Sun 2013's rates are unverified. The modelled behaviour (ignore the amber and the first 1.5 s of red) is narrower than the field definition (did not stop at red). Without the numbers, readers cannot tell that s = 30 % is a stress test.
- **Evidence.**
  - /tmp/.../LIT/tops2005.txt §2.4 and Tables 3-14/3-15
  - paper.qmd:149
- **Failure scenario.** Readers take 30 % runners as realistic and over-interpret the C1 runner rows (24.4 % and 27.6 %).
- **How to test.** Read the Sun 2013 and Zhu thesis compliance tables and quote both sources' ranges next to s.
- **Related claims.** C19, C63

#### G8-F1 (R2 G8, minor, unsupported-interpretation): Work-zone field data put s = 30 % inside the observed non-compliance range; the numbers are in the companion report and thesis, not verified in the cited TRR article

- **Description.** Round-1 LIT-F7 and C63 called s = 30 % 'well above field values', based on TOPS SOV violations of at most 9 %. The Sun et al. field study, read through its 2012 final report and Zhu's thesis, reports far lower compliance at temporary work-zone meters. Non-compliance is 25.0-54.5 % per signal scheme, 14.4 % with platoons and 36.4 % in free flow, and 17.1-59.5 % per site. So s = 10 % sits between permanent and temporary meters, and s = 30 % lies within the work-zone range. These field meters also used three-section heads with a 1-s amber (4R-1Y-2G), and compliance was higher than with two-section heads. That gives a field source for the paper's amber design (cf. LIT-F4). Small inconsistency: 4R-2G compliance is 45.5 % in the report but 40.5 % in the thesis.
- **Evidence.**
  - G8/edara2012_report.txt:699-710, :758
  - G8/zhu2012_thesis.txt:345-347, :839, Table 5.1 (:1124-1156)
  - G8/noncompliance_ranges_output.txt
  - LIT/tops2005.txt:1333
- **Failure scenario.** The author adopts round-1's advice and calls s = 30 % an extreme stress test. A reviewer who knows the Missouri work-zone study objects that 30 % is typical there.
- **How to test.** Quote both ranges next to s (permanent SOV 0.9-9.0 %; temporary work-zone 25-55 % per scheme). Cite the Edara, Sun & Zhu 2012 SWZDI final report (InTrans 06-277), or check the TRR article in a library, before attributing numbers to Sun2013.
- **Related claims.** C63, C19

### B55. [minor] LIT-F9: TOPS2005 wrong author and missing report details

Raised as minor; verification: not adversarially verified.

#### LIT-F9 (R1 LIT, minor, citation): TOPS2005 lists the wrong author and has no report details

- **Description.** The bib says author = 'Traffic Operations and Safety Laboratory'. The report's title page reads 'Intelligent Transportation System (ITS) Program, University of Wisconsin-Madison', prepared for the Wisconsin DOT, WisDOT Project ID 1206-00-17, final report dated January 13, 2005. It is hosted at files.topslab.wisc.edu/its/rampmetering/madison_beltline_meter_eval.pdf.
- **Evidence.**
  - /tmp/.../LIT/tops2005.txt lines 1-25
  - papers/paper_1/references.bib TOPS2005
- **Failure scenario.** A reader cannot find the report under the given author.
- **How to test.** Correct the author and institution, and add the project ID, date and URL.
- **Related claims.** C19, C63

### B56. [minor] PLANT-F10: Amber threshold and dilemma zone not stated; 3-s amber short for 23 m/s

Raised as minor; verification: not adversarially verified.

#### PLANT-F10 (R1 PLANT, minor, disclosure): The amber threshold and the dilemma zone are not stated; a 3-s amber is short for 23 m/s

- **Description.** The stop decision uses tls.yellow.min-decel (default 3 m/s2) when planning and the vType decel of 1.5 m/s2 at the step-level yellow check. At 23 m/s, vehicles 69-88 m from the line at amber onset can neither stop at 3 m/s2 nor clear the line before red. This is the source of the forced stops in PLANT-F3. The approach speed at red reached 26 m/s, with 1,020 approaches at 10 m/s or more for PI in slow_q2000.
- **Evidence.**
  - SUMO MSFrame.cpp:513; MSVehicle.cpp:2793-2796, 3772-3780
  - p1b_result.json eval.table1_operating_map.slow_q2000.arms.PI approach_red_mps_max 26.2, n_ge_10 1020
- **Failure scenario.** A reader assumes a realistic dilemma-zone design. The amber is shorter than common engineering practice for this speed (my general knowledge; not checked against a source).
- **How to test.** State both thresholds. Run a sensitivity with a longer amber (for example 4-5 s) on a small seed set.
- **Related claims.** C61

#### G4-F2 (R2 G4, minor, wording): 'Stop comfortably' in the paper means 3.0 m/s2 (twice b) in the model; a stop at b is impossible within about 7.4 s of the line

- **Description.** The vType deceleration is b = 1.5 m/s2. SUMO decides to stop at amber with stopDecel = max(min(3.0, 9), 1.5) = 3.0 m/s2. The code sets no option for this, so the default applies. At 23 m/s the stop gaps are 170.6 m at b and 82.5 m at 3.0 m/s2 (Euler, 0.5 s), against 69 m covered in the 3-s amber. Free-flowing vehicles less than 7.4 s from the line when the amber starts split as follows: about 40 % clear the line, about 8 % fall in the dilemma zone, about 52 % stop with a deceleration between b and 2b, and 0 % stop at b or less. Free-road speed at the line from my IDM re-implementation: 22.3 m/s for the AV type, up to about 27 m/s for fast humans.
- **Evidence.**
  - SUMO MSVehicle.cpp:2793-2796, :3768-3773; MSFrame.cpp:513
  - plant.py@93ba655:27
  - G4/kinematics.py, G4/kinematics.out
- **Failure scenario.** A reader assumes that compliant drivers brake at most at their comfortable deceleration. In the model they brake at up to 2b, and they are force-stopped when that is not possible.
- **How to test.** State the rule: 'SUMO default: stop if the stop is possible at 3 m/s2 (tls.yellow.min-decel), otherwise continue'. Optionally check with a single-vehicle SUMO scenario (extend runners.signal_scenario) at several distances.
- **Related claims.** C61

#### G4-F3 (R2 G4, minor, hidden-assumption): The executed IDM braking at amber may exceed the 3.0 m/s2 decision threshold (own re-implementation, not checked in SUMO)

- **Description.** After SUMO decides to stop, the speed comes from IDM stopSpeed = _v(gap, v, 0) (MSCFModel_IDM.cpp:179-197, :225-268). finalizeSpeed allows braking down to emergencyDecel 9 (MSCFModel.cpp:199-207). In my re-implementation, a vehicle that can only just stop at 3.0 m/s2 has a peak deceleration of about 7.2-7.8 m/s2 at 10-23 m/s, and about 3.2-4.0 m/s2 in the middle of the zone. SUMO logs a warning only at 9 m/s2 or more, so the data cannot confirm or refute this.
- **Evidence.**
  - SUMO MSCFModel_IDM.cpp:179-197, :225-268; MSCFModel.cpp:199-207; MSVehicle.cpp:4975-4983
  - G4/kinematics.out section 4
- **Failure scenario.** The model's compliant drivers stop more harshly than 'comfortably' suggests. This is uncertain because my code is a re-implementation, not SUMO.
- **How to test.** One SUMO run with a single vehicle per lane at fixed distances at amber onset, logging vehicle.getAcceleration every step (allowed only with author approval).
- **Related claims.** C61

### B57. [minor] PLANT-F5: Emergency braking at downstream merges in 94.5 % of metered runs unreported

Raised as major; verification: reproduce: CONFIRMED/minor, defend: REFUTED/minor.

#### PLANT-F5 (R1 PLANT, major, missing-evidence): Emergency braking at the downstream merges in 94.5 % of metered runs is not reported

- **Description.** Among evaluation main runs (s=0), 94.5 % of metered runs log SUMO 'emergency braking' (braking at or above 9 m/s2) on merge edges 4/5, against 61.2 % of NC runs. Metered runs contain about 201k such events over 54,600 runs. The realism paragraph reports only meter emergency stops and zero collisions. The platoons released by the meter appear to hit the zipper merges hard.
- **Evidence.**
  - emerg_edges.out
  - log_sample_emerg.txt / emerg_parse.py: braking on edges 4 and 5 is at decel 9.0 = emergencyDecel
- **Failure scenario.** The safety picture is incomplete: metering raises the frequency of maximum-deceleration events at the merges.
- **How to test.** Add the merge emergency-braking share per arm to the realism row. Check sensitivity to the zipper parameters or a longer merge.
- **Related claims.** C83

#### G3-F3 (R2 G3, minor, unsupported-interpretation): The critic's premise is mostly wrong: hard braking is on the incident lanes, not at the junction merges

- **Description.** G3 (and PLANT-F5, which says platoons released by the meter hit the zipper merges hard) puts the emergency braking at the junction lane drops. Lane-level log counts contradict this. Of 1,309,783 P1b emergency-braking warnings, only 3,319 (0.25 %) are on zipper internal lanes (:5_0_* 3,304, all in slow cells inside the incident window; :4_0_* 15), and 245 on meter internal lanes. The bulk is on normal lanes, where collisions are checked: 5_0 626,069 (the slowdown lane) and 4_1 556,012 (the crawl lane). It falls almost entirely inside the incident window (block metered: edge 4 564,636 of 565,605; slow metered: edge 5 614,976 of 614,976), caused by the instant setMaxSpeed cut to 1 m/s or 5 m/s. NC runs show it too: per incident cell, NC and metered rates are similar (slow 98.9 % vs 98.1 %, block 84.0 % vs 98.0 % of runs). Without an incident, only 314 of 23,242 metered runs (1.4 %) had braking on edges 4/5. C1 has 0 internal-lane warnings in all 1,100 runs. So the hard braking is mainly an artefact of how incidents are imposed, not a sign of hidden merge collisions. Caveat: emergency_by_edge is counted per edge; the lane split comes from the logs.
- **Evidence.**
  - G3/p1b_log_emerg_lanes.out (counts per lane, all 344,852 P1b logs)
  - G3/scan_p1b_emerg.out / .json (per incident x metered cell, inside and outside the incident window)
  - G3/lane_by_cell.out (':5_0_' braking only in slow cells; ':4_0_' 14 runs)
  - G3/c1_log_lanes.out (no internal-lane warnings in C1)
  - v5b/d2/incidents.py@e7dd561 BLOCK_LANE 4_1 at 1.0 m/s, edge 5 at 5.0 m/s via setMaxSpeed
- **Failure scenario.** If PLANT-F5 is reported as written, the paper would wrongly blame the meter for merge hard braking that the incident model causes in every arm, including no control.
- **How to test.** Re-state PLANT-F5 per lane and per incident window. Optionally ramp the incident speed limit down over a few seconds and check that the edge-4/5 hard braking disappears.
- **Related claims.** C83

#### Verifier R2 reproduce: CONFIRMED / minor

Core facts reproduced exactly from raw SUMO logs (basis: direct observation). I parsed every raw log for the 55,200 P1b v108 main evaluation runs (seeds 7,400,600-699, k=0, d=c=0, no false alarm, no VSL, rs=0). NC: 600 runs, 61.2 % with emergency braking on edges 4/5 (internal lanes included). Metered: 54,600 runs, 94.5 %. There are 201,432 events on edges 4 and 5 (201,956 with the internal lanes :4_0/:5_0). All 217,807 braking warnings have decel=9.00, wished=1.50, severity=1.00, so they are braking at emergencyDecel (9 m/s2; the vType at plant.py sets decel=1.5 and no emergencyDecel). My log counts match the SUMO statistic-output emergencyBraking counter in all 55,200 runs and match the JSON field emergency_by_edge. The paper (line 197) reports only meter emergency stops and zero collisions. The protocol (p1b_addendum.md:20) pre-registered only meter emergency stops. So the omission is real.

The finding's mechanism and its safety reading are CONTRADICTED (basis: derived):
(1) The events are on the incident lanes at the moment the incident starts. They are not platoons released by the meter hitting the zipper merges. In slowdown runs, 99 % are on lane 5_0, the slowed edge. In crawl runs, 96.5 % are on lane 4_1, the crawl lane. Only 524 of about 202k are on the junction internal lanes. About 80 % happen in the exact step t = t_on, and 89-99 % within 3 s of t_on. Each vehicle brakes once, and about 3-4 vehicles brake per run. The cause is the instant TraCI speed-limit cut in incidents.py.
(2) In incident-free cells, metered runs have 0.014 merge-braking events per run (30 events in 2,200 runs). Metering itself almost never causes these events.
(3) The 61.2 % vs 94.5 % gap is mostly a difference in cell mix. One third of the NC main runs have no incident (200/600), against 4 % of the metered runs (2,200/54,600). Within the incident cells the shares are 91.5 % (NC) vs 98.4 % (metered), and the mean is 3.32 vs 3.85 events per run. Per cell: slow 1600 98.0 vs 97.9; slow 2000 99.0 vs 97.1 (here metered is lower); block 1600 95.0 vs 98.8; block 2000 74.0 vs 99.8.
A plausible but untested reason why metered runs are a little higher: metering keeps the bottleneck free-flowing, so more vehicles are at speed when the speed limit drops (speculation).

Effect on the paper: no headline result changes, and the reading "metering is unsafe at the merges" is not supported. What remains is a missing modelling caveat. The incident model forces about 3-4 vehicles to brake at 9 m/s2 at onset, in about 92-98 % of incident runs of every arm, NC included. The realism paragraph could state this. Severity lowered from major to minor.

Side note (info, not part of this finding): the runs use --collision.check-junctions false (sumo_runner.py:105). The statement "no collisions occurred" (0 in the JSON and in the stats XML for all main runs) therefore does not cover junction-internal lanes.

Checks: git archive 93ba655 into /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/PLANT-F5-reproduce/code_93ba655; read d2/episode.py, p1b/episode.py, d1/sumo_runner.py, d1/plant.py, d2/incidents.py, d1/netgen_bn4.py; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/PLANT-F5-reproduce/scan_emerg.py: own regex parse of the raw sumo_pid*.log and stats_pid*.xml for all 63,182 eval-seed runs -> eval_emerg.jsonl; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/PLANT-F5-reproduce/agg_emerg.py -> agg_emerg.out (shares, totals, per cell, decel/severity, cross-check against stats XML and JSON); /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/PLANT-F5-reproduce/onset_timing.py -> onset_timing.out (time of events relative to t_on, edge per incident type); /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/PLANT-F5-reproduce/lane_sample.py -> lane_sample.out (lane and vehicle detail, seeds ending in 0); grep of paper.qmd, p1b_result.md, p1b_summary.md, p1b_c1_summary.md, p1b_addendum.md for emergency/braking/merge

#### Verifier R2 defend: REFUTED / minor

The counts in the finding are correct, but they do not mean what the finding says. I parsed the SUMO logs of the same 55,200 P1b evaluation main runs myself (seeds 7,400,600-699, s=0, no k/d/c/fa/vsl/rep). They give 94.5 % of metered runs vs 61.2 % of NC runs, and 201,956 merge events. My parse also matches the emergency_by_edge JSON field in every run (direct observation).

Three facts remove the problem:
(1) Almost all merge events are caused by how the incident is injected, not by the meter or the zippers. 96.5 % of metered merge events (194,836 / 201,956), and 80.7 % of all merge events at exactly t_on, fall within 5 s of incident switch-on. They sit on the incident lane itself: lane 5_0 for the slowdown, lane 4_1 for the crawl. Incidents.py at 93ba655 sets the new speed limit instantly (edge.setMaxSpeed('5', 5) / lane.setMaxSpeed('4_1', 1)). Vehicles already on the link then brake at emergencyDecel, 9 m/s2. IDM decel is 1.5 m/s2, which is the 'wished=1.50' value in the log. This happens in every arm, NC included (NC: 1,273 of 1,330 merge events are in this burst) (derived).
(2) The 94.5 % vs 61.2 % contrast comes mostly from a different mix of runs. One third of NC runs are clean (no incident), but only 4.0 % of metered runs are clean, because switch runs exist only with an incident. Comparing like with like:
- slowdown: metered 97.9 / 97.1 % vs NC 98 / 99 %;
- lane crawl: metered 98.8 / 99.8 % vs NC 95 / 74 %;
- clean days: metered 1.3 / 1.5 % vs NC 1 / 0 %.
Reweighted to NC's mix of conditions, the metered share is 66.1 %, against 61.2 % for NC (derived).
(3) The data do not support 'meter platoons hit the zipper merges hard'. On clean days, with the meter on and no incident, only 1.4 % of metered runs have any merge braking. Merge braking outside the onset burst is mixed: higher with metering in the slowdown cells (10-11 % vs 1-2 % of runs), lower in the crawl cells (9.5-20 % vs 20-30 %). In C1 (lane crawl, 1600 veh/h, v114) it was IP 12 %, PI 18 % and NC 29 % of runs. All merge events are 'braking'; none is an 'emergency stop'. So the paper's emergency-stop share (all stops are at the meter: 7,530 events in 7,081 of 54,600 metered runs) and its zero-collision count (0 in 55,200 runs) are unaffected.

Other context:
- The protocol (p1b_addendum.md B1 and R4) pre-registered only meter emergency stops, approach speed and collisions, and the paper reports those.
- The project's own notes (docs/architecture/port_map_v0.md:77,160) state that SUMO emergency-braking warnings are not used as a safety metric.

What remains is minor:
- The paper says the incidents are speed limits (paper.qmd:110), but it does not say that they start instantly and so force a 9 m/s2 braking event on the incident lane in about 98 % of incident runs of every arm, NC included. That is a limit of the incident model and should be disclosed in one sentence.
- There is a small effect associated with metering in the slowdown cells, outside the onset burst.
- Separately, the paper's emergency-stop sentence leaves out the meter emergency-braking warnings: 14,359 events. This is outside the scope of this finding.

None of this touches S1a/S1b, C1 or Table II. All compared arms see the same paired incident onset.

Checks: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/PLANT-F5-defend/scan_merge_braking.py: selects the 55,200 P1b evaluation main runs from the raw run JSONs and parses each retained SUMO log (~/work/phd/v5b1_runs/p1b/v108/sumo/<key>/sumo_pid*.log). Output: merge_runs.jsonl; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/PLANT-F5-defend/scan_merge_braking_lane.py: same scan, keeping lane ids. Output: merge_runs_lane.jsonl; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/PLANT-F5-defend/analyze_merge_braking.py: reproduces the 94.5 / 61.2 % shares, cross-checks against the JSON field, groups runs by incident, q and arm family. Output: analyze_merge_braking.out; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/PLANT-F5-defend/analyze_lane_timing.py: offsets after t_on, lanes, timing classes, like-for-like and reweighted shares. Output: analyze_lane_timing.out; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/PLANT-F5-defend/kinds_by_location.py: event kinds by location, emergency-stop runs, collisions. Output: kinds_by_location.out; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/PLANT-F5-defend/c1_merge_braking.py: the same timing split on all 1,100 C1 runs (v114). Output: c1_merge_braking.out; Read code at 93ba655 with git show: v5b/d2/incidents.py, v5b/d2/episode.py:42-63, v5b/p1b/episode.py:256-290, v5b/d1/sumo_runner.py:100-140 and 180-310, v5b/d1/netgen_bn4.py, v5b/d1/plant.py:25-29; Read paper.qmd:80-203, protocol p1b_addendum.md, results notes p1b_result.md and p1_result.md (realism parts), and grepped docs/ for emergency-braking conventions; Read the round-1 PLANT scripts emerg_edges.py and emerg_parse.py and their outputs, for comparison only

### B58. [minor] PLANT-F7: Delay reference speed is the incident-reduced lane limit

Raised as minor; verification: not adversarially verified.

#### PLANT-F7 (R1 PLANT, minor, hidden-assumption): The delay reference speed is the incident-reduced lane limit

- **Description.** SUMO's timeLoss uses the current lane limit x speedFactor, so travel at 5 m/s on edge 5, or at 1 m/s on lane 4_1, adds no delay. The hidden travel time is 3.3-4.3 s/veh (slow) and 6.2-8.2 s/veh (block). Adding it back changes the Table II rel values by at most 0.8 percentage points (block_q1600 IP vs PI 18.0 -> 17.5; IP vs ID 22.0 -> 21.6; slow_q1600 IP vs ID 16.2 -> 15.4). The headline survives, but 'door-to-door delay' is not delay relative to a fixed free-flow time.
- **Evidence.**
  - SUMO MSVehicle.cpp:4295-4304, MSLane.h:575-592
  - delay_reference.out
- **Failure scenario.** Absolute delays and the denominators of rel understate the incident's cost. Arms that move vehicles through the incident zone while it is active are slightly favoured.
- **How to test.** Define delay against a fixed free-flow time (arrival minus desired departure minus free-flow time), as in delay_reference.py, and report it.
- **Related claims.** C24

#### FU1-F6 (R1 FU1, minor, wording): 'Door-to-door delay' excludes time spent at the incident speed limit

- **Description.** The delay is departDelay + SUMO timeLoss. Incidents are speed-limit changes (incidents.py@93ba655:67,69). Mean ideal trip time (TIS - delay) rises from 44.5 s on clean days to 47.8-52.6 s on incident days of the same seeds. That is consistent with timeLoss being measured against the reduced limit, so 3-8 s/veh of incident time is not counted as delay. This is inferred from the data and from general knowledge of SUMO; I did not check it in the SUMO source. The paired effect on the headlines is ≤ 0.5 points: D' = TIS minus clean-day ideal gives 11.7, 21.6, 17.5 and 16.1, against 11.8, 22.0, 18.0 and 16.2.
- **Evidence.**
  - v5b/d1/episode.py@93ba655:72-79
  - v5b/p1b/episode.py@93ba655:253-254,271
  - FU1/metric_ideal.out part (1)
- **Failure scenario.** A reader assumes delay = door-to-door time minus free-flow time. The absolute delays and the delay per incident are understated, while the paired rels are almost unchanged.
- **How to test.** Re-run FU1/metric_ideal.py. Optionally confirm the definition of timeLoss under a changed lane speed in SUMO 1.27.1 (MSDevice_Tripinfo).
- **Related claims.** FU1-C1

### B59. [minor] PLANT-F8: Emergency-stop share dominated by meter start-up transient

Raised as minor; verification: not adversarially verified.

#### PLANT-F8 (R1 PLANT, minor, unsupported-interpretation): The 12.8 % emergency-stop share is dominated by the meter switching on at t=40 s

- **Description.** 44 % of P1b forced stops (19,898 of 44,816) occur at the first red (t=49 s), right after the all-green warm-up, when traffic arrives at free speed. In evaluation main runs (s=0), 13.0 % of metered runs have a stop, but only 5.3 % have one at t >= 60 s. The 87 % to 12.8 % comparison therefore partly measures a start-up transient, not steady-state amber behaviour.
- **Evidence.**
  - estop_times.out; estop_eval.out
- **Failure scenario.** The amber's effect is misread. A different start-up (for example a meter already running during warm-up) would change the number a lot.
- **How to test.** Report the share excluding the first cycle, or start the meter during warm-up.
- **Related claims.** C61, C83

### B60. [minor] PLANT-F9: Runners cross later reds whenever they cannot brake

Raised as minor; verification: not adversarially verified.

#### PLANT-F9 (R1 PLANT, minor, discrepancy): Runners in SUMO also cross later reds whenever they cannot brake

- **Description.** With jmDriveAfterRedTime=1.5, SUMO's ignoreRed returns '!canBrake || 1.5 > redDuration' at red and 'always drive' at yellow. At the lane-advance check it is called with canBrake=false, so runners are never force-stopped. A runner that cannot stop at 1.5-3 m/s2 runs a red of any age (above 2 s its speed is capped at 13.9 m/s). The pre-data test (tests/test_p1b_sumo.py:27-31) covers only a 10 m/s approach. jmDriveAfterYellowTime has no effect.
- **Evidence.**
  - SUMO MSVehicle.cpp:7605-7621, 2937-2940, 4522
  - v5b/p1b/runners.py@93ba655:15
  - runner_share.out
- **Failure scenario.** Runner rows overstate the 'first 1.5 s of red' description. The leakage modelled is larger and differs in kind.
- **How to test.** Log time-into-red for each runner crossing in a small diagnostic run (no claim run), or describe the SUMO rule as it is.
- **Related claims.** C62

### B61. [minor] PROV-F4: 'Run once from frozen code' does not hold for P1 or D1/D2

Raised as minor; verification: not adversarially verified.

#### PROV-F4 (R1 PROV, minor, reproducibility): 'Every study was run once from a frozen code version' does not hold for P1 or for D1/D2

- **Description.** P1 was started by queue_v100.sh in the main (non-frozen) worktree. A docs commit (e973f6e, 18:43) changed HEAD, and the run aborted after tcheck-A (6,146 runs). It was resumed at 19:06 from a frozen worktree with --resume, reusing those runs; this was allowed by the protocol ('resume only at the same commit'). D1 and D2 were re-run after the V100 meter-phase bug. e973f6e touched only docs and results, so P1's data are code-identical. The claim is true for P1b and C1, the only studies the paper describes, but the paper uses a P1 number.
- **Evidence.**
  - ~/work/phd/v5b1_runs/queue_v100.log 18:51:30
  - p1/v99/run.log:13-15
  - P1_EVAL_STARTED.json args.resume=true
  - git show --stat e973f6e (docs/decisions.md and results files only)
  - docs/baseline/BASELINE_2026-10-20.md:81
- **Failure scenario.** A reader of 'run once from a frozen code version' is not told that one study in the line was halted and resumed, and that a bug forced re-runs of two others.
- **How to test.** grep -n 'reused\|code changed' ~/work/phd/v5b1_runs/p1/v99/run.log ~/work/phd/v5b1_runs/queue_v100.log
- **Related claims.** C54

### B62. [minor] PROV-F5: Amber 87 % -> 12.8 % emergency-stop reduction compares two different studies

Raised as minor; verification: not adversarially verified.

#### PROV-F5 (R1 PROV, minor, invalid-comparison): 'Amber reduced emergency stops from 87 % to 12.8 %' compares two different studies

- **Description.** The 87 % comes from P1 (43,370 of 50,061 main evaluation runs, no amber, A of 100 actions, seeds 500-599). The 12.8 % comes from P1b (7,396 of 57,782 runs; amber; A of 120 actions; rate clip; seeds 600-699). The difference is not attributable to amber alone. A controlled paired comparison exists in the P1b smoke (162 runs: 538 to 13 emergency stops; 150 to 23 runs with meter emergency braking), but it uses smoke seeds.
- **Evidence.**
  - paper.qmd:197
  - scratch estop_share.py: P1 86.6 %, P1b 12.8 %
  - ~/work/phd/v5b1_runs/p1b_smoke_93ba655/smoke.json smoke_report.emergency_with_without_amber
- **Failure scenario.** A causal reading of the amber effect also includes the changes in action set, clip and seeds, and it cites an unreported study.
- **How to test.** Run scratch estop_share.py; read the smoke.json key.
- **Related claims.** C54

#### C1-F6 (R1 C1, minor, invalid-comparison): Emergency-stop drop attributed to the amber, but P1 -> P1b changed more than the amber

- **Description.** The 87 % and 12.8 % figures come from two studies. They share the counter, the SUMO version and the way the run population is defined. They differ in the meter (minimum red 2 s, rate cap 4000 -> 2618 veh/h, PI law with carry-over), the action set, the tuned arms and the seeds. Only 30 run specs are shared. On those, the share falls from 67.6 % to 14.7 %. For constant-rate arms, where only the amber differs, it falls from 68-97 % to 8-20 %. The amber is a plausible main cause, but 'reduced' should be worded as a P1-vs-P1b comparison that names the other changes.
- **Evidence.**
  - v5b/p1b/meters.py@93ba655:1-40; v5b/d1/episode.py@85f7d34:46-57
  - estops2.py output (matched specs)
  - papers/paper_1/paper.qmd:197
- **Failure scenario.** A reviewer asks for a same-seed amber on/off ablation; part of the drop could come from the rate cap removing 1.2-5 s reds at high commanded rates in feedback and PI arms.
- **How to test.** estops2.py; ideally rerun P1b code with the amber disabled on the same seeds (needs SUMO).
- **Related claims.** C82

#### TEXT-F14 (R1 TEXT, minor, unsupported-interpretation): The emergency-stop reduction is attributed to amber using a comparison across studies

- **Description.** The 87 % figure comes from 50,061 P1 runs and the 12.8 % figure from 57,782 P1b runs. The two studies differ in seeds, tuned arms and action set, so this is not a controlled amber on/off comparison. P1b's emergency_meter counter gives 22.0 % (12,726 / 57,782).
- **Evidence.**
  - paper.qmd:197
  - p1_result.md:81
  - p1b_verification/out/p1_vs_p1b.log:24
- **Failure scenario.** Overstates a causal effect of amber.
- **How to test.** Say 'across the two rounds', or run a matched amber on/off check.
- **Related claims.** C14

### B63. [minor] PROV-F6: Seed use departs from approved block labels; not disclosed in paper

Raised as minor; verification: not adversarially verified.

#### PROV-F6 (R1 PROV, minor, disclosure): The seed use departs from the approved block's labels; this is disclosed internally, not in the paper

- **Description.** Approved block: 010-099 tool checks, 100-299 tuning, 300-499 validation, 500-699 test, 700-999 confirmatory. P1b used 260-279 (in the tuning range) for tool checks and 300-339 (in the validation range) for tuning. D2 evaluated on 140-189 (in the tuning range). Smoke runs used 000-009 (the calibration range). The author approved this (V108) and the addendum discloses it (line 81). There is no reuse across studies: main seeds are disjoint, and C1's 700-799 were untouched before C1. The P1b T3 replicate seed 17,400,260 follows the derived rule but was not approved by name, unlike P1's 17,400,240 (V100 D2).
- **Evidence.**
  - scratch seed_sets.py (distinct seeds and overlaps)
  - scratch scan_runs.py sumo_seed_ranges: P1b '+1e7 260-279': 2
  - p1b_addendum.md@75bcd2b:81; decisions.md V108
- **Failure scenario.** A reader who checks the seed block against the paper's 'seed ranges fixed and approved' finds the label deviations without an explanation.
- **How to test.** Run scratch seed_sets.py.
- **Related claims.** C53, C55

### B64. [minor] REPRO-F2: Fig. 2 marginal medians disagree with paired statistics

Raised as major; verification: reproduce: CONFIRMED/minor, defend: CONFIRMED/minor.

#### REPRO-F2 (R1 REPRO, major, unsupported-interpretation): Fig. 2 shows marginal medians; its 'bounds' and gaps disagree with the paired statistics in Table II

- **Description.** Fig. 2 bars are medians of each arm. The paper's statistic is median(r-t)/median(r), and the S2 bracket uses 98.75 % CI ends: the median version for OR_in and the mean version for ORX_4. Gaps read off the figure therefore differ from the reported results, sometimes in sign. The caption calls ORX_4 and OR_in 'the two bounds', but those bars are not the bounds in Table II or line 193.
- **Evidence.**
  - scratch/fig2_vs_paired.py output: slow_q1600 IP vs PI marginal -0.3 % vs paired +4.5 % (Table II 4.5); ORX_4 vs IP marginal +8.9 % vs paired -0.5 % (S2 lower -0.4 %); OR_in vs IP +32.6 % vs +15.1 %; block_q2000 ORX_4 vs IP +1.9 % vs +6.0 %
  - v5b/p1/stats.py@e7dd561:112-127 (x, y definitions)
  - fig_ladder.py@HEAD:26 (plots median_delay_s)
- **Failure scenario.** A reader concludes from Fig. 2 that cross-fitted hindsight gives about 9 % over IP for the slowdown at 1600 veh/h, and that IP is no better than PI there. Table II says about -0.4 % and +4.5 %.
- **How to test.** Run scratch/fig2_recompute.py, then scratch/fig2_vs_paired.py on scratch/out/fig2_recomputed.json.
- **Related claims.** C68

#### Verifier R2 reproduce: CONFIRMED / minor

I reproduced the core fact with my own code. I read 242,000 raw P1b run files from ~/work/phd/v5b1_runs/p1b/v108/runs, and every file has code_commit 93ba655. The Fig. 2 bars are the median delay of each arm on its own (marginal medians). The paper's statistic is the paired one, median(r-t)/median(r). The gaps between bars therefore differ from the paired numbers, and in some cells the sign differs too. Every number in the finding matches my recomputation:
- slow_q1600, IP vs PI: bars -0.3 %, paired +4.5 %.
- slow_q1600, ORX_4 vs IP: bars +8.9 %, paired median -0.5 %.
- slow_q1600, OR_in vs IP: bars +32.6 %, paired +15.1 %.
- block_q2000, ORX_4 vs IP: bars +1.9 %, paired +6.0 %.

The S2 bracket mixes two versions of the statistic. Its upper end is the upper 98.75 % CI end of the median version for OR_in. Its lower end is the lower CI end of the MEAN version for ORX_4 (v5b/p1/stats.py lines 120-121). This mix was pre-registered (p1_incident_information.md:106-107). But the paper (line 145) defines only the median version, and it never says that the S2 lower end uses the mean version. The caption calls the ORX_4 and OR_in bars "the two bounds". The bounds in Table II are CI ends of paired gains, not these bars. Also, the protocol says ORX is low only in expectation (mean version), so a median-delay bar is not that bound.

Where the finding goes too far:
(1) Its failure scenario says "Table II says about -0.4 %". But -0.4 % is a CI end. The matching point estimate, the paired mean, is +11.9 %. So a reader who reads about 9 % from the bars is not far from the protocol's own ORX point estimate.
(2) For slow_q1600 IP vs PI, the paired-median 95 % CI is [-24.4, +12.8] and the paired mean is -13.5 %. So "IP no better than PI", read from the bars, is not contradicted by the data.

A clearer conflict the finding does not give: in block_q2000 the ORX_4 bar implies a gain of only 1.9 % over IP. The reported lower bound is larger, 3.5 % (Table II; line 193).

No headline result changes. All plotted values are correct, and the figure design was pre-registered (protocol A10, line 116). The fixes are wording: the caption, plus one methods sentence stating that the S2 lower end uses the mean version. So I rate it minor, not major. If the missing statement of the mean version is judged as its own finding, a reviewer would require that sentence.

Unrelated to this finding: line 193 says "upper bounds ranged from 13.3 % to 47.9 %". The S2 upper ends in the JSON are 47.9, 19.3, 25.4 and 22.4, and no S2 or TP value equals 13.3 %. This is probably a typo for 19.3.

Checks: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/REPRO-F2-reproduce/recompute_fig2_paired.py: independent rebuild of run keys from the tuned arms. Recomputes, from raw runs, L0/ID/IP/OR_in/ORX_4 per seed, the marginal and paired gaps (median and mean) and the S2 x/y with its own bootstrap. Output: recompute_out.json in the same folder.; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/REPRO-F2-reproduce/summ_json.py: prints the ladder rungs and S2 (median and mean versions, statements x/y) from p1b_result.json.; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/REPRO-F2-reproduce/inspect_json.py: lists the structure of p1b_result.json.; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/REPRO-F2-reproduce/find_133.py: searches S2/TP for a 13.3 % value (none found).; git show 93ba655 and e7dd561: v5b/p1/stats.py lines 48-60 and 112-127; git diff 93ba655 e7dd561 -- v5b/p1/stats.py (empty).; git show 93ba655:v5b/p1b/analysis.py (ladder lines 375-380; cell_runs, or_in, orx) and v5b/p1/episode.py run_key; v5b/p1b/family.py action order.; Read papers/paper_1/figures/fig_ladder.py; pdftotext of fig_ladder.pdf.; Read paper.qmd lines 139-195 (methods, caption, Table II, S2 text); grep for any mention of the mean version.; Read the protocol p1_incident_information.md lines 100-117 (S2 definition, A10 figure plan).

#### Verifier R2 defend: CONFIRMED / minor

Defend lens. The core fact is correct, and I checked it myself from the raw data. The Fig. 2 bars are the median delay of each arm. The paper's effect statistic is the median of paired differences, median(r-t)/median(r). So a gap read off the bars is not the reported effect. I rebuilt all 20 bars from the raw P1b runs (code 93ba655) with my own code. They match the JSON and the PDF labels exactly.

Most of the finding's harm does not survive the defence:
(1) The caption is accurate as written. It says "Median delay", and n = 100 per cell is correct.
(2) The figure follows the pre-registered design. Protocol A10 (line 116, commit ee3ce1e, 2026-10-19) fixes "strongest L0 -> ID -> IP -> [ORX_Rmax, OR_in]". Rule I13 (line 177) picks the strongest L0 by the lowest median delay. Both were committed before the 93ba655 runs (2026-10-20).
(3) "The two bounds" uses the paper's own vocabulary. Table I (line 133) and the methods (line 141) define the arms OR_in and ORX_R as the bounds. The OR_in bar is a valid optimistic bound even as a median: on every seed OR_in is at most any action, including IP. The ORX_4 >= OR_in ordering also holds on every seed.
(4) The finding's sign conflict for ORX_4 in the slowdown cell at 1600 veh/h (bars +8.9 % vs paired median -0.5 %) uses the median version. That is not the statistic the protocol uses for ORX. Protocol line 107 and stats.py@93ba655:121-122 use the mean version, which gives +11.9 % (same sign and size as the bars). In all 4 cells the ORX_4 bar gap has the same sign as the mean version.
(5) The failure scenario misreads Table II. Its -0.4 % is the lower end of a 98.75 % CI, not an 'about' estimate. The paper says the bracket did not converge, so it states no point value.
(6) IP vs PI in the slowdown cell at 1600 veh/h is not significant in any version. Bars -0.3 %, paired median +4.5 % (95 % CI -24.4 to 12.8), mean version -13.6 %. The paper claims nothing there: 4.5 is not bold, and line 155 says the interval is above zero only for the lane crawl at 1600 veh/h. A reader of the figure would reach the same conclusion as the paper.
(7) The OR_in and ORX_4 bar gaps lie inside the Table II bracket in 3 of 4 cells. No headline (S1a, S1b, C1, Table II) changes.

What survives:
- The caption does not warn that bar gaps differ from the reported paired effects.
- In some cells the visible gap differs a lot from the reported effect. For the slowdown at 2000 veh/h, IP vs ID is 6.0 % in the bars but 11.8 % in the text (the S1b pass). IP vs PI in the same cell is 1.6 % vs 7.4 %.
- For the lane crawl at 2000 veh/h, the ORX_4 bar gap (1.9 %) lies below the stated lower bound "at least 3.5 %".
- A careful reviewer could notice these, and one caption sentence fixes them. This makes it a minor wording issue, not major.

Related item, outside this group but worth tracking separately; it may be major on its own: the paper never says that the S2 lower bound uses the mean version, or that S2 uses the 98.75 % CI level. Line 145 defines only the median rel; the mean version is pre-registered in the protocol but not disclosed in the paper.

Aside: paper line 193 says "upper bounds ranged from 13.3 % to 47.9 %", but the Table II and JSON upper ends are 19.3 to 47.9 %. This looks like a typo; the value 13.3 % is not an S2 value in the JSON.

Basis: direct observation for the recomputed numbers; derived for the interpretation.

Checks: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/REPRO-F2-defend/fig2_defend.py (own code, no v5b imports): rebuilds per-seed delays for the L0 arms, ID, IP, OR_in, ORX_4 from about 243k raw run files; compares the marginal-median gap, the paired median and the mean version; output fig2_defend_out.json in the same dir; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/REPRO-F2-defend/bars_in_bracket.py: checks whether the bar gaps lie inside the Table II S2 bracket and compares bars with the reported S1 rel; git show 93ba655:v5b/p1/stats.py (lines 112-140: definitions of x, y, y_hat) and 93ba655:v5b/p1b/analysis.py (lines 375-381: how fig1_ladder is built); git show 93ba655:v5b/p1b/episode.py:50-56 (run key format, re-implemented in my script); git blame of protocol lines 116 and 177 vs the date of 93ba655 (pre-registration of the figure design); Read paper.qmd lines 125-200 (Table I, methods, Fig. 2 caption, Table II, S2 text); grep for 'mean' in the paper; pdftotext on papers/paper_1/figures/fig_ladder.pdf to check the bar labels; JSON scan for the 13.3 % value cited at paper.qmd:193

### B65. [minor] REPRO-F5: Fig. 1 text labels overlap

Raised as minor; verification: not adversarially verified.

#### REPRO-F5 (R1 REPRO, minor, wording): Fig. 1 text labels overlap

- **Description.** In the rendered figure, 'queue storage' (fig_plant.py:34, x=3, y=2.35) collides with the centred signal label '(G 6 s, amber 3 s, red ≥ 2 s)' (fig_plant.py:25, x=6, y=2.35), which makes both unreadable.
- **Evidence.**
  - scratch/out/fig_plant.png (pixel-identical to the repo PDF)
  - fig_plant.py@HEAD:25, :34
- **Failure scenario.** The printed figure shows garbled text at the top.
- **How to test.** Render papers/paper_1/figures/fig_plant.pdf to PNG and inspect it.
- **Related claims.** C25

#### G2-F6 (R2 G2, minor, wording): Fig. 1 draws local incident zones and omits the lane-to-lane feed; the labels overlap

- **Description.** The caption is true. The drawing shows the crawl and the slowdown over about 73 % of their edges, while the code applies them to the whole lane 4_1 (240 m) and the whole edge 5 (135 m). It does not show that lanes 2-3 feed only the crawl lane, or that lane changing is off. In the rendered PDF, the 'queue storage' label overlaps the signal label.
- **Evidence.**
  - papers/paper_1/figures/fig_plant.py:25, 27-30, 34
  - REPRO/out/fig_plant_repo.png
  - G2/net_read.out
- **Failure scenario.** Readers infer a short, local incident zone with merging, which is not the simulated mechanism.
- **How to test.** Draw the incidents over the full lane and edge. Mark the 3_2/3_3 -> 4_1 feed, or add 'no lane changing' to the caption. Move one of the two labels.
- **Related claims.** C25

### B66. [minor] REPRO-F7: 'Incident of random type may occur' does not match cell design

Raised as minor; verification: not adversarially verified.

#### REPRO-F7 (R1 REPRO, minor, wording): Line 93 'incident of random type ... may occur' does not match the cell design

- **Description.** In every evaluation cell the incident type is fixed and every seed has an incident; only onset and duration are random (incidents.py:34-39). Line 114 states the cells correctly.
- **Evidence.**
  - paper.qmd:93, :114
  - v5b/d2/incidents.py@e7dd561:16-18, :34-39
- **Failure scenario.** A reader assumes type uncertainty inside each run or cell, which the design does not include.
- **How to test.** Read cell_runs in analysis.py@93ba655:236-253 (one incident per cell).
- **Related claims.** C25

### B67. [minor] S1-F6: S1 family and interval construction not described

Raised as minor; verification: not adversarially verified.

#### S1-F6 (R1 S1, minor, disclosure): Paper omits how the S1 family and intervals are formed

- **Description.** The paper does not state four things. First, the Bonferroni family is m = 8 (2 statements × 4 cells). Second, the five L0 comparisons within S1a are combined by intersection-union with no further correction. Third, every statement must hold in both seed views and fails closed on a missing cell. Fourth, the printed intervals are percentile CIs of the ratio, while the rule uses the CI of median(r − t). None of this changes a number here: all intervals agree in sign, and no runs are invalid or missing.
- **Evidence.**
  - protocol lines 88, 90; addendum R1/R5 (lines 184-185); stats.py@93ba655:63-64; analysis.py@93ba655:487-518
  - sign_consistency.py: 44/44 consistent
- **Failure scenario.** A reviewer questions the multiplicity control across 20 ID-vs-L0 comparisons, or which interval the rule used.
- **How to test.** Add one sentence on the family, the IUT and the interval type.
- **Related claims.** C57, C58, C56

### B68. [minor] S1-F8: Table II shows S1a only against PI; FB also blocks S1a

Raised as minor; verification: not adversarially verified.

#### S1-F8 (R1 S1, minor, wording): Table II shows S1a only against PI; FB also blocks S1a

- **Description.** Row 1 is labelled 'ID vs PI (S1a)'. S1a needs every L0 arm, and R(ID, FB) also meets (a) in no cell (−1.5, +4.8, −2.6, +6.6 %). At q1600 the binding comparison is ID against its own controller, FB. The note p1b_result.md shows both rows.
- **Evidence.**
  - s1_recompute.py: R(ID,FB) a_cells []
  - docs/research/results/p1b_result.md:19-20
- **Failure scenario.** A reader concludes that only PI-ALINEA stood in the way of S1a.
- **How to test.** Add an 'ID vs FB' row, or label row 1 'binding arm'.
- **Related claims.** C69, C64

### B69. [minor] S23-F3: 'Lead vanished within 3 s' is an interpolation artefact

Raised as minor; verification: not adversarially verified.

#### S23-F3 (R1 S23, minor, unsupported-interpretation): 'Lead vanished within 3 s' is an interpolation artefact on a 0/30 s grid, and the lead was never detected

- **Description.** d* = 2.61 s is 30*7.81/(7.81+81.93), a linear interpolation between d = 0 and d = 30 s (protocol :77). No run exists between those points. IP's delay distribution is bimodal (quartiles 125.8 / 175.2 / 289.1 s), and the share of seeds where IP beats PI falls from 54 % to 25 % between d = 0 and d = 30. IP vs PI at d = 0 is 4.5 % [-35.2, 14.6] (S1 level), and 20 % of bootstrap draws give 'never ahead'.
- **Evidence.**
  - v5b/p1/stats.py@93ba655:164-184
  - result.json eval.S3.slow_q1600.d_star
  - s23_dgrid_check.log; s23_recompute_20261019.log
- **Failure scenario.** Readers infer a measured 3-s tolerance; the true break-even could be anywhere in (0, 30) s, or there may be no lead at all.
- **How to test.** Run IP with d in {1, 3, 5, 10, 20} s on fresh seeds; or report 'gone at the first tested delay (30 s)'.
- **Related claims.** C80

### B70. [minor] S23-F4: 'Stayed ahead to ~120 s' omits wide CI and zero margin

Raised as minor; verification: not adversarially verified.

#### S23-F4 (R1 S23, minor, statistics): 'Stayed ahead up to about 120 s' omits the CI [20.1, 168.5] s and a margin of zero at 120 s

- **Description.** In slow_q2000, M_PI is 0.14 s/veh at d = 120 (IP vs PI 0.04 % [-2.84, 5.89]). The 95 % CI of IP vs PI includes 0 at d = 30 and at d = 120. At d = 0 the S1-level CI is [-2.65, 13.12]. The binding arm is PI, which is also the best always-on arm, so that part of the wording is correct.
- **Evidence.**
  - result.json eval.S3.slow_q2000.d_star.all_seeds.ci = [20.14, 168.48]
  - s23_recompute_20261019.log 'IP vs bind at d'
- **Failure scenario.** The robustness ranking of the type plans across cells rests on point break-evens with very wide intervals.
- **How to test.** Report d* with its CI; recompute at 95 % at each grid delay.
- **Related claims.** C79

### B71. [minor] S23-F6: Plateau criterion unattainable at n=100 and tests ORX only

Raised as minor; verification: not adversarially verified.

#### S23-F6 (R1 S23, minor, statistics): Plateau criterion could not pass at n = 100, and it tests ORX only

- **Description.** The pre-registered plateau test needs the 95 % CI of rel_mean(ORX_2, ORX_4) within +-1 point, i.e. a width of 2 points or less. The achieved widths were 15.1 / 5.8 / 6.2 / 4.0 points, so 'about y_hat' was unattainable in every cell regardless of convergence. In slow_q2000 the CI [-1.6, 4.2] includes 0, so non-convergence is not shown there. The test concerns the lower estimator, not 'the bracket'.
- **Evidence.**
  - v5b/p1/stats.py@93ba655:25,123-125
  - s23_recompute_20261019.log plateau rows
- **Failure scenario.** Line 193 presents a precision limit as a substantive finding of non-convergence.
- **How to test.** Compute the CI width per cell, and the n needed for a width of 2 points or less.
- **Related claims.** C76

### B72. [minor] TEXT-F15: Loaded or overstated wording

Raised as minor; verification: not adversarially verified.

#### TEXT-F15 (R1 TEXT, minor, wording): Loaded or overstated wording

- **Description.** Cases:
- 'never better' (line 155): the CI in block_q1600 reaches +6.7 %.
- 'lead' for slow_q1600 (IP vs PI +4.5 % [-35.2, 14.6]).
- 'stayed ahead ... about 120 s' (line 197): CI [20.1, 168.5]; P1 gave 25.8 s.
- 'the lead held' (line 187): only the favourable rows were run or shown.
- 'strong' (lines 67, 155) and 'full set' (line 73).
- 'honest' (title, line 74, line 87 header).
- 'upper limit for any incident-aware controller' (line 102): it holds only for controllers that switch once at onset to an action of A, starting from N.
- **Evidence.**
  - paper.qmd:2, 67, 73, 74, 87, 102, 155, 187, 197
  - p1b_result.json S1 per_cell_stats, cells.*.IP_vs_L0, S3.d_star
- **Failure scenario.** Reviewers read these words as overclaims.
- **How to test.** Replace them with point-estimate and CI wording, and add the scope of the upper limit.
- **Related claims.** C85, C12, C13

### B73. [minor] TEXT-F17: Small internal inconsistencies

Raised as minor; verification: not adversarially verified.

#### TEXT-F17 (R1 TEXT, minor, wording): Small internal inconsistencies

- **Description.** Cases:
- Line 93 says four lanes 'reduce to one'; lines 95 and 110 say 'to two and then to one'.
- Line 114: 'two incident types act on the bottleneck', but the crawl is on the 2-lane edge 4 and the slowdown on the 1-lane edge 5.
- TP is described as 'best of five replicate runs'; it is the main run plus 4 replicates.
- The S2 bracket mixes a median upper bound with a mean lower bound, at level 0.9875; neither is stated (line 145, Table II).
- The C1 'valid-only' remark is vacuous (TEXT-F9).
- **Evidence.**
  - paper.qmd:93, 95, 110, 114, 141, 145, 177
  - p1_incident_information.md:88, 106-110
  - 93ba655:v5b/d2/incidents.py:4-5
- **Failure scenario.** The reader is confused about the geometry and the definitions.
- **How to test.** Edit the text.
- **Related claims.** C13

### B74. [minor] TEXT-F18: Other protocol-required outputs absent (NC row, operating map, tool checks)

Raised as minor; verification: not adversarially verified.

#### TEXT-F18 (R1 TEXT, minor, disclosure): Other outputs required by the protocol and the claim rules are absent

- **Description.** Missing items:
- No NC row anywhere, and the pre-registered Table 1 operating map (every arm, every cell, clean day) is not delivered. In C1's cell, N is worse than NC (320.5 vs 301.7 s/veh), and PI beats NC by only 13.5 % [5.3, 20.8].
- The T0-T4 tool checks and the VSL check (VSL did not enter) are not reported.
- The V100 meter-phase bug and the D1/D2 screens that shaped the design are not mentioned.
- The seed-label deviations (V108) and the demand-only unit test on evaluation seeds 600-601 (V109) are not disclosed.
- **Evidence.**
  - p1_incident_information.md:40, :52-60, :116, :133-136
  - p1b_c1_summary.md:20-23, :41-44
  - p1b_result.md:83-84
  - docs/decisions.md:119, :127, :128
- **Failure scenario.** There is no scale for how much metering helps at all, and hidden pre-checks and variants break the 'every run reported' rule.
- **How to test.** Add an operating-map table or appendix and one disclosure paragraph.
- **Related claims.** C12

### B75. [minor] TEXT-F6: What ID knows is defined inconsistently

Raised as major; verification: reproduce: CONFIRMED/major, defend: CONFIRMED/minor.

#### TEXT-F6 (R1 TEXT, major, discrepancy): What ID knows is defined inconsistently

- **Description.** Line 100 says ID 'knows when an incident starts and ends'. Table I says 'onset (and clearance)'. Line 118 says 'ID knows only that an incident has started', while the same sentence lets plans be 'released back to N when the incident clears'. The protocol says presence and timing: onset and clearance. The P1b-tuned ID plans contain no +back plans, so no number changes.
- **Evidence.**
  - paper.qmd:100, :118, :131
  - p1_incident_information.md:7, :36
  - p1b_result.json tune.arms ID = f40_10 / p20_20_14_e4 (no +back)
- **Failure scenario.** The paper's central concept (the information levels) is ambiguous, and reviewers cannot tell what L1a contains.
- **How to test.** Make line 118 read 'ID knows when an incident starts and ends, but not its type'.
- **Related claims.** C12, C08

#### Verifier R2 reproduce: CONFIRMED / major

I reproduced the core fact: the paper describes what ID (L1a) knows in three ways that do not agree.
- paper.qmd:100 says ID 'knows when an incident starts and ends'.
- Table I (paper.qmd:131) says 'incident onset (and clearance)'.
- paper.qmd:118 says 'ID knows only that an incident has started'.

The code and protocol match :100, not :118. The protocol (p1_incident_information.md:7, :36, the same at 93ba655 and HEAD) defines L1a as 'presence and timing ... (onset and clearance)'. Addendum line 35 says ID chooses from A = (G u G_PI) x {stay, back}. In the code at 93ba655, ID is the best pooled action over that whole 120-action set, which includes the +back plans. A +back plan returns to N at the clearance tick (switch_schedule uses t_off). So the information set ID was tuned over includes the clearance time. That makes :118 false as written: it is not true of the L1a level as defined and tuned.

I recomputed the selection from the raw tuning runs (v108, seeds 7400300-339, 80 pooled runs per action, no files missing).
- ID is f40_10 at q1600 and p20_20_14_e4 at q2000. Both are 'stay' plans and match the JSON.
- The best +back action ranks 32nd of 120 at both demand levels.
- The overall winner is a stay plan, so restricting A to stay plans would select the same ID. No ID number in the paper changes.
- C1 has no ID arm (only IP vs PI, block_q1600) and contains no +back plans, so C1 is not affected either.

Small inaccuracy in the finding: the onset-only statement and 'released back to N when the incident clears' are in adjacent sentences on source line 118, not in the same sentence. The core fact still holds. The severity stays major under the definitions: a paper statement about the central concept is false as written, and the headline survives unchanged.

Checks: sed -n 95,135p paper.qmd and grep of the ID/presence/clearance/onset wording in paper.qmd; sed -n 1,45p p1_incident_information.md; git diff 93ba655 HEAD on the protocol and addendum (empty); grep of the addendum; git show/grep at 93ba655: v5b/p1b/analysis.py (fit_switch, sw), v5b/p1b/run.py:230-246, v5b/p1b/family.py actions, v5b/p1/family.py actions/best_by_median, v5b/p1/meters.py switch_schedule, v5b/p1b/episode.py run_key/make_spec/check_spec; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/TEXT-F6-reproduce/check_id_actions.py (output check_id_actions.out): tuned ID/IP arms and A_size from p1b_result.json; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/TEXT-F6-reproduce/recompute_id.py (output recompute_id.out): independent recomputation of the ID and IP selection over 120 actions from raw v108 tuning runs, plus the rank of the best +back plan; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/TEXT-F6-reproduce/check_back_timing.py (output check_back_timing.out): +back runs return at t_off, stay runs never return; Inline python: p1b_c1_result.json frozen_arms, cell, and +back count; p1_result.json (v99) ID/IP arms (q1600 ID f70_8; q2000 ID f40_10, IP slow c800+back)

#### Verifier R2 defend: CONFIRMED / minor

The inconsistency is real and survives my best defence. Six sources say ID knows the clearance: paper line 100 ('knows when an incident starts and ends'), line 69 ('incident presence'), line 155 ('an incident is on'), Table I line 131 ('onset (and clearance)'), the protocol at p1_incident_information.md:7 ('presence and timing ... onset and clearance'), and addendum p1b_addendum.md:35 (ID chooses from G u G_PI x {stay, back}). The code agrees. At 93ba655, v5b/p1b/analysis.py:134-140 (fit_switch) tunes ID over the full set A_q, and that set includes the back plans. Those plans switch back to N at the clearance tick (v5b/p1/meters.py:203-215; raw run c1800-f40_10+back_block_q1600_s7400300: t_back = t_off = 582). Only line 118 disagrees: 'ID knows only that an incident has started' is false as written. The same sentence even says that plans for 'Both' ID and IP can be 'released back to N when the incident clears'.

Defence that holds, and why I lower the severity. (1) I recomputed the tuning myself from the 80 raw tuning runs per action (seeds 7400300-339, slow + block pooled, 120 actions per q). The tuned ID plans are both stay plans. At q1600 the best is f40_10 with a median of 211.6 s, against 295.5 s for the best back plan (c800+back). At q2000 the best is p20_20_14_e4 with 381.3 s, against 477.4 s for the best back plan. So the plan is the same whether ID knows only the onset or onset plus clearance. ID's numbers, and the S1a and S1b rows that use ID, are the same under either reading. (2) In all 400 ID evaluation runs the meter never switched back (t_back is None). The 'presence' definition was applied as the protocol says, and the evaluated ID plans in fact used only the onset. (3) S1b stays fair. IP uses the clearance in one cell: slow q1600, plan c1000+back, which switched back at t_off in 100 of 100 runs. ID could also choose back plans, so the 16.2 % IP-vs-ID gain there measures type information (type makes the clearance useful), not extra clearance access. (4) The definition section (line 100) and Table I state the level clearly. Line 118 can be read as a shorthand in which 'only' contrasts ID with IP's type knowledge. So the failure scenario, 'reviewers cannot tell what L1a contains', is overstated.

What remains is one sentence that contradicts the paper's own definition, with no effect on any number, any verdict or the pre-registration. Under the given definitions this is a 'small inconsistency' in wording, so minor, not major. Fix: line 118 should read 'ID knows when an incident starts and ends, but not its type'. Optionally, Table I could note that ID's tuned plans did not use the clearance and IP's did in one cell.

Checks: Read paper.qmd lines 90-140 and grepped for clear/onset/knows/presence/ID wording (lines 35, 69, 100, 118, 131-132, 155); Read p1_incident_information.md lines 1-60 and grepped p1b_addendum.md for the ID / clearance definition; git show 93ba655: v5b/p1b/analysis.py fit_switch, v5b/p1b/run.py stage_tune, v5b/p1/meters.py switch_schedule, v5b/p1b/episode.py back/clearance handling; Independent recomputation of the ID and IP tuning and the evaluation switch-back counts from raw runs: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/verify2/TEXT-F6-defend/id_tune_recompute.py (output id_tune_recompute.out.json in the same dir); Inspected one raw back-plan run (t_back = t_off = 582) to confirm a back plan uses the clearance time

### B76. [info] C1-F9: C1 throughput co-headline not reported

Raised as info; verification: not adversarially verified.

#### C1-F9 (R1 C1, info, missing-evidence): C1 throughput (co-headline metric) not reported

- **Description.** Under the project's metric rule, served throughput is a co-headline with delay. For C1 it supports the result: median served 1140 veh/h for IP vs 1074 for PI. The V109 spill share is 0.05 for IP and 0.32 for PI (queue tail within 50 m of the entry). Median depart delay is about 0.1 s for both, so there is no insertion backlog. The paper reports only delay for C1.
- **Evidence.**
  - result.json c1.rows (median_served_vph, spill_share, median_depart_delay_s)
  - c1_spill.py output
- **Failure scenario.** A reviewer asks whether IP buys delay by holding vehicles back. The data say no, but the paper does not show it.
- **How to test.** c1_spill.py
- **Related claims.** C71

### B77. [info] CTRL-F13: No data leakage found

Raised as info; verification: not adversarially verified.

#### CTRL-F13 (R1 CTRL, info, data-leakage): No data leakage found in tuning, plan selection or the C1 arms

- **Description.** Every tuned choice and G_PI is reproduced exactly from tuning-seed runs only. Run-file mtimes separate the stages. Seed sets are disjoint: P1 200-259/500-599; P1b 260-279/300-339/600-699; C1 700-799; replicates +k*1e7. There is one code commit per study. The C1 frozen arms (c1800 -> p20_20_16_e4; PI p70_120_8_e4) match the P1b tuning, and the committed p1b_result.json tune.arms equals the raw result. My C1 recomputation gives 16.2 % [7.3, 23.7], diff 41.4 [16.6, 65.7]. The only evaluation-seed selections are OR_in (by design), the Fig. 2 strongest L0 and the d* binding arm (both conservative).
- **Evidence.**
  - /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/CTRL/out/retune.json, seed_audit.json, c1_check.txt
- **Failure scenario.** n/a
- **How to test.** Re-run the listed scripts.
- **Related claims.** C47, C50

### B78. [info] CTRL-F14: Unequal tuning freedom across arms

Raised as info; verification: not adversarially verified.

#### CTRL-F14 (R1 CTRL, info, hidden-assumption): Unequal tuning freedom across arms

- **Description.** Candidates per q: N 50, FX 20, FB 30, PI 180, AD 3 (with FB fixed), ID 120, IP 2 x 120. Selection is out of sample, so IP's larger menu with fewer seeds per choice (40 vs 80) does not inflate its evaluation score. Several choices sit on grid edges: FX c2600; N at q2000 K_F = 10; IP block1600 K_P = 20 and n_crit = 16; PI at q2000 K_P = 20; AD eta = 0.5.
- **Evidence.**
  - result.json tune.grid_edges_report_only; v5b/p1/family.py@93ba655:21-36
- **Failure scenario.** Reviewers question whether the baseline is strong enough.
- **How to test.** Report grid edges in the paper, as the protocol requires.
- **Related claims.** C26, C42

### B79. [info] FU2-1-F5: Round-1 VERIFIED verdicts on C66, C69, C71 contradict the tracers' own failure points

Raised as info; verification: not adversarially verified.

#### FU2-1-F5 (R2 FU2, info, discrepancy): Round-1 VERIFIED verdicts on C66, C69, C71 contradict the tracers' own failure points

- **Description.** Each of these tracers listed a mismatch in its failure points but still gave VERIFIED:
- S1 tracer on C66: the controller-family change;
- S1 tracer on C69: the inverted caption;
- C1 tracer on C71: 16.2 % vs 17.3 %.

FU1-C4's VERIFIED on C64 tested only the drain convention. Under the audit's 'matches as written' rule, all four headline claims are PARTIALLY SUPPORTED. The computed numbers and the pre-registered verdicts are unchanged: S1a FAIL, S1b PASS, C1 CONFIRMED.
- **Evidence.**
  - FU2-1/claims_full.txt (round-1 and FU1 claim texts)
  - critic2/verdict_conflicts.out
- **Failure scenario.** The final report states VERIFIED for sentences that the audit itself found misleading as printed.
- **How to test.** Re-read the failure_points of C66, C69 and C71 in wf_result.json against the VERIFIED definition.
- **Related claims.** C64, C66, C69, C71, FU1-C3, FU1-C4, FU1-C7

### B80. [info] G2-F7: The protocols give node-to-node lengths, not the simulated lane lengths

Raised as info; verification: not adversarially verified.

#### G2-F7 (R2 G2, info, discrepancy): The protocols give node-to-node lengths, not the simulated lane lengths

- **Description.** screen_D2_incidents.md A2 says lane 4_1 is 280 m long, and p1_incident_information.md says edge 5 is 155 m. The cached net has lanes of 240.0 m and 135.0 m. The differences are the 20-m-radius zipper junctions (internal lanes 40.22 and 40.06 m), which the incidents do not slow. The paper gives no lengths, so only the protocols are affected.
- **Evidence.**
  - docs/research/protocols/screen_D2_incidents.md:92
  - docs/research/protocols/p1_incident_information.md:21
  - G2/net_read.out
- **Failure scenario.** Any paper text or calculation that takes lengths from the protocols (for example, crawl crossing time 280 s instead of 240 s) would be off by about 15 %.
- **How to test.** Parse the lane lengths in bn4.net.xml.
- **Related claims.** C37

### B81. [info] G5-F6: slow_q1600 c* is non-monotone and interpolated; a 60-s late return beats the exact return

Raised as info; verification: not adversarially verified.

#### G5-F6 (R2 G5, info, statistics): slow_q1600 c* is non-monotone and interpolated; a 60-s late return beats the exact return

- **Description.** M_PI(c) = 7.81, 12.08, -14.19 s/veh at c = 0, 60, 180. c* = 115.2 s is a linear interpolation with no run between 60 and 180 s. The CI is [0, 156.2], and 20 % of bootstrap draws are 'never ahead'. IP with c=60 beats PI by 6.9 % [3.7, 13.9], while IP at the exact clearance gives 4.5 % [-24.4, 12.8]. This suggests that the tuned return time is not optimal and that the plan is noise-sensitive. Post hoc, so it should not be over-read.
- **Evidence.**
  - p1b_result.json S3.slow_q1600.c_star
  - g5_recompute_20261019.log (c60_only row)
- **Failure scenario.** Citing 'c* about 115 s' as a precise tolerance.
- **How to test.** Re-run g5_recompute.py and read the slow_q1600 c* per_arm M values.
- **Related claims.** C80

### B82. [info] G8-F7: Several cited works remain abstract-only after all legal routes failed

Raised as info; verification: not adversarially verified.

#### G8-F7 (R2 G8, info, missing-evidence): Several cited works remain abstract-only after all legal routes failed

- **Description.** No legal full text could be reached for: Tympakianaki2014 (closed; the OA 2012 EWGT Procedia version is behind ScienceDirect 403; TUC behind Anubis), Wang2014 (closed; TUC behind Anubis), Wu2014 (CC BY-NC-ND, but ScienceDirect 403, journal site timed out, Elsevier API needs a key), Spiliopoulou2010 and Carlson2010/2011 (EPFL records hold only a license file; TUC behind Anubis), Smaragdis2003/2004, Carlson2014, and the Sun2013 TRR article. Claims resting on them (C02 partly, C05, C06, C16 partly, C44, the Wu part of C07) stay at abstract level. Wu's 25 % delay saving has an unnamed baseline.
- **Evidence.**
  - G8/access_log.txt
  - G8/oa_locations_output.txt
  - G8/s2_oa_output.txt
- **Failure scenario.** A body-text detail (e.g., Wang's exact PI form or Wu's baseline) contradicts the paper's wording.
- **How to test.** Get these PDFs through the university library and add [VERIFY] marks in the qmd until they are read.
- **Related claims.** C02, C05, C06, C07, C16, C44

### B83. [info] HEADLINE-F8: slow_q1600 median and mean disagree in sign

Raised as info; verification: not adversarially verified.

#### HEADLINE-F8 (R1 HEADLINE, info, statistics): slow_q1600: median and mean disagree in sign for IP vs PI

- **Description.** Meaning: In slow_q1600, IP (an open-loop constant rate, c1000+back) has a paired-median rel vs PI of +4.5 % but a mean rel of -13.5 %, and vs ID +16.2 % (median) against +4.1 % (mean). So IP sometimes loses heavily to PI. This fits the paper's robustness remark at :197, but Table II shows only the median.
- **Evidence.**
  - /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/HEADLINE/pairing_check.py output
- **Failure scenario.** Table II's 4.5 % in slow_q1600 hides a heavy right tail of IP's delay.
- **How to test.** Report the mean or the share of seeds where IP < PI (54 %) alongside the median.
- **Related claims.** paper.qmd:176

### B84. [info] HEADLINE-F9: Headline numbers verified from raw data

Raised as info; verification: not adversarially verified.

#### HEADLINE-F9 (R1 HEADLINE, info, discrepancy): Claim check (a)-(d), seeds and data integrity: all headline numbers VERIFIED from raw per-seed data

- **Description.** Meaning: The paper's headline numbers come from 100 paired seeds per comparison: rel = median(r - t)/median(r), with a percentile bootstrap that resamples seeds jointly. Verification (derived; own numpy code, no v5b imports): I loaded all 344,852 P1b and 1,100 C1 raw run files and re-derived every tuned arm from the 40 tuning seeds. The arms match the run record and the C1 frozen arms. All headline values match (see recomputations). The point estimates are exact. The CI bounds agree within Monte Carlo noise, and exactly when the repo's fixed bootstrap seeds are replayed in my code. S1b passes in slow_q2000 and block_q1600 (diff-CI lower bounds 21.4 s and 17.3-21.4 s > 0, rel ≥ 10 %), and the point rel is ≥ -5 % in all cells. S1a fails: vs PI, rel < 10 % in every cell, and slow_q1600 is -17.9 % < -5 %. C1 is CONFIRMED (16.2 % ≥ 10 %, diff-CI lower bound 16.6 s > 0). Seeds: exactly 7,400,600-699 and 7,400,700-799, identical ids in each pair, none missing. Each pair shares demand seed, SUMO seed, incident onset/duration and generated count. No invalid runs, teleports or collisions. All P1b files carry code_commit 93ba655 and all C1 files e7dd561; code_dirty = False. Evaluation files are dated 13:07:56-20:28:55 (after the 13:07:53 sentinel), tuning files end at 13:07:52, and C1 files run 21:27:50-21:28:59 (after the sentinel). No other run directory holds seeds 7,400,600-799 except 6 post-hoc verification re-runs (20:40). Code: the v5b working tree equals e7dd561, and 93ba655 -> e7dd561 adds only confirm_c1.py. Failure points: the arm selection (F1), the comparator choice (F2), and bootstrap MC noise (F4). The delay metric is mean(departDelay + timeLoss) over all trips (episode.py:254, :271@93ba655), so origin and meter queues are included only because every run drained.
- **Evidence.**
  - /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/HEADLINE/headline_out.json
  - v5b/p1b/run.py:51-52@93ba655 (SEEDS); v5b/p1b/confirm_c1.py:52, :56-57, :121-124@e7dd561
  - v5b/p1/stats.py:14-15, :48-64, :79@93ba655
  - ~/work/phd/v5b1_runs/P1B_EVAL_STARTED.json, P1B_C1_STARTED.json
- **Failure scenario.** None found for the arithmetic. See F1, F2 and F4 for the interpretation and precision limits.
- **How to test.** Re-run load_runs.py, tune.py, headline.py, repo_seed_replay.py and pairing_check.py from the scratch dir.
- **Related claims.** paper.qmd:155, paper.qmd:174-176, paper.qmd:187

### B85. [info] LIT-F14: PI degradation with runners unexplained vs literature

Raised as info; verification: not adversarially verified.

#### LIT-F14 (R1 LIT, info, unsupported-interpretation): The literature predicts stationary accuracy under red-light violations; the paper does not explain PI's degradation with runners

- **Description.** Papageorgiou 2008 §2.7.1: 'Stationary accuracy is also guaranteed if there are errors in the implementation of the calculated q (e.g., due to traffic light operation inaccuracies, red-light violations)'. Line 187 reports that always-on PI 'itself degraded' with runners. Possible reasons include transients, clipping at the rate bounds, plans tuned without runners, or safety interactions. None is discussed.
- **Evidence.**
  - Papageorgiou 2008 p. 541
  - paper.qmd:187
- **Failure scenario.** A reviewer asks why an integral law did not absorb the runners.
- **How to test.** In the runner rows, check how often PI's q sits at the 200 or 2618 bound and how the edge count tracks n_crit.
- **Related claims.** C19, C63

### B86. [info] LIT-F15: Bib metadata state

Raised as info; verification: not adversarially verified.

#### LIT-F15 (R1 LIT, info, citation): Metadata state of the bib (for the record)

- **Description.** tools/verify_bib_crossref.py: 15 OK, 1 CHECK (the Smaragdis2003 Crossref title includes the author names; the bib title is correct), 5 NO-DOI. My full field comparison found every DOI entry matching Crossref on authors, volume, issue, pages and year. The only difference is the Lopez2018 author order, where Crossref and OpenAlex put Wiessner second; the bib follows DLR's recommended citation (sumo.dlr.de/docs/Publications.html). All five no-DOI entries were confirmed by hand, apart from the TOPS2005 author (LIT-F9). Frejo2021a is in the bib but never cited. The rendered PDF reference list has no unresolved keys.
- **Evidence.**
  - /tmp/.../LIT/crossref_tool_output.txt
  - /tmp/.../LIT/compare_bib_full_output.txt
  - /tmp/.../LIT/paper_pdf.txt
- **Failure scenario.** None.
- **How to test.** Re-run the scripts after any bib edit.
- **Related claims.** C02, C03, C04, C05, C10, C16, C19, C21

### B87. [info] LIT-F16: FB and PI laws match ALINEA/PI-ALINEA structure

Raised as info; verification: not adversarially verified.

#### LIT-F16 (R1 LIT, info, discrepancy): FB and PI laws match the ALINEA and PI-ALINEA structure; the cycle rule follows Papageorgiou 2008

- **Description.** FB is the ALINEA integral law with anti-windup by truncation, re-using the clipped value (Papageorgiou 2008 §2.7.1). PI is the velocity-form PI extension; at a plan's first update n(k-1) is set to n(k), so the P term starts at zero. The e5 variant measures the one-lane section 420 m downstream of the signal (node 3 at x = 410 m; the 2-to-1 zipper at x = 830 m), consistent with the distant-bottleneck use of PI-ALINEA. Cycle c = max(11, 7200·M/q) is Papageorgiou 2008 eq. (3), with a longer minimum cycle (11 s instead of 6 s). Not verified: whether 6 s of green plus 3 s of amber passes about two vehicles per lane per cycle, which the nominal rate assumes; this matters mainly for the constant-rate arms.
- **Evidence.**
  - v5b/p1b/meters.py@93ba655:37-42, 87-112
  - v5b/d1/netgen_bn4.py@93ba655:23-27
  - Papageorgiou 2008 eq. (3) p. 543
- **Failure scenario.** If actual discharge per green differs from 2 vehicles per lane, the constant rates in N/FX/IP plans are mislabelled (feedback laws compensate).
- **How to test.** From the raw runs, compare measured meter discharge per cycle with the commanded q (plant domain).
- **Related claims.** C04, C16

### B88. [info] LIT-F8: PI-ALINEA first proposed in Wang & Papageorgiou 2006

Raised as info; verification: not adversarially verified.

#### LIT-F8 (R1 LIT, info, citation): PI-ALINEA was first proposed in Wang & Papageorgiou 2006

- **Description.** Frejo 2021a (full text, ref. [21]) credits the proposal of PI-ALINEA to Wang & Papageorgiou, ITSC 2006, pp. 426-431, doi:10.1109/itsc.2006.1706778 (Crossref verified). Wang 2014 is the theory-and-simulation journal paper. Citing 2014 alone is acceptable; adding 2006 gives priority correctly.
- **Evidence.**
  - /tmp/.../LIT/frejo2021a_raw.txt lines 135, 1796-1797
- **Failure scenario.** A minor priority complaint from a reviewer.
- **How to test.** Optionally add the 2006 citation.
- **Related claims.** C04, C16

### B89. [info] PLANT-F13: Collision check excludes junctions

Raised as info; verification: not adversarially verified.

#### PLANT-F13 (R1 PLANT, info, hidden-assumption): The collision check excludes junctions, including the 40-m zipper merges

- **Description.** --collision.check-junctions false is the SUMO default. A collision is registered only when the gap on the same lane falls below minGap (2 m). Conflicts between the converging internal lanes of zipper junctions 4 and 5 are not checked.
- **Evidence.**
  - v5b/d1/sumo_runner.py@93ba655:105
  - SUMO MSFrame.cpp:414; MSLane.cpp:1991-1999
- **Failure scenario.** 'No collisions' does not cover merge conflicts.
- **How to test.** Re-run a small diagnostic set with collision.check-junctions true (outside the claim runs).
- **Related claims.** C83

#### G3-F1 (R2 G3, minor, disclosure): The scope of the zero-collision count is not stated: junction (zipper) conflicts are not checked

- **Description.** All runs used --collision.check-junctions false, so SUMO checked only same-lane gaps (below minGap 2.0 m), including gaps on a single internal lane. It never checked overlap between vehicles on foe internal lanes. In this plant, lane changing is disabled, so the 4->2 and 2->1 lane drops happen only on the 40-m internal lanes of zipper junctions 4 and 5 (80 m of the 985-m route). This is the only place where vehicles from different lanes meet. The paper (line 197) says 'no collisions occurred' without saying what was checked. A collision on those internal lanes would also not trigger H-R4 FAIL, so the run would stay valid.
- **Evidence.**
  - v5b/d1/sumo_runner.py@93ba655:105 and @e7dd561:105
  - SUMO MSLane.cpp:1710-1712, 4725-4730 (foe-lane check only when check-junctions is true); MSFrame.cpp:414 default false
  - G3/net_internal_map.out (zipper internal lanes and foe matrices)
  - v5b/d1/plant.py@e7dd561:26-27 (lane changing disabled, minGap 2.0)
  - v5b/d1/sumo_runner.py@e7dd561:203-204; v5b/p1b/episode.py@93ba655:255
- **Failure scenario.** At a congested zipper, two vehicles on :5_0_0 and :5_0_1 overlap for a few steps and then separate before both are on lane 5_0. SUMO logs nothing, the run counts as collision-free and valid, and the paper's 'no collisions' includes it.
- **How to test.** Re-run a sample of the P1b slow-cell runs that logged emergency braking on ':5_0_*' (e.g. f20_6_slow_q1600_s7400262, f70_6_slow_q1600_s7400263, f70_14_slow_q1600_s7400264; 3,304 such runs in G3/lane_by_cell.out), and C1 runs with braking on lane 4_0 (IP s7400701, 7400713, 7400766, 7400777; PI s7400720, 7400726, 7400738, 7400740; G3/c1_log_lanes.out), using --collision.check-junctions true and nothing else changed. Then add to the paper: 'collisions = same-lane gaps below minGap; junction overlaps checked in N diagnostic runs'.
- **Related claims.** C83, C72

#### G3-F4 (R2 G3, info, missing-evidence): Junction-check re-runs: identical outputs and 0 collisions in the 4 C1 runs tested

- **Description.** I re-ran 4 runs from e7dd561 with only --collision.check-junctions true changed: C1 block_q1600 s=0, IP (c1800 -> p20_20_16_e4) and PI (p70_120_8_e4), seeds 7400750 (most off-edge-4 emergency events) and 7400760 (a REPRO seed). Results: collisions 0 in the JSON, the statistic-output and the log. Emergency stops 1/0/3/0 and emergencyBraking 4/4/10/5 equal the stored values. Run hashes are identical (36ab9ea83f058ae0, 9332bbdd6ef031ee, 7bd5622876b2796c, 550811123cf235e7). So the flag does not change dynamics (action warn, stoptime 0), and enabling it would not have changed C1 delays. Limit: these 4 runs had no emergency braking on lane 4_0 or on any internal lane, so they are a weak test of the high-conflict cases named in G3-F1.
- **Evidence.**
  - G3/compare_cj.out
  - G3/spot_run_cj.sh; G3/code_e7dd561 (patched) vs G3/code_e7dd561_orig: diff shows only sumo_runner.py:105
  - G3/scan_c1_emerg.out (seed choice)
- **Failure scenario.** Using these 4 runs to claim 'no junction collisions anywhere' would over-generalise to the P1b slow cells, which have braking on internal lanes.
- **How to test.** See G3-F1: re-run the listed high-conflict seeds with the flag on (each run takes about 1 s of CPU).
- **Related claims.** C83, C72, C40

#### G3-F5 (R2 G3, info, hidden-assumption): Validity views (C72/C40) depend on collisions only through H-R4 FAIL; no effect found

- **Description.** valid = drained and all trips recorded and health != FAIL. A collision affects validity only through H-R4. Because junction overlaps are not detected, they can never make a run invalid. In the 4 re-runs with the check on, validity and health codes did not change (WARN: H-R4b, H-R4e, H-R5), so there is no evidence that C72's 'no invalid runs' or C40's integrity checks would change. Untested beyond those 4 runs.
- **Evidence.**
  - v5b/p1b/episode.py@93ba655:255
  - v5b/d1/sumo_runner.py@e7dd561:203-204
  - G3/compare_cj.out (valid True, health WARN, codes unchanged)
- **Failure scenario.** If junction collisions existed in some C1 runs, they would be counted valid and the valid-only view would still equal the all-seeds view.
- **How to test.** Same re-runs as G3-F1; count H-R4 FAIL with the flag on.
- **Related claims.** C72, C40

### B90. [info] PLANT-F14: Floating-point artefact in signal clock

Raised as info; verification: not adversarially verified.

#### PLANT-F14 (R1 PLANT, info, bug): Floating-point artefact in the continuous signal clock

- **Description.** After a change of cycle length, the anchor becomes non-integer. Phases computed with % can then fall 1e-15 on the wrong side of the 0, 6 or 9 boundaries, giving occasional 5-s or 7-s greens (seen in my own re-implementation with grid rates). Amber stayed 3 s and red at least 2 s. Constant-rate plans anchored at 40.0 show no artefact.
- **Evidence.**
  - v5b/d1/meter_signal.py@93ba655:24-34
  - signal_clock_check.out, signal_clock_debug.py, signal_const_rate.out
- **Failure scenario.** Rare plus or minus 1-s green errors in feedback arms; negligible effect.
- **How to test.** Round the phase (for example round(ph, 9)) and re-run the unit test with rate sequences from the grid.
- **Related claims.** C35

### B91. [info] PLANT-F15: Protocol edge lengths differ from built network

Raised as info; verification: not adversarially verified.

#### PLANT-F15 (R1 PLANT, info, discrepancy): Protocol edge lengths differ from the built network

- **Description.** The protocols describe edge 5 as '155 m' and lane 4_1 as '280 m'. The built lanes are 135 m and 240 m, because the zipper internal lanes take about 20-40 m of the node spacing. This is not in the paper.
- **Evidence.**
  - docs/research/protocols/p1_incident_information.md:21; screen_D2_incidents.md:92
  - bn4.net.xml lane lengths
- **Failure scenario.** Wrong lengths if they are copied into the paper.
- **How to test.** Use the net.xml lane lengths.
- **Related claims.** C37

### B92. [info] PROV-F8: Frozen worktrees deleted; frozen launch inferred

Raised as info; verification: not adversarially verified.

#### PROV-F8 (R1 PROV, info, reproducibility): The frozen worktrees were deleted; the 'frozen' launch is inferred, not inspectable

- **Description.** git worktree list shows only the two main worktrees, and /home/catalin/work/phd/p1_frozen_85f7d34 and p1b_frozen_93ba655 no longer exist. For P1b, the frozen launch is inferred: code_commit 93ba655 differs from main HEAD 8e10812 at launch. For C1, main HEAD was e7dd561 at launch, so frozen and main cannot be told apart. Either way, code_dirty=false and the tree guard pin the code. Reproduction relies on the commits (the BASELINE doc gives the worktree-add steps).
- **Evidence.**
  - git worktree list --porcelain
  - journalctl --user: p1b-run.service, p1b-c1.service command lines (no PYTHONPATH, working directory not logged)
- **Failure scenario.** An auditor cannot confirm the working directory of the run, only the commit and the clean state.
- **How to test.** git -C REPO worktree list; journalctl --user -u p1b-run
- **Related claims.** C54, C70

### B93. [info] PROV-F9: Hashed P1 page lists D1-D5 as open choices

Raised as info; verification: not adversarially verified.

#### PROV-F9 (R1 PROV, info, reproducibility): The hashed P1 page still lists D1-D5 as open choices; their resolution is recorded elsewhere

- **Description.** The page version recorded by P1 and P1b (0e8d49b) ends with the open decisions D1-D5 (meter signal and others). They were resolved in decisions.md V100 (c225049, 16:54) and through required CLI flags recorded in P1_EVAL_STARTED.json args and the TCHECK decisions. The page hash alone does not pin the decisions. The page was also amended after the P1 smoke data, on smoke seeds only.
- **Evidence.**
  - p1_incident_information.md@0e8d49b:191-199
  - P1_TCHECK_RECORD.json decisions
- **Failure scenario.** Someone re-deriving the design from the hashed page alone could pick a different meter-signal option.
- **How to test.** git show 0e8d49b:docs/research/protocols/p1_incident_information.md | tail -10
- **Related claims.** C53

### B94. [info] REPRO-F10: Reproducibility positives; build artefacts not versioned

Raised as info; verification: not adversarially verified.

#### REPRO-F10 (R1 REPRO, info, reproducibility): Reproducibility positives, plus build artefacts not under version control

- **Description.** Figures regenerate pixel-identically from the committed JSONs. Those JSONs are byte-identical to the raw result.json files. All 255,182 P1b evaluation files carry 93ba655 and all 1,100 C1 files carry e7dd561, with write times inside the run windows. netconvert rebuilds an identical network. 4/4 spot re-runs are identical in every field. 99/99 unit tests pass. However, the figure PDFs and paper.pdf are gitignored, and fig_c1_delay.py is an orphan. The tests do not cover the figure scripts or compare against stored raw results.
- **Evidence.**
  - papers/paper_1/.gitignore (paper.pdf, figures/*.pdf)
  - scratch/chain_integrity.py, scratch/spot_compare.py outputs
- **Failure scenario.** A future regeneration with a changed JSON or library silently changes the figures, with no versioned reference to compare against.
- **How to test.** Re-run the scratch scripts listed in checks_run.
- **Related claims.** C68, C75

### B95. [info] S1-F10: summary.md labels page path with addendum hash

Raised as info; verification: not adversarially verified.

#### S1-F10 (R1 S1, info, reproducibility): Auto-generated summary.md labels the page path with the addendum's hash

- **Description.** v108/summary.md (and docs/research/results/p1b_summary.md) prints 'Page docs/research/protocols/p1_incident_information.md (sha256 2b3d3ccb957a)'. The hash 2b3d3ccb… is p1b_addendum.md's; the base page's hash is fed27bf6…. The values in result.json are labelled correctly.
- **Evidence.**
  - ~/work/phd/v5b1_runs/p1b/v108/summary.md line 3; result.json page/page_sha256/base_page_sha256; sha256sum of both protocol files at 93ba655
- **Failure scenario.** A provenance check of the summary against the base page hash fails.
- **How to test.** Compare sha256 of both protocol files with the summary header.
- **Related claims.** 

### B96. [info] S1-F11: 'Never beat PI' is a median statement

Raised as info; verification: not adversarially verified.

#### S1-F11 (R1 S1, info, wording): 'never beat always-on PI' (line 197, crawl 2000) is a median statement; IP beat PI on 32/100 seeds

- **Description.** In block_q2000, IP equals PI's controller started at onset. Per seed, IP is better on 32 seeds, worse on 61 and tied on 7. Median rel is −2.1 % [−6.6, 0.0]. 'Never' refers to the median detection-delay break-even, not to individual incidents. This is outside the claims assigned to me but uses the same runs.
- **Evidence.**
  - zero_diffs.py block_q2000 IP vs PI: d<0 61, d>0 32, zero 7
  - paper.qmd:197
- **Failure scenario.** A reader reads 'never' as 'on no incident'.
- **How to test.** Write 'did not beat ... in median'.
- **Related claims.** C67

### B97. [info] S1-F9: Integrity checks passed; tiny selection margins for two IP plans

Raised as info; verification: not adversarially verified.

#### S1-F9 (R1 S1, info, reproducibility): Integrity checks passed; selection margins are tiny for two IP plans

- **Description.** Everything checked is consistent. All 3,200 S1 run files carry commit 93ba655, valid = true and drained = true, with matching fields and identical incident windows across arms. p1b_result.json is byte-identical to the raw result.json. The protocol hashes match. All tuned arms were re-derived exactly. However, two IP plans won tuning by noise-level margins. IP block_q1600 (p20_20_16_e4) beat p20_20_14_e4 by 0.15 s/veh, and IP slow_q1600 (c1000+back) beat PI's own controller by 4.05 s/veh. This does not bias the evaluation, which uses separate seeds, but it explains the fragility of slow_q1600.
- **Evidence.**
  - load_eval.py (0 problems); cmp of the two result.json files; tune_check.py top-2 margins
- **Failure scenario.** None for S1. A different set of tuning seeds could pick a different plan in slow_q1600 or block_q1600.
- **How to test.** Report the tuning margin of the chosen IP plans.
- **Related claims.** C66, C67

### B98. [info] S23-F7: S2 bracket mixes estimands and confidence levels without disclosure

Raised as info; verification: not adversarially verified.

#### S23-F7 (R1 S23, info, hidden-assumption): S2 bracket mixes estimands and confidence levels without disclosure

- **Description.** The upper end x is the 0.9875 upper CI bound of the median-version rel(IP, OR_in). The lower end y is the 0.9875 lower CI bound of the mean-version rel_mean(IP, ORX_4). This is as pre-registered (protocol :106-107, with reasons), but the paper states neither the versions nor the level. A bracket of one quantity assumes the median and mean gains coincide. In slow_q1600, OR_in is 15.1 % (median) vs 38.9 % (mean). A consistent mean-version bracket gives [-0.4, 45.7], [-2.4, 19.7], [0.4, 27.6], [3.5, 21.5], so the numbers are not materially changed.
- **Evidence.**
  - v5b/p1/stats.py@93ba655:112-126
  - s23_recompute_20261019.log OR_in mean/median rows
- **Failure scenario.** A reviewer questions what the bracket bounds; in principle y > x is possible.
- **How to test.** Report both versions, or state the construction in Table II's caption.
- **Related claims.** C86, C59

### B99. [info] S23-F8: Table II d* row lacks CIs and binding arms

Raised as info; verification: not adversarially verified.

#### S23-F8 (R1 S23, info, missing-evidence): Table II d* row lacks CIs and binding arms; '>240' is an all-arm censoring

- **Description.** Missing details per cell:
- block_q1600: every L0 arm is above the grid; the binding arm is 'N' only by tie order; CI [192.8, 240].
- block_q2000: 'never ahead' is against PI only; FB's own d* is 196.8 s.
- slow_q1600: 2.6 s is interpolated (see S23-F3).
- **Evidence.**
  - result.json eval.S3.*.d_star.all_seeds.per_arm
- **Failure scenario.** Readers over-read the precision or the generality of the d* row.
- **How to test.** Add CI and binding arm to Table II.
- **Related claims.** C86

### B100. [info] S23-F9: TP wording 'best of five replicate runs' is inaccurate

Raised as info; verification: not adversarially verified.

#### S23-F9 (R1 S23, info, wording): TP wording: 'best of five replicate runs'

- **Description.** TP is the minimum over the evaluated main run plus 4 replicates (Rmax = 4), not over five replicates.
- **Evidence.**
  - v5b/p1/stats.py@93ba655:145-149; v5b/p1b/analysis.py@93ba655:370-372
- **Failure scenario.** Minor misdescription of the placebo.
- **How to test.** Read tp_placebo.
- **Related claims.** C78

### B101. [info] TEXT-F19: Draft state: limitations not written

Raised as info; verification: not adversarially verified.

#### TEXT-F19 (R1 TEXT, info, disclosure): Draft state: limitations not yet written

- **Description.** The Abstract, Discussion/Limitations and Conclusion are empty, and one [CITE] marker remains (line 63). Of the limits in p1b_result.md §7, only three appear inline: the runner share (line 149), q2000 storage (line 197) and the crawl as a substitute (line 110, partly). One more point: addendum R4 claims that s in {10, 30} % 'brackets' field rates, but work-zone non-compliance of 25.0-54.5 % exceeds 30 %. The paper only says 'context', which is correct.
- **Evidence.**
  - paper.qmd:57-59, 63, 199-203
  - p1b_result.md:78-86
  - p1b_addendum.md:77
- **Failure scenario.** If submitted as is, every limit listed in §7 would go undisclosed.
- **How to test.** Write the limitations section from p1b_result.md §7 together with TEXT-F2 to F13.
- **Related claims.** C85

