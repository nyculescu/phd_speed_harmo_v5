"""One ALKS alone on the r1m3 road: lower its maxSpeed as the smooth rule does and read what SUMO does, at 0.1 s."""
import libsumo as ls, sys
from pathlib import Path
net = sorted(Path("/home/catalin/work/phd/v5b1_runs/_netcache").glob("m32_*/net.xml"))[0]
Path("b.rou.xml").write_text('''<routes><route id="m" edges="1 2 3a 3 4 5"/>
<vType id="a" length="4.4" width="1.78" laneChangeModel="LC2013" lcCooperative="1" lcAssertive="1.4" lcOvertakeRight="1" vClass="passenger" carFollowModel="IDM" tau="1.6" accel="2.6" decel="4.5" emergencyDecel="9" actionStepLength="0.5"/>
<vehicle id="v" type="a" route="m" depart="0" departLane="0" departSpeed="max" speedFactor="1"/></routes>''')
for ratio, once in ((1.10, False), (1.02, False), (1.10, True)):
    ls.start(["sumo", "-n", str(net), "-r", "b.rou.xml", "--step-length", "0.1", "--no-step-log", "true", "--no-warnings", "true", "--seed", "1"])
    t = 0; out = []; cap = None
    while t < 700:
        ls.simulationStep(); t += 1
        if "v" not in ls.vehicle.getIDList():
            continue
        s = ls.vehicle.getSpeed("v")
        if t >= 300 and t % 10 == 0 and (not once or t == 300):
            cap = max(s / ratio, 16.67)       # one-second clock, as the rule does
            ls.vehicle.setMaxSpeed("v", cap)
        if 295 <= t <= 345:
            out.append((round(t / 10, 1), round(s, 2), round(ls.vehicle.getAcceleration("v"), 2), None if cap is None else round(cap, 2)))
    print("ratio", ratio, "once" if once else "every second")
    print(" ".join(f"{a}:{b}/{c}" for a, b, c, d in out))
    ls.close()
