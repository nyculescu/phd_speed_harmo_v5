"""Design-space heatmaps for a restart of the v5 DRL traffic-control project (2026-10-04).

Scores are expert judgements grounded in the five notes in this folder (notes_vehicles.md,
notes_networks.md, notes_rl_design.md, notes_history.md, notes_drl_families.md). They are
NOT measurements. Every row carries a one-line rationale that is printed into the report.

Outputs (this folder):
  fig1_factor_mechanism.png / .csv   63 design factors x 10 mechanisms, 0-3
  fig2_factor_coupling.png  / .csv   63 x 63 coupling = weighted Jaccard of the fig1 profiles
  fig3_family_fit.png       / .csv   13 requirements x 13 DRL (and non-RL) families, -2..+2
  fig4_status.png           / .csv   20 design aspects: v5 original / vsl_lab / restart plan, 0-3
  tables.md                          table view of every figure (for reading without colour)

Run: <venv>/bin/python build_heatmaps.py
"""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap, ListedColormap  # noqa: E402

OUT = Path(__file__).resolve().parent

# ---------------------------------------------------------------- palette (dataviz reference instance)
SURFACE, INK, INK2, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9"
ZERO = "#f0efec"                                     # neutral "none" cell (diverging midpoint grey)
SEQ = ["#86b6ef", "#3987e5", "#184f95"]              # ordinal blue steps 250 / 400 / 600 for 1 / 2 / 3
SEQ_CONT = ["#f0efec", "#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]
DIV = {-2: "#c43a39", -1: "#ee8f8d", 0: ZERO, 1: "#86b6ef", 2: "#256abf"}


def _lin(c):
    c = c / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def _rgb(h):
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], float)


def contrast(a, b):
    la, lb = (0.2126 * _lin(_rgb(x))[0] + 0.7152 * _lin(_rgb(x))[1] + 0.0722 * _lin(_rgb(x))[2] for x in (a, b))
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def ok_l(h):
    r, g, b = _lin(_rgb(h))
    l_ = np.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b)
    m_ = np.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b)
    s_ = np.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b)
    return 0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_


def check_ordinal(steps, name):
    """The dataviz validator's ordinal checks (node is not installed here): lightest step >= 2:1 vs
    the surface; adjacent OKLCH lightness gaps >= 0.06."""
    cr = contrast(steps[0], SURFACE)
    gaps = [abs(ok_l(steps[i]) - ok_l(steps[i + 1])) for i in range(len(steps) - 1)]
    ok = cr >= 2.0 and min(gaps) >= 0.06
    print(f"palette {name}: lightest contrast {cr:.2f}:1, min dL {min(gaps):.3f} -> {'PASS' if ok else 'FAIL'}")
    return ok


# ---------------------------------------------------------------- data: factors x mechanisms
MECH = ["Breakdown /\ncapacity\ndrop", "Stop-and-go\nwaves", "Actuator\nauthority", "Hidden\ncondition /\npartial obs.",
        "Delayed\neffect /\ncredit", "Reward-\nmetric\nalignment", "Sim\nartefacts", "Sample\ncost /\nstability",
        "Generalis-\nation /\nOOD", "Fair\ncomparison /\nstatistics"]
MECH_SHORT = ["M1 drop", "M2 waves", "M3 authority", "M4 hidden", "M5 delay", "M6 reward", "M7 artefacts",
              "M8 samples", "M9 OOD", "M10 fairness"]

