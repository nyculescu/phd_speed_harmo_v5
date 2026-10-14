# External research runs (Claude Console Workbench)

Prompts that the author runs by hand on platform.claude.com (budget $200, from 2026-10-13). The answers are pasted back into the same file.
- **Never codebase work:** no code, no repo content, no code review.
- **Two uses only:** parallel web research, or a second-angle review of an idea described in full.

## Workbench settings (apply to every run unless the file says otherwise)
| Setting | Opus 5.5 research runs | Fable 5.1 review runs |
|---|---|---|
| Model | `claude-opus-5-5` | `claude-fable-5-1` |
| Thinking | adaptive (it is always on) | always on (no setting needed) |
| Effort | **high** (the default is medium; raise it) | **high** |
| Max tokens | 16,000 | 32,000 |
| Tools | **web search ON**, max uses 25 (caps cost). Add web fetch too if offered | **none** (no web) |
| System prompt | the "Shared rules" block below | the "Shared rules" block below |

If the Workbench does not offer the web search tool for a model, do not run that research prompt; tell Claude Code instead. Without search, the model can only answer from memory, and citations would be unreliable.

## Shared rules (paste as the system prompt)
```
You are a careful research assistant for a PhD in traffic control. Accuracy beats completeness.
- Never invent titles, authors, years, venues, DOIs, URLs, equations, numbers or quotes.
- For every factual claim give the source (authors, year, title, venue) and the URL you actually opened, and say what you read: full text, abstract, or a secondary mention.
- Mark anything you could not confirm from a source you opened as [VERIFY].
- Use SI units. Give equations exactly as published, with symbol definitions and units.
- If sources disagree, show both. If something is unknown, say "unknown".
- Prefer peer-reviewed papers, official reports and primary data over blogs and summaries.
- Keep to the requested output structure and length.
```

## After pasting
Claude Code spot-checks the key citations and numbers before anything enters the design or the protocol. Pasted answers are research input, not decisions.

## Runs
| File | Model | Status |
|---|---|---|
| X01_cav_controller_laws.md | Opus 5.5 + web | ready to run |
| X02_vsl_compliance.md | Opus 5.5 + web | ready to run |
| X03_redteam_design.md | Fable 5.1, no web | ready to run |
| X04_sumo_capacity_drop.md | Opus 5.5 + web | ready to run (needed for V70) |
