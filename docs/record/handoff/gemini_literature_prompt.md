# Prompt for Gemini: literature, references and background for the ITSC 2027 paper

(Paste everything below the line into Gemini. Paste or attach the Web of Science exports where step 2 asks for them.)

---

You are helping a PhD researcher prepare the **literature review, reference list, introduction and background** for an IEEE ITSC 2027 conference paper (6 pages, deadline 1 March 2027). Accuracy matters more than volume. **A wrong or invented reference is worse than a missing one.**

## 1. The paper (context; do not change its claims)

- **Working title:** "How much incident information does mainline metering need? An honest headroom decomposition in microsimulation".
- **Setting:**
  - one simulated freeway bottleneck in SUMO: 4 lanes merging toward a 1-lane bottleneck;
  - **mainline (mainstream) metering**: one traffic signal across all 4 mainline lanes, upstream of the bottleneck, with a 3-s amber and a minimum red. It is **not** on-ramp metering.
- **Incidents:** non-recurring; a bottleneck slowdown, or one lane crawling. Random onset and duration.
- **The information ladder compared:**
  1. **L0, always-on control without incident information:** fixed rate; integral feedback; a PI law in PI-ALINEA form; a set point estimated online (AD-ALINEA style).
  2. **Incident presence:** switch to a plan at onset.
  3. **Incident type:** a stored plan per type, with switch-back at clearance.
  4. **Full per-incident hindsight information:** bracketed honestly. The in-sample oracle is an upper bound inflated by selection on simulation noise; a cross-fitted oracle is a lower bound.
- **Results** (do not restate them as novel; they are for positioning only):
  - knowing only that an incident is on gave no ≥ 10 % gain over strong always-on control;
  - knowing the incident type added 12–22 % over presence alone in 2 of 4 conditions;
  - one condition was confirmed on fresh seeds: the type plan beat always-on PI-ALINEA by 16.2 % [7.3, 23.7];
  - in this simulator, gains are fragile to detection delay in some conditions;
  - red-light runners (10 % / 30 %) leave the confirmed result intact.
- **Methods features:**
  - pre-registered protocols;
  - paired seeds with block bootstrap CIs;
  - cross-fitting against the "winner's curse" (selection on noise) in hindsight oracles;
  - common-random-number problems in SUMO;
  - amber and red-runner modelling via SUMO junction-model parameters.

## 2. Web of Science (the researcher runs these; you analyse the exports)

You cannot access Web of Science. The researcher will run these searches (Advanced Search, Topic field) and paste or attach the exported records (titles, authors, year, source, DOI, abstract). **Use only those records and sources you can verify.** Propose better search strings if you see gaps.

1. `TS=("mainline metering" OR "mainstream metering" OR "mainstream traffic flow control" OR "MTFC" OR "bottleneck metering" OR "toll plaza metering" OR "merging control" ) AND TS=(freeway OR motorway OR highway)`
2. `TS=("ramp metering" OR "freeway control") AND TS=(incident* OR "non-recurrent" OR "non-recurring" OR "lane closure" OR "lane blockage" OR "work zone")`
3. `TS=(ALINEA OR "PI-ALINEA" OR "AD-ALINEA" OR "feedback control") AND TS=("traffic" AND ("bottleneck" OR "capacity drop"))`
4. `TS=("incident detection" OR "automatic incident detection") AND TS=("detection time" OR "detection delay" OR "false alarm") AND TS=(freeway OR motorway)`
5. `TS=("value of information" OR "information level*" OR "partial information" OR "information requirement*") AND TS=("traffic control" OR "ramp metering" OR "traffic management")`
6. `TS=("common random numbers" OR "variance reduction" OR "replication*" OR "random seed*") AND TS=("traffic simulation" OR "microsimulation" OR SUMO OR VISSIM OR AIMSUN)`
7. `TS=("winner's curse" OR "optimizer's curse" OR "selection bias" OR "cross-fitting" OR "sample splitting") AND TS=(simulation OR "algorithm selection" OR benchmark*)`
8. `TS=("red light running" OR "signal violation" OR "ramp meter violation" OR compliance) AND TS=("ramp meter*" OR "metering signal*" OR "traffic signal*")`
9. `TS=("pre-registration" OR "preregistration" OR "reproducib*") AND TS=("transportation research" OR "traffic simulation")`

## 3. Seed references to VERIFY first

These came from an earlier search. Verify each one (title, authors, year, venue, DOI) against the publisher or the DOI resolver. Mark it **VERIFIED**, **CORRECTED** (give the correction) or **NOT FOUND**. Never "fix" a reference by guessing.

