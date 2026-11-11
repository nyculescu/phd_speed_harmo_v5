"""V505 plant hooks (docs/research/protocols/v505_*.md). M2's variant V-A: ramp-2 cars merge with lcAssertive = a while on the
accelerating lane 4a_0, and go back to the plant's value the step after they leave it (V508 D3). EV's T0 check of a slowdown."""

KEY = "laneChangeModel.lcAssertive"
BEFORE, ON, AFTER = 0, 1, 2
RAMP2_FEED = ("r2", "rj2")
FREE_TOL = 0.006     # netconvert writes lane speeds with 2 decimals: 100/3.6 is stored as 27.78


def slowdown_limit(spec: dict, t: float, free: float) -> float:
    """The edge limit a slowdown spec asks for at time t, written apart from perturb._slowdown so T0 can check that code against it."""
    for t0 in spec["times"]:
        if t0 <= t < t0 + spec["dur"]:
            taper = spec.get("taper", 0.0)
            lim = spec["limit_kmh"] / 3.6
            return free + (lim - free) * (t - t0) / taper if taper and t < t0 + taper else lim
    return free


def t0_step(acc: dict, spec: dict, t: float, dt: float, got: float, edge_speed: float, free: float) -> None:
    """EV §8 T0, one step: the lane limit read back (got) against the schedule at t or t - dt. Outside the event the free limit is
    accepted within netconvert's rounding; inside it, exactly. The hold's mean edge speed is accumulated."""
    want = [slowdown_limit(spec, x, free) for x in (t, t - dt)]
    in_event = any(w != free for w in want)
    err = min(abs(got - w) for w in want)
    acc["steps"] = acc.get("steps", 0) + 1
    acc["limit_bad"] = acc.get("limit_bad", 0) + (err > (1e-6 if in_event else FREE_TOL))
    acc["max_err"] = max(acc.get("max_err", 0.0), err if in_event else 0.0)
    t1 = spec["times"][0]
    if t1 + spec.get("taper", 0.0) <= t < t1 + spec["dur"]:
        acc["hold_steps"] = acc.get("hold_steps", 0) + 1
        acc["hold_speed_sum"] = acc.get("hold_speed_sum", 0.0) + edge_speed


class Ramp2Assertive:
    """Tracks every ramp-2 car from departure to arrival. With a = None it only tracks (for the lane-change counts of M2 §2)."""

    def __init__(self, ls, a, base):
        self.ls, self.a, self.base = ls, a, str(base)
        self.state = {}
        self.skipped = 0     # cars seen past the feed without a step on 4a_0 (entered and merged within one step)

    def _done(self, v) -> None:
        self.state[v] = AFTER
        if self.a is not None:
            self.ls.vehicle.setParameter(v, KEY, self.base)

    def step(self) -> None:
        ls = self.ls
        for v in ls.simulation.getDepartedIDList():
            if ls.vehicle.getRoadID(v) == "r2":
                self.state[v] = BEFORE
                if self.a is not None:
                    ls.vehicle.setParameter(v, KEY, str(self.a))
        for v in ls.simulation.getArrivedIDList():
            self.state.pop(v, None)
        for v, k in list(self.state.items()):
            if k == AFTER:
                continue
            lane = ls.vehicle.getLaneID(v)
            if lane == "4a_0":
                self.state[v] = ON
            elif k == ON:
                self._done(v)
            elif not lane.startswith(":") and lane.rsplit("_", 1)[0] not in RAMP2_FEED:
                self.skipped += 1     # SUMO moves and changes lanes in the same step (MSNet.cpp:872-884)
                self._done(v)

    def read_back(self, S) -> None:
        """M2 §7 "V-A binds", by lane: a on the feed and on 4a_0, the plant's value on any other road lane."""
        if self.a is None:
            return
        for v, k in self.state.items():
            lane = self.ls.vehicle.getLaneID(v)
            if lane.startswith(":"):
                continue
            on_va = lane == "4a_0" or lane.rsplit("_", 1)[0] in RAMP2_FEED
            want = float(self.a) if on_va else float(self.base)
            key = "on" if lane == "4a_0" else "feed" if on_va else "off"
            S[f"va_n_{key}"] += 1
            S[f"va_bad_{key}"] += abs(float(self.ls.vehicle.getParameter(v, KEY)) - want) > 1e-6
        S["va_skipped"] = float(self.skipped)
