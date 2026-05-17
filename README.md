# phd_speed_harmo_v5

Speed harmonization at a highway **on-ramp / off-ramp interchange** using Lagrangian CAV direct control
(`traci.vehicle.slowDown()`) and distributional RL (TQC / SAC / RecurrentPPO).

Single topology: **ramps_v0** — 3-lane mainline → 4-lane weaving buffer → 3-lane downstream,
with on-ramp and off-ramp flanking a 250 m weaving section.

Run all commands from the project root (`phd_speed_harmo_v5/`).

---

## Research pipeline

```
Step 1 (current): No-control baseline diagnostic
    → "At what demand level does seg_0_after break down, and is it predictable?"
    → python3 -m tools.no_control_baseline

Step 2 (next):    SAR framework design (state / action / reward)
    → informed by breakdown characterisation from Step 1

Step 3 (next):    Algorithm selection and training
    → TQC (primary) · SAC (baseline) · RecurrentPPO (POMDP-safe)
```

---

## v4 → v5 paradigm shift

| | v4 | v5 |
|---|---|---|
| Topology | 4→3 lane-drop (forced merge, stochastic gap-acceptance) | Ramp-on + ramp-off interchange (3L→4L buffer→3L; CAVs + ramp VSL) |
| Control | Eulerian VSL → sign → wait for HDV compliance | Lagrangian → `slowDown()` on CAVs directly |
| Observation window | 150 s | 30 s (5× finer; 5-frame stack gives 150 s temporal context) |
| Algorithm family | DQN / QR-DQN (discrete only) | TQC · SAC · RecurrentPPO (continuous) |
| State of SAR design | Fixed 3 years, no positive result | From scratch, data-informed |

---

## Directory layout

```
phd_speed_harmo_v5/
├── core/                                   lightweight SUMO/RL interface
│   ├── constants.py                        MAX_SPEED_KPH and step/action limits
│   ├── env_metrics.py                      TrafficMetrics dataclass
│   ├── env_interact.py                     TrafficEnv (gymnasium.Env)
│   ├── regime_detector.py                  free-flow / metastable / congested classifier
│   └── sar_frame.py                        SAR ABCs + factory functions
├── sar_components/                         isolated SAR registry (to be populated)
│   ├── states/
│   ├── actions/
│   └── rewards/
├── tools/                                  standalone diagnostic utilities
│   ├── no_control_baseline.py              Step 1: breakdown characterisation
│   └── results/                            CSV + PNG outputs (gitignored)
├── traffic_environment/
│   ├── scenario_generator.py               scenario pair generation (rou + sumocfg)
│   ├── rou_writer.py                       SUMO route file builder
│   ├── demand_profiles.py                  demand curve utilities
│   └── sumo/
│       ├── generate_ramp_network.py        generates ramps_v0.net.xml
│       ├── ramps_v0.net.xml                highway network (3L→4L buffer→3L, on+off ramp)
│       ├── detectors_ramps_v0.add.xml      E1 induction loops + E3 travel-time detectors (freq=30 s)
│       └── colored.view.xml                SUMO-GUI settings
├── configurations/
│   └── _common_config.yaml                 project-level defaults
├── tests/
│   ├── test_env_inter.py                   integration tests (no SUMO needed)
│   ├── test_traf_env.py                    full single-episode SUMO smoke test
│   └── test_env_metr.py                    E1/E3 sensor metric tests
├── docs/speed_harmo_approach_v0.md
├── pytest.ini
└── .gitignore
```

---

## Step 1: No-control baseline

Characterises merge breakdown across 5 demand levels **without any control intervention**.

```bash
# Run all 5 scenarios (requires SUMO 1.21+ and TraCI)
python3 -m tools.no_control_baseline

# Run with sumo-gui (interactive)
python3 -m tools.no_control_baseline --gui

# Run a single scenario (index 0 = lightest demand)
python3 -m tools.no_control_baseline --scenarios 0
```

**Demand scenarios** (off-ramp = 15 % of mainline)