- Tympakianaki, Spiliopoulou, Kouvelas, Papamichail, Papageorgiou (2014), Transportation Research Part C 44, 242–252, doi:10.1016/j.trc.2014.04.006 (mainstream signals at work-zone lane drops; the closest prior work).
- Papageorgiou, Papamichail, Spiliopoulou, Lentzakis (2008), TR-C 16, 535–553, doi:10.1016/j.trc.2007.11.002 (ALINEA-based merging control).
- Spiliopoulou, Papamichail, Papageorgiou (2010), J. Transp. Eng. 136(1) (toll-plaza merging control).
- Haboian (1995), Transportation Research Record 1494, 11–20 (mainline metering in practice: SF–Oakland Bay Bridge, Baltimore Harbor Tunnel).
- Hale, Ma, Ghiasi et al. (2020), FHWA-HRT-20-008; Ghiasi et al. (2018), IEEE ITSC, doi:10.1109/ITSC.2018.8569567 (mainline plus ramp signals at a merge).
- Carlson, Papamichail, Papageorgiou, Messmer (2010), TR-C, doi:10.1016/j.trc.2009.05.014; Carlson et al. (2011), IEEE T-ITS, doi:10.1109/TITS.2011.2156792 (MTFC).
- Wang, Kan, Papageorgiou, Papamichail (2014), IEEE T-ITS, doi:10.1109/TITS.2014.2307884 (PI-ALINEA).
- Papageorgiou, Hadj-Salem, Blosseville (1991), ALINEA, Transportation Research Record 1320.
- Sheu & Chang (2007), IEEE T-ITS, doi:10.1109/tits.2007.893327; Dabiri & Kulcsár (2014), IFAC, doi:10.3182/20140824-6-za-1003.02383; Wu et al. (2014), JTTE, doi:10.1016/s2095-7564(15)30097-0 (incident-responsive ramp metering).
- Cameron, Hoos & Leyton-Brown (2016), IJCAI ("Bias in Algorithm Portfolio Performance Evaluation"); van Hasselt (2010), "Double Q-learning", NIPS; Smith & Winkler (2006), Management Science, doi:10.1287/mnsc.1050.0451 (selection on noise / the optimizer's curse).
- Lopez et al. (2018), "Microscopic Traffic Simulation using SUMO", IEEE ITSC (the SUMO reference).
- Madison Beltline ramp meter evaluation (UW-Madison for WisDOT, 2005); Edara, Sun & Zhu (2012), InTrans report on work-zone meter compliance.
- Frejo & De Schutter (2021) on logic-based traffic flow control vs MTFC + PI-ALINEA.

## 4. What to deliver (in this order)

1. **Verified reference table**, one row per reference:
   - key; full citation in **IEEE style**; DOI or URL;
   - status (VERIFIED / CORRECTED / NOT FOUND / NEW-FROM-WOS);
   - what you actually read (abstract only / full text);
   - category (mainline metering; ramp metering under incidents; feedback control; incident detection; simulation methodology; selection bias; compliance);
   - one sentence on **how it relates to our paper**: supports, contrasts, or is the method source.
2. **BibTeX** for every VERIFIED or CORRECTED reference, with DOIs. Nothing for NOT FOUND.
3. **Gap map:** what the literature has done vs not done on the information question. Be honest: if you find a paper that already answers "how much incident information does a meter need", say so prominently. That would change our framing.
4. **Introduction draft** (about 450 words, IEEE style, citations as [n] keyed to the table):
   - motivation: incidents and non-recurrent congestion; mainline metering in practice;
   - what is known (ALINEA/PI-ALINEA, MTFC, incident-responsive metering);
   - the open question (which information is actually needed);
   - our approach in one paragraph;
   - contributions as 3 bullets, **without** "first", "novel" or "unprecedented".
5. **Background section draft** (about 400 words): mainline metering and its controllers; incident detection timing; why simulation benchmarks need honest headroom (selection on noise, common random numbers).
6. **Open questions for the researcher:** anything uncertain, conflicting or behind a paywall.

## 5. Rules (strict)

- **Never invent** a title, author, year, venue, page, DOI or quote. If you cannot verify it, write NOT FOUND or [VERIFY].
- **Say exactly what you read** (abstract vs full text). Do not attribute findings you did not read.
- **No novelty claims** ("first", "novel", "unprecedented") in any draft text.
- **Keep our framing:** this is **mainline** metering, not ramp metering. The always-on PI controller is an **established baseline** (Tympakianaki et al. 2014; Papageorgiou et al.), not our contribution. Our contribution is the information ladder and the honest headroom accounting.
- **Prefer** peer-reviewed journals (TR-B, TR-C, IEEE T-ITS, TRR), IEEE ITSC/IV, and official agency reports (FHWA, state DOTs). Flag preprints as preprints.
- **Use plain, precise English** (the researcher's English is a second language).
