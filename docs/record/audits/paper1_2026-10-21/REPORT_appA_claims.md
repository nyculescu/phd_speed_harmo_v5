# Appendix A: claim dossiers to the paper_1 forensic audit

Main report: `REPORT_paper1_forensic_audit.md` (same folder). The text below is the agents' own output, reconciled as described in §0.2 of the main report. Paths of the form `/tmp/claude-1000/.../scratchpad/audit/<dir>/...` refer to the session scratch folder; the same files are now in `~/work/phd/v5b1_runs/audit_paper1_2026-10-21/<dir>/...` (caches over 10 MB excluded, see `EXCLUDED_CACHES.txt`).

### C01 (paper line 63): final verdict **UNVERIFIED**

> Non-recurring events (crashes, breakdowns, lane blockages) reduce freeway bottleneck capacity at unpredictable times; currently marked [CITE needed].

**Reconciliation:** Still a [CITE] placeholder. Two candidate sources with verified metadata (Knoop et al. 2008; Skabardonis et al. 2003); their full texts were not read.

#### Source: R1 LIT, verdict UNVERIFIED (basis: direct observation)

- **Meaning.** The paper's opening motivation is that incidents occur at random times and cut the capacity of a bottleneck. The draft has no source for this yet: there is only a red [CITE] placeholder. To support it, a reference must show empirically that incidents reduce capacity, or that incident-related (non-recurrent) congestion is a measurable share of delay.
- **Evidence.**
  - papers/paper_1/paper.qmd:63 \citeneeded{non-recurrent congestion share / capacity drop}; macro defined at paper.qmd:20
  - Candidate A (metadata verified on Crossref, abstract read on OpenAlex): Knoop, Hoogendoorn & van Zuylen 2008, 'Capacity Reduction at Incidents', TRR 2071:19-25, doi:10.3141/2071-03. Abstract: 'the (outflow) capacity of the remaining lanes is about 50% lower than the (free-flow) capacity of the same number of lanes'
  - Candidate B (Crossref plus abstract): Skabardonis, Varaiya & Petty 2003, 'Measuring Recurrent and Nonrecurrent Traffic Congestion', TRR 1856:118-124, doi:10.3141/1856-12. Abstract: 'incident-related delay was found to be 13% to 30% of the total congestion delay during peak periods'
- **Verification.** Confirmed that the placeholder is present in the qmd. Verified both candidates' DOIs with /tmp/.../LIT/scripts/crossref_candidates.py and read their abstracts on OpenAlex. Neither full text was read.
- **Failure points.** Neither candidate is about 'unpredictable times' as such: this follows from the definition of non-recurrent congestion. Knoop's 50 % applies to the remaining lanes at two observed accidents, so it should not be generalised. The author should read both full texts before citing.

### C02 (paper line 63): final verdict **VERIFIED**

> Mainline metering regulates flow with signals across all lanes of the freeway upstream of a bottleneck; studied for lane drops at work zones and toll plazas [Papageorgiou2008; Spiliopoulou2010; Tympakianaki2014].

**Reconciliation:** Papageorgiou 2008 (full text, local PDF) covers toll plazas and work zones; Spiliopoulou 2010 and Tympakianaki 2014 were checked by abstract only.

#### Source: R1 LIT, verdict VERIFIED (basis: direct observation)

- **Meaning.** The claim is that earlier work places traffic signals across every lane of the main road, upstream of a place where lanes merge, and uses a feedback law to keep the merge at capacity. The cited studies did this for work-zone lane drops and for toll plazas (many booth lanes merging into few).
- **Evidence.**
  - Papageorgiou 2008 full text (papers/refs_papers/1-s2.0-S0968090X07000873-main.pdf), §3.1 p. 543: toll plaza with 15 booth lanes merging into 5, '15 traffic lights (one per lane)'
  - Papageorgiou 2008 §4.1 p. 548: work zone, 3 lanes into 1; the example 'assumes that all upstream lanes are signal-controlled for reasons of equity and safety'
  - Spiliopoulou 2010 abstract (OpenAlex): toll-plaza merging control; 'an algorithm known from local ramp metering operations is proposed (ALINEA)'
  - Tympakianaki 2014 abstract (Semantic Scholar): 'green-red traffic signals at the motorway mainstream' at work-zone lane drops
- **Verification.** Read Papageorgiou 2008 in full via pdftotext (/tmp/.../LIT/papageorgiou2008.txt), and the other two abstracts via fetch_meta.py and fetch_s2.py.
- **Failure points.** The cited works call this 'merging traffic control', not 'mainline metering'. All three are simulation studies (AIMSUN), not field deployments. In the toll-plaza case the signals stand at the booth exits rather than on 'the freeway itself'.

#### Source: R2 G8, verdict VERIFIED (basis: direct observation)

- **Meaning.** Concept: traffic lights on every lane of the main road, set before a merge where lanes drop. Detail: earlier work used an ALINEA-type feedback law to keep the merge area near its critical number of vehicles, at toll plazas (many booths merging into few lanes) and at work-zone lane drops.
- **Evidence.**
  - Papageorgiou 2008 full text (LIT/papageorgiou2008.txt:439): '15 traffic lights (one per lane) ... placed at the exit of the booth area'; :654: all upstream lanes signal-controlled 'for reasons of equity and safety' (work zone)
  - Spiliopoulou2010 full abstract (EPFL REST, G8/dl_epfl/item_ac040851...json): 'Merging traffic control aims at maintaining the number of vehicles in the merge area close to a critical value that maximizes throughput'
  - Tympakianaki2014 abstract (workzonesafety.org record 47333, G8/dl_tymp/wzs_47333.html): 'Work zones on motorways necessitate the drop of one or more lanes'; 'green-red traffic signals at the motorway mainstream'
- **Verification.** Re-read the Papageorgiou 2008 passages. Fetched the complete Spiliopoulou abstract via EPFL DSpace REST and the complete Tympakianaki abstract from the NWZSIC record. Tried every legal full-text route for both; all failed (G8/access_log.txt).
- **Failure points.** Spiliopoulou2010 and Tympakianaki2014 rest on their abstracts, but the claim is high-level and the abstracts state it. The sources call this 'merging traffic control'. All three are simulation studies. At the toll plaza the lights stand at the booth exits, not on 'the freeway itself'.

### C03 (paper line 63): final verdict **VERIFIED**

> ...and for merges that combine mainline and ramp signals [Ghiasi2018; Hale2020].

**Reconciliation:** Supported at abstract / landing-page level (Ghiasi 2018, Hale 2020); full texts not read.

#### Source: R1 LIT, verdict VERIFIED (basis: direct observation)

- **Meaning.** At on-ramp merges, some studies signal both the ramp and the main road together. The paper cites one ITSC paper and the FHWA report from the same team.
- **Evidence.**
  - Ghiasi 2018 abstract (OpenAlex): 'a dynamic signal control algorithm for an integrated ramp and mainline metering control strategy' at freeway merging areas
  - Hale 2020, FHWA-HRT-20-008, May 2020 (FHWA landing page fhwa.dot.gov/publications/research/operations/20008): mainline metering is one of five designs; 'Mainline metering also showed reasonably good benefits but could be challenging to implement.'
- **Verification.** Read the abstract and the FHWA landing page. Hale2020's metadata matches the report's technical documentation page: Hale, Ma, Ghiasi plus 7 more authors.
- **Failure points.** Ghiasi's mainline signal is activated only 'when a significant speed drop is detected at all lanes ... and the traffic has been already almost stopped' (safety). The paper's meter runs on free-flowing traffic: see finding LIT-F11.

### C04 (paper line 65): final verdict **VERIFIED**

> For a known, stationary bottleneck, integral laws such as ALINEA [Papageorgiou1991] and PI extensions such as PI-ALINEA [Wang2014] keep the bottleneck near its critical state without a demand model.

**Reconciliation:** ALINEA law confirmed via the Papageorgiou 2008 full text (same first author, cites 1991). The 1991 original and the Wang 2014 full text were not read.

#### Source: R1 LIT, verdict VERIFIED (basis: direct observation)

- **Meaning.** ALINEA adds, at every control step, a gain times the gap between the target occupancy (or vehicle count) and the measured one. In steady state this drives the bottleneck to its critical state, which gives maximum flow. It uses measurements only, with no prediction of demand. PI-ALINEA adds a proportional term for bottlenecks further downstream.
- **Evidence.**
  - TRID 365587 (Papageorgiou, Hadj-Salem & Blosseville 1991, TRR 1320:58-64): 'ALINEA is a simple, robust, flexible, and effective local strategy for ramp metering'
  - Papageorgiou 2008 full text §2.7.1 p. 540, eq. (1): q(k) = q(k-1) + K_R[o_hat - o(k-1)]; p. 541: in steady state o(k-1) = o_hat (exact regulation); §2.4 p. 538: the aim is to 'maintain (whenever necessary) the number of vehicles N in the merge area close to its critical value Ncr'
  - Papageorgiou 2008 §2.7.1 p. 542: uncontrolled flows 'act as disturbances that do not need to be taken into account in the control algorithm thanks to its feedback character'
  - Wang 2014 abstract (OpenAlex): PI-ALINEA 'can lead to satisfactory control performance' for a distant downstream bottleneck
- **Verification.** Read Papageorgiou 2008 in full. ALINEA 1991 itself was not read: its law was checked through the 2008 paper, which has the same first author and cites 1991 for eq. (1). TRID metadata matches the bib (pages 58-64; one library catalogue gives 58-65).
- **Failure points.** For ALINEA, a secondary full text stands in for the primary one. 'Known, stationary' is the paper's framing; ALINEA's set point still has to be known or tuned. Wang's support comes from an abstract with macroscopic simulation only.

### C05 (paper line 65): final verdict **PARTIALLY SUPPORTED**

> The same laws drive mainstream traffic flow control with variable speed limits [Carlson2010; Carlson2011] and remain strong benchmarks [Frejo2021b].

**Reconciliation:** Carlson2010 is model-based optimal control, not "the same laws". The feedback MTFC benchmark Frejo uses is Carlson et al. 2014 (not cited). Carlson2011 not read in full.

#### Source: R1 LIT, verdict PARTIALLY SUPPORTED (basis: direct observation)

- **Meaning.** The claim is that ALINEA-type feedback laws are also used to set variable speed limits (mainstream traffic flow control, MTFC), and that these simple laws remain hard to beat. Carlson 2010 would have to be a feedback-law paper, and Frejo would have to treat these laws as a strong reference.
- **Evidence.**
  - Carlson 2010 (EPFL Infoscience 154946 abstract): uses a tool for 'optimal integrated motorway network traffic control', i.e. model-based optimal control, not an ALINEA-type law
  - Carlson 2011 abstract (OpenAlex): 'A simple local MTFC feedback controller is designed in this paper'; 'no online model usage and no demand predictions are needed'. The PI form is not stated in the abstract
  - Frejo 2021b author accepted copy (idus.us.es/handle/11441/108871), §III.A: 'The integrated controller MTFC + PI-ALINEA [2] is probably the most well-known easy-to-implement control architecture for VSLs and RMs.' Its [2] is Carlson, Papamichail & Papageorgiou 2014, TR-C 46:209-221; its [5], used as the optimal reference, is Carlson 2010
  - Frejo 2021b: MTFC + PI-ALINEA averages a 27.6 % TTS reduction, against 29.2 % for LB-TFC and 30.3 % for the optimum; conclusions: 'LB-TFC outperforms MTFC + PI-ALINEA'. Frejo 2021a: MTFC performance is 'highly decreased' when parameters are used in different conditions
- **Verification.** Read both Frejo parts in full (/tmp/.../LIT/frejo2021b_raw.txt, frejo2021a_raw.txt) and the Carlson abstracts and landing pages. Verified Carlson 2014's metadata on Crossref (doi:10.1016/j.trc.2014.05.017).
- **Failure points.** Carlson2010 does not support 'the same laws' (finding LIT-F2). That Carlson2011 is PI-type is not verified from its own text; Frejo calls MTFC and PI-ALINEA 'PI controllers'. 'Strong' is an interpretation: Frejo beats the benchmark and reports it is fragile under recalibration.

#### Source: R2 G8, verdict PARTIALLY SUPPORTED (basis: direct observation)

- **Meaning.** Concept: ALINEA-type feedback laws are also used to set variable speed limits (MTFC), and they remain hard to beat. Detail: each cited Carlson paper should use such a feedback law, and Frejo should treat it as a strong reference.
- **Evidence.**
  - Carlson2010 full abstract (EPFL REST): 'A previously developed, computationally efficient software tool for optimal integrated motorway network traffic control including MTFC is applied'
  - Frejo 2021a full text (LIT/frejo2021a_raw.txt:104-108) lists [9] = Carlson 2010 under 'Optimization-based controllers'; :145-155 describes [6] = Carlson 2011 MTFC as 'a local VSL controller with feedback of the flow downstream ... and of the density at the bottleneck area'
  - Carlson2011 abstract: 'A simple local MTFC feedback controller is designed'
  - Frejo 2021b full text :128 'MTFC + PI-ALINEA [2] is probably the most well-known easy-to-implement control architecture' ([2] = Carlson 2014); eq. (4) :1252 velocity PI form; :1921 'PI controllers ... such as PI-ALINEA and MTFC'; :415-424 TTS reductions of 27.6 % (MTFC+PI-ALINEA), 29.2 % (LB-TFC) and 30.3 % (optimum)
- **Verification.** Fetched the Carlson 2010/2011 abstracts from EPFL REST (the records hold no PDF) and re-read the relevant passages of both Frejo full texts.
- **Failure points.** For Carlson2010 the claim is false: it is optimal control (LIT-F2, G8-F5). Carlson2011 is a PI-type feedback with the same structure, not ALINEA itself; its full text was not read. Frejo's benchmark is Carlson 2014, which the paper does not cite. 'Strong' fits the near-optimal numbers, but Frejo's own controller beats the benchmark, and Frejo 2021a reports that it is fragile under recalibration.

### C06 (paper line 65): final verdict **CONTRADICTED**

> Set-point adaptation [Smaragdis2003] tracks slow changes in the bottleneck without an incident detector.

**Reconciliation:** Concept right, citation wrong: AD-ALINEA (online set-point estimation) is Smaragdis, Papageorgiou & Kosmatopoulos 2004 (TR-B 38(3)); the cited 2003 abstract covers other ALINEA extensions. The 2003 full text could not be read legally.

#### Source: R1 LIT, verdict CONTRADICTED (basis: derived)

- **Meaning.** An adaptive version of ALINEA estimates the critical occupancy online, so it can follow changes in capacity without being told about incidents. The claim credits this idea to Smaragdis & Papageorgiou 2003.
- **Evidence.**
  - Smaragdis2003 abstract (Crossref and OpenAlex, TRR 1856:74-86): 'the following new local ramp metering strategies are presented: FL-ALINEA ..., UP-ALINEA ..., and UF-ALINEA ...', plus X-ALINEA/Q; no adaptive or AD strategy is listed
  - Smaragdis, Papageorgiou & Kosmatopoulos 2004, TR-B 38(3):251-270, doi:10.1016/S0191-2615(03)00012-2 (IDEAS abstract): 'An extension of the feedback local ramp metering strategy ALINEA is proposed that allows the automatic tracking of the critical occupancy'; it names AD-ALINEA
  - Papageorgiou 2008 full text §2.7.1 p. 541: 'one may employ a real-time estimator for these quantities, e.g., as proposed in Smaragdis et al. (2004) and Kosmatopoulos et al. (2006)'. The same section attributes FL-ALINEA to Smaragdis and Papageorgiou 2003
  - The repo protocol docs/research/protocols/p1_incident_information.md:35 cites 'Smaragdis et al. 2004 [VERIFY]; not its estimator'. docs/colab_with_other_llm/argon_v1_review.md:5 wrongly says 'AD-ALINEA is already cited via Smaragdis & Papageorgiou (2003)'
- **Verification.** Compared the abstracts of both Smaragdis papers with how Papageorgiou 2008's full text attributes them. The 2003 full text was not read (paywalled).
- **Failure points.** If the 2003 full text does describe AD-ALINEA, this softens to PARTIALLY SUPPORTED, but the defining paper would still be 2004. 'Slow changes': the 2004 abstract motivates the method by environmental conditions and traffic composition (trucks), not by incidents.

#### Source: R1 recheck (LIT), verdict CONTRADICTED (basis: derived)

- **Evidence.**
  - papers/paper_1/paper.qmd:65@1e5e8d7 (working tree clean for papers/paper_1): 'Set-point adaptation [@Smaragdis2003] tracks slow changes in the bottleneck without an incident detector.' The same key is used at qmd:81 ('adaptive schemes estimate it online [@Smaragdis2003]') and qmd:118 ('in the spirit of AD-ALINEA (AD) [@Smaragdis2003]').
  - papers/paper_1/references.bib:137-148: Smaragdis2003 = 'Series of New Local Ramp Metering Strategies', TRR 1856(1):74-86, doi 10.3141/1856-08. There is no Smaragdis 2004 entry, and the Zotero library (~/Zotero/zotero.sqlite, read with immutable=1) has only item 16 (the 2003 paper) with no attachment.
  - Papageorgiou, Papamichail, Spiliopoulou & Lentzakis 2008, TR-C 16:535-553, local full text papers/refs_papers/1-s2.0-S0968090X07000873-main.pdf, p. 541, §2.7.1: 'The precise value of ocr (or Ncr) ... can be identified experimentally. Alternatively, one may employ a real-time estimator for these quantities, e.g., as proposed in Smaragdis et al. (2004) and Kosmatopoulos et al. (2006).' Same page: 'flow-based regulator (FL-ALINEA; see Smaragdis and Papageorgiou, 2003)'. Reference list p. 552: 2003 = 'A series of new local ramp metering strategies'; 2004 = 'A flow-maximizing adaptive local ramp metering strategy. TR-B 38, 251-270'.
  - Papageorgiou 2008 §2.4, p. 539: the critical occupancy 'was found to be fairly stable ... even under adverse environmental conditions'.
  - Smaragdis 2003 Crossref and OpenAlex abstract (LIT tracer cache .../scratchpad/audit/LIT/dl_meta/Smaragdis2003.json, key crossref.abstract): 'the following new local ramp metering strategies are presented: FL-ALINEA ..., UP-ALINEA ..., and UF-ALINEA ... X-ALINEA/Q ...'. Strategies named: FL-, UF-, UP-ALINEA and X-ALINEA/Q. Adaptation-related terms found: none.
  - Smaragdis, Papageorgiou & Kosmatopoulos 2004 abstract (LIT tracer cache .../scratchpad/audit/LIT/dl_misc/ideas_smaragdis2004.html): 'An extension of the feedback local ramp metering strategy ALINEA is proposed that allows the automatic tracking of the critical occupancy ... The developed AD-ALINEA strategy may be valuable whenever the critical occupancy cannot be estimated beforehand or is subject to real-time change due to changing environmental conditions or traffic composition (e.g. trucks). ... (AU-ALINEA) is also developed.'
  - The repo's own attribution is 2004: docs/research/protocols/p1_incident_information.md:35 ('in the spirit of AD-ALINEA (Smaragdis et al. 2004 [VERIFY]; not its estimator)'); docs/research/direction_sweep_v2_margins.json:129 ('AD-ALINEA from 2004').
  - Error chain: 'docs/colab_with_other_llm/Argon IEEE ITSC Paper Literature Preparation v0.md':27,267,317 (Argon added the 2003 paper 'to verify AD-ALINEA', claimed 'extremum-seeking set-point adaptation' for 'weather, incidents', and asked which of 2003 and 2004 matches). 'Argon ... v1.md':54-60 replaced it with the 2004 paper as [20]. docs/colab_with_other_llm/argon_v1_review.md:5 kept 2003 ('AD-ALINEA is already cited via Smaragdis & Papageorgiou (2003)'). docs/baseline/BASELINE_2_2026-10-20.md:43 checked the 2003 entry against the registry for metadata only.
- **Verification.** Re-check outcome UPHELD: Meaning: line 65 of the paper says there is a known way to adapt the set point (target value) of an ALINEA-type controller online. This lets it follow slow changes of the bottleneck without an incident detector. The sentence gives Smaragdis & Papageorgiou (2003) as the source. The idea itself is real: AD-ALINEA estimates the critical occupancy online. But it was proposed in Smaragdis, Papageorgiou & Kosmatopoulos (2004, TR-B 38:251-270), not in the 2003 TRR paper.

How I tried to save the claim: (a) the 2003 paper might also contain an adaptive or set-point estimating strategy; (b) one of its strategies might count as 'set-point adaptation' if read loosely; (c) a local copy of the 2003 full text, or a Zotero note, might show otherwise. All three fail on the primary evidence I have.

- (a) The publisher abstract of the 2003 paper (Crossref and OpenAlex) lists the paper's new strategies exhaustively ('More specifically, the following new local ramp metering strategies are presented'): FL-ALINEA, UP-ALINEA, UF-ALINEA and X-ALINEA/Q. No adaptive, estimation or set-point term appears.
- (b) FL-ALINEA follows a flow set point that is given from outside. UP-ALINEA and UF-ALINEA replace the measurement with upstream data. X-ALINEA/Q adds queue control. None of them adapts the set point.
- (c) The 2004 abstract presents AD-ALINEA as new ('An extension ... is proposed that allows the automatic tracking of the critical occupancy'). Papageorgiou et al. 2008 shares a co-author with both papers, and I read its full text locally. On p. 541 (§2.7.1) it credits the online estimation of o_cr to 'Smaragdis et al. (2004) and Kosmatopoulos et al. (2006)', and in the same section it credits 2003 only for FL-ALINEA.
- The repo itself agrees with 2004. The protocol (docs/research/protocols/p1_incident_information.md:35) says 'Smaragdis et al. 2004 [VERIFY]'. docs/research/direction_sweep_v2_margins.json:129 says 'AD-ALINEA from 2004'.
- Where the error came from: Argon v0 (an external LLM) added the 2003 paper to back AD-ALINEA. It described that paper as proposing 'extremum-seeking set-point adaptation' for 'weather, incidents', which the 2003 abstract does not support, and it asked the author which of the 2003 and 2004 papers matched. Argon v1 then switched to the 2004 paper. The in-repo review argon_v1_review.md:5 wrongly kept 2003 ('AD-ALINEA is already cited via Smaragdis & Papageorgiou (2003)'). BASELINE_2 checked only the bibliographic metadata of the 2003 entry, not what the paper says.

The citation is therefore wrong as written, so CONTRADICTED stands. The method content is true once it is credited to the 2004 paper. One sub-claim is only an interpretation: 'slow changes in the bottleneck'. The 2004 abstract speaks of 'real-time change due to changing environmental conditions or traffic composition (e.g. trucks)'. It says nothing about 'slow' and nothing about incidents. Papageorgiou 2008 §2.4 (p. 539) adds that o_cr is 'fairly stable even under adverse environmental conditions'.

The same misattribution appears twice more. Line 81 says 'adaptive schemes estimate it online [@Smaragdis2003]' and ties this to incidents, which the 2004 abstract does not mention. Line 118 says 'in the spirit of AD-ALINEA (AD) [@Smaragdis2003]'. AD-ALINEA is named in the 2004 abstract, not in the 2003 one.

Severity: major. The statement is wrong as written, and reviewers would notice because it credits the source of a baseline arm to the wrong paper. The headline results are not affected. Fix: cite Smaragdis et al. 2004 (doi:10.1016/S0191-2615(03)00012-2), and optionally Kosmatopoulos et al. 2006 (TRR 1959:65-76), at lines 65, 81 and 118. Keep Smaragdis2003 only if FL-ALINEA, UP-ALINEA or UF-ALINEA is mentioned. Neither references.bib nor Zotero has a 2004 entry at present.

Remaining risk: I did not read the 2003 full text (it is not available locally, and this task allows no web access). The abstracts I used are the LIT tracer's cached downloads; I did not fetch them again. If the 2003 body did discuss AD-ALINEA, the verdict would soften to PARTIALLY SUPPORTED. But the 2004 abstract calls the method a new proposal, and the co-author's 2008 attribution makes that very unlikely. To test it, get TRR 1856:74-86 and search it for 'AD-ALINEA', 'adaptive' and 'critical occupancy estimation'.

#### Source: R2 G8, verdict CONTRADICTED (basis: derived)

- **Meaning.** Concept: an adaptive ALINEA estimates its critical set point online and so can follow capacity changes without being told about incidents. Detail: the claim credits this to Smaragdis & Papageorgiou 2003 (TRR 1856).
- **Evidence.**
  - Smaragdis2003 abstract (LIT/dl_meta/Smaragdis2003.json): the strategies presented are FL-ALINEA, UP-ALINEA, UF-ALINEA and X-ALINEA/Q; no adaptive strategy is listed
  - Smaragdis, Papageorgiou & Kosmatopoulos 2004 abstract (IDEAS, LIT/dl_misc/ideas_smaragdis2004.html): 'allows the automatic tracking of the critical occupancy'; 'The developed AD-ALINEA strategy'
  - Papageorgiou 2008 full text (LIT/papageorgiou2008.txt:333-334): real-time estimator 'as proposed in Smaragdis et al. (2004) and Kosmatopoulos et al. (2006)'; :356 attributes FL-ALINEA to Smaragdis and Papageorgiou 2003
- **Verification.** Tried every legal full-text route for both Smaragdis papers: SAGE closed, ScienceDirect subscribers only, TUC behind Anubis, OpenAlex/S2 closed. Compared both abstracts with how the 2008 full text (same senior author) attributes them.
- **Failure points.** The concept is correct (2004 abstract). The citation is wrong, unless the unread 2003 full text also describes an adaptive set point; even then the defining paper would be 2004. The 2004 abstract motivates the method by 'environmental conditions or traffic composition', not by incidents.

### C07 (paper line 65): final verdict **PARTIALLY SUPPORTED**

> Incident-responsive ramp metering switches or schedules the controller when an incident is reported [Sheu2007; Dabiri2014; Wu2014], usually compared with no control or with a fixed-parameter controller.

**Reconciliation:** Sheu 2007 detects incidents itself; Dabiri 2014 schedules gains continuously on estimated incident magnitudes (no plan switch on a flag); Wu 2014 full text unreachable. "Usually compared with no control or a fixed-parameter controller" holds for 2 of 3 cited works; as a generalisation it is unsupported.

#### Source: R1 LIT, verdict PARTIALLY SUPPORTED (basis: direct observation)

- **Meaning.** Earlier incident-aware ramp metering changes the control law once an incident is known, and is evaluated against weak baselines: no control, or one fixed tuning. The second half is a statement about the comparison practice of a whole literature.
- **Evidence.**
  - Sheu2007 abstract (OpenAlex): 'identification of control-zone-based congestion patterns using the modified generalized-sequential-probability-ratio-testing technology', followed by stochastic optimal control; the method detects incidents itself
  - Dabiri2014 abstract (research.chalmers.se/publication/211200): 'The main idea is to use local freeway control solution triggered by available incident parameter values.'; 'compared to other existing approach' (the approach is not named)
  - Wu2014 abstract (OpenAlex): the lower model must 'recognize where the incident congestion exists, based on an adaptive neural network'; 'shorten the delay by about 25%' (baseline not named)
- **Verification.** Read the three abstracts. Full texts are closed or were blocked (ScienceDirect 403, NTNU mirror TLS error) and were not read. No source was found for 'usually'.
- **Failure points.** Two of the three works detect incidents themselves rather than act 'when reported'. The baseline clause is UNVERIFIED: it would need the baseline sections of these three papers plus a wider set (or a review) to justify 'usually'. Otherwise reword it, e.g. 'often evaluated against ...', citing the papers whose baselines were checked.

#### Source: R2 G8, verdict PARTIALLY SUPPORTED (basis: direct observation)

- **Meaning.** Concept: earlier incident-aware ramp metering changes its control once an incident is known, and is tested against weak baselines. Detail: (a) the controller acts on an incident report; (b) its baselines are no control or a fixed-parameter controller.
- **Evidence.**
  - Sheu 2007 full text (G8/sheu2007.txt:61-63, p. 359): congestion patterns 'are identified and grouped in real time' by M-GSPRT, including 'incident-induced and incident-free patterns' (:87). The method detects incidents itself; nothing is reported to it
  - Sheu 2007 p. 366 (:1357-1360): compared with 'incident-responsive isolated multiramp control and two existing control strategies implemented in the site, i.e., pretimed ramp control and no control'; :1372 'direct comparisons with these published ramp-control models are not taken into account'
  - Dabiri 2014 full text (G8/dabiri2014.txt:23, p. 11338): 'local freeway control solution triggered by available incident parameter values'; p. 11342 (:382-397): compared with 'the scheduled LQR controller as well as the nominal LQR controller' 'along with no-control case'; footnote :432 says the nominal LQR is 'an already existing solution'
  - Wu 2014 abstract only: the lower model must 'recognize where the incident congestion exists, based on an adaptive neural network'; 'shorten the delay by about 25%' (baseline not named)
- **Verification.** Read the Sheu and Dabiri full texts (G8/access_log.txt). Wu2014 is CC BY-NC-ND, but every route failed (ScienceDirect 403, journal site timed out, Elsevier API returns metadata only without a key).
- **Failure points.** (a) 'When an incident is reported' is wrong for Sheu (it detects incidents itself) and, from its abstract, for Wu. Dabiri assumes the incident parameters are measured or estimated. (b) The baseline clause now holds for Sheu (no control, pretimed) and Dabiri (no control, nominal LQR). Wu's baseline is unknown. 'Usually' generalises from 3 works, 2 of them checked.

### C08 (paper line 67): final verdict **PARTIALLY SUPPORTED**

> An incident-aware meter needs a detection and classification system, which adds delay and errors; research question: how much incident information does a mainline meter need beyond strong always-on feedback?

**Reconciliation:** Matches the protocol question, but "adds delay and errors" is uncited and the answer covers one plant with perfect detection in the main rows.

#### Source: R1 TEXT, verdict PARTIALLY SUPPORTED (basis: direct observation)

- **Meaning.** The paper motivates its study in two steps. A meter that reacts to incidents needs a system that detects and classifies them, and such a system is late and sometimes wrong. So the question is how much incident knowledge (that an incident is on, its type, or full knowledge of each incident) a mainline meter needs on top of good always-on feedback control. This question frames the whole information ladder.
- **Evidence.**
  - papers/paper_1/paper.qmd:67 (no citation on 'adds delay and errors')
  - docs/research/protocols/p1_incident_information.md:5-11 (paper question; robustness to detection imperfections)
  - docs/decisions.md:143 (V124: \citeneeded for AID detection delay), :147 (V128: Background reworded so that no citation is needed)
  - docs/research/results/p1b_result.md:69-76 (one plant; cannot say generality)
- **Verification.** Compared the RQ with the protocol's paper question: they are consistent. Searched the paper for a source on detection delay and errors: there is none, and line 67 still states it as a fact. Checked the scope of the answer: one SUMO plant, 2 demands, 2 incident types (one a substitute), perfect detection in the main rows, given an incident. The protocol also asks about robustness to detection imperfections, and the paper reports only detection delay (see C18).
- **Failure points.** A reviewer may ask for an AID or incident-detection source. 'A mainline meter' is phrased generally but answered for one plant. 'Strong always-on feedback' is unquantified: PI is tuned on grid edges (TEXT-F11).

### C09 (paper line 69): final verdict **VERIFIED**

> One microsimulated bottleneck with a four-lane mainline signal in SUMO [Lopez2018].

**Reconciliation:** One BN4 bottleneck, one signal across 4 lanes, SUMO 1.27.1. The geometry and the FB meter come from Flow / Vinitsky et al. 2018, which is not cited (LIT-F3).

