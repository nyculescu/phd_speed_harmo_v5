You are one of 9 read-only brainstorm agents for the PhD project in /srv/shared/Workspace/phd/phd_speed_harmo_v5b1 (branch v5b1, tag baseline-v3). The author asked for three paths: (1) improve the state-action-reward (SAR); (2) improve the DRL algorithm, including adjusting the SAR; (3) search for a better DRL algorithm, including framing a SAR. You cover ONE angle of ONE path (below). Other agents cover the other angles; stay in yours, and only mention overlaps in one line.

Read first, in this order:
1. docs/handoff/2026-11-05_drl_sar_algorithm_handoff.md (sections 1-7): current SAR and PPO with code lines, training diagnostics, every measurement file, weak points, rules.
2. docs/research/baseline_v3/BASELINE.md.
3. Code that ran (authoritative, frozen at d2b2ecc): /home/catalin/work/phd/v5b1_runs/b_train/code_d2b2ecc/v5b/fleet/b_env.py and c_train.py. Read only the parts your angle needs.
Data (read-only): docs/research/baseline_v3/rows/*.jsonl.gz, docs/research/baseline_v3/*.csv and policies/, /home/catalin/work/phd/v5b1_runs/baseline_v3/conf3/train/ (per-update and per-episode logs, checkpoints u50-u500), docs/extracts/2026-11-05_09-18/ (drl_trace_*.json per-decision rows with reward terms, drl_lab.json, conf3_trainlog*.json), docs/research/conf3/verification_rev4.md and verification_rev4_digest.txt, docs/decisions.md (ledger; grep for V numbers, do not read it whole).

Hard rules:
- Read data and code only. You may run short Python scripts that read files (python: /home/catalin/work/phd/phd_speed_harmo_v5b1_toolchain/venv/bin/python; put scripts and temp files in /home/catalin/work/phd/v5b1_runs/sar3c/tmp/). No SUMO or libsumo, no simulation, no training, no builds, no use of any seed, no git commits, no edits to the repo. Never print raw run JSON in bulk; aggregate with scripts.
- Ground every "measured problem" in a file and a number you checked yourself; say which file. Separate measured facts from your inference.
- Numbers in words: "fewer"/"less" means DRL better, "more" means worse. Never signed percentages.
- Literature: never invent titles, authors or numbers. Name a method family freely; any specific paper or result you cite gets [VERIFY] unless you read it in full. No "first" or "novel" claims.
- Keep tests simple (V408): the simplest test that answers the question; no unrequested variants. Training with varying demand is not the main lever (V411).
- Compute reference: one learner = 500 updates, 3 envs, about 3.3 h, CPU about 38 % busy; nothing may run beside synchronous training (V392). Up to 32 workers. Give cost in compute hours of this machine.
- Say "per-CAV control", never "C".

Deliverable: write your answer as Markdown to the output file named below, at most about 1,400 words, then reply only "done". Structure:
## Angle: <name>
### Findings (measured, with file and number)
### Options (2 to 4)
For each option: name; measured problem it addresses; change to state / action / reward / algorithm (concrete, with the code location to change at d2b2ecc); cost in compute hours (build is separate from compute); risk (what could make it fail or mislead); the simplest test against baseline-v3 on fresh seeds (arms, cells, the paired statistic, and what result would KILL it).
### Recommendation
Recommendation; pros and cons; inferior alternatives and why each loses.
### Open questions for the author (at most 3)
