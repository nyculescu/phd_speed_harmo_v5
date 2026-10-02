"""libsumo runner with built-in health monitoring (roadmap §4).

One simulation per process. Counters are accumulated every simulation step because libsumo's
get*Number() calls report the *last step only*.

Health levels: PASS / WARN / FAIL. Nothing is dropped silently: every issue is recorded with a code.
  H-R1  vehicle conservation (exact identities, every checkpoint)
  H-R2  insertion backlog (pending vehicles, max insertion delay)
  H-R3  teleports
  H-R4  collisions, emergency stops
  H-R5  long-waiting (possibly stuck) vehicles
  H-R6  numerics (checked by envs)
  H-R7  actuator / signal state assertions (callables registered by the controller or job)
  H-E1  drain (network and origin queue empty at the end)
  H-E2  arrivals == generated, per route, after drain
  H-E3  SUMO --statistic-output totals agree with the runner's counters
  H-E4  SUMO log: Error -> FAIL; warnings counted by category
"""
from __future__ import annotations

import bisect
import hashlib
import json
import os
import re
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import libsumo as ls

from vsl_lab.config import SUMO_BIN

LEVELS = {"PASS": 0, "WARN": 1, "FAIL": 2}


class Health:
    def __init__(self):
        self.issues = []          # (level, code, sim_time, message)

    def add(self, level: str, code: str, t: float, msg: str) -> None:
        self.issues.append((level, code, round(t, 2), msg))

    @property
    def status(self) -> str:
        worst = max((LEVELS[i[0]] for i in self.issues), default=0)
        return [k for k, v in LEVELS.items() if v == worst][0]

    def summary(self) -> dict:
        by_code = {}
        for lvl, code, _, _ in self.issues:
            by_code.setdefault(code, {"level": lvl, "n": 0})
            by_code[code]["n"] += 1
            if LEVELS[lvl] > LEVELS[by_code[code]["level"]]:
                by_code[code]["level"] = lvl
        return {"status": self.status, "by_code": by_code, "first_issues": self.issues[:20]}


