"""Writes trainlog.py's series as TensorBoard scalars, one run per learner, then reads every value back and compares it.
Runs in the separate TensorBoard environment (V393). usage: to_tensorboard.py series.json logdir start_epoch"""
import json
import sys
from pathlib import Path

from tensorboard.backend.event_processing.event_accumulator import EventAccumulator
import numpy as np
from tensorboard.compat.proto.event_pb2 import Event
from tensorboard.compat.proto.summary_pb2 import Summary
from tensorboard.plugins.scalar import metadata as scalar_metadata
from tensorboard.summary.writer.event_file_writer import EventFileWriter
from tensorboard.util import tensor_util

MIX = "Training mode: actions are drawn at random from the policy, 3 episodes per update, one at each demand level, 2 of 3 episodes with a random slowdown. Not an evaluation result."
DESC = {
    "ppo/reward_per_decision": "Mean, over all decisions of this update, of each decision's mean reward per second. " + MIX + " Not comparable across plants, reward versions or input designs.",
    "ppo/entropy": "Policy entropy in nats, mean over this update's minibatch steps. 1.386 = 4 equal choices.",
    "ppo/value_loss_scaled": "Critic loss as logged, in units of the critic's own scale, which is fixed at update 0 and differs by learner. Do not compare learners on this tag.",
    "ppo/value_loss_reward_units": "Critic loss × scale². Comparable across learners.",
    "ppo/explained_variance": "1 - Var(target - V) / Var(target) on this update's batch, before learning from it. The target is the lambda-return, which contains the critic's own values, so this overstates how well the critic predicts outcomes.",
    "ppo/approx_kl": "Mean of (old - new log-probability) of the actions taken, over this update's minibatch steps. A noisy estimate; it can be slightly negative.",
    "ppo/clip_fraction": "Share of samples with |ratio - 1| > 0.2, mean over this update's minibatch steps.",
    "ppo/decisions": "Decisions in this update's batch.",
    "ppo/seconds_per_update": "Wall seconds since the previous update. Depends on machine load.",
}
TDESC = {
    "vehicles_into_road4": "Vehicles that entered road 4 in this episode, at this demand level. " + MIX,
    "vehicle_seconds_in_system": "Sum over 1,500 s of vehicles on the network or waiting to enter. Lower is better. " + MIX,
    "mean_speed_kmh": "Mean over 1,500 s of the network's mean speed, km/h. " + MIX,
    "ttc_below_3s_merge1_lanes": "Vehicle-seconds at TTC below 3 s, merge 1 lanes only, read once a second. Merge 2 is not covered: training does not measure network counts. " + MIX,
    "braking_3ms2_merge1_lanes": "Vehicle-seconds braking at 3 m/s² or more, merge 1 lanes only, read once a second, so short braking can be missed (V367). " + MIX,
    "collisions": "New collisions in this episode.",
    "level_moves": "Level changes made by all ALKS in this episode.",
    "level_reversals": "Level changes that reversed the previous one.",
    "slowdown_limit_kmh": "This episode's random slowdown, km/h; 0 = no slowdown. Recomputed from the seed with the training code.",
}


def tags(L: dict) -> dict:
    t = {f"ppo/{k}": v for k, v in L["ppo"].items()}
    t.update({f"levels_{k.split('/')[0]}/share_open_gate_{k.split('/')[1]}": v for k, v in L["levels"].items()})
    for q, T in L["traffic"].items():
        t.update({f"traffic_{q}vph/{k}": v for k, v in T.items()})
    return t


def describe(tag: str) -> str:
    if tag in DESC:
        return DESC[tag]
    if tag.startswith("levels_"):
        return "Share of open-gate ALKS-seconds at this level, in this zone, over the update's 3 episodes. " + MIX
    return TDESC[tag.split("/")[1]]


if __name__ == "__main__":
    src, logdir, t0 = Path(sys.argv[1]), Path(sys.argv[2]), float(sys.argv[3])
    S = json.load(open(src))
    want = {}
    for name, L in S["learners"].items():
        run = logdir / name
        if run.exists() and any(run.iterdir()):
            sys.exit(f"{run} is not empty: refusing to mix runs")
        run.mkdir(parents=True)
        w = EventFileWriter(str(run))
        wall = 0.0
        sec = L["ppo"]["seconds_per_update"]
        for tag, ys in tags(L).items():
            want[(name, tag)] = {u: y for u, y in enumerate(ys) if y is not None}
            wall, first = 0.0, True
            for u, y in enumerate(ys):
                wall += sec[u] or 0.0
                if y is None:
                    continue
                # float32: TensorBoard's default loader drops float64 scalars without a warning
                v = Summary.Value(tag=tag, tensor=tensor_util.make_tensor_proto(np.float32(y)))
                if first:     # TensorBoard reads a tag's description from its first event
                    v.metadata.CopyFrom(scalar_metadata.create_summary_metadata(display_name=tag, description=describe(tag)))
                    first = False
                w.add_event(Event(wall_time=t0 + wall, step=u, summary=Summary(value=[v])))
        w.close()
    # Read back every value: the files must hold exactly the series, step by step.
    bad, n = [], 0
    for name in S["learners"]:
        acc = EventAccumulator(str(logdir / name), size_guidance={"tensors": 0})
        acc.Reload()
        got_tags = set(acc.Tags()["tensors"])
        mine = {t for (nm, t) in want if nm == name}
        if got_tags != mine:
            bad.append(f"{name}: tags differ: {sorted(got_tags ^ mine)[:5]}")
        for t in mine & got_tags:
            got = {e.step: float(tensor_util.make_ndarray(e.tensor_proto)) for e in acc.Tensors(t)}
            exp = want[(name, t)]
            if set(got) != set(exp):
                bad.append(f"{name} {t}: steps differ")
                continue
            for u, y in exp.items():
                n += 1
                if abs(got[u] - y) > 1e-6 * max(1.0, abs(y)):
                    bad.append(f"{name} {t} step {u}: wrote {y}, read {got[u]}")
    print("values read back:", n, "mismatches:", len(bad), bad[:5], flush=True)
    sys.exit(1 if bad else 0)
