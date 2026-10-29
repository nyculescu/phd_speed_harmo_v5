"""SUMO checks for the fleet that libsumo cannot read back: the ACC gains take effect."""
import json
import subprocess
import textwrap

from v5b.d1.config import PYTHON_BIN, clean_sumo_env

PROBE = textwrap.dedent("""
    import json, sys
    from pathlib import Path
    import libsumo as ls
    from v5b.fleet import fleet as fl, smoke
    d = fl.build_net(smoke.CFG)
    gains = json.loads(sys.argv[2])
    r = Path(sys.argv[1])
    g = " ".join(f'{k}="{v}"' for k, v in gains.items())
    r.write_text('<routes><route id="m" edges="1 2 3 4 5"/>'
                 '<vType id="lead" vClass="passenger" sigma="0"/>'
                 f'<vType id="acc" vClass="passenger" carFollowModel="ACC" tau="1.1" {g}/>'
                 '<vehicle id="L" type="lead" route="m" depart="0" departPos="60" departSpeed="20"/>'
                 '<vehicle id="F" type="acc" route="m" depart="0" departPos="0" departSpeed="20"/></routes>')
    ls.start(["sumo", "-n", str(d / "net.xml"), "-r", str(r), "--step-length", "0.1", "--no-step-log", "true"])
    out = []
    for i in range(300):
        if i == 50:
            ls.vehicle.slowDown("L", 8.0, 3.0)
        ls.simulationStep()
        if "F" in ls.vehicle.getIDList():
            out.append(round(ls.vehicle.getSpeed("F"), 4))
    ls.close()
    print(json.dumps(out))
""")


def _trace(tmp_path, gains, name):
    script = tmp_path / "probe.py"
    script.write_text(PROBE)
    r = subprocess.run([PYTHON_BIN, str(script), str(tmp_path / f"{name}.rou.xml"), json.dumps(gains)],
                       env=clean_sumo_env(), capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr[-2000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


def test_acc_original_gains_change_behaviour(tmp_path):
    from v5b.fleet import fleet as fl
    default = _trace(tmp_path, {}, "default")
    original = _trace(tmp_path, fl.ACC_ORIGINAL, "original")
    assert len(default) == len(original) > 100
    assert max(abs(a - b) for a, b in zip(default, original)) > 0.05
