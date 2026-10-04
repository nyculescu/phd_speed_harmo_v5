# Lead 1, T1-M2: incident-aware hybrid metering with varied severity and duration, pre-registration

*Committed 2026-10-03, before any run.*
- **Author decisions:** "both leads in parallel"; seed block **7,170,000–7,170,999** approved, with roles 000–099 scan, 100–299 tuning, 300–499 validation, 500–699 test, 700–999 reserved confirmatory.
- **Builds on** the R6 claim (`t1_meter_r6.md`).

**Why.** The R6 controller is still 5.8 % behind the oracle, and it chooses among 4 fixed settings tuned for 4 fixed event types. Real events vary in severity and duration. Fixed detector thresholds and fixed lookup settings should degrade there, while a policy with memory need not.

## Stage S: headroom scan (seeds 7,170,000–7,170,009)

**Plant:** BN4 at q = 1,600 (as in T1-M), 10 % uncontrolled AVs. Metric: door-to-door time.

**22 conditions** (per-seed start time from rng(seed + 991)):

| Kind | Variants |
|---|---|
| `none` | — |
| `slow` | v ∈ {3, 5, 8} m/s × duration ∈ {150, 300, 600} s |
| `block` | duration ∈ {60, 180, 360} s |
| `surge` | factor ∈ {1.15, 1.3, 1.5} × duration ∈ {150, 300, 600} s |

**Controllers (22):** `nc`, `meter:K:n` for K ∈ {5, 10, 20, 40} and n ∈ {4, 6, 8, 10, 12}, and `evsched:7:20:1.15` (the T1-M tuning, not re-tuned).
**Runs:** 4,840.

**Measures:**
- **G (all 22 conditions)** = (J of the pooled best fixed setting − mean of the per-condition best fixed J) / J pooled. Also reported per kind.
- **H_pre** = the same lookup against the best of {pooled fixed, `evsched`}. This is preliminary, because `evsched` is not re-tuned on this mix.

**Rule:**
- **G ≥ 10 % and H_pre ≥ 10 %:** go to stage H, pre-registered then. It will have a re-tuned `evsched`, an MPC-F refit on this mix (tuning seeds 7,170,100–7,170,299), and gate seeds.
- **Otherwise:** Lead 1 stops. G is biased upwards, so this is a conservative stop.