#### Source: R1 PLANT, verdict VERIFIED (basis: direct observation)

- **Meaning.** All experiments use one simulated freeway section with one bottleneck, simulated vehicle by vehicle in SUMO. A single traffic light spans all four lanes of the main road. Lopez2018 is the standard SUMO reference.
- **Evidence.**
  - v5b/d1/netgen_bn4.py@93ba655:22-34 (SPEC: nodes, edges 4/4/4/2/1, node 3 traffic_light); :58-66 connections; :81-83 all-green tlLogic
  - ~/work/phd/v5b1_runs/_netcache/bn4_e578788201/bn4.net.xml: junction 3 type traffic_light, incLanes 2_0..2_3, tl=3 linkIndex 0-3
  - v5b/d1/config.py@93ba655:11 SUMO_BIN venv sumo; toolchain SUMO 1.27.1
  - papers/paper_1/references.bib:92-100 Lopez2018 (ITSC 2018, 2575-2582, doi 10.1109/itsc.2018.8569938)
  - v5b/d1/netgen_bn4.py@93ba655:2 docstring: geometry copied from Flow / Vinitsky et al. (2018), which the paper does not cite
- **Verification.** Read the generator and the cached net.xml (lanes, junctions, tl links). All 344,852 P1b and 1,100 C1 run JSONs carry signal='amber' and the run commit (scan_runs.py, analyze_plant.py).
- **Failure points.** The attribution of the geometry and the meter law to Flow/Vinitsky is missing from the paper (see PLANT-F11). I did not check the bib entry against Crossref.

### C10 (paper line 69): final verdict **VERIFIED**

> Hindsight gains are inflated when the best plan is selected on the same noisy runs used for evaluation [Smith2006; Cameron2016]; so we bracket them between an in-sample and a cross-fitted oracle [vanHasselt2010].

**Reconciliation:** Smith & Winkler 2006, Cameron 2016 and van Hasselt 2010 support the bias argument; their results concern expectations, while the paper reports medians (LIT-F10).

#### Source: R1 LIT, verdict VERIFIED (basis: direct observation)

- **Meaning.** If you pick the best of many noisy results and report that same result, luck makes it look better than it really is. Choosing on separate runs and scoring on the evaluation run removes this optimism but can make the estimate too low. The paper therefore reports both numbers as a bracket.
- **Evidence.**
  - Smith & Winkler 2006 abstract: 'we should expect the value of the chosen alternative to be less than its estimate, even if the value estimates are unbiased'
  - Cameron et al. 2016 full text (author copy cs.ubc.ca/~cchris13/docs/ijcai16_bias.pdf), abstract: 'this flawed notion of VBS tends to show performance better than that achievable by a perfect selector'; the bias 'decreases as we average solver performance over many independent runs per instance'
  - van Hasselt 2010 full text (papers.nips.cc), abstract: 'The obtained double estimator method is shown to sometimes underestimate rather than overestimate the maximum expected value.'
- **Verification.** Read Cameron and van Hasselt in full (pdftotext into /tmp/.../LIT/) and the Smith abstract. Metadata: Smith2006 matches Crossref; Cameron is IJCAI 2016 pp. 712-719 (OpenAlex); van Hasselt is NeurIPS 23 pp. 2613-2621 (OpenAlex; proceedings page title).
- **Failure points.** The cited results concern expectations, while the paper reports medians (finding LIT-F10). They also need the selection runs to be independent of the evaluation run; the paper's replicates use new demand and SUMO seeds, which satisfies this.

### C11 (paper line 69): final verdict **CONTRADICTED**

> All statements were pre-registered before any data were produced.

**Reconciliation:** Each study (P1, P1b, C1) was pre-registered before its own data (page hashes match). But P1b was redesigned after P1 data, C1 (cell, arms, comparator) was fixed after P1b data, and the D1/D2 screens ran first on the same plant and cells. "Before any data" is false as worded (PROV-F1).

#### Source: R1 PROV, verdict CONTRADICTED (basis: direct observation)

