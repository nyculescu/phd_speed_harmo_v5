# METANET plant of U.S.169 SB: protocol v4 (BINDING; author items V1–V9 decided 2026-10-07, D4.9)

**What v4 is.** v4 is a **new plant attempt** after the pre-registered route stop of v3 (D4.1). In form it is a post hoc amendment of v3 that reopens the METANET route stopped by v3 §0.3, a disclosed deviation (§A11 item 1). Under the D4.4 addendum, no v3 result is re-labelled, re-run to pass, or replaced.

**Form.** v4 = **protocol v3 (commit fc77668, `day_pattern_metanet_protocol_v3.md`) with the amendments listed here.** Every v3 section not amended below applies **word for word**. Seeds are those of §A8 and output paths those of §A9; every v3 path (defined in §A9) is read-only for v4, and the shared paths v4 may modify are listed there.
- Where an amendment changes T or seeds, the amended value applies everywhere.
- **Labels.** In v3 text, bare 'A1'–'A10' and '§0.6' mean v3's own author items. v4's amendments are §A1–§A14 (the §A3 constraint is named 'A3', as in A3-feasible); v4's author items are V1–V9, listed in v4's §0.6.
- v3 cell numbers in text that v4 does not restate are read **by role** through the §A1 concordance. Where v4 restates a v3 section in v4 cells, the restatement governs.
- Each amendment states the v3 text it replaces.

Decisions behind v4 (decision log `day_pattern_decisions_v0.md`):
- D4.1: the v3 route stop (author chose (a), "accept the stop as pre-registered").
- D4.2: METANET v4 as the gate plant, originally conditional on the prize screen.
- D4.3: seed block 7,191,000–7,191,999.
- D4.4: post-stop lessons may be used, with disclosure.
- D4.5: lane check (inconclusive).
- D4.7: R4(d) and R2(c) are bound.
- D4.8: skip the prize screen; METANET v4 unconditionally next.
- Pending: V6 (§0.6), the route reopening, to be recorded as a decision.

```
 why each amendment exists (v3 lesson → v4 change)
 ─────────────────────────────────────────────────
 5-s explicit scheme unstable (step-halving FAIL)   → §A2: T from a stability rule (0.75 s), new build checks, test-2 gate
 stations read capacity-scaled cells                → §A1: cell boundaries at ramp gores, station cells never scaled
 B1 "congestion" from the speed–density curve       → §A3: speed at capacity must be ≥ the event threshold
 P_1 episodes with no queue behind them             → §A12: gated queue-backing row P11-k
   (v3: 142 of 147 P_1 bins, no v3 cell 20–31 > ρ_cr)
 relocation at the E15 merge (v3: branch (a) at     → §A4: §1.7 step (b); V9 adopted, E15 lane-adding,
   cell 33 on 6/22 days at c = 1; ≥ 7 days at             δ_m = 0. The relocation is addressed only by V9,
   c1 0.80–0.82, c2 0.80); lane count unknown             untested; see §A11 item 8
 v3 seeds/paths must stay untouched                 → §A8, §A9: new seed block, new paths, v3 evidence frozen
```

---

## A1. Cells, bottleneck cells, station readings

*Replaces v3 §1.4 "Rule", "Merges", "Result", the table and "Bottleneck cells", and the second bullet of §1.5. §1.5's first bullet (ramp placement) applies unchanged and is binding; its third bullet applies with 400 steps in place of 60. Amends the cell references of §1.7, §2.1, §2.4 and §4.7 (concordance below).*

**Rule (v4).**
1. **Break points** = every λ-change point of the model geometry (§1.3), every ramp gore (entrance and exit km of §1.2, X6+X7 lumped as in v3) and the two stretch ends. **Stations are no longer break points.**
2. **Short pieces.** A piece shorter than **L_merge = 250 m** is merged, shortest first (ties: the upstream one), with an adjacent piece of the same λ; if both neighbours qualify, with the shorter one. If no neighbour has the same λ, it merges into the neighbour with the larger λ, which moves that λ-change point (logged). A gore that stops being a break point leaves its ramp inside a cell (logged).
3. Each piece of length L is split into n = max(1, ⌊L/500 m + 0.5⌋) equal cells.
4. **The 39-row table and the merge log below are binding.** `build_network("v4", step)` must reproduce them (test 9); the build fails if it differs. The draft table came from a data-free prototype on configuration geometry (disclosed). No repository v4 code is required before the protocol commit.

**Merge log** (rule order; configuration geometry, no traffic data):

| # | Piece (km) | Length, λ | Merged into | Effect (logged) |
|---|---|---|---|---|
| 1 | 1.810–1.833 | 23 m, 4 | 1.833–2.390 (same λ) | E12 inside cell 23 |
| 2 | −8.413 to −8.382 | 31 m, 2 | −8.382 to −8.074 (same λ) | E1 inside cell 1 |
| 3 | 1.730–1.810 | 80 m, 3 | 1.810–2.390 (λ = 4; no same-λ neighbour) | the I-494 EB lane addition moves 80 m upstream to km 1.730, as in v3; E11 inside cell 23 |
| 4 | 9.217–9.390 | 173 m, 2 | 8.999–9.217 (same λ) | X15 inside cell 39 |
| 5 | −2.549 to −2.300 | 249 m, 2 | −2.901 to −2.549 (same λ) | X6+X7 inside cell 13 |

**Result under §1.7 step (b): 39 cells, 300–660 m.**

