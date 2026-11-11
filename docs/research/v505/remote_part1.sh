#!/bin/bash
# Runs on the rented machine (V483), V505 part 1 in the order of v505_common.md §2: M2 smoke, identity, trace, pick and the S and
# TRUCK verdict; then EV smoke, sizing and gate. Each reading is the committed reader's, read once; a stage whose rule says stop
# writes STOPPED with the reason. M2 and EV are independent here, so an M2 VOID does not stop EV. Progress in v505/status.txt.
# usage: remote_part1.sh WORKERS
set -u
W=${1:?WORKERS}
P=/home/catalin/work/phd
R=$P/v5b1_runs/v505
PY=$P/phd_speed_harmo_v5b1_toolchain/venv/bin/python
D=docs/research/v505
mkdir -p "$R"
unset SUMO_HOME
export OMP_NUM_THREADS=1
say() { echo "$(date -u '+%F %T') $1" >> "$R/status.txt"; }
step() { say "start $1"; shift; "$@" >> "$R/run.log" 2>&1; rc=$?; say "end rc=$rc"; return $rc; }
must() { step "$@" || { say "STOPPED"; exit 1; }; }
val() { $PY -c "import json,sys; print(json.load(open(sys.argv[1]))$2)" "$1"; }
stage() {     # stage NAME [--a A]: plan the job file, then run it
  local s=$1; shift
  must "plan $s" $PY $D/v5.py plan "$s" --out "$R/$s/jobs.json" "$@"
  must "run $s" $PY $D/v5.py run --jobs "$R/$s/jobs.json" --out "$R/$s" --workers "$W"
}

say "code $(cat COMMIT), workers $W"

m2() {
  must "plan m2_smoke" $PY $D/v5.py plan m2_smoke --out "$R/m2_smoke/jobs.json"
  must "smoke m2" $PY $D/v5.py smoke --jobs "$R/m2_smoke/jobs.json" --out "$R/m2_smoke" --workers "$W"
  stage m2_ident
  must "read ident" $PY $D/read_m2.py ident "$R/m2_ident/s6_rows.jsonl" "$R/m2_ident/ident.json"
  act=$(val "$R/m2_ident/ident.json" '["action"]')
  [ "$act" = stop ] && { say "M2 STOPPED: a rule replay differs from S6 (bug rule)"; return 1; }
  stage m2_trace
  must "read trace" $PY $D/read_m2.py trace "$R/m2_trace/s6_rows.jsonl" "$R/m2_trace/trace.json"
  [ "$(val "$R/m2_trace/trace.json" '["pass"]')" = True ] || { say "M2 VOID: the PR-24 trace failed"; return 0; }
  stage m2_pick
  must "read pick" $PY $D/read_m2.py pick "$R/m2_pick/s6_rows.jsonl" "$R/m2_pick/pick.json"
  a=$(val "$R/m2_pick/pick.json" '["a"]')
  [ "$a" = None ] && { say "M2 VOID at the pick"; return 0; }
  if [ "$act" = fresh_seeds ]; then
    say "v3w identity differs: verdict on fresh seeds (M2 §6)"
    stage m2_fallback --a "$a"
    must "read verdict" $PY $D/read_m2.py verdict "$R/m2_fallback/s6_rows.jsonl" "$R/m2_fallback/verdict.json" --pick "$R/m2_pick/pick.json" --fallback
  else
    stage m2_verdict --a "$a"
    must "read verdict" $PY $D/read_m2.py verdict "$R/m2_verdict/s6_rows.jsonl" "$R/m2_verdict/verdict.json" --pick "$R/m2_pick/pick.json"
  fi
  say "M2 S and TRUCK read"
}

ev() {
  must "plan ev_smoke" $PY $D/v5.py plan ev_smoke --out "$R/ev_smoke/jobs.json"
  must "smoke ev" $PY $D/v5.py smoke --jobs "$R/ev_smoke/jobs.json" --out "$R/ev_smoke" --workers "$W"
  stage ev_size
  must "read size" $PY $D/read_ev.py size "$R/ev_size/s6_rows.jsonl" "$R/ev_size/size.json"
  lim=$(val "$R/ev_size/size.json" '["limit_kmh"]')
  [ "$lim" = None ] && { say "EV VOID at sizing"; return 0; }
  stage ev_gate --a "$lim"
  must "read gate" $PY $D/read_ev.py gate "$R/ev_gate/s6_rows.jsonl" "$R/ev_gate/gate.json" --size "$R/ev_size/size.json"
  say "EV gate: $(val "$R/ev_gate/gate.json" '["outcome"]')"
}

m2 || say "M2 ended early"
ev
say "DONE"