- **Meaning.** Every hypothesis test in the paper (S1a, S1b, S2, S3 and the confirmation C1) was written down and approved before any simulation output existed. A reader takes this to mean that no decision about which hypotheses to test was informed by results.
- **Evidence.**
  - P1 data: ~/work/phd/v5b1_runs/p1/v99/run.log lines 1-519 (2026-10-19 18:42 to 2026-10-20 03:17)
  - p1b_addendum.md@75bcd2b:5-9 ('P1 stays in the record as the earlier run ... Why: ... V105 amber necessary; controller-family confound (V103)'), drafted a0144e3 10-20 09:42 after P1 results c2d11c2 03:19 and verification dc7ded8 06:44
  - p1b_confirm_c1.md@7c6acc8:5 and :36 ('the cell and the arms were chosen *after* seeing P1b's evaluation data'); drafted a4e3e6d 21:09:49 after P1b eval (P1B_EVAL_STARTED.json 13:07:53; run.log eval finished 20:28:55)
  - p1_incident_information.md@0e8d49b:133-134 (screens D1/D2 and their numbers were seen; D2 evaluation runs re-analysed by the design review)
  - D2 screen data 10-19 10:24-11:38 (D2_TCHECK_RECORD.json, fac8789) before the P1 protocol draft 14d8866 13:38
  - page hashes: P1 fed27bf6 = p1 page@0e8d49b; P1b 2b3d3ccb = addendum@75bcd2b; C1 8b6005aa = c1 page@7c6acc8 (each before its own study's data)
- **Verification.** Rebuilt the timeline from git commit times, run logs, STARTED/TCHECK records and journalctl. Hashed every protocol version (scratch page_sha.sh). Result: each study's statements were fixed before that study's own data. However, the C1 statement, cell and comparator were fixed after the P1b data had been produced and seen. P1b's design (amber, PI-law plans in A, the rate clip, runner rows) was fixed after P1's data. P1's statements were written after the D1/D2 data on the same plant and cells.
- **Failure points.** True only in a per-study sense ('each study's statements were fixed before that study's data'). The fix is a rewording plus disclosure of the D2 -> P1 -> P1b -> C1 sequence. To check, compare git log times of docs/research/protocols/* with the *_STARTED.json times.

#### Source: R1 recheck (PROV), verdict CONTRADICTED (basis: derived)

- **Evidence.**
  - papers/paper_1/paper.qmd:69 (working tree; last paper commit 4de404a): 'All statements were pre-registered before any data were produced.'; :145 'The protocol, its statements and the seed ranges were fixed and approved before any data were produced'; :187 'The lane-crawl cell at 1600 veh/h was tested once on 100 fresh seeds.' No mention of P1, 'chosen after', 'after seeing' or 'earlier run' anywhere in paper.qmd (grep count 0); Discussion section empty
  - docs/research/protocols/p1b_confirm_c1.md@7c6acc8:5 ('P1b found, in a report-only row, that in cell block_q1600 ... IP beats tuned always-on PI by 18.0 %') and :36 ('Disclosure: the cell and the arms were chosen *after* seeing P1b's evaluation data'); C1 draft a4e3e6d 2026-10-20 21:09:49, approved 7c6acc8 21:11:24; P1b run.log last line 2026-10-20 20:30:10 'done: {S1a: False, S1b: True ...'
  - docs/research/protocols/p1b_addendum.md@75bcd2b:4 (statements S1a/S1b/S2/S3 unchanged from P1 page), :5 ('P1 stays in the record as the earlier run. P1b becomes the paper's main result. Both are reported.'), :9 ('controller-family confound (V103)'); approved 09:51:10 10-20, after P1 run.log end 2026-10-20 03:18:42; docs/decisions.md V103 lists 'controller-family confound (A had no PI-law plans)' as a P1 finding
  - docs/research/protocols/p1_incident_information.md@0e8d49b:19-20 (plant and incidents 'as ported for D1/D2', 'as in screen D2'), :133-134 ('screens D1 and D2 and their numbers were seen ... IP beat N by 10-35 % per cell'; 'the design review re-analysed D2's evaluation runs'); P1 draft 14d8866 2026-10-19 13:38:01 after D2 data ~/work/phd/v5b1_runs/screen_d2/v92/run.log 10:06:39-11:37:03; commit 7da4ab4 message cites 'D2 paired gain 10-35 %'
  - Sentinel page_sha256 equals the sha256 of the page at its approval commit and in the working tree: P1_EVAL_STARTED.json/P1_TCHECK_RECORD.json fed27bf6... = p1 page@0e8d49b; P1B_EVAL_STARTED.json/P1B_TCHECK_RECORD.json 2b3d3ccb... = addendum@75bcd2b; P1B_C1_STARTED.json 8b6005aa... = c1 page@7c6acc8; no protocol commits after 7c6acc8
  - Per-study ordering: P1 page 0e8d49b 10-19 16:32:27 < p1/v99/run.log first line 18:42:22; P1b page 75bcd2b 10-20 09:51:10 < p1b/v108/run.log first line 10:38:07 (code 93ba655 committed 10:17:11); C1 page 7c6acc8 21:11:24 < code e7dd561 21:16:00 < P1B_C1_STARTED.json 21:27:50
  - Headline robustness: p1/v99/run.log and p1b/v108/run.log both end with S1a False, S1b True (same verdicts before and after the post-P1 redesign); Bonferroni level 1-0.05/8 = 0.99375 already in p1 page@0e8d49b:88
  - Further: p1b_result.md:56 ('runs with >= 1 [emergency stop] fell from 87 % to 12.8 %'), where 87 % is the P1 (no amber) rate, used in paper:197 without naming P1; p1b_result.md:64 spill recomputed '(D, V109: tail within 50 m of the entry, or mean depart delay > 5 s)'; V109 (commit 8e10812, 10:38:01) promised only 'recomputed after the run ... (max_queue_m + depart delay)' without thresholds
- **Verification.** Re-check outcome UPHELD: Meaning: paper.qmd:69 says "All statements were pre-registered before any data were produced". Line 145 repeats it: "The protocol, its statements and the seed ranges were fixed and approved before any data were produced". A reader takes this to mean that every tested statement (S1a, S1b, S2, S3 and C1), with its cells and its seeds, was fixed before any simulation output existed. On that reading, no data could have shaped which hypotheses were tested.

The claim holds only if "any data" is read as "that study's own data". I looked for a definition, another reading, or other code or data that would support it. What I found:

(1) The per-study reading holds, with clear margins. P1 page committed 16:32 on 10-19, P1 data from 18:42. P1b page 09:51, P1b data from 10:38:07. C1 page 21:11:24, C1 code 21:16, C1 data 21:27:50. The protocol hashes stored in the run sentinels match each page at its approval commit and in the working tree. No protocol commit follows 7c6acc8.

(2) The literal sentence is false. It fails in at least three places, and the protocol pages themselves admit each one.
- C1's own page says the cell and the arms "were chosen *after* seeing P1b's evaluation data". C1's seeds were approved (V115) after P1b had finished.
- P1b keeps the S1-S3 text from P1, which was fixed before P1's data. But its design was changed after seeing P1's results: amber, PI-law plans added to the action set A, the rate clip, and the runner rows. The reasons given are V103 (from the P1 verification) and V105.
- The P1 page was drafted at 13:38 on 10-19, after the screen D2 data (10:06-11:37) on the same plant, cells and incident types. The page discloses that "screens D1 and D2 and their numbers were seen".

No document in the repo defines "pre-registered" in the per-study sense, and the paper never discloses this sequence. The paper names P1 nowhere and has no phrase like "chosen after" or "after seeing". The Discussion section is empty.

Under the given definitions, the sentence is false as written ("any data"). So CONTRADICTED stands, not PARTIALLY SUPPORTED, which needs the claim to be true but overstated.

Severity: major, not critical. The headline results survive:
- C1 was a single test fixed in advance, on fresh seeds (7,400,700-799), so selecting its cell after P1b is handled by the design.
- The redesign after P1 did not change the S1 verdicts. Both run logs end with S1a False, S1b True.

Fix: reword lines 69 and 145 to the per-study form, and disclose the D2 -> P1 -> P1b -> C1 sequence: P1 was an earlier run without amber, with the same statements and the same verdicts, and the C1 cell was selected after P1b.

Further findings:
- (a) Major: the paper never reports or names P1. The P1b addendum (line 5) says "P1 stays in the record as the earlier run ... Both are reported". Yet paper line 197 uses a P1 number ("87 % (no amber)", source p1b_result.md:56) without saying it comes from P1.
- (b) Major: line 187, "The lane-crawl cell at 1600 veh/h was tested once", leaves out the post-hoc cell selection that C1's page discloses at line 36.
- (c) Minor: the spill share "85-100 %" on line 197 uses a definition (tail within 50 m of the entry, or mean depart delay > 5 s) whose thresholds were set after the P1b data. V109 (commit 8e10812, 10:38:01) promised only a recomputation "max_queue_m + depart delay", and p1b_result.md:64 labels the number (D). The paper does not say that it was defined after the data, or that the pre-registered B4 flag never fired.
- (d) Info: line 145 says "the protocol" (singular), but three pages governed the reported studies (P1, the P1b addendum, C1).

### C12 (paper line 73): final verdict **PARTIALLY SUPPORTED**

> Contribution 1: an information-ladder decomposition for incident-responsive mainline metering against a full set of tuned always-on controllers, including a PI law.

**Reconciliation:** The L0 set is N, FX, FB, PI, AD. PI at q1600 sits on two grid edges and is Pareto-dominated; FX is at the top rate (barely meters); AD is weak; no MPC/MTFC arm. "Full set of tuned" overstates.

#### Source: R1 TEXT, verdict PARTIALLY SUPPORTED (basis: direct observation)

- **Meaning.** The first contribution is a step-by-step comparison. Each extra level of incident information (none, presence, type, full hindsight) is compared with a complete set of well-tuned always-on controllers. That set includes a proportional-integral law in the PI-ALINEA form.
- **Evidence.**
  - paper.qmd:118, 126-136 (Table I), 174-179 (Table II)
  - docs/research/protocols/p1_incident_information.md:29-46 (arms; grid edges 'reported for every arm ... No further extension')
  - docs/research/results/p1b_result.json tune.arms, tune.grid_edges_report_only: q1600 PI=p70_120_8_e4 edges K_P=70, K_I=120; FX=c2600 edge rate=2600; q2000 N=f10_8 edge K_F=10
  - p1b_result.json tcheck.vsl_enters=false (VSL tested, not reported)
  - /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/TEXT/check_paper_numbers.out
- **Verification.** All 24 ladder values in Table II match p1b_result.json (check_paper_numbers.py). The L0 set is N, FX, FB, PI and AD, tuned on 40 seeds over fixed grids. At q1600 the always-on PI sits on two grid edges, and FX is at the top rate (2600), so FX barely meters. The set has no model-based or coordinated controller (MPC, MTFC); CLAUDE.md requires that dropping MPC be disclosed. AD is 'in the spirit of' AD-ALINEA, not its estimator. VSL was tested, did not enter, and is not mentioned. The operating map with NC is not shown.
- **Failure points.** A PI grid extended past K_P=70 and K_I=120 at q1600 could give a stronger PI and shrink S1b and C1 against PI. Reviewers may contest 'full set' without MPC/MTFC. Test: re-tune PI on the P1b tuning seeds over an extended grid (not run here).

### C13 (paper line 74): final verdict **PARTIALLY SUPPORTED**

> Contribution 2: honest bounds on the value of per-incident hindsight under simulation noise, with pre-registered statements, paired seeds and a confirmation on fresh seeds.

**Reconciliation:** The S2 bounds are computed as described, but C1 confirms only IP vs PI, not the bounds; pre-registration holds per study only (C11).

#### Source: R1 TEXT, verdict PARTIALLY SUPPORTED (basis: direct observation)

- **Meaning.** The second contribution: the value of knowing everything about each incident (L2) is not given as one number. It is given as an interval. The upper end comes from an optimistic oracle that picks on the scored run itself (in-sample). The lower end comes from a pessimistic oracle that picks on separate replicate runs (cross-fitted). The statements were fixed in advance, the seeds are paired, and the paper says the results were confirmed on new seeds.
- **Evidence.**
  - docs/research/protocols/p1_incident_information.md:105-110 (S2 rules; x = upper CI of the median rel vs OR_in; y = lower CI of rel_mean vs ORX_4; level 1-0.05/4)
  - p1b_result.json eval.S2.*.statements (x, y; level 0.9875); all 4 cells, plateau failed
  - docs/research/protocols/p1b_confirm_c1.md:17-25 (C1 tests IP vs PI only)
  - paper.qmd:193 ('13.3 %' = P1 value; p1_summary.md:39)
- **Verification.** The S2 brackets in Table II match the JSON. The fresh-seed confirmation (C1) tests IP vs PI, not any L2 bound; no bracket was re-checked on fresh seeds. Pre-registration holds per study (sha256 of the pages match the sentinels), but see TEXT-F1. The paper does not state that the lower bound uses the mean version and the upper the median, nor the 0.9875 level. Line 193 carries a P1 number. 'Honest' is a self-label, and the omissions in TEXT-F2/F7/F8 undermine it.
- **Failure points.** A reader may think C1 confirmed the L2 bracket. The bracket depends on the size of A (120 actions; a larger A inflates OR_in, as addendum B3 says, but the paper does not). Fix: say that C1 confirms only the IP vs PI row.

### C14 (paper line 75): final verdict **PARTIALLY SUPPORTED**

> Contribution 3: the sensitivity of the gains to detection delay and to red-light running at the meter.

**Reconciliation:** d* and the C1 delay/runner rows are correct. "Detection delay" is onset delay only (clearance perfect); the pre-registered c*, p*, f* and combined row are omitted, and they are the unfavourable rows.

#### Source: R1 TEXT, verdict PARTIALLY SUPPORTED (basis: direct observation)

- **Meaning.** The third contribution shows how fast the gains from incident-aware control shrink in two cases: when detection comes late, and when a share of drivers ignores the amber and the first part of the red at the meter.
- **Evidence.**
  - paper.qmd:179 (d* row, no CIs), 187, 197
  - p1b_result.json eval.S3.*.d_star.all_seeds (slow_q2000 120.4 [20.1, 168.5]; slow_q1600 2.6 [0, 7.1]; block_q1600 >240 [192.8, 240])
  - docs/research/results/p1b_c1_summary.md:24-35 (C1 delay and runner rows)
  - p1b_addendum.md:78 (R5: runner rows for every L0 arm, ID and IP); p1b_result.json eval.runner_rows
- **Verification.** The d* values and the C1 rows match the JSONs. The CIs of d* are omitted; slow_q2000's 'about 120 s' has a lower bound of 20.1 s, and P1 gave 25.8 s. Of the pre-registered P1b runner rows, the paper shows only slow_q1600 IP. The clearance delay c*, misclassification p*, false alarm f* and the combined row are missing (TEXT-F7).
- **Failure points.** With its CI shown, the detection-delay tolerance in slow_q2000 is not robust. The runner sensitivity is reported only where it is favourable (C1) plus one fragile row.

#### Source: R2 G5, verdict PARTIALLY SUPPORTED (basis: derived)

- **Meaning.** The paper says it shows how the incident-aware gain changes when detection is late (and with runners). In the code, 'detection delay' is the onset delay d only. The switch starts at t_on+d. Clearance is always detected exactly (c=0) in every d row. Separate pre-registered rows exist for clearance delay c, misclassification p, false alarms f, and a combined row (d=60, c=60, p=0.2).
- **Evidence.**
  - v5b/p1/meters.py@93ba655:203-217 (switch_schedule: t_sw = first tick >= t_on+d; t_bk = first tick >= t_off+c)
  - v5b/p1b/analysis.py@93ba655:40-45 (D_GRID, C_GRID, COMBINED), 223-225 (d rows with c=0; c rows; combined), 540-562
  - p1b_result.json eval.S3.*.c_star / combined_row / clearance_delay_applies (True only for slow_q1600)
  - paper.qmd:179 (only d*), 187, 197; no mention of clearance, combined row, p* or f* in the Results
  - raw runs: slow_q1600 back plan at d=0..120 returns at t_off in 100/100 runs per d (g5_schedules.log)
- **Verification.** Read the code at 93ba655. Recomputed c*, the combined row and d* from raw runs with my own code (g5_recompute.py, g5_dstar_c1.py): all values equal the JSON. Checked the switch and return ticks in every run used (0 mismatches).
- **Failure points.** Onset-delay sensitivity is reported correctly. 'Detection delay' is not qualified as onset only. The pre-registered rows for clearance delay, misclassification, false alarm and the combined row are omitted. The combined row is unfavourable: IP is not ahead of the strongest always-on arm in any cell (G5-F1).

### C15 (paper line 81): final verdict **PARTIALLY SUPPORTED**

> A mainline meter holds traffic upstream with green, amber and red signals across all lanes; feedback laws developed for ramp metering apply directly [Papageorgiou2008; Tympakianaki2014].

**Reconciliation:** "Apply directly" is supported by Papageorgiou 2008 (which also reports tuning was needed). "Green, amber and red" is not: the cited works use green-red signals; the amber is this study's own design.

#### Source: R1 LIT, verdict PARTIALLY SUPPORTED (basis: direct observation)

- **Meaning.** A mainline meter is a set of traffic lights across all lanes that releases vehicles at a controlled rate. The same feedback laws used for on-ramps can drive it. The sentence names an amber phase as part of this standard picture.
- **Evidence.**
  - Papageorgiou 2008 §2.7.1 p. 540: 'This is the central task of the control algorithm that is essentially identical for any kind of merge infrastructure.'
  - Papageorgiou 2008 §3.1 p. 543: 'Each traffic light has a constant green phase of 4 s'; 'The red phase is not allowed to be lower than 2 s'. §4.1 p. 548: the work-zone lights are 'operated as described in Section 3.1'. There is no amber
  - Tympakianaki 2014 abstract: 'green-red traffic signals at the motorway mainstream'; 'an ALINEA-like PI-type feedback regulator'; 'some calibration of the regulator's parameters may be necessary'
  - Sun 2013 abstract: 'a three-section instead of a traditional two-section signal head ... produced significantly higher compliance rates' (a possible source for the amber phase)
- **Verification.** Read Papageorgiou 2008 in full and the abstracts of the other two.
- **Failure points.** 'Apply directly' is supported. 'Green, amber and red' is not: both cited works use green-red signals, and the amber is the paper's own P1b design (finding LIT-F4). 'Apply directly' also hides the tuning that Tympakianaki reports was needed.

### C16 (paper line 81): final verdict **VERIFIED**

> ALINEA integrates the deviation of a downstream measurement from its critical value [Papageorgiou1991]; PI-ALINEA adds a proportional term that helps when the bottleneck is further downstream of the signal [Wang2014].

**Reconciliation:** ALINEA (via the 2008 full text) and PI-ALINEA (Wang abstract plus two secondary full texts) as described.

#### Source: R1 LIT, verdict VERIFIED (basis: direct observation)

- **Meaning.** ALINEA adds up the error between target and measured downstream occupancy over time (integral control). Wang et al. add a proportional term because pure integral control can oscillate when the bottleneck is far downstream.
- **Evidence.**
  - Papageorgiou 2008 §2.7.1 pp. 540-541 (citing Papageorgiou et al. 1991): eq. (1), and 'The regulator (1) apparently integrates (accumulates) the regulation error'
  - Wang 2014 abstract: 'ALINEA may lead to a poorly damped closed-loop behavior in this case, but PI-ALINEA, which is a suitable proportional-integral (PI) extension of ALINEA'
- **Verification.** Full text (secondary source) for ALINEA; abstract for Wang 2014.
- **Failure points.** I did not read Wang 2014's exact equation. Frejo 2021a ref. [21] says PI-ALINEA was first proposed in Wang & Papageorgiou 2006, ITSC pp. 426-431, doi:10.1109/itsc.2006.1706778 (finding LIT-F8).

#### Source: R2 G8, verdict VERIFIED (basis: direct observation)

- **Meaning.** Concept: ALINEA is integral control on the error between target and measured downstream occupancy. Detail: PI-ALINEA adds a P term because pure integral control is poorly damped when the bottleneck is far from the meter.
- **Evidence.**
  - Papageorgiou 2008 full text §2.7.1 pp. 540-541: eq. (1), the 'well-known integral-feedback (I-type) ALINEA regulator (Papageorgiou et al., 1991)'
  - Wang 2014 abstract (LIT/dl_meta/Wang2014.json): 'ALINEA may lead to a poorly damped closed-loop behavior in this case, but PI-ALINEA, which is a suitable proportional-integral (PI) extension of ALINEA, can lead to satisfactory control performance'
  - Frejo 2021a full text (LIT/frejo2021a_raw.txt:128-137): if the bottleneck is far from the on-ramp, ALINEA is 'not always effective'; 'PI-ALINEA was proposed in [21], improving the performance given by ALINEA for a distant bottleneck'
- **Verification.** Checked against Wang's own abstract and two independent full texts. Wang 2014's full text is not reachable (closed; TUC behind Anubis).
- **Failure points.** Neither the ALINEA 1991 primary text nor Wang's body and equations were read. For priority, PI-ALINEA was first proposed in Wang & Papageorgiou 2006 (LIT-F8).

### C17 (paper line 81): final verdict **PARTIALLY SUPPORTED**

> When an incident changes the bottleneck a fixed set point may no longer fit; adaptive schemes estimate it online [Smaragdis2003]; incident-scheduled controllers switch plans or parameters when an incident flag arrives [Dabiri2014].

**Reconciliation:** Smaragdis citation wrong (see C06). Dabiri is continuous gain scheduling on estimated incident parameters, not a plan switch on a flag.

#### Source: R1 LIT, verdict PARTIALLY SUPPORTED (basis: direct observation)

- **Meaning.** There are two ways to cope with a capacity change: let the controller estimate its set point continuously, or switch to different settings once an incident is known. The sentence credits the first to Smaragdis 2003 and the second to Dabiri 2014.
- **Evidence.**
  - Same Smaragdis 2003 and 2004 evidence as C06: the 2003 abstract has no adaptive strategy; the 2004 abstract introduces AD-ALINEA
  - Dabiri 2014 abstract: control 'triggered by available incident parameter values'; the incident parameters 'can be on-line estimated'
- **Verification.** Read the abstracts, and Papageorgiou 2008 in full for how it attributes the estimators.
- **Failure points.** The Smaragdis citation is wrong (LIT-F1); also cite Kosmatopoulos et al. 2006, TRR 1959:65-76, doi:10.1177/0361198106195900108 (Crossref verified). Dabiri schedules on continuous incident parameters estimated online, which is more than a binary 'flag'. The 2004 abstract does not motivate AD-ALINEA by incidents.

#### Source: R2 G8, verdict PARTIALLY SUPPORTED (basis: direct observation)

- **Meaning.** Concept: there are two ways to cope with a capacity change. One estimates the set point continuously; the other changes the controller once the incident is known. Detail: Dabiri is cited for switching plans or parameters on a binary incident flag.
- **Evidence.**
  - Smaragdis evidence as in C06: 2003 has no adaptive strategy; 2004 introduces AD-ALINEA
  - Dabiri 2014 p. 11340 (G8/dabiri2014.txt:168-170): 'we assume that the α and β and consequently θ(α, β) are real-time measured (or estimated)'; the controller is a 'parameter dependent state feedback controller' (gain scheduling, LPV)
  - Dabiri p. 11341 (:349-353): the incident is 'modeled by a change in the incident parameters' (α = 0.3, β = 0.6 from t = 35 min) and then they 'go back to their nominal values'; Remark 3 (:275-281): without parameter reconstruction, a constant robust gain
- **Verification.** Read the Dabiri full text: model, controller design, case study and conclusion.
- **Failure points.** Smaragdis2003 is the wrong citation (G8-F4). Dabiri schedules gains continuously on real-valued incident magnitudes. It switches no plans, and it needs more than a binary flag (closer to knowing the incident's severity). Only in its step-shaped case study does this behave like a switch at incident onset.

### C18 (paper line 85): final verdict **CONTRADICTED**

> We report how long detection may take, and how often the type may be wrong or a false alarm occur, before the gain disappears.

**Reconciliation:** Only the onset-detection break-even d* is reported. The promised misclassification (p*) and false-alarm (f*) results are absent, although they are in p1b_result.json and A10 lists p* and f* as paper outputs. They are unfavourable: in the C1 cell the lead over FB is gone at p = 0.21.

#### Source: R1 TEXT, verdict PARTIALLY SUPPORTED (basis: direct observation)

- **Meaning.** The paper promises three tolerances: how long the detection delay, how high the misclassification rate and how high the false-alarm rate can be before the incident-aware gain is gone. These are the break-even values d*, p* and f* of protocol S3.
- **Evidence.**
  - paper.qmd:145 (S3 reduced to 'break-even detection delays'), :179 (d* only)
  - p1b_result.json eval.S3.*.p_star: slow_q1600 0.13 [0, 0.30] PI; slow_q2000 0.53 [0.21, 0.89]; block_q1600 0.21 [0.12, 0.33] FB; block_q2000 never ahead
  - p1b_result.json eval.per_q.*.prevalence.*.f_star (0.10-0.44); per_q.*.false_alarm_cost (+39.5 s [22.0, 69.6] q1600; +120.4 s [89.7, 147.4] q2000)
  - /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/TEXT/check_paper_numbers.out
- **Verification.** Searched paper.qmd and the pdftotext output of paper.pdf: only d* is reported. p* and f* exist in the JSON but appear nowhere in the paper. In the C1 cell, the lead over FB is gone at 21 % misclassification.
- **Failure points.** The promise is not kept, and the omitted values are the unfavourable ones. Fix: add p*, f* and the combined row with CIs, or drop the promise.

#### Source: R2 G5, verdict CONTRADICTED (basis: direct observation)

- **Meaning.** The paper promises three break-even values: d* (detection delay), p* (misclassification rate) and f* (false-alarm rate). The protocol (A10) also put the clearance delay in the text.
- **Evidence.**
  - paper.qmd:85 (promise), :145 ('S3 reports break-even detection delays'), :179 (d* row only)
  - p1_incident_information.md:112 (S3 = d*, c*, p*, f*(pi) and combined row), :116 (A10: 'One break-even table (d*, p*, f*); the clearance delay in the text'); p1b_addendum.md:4 (everything not changed stays)
  - p1b_result.json S3 p_star: slow_q1600 0.13 PI; slow_q2000 0.53 PI; block_q1600 0.21 FB (0.31 vs PI); block_q2000 never ahead
  - grep of paper.qmd and TEXT/paper_pdf.txt: no p*, f*, c*, false-alarm cost or combined row
- **Verification.** Searched paper.qmd and the PDF text. Read the protocol at 93ba655. Read the p* values per arm from the JSON. I did not recompute p* (round 1 did); I did recompute the combined row and the p=0.2 component.
- **Failure points.** Only the 'how long detection may take' part is delivered, and only for onset detection. The paper contains no misclassification or false-alarm tolerance, so the sentence is false as written for 2 of its 3 items. The omitted values are unfavourable: in the C1 cell, the lead over FB is gone at p=0.21.

### C19 (paper line 85): final verdict **VERIFIED**

> Field evaluations of ramp and work-zone meters report non-compliance at red [TOPS2005; Sun2013].

**Reconciliation:** TOPS 2005 report (full text) and the Sun et al. companion report/thesis report red non-compliance; the cited TRR article itself was not reachable. TOPS2005 bib author is wrong (LIT-F9).

#### Source: R1 LIT, verdict VERIFIED (basis: direct observation)

- **Meaning.** Real drivers sometimes pass ramp meters on red. Two field studies are cited: a permanent ramp-metering evaluation in Madison, Wisconsin, and temporary work-zone meters in Missouri.
- **Evidence.**
  - TOPS 2005 full text (files.topslab.wisc.edu/its/rampmetering/madison_beltline_meter_eval.pdf), §2.4: 'Vehicles that did not stop for a metered red light in an SOV lane constituted an SOV lane violation.'; §3, Tables 3-14 and 3-15: 'For SOV lanes, violations ranged from 0.9% - 9.0%'
  - Sun 2013 abstract: 'The compliance analysis showed that noncompliance could be a major safety issue in the deployment of temporary ramp meters.'
- **Verification.** Downloaded and read the TOPS report (/tmp/.../LIT/tops2005.txt). For Sun 2013 only the abstract was read; the agency copies were blocked (rosap Access Denied; publications.iowa.gov 403).
- **Failure points.** Sun's definition of non-compliance was not read, so 'at red' rests on TOPS alone. The TOPS bib author is wrong (finding LIT-F9).

#### Source: R2 G8, verdict VERIFIED (basis: direct observation)

- **Meaning.** Concept: in the field, some drivers pass metering signals on red. Detail: a permanent ramp-meter evaluation (Madison Beltline) and temporary ramp meters at Missouri work zones both measured this.
- **Evidence.**
  - TOPS 2005 full text (LIT/tops2005.txt:550-551): 'Vehicles that did not stop for a metered red light in an SOV lane constituted an SOV lane violation'; :1333 SOV violations 0.9-9.0 %
  - Sun2013 abstract (TRR): 'noncompliance could be a major safety issue in the deployment of temporary ramp meters'
  - Companion report, Edara, Sun & Zhu, Nov 2012 (G8/edara2012_report.txt, around line 578): a vehicle 'complied with the ramp meter if it went through the signal when the signal display is green'
  - Zhu 2012 thesis (G8/zhu2012_thesis.txt:839): 'If a vehicle passes the signal on red, then it is considered not to be in compliance'
- **Verification.** Read the ROSAP report and the MOspace thesis in full where relevant. The TRR article itself is closed (SAGE; Iowa copy 403; InTrans behind a WAF challenge).
- **Failure points.** The 'at red' definition for Sun2013 comes from the companion report and thesis (same authors, same deployment), not from the TRR article's text. Sun's meters were temporary ramp meters at work zones, not mainline meters. The TOPS2005 bib author is wrong (LIT-F9).

### C20 (paper line 85): final verdict **VERIFIED**

> We model the amber phase explicitly and add red-light runners as a sensitivity row.

**Reconciliation:** Amber state and runner rows exist in code and data (realised runner shares 0.1009 / 0.3011).

#### Source: R1 PLANT, verdict VERIFIED (basis: direct observation)

- **Meaning.** The signal has a real yellow (amber) state, not just green and red. A separate set of runs, reported only as sensitivity rows, adds drivers who ignore amber and early red.
- **Evidence.**
  - v5b/p1b/meters.py@93ba655:29-34 GREEN 6, AMBER 3, STATES y='yyyy'; :41-42 state_of; :127-128 setRedYellowGreenState every tick
  - v5b/p1b/runners.py@93ba655:15-16 RUNNER_JM, SHARES (0.10, 0.30); :39-52 apply_runners
  - raw: p1b/v108 runs with rs=0.1: 2,700 runs; rs=0.3: 2,702; C1: 200 + 200
- **Verification.** Code read. Data: amber crossings occur in metered s=0 runs (5,857,325 in total). Realised runner shares are 0.1009 and 0.3011 (runner_share.py).
- **Failure points.** The runner behaviour in SUMO is broader than the paper describes (see C62 and PLANT-F9).

### C21 (paper line 89): final verdict **VERIFIED**

> In-sample oracle selection is the optimizer's curse [Smith2006] and the virtual-best-solver bias [Cameron2016]; selecting on one set of runs and evaluating on another removes the upward bias at the cost of a downward one [vanHasselt2010].

**Reconciliation:** Full texts of Cameron 2016, van Hasselt 2010 and Smith & Winkler 2006 read; statements concern expectations.

#### Source: R1 LIT, verdict VERIFIED (basis: direct observation)

- **Meaning.** This is the same idea as C10, stated in the Background. A hindsight oracle scored on its own selection runs is optimistic. Scoring the chosen plan on independent runs is pessimistic in expectation.
- **Evidence.**
  - The C10 sources
  - van Hasselt 2010 full text §2: 'The double estimator underestimates because the probabilities P(j = a*) sum to one and therefore the approximation is a weighted estimate of unbiased expected values', which is <= the maximum expected value (lemma)
  - Cameron 2016 proposes the analogous fix: pick each instance's solver by best expected performance, then bootstrap
- **Verification.** Read both full texts.
- **Failure points.** The inequality holds in expectation, not for medians (LIT-F10). 'Removes the upward bias' is right for expectations; equality holds when the variables are iid.

### C22 (paper line 93): final verdict **PARTIALLY SUPPORTED**

> Constant demand q approaches a bottleneck where four lanes reduce to one; a single signal across the four mainline lanes releases vehicles at a commanded rate; the queue is stored upstream on four lanes.

**Reconciliation:** Demand is a constant-rate Poisson stream that stops at 940 s; realised discharge is below the commanded rate (FX 25-46 % lower); on-road storage ends at about 369 m, beyond which the queue is an unlimited insertion backlog; with lane changing off the four lanes are four fixed queues.

#### Source: R1 PLANT, verdict PARTIALLY SUPPORTED (basis: derived)

- **Meaning.** Traffic arrives at a steady average rate. The road narrows from four lanes to one (via two). One signal over all four lanes lets vehicles through at a rate chosen by the controller, and the waiting vehicles queue on the four lanes upstream of the signal.
- **Evidence.**
  - netgen_bn4.py@93ba655:27 edges 4/4/4/2/1
  - p1b/meters.py@93ba655:37-38 cycle_s = max(11, 2*4*3600/q)
  - delay_reference.out: realised discharge / commanded q, medians: q2000 FB/PI/AD/ID/IP 0.96-0.99, FX 0.75; q1600 0.78-0.93, FX 0.54-0.59
  - analyze_plant.out: max queue tail 368.7 m of 410 m; beyond that the overflow becomes insertion backlog (depart delay up to ~44 s median for N at slow_q2000)
- **Verification.** Code read. Realised versus commanded discharge recomputed per arm and cell from the crossings and commanded_mean_vph fields (delay_reference.py).
- **Failure points.** The commanded rate is only an upper bound: realised discharge is 25-46 % lower for FX, because of downstream spillback and short queues. Storage on the road is limited to about 368 m. Beyond that the queue is a virtual, unlimited insertion backlog. With no lane changing, the four lanes act as four independent queues fixed at entry. The demand is Poisson, not constant (see C33).

### C23 (paper line 93): final verdict **PARTIALLY SUPPORTED**

> An incident of random type, onset and duration may occur at the bottleneck.

**Reconciliation:** Onset and duration are random as stated. The type is a design factor (both types run on every seed, analysed per cell), and the crawl acts on lane 4_1 of the 2-lane edge, not on the 1-lane bottleneck.

#### Source: R1 PLANT, verdict PARTIALLY SUPPORTED (basis: direct observation)

- **Meaning.** The scenario contains one incident whose start time and length are random. The paper also says its type is random, and that it happens at the narrow section.
- **Evidence.**
  - v5b/d2/incidents.py@93ba655:34-39 incident_window rng(seed+3301): onset U(t_ctrl0, t_ctrl0+300), duration U(120,480)
  - v5b/p1b/analysis.py@93ba655 cells: every seed is run under both types (slow, block), and results are reported per type cell
  - analyze_plant.out: 320 (seed, type) groups in P1b, 0 with different windows; slow and block share each seed's window
- **Verification.** Code read. Windows recomputed from the raw runs: onset in [40.70, 338.90] and duration in [121.88, 478.15] (analyze_plant.py).
- **Failure points.** The type is a design factor, not a random draw: each seed is run under both types and analysed per type. Within an incident cell the incident always occurs; clean days are a separate cell. 'At the bottleneck' means edge 5 for the slowdown and lane 4_1 of the two-lane edge for the crawl.

### C24 (paper line 93): final verdict **PARTIALLY SUPPORTED**

> The objective is the door-to-door delay per vehicle, including the time spent waiting in the meter queue and at the network entry.

**Reconciliation:** Delay = SUMO departDelay + timeLoss, which does include origin and meter waits. But timeLoss is measured against the incident-reduced speed limit (3-8 s/veh of incident time not counted; <= 0.8 pt effect), and the metric includes the uncontrolled all-green drain after 940 s, which carries 55-106 % of the headline gains (DRAIN).

#### Source: R1 PLANT, verdict PARTIALLY SUPPORTED (basis: derived)

- **Meaning.** Each vehicle's delay is its extra travel time compared with an ideal trip. This includes time stopped at the signal and time waiting to enter the network. The reported number is the average over all vehicles.
- **Evidence.**
  - v5b/p1b/episode.py@93ba655:253-255 delays = departDelay + timeLoss from tripinfo; valid requires all trips
  - SUMO v1_27_1 src/microsim/MSVehicle.cpp:4295-4304 updateTimeLoss uses vmax = myLane->getVehicleMaxSpeed(this); MSLane.h:591 = min(vehMax, myMaxSpeed*speedFactor), where myMaxSpeed is the current (setMaxSpeed-modified) limit
  - delay_reference.out: (mean_time_in_system - delay) minus the same seed's clean value = 3.3-8.2 s/veh of incident travel time not counted; rel shifts by at most 0.8 percentage points (e.g. block_q1600 IP vs PI 18.0 -> 17.5, IP vs ID 22.0 -> 21.6)
  - drain_share.out: 22-56 % of total time in system accrues after control end, in the all-green drain
- **Verification.** Read the SUMO 1.27.1 source (the same version as the toolchain). Recomputed the gap from raw per-run fields, then recomputed rel with own code: point estimates match Table II (-17.9/-1.8/-0.7/-2.1; 16.2/11.8/22.0/0.0; 4.5/7.4/18.0/-2.1).
- **Failure points.** The reference is the time-varying incident speed limit, so travel at the incident speed counts as zero delay. The metric also includes delay accrued after the meter is switched off (an uncontrolled drain). Neither point is stated in the paper.

#### Source: R1 FU1 (FU1-C1), verdict PARTIALLY SUPPORTED (basis: derived)

- **Meaning.** The paper scores each controller by the average extra time per vehicle, counting the wait at the network entry and in the meter queue. A reader would take this to mean door-to-door time minus free-flow time, counted over the whole trip.
- **Evidence.**
  - v5b/p1b/episode.py@93ba655:253-254,271 delay_s = mean over tripinfo of departDelay + timeLoss
  - v5b/d1/episode.py@93ba655:72-79 parse_tripinfo
  - v5b/d2/incidents.py@93ba655:67,69 incidents applied via edge/lane setMaxSpeed
  - episode.py@93ba655:242-251 all-green drain counted in delay
  - FU1/metric_ideal.out: ideal (TIS-delay) clean 44.5 s vs incident 47.8-52.6 s; D' rel 11.7/21.6/17.5/16.1 vs D 11.8/22.0/18.0/16.2
- **Verification.** I read the code at 93ba655 and computed TIS minus delay per run from mean_time_in_system_s and delay_s, on clean days and on incident days of the same seeds. I then recomputed the headline rels on D' = TIS minus the clean-day ideal time (FU1/metric_ideal.py).
- **Failure points.** 1. The meter queue and entry wait are included, as stated. 2. timeLoss appears to be measured against the prevailing, incident-reduced speed limit, so about 3-8 s/veh of incident time is not counted. This is inferred from the data and from general SUMO knowledge; I did not check it in the SUMO 1.27.1 source. 3. 55-92 % of the paired differences accrue in an uncontrolled all-green drain, and the paper does not say so. On the paired comparisons, item 2 changes the rels by ≤ 0.5 points.

### C25 (paper line 95): final verdict **PARTIALLY SUPPORTED**

> Fig. 1 schematic: four lanes reduce to two and then to one; one mainline signal across all four lanes; two incident types (the drawing must match the simulated geometry).

**Reconciliation:** Topology, signal and incident lanes are drawn correctly. Incidents are drawn as local zones although they cover the whole edge or lane; the crawl-lane feed (3_2, 3_3 -> 4_1) is not shown; labels overlap.

#### Source: R1 REPRO, verdict VERIFIED (basis: direct observation)

- **Meaning.** The first figure is a sketch of the simulated road. It should show the same lane counts, the same place for the traffic signal (upstream of the lane drops, across all four lanes) and the same places for the two incident types as the SUMO network and the incident code. 'Not to scale' allows any lengths, but not a different topology.
- **Evidence.**
  - papers/paper_1/figures/fig_plant.py@HEAD:14 edges (0,3,4),(3,6,4),(6,9,4),(9,12,2),(12,15,1); :24 signal at x=6 = end of edge 2; :27 slowdown box on the 1-lane edge; :29 crawl box on the upper lane of the 2-lane edge
  - v5b/d1/netgen_bn4.py@e7dd561:22-34 (nodes 1..6, node 3 traffic_light at x=410; edges lanes 4,4,4,2,1), :58-66 (lane i -> i//2, 2->1)
  - cached net ~/work/phd/v5b1_runs/_netcache/bn4_e578788201/bn4.net.xml parsed: edges 4/4/4/2/1 lanes, lengths 100/310/120/240/135 m; junction 3 traffic_light; connections 2_0..2_3 -> 3_x on tl 3 linkIndex 0-3
  - v5b/p1b/meters.py@e7dd561:29-34 (G 6 s, amber 3 s, red >= 2 s; STATES GGGG/yyyy/rrrr: one state for all 4 lanes)
  - v5b/d2/incidents.py@e7dd561:28-29 (SLOW_EDGE '5' at 5 m/s; BLOCK_LANE '4_1' at 1 m/s), :64-69
  - raw run incident_log e.g. p1b_c1/v114/runs/c1800-p20_20_16_e4_block_q1600_s7400700.json: [[74.0,'on',{'4_1':1.0}],[278.0,'off',{'4_1':23.0}]]
  - v5b/d1/plant.py@e7dd561:20-26 (TLS_ID '3'; lane changing disabled)
- **Verification.** Read the plant, incident and meter code at e7dd561. Parsed the cached network that the runs used (scratch/net_geometry.py). Re-ran fig_plant.py from a scratch copy and rendered it to PNG; it is pixel-identical to the repo PDF. Rebuilt the network with netconvert in scratch; the body is identical to the cache. Checked visually that the drawn topology matches: the signal sits at the edge 2/3 boundary, the 4->2 drop follows a 4-lane edge, the crawl is on lane 1 (the left/upper lane) of the 2-lane edge, and the slowdown is on the 1-lane edge.
- **Failure points.** (1) Cosmetic: the 'queue storage' label overlaps the signal-timing label in the rendered figure. (2) The incident boxes cover only part of each edge, while the code applies the incident to the whole of edge 5 (135 m) and the whole of lane 4_1 (240 m). (3) The figure does not show that, with lane changing disabled, lanes 3_2 and 3_3 can only enter the crawling lane, so about half of the flow must pass at 1 m/s. The drawing is correct, but this mechanism is not visible. (4) The check is valid only for this network hash (bn4_e578788201), which netconvert 1.27.1 reproduces.

#### Source: R2 G2, verdict PARTIALLY SUPPORTED (basis: direct observation)

- **Meaning.** The caption and the drawing should match the simulated net: lanes 4/4/4/2/1, the signal at node 3, the crawl on lane 4_1 (the upper lane when traffic moves in +x), and the slowdown on edge 5.
- **Evidence.**
  - papers/paper_1/figures/fig_plant.py:14, 24, 27-30 (crawl box x 9.4-11.6 of edge 4 = 9-12, upper lane; slowdown box x 12.4-14.6 of edge 5 = 12-15)
  - REPRO/out/fig_plant_repo.png (the rendered repo figure)
  - G2/net_read.out (incidents act on the whole 240-m lane and the whole 135-m edge)
- **Verification.** Read the figure script, viewed the rendered repo figure, and compared it with the parsed net and the incident code.
- **Failure points.** Nothing in the caption is false; the critic's word 'misdescribes' is too strong for the caption. Topology, signal position and incident lanes are drawn correctly. But the drawing shows both incidents as local zones covering about 73 % of an edge, while the code applies them to the whole lane or edge ('not to scale' is disclosed). Neither caption nor drawing shows that lanes 2-3 feed only the crawl lane, or that lane changing is off. In the rendered figure, the 'queue storage' label overlaps the signal label.

### C26 (paper line 99): final verdict **VERIFIED**

> L0: the meter runs one always-on law (a constant rate or feedback), tuned once.

**Reconciliation:** L0 arms run one always-on law, tuned once per q on pooled incident runs (all 5 re-derived from tuning seeds).

#### Source: R1 CTRL, verdict VERIFIED (basis: direct observation)

- **Meaning.** The lowest rung uses no incident information. The meter runs a single control law from the start to the end of the control period and never switches. Its parameters are chosen once, on tuning runs, and then frozen for evaluation.
- **Evidence.**
  - v5b/p1b/analysis.py@93ba655:119-131 fit_fixed (N, FX, FB, PI), :149-154 fit_ad; v5b/p1b/run.py@93ba655:230-247 stage_tune
  - fixed runs: make_spec(g, None, ...) has no post, so there is no switch (analysis.py:67-68)
  - result.json tune.arms (q1600: N c1800, FX c2600, FB f40_10, PI p70_120_8_e4, AD ad0p5_f40_10; q2000: N f10_8, FX c2000, FB f20_12, PI p20_20_14_e4, AD ad0p5_f20_12)
- **Verification.** Read the code at 93ba655. Re-derived every L0 choice from the tuning-seed runs with my own code (retune.py): 5/5 arms match result.json for both q.
- **Failure points.** 'Tuned once' means once per demand level q, and N is tuned on clean days while the others are tuned on incident days. AD's set point adapts online, but it is still one law. Several L0 optima lie on grid edges or are Pareto-dominated (see CTRL-F1 and CTRL-F2), so 'strong' L0 should be qualified.

### C27 (paper line 100): final verdict **VERIFIED**

> ID (presence): the meter knows when an incident starts and ends, and switches to one plan.

**Reconciliation:** ID switches exactly at onset (t_switch = t_on in all 268,854 main switch runs); back plans return at clearance. Conflicts with the line-118 wording (TEXT-F6).

#### Source: R1 CTRL, verdict VERIFIED (basis: direct observation)

- **Meaning.** ID is told the exact onset and clearance times but not the type. At onset it switches from N to one fixed action. The action is the same for both incident types at a given demand level. A 'back' action returns to N at clearance.
- **Evidence.**
  - v5b/p1b/analysis.py@93ba655:134-142 fit_switch: ID = best_by_median over the pooled per['slow'] + per['block'] lists, per q
  - episode.py@93ba655:195-204 switch at t_sw_plan, back at t_bk_plan; p1/meters.py:203-217 switch_schedule
  - result.json tune.arms: ID q1600 = f40_10 (stay), q2000 = p20_20_14_e4 (stay)
- **Verification.** Own re-derivation reproduces ID at both q. From the raw runs: t_switch == t_on in 268,854/268,854 main switch runs, and t_back == t_off in 133,868/133,868 back runs (s3_tp_checks.py).
- **Failure points.** Both chosen ID actions are 'stay', so clearance information is never used in practice. At q1600 ID's plan is FB's own law, and at q2000 it is PI's own law, so ID differs from those L0 arms only by running N before onset (CTRL-F3). The pooled-median rule picks a Pareto-dominated ID at q1600 (CTRL-F1).

### C28 (paper line 101): final verdict **VERIFIED**

> IP (type): the meter also knows the incident type and switches to a plan for that type.

**Reconciliation:** IP picks one plan per (type, q). In block_q2000 IP = ID by construction (identical runs), so IP vs ID = 0.0 there is an identity.

#### Source: R1 CTRL, verdict VERIFIED (basis: direct observation)

- **Meaning.** IP has the same timing information as ID, plus the incident type. At onset it switches from N to the best action for that type at that demand level. Each action is tuned on the tuning runs of that (type, q) cell.
- **Evidence.**
  - v5b/p1b/analysis.py@93ba655:136-138 ip = {inc: best_by_median(per[inc], A_)}
  - result.json tune.arms IP: q1600 slow c1000+back, block p20_20_16_e4; q2000 slow p70_40_8_e4, block p20_20_14_e4
- **Verification.** Own re-derivation (retune.py) matches all 4 IP choices. In block_q2000, IP == ID by construction: identical run keys and identical delays on all 100 evaluation seeds (oracles.py, confound.py).
- **Failure points.** The IP choice in block_q1600 is a near-tie on the tuning seeds (224.74 vs 224.89 s/veh). IP's gain largely comes from type-specific parameters, not from timing (CTRL-F4).

### C29 (paper line 102): final verdict **PARTIALLY SUPPORTED**

> L2: in hindsight the best plan for each individual incident; an upper limit for any incident-aware controller using the same plans; cannot be measured without bias.

**Reconciliation:** OR_in bounds only policies that run N until onset and then take one action of A with perfect timing. Always-on PI beats even OR_in on 5-16 % of seeds, so "an upper limit for any incident-aware controller" is too broad.

#### Source: R1 CTRL, verdict PARTIALLY SUPPORTED (basis: derived)

- **Meaning.** L2 picks, for each incident, the action of A that is truly best for that incident. No controller that chooses one of the same actions at onset can do better on average. L2 can only be estimated: the in-sample oracle is too optimistic, and the cross-fitted oracle is too pessimistic.
- **Evidence.**
  - analysis.py@93ba655:256-276 or_in, orx; every action of A runs N before onset (sw(N, a))
  - oracles.py: always-on PI beats OR_in (the per-seed minimum over all 120 actions) on 8/5/10/16 of 100 seeds (slow1600/block1600/slow2000/block2000); FX, FB and AD also beat it on some seeds
  - split_type_tuned.py: per-type always-on laws beat IP out of sample in 8/8 fold-cells
- **Verification.** Logic check: OR_in <= the main-run delay of every action of A on every seed, so the 'at most' bound is valid for policies that pick from A. Checked against the data with my own code.
- **Failure points.** The bound covers only controllers that run N until onset and then take one action of A with perfect timing. It does not cover incident-aware controllers that run another law before onset (for example PI with switching), switch at other times, or switch more than once. Always-on PI beats even the in-sample oracle on 5-16 % of seeds. The wording 'any incident-aware controller using the same plans' is broader than the construction.

### C30 (paper line 104): final verdict **VERIFIED**

> All comparisons are made given that an incident occurs.

**Reconciliation:** Every evaluation cell contains an incident; clean days are a separate cell.

#### Source: R1 CTRL, verdict VERIFIED (basis: direct observation)

- **Meaning.** The statistics S1, S2, S3 (d*) and C1 use only runs in which an incident happens. Clean-day runs are used only for tuning N, for the false-alarm and prevalence rows, and for clean-day reporting.
- **Evidence.**
  - analysis.py@93ba655:335-400 evaluate loops over INCIDENTS x QS cells only; clean days in clean_and_prevalence (583-633)
  - confirm_c1.py@e7dd561: INC='block', Q=1600
- **Verification.** Read the code. The C1 index holds only block runs (seed_audit.py).
- **Failure points.** The same paper line promises clean-day costs 'reported separately', but the draft reports none. On clean days, always-on PI has about 1.8-2.0x N's delay (81.1 vs 45.4 s/veh at 1600; 301.1 vs 151.6 at 2000; result.json eval.per_q.clean_day). See CTRL-F11.

### C31 (paper line 104): final verdict **PARTIALLY SUPPORTED**

> Always-on controllers tuned on incident runs may pay a cost on incident-free days, which we report separately.

**Reconciliation:** The data exist (clean-day cost vs N: PI +12.0 s/veh at q1600, +151.6 s/veh at q2000) but the paper does not report them, despite "which we report separately".

#### Source: R1 TEXT, verdict PARTIALLY SUPPORTED (basis: derived)

- **Meaning.** Every comparison assumes that an incident occurs. The always-on controllers were tuned on incident runs, so on normal days they can work worse than N, the controller tuned for normal days. ID and IP run N on normal days. The paper says this cost is reported separately.
- **Evidence.**
  - docs/research/protocols/p1_incident_information.md:102 ('The clean-day delay of every arm is printed next to S1'), :103 (prevalence line)
  - p1b_result.json eval.per_q.{1600,2000}.clean_day (medians N 45.4 / 151.6; PI 81.1 / 301.1; FX 227.8 / 388.4)
  - /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/TEXT/clean_day_paired.out
- **Verification.** Paired recomputation from the raw runs, with my own code and B = 20,000; costs vs N in s/veh with 95 % CI. At q1600: PI +12.0 [-0.5, 19.8], FB +85.3, AD +77.9, FX +119.0. At q2000: PI +151.6 [135.3, 163.3], FB +194.9, AD +200.4, FX +174.9. The paper reports none of these, and no prevalence line.
- **Failure points.** 'May pay' understates large costs that are significant at q2000. Once they are reported, the S1a message needs the prevalence qualifier (TEXT-F8). Clean days are bimodal (N at q2000: 75th percentile 245.8 s), so medians alone can mislead.

### C32 (paper line 110): final verdict **VERIFIED**

> Single freeway bottleneck, lanes per edge 4/4/4/2/1; one signal across all four mainline lanes, upstream of the lane drop (mainline metering).

**Reconciliation:** Lanes 4/4/4/2/1; one TLS at node 3 across all four lanes, upstream of both lane drops.

#### Source: R1 PLANT, verdict VERIFIED (basis: direct observation)

- **Meaning.** The road has five sections with 4, 4, 4, 2 and 1 lanes. The single signal sits on the four-lane road, before the road narrows.
- **Evidence.**
  - netgen_bn4.py@93ba655:22-27
  - bn4.net.xml: edge 2 (310 m, 4 lanes) ends at junction 3 (traffic_light); edge 3 is 120 m; zipper junction 4 at x=550; edge 4 is 240 m with 2 lanes; edge 5 is 135 m with 1 lane
- **Verification.** Read the generated net.xml.
- **Failure points.** None for the statement itself. The signal is 160 m upstream of the 4->2 merge and about 440 m upstream of the 2->1 merge.

### C33 (paper line 110): final verdict **PARTIALLY SUPPORTED**

> Demand is constant at q in {1600, 2000} veh/h.

**Reconciliation:** Constant rate, but Poisson arrivals (vehicle count varies by seed), demand stops at 940 s, and 10 % of vehicles are an "av" vType; none of this is stated.

#### Source: R1 PLANT, verdict PARTIALLY SUPPORTED (basis: derived)

- **Meaning.** Vehicles enter at an average rate of 1600 or 2000 vehicles per hour, the same throughout the run.
- **Evidence.**
  - v5b/d1/demand.py@93ba655:38-57 Poisson process (exponential gaps), seeded
  - v5b/p1b/episode.py@93ba655:133 profile [(0, warmup+control, q)] = [0, 940) s
  - plant.py@93ba655:32-38 av_share 0.1, depart_lane random, depart_speed 10
  - demand_check.out: own regeneration gives 0 count mismatches over 345,952 runs; count variance 417 / 528 against Poisson means 418 / 522
- **Verification.** Re-implemented the generator with numpy and compared the counts with the 'generated' field of every run (demand_check.py).
- **Failure points.** The rate is constant but arrivals are random (Poisson): the number of vehicles differs between seeds and replicates (SD about 20). Demand stops at 940 s. 10 % of vehicles are an 'av' vType with speedFactor 1. None of this is in the paper.

### C34 (paper line 110): final verdict **PARTIALLY SUPPORTED**

> Each run has a 40-s warm-up and a 900-s control period, and continues until the network is empty.

**Reconciliation:** Timeline correct, but the paper omits that demand stops and the meter goes all-green at 940 s, so 22-56 % of time in system accrues in an uncontrolled drain; the 40-s warm-up is shorter than a free-flow trip (about 45 s).

#### Source: R1 PLANT, verdict PARTIALLY SUPPORTED (basis: derived)

- **Meaning.** For the first 40 s the signal stays green. A controller then acts for 900 s. After that the simulation keeps running until every vehicle has left.
- **Evidence.**
  - v5b/p1b/episode.py@93ba655:124-125 warmup_s 40, control_s 900, t_drain_max 7200; :153-161 all-green warm-up; :192-230 control loop; :242-244 meter set to all-green at control end; :249 drain
  - analyze_plant.out: 0 undrained runs in P1b, C1 and P1
  - drain_share.out: 22-56 % of TTT after control end (q2000 incident cells 42-56 %)
- **Verification.** Code read. Drain fields recomputed from raw runs (drain_share.py).
- **Failure points.** The paper omits that no vehicles arrive after 940 s and that the meter is off (all-green) during the drain. A large part of the measured delay is therefore produced without control. The 40-s warm-up is shorter than a free-flow trip (about 45 s), so control starts on a partly filled network.

#### Source: R1 FU1 (FU1-C2), verdict PARTIALLY SUPPORTED (basis: direct observation)

- **Meaning.** A run lasts 940 s with control active, then keeps going until every vehicle has left. The sentence does not say what the meter does after 940 s or whether new traffic keeps arriving.
- **Evidence.**
  - v5b/p1b/episode.py@93ba655:133 demand profile [(0, warmup+control, q)]
  - episode.py@93ba655:192-230 control loop until t_ctrl0+900
  - episode.py@93ba655:242-244 plant.set_all_green() at control end; v5b/d1/plant.py@93ba655:46-47
  - episode.py@93ba655:248-249 sim.drain(7200); v5b/d1/sumo_runner.py@93ba655:224-230
  - FU1/drain_audit.out: invalid pairs 0, incident on at 940 = 0 in every pair
- **Verification.** I read the code at the run commits and checked that the working tree is identical. I checked the drained/valid flags and incident_on_at_control_end for all compared runs.
- **Failure points.** The sentence is true as written. It leaves out two facts: demand stops at 940 s, and the meter goes all-green during the drain. The drain carries 55-92 % of the paired gains (FU1-F1), so the omission is material.

### C35 (paper line 110): final verdict **PARTIALLY SUPPORTED**

> Signal cycle: 6 s green, 3 s amber, at least 2 s red; cycle length c(q) = max(11, 28800/q) s (two vehicles per lane per green); commanded rate limited to [200, 2618] veh/h.

**Reconciliation:** Durations and formula correct, but c uses the commanded rate, not the demand q; "two vehicles per lane per green" is a design target (realised discharge 0.54-0.99 of the command). The 200 veh/h floor means 135-s reds on all four lanes (G3R-F1).

#### Source: R1 PLANT, verdict VERIFIED (basis: derived)

- **Meaning.** Each signal cycle shows green for 6 s, amber for 3 s, then red for at least 2 s. The cycle length is set so that two vehicles per lane can pass in each green. The commanded rate is kept between 200 and 2618 veh/h.
- **Evidence.**
  - v5b/p1b/meters.py@93ba655:29-31, 37-38, 41-42, 87-88 (clip to [200, 2618]), 117-129
  - v5b/d1/meter_signal.py@93ba655:24-34 continuous clock (V100)
  - signal_clock_check.out: own re-implementation over random q sequences: amber always 3 s, red >= 2 s; rare 5/7-s greens from floating-point arithmetic after cycle changes; none for constant rates (signal_const_rate.out)
  - analyze_plant.out: commanded_mean_vph range [400, 2600]
- **Verification.** Code read. Own independent clock simulation checked the green, amber and minimum-red durations.
- **Failure points.** Rare plus or minus 1-s green errors (info). 'Two vehicles per lane per green' is the design target; realised discharge can fall below it (C22).

#### Source: R2 G4, verdict PARTIALLY SUPPORTED (basis: direct observation)

- **Meaning.** Concept: the meter releases a fixed batch of vehicles every cycle, and the cycle length sets the release rate. Detail: green 6 s, amber 3 s, red at least 2 s. The cycle is c = 2 x 4 lanes x 3600 / rate, never below 11 s. In the same paragraph (and at line 93) q is the demand, so the text says the cycle follows the demand.
- **Evidence.**
  - v5b/p1b/meters.py@93ba655:12 (docstring c(q) = max(11, 2 M 3600 / q)), :29-31 (GREEN 6, AMBER 3, RED_MIN 2, C_MIN 11, Q_MIN 200, Q_CAP 2618), :37-38 cycle_s(q) = max(C_MIN, 2*M*3600/q), :114-115 cycle() = cycle_s(self.q), :87-88 clip, :124-128 law update then state
  - self.q is the law state (the commanded rate): meters.py@93ba655:57 q0 1500, :75 const plan sets q = rate, :101/108/111 feedback updates, clipped
  - v5b/d1/meter_signal.py@93ba655:24-34 continuous clock
  - paper.qmd:93 and :110 define q as the demand ('Demand is constant at q in {1600, 2000}')
  - G4/clock_check.out: own clock over 3,000 random commanded-rate sequences: every green 6 s, every amber 3 s, red 2-116 s
  - G4/approach_cross_p1b.out: in s = 0 metered runs, 7.8 % (q1600) and 3.5 % (q2000) of stop-line crossings happen during amber
- **Verification.** Read the code at 93ba655. Re-implemented the clock on my own (G4/clock_check.py) and measured the phase durations. Traced which variable cycle() reads.
- **Failure points.** The formula and durations are right, but the variable is not the demand q. It is the commanded rate r (for example, FX with a constant 2600 veh/h at a demand of 1600 gives c = 11.08 s, not 18 s). 'Two vehicles per lane per green' is the design target only: amber is also used for discharge (3.5-7.8 % of crossings), and the realised discharge is below the commanded rate (PLANT delay_reference.out). My clock uses whole-second ticks, so it does not reproduce the rare floating-point 5/7-s greens that PLANT reported.

### C36 (paper line 110): final verdict **PARTIALLY SUPPORTED**

> Lane changing is disabled in this plant, so a lane blockage is represented by a crawling lane.

**Reconciliation:** True of the code, but the crawl is not a faithful blockage: with no lane changes about half the inflow (lanes 3_2, 3_3) is forced through the 240-m crawl lane at about 1 m/s; the protocol itself calls it more severe than a closure.

#### Source: R1 PLANT, verdict PARTIALLY SUPPORTED (basis: direct observation)

- **Meaning.** Vehicles never change lanes. A lane cannot therefore be closed, because vehicles in it could not move out. Instead, one lane is slowed to walking speed.
- **Evidence.**
  - v5b/d1/plant.py@93ba655:25-29 lcStrategic=-1 lcSpeedGain=0 lcCooperative=0 lcKeepRight=0 for both vTypes
  - bn4.net.xml connections 3_2,3_3 -> 4_1 (zipper)
  - v5b/d2/incidents.py@93ba655:5-14 (closure probe: 54 teleports; crawl kept)
  - docs/research/protocols/screen_D2_incidents.md:94 (crawl delay 1.3-2.4 x the closure's)
- **Verification.** Code and net read. Raw incident_log shows 4_1 at 1.0 m/s on and 23.0 m/s off in 160,440 P1b runs.
- **Failure points.** Undisclosed consequences: vehicles that entered on lanes 2-3 (about half, random lane at entry) must cross the 240-m crawl lane at about 1 m/s x speedFactor, roughly 4 min, and cannot avoid it. A review probe found the crawl 1.3-2.4 times more severe than a closure. The 'lane blockage' cells, which include the C1 cell, rest on this representation.

#### Source: R2 G2, verdict PARTIALLY SUPPORTED (basis: direct observation)

- **Meaning.** Both vTypes set lcStrategic=-1, lcSpeedGain=0, lcCooperative=0 and lcKeepRight=0, so vehicles keep their depart lane (random) all the way along. A permission closure would trap vehicles (the D2 probe: 54 teleports), so a 1 m/s crawl on lane 4_1 is used instead. Because of the 3_2/3_3->4_1 connections, the crawl is not a blockage that drivers can avoid: it is a forced 240-m walking-pace pipe for half the inflow. The D2 review found its delay 1.3-2.4 times that of a closure.
- **Evidence.**
  - v5b/d1/plant.py@93ba655:25-29, :32-37
  - route file in REPRO spot dir: both vTypes carry the lc* parameters
  - v5b/d2/incidents.py@93ba655:5-14 ('It is NOT a closure ... more severe than a closure')
  - docs/research/protocols/screen_D2_incidents.md:91-96 (A2: crawl 1.3-2.4 x closure; 'results speak only about that crawl')
  - G2/g2_spot_lanes.out (free-path vs crawl-path flows)
- **Verification.** Read the code and the generated route file. Confirmed the lane partition from the net connections and the depart-lane shares in the spot runs. That lane changes really are zero rests on the lc* settings and on SUMO's documented meaning of lcStrategic=-1 (general knowledge, not checked in the SUMO source). No raw output records lane changes.
- **Failure points.** The sentence is true as a description of the code. 'Represented by' suggests the crawl stands in for a lane blockage, but it behaves differently: drivers cannot leave the lane, half the inflow is forced through it, and the protocol itself calls it more severe than a closure. The protocol's caveat that 'results speak only about that crawl' is not in the paper.

### C37 (paper line 114): final verdict **PARTIALLY SUPPORTED**

> Two incident types act on the bottleneck: a slowdown (speed limit 5 m/s) and a lane crawl (one lane at 1 m/s).

**Reconciliation:** Speeds correct. The slowdown acts on edge 5 (the 1-lane bottleneck); the crawl acts on lane 4_1 of the upstream 2-lane edge 4, so "act on the bottleneck" holds only for the whole merge zone.

#### Source: R1 PLANT, verdict VERIFIED (basis: direct observation)

- **Meaning.** The slowdown lowers the speed limit of the final one-lane section to 5 m/s. The crawl lowers one of the two lanes of the two-lane section to 1 m/s.
- **Evidence.**
  - v5b/d2/incidents.py@93ba655:28-29 SLOW_EDGE '5', 5.0; BLOCK_LANE '4_1', 1.0; :64-69 _apply
  - analyze_plant.out incident_log: ('slow','on','5_0',5.0) x160,930; ('block','on','4_1',1.0) x160,440 (P1b); 1,100 block in C1
- **Verification.** Code read. Read-back speeds counted in all raw runs.
- **Failure points.** The values are speed limits; each vehicle multiplies them by its speedFactor (0.2-2.0). The paper does not say which edge or lane each type uses (edge 5, 135 m; lane 4_1, 240 m).

#### Source: R2 G2, verdict PARTIALLY SUPPORTED (basis: direct observation)

- **Meaning.** Where and how each incident acts. Slowdown: edge.setMaxSpeed('5', 5.0), applied to all of lane 5_0 (135 m), which is the single-lane final bottleneck. Crawl: lane.setMaxSpeed('4_1', 1.0), applied to all of the left lane of the 2-lane edge 4 (240 m), upstream of the final bottleneck. The junction internal lanes (:4_0_*, 40.22 m; :5_0_*, 40.06 m) are not changed. 1 m/s is a speed limit: each human scales it by their speedFactor normc(1,0.2,0.2,2.0), and with no overtaking a platoon moves at its slowest leader's speed. Lanes 3_2 and 3_3 connect only to 4_1, so the crawl lane is the only path for about half the inflow.
- **Evidence.**
  - v5b/d2/incidents.py@93ba655:28-29 (SLOW_EDGE '5', BLOCK_LANE '4_1', 1.0), :64-69 (_apply)
  - ~/work/phd/v5b1_runs/_netcache/bn4_e578788201/bn4.net.xml: 4_0/4_1 240.0 m, 5_0 135.0 m; connections 3_0,3_1->4_0 and 3_2,3_3->4_1; 4_0,4_1->5_0 (G2/net_read.out)
  - v5b/d1/netgen_bn4.py@93ba655:58-66 (lane i -> i//2)
  - v5b/d1/plant.py@93ba655:25-29 (lcStrategic=-1, lcSpeedGain/Cooperative/KeepRight=0), :34 (depart_lane random)
  - incident_log read-back {'4_1':1.0} on / {'4_1':23.0} off in all 12,500 block runs loaded (G2/g2_actions_traj.out)
  - paper.qmd:93 defines 'a bottleneck where four lanes reduce to one'; fig_plant.py:2 itself says 'slowdown on the 1-lane bottleneck; crawling lane on the 2-lane edge'
  - REPRO spot tripinfo: lanes 2-3 share 0.494/0.519/0.494/0.501; crawl-path exits during the incident 0-15 vehicles (0-122 veh/h) (G2/g2_spot_lanes.out)
- **Verification.** Read the incident, plant and net-generator code at 93ba655. Parsed the cached net myself. Counted read-back speeds in the raw runs. Computed per-lane-group flows from the 4 REPRO spot tripinfo files (hashes equal to the raw C1 runs). For the slowdown I checked the code only; PLANT counted its read-backs.
- **Failure points.** The speeds (5 and 1 m/s) are correct. 'Act on the bottleneck' is exact for the slowdown. For the crawl it holds only if 'bottleneck' means the whole 4->2->1 zone (line 93). The crawl acts on one of the two lanes of the upstream 2-lane stage. The sentence leaves out what drives the cell's results: with lane changing off, that lane is the only path for depart lanes 2-3 (about 50 % of vehicles), and it releases only 0-122 veh/h while the incident is on. A reader will picture a local one-lane slowdown that drivers can avoid.

### C38 (paper line 114): final verdict **VERIFIED**

> Onset is uniform in the first third of the control period; duration uniform in 120-480 s.

**Reconciliation:** Onset U(40, 340) s (first third of control), duration U(120, 480) s, recomputed from 420 seed draws.

#### Source: R1 PLANT, verdict VERIFIED (basis: direct observation)

- **Meaning.** The incident starts at a random time in the first 300 s of control, chosen with equal probability. It lasts a random time between 2 and 8 minutes.
- **Evidence.**
  - v5b/d2/incidents.py@93ba655:34-39; p1b/episode.py@93ba655:140 incident_window(seed, warmup_s=40, control_s=900)
  - analyze_plant.out: onset [40.70, 338.90]; duration [121.88, 478.15]; eval mean onset 198.3 (expected 190), mean duration 308.3 (expected 300); t_on - onset in (0.009, 0.997) s; 0 incidents still on at control end
- **Verification.** Code read. Ranges and means recomputed from 320 + 100 seed draws.
- **Failure points.** The incident is applied and removed on the 1-s tick grid (lag under 1 s). The window assumes t_ctrl0 = 40 s exactly, which holds.

### C39 (paper line 114): final verdict **VERIFIED**

> Every controller sees the same incident in a given seed.

**Reconciliation:** Identical incident windows across arms and types on every seed.

#### Source: R1 PLANT, verdict VERIFIED (basis: derived)

- **Meaning.** For a given random seed, every controller faces exactly the same incident timing, so the comparisons are paired.
- **Evidence.**
  - v5b/d2/incidents.py@93ba655:31-39 rng(seed+3301), independent of the arm
  - analyze_plant.out: P1b 320 and C1 100 (seed, type) groups, 0 with more than one distinct (onset, duration, t_on, t_off)
- **Verification.** Grouped every raw incident run by (seed, type) and compared the windows.
- **Failure points.** Only the incident window is shared. Lane draws and other SUMO randomness diverge between arms (stated in the paper at line 141).

### C40 (paper line 114): final verdict **VERIFIED**

> The four evaluation cells are the two incident types at the two demand levels.

**Reconciliation:** Four cells (slow/block x 1600/2000), checked on every S1 run file.

#### Source: R1 S1, verdict VERIFIED (basis: direct observation)

- **Meaning.** The study tests every combination of the two incident types and the two demand levels. Slowdown and lane crawl ('block' in the code), times 1600 and 2000 veh/h, give four cells. Every arm is evaluated on the same 100 seeds in each cell.
- **Evidence.**
  - v5b/p1b/analysis.py@93ba655:35 QS = (1600.0, 2000.0); :338-341 loop over INCIDENTS x QS calling cell_runs
  - result.json eval.cells: slow_q1600, slow_q2000, block_q1600, block_q2000, each n_seeds 100, n_dropped_seeds 0
  - raw files runs/<arm>_<inc>_q<q>_s74006xx.json: incident/q/seed fields match the key for all 3,200 S1 runs; t_on/t_off identical across the 8 arms on every seed
- **Verification.** load_eval.py read every S1 run file and checked the key, commit, seed, incident, q, k, rs, d, c, pre, post, back, sumo/demand seed, signal and drained fields, and that the incident window is equal across arms. Result: 0 problems.
- **Failure points.** None for the statement. The paper's 'lane crawl' is the code's 'block' (lane 4_1 at 1 m/s). A reader comparing with the notes must map the names.

### C41 (paper line 118): final verdict **CONTRADICTED**

> N = the best constant rate on incident-free days.

**Reconciliation:** At q2000 N is f10_8, an integral-feedback law; "best constant rate" holds only at q1600 (c1800).

#### Source: R1 CTRL, verdict CONTRADICTED (basis: direct observation)

- **Meaning.** The paper says the base arm N is the constant metering rate with the lowest delay on clean days. N is also the controller that ID and IP run before onset.
- **Evidence.**
  - analysis.py@93ba655:124 'N': fam.best_by_median(none, G_) over all of G (20 constant + 30 feedback laws)
  - result.json tune.arms['2000'].N = 'f10_8' (integral feedback, K_F=10, n_crit=8); q1600 N = 'c1800'
  - protocol p1_incident_information.md §2: N = 'Best of G on no-incident tuning runs'
- **Verification.** Own re-derivation: at q2000 the clean-day best of G is f10_8 (144.67 s/veh), ahead of c1700 (146.91).
- **Failure points.** At q=2000, N is a feedback law, not a constant rate. The text should say 'the best constant-rate or feedback meter of G on incident-free days'.

#### Source: R1 recheck (CTRL), verdict CONTRADICTED (basis: derived)

- **Evidence.**
  - papers/paper_1/paper.qmd:118 'the best constant rate on incident-free days (N)'; the PDF has the same text (pdftotext line 66). The only other mention of N is in Table I (qmd:130), and no other part of the paper says what N is at q=2000.
  - v5b/p1b/analysis.py@93ba655:124 'N': fam.best_by_median(none, G_) is taken over all of G, while :125 FX is limited to fam.CONST and :126 FB to fam.FEEDBACK. No diff to HEAD.
  - v5b/p1/family.py@93ba655:21-26: G = CONST (20 rates) + FEEDBACK (5 K_F x 6 n_crit = 30). best_by_median at :110-118 picks the lowest median and breaks ties by G order.
  - docs/research/protocols/p1_incident_information.md:31: N = 'Best of G on no-incident tuning runs, per q (as D2)'. The paper's wording is narrower than the protocol.
  - docs/research/results/p1b_result.json: tune.arms.1600.N = c1800; tune.arms.2000.N = f10_8; eval.table1_operating_map.slow_q2000 and block_q2000 controllers.N = f10_8. docs/research/results/p1b_summary.md:21 'q = 2000: N f10_8, ... FB f20_12'.
  - Derived from raw ~/work/phd/v5b1_runs/p1b/v108/runs/<g>_none_q<q>_s<seed>.json on tuning seeds 7400300-339, 40 runs per law: q1600 best of G = c1800 44.74 s/veh (rank 1); q2000 best of G = f10_8 144.67 s/veh, best constant c1700 146.91 (rank 2, +1.55 %).
  - Derived from the f10_8 meter_log [t, n, q] at q2000: the rate starts at 1500 and reaches a median maximum of 1845. Median range is 400 veh/h (min 270) with about 19 changes per run on incident-free tuning runs. Before onset in the evaluation incident runs, the median range is 130 veh/h (max 320). Seed 7400300: n 2 to 8 gives q 1500 to 1560, which is integral feedback, not a constant rate.
  - Context: in P1 (p1_result.json tune.arms) N = c2000 at q1600 and c1800 at q2000, both constants. In C1 (p1b_c1_result.json frozen_arms.N) N = c1800. The paper's wording fits those runs but not the P1b q2000 cells that the paper reports.
- **Verification.** Re-check outcome UPHELD: Meaning: paper.qmd:118 (the PDF has the same text) defines N as "the best constant rate on incident-free days". The sentence sets N beside FX ("the best constant rate tuned on incident runs") and FB (integral feedback), so a reader takes N to be an open-loop constant rate. N is also the law that ID and IP run before onset.

What ran: v5b/p1b/analysis.py@93ba655:119-126 (fit_fixed). N is fam.best_by_median(none, G_), taken over all of G. FX is limited to fam.CONST and FB to fam.FEEDBACK, but N has no such limit. G (v5b/p1/family.py@93ba655:21-26) holds 50 laws: 20 constant rates and 30 integral-feedback laws named f<K_F>_<n_crit>. The protocol says the same thing: p1_incident_information.md:31 defines N as 'Best of G on no-incident tuning runs, per q'. So the code follows the protocol, and only the paper's wording is wrong. The working tree does not differ from 93ba655 in analysis.py or family.py.

My own recomputation from the raw runs used no v5b imports, the 40 tuning seeds 7,400,300-339, incident = none, and 40 runs for each of the 50 laws. At q=1600, N = c1800 (44.74 s/veh), a constant rate, so the sentence holds there. At q=2000, N = f10_8 (144.67 s/veh). The best constant, c1700 (146.91), is 2.24 s/veh or 1.55 % worse. These values match p1b_result.json tune.arms.2000.N, eval.per_q.2000.controllers.N, eval.table1_operating_map.{slow,block}_q2000.controllers.N and p1b_summary.md:21.

Ways to save the claim, and why each fails:
(1) 'f10_8 is in effect a constant rate.' It is not. Its meter_log rises from q0 = 1500 to about 1845 veh/h. On the incident-free tuning runs the median range is 400 veh/h (the smallest is 270), with about 19 rate changes per run. Before onset in the q=2000 evaluation incident runs, the median range is 130 veh/h, up to 320. One sample step: n goes from 2 to 8 and q from 1500 to 1560, which is integral action with K_F = 10.
(2) 'Another reading of constant rate.' Nothing in the paper supports one. The only other mention of N is in Table I (line 130), and no other part of the paper says that N at q=2000 is a feedback law. Line 99 says that an L0 law may be 'a constant rate or feedback', but line 118 then defines N narrowly.
(3) 'Other data.' In P1, the round without amber, N was a constant at both demand levels (c2000 and c1800). C1 also uses N = c1800. That probably explains where the wording came from. But the paper reports P1b (it has amber and four cells), and in P1b the q=2000 N is f10_8.

Severity: major. The statement is false as written for 2 of the 4 evaluation cells. In those cells it misdescribes the comparison arm N and the controller that ID and IP run before onset, which is itself a feedback law there (FB is a different law, f20_12). The headline numbers are not affected, because the code and the protocol agree. Suggested fix: 'the best meter of G (constant rate or integral feedback) on incident-free days (N; c1800 at 1600 veh/h, f10_8 at 2000 veh/h)'.

### C42 (paper line 118): final verdict **VERIFIED**

> FX = the best constant rate tuned on incident runs.

**Reconciliation:** FX = c2600 at q1600 (top of the grid, barely meters) and c2000 at q2000.

#### Source: R1 CTRL, verdict VERIFIED (basis: direct observation)

- **Meaning.** FX is the single constant metering rate with the lowest median delay over the pooled slow and crawl tuning runs at a demand level.
- **Evidence.**
  - analysis.py@93ba655:125 FX = best_by_median(pooled, CONST)
  - result.json: FX q1600 c2600, q2000 c2000; tune.grid_edges_report_only['1600'].FX = ['rate=2600']
- **Verification.** Re-derived: c2600 (303.9) ahead of c2400 (306.2) at q1600; c2000 (495.6) ahead of c2100 (498.2) at q2000.
- **Failure points.** At q1600, FX sits at the top of the rate grid, next to the 2618 cap, so it is nearly unmetered. The constant-rate surface is flat and non-monotone (top three are c2600, c2400, c2100).

### C43 (paper line 118): final verdict **VERIFIED**

> FB = an integral feedback law on the downstream vehicle count in the style of ALINEA [Papageorgiou1991].

**Reconciliation:** Integral law on the edge-4 vehicle count (a 0.5-s snapshot, not a period average) = ALINEA form of Papageorgiou 2008 eq. (1). The edge-4 count includes the crawl lane (G2-F2).

#### Source: R1 CTRL, verdict VERIFIED (basis: direct observation)

- **Meaning.** FB raises or lowers the metered rate in proportion to the gap between a target vehicle count and the measured count on the two-lane section downstream of the meter, updated every 30 s. This is the I-type ALINEA structure with a vehicle count in place of occupancy.
- **Evidence.**
  - v5b/p1b/meters.py@93ba655:150-151 q = clip(q + K_F (n_crit - n), 200, 2618); episode.py:147-150 n = ls.edge.getLastStepVehicleNumber('4') at the 30-s tick (snapshot)
  - Papageorgiou et al. 2008 TR-C 16:535-553 (papers/refs_papers/1-s2.0-S0968090X07000873-main.pdf) §2.7.1 eq.(1): q(k)=q(k-1)+K_R[o_hat - o(k-1)], T in [20,60] s, 'or the latest measurements or estimates of vehicle-number N'; toll-plaza example uses N, T = 30 s
- **Verification.** Read the code and compared it with eq. (1) of the local full text: same form, with a vehicle-number measurement as the 2008 paper allows.
- **Failure points.** The measurement is a single-step snapshot, not an interval average. The cited 1991 paper is on-ramp and occupancy-based; the 2008 paper, which is in the .bib, matches the count-based mainline version better. The FB gain grid tops at 120 veh/h per vehicle, whereas the 2008 example found K_R >= 300 h^-1 virtually equivalent (§3, Fig. 7 discussion); plant scales differ, so this is indicative only.

### C44 (paper line 118): final verdict **PARTIALLY SUPPORTED**

> PI = a PI law in the form of PI-ALINEA [Wang2014], as used for mainstream signals at lane drops [Tympakianaki2014].

**Reconciliation:** Code matches the PI-ALINEA velocity form with counts; Wang 2014's own equation not read. The PI optimum at q1600 is on two grid edges and Pareto-dominated (CTRL-F2).

#### Source: R1 CTRL, verdict PARTIALLY SUPPORTED (basis: direct observation)

- **Meaning.** PI adds a proportional term on the change in the count to FB's integral term. It is tuned over 180 combinations of gains, set point and detector edge, and pooled over both incident types.
- **Evidence.**
  - meters.py@93ba655:152-155 q = clip(q - K_P*dn + K_I*(n_crit - n)); family.py@93ba655:30-35 grid
  - result.json PI q1600 p70_120_8_e4 (grid_edges: K_P=70, K_I=120), q2000 p20_20_14_e4 (K_P=20)
  - pi_surface.txt: at q1600, n_crit=8, the K_P=70 row decreases monotonically toward K_I=120 (289.7, 259.3, 227.1, 214.4, 210.1) and the K_I=120 column decreases toward K_P=70 (234.1, 222.8, 210.1)
- **Verification.** The code form matches PI-ALINEA's r(k)=r(k-1)-K_P[o(k)-o(k-1)]+K_I[o_hat-o(k)] with counts. The literature part (Wang2014 form, Tympakianaki2014 usage) was not checked by me: no full text, no web.
- **Failure points.** The q1600 optimum sits on two upper grid edges, and the surface still decreases there, so the optimum may lie outside the grid. It is also Pareto-dominated by 6 PI laws on the per-type tuning medians (CTRL-F2). The Tympakianaki usage claim is unverified here.

#### Source: R2 G8, verdict PARTIALLY SUPPORTED (basis: direct observation)

- **Meaning.** Concept: the PI arm is the standard proportional-integral extension of ALINEA. Detail: q(k) = q(k-1) - K_P (n(k) - n(k-1)) + K_I (n_crit - n(k)) on a downstream vehicle count; the same law family was used for mainline work-zone signals.
- **Evidence.**
  - Code: v5b/p1b/meters.py@93ba655:111 'self.q = self._clip(self.q - self.K_P * dn + self.K_I * (self.n_crit - n))'; header :7
  - Frejo 2021b full text eq. (4) (LIT/frejo2021b_raw.txt:1252), the PI-ALINEA/MTFC velocity form from Carlson 2014: q(k-1) + (K_P + K_I) e(k) - K_P e(k-1). This equals the code's form with e = n_crit - n
  - Wang 2014 abstract: 'a suitable proportional-integral (PI) extension of ALINEA'
  - Tympakianaki 2014 abstract: 'green-red traffic signals at the motorway mainstream'; 'ALINEA-like proportional-integral (PI-type) feedback regulator'; work-zone lane drop
- **Verification.** Read the code at the run commit. Expanded Frejo's eq. (4) by hand and compared it with the code. Read both abstracts. Neither the Wang nor the Tympakianaki full text is reachable.
- **Failure points.** The citation part is supported by abstracts plus a secondary full-text equation; Wang's own equation was not read. The code feeds a 0.5-s count snapshot, not a period-averaged occupancy (LIT-F5). Tympakianaki notes that calibration was needed. The round-1 CTRL issue (PI optimum on the grid edge) was not re-checked here.

### C45 (paper line 118): final verdict **PARTIALLY SUPPORTED**

> AD = FB with an online set point in the spirit of AD-ALINEA [Smaragdis2003].

**Reconciliation:** AD is the study's own sign-rule hill-climb, not AD-ALINEA's estimator (the protocol says so, the paper does not); the citation is the wrong Smaragdis paper; tuned eta at the grid edge; AD is worse than FB on tuning seeds.

#### Source: R1 CTRL, verdict PARTIALLY SUPPORTED (basis: direct observation)

- **Meaning.** AD is FB whose target count moves up or down every 30 s by a sign rule on changes in network outflow and in the count, so the meter can hunt for the count that maximises flow.
- **Evidence.**
  - meters.py@93ba655:134-146; protocol p1_incident_information.md §2 AD row: 'in the spirit of AD-ALINEA (Smaragdis et al. 2004 [VERIFY]; not its estimator)'
  - references.bib Smaragdis2003 = 'Series of New Local Ramp Metering Strategies', TRR 1856 (2003)
  - retune.json AD_gap: q1600 eta 0.5/1/2 = 251.3/300.0/303.6 vs FB f40_10 223.4; q2000 411.7/439.9/478.1 vs FB 395.7
- **Verification.** Read the code and the protocol. The sign-rule hill-climb is not AD-ALINEA's estimator, which the protocol itself states. On the tuning seeds, AD is worse than its own eta -> 0 limit (FB) at both q.
- **Failure points.** The paper does not say the estimator differs. The citation year is inconsistent between the protocol (2004) and the paper (2003). I believe AD-ALINEA is from Smaragdis, Papageorgiou & Kosmatopoulos 2004 (TR-B), but I cannot verify this here. AD is a weak L0 arm: tuned eta sits at the lowest grid edge, 0.5.

### C46 (paper line 118): final verdict **PARTIALLY SUPPORTED**

> ID knows only that an incident has started; IP also knows its type. Both run N before the incident and then switch to an action from a set A of 120 actions: 50 constant-rate and integral-feedback plans plus the 10 best PI-law plans, each either kept to the end or released back to N when the incident clears.

**Reconciliation:** 120 actions confirmed. "ID knows only that an incident has started" contradicts line 100 and Table I (back actions use clearance). The "10 best PI-law plans" are the 10 best always-on PI controllers on tuning seeds, not the best as plans.

#### Source: R1 CTRL, verdict PARTIALLY SUPPORTED (basis: direct observation)

- **Meaning.** The plan menu is the 50 controllers of G (20 constant, 30 FB) plus 10 PI laws, each in a 'stay' and a 'back' version, which makes 120 actions. ID and IP choose from it at onset. Before onset they always run N.
- **Evidence.**
  - p1b/family.py@93ba655:23-26 actions = fam.actions(G) + fam.actions(G_PI); p1/family.py:21-28 (20+30); result.json tune.A_size = {1600:120, 2000:120}
  - run.py@93ba655:219-223 gpi_select uses FIXED (always-on, t=0) PI runs pooled over slow+block on the tuning seeds; family.top_pi:37-43
  - G_PI(1600) = [p70_120_8_e4, p20_40_10_e4, ...], G_PI(2000) = [p20_20_14_e4, ...] (differ per q)
- **Verification.** Counted 120 unique actions per q from my own grid (retune.py). Re-derived G_PI from the tuning seeds (match). t_switch == t_on and t_back == t_off in all raw runs.
- **Failure points.** 'ID knows only that an incident has started' contradicts C27 and Table I: back actions give ID the clearance time too. The '10 best PI-law plans' are the 10 best always-on PI controllers per q, ranked by pooled median on the tuning seeds, not the 10 best as plans. 'Kept to the end' means to the end of the 900-s control period; after that every arm drains unmetered.

### C47 (paper line 118): final verdict **VERIFIED**

> All arms are tuned on 40 tuning seeds; detection is perfect in the main rows.

**Reconciliation:** 40 tuning seeds 7,400,300-339; switches exactly at onset in main rows. Law plans act on a 30-s update grid (lag 1-29 s); no bias found (G3R-F3).

#### Source: R1 CTRL, verdict VERIFIED (basis: direct observation)

- **Meaning.** Every tuned choice (N, FX, FB, PI, AD, G_PI, ID, IP) uses the same 40 seeds, which are separate from the evaluation seeds. In the main results the plan starts exactly at the onset tick and a back plan ends exactly at the clearance tick.
- **Evidence.**
  - run.py@93ba655:51-52 SEEDS tune 7,400,300-339; :509 stage_tune(seeds['tune']); retune.json n_tune_seeds_per_action = 40 for every action
  - s3_tp.json: main_t_switch_ok 268,854/268,854; main_back_ok 133,868/133,868
  - run-file mtimes: tune 11:03:11-13:07:52, eval 13:07:56-20:28:55, sentinel 13:07:53 (PDT)
- **Verification.** Own re-derivation from tuning-seed runs alone reproduces every choice. Checked mtimes. Checked the switch ticks on all raw runs.
- **Failure points.** N uses the 40 clean-day runs, while the others use 80 pooled incident runs or 40 per type. 'Perfect detection' still leaves up to 30 s of response lag for FB and PI plans, because the law updates on the 30-s grid anchored at control start (meters.py:167-169).

### C48 (paper line 130): final verdict **VERIFIED**

> Table I: L0 = N, FX, FB, PI, AD use no incident information; L1a ID uses incident onset (and clearance); L1b IP uses onset, clearance and type; L2 OR_in, ORX_R = full per-incident hindsight (bounds).

**Reconciliation:** Matches code and data, apart from the ID-knowledge wording conflict (C46).

#### Source: R1 CTRL, verdict VERIFIED (basis: direct observation)

- **Meaning.** Table I lists which run-time incident information each arm uses.
- **Evidence.**
  - analysis.py@93ba655:236-253 cell_runs (L0 fixed, ID/IP switch runs), 256-276 OR_in/ORX
  - result.json tune.arms; replicate runs share the incident window (oracles.py: 0 mismatches)
- **Verification.** Read the code and checked it against the raw runs.
- **Failure points.** All arms know the demand level (tuned per q). L0 arms are tuned on the 50/50 incident mix, an implicit prior. OR_in also exploits the main run's noise and demand draw, which is more than 'per-incident' hindsight.

### C49 (paper line 141): final verdict **VERIFIED**

> OR_in picks, for each seed, the best action of A on the evaluated run itself; it is optimistic because noise makes some actions look better by chance.

**Reconciliation:** Recomputed exactly; optimistic by construction (minimum over 120 runs per seed).

#### Source: R1 CTRL, verdict VERIFIED (basis: derived)

- **Meaning.** For each evaluation seed, OR_in takes the lowest delay among the 120 actions' main runs on that same seed. Because it chooses and scores on the same noisy run, its expected delay is below that of the truly best action (E[min] <= min E).
- **Evidence.**
  - analysis.py@93ba655:256-263 or_in = argmin_tie over the main runs
  - oracles.json OR_in median rel CI upper bounds: 47.78/25.55/19.29/22.37 % vs result.json x = 47.87/25.43/19.30/22.35 %
- **Verification.** Recomputed with my own code and bootstrap (B=20,000, level 1-0.05/4). Differences only from the bootstrap RNG.
- **Failure points.** Valid only over A, which has N before onset (see C29).

### C50 (paper line 141): final verdict **VERIFIED**

> ORX_R picks the action with the best mean over R in {1,2,4} independent replicate runs (new demand and simulator seeds, same incident) and scores it on the evaluated run; this yields a bound that is low in expectation.

**Reconciliation:** Recomputed exactly (ORX_1/2/4, replicate seeds disjoint, incident fixed). "Low in expectation" holds for the mean version used; the paper reports medians elsewhere (LIT-F10).

#### Source: R1 CTRL, verdict VERIFIED (basis: derived)

- **Meaning.** The action is chosen on separate replicate simulations of the same incident with new arrivals and new SUMO seeds, then scored on the evaluation run. Selection noise is independent of the scoring run, so the expected delay of the chosen action is at least that of the truly best action, which makes the gain biased low.
- **Evidence.**
  - analysis.py@93ba655:266-276 orx (reps[:R], mean, argmin_tie, main[i]); p1/meters.py@93ba655:233-239 replicate_seeds: sumo = demand = seed + k*1e7, window from seed
  - oracles.json: replicate_seed_rule_violations 0, incident_window_mismatches 0; ORX_4 mean lower CI -0.37/0.67/-2.44/3.55 vs result.json y -0.40/0.44/-2.43/3.52 %
  - seed_audit.json: replicate seeds 17,400,600-47,400,699 do not overlap any other study
- **Verification.** Read the code, checked seeds and windows on all raw runs, and recomputed ORX_1, ORX_2, ORX_4.
- **Failure points.** 'Low in expectation' holds for the expected delay. The reported y is a ratio of means, so it is only approximately bounded. y in block_q1600 is close to 0 and depends on the bootstrap seed (0.44 vs 0.67).

### C51 (paper line 141): final verdict **PARTIALLY SUPPORTED**

> The placebo TP picks the best of five replicate runs of IP itself and shows the size of pure-noise gains.

**Reconciliation:** TP is best of the main run plus 4 replicates with demand redrawn; it partly exploits luck in the arrival draw, and is best-of-5 vs OR_in's best-of-120 with shared demand. Not a matched placebo.

#### Source: R1 CTRL, verdict PARTIALLY SUPPORTED (basis: derived)

- **Meaning.** TP takes IP's main run and its 4 replicates of the same incident, keeps the lowest delay per seed, and reports how much 'gain' this selection alone produces with no change of controller.
- **Evidence.**
  - p1/stats.py@93ba655:145-149 tp_placebo: best = min(main, reps.min); analysis.py:370-372 (rmax = 4 replicates)
  - s3_tp.json: the run TP picks has fewer generated vehicles than the main run (median -10.5/-10.5/-7.5/-15.5 vehicles, block1600/slow2000/slow1600/block2000)
  - oracles.json TP rel 37.65/13.58/16.77/15.71 % matches result.json
- **Verification.** Recomputed TP. Checked which run is picked and its 'generated' count.
- **Failure points.** The five runs are the main run plus 4 replicates. The replicates redraw demand, so TP exploits luck in the arrival draw (fewer vehicles). OR_in cannot do this, because all its 120 runs share one demand file. TP is best-of-5 while OR_in is best-of-120. TP is therefore not a matched null for OR_in's simulation-noise inflation (CTRL-F6).

### C52 (paper line 141): final verdict **PARTIALLY SUPPORTED**

> In SUMO a change of controller also changes later random draws, so paired runs with equal seeds do not share common random numbers.

**Reconciliation:** 4 spot re-runs (2 seeds): equal seeds give identical vehicle streams until the controller changes insertion times (spillback); then the draws desynchronise. "A change of controller changes later random draws" is too general, and no evidence for "we found" is documented.

#### Source: R1 CTRL, verdict UNVERIFIED (basis: assumption)

- **Meaning.** SUMO's own randomness (here the vType speedFactor normc(1,0.2,0.2,2) and departLane='random') is drawn from per-lane RNG streams. A different signal command can shift later draws, so two arms on the same seed are not perfectly paired.
- **Evidence.**
  - docs/research/prior_art_P1_P2.md:34 '(agent read the source): MSBaseVehicle::getRNG() uses the current lane's RNG from a shared pool'
  - v5b/d1/plant.py@93ba655:28,34 speedFactor normc and depart_lane='random' (SUMO RNG draws)
  - no empirical test found in the repo (grep 'common random' / 'CRN' over docs, results, decisions)
- **Verification.** Searched the repo. No SUMO run is allowed under the audit rules. A SUMO source tree exists at /home/catalin/work/phd/phd_speed_harmo_v6_toolchain/sumo-src (MSBaseVehicle.cpp); I did not open it, because it sits under the v6 toolchain (boundary).
- **Failure points.** 'We found' implies an empirical finding, but the only basis is an agent's reading of the source, with no file or line or SUMO version recorded. Test: two runs with the same seed whose controllers differ only after time T; compare per-vehicle speedFactor and departLane for vehicles inserted after T (needs tripinfo or vehicle output).

#### Source: R1 REPRO, verdict PARTIALLY SUPPORTED (basis: derived)

- **Meaning.** Common random numbers (CRN) means that two arms run with the same seed see exactly the same random vehicle stream, so their difference reflects only the controller. The paper says SUMO breaks this as soon as the controller changes. The check: is the realised vehicle stream (insertion lane, desired-speed factor, departure time) identical across IP and PI for the same seed, and if not, where does it split?
- **Evidence.**
  - docs/research/prior_art_P1_P2.md:34 (the source of the claim: 'agent read the source', MSBaseVehicle::getRNG; no measurement cited)
  - v5b/d1/plant.py@e7dd561:32-38 (departLane='random', speedFactor normc(1,0.2,0.2,2.0): both drawn by SUMO)
  - scratch spot runs, tripinfo: seed 7400700 IP vs PI: 0/403 vehicles differ in departLane, speedFactor, depart, departDelay (controllers differ from t=40 s; meter_log q 1800 vs 1500)
  - seed 7400760 (PI queue reaches the entry; PI max departDelay 93.5 s): the first difference is main.226 at 475 vs 476 s (an insertion delay); 166/445 departLane differ; 21 of the 23 vehicles inserted on time in both arms after 475 s got different lanes; 1 speedFactor differs
- **Verification.** Ran the 4 C1 spot runs with --keep-files. scratch/crn_check.py and scratch/crn_check2.py compare route files and per-vehicle tripinfo attributes between IP and PI for each seed.
- **Failure points.** Only 2 seeds were tested, and only attributes visible in tripinfo (lane, speedFactor at 2 decimals, depart). Hidden RNG uses cannot be ruled out, but none showed up in seed 7400700. As written ('a change of controller ... changes later random draws'; 'do not share CRN') the claim is too general: CRN held exactly while insertion was unaffected and broke after the first controller-induced insertion delay. Test: run more seed pairs; count the runs whose insertion timing differs between arms (queue at the entry) and compare with the spill shares (C1 PI 0.32; 85-100 % of metered runs at 2000 veh/h).

### C53 (paper line 145): final verdict **CONTRADICTED**

> The protocol, its statements and the seed ranges were fixed and approved before any data were produced.

**Reconciliation:** As C11: true study by study, false as worded.

#### Source: R1 PROV, verdict CONTRADICTED (basis: direct observation)

- **Meaning.** The study plan (design, tests, seed ranges) was frozen and approved by the author before simulation. The singular 'the protocol' suggests one plan that came before all data.
- **Evidence.**
  - approval entries first committed: V99 7da4ab4 10-19 14:12; V100 c225049 16:54; V108 75bcd2b 10-20 09:51; V115 7c6acc8 21:11 (git log -S on docs/decisions.md)
  - P1b seeds 260-279/300-339/600-699 approved V108 before P1b start 10:38:06 (journal p1b-run.service)
  - C1 seeds 700-799 approved V115 21:11:24, before C1 start 21:27:50, but after P1b data
  - P1 page amended 0e8d49b 16:32 (I1-I16, R1/R5/R8, D1-D5) after P1 smoke data (p1_smoke_20261019a, commit 8f204c6, 14:44)
  - no protocol file or decision row changed after 10-19 18:40, except the new P1b/C1 pages before their own runs (git log; scratch check of '-| V' lines)
- **Verification.** Hashed every protocol version and matched it to the recorded page_sha256 values. Checked that no protocol file or decision row was edited after any run start. Per study, protocol, statements and seeds were approved before that study's data. However, the P1b protocol was written after P1 data, and the C1 protocol and seeds after P1b data.
- **Failure points.** Per study the claim is VERIFIED. The literal 'before any data' is false for P1b (after P1) and for C1 (after P1b). Minor point: the P1 page was amended after its smoke data, which used smoke seeds only.

#### Source: R1 recheck (PROV), verdict CONTRADICTED (basis: derived)

- **Evidence.**
  - papers/paper_1/paper.qmd:145 and :69 (both sentences also appear in the rendered paper.pdf, pdftotext lines 54 and 165); the paper body never mentions P1, D1 or D2
  - Protocol commits: p1_incident_information.md 14d8866 13:38 / ee3ce1e 13:55 / 7da4ab4 14:12 / 0e8d49b 16:32 (10-19); p1b_addendum.md a0144e3 09:42 / 75bcd2b 09:51 (10-20); p1b_confirm_c1.md a4e3e6d 21:09:49 / 7c6acc8 21:11:24 (10-20); none changed after their run started
  - Recorded page_sha256 values match the final pages: P1 fed27bf6 = 0e8d49b; P1b 2b3d3ccb = 75bcd2b (base fed27bf6); C1 8b6005aa = 7c6acc8 (~/work/phd/v5b1_runs/*_STARTED.json, */result.json)
  - Data before the P1 protocol: screen_d2/v92 finished 2026-10-19 11:37 (V94 committed fac8789 11:38); screen_D2_incidents.md:13 uses BN4 with q in {1600, 2000} and slow/block incidents; p1_incident_information.md:19-43 builds on D2's plant, grid and rules
  - Data before the P1b protocol: queue_v100.log 'start P1 (V99/V100)' 2026-10-19 18:42:22; V102 (P1 results) c2d11c2 03:19 and V103 (P1 verified, 'controller-family confound (A had no PI-law plans)') e24c02a 06:44, both before the P1b draft at 09:42
  - p1b_addendum.md lines 3-11: statements S1a/S1b/S2/S3 carried over unchanged from V99/V100; 'P1 stays in the record as the earlier run. P1b becomes the paper's main result. Both are reported.'; B3 adds PI-law plans to A because of the V103 confound
  - p1_result.json eval.cells.block_q1600.IP_vs_L0.PI.all_seeds rel -0.0070 CI [-0.1141, 0.1292]; p1b_result.json same key rel 0.1798 CI [0.0890, 0.3157]; tune.arms['1600'].IP block = f40_14 (P1) vs p20_20_16_e4 (P1b, a G_PI plan); C1 tests IP = c1800 -> p20_20_16_e4 (V114/V116)
  - The paper's '87 % (no amber)' comes from P1: p1_result.md:81 ('87 % of 50,061 non-replicate evaluation runs'); p1b_result.md:56
  - Per-study ordering holds: P1b smokes 10:14/10:30, T-check record 11:03, eval 13:07, all after V108 at 09:51; C1 started 21:27:50, after V115 at 21:11:24; c1_build job (21:10-21:26) ran its smoke only on seeds 7,400,000-003; draft-to-approved diff of the C1 page changes only the status line
  - Seeds: P1 tcheck 240-259 / tune 200-239 / eval 500-599; P1b 260-279 / 300-339 / 600-699; C1 700-799 (result.json .seeds); each set was approved before its own study's data; P1b's ranges carry other roles than the block's labels (disclosed in the addendum, not in the paper)
  - 0e8d49b (16:32) amended the P1 page after the 14:44 smoke (p1_smoke_20261019a.stdout); D1 meter-signal row cites smoke reds of up to 322 s; smoke seeds 7,400,000-009 only
- **Verification.** Re-check outcome UPHELD: Meaning: paper.qmd:145 says that one plan (the protocol, its statements and its seed ranges) was frozen and approved before any simulation data existed. The introduction says the same at paper.qmd:69 ("All statements were pre-registered before any data were produced"), and the rendered PDF prints both sentences.

I looked for a reading under which the claim holds. Only one works: the per-study reading ("each study's protocol was approved before that study's data"). It does hold.
- P1 page approved 14:12 (V99); its last version 0e8d49b is from 16:32; P1 started 18:42.
- P1b addendum approved 09:51 (V108); P1b smoke 10:14; tool checks 11:03; evaluation 13:07.
- C1 approved 21:11:24 (V115); C1 started 21:27:50. The C1 build job ran its smoke only on smoke seeds 7,400,000-003.
- Each run's recorded page_sha256 matches the final committed page. Seed ranges never overlap: P1 240-259/200-239/500-599, P1b 260-279/300-339/600-699, C1 700-799, all inside the v5.B block approved 2026-10-13.
- The statement texts S1a/S1b/S2/S3 were fixed in V99/V100, before P1 data, and the P1b addendum carries them over unchanged.

The sentence does not say "per study", though. It says "The protocol ... before any data were produced", and the paper never mentions P1, D1 or D2. Under the plain reading the claim is false, and in a way that matters:
1. Before the P1 protocol was drafted (13:38), screen D2 had already run on the same plant (BN4), the same demand levels (q 1600/2000) and the same incident types (slow/block). D2 ran 10:45-11:37 and its result is V94. The P1 page builds on D2's grid and rules.
2. The paper's main study, P1b, was designed after the full P1 evaluation had run and been read: P1 ran from 10-19 18:42 (V102 03:19, V103 06:44); the P1b draft is from 10-20 09:42. Its changes were motivated by P1's findings, including V103's "controller-family confound (A had no PI-law plans)".
3. That change affected the result. Adding PI-law plans to the action set A turned block_q1600 IP vs PI from -0.7 % [-11.4, 12.9] in P1 to +18.0 % [8.9, 31.6] in P1b. P1b's IP block plan became p20_20_16_e4, a PI-law plan (P1's was f40_14). C1 then tested exactly that plan.
4. The paper uses P1 data without saying so: "87 % (no amber)" comes from P1's 50,061 evaluation runs (p1_result.md:81).
5. The P1b addendum itself says "P1 stays in the record as the earlier run ... Both are reported". The paper does not report P1.
6. C1's statement and cell were fixed after P1b data. That is normal for a confirmation, but the absolute wording also covers it.

