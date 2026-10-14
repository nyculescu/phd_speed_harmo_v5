import itertools, os, subprocess, sys, time
from multiprocessing import Pool
D = os.path.dirname(os.path.abspath(__file__)); PY = sys.executable
RUNS = "/home/catalin/work/phd/v5b1_runs/pilot_20261013"
jobs = [("base", a, l, s) for l in [0.55,0.60,0.65,0.70,0.75,0.80,0.85,0.90,0.95,1.00] for s in range(1,6) for a in ("B0","B1")]
jobs += [(v, a, l, s) for v in ("laneend","gap3k") for l in (0.70,0.80,0.90) for s in range(1,4) for a in ("B0","B1")]
def one(j):
    v,a,l,s = j
    tag=f"{v}_{a}_l{l:.2f}_s{s}"
    if os.path.exists(f"{RUNS}/{tag}/rc.txt") and open(f"{RUNS}/{tag}/rc.txt").read().strip()=="0": return tag,"skip"
    while os.getloadavg()[0] > 30: time.sleep(20)          # CPU guard (simple): never start above 30 load
    t=time.time(); r=subprocess.run([PY, f"{D}/pilot.py","run",v,a,str(l),str(s)],capture_output=True,text=True)
    return tag, f"rc={r.returncode} {time.time()-t:.0f}s"
if __name__=="__main__":
    with Pool(24) as p:
        for i,(tag,res) in enumerate(p.imap_unordered(one, jobs),1):
            print(f"{i}/{len(jobs)} {tag} {res}", flush=True)
    print("DONE", flush=True)
