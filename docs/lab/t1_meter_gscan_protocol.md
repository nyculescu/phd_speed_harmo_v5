# T1-M: headroom scan for the BN4 feedback meter under perturbations, pre-registration

*Committed 2026-10-03, before any scan run. Author choice: "A now, build B in parallel".*

**Why.** Posted-VSL harmonisation on LD3 was killed (G ≤ 4 %). DRL needs conditions in which the best classical *setting* changes strongly.
- **BN4** is the one plant where SUMO showed a capacity drop (1,044 → 900 veh/h).
- **Its meter** has large authority (−45 % door-to-door vs NC, R2 v2).
- **A feedback meter with a fixed set-point** (Vinitsky's q ← q + K_F (n_crit − n̂)) is expected to be wrong when capacity or demand changes unexpectedly.

**Plant:** BN4 as in R2 v2, with 10 % uncontrolled AVs, 40 s warm-up, 900 s control and an uncontrolled drain.
**Metric:** mean door-to-door time, including the origin queue.

**Perturbations** (env `perturb`; start ~ U(warm-up + 100, end − dur − 100) from rng(seed + 991)):

| Kind | Effect |
|---|---|
| `none` | no perturbation |
| `slow` | bottleneck edge 5 speed limit → 5 m/s for 300 s (3 m/s caused a teleport in the smoke run, so it was made milder; disclosed) |
| `block` | a vehicle stops at mid-edge 4, lane 1, for 180 s (it brakes normally) |
| `surge` | inflow × 1.3 for 300 s |

**Conditions:** q ∈ {1,600, 2,000} × the 4 kinds = 8.
**Controllers:** `nc` + `meter:K:n` for K ∈ {5, 10, 20, 40} and n ∈ {4, 6, 8, 10, 12}, i.e. 21.
**Seeds:** 7,110,160–7,110,179. This is the unused part of the T1 tuning range, reassigned and disclosed.
**Runs:** 3,360.

**Families**, per q:
- {none, slow}, {none, block}, {none, surge}, and all four together.

For each family:
- **G** = (J_pool − J_look) / J_pool;
- **J_pool** = the best single setting, averaged over the family's conditions;
- **J_look** = the per-condition best setting (oracle);
- J is the median over seeds;
- teleports are reported per condition.

**Rule:**
- G ≥ 10 % → candidate DRL target. An **H** step follows, pre-registered then, with non-learning adaptive meters, e.g. set-point switching on a detected slowdown or blockage.
- G < 10 % everywhere → the meter is killed as a DRL target on BN4.
- G is biased upwards, so a FAIL is a conservative KILL.
