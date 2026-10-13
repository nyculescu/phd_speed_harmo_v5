# v5.B.1: coordinated zone control on a multi-bottleneck freeway

PhD thesis: "Adaptive driving algorithms for intelligent road traffic systems".
v5.B.1 is the primary PhD line (author, 2026-10-13), rebuilt from the ground up, step by step.

**Research question (draft, to be confirmed):** can communicating zone controllers that command CAV speeds,
per-lane speed limits for human drivers and ramp meters cut door-to-door delay and stop-and-go traffic,
without hurting safety or shifting congestion? And does learning-based control (DRL alone or a hybrid) beat
the best tuned conventional control in identifiable regimes (the D5.8 conditional bar in `CLAUDE.md`)?

## Status
```
project_init ─► architecture review ─► §11 design artifacts ─► gap analysis vs the archive ─► protocol (P0/P1) ─► code
     ▲ here
```
Nothing is implemented yet. The network is not chosen (CORR2X is one candidate).

## Layout
| Path | Content |
|---|---|
| `v5b/` | the Python package (empty at init) |
| `tests/` | pytest suite; `test_toolchain.py` pins the toolchain |
| `docs/architecture/` | system context, interfaces, diagrams |
| `docs/testing/` | test strategy |
| `docs/research/` | experiment protocol |

## Running
```bash
unset SUMO_HOME; export OMP_NUM_THREADS=1
/home/catalin/work/phd/phd_speed_harmo_v6_toolchain/venv314/bin/python -m pytest
```

## History
This branch starts with empty history. Earlier work is archived on `claude/v5b-core`, `claude/day-pattern-core`,
`claude/vsl-lab-core` and `main`; see `CLAUDE.md` (Repo state). Code ported from them is recorded in the commit
that ports it.
