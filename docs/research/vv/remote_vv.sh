#!/bin/bash
# Runs on the rented machine (V483): the merge V&V checks (merge_vv.md §4, V532), each reading by the committed reader, read once.
# smoke (T3, twins, T0 lengths, meter equality, input checks, wall time) -> identity replay (+ traced) -> V1 traces -> cap check ->
# screen -> V2/V3 reading. Progress in RUN/status.txt; SHA256SUMS of RUN written at the end. Deploy with the data below
# (remote.sh DATA_EXTRA), checked against docs/research/c1/data.sha256 before any run:
#   DATA_EXTRA="$P/v5b1_runs/planb_s56_remote/jobs/s6_jobs.json $P/v5b1_runs/planb_s56_remote/s6/s6_rows.jsonl
#               $P/v5b1_runs/round2/test/job_6c49e7e.json $P/v5b1_runs/baseline_v4/policies
#               $P/v5b1_runs/planb_s56_remote/jobs/mpcf_da8e9f8e5b59.pt"
# usage: remote_vv.sh WORKERS PRICE_USD_H CAP_USD [RUN]
# After DONE, ASK AUTHOR or STOPPED: fetch v5b1_runs/vv with remote.sh fetch, `sha256sum -c SHA256SUMS` in the laptop copy, destroy.
set -u
W=${1:?WORKERS}; PRICE=${2:?PRICE_USD_H}; CAP=${3:?CAP_USD}
P=/home/catalin/work/phd
R=${4:-$P/v5b1_runs/vv}
PY=$P/phd_speed_harmo_v5b1_toolchain/venv/bin/python
D=docs/research/vv
mkdir -p "$R"
[ -f "$R/t0" ] || date +%s > "$R/t0"
T0=$(cat "$R/t0")
unset SUMO_HOME
export OMP_NUM_THREADS=1
CPU=$(lscpu | sed -n 's/^Model name: *//p' | head -1)
say() { echo "$(date -u '+%F %T') $1" >> "$R/status.txt"; }
step() { say "start $1"; shift; "$@" >> "$R/run.log" 2>&1; rc=$?; say "end rc=$rc"; return $rc; }
must() { step "$@" || { say "STOPPED"; exit 1; }; }
val() { $PY -c "import json,sys; print(json.load(open(sys.argv[1]))$2)" "$1"; }
sums() { (cd "$R" && find . -type f ! -name SHA256SUMS -print0 | LC_ALL=C sort -z | xargs -0 sha256sum > SHA256SUMS); }
trap sums EXIT
if [ -f "$R/cpu" ] && [ "$(cat "$R/cpu")" != "$CPU" ]; then     # VV-D6: one instance type
  say "STOPPED: CPU model changed ($(cat "$R/cpu") -> $CPU)"; exit 1
fi
[ -f "$R/cpu" ] || echo "$CPU" > "$R/cpu"
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
stage() {     # stage NAME: plan, cap check, run
  local s=$1 n had
  must "plan $s" $PY $D/vv.py plan "$s" --out "$R/$s/jobs.json"
  n=$(runs_of "$R/$s/jobs.json")
  had=$(cat "$R/$s/s6_rows.jsonl" 2>/dev/null | wc -l)
  cost_ok "$s" "$((n - had))" || return 2
  must "run $s ($n runs)" $PY $D/vv.py run --jobs "$R/$s/jobs.json" --out "$R/$s" --workers "$W" --cpu "$CPU"
  say "drops $s: $(cat "$R/$s/drops.json" 2>/dev/null)"
}

say "code $(cat COMMIT), cpu $CPU, workers $W, price $PRICE/h, cap $CAP, rate ${COST_PER_RUN:-not yet measured}"
sha256sum -c --quiet docs/research/c1/data.sha256 >> "$R/run.log" 2>&1 || { say "STOPPED: data missing or changed (data.sha256)"; exit 1; }

