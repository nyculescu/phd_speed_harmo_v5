"""Rent and release vast.ai machines, one training each, through the vastai CLI. Every rental and every destroy asks for a typed yes.
usage:
  vast.py offers [N]               the N cheapest offers that fit one training (spends nothing)
  vast.py rent [OFFER_ID] [--yes]  rent that offer, or the cheapest; wait for SSH; the last stdout line is the SSH command
  vast.py list                     your instances
  vast.py destroy ID [--yes]       stop the instance and its billing
--yes skips the prompt; use it only for an offer the author approved in writing.
The API key is set once with: vastai set api-key KEY"""
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

VAST = str(Path(sys.executable).with_name("vastai"))
# One training: 20 processes, 6.5 GB peak; evaluation wants more threads, so RAM has headroom.
SPEC = "cpu_arch=amd64 cpu_cores_effective>=24 cpu_ram>=32 disk_space>=40 reliability>0.99 duration>=2 inet_down>=100"
SLOW = re.compile(r"E5-|E7-|Xeon Phi|EPYC 7\d\d1")  # 2014-2017 Xeons, Xeon Phi and first-generation EPYC: far slower per core than the laptop
IMAGE = os.environ.get("VAST_IMAGE", "ubuntu:22.04")
# A saved console template (SSH launch, from vast.ai's base image) takes precedence over IMAGE.
TEMPLATE = os.environ.get("VAST_TEMPLATE") or (Path(__file__).with_name("vast_template").read_text().strip() if Path(__file__).with_name("vast_template").exists() else "")


def say(*a) -> None:
    print(*a, file=sys.stderr, flush=True)


def vast(*args, raw=True):
    r = subprocess.run([VAST, *args] + (["--raw"] if raw else []), capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"vastai {' '.join(args)} failed: {(r.stderr or r.stdout).strip()}")
    return json.loads(r.stdout) if raw else r.stdout.strip()


def offers() -> list:
    return [r for r in vast("search", "offers", SPEC, "-o", "dph") if not SLOW.search(r.get("cpu_name") or "")]


def line(r) -> str:
    return (f"{r['id']}  ${r['dph_total']:.3f}/h  {int(r['cpu_cores_effective'])} threads  {r['cpu_ram'] / 1024:.0f} GB  "
            f"{(r.get('cpu_name') or '?').strip()} {r.get('cpu_ghz') or 0:.1f} GHz  {r.get('geolocation')}  reliability {r.get('reliability2', 0):.3f}")


def confirm(what: str, yes: bool) -> None:
    say(what)
    if yes:
        return
    say("Type yes to go on: ")
    if sys.stdin.readline().strip() != "yes":
        sys.exit("stopped")


def rent(offer_id, yes: bool) -> None:
    o = offers()
    r = o[0] if offer_id is None and o else next((x for x in o if str(x["id"]) == offer_id), None)
    if r is None:
        sys.exit("no offer fits the spec" if offer_id is None else f"offer {offer_id} is gone or does not fit the spec")
    how = ["--template_hash", TEMPLATE] if TEMPLATE else ["--image", IMAGE, "--ssh", "--direct"]
    confirm(f"Rent {line(r)}, {'template ' + TEMPLATE if TEMPLATE else 'image ' + IMAGE}, 40 GB disk? Billing runs until destroy.", yes)
    iid = vast("create", "instance", str(r["id"]), *how, "--disk", "40", "--label", "v5b1")["new_contract"]
    say(f"rented instance {iid}; stop billing with: vast.py destroy {iid}")
    for _ in range(90):
        if vast("show", "instance", str(iid)).get("actual_status") == "running":
            break
        time.sleep(10)
    else:
        sys.exit(f"instance {iid} not running after 15 min and still billing: vast.py destroy {iid}")
    url = vast("ssh-url", str(iid), raw=False)
    m = re.search(r"ssh://(\w+)@([^:\s]+):(\d+)", url)
    if not m:
        sys.exit(f"no SSH address in {url!r}; instance {iid} still bills")
    user, host, port = m.groups()
    for _ in range(30):
        ok = subprocess.run(["ssh", "-p", port, "-o", "StrictHostKeyChecking=accept-new", "-o", "ConnectTimeout=10", "-o", "BatchMode=yes",
                             f"{user}@{host}", "true"], capture_output=True).returncode == 0
        if ok:
            break
        time.sleep(10)
    else:
        sys.exit(f"SSH to {host}:{port} not answering after 5 min; is the laptop's key in the vast.ai account? Instance {iid} still bills")
    print(f"ssh -p {port} {user}@{host}")


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if x != "--yes"]
    yes = "--yes" in sys.argv
    cmd = a[0] if a else "offers"
    if cmd == "offers":
        for r in offers()[: int(a[1]) if len(a) > 1 else 5]:
            print(line(r))
    elif cmd == "rent":
        rent(a[1] if len(a) > 1 else None, yes)
    elif cmd == "list":
        for i in vast("show", "instances"):
            print(i.get("id"), i.get("actual_status"), f"${i.get('dph_total', 0):.3f}/h", i.get("label"), (i.get("cpu_name") or "").strip())
    elif cmd == "destroy":
        confirm(f"Destroy instance {a[1]}? Its disk and any unfetched results are lost.", yes)
        say(vast("destroy", "instance", a[1], "-y", raw=False))
    else:
        sys.exit(__doc__)
