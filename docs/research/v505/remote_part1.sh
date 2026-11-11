#!/bin/bash
# Runs on the rented machine (V483), V505 part 1 in the order of v505_common.md §2: M2's planned power, smoke, identity, trace,
# pick and the S and TRUCK verdict; then EV's smoke, sizing and gate. Each reading is the committed reader's, read once. M2 runs in
# a subshell, so an M2 stop or VOID leaves EV running. Progress in RUN/status.txt; SHA256SUMS of RUN written at the end.
# Deploy with the data below (remote.sh DATA_EXTRA), checked against docs/research/v505/data.sha256 before any run:
#   DATA_EXTRA="$P/v5b1_runs/planb_s56_remote/jobs/s6_jobs.json $P/v5b1_runs/planb_s56_remote/s6/s6_rows.jsonl
#               $P/v5b1_runs/round2/test/job_6c49e7e.json $P/v5b1_runs/baseline_v4/policies"
# usage: remote_part1.sh WORKERS PRICE_USD_H CAP_USD [RUN]
#   PRICE_USD_H: the accepted offer's price; CAP_USD: the cap left for this rental. Common §7's cap action: from the identity stage on,
#   the measured cost per worker slot projects each next stage; a stage that would pass the cap does not start, and this is logged.
# After DONE or STOPPED: fetch v5b1_runs/v505 with remote.sh fetch, run `sha256sum -c SHA256SUMS` in the laptop copy, then destroy
# (finish.sh is not used: its run list is round1/round2).
set -u
W=${1:?WORKERS}; PRICE=${2:?PRICE_USD_H}; CAP=${3:?CAP_USD}
P=/home/catalin/work/phd
R=${4:-$P/v5b1_runs/v505}
PY=$P/phd_speed_harmo_v5b1_toolchain/venv/bin/python
D=docs/research/v505
T0=$(date +%s)
mkdir -p "$R"
unset SUMO_HOME
export OMP_NUM_THREADS=1
say() { echo "$(date -u '+%F %T') $1" >> "$R/status.txt"; }
step() { say "start $1"; shift; "$@" >> "$R/run.log" 2>&1; rc=$?; say "end rc=$rc"; return $rc; }
must() { step "$@" || { say "STOPPED"; exit 1; }; }
val() { $PY -c "import json,sys; print(json.load(open(sys.argv[1]))$2)" "$1"; }
sums() { (cd "$R" && find . -type f ! -name SHA256SUMS -print0 | LC_ALL=C sort -z | xargs -0 sha256sum > SHA256SUMS); }
trap sums EXIT
COST_PER_RUN=""
cost_ok() {     # cost_ok STAGE RUNS: common §7's cap action
  [ -z "$COST_PER_RUN" ] && return 0
  local ok
  ok=$($PY -c "import math,time; spent=(time.time()-$T0)/3600*$PRICE; nxt=math.ceil($2/$W)*$W*$COST_PER_RUN; print(int(spent+nxt<=$CAP), round(spent,2), round(nxt,2))")
  say "cap check $1: fits/spent/next $ok (cap $CAP)"
  [ "${ok%% *}" = 1 ] || { say "cap: $1 not started"; return 1; }
}
stage() {     # stage NAME [--a A]: plan the job file, check the cap, run it
  local s=$1; shift
  must "plan $s" $PY $D/v5.py plan "$s" --out "$R/$s/jobs.json" "$@"
  local n
  n=$($PY -c "import json,sys; j=json.load(open(sys.argv[1])); print(len(j['arms'])*(j['seed_range'][1]-j['seed_range'][0]+1))" "$R/$s/jobs.json")
  cost_ok "$s" "$n" || return 2
  local t1 had
  t1=$(date +%s)
  had=$(cat "$R/$s/s6_rows.jsonl" 2>/dev/null | wc -l)
  must "run $s ($n runs)" $PY $D/v5.py run --jobs "$R/$s/jobs.json" --out "$R/$s" --workers "$W"
  say "drops $s: $(cat "$R/$s/drops.json" 2>/dev/null)"
  # common §7's rate, per worker slot at full load (ceil(n/W) waves of W), from every fresh stage of at least W runs; kept in a file so
  # EV sees it after M2's subshell. A resumed stage (rows already there) is not measured.
  if [ "$had" -eq 0 ] && [ "$n" -ge "$W" ]; then
    COST_PER_RUN=$($PY -c "import math; print(($(date +%s)-$t1)/3600*$PRICE/(math.ceil($n/$W)*$W))")
    echo "$COST_PER_RUN" > "$R/cost_per_run"
    say "rate from $s: $COST_PER_RUN USD per worker slot"
  fi
}

