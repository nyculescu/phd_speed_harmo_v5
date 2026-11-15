#!/bin/bash
# Runs on the rented machine (V483): the C1 confirmation (c1_confirm.md §3, V527), each reading by the committed reader, read once.
# smoke (T0, T3, twins, splits, per-arm wall time) -> identity of the 29 stored arms -> cap check -> screen -> reading.
# Progress in RUN/status.txt; SHA256SUMS of RUN written at the end. Deploy with the data below (remote.sh DATA_EXTRA), checked
# against docs/research/c1/data.sha256 before any run:
#   DATA_EXTRA="$P/v5b1_runs/planb_s56_remote/jobs/s6_jobs.json $P/v5b1_runs/planb_s56_remote/s6/s6_rows.jsonl
#               $P/v5b1_runs/round2/test/job_6c49e7e.json $P/v5b1_runs/baseline_v4/policies
#               $P/v5b1_runs/planb_s56_remote/jobs/mpcf_da8e9f8e5b59.pt"
# usage: remote_cf.sh WORKERS PRICE_USD_H CAP_USD [RUN]
#   Common §7's cap action: the measured cost per worker slot projects each next stage; a stage that would pass the cap does not
#   start, and this is logged. If no n passes or the screen would pass the cap, the run ends with ASK AUTHOR (§5).
# After DONE, ASK AUTHOR or STOPPED: fetch v5b1_runs/cf with remote.sh fetch, `sha256sum -c SHA256SUMS` in the laptop copy, destroy.
set -u
W=${1:?WORKERS}; PRICE=${2:?PRICE_USD_H}; CAP=${3:?CAP_USD}
P=/home/catalin/work/phd
R=${4:-$P/v5b1_runs/cf}
PY=$P/phd_speed_harmo_v5b1_toolchain/venv/bin/python
D=docs/research/c1
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
if [ -f "$R/cpu" ] && [ "$(cat "$R/cpu")" != "$CPU" ]; then     # §7: one CPU model; a new host follows §5's procedure under a V#
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

must "plan cf_smoke" $PY $D/c1.py plan cf_smoke --out "$R/cf_smoke/jobs.json"
t1=$(date +%s)
must "smoke" $PY $D/c1.py smoke --jobs "$R/cf_smoke/jobs.json" --out "$R/cf_smoke" --workers "$W" --cpu "$CPU"
if [ -z "$COST_PER_RUN" ]; then     # the smoke's two passes (every arm, then each distinct config again) set the rate before the screen
  n=$(( $(wc -l < "$R/cf_smoke/a/s6_rows.jsonl") + $(wc -l < "$R/cf_smoke/b/s6_rows.jsonl") ))
  COST_PER_RUN=$($PY -c "import math; print(($(date +%s)-$t1)/3600*$PRICE/(math.ceil($n/$W)*$W))")
  echo "$COST_PER_RUN" > "$R/cost_per_run"
  say "rate from the smoke: $COST_PER_RUN USD per worker slot ($n runs)"
fi
say "wall s per arm (smoke): $(wall "$R/cf_smoke/a/s6_rows.jsonl")"

stage cf_ident || { say "ASK AUTHOR: cap at identity"; exit 0; }
must "read ident" $PY $D/read_cf.py ident "$R/cf_ident/s6_rows.jsonl" "$R/cf_ident/ident.json" --cpu "$CPU"
[ "$(val "$R/cf_ident/ident.json" '["action"]')" = stop ] && { say "STOPPED: identity (bug rule; see ident.json)"; exit 1; }
say "identity: learner-class traffic mismatch disclosed = $(val "$R/cf_ident/ident.json" '["learner_diff_disclosed"]')"

stage cf_screen || { say "ASK AUTHOR: the screen would pass the cap"; exit 0; }
must "read screen" $PY $D/read_cf.py screen "$R/cf_screen/screen.json" --rows "$R/cf_screen/s6_rows.jsonl" --seeds "$(range_of "$R/cf_screen/jobs.json")" --workers "$W"
say "screen: $(val "$R/cf_screen/screen.json" '["decision"]["outcome"]')"
say "DONE"
