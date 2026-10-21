"""Self-check: every number in ../p1b_result.md must appear in an out/*.log of this folder (signs and leading '+'
ignored). Prints the numbers not found, for a manual check. Usage: check_note.py"""
import glob, os, re
D = os.path.dirname(os.path.abspath(__file__))
note = open(os.path.join(D, "..", "p1b_result.md")).read()
logs = " ".join(open(f).read() for f in glob.glob(os.path.join(D, "out", "*.log")))
logs = logs.replace(",", "")
nums = set(re.findall(r"(?<![\w.])\d[\d,]*\.?\d*", note))
miss = sorted(n for n in nums if n.replace(",", "").rstrip(".") not in logs)
print(len(nums), "numbers;", len(miss), "not found in logs:", miss)