**Groups (FD groups: each cell's v_f, ρ_cr, a).**
- G1 = cells 1–18 (km −8.413 to 0.000); G2 = cells 19–26 (0.000–3.751); **G3 = cells 27–35** (3.751–7.518); **G4 = cells 36–39** (7.518–9.390).
- Under step (b), v_f,G4 ≡ v_f,G3; ρ_cr,G4 and a_G4 are fitted. G4 runs from the cell fed by E15 to the stretch end.
- Where v3 says "G3" for the whole 2-lane section (§3.2.4 m_G and T.H.101's c_s, F16), it means G3 ∪ G4 (cells 27–39). The "group" field of F6 is the **scaling** group, not the FD group.
- §2.2's g(N) is a single group: G4 (cell 39) under step (b), G3 (cell 35) under step (c).
- **φ** (the 4 → 3 drop term) applies in cell 23 (λ = 4), v3's cell 22.

**Cell table (binding; step (b)).** km to 3 decimals, except split points that are exact at 4 decimals (−5.4495, 0.9105, 4.9365, 6.5675); every split is an exact equal division, and test 9 compares exact values (tolerance ±0.5 m), not printed ones. "Correction" = the same-cell ramp correction below.

| Cell | km | L (m) | λ | Group | Station read | Ramps (placement rule) | Correction |
|---|---|---|---|---|---|---|---|
| 1 | −8.413 to −8.074 | 339 | 2 | G1 | S453 Minnetonka Blvd (boundary) | E1, X1 | −E1, +X1 (input only) |
| 2 | −8.074 to −7.670 | 404 | 2 | G1 | — | X2 | — |
| 3 | −7.670 to −7.233 | 437 | 2 | G1 | S455 T.H.7 | — | — |
| 4 | −7.233 to −6.835 | 398 | 2 | G1 | S456 Van Buren Way | E2 | — |
| 5 | −6.835 to −6.221 | 614 | 2 | G1 | — | E3, X3 | — |
| 6 | −6.221 to −5.896 | 325 | 2 | G1 | S457 Excelsior Blvd | — | — |
| 7 | −5.896 to −5.4495 | 446.5 | 2 | G1 | — | E4 | — |
| 8 | −5.4495 to −5.003 | 446.5 | 2 | G1 | — | X4 | — |
| 9 | −5.003 to −4.576 | 427 | 2 | G1 | S458 Lincoln Dr | — | — |
| 10 | −4.576 to −4.034 | 542 | 2 | G1 | — | E5 | — |
| 11 | −4.034 to −3.492 | 542 | 2 | G1 | — | X5 | — |
| 12 | −3.492 to −2.901 | 591 | 2 | G1 | S459 Bren Rd | — | — |
| 13 | −2.901 to −2.300 | 601 | 2 | G1 | — | E6, X6+X7 | — |
| 14 | −2.300 to −1.866 | 434 | 2 | G1 | S460 T.H.62 | E7 | — |
| 15 | −1.866 to −1.435 | 430.7 | 2 | G1 | — | E8 | — |
| 16 | −1.435 to −1.005 | 430.7 | 2 | G1 | — | — | — |
| 17 | −1.005 to −0.574 | 430.7 | 2 | G1 | S461 69th St | X8 | +X8 |
| 18 | −0.574 to 0.000 | 574 | 2 | G1 | S462 Valley View Rd | — | — |
| 19 | 0.000 to 0.466 | 466 | 3 | G2 | S1770 S of Valley View Rd | E9, X9 | +X9 |
| 20 | 0.466 to 0.9105 | 444.5 | 3 | G2 | — | — | — |
| 21 | 0.9105 to 1.355 | 444.5 | 3 | G2 | S1771 I-494 | X10 | +X10 |
| 22 | 1.355 to 1.730 | 375 | 2 | G2 | S1772 Highwood Ave | — | — |
| 23 | 1.730 to 2.390 | 660 | 4 | G2 | — | E10, E11, E12 (φ here) | — |
| 24 | 2.390 to 2.844 | 453.7 | 3 | G2 | — | — | — |
| 25 | 2.844 to 3.297 | 453.7 | 3 | G2 | S1773 S of Highwood Ave | — | — |
| 26 | 3.297 to 3.751 | 453.7 | 3 | G2 | — | X11 | — |
| 27 | 3.751 to 4.055 | 304 | 2 | G3 | S1147 Anderson Lakes Pkwy (fit layer only) | — | — (v3's −E13 gone) |
| **28** | 4.055 to 4.496 | 440.75 | 2 | G3, **B1 head H1** (θ1) | — | **E13** | — |
| **29** | 4.496 to 4.9365 | 440.75 | 2 | G3, **B1** | — | — | — |
| **30** | 4.9365 to 5.377 | 440.75 | 2 | G3, **B1** | — | — | — |
| **31** | 5.377 to 5.818 | 440.75 | 2 | G3, **B1** | — | X12 | — |
| 32 | 5.818 to 6.118 | 300 | 2 | G3 (unscaled) | **S1140 Pioneer Tr** | — | — |
| **33** | 6.118 to 6.5675 | 449.5 | 2 | G3, **B2 head H2** | — | **E14** | — |
| **34** | 6.5675 to 7.017 | 449.5 | 2 | G3, **B2** | — | X13 | — |
| 35 | 7.017 to 7.518 | 501 | 2 | G3 (unscaled) | **S1141 Old Shakopee Rd** | — | — |
| 36 | 7.518 to 8.012 | 493.7 | 2 | G4 | — | E15 | — |
| 37 | 8.012 to 8.505 | 493.7 | 2 | G4 | — | — | — |
| 38 | 8.505 to 8.999 | 493.7 | 2 | G4 | — | X14 | — |
| 39 | 8.999 to 9.390 | 391 | 2 | G4 | S1610 T.H.101 (downstream end) | X15 | — (X15 upstream of the station) |

**Bottleneck cells (data-free rule).** B_k = the cells from the cell fed by B_k's merging entrance (E13 for B1, E14 for B2) up to and including the cell holding the last exit before the pair's downstream station (X12, X13).
- **B1 = cells 28–31** (head **H1 = 28**, carries θ1). **B2 = cells 33–34** (head H2 = 33).
- c1, c2 (§4.7) and F1 (§6.1) act on these cells only, everywhere ρ_cr appears (FD, origin supply term).
- **Build checks (fail the build):** (1) no event-layer or fit-layer station reads a cell in B1 ∪ B2; (2) each head lies strictly between its pair's station cells: H1 between cells 25 and 32, H2 between cells 32 and 35.
- **Weave sensitivity:** B2 = the cell fed by E14 through the cell holding X13, whatever E14's lane event.

*Why H1 is the merge cell and not the 3 → 2 lane end (cell 27).* Cell 27 holds the Anderson Lakes Pkwy station, so build check (1) excludes it. In METANET the merging term δ_m acts in the cell an entrance feeds, which is where a merge breakdown forms in the model. Both reasons are data-free.

**Cell 32 (Pioneer Tr) is unscaled between B1 and B2.** At high c1, B1's discharge may be capped there (static estimate c1 ≳ (1 + X12/(2·Q_cap,G3))/θ1; model-dependent). **No relocation rule on cell 32's density is used:** the cell lies in B2's queue on B2 days and can lie in B1's acceleration zone. Report: §A13 item 5.

**Relocation (a) in v4** (replaces the §4.7 "(a)" bullet): any cell downstream of B2's last scaled cell (**cells 35–39**) with ρ_i > ρ_cr,i for ≥ 3 consecutive 5-min bins (bin means). **This is a change of domain:** v3's cells 33–36 spanned km 7.199–9.390, v4's span 7.017–9.390, and 7.017–7.199 moves from v3's c2-scaled cell 32 into unscaled cell 35 (OSR station, no ramp), so relocation (a) can fire upstream of E15. Relocation (b), c2\*, the grid, the KM rules (i)–(iv) and the Tobit substitute are unchanged in text.

**F16:** see §A4.

**Concordance v3 → v4 (binding; read by role).**

| Role | v3 cell(s) | v4 cell(s) |
|---|---|---|
| Origin cell; E1, X1, S453 | 1 | 1 (unchanged) |
| T.H.7, Van Buren Way, Excelsior Blvd, Lincoln Dr, Bren Rd, T.H.62 stations | 2, 3, 5, 8, 10, 13 | 3, 4, 6, 9, 12, 14 |
| 69th St; Valley View Rd stations | 15; 16 | 17; 18 |
| S of Valley View Rd; I-494; Highwood Ave | 18; 20; 21 | 19; 21; 22 |
| S of Highwood Ave | 23 | 25 |
| Anderson Lakes Pkwy station / 3 → 2 lane end | 26 | 27 (unscaled, outside B1) |
| Pioneer Tr station | 30 | 32 (unscaled) |
| Old Shakopee Rd station | 32 | 35 (unscaled) |
| T.H.101 station | 36 | 39 |
| φ; E10–E12 | 22 | 23 |
| X11 | 25 | 26 |
| B1 head (E13, θ1); B1 non-head cells; X12 | 26; 27–30; 30 | 28; 29–31; 31 |
| B2 head (E14); B2 cells; X13 | 31; 31–32; 32 | 33; 33–34; 34 |
| E15; X14; X15 | 33; 36; 36 | 36; 38; 39 |
| G4 (step (b)) | 33–36 | 36–39 |
| Relocation (a) domain | 33–36 | 35–39 |
| F1 cells | 26–32 | 28–31 ∪ 33–34 |
| N | 36 | 39 |
| *new, no v3 counterpart:* unscaled G3 cell between B1 and B2 | — | 32 |

**v3 text restated in v4 cells (governs).**
- §2.1 FD: ρ_cr,i = c1·ρ_cr,G3 in cells 29–31; ρ_cr,28 = c1·θ1·ρ_cr,G3; ρ_cr,i = c2·ρ_cr,G3 in cells 33–34; Δλ_i = 1 in cell 23 only.
- §4.7 Definition: c1 multiplies θ1·ρ_cr,G3 in cell 28 and ρ_cr,G3 in cells 29–31; c2 multiplies ρ_cr,G3 in cells 33–34.
- §2.4: X12 in cell 31, X13 in cell 34 (EXIT-branch caps there); X14 in cell 38 sees q_37; X15 in cell 39 sees q_38.
- **Informative only** (not binding): §3.2.1's physical reading (note: lane-end cell 27 is outside B1 and unscaled) and §4.7 "Why" (note: c2-driven relocation lands in OSR's cell 35).

**Ramp placement and station readings** (§1.5: first bullet restated; second bullet replaced; third bullet with 400 steps).
- **Ramp placement (v3 §1.5 bullet 1, unchanged, binding):** an entrance at km x feeds the cell containing x, and one exactly on a boundary feeds the downstream cell; an exit leaves the cell containing x, and one exactly on a boundary leaves the upstream cell. On step (b): E1→1, E2→4, E3→5, E4→7, E5→10, E6→13, E7→14, E8→15, E9→19, E10/E11/E12→23, E13→28, E14→33, E15→36; X1→1, X2→2, X3→5, X4→8, X5→11, X6+X7→13, X8→17, X9→19, X10→21, X11→26, X12→31, X13→34, X14→38, X15→39.
- **Station value:** a station reads the cell containing its km; one exactly on a boundary reads the upstream cell; S453 (stretch start) reads cell 1; T.H.101 reads cell 39.
- **Same-cell correction** (v3 formula unchanged: q_s = q_i − Σ entrance releases downstream of s in cell i + Σ exit flows downstream of s in cell i). It applies to every ramp assigned to the station's cell by the placement rule and lying downstream of the station, including an exit on the cell's downstream boundary: **S453 (cell 1: −E1, +X1; input only), S461 69th St (cell 17: +X8), S1770 S of Valley View Rd (cell 19: +X9), S1771 I-494 (cell 21: +X10); no other station.** Anderson Lakes no longer needs −E13 (E13 feeds cell 28); T.H.101 needs none (X15 is upstream of it).
- **5-min aggregates:** over the bin's 400 steps; otherwise v3 §1.5 bullet 3 unchanged.

**Geometry variants (§1.4 variants replaced).** The weave sensitivity, §1.7 step (a) and step (c) tables are regenerated by the same rule (B cells by the same rule; weave B2 as above) and reproduced by test 9. Step (b) is the build in use (§A4).
- **Variants (binding; cells 1–35 the same everywhere):** weave: λ = 3 in cells 33–34; step (a): λ = 3 in 36–39, merge 4 goes into the λ = 3 piece 8.999–9.217 (X15 lane end moves to km 9.390, logged); step (c): N = 35, merges 1–3 and 5, no G4, relocation (a) = cell 35. Stations, ramp cells, corrections, B1 = 28–31, B2 = 33–34 and station cells are unchanged where they exist (step (c) removes E15, X14, X15 and S1610, v3 §1.7 (c)).

**Disclosed consequence (D4.4).**
- Moving stations out of scaled cells removes v3's main relocation-(b) mechanism: Old Shakopee Rd read the c2-scaled cell.
- **Candidates** (2026-10-06 design study, neither simulated): (a) head-only, B1 = {28}, B2 = {33}; (b) v3 §1.4's sets on v4 cells (B1 = 27–32, B2 = 33–35) minus the station cells, giving B1 = 28–31 and B2 = 33–34. The §A1 rule reproduces (b), **selected from 2**. Data-free reason: (b) departs least from v3, removing only station cells, while (a) makes c_k inert above saturation and truncates F̂'s upper tail.
- **Direction (expected, not tested):** B-set membership acts only where c_k ≠ 1 and under F1. Removing relocation (b) at low c2 means c2\* can only rise, rule (iv) becomes less likely, and rules (i)/(iii) become less likely to fire. Each eases a v3 failure path toward an estimable F̂ and a stochastic PASS. Relocation (a) at E15 is not eased.
- **F1's cells change** from v3's 26–32 to 28–31 ∪ 33–34.
- Designed after seeing v3's capacity grid.

## A2. Numerics

*Replaces v3 §2.5 "Time step", "CFL" and "Relaxation" bullets and the step-halving T values; amends §4.1 "Fixed" (T = 0.75 s) and its τ row, and unit test 2.*

**Units in (a)–(f):** T and τ in h, L in km, ν in km²/h, speeds in km/h, Q_o in veh/h, κ in veh/km/lane. **L_tab** = min_i L_i of the generated table (300 m on step (b)); it is not the §A1 merge threshold L_merge = 250 m.

**Time step: a data-free rule over a pre-registered ladder.** T = the largest value in **{1.25, 1.0, 0.75, 0.625, 0.5} s** that satisfies (a)–(f) against the bound maxima and the generated table.

| | Condition | At T = 0.75 s, step (b) |
|---|---|---|
| (a) diffusion number | ν_max·T/L_tab² ≤ **0.25** (ν_max = 90 km²/h) | **0.208** (1.0 s: 0.278; 1.25 s: 0.347, both fail) |
| (b) wave Courant number | (v_cap + √(ν_max/τ_min))·T/L_tab ≤ **0.5** | 0.234 |
| (c) relaxation | T ≤ τ_min/10 | T/τ_min = 0.075 |
| (d) merge stiffness | δ_m,max·T·ΣQ_o/(L_i·λ_i·κ_min) < 1 in every cell fed by a merging entrance (ΣQ_o over the cell's merging entrances) | max 0.541 (cell 1) |
| (e) test-2 gate | §A10 test 2 (iii) passes at T | review scan: passes (§A11 item 9); asserted by test 2 |
| (f) combined sink | T/τ_min + δ_m,max·T·ΣQ_o/(L_iλ_iκ_min) + v_cap·T/L_i < 1 in every cell (ΣQ_o = 0 without a merging entrance) | max 0.713 (cell 1) |

- (a): for this scheme the shortest-wave edge is νT/L² = (ρ+κ)/(4ρ) as v → 0 (≥ 0.257 within bounds, → 0.25 as κ/ρ → 0). It is ≈ 0.32 at v_min with τ = 10 s, κ = 5, ρ = ρ_max, L = 300 m, and larger for larger τ (≈ 0.66 at τ = 60 s). 0.25 is a design margin, not a necessary condition.
- **So T = 0.75 s (400 steps per 5-min bin).** T is fixed by this rule before any refit and never revisited after results. A different table (step (a) or (c)) re-applies the rule.
- At 1.0 s only (a) fails; (b)–(f) pass ((c) 0.100, exactly at its limit; (f) 0.950). At 1.25 s, (a), (c), (e) and (f) fail. A margin condition, (a), sets the rung.
- **If no rung satisfies (a)–(f), the build fails before any calibration** and the author decides between an amendment and a route stop.
- (a)–(f) replace v3's "T·v_cap ≤ L_min" and "τ_min = 2T" assertions. They are frozen-coefficient linear conditions without boundaries or clipping; the gated step-halving check stays the empirical test.
- **Enforced in code:** (a)–(d) and (f) are evaluated inside every `simulate()` call against the T that call uses; (e) is computed once per (T, table), cached, and asserted in the same call.
- Report-only: the maximum per-step φ factor 2φTρv/(Lλρ_cr) in cell 23.

**Derived values (replace v3's).** 400 steps per 5-min bin (§1.5, §2.6); N = 39; 91,200 steps per model-day (§8.2); step-halving at T/2 = 0.375 s; the §2.5 clipping example becomes νT/(τL) ≈ 22.5 km/h (ν = 90, τ = 10 s, L = 300 m); §4.1's τ row reads "10–60 s (prior bound)", no longer tied to 2T; §1.7's 319-m clause is void; the weave sensitivity runs at the frozen v4 parameters.

**Step-halving (gated, criterion unchanged):** T vs **T/2 = 0.375 s** on all usable calibration days: |ΔJ|/J ≤ 0.05 and identical P_1 and P_2 model-episode day sets, with no tolerance.

**Report-only diagnostics (no consequence).**
- **Margins:** per day and pair at T and T/2, the count margin (best 7-bin count − 5) and, for every bin of the window reaching it plus every bin whose status differs between T and T/2, the signed m_v = 40 − v_u and m_d = (v_d − v_u) − 20 (mph, detector scale).
- **T/4 check:** if the day sets differ, the differing days are also run at T/4 = 0.1875 s; v_u and v_d − v_u per deciding bin at T, T/2 and T/4 are reported with r = |x(T/2) − x(T/4)|/|x(T) − x(T/2)|. Numbers only: no label, no effect on N0, the route or T.
- **Stability (Payne-type):** per group g and ρ ∈ {1.0, 1.25, 1.5, 1.75, 2.0}·ρ_cr,g at the frozen parameters, c = √(νρ/(τ(ρ+κ))) vs ρ|V′(ρ)|, and the maximum semi-discrete growth rate (s⁻¹) on g's shortest cell.
- **The margins and the stability diagnostic are report-only. They cannot waive, re-judge or soften N0 or any gated row, and cannot select the nominal plant or ensemble members.**

**State limits, clipping count, admissibility (J = 10) and N0:** unchanged. The clipped share is a fraction of cell-steps, so its meaning does not depend on T.

## A3. Speed at capacity

*Amends v3 §4.1, §2.5 admissibility and §4.5 (profiles). v3 §4.4 (initial means included) is unchanged.*

**Constraint.** For each FD group g, v_c,g = v_f,g·exp(−1/a_g) ≥ thr_g = max over the event-layer stations read in g of (40 mph × 1.609344 × c_s).
- A station is **read in g** if the cell it reads (§A1) belongs to FD group g. Only event-layer stations count.
- c_s comes from F6 (the computed value, also for stations dropped from the speed term); F6's group field is not used.
- **The table is binding;** if code and table differ, the build fails.

| Group | Event-layer stations read | max c_s | thr_g |
|---|---|---|---|
| G1 | S455–S462 (S453 is the upstream boundary, has no c_s and is not used) | 1.169 (S461; computed value, used by the event layer) | 75.3 km/h |
| G2 | S1770–S1773 | 1.052 (S1771 I-494) | 67.7 km/h |
| G3 | S1140, S1141 (S1147 is not in the event layer) | 1.000 | 64.4 km/h |
| G4 | S1610 (T.H.101, cell 39), although F6 labels it G3 for scaling | 1.133 | 72.9 km/h |

thr_g is computed at full precision from F6's c_s (75.2829, 67.6900, 64.3738, 72.9309 km/h); the table shows it to 0.1 km/h. The choice changes optimiser trajectories (data-free replay: seed 7,191,012 is first A3-feasible at evaluation 27 with exact values, 39 with tabled ones).

**Enforcement.**
- (a) A3 is checked **before simulation**, on the bounded vector that would be simulated; a violator is not simulated.
- (b) A violator gets **J = 10 + Σ_g max(0, thr_g − v_c,g)/thr_g**. This is above every admissible J and above the J = 10 for clipping or non-finite values. It counts as one evaluation and is counted per restart as "inadmissible (A3)", separately from clipping.
- (c) (a)–(b) apply identically in base, continuation, F1 and profile runs.
- (d) A restart with best J ≥ 10 is reported as "no admissible point". It is not re-run or replaced, and it counts in every restart statistic. If no restart has an admissible point, there is no nominal plant: v4 stops at the base plant's freeze (route STOP; counted as an N0 route stop under §A6 (2)–(3)).
- (e) **Profiles:** points with no A3-feasible completion (v_f,G3 = 80 and 88.75 km/h) are not run and are recorded as "infeasible (A3)". The warm start is the frozen optimum with each violating a_g raised to its smallest A3-feasible value. The flat share is reported over all 8 intervals and over the A3-feasible intervals; for v_f,G3 the non-identifiable flag applies v3's ≥ 50 % rule to the width of the A3-feasible intervals (j = 2…8, 6 intervals, 97.5–150 km/h).
- (f) **Implied limits** (disclosed, not new bounds; rounded up, so each stated value is feasible): v_f,G1 ≥ 100.2, v_f,G2 ≥ 90.1, v_f,G3 ≥ 97.06 km/h (through G4); a_G1 ≥ 1.451, a_G2 ≥ 1.26, a_G3 ≥ 1.183, a_G4 ≥ 1.39. Exact: 100.18, 90.08, 97.0501; 1.4506, 1.2568, 1.1821, 1.3867.
- (g) **Reported** per restart and at the optimum: v_c,g − thr_g; an "A3-active" flag if within 1 %; the A3-violating share; the index of the first A3-feasible evaluation.

**Why.** Without it, a group's free-flow branch can read below 40 mph with no queue. All 8 v3 restarts put G2's speed at capacity at 46.5–48.1 km/h, and v3's B1 "agreement" came from that (D4.4 addendum). **A3 removes only the equilibrium route.** With v_c,G2 on its A3 bound, the capacity state reads within 0.32 km/h of S of Highwood Ave's threshold and exactly at I-494's. A queue headed upstream of a pair's upstream station (e.g. the 4 → 3 drop, cells 23–24), the anticipation term across a per-lane density increase (cell 21 → 22, S1771) and δ_m in merge-fed event-station cells (4, 14; cell 1 is S453, input only) can still give sub-threshold station speeds with every cell ≤ ρ_cr,i. **A3 is complemented by the gated row P11-k (§A12).**

**Disclosed:**
- it is a fit-informed narrowing of the admissible set, designed after seeing v3;
- it may make B1's occurrence unreproducible, which would be an honest FAIL;
- typical freeway speeds at capacity are well above 40 mph [VERIFY: HCM basic-segment curves, not read here];
- v3's restarts also fall below the A3 thresholds at G3 (7 of 8 restarts, by 0.26–1.94 km/h) and G1 (2 of 8: 7,190,011 by 1.85 and 7,190,014 by 3.21 km/h); A3 is expected to be active at G2 and probably at G3;
- **initial means: v3 §4.4 unchanged, no rejection-sampled start; the graded penalty (b) is relied on instead.** Data-free replay (pycma 4.5.0, numpy 2.5.3): under v3's initialisation, seed 7,191,010 reached no A3-feasible point in 4,000 evaluations with a flat J = 10; with (b)'s graded penalty it reaches one at evaluation 16, and every base seed by evaluation 27. Every F1 seed (n = 19, §A5 order) is first A3-feasible by evaluation 19 (1, 4, 19, 16, 8, 1, 8, 6).

No other bound changes. **No bound is widened.**

## A4. Downstream geometry

*Amends v3 §1.3, §1.7 (domain sentence, "Rule") and §2.1's list of merging entrances.*

The geometry-only lane check (D4.5, `docs/lab/day_pattern/e15_x15_lane_check.md`) is **inconclusive**: IRIS 2 lanes; OSM 3 lanes since 2021-10, from just upstream of E15; the press reports a temporary flood-time third lane.

**F16 and the step (replaces v3 §1.7's domain sentence and "Rule" for v4).**
- (i) **G4 = cells 36–39 (step (b)) is adopted without condition** (lane check inconclusive, D4.5; v3's F16 on the same arriving flow gave R = 1.371, so v3's rule would also select step (b)).
- (ii) F16 is recomputed cell by cell by v3's A_i definition on **cells 27, 32, 35–39**: cell 35 OSR only; cells 36–38 OSR + E15; cell 39 OSR + E15 − X14. The domain comes from the build, never from a fixed index, and v3's `f16()` loop is not reused.
- (iii) **F16 is report-only in v4:** no outcome changes geometry or blocks calibration. A ratio > 1.10 at cell 27, 32 or 35 is listed in F14 as a capacity question, because there it compares a station's own peak with discharge and is not a lane test.
- (iv) This removes v3's blocking clause (disclosed, §A11 item 11).

**E15 lane-adding under step (b) (V9, adopted 2026-10-07).** Under step (b), E15 is lane-adding: **δ_m = 0 at E15** (E15 leaves v3 §1.3's δ_m list and §2.1's r_i^m list). λ stays 2 in cells 36–39; G4's fitted ρ_cr and a remain the capacity substitute.
- Disclosed: designed after seeing v3's relocation at E15 (D4.4); consistent with the G4 premise of an added lane at E15 (OSM shows 3 lanes from about the E15 gore).
- Alternative: none (δ_m at E15 as in v3). No per-ramp δ_m.
- Its effect on relocation is not tested (§A11 item 8 (a)).

If the author later supplies dated 2023 imagery that resolves the count, that is a new protocol version. It may replace v4 only before the first v4 CMA-ES evaluation; after that it is a later plant under §A6 (3).

## A5. Parameters

n = 17: G1–G3 (9), τ, ν, κ, δ_m, φ, θ1, plus ρ_cr,G4 and a_G4. Bounds are as in v3 §4.1, θ1 included; §A3 adds an admissibility constraint, not a bound. The EXIT branch stays as in v3 (§1.6 is unchanged; F7 = base/base is reused).
- **Vector order (binding; v3 §4.4's seeded draw x ~ U[0.25, 0.75]^n depends on it):** v_f,G1–G3, ρ_cr,G1–G3, a_G1–G3, τ, ν, κ, δ_m, φ, θ1, ρ_cr,G4, a_G4 (n = 17, the v3 code order). F1 (n = 19): the same 17, then Δ, η.

## A6. Reuse, recompute, order of work, single look

*Amends v3 §3.6, §3.8, §6.3 (last sentence) and §8.6.*

**Reused as committed** (v3 `metanet_precal_facts.json`):
- day split, cleaning, exclusions and usable-day lists (F2);
- c_s and the lane screen (F6); ramp sources (F4) and the flow-reliability classification (F5); the E4 reference;
- F3, F7 (outcome base/base), F8, F9, F10, F11 (minima, floors L_r,k, N2_q, P8 tolerance 10), F12, F13, F14 (except its G1/G2 ratios) and F15.

**Recomputed**, committed to `metanet_v4_precal_facts.json` (§A9) before any CMA-ES evaluation:
- F1: cell table, merge log and the per-entrance merging flags (must equal §A1 and §A4; E15: δ_m = 0 V9 adopted);
- F14's G1/G2 §1.7 ratios on v4 cells 1–26 (report-only);
- F16 per §A4;
- F7's cell references restated (X12 in cell 31, X13 in cell 34); outcome unchanged.

**Order of work.** v3 §8.6 applies with:
- step 0, before the protocol commit: the §A9 sha256 manifest and the tag `metanet-v3-stop`;
- step 1: author items V1–V9, then the protocol commit;
- step 2: code, unit tests and synthetic timing;
- step 3: the recompute list above, committed to `metanet_v4_precal_facts.json` before any CMA-ES evaluation;
- steps 4–7 unchanged; step 4 also runs P11-k on calibration days (§A12) and applies (7) below.

v3 §3.8 steps 1–10 are not re-run.

**Single look** (V7):
1. No model of any kind (smoke and debug runs included) runs on a validation day until `metanet_v4_calibration.json` is committed with stage "freeze". v4 smoke tests use synthetic inputs or calibration days.
2. Once the first v4 CMA-ES evaluation has run, v4 ends only by an N0 route stop (§2.5), a P11-k route stop at the base plant's freeze (§A12), the pre-registered freeze choice in (7), or a §0.3 gate outcome (§8.6 steps 5–6; F1 if triggered). A §6.3 bug fix and its re-run is not a stop. Any other stop is recorded as **"abandoned after calibration"**.
3. After a v4 FAIL (with F1 if triggered), "abandoned after calibration" or "PASS, deterministic-only", any later plant judged on these 97 days (a new METANET version under §6.3, or SUMO) is labelled **"second look on the same validation days"**, and its gate can yield **only a KILL**. A GO-capable later plant needs validation days on which no model has run and which no design step has inspected, chosen by a rule committed before they are pulled. After an N0 or P11-k route stop at the freeze, or the freeze stop in (7)(b), the days stay unlooked and the attempt is counted under §A11 item 5.
4. An F1 PASS keeps its v3 §6.1 status and label.
5. A §A4 imagery amendment may replace v4 only before the first v4 CMA-ES evaluation; after that, it is a later plant under (3).
6. Until the v4 gate outcome is committed, only committed gate code reads validation-day real data.
7. **Freeze choice ((b), decided 2026-10-07):** if no usable spread exists at the base plant's freeze, that is, F̂ is not estimable by rule (i) or (iv), or F̂ is not estimable by (ii)/(iii) and F̂_T is not usable (v3 §0.3, §4.7), v4 **stops at the freeze** as a pre-registered end; the gate does not run. Alternative (a): run the gate anyway (deterministic-only, KILL-only; uses the look). (7) does not apply to F1, whose spread follows v3 §0.3 unchanged.

This amends v3 §6.3's last sentence: a new protocol version judged on these 97 days falls under (3).

**2024** stays unopened (D3.3).

## A7. Unchanged and explicitly frozen

- The objective J and its sets, and NRMSE.
- The event layer (EA-2), the observation operator and c_s.
- Every P-row, its threshold and minimum; **P11-k is added (§A12)**, no row is removed or changed.
- N0's 1 % and the step-halving criterion.
- F̂ rules (i)–(iv), the Tobit substitute and the deterministic-only consequence: **text unchanged; their effective behaviour changes through §A1's B-sets.**
- Relocation (a)/(b) definitions (**domain re-cut per §A1; disclosed change**), c2\* and the c-grid.
- F1 (Δ, η, trigger set unchanged; P11-k joins the non-trigger list, §A12; **cells = B1 ∪ B2, changed from 26–32 to 28–31 ∪ 33–34**).
- §7 R1–R13, including **R4(d) and R2(c), bound by D4.7.**
- The optimiser settings: 8 restarts × 4,000 evaluations, continuation rule, profiles (8 parameters × 9 points, 600 evaluations, σ0 = 0.1), **except §A3 (a)–(e).**
- The ensemble rule.

**No bound is widened; no threshold is loosened.**

## A8. Seeds

*Replaces v3 §8.1; block 7,191,000–7,191,999, D4.3. Concordance checked against v3 §8.1.*

| Seeds | Use | Replaces v3 seed |
|---|---|---|
| 7,191,010–017 | base CMA-ES restarts (8) | 7,190,011–018 |
| 7,191,018–025 | F1 CMA-ES restarts (8) | 7,190,021–028 |
| 7,191,026–097 | profiles: seed = 7,191,026 + 9p + j, p = 0…7 in the v3 order (v_f,G3, ρ_cr,G3, τ, ν, κ, δ_m, φ, θ1), j = 0…8 | 7,190,030–092 (p = 0…6) and 7,190,100–108 (θ1) |
| 7,191,098 | bootstrap of the §4.7 correlations (calibration days) | 7,190,094 (its §4.7 use only) |
| 7,191,300 | bootstrap of the base-plant gate statistics (validation-role range) | 7,190,093 |
| 7,191,301 | joint capacity-factor draws for the stochastic rows (base plant, ensemble, F1) | 7,190,095 |
| 7,191,302 | bootstrap of the F1 gate statistics | 7,190,096 |
| all others | unused | — |

- **No v3 seed is used for any new draw.** F8 (7,190,094) and F11 (7,190,097) are reused as committed and are not re-drawn.
- Cold starts only; no warm start from any v3 restart.
- A re-run after a bug fix reuses the original seeds.

## A9. Paths, records, guards, compute

*Amends v3 §8.2–§8.3.*

**Step 0 (before the protocol commit and any v4 code change):**
- a sha256 manifest of `/home/catalin/work/phd/vsl_lab_runs/day_pattern/metanet/` (v3) is committed;
- git tag `metanet-v3-stop` is set at `0f02418`.

**v3 paths (read-only for v4):** the v3 raw-run directory `/home/catalin/work/phd/vsl_lab_runs/day_pattern/metanet/` and the v3 records `docs/lab/day_pattern/metanet_precal_facts.json`, `metanet_calibration.{json,md}` and the v3 addenda (`metanet_calibration_addendum_*.md`).

**Shared paths v4 may modify (not v3 paths):** `vsl_lab/runs/ledger.csv` (append-only); `vsl_lab/plants/metanet.py`, `vsl_lab/jobs/metanet_calibrate.py`, `tests/test_metanet.py` and the other METANET code and tests (`vsl_lab/data/metanet_facts.py`, `vsl_lab/jobs/metanet_*.py`, `tests/test_metanet*.py`). v3's code stays at tag `metanet-v3-stop`.

**v4 paths:**
- raw output: `/home/catalin/work/phd/vsl_lab_runs/day_pattern/metanet_v4/`;
- records: `docs/lab/day_pattern/metanet_v4_calibration.{json,md}`;
- **pre-calibration facts: `docs/lab/day_pattern/metanet_v4_precal_facts.json`.** It holds exactly the items §A6 lists as recomputed, records protocol v4 and the git blob hash of the reused v3 `metanet_precal_facts.json`, and is committed before any CMA-ES evaluation. v4 code reads reused facts from the v3 file and never writes it.

**Reused v3 raw inputs** are read only from `/home/catalin/work/phd/vsl_lab_runs/day_pattern/metanet/`, after their sha256 matches the committed manifest; a mismatch stops the run. `calib_data.npz` is rebuilt into `metanet_v4/` and must equal v3's array for array (day list, station order and masks bit-for-bit); any difference is a logged deviation that stops the run until the author decides. The v3 manifest is re-verified after every v4 batch.

**Guards and records:**
- The v4 gate jobs (prep included) refuse to run unless `metanet_v4_calibration.json` is tracked by git, unchanged against HEAD, names protocol v4, has stage freeze and a route not starting with STOP. They never read the v3 record. The freeze record's route starts with "STOP" after an N0 failure, a P11-k failure at the freeze (§A12), no admissible restart (§A3 (d)) or the freeze stop of §A6 (7)(b).
- The v4 record stores T and T/2. Every ledger row of a simulating batch states its T; a mismatch is a bug (fix, re-run, log both).
- Committed v3 records are never edited; only dated addenda are added.

**Compute.** Projections (estimates from v3 timings: about 7 × v3 per model-day at T = 0.75 s with 39 cells; measured on synthetic inputs before launch):

| Stages | Projection |
|---|---|
| base: calibration, profiles, nominal grid | ≈ 17 h |
| with the continuation | ≈ 23 h |
| with F1 and the continuation | ≈ 30–36 h |
| each further capacity grid (ensemble member; the optional v3-set sensitivity, §A13) | + ≈ 0.8 h |

- The 24-h rule applies to the worst-case projection of all stages that can run without a new author decision. On these projections it is exceeded, so the notice applies: V1 gives it now, and it is repeated with the measured timings before launch.
- Every batch: resource check, v6-idle check, CPU and thermal guard, one ledger row.

## A10. Unit tests

*Amends v3 §8.4.*

| Test | v4 change |
|---|---|
| 2 | Replaced by the block below. |
| 9 | Reproduces the §A1 39-row table (exact km, tolerance ±0.5 m, not printed values), the merge log, the FD groups (group(35) = G3, group(36) = G4), the B cells and heads, build checks (1)–(2) and the §A1 'Variants' line (weave B2 rule); per station and variant, its cell and corr_entr/corr_exit lists, checked against §A1; the per-entrance merging flags (E15 δ_m = 0 under step (b) V9 adopted, §A4); the §A3 per-group station sets and thresholds; and the split builder reproduces the §3.1 date lists. |
| 11 | Head location in v4 cells: H1 = 28, H2 = 33; P_1 = cells 25/32, P_2 = 32/35; an overloaded B1 gives a queue in cell 28 that reaches cell 25. |
| 15 | Relocation and c2\*: re-stated with cells 35–39; raising c2 until cell 35 binds triggers the flag at the first such c2, not below it. |
| 17 | θ1 on cell 28: the head forms in cell 28 while cells 29–31 stay on the free-flow branch. |
| 18a, 18b | v3's two tests numbered 18 become 18a (P7c) and 18b (clipping); 18b compares T and T/2 (0.75 vs 0.375 s). |
| **19 (new)** | A3: a violator is not simulated; the graded J increases with the violation; infeasible profile points are skipped; the admissible case is an explicit A3-feasible set, not `midpoint_params` (which violates G1 at 73.7 km/h); the per-group thresholds from the cell → FD-group map, at full precision, equal G1 75.2829, G2 67.6900, G3 64.3738, G4 72.9309 km/h (to 1e-4; the §A3 table shows them to 0.1). |
| **20 (new)** | Station cells: no station reads a scaled cell, under c1 = c2 = 0.8 and 1.2. |
| **21 (new)** | P11-k (§A12). (i)–(iii) test the classifier on synthetic per-bin ρ, ρ_cr, v and station-speed arrays with known answers, pair condition met at P_1: (i) only cells 23–24 above ρ_cr,i (a 4 → 3 drop queue) → unbacked; (ii) cells 26–28 above (an H1 queue spilling back), and separately cell 27 alone → backed; (iii) only station cell 25 or 32 above → unbacked. (iv) a simulated 3 → 2 lane-drop toy at ν = 90, κ = 5 → non-zero station diagnostic (§A13 item 1) at the last 3-lane cell; its full parameter vector, demand and c_s are pinned in the test source, committed at §A6 step 2 before any CMA-ES evaluation. (v) pair condition met at P_2: only cell 32 or 35 above → unbacked; cell 33 or 34 alone → backed; (vi) a day whose pooled qualifying bins are exactly 50 % backed is not unbacked. |
| **22 (new)** | With v4 paths set, no v4 job (facts, calibrate prep/fit, postcal, freeze, gate) opens a v3 path (as defined in §A9) in write mode; run against a read-only copy of the v3 paths. Ledger appends and the shared paths of §A9 are outside the test. |
| **23 (new)** | F16 per-cell sources on synthetic flows: A_35 excludes E15, A_36 includes it, A_39 subtracts X14; cells 33–34 are not in the output. |

**Test 2 (replaces v3's).**
- (i) v3's worst-case shock check is kept: no negative speed, ρ ≤ ρ_max.
- (ii) The §A2 assertions (a)–(d), (f) at the bound corners ((e) is this test's gate (iii)), and their 0.75-s values on step (b): (a) 0.208, (b) 0.234, (c) 0.075, (d) 0.541, (f) 0.713. `simulate()` on the v4 table at T = 5 s and at 2.5 s raises.
- (iii) **Frozen-coefficient von Neumann scan** of the `simulate()` cell update, linearised about uniform states (constant λ; no ramps, δ_m, φ or boundaries). The Euler eigenvalues are 1 + Tλ_k(θ) of
  ```
  A(θ) = [[ −(v0/L)(1 − e^{−iθ}),                    −(ρ0/L)(1 − e^{−iθ})            ],
          [ V′/τ − ν(e^{iθ} − 1)/(τ L (ρ0 + κ)),      −1/τ − (v0/L)(1 − e^{−iθ})      ]]
  ```
  - **States:** equilibria with ρ0/ρ_cr ∈ {0.1, 0.3, 0.6, 1, 1.25, 1.5, 2, 3, 5, 8, 12}, ρ0 ≤ ρ_max, V ≥ v_min; floor states (v0 = v_min, both with V′ = 0 and with V′ kept) where V < v_min; cap states v0 = 1.05·v_f at ρ0/ρ_cr ∈ {0.1, 0.3}.
  - **Grid:** τ ∈ {10, 15, 30, 60} s; ν ∈ {5, 30, 60, 90} km²/h; κ ∈ {5, 20, 40, 60}; v_f ∈ {80, 120, 150}; ρ_cr ∈ {15, 30, 45}; a ∈ {1, 2, 3.5}; every distinct L_i; θ_j = jπ/181, j = 0, …, 181 (A(−θ) is the conjugate of A(θ)).
  - Units here: λ in s⁻¹ and T in s (not h as in §A2's (a)–(f)).
  - A state is **stable** iff max Re λ ≤ 1e-9·max|λ| (semi-discrete; zero tolerance for round-off; the continuum sub-characteristic condition is not used).
  - **GATE:** in every stable state, max ln|1 + Tλ|/T ≤ **ε = 1e-4 s⁻¹** [lab convention].
  - Report-only: the excess growth in unstable states (truncation error, tested by step-halving), the count of continuum-stable but semi-discretely unstable states, and the count of states with 0 < max Re λ ≤ 1e-9·max|λ| (review scan: no state with Re λ in (0, 1e-12]).

## A11. Disclosures (added to v3 §0.5)

1. **History.** v3 failed N0. Its pre-registered consequence (v3 §0.3, §6.2) was a route stop that "stops the METANET route"; §0.3 named only SUMO as a continuation. D4.1 offered (a) "accept the stop as pre-registered" or (b) "a post hoc v4 amendment"; the author chose (a). **In form v4 is a post hoc amendment of v3 that reopens the METANET route.** This is a deviation from v3 §0.3 decided by the author after the v3 results (D4.2, conditional on the prize screen; D4.8, unconditional), made after the post-stop diagnostics diagnosed a numerical defect. v4 differs from option (b) in these ways: v3's FAIL and route stop stand as attempt 1; under the D4.4 addendum no v3 result is re-labelled, re-run to pass or replaced; v4 refits from cold starts on new seeds; its single validation look is governed by §A6.
2. **Design provenance.** The v4 changes (T rule, cell and station rule, speed-at-capacity constraint and its enforcement, P11-k, relocation domain, E15 δ_m = 0 under step (b) V9 adopted) were designed after seeing v3 calibration-day model output, including post-stop diagnostics: the step probe, the capacity grid, §4.8, and the 2026-10-06 review and design runs, all ledgered report-only (D4.4). **The §A1 B-set rule eases relocation (b), rule (iv) and F̂ estimability, and shrinks F1's domain; every F̂-based result names this.**
3. **Calibration days are used a second time.** Every v4 calibration-day diagnostic is in-sample.
4. **Validation days:** never simulated by any model, but not data-blind. Their real-side facts (F11, per-day real episodes) are committed, and review rounds 2–3 inspected the Wednesdays.
5. **Plant attempts.** Every downstream result states "plant selected after N attempts (listed)", where N counts every committed METANET or SUMO plant protocol for this corridor that reached calibration, stopped or abandoned ones included (**N = 2 at v4:** METANET v3 stopped; v4 reopened the route as a disclosed deviation from v3 §0.3).
6. **Carried over from the v3 record:** the §5.5 / Appendix A remnant that lists step-halving as reported; the isfinite-to-NaN mask fix; the CMA-ES provenance; the late step-probe ledger row; the 7,190,100–108 seed-role mix; and **v3's F14 omitted the G1/G2 ratios required by v3 §1.7; computed for v4 only.**
7. **Known model properties:**
   - the fitted model may be linearly unstable in the queue band (Payne-type);
   - δ_m bounds go far beyond reported literature values [VERIFY];
   - metering and VSL responses are extrapolations;
   - the lane count at E15–X15 is unresolved (G4 substitute);
   - **residual risk:** a day at a threshold can flip between T and T/2 even when converged (v3: 20230517 at margin 0 at every converged step). Such a flip is an N0 FAIL (no tolerance).
8. **Known failure paths** (consequences unchanged from v3):
   - (a) **E15 relocation** → c2\* < 1.00 → rule (iv) → neither F̂ nor F̂_T → at best deterministic-only, KILL-only (under §A6 (7)(b): no usable spread at the freeze, so a stop at the freeze). Days that relocate at every pair also count toward rule (i). An E15 queue reaching cell 35 shows as a model P_2 episode: on real-B2-inactive days it is a P8(iii) extra; on real-B2 days it is agreement at the wrong head. If V9 is adopted, its δ_m = 0 at E15 removes the merge term only; relocation by E15 inflow against G4's fitted capacity stays possible.
   - (b) **B2 knife edge** (v3 grid at c1 = 1: B2 active on 22/22 days at c2 = 0.90, 2/22 at 1.00). P3-2 or P8(iii) failing alone → route stop. P4-2 or P5a-2 failing → F1 is fitted, then a FAIL is expected.
   - (c) **B1 after §A3:** P3-1 and P4-1 fail together → F1 → expected FAIL.
   - (d) **Step-halving tie** (item 7, residual risk).
9. **Test-2 provenance.** ε and the grid were fixed after data-free review scans. Worst stable-state growth: 1.1e-5 s⁻¹ at 0.75 s and 2.0e-5 at 1.0 s (floor state with V′ kept: τ = 10, ν = 30, κ = 60, v_f = 120, ρ_cr = 30, a = 3.5, ρ = 2ρ_cr, L = 304 m); 4.95e-3 at 1.25 s (floor state with V′ = 0: τ = 10, ν = 90, κ = 5, ρ = ρ_max, L = 300 m; 217 stable states > ε). Unchanged with 721 θ. T stays 0.75 s.
10. **Same-cell corrections.** v3's text listed I-494 (+X10) and Anderson Lakes Pkwy (−E13). On v4 cells the set is S453 (−E1, +X1; input only), S461 (+X8), S1770 (+X9) and S1771 (+X10) (§A1); Anderson Lakes needs none.
11. **v3 rules changed without a v3 counterpart:** the relocation (a) domain (§A1); F16 report-only, v3's blocking clause removed (§A4).

## A12. P11-k queue backing (new gated deterministic row, added to v3 §5.3; V8, adopted 2026-10-07)

| Item | Definition |
|---|---|
| Qualifying bin | a 5-min bin inside a model P_k episode in which the pair condition holds on detector scale (v_u < 40 mph and v_d − v_u ≥ 20 mph, model speeds after the observation operator) |
| Congested cell | bin-mean ρ_i > ρ̄_cr,i, where ρ̄_cr,i = the bin mean of cell i's per-step effective ρ_cr,i (θ1, c_k and the F1 state included), recorded by `simulate()` next to the bin-mean ρ_i |
| Backed bin | a qualifying bin with at least one congested cell **strictly between** the pair's station cells. **P_1: cells 26–31; P_2: cells 33–34.** The pair's own station cells (25 and 32 for P_1; 32 and 35 for P_2) never count; cell 27 (S1147, fit layer only) counts |
| Unbacked episode-day | a day with model P_k episodes whose qualifying bins, pooled over all model P_k episodes of the day, are < 50 % backed |
| Criterion (per k) | **PASS iff unbacked episode-days ≤ max(2, ⌈0.10·n⌉)** at c1 = c2 = 1, n = the usable days of the set evaluated [lab convention; P8 tolerance; fit-informed, disclosed under D4.4] |
| Nominal plant | usable calibration days at the freeze (a failure is a **route stop before any validation run**), then all usable validation days in the gate (gated) |
| Ensemble candidate | calibration and validation days; a failure on either makes that candidate **inadmissible**, as its own step-halving check does (v3 §4.6); no route stop |
| F1 | calibration days at F1's own freeze (a failure is an **F1 FAIL**, route stop, before F1's gate run), then validation days in F1's gate (gated) |
| v3 text | v3 §0.3's "P1–P9" reads "P1–P9 and P11-k". P11-k joins v3 §6.1's non-trigger list: it is not in the F1 trigger set, and a P11-k-only failure is a route stop |
| Reported | the pooled backed share per k; each unbacked day with its most downstream congested cell; under stochastic draws, the per-day share of draws with an unbacked episode (report-only) |

The deterministic conjunction grows from v3's 22 rows (§9.1) to 24; its false-FAIL risk is not computed.

## A13. Report-only additions

*Added to v3 §4.7 "Reported alongside", §4.8 and §5.5. None can waive, re-judge or soften a gated row, select a plant or ensemble member, or change T or the route.*

1. Per event station, the share of bins with event-scale model speed < 40 mph while every cell from its cell to the next downstream event station's cell is ≤ ρ̄_cr,i (§A12) (§4.8, §5.5).
2. v3 §2.3 mainstream-origin misfit minutes, split by ρ_1 ≤ / > ρ_cr,1.
3. Per group, v_c,g − thr_g, flagged "A3-active" if within 1 % (§A3 (g)).
4. For each model P_2 episode, the most upstream congested cell (§A12); episodes whose only congested cells are 35–39 are flagged (§4.8, §5.5).
5. **B1 discharge vs c1** (§4.7; cell 32, §A1): on usable calibration days with a real P_1 and no real P_2 episode, at grid pairs with a model P_1, no P_2 and no relocation: the median model B1 discharge (Pioneer Tr + X12) over the C4 window vs c1 at c2 = 1, and R(g) = median increment per 0.05 step / (0.05 × median at c1 = 1.00).
6. **Optional v3-set sensitivity** (runs only if opted in at V1; never replaces the primary): after the primary §4.7 result is committed, the §4.7 grid on calibration days at the frozen parameters with v3's sets on v4 cells (B1 = 27–32 with θ1 on 28, B2 = 33–35, relocation (a) on 36–39). Reported: c2\*, the F̂ verdict and the rules triggered.
7. **Backing of the §4.7 observations** (P11-k is gated only at c = 1): per plant, the backed share (§A12 definitions) of the model P_k episodes behind each exact ĉ_k,d.

## A14. Lab conventions added to v3 §9.2

- The T ladder {1.25, 1.0, 0.75, 0.625, 0.5} s and the limits of (a) 0.25, (b) 0.5, (c) τ_min/10, (d) and (f) < 1 (§A2); L_merge 250 m and the 500-m target (v3's L_min, renamed).
- Test 2's ε = 1e-4 s⁻¹, its state set and its grid (fixed after data-free review scans; §A11 item 9).
- A3: thresholds from the 40-mph event rule per FD group; the graded penalty form; the 1 % "A3-active" band.
- P11-k: the 50 % backed share; the strictly-between cell sets P_1: cells 26–31, P_2: cells 33–34 (the pair's own station cells, 25 and 32 for P_1 and 32 and 35 for P_2, never count; cell 27 (S1147, fit layer only) counts); the P8 tolerance max(2, ⌈0.10·n⌉).
- F16's 1.10, now report-only (§A4).

## 0.6 Author items for v4 (each answered before commit)

**All defaults below were accepted by the author on 2026-10-07 ("Let's go" to the proposed defaults; decision D4.9). V3: graded penalty, no rejection-sampled start (alternative (i) not taken). V7: freeze choice (b). V9: adopted.**

| # | Item | Decided default | Author |
|---|---|---|---|
| V1 | T rule and compute (§A2, §A9) | T = 0.75 s. Projections, measured on synthetic inputs before launch: base ≈ 17 h; with continuation ≈ 23 h; with F1 and continuation ≈ 30–36 h; + ≈ 0.8 h per further grid. The 24-h notice applies to the worst case. Residual risk: a threshold day can flip between T and T/2 even when converged, which is an N0 FAIL (§A11 item 7). The optional v3-set sensitivity (§A13 item 6, ≈ 0.8 h) runs only if opted in here; default: not run. Confirmed knowing §A11 item 8. | accepted 2026-10-07 |
| V2 | Cell rule (§A1) | Stations are not break points; B1 = 28–31 with H1 = 28 (E13 merge cell), B2 = 33–34; station cells never scaled; relocation (a) on cells 35–39. Rejected alternative: head-only (28; 33); selected from 2. | accepted 2026-10-07 |
| V3 | Speed at capacity (§A3) | Admissibility constraint with the graded penalty J = 10 + Σ shortfall, pre-simulation check, no rejection-sampled start (v3 §4.4 initial means unchanged; replay disclosed in §A3); infeasible profile points skipped. Alternative (review R2-1 (i)): keep a rejection-sampled initial mean (redraw x ~ U[0.25, 0.75]^n until A3 holds; base and F1) as insurance. Also confirms: no admissible restart → stop at the freeze (§A3 (d)). | accepted 2026-10-07 |
| V4 | Seeds (§A8) | 7,191,xxx as tabled, with the v3 concordance; F8 and F11 seeds reused as committed. | accepted 2026-10-07 |
| V5 | Downstream geometry (§A4) | Lane check inconclusive → step (b), G4 = cells 36–39 without condition; F16 report-only on cells 27, 32, 35–39. Confirmed knowing §A11 item 8. | accepted 2026-10-07 |
| V6 | Route reopening (§A11 item 1) | v4 reopens the METANET route stopped by v3 §0.3/§6.2, on the same 97 validation days, as a disclosed deviation decided by the author after the v3 results. Recorded in the decision log in the D3.1/D3.5 style. | accepted 2026-10-07 |
| V7 | Single look and freeze choice (§A6) | Rule (1)–(6), including the v3 §6.3 amendment. Freeze choice (7): **(b) stop at the freeze** as a pre-registered end if no usable spread exists at the freeze, that is, F̂ is not estimable by rule (i) or (iv), or F̂ is not estimable by (ii)/(iii) and F̂_T is not usable (v3 §0.3, §4.7). Reason: it keeps the 97 days unlooked, since a deterministic-only plant can only KILL and only positive DRL results count. Alternative: (a) run the gate anyway (KILL-only; uses the look). | accepted 2026-10-07 |
| V8 | P11-k (§A12; review record `docs/plans/day_pattern_metanet_protocol_v4_review.md` R1-1) | Adopt the gated queue-backing row and its conventions. | accepted 2026-10-07 |
| V9 | E15 mitigation (§A4) | Adopt "under step (b), E15 is lane-adding, δ_m = 0 at E15", disclosed as designed after seeing v3's relocation at E15 (D4.4), consistent with the G4 premise of an added lane at E15 (OSM shows 3 lanes from about the E15 gore). Alternative: none (δ_m at E15 as in v3). | accepted 2026-10-07 |
