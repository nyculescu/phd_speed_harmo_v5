# METANET v5: §B11.2 fix record format (operational; what the gate guard checks)

A fix record is a JSON file in `docs/lab/day_pattern/metanet_v5_fixes/`, **committed after the fix commit** (the guard only reads tracked, unchanged records). Protocol: v5 §B11.2 (rule, order, audits, which outcome counts) and §B8 (gate guard).

| Field | Required | Checked by the guard (`metanet_v5_gate.fix_record_valid`, `fix_rerun_ok`) |
|---|---|---|
| `fix_commit` | yes | a full 40-character SHA (never `HEAD` or a branch); the commit changed at least one v5 code path (`metanet_v5_calibrate.CODE_PATHS`) |
| `failing_before_test` | yes | a repo path that exists at `fix_commit` (the unit test that fails on the code that produced the result and passes after) |
| `rerun_seed` | for a re-run | one seed or a list (nominal and members); the seed's earlier start-record code must be an ancestor of `fix_commit` (the fix postdates the run it repairs); `fix_commit` must be an ancestor of the current code identity, with no v5 code-path change after it |
| `freeze_record_commit` | only to name a later freeze record | equals the latest commit of `metanet_v5_calibration.json`; `fix_commit` must be an ancestor of it |
| `quote`, `why` | yes (§B11.2 item 1 "Record") | not machine-checked: the committed protocol text and why the old code contradicts its only reading |

**Code identity** (start records, provenance stamps, batch summaries) is the last commit that changed a v5 code path or committed input, not HEAD. Commits that touch none of them (docs, ledger, other tracks, sibling sessions) never lock a run between stages. A real code change does, until a valid fix record names the seed.