Under the task definitions this is a false statement about pre-registration, so it is critical. The headline numbers themselves are not invalidated: C1 used fresh seeds 700-799 under a protocol approved before its data. So the fix is to correct the disclosure, not to re-run anything. Suggested wording: "Each study's protocol, statements and seeds were approved before that study's data; P1b revised an earlier round (P1: no amber, no PI-law plans in A) after its results and was run on fresh seeds; the C1 cell was chosen from P1b."

Minor: the P1 page was amended at 16:32 (I1-I16, R1/R5/R8, the D1 meter-signal choice) partly because of the 14:44 smoke data, which used smoke seeds only. The page says no item made S1a/S1b/S2 easier. Info: P1 was resumed once mid-run (V102), which bears on "run once".

### C54 (paper line 145): final verdict **PARTIALLY SUPPORTED**

> Every study was run once from a frozen code version.

**Reconciliation:** True for P1b and C1 (one launch, clean committed code, every run tagged). P1 was aborted by a docs commit and resumed from a frozen worktree (reusing 6,146 tool-check runs); D1/D2 were re-run after the V100 bug. None of this is stated.

#### Source: R1 PROV, verdict PARTIALLY SUPPORTED (basis: direct observation)

- **Meaning.** Each experiment was launched once, never restarted or partly re-run, and used a fixed, committed code version that did not change during the run.
- **Evidence.**
  - P1B_EVAL_STARTED.json args.resume=false; p1b/v108/run.log: every stage '0 reused', 'failed 0'; one p1b-run.service start 10-20 10:38:06 (journalctl --user)
  - P1b result.json code_commit 93ba655, code_dirty false; all 344,852 run JSONs code_commit 93ba655; main HEAD at launch was 8e10812, so the run came from another checkout at 93ba655 (frozen worktree, now deleted; git worktree list shows none)
  - C1: P1B_C1_STARTED.json resume=false; one p1b-c1.service start 21:27:49; all 1,100 runs e7dd561; code_dirty false; diff 93ba655..e7dd561 adds only confirm_c1.py, tests and a tool
  - P1: queue_v100.log 18:51:30 'code changed during the screen (tcheck-A): HEAD 85f7d34da9 -> e973f6e377 ... FIX/rerun'; p1/v99/run.log:13-15 '0 runs to do (6146 reused)'; P1_EVAL_STARTED.json args.resume=true; queue_v100.sh cd to the main worktree
  - V100/V101: D1 and D2 re-run after the meter-phase bug (D1_BUGRERUN_V100.json, D2_BUGRERUN_V100.json)
  - guards: v5b/p1b/run.py@93ba655:430-444, 466-485 (dirty refusal, make_verify)
