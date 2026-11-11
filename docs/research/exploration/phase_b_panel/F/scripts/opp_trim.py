import sys
f = sys.argv[1]
s = open(f).read()
R = [
 ("(cmab.py:220-223)", "(cmab.py:221-224)"),
 ("(`planb_remote/s2/s2_trace.json`)", "(`v5b1_runs/planb_remote/s2/s2_trace.json`)"),
 ("""- The planb.md:575 override; S2's registered KILL and V486's replacement (V487).
- TRUCK was chosen after related DRL results (planb.md:164).
- Close-following is a reward term, read at 1 Hz (PR-23).
- v3w's checkpoints were chosen on X1/X2 validation (planb.md:188).
- Each search's budget and plateau label.""",
  """- The planb.md:575 override; S2's registered KILL and V486's replacement (V487); TRUCK chosen after related DRL results (planb.md:164).
- Close-following is a reward term, read at 1 Hz (PR-23). v3w's checkpoints were chosen on X1/X2 validation (planb.md:188).
- Each search's budget and plateau label."""),
 ("- No barred word. No win on one measure alone, unless decision 2 allows the paired form.", "- No barred word; no win on one measure alone unless decision 2 allows the paired form."),
 ("The search was still moving at generation 100 (generation-median close-following −12.6 % to −17.0 %, critic_F F4), and", "The search was still moving at generation 100 (critic_F F4), and"),
 ("leaves room for stage A only, until 2026-11-16.", "leaves room for stage A only until 2026-11-16."),
 ("Author time, apart: about 2 h for three approvals.", "Author time, apart: about 2 h."),
 ("Proposal. No run, seed, rental or ledger row. Stored-row numbers", "Proposal: no run, seed, rental or ledger row. Stored-row numbers"),
]
for a, b in R:
    assert a in s, a[:60]
    s = s.replace(a, b)
open(f, "w").write(s)
