# Day-pattern track: corridor selection, status (v0)

*2026-10-05 · desk work and access probes only; no traffic data downloaded.*

## What was done

**1. MnDOT configuration downloaded.** The file is `metro_config.xml.gz` (514 kB, from `https://data.dot.state.mn.us/iris_xml/`), stored outside the repo in `/home/catalin/work/phd/dp_data/mndot/`. It describes:
- 151 corridors;
- 15,162 roadway nodes;
- 10,377 detectors (categories: mainline, Exit, Queue, Passage, Merge, Green, Auxiliary, HOT, …);
- 501 ramp meters, each with its queue storage.

**2. Candidate windows.**
- **Filter:** freeway corridors (I-, U.S., T.H.) with 2–3 metered on-ramps within 1.5–8 km, where every ramp has a **Queue** detector and a **Passage or Merge** detector, plus mainline stations upstream (≤ 2 km), in between and downstream (≤ 2 km).
- **Result: 436 windows** qualify on instrumentation alone, on I-94, I-35W, I-35E, I-494, I-694, I-394, T.H.62, T.H.100, T.H.36, U.S.169 and others.
- Queue plus passage detectors on each ramp are what make ramp demand reconstructible: arrivals = passage + Δqueue.

**3. The configuration cannot show which windows hold a *recurrent* bottleneck.** That needs the traffic data, and from this machine the MnDOT traffic data is **blocked**:
- `data.dot.state.mn.us:8080` (`trafdat`) times out;
- `https://data.dot.state.mn.us/trafdat/...` returns a web-firewall "Request Rejected" page for every per-detector file and archive tried, with or without a browser user agent (support IDs logged in the session);
- I stopped probing at that point. I did not try to work around the firewall.

**4. Alternatives reachable from here (2026-10-05):**
- **National Highways WebTRIS** (UK): the open JSON API answers (`/api/v1.0/sites`, 4.4 MB). Native resolution is unconfirmed, but the research notes say 15-min reports are typical.
- **NDW** (Netherlands): the open data portal answers (minute data).
- **PeMS** (California): the site answers; it needs a free account (yours).

## Selection criteria (to apply once data is available; proposed, not yet pre-registered)

1. **A recurrent active bottleneck inside the window.** A speed drop below 50 km/h at the downstream end on ≥ 30 % of weekdays in the tuning year, with free flow upstream of the queue tail.
2. **Ramp demand reconstructible.** Queue and passage detectors are healthy on ≥ 90 % of days (MnDOT data-quality flags / zero-count runs).
3. **Upstream boundary uncongested on ≥ 95 % of days.** Its counts must be demand, not clipped volume.
4. **A measurable capacity drop.** Queue discharge vs pre-queue flow at the bottleneck station, estimated as in S1 R-a.
5. **Prefer** a site with published capacity-drop work (Twin Cities merges in Srivastava & Geroliminis 2013 [VERIFY which sites]; I-94 in Guardiola et al. 2014 [VERIFY]).

## Decision needed from the author

**How to get the data:**
- **(a) MnDOT, by you.** Check whether the trafdat files download from your browser. If they do, the firewall is blocking automated or datacenter access, and a small download script run from your session, or a request to MnDOT RTMC citing the support ID, would unblock it.
- **(b) PeMS.** Register an account (approval is typically 1–2 business days, per the research notes [VERIFY]). It has 30-s/5-min data and ramp detectors, but ramp data quality is often poor.
- **(c) WebTRIS (UK) or NDW (NL).** Reachable now. UK motorways have ramp metering and MIDAS loops, but the open resolution is likely coarser (15 min), which is weak for fitting a capacity drop.

**Recommendation:** (a) first, because MnDOT has the best ramp instrumentation (queue plus passage on every candidate ramp). Then (b) as the fallback.
