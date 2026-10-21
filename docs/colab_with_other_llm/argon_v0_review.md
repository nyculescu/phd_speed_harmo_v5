# Review of "Argon IEEE ITSC Paper Literature Preparation v0" (2026-10-20, V120)

**Method:** every DOI was checked against Crossref with `tools/verify_bib_crossref.py` (no LLM tokens). The drafts were read against our verified results (`p1b_result.md`, `p1b_c1_summary.md`).

## References: 21 entries

| Result | Entries |
|---|---|
| **Exact match on Crossref** | 12: Papageorgiou 2008, Spiliopoulou 2010, Ghiasi 2018, Carlson 2010, Carlson 2011, Wang 2014, Sheu 2007, Smith 2006, Lopez 2018, Sun 2013, Frejo 2021 (Part 2), Smaragdis 2003 (the Crossref title is malformed; the content matches) |
| **Marked "VERIFIED" but wrong** | 3. **Tympakianaki 2014** misses its 6th author (Y. Wang). **Wu 2014** misses its 5th author (Li), and its pages are 129–137, not 129–136. **Dabiri 2014**'s title is truncated (it should end "– a ramp meter approach") |
| **No DOI (check by hand)** | 6: Haboian 1995, Hale 2020 (FHWA), Papageorgiou 1991 (ALINEA), Cameron 2016, van Hasselt 2010, the TOPS Lab 2005 report |
| **Real error it caught in our seed list** | Wang 2014's 2nd author is Kosmatopoulos, not Kan (confirmed by Crossref) |

Sloppiness: one table URL is wrapped in a Google redirect (`google.com/url?...`). The "full text" read status cannot be checked from here.

## Draft text: must be fixed before use

1. **It contradicts our data.** Background B: "a detection delay of even one to two minutes allows queue formation and capacity drop to set in". C1 kept a 12.5–16.4 % lead with delays of 30–120 s (V116). The sentence is also unsourced.
2. **Unsourced claim:** "non-recurrent disturbances account for a large share of freeway delay" (Introduction, sentence 1) has no citation.
3. **Overclaim:** "binary presence alone yields less than 10 % improvement". Our result is "no gain of 10 % or more was **detected**" (S1a FAIL).
4. **Terminology drift:** it renames our ladder L0/L1/L2/L3. The protocol uses L0, ID (presence), IP (type) and L2 (hindsight oracle). We must keep one set of terms.
5. **Missing CI:** the "16.2 % gain" needs its CI [7.3, 23.7] and its scope: one regime, against always-on PI-ALINEA.

## Verdict

- **Usable for:** finding papers, building a first-pass reference list, and catching seed errors.
- **Not trustworthy for:** final bibliographic accuracy ("VERIFIED" was wrong in 3 of 15 DOI entries) or factual claims in draft prose.
- **Required pipeline:** Argon output → `tools/verify_bib_crossref.py` (free) → a targeted check of draft claims against our result files (main session) → only then into `paper/`.