# group, label, scores M1..M10, rationale (evidence in the notes)
F = [
    ("Vehicle (SUMO vType)", "length (truck 16.5 m)", [1, 0, 1, 2, 0, 0, 1, 0, 2, 0], "Trucks raise occupancy at the same flow, shifting occupancy-based set-points (v6 ramp T2 saw no consistent shift)."),
    ("Vehicle (SUMO vType)", "minGap", [2, 1, 1, 0, 0, 0, 1, 0, 1, 0], "Sets jam density and steady-state capacity; v5 CAVs used half minGap (~3,070 veh/h/lane)."),
    ("Vehicle (SUMO vType)", "maxSpeed / speedFactor", [1, 1, 3, 1, 0, 0, 0, 0, 2, 0], "A posted limit binds only if desired speed exceeds it; compliance groups were built on speedFactor."),
    ("Vehicle (SUMO vType)", "accel", [3, 2, 1, 1, 0, 0, 1, 0, 2, 0], "Queue-discharge rate drives the capacity drop; slow-accel variants removed metering benefit (v6 ramp calibration)."),
    ("Vehicle (SUMO vType)", "decel / emergencyDecel", [1, 2, 0, 0, 0, 0, 3, 0, 1, 0], "ACC/CACC at 0.5 s braked at 9 m/s2 tens of times per run: an artefact source."),
    ("Vehicle (SUMO vType)", "tau (headway)", [3, 2, 1, 2, 0, 0, 1, 0, 2, 0], "Capacity and wave growth; 'driver-population class' as a hidden condition was never tested; short tau caused teleports (v6 ramp)."),
    ("Vehicle (SUMO vType)", "sigma (imperfection)", [2, 3, 0, 1, 0, 0, 1, 1, 2, 0], "Krauss noise seeds stop-and-go waves; sigma 0 CAVs remove them."),
    ("Vehicle (SUMO vType)", "carFollowModel", [3, 3, 1, 1, 0, 0, 3, 1, 3, 0], "Krauss/IDM/EIDM/W99 all give realistic waves, none an artefact-free drop at merges; IDM strands ramp vehicles."),
    ("Vehicle (SUMO vType)", "lane-change params", [3, 1, 1, 1, 0, 0, 3, 0, 2, 0], "lcAssertive moves breakdown onsets to the network entry; merge behaviour decides the drop."),
    ("Vehicle (SUMO vType)", "step / actionStepLength", [1, 1, 0, 0, 0, 0, 3, 2, 1, 0], "0.5 s step gave CACC emergency-braking artefacts; smaller steps cost runtime."),
    ("Vehicle diversity", "class library (4 x 25 types)", [1, 1, 1, 2, 0, 0, 1, 1, 3, 1], "v5's 100-type library never reached the headline runs (100 % CAV); hard-coded, no config."),
    ("Vehicle diversity", "per-vehicle sampling", [1, 2, 1, 2, 0, 0, 1, 0, 3, 0], "Only speedFactor and CF noise vary per vehicle; lab vTypeDistribution + normc is the reusable pattern."),
    ("Vehicle diversity", "truck share", [2, 1, 1, 3, 0, 0, 1, 0, 2, 0], "Largest measured adaptivity headroom among heterogeneity families: G = 4.0 % (LD3 Round 4)."),
    ("Vehicle diversity", "compliance to posted limit", [0, 1, 3, 2, 0, 0, 0, 0, 2, 0], "Decides VSL authority; v5 model was binary/dead code; lab compliance family G = 0.8 %."),
    ("Vehicle diversity", "reckless / aggressive share", [1, 2, 0, 1, 0, 0, 1, 0, 1, 0], "Fixed 2 % in v5; inert at 100 % CAV; never a tested condition."),
    ("Vehicle diversity", "weather multipliers", [1, 1, 1, 2, 0, 0, 1, 0, 2, 1], "Trained with 30 % rain/fog, evaluated only clear: a train/eval mismatch."),
    ("CAV", "CAV / AV penetration", [1, 2, 3, 1, 0, 0, 1, 1, 3, 1], "Authority scales with share; policies trained at one share underperform at another (Vinitsky 2020); 10/25 % AVs never beat a tuned cap."),
    ("CAV", "CAV car-following (ACC/CACC)", [1, 2, 2, 0, 0, 0, 3, 0, 2, 0], "SUMO default CACC at 25 % added 46-93 % delay on its own; v5 CAVs were Krauss sigma 0."),
    ("CAV", "CAV actuation channel", [0, 2, 3, 0, 1, 1, 2, 1, 1, 1], "slowDown re-issued every 5 s (v5), setMaxSpeed caps, set-point staircases: channel decides authority and artefacts."),
    ("Network & demand", "bottleneck type", [3, 2, 3, 0, 1, 0, 2, 0, 1, 0], "Only zipper nodes (BN4 13.8 %, ZM3 3.3 %) gave an artefact-free capacity drop; acceleration-lane merges did not."),
    ("Network & demand", "lanes / drop ratio", [3, 1, 2, 0, 0, 0, 1, 0, 1, 0], "BN4 4->2->1 gave the only plant with large metering authority (+20 %)."),
    ("Network & demand", "merge / acc-lane geometry", [3, 1, 1, 0, 0, 0, 3, 0, 1, 0], "ramps_v1 drop -0.4 %; IDM stranded ramp vehicles; MRG3 edge lengths drifted."),
    ("Network & demand", "VSL sign stretch / placement", [1, 2, 3, 0, 2, 0, 0, 0, 1, 0], "Posted VSL did not bind on BN4 (4 lanes of storage); bound on LD3 (stops -55 to -63 %)."),
    ("Network & demand", "meter location / storage", [2, 0, 3, 1, 2, 1, 1, 0, 0, 0], "Metering authority needs storage and a binding bottleneck; queue must enter the reward."),
    ("Network & demand", "detector layout vs ground truth", [0, 1, 1, 3, 1, 1, 0, 0, 2, 2], "BN4 meter and DRL read ground-truth counts (S-VIN), not loops: optimistic information."),
    ("Network & demand", "demand level / band", [3, 3, 3, 1, 0, 0, 1, 0, 2, 1], "Control matters only in a narrow band (LD3: one of four levels); v5 never reached it."),
    ("Network & demand", "demand profile / generator", [2, 1, 1, 2, 0, 1, 1, 0, 2, 3], "v5 Bernoulli cap (<= 3,600 veh/h, bound 77 % of seconds), ramp burst at t = 100 s, train/eval mismatch; lab used fixed trapezoids."),
    ("Network & demand", "perturbations (block / surge)", [1, 1, 2, 3, 2, 0, 2, 1, 3, 1], "R6 headroom came from the hidden perturbation type (G 15.4 %); OOD severities broke it (+16 %); long blocks teleport."),
    ("Network & demand", "insertion & teleport settings", [1, 0, 0, 0, 0, 3, 3, 0, 0, 2], "v5: insertionChecks none, teleports disabled, insertion backlog outside the KPI."),
    ("Observation", "aggregated detectors (E1/E2)", [0, 1, 0, 3, 1, 0, 0, 1, 2, 1], "Realistic, partial; the information level a fair baseline also gets."),
    ("Observation", "vehicle-level ground truth", [0, 0, 0, 2, 0, 0, 0, 1, 1, 3], "Gives DRL more than the baseline sees unless both get it (signal-control lesson)."),
    ("Observation", "memory (stack / LSTM)", [0, 1, 0, 3, 3, 0, 0, 2, 2, 0], "Only the LSTM policy passed (R6); frame-stack and plain PPO failed (1 pass in 8 looks)."),
    ("Observation", "privileged context (critic/oracle)", [0, 0, 0, 3, 1, 0, 0, 2, 2, 2], "Asymmetric critic / context head: diagnoses whether history carries the hidden condition."),
    ("Action", "posted VSL (discrete levels)", [1, 3, 2, 1, 2, 0, 0, 1, 1, 0], "LD3 Discrete(11) PPO lost ~10 % to a constant 0.75 limit."),
    ("Action", "per-lane continuous CAV speeds", [1, 2, 2, 0, 2, 2, 1, 3, 2, 1], "v5 Box(4) TQC: slowed everyone, TTS +23 %; large continuous space, hard credit."),
    ("Action", "controller-setting menu", [3, 0, 3, 2, 2, 0, 0, 1, 1, 1], "R6 Discrete(4) over a validated meter: the only win."),
    ("Action", "residual on tuned controller", [1, 1, 2, 1, 1, 0, 0, 2, 1, 2], "LD3 residual degraded during training; reviewers may credit the controller."),
    ("Action", "decision interval", [0, 2, 1, 1, 3, 0, 1, 2, 0, 0], "30-60 s steps versus 30-60 s wave delays sets the credit-assignment horizon."),
    ("Reward / metric", "door-to-door delay incl. queue", [2, 1, 1, 0, 2, 3, 1, 0, 0, 3], "The lab's R-TTS including origin queue; screened against a constant policy."),
    ("Reward / metric", "stops weight (J = delay + 40 s/stop)", [0, 3, 1, 0, 1, 3, 0, 0, 0, 2], "Whether harmonisation 'wins' at 3,900 veh/h depends on this weight (+2 % delay, -63 % stops)."),
    ("Reward / metric", "speed-variance proxies", [0, 2, 0, 0, 0, 3, 0, 0, 0, 2], "4 of 5 v5 reward terms; gamed: +221 reward while TTS +23 %."),
    ("Reward / metric", "safety proxies (TTC, hard braking)", [0, 2, 0, 0, 0, 2, 2, 0, 0, 1], "Polled 1/30 in v5; secondary metric only."),
    ("Reward / metric", "metric sampling resolution", [0, 0, 0, 0, 0, 3, 1, 0, 0, 3], "v5 polled arrivals and hard brakes once per 30 s (~1/30 counted)."),
    ("DRL family", "PPO (memoryless)", [0, 0, 0, 1, 2, 0, 0, 2, 1, 1], "Failed screening on BN4 and LD3."),
    ("DRL family", "RecurrentPPO (LSTM)", [0, 0, 0, 3, 2, 0, 0, 2, 2, 1], "R6 win (in-distribution); no OOD transfer; LR decay flag ignored; no convergence."),
    ("DRL family", "SAC / TD3", [0, 0, 0, 1, 2, 0, 0, 2, 1, 1], "v5 SAC proxy runs only; TD3 matched ALINEA at 40 % AVs (Vinitsky 2020)."),
    ("DRL family", "TQC / QR-DQN (distributional)", [1, 0, 0, 1, 1, 0, 0, 2, 1, 1], "Chosen for assumed bimodal returns never reached; no traffic evidence; 20.6 k gradient steps per run."),
    ("DRL family", "DQN family", [0, 0, 0, 1, 2, 0, 0, 1, 1, 1], "Reliable in RESCO signal control (vs untuned baselines); untried in the lab."),
    ("DRL family", "MaskablePPO / hybrid menu", [1, 0, 3, 1, 1, 0, 0, 1, 1, 2], "Baseline inside the action set; masks enforce queue limits; untried."),
    ("DRL family", "MARL (IPPO / MAPPO)", [0, 1, 1, 1, 2, 0, 0, 3, 1, 1], "Only for multi-ramp corridors; unstable in RESCO."),
    ("DRL family", "model-based (Dreamer / MBPO)", [0, 0, 0, 1, 2, 0, 0, 2, 2, 1], "No clear data-efficiency gain in the one traffic paper found."),
    ("DRL family", "non-RL search (BO / CMA-ES / ARS)", [0, 0, 1, 1, 1, 0, 0, 1, 1, 3], "Tunes baselines with equal budget; ARS on the same features falsifies 'deep' learning."),
    ("Training", "budget (updates, env steps)", [0, 0, 0, 0, 2, 0, 0, 3, 1, 2], "v5: 20.6 k gradient steps, flat curves; R6: 2,000 updates."),
    ("Training", "domain randomisation", [0, 0, 0, 3, 0, 0, 0, 2, 3, 1], "Penetration DR gave one robust TD3 controller with 'small loss' (Vinitsky 2020)."),
    ("Training", "learner seeds (3-5)", [0, 0, 0, 0, 0, 0, 0, 2, 1, 3], "Single-seed screening passes were false positives (lab)."),
    ("Training", "validation-only checkpointing", [0, 0, 0, 0, 0, 0, 0, 1, 2, 3], "v5 picked best_model on the training pool; R6 final policy 6.7-10.7 % worse than best checkpoint."),
    ("Training", "train / eval scenario split", [1, 0, 0, 1, 0, 0, 0, 0, 3, 3], "v5 trained on a 200-scenario pool, evaluated on a capped generator."),
    ("Evaluation", "tuned baselines (const, ALINEA, MTFC, MPC-F)", [1, 1, 3, 1, 0, 1, 0, 0, 0, 3], "A constant limit or tuned meter beat every direct DRL design."),
    ("Evaluation", "static headroom gate (G / H)", [2, 1, 2, 3, 0, 0, 0, 0, 1, 3], "Killed LD3, CORR2, BN4-M2 and the v6 cards before DRL."),
    ("Evaluation", "within-run timing reference", [1, 2, 1, 3, 3, 0, 0, 0, 0, 2], "Never built; the one open question on LD3."),
    ("Evaluation", "paired seeds, CIs, pre-registration", [0, 0, 0, 0, 0, 1, 0, 0, 0, 3], "R6's CI vs MPC-F only just excluded 0 (-0.8 s)."),
    ("Evaluation", "OOD context tests", [0, 0, 0, 2, 0, 0, 0, 0, 3, 2], "Lead 1 showed R6 does not transfer (+16 % on surges)."),
    ("Evaluation", "plant realism gate", [3, 3, 1, 0, 0, 0, 3, 0, 1, 1], "Waves pass everywhere; capacity drop only on zipper plants; BN4 never gated."),
]

