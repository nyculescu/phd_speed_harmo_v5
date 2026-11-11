#!/bin/bash
# Runs on the rented machine (V483): C1 in the order of c1_screen.md §9, each reading by the committed reader, read once.
# smoke (T0, T3, twins, splits) -> rate -> identity -> checks (a), (b) -> gate (-> fallback) -> pilot -> n rule -> cap -> screen -> reading.
# Progress in RUN/status.txt; SHA256SUMS of RUN written at the end. Deploy with the data below (remote.sh DATA_EXTRA), checked
# against docs/research/c1/data.sha256 before any run:
#   DATA_EXTRA="$P/v5b1_runs/planb_s56_remote/jobs/s6_jobs.json $P/v5b1_runs/planb_s56_remote/s6/s6_rows.jsonl
#               $P/v5b1_runs/round2/test/job_6c49e7e.json $P/v5b1_runs/baseline_v4/policies"
# usage: remote_c1.sh WORKERS PRICE_USD_H CAP_USD [RUN]
#   Common §7's cap action: the measured cost per worker slot projects each next stage; a stage that would pass the cap does not
#   start, and this is logged. If no n passes or the screen would pass the cap, the run ends with ASK AUTHOR (§5).
# After DONE, VOID, ASK AUTHOR or STOPPED: fetch v5b1_runs/c1 with remote.sh fetch, `sha256sum -c SHA256SUMS` in the laptop copy, destroy.
set -u
W=${1:?WORKERS}; PRICE=${2:?PRICE_USD_H}; CAP=${3:?CAP_USD}
P=/home/catalin/work/phd
R=${4:-$P/v5b1_runs/c1}
PY=$P/phd_speed_harmo_v5b1_toolchain/venv/bin/python
D=docs/research/c1
mkdir -p "$R"
[ -f "$R/t0" ] || date +%s > "$R/t0"
T0=$(cat "$R/t0")
unset SUMO_HOME
export OMP_NUM_THREADS=1
CPU=$(lscpu | sed -n 's/^Model name: *//p' | head -1)
if [ -f "$R/cpu" ] && [ "$(cat "$R/cpu")" != "$CPU" ]; then     # §7: one CPU model; a new host follows §5's procedure under a V#
  echo "$(date -u '+%F %T') STOPPED: CPU model changed ($(cat "$R/cpu") -> $CPU)" >> "$R/status.txt"; exit 1
fi
[ -f "$R/cpu" ] || echo "$CPU" > "$R/cpu"
say() { echo "$(date -u '+%F %T') $1" >> "$R/status.txt"; }
step() { say "start $1"; shift; "$@" >> "$R/run.log" 2>&1; rc=$?; say "end rc=$rc"; return $rc; }
must() { step "$@" || { say "STOPPED"; exit 1; }; }
val() { $PY -c "import json,sys; print(json.load(open(sys.argv[1]))$2)" "$1"; }
sums() { (cd "$R" && find . -type f ! -name SHA256SUMS -print0 | LC_ALL=C sort -z | xargs -0 sha256sum > SHA256SUMS); }
trap sums EXIT
COST_PER_RUN=$(cat "$R/cost_per_run" 2>/dev/null)
cost_ok() {     # cost_ok STAGE RUNS
  [ -z "$COST_PER_RUN" ] && return 0
  local ok
  ok=$($PY -c "import math,time; spent=(time.time()-$T0)/3600*$PRICE; nxt=math.ceil($2/$W)*$W*$COST_PER_RUN; print(int(spent+nxt<=$CAP), round(spent,2), round(nxt,2))")
  say "cap check $1: fits/spent/next $ok (cap $CAP)"
  [ "${ok%% *}" = 1 ] || { say "cap: $1 not started"; return 1; }
}
runs_of() { $PY -c "import json,sys; j=json.load(open(sys.argv[1])); print(len(j['arms'])*(j['seed_range'][1]-j['seed_range'][0]+1))" "$1"; }
range_of() { $PY -c "import json,sys; j=json.load(open(sys.argv[1])); print(f\"{j['seed_range'][0]}-{j['seed_range'][1]}\")" "$1"; }
stage() {     # stage NAME [plan options]: plan, cap check, run; measures the per-slot rate on a fresh stage of at least W runs
  local s=$1; shift
  must "plan $s" $PY $D/c1.py plan "$s" --out "$R/$s/jobs.json" "$@"
  local n t1 had
  n=$(runs_of "$R/$s/jobs.json")
  had=$(cat "$R/$s/s6_rows.jsonl" 2>/dev/null | wc -l)
  cost_ok "$s" "$((n - had))" || return 2     # a relaunch charges only the runs still to do
  t1=$(date +%s)
  must "run $s ($n runs)" $PY $D/c1.py run --jobs "$R/$s/jobs.json" --out "$R/$s" --workers "$W" --cpu "$CPU"
  say "drops $s: $(cat "$R/$s/drops.json" 2>/dev/null)"
  if [ "$had" -eq 0 ] && [ "$n" -ge "$W" ]; then
    COST_PER_RUN=$($PY -c "import math; print(($(date +%s)-$t1)/3600*$PRICE/(math.ceil($n/$W)*$W))")
    echo "$COST_PER_RUN" > "$R/cost_per_run"
    say "rate from $s: $COST_PER_RUN USD per worker slot"
  fi
}
wall() {     # mean wall time per arm of a stage's rows (§9: policy and rule runs)
  $PY -c "
import json,sys,collections
w=collections.defaultdict(list)
for l in open(sys.argv[1]):
    r=json.loads(l); w[r['arm']].append(r.get('wall_s') or 0)
print({a: round(sum(v)/len(v),1) for a,v in sorted(w.items())})" "$1"
}

