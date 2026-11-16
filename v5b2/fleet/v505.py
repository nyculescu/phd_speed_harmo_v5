"""V505 plant hooks (docs/local/research/protocols/v505_*.md). M2's variant V-A: ramp-2 cars merge with lcAssertive = a while on the
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
    tol = lambda w: FREE_TOL if w == free else 1e-6     # per candidate: at onset the lane may still hold the net's free value
    ok = [abs(got - w) for w in want if abs(got - w) <= tol(w)]
    acc["steps"] = acc.get("steps", 0) + 1
    acc["limit_bad"] = acc.get("limit_bad", 0) + (not ok)
    inev = [abs(got - w) for w in want if w != free]
    if inev:
        acc["max_err"] = max(acc.get("max_err", 0.0), min(inev))
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
        self.merges = 0     # every ramp-2 car that left the feed and 4a_0, counted at 0.1-s resolution

    def _done(self, v, count: bool) -> None:
        self.state[v] = AFTER
        self.merges += count
        if self.a is not None:
            self.ls.vehicle.setParameter(v, KEY, self.base)

    def step(self, count: bool = True) -> None:
        """count: whether merges and same-step merges are counted (False in the warm-up, so the counts cover the 1-Hz window)."""
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
                self._done(v, count)
            elif not lane.startswith(":") and lane.rsplit("_", 1)[0] not in RAMP2_FEED:
                self.skipped += count     # SUMO moves and changes lanes in the same step (MSNet.cpp:872-884)
                self._done(v, count)

    def counts(self, S) -> None:
        S["r2_merge"] = float(self.merges)
        S["va_skipped"] = float(self.skipped)

    def read_back(self, S) -> None:
        """M2 §7 "V-A binds", by lane: a on the feed and on 4a_0 before the merge, the plant's value on any other road lane and on
        4a_0 for a merged car that moved back onto it (counted apart)."""
        if self.a is None:
            return
        for v, k in self.state.items():
            lane = self.ls.vehicle.getLaneID(v)
            if lane.startswith(":"):
                continue
            on_va = k != AFTER and (lane == "4a_0" or lane.rsplit("_", 1)[0] in RAMP2_FEED)
            want = float(self.a) if on_va else float(self.base)
            key = ("on" if lane == "4a_0" else "feed") if on_va else "back" if lane == "4a_0" else "off"
            S[f"va_n_{key}"] += 1
            S[f"va_bad_{key}"] += abs(float(self.ls.vehicle.getParameter(v, KEY)) - want) > 1e-6


EDGE2_X, EDGE2_END = 3000.0, 3498.3     # r2m3 (corridor.py): edge 1 runs 0-3000 m, edge 2 3000-3498.3 m, as on r1m3
TAU_RISE_MAX_S = 5.0     # 0.8 -> 1.6 s at tau_rise 0.2 s/s takes 4 s; read-back is checked after 5 s in the switched state


class _Switch:
    """V505 EV §3: a level that replaces the base rule's in the per-second headway update (b_env._v2v), for every ALKS at once,
    bypassing the 10-s hold but not tau_rise. Told (IP) and detected (SW (a)) switches share this path, so they differ only in how
    they know about the event. T0 counts (EV §8): cars switched and read back at L after TAU_RISE_MAX_S."""

    def __init__(self, env, L: int, after: float):
        self.env, self.L, self.after = env, int(L), float(after)
        self.since = {}
        self.t0 = {"switched_s": 0, "read_n": 0, "read_bad": 0}

    def active(self, v: str, t: float) -> bool:
        raise NotImplementedError

    def level(self, v: str, lev: int, on: bool) -> int:
        import libsumo as ls
        t = self.env.sim.t
        if not self.active(v, t):
            self.since.pop(v, None)
            return lev
        self.t0["switched_s"] += 1
        s = self.since.setdefault(v, t)
        # read back only when the car held a commanded level last second too (env.on still holds last second's state here), so the
        # tau SUMO holds is last second's command at L, not the contract 1.6 s of a second without an ALKS leader (review blocker)
        if on and v in getattr(self.env, "on", ()) and t - s >= TAU_RISE_MAX_S:
            self.t0["read_n"] += 1
            self.t0["read_bad"] += abs(ls.vehicle.getTau(v) - self.env.headways[self.L]) > 1e-6
        return self.L


class Told(_Switch):
    """IP: ALKS within d m upstream of the edge-2 entry, or on edge 2, from d / 25 s before onset until `after` s past the end of
    the drawn event (EV §3). Reads the event schedule, which no real controller has."""

    def __init__(self, env, d: float, L: int, after: float):
        super().__init__(env, L, after)
        self.d = float(d)
        from v5b2.fleet.b_env import ROAD_X
        if (ROAD_X.get("2"), ROAD_X.get("3a")) != (EDGE2_X, EDGE2_END):     # a geometry change must fail loudly
            raise ValueError(f"edge 2 is not at {EDGE2_X}-{EDGE2_END} m: {ROAD_X}")

    def active(self, v: str, t: float) -> bool:
        import libsumo as ls
        p = self.env.pert
        if p is None or p.kind != "slowdown":
            return False
        t0, dur = p.s["times"][0], p.s["dur"]
        if not t0 - self.d / 25.0 <= t < t0 + dur + self.after:
            return False
        road = ls.vehicle.getRoadID(v)
        if road.startswith(":n2"):     # the junction at the edge-2 entry lies inside the zone
            return True
        if road not in ("1", "2"):
            return False
        x = (0.0 if road == "1" else EDGE2_X) + ls.vehicle.getLanePosition(v)
        return EDGE2_X - self.d <= x <= EDGE2_END


class Detect(_Switch):
    """SW (a): a car whose roadside mean speed over the next r m is below th m/s switches to L, and holds it `after` s after the
    condition clears (EV §3). It knows nothing about the event in advance."""

    def __init__(self, env, r: float, th: float, L: int, after: float):
        super().__init__(env, L, after)
        from v5b2.fleet.b_env import LocalRule
        self.look = LocalRule(env, r, th)
        self.th = float(th)
        self.fired = {}

    def active(self, v: str, t: float) -> bool:
        if getattr(self.env, "bins", None):     # the roadside bins exist only once the env reports (not in the first warm-up second)
            s = self.look._ahead(v)
        else:
            s = None
        if s is not None and s < self.th:
            self.fired[v] = t
        on = v in self.fired and t - self.fired[v] <= self.after
        if not on and v in self.fired and v in self.since:     # EV §8 T0: a release comes `after` s past the last detection, within 1 s
            gap = t - self.fired[v]
            self.t0["release_n"] = self.t0.get("release_n", 0) + 1
            self.t0["release_bad"] = self.t0.get("release_bad", 0) + (not self.after < gap <= self.after + 1.0 + 1e-6)
        return on
