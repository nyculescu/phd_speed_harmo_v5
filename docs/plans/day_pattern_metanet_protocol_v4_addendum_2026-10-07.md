# Protocol v4 addendum (2026-10-07): relocation rule (a), acceleration-zone bins excluded (D4.10)

**Status.** Binding amendment of v4 §A1 "Relocation (a) in v4". Decided by the author on 2026-10-07, before any capacity-factor grid on the calibrated v4 plant, from synthetic evidence only. The v4 calibration run (launched 09:49 from commit 4e7de3d) does not use relocation; no calibrated-plant output informed this decision.

**Amended rule.** Relocation (a): any cell downstream of B2's last scaled cell (cells 35–39) with bin-mean ρ_i > ρ̄_cr,i (the per-bin effective value, §A12) for ≥ 3 consecutive 5-min bins, **counting only bins in which B2's last scaled cell (cell 34) is not itself over-critical** (ρ_34 ≤ ρ̄_cr,34). Branch (b), c2\*, the grid, the KM rules (i)–(iv) and the Tobit substitute are unchanged.

**Why.** In v4, Old Shakopee Rd's cell 35 is unscaled and directly downstream of B2. In METANET, the cell just downstream of an active jam briefly exceeds ρ_cr while traffic accelerates out of the queue (convection term). As written, rule (a) therefore fires on almost every day with B2 active, at every c2. It reads as a "relocated bottleneck" what is the active B2 head's discharge zone.

Synthetic evidence (pre-launch code review, workflow wf_c94e0932-f2a; scenarios in `tests/test_metanet_v4.py::test15` and the session notes):
- As written, every c2 in 0.80–1.20 is flagged in the pinned scenario.
- With the amendment, there is no flag while B2 is active at low c2. The flag fires from c2 ≈ 1.10, where a downstream cell binds with B2 free.
- In a scenario with a heavy E15 merge (1,200 veh/h), the amended rule still flags from c2 = 0.85. That is a genuine downstream bottleneck, as intended.

**Disclosure (D4.4 style).**
- The amendment eases rule (iv) and F̂ estimability, in the same direction as the §A1 B-set rule (§A11 item 2).
- It was designed after the v3 results and after the v4 code review. It used no real-day model output of the v4 plant.
- Every F̂-based result names it.
- Test 15 checks both readings.
