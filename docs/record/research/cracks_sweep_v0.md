# Search for "cracks" around self-calibrating safety margins (2026-10-17)

The method was a workflow of 10 agents. Five scouts searched from different angles: literature, standards and industry, public data, our own results, and medical-device regulation. One agent merged their finds into 8 candidates. Three adversarial judges scored each candidate on prior art, feasibility and value. A final agent ranked them.

- Full output: `cracks_sweep_v0.json`.
- The scouts' exploratory numbers come from **spent TGSIM data only**, using scripts that were not code-reviewed. WaveX was not opened.

| ID | Candidate | Status | Scores (prior art / feasibility / value, out of 10) |
|---|---|---|---|
| C1 | Binding gate: does any leader-braking margin ever change driving compared with a production-like ACC gap (2 m + 1.5 s·v)? If it does, calibrate the ACC time gap on a replayed outcome and test it at an unseen site | recommended as a cheap first gate, not a paper | 6.5 / 6 / 4.5 |
| C2 | Context-conditional braking envelope (is the car two ahead closing in?) with validity per context group at an unseen site | recommended only if C1 passes | 6 / 3 / 6 |
| C6 | Two-risk calibrated activation cascade for a safety filter (idea taken from alarm design in patient monitoring) | possible | 5 / 3 / 5 |
| C7 | Roadside radar alert triggers early gap opening (WaveX) | possible; high scoop risk | 2.5 / 7 / 3.5 |
| C5 | Self-tuning ACC time gap from a string-stability monitor | killed (prior art; a fixed analytic gap likely wins) | |
| C3 | Governed freeze-and-monitor margin, in the style of FDA PCCP | killed (too few shift events; low power) | |
| C4 | Envelope by leader type (car vs truck) | killed (does not bind; reduces to a lookup table) | |
| C8 | Cross-site cold start with leave-one-site-out validity | killed (needs 6 or more sites) | |

## Key findings (main session)

1. **The margin we calibrated in line #1 almost never binds against a normal ACC gap.**
   - Exploratory result on spent TGSIM, with own braking of 4 m/s²: at α = 0.04 or 0.01, the RSS-style gap exceeds 2 m + 1.5 s·v in 0 % of R2/R3 windows.
   - It binds only at very small α, or with weaker own braking (3 m/s²).
   - Line #1 never checked this.
2. **Neural networks are not needed for the calibration step.** Order statistics and conformal methods give finite-sample statements. A small network might help only in C2, underneath a conformal layer.
3. **I-24 MOTION (INCEPTION) caps accelerations at about ±3 m/s²** in its reconciliation step (arXiv 2212.07907 §4.2). It therefore cannot test the hard-braking tail. Whether the released v1.0.0 uses exactly that bound is [VERIFY].
4. **Limits of this search:**
   - The shared web-search budget ran out, so the prior-art checks for C3–C8 were thin.
   - The medical-device half of the ChatGPT sentence was not researched.
   - Non-English literature and patent claims were not read.

## Addendum (2026-10-17): five-year check, Oct 2021 – Oct 2026

**arXiv.** 10 query phrasings returned 141 unique papers (`cracks_arxiv_5y.json`).
- By year: 1, 12, 15, 34, 32, 47.
- By content: 66 mention simulation, 18 mention real data, 18 are longitudinal or car-following.
- Only 4 combine online adjustment, a statistical guarantee and a margin. None of the 4 is about car-following or uses real traffic data.
- The keyword tagging misses some papers; it missed Zhou 2026, for example.

**The closest longitudinal work:**

| Paper | What it does | How it differs from a leader-behaviour margin |
|---|---|---|
| arXiv 2412.03792 / 2403.15577 | Perception-uncertainty ACC (conformal tube / chance-constrained MPC) | Simulator; the uncertainty is the ego's own perception, not the leader's behaviour |
| Zhou 2026 (arXiv 2609.35415) | Conformal residual margin | Scripted leaders; residuals of the ego's own model |
| VLM-CASE (arXiv 2607.05180) | Context-adaptive RSS envelope from a camera (weather, friction) | |
| arXiv 2512.05682 | Per-scenario conformal intervals for trajectory prediction | A prediction method, not a margin |
| arXiv 2609.07251 | Theory of adaptive conformal inference under delayed feedback | Relevant to line #1's delayed, batched updates |

**Patents.** Google Patents refused all automated requests from this machine and from the web-fetch tool (HTTP 503). An official API is needed (EPO OPS or USPTO), and only the author can create the key.
