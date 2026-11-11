"""V505 plant hooks (docs/research/protocols/v505_*.md). M2's variant V-A: ramp-2 cars merge with lcAssertive = a while on the
accelerating lane 4a_0, and go back to the plant's value the step after they leave it (V508 D3)."""

KEY = "laneChangeModel.lcAssertive"
BEFORE, ON, AFTER = 0, 1, 2


class Ramp2Assertive:
    """Tracks every ramp-2 car from departure to arrival. With a = None it only tracks (for the lane-change counts of M2 §2)."""

    def __init__(self, ls, a, base):
        self.ls, self.a, self.base = ls, a, str(base)
        self.state = {}

    def step(self) -> None:
        ls = self.ls
        for v in ls.simulation.getDepartedIDList():
            if ls.vehicle.getRoadID(v) == "r2":
                self.state[v] = BEFORE
                if self.a is not None:
                    ls.vehicle.setParameter(v, KEY, str(self.a))
        for v in ls.simulation.getArrivedIDList():
            self.state.pop(v, None)
        for v, k in self.state.items():
            if k == AFTER:
                continue
            if ls.vehicle.getLaneID(v) == "4a_0":
                self.state[v] = ON
            elif k == ON:
                self.state[v] = AFTER
                if self.a is not None:
                    ls.vehicle.setParameter(v, KEY, self.base)

    def read_back(self, S) -> None:
        """M2 §7 "V-A binds": counts per state of cars read and of cars whose SUMO value differs from the wanted one."""
        if self.a is None:
            return
        for v, k in self.state.items():
            want = float(self.base) if k == AFTER else float(self.a)
            S[f"va_n_{k}"] += 1
            S[f"va_bad_{k}"] += abs(float(self.ls.vehicle.getParameter(v, KEY)) - want) > 1e-6
