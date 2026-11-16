# ADR-001: Multi-agent trainer: own shared-parameter PPO on PettingZoo, replaceable

*Status: accepted (author, 2026-10-13; decisions V7, V17). Owner: the author. Revisit when a switch trigger in §5 fires.*

## 1. Context
- Each CAV is an agent (V7). Agents appear when a CAV enters a zone and disappear when it leaves, so the agent set changes every few seconds.
- The method requires a fair vanilla DRL arm: a standard algorithm (PPO), the same actuators and observations, the same budget, and checkpoints chosen on validation only (`CLAUDE.md`).
- What is available:
  - PettingZoo is an environment API, not a trainer.
  - SB3 trains a single agent. With SuperSuit parameter sharing it needs a fixed agent set (slots plus masks), and that re-creates the zone-slot design the author rejected (V3).
  - RLlib handles changing agent sets natively, but it is heavy (Ray) and hard to fit to "one libsumo simulation per process" and the CPU guard. TorchRL / BenchMARL: support for changing agent sets is unverified [VERIFY].

## 2. Decision
Write our own **shared-parameter PPO** in CleanRL style (one readable module, no framework) on a **standard PettingZoo `ParallelEnv`**:
- **Vanilla arm:** independent PPO, one policy shared by all CAVs, observations local to each CAV, no zone messages.
- **Candidate arm(s):** the same code with zone messages in the observation and, optionally, a centralised critic (MAPPO).
- Both arms use the same trainer code, budget and validation-only checkpoint selection.

## 3. Replaceability: the boundaries that make a switch cheap
| Boundary | Rule |
|---|---|
| Environment | `F3ZParallelEnv` is a plain PettingZoo `ParallelEnv` and passes `pettingzoo.test.parallel_api_test`. It imports no trainer library. Changing agent sets are expressed only through the per-step agent dict. |
| Policy contract | `Policy.act(obs: dict[agent_id, ndarray], deterministic: bool) -> dict[agent_id, action]`, plus `save(dir)` / `load(dir)` (torch `state_dict` + a JSON config). The evaluation runner sees only this contract. |
| Trainer contract | `train(env_factory, config, train_seeds, val_seeds, budget) -> run_dir` (checkpoints, learning curves, ledger row). The budget is stated in simulated seconds and in agent-steps, so it can be compared across trainers. |
| Adapters | Anything a replacement trainer needs (fixed slots plus masks for SB3/SuperSuit, the RLlib env wrapper) lives in `adapters/`, never in the environment. |
| Records | Every ledger row stores the trainer name, version or commit, and config hash. |

## 4. Verification before any traffic training (criteria fixed now; numbers are proposals until the protocol)
1. **Unit checks:** GAE / returns, advantage normalisation, the clipped objective, entropy and value loss against hand-computed values; correct handling of agents that leave mid-rollout (terminated vs truncated).
2. **Single-agent sanity:** on a Gymnasium task wrapped as a one-agent `ParallelEnv` (e.g. CartPole-v1), reach the task's solved threshold within a stated budget. Match SB3 PPO's learning curve within a stated tolerance on the same seeds.
3. **Changing-agent sanity:** a small toy with agents entering and leaving and a known (analytic) optimum. Reach ≥ 90 % of the optimum.
4. **Throughput:** agent-steps per second, stated against the CPU budget.

## 5. Switch triggers and fallback order
**Switch when** any §4 check fails after one bug-fix round, or when traffic training shows a defect traced to the trainer rather than to the environment or the reward.

**Fallback order:**
1. RLlib multi-agent, which handles changing agent sets natively [VERIFY the current API];
2. TorchRL / BenchMARL [VERIFY support for changing agent sets];
3. SB3 PPO + SuperSuit with a fixed-slot adapter (last resort: it re-introduces slots).

**Consequences of a switch:** every arm in a comparison uses the same trainer. A switch re-runs all learned arms; trainers are never mixed within one comparison. Both outcomes are logged.

## 6. Costs accepted
- We own a few hundred lines of RL code, and their correctness. Mitigation: the §4 ladder, and the "DRL training code done" review checkpoint (ultracode on) before long runs.
