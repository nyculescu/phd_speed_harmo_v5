"""V306: dumps the plant as SUMO sees it, every module constant and the policy structures. usage: plant_dump.py baseline_dir out_dir [plant.json]"""
import json
import shutil
import sys
from pathlib import Path

import libsumo as ls
import torch

from v5b.fleet import b_env as be, b_train as bt, c_train as ct

X, out = Path(sys.argv[1]), Path(sys.argv[2])
PLANT = json.load(open(sys.argv[3])) if len(sys.argv) > 3 else None
out.mkdir(parents=True, exist_ok=True)
seed = 7_419_650
cap = []
start0 = ls.start
ls.start = lambda a, *p, **k: (cap.append(list(a)), start0(a, *p, **k))[1]
KW = {"zone": {"zones": True, "decision": 10.0, "alks_asl": 0.5, "w_change": 0.1, "ref_delay": True},
      "cav": {"cav": True, "decision": 5.0, "alks_asl": 0.5, "ref_delay": True}}
VT = ("Length", "MaxSpeed", "SpeedFactor", "SpeedDeviation", "Accel", "Decel", "EmergencyDecel", "ApparentDecel", "Imperfection", "Tau", "MinGap", "MinGapLat",
      "MaxSpeedLat", "LateralAlignment", "VehicleClass", "EmissionClass", "ShapeClass", "Width", "Height", "ActionStepLength")
res = {}
for name, kw in KW.items():
    env = be.make(share=0.5, levels=(5300.0,), run_dir=str(out / "rd"), seeds=[seed], report_net=True, **({"plant": PLANT} if PLANT else {}), **kw)
    env.reset()
    plain = (int, float, str, bool, type(None))
    r = {"sumo_args": cap[-1], "env": {k: v for k, v in vars(env).items() if isinstance(v, plain) or (isinstance(v, (tuple, list)) and len(v) < 40 and all(isinstance(x, plain) for x in v))}}
    r["env"]["ref"] = {str(k): list(v) for k, v in env.ref.items()}
    types = {}
    for t in ls.vehicletype.getIDList():
        types[t] = {}
        for g in VT:
            try:
                types[t][g] = getattr(ls.vehicletype, "get" + g)(t)
            except Exception as e:
                types[t][g] = f"unavailable: {e}"
    r["vtypes"] = types
    r["edges"] = {e: {"lanes": {f"{e}_{i}": {"length": ls.lane.getLength(f"{e}_{i}"), "maxspeed": ls.lane.getMaxSpeed(f"{e}_{i}"), "width": ls.lane.getWidth(f"{e}_{i}"),
                                              "allowed": list(ls.lane.getAllowed(f"{e}_{i}")), "links": [str(x[0]) for x in ls.lane.getLinks(f"{e}_{i}")]}
                                 for i in range(ls.edge.getLaneNumber(e))}} for e in ls.edge.getIDList() if not e.startswith(":")}
    r["traffic_lights"] = {t: ls.trafficlight.getRedYellowGreenState(t) for t in ls.trafficlight.getIDList()}
    r["cfg"] = {k: repr(v)[:800] for k, v in (vars(env.cfg) if hasattr(env.cfg, "__dict__") else {"repr": env.cfg}).items()}
    shutil.copy(env.rou, out / f"example_routes_{name}_{seed}_5300.rou.xml")
    d = be.fl.build_net(env.cfg)
    for f in Path(d).iterdir():
        if f.is_file() and f.stat().st_size < 4_000_000:
            shutil.copy(f, out / f"plant_{f.name}")
    res[name] = r
    env.close()
(out / "plant.json").write_text(json.dumps(res, indent=1, default=repr))
constants = {}
for m in (be, ct, bt, be.fl, be.bm):
    constants[m.__name__] = {k: repr(v)[:1500] for k, v in vars(m).items() if k.isupper()}
(out / "constants.json").write_text(json.dumps(constants, indent=1))
pol = {}
for f in sorted((X / "b_train/night").rglob("*_final.pt")):
    s = torch.load(f, map_location="cpu", weights_only=False)
    sd = s.get("net", s) if isinstance(s, dict) else s
    pol[str(f.relative_to(X))] = {"top_keys": list(s) if isinstance(s, dict) else [], "extra": {k: repr(v)[:200] for k, v in s.items() if k != "net" and not hasattr(v, "shape")} if isinstance(s, dict) else {},
                                  "shapes": {k: list(v.shape) for k, v in sd.items() if hasattr(v, "shape")}, "params": int(sum(v.numel() for v in sd.values() if hasattr(v, "numel")))}
from stable_baselines3 import PPO
for f in sorted((X / "b_train/night/c8/trainB").glob("*_final.zip")) + sorted((X / "b_train/night/run5b").glob("*_final.zip")):
    m = PPO.load(f, device="cpu")
    pol[str(f.relative_to(X))] = {"policy": repr(m.policy)[:1500], "params": int(sum(p.numel() for p in m.policy.parameters())), "gamma": m.gamma, "gae_lambda": m.gae_lambda, "n_steps": m.n_steps,
                                  "batch_size": m.batch_size, "n_epochs": m.n_epochs, "ent_coef": m.ent_coef, "vf_coef": m.vf_coef, "clip": repr(m.clip_range), "lr": repr(m.learning_rate)[:60], "timesteps": m.num_timesteps}
(out / "policies.json").write_text(json.dumps(pol, indent=1))
print("ok", len(pol), cap[-1][:3])
