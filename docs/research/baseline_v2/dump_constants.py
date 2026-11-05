"""Plant files and module constants as frozen for baseline v2. usage: dump_constants.py out_dir"""
import json
import shutil
import sys
from pathlib import Path

from v5b.fleet import b_env as be, b_merge as bm, c_train as ct, corridor as co, fleet as fl, perturb as pt

out = Path(sys.argv[1])
cfg = bm.setup(0.5, 0.1)
fl.tune(json.load(open(out / "plant_p0d.json")))
c = {}
for m in (be, ct, fl, bm, co, pt):
    c[m.__name__] = {k: repr(v) for k, v in vars(m).items() if k.isupper() and not callable(v)}
(out / "constants.json").write_text(json.dumps(c, indent=1))
import dataclasses
for name, geom in (("r1m3", "m32"), ("r2m3", "r2m3")):
    d = fl.build_net(dataclasses.replace(cfg, geom=geom))
    shutil.copy(d / "net.xml", out / f"{name}_net.xml")
    shutil.copy(d / "add.xml", out / f"{name}_add.xml")
    shutil.copy(d / "spec.json", out / f"{name}_spec.json")