# ---------------------------------------------------------------- data: family fit
FAM = ["PPO", "Recurrent\nPPO", "Context-\nconditioned\nRecPPO", "SAC /\nTD3", "TQC /\nQR-DQN\n(distrib.)", "DQN",
       "Maskable\nPPO menu", "Residual\nPPO", "RL-in-\nMPC", "MARL", "Model-\nbased", "Offline\nRL", "BO / CMA /\nARS\n(non-RL)"]
REQ = [
    ("Infers hidden context from history", [-1, 2, 2, -1, -1, -1, 0, -1, 0, 0, 1, -1, 0]),
    ("Handles 30-60 s delayed effects", [0, 1, 1, 0, 0, 0, 1, 0, 2, -1, 1, 0, 1]),
    ("Discrete menu of controller settings", [1, 2, 2, -2, 1, 1, 2, -1, 0, 0, 0, 0, 1]),
    ("Continuous per-lane speed actions", [1, 1, 1, 2, 1, -2, -2, 1, 1, 1, 1, 0, 1]),
    ("Sample efficiency (SUMO cost)", [0, -1, -1, 1, 1, 1, 1, 1, 1, -2, 0, -1, 0]),
    ("Generalises across vehicle diversity", [0, 0, 1, 0, 0, 0, 1, 1, 1, 0, 0, -1, 0]),
    ("Safety / constraint handling", [-1, -1, -1, -1, 0, -1, 2, 1, 2, -1, -1, 0, 0]),
    ("Never worse than tuned baseline", [-1, -1, -1, -1, -1, -1, 1, 2, 2, -1, -1, 0, 1]),
    ("Gain attributable to DRL (thesis)", [2, 2, 1, 2, 2, 2, 0, -1, -1, 1, 1, 1, -2]),
    ("Tooling (SB3 / contrib)", [2, 2, 0, 2, 1, 2, 2, 1, -1, -2, -2, -1, 2]),
    ("Evidence vs tuned baselines (traffic)", [0, 1, 0, -1, -1, 0, 0, -1, 0, -1, -1, -1, 1]),
    ("Risk-sensitive / tail objectives", [0, 0, 0, 0, 2, 0, 0, 0, 1, 0, 0, 1, 1]),
    ("Multi-ramp / multi-gantry coordination", [1, 1, 1, 1, 1, 0, 0, 1, 2, 2, 0, 0, 0]),
]

