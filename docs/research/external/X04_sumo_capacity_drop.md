# X04: SUMO driver-model settings that reproduce a motorway capacity drop

**Model:** Opus 5.5 · web search ON (max 25) · effort high · max tokens 16,000 · system prompt: Shared rules (README)

## Prompt (paste as the user message)
```
I simulate a motorway in the microscopic simulator SUMO (version 1.27, step 0.2 s): three lanes reduced to two at a lane drop (SUMO "zipper" node), human drivers modelled with SUMO's Extended IDM (EIDM) car-following model and the LC2013 lane-change model, mostly at default parameters. Test runs show NO capacity drop: once a queue forms at the lane drop, the queue discharge flow downstream (about 1,900-1,980 veh/h/lane) is equal to or higher than the maximum flow before breakdown. Field studies report that discharge after breakdown is lower than pre-breakdown capacity.

I need PUBLISHED evidence (peer-reviewed or official SUMO documentation) on how to make SUMO, or comparable microscopic models, reproduce a realistic capacity drop at lane drops and merges, with parameters chosen from the literature, NOT tuned to my own data.

Find and report:
1. Field values of the capacity drop at lane drops and on-ramp merges: magnitude (%), queue discharge rate per lane, how it was measured, and its dependence on queue speed (e.g. Yuan, Knoop, Hoogendoorn; Chung, Rudjanakanoknad, Cassidy; Srivastava and Geroliminis; Oh and Yeo review). Give numbers with sources.
2. Studies that reproduced a capacity drop in SUMO: which car-following model (Krauss, IDM, EIDM, ACC, Wiedemann), which parameters (e.g. actionStepLength / reaction time, tau, sigma, accel/decel, EIDM-specific parameters such as driver-error or "taction" settings, minGap), which lane-change parameters (lcCooperative, lcSpeedGain, lcAssertive, lcImpatience, lcStrategic, lcSigma), which node type (zipper vs priority merge), and the resulting drop magnitude. Include SUMO Users Conference papers and journal papers.
3. Known mechanisms that produce a capacity drop in microscopic models: slow acceleration out of queues, reaction delays and action steps, lane-change friction or voids at merges, driver heterogeneity. Which of these SUMO can represent, with which parameters, and with what evidence.
4. Known SUMO-specific pitfalls: e.g. the zipper node discharging "like a metronome", unrealistically high discharge with default models, step-size effects, or lane-change models that move bottlenecks upstream.
5. A ranked list of at most 4 concrete, literature-backed parameter sets I could pre-register as discrete candidates, each with its source, the expected drop magnitude, and the risks (e.g. collisions, unrealistic stop-and-go).

Rules: separate field data from simulation results; give the SUMO version used in each study when stated; mark any parameter value not read in a source as [VERIFY]. At most about 3,500 words.
```

## Output (pasted by the author, date: )
