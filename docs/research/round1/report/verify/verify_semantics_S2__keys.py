import json
with open("/home/catalin/work/phd/v5b1_runs/round1_remote/out/test/test.jsonl") as h:
    for line in h:
        r = json.loads(line)
        if r["name"] == "X2|nc":
            break
def walk(d, p=""):
    for k, v in d.items():
        if isinstance(v, dict):
            walk(v, p + k + ".")
        else:
            t = type(v).__name__ + (f"[{len(v)}]" if isinstance(v, list) else "")
            print(p + k, t)
walk({k: v for k, v in r.items() if k != "cfg"})