say "code $(cat COMMIT), cpu $CPU, workers $W, price $PRICE/h, cap $CAP, rate ${COST_PER_RUN:-not yet measured}"
sha256sum -c --quiet $D/data.sha256 >> "$R/run.log" 2>&1 || { say "STOPPED: data missing or changed (data.sha256)"; exit 1; }

must "plan c1_smoke" $PY $D/c1.py plan c1_smoke --out "$R/c1_smoke/jobs.json"
must "smoke" $PY $D/c1.py smoke --jobs "$R/c1_smoke/jobs.json" --out "$R/c1_smoke" --workers "$W" --cpu "$CPU"
stage c1_rate || { say "ASK AUTHOR: cap at the rate stage"; exit 0; }
say "wall s per arm (rate stage): $(wall "$R/c1_rate/s6_rows.jsonl")"

stage c1_ident || { say "ASK AUTHOR: cap at identity"; exit 0; }
must "read ident" $PY $D/read_c1.py ident "$R/c1_ident/s6_rows.jsonl" "$R/c1_ident/ident.json" --cpu "$CPU"
[ "$(val "$R/c1_ident/ident.json" '["action"]')" = stop ] && { say "STOPPED: identity (bug rule; see ident.json)"; exit 1; }
say "identity: learner traffic mismatch disclosed = $(val "$R/c1_ident/ident.json" '["learner_diff_disclosed"]')"

stage c1_checks || { say "ASK AUTHOR: cap at checks"; exit 0; }
must "read checks" $PY $D/read_c1.py checks "$R/c1_checks/s6_rows.jsonl" "$R/c1_checks/checks.json" --st "$R/c1_checks/st" --seeds "$(range_of "$R/c1_checks/jobs.json")"
if [ "$(val "$R/c1_checks/checks.json" '.get("outcome")')" = VOID ]; then     # the checks are labels: C1 goes on
  say "checks VOID: $(val "$R/c1_checks/checks.json" '.get("reason")') (labels not readable; a re-run needs its own V#)"
else
  say "checks: (a) $(val "$R/c1_checks/checks.json" '["a"].get("label")'), (b) amend $(val "$R/c1_checks/checks.json" '["b"]["amend"]') void $(val "$R/c1_checks/checks.json" '["b"]["void"]')"
fi

stage c1_gate || { say "ASK AUTHOR: cap at the gate"; exit 0; }
must "read gate" $PY $D/read_c1.py gate "$R/c1_gate/s6_rows.jsonl" "$R/c1_gate/gate.json" --seeds "$(range_of "$R/c1_gate/jobs.json")"
g=$(val "$R/c1_gate/gate.json" '.get("outcome")')
CELL=E30
if [ "$g" = "DRAIN FAILS" ]; then
  say "gate: drain or stuck fails; fallback E30-short (§2)"
  stage c1_fallback || { say "ASK AUTHOR: cap at the fallback gate"; exit 0; }
  must "read fallback gate" $PY $D/read_c1.py gate "$R/c1_fallback/s6_rows.jsonl" "$R/c1_fallback/gate.json" --fallback --seeds "$(range_of "$R/c1_fallback/jobs.json")"
  g=$(val "$R/c1_fallback/gate.json" '.get("outcome")')
  CELL=E30s
fi
[ "$g" = PASS ] || { say "VOID: gate $g (C parked)"; exit 0; }
say "gate PASS, cell $CELL"

stage c1_pilot --cell "$CELL" || { say "ASK AUTHOR: cap at the pilot"; exit 0; }
must "read pilot" $PY $D/read_c1.py pilot "$R/c1_pilot/s6_rows.jsonl" "$R/c1_pilot/pilot.json" --st "$R/c1_pilot/st" --cell "$CELL" --seeds "$(range_of "$R/c1_pilot/jobs.json")"
say "wall s per arm (pilot): $(wall "$R/c1_pilot/s6_rows.jsonl")"
[ "$(val "$R/c1_pilot/pilot.json" '.get("outcome")')" = VOID ] && { say "VOID: pilot $(val "$R/c1_pilot/pilot.json" '.get("reason")') (C parked; a re-run needs its own V#)"; exit 0; }
N=$(val "$R/c1_pilot/pilot.json" '.get("n")')
[ "$N" = None ] && { say "ASK AUTHOR: no n passes the n rule (§5); host to be released"; exit 0; }
say "pilot: n = $N"

stage c1_screen --cell "$CELL" --n "$N" || { say "ASK AUTHOR: the screen at n = $N would pass the cap"; exit 0; }
LAST=$((7490000 + N - 1))
must "read screen" $PY $D/read_c1.py screen "$R/c1_screen/screen.json" --rows "$R/c1_pilot/s6_rows.jsonl" "$R/c1_screen/s6_rows.jsonl" \
  --st "$R/c1_pilot/st" "$R/c1_screen/st" --pilot "$R/c1_pilot/pilot.json" --cell "$CELL" --seeds "7490000-$LAST"
say "screen: $(val "$R/c1_screen/screen.json" '["decision"]["outcome"]')"
say "DONE"