- **Verification.** Read the logs, sentinels and journal unit starts, and scanned the code_commit field of every run JSON (scratch scan_runs.py). P1b and C1: one launch each, no reuse, clean committed code, a tree-change guard, and every run carries the run commit. The P1b frozen worktree was inferred because its code_commit differs from main HEAD at launch; it cannot be inspected now. P1, which the paper uses for its 87 % figure, was started from the non-frozen main worktree, aborted by a docs commit, and resumed. D1/D2 were re-run for a bug.
- **Failure points.** True for P1b and C1. Not true for P1 (resumed; first segment from the main worktree) or D1/D2 (bug re-runs), which the paper does not mention. The mid-run commit e973f6e was docs only (git show --stat), so P1's data are code-identical. The frozen state of C1 cannot be checked independently, but HEAD = e7dd561 with a clean tree pins the code anyway.

### C55 (paper line 145): final verdict **VERIFIED**

> Evaluation uses 100 seeds that are separate from the tuning seeds; comparisons are paired by seed.

**Reconciliation:** Evaluation seeds 7,400,600-699 disjoint from tuning 300-339; pairs share demand, SUMO seed and incident.

#### Source: R1 PROV, verdict VERIFIED (basis: derived)

- **Meaning.** The controllers are tuned on one set of random seeds and scored on a different set of 100 seeds, so tuning cannot overfit the evaluation runs. Every arm is run on the same seeds, and differences are taken seed by seed.
- **Evidence.**
  - P1b result.json seeds: tune [7400300, 7400339], eval [7400600, 7400699]; tune.A_size 120
  - raw file names: P1b 160 distinct seeds 260-279, 300-339, 600-699 (scratch seed_sets.py)
  - pairing.py: P1b 960 (incident, q, seed) groups; 0 with more than one incident window; 0 with more than one main-run n_trips; 152,850 main runs with sumo_seed = demand_seed = seed; 192,002 replicates with sumo_seed = seed + k·1e7
  - C1: 100 groups, all paired; arms frozen from P1b tuning (result.json frozen_arms.check.match = true)
- **Verification.** Own scripts over all raw run JSONs: seed sets, overlaps and pairing (incident window, demand size, seeds).
- **Failure points.** Evaluation also uses 400 derived replicate seeds (seed + k·1e7) for ORX/TP. 'Paired by seed' does not mean common random numbers inside SUMO (the paper says so itself). The C1 cell and comparator were selected on P1b's evaluation seeds, which is not tuning, but it is selection (see C60).

### C56 (paper line 145): final verdict **VERIFIED**

> rel = median(r - t)/median(r), positive favours t over reference r; percentile bootstrap CIs with B = 20,000.

**Reconciliation:** Definitions and B = 20,000 match the code; all 44 S1-level rows reproduced exactly.

#### Source: R1 S1, verdict VERIFIED (basis: derived)

- **Meaning.** For each seed, the treatment's delay is subtracted from the reference's delay. The median of these paired differences is divided by the reference's median delay. A positive value means the treatment has lower delay. The confidence intervals come from resampling the 100 seeds with replacement 20,000 times. The same seeds are used for both arms (paired), and the 0.3125th and 99.6875th percentiles of the resampled statistic are taken.
- **Evidence.**
  - v5b/p1/stats.py@93ba655:14 B_BOOT = 20_000; :35-41 boot_idx default_rng(20261019).integers(0, n, (B, n)); :52 d = r - t; :55 one idx for both d and r (paired); :62 diff_ci = percentile of median(d*); :63 rel = median(d)/median(r); :64 rel_ci = nanpercentile of median(d*)/median(r*)
  - protocol p1_incident_information.md:86 and addendum I12 (line 176)
  - result.json eval.S1.per_cell_stats.*.level = 0.99375, n = 100
- **Verification.** s1_recompute.py re-implements the statistic in its own numpy code. With the same draws, all 44 rows match result.json exactly (max abs deviation 0 for rel, diff, medians and both CIs). The share of draws with median(r*) <= 0 is 0, so the ratio is always defined.
- **Failure points.** The intervals printed in the text are percentile CIs of the ratio (rel), while the S1 rule uses the CI of median(r − t). The paper does not say this. The two agree in sign in all 44 rows (sign_consistency.py). The tails at the 0.99375 level hold about 62 draws each, so bounds carry Monte Carlo error of up to 1.6 points (robustness.py).

### C57 (paper line 145): final verdict **VERIFIED**

> S1 rule R(t, r): (a) in at least one cell rel >= 10 % with the lower CI bound of median(r - t) above zero, and (b) in every cell point rel >= -5 %. S1a requires R(ID, r) for every L0 arm with (a) met in the same cell; S1b requires R(IP, ID).

**Reconciliation:** Rule text matches the protocol and the code; re-implemented independently with the same outcome.

#### Source: R1 S1, verdict VERIFIED (basis: direct observation)

- **Meaning.** Arm t 'beats' r when two things hold. First, in at least one cell its median gain is at least 10 % and the paired-difference interval lies above zero. Second, in no cell is its point estimate more than 5 % worse. 'Presence pays' (S1a) needs ID to beat each of the five always-on arms, with the same winning cell for all five. 'Type pays' (S1b) needs IP to beat ID.
- **Evidence.**
  - protocol p1_incident_information.md:94-100 (rule and statements), :90 intersection-union, A2(a) line 147; addendum R1/R5 lines 184-185 (fail closed; same (a) cell in both views)
  - v5b/p1/stats.py@93ba655:79-80 rule_cell, :83-90 rule_R, :93-102 s1a
  - v5b/p1b/analysis.py@93ba655:487-518 s1_decision (both views, a_both/b_both, missing cells)
- **Verification.** I compared the paper text, the protocol and the code line by line, then re-implemented R, S1a and S1b in s1_recompute.py. The outcome is the same as result.json: S1a False with common (a) cells [], and S1b True with (a) cells [slow_q2000, block_q1600].
- **Failure points.** The paper leaves out two pre-registered strictness clauses: the rule must hold in both views (all seeds and valid-only), and it fails closed on a missing cell. This has no numeric effect here, because 0 runs were invalid or missing among the 3,200 S1 runs.

### C58 (paper line 145): final verdict **VERIFIED**

> The S1 intervals are Bonferroni-corrected (level 0.99375).

**Reconciliation:** 0.99375 = 1 - 0.05/8 in all 44 rows. The family behind /8 is not explained in the paper; CI ends at this level move up to 1.6 points with the bootstrap RNG.

#### Source: R1 S1, verdict VERIFIED (basis: direct observation)

- **Meaning.** There are two statements (S1a, S1b), each tested in four cells, which makes 8 tests. Each interval is therefore made at the 1 − 0.05/8 = 99.375 % level instead of 95 %. Within S1a, the comparisons against the five always-on arms are combined by intersection-union (all must pass), which needs no further correction.
- **Evidence.**
  - v5b/p1/stats.py@93ba655:17 LEVEL_S1 = 1.0 - 0.05/8
  - v5b/p1b/analysis.py@93ba655:353-355 ID vs L0, IP vs ID and IP vs L0 all at st.LEVEL_S1
  - protocol p1_incident_information.md:88 (family S1a and S1b x 4 cells), :90 IUT with no extra correction
  - result.json: level 0.99375 in every S1 stat
- **Verification.** Code read. The level was recomputed and matches all 44 rows. I also checked that the family is valid: the union over 4 cells is covered by /4, IUT needs no correction, and two-sided intervals used for a one-sided rule are conservative.
- **Failure points.** The paper does not state the family (m = 8 = 2 statements x 4 cells) or the IUT. A reviewer may ask why the 20 ID-vs-L0 comparisons are not corrected for. The answer is IUT, but it needs one sentence.

### C59 (paper line 145): final verdict **PARTIALLY SUPPORTED**

> S2 states the bracket of the gain of per-incident information over IP; S3 reports break-even detection delays (descriptive).

**Reconciliation:** S2 correct. S3 is described as detection delays only, but the pre-registered S3 includes c*, p*, f* and a combined row, and A10 lists p* and f* as paper outputs.

#### Source: R1 S23, verdict PARTIALLY SUPPORTED (basis: direct observation)

- **Meaning.** S2 is a pre-registered statement about how much a controller that knew each incident in full (hindsight) could add beyond the type plan IP. It is reported as an interval [lower, upper]. S3 is a descriptive (untested) robustness map: how large an imperfection can be before IP loses its lead over the always-on arms. The paper names only the detection delay.
- **Evidence.**
  - v5b/p1/stats.py@93ba655:112-142 (s2_cell, s2_statements: x, y, y_hat, plateau, 'bracket [y, x]' text)
  - v5b/p1b/analysis.py@93ba655:356-369 (S2 per cell), 521-570 (imperfection_cell: d_star, c_star, p_star, combined_row, never_switch_back)
  - protocol p1_incident_information.md:105-112 (S2 rules; 'S3, robustness (descriptive): d*, c*, p*, f*(pi) and the combined row, with 95 % CIs'); :116 (A10 paper outputs: one break-even table (d*, p*, f*))
  - result.json eval.S2.<cell>.statements.text = 'adds at most ...; bracket [y, x] %'
  - paper.qmd Table II (lines 177-179) reports only d*; no c*, p*, f* or combined row anywhere in the paper (grep)
- **Verification.** Read the run-commit code and the protocol. S2 in result.json yields brackets only (plateau false in every cell). Recomputed independently: S3 in code and protocol includes c*, p*, f*(pi) and a combined row, besides d*; s23_extra.py reproduces c* and p* exactly.
- **Failure points.** The S2 description is correct. The S3 description narrows the pre-registered S3 to detection delay only, and the paper omits the other pre-registered S3 rows (c*, p*, f*, combined), which A10(a) says belong in the paper. Test: compare protocol §6/A10 with the paper's tables.

### C60 (paper line 145): final verdict **PARTIALLY SUPPORTED**

> A separate confirmation (C1) tested one cell on 100 fresh seeds with a single pre-fixed statement at the 95 % level.

**Reconciliation:** Fresh seeds, statement fixed before the run, run once: verified. Omitted: cell and comparator chosen after P1b data; the rule tests rel >= 10 % on the point estimate (rel CI lower bound 7.3 %); PI was not the strongest L0 arm there (FB).

#### Source: R1 PROV, verdict PARTIALLY SUPPORTED (basis: derived)

- **Meaning.** After the main study, one result was re-tested on new seeds, with a single pass/fail rule written before the new runs. This guards against chance findings.
- **Evidence.**
  - p1b_confirm_c1.md@7c6acc8 (statement: rel >= 10 % AND lower bound of the 95 % CI of median(PI - IP) > 0, in both views; disclosure at line 36 that cell and arms were chosen after P1b data)
  - C1 runs: 1,100 files, seeds 7400700-7400799 only, commit e7dd561 (scan_runs.py)
  - no earlier run directory holds a 74007xx seed; tests at e7dd561 build run keys only (tests/test_p1b_c1.py:1-3, 44-48)
  - recompute (c1_recompute.py): rel 16.2 %, diff 41.4 s/veh [16.6, 65.7], rel CI [7.3, 23.6]; valid IP 100, PI 100
  - P1b block_q1600 (c1_opponent.py): FB median 247.9 < PI 252.1; IP vs FB 15.9 % (39.4 [20.1, 55.3]) vs IP vs PI 18.0 %
- **Verification.** Checked that C1's seeds are fresh, that its statement was fixed before its run (7c6acc8 21:11 < 21:27:50), and that it ran once. Recomputed the statement independently. Checked how the cell and the comparator were chosen.
- **Failure points.** The paper omits that the cell, arms and comparator were chosen after seeing P1b's evaluation data (the C1 protocol discloses this). It omits that the statement also needs rel >= 10 % in both views; the rel CI's lower end, 7.3 %, is below 10 %. It omits that PI was not the strongest always-on arm in that cell (FB had the lower median and the smaller paired gap), and FB was not run in C1.

### C61 (paper line 149): final verdict **PARTIALLY SUPPORTED**

> Drivers obey the amber unless they cannot stop comfortably.

**Reconciliation:** "Comfortably" = SUMO tls.yellow.min-decel 3 m/s2 (twice b = 1.5). Vehicles that cannot stop before red are forced to an instantaneous, non-physical stop. Not stated.

#### Source: R1 PLANT, verdict PARTIALLY SUPPORTED (basis: direct observation)

- **Meaning.** When the light turns amber, a normal driver stops unless stopping would need hard braking; in that case the driver continues.
- **Evidence.**
  - SUMO v1_27_1 MSVehicle.cpp:2793-2796 stopDecel = max(min(tls.yellow.min-decel, emergencyDecel), decel) and :2924 plan to stop if canBrakeBeforeStopLine
  - MSFrame.cpp:513 tls.yellow.min-decel default 3.0 (not overridden in sumo_runner.py@93ba655:102-107)
  - MSVehicle.cpp:3772-3780 the step check uses vType decel 1.5 m/s2
  - MSVehicle.cpp:4520-4524 and 4780-4786 a red link forces 'emergency stop at the end of lane' with position reset and speed 0
  - estop_times.out: P1b 44,816 such stops, all on edge 2, 'because of a red traffic light'; implied decel median 26.4 m/s2, overshoot median 6.0 m, max 11.0 m
- **Verification.** Read the SUMO source of the exact version. Grepped all 344,852 P1b SUMO logs and tallied with own parser.
- **Failure points.** 'Comfortably' means 3 m/s2 when the stop is planned and 1.5 m/s2 at the step-level yellow check; neither value is stated. Drivers who continue at amber but do not clear the line before red are stopped instantly, which is physically impossible. A 3-s amber at 23 m/s leaves a dilemma zone of about 69-88 m.

#### Source: R2 G4, verdict PARTIALLY SUPPORTED (basis: derived)

