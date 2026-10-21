"""Check a BibTeX block (or .bib file) against Crossref: title, year, volume, pages, first author per DOI.
Usage: python3 -I tools/verify_bib_crossref.py <file.md|file.bib>   (V120; costs no LLM tokens)"""
import difflib, json, re, sys, time, urllib.parse, urllib.request
t = open(sys.argv[1]).read()
bib = t.split("```bibtex")[1].split("```")[0] if "```bibtex" in t else t
def fld(b, k):
    m = re.search(rf"\b{k}\s*=\s*\{{(.*?)\}}\s*,?\s*(?:\n|$)", b + "\n", re.S)
    return re.sub(r"[{}\\'\"]", "", m.group(1)).strip() if m else ""
for key, b in re.findall(r"@\w+\{([^,]+),(.*?)\n\}", bib, re.S):
    doi = fld(b, "doi")
    if not doi:
        print(f"{key:20} NO-DOI  url={fld(b, 'url')[:70]}  -> check by hand"); continue
    try:
        r = json.load(urllib.request.urlopen(urllib.request.Request(
            "https://api.crossref.org/works/" + urllib.parse.quote(doi), headers={"User-Agent": "mailto:none@example.com"}), timeout=30))["message"]
    except Exception as e:
        print(f"{key:20} DOI-FAIL {doi} {e}"); continue
    ct = (r.get("title") or [""])[0]
    au = [a.get("family", "") for a in (r.get("author") or [])]
    cy = str((r.get("issued", {}).get("date-parts") or [[None]])[0][0])
    iss = []
    if difflib.SequenceMatcher(None, fld(b, "title").lower(), ct.lower()).ratio() < 0.85: iss.append(f"title vs '{ct[:90]}'")
    if cy != fld(b, "year"): iss.append(f"year {fld(b, 'year')}->{cy}")
    if fld(b, "volume") and fld(b, "volume") != r.get("volume", ""): iss.append(f"vol {fld(b, 'volume')}->{r.get('volume', '')}")
    if fld(b, "pages") and fld(b, "pages").replace("--", "-") != r.get("page", ""): iss.append(f"pages {fld(b, 'pages')}->{r.get('page', '')}")
    if au and au[0].lower() not in fld(b, "author").split(",")[0].lower(): iss.append(f"1st author -> {au[0]}")
    n_bib = len(fld(b, "author").split(" and ")) if fld(b, "author") else 0
    if au and n_bib and n_bib != len(au): iss.append(f"author count {n_bib}->{len(au)} ({', '.join(au)})")
    print(f"{key:20} {'OK' if not iss else 'CHECK'}  {'; '.join(iss)}")
    time.sleep(1)
