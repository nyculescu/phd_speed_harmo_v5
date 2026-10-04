"""Verify every Q[fNNN pN]: "..." quote in a profile file against the cited PDF page.

Usage: python docs/review/verify_quotes.py docs/review/drl_vsl_red_flags_per_paper_v0.md
The file map in the profile file links each fNNN id to a PDF under docs/knowledge_base/.
Text is extracted with `pdftotext -layout`; page n = PDF page index (1-based).
Matching ignores case, whitespace and hyphens (layout mode splits columns and hyphenates line ends).
QI[...] quotes (read from page images) are not checked.
"""
import re, subprocess, sys, unicodedata
from pathlib import Path

KB = Path(__file__).resolve().parents[1] / "knowledge_base"
QRE = re.compile(r'Q\[(f\d{3}) p(\d+)\]:\s*"(.+?)"\s*$', re.M)
MAPRE = re.compile(r"^\| (f\d{3}) \| `(.+?)` \|$", re.M)


def norm(s):
    s = unicodedata.normalize("NFKC", s)
    for a in "‐‑–—−":
        s = s.replace(a, "-")
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"[\s\-]+", "", s).lower()


def pages(pdf):
    txt = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True).stdout
    return [norm(p) for p in txt.split("\f")]


def main(fn):
    doc = Path(fn).read_text(encoding="utf-8")
    fmap = dict(MAPRE.findall(doc))
    cache, tot, bad = {}, 0, 0
    for fid, p, q in QRE.findall(doc):
        tot += 1
        if fid not in cache:
            cache[fid] = pages(KB / fmap[fid])
        pg = cache[fid][int(p) - 1] if int(p) <= len(cache[fid]) else ""
        chunks = [c for c in norm(q.replace("…", "...")).split("...") if c]
        if not all(c in pg for c in chunks):
            bad += 1
            print(f"NOT FOUND {fid} p{p}: {q[:90]}")
    print(f"{tot} quotes checked, {bad} not found")
    return bad


if __name__ == "__main__":
    sys.exit(1 if main(sys.argv[1]) else 0)