- **Meaning.** Concept: a normal (non-runner) driver stops at amber when a comfortable stop is possible and otherwise drives on. Detail in SUMO 1.27.1: at amber a vehicle plans to stop if brakeGap(v, stopDecel) fits before the line, with stopDecel = max(min(tls.yellow.min-decel 3.0, emergencyDecel 9), decel 1.5) = 3.0 m/s2. Otherwise it drives on. A vehicle that drives on but has not crossed by red onset brakes at up to 9 m/s2. If it still cannot stop, it is reset to the end of the lane with speed 0.
- **Evidence.**
  - SUMO v1_27_1 src/microsim/MSVehicle.cpp:2793-2796 (stopDecel, canBrakeBeforeStopLine), :2924 (plan to stop at yellow/red), :3768-3773 (the step check with decel 1.5 is reached only by vehicles that already failed the 3.0 test), :4520-4523 (a red link without ignoreRed gives the reason 'red traffic light'), :4776-4786 (forced stop: position set to the lane end, speed 0), :7585-7621 ignoreRed (non-runner at red: false)
  - src/microsim/MSFrame.cpp:513 tls.yellow.min-decel default 3.0; src/utils/vehicle/SUMOVTypeParameter.cpp:979-1013 emergencyDecel default max(decel, 9) for passenger cars
  - No override in the run code: grep for min-decel / emergencyDecel / step-method in code_93ba655 finds none; d1/sumo_runner.py@93ba655 start() args
  - plant.py@93ba655:27 decel 1.5 for both types; netgen_bn4.py@93ba655:24 speed 23
  - G4/kinematics.out: at 23 m/s the brake gap is 170.6 m at 1.5 m/s2 and 82.5 m at 3.0 m/s2 (Euler, 0.5 s), or 176.3 / 88.2 m continuous; a 3-s amber covers 69 m; dilemma zone 69-82.5 m
  - G4/pair_check_p1b.out and G4/by_type_p1b.out: 44,816 forced stops on edge 2 (40,862 together with a 9-m/s2 braking line in the same step); 95,215 meter-edge braking warnings, all at decel=9.00; C1: 154 forced stops, 554 brakings on edge 2
  - G4/approach_cross_p1b.out: no non-runner ever crossed at red (0 in all cells)
  - paper.qmd: no mention of emergency stops, forced stops, deceleration values or IDM; docs/research/protocols/p1b_addendum.md:19-20 pre-registers the rule and 'Reported per arm: emergency stops at the meter'
- **Verification.** Read the SUMO source of the exact version (git tag v1_27_1) and the run code. Re-implemented the brake-gap and IDM rules on my own (G4/kinematics.py). Grepped all 344,852 P1b and 1,100 C1 SUMO logs myself and split the events by type and runner status with my own demand rebuild (G4/by_type.py; 0 count mismatches).
- **Failure points.** 'Comfortably' is not defined. In the model it means 3.0 m/s2, twice the vehicle's comfortable deceleration b = 1.5. At free-road speed, no vehicle within about 7.2-8.1 s of the line can stop at b or less. My re-implementation (not checked against SUMO trajectories) suggests that the executed IDM braking can reach about 7 m/s2 even when SUMO decides to stop. Drivers who cannot stop and do not clear do not 'run' the amber: they are stopped instantly in a physically impossible way. This happens about 0.13 times per metered run in P1b, and 44 % of these stops fall at the first amber after the all-green warm-up. The paper does not disclose this.

### C62 (paper line 149): final verdict **PARTIALLY SUPPORTED**

> In report-only rows a share s in {10, 30} % of drivers ignore the amber and the first 1.5 s of red.

**Reconciliation:** Shares implemented as written; runners also cross any red when they cannot brake, are never emergency-stopped, and include AV-type vehicles.

#### Source: R1 PLANT, verdict PARTIALLY SUPPORTED (basis: direct observation)

- **Meaning.** In some extra runs, 10 % or 30 % of drivers are 'runners': they drive through amber and through the first 1.5 s of red.
- **Evidence.**
  - v5b/p1b/runners.py@93ba655:15 jmDriveAfterYellowTime 3, jmDriveAfterRedTime 1.5, jmDriveRedSpeed 13.9; :33-37 per-vehicle draw
  - SUMO v1_27_1 MSVehicle.cpp:7605-7621 ignoreRed: with jmDriveAfterRedTime >= 0 always drive at yellow; at red return !canBrake || 1.5 > redDuration; :4522 ignoreRed(link,false) is true for runners, so they are never force-stopped
  - runner_share.out: realised shares 0.1009 / 0.3011; runner red crossings per run median 2 / 8 (max 14 / 35)
- **Verification.** Read the SUMO source. Recomputed shares and runner crossings from raw runs.
- **Failure points.** Runners also cross a red of any age when they cannot brake at 1.5-3 m/s2, and they are never emergency-stopped. Timing within the red is not logged, so how many crossings happen after 1.5 s is unknown. Runners include AV-type vehicles.

#### Source: R2 G4, verdict PARTIALLY SUPPORTED (basis: derived)

- **Meaning.** Concept: some drivers are runners. Detail: each vehicle, of either type, is a runner if u_i < s. A runner gets jmDriveAfterYellowTime 3, jmDriveAfterRedTime 1.5 and jmDriveRedSpeed 13.9. In SUMO a runner always drives at amber. At red it drives if the red is younger than 1.5 s or if it cannot brake, and its speed through red is capped at 13.9 m/s.
- **Evidence.**
  - v5b/p1b/runners.py@93ba655:15 RUNNER_JM, :20-30 a runner copy of both base types (human and av), :33-36 runner_flags, :39-52 apply_runners
  - SUMO MSVehicle.cpp:7585-7621 ignoreRed (:7621 return !canBrake || ignoreRedTime > redDuration), :2939 redSpeed = min(v, jmDriveRedSpeed)
  - G4/by_type_p1b.out: runner-run population 507,536 runners in 2,526,138 vehicles (share 0.2009 pooled over s = 0.1/0.3); 9.79 % of runners are 'av' type; runners have 0 of 940 forced stops; runners have 3,051 of 4,806 (63 %) meter-edge 9-m/s2 brakings in runner runs
  - G4/by_type_c1.out: runners 0 of 60 forced stops, 235 of 379 brakings at 9 m/s2; 10.0 % of runners are 'av' type
  - G4/approach_cross_p1b.out: non-runner red crossings are 0; runner red crossings are 4,769 / 2,548 (s = 0.1) and 16,522 / 9,989 (s = 0.3) for q1600 / q2000
- **Verification.** Read the code and the SUMO source. Rebuilt every vehicle's runner flag and type with my own code (counts equal n_runners in every checked run) and joined them with the log events.
- **Failure points.** The shares are implemented as written. The physics is wider than the text: runners also cross a red of any age when they cannot brake, their speed through red is capped at 13.9 m/s, and red onset makes them brake at the 9 m/s2 emergency limit (over-represented 3x). About 10 % of runners are the 'av' vType, which the paper does not mention. Runner crossings by vehicle type cannot be checked from the stored data: runner_crossings is kept only by signal state, and the route and tripinfo files are deleted (episode.py@93ba655:175-180). The timing of crossings within the red is not logged.

### C63 (paper line 149): final verdict **PARTIALLY SUPPORTED**

> Published field rates of metered-signal violations [TOPS2005; Sun2013] give context for these shares (s in {10, 30} %); they are model parameters, not field estimates.

**Reconciliation:** No numbers given in the paper. Field data (companion report/thesis) put s = 30 % inside observed work-zone non-compliance; permanent ramp meters are lower (<= 9 %); definitions differ.

#### Source: R1 LIT, verdict PARTIALLY SUPPORTED (basis: direct observation)

- **Meaning.** The paper models 10 % or 30 % of drivers ignoring the amber and the first 1.5 s of red. It points to field violation rates as context, while saying these shares are not taken from field data.
- **Evidence.**
  - TOPS 2005 Tables 3-14 and 3-15: SOV red-light violations 0.9-9.0 % per ramp and peak period. HOV 8.3-34.3 %, but HOV violations also count vehicles with fewer than two occupants (§2.4), so they are not comparable
  - Sun 2013: the abstract gives no rates. A search-engine snippet (not opened, unverified) attributes 40.5-82.9 % compliance to a related Missouri thesis
  - Model behaviour (paper line 149): runners ignore the amber and the first 1.5 s of red. The field definition counts any vehicle that did not stop at red
- **Verification.** Read the TOPS full text; Sun abstract only.
- **Failure points.** The paper quotes no numbers. Verified permanent-meter data (at most 9 % for SOV) put s = 30 % well above field values, so it is a stress test. The behaviour definitions differ. Sun's rates are needed before 30 % can be called field-like (LIT-F7).

#### Source: R2 G8, verdict PARTIALLY SUPPORTED (basis: direct observation)

- **Meaning.** Concept: the modelled shares of red-light runners are compared with real-world violation rates. Detail: s = 10 % or 30 % of drivers ignore the amber and the first 1.5 s of red; field studies report the share of vehicles that passed on red.
- **Evidence.**
  - TOPS 2005 :1333: SOV violations 0.9-9.0 % (permanent meters); HOV 8.3-34.3 % includes occupancy violations
  - Edara/Sun/Zhu 2012 report :707-710: compliance 45.5 % (4R-2G), 54.0 % (4R-3G), 75.0 % (4R-1Y-2G), 69.6 % (4R-1Y-3G), i.e. 25.0-54.5 % non-compliance; Table 4.2 :758: 85.6 % platoon / 63.6 % free-flow compliance (14.4 / 36.4 % non-compliance)
  - Zhu 2012 thesis Table 5.1: per-site compliance 40.5-82.9 %, i.e. 17.1-59.5 % non-compliance (G8/noncompliance_ranges_output.txt)
  - Sun2013 TRR abstract: no rates
- **Verification.** Computed the ranges with G8/scripts/noncompliance_ranges.py from the report and thesis texts, and compared them with the TOPS ranges.
- **Failure points.** I did not verify that the cited TRR article contains rates; the numbers are in the companion report and thesis. The definitions differ: the field counts not passing on green; the model's runners ignore only the amber and the first 1.5 s of red. The meters differ too: temporary ramp meters releasing one vehicle per green, versus a mainline meter at 23 m/s. s = 30 % is inside the work-zone field range, so round-1's 'well above field values' is wrong (G8-F1).

### C64 (paper line 155): final verdict **PARTIALLY SUPPORTED**

> S1a fails: knowing only that an incident is on gave no detected gain of 10 % or more over strong always-on control.

**Reconciliation:** FAIL reproduced. "No detected gain >= 10 %" holds for the pre-registered pooled-median ID; with other type-blind ID rules fitted on tuning seeds, ID beats FB/PI by 13.7-18.0 % in crawl-1600 (S1a still fails, via (b)). ID is an L0 law started at onset by construction (CTRL-F3).

#### Source: R1 S1, verdict PARTIALLY SUPPORTED (basis: derived)

- **Meaning.** When an incident occurs, switching at onset to one plan for all incidents (ID) was not clearly at least 10 % better than the best always-on meters in any cell. Formally, the pre-registered rule R(ID, r) did not pass for every always-on arm in a common cell.
- **Evidence.**
  - result.json eval.S1.S1a_pass = false, S1a_cells_both_views = []
  - s1_recompute.py: R(ID,FB) a_cells [] (rel -1.5, +4.8, -2.6, +6.6); R(ID,PI) a_cells [] and b fails in slow_q1600 (-17.9); R(ID,N), R(ID,FX) pass with all 4 cells; R(ID,AD) passes with (a) in the block cells only
  - ID vs PI 99.375 % rel CIs: [-35.1,-6.7], [-5.2,0.0], [-10.1,6.7], [-6.6,0.0]; ID vs FB upper bounds 4.7, 6.9, 3.7, 10.1
  - result.json tune.arms: ID = f40_10 = FB at q1600; ID = p20_20_14_e4 = PI at q2000 (re-derived by tune_check.py)
  - clean_day.py: clean-day median delay N 45.4 vs PI 81.1 s/veh (q1600), N 151.6 vs PI 301.1 (q2000); ID and IP run N on clean days
- **Verification.** I recomputed S1a and found the same FAIL. I identified the binding arms (FB and PI) and read the upper CI bounds. I checked controller identity and clean-day costs from raw runs.
- **Failure points.** The verdict is correct. The wording understates the CIs and leaves out a material caveat.
(1) Against PI, the 99.375 % intervals exclude a gain of 10 % or more in every cell (upper bounds at most 6.7 %), so the data support more than 'not detected'. This reading is post hoc, not the pre-registered test.
(2) By construction, ID's selected plan is the always-on FB controller (q1600) or PI controller (q2000). ID therefore differs from those arms only by running N before onset, and S1a against them can hardly pass on incident days.
(3) Presence information pays on clean days, where always-on PI costs +79 % (q1600) and +99 % (q2000) in delay versus N. Line 104 promises this cost 'separately' and the protocol requires it next to S1, but the paper never reports it.

#### Source: R1 FU1 (FU1-C4), verdict VERIFIED (basis: derived)

- **Meaning.** A plan that knows only that an incident has started does not beat every tuned always-on controller under the pre-registered rule.
- **Evidence.**
  - p1b_result.json eval/S1/all_seeds/S1a: binding FB, common_a_cells []
  - FU1/drain_audit.out S1 verdicts: D, W and F all S1a FAIL; on W no L0 arm has any a-cell
- **Verification.** I recomputed R(ID, r) for r in {N, FX, FB, PI, AD} in all 4 cells on 3 metrics (FU1/drain_audit.py).
- **Failure points.** The verdict is the same on all three metrics, so the drain convention cannot flip it. ID vs N, FX and AD shows ≥ 10 % gains on delay, but 79-103 % of those accrue after control ends. That matters only for the word 'strong'.

#### Source: R2 FU2 (C64), verdict PARTIALLY SUPPORTED (basis: derived)

- **Meaning.** R(ID, r) does not pass for every L0 arm with (a) in a common cell. The clause says presence information gave no detected gain of at least 10 % over the strong L0 arms (FB, PI).
- **Evidence.**
  - FU2-1/s1_indep.out delay: ID vs FB -1.5/4.8/-2.6/6.6 % and ID vs PI -17.9/-1.8/-0.7/-2.1 %, no a-cells; ID vs N, FX all cells; ID vs AD block cells; S1a FAIL (also FAIL on window and full TTT)
  - FU2-1/id_rule_sens.out: ID p20_20_14_e4 (pooled mean or mean of per-type medians, q1600) in block_q1600 vs FB 13.7 % (diff LCB 11.5), vs PI 16.3 % (LCB 10.4); (a) against every L0 arm in both views; ID p20_20_16_e4 (minimax) vs FB 15.9 %, vs PI 18.0 %
  - FU2-1/id_rule_sens.out: under those rules S1a still fails via (b): slow_q1600 ID vs PI -16.2 % / -29.9 %
  - result.json tune.arms: ID = f40_10 = FB at q1600; ID = p20_20_14_e4 = PI at q2000
  - protocol p1_incident_information.md:101 pre-registered fail text 'knowing that an incident is on did not pay >= 10 % beyond strong always-on control'
- **Verification.** Own recomputation of R(ID, r) for all 5 L0 arms, 4 cells, both views, on 3 metrics and under 4 ID rules.
- **Failure points.** The S1a FAIL is robust: it holds on every metric and every ID rule tested. The clause holds only for the pooled-median ID. A type-blind ID chosen on the tuning seeds by pooled mean, by mean of per-type medians or by minimax has a detected gain of 13.7-18.0 % over FB and PI in crawl-1600. S1a then fails only through (b) in slow_q1600. Also, the ID plan is FB's law at q1600 and PI's law at q2000, so ID differs from them only before onset. The paper does not disclose either point. FU1-C4's VERIFIED covered only the drain lens. The wording follows the pre-registered fail text, so this is no deviation.

#### Source: R2 FU2 (FU1-C4), verdict PARTIALLY SUPPORTED (basis: derived)

- **Meaning.** Same sentence as C64.
- **Evidence.**
  - See C64; FU2-1/id_rule_sens.out
- **Verification.** Merged into C64.
- **Failure points.** FU1 showed correctly that the drain convention cannot flip the verdict. It did not test the ID tuning rule, under which the clause 'no detected gain >= 10 %' becomes false in crawl-1600.

### C65 (paper line 155): final verdict **VERIFIED**

> Against always-on PI, ID was never better (rel between -17.9 % and -0.7 %).

**Reconciliation:** Values exact. In the q2000 cells ID is PI's own law started at onset, so this row measures the cost of running N before onset.

#### Source: R1 S1, verdict VERIFIED (basis: derived)

- **Meaning.** In all four cells, ID's median paired gain over always-on PI is negative, ranging from −17.9 % to −0.7 %. In other words, the presence-triggered plan had higher median delay than PI-ALINEA running all the time.
- **Evidence.**
  - result.json eval.S1.per_cell_stats.<cell>.ID_vs.PI.all_seeds.rel: -0.1791, -0.0182, -0.0071, -0.0207
  - s1_recompute.py identical; CIs [-35.1,-6.7], [-5.2,0.0], [-10.1,6.7], [-6.6,0.0]
- **Verification.** Recomputed from raw per-seed delays; the values are exact.
- **Failure points.** 'Never better' is true for the point estimates and for the intervals (none lies above zero). In block_q1600 the interval still allows ID to be up to 6.7 % better. Only slow_q1600 is clearly worse at the S1 level. At q2000 the two arms run the same controller (7 seeds give hash-identical runs), so the difference measures only the N-before-onset period.

#### Source: R1 FU1 (FU1-C5), verdict VERIFIED (basis: derived)

- **Meaning.** In all four cells the presence-only plan is slightly or clearly worse than always-on PI.
- **Evidence.**
  - FU1/drain_audit.out: ID vs PI D -17.9, -1.8, -0.7, -2.1; W -7.2, -1.6, +0.6, -3.3; F -14.5, -1.7, -0.9, -1.9
- **Verification.** Recomputed from raw runs (FU1/drain_audit.py).
- **Failure points.** On window TTT, block_q1600 shows +0.6 %, a trivial reversal well inside its CI. Otherwise the result holds on every metric.

### C66 (paper line 155): final verdict **PARTIALLY SUPPORTED**

> S1b passes: knowing the type added 11.8 % [5.8, 16.7] (slowdown, 2000 veh/h) and 22.0 % [8.8, 31.4] (lane crawl, 1600 veh/h) over presence alone.

**Reconciliation:** Numbers and PASS reproduced exactly (two independent derivations). Attribution to "type knowledge" depends on the pooled-median ID rule (alternative type-blind rules: block_q1600 gain 0.0-2.8 %), and 83 % of the slow_q2000 gain is realised in the uncontrolled drain (window-TTT rel 1.7 %).

#### Source: R1 S1, verdict VERIFIED (basis: derived)

- **Meaning.** Using a stored plan per incident type (IP) instead of one plan for all incidents (ID) cut median delay by 11.8 % in the slowdown/2000 cell and by 22.0 % in the crawl/1600 cell. The 99.375 % intervals on rel lie above zero in both cells. In the other two cells, IP is not worse by more than 5 %.
- **Evidence.**
  - result.json eval.S1.per_cell_stats.slow_q2000.IP_vs_ID.all_seeds: rel 0.1183, rel_ci [0.0583, 0.1674], diff 44.5 s/veh, diff_ci [21.6, 63.3]; block_q1600: rel 0.2199, rel_ci [0.0884, 0.3138], diff 56.7, diff_ci [21.4, 84.8]
  - S1b_pass true, S1b_cells_both_views [slow_q2000, block_q1600]
  - robustness.py: over 20 RNG seeds, rel lower bound 5.4-5.8 and 7.3-8.9; diff lower bound >= 17.0 s/veh
- **Verification.** I recomputed the values exactly and checked their sensitivity to the bootstrap RNG. The point rel moves by at most ±0.4 points when one seed is left out. In slow_q2000, it takes 8 adversarially removed seeds to bring the point rel below 10 %.
- **Failure points.** The lower bounds (5.8 % and 8.8 %) are below 10 %. The rule shows a gain above zero with a point estimate of at least 10 %; it does not show a gain of at least 10 %. The 8.8 bound has about ±0.8 points of Monte Carlo error at B = 20,000. In block_q1600, part of the 'type' gain comes from changing controller family: IP uses a PI law and ID an integral FB law.

#### Source: R1 FU1 (FU1-C3), verdict PARTIALLY SUPPORTED (basis: derived)

- **Meaning.** Under the pre-registered rule, a plan chosen for the incident type cuts median delay against a plan that knows only that an incident is on, by at least 10 % in at least one cell with a positive lower bound. The paper attributes the 11.8 % and 22.0 % to the type information.
- **Evidence.**
  - docs/research/results/p1b_result.json eval/S1/per_cell_stats/{slow_q2000,block_q1600}/IP_vs_ID/all_seeds rel 0.1183 [0.0584,0.1674], 0.2199 [0.0884,0.3138]
  - FU1/drain_audit.out: D 11.8 [5.3,16.6], 22.0 [7.5,31.3]; post share of mean dTTT 0.83 [0.77,0.87], 0.67 [0.63,0.70]; per-seed median share 0.87, 0.69
  - FU1/drain_audit.out S1 verdicts: W (window TTT) S1b FAIL (1.7 %, 9.9 %); F (full TTT) S1b PASS (10.3 %, 18.6 %)
  - FU1/drain_dynamics.out: arm-neutral drain price k=1: 6.0 % (LCB 0.54), 19.0 % (LCB 2.95)
  - FU1/metric_ideal.out: two-arm model, 44 % (slow_q2000) and 8 % (block_q1600) of the post difference not explained by n_left
- **Verification.** I recomputed the rels on delay, window TTT and full TTT with my own bootstrap at level 0.99375 and applied rule (a)/(b) for S1b on each metric. I split the paired TTT differences additively into the control window and the drain, and fitted drain-price models (FU1/drain_audit.py, drain_dynamics.py, metric_ideal.py).
- **Failure points.** 1. On the pre-registered delay metric, the numbers and the PASS reproduce; CI ends differ by up to 1.3 points, from bootstrap tail noise or method. 2. The PASS survives full TTT and an arm-neutral drain price, because block_q1600 alone suffices. 3. It does not survive the protocol's own fixed-window TTT co-metric. 4. The slowdown-2000 figure is mostly drain-dependent: 83 % of it accrues after control ends, 44 % of that is arm-specific drain behaviour, and an arm-neutral price gives 6.0 %. The wording 'knowing the type added' omits this.

#### Source: R2 FU2 (C66), verdict PARTIALLY SUPPORTED (basis: derived)

- **Meaning.** Under the pre-registered R(IP, ID), the type-specific plan IP beats the single presence plan ID in two cells. The sentence credits the gain to type information.
- **Evidence.**
  - FU2-1/s1_indep.out: IP vs ID delay 11.8 % relCI [5.8,16.7] diff LCB 21.56; 22.0 % [8.8,31.4] LCB 21.40; S1b PASS in both views (exact match to p1b_result.json)
  - FU2-1/s1_indep.out: window TTT (ttt_ctrl_vehh) IP vs ID 7.4/1.7/9.9/0.0 %, no a-cell, S1b FAIL; full TTT PASS (10.3 %, 18.6 %)
  - FU2-1/s1_indep.out: arm medians slow_q2000 ID 375.7 vs IP 353.2 = 6.0 %; mean rel 9.1 %
  - FU2-1/s1_indep.out drain split: post-940 s share of mean paired TTT gain 0.83 (slow_q2000), 0.67 (block_q1600); FU2-1/drain_nleft.out arm-specific residual share 0.43 and 0.08
  - FU2-1/id_rule_sens.out: q1600 ID f40_10 tuning medians slow 204.5 / block 244.7, ranks 10 and 7 of 120, dominated by p70_40_10_e4 (203.4/239.4) and p20_20_12_e4 (202.5/242.3)
  - FU2-1/id_rule_sens.out: block_q1600 IP vs ID = 2.8 % (pooled mean / mean of per-type medians, ID p20_20_14_e4), 0.0 % (max of per-type medians, ID p20_20_16_e4 = IP plan); pooled mean also changes q2000 ID to p70_40_10_e4 and S1b has no a-cell (FAIL)
  - v5b/p1b/analysis.py@93ba655:139-140 (pooled-median ID), :354 (paired(r=ID, t=IP)); protocol p1_incident_information.md:36,43 (rule pre-registered); paper.qmd:118 does not state the rule
- **Verification.** Own numpy recomputation from 800 evaluation runs plus the tuning runs. I used the repo bootstrap convention (seed 20261019, B 20,000, level 0.99375) and both views. I re-ran S1b on three metrics and under three alternative type-blind ID rules chosen on tuning seeds only.
- **Failure points.** The numbers and the pre-registered PASS are exact. 'Knowing the type added X over presence alone' does not match as written. (1) The 22.0 % is measured against f40_10, a plan that two other plans beat in both incident types on the tuning seeds. Other type-blind rules shrink it to 2.8 % or 0.0 %, and the pooled-mean rule makes S1b FAIL. (2) The 11.8 % is 6.0 % in arm medians and 1.7 % on window TTT. 83 % of the TTT gain comes after control ends, and 43 % of that is arm-specific. (3) The paper does not state the ID tuning rule and omits the TTT co-metric. The sensitivity rules are post hoc, and the rule that was used is pre-registered. Resolution: the S1 tracer's VERIFIED is overruled; FU1-C3's PARTIALLY SUPPORTED is kept.

#### Source: R2 FU2 (FU1-C3), verdict PARTIALLY SUPPORTED (basis: derived)

- **Meaning.** Same sentence as C66.
- **Evidence.**
  - See C66; FU2-1/s1_indep.out, FU2-1/id_rule_sens.out, FU2-1/drain_nleft.out
- **Verification.** Merged into C66. I reproduced FU1's window-TTT FAIL, the 0.83/0.67 drain shares and the 43 %/8 % arm-specific shares.
- **Failure points.** Merged into C66. The ID-rule sensitivity (CTRL-F1) is a second reason, independent of FU1's drain and co-metric reasons.

### C67 (paper line 155): final verdict **VERIFIED**

> Against always-on PI, IP's interval lay above zero only for the lane crawl at 1600 veh/h: 18.0 % [8.9, 31.6] (report-only row).

**Reconciliation:** 18.0 % [8.9, 31.6] exact; the "only" holds across 20 bootstrap seeds.

#### Source: R1 S1, verdict VERIFIED (basis: derived)

- **Meaning.** Comparing the type plan with always-on PI-ALINEA, the 99.375 % interval is above zero only in the crawl/1600 cell, where the median gain is 18.0 %. This comparison is descriptive and was not one of the pre-registered statements.
- **Evidence.**
  - result.json eval.cells.<cell>.IP_vs_L0.PI.all_seeds: rel 4.5/7.4/18.0/-2.1 %, rel_ci lower -35.2/-2.7/8.9/-6.6 % at level 0.99375
  - v5b/p1b/analysis.py@93ba655:355 ip_vs_l0 at LEVEL_S1; protocol line 101 'IP vs each L0 arm is reported (descriptive)'
- **Verification.** Recomputed exactly. Across 20 RNG seeds, the slow_q2000 lower bound stays between −4.0 and −2.6, so the 'only' holds.
- **Failure points.** 'Only' depends on using the Bonferroni level for a report-only row. At 95 %, slow_q2000 would also lie above zero ([3.0, 11.7]). The paper's caption says 'at the S1 level', so this is disclosed, but the text does not repeat it.

#### Source: R1 FU1 (FU1-C6), verdict VERIFIED (basis: derived)

- **Meaning.** The type plan beats tuned always-on PI clearly only in the lane-crawl cell at 1600 veh/h.
- **Evidence.**
  - FU1/drain_audit.out: IP vs PI block_q1600 D 18.0 [9.1,31.1], W 10.5 [4.2,16.6] (LCB 0.98 > 0), F 14.9; post share 0.57 [0.51,0.62]; slow_q2000 W 0.1 %
  - FU1/metric_ideal.out: two-arm model, arm-specific drain share 0.11; FU1/drain_dynamics.out k=1 13.0 %
- **Verification.** Recomputed on 3 metrics, plus the drain split and drain-price sensitivity.
- **Failure points.** Robust: the row passes rule (a) even on fixed-window TTT, and only 57 % of it accrues after control ends. The slow_q2000 IP vs PI 7.4 % row is 92 % post-control (0.1 % on window TTT), but the paper does not claim that row.

### C68 (paper line 160): final verdict **PARTIALLY SUPPORTED**

> Fig. 2: median delay along the information ladder in the four cells: strongest always-on arm (L0), ID, IP, and the two bounds on per-incident hindsight (ORX_4 low, OR_in high); 100 seeds per cell.

**Reconciliation:** All 20 bars exact, but the ORX_4 and OR_in bars are marginal medians, not the bounds reported in Table II (paired CI ends; mean version for ORX).

#### Source: R1 REPRO, verdict PARTIALLY SUPPORTED (basis: derived)

- **Meaning.** Each panel shows, for one incident type and demand level, the median delay per vehicle of five arms. The arms are the best always-on controller, the presence-only switch (ID), the type-aware switch (IP), the cross-fitted hindsight oracle with 4 replicates (ORX_4), and the in-sample hindsight oracle (OR_in). Each median is over the same 100 evaluation seeds. The caption calls the last two bars the lower and upper bounds of the value of per-incident knowledge.
- **Evidence.**
  - papers/paper_1/figures/fig_ladder.py@HEAD:14 reads eval.fig1_ladder; :21-27 plots rungs[*].median_delay_s
  - v5b/p1b/analysis.py@93ba655:376-380: strongest = min over L0=(N,FX,FB,PI,AD) of the marginal median on the evaluation seeds; rungs = [strongest, ID, IP, ORX_max(R), OR_in]
  - analysis.py@93ba655:236-276 cell_runs / or_in / orx (ORX: best mean over replicates k=1..R, scored on the main run; ties in A order)
  - p1b_result.json eval.fig1_ladder: strongest L0 = PI, PI, FB, PI for slow_q1600, slow_q2000, block_q1600, block_q2000; e.g. block_q1600 FB 247.87, ID 257.93, IP 210.78, ORX_4 200.92, OR_in 160.82
  - v5b/p1/stats.py@e7dd561:112-127 s2_cell: the S2 bracket is x = upper 98.75 % CI of median-rel(IP, OR_in) and y = lower 98.75 % CI of MEAN-rel(IP, ORX_4), which is not what the bars show
- **Verification.** Re-ran fig_ladder.py from a scratch copy: pixel-identical to the repo PDF. scratch/fig2_recompute.py, my own code, rebuilt the run keys from 242,400 raw P1b files and recomputed all 20 medians, the strongest-L0 choice, OR_in and ORX_1/2/4. All match the JSON exactly (diff 0.0), n = 100 per cell, all files at 93ba655. scratch/fig2_vs_paired.py then compared the gaps between bars with the paper's paired statistic median(r-t)/median(r). The gaps differ, sometimes in sign. slow_q1600 IP vs PI: bars -0.3 %, paired +4.5 % (Table II 4.5). ORX_4 vs IP: bars +8.9 %, paired -0.5 %, while the S2 lower bound in Table II is -0.4 %. OR_in vs IP: bars +32.6 %, paired +15.1 %.
- **Failure points.** The plotted values, the arm choice and n = 100 are exact. Overstatement: the bars are marginal medians of the ORX_4 and OR_in arms, not the bounds the paper reports. The S2 bracket in Table II and line 193 uses CI ends of paired statistics, and the mean version for ORX. A reader who reads gains off Fig. 2 gets different numbers, and in slow_q1600 even a different sign. 'Strongest L0' is chosen in-sample on the evaluation seeds by marginal median; this is conservative for IP and only descriptive. Test: plot paired rel with CIs per rung, or state in the caption that the bars are marginal medians and that the bounds are in Table II.