| # | Mainline (veh/h) | Ramp-on (veh/h) | Ramp-off (veh/h) | Weaving flow (veh/h) |
|---|---|---|---|---|
| 0 | 1 200 | 200 | 180 | 1 400 |
| 1 | 1 800 | 300 | 270 | 2 100 |
| 2 | 2 400 | 400 | 360 | 2 800 |
| 3 | 3 000 | 500 | 450 | 3 500 |
| 4 | 3 600 | 600 | 540 | 4 200 |

**Outputs** → `tools/results/`
- `baseline_<main>_<ramp>.csv` — per 30-s window: flow, space-mean speed, breakdown flag
- `baseline_summary.csv` — breakdown time, min/mean speed, throughput per scenario
- `baseline_<main>_<ramp>.png` — speed + flow time-series (requires matplotlib)

**Breakdown criterion**: harmonic-mean speed across all 4 lanes of `seg_0_after` entry drops
below **60 km/h** for at least one 30-s window with ≥ 1 vehicle detected.

> ⚠ `ramps_v0.net.xml` must exist before running.  If missing, run
> `python3 traffic_environment/sumo/generate_ramp_network.py` and then open the file
> in **netedit → Processing → Compute Junctions** to generate internal edges.

---

## Detector inventory

| Family | Count | ID pattern | Freq |
|---|---|---|---|
| E1 induction loops | 48 | `flow_loop_{seg}_{lane}_{pos}` | 30 s |
| E3 multi-entry-exit | 5 | `e3_seg_*`, `e3_corridor` | 30 s |

Segments covered: `seg_2_before`, `seg_1_before`, `seg_0_before`,
`seg_0_after` (4-lane weaving zone — **critical**),
`ramp_on_approach`, `ramp_on_transition`, `ramp_on_merge`,
`ramp_off_diverge`, `ramp_off_transition`, `ramp_off_departure`.

---

## Academic grounding

| Decision | Reference |
|---|---|
| Lagrangian CAV control (30 s action frequency) | Vinitsky et al. (2018); Ko et al. (2020) |
| Regime embedded in observation | Li et al. (2017); Han et al. (2022) |
| Absolute action space (Markov-preserving) | Vinitsky et al. (2018); Sutton & Barto (2018) |
| TQC for continuous distributional RL | Kuznetsov et al. (2020) |
| Ramp VSL + on-ramp merge | Ko et al. (2020); Zhang et al. (2024) — MARVEL |

---

## Remote VM bootstrap

Reproducible 8-step sequence to take a clean PyTorch VM (Ubuntu, sudo, internet) from zero to a running experiment. Run **on the VM** after SSH-ing in.

```bash
# 1. Generate an SSH keypair on the VM
ssh-keygen -t ed25519 -C "phd-vm-$(hostname)" -f ~/.ssh/id_ed25519 -N ""

# 2. Print the public key
cat ~/.ssh/id_ed25519.pub

# 3. Paste it into GitHub as a *deploy key* on this repo
#    https://github.com/nyculescu/phd_speed_harmo_v5/settings/keys
#    (Add deploy key → leave "Allow write access" unchecked → Add key)

# 4. Verify SSH auth to GitHub
ssh -T git@github.com
#    Expected: "Hi nyculescu/phd_speed_harmo_v5! You've successfully authenticated..."

# 5. Clone the repo
git clone git@github.com:nyculescu/phd_speed_harmo_v5.git ~/phd_speed_harmo_v5

# 6. Enter it
cd ~/phd_speed_harmo_v5

# 7. Bootstrap (system pkgs, SUMO, venv, deps, smoke test) — ~5 min
bash deploy_remote.sh

# 8. Launch the assigned experiment inside tmux (N ∈ {1,2,3,4})
tmux new -s v5
./deploy_4vm.sh N      # 1=SAC Box(4) · 2=TQC Box(4) · 3=SAC Box(5) · 4=TQC Box(5)
#    Ctrl-B, D to detach.  tmux attach -t v5 to reattach.
```

**Result collection** must run *while* the VM is alive — `deploy_4vm.sh` triggers auto-shutdown ~2 min after the experiment exits. From your laptop, against each VM:

```bash
rsync -avz --partial user@vm_N:~/phd_speed_harmo_v5/training_runs/ ./training_runs_vm_N/
```
