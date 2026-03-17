# phd_speed_harmo_v5

Standalone v5 project — Lagrangian CAV control with distributional RL (QR-DQN).
Rooted at `phd_speed_harmo_v4/phd_speed_harmo_v5/`; run all commands from here.

## v4 → v5 paradigm shift

| | v4 | v5 |
|---|---|---|
| Control | Eulerian VSL → post sign → wait for HDV compliance | Lagrangian → `slowDown()` on CAVs directly |
| Useful episode time | 16–27% (METASTABLE only) | 100% (CAV control is always applicable) |
| E1 window | 150s (= propagation lag, breaks credit assignment) | 30s (5× finer, 5-frame stack = 150s context) |
| State | Single-frame, no regime awareness | 5 × 21 = 105-dim stacked; regime one-hot inside |
| Action | Relative delta (stateful, anti-flicker logic) | Absolute 7 levels 70–100 kph (stateless) |
| Reward | 9 terms + mobility-budget constraint | 3 terms: variance + throughput + smoothness |
| Algorithm | DQN (collapses to do-nothing) | QR-DQN (distributional; handles bimodal returns) |

## Directory layout

```
phd_speed_harmo_v5/
├── core/                               lightweight SUMO/RL interface (standalone)
│   ├── constants.py
│   ├── env_metrics.py                  TrafficMetrics dataclass
│   ├── env_inter.py                    TrafficEnv (gymnasium.Env)
│   ├── regime_detector.py
│   └── sar_frame.py                    SAR ABCs + factory functions
├── sar_components/                     isolated registry; only v0 components
│   ├── states/m43_state_v0.py          5×21 stacked E1 obs (105-dim)
│   ├── actions/m43_action_v0.py        Discrete(7) absolute speed [70-100 kph]
│   └── rewards/m43_reward_v0.py        3-term: −σ² + Δflow − smoothness
├── traffic_environment/
│   ├── scenario_generator.py           merge_4_to_3_v0 topology
│   └── sumo/
│       ├── loops_detectors_m43_v0.add.xml   freq=30s detectors
│       └── 4_3_merge.net.xml
├── train_eval/
│   ├── algorithms/                     QRDQN_v3, DQN_v1, …
│   ├── config/m43_v0/                  experiment configs
│   ├── drl_vsl_train.py
│   ├── drl_vsl_eval.py
│   └── trained_models/m43_v0_s0_0/
├── tests/
│   └── test_env_inter.py               21 dry-run integration tests
├── logs/m43_v0/
├── docs/speed_harmo_approach_v0.md
└── run_v0_sequential.sh                entry point
```

## Quick start

```bash
cd phd_speed_harmo_v4/phd_speed_harmo_v5

# Verify setup
python -c "
from sar_components.discovery import discover_components; discover_components()
from sar_components.registry import STATE_REGISTRY, ACTION_REGISTRY, REWARD_REGISTRY
assert 'm43_state_v0' in STATE_REGISTRY
assert 'm43_action_v0' in ACTION_REGISTRY
assert 'm43_reward_v0' in REWARD_REGISTRY
print('All components OK')
"

# Smoke test (10 envs, 100k steps, skip scenario generation)
python train_eval/drl_vsl_train.py \
  --config train_eval/config/m43_v0/s0_0/qrdqn_config.yaml \
  --override training.total_timesteps=100000 \
  --override training.num_train_envs=10 \
  --override scenario_generation.new_scenarios=false

# Full run (50% CAV penetration)
bash run_v0_sequential.sh

# CAV sweep
CAV_PERCENT=75.0 bash run_v0_sequential.sh
CAV_PERCENT=100.0 bash run_v0_sequential.sh
```

## Academic grounding

| Decision | Paper |
|---|---|
| Lagrangian CAV control | Vinitsky et al. (2018) |
| 3-term reward + deployment | Zhang et al. (2023-2024) — MARVEL, I-24 |
| QR-DQN for stochastic returns | Dabney et al. (2017) |
| CAV mixed-traffic DRL | Hua et al. (2023) |

## Scripts

### Integration tests

Tests run in **dry-run mode** (no SUMO required). From the project root:

```bash
# activate venv first
source .venv/bin/activate

# run all tests
pytest tests/ -v

# run a single test class
pytest tests/test_env_inter.py::TestEpisode -v
```

All 21 tests should pass in under a second.