### C69 (paper line 174): final verdict **PARTIALLY SUPPORTED**

> Table II rows: ID vs PI (-17.9, -1.8, -0.7, -2.1); IP vs ID (16.2, 11.8 bold, 22.0 bold, 0.0); IP vs PI (4.5, 7.4, 18.0 bold, -2.1); bold = interval above zero at the S1 level.

**Reconciliation:** All 12 values and the bold pattern exact; the caption's sign convention is inverted (positive favours the FIRST-named arm).

#### Source: R1 S1, verdict VERIFIED (basis: derived)

- **Meaning.** Table II rows 1-3 give rel in % for each comparison in the four cells. Bold marks cells where the 99.375 % interval lies above zero.
- **Evidence.**
  - paper.qmd:174-176; paper.pdf Table II (pdftotext) identical
  - s1_recompute.py output rows ID_vs_PI, IP_vs_ID, IP_vs_PI; lower bounds > 0 only in IP_vs_ID slow_q2000, block_q1600 and IP_vs_PI block_q1600; block_q2000 IP_vs_ID is [0.0, 0.0] (identical runs), correctly not bold
  - paper.qmd:165 caption 'positive favours the second arm'
- **Verification.** Every number recomputed from raw runs; rounding to 0.1 checked (for example, −1.80/252.1 = −0.71 %). The bold pattern was checked against both CI types.
- **Failure points.** The numbers and bold marks are correct. The caption's sign statement is inverted (see S1-F1), and the 'ID vs PI (S1a)' row hides that FB also blocks S1a (S1-F8).

#### Source: R2 FU2 (C69), verdict PARTIALLY SUPPORTED (basis: direct observation)

- **Meaning.** Rows 1-3 give rel in % per cell, with bold where the 99.375 % interval is above zero. The caption tells the reader how to read the sign.
- **Evidence.**
  - FU2-1/s1_indep.out: all 12 values reproduce to 0.1; bold pattern identical for diff-CI and rel-CI lower bounds (only IP vs ID slow_q2000, block_q1600 and IP vs PI block_q1600)
  - v5b/p1b/analysis.py@93ba655:353-355 passes the second-named arm as reference r and the first-named as t; v5b/p1/stats.py@93ba655:52,63 rel = median(r - t)/median(r): positive favours the first-named arm
  - paper.qmd:145 'positive values favour arm t over reference r'; paper.qmd:165 and paper.pdf Table II caption 'positive favours the second arm'
- **Verification.** Recomputed every cell from raw runs and read the sign convention in the code that ran.
- **Failure points.** The numbers and bold marks are correct. Read with its caption, the table states the opposite direction in every row: 'IP vs ID 22.0' would mean ID is better. The row label 'ID vs PI (S1a)' also hides that FB blocks S1a too (S1-F8). The S1 tracer's VERIFIED is overruled.

### C70 (paper line 187): final verdict **VERIFIED**

> The lane-crawl cell at 1600 veh/h was tested once on 100 fresh seeds.

**Reconciliation:** Seeds 7,400,700-799 unused before C1; one launch.

#### Source: R1 PROV, verdict VERIFIED (basis: direct observation)

- **Meaning.** The confirmation ran exactly one time, in the block-incident cell at 1,600 veh/h, on 100 seeds that had never been simulated before.
- **Evidence.**
  - P1B_C1_STARTED.json 2026-10-20 21:27:50 (resume false); p1b_c1/v114/run.log: '1100 runs to do (0 reused)', 'failed 0'; one p1b-c1.service start in journalctl
  - result.json cell block_q1600; seeds [7400700, 7400799]; n_runs 1100; invalid/teleport/collision 0
  - grep of all ~/work/phd/v5b1_runs outputs: 74007xx appears only in p1b_c1/v114 and in job prompt texts; C1 smoke used 7400000-003
- **Verification.** Scanned all run directories and logs for the C1 seeds; read the sentinel, the log and the journal.
- **Failure points.** The frozen worktree was deleted. The same sentence's 'same result when seeds with invalid runs are excluded' is true only trivially: C1 had 0 invalid runs, so both views are identical by construction.

### C71 (paper line 187): final verdict **PARTIALLY SUPPORTED**

> C1 is confirmed: the type plan reduced median delay relative to always-on PI by 16.2 % [7.3, 23.7] (41.4 s/veh [16.6, 65.7]).

**Reconciliation:** Numbers reproduced exactly (two independent derivations; 4 spot re-runs bit-identical). Caveats: it is the median of paired differences over median(PI) (the medians differ by 17.3 %); the comparator PI is Pareto-dominated, on grid edges and not the strongest L0 arm (FB); the gain reverses for incidents shorter than about 230 s; it rests on the no-lane-change crawl and on PI sitting at the 200 veh/h floor.

#### Source: R1 C1, verdict VERIFIED (basis: derived)

- **Meaning.** On 100 new seeds in the lane-crawl cell at 1600 veh/h, two controllers were compared seed by seed. IP runs a constant rate until the incident starts and then a PI law tuned for this incident type. PI is the always-on PI controller. The paper reports the median of the per-seed delay differences (PI minus IP) divided by PI's median delay, with a bootstrap 95 % CI. The pre-fixed rule says C1 is confirmed if this point estimate is at least 10 % and the CI lower bound of the median difference in s/veh is above zero.
- **Evidence.**
  - v5b/p1b/confirm_c1.py@e7dd561:49-58 (cell, arms N=c1800, IP_PLAN=p20_20_16_e4, PI=p70_120_8_e4, SEEDS 7,400,700-799, B=20,000, BOOT_SEED_C1=20261020, LEVEL 0.95, REL_MIN 0.10)
  - v5b/p1b/confirm_c1.py@e7dd561:121-136 (c1_view, statement_c1); v5b/p1/stats.py@e7dd561:48-64 (paired)
  - raw per-seed delay_s: ~/work/phd/v5b1_runs/p1b_c1/v114/runs/p70_120_8_e4_block_q1600_s74007NN.json and c1800-p20_20_16_e4_block_q1600_s74007NN.json
  - ~/work/phd/v5b1_runs/p1b_c1/v114/result.json c1.C1.all_seeds: rel 0.1625, rel_ci [0.0731, 0.2368], diff 41.373, diff_ci [16.612, 65.685], n 100, pass True; decision CONFIRMED
  - protocol docs/research/protocols/p1b_confirm_c1.md (identical at e7dd561 and HEAD), approved in 7c6acc8 21:11:24 before the code commit e7dd561 21:16:00 and the run at 21:27:50 (P1B_C1_STARTED.json; run.log: 1100 runs, 0 reused, 0 failed)
  - P1b raw tuning runs ~/work/phd/v5b1_runs/p1b/v108/runs (seeds 7,400,300-339, q1600): N c1800 clean median 44.74; PI p70_120_8_e4 pooled median 210.05; IP block p20_20_16_e4 median 224.74 (runner-up p20_20_14_e4 224.89)
- **Verification.** Independent numpy recomputation from the raw run JSONs (c1_recompute.py): rel 16.2 % [7.3, 23.7], diff 41.37 [16.61, 65.69], n 100. This is identical to result.json and to the committed p1b_c1_result.json (full JSON equality). The rule holds: 16.25 % >= 10 % and 16.61 > 0. Robustness checks: other bootstrap seeds give the same lower bounds, with the upper diff bound between 63.3 and 65.7. Leave-one-out rel ranges over 15.5-17.0 %. Dropping the 10 seeds most favourable to IP gives 12.3 %. IP is better on 67/100 seeds (sign test p = 4e-4). Frozen arms re-derived from the raw P1b tuning runs (tune_check.py): they match. Seeds: no overlap with any P1 or P1b seed, or their replicate RNG seeds (seed_overlap.py), and no run filename under v5b1_runs uses 7,400,700-999.
- **Failure points.** (1) Wording: 'reduced median delay by 16.2 %' is not the difference of medians. That would be (254.7 - 210.6)/254.7 = 17.3 %, or 44.1 s/veh. The 16.2 % is the median paired difference over median(PI), as defined at line 145. (2) The rule tests the point estimate >= 10 %, not the CI. The rel CI lower bound of 7.3 % does not exclude gains below 10 %. (3) The upper diff CI bound depends on the bootstrap seed (discreteness of the median of 100). (4) One cell, one plant. The cell and arms were chosen after seeing P1b data (see finding C1-F1). Test: rerun c1_recompute.py; compute the difference of medians.

#### Source: R1 FU1 (FU1-C7), verdict VERIFIED (basis: derived)

- **Meaning.** On 100 fresh seeds, the pre-fixed confirmatory statement (rel ≥ 10 % and positive 95 % lower bound) holds for IP vs PI in the lane-crawl 1600 cell.
- **Evidence.**
  - FU1/drain_audit.out C1 IP vs PI: D 16.2 [7.3,23.7]; W 11.7 [6.9,14.0], LCB diff 1.60 veh.h; F 13.8 [6.1,20.2]; post share 0.55 [0.47,0.62]
  - FU1/c1_diff.out: median diff 41.37 s/veh, 95 % CI [16.61, 65.08-65.69]
  - FU1/metric_ideal.out: arm-specific drain share -0.04
  - FU1/drain_dynamics.out: k=1 14.9 %, k=0.6 14.5 %
- **Verification.** Recomputed from C1 raw runs (code e7dd561) on delay, window TTT, full TTT and the drain-price variants.
- **Failure points.** C1 holds on every metric tested, including fixed-window TTT. 55 % of the gain accrues after control ends, but that part is explained by IP leaving 13 fewer vehicles at 940 s (in-window served +52 [12, 100] veh/h), not by arm-specific drain behaviour.

#### Source: R2 G2, verdict PARTIALLY SUPPORTED (basis: derived)

- **Meaning.** Mechanism and interpretation side only. IP runs N (c1800) and switches at onset to p20_20_16_e4 (K_P 20, K_I 20, n_crit 16 on the edge-4 count) for the rest of the run. Always-on PI is p70_120_8_e4 (n_crit 8). Both hold all four lanes with one signal state.
- **Evidence.**
  - G2/g2_c1_recheck.out: rel 16.2 % [7.3, 23.7], diff 41.37 [16.61, 65.08] (own bootstrap; the upper bound depends on the bootstrap seed)
  - G2/g2_mechanism.out C1: entered_e4_incident median PI 45, IP 85, NC 85; time-weighted q during the incident PI 770, IP 1801 veh/h; min q PI 200, IP 1070; IP lets more vehicles onto edge 4 in 99/100 seeds; Spearman(d delay, d e4) 0.67
  - G2/g2_actions_traj.out: PI q = 200 from +120 s after onset until clearance; IP q 1800-2040 for the first 180 s; IP holds 480-890 for about 200 s after clearance; N's edge-4 count reaches 60 after clearance
  - G2/g2_spot_lanes.out: free-path exits during the incident 724->424 and 548->213 veh/h (IP->PI); free-path share of IP's time-loss lead 61 % and 90 %
  - G2/g2_duration_split.out: C1 IP vs PI -19.2 % [-45.5, -6.5] for 120-240 s incidents and +33.8 % for 360-480 s
  - G2/g2_mechanism.out TUNING block_q1600: always-on p20_20_16_e4 222.0 vs IP 224.7 vs PI 293.4; slow_q1600: PI 189.4 vs gentle law 226.7
  - v5b/p1b/meters.py@93ba655:34, 104-112; v5b/p1/family.py@93ba655:11-13
- **Verification.** Recomputed the C1 statistic with my own code. Derived per-run q and edge-4 count over the incident window from meter_log, and entered_e4_incident from the raw JSONs. Made paired comparisons and correlations, split per lane group in the spot tripinfo files, and ran an exploratory split by incident duration.
- **Failure points.** The numbers are verified. What they mean is narrower than the framing 'knowing the type pays'. In this cell, the type is used to switch to a law that does not react to the crawl. PI's edge-4 detector counts the vehicles stored on the crawl lane, so PI throttles all four lanes to 200 veh/h, mainly delaying vehicles bound for the free lane 4_0. The gain reverses for short incidents (post hoc) and grows with duration. It depends on the no-lane-change split of lanes and on the edge-4 detector. Whether it holds with lane changing is untested (needs BN4-L runs). The 2 spot seeds are indicative only.

#### Source: R2 FU2 (C71), verdict PARTIALLY SUPPORTED (basis: derived)

- **Meaning.** On 100 fresh seeds in crawl-1600, the pre-fixed rule (rel >= 10 % and 95 % diff LCB > 0) holds for IP vs PI. The sentence describes the result as a cut in median delay.
- **Evidence.**
  - FU2-1/c1_indep.out: paired rel 16.25 % [7.3, 23.7], median diff 41.37 [16.61, 65.69], 0 invalid seeds (match to v114 result.json c1.C1)
  - FU2-1/c1_indep.out: arm medians PI 254.68, IP 210.57: change of medians 17.32 % (44.11 s/veh); mean rel 15.94 %; IP better on 67/100 seeds
  - FU2-1/c1_indep.out: window TTT 11.66 % [6.8, 14.1], diff LCB 1.58 veh.h; full TTT 13.85 % [6.0, 20.2]
  - v5b/p1b/confirm_c1.py@e7dd561:49-58,121-136
- **Verification.** Own recomputation from the 200 main C1 runs, with bootstrap seed 20261020 and level 0.95, on 3 metrics.
- **Failure points.** CONFIRMED is correct and robust to the TTT co-metrics. 'Reduced median delay by 16.2 % (41.4 s/veh)' does not match as written. Median delay fell by 17.3 % (44.1 s/veh). The 16.2 % is the median paired difference over PI's median, as defined at line 145. The mismatch is small and understates the gain. The clause about excluding invalid seeds is vacuous: there are 0 invalid seeds (HEADLINE-F5). The post-hoc choice of cell and arms (C1-F1) affects what 'confirmed' means. Resolution: the VERIFIED verdicts of the C1 tracer and FU1-C7 are overruled; G2's PARTIALLY SUPPORTED is kept.

#### Source: R2 FU2 (FU1-C7), verdict PARTIALLY SUPPORTED (basis: derived)

- **Meaning.** Same sentence as C71.
- **Evidence.**
  - See C71; FU2-1/c1_indep.out
- **Verification.** Merged into C71.
- **Failure points.** FU1 checked robustness across metrics, which holds. The wording mismatch (16.2 % vs 17.3 %) still breaks 'as written'.

### C72 (paper line 187): final verdict **PARTIALLY SUPPORTED**

> ...with the same result when seeds with invalid runs are excluded.

**Reconciliation:** True but empty: no C1 run was invalid, so nothing was excluded.

#### Source: R1 C1, verdict PARTIALLY SUPPORTED (basis: derived)

- **Meaning.** The protocol requires C1 to hold in two views: all seeds, and only seeds where both the IP run and the PI run were valid. A run is valid if the network drained, every generated vehicle has a trip record, and SUMO health is not FAIL. The paper says the second view gives the same result.
- **Evidence.**
  - v5b/p1b/episode.py@93ba655:255 valid = drained and len(trips) == gen and health != FAIL
  - v5b/p1b/confirm_c1.py@e7dd561:127-136 (keep = ~invalid)
  - result.json: invalid_runs 0, teleport_runs 0, collision_runs 0, c1.C1.n_invalid_seeds 0; valid_only == all_seeds (n 100)
- **Verification.** Counted the valid flags in all 1,100 raw C1 runs (c1_recompute.py, integrity block): 0 invalid in every row and 0 teleports. Health codes are WARN-only (H-R4b 1081, H-R4e 144, H-R5 55, H-R2 3); WARN does not make a run invalid. So the valid-only view equals the all-seeds view by construction.
- **Failure points.** The statement is true but empty: no seed was excluded, because no run was invalid. The wording suggests that some seeds were removed and the result survived. Better wording: 'no run was invalid'. If invalid runs had existed, the sensitivity would be real; here it tests nothing.

### C73 (paper line 187): final verdict **VERIFIED**

> The lead held with detection delays of 30-120 s (12.5-16.4 %).

**Reconciliation:** 15.5 / 16.4 / 12.5 % with 95 % CIs above 0. The tolerance comes from a slow-acting plan whose action is set by the traffic state, not the switch time (G3R-F4).

#### Source: R1 C1, verdict VERIFIED (basis: derived)

- **Meaning.** In C1, the type plan was also run with the switch delayed by 30, 60 or 120 s after the incident starts (late detection). Each delayed run was compared with always-on PI on the same seeds. 'The lead held' means IP still had lower median delay, with the 95 % CI of the median difference above zero. The protocol lists these rows as descriptive, so they are not claims.
- **Evidence.**
  - protocol p1b_confirm_c1.md 'Reported, descriptive (no claims)': IP vs PI with d in {30, 60, 120} s (pre-registered as descriptive)
  - v5b/p1b/confirm_c1.py@e7dd561:71-77 (ip_spec via canon_sw), 179-183 (rows PI_vs_IP_d*, IP_vs_IP_d*, n_no_switch)
  - result.json c1.descriptive: PI_vs_IP_d30 rel 15.5 [7.9, 21.7], diff 39.50 [18.11, 60.73]; PI_vs_IP_d60 16.4 [10.8, 25.5], diff 41.88 [25.33, 72.10]; PI_vs_IP_d120 12.5 [5.7, 25.0], diff 31.84 [13.37, 68.75]; n_no_switch 0
  - raw runs c1800-p20_20_16_e4_d{30,60,120}_block_q1600_s74007NN.json: t_switch - t_on = d exactly for all 100 seeds
- **Verification.** Recomputed independently (c1_recompute.py, bootstrap seed 20261019 as used by the code): numbers identical to result.json. All three diff CIs lie above 0 at 95 %, and still do at 99 % (Bonferroni over the 5 IP-vs-PI descriptive rows; c1_desc_sens.py). The rel CI lower bound is >= 10 % only for d = 60 (10.8 %); it is 7.9 % for d = 30 and 5.7 % for d = 120. IP_d vs IP: -0.7, +0.2 and -1.5 %, all CIs include 0, so detection delay barely changes IP.
- **Failure points.** (1) These rows are descriptive. The paper does not label them as such at line 187. (2) 'Held' is true for a lead above 0, not for a lead of 10 % or more (the CIs for d = 30 and d = 120 reach below 10 %). (3) The near-zero effect of the delay follows from the design. The stay plan runs from onset to the end of control, and in the median seed 52 % of the control period lies after clearance. The gain therefore does not come from fast switching (see finding C1-F5).

#### Source: R1 FU1 (FU1-C8), verdict VERIFIED (basis: derived)

- **Meaning.** The C1 advantage stays above about 12 % when detection is late by up to 2 minutes, and grows when some drivers run the amber or red.
- **Evidence.**
  - FU1/drain_audit.out: IP_d30/d60/d120 vs PI D 15.5/16.4/12.5, W 10.5/10.7/9.9, post shares 0.56-0.57; IP_s0.1 vs PI_s0.1 D 24.4 (W 14.8), IP_s0.3 vs PI_s0.3 D 27.6 (W 15.3), post shares 0.59-0.61
- **Verification.** Recomputed from C1 raw runs.
- **Failure points.** The numbers match. On window TTT the rows are 9.9-15.3 %, and 56-61 % of each gain accrues after control ends. The direction holds; the sizes depend on the end-of-horizon convention. I did not check 'PI itself degraded'.

#### Source: R2 G5, verdict VERIFIED (basis: derived)

- **Meaning.** In C1 (block_q1600, fresh seeds 7,400,700-799), IP switched 30, 60 or 120 s after onset still had lower median delay than always-on PI, with the 95 % CI above 0.
- **Evidence.**
  - v5b/p1b/confirm_c1.py@e7dd561:71-77 (ip_spec: canon_sw with d only, stay plan p20_20_16_e4)
  - p1b_confirm_c1.md:29 (d rows pre-registered as descriptive)
  - raw C1 runs: t_back None, back False, c=0, t_switch = first tick >= t_on+d in 100/100 runs for d = 0, 30, 60, 120 (g5_schedules.log)
  - own recompute (seed 20261019): d30 15.5 [7.9, 21.7], d60 16.4 [10.8, 25.5], d120 12.5 [5.7, 25.0]; equal to p1b_c1_result.json
- **Verification.** Recomputed the C1 delay rows from raw files with my own bootstrap: identical to the JSON. Checked that the C1 plan never returns, so clearance detection plays no role.
- **Failure points.** Clearance is irrelevant in this cell (stay plan), so the sentence does not overstate anything about clearance. The rows are descriptive, and the lead is above 0 but not >= 10 % at the lower CI bound for d=30 and d=120. Misclassification was not tested in C1. On the P1b seeds, the same cell at p=0.2 gives IP vs PI 6.1 % [-2.1, 17.5] and vs FB 0.5 % [-5.3, 7.3]. The combined row gives vs FB 0.5 % [-6.1, 7.8]. The 'lead' is therefore robust to onset delay, not to type errors.

### C74 (paper line 187): final verdict **VERIFIED**

> ...and with red-light runners (24.4 % at s = 10 %, 27.6 % at s = 30 %), where always-on PI itself degraded.

**Reconciliation:** 24.4 % and 27.6 % exact; PI vs itself -8.5 % and -11.0 % (95 % CIs below 0).

#### Source: R1 C1, verdict VERIFIED (basis: derived)

- **Meaning.** In C1 a share s of drivers was made to ignore the amber and the first 1.5 s of red. Both arms were run with these runners. IP's lead over PI grew to 24.4 % at s = 10 % and 27.6 % at s = 30 %. The claim adds that PI's own delay rose with runners compared with PI at s = 0, so the larger lead comes from PI getting worse.
- **Evidence.**
  - protocol p1b_confirm_c1.md: 'IP vs PI with runner share s in {10 %, 30 %}' descriptive (pre-registered as descriptive); the PI-vs-PI_s rows are not in the protocol text but in the code committed before data: confirm_c1.py@e7dd561:184-186
  - result.json c1.descriptive: PI_s0.1_vs_IP_s0.1 24.4 [21.1, 29.8], diff 65.87 [55.19, 84.55]; PI_s0.3_vs_IP_s0.3 27.6 [18.6, 30.9], diff 79.52 [50.01, 91.81]; PI_vs_PI_s0.1 -8.5 [-11.7, -1.0]; PI_vs_PI_s0.3 -11.0 [-17.4, -4.0]; IP_vs_IP_s0.1 +1.8 [-0.0, 3.5]; IP_vs_IP_s0.3 +1.9 [-1.5, 4.7]
  - raw runs *_rs0p1_*, *_rs0p3_* (rs field 0.1 / 0.3; median n_runners 43 / 125; red-crossing share max 3.5 % / 9.3 % for IP)
  - row medians: PI 254.7 -> 270.2 (s=10 %) -> 288.6 (s=30 %); IP 210.6 -> 204.1 -> 210.7
- **Verification.** Recomputed independently (c1_recompute.py, c1_desc_sens.py): every number matches. PI's degradation has a 95 % CI below 0 at both shares. At a 99 % level the s = 10 % CI includes 0 ([-13.8, +1.1]), while s = 30 % stays below 0. IP did not degrade.
- **Failure points.** (1) Descriptive rows. The PI self-comparison was fixed in code before data but is not in the protocol text. (2) The s = 10 % degradation is marginal (95 % upper bound -1.0 %). (3) Runners change SUMO's random draws, so 'PI degraded' includes noise from non-common random numbers; pairing by seed only partly controls it. (4) Runner behaviour depends on the SUMO junction-model parameters (jmDriveAfterYellowTime 3 s, jmDriveAfterRedTime 1.5 s; runners.py@93ba655). These are model parameters, not field-calibrated.

#### Source: R1 FU1 (FU1-C8), verdict VERIFIED (basis: derived)

- **Meaning.** The C1 advantage stays above about 12 % when detection is late by up to 2 minutes, and grows when some drivers run the amber or red.
- **Evidence.**
  - FU1/drain_audit.out: IP_d30/d60/d120 vs PI D 15.5/16.4/12.5, W 10.5/10.7/9.9, post shares 0.56-0.57; IP_s0.1 vs PI_s0.1 D 24.4 (W 14.8), IP_s0.3 vs PI_s0.3 D 27.6 (W 15.3), post shares 0.59-0.61
- **Verification.** Recomputed from C1 raw runs.
- **Failure points.** The numbers match. On window TTT the rows are 9.9-15.3 %, and 56-61 % of each gain accrues after control ends. The direction holds; the sizes depend on the end-of-horizon convention. I did not check 'PI itself degraded'.

### C75 (paper line 189): final verdict **VERIFIED**

> Fig. 3: delay reduction of IP over always-on PI with 95 % CI in C1 (lane crawl, 1600 veh/h, 100 fresh seeds); the dashed line marks 10 %.

**Reconciliation:** Fig. 3 rebuilt pixel-identical from a scratch copy; values recomputed from raw runs.

#### Source: R1 REPRO, verdict VERIFIED (basis: derived)

- **Meaning.** Fig. 3 shows how much the type plan IP reduces delay compared with tuned always-on PI in the confirmation run C1. The reduction is rel = median of paired differences / median PI delay, with a two-sided 95 % bootstrap CI. Rows: the baseline, detection delays of 30/60/120 s, and 10 %/30 % red-light runners. C1 used 100 seeds never used before, and a dashed vertical line marks the 10 % threshold of the C1 statement.
- **Evidence.**
  - papers/paper_1/figures/fig_c1_robust.py@HEAD:15-22 (keys c1.C1.all_seeds; descriptive PI_vs_IP_d30/d60/d120, PI_s0.1_vs_IP_s0.1, PI_s0.3_vs_IP_s0.3), :31 axvline(10, ls='--')
  - v5b/p1b/confirm_c1.py@e7dd561:51-57 (frozen arms, seeds 7,400,700-799, B=20,000, BOOT_SEED_C1=20261020, level 0.95), :121-124 c1_view, :160 descriptive rows at st.LEVEL_95 with BOOT_SEED 20261019
  - v5b/p1/stats.py@e7dd561:35-66 paired(): joint percentile bootstrap, rel_ci = percentile of median(d*)/median(r*)
  - p1b_c1_result.json: C1 rel 0.16245 [0.0731, 0.2368], diff 41.37 [16.61, 65.69]; d30 15.51 [7.89, 21.67]; d60 16.44 [10.80, 25.52]; d120 12.50 [5.75, 24.97]; s0.1 24.38 [21.10, 29.80]; s0.3 27.56 [18.56, 30.88]; n = 100 each, 0 invalid
  - ~/work/phd/v5b1_runs/P1B_C1_STARTED.json (e7dd561, 2026-10-20 21:27:50)
- **Verification.** Re-ran fig_c1_robust.py from a scratch copy: pixel-identical to the repo PDF. scratch/fig3_recompute.py, my own code, loaded the 1,200 raw C1 files used by the 6 rows (all valid, all e7dd561) and recomputed rel, diff and the 95 % CIs. With the same RNG recipe they match the JSON to every printed digit. With an independent RNG seed the CI ends move by at most 0.3 points. scratch/c1_arm_medians.py confirmed all 11 per-arm medians (PI 254.68 -> 270.19 -> 288.58 with runners). Spot re-runs: 2 seeds x IP/PI re-simulated in systemd units from code e7dd561; delay_s and every other field are identical to the stored runs. Freshness: no file with seeds 74007xx exists in any other run directory, and confirm_1 used other seeds.
- **Failure points.** The rel CI lower bound (7.3 %) lies below the dashed 10 % line. C1 passes on point rel >= 10 % and diff-CI > 0, so a reader could misread the line as a CI threshold. The C1 cell and reference arm were chosen after seeing the P1b evaluation data; the C1 protocol discloses this, the paper does not (REPRO-F4). Reproduction depends on SUMO/libsumo 1.27.1 and on this network cache; both were checked here.

### C76 (paper line 193): final verdict **PARTIALLY SUPPORTED**

> Per-incident hindsight beyond the type plan could only be bracketed, because the bracket did not converge as R grew.

**Reconciliation:** What failed is the plateau of ORX_R (R = 2 vs 4), not "the bracket"; the +-1-point criterion needs a CI width <= 2 points, unreachable at n = 100 (widths 4.0-15.1).

#### Source: R1 S23, verdict PARTIALLY SUPPORTED (basis: derived)

- **Meaning.** The protocol allowed a point value ('adds about y_hat %') only if the lower-bound estimator ORX stopped changing between R = 2 and R = 4 replicates: the 95 % CI of rel_mean(ORX_2, ORX_4) had to lie within +-1 point. This check failed, so only the interval [y, x] may be stated.
- **Evidence.**
  - v5b/p1/stats.py@93ba655:123-125 (plateau = paired(orx[2], orx[4], 0.95, mean=True); ok iff CI within +-PLATEAU_Z = 0.01)
  - result.json eval.S2.<cell>.all_seeds.plateau_holds = false in all 4 cells
  - own recompute (s23_recompute_20261019.log): plateau rel 12.03 [4.31, 19.44] (slow_q1600), 1.37 [-1.60, 4.17] (slow_q2000), 4.33 [1.22, 7.46] (block_q1600), 2.71 [0.72, 4.75] (block_q2000); CI widths 15.1, 5.8, 6.2, 4.0 points
  - ORX_R mean rel by R=1,2,4: slow_q1600 -11.5, -0.2, 11.9; slow_q2000 -6.5, 0.05, 1.4; block_q1600 -2.6, 2.0, 6.3; block_q2000 4.65, 3.95, 6.55
- **Verification.** Recomputed OR_in, ORX_1/2/4 and the plateau CI from the raw main and replicate run files (120 actions x 5 runs x 100 seeds per cell) with my own bootstrap. Exact match to result.json; stable under bootstrap seed 777.
- **Failure points.** (1) What failed is the plateau of the lower estimator ORX_R (R=2 vs 4). OR_in, the upper end, does not depend on R, so 'the bracket did not converge' misnames the test. (2) The criterion needs a CI width of 2 points or less; the achieved widths were 4.0-15.1 points, so it could not pass in any cell even with a zero point estimate. (3) Non-convergence is shown (CI excludes 0) in 3 cells; in slow_q2000 the CI includes 0, so there the result is inconclusive rather than non-convergent. Suggested wording: 'the ORX plateau check failed (not precise enough to pass at n = 100; ORX still rising in 3 cells)'.

### C77 (paper line 193): final verdict **CONTRADICTED**

> The lower bounds were positive in the two lane-crawl cells (0.4 % and 3.5 %); the upper bounds ranged from 13.3 % to 47.9 %.

**Reconciliation:** Lower bounds correct; "13.3 %" is a stale P1 value (P1 slow_q2000 upper bound 0.1331). The P1b range is 19.3-47.9 %.

#### Source: R1 S23, verdict CONTRADICTED (basis: derived)

- **Meaning.** The lower end y (CI lower bound of the mean gain of ORX_4 over IP) is above zero in block_q1600 and block_q2000. The upper end x (CI upper bound of the median gain of OR_in over IP) is claimed to lie between 13.3 % and 47.9 % across the four cells.
- **Evidence.**
  - result.json eval.S2: y = 0.44 % (block_q1600), 3.52 % (block_q2000), -0.40 % (slow_q1600), -2.43 % (slow_q2000); x = 47.87, 19.30, 25.43, 22.35 %
  - paper Table II line 177: upper bounds 47.9, 19.3, 25.4, 22.4, so the range is 19.3-47.9
  - docs/research/results/p1_result.json /eval/S2/slow_q2000 adds_at_most_pct = 13.31 ('bracket [-9.1, 13.3] %'): P1 (no amber), not P1b
  - git blame: line 193 from f53b9c3 (2026-10-20 22:10); also in the rendered paper.pdf
