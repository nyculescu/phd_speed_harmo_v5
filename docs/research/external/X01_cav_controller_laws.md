# X01: published rule-based CAV speed controllers (exact control laws)

**Model:** Opus 5.5 · web search ON (max 25) · effort high · max tokens 16,000 · system prompt: Shared rules (README)

## Prompt (paste as the user message)
```
I need the exact, published control laws of rule-based (non-learning) controllers that command individual connected automated vehicles (CAVs) in mixed traffic on freeways, to dampen stop-and-go waves, harmonise speeds or save energy, WITHOUT roadside speed-limit signs or ramp meters. I will re-implement them as comparison baselines in a microscopic simulation.

Cover these, in this order (find the primary source for each):
1. "PI with saturation" and "FollowerStopper" from Stern et al. (2018), Transportation Research Part C, the ring-road field experiment with one automated vehicle.
2. The explicit CAV controller used in the CIRCLES consortium's I-24 field test (Nashville, November 2022), described as taking the minimum of a safety acceleration, a target-speed acceleration and an MPC-style acceleration (authors include Hayat, Lee, Wang, Bayen, Work, Piccoli and others), including the "speed planner" that sets the target speed from downstream traffic information.
3. US FHWA speed harmonisation for CAVs (report FHWA-HRT-21-008, and the related work by Ma, Ghiasi, Li, Zhou et al., e.g. Ghiasi et al. 2019 in Transportation Research Part C): the rule that ramps CAV speed toward the downstream bottleneck speed.
4. Malikopoulos, Hong, Park, Lee (2019), "Optimal control for speed harmonization of automated vehicles", IEEE Transactions on Intelligent Transportation Systems: the closed-form solution and its assumptions.
5. Kesting, Treiber, Schönhof, Helbing (2008), "Adaptive cruise control design for active congestion avoidance", Transportation Research Part C: the traffic-state-dependent ACC rule.

For EACH controller give:
(a) the control law exactly as published (equations, symbols, units), and the update rate used;
(b) the inputs it needs: own speed, gap and relative speed to the leader, downstream speed or density, communication (V2V or V2X), penetration-rate assumptions;
(c) every parameter with its published value and how it was tuned;
(d) published results: setting (ring road, field test, simulation), penetration rate, and effects on speed variance, fuel or energy, travel time and throughput, with numbers;
(e) known limitations or failure cases reported by the authors or later papers;
(f) whether it can be driven by a command that changes the vehicle's target speed by -5, 0 or +5 km/h every 2 s on a 100 km/h motorway, and what is lost if quantised that way (your analysis, labelled as analysis).

Then add: (g) any other rule-based CAV freeway controller from 2015-2026 that a PhD examiner would expect as a baseline and that is missing above (at most 3, each with a source); (h) a 10-line comparison table of all controllers.

Length: at most about 4,000 words. Equations in plain text or LaTeX.
```

## Output (pasted by the author, date: )