say "code $(cat COMMIT), workers $W, price $PRICE/h, cap $CAP"
sha256sum -c --quiet $D/data.sha256 >> "$R/run.log" 2>&1 || { say "STOPPED: data missing or changed (data.sha256)"; exit 1; }

m2() {
  must "M2 planned power (S6 rows, before any variant row)" $PY $D/read_m2.py power - "$R/m2_power.json"
  must "plan m2_smoke" $PY $D/v5.py plan m2_smoke --out "$R/m2_smoke/jobs.json"
  must "smoke m2" $PY $D/v5.py smoke --jobs "$R/m2_smoke/jobs.json" --out "$R/m2_smoke" --workers "$W"
  stage m2_ident || exit 0
  must "read ident" $PY $D/read_m2.py ident "$R/m2_ident/s6_rows.jsonl" "$R/m2_ident/ident.json"
  act=$(val "$R/m2_ident/ident.json" '.get("action", "void")')
  [ "$act" = stop ] && { say "M2 STOPPED: a rule replay differs from S6 or is missing (bug rule)"; exit 1; }
  [ "$act" = void ] && { say "M2 VOID: identity stage dropped more than 3 seeds"; exit 0; }
  stage m2_trace || exit 0
  must "read trace" $PY $D/read_m2.py trace "$R/m2_trace/s6_rows.jsonl" "$R/m2_trace/trace.json"
  tr=$(val "$R/m2_trace/trace.json" '.get("action", "void")')
  [ "$tr" = stop ] && { say "M2 STOPPED: a traced run differs from its untraced twin (bug rule)"; exit 1; }
  [ "$tr" = void ] && { say "M2 VOID: the PR-24 recount differs from the counter"; exit 0; }
  stage m2_pick || exit 0
  must "read pick" $PY $D/read_m2.py pick "$R/m2_pick/s6_rows.jsonl" "$R/m2_pick/pick.json"
  a=$(val "$R/m2_pick/pick.json" '.get("a")')
  [ "$a" = None ] && { say "M2 VOID at the pick"; exit 0; }
  if [ "$act" = fresh_seeds ]; then
    say "v3w identity differs: verdict on fresh seeds (M2 §6)"
    stage m2_fallback --a "$a" || exit 0
    must "read verdict" $PY $D/read_m2.py verdict "$R/m2_fallback/s6_rows.jsonl" "$R/m2_fallback/verdict.json" --pick "$R/m2_pick/pick.json" --fallback
  else
    stage m2_verdict --a "$a" || exit 0
    must "read verdict" $PY $D/read_m2.py verdict "$R/m2_verdict/s6_rows.jsonl" "$R/m2_verdict/verdict.json" --pick "$R/m2_pick/pick.json"
  fi
  say "M2 S and TRUCK read"
}

ev() {
  must "plan ev_smoke" $PY $D/v5.py plan ev_smoke --out "$R/ev_smoke/jobs.json"
  must "smoke ev" $PY $D/v5.py smoke --jobs "$R/ev_smoke/jobs.json" --out "$R/ev_smoke" --workers "$W"
  stage ev_size || return 0
  must "read size" $PY $D/read_ev.py size "$R/ev_size/s6_rows.jsonl" "$R/ev_size/size.json"
  lim=$(val "$R/ev_size/size.json" '.get("limit_kmh")')
  [ "$lim" = None ] && { say "EV VOID at sizing"; return 0; }
  stage ev_gate --a "$lim" || return 0
  must "read gate" $PY $D/read_ev.py gate "$R/ev_gate/s6_rows.jsonl" "$R/ev_gate/gate.json" --size "$R/ev_size/size.json"
  say "EV gate: $(val "$R/ev_gate/gate.json" '["outcome"]')"
}

( m2 ) || say "M2 ended early"
COST_PER_RUN=$(cat "$R/cost_per_run" 2>/dev/null)
ev
say "DONE"
