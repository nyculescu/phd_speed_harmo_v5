# phd_speed_harmo_v5

Standalone project — Lagrangian CAV control with distributional RL (QR-DQN).
Single topology: 4-to-3 highway merge (`merge_4_to_3_v0`).
Run all commands from the project root (`phd_speed_harmo_v5/`).

## v4 → v5 paradigm shift

| | v4 | v5 |
|---|---|---|
| Control | Eulerian VSL → post sign → wait for HDV compliance | Lagrangian → `slowDown()` on CAVs directly |
| Useful episode time | 16–27% (METASTABLE only) | 100% (CAV control always applicable) |
| E1 window | 150 s (propagation lag breaks credit assignment) | 30 s (5× finer; 5-frame stack gives 150 s context) |
| State | Single-frame, no regime awareness | 5 × 21 = 105-dim stacked; regime one-hot inside |
| Action | Relative delta (stateful, anti-flicker logic) | Absolute 7 levels 70–100 kph (stateless) |
| Reward | 9 terms + mobility-budget constraint | 3 terms: variance + throughput + smoothness |
| Algorithm | DQN (collapses to do-nothing) | QR-DQN (distributional; handles bimodal returns) |

## Directory layout

```
phd_speed_harmo_v5/
├── core/                                   lightweight SUMO/RL interface
│   ├── algos/                              algorithms ported from v4
│   │   ├── dqn_v0.py                       DQN with prioritised replay
│   │   ├── qrdqn_v0.py                     QR-DQN (primary algorithm)
│   │   ├── qrdqn_policy_cvar_v0.py         CVaR risk-averse policy for QR-DQN
│   │   └── rbc51dqn_v0.py                  Rainbow-C51-DQN variant
│   ├── constants.py                        MAX_SPEED_KPH and step/action limits
│   ├── env_metrics.py                      TrafficMetrics dataclass
│   ├── env_interact.py                     TrafficEnv (gymnasium.Env)
│   ├── regime_detector.py                  free-flow / metastable / congested classifier
│   └── sar_frame.py                        SAR ABCs + factory functions
├── sar_components/                         isolated registry; only v0 components
│   ├── states/m43_state_v0.py              5×21 stacked E1 obs (105-dim)
│   ├── actions/m43_action_v0.py            Discrete(7) absolute speed [70–100 kph]
│   └── rewards/m43_reward_v0.py            3-term: −σ² + Δflow − smoothness
├── traffic_environment/
│   ├── scenario_generator.py               scenario pair generation (rou + sumocfg)
│   ├── rou_writer.py                       SUMO route file builder
│   ├── demand_profiles.py                  demand curve utilities
│   └── sumo/
│       ├── 4_3_merge.net.xml               highway network
│       ├── loops_detectors_m43_v0.add.xml  48 E1 + 4 E3 detectors (freq=30 s)
│       ├── variable_speed_limits_signs.add.xml
│       ├── network_config_4_3.yaml         segment/route definitions
│       └── colored.view.xml                SUMO-GUI settings
├── configurations/
│   ├── _common_config.yaml                 project-level defaults (SAR, SUMO, logging)
│   └── m43_v0/
│       ├── _common_agents.yaml             agent-level overrides + evaluation spec
│       ├── qrdqn_config.yaml               QR-DQN hyperparameters (primary)
│       └── dqn_config.yaml                 DQN hyperparameters (comparison baseline)
├── training/                               training scripts (to be written)
├── evaluation/                             evaluation scripts (to be written)
├── tests/
│   ├── test_env_inter.py                   21 dry-run integration tests (no SUMO needed)
│   ├── test_traf_env.py                    full single-episode SUMO smoke test
│   ├── test_env_metr.py                    34 E1/E3 sensor metric tests
│   └── results/                            per-run CSVs + summaries (gitignored)
├── docs/speed_harmo_approach_v0.md
├── pytest.ini
├── run_v0_sequential.sh                    full train + eval entry point
└── .gitignore
```

## Tests

### Dry-run (no SUMO required)

Exercises the full SAR call stack with all traffic metrics set to zero.

```bash
source .venv/bin/activate
pytest tests/test_env_inter.py -v
# 21 tests, < 1 s
```

### SUMO integration (requires SUMO 1.26+)

```bash
# Single-episode smoke test — generates one scenario and runs it end-to-end.
# Writes episode_steps.csv + summary.txt to tests/results/m43-v0_<date>/
pytest tests/test_traf_env.py -v -s

# E1 / E3 sensor metric coverage — 34 tests across all 48 E1 and 4 E3 detectors.
# Writes metric_snapshot.csv to tests/results/m43-v0_<date>/
pytest tests/test_env_metr.py -v

# All SUMO tests at once
pytest -m sumo -v

# Full suite (dry-run + SUMO)
pytest tests/ -v
# 56 tests, ~9 s
```

### Detector inventory

| Family | Count | IDs | Freq |
|---|---|---|---|
| E1 induction loops | 48 | `flow_loop_{seg}_{lane}_{pos}` | 30 s |
| E3 multi-entry-exit | 4 | `e3_seg_2_before`, `e3_seg_1_before`, `e3_seg_0_before`, `e3_corridor` | 30 s |

To add a new metric to `test_env_metr.py`: append one `E1Spec` or `E3Spec` entry to `_E1_SPECS` / `_E3_SPECS`. No other change needed.

## Full training run

```bash
# 50% CAV penetration (default)
bash run_v0_sequential.sh

# CAV sweep
CAV_PERCENT=75.0  bash run_v0_sequential.sh
CAV_PERCENT=100.0 bash run_v0_sequential.sh
```

Trains QR-DQN then DQN sequentially, then evaluates all controllers.
Logs → `logs/m43_v0/` · Results → `evaluation/results/m43_v0/`

## Academic grounding

| Decision | Reference |
|---|---|
| Lagrangian CAV control | Vinitsky et al. (2018) |
| 3-term reward + real deployment | Zhang et al. (2023–2024) — MARVEL, I-24 |
| QR-DQN for stochastic returns | Dabney et al. (2017) |
| CAV mixed-traffic DRL | Hua et al. (2023) |