# weights for the restart's priorities (stated before ranking; judgement): hidden context and OOD
# generalisation are what failed or is untested in R6; continuous per-lane actions, tail objectives and
# multi-ramp coordination are not part of the restart design, so they get weight 0.
REQ_W = [3, 2, 2, 0, 1, 3, 1, 1, 2, 1, 2, 0, 0]

# ---------------------------------------------------------------- data: status v5 -> lab -> restart
STAGES = ["v5 original", "vsl_lab", "restart (plan)"]
STATUS = [
    ("Diversity reaches SUMO", [0, 2, 3], "100 % CAV headline; compliance dead code -> lab vTypeDistribution + normc -> sampled populations with held-out ranges"),
    ("Diversity changes the best action", [0, 2, 2], "untested -> compliance G 0.8 %, trucks G 4.0 % -> add driver-population class; context-prediction diagnostic"),
    ("Driver-model realism", [0, 2, 3], "no gate -> waves pass, drop only on zipper plants -> gate every plant incl. BN4 first"),
    ("CAV modelling", [1, 1, 2], "Krauss sigma 0 + slowDown -> default CACC harmful -> CAVs only after an authority check, 0.1 s step"),
    ("Controllable bottleneck", [0, 3, 3], "no breakdown -> BN4 13.8 % drop -> zipper family (BN4 / ZM3) only"),
    ("Demand generation", [0, 2, 3], "Bernoulli cap, ramp burst, mismatch -> Poisson trapezoids -> stochastic shapes, uncapped"),
    ("Hidden events / perturbations", [1, 3, 3], "ramp_spike no-op, overrides -> R6 mix -> mix + held-out severities"),
    ("Insertion / teleport health", [0, 3, 3], "checks off, teleports off -> health-checked runner -> keep"),
    ("Observation realism", [2, 1, 3], "E1 30 s -> BN4 ground-truth counts -> loops + memory; privileged info only in the critic"),
    ("Action design", [0, 3, 3], "per-lane continuous CAV speeds -> menu over validated meter -> menu (+ residual variant)"),
    ("Reward = real objective", [0, 3, 3], "speed-variance proxies -> R-TTS incl. queue -> keep; screen vs constant policy"),
    ("Metric correctness", [0, 3, 3], "1/30 sampling, backlog ignored -> fixed -> keep"),
    ("Algorithm fit", [1, 2, 3], "TQC unjustified -> RecurrentPPO -> context-conditioned RecPPO; MaskablePPO hybrid"),
    ("Training budget & convergence", [0, 2, 3], "20.6 k grad steps -> 2,000 updates, no convergence, LR decay ignored -> convergence rule enforced"),
    ("Checkpoint selection", [0, 3, 3], "training pool -> validation only -> keep"),
    ("Tuned baselines incl. MPC", [0, 3, 3], "NC yardstick -> const / MTFC / evsched / MPC-F -> + BO-tuned with equal budget"),
    ("Headroom gating", [0, 3, 3], "none -> static G / H -> + within-run timing reference"),
    ("Statistics & pre-registration", [0, 3, 3], "none -> paired CIs, ledger -> keep"),
    ("OOD / generalisation test", [0, 2, 3], "none -> Lead 1 (exploratory) -> pre-registered held-out contexts"),
    ("Non-RL learned comparator", [0, 1, 3], "none -> MPC-F learned model -> + ARS / BO on the same features"),
]