must "plan vv_smoke" $PY $D/vv.py plan vv_smoke --out "$R/vv_smoke/jobs.json"
must "smoke" $PY $D/vv.py smoke --jobs "$R/vv_smoke/jobs.json" --out "$R/vv_smoke" --workers "$W" --cpu "$CPU"
say "smoke wall s: $(val "$R/vv_smoke/smoke.json" '["wall_s"]')"
say "smoke standing for the author (end_stop, end_stop2, vehicles): $(val "$R/vv_smoke/smoke.json" '["standing_for_author"]')"
if [ -z "$COST_PER_RUN" ]; then     # the screen's rate from the smoke's screen arms, x 1.3 (one seed, one wave), as CF
  COST_PER_RUN=$($PY -c "
import json,sys
w=[r['wall_s'] for r in map(json.loads, open(sys.argv[1])) if '~' not in r['name']]
print(1.3*sum(w)/len(w)/3600*$PRICE/$W)" "$R/vv_smoke/a/s6_rows.jsonl")
  echo "$COST_PER_RUN" > "$R/cost_per_run"
  say "rate from the smoke's screen arms (x 1.3): $COST_PER_RUN USD per worker slot"
fi

stage vv_replay || { say "ASK AUTHOR: cap at the replay"; exit 0; }
[ "$(wc -l < "$R/vv_replay/s6_rows.jsonl")" -eq "$(runs_of "$R/vv_replay/jobs.json")" ] || { say "STOPPED: replay rows missing"; exit 1; }
rm -f "$R/vv_replay/ident.json"
step "read ident" $PY $D/vv.py ident "$R/vv_replay/s6_rows.jsonl" "$R/vv_replay/ident.json" --cpu "$CPU"
[ -s "$R/vv_replay/ident.json" ] || { say "STOPPED: identity read wrote no result"; exit 1; }
[ "$(val "$R/vv_replay/ident.json" '["action"]')" = stop ] && { say "STOPPED: identity (bug rule; see ident.json)"; exit 1; }
[ "$(val "$R/vv_replay/ident.json" '["tracer_bug"]')" = True ] && { say "STOPPED: a traced replay differs from its stored row (tracer bug)"; exit 1; }
say "identity: learner mismatch disclosed = $(val "$R/vv_replay/ident.json" '["learner_diff_disclosed"]')"

stage vv_trace || { say "ASK AUTHOR: cap at the traces"; exit 0; }
[ "$(wc -l < "$R/vv_trace/s6_rows.jsonl")" -eq "$(runs_of "$R/vv_trace/jobs.json")" ] || { say "STOPPED: trace rows missing"; exit 1; }
must "read V1" $PY $D/read_vv.py v1 "$R/vv_trace/v1.json" --trace "$R/vv_trace/s6_rows.jsonl" "$R/vv_replay/s6_rows.jsonl" --vv "$R/vv_trace/vv" "$R/vv_replay/vv"
o=$(val "$R/vv_trace/v1.json" '["outcome"]')
say "V1: $o"
case "$o" in CHECKS*) ;; *) say "STOPPED: V1 $o (see v1.json; §6)"; exit 1 ;; esac

stage vv_screen || { say "ASK AUTHOR: the screen would pass the cap"; exit 0; }
must "read V2 V3" $PY $D/read_vv.py v3 "$R/vv_screen/v3.json" --rows "$R/vv_screen/s6_rows.jsonl" --st "$R/vv_screen/st" --seeds "$(range_of "$R/vv_screen/jobs.json")"
say "V2 $(val "$R/vv_screen/v3.json" '["v2"]["outcome"]') | V3a $(val "$R/vv_screen/v3.json" '["v3a"]["replication"]["reading"]') | V3b $(val "$R/vv_screen/v3.json" '["v3b"]["reading"]')"
v=$(val "$R/vv_screen/v3.json" '["void"]')
[ "$v" = "[]" ] || say "VOID: $v (merge_vv.md §6)"
say "DONE"
