# paper_1 forensic audit (2026-10-21)

A read-only, claim-by-claim audit of `papers/paper_1/paper.qmd` at commit `4de404a`. Decisions about it: V130 and V131 in `docs/decisions.md`.

| File | Content |
|---|---|
| `REPORT_paper1_forensic_audit.md` | Main report: method, bottom line, big picture, implementation vs paper, experimental forensics, claim-evidence matrix (86 claims), prioritised findings (101 groups), what the paper can claim, verification steps, limits |
| `REPORT_appA_claims.md` | Full dossier per claim and per agent: meaning, evidence, verification, verdict, failure points |
| `REPORT_appB_findings.md` | Full text of every finding and every adversarial verifier's reasoning |
| `REPORT_appC_scripts.md` | Every command and script each agent ran, with its outcome |
| `FINDINGS_REGISTER.md` | One proposed resolution per finding group; decisions D1-D6 |

Scripts and small outputs: `~/work/phd/v5b1_runs/audit_paper1_2026-10-21/` (not in the repo; caches over 10 MB excluded, listed in `EXCLUDED_CACHES.txt`). The generators for these files are `build_report_parts.py`, `make_notes.py` and `make_register.py` in that folder.
