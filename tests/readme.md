# Test Suite

## When to run

Run the **full suite** before:
- Starting a training run
- Merging a pull request
- Changing any SAR component (state, action, reward)
- Changing the SUMO network or detectors

Quick command:
```bash
pytest tests/ -v -s
```

Run only the fast tests (no SUMO needed):
```bash
pytest tests/ -v -k "not sumo"
```

---

## Test overview

### Tests that do NOT need SUMO

These run in seconds. They verify that the Python code is internally consistent.

| Test file | What it checks | Why it matters |
|---|---|---|
| `test_config_consistency.py` (8 tests) | The YAML config file (`_common_config.yaml`) matches the hardcoded values used elsewhere in the code. Also checks that episode duration divides evenly by the aggregation window. | If someone changes a number in the config but forgets to update the code (or vice versa), training silently uses wrong values. This catches that. |
| `test_env_inter.py` (9 tests) | Runs the full environment in "dry-run" mode (no SUMO, all traffic metrics are zero). Checks observation shape (56 dims), action space bounds ([60-120] kph mainline, [40-90] kph ramp), reward component ranges, episode length, and that nothing crashes at action-space corners. | Proves the SAR framework wires together correctly. If the state representation changes its output size, or the action space changes its bounds, these tests catch it immediately without needing to wait for a SUMO simulation. |

### Tests that NEED SUMO

These launch real SUMO simulations. They take 1-10 minutes each depending on the demand level and episode length.

| Test file | What it checks | Why it matters |
|---|---|---|
| `test_detector_alignment.py` (1 test) | Boots SUMO with the ramps_v1 network and tries to read every detector ID that the environment code generates programmatically. If a detector ID is wrong (typo, wrong naming convention), the read fails. | The environment's `_collect_metrics()` silently catches exceptions when a detector ID doesn't exist — it just returns zero. This means a broken detector ID produces zero metrics with no error message. This test catches that silent failure. |
| `test_state_live.py` (1 test) | Runs a full 1-hour episode at 7000 veh/h (guaranteed congestion). At every step, checks that the 56-dim observation is in [0, 1], the regime one-hot sums to 1.0 in populated frames, frame stacking produces different frames after step 3, and the previous-action features encode correctly. | Verifies the observation contract under real traffic conditions, including the transition from free-flow to congestion. A broken normalisation (e.g., speed exceeding the assumed max) would push observation values outside [0, 1], which breaks neural network training. |
| `test_ramp_vsl_effect.py` (1 test) | Runs two identical episodes (same demand, same seed) but with different ramp VSL settings: 90 kph vs 40 kph. Measures the actual CAV speed on the ramp transition edge. Asserts the difference is at least 5 kph. | Proves that the second action dimension (ramp VSL) actually does something. If the ramp control has no measurable effect on vehicle speeds, the agent cannot learn to use it — the action dimension would be dead weight. |
| `test_reward_e2e_verification.py` (2 tests) | The main test: runs a 600s episode at 6500 veh/h. At each step, reads the raw E1 detector values independently (not through the environment's code) and hand-computes what the reward should be using the exact same formulas as the reward function. Then compares the hand-computed reward against what the environment actually returned. Tolerance: 0.001. The second test verifies that the temporal reward term uses downstream speed (seg_0_after) and NOT upstream speed. | This is the strongest test. It proves that the reward the agent receives during training is mathematically correct — that there is no bug in the chain from SUMO detectors to the final reward number. Without this test, a reward computation bug could silently produce wrong training signal for hundreds of episodes before anyone notices. |
| `test_nocontrol_baseline.py` (1 test) | Runs 8 no-control episodes at different demand levels (2500-7000 veh/h) with no VSL applied. Records speed, flow, and occupancy at every segment for every 30s window. Writes a CSV to `tests/results/`. | Provides the baseline data that answers: "at what demand does congestion form?" and "how fast does the transition happen?". This is needed both for calibrating the reward function and for evaluating whether the trained agent actually improves over doing nothing. |
| `test_env_metr.py` (21 tests) | Comprehensive check of all E1 and E3 detector readings: correct count, correct data types, correct value ranges, correct vehicle ID formats, lane IDs, positions. Also runs a full-episode metric snapshot. | Verifies that the raw data pipeline from SUMO to the environment's TrafficMetrics object works correctly. **Note: currently broken** — depends on `scenario_generator.py` → `rou_writer.py` pipeline which requires a missing config file (`network_config_4_3.yaml`). |
| `test_traf_env.py` (1 test) | Full integration test: generates a scenario using the production pipeline (`scenario_generator.py`), boots SUMO, runs a complete episode through the TrafficEnv, and verifies observation/reward/termination at every step. | End-to-end test of the entire system as it would run during training. **Note: currently broken** — same dependency issue as `test_env_metr.py`. |

### Offline scripts (not pytest tests)

| Script | What it does | When to run |
|---|---|---|
| `run_fixed_vsl_sweep_v1.py` | Runs 25 SUMO simulations in parallel: 5 constant VSL levels (no-control, 50, 70, 90, 110 kph) × 5 demand levels (5000-7500 veh/h). Each simulation is a full 1-hour episode. Records per-step speed, flow, and occupancy for every segment. Produces per-scenario CSVs and a summary table with upstream speed variance (σ), per-segment averages, downstream flow, and breakdown step count. | Once before the first training run, and again if the network, vehicle types, or demand split change. This answers "is the problem solvable at all?" — if no constant VSL reduces speed variance compared to no-control, no RL agent can learn to do it either. The summary CSV is also the evaluation benchmark: after training, compare the agent's performance against the best fixed-VSL row. Takes ~15-30 min depending on CPU cores. |
| `run_reward_landscape_check.py` | Reads the summary CSV produced by `run_fixed_vsl_sweep_v1.py` and computes what the reward function would return for each scenario. Prints a table showing whether the reward gradient is correct (no-control beats VSL at free-flow; moderate VSL beats no-control at congestion). | After changing the reward function or its weights. Requires the summary CSV from `run_fixed_vsl_sweep_v1.py` to exist first. |

---

## Known issues

1. **`test_env_metr.py` and `test_traf_env.py` are broken.** They use the production scenario generation pipeline (`scenario_generator.py` → `rou_writer.py`) which depends on `network_config_4_3.yaml` — a file that does not exist in v5. The other SUMO tests bypass this by using the simpler `_sumo_helpers.py` generator.

2. **All SUMO tests use `_sumo_helpers.py`**, which generates constant-flow, homogeneous-fleet scenarios. This is sufficient for validating the framework but does NOT test the production scenario generation pipeline that would be used for real training.

---

## Recommended run order

1. `test_config_consistency.py` — instant, catches config drift
2. `test_env_inter.py` — instant, catches SAR wiring bugs
3. `test_detector_alignment.py` — ~10s, catches detector ID mismatches
4. `test_reward_e2e_verification.py` — ~2 min, catches reward computation bugs
5. `test_state_live.py` — ~5 min, catches observation normalisation bugs
6. `test_ramp_vsl_effect.py` — ~10 min, catches dead action dimensions
7. `test_nocontrol_baseline.py` — ~30 min, generates baseline data for evaluation
