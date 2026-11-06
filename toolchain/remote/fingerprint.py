"""One pilot and one PPO update in baseline-v3's mode on fixed seeds (as in checks1.py identity), then a SHA-256 of the weights, scale and pilot statistics.
Equal fingerprints on two machines mean training gives identical numbers on both. The reference is made on the laptop and belongs to one version of v5b/.
usage: fingerprint.py OUT_DIR [--write REF_FILE | --check REF_FILE]"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "docs/research/round1")]
from checks1 import ENV_V3, GAMMA, LAM, NET_SEED, PY, Q, SHORT  # noqa: E402


def feed(h, x) -> None:
    if isinstance(x, torch.Tensor):
        h.update(str(x.dtype).encode() + str(tuple(x.shape)).encode())
        h.update(x.detach().reshape(-1).contiguous().view(torch.uint8).numpy().tobytes())
    elif isinstance(x, dict):
        for k in sorted(x, key=str):
            h.update(str(k).encode())
            feed(h, x[k])
    elif isinstance(x, (list, tuple)):
        for v in x:
            feed(h, v)
    else:
        h.update(repr(x).encode())


def code_hash() -> str:
    h = hashlib.sha256()
    for f in sorted((ROOT / "v5b").rglob("*.py")):
        h.update(str(f.relative_to(ROOT)).encode() + f.read_bytes())
    return h.hexdigest()[:16]


def fingerprint(out: Path) -> str:
    d = out / "fingerprint"
    shutil.rmtree(d, ignore_errors=True)
    cmd = [PY, "-m", "v5b.fleet.c_train", "train", "--out", str(d), "--learner", "0", "--updates", "1", "--n-envs", "1",
           "--env", json.dumps({**ENV_V3, **SHORT}), "--levels", json.dumps([Q]), "--gamma", str(GAMMA), "--lam", str(LAM),
           "--net-seed", str(NET_SEED)]
    subprocess.run(cmd, cwd=ROOT, env={**os.environ, "PYTHONPATH": str(ROOT), "PYTHONDONTWRITEBYTECODE": "1"}, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    ck = torch.load(d / "C0_final.pt", map_location="cpu")
    h = hashlib.sha256()
    feed(h, ck["net"])
    feed(h, ck["scale"])
    feed(h, json.loads((d / "C0_pilot.json").read_text()))
    return h.hexdigest()


if __name__ == "__main__":
    out, mode, ref = Path(sys.argv[1]), *(sys.argv[2:4] + [None, None])[:2]
    fp, code = fingerprint(out), code_hash()
    print(f"fingerprint {fp} code {code}")
    if mode == "--write":
        Path(ref).write_text(f"{fp} {code}\n")
    elif mode == "--check":
        if not Path(ref).exists():
            print("no laptop reference yet: training is not checked")
            sys.exit(0)
        rfp, rcode = Path(ref).read_text().split()
        if rcode != code:
            print(f"reference is for other code ({rcode}); remake it on the laptop: training is not checked")
        elif rfp == fp:
            print("PASS training fingerprint equals the laptop's")
        else:
            print("FAIL training gives other weights than on the laptop")
            sys.exit(1)