# ---------------------------------------------------------------- rendering helpers
def _style(ax):
    ax.set_facecolor(SURFACE)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0, colors=INK2)


def groups_of(rows):
    out, start = [], 0
    for i in range(1, len(rows) + 1):
        if i == len(rows) or rows[i][0] != rows[start][0]:
            out.append((rows[start][0], start, i))
            start = i
    return out


def fig1():
    M = np.array([r[2] for r in F])
    cmap = ListedColormap([ZERO] + SEQ)
    fig, ax = plt.subplots(figsize=(11.5, 17.5), facecolor=SURFACE)
    _style(ax)
    ax.imshow(M, cmap=cmap, vmin=-0.5, vmax=3.5, aspect="auto")
    ax.set_xticks(range(len(MECH)), MECH, fontsize=8, color=INK)
    ax.xaxis.tick_top()
    ax.set_yticks(range(len(F)), [r[1] for r in F], fontsize=8, color=INK)
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            if M[i, j]:
                ax.text(j, i, str(M[i, j]), ha="center", va="center", fontsize=7,
                        color="#ffffff" if M[i, j] >= 2 else INK)
    for x in np.arange(-0.5, M.shape[1], 1):
        ax.axvline(x, color=SURFACE, lw=2)
    for y in np.arange(-0.5, M.shape[0], 1):
        ax.axhline(y, color=SURFACE, lw=1.2)
    for g, a, b in groups_of(F):
        ax.axhline(a - 0.5, color=INK2, lw=0.8)
        ax.text(M.shape[1] - 0.3, (a + b - 1) / 2, g, rotation=-90, va="center", ha="left", fontsize=8, color=INK2)
    ax.set_title("How each design choice couples to the mechanisms that decide whether DRL can win\n"
                 "0 none · 1 weak · 2 moderate · 3 strong (expert judgement from the v5 notes; not measured)",
                 fontsize=10, color=INK, pad=60, loc="left")
    fig.tight_layout()
    fig.savefig(OUT / "fig1_factor_mechanism.png", dpi=150, facecolor=SURFACE)
    plt.close(fig)
    with open(OUT / "fig1_factor_mechanism.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["group", "factor"] + MECH_SHORT + ["rationale"])
        for g, lab, s, why in F:
            w.writerow([g, lab] + s + [why])
    return M


def fig2(M):
    n = len(F)
    C = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            mx = np.maximum(M[i], M[j]).sum()
            C[i, j] = np.minimum(M[i], M[j]).sum() / mx if mx else 0.0
    C_plot = C.copy()
    np.fill_diagonal(C_plot, np.nan)
    cmap = LinearSegmentedColormap.from_list("seq", SEQ_CONT)
    cmap.set_bad(SURFACE)
    fig, ax = plt.subplots(figsize=(17, 16), facecolor=SURFACE)
    _style(ax)
    im = ax.imshow(C_plot, cmap=cmap, vmin=0, vmax=1, aspect="equal")
    labels = [r[1] for r in F]
    ax.set_xticks(range(n), labels, fontsize=6.5, rotation=90, color=INK)
    ax.set_yticks(range(n), labels, fontsize=6.5, color=INK)
    for g, a, b in groups_of(F):
        ax.axhline(a - 0.5, color=INK2, lw=0.8)
        ax.axvline(a - 0.5, color=INK2, lw=0.8)
        ax.text(-0.8 - 9.5, (a + b - 1) / 2, g, va="center", ha="right", fontsize=8, color=INK2)
    cb = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.01)
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=8, colors=INK2, length=0)
    cb.set_label("coupling (weighted overlap of mechanism profiles, 0-1)", color=INK2, fontsize=8)
    ax.set_title("Everything against everything: which design choices interact through the same mechanisms\n"
                 "coupling = sum(min) / sum(max) of the two rows in figure 1; dark = must be designed together",
                 fontsize=11, color=INK, loc="left")
    fig.tight_layout()
    fig.subplots_adjust(left=0.22)
    fig.savefig(OUT / "fig2_factor_coupling.png", dpi=130, facecolor=SURFACE)
    plt.close(fig)
    with open(OUT / "fig2_factor_coupling.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["factor"] + labels)
        for i in range(n):
            w.writerow([labels[i]] + [f"{x:.2f}" for x in C[i]])
    return C


def fig3():
    S = np.array([r[1] for r in REQ])
    tot = S.sum(axis=0)
    wtot = (S * np.array(REQ_W)[:, None]).sum(axis=0)
    cmap = ListedColormap([DIV[k] for k in (-2, -1, 0, 1, 2)])
    fig, ax = plt.subplots(figsize=(13.5, 8.8), facecolor=SURFACE)
    _style(ax)
    ax.imshow(S, cmap=cmap, vmin=-2.5, vmax=2.5, aspect="auto")
    ax.set_xticks(range(len(FAM)), FAM, fontsize=8, color=INK)
    ax.xaxis.tick_top()
    ax.set_yticks(range(len(REQ) + 2), [f"{r[0]}  (w{w})" for r, w in zip(REQ, REQ_W)] + ["Sum (unweighted)", "Weighted sum (restart priorities)"], fontsize=8.5, color=INK)
    for i in range(S.shape[0]):
        for j in range(S.shape[1]):
            v = S[i, j]
            ax.text(j, i, f"{v:+d}" if v else "0", ha="center", va="center", fontsize=8,
                    color="#ffffff" if abs(v) == 2 else INK)
    for j, (t, wt) in enumerate(zip(tot, wtot)):
        ax.text(j, len(REQ), f"{t:+d}", ha="center", va="center", fontsize=9, color=INK2)
        ax.text(j, len(REQ) + 1, f"{wt:+d}", ha="center", va="center", fontsize=9.5, fontweight="bold", color=INK)
    ax.set_ylim(len(REQ) + 1.5, -0.5)
    for x in np.arange(-0.5, S.shape[1], 1):
        ax.axvline(x, color=SURFACE, lw=2)
    for y in np.arange(-0.5, S.shape[0], 1):
        ax.axhline(y, color=SURFACE, lw=2)
    ax.axhline(len(REQ) - 0.5, color=INK2, lw=0.8)
    ax.set_title("Which DRL family fits this problem class (-2 poor fit ... +2 strong fit)\n"
                 "red = works against the requirement · grey = neutral · blue = supports it; judgement from notes_drl_families.md",
                 fontsize=10, color=INK, loc="left", pad=55)
    fig.tight_layout()
    fig.savefig(OUT / "fig3_family_fit.png", dpi=150, facecolor=SURFACE)
    plt.close(fig)
    with open(OUT / "fig3_family_fit.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["requirement"] + [x.replace("\n", " ") for x in FAM])
        for r, s in REQ:
            w.writerow([r] + s)
        w.writerow(["SUM"] + list(tot))
        w.writerow(["WEIGHTED SUM (weights " + " ".join(map(str, REQ_W)) + ")"] + list(wtot))
    return S, tot, wtot


def fig4():
    S = np.array([r[1] for r in STATUS])
    cmap = ListedColormap([ZERO] + SEQ)
    fig, ax = plt.subplots(figsize=(8.5, 8.8), facecolor=SURFACE)
    _style(ax)
    ax.imshow(S, cmap=cmap, vmin=-0.5, vmax=3.5, aspect="auto")
    ax.set_xticks(range(3), STAGES, fontsize=9, color=INK)
    ax.xaxis.tick_top()
    ax.set_yticks(range(len(STATUS)), [r[0] for r in STATUS], fontsize=8.5, color=INK)
    words = {0: "absent / broken", 1: "flawed", 2: "adequate", 3: "strong"}
    for i in range(S.shape[0]):
        for j in range(3):
            v = S[i, j]
            ax.text(j, i, f"{v} {words[v]}", ha="center", va="center", fontsize=7.5,
                    color="#ffffff" if v >= 2 else INK, style="italic" if j == 2 else "normal")
    for x in np.arange(-0.5, 3, 1):
        ax.axvline(x, color=SURFACE, lw=3)
    for y in np.arange(-0.5, S.shape[0], 1):
        ax.axhline(y, color=SURFACE, lw=2)
    ax.axvline(1.5, color=INK2, lw=0.8, ls=(0, (3, 2)))
    ax.set_title("What v5 got wrong, what the lab fixed, and what a restart must add\n"
                 "the restart column is a plan (italic), not a result", fontsize=10, color=INK, loc="left", pad=28)
    fig.tight_layout()
    fig.savefig(OUT / "fig4_status.png", dpi=150, facecolor=SURFACE)
    plt.close(fig)
    with open(OUT / "fig4_status.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["aspect"] + STAGES + ["what changes"])
        for a, s, why in STATUS:
            w.writerow([a] + s + [why])


def tables(M, C, S, tot, wtot):
    lines = ["# Table view of the heatmaps", "",
             "Generated by `build_heatmaps.py`. Scores are judgements from the notes in this folder, not measurements.", ""]
    lines += ["## Figure 1: factor x mechanism (0-3)", "",
              "| Group | Factor | " + " | ".join(MECH_SHORT) + " | Rationale |",
              "|---|---|" + "---|" * len(MECH_SHORT) + "---|"]
    for g, lab, s, why in F:
        lines.append(f"| {g} | {lab} | " + " | ".join(str(x) or "" for x in s) + f" | {why} |")
    lines += ["", "## Figure 2: strongest cross-group couplings (top 40)", "",
              "| Factor A | Factor B | Coupling |", "|---|---|---|"]
    n = len(F)
    pairs = [(C[i, j], i, j) for i in range(n) for j in range(i + 1, n) if F[i][0] != F[j][0]]
    for c, i, j in sorted(pairs, reverse=True)[:40]:
        lines.append(f"| {F[i][1]} ({F[i][0]}) | {F[j][1]} ({F[j][0]}) | {c:.2f} |")
    lines += ["", "## Figure 3: DRL family fit (-2..+2)", "",
              "| Requirement | " + " | ".join(x.replace("\n", " ") for x in FAM) + " |",
              "|---|" + "---|" * len(FAM)]
    for (r, s), w in zip(REQ, REQ_W):
        lines.append(f"| {r} (w{w}) | " + " | ".join(f"{x:+d}" if x else "0" for x in s) + " |")
    lines.append("| Sum (unweighted) | " + " | ".join(f"{x:+d}" for x in tot) + " |")
    lines.append("| **Weighted sum** | " + " | ".join(f"**{x:+d}**" for x in wtot) + " |")
    lines += ["", "## Figure 4: status (0 absent/broken, 1 flawed, 2 adequate, 3 strong)", "",
              "| Aspect | " + " | ".join(STAGES) + " | What changes |", "|---|---|---|---|---|"]
    for a, s, why in STATUS:
        lines.append(f"| {a} | " + " | ".join(str(x) for x in s) + f" | {why} |")
    (OUT / "tables.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    assert len(F) == 63 and all(len(r[2]) == 10 for r in F)
    assert all(len(r[1]) == len(FAM) for r in REQ) and len(REQ_W) == len(REQ)
    check_ordinal(SEQ, "sequential blue (1-3)")
    check_ordinal(["#ee8f8d", "#c43a39"], "diverging red arm")
    check_ordinal(["#86b6ef", "#256abf"], "diverging blue arm")
    M = fig1()
    C = fig2(M)
    S, tot, wtot = fig3()
    fig4()
    tables(M, C, S, tot, wtot)
    print("family sums:", dict(zip([x.replace("\n", " ") for x in FAM], tot.tolist())))
    print("weighted sums:", dict(zip([x.replace("\n", " ") for x in FAM], wtot.tolist())))
    n = len(F)
    pairs = sorted(((C[i, j], F[i][1], F[j][1]) for i in range(n) for j in range(i + 1, n) if F[i][0] != F[j][0]), reverse=True)
    print("top cross-group couplings:")
    for c, a, b in pairs[:15]:
        print(f"  {c:.2f}  {a}  <->  {b}")
    mech_load = M.sum(axis=0)
    print("mechanism load (column sums):", dict(zip(MECH_SHORT, mech_load.tolist())))