- **Verification.** Recomputed x and y from the raw runs (s23_recompute.py): exact match. Searched every results file for 13.3: it occurs only as P1's slow_q2000 upper bound (and unrelated numbers).
- **Failure points.** The lower-bound part is verified. The '13.3 %' is a stale P1 number and contradicts Table II; the correct range is 19.3-47.9 %. Also, block_q1600's 0.4 % is close to 0 and depends on the bootstrap draws (0.56 % with another seed), though it stays positive.

#### Source: R1 recheck (S23), verdict CONTRADICTED (basis: derived)

- **Evidence.**
  - papers/paper_1/paper.qmd:193@HEAD 1e5e8d7 (working tree identical; introduced in f53b9c3, 2026-10-20 22:10): 'the upper bounds ranged from 13.3 % to 47.9 %'
  - papers/paper_1/paper.qmd:177 Table II S2 bracket row: [-0.4, 47.9], [-2.4, 19.3], [0.4, 25.4], [3.5, 22.4]: the upper bounds are 19.3-47.9
  - docs/research/results/p1b_result.json (md5 a6779c18..., byte-identical to ~/work/phd/v5b1_runs/p1b/v108/result.json; code_commit 93ba655, code_dirty False) eval.S2.<cell>.statements.x: slow_q1600 0.4787, slow_q2000 0.1930, block_q1600 0.2543, block_q2000 0.2235; y: -0.0040, -0.0243, 0.0044, 0.0352
  - docs/research/results/p1_result.json eval.S2.<cell>.statements.x (P1, code 85f7d34): slow_q1600 0.3975, slow_q2000 0.1331 ('bracket [-9.1, 13.3] %'), block_q1600 0.2656, block_q2000 0.1982: 13.3 is P1's minimum
  - v5b/p1/stats.py:112-126@93ba655 s2_cell: x = OR_in median rel_ci[1]; y = ORX_Rmax mean rel_ci[0] (matches protocol p1_incident_information.md:106-107 and I12 at line 176)
  - v5b/p1b/analysis.py:256-277@93ba655 or_in / orx: OR_in = per-seed min main-run delay over A; ORX_R = best mean over replicates 1..R, scored on its main run
  - Independent recompute: A size 120 per seed in all cells; median_IP, median_ORin, rel and y_hat match the JSON exactly; x (own bootstrap seed 4242, B=20000) = 48.09, 19.36, 25.61, 22.37 %; range 19.4-48.1 %
  - In p1b_result.json no eval.S2 value rounds to 13.3 %. The values that do (search_133.py output) are in S3, per_q, runner_rows and the prevalence rows, none of them S2 upper bounds
  - Rendered papers/paper_1/paper.pdf (pdftotext) lines 170-172 contain the same '13.3 % to 47.9 %' text; its Table II row shows 19.3 as the minimum upper bound
  - Bootstrap-seed sensitivity (50 seeds × B=20000): slow_q1600 y in [-0.55, +0.16] %, positive in 8 %; block_q1600 y in [0.44, 0.77] %, always positive; x varies by at most about 0.9 points
- **Verification.** Re-check outcome UPHELD: Meaning: in the S2 analysis, each cell gets a bracket [y, x] on how much per-incident hindsight could add beyond the type plan IP. y is the lower end of the 98.75 % CI of the mean gain of ORX_4 over IP. x is the upper end of the 98.75 % CI of the median gain of OR_in over IP. Line 193 says y > 0 only in the two lane-crawl cells (0.4 % and 3.5 %), and that x lies between 13.3 % and 47.9 % across the four cells.

Lower-bound half: verified. My own numpy-only recomputation from the raw P1b runs matches every stored point estimate exactly. With the protocol's fixed bootstrap draws, y = 0.44 % for crawl 1600 and 3.52 % for crawl 2000, and y is negative in both slowdown cells.

Upper-bound half: contradicted. I tried every other reading I could find, and none of them produces 13.3 % as a P1b S2 upper bound:
- the valid-only view (identical, because there are 0 invalid seeds);
- the OR_in mean version (upper ends 19.7-45.7 %);
- the ORX_R upper ends for R = 1, 2, 4 (all at or below 22.5 %);
- the OR_in point estimates (14.8-17.9 %);
- the placebo (13.6-37.7 %);
- the C1 results (no S2, and no value near 13.3 at all).

There is also a structural reason. The smallest OR_in median point estimate in P1b is 14.8 % (slow 2000). So no percentile upper bound on that statistic can be 13.3 %.

The only S2 value of 13.3 is P1's slow_q2000 x, from the earlier round without amber. P1's x range was 13.3-39.7 %; P1b's is 19.3-47.9 %. The sentence takes P1's minimum and P1b's maximum. It contradicts Table II on the same page and appears in the rendered PDF as well.

The correct wording is: "the upper bounds ranged from 19.3 % to 47.9 %." The headline survives, and Table II is correct. Under the audit's definitions this is a major issue (a false statement in the paper) rather than critical, although it could reasonably be treated as minor because the correct numbers sit in Table II.

Further finding (info): for slow 1600 the sign of y depends on the bootstrap draws. Over 50 other bootstrap seeds, y ranged from -0.55 to +0.16 % and was positive in 8 % of them. The protocol (I12) fixes the draws at seed 20261019, so the reported -0.40 % is the pre-registered value and the sentence is right as written. Crawl 1600's y stayed positive under all 50 seeds (0.44-0.77 %).

### C78 (paper line 193): final verdict **PARTIALLY SUPPORTED**

> The placebo alone gained 13.6-37.7 %, which shows how strongly in-sample selection on simulation noise inflates hindsight gains.

**Reconciliation:** TP values exact, but TP is not a like-for-like measure of OR_in's noise inflation (C51).

#### Source: R1 S23, verdict PARTIALLY SUPPORTED (basis: derived)

- **Meaning.** TP keeps the same plan (IP) and picks the best of 5 runs of it: the evaluated run and 4 replicates with new demand and SUMO seeds. Any 'gain' is pure luck. The paper uses its size to show that the in-sample oracle OR_in, the upper end of the bracket, is inflated by noise.
- **Evidence.**
  - v5b/p1/stats.py@93ba655:145-149 (tp_placebo: min over main + 4 replicates, rel at 95 %)
  - result.json eval.TP: 37.65 [23.80, 46.04], 16.77, 13.58, 15.71 %
  - own recompute: OR_in point rel (120 candidates, demand fixed) 15.13 / 14.81 / 17.87 / 17.30 %; slow_q1600 TP 37.7 % exceeds the OR_in point estimate; mean gains in s/veh: TP 92.7 vs OR_in 77.9 (slow_q1600) and 71.1 vs 59.7 (slow_q2000)
  - s23_extra.log: OR_in limited to the 5 best tuning actions (same candidate count as TP, main run only) gains only 2.5 / 10.3 / 7.5 / 8.6 %
  - protocol :110 'It illustrates pure-noise inflation and is never subtracted'; addendum :36 'A larger set inflates OR_in's selection-on-noise'
- **Verification.** Recomputed TP per cell from the raw IP main and replicate runs (exact match). Compared candidate counts and noise structure with OR_in, and built a placebo matched in candidate count.
- **Failure points.** The numbers are verified. The interpretation is not like-for-like: (a) 5 candidates in TP versus 120 in OR_in; (b) TP's candidates differ in demand and pre-onset history, while OR_in's candidates share the main-run demand and diverge only after onset, so TP's per-candidate noise is larger than what OR_in can exploit; (c) in slow_q1600 the placebo exceeds OR_in itself, so TP cannot measure how much of OR_in is noise; (d) the sentence compares TP point estimates with bracket ends that are CI bounds. TP shows that pure-noise selection gains are large; it does not quantify OR_in's inflation.

### C79 (paper line 197): final verdict **PARTIALLY SUPPORTED**

> Slowdown at 2000 veh/h: IP stayed ahead of the best always-on arm up to a detection delay of about 120 s.

**Reconciliation:** d* = 120.4 s exact, but its 95 % CI is [20.1, 168.5] s and the margin at 120 s is 0.14 s/veh; IP's lead over PI was not significant even at d = 0.

#### Source: R1 S23, verdict PARTIALLY SUPPORTED (basis: derived)

- **Meaning.** When the type plan starts d seconds after onset, the median paired difference between always-on PI and IP stays positive (IP ahead) up to d* = 120.4 s, found by linear interpolation between the grid points 120 s and 240 s.
- **Evidence.**
  - result.json eval.S3.slow_q2000.d_star.all_seeds: value 120.37, binding_arm PI, ci [20.14, 168.48], share_never_ahead 0.010
  - own recompute: M_PI(d) = 26.54, 16.54, 19.55, 0.14, -43.84 s/veh at d = 0, 30, 60, 120, 240; strongest L0 by median = PI (= binding arm; fig1_ladder strongest_L0 PI)
  - IP vs PI at 95 %: d=0 7.39 % [2.97, 11.69]; d=30 4.61 [-2.01, 9.61]; d=60 5.45 [1.23, 10.30]; d=120 0.04 [-2.84, 5.89]; at the S1 level (d=0) [-2.65, 13.12] (Table II 'IP vs PI 7.4', not bold)
  - check of t_switch = first tick at or after t_on + d in all delayed runs: 0 mismatches; 29 seeds have no switch at d = 240
- **Verification.** Recomputed d* from the raw L0 and delayed IP runs with my own crossing and bootstrap code. Exact match: value, binding arm, CI. PI is both the binding arm and the best always-on arm.
- **Failure points.** 'Best always-on arm' is correct (PI). But at 120 s the margin is 0.14 s/veh (0.04 %), so the lead is already gone there. The 95 % CI of d* is [20.1, 168.5] s. IP's lead over PI was not significant at the S1 level even at d = 0, and not significant at 95 % at d = 30. 'About 120 s' should carry its CI, e.g. 'break-even at 120 s (95 % CI 20-168 s)'.

#### Source: R2 G5, verdict PARTIALLY SUPPORTED (basis: derived)

- **Meaning.** d* = 120.4 s is the linear-interpolated onset delay at which the median of (PI - IP_d) reaches 0. PI is the binding and strongest L0 arm.
- **Evidence.**
  - p1b_result.json S3.slow_q2000.d_star: 120.37 PI [20.14, 168.48]
  - own recompute: M_PI = 26.54, 16.54, 19.55, 0.14, -43.84 s/veh at d = 0..240 (g5_dstar_c1.log)
  - IP p70_40_8_e4 is a stay plan: clearance_delay_applies False; c rows are the same runs as c=0 (0/100 distinct keys); c* '> 180' is vacuous
  - combined row vs PI +2.7 % [-1.5, 8.0] (g5_recompute_20261019.log)
- **Verification.** Recomputed d* with my own crossing and bootstrap code: exact match. Verified that the plan never returns, so clearance delay cannot act.
- **Failure points.** Clearance is not an issue here. The value has a 95 % CI of [20.1, 168.5] s, and the margin at 120 s is 0.14 s/veh, i.e. the lead is already gone there. Under the combined imperfection, IP's lead over PI is not significant.

### C80 (paper line 197): final verdict **PARTIALLY SUPPORTED**

> Slowdown at 1600 veh/h: the tuned plan was an open-loop constant rate whose lead vanished within 3 s of detection delay and which lost 49.8 % with 30 % runners.

**Reconciliation:** "Open-loop constant rate" and "-49.8 % with 30 % runners" exact. "Within 3 s" is a linear interpolation between d = 0 and 30 s with no run in between; the d = 0 lead was never significant.

#### Source: R1 S23, verdict PARTIALLY SUPPORTED (basis: derived)

- **Meaning.** IP for this cell switches from N (constant 1800 veh/h) to a constant 1000 veh/h at onset and back at clearance: no feedback. Its break-even detection delay against always-on PI is 2.6 s. With 30 % red-light runners its paired median delay rises by 49.8 % of its no-runner median.
- **Evidence.**
  - result.json tune.arms.1600.IP.slow = 'c1000+back', N = 'c1800'; v5b/p1/family.py@93ba655:5,22-25 ('c<rate>': constant rate); own re-tuning on seeds 7400300-339: c1000+back 180.6 s vs runner-up p70_120_8_e4 184.7 s
  - result.json eval.S3.slow_q1600.d_star.all_seeds: 2.61, PI, ci [0, 7.10], share_never_ahead 0.20; own: M_PI = 7.81 (d=0), -81.93 (d=30), so 30*7.81/89.74 = 2.61; bootstrap P(d* <= 3 s) = 0.63
  - IP vs PI at d=0: 4.47 % [-24.41, 12.78] (95 %), [-35.18, 14.55] (S1 level); IP's delay is bimodal (quartiles 125.8 / 175.2 / 289.1 s); seeds where IP beats PI fall from 54 % (d=0) to 25 % (d=30) (s23_dgrid_check.log)
  - result.json eval.runner_rows['s0.3_slow_q1600'].vs_self_s0.IP: rel -49.8 %, diff -87.3 s/veh; own 95 % CI [-76.3, -29.1]
- **Verification.** Re-tuned IP on the tuning seeds, then recomputed d* and the runner rows from the raw runs (all exact). Checked that the delayed runs switched at t_on + d and returned at t_off (all 100).
- **Failure points.** 'Open-loop constant rate' and '-49.8 % with 30 % runners' are verified. 'Within 3 s' is a linear interpolation between d = 0 and d = 30 s: no run lies between them, and the delay distribution is bimodal, so the true break-even could be anywhere in (0, 30) s. The 'lead' at d = 0 (7.8 s/veh, 4.5 %) was never statistically detected, and 20 % of bootstrap draws say IP is never ahead. Safer wording: 'its small, non-significant lead at zero delay was gone at the first tested delay (30 s)'.

#### Source: R2 G5, verdict PARTIALLY SUPPORTED (basis: derived)

- **Meaning.** IP = c1800 before onset, c1000 from onset, back to c1800 at clearance. d* vs PI = 2.6 s is an interpolation between d=0 and d=30. This is the only cell where the clearance delay acts.
- **Evidence.**
  - p1b_result.json tune.arms.1600.IP.slow = 'c1000+back'; S3.slow_q1600.d_star 2.61 [0, 7.10]; c_star 115.17 PI [0, 156.23]
  - own recompute: M_PI(c) = 7.81, 12.08, -14.19 at c = 0, 60, 180; IP_c60 vs PI 6.9 % [3.7, 13.9]; d60 only vs PI -66.5 %; combined vs PI -52.0 % [-65.4, -40.1]
  - d rows return at exactly t_off in 100/100 runs for d <= 120 (g5_schedules.log)
- **Verification.** Recomputed d*, c*, the rows with one imperfection at a time, and the combined row from raw runs: all equal the JSON.
- **Failure points.** 'Detection delay' here is onset only; clearance was perfect. The plan tolerates a clearance delay of about 115 s (interpolated, CI [0, 156]). A 60-s late return even raises the lead over PI. The 'fragile' conclusion stands, and the combined row reinforces it (-52 %). 'Within 3 s' is an interpolation with no run between 0 and 30 s, and the lead at d=0 was never significant.

### C81 (paper line 197): final verdict **VERIFIED**

> Lane crawl at 2000 veh/h: the best plan was PI's own law, and starting it only at onset never beat always-on PI.

**Reconciliation:** Re-derived: IP = PI's law in block_q2000; started at onset it never beats always-on PI (median statement).

#### Source: R1 S23, verdict VERIFIED (basis: derived)

- **Meaning.** The type plan chosen in tuning for this cell is the same PI controller as the always-on PI arm (p20_20_14_e4). Running N before onset and switching to it at onset was never better than running PI all the time, at any detection delay.
- **Evidence.**
  - result.json tune.arms.2000: IP.block = PI = ID = 'p20_20_14_e4'; own re-tuning: p20_20_14_e4 381.3 s vs runner-up p20_20_16_e4 384.2 s
  - result.json eval.S3.block_q2000.d_star: 'IP never ahead', binding PI, share_never_ahead 0.99975; own M_PI = -7.74, -12.61, -19.29, -24.32, -54.40 s/veh at d = 0..240
  - IP vs PI at d=0: -2.07 % [-5.65, -0.07] (95 %); S1 level [-6.64, 0.0]; runners: IP vs PI -0.45 % (s=10 %), 0.0 % (s=30 %)
- **Verification.** Re-tuned IP from the raw tuning runs, then recomputed M(d), the bootstrap and the runner rows independently.
- **Failure points.** This holds for this tuning (margin 2.9 s/veh over the runner-up). 'Never beat' refers to point estimates. At the S1 level the CI touches 0, so 'significantly worse' would be too strong, but the paper does not claim that.

### C82 (paper line 197): final verdict **PARTIALLY SUPPORTED**

> The amber phase reduced the share of runs with an emergency stop from 87 % (no amber) to 12.8 %.

**Reconciliation:** Both shares exact (P1 43,370/50,061 = 86.6 %; P1b 7,396/57,782 = 12.8 %), but this compares two studies that differ in more than amber (min red 2 s, rate cap 4000 -> 2618, PI law, action set, tuned arms, seeds). "The amber reduced" is not established, and the 87 % is an undisclosed P1 number.

#### Source: R1 C1, verdict PARTIALLY SUPPORTED (basis: derived)

- **Meaning.** SUMO counts 'emergency stops': a vehicle had to brake harder than its normal deceleration allows, here mostly when the meter turned red in front of it. In P1 the meter had no amber phase; in P1b it had a 3-s amber. The paper compares the share of runs with at least one emergency stop between the two studies and attributes the drop to the amber.
- **Evidence.**
  - counter: v5b/d1/sumo_runner.py@93ba655:137 estops += libsumo getEmergencyStoppingVehiclesNumber (per step); git diff 85f7d34..93ba655 -- v5b/d1 v5b/d2 v5b/ops is empty; SUMO 1.27.1 in stats XML of P1, P1b and C1 (one run each)
  - P1: ~/work/phd/v5b1_runs/p1/v99/runs, code 85f7d34, signal 'continuous'; P1 note docs/research/results/p1_result.md:81 '87 % of 50,061'; docs/research/results/p1_verification/out/safety.log 'runs with estops 43370'
  - P1b: ~/work/phd/v5b1_runs/p1b/v108/runs, code 93ba655, signal 'amber'; docs/research/results/p1b_result.md:56; p1b_verification/out/p1_vs_p1b.log:24 '57782 ... 7396'
  - meter differences beyond amber: v5b/p1b/meters.py@93ba655:1-40 (G 6 s, amber 3 s, red >= 2 s, C_MIN 11 s, q clipped to [200, 2618], one PI law with carry-over) vs v5b/d1/episode.py@85f7d34:46-57 (cycle max(6, 28800/q), green 6 s then red, q_max 4000, so the red can be 1.2 s)
- **Verification.** Scanned all 296,527 P1 and 344,852 P1b run JSONs with my own code (scan_runs.py, estops.py, estops2.py).
- P1, k=0, seeds 7,400,500-599: 43,370 / 50,061 = 86.6 % (87.7 % of metered runs).
- P1b, k=0, rs=0, seeds 7,400,600-699: 7,396 / 57,782 = 12.8 %.
- Composition of the 57,782: 600 NC, 6,600 fixed L0 runs, 48,000 switch runs over all 120 actions, 2,182 detection-delay runs, 400 false alarms. P1 is built the same way (40,000 switch runs).
- Other P1b populations: 13.0 % with runners included, 11.8 % with replicates included.
- Matched specs (the 30 controller specs present in both studies, 100 seeds each): 67.6 % -> 14.7 %. For constant-rate arms c1700 and c1800, where neither the cap nor the minimum red binds, the amber is the only meter change: 68-97 % -> 8-20 %.
- 0 collisions in all runs of both studies. P1b had 0 red crossings in 339,450 runs at s = 0.
- **Failure points.** (1) Both numbers are exact. But the comparison is a before/after between two studies. Besides the amber, they differ in: minimum red 2 s, rate cap 4000 -> 2618 veh/h, the PI law implementation, the action set (100 -> 120 actions, only 30 shared specs), the tuned arms, and the seeds (500-599 vs 600-699). (2) The matched constant-rate arms support the amber as the main cause, but this was not tested by design. (3) The population is not stated in the paper; 83 % of it is oracle action runs, not deployed arms. (4) P1b still has SUMO emergency-braking warnings at the meter in 22.0 % of runs (P1: 98.7 %, same log parser); the paper does not report this. Test: rerun estops2.py; best would be a P1b-code run with the amber switched off on the same seeds (not done here: no SUMO).

### C83 (paper line 197): final verdict **PARTIALLY SUPPORTED**

> No collisions occurred, and no vehicle crossed on red without runners.

**Reconciliation:** Zero counts verified. But for non-runners zero red crossings are enforced by SUMO (forced stops), and collisions on junction internal lanes (the zipper merges) were not checked (4 re-runs with junction checks on: 0).

#### Source: R1 PLANT, verdict PARTIALLY SUPPORTED (basis: direct observation)

- **Meaning.** No crash was recorded in any run. In runs without runners, no vehicle passed the signal during red.
- **Evidence.**
  - analyze_plant.out: collision runs 0 of 344,852 (P1b), 0 of 1,100 (C1), 0 of 296,527 (P1); red crossings 0 in 338,648 metered s=0 P1b runs and 600 C1 runs
  - v5b/d1/sumo_runner.py@93ba655:105 --collision.check-junctions false; :136 getCollidingVehiclesNumber; SUMO MSLane.cpp:1991-1999 collision = gap < minGap (factor 1, MSCFModel.cpp:62)
  - v5b/p1b/episode.py@93ba655:170-184 crossing = left edge 2 in an r step
  - estop_times.out / estop_eval.out: 44,816 non-runner red-light overshoot resets (11.8 % of P1b runs; C1 154 in 14.4 % of runs)
- **Verification.** Counted from all raw runs. Read the SUMO source for why red crossings are impossible for non-runners. Grepped all logs.
- **Failure points.** For non-runners the zero is built into SUMO: a red link is closed, and a vehicle that cannot stop is teleported back to the line after overshooting by up to 11 m (median implied 26 m/s2). Physically these are red crossings or crashes. Collisions on junction internal lanes, including the 40-m zipper merges, are not checked.

#### Source: R2 G3, verdict PARTIALLY SUPPORTED (basis: direct observation)

- **Meaning.** Concept: the simulated metering caused no crashes, and normal (non-runner) drivers always obeyed red. Technical: SUMO's collision counter (getCollidingVehiclesNumber, summed every step) is 0 in every run, and the stop-line crossing counter of the meter (vehicles leaving edge 2 in a red step, minus runners) is 0 in every metered run.
- **Evidence.**
  - v5b/d1/sumo_runner.py@93ba655:102-110 and @e7dd561:102-110 (identical; git diff 93ba655 e7dd561 -- v5b/d1 v5b/d2 v5b/p1 v5b/p1b/episode.py is empty): '--time-to-teleport 300', '--collision.action warn', '--collision.check-junctions false'; no collision.mingap-factor or ignore-junction-blocker set
  - v5b/p1b/episode.py@93ba655:139 the only extra_args is --tripinfo-output; :170-184 red-crossing hook; :255 valid rule
  - v5b/d1/sumo_runner.py@e7dd561:136 collisions summed per step; :203-204 collision -> H-R4 FAIL -> run invalid
  - v5b/d1/plant.py@e7dd561:26-29 IDM, minGap 2.0, decel 1.5, lane changing disabled (lcStrategic -1 ...)
  - SUMO 1.27.1 source (/home/catalin/work/phd/phd_speed_harmo_v6_toolchain/sumo-src, tag v1_27_1 = installed version): MSFrame.cpp:393 ignore-junction-blocker -1, :408 collision.stoptime 0, :414 check-junctions false, :417 check-junctions.mingap 0, :420 mingap-factor -1, :441 time-to-teleport 300; MSCFModel.cpp:62 collisionMinGapFactor default 1; MSLane.cpp:1990-1999 gap = victimBack - colliderPos - factor*minGap; MSLane.cpp:1824-1835 same-lane check, run on every active lane incl. internal ones (MSLane.cpp:2313); MSLane.cpp:1710-1712 and 4725-4730 foe-lane (junction) check only if check-junctions is true; MSVehicle.cpp:4776-4787 overshoot at lane end -> 'emergency stop', position reset to the lane end, speed 0
  - G3/net_internal_map.out: zipper junction 4 internal lanes :4_0_0..3 40.22 m (x 530-570), junction 5 :5_0_0/1 40.06 m (x 810-850), foes 0010/0001/1000/0100 and 10/01; node 3 (meter) internal lanes 0.1 m, foes 0000
  - G3/collision_log_grep.out: logs with any 'collision' line: 0 of 1,100 (C1), 0 of 296,527 (P1), 0 of 344,852 (P1b)
  - G3/scan_red_cross.out: collision runs 0 in C1 (1,100), P1b (344,852), P1 (296,527); non-runner red crossings 0 in 1,000 metered C1 and 344,050 metered P1b runs; P1 runs have no crossing counts
  - G3/compare_cj.out: 4 re-runs with check-junctions true: collisions 0; hash, delay, emergency counts and statistic-output identical to stored v114 runs
- **Verification.** Read the runner at both commits and the SUMO 1.27.1 source for option defaults and collision logic. Mapped the cached net.xml with my own parser (net_internal_map.py). Scanned every run JSON (scan_red_cross.py, scan_p1b_emerg.py, scan_c1_emerg.py) and grepped every stored SUMO log (log_greps.sh). Re-ran 4 C1 runs from a git-archive copy of e7dd561. The only change was line 105 'false' -> 'true' (diff against an untouched copy shows only that line). The runs used a copy of the cached net and went through systemd-run units audit-r2-1..4; CPU was 3 % beforehand and no heavy jobs were running.
- **Failure points.** (1) In the stored runs, the zero does not cover overlaps between vehicles on the converging internal lanes of the two zipper junctions. This is the only place where vehicles from different lanes meet, because lane changing is off. Only 4 C1 runs were re-checked with the junction check on (0 found). The 3,304 P1b slow-cell runs with emergency braking on ':5_0_*' were not re-checked. (2) Both zeros are partly built into SUMO. A non-runner that cannot stop at red is put back at the stop line with speed 0 and counted as an 'emergency stop' (40,803 P1b runs, 144 C1 runs), so it can never be a red crossing or a crash. Collision-free car following with 9 m/s2 emergency braking turns near-crashes into hard-braking warnings. (3) 'Collision' here means a same-lane gap below 2.0 m (minGap x 1), not physical contact. That is stricter on lanes but blind across lanes inside junctions. (4) The sentence follows the amber comparison, so its scope is unclear. Collisions are 0 in P1 (no amber) as well, but P1 runs store no red-crossing count.

### C84 (paper line 197): final verdict **PARTIALLY SUPPORTED**

> At 2000 veh/h the meter queue reached the upstream entry in 85-100 % of metered runs, so these cells assume unlimited upstream storage.

**Reconciliation:** The measure is a post-run proxy (recompute decided in V109 just before launch; thresholds tail within 50 m of the entry or mean depart delay > 5 s documented only post-run); FX, a metered arm, has 7 % and 42 %; the queue tail never passed 368.7 m of 410 m.

#### Source: R1 PLANT, verdict PARTIALLY SUPPORTED (basis: derived)

- **Meaning.** At the high demand, in almost all runs with a meter, the queue behind the signal filled the road back to where vehicles enter. Vehicles that do not fit wait outside the network without limit.
- **Evidence.**
  - v5b/p1b/analysis.py@93ba655:50,284-285 pre-registered B4 (7 m) flag: 0 everywhere
  - v5b/p1b/confirm_c1.py@e7dd561:59,140-141 V109 indicator: tail >= avail - 50 m OR mean depart delay > 5 s (post-run)
  - analyze_plant.out / spill_rows.json (eval main, s=0), V109 share slow_q2000 / block_q2000: N 1.00/1.00, FX 0.07/0.42, FB 0.98/0.98, PI 0.89/0.95, AD 1.00/1.00, ID 0.94/0.96, IP 0.85/0.96; NC 0.11/0.34; max tail 368.7 m of 410 m
  - docs/decisions.md:132 (V113) restricts the range to N, FB, PI, AD, ID and IP
- **Verification.** Recomputed both indicators per arm and cell from 100 eval seeds with own code. The numbers match p1b_verification/out/spill.log.
- **Failure points.** False for FX, a metered arm (7 % and 42 %). The pooled share over the 7 metered arms is 85.7 %. 'Reached the entry' is a proxy: the tail never passes 368.7 m, and depart delay above 5 s holds in only 32-97 % of runs. The indicator is a post-run replacement for the pre-registered B4 flag, which is not stated in the paper.

### C85 (paper line 2): final verdict **PARTIALLY SUPPORTED**

> Title: 'How Much Incident Information Does Mainline Metering Need? An Honest Headroom Decomposition in Microsimulation'.

**Reconciliation:** Answers one plant, 2 demands, 2 incident types (one a substitute), perfect detection, conditional on an incident. "Honest" invites scrutiny of exactly the undisclosed items.

#### Source: R1 TEXT, verdict PARTIALLY SUPPORTED (basis: direct observation)

- **Meaning.** The title asks a general question: how much incident information mainline metering needs. It promises an 'honest' breakdown of the attainable improvement (the headroom) by information level, measured in traffic microsimulation.
- **Evidence.**
  - paper.qmd:2, :69 ('for one microsimulated bottleneck')
  - docs/research/results/p1b_result.md:76 (cannot say generality), :80 (one plant; block substitute)
- **Verification.** The answer covers one SUMO plant (BN4, 4/4/4/2/1 lanes, lane changing off), 2 demands, 2 incident types (the crawl is a substitute), perfect detection in the main rows, and is conditional on an incident. The title has no scope qualifier beyond 'in Microsimulation'. 'Honest' clashes with the undisclosed items TEXT-F1, F2, F7, F8 and F9.
- **Failure points.** Reviewers may read the title as an overgeneralisation, and 'honest' invites scrutiny of exactly these omissions. Fix: add 'at a single bottleneck' (or similar) and drop 'Honest'.

### C86 (paper line 177): final verdict **VERIFIED**

> Table II rows: S2 bracket ([-0.4, 47.9], [-2.4, 19.3], [0.4, 25.4], [3.5, 22.4]); placebo TP (37.7, 16.8, 13.6, 15.7); d* in s (2.6, 120.4, >240, never ahead).

**Reconciliation:** All values recomputed from 269,084 raw run files; exact under the page bootstrap seed.

#### Source: R1 S23, verdict VERIFIED (basis: derived)

- **Meaning.** For each of the four cells, the table gives the S2 bracket [y, x] in %, the placebo gain TP in %, and the break-even detection delay d* in seconds (the minimum over the L0 arms).
- **Evidence.**
  - result.json eval.S2.<cell>.statements.{x,y}; eval.TP.<cell>.rel; eval.S3.<cell>.d_star.all_seeds.{value,flag,binding_arm,ci}
  - own recompute s23_recompute_20261019.log: brackets [-0.40, 47.87], [-2.43, 19.30], [0.44, 25.43], [3.52, 22.35]; TP 37.65, 16.77, 13.58, 15.71; d* 2.61 (PI, CI [0, 7.1]), 120.37 (PI, [20.1, 168.5]), 240 censored (all arms > max, CI [192.8, 240]), never ahead (PI)
- **Verification.** Independent recomputation from 269,084 raw run files. Every number matches when rounded, with exact float agreement under the page bootstrap seed.
- **Failure points.** The numbers are right, but the table has no legend explaining that: the S2 ends are CI bounds at level 0.9875, built from different estimators (median OR_in for the upper end, mean ORX_4 for the lower end); TP is a point estimate; d* has no CI or binding arm and is interpolated (2.6 s). A reader could mistake the bracket ends for point estimates.

