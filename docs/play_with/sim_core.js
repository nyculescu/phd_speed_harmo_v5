// Toy two-ramp freeway in the shape of r2m3; IDM and MOBIL-like lane changes, not SUMO's models.
const GEO = {
  L: 6800, vmax: 27.78, dt: 0.2, warm: 300, end: 1800,
  ramps: [
    { start: 3108, merge: 3498.3, end: 3793 },
    { start: 4597, merge: 4987.3, end: 5282 },
  ],
  measureX: 5282,
  zones: [0, 3400, 4900, 5282, 6300, 6800],
};
const LEVELS = [1.6, 1.2, 1.0, 0.8];

function rng32(seed) {
  let a = seed >>> 0;
  return function () {
    a = (a + 0x6D2B79F5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function gauss(r) {
  return Math.sqrt(-2 * Math.log(r() + 1e-12)) * Math.cos(2 * Math.PI * r());
}

// Disturbance catalogue. Times are seconds from the start of the run.
const DISTURBANCES = {
  x1: { label: 'X1 slowdown', slows: [{ x0: 5282, x1: 6300, v: 25 / 3.6, t0: 600, dur: 120 }, { x0: 5282, x1: 6300, v: 25 / 3.6, t0: 1200, dur: 120 }] },
  x2: { label: 'X2 slowdown', slows: [{ x0: 3793, x1: 4987, v: 30 / 3.6, t0: 700, dur: 180 }] },
  up: { label: 'Unplanned slowdown upstream', slows: [{ x0: 1900, x1: 2700, v: 35 / 3.6, t0: 650, dur: 180 }] },
  truck: { label: 'Slow truck' },
  burst: { label: 'Ramp 2 burst' },
  surge: { label: 'Demand surge' },
  v2v: { label: 'V2V dropouts' },
};

const CONTROLLERS = {
  none: { label: 'No control' },
  fixed: { label: 'Fixed 0.8 s rule' },
  zone: { label: 'Zone rule' },
  policy: { label: 'Adaptive policy' },
};

// Zone levels from the toy grid search on X1 (seeds 101-102): least close-following with delay at most 10 % above the fixed rule.
let ZONE_LEVELS = [0.8, 0.8, 1.2, 0.8, 0.8];

function zoneOf(x) {
  const z = GEO.zones;
  for (let i = 0; i < z.length - 1; i++) if (x < z[i + 1]) return i;
  return z.length - 2;
}

function decide(ctrl, obs) {
  if (ctrl === 'none') return { T: 1.6, why: 'No control: every ALKS keeps 1.6 s.' };
  if (ctrl === 'fixed') return { T: 0.8, why: 'Fixed rule: 0.8 s everywhere, whatever happens.' };
  if (ctrl === 'zone') {
    const z = zoneOf(obs.x);
    return { T: ZONE_LEVELS[z], why: `Zone rule: road zone ${z + 1} has level ${ZONE_LEVELS[z].toFixed(1)} s, set in advance for X1.` };
  }
  const v = obs.v, va = obs.vAhead;
  if (v > 15 && va < 0.6 * v) return { T: 1.6, why: `Traffic ${Math.round(va * 3.6)} km/h ahead, own ${Math.round(v * 3.6)} km/h: approaching a queue, so open the gap early.` };
  if (v <= 15 && va >= v) return { T: 0.8, why: 'Slow but traffic ahead is faster: leaving a queue, so close up to discharge more cars.' };
  if (v <= 15) return { T: 1.2, why: 'Inside a queue that is not clearing yet: keep a middle gap.' };
  return { T: 1.2, why: 'Free flow: middle gap.' };
}

class Sim {
  constructor(opts) {
    this.seed = opts.seed || 1;
    this.ctrl = opts.ctrl || 'none';
    this.q = opts.q || 5300;
    this.dist = new Set(opts.dist || []);
    this.extra = [];
    this.t = 0;
    this.nextId = 1;
    this.veh = [];
    this.queues = [[], [], []];
    this.demandR = rng32(this.seed * 7919 + 1);
    this.m = { delay: 0, flow: 0, cf: 0, cf15: 0, hb3: 0, hb7: 0, coll: 0, laneEnd: 0, finished: 0 };
    this.lastSec = -1;
    this.heat = [];
    this.truckDone = false;
  }

  limitAt(x, t) {
    let lim = GEO.vmax;
    const apply = (s) => {
      if (x < s.x0 || x > s.x1 || t < s.t0 || t > s.t0 + s.dur) return;
      const f = Math.min(1, (t - s.t0) / 20);
      lim = Math.min(lim, GEO.vmax + (s.v - GEO.vmax) * f);
    };
    for (const k of this.dist) if (DISTURBANCES[k].slows) DISTURBANCES[k].slows.forEach(apply);
    this.extra.forEach(apply);
    return lim;
  }

  activeSlows(t) {
    const out = [];
    for (const k of this.dist) if (DISTURBANCES[k].slows) for (const s of DISTURBANCES[k].slows) if (t >= s.t0 && t <= s.t0 + s.dur) out.push(s);
    for (const s of this.extra) if (t >= s.t0 && t <= s.t0 + s.dur) out.push(s);
    return out;
  }

  // The speed a vehicle may aim for at x, anticipating lower limits within 300 m.
  // Rebuilt once per second; the 20-s taper does not need finer steps.
  buildProfile(t) {
    const sec = Math.floor(t);
    if (this.prof && sec === this.profSec) return;
    this.profSec = sec;
    const n = 690, p = this.prof || (this.prof = new Float32Array(n));
    if (!this.activeSlows(t).length) { p.fill(GEO.vmax); return; }
    for (let i = 0; i < n; i++) p[i] = this.limitAt(i * 10, t);
    for (let i = n - 2; i >= 0; i--) p[i] = Math.min(p[i], Math.sqrt(p[i + 1] * p[i + 1] + 2 * 1.5 * 10));
  }

  allowed(x) {
    const i = Math.max(0, Math.min(689, Math.floor(x / 10)));
    return this.prof[i];
  }

  rates(t) {
    let main = this.q * 0.7, r1 = this.q * 0.15, r2 = this.q * 0.15;
    if (this.dist.has('surge') && t >= 500 && t < 1100) main *= 1.2;
    if (this.dist.has('burst') && t >= 600 && t < 720) r2 *= 3;
    return [main / 3600, r1 / 3600, r2 / 3600];
  }

  makeVehicle(route) {
    const r = this.demandR;
    const u = r();
    const type = u < 0.075 ? 'truck' : u < 0.575 ? 'alks' : 'hdv';
    const id = this.nextId++;
    const vr = rng32(this.seed * 100003 + id * 31);
    const v = { id, type, route, x: 0, lane: 0, v: 0, a: 0, rng: vr, lcCool: 0, lcFrom: 0, lcT: 1, enterT: this.t };
    if (type === 'hdv') {
      v.len = 4.5 + vr() * 0.8; v.amax = 1.6 + vr() * 0.8; v.b = 2.0; v.s0 = 2.0;
      v.T = Math.min(1.8, Math.max(0.5, 0.95 + 0.25 * gauss(vr))); v.sf = 0.95 + vr() * 0.15;
    } else if (type === 'truck') {
      v.len = 16.5; v.amax = 0.8; v.b = 1.5; v.s0 = 2.5; v.T = 1.5; v.sf = 0.82 + vr() * 0.05;
    } else {
      v.len = 4.8; v.amax = 1.8; v.b = 2.0; v.s0 = 2.0; v.T = 1.6; v.sf = 1.0;
      v.Tcmd = 1.6; v.level = 1.6; v.prevLeader = -1; v.gate = false; v.nextDec = this.t + (id % 50) * 0.2;
      v.nextGate = this.t + (id % 5) * 0.2; v.info = null;
    }
    return v;
  }

  insert() {
    const rt = this.rates(this.t);
    for (let k = 0; k < 3; k++) {
      let p = rt[k] * GEO.dt;
      while (p > 0) {
        if (this.demandR() < Math.min(p, 1)) this.queues[k].push(this.makeVehicle(k));
        p -= 1;
      }
    }
    if (this.dist.has('truck') && !this.truckDone && this.t >= 450) {
      const tr = this.makeVehicle(0);
      tr.type = 'truck'; tr.len = 16.5; tr.amax = 0.6; tr.b = 1.5; tr.s0 = 2.5; tr.T = 1.5; tr.sf = 1; tr.slow = 50 / 3.6; tr.noLC = true;
      this.queues[0].unshift(tr);
      this.truckDone = true;
    }
    const firstIn = (lane, x0) => {
      let best = null;
      for (const v of this.veh) if (v.lane === lane && v.x >= x0 && (!best || v.x < best.x)) best = v;
      return best;
    };
    const q0 = this.queues[0];
    while (q0.length) {
      const v = q0[0];
      let bestLane = -1, bestGap = -1, bestLead = null;
      const lanes = v.type === 'truck' ? [0, 1] : v.slow ? [0] : [0, 1, 2];
      for (const l of lanes) {
        const f = firstIn(l, 0);
        const gap = f ? f.x - f.len : 1e9;
        if (gap > bestGap) { bestGap = gap; bestLane = l; bestLead = f; }
      }
      if (bestGap < 12) break;
      q0.shift();
      v.lane = bestLane; v.x = 0;
      v.v = Math.min(GEO.vmax * v.sf, bestLead ? Math.min(bestLead.v + (bestGap - 12) / 4, (bestGap - 2) / 1.2) : GEO.vmax, v.slow || 99);
      this.veh.push(v);
    }
    for (let k = 1; k <= 2; k++) {
      const q = this.queues[k];
      const R = GEO.ramps[k - 1];
      while (q.length) {
        const v = q[0];
        const f = firstIn(-1, R.start);
        const gap = f && f.x < R.end ? f.x - f.len - R.start : 1e9;
        if (gap < 12) break;
        q.shift();
        v.lane = -1; v.x = R.start;
        v.v = Math.min(GEO.vmax * v.sf, f && f.x < R.end ? Math.min(f.v + (gap - 12) / 4, (gap - 2) / 1.2) : 20);
        this.veh.push(v);
      }
    }
  }

  // Vehicles stay nearly sorted between steps, so an insertion sort is close to linear.
  lanesSorted() {
    const a = this.veh;
    for (let i = 1; i < a.length; i++) {
      const v = a[i];
      let j = i - 1;
      while (j >= 0 && a[j].x > v.x) { a[j + 1] = a[j]; j--; }
      a[j + 1] = v;
    }
    const L = { '-1': [], 0: [], 1: [], 2: [] };
    for (const v of a) L[v.lane].push(v);
    return L;
  }

  // Leader in lane l of a vehicle at x (or a virtual stop at the end of an acceleration lane).
  leaderIn(arr, x, lane, selfId) {
    let lo = 0, hi = arr.length;
    while (lo < hi) { const m = (lo + hi) >> 1; if (arr[m].x <= x) lo = m + 1; else hi = m; }
    let lead = null;
    for (let i = lo; i < arr.length; i++) if (arr[i].id !== selfId) { lead = arr[i]; break; }
    if (lane === -1) {
      for (const R of GEO.ramps) if (x <= R.end && x >= R.start - 1) {
        // Drivers look for a gap at speed and react to the lane end only in its last 80 m.
        if (x > R.end - 80 && (!lead || lead.x - lead.len > R.end)) lead = { x: R.end, len: 0, v: 0, virtual: true };
        break;
      }
    }
    return lead;
  }

  followerIn(arr, x, selfId) {
    let lo = 0, hi = arr.length;
    while (lo < hi) { const m = (lo + hi) >> 1; if (arr[m].x < x) lo = m + 1; else hi = m; }
    for (let i = lo - 1; i >= 0; i--) if (arr[i].id !== selfId) return arr[i];
    return null;
  }

  idm(v, vel, v0, lead, T) {
    const d = 4;
    let af;
    if (vel <= v0) { const r = vel / Math.max(v0, 0.1), r2 = r * r; af = v.amax * (1 - r2 * r2); }
    else af = -v.b * (1 - Math.pow(v0 / vel, v.amax * d / v.b));
    if (!lead) return af;
    const s = Math.max(0.1, lead.x - lead.len - v.x);
    const dv = vel - lead.v;
    const ss = v.s0 + Math.max(0, vel * T + vel * dv / (2 * Math.sqrt(v.amax * v.b)));
    return af - v.amax * (ss / s) * (ss / s);
  }

  speedAhead(v, L) {
    let sum = 0, n = 0;
    for (const l of [0, 1, 2]) for (const u of L[l]) if (u.x > v.x + 100 && u.x < v.x + 400) { sum += u.v; n++; }
    return n ? sum / n : GEO.vmax;
  }

  control(v, L) {
    const arr = L[v.lane];
    const lead = v.lane >= 0 ? this.leaderIn(arr, v.x, v.lane, v.id) : null;
    if (this.t >= v.nextGate) {
      v.nextGate += 1;
      const gap = lead && !lead.virtual ? lead.x - lead.len - v.x : 1e9;
      const ok = lead && !lead.virtual && lead.type === 'alks' && gap <= 150;
      const same = ok && lead.id === v.prevLeader;
      const drop = this.dist.has('v2v') && v.rng() < 0.3;
      v.prevLeader = ok ? lead.id : -1;
      v.gate = same && !drop;
      v.gateWhy = { alks: !!(lead && !lead.virtual && lead.type === 'alks'), near: gap <= 150, same: !!same, drop, gap };
    }
    if (this.t >= v.nextDec) {
      v.nextDec += 10;
      const obs = { x: v.x, v: v.v, vAhead: this.speedAhead(v, L), gap: lead && !lead.virtual ? lead.x - lead.len - v.x : null, vLead: lead ? lead.v : null };
      const d = decide(this.ctrl, obs);
      v.level = d.T;
      v.info = { t: this.t, obs, why: d.why, T: d.T };
    }
    v.Tcmd = v.gate ? v.level : 1.6;
    if (v.Tcmd > v.T) v.T = Math.min(v.Tcmd, v.T + 0.2 * GEO.dt);
    else v.T = v.Tcmd;
  }

  laneChanges(L) {
    const t = this.t;
    for (const v of this.veh) {
      if (v.noLC) continue;
      if (v.lcCool > 0) { v.lcCool -= GEO.dt; continue; }
      const onRamp = v.lane === -1;
      let R = null;
      if (onRamp) { R = v.x <= GEO.ramps[0].end + 1 ? GEO.ramps[0] : GEO.ramps[1]; if (v.x < R.merge) continue; }
      else if ((Math.floor(t / GEO.dt) + v.id) % 5 !== 0) continue;
      const v0 = this.allowed(v.x) * v.sf;
      const curLead = this.leaderIn(L[v.lane], v.x, v.lane, v.id);
      const aCur = this.idm(v, v.v, v0, curLead, v.T);
      const cands = onRamp ? [0] : [v.lane - 1, v.lane + 1].filter((l) => l >= 0 && l <= 2 && !(v.type === 'truck' && l === 2));
      let best = null, bestGain = onRamp ? -1e9 : 0;
      for (const nl of cands) {
        const arr = L[nl];
        const lead = this.leaderIn(arr, v.x, nl, v.id);
        const fol = this.followerIn(arr, v.x, v.id);
        const hw = onRamp ? 0.25 : 0.8;
        const cl = onRamp ? 0.8 : 1.0;
        if (lead && lead.x - lead.len - v.x < v.s0 + v.v * hw + Math.max(0, v.v - lead.v) * cl) continue;
        if (fol && v.x - v.len - fol.x < fol.s0 + fol.v * hw + Math.max(0, fol.v - v.v) * cl) continue;
        // A driver waiting at the lane end accepts a harder brake from the follower as the wait grows.
        const bsafe = onRamp ? 4.0 + Math.min(3, (v.wait || 0) / 2) : 2.5;
        let folLoss = 0;
        if (fol) {
          const fv0 = this.allowed(fol.x) * fol.sf;
          const aNew = this.idm(fol, fol.v, fv0, v, fol.T);
          if (aNew < -bsafe) continue;
          const aOld = this.idm(fol, fol.v, fv0, this.leaderIn(arr, fol.x, nl, fol.id), fol.T);
          folLoss = Math.max(0, aOld - aNew);
        }
        const aNew = this.idm(v, v.v, v0, lead, v.T);
        if (aNew < -bsafe) continue;
        const R0 = GEO.ramps[0], R1 = GEO.ramps[1];
        const nearMerge = v.lane === 0 && v.route === 0 && ((v.x > R0.merge - 400 && v.x < R0.end) || (v.x > R1.merge - 400 && v.x < R1.end));
        const bias = (nl < v.lane ? 0.3 : -0.3) + (nearMerge && nl === 1 ? 1.2 : 0);
        const gain = onRamp ? 1 : aNew - aCur - 0.3 * folLoss + bias - 0.2;
        if (gain > bestGain) { bestGain = gain; best = nl; }
      }
      if (best !== null) {
        v.lcFrom = v.lane; v.lcT = 0; v.lane = best; v.lcCool = 3;
        const arr = L[best];
        let k = 0;
        while (k < arr.length && arr[k].x < v.x) k++;
        arr.splice(k, 0, v);
        const old = L[v.lcFrom]; old.splice(old.indexOf(v), 1);
      }
    }
  }

  step() {
    const dt = GEO.dt, t = this.t;
    this.buildProfile(t);
    this.insert();
    const L = this.lanesSorted();
    for (const v of this.veh) if (v.type === 'alks') this.control(v, L);
    this.laneChanges(L);
    const inWin = t >= GEO.warm && t < GEO.end;
    for (const v of this.veh) {
      let v0 = this.allowed(v.x) * v.sf;
      if (v.slow) v0 = Math.min(v0, v.slow);
      // No passing on the right above 60 km/h: cap at a slower vehicle ahead in the lane to the left.
      if (this.noUndertake && v.lane >= 0 && v.lane < 2 && v.v > 16.7) {
        const ll = this.leaderIn(L[v.lane + 1], v.x, v.lane + 1, v.id);
        if (ll && ll.x - v.x < 8 * v.v && ll.v < v0) v0 = Math.max(ll.v, 16.7);
      }
      const lead = this.leaderIn(L[v.lane], v.x, v.lane, v.id);
      let a = this.idm(v, v.v, v0, lead, v.T);
      if (v.type === 'hdv' && v.v > 1) a -= 0.25 * v.rng();
      v.a = Math.max(-9, Math.min(v.amax, a));
      v.lead = lead;
    }
    for (const v of this.veh) {
      const nv = Math.max(0, v.v + v.a * dt);
      v.x += (v.v + nv) * 0.5 * dt;
      v.v = nv;
      if (v.lcT < 1) v.lcT = Math.min(1, v.lcT + dt / 2);
      if (v.lane === -1 && v.v < 2) v.wait = (v.wait || 0) + dt;
    }
    const L2 = this.lanesSorted();
    for (const k in L2) {
      const arr = L2[k];
      for (let i = 0; i < arr.length - 1; i++) {
        const f = arr[i], l = arr[i + 1];
        if (f.x > l.x - l.len) {
          if (inWin) this.m.coll++;
          f.x = l.x - l.len - 0.5; f.v = Math.min(f.v, l.v);
        }
      }
      if (+k === -1) for (const v of arr) for (const R of GEO.ramps) if (v.x > R.end - 0.1 && v.x < R.end + 5) { v.x = R.end - 0.1; v.v = 0; }
    }
    const sec = Math.floor(t + 1e-9);
    const newSec = sec !== this.lastSec;
    if (newSec) this.lastSec = sec;
    for (const v of this.veh) {
      if (inWin) {
        this.m.delay += dt * (1 - v.v / GEO.vmax);
        if (v.a <= -3) this.m.hb3 += dt;
        if (v.a <= -7) this.m.hb7 += dt;
        if (newSec && v.lead && !v.lead.virtual && v.v > v.lead.v) {
          const ttc = (v.lead.x - v.lead.len - v.x) / (v.v - v.lead.v);
          if (ttc < 3) this.m.cf++;
          if (ttc < 1.5) this.m.cf15++;
        }
      }
      if (inWin && v.prevX !== undefined && v.prevX < GEO.measureX && v.x >= GEO.measureX) this.m.flow++;
      v.prevX = v.x;
    }
    if (inWin) for (const q of this.queues) this.m.delay += dt * q.length;
    let w = 0;
    for (let i = 0; i < this.veh.length; i++) { const v = this.veh[i]; if (v.x < GEO.L) this.veh[w++] = v; else if (inWin) this.m.finished++; }
    this.veh.length = w;
    if (newSec && sec % 5 === 0) this.recordHeat(sec);
    this.t += dt;
  }

  recordHeat(sec) {
    const bins = 68, s = new Float32Array(bins), n = new Uint16Array(bins);
    for (const v of this.veh) if (v.lane >= 0) { const b = Math.min(bins - 1, Math.floor(v.x / 100)); s[b] += v.v; n[b]++; }
    const col = new Float32Array(bins);
    for (let i = 0; i < bins; i++) col[i] = n[i] ? s[i] / n[i] : -1;
    this.heat.push({ t: sec, col });
  }

  queued() { return this.queues[0].length + this.queues[1].length + this.queues[2].length; }
}

function runHeadless(opts) {
  const s = new Sim(opts);
  while (s.t < GEO.end) s.step();
  return s.m;
}

if (typeof module !== 'undefined') module.exports = { Sim, GEO, LEVELS, DISTURBANCES, CONTROLLERS, runHeadless, decide, setZone: (z) => { ZONE_LEVELS = z; } };