class SumoSim:
    def __init__(self, net_file: Path, route_file: Path, run_dir: Path, demand, additional=(),
                 step_length: float = 0.5, checkpoint_s: float = 300.0, seed: int = 0,
                 extra_args=(), stuck_wait_s: float = 120.0, backlog_warn_s: float = 60.0,
                 bin_s: float = 10.0):
        self.run_dir = Path(run_dir)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.net_file, self.route_file = Path(net_file), Path(route_file)
        self.additional = [str(a) for a in additional]
        self.dt = step_length
        self.checkpoint_s = checkpoint_s
        self.seed = seed
        self.extra_args = list(extra_args)
        self.stuck_wait_s = stuck_wait_s
        self.backlog_warn_s = backlog_warn_s
        self.bin_s = bin_s
        self.demand = demand
        self._dep_times = demand.depart_times
        self._total = len(self._dep_times)
        self._route_counts = demand.counts_by_route()
        self.health = Health()
        self.asserts = []          # callables(t) -> (ok: bool, code: str, msg: str)
        self.t = 0.0
        self.loaded = self.departed = self.arrived = 0
        self.tele_start = self.tele_end = self.collisions = self.estops = 0
        self.tts_system = 0.0      # veh*s, network + origin queue (primary metric basis)
        self.tts_network = 0.0     # veh*s, network only
        self.max_pending = 0
        self.arrivals_bins = {}    # bin index -> arrivals
        self.arrived_by_route = {}
        self._next_cp = checkpoint_s
        self._started = False
        self._wall0 = None
        self._pending_since = {}   # vid -> first sim time seen pending
        self.max_insert_delay = 0.0
        self.identity_mode = None  # calibrated teleport handling for identity I2

    # ---------------------------------------------------------------- lifecycle
    def start(self) -> None:
        self.log_file = self.run_dir / f"sumo_pid{os.getpid()}.log"
        self.stat_file = self.run_dir / f"stats_pid{os.getpid()}.xml"
        args = [SUMO_BIN, "-n", str(self.net_file), "-r", str(self.route_file),
                "--step-length", str(self.dt), "--seed", str(self.seed),
                "--route-steps", "0", "--time-to-teleport", "300",
                "--collision.action", "warn", "--collision.check-junctions", "false",
                "--no-step-log", "true", "--duration-log.disable", "true",
                "--log", str(self.log_file), "--statistic-output", str(self.stat_file)]
        if self.additional:
            args += ["-a", ",".join(self.additional)]
        args += self.extra_args
        ls.start(args)
        # With --route-steps 0 every vehicle is loaded during start(), before the first step;
        # getLoadedNumber() reports that initial load here (caught by H-S2 in the first smoke run).
        self.loaded += ls.simulation.getLoadedNumber()
        self._started = True
        self._wall0 = time.time()

    def step(self, n: int = 1) -> None:
        for _ in range(n):
            ls.simulationStep()
            self.t = ls.simulation.getTime()
            self.loaded += ls.simulation.getLoadedNumber()
            self.departed += ls.simulation.getDepartedNumber()
            arr_ids = ls.simulation.getArrivedIDList()
            na = len(arr_ids)
            self.arrived += na
            if na:
                b = int((self.t - 1e-9) // self.bin_s)
                self.arrivals_bins[b] = self.arrivals_bins.get(b, 0) + na
                for vid in arr_ids:
                    rid = vid.rsplit(".", 1)[0]
                    self.arrived_by_route[rid] = self.arrived_by_route.get(rid, 0) + 1
            self.tele_start += ls.simulation.getStartingTeleportNumber()
            self.tele_end += ls.simulation.getEndingTeleportNumber()
            self.collisions += ls.simulation.getCollidingVehiclesNumber()
            self.estops += ls.simulation.getEmergencyStoppingVehiclesNumber()
            running = ls.vehicle.getIDCount()
            pending = ls.simulation.getPendingVehicles()
            npend = len(pending)
            self.max_pending = max(self.max_pending, npend)
            self.tts_system += (running + npend) * self.dt
            self.tts_network += running * self.dt
            if npend:
                for vid in pending:
                    self._pending_since.setdefault(vid, self.t)
            if self._pending_since and (npend == 0 or len(self._pending_since) > npend):
                pset = set(pending)
                for vid in [v for v in self._pending_since if v not in pset]:
                    self.max_insert_delay = max(self.max_insert_delay, self.t - self._pending_since.pop(vid))
            if self.t >= self._next_cp - 1e-9:
                self.checkpoint(running, npend)
                self._next_cp += self.checkpoint_s

    def due(self, t: float) -> int:
        """Vehicles SUMO must have processed by time t: depart < t. A vehicle with depart == t is inserted
        in the step that starts at t, i.e. after getTime() == t is reported (R1 v1 counted it one step early:
        448 false H-R1 FAILs of +1..+3 in 500 runs; end-of-run identities held in all 500)."""
        return bisect.bisect_left(self._dep_times, t - 1e-9)

    # ---------------------------------------------------------------- health
    def _identities(self, running: int, npend: int) -> dict:
        teleporting = self.tele_start - self.tele_end
        i1 = self.due(self.t) - self.departed - npend
        i2_plain = self.departed - self.arrived - running
        i2_tele = i2_plain - teleporting
        return {"I1": i1, "I2_plain": i2_plain, "I2_minus_teleporting": i2_tele, "teleporting": teleporting}

    def checkpoint(self, running: int | None = None, npend: int | None = None) -> dict:
        if running is None:
            running = ls.vehicle.getIDCount()
        if npend is None:
            npend = len(ls.simulation.getPendingVehicles())
        ids = self._identities(running, npend)
        t = self.t
        if self.loaded != self._total:
            self.health.add("FAIL", "H-S2", t, f"loaded {self.loaded} != generated {self._total}")
        if ids["I1"] != 0:
            self.health.add("FAIL", "H-R1", t, f"I1 due-departed-pending = {ids['I1']}")
        ok_i2 = ids["I2_plain"] == 0 or (ids["teleporting"] and ids["I2_minus_teleporting"] == 0)
        if not ok_i2:
            self.health.add("FAIL", "H-R1", t, f"I2 departed-arrived-running = {ids['I2_plain']} "
                                               f"(teleporting {ids['teleporting']})")
        oldest_pending = 0.0
        if self._pending_since:
            oldest_pending = t - min(self._pending_since.values())
        if oldest_pending > self.backlog_warn_s:
            self.health.add("WARN", "H-R2", t, f"oldest pending vehicle waited {oldest_pending:.0f} s; "
                                               f"backlog {npend}")
        if self.tele_start:
            self.health.add("FAIL", "H-R3", t, f"teleports started so far {self.tele_start}")
        if self.collisions:
            self.health.add("FAIL", "H-R4", t, f"collisions so far {self.collisions}")
        if self.estops:
            self.health.add("WARN", "H-R4e", t, f"emergency stops so far {self.estops}")
        n_long = 0
        for vid in ls.vehicle.getIDList():
            if ls.vehicle.getWaitingTime(vid) > self.stuck_wait_s:
                n_long += 1
        if n_long:
            self.health.add("WARN", "H-R5", t, f"{n_long} vehicles waiting > {self.stuck_wait_s:.0f} s")
        for fn in self.asserts:
            ok, code, msg = fn(t)
            if not ok:
                self.health.add("FAIL", code, t, msg)
        return ids

    def run_until(self, t_end: float) -> None:
        n = int(round((t_end - self.t) / self.dt))
        if n > 0:
            self.step(n)

    def drain(self, t_max: float) -> bool:
        """Run (with whatever controller state is active) until empty or t_max."""
        while self.t < t_max - 1e-9:
            if self.due(self.t) == self._total and ls.vehicle.getIDCount() == 0 and \
                    len(ls.simulation.getPendingVehicles()) == 0 and self.departed == self._total:
                return True
            self.step(int(round(10.0 / self.dt)))
        return self.due(self.t) == self._total and ls.vehicle.getIDCount() == 0 and \
            len(ls.simulation.getPendingVehicles()) == 0

    def close(self, drained: bool | None = None) -> dict:
        running = ls.vehicle.getIDCount()
        npend = len(ls.simulation.getPendingVehicles())
        ids = self.checkpoint(running, npend)
        t_end = self.t
        ls.close()
        self._started = False
        wall = time.time() - self._wall0
        if drained is not None and not drained:
            self.health.add("WARN", "H-E1", t_end, f"not drained: running {running}, pending {npend}")
        if drained:
            for rid, n in self._route_counts.items():
                a = self.arrived_by_route.get(rid, 0)
                if a != n:
                    self.health.add("FAIL", "H-E2", t_end, f"route {rid}: arrived {a} != generated {n}")
        stats = self._parse_stats()
        if stats:
            if stats.get("inserted") is not None and stats["inserted"] != self.departed:
                self.health.add("FAIL", "H-E3", t_end, f"statistic inserted {stats['inserted']} != {self.departed}")
            if stats.get("loaded") is not None and stats["loaded"] != self._total:
                self.health.add("FAIL", "H-E3", t_end, f"statistic loaded {stats['loaded']} != {self._total}")
            if stats.get("teleports") is not None and stats["teleports"] != self.tele_start:
                self.health.add("FAIL", "H-E3", t_end, f"statistic teleports {stats['teleports']} != {self.tele_start}")
        else:
            self.health.add("WARN", "H-E3", t_end, "statistic-output missing or unreadable")
        warn_cats, n_err = self._parse_log()
        if n_err:
            self.health.add("FAIL", "H-E4", t_end, f"{n_err} SUMO errors in log")
        out = {
            "sim_time_end": t_end, "wall_s": round(wall, 2), "sim_per_wall": round(t_end / max(wall, 1e-6), 1),
            "generated": self._total, "loaded": self.loaded, "departed": self.departed, "arrived": self.arrived,
            "running_end": running, "pending_end": npend, "max_pending": self.max_pending,
            "max_insert_delay_s": round(self.max_insert_delay, 1),
            "teleports": self.tele_start, "collisions": self.collisions, "emergency_stops": self.estops,
            "tts_system_vehh": round(self.tts_system / 3600.0, 4), "tts_network_vehh": round(self.tts_network / 3600.0, 4),
            "identities_end": ids, "sumo_stats": stats, "sumo_warning_categories": warn_cats,
            "arrivals_bins": {str(k): v for k, v in sorted(self.arrivals_bins.items())}, "bin_s": self.bin_s,
            "drained": drained, "health": self.health.summary(),
        }
        out["hash"] = self.result_hash(out)
        return out

    @staticmethod
    def result_hash(out: dict) -> str:
        keys = ["generated", "departed", "arrived", "running_end", "pending_end", "teleports", "collisions",
                "tts_system_vehh", "tts_network_vehh", "arrivals_bins", "sim_time_end"]
        return hashlib.sha1(json.dumps({k: out[k] for k in keys}, sort_keys=True).encode()).hexdigest()[:16]

    # ---------------------------------------------------------------- outputs
    def _parse_stats(self) -> dict:
        try:
            root = ET.parse(self.stat_file).getroot()
        except Exception:
            return {}
        out = {}
        v = root.find("vehicles")
        if v is not None:
            for k in ("loaded", "inserted", "running", "waiting"):
                if v.get(k) is not None:
                    out[k] = int(float(v.get(k)))
        tp = root.find("teleports")
        if tp is not None and tp.get("total") is not None:
            out["teleports"] = int(float(tp.get("total")))
        sf = root.find("safety")
        if sf is not None:
            for k in ("collisions", "emergencyStops", "emergencyBraking"):
                if sf.get(k) is not None:
                    out[k] = int(float(sf.get(k)))
        return out

    def _parse_log(self):
        cats, n_err = {}, 0
        try:
            text = self.log_file.read_text(errors="replace").splitlines()
        except Exception:
            return {"_log_missing": 1}, 0
        for line in text:
            if line.startswith("Error"):
                n_err += 1
            elif line.startswith("Warning"):
                key = re.sub(r"'[^']*'", "'*'", line)
                key = re.sub(r"[-+]?\d+(\.\d+)?", "#", key)[:120]
                cats[key] = cats.get(key, 0) + 1
        return dict(sorted(cats.items(), key=lambda kv: -kv[1])[:15]), n_err


def outflow_vph(out: dict, t0: float, t1: float) -> float:
    """Arrivals per hour in [t0, t1) from the binned arrivals (bin edges must align)."""
    b = out["bin_s"]
    i0, i1 = int(round(t0 / b)), int(round(t1 / b))
    n = sum(v for k, v in out["arrivals_bins"].items() if i0 <= int(k) < i1)
    return n * 3600.0 / (t1 - t0)
