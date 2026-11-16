#!/bin/bash
# Runs on the same rented host after remote_part1.sh (V515), in the same RUN folder, so part 1's readings are at hand. Order (common
# §2): EV tuning and evaluation (only if part 1's EV gate passed), then M2's X1 stage (only if M2 picked a level). EV tuning and
# evaluation form one stage for the cap check: tuning starts only if evaluation fits too. Progress in RUN/status.txt.
# usage: remote_part2.sh WORKERS PRICE_USD_H CAP_USD [RUN]    (CAP_USD: the cap left for part 2)
set -u
W=${1:?WORKERS}; PRICE=${2:?PRICE_USD_H}; CAP=${3:?CAP_USD}
P=/home/catalin/work/phd
R=${4:-$P/v5b1_runs/v505}
PY=$P/phd_speed_harmo_v5b1_toolchain/venv/bin/python
D=analysis/v505
unset SUMO_HOME
export OMP_NUM_THREADS=1
mkdir -p "$R"
[ -f "$R/t2" ] || date +%s > "$R/t2"     # part 2's start, so spend survives a relaunch (as part 1's t0)
T2=$(cat "$R/t2")
say() { echo "$(date -u '+%F %T') $1" >> "$R/status.txt"; }
step() { say "start $1"; shift; "$@" >> "$R/run.log" 2>&1; rc=$?; say "end rc=$rc"; return $rc; }
must() { step "$@" || { say "STOPPED"; exit 1; }; }
val() { $PY -c "import json,sys; print(json.load(open(sys.argv[1]))$2)" "$1" 2>/dev/null || echo None; }
sums() { (cd "$R" && find . -type f ! -name SHA256SUMS -print0 | LC_ALL=C sort -z | xargs -0 sha256sum > SHA256SUMS); }
trap sums EXIT
RATE=$(cat "$R/cost_per_run" 2>/dev/null)
[ -n "$RATE" ] || { say "STOPPED: no measured rate from part 1"; exit 1; }
fits() {     # fits LABEL RUNS: part 2's cap action (common §7), from part 1's measured cost per worker slot
  local ok
  ok=$($PY -c "import math,time; spent=(time.time()-$T2)/3600*$PRICE; nxt=math.ceil($2/$W)*$W*$RATE; print(int(spent+nxt<=$CAP), round(spent,2), round(nxt,2))")
  say "cap check $1: fits/spent/next $ok (cap $CAP)"
  [ "${ok%% *}" = 1 ]
}
runs() { $PY -c "import json,sys; j=json.load(open(sys.argv[1])); print(len(j['arms'])*(j['seed_range'][1]-j['seed_range'][0]+1))" "$1"; }
ev_run() {     # ev_run STAGE [plan args]: plan and run one EV part-2 stage
  local s=$1; shift
  must "plan $s" $PY $D/ev2.py plan "$s" --out "$R/$s/jobs.json" --limit "$LIM" "$@"
  must "run $s ($(runs "$R/$s/jobs.json") runs)" $PY $D/v5.py run --jobs "$R/$s/jobs.json" --out "$R/$s" --workers "$W"
  say "drops $s: $(cat "$R/$s/drops.json" 2>/dev/null)"
}

say "part 2: code $(cat COMMIT), workers $W, price $PRICE/h, cap $CAP, rate $RATE per worker slot"
A=$(val "$R/m2_pick/pick.json" '.get("a")')

ev2() {
  [ "$(val "$R/ev_gate/gate.json" '["outcome"]')" = pass ] || { say "EV part 2 not run: the gate did not pass"; return 0; }
  LIM=$(val "$R/ev_size/size.json" '["limit_kmh"]')
  # projected EV runs before the power rule: FX 21 + IP and SW up to 36 + 108 + 54, each x 60, and evaluation 9 x 120
  # common §7: tuning starts only if all of EV fits, extensions included (worst case: n = 100 tuning, n = 160 evaluation, smoke2)
  if [ -f "$R/ev_tune_fx/s6_rows.jsonl" ]; then
    say "EV part 2 resumed: the first projection is skipped"
  else
    fits "EV tuning and evaluation (worst case)" $(( 21 * 100 + 5 * 2 + (36 + 108 + 54) * 100 + 11 * 160 )) || { say "cap: EV part 2 not started"; return 0; }
  fi
  ev_run ev_tune_fx
  must "read fx" $PY $D/ev2.py fx "$R/ev_tune_fx/s6_rows.jsonl" "$R/ev_tune_fx/fx.json"
  must "planned power" $PY $D/ev2.py power "$R/ev_tune_fx/s6_rows.jsonl" "$R/ev_gate/s6_rows.jsonl" "$R/ev_tune_fx/fx.json" "$R/ev_power.json" --limit "$LIM"
  [ "$(val "$R/ev_tune_fx/fx.json" '.get("outcome")')" = VOID ] && { say "EV VOID: FX tuning dropped more than 3 seeds"; return 0; }
  rule=$(val "$R/ev_power.json" '["rule"]')
  say "EV power rule: $rule"
  [ "$rule" = VOID ] && { say "EV VOID: tuning or gate dropped more than 3 seeds"; return 0; }
  # cap action once the stage's size is known (common §7): every EV run still to come, extensions included
  case $rule in
    tune60_eval120) left=$(( (36 + 108 + 54) * 60 + 11 * 120 )) ;;
    tune100_eval120) left=$(( 21 * 40 + (36 + 108 + 54) * 100 + 11 * 120 )) ;;
    *) left=$(( 21 * 40 + (36 + 108 + 54) * 100 + 11 * 160 )) ;;
  esac
  fits "EV after the power rule ($rule)" "$left" || { say "cap: EV tuning not continued after the power rule; EV reads nothing"; return 0; }
  FXJ="$R/ev_tune_fx/fx.json"
  if [ "$rule" != tune60_eval120 ]; then     # EV §5: extend tuning to n = 100, every family re-picked
    ev_run ev_tune_fx_ext
    must "read fx (n = 100)" $PY $D/ev2.py fx "$R/ev_tune_fx/s6_rows.jsonl" "$R/ev_tune_fx_ext/fx.json" --ext-rows "$R/ev_tune_fx_ext/s6_rows.jsonl"
    FXJ="$R/ev_tune_fx_ext/fx.json"
  fi
  [ "$(val "$FXJ" '.get("outcome")')" = VOID ] && { say "EV VOID: tuning dropped more than 3 seeds"; return 0; }
  must "plan ev_smoke2" $PY $D/ev2.py plan ev_smoke2 --out "$R/ev_smoke2/jobs.json" --limit "$LIM" --picks "$FXJ"
  must "smoke ev part 2 (T0 IP, SW)" $PY $D/v5.py smoke --jobs "$R/ev_smoke2/jobs.json" --out "$R/ev_smoke2" --workers "$W"
  ev_run ev_tune_sw --picks "$FXJ"
  EXT=""
  if [ "$rule" != tune60_eval120 ]; then
    ev_run ev_tune_sw_ext --picks "$FXJ"
    EXT="--ext"
  fi
  must "read picks" $PY $D/ev2.py picks "$R/ev_tune_fx/s6_rows.jsonl" "$R/ev_tune_sw/s6_rows.jsonl" "$FXJ" "$R/ev_picks.json" $EXT
  [ "$(val "$R/ev_picks.json" '.get("outcome")')" = VOID ] && { say "EV VOID: tuning dropped more than 3 seeds"; return 0; }
  ev_run ev_eval --picks "$R/ev_picks.json"
  UP=""; EXTR=""; VAX=""
  if [ "$rule" = tune100_eval160 ] || [ "$rule" = underpowered ]; then
    ev_run ev_eval_ext --picks "$R/ev_picks.json"
    EXTR="--ext-rows $R/ev_eval_ext/s6_rows.jsonl"
  fi
  [ "$rule" = underpowered ] && UP="--underpowered $(val "$R/ev_power.json" '["tune100_eval160"]["p_false_kill_at_15"]')"
  must "read EV" $PY $D/ev2.py read "$R/ev_eval/s6_rows.jsonl" "$R/ev_picks.json" "$R/ev_result.json" $EXTR $UP
  say "EV: $(val "$R/ev_result.json" '["outcome"]'), lane-end-bound $(val "$R/ev_result.json" '.get("lane_end_bound")')"
  VA=""
  OUT=$(val "$R/ev_result.json" '["outcome"]')
  if [ "$(val "$R/ev_result.json" '.get("lane_end_bound")')" = True ] && [ "$A" != None ] && [[ "$OUT" != *underpowered* ]]; then     # common §6: repeat on V-A
    n_va=$(( 11 * 120 )); [ -n "$EXTR" ] && n_va=$(( 11 * 160 ))
    if fits "ev_va" "$n_va"; then
      ev_run ev_va --picks "$R/ev_picks.json" --a "$A"
      if [ -n "$EXTR" ]; then ev_run ev_va_ext --picks "$R/ev_picks.json" --a "$A"; VAX="--ext-rows $R/ev_va_ext/s6_rows.jsonl"; fi
      must "read EV on V-A" $PY $D/ev2.py read "$R/ev_va/s6_rows.jsonl" "$R/ev_picks.json" "$R/ev_result_va.json" --s-cell "SV${A%.0}" --by-pick 0 $VAX $UP
      VA="--va $R/ev_result_va.json --va-rows $R/ev_va/s6_rows.jsonl"
    else
      say "cap: ev_va not started"
    fi
  fi
  AA=""; [ "$A" != None ] && AA="--a $A"
  must "EV final (common §6)" $PY $D/ev2.py final "$R/ev_eval/s6_rows.jsonl" "$R/ev_result.json" "$R/ev_final.json" $EXTR $VA $AA
  say "EV final: $(val "$R/ev_final.json" '["outcome"]') ($(val "$R/ev_final.json" '["repeat"]'))"
}

x1() {
  [ "$A" = None ] && { say "M2 X1 not run: no V-A level"; return 0; }
  [ -f "$R/m2_verdict/verdict.json" ] || [ -f "$R/m2_fallback/verdict.json" ] || { say "M2 X1 not run: no S/TRUCK verdict"; return 0; }
  must "plan m2_x1" $PY $D/v5.py plan m2_x1 --out "$R/m2_x1/jobs.json" --a "$A"
  fits "m2_x1" "$(runs "$R/m2_x1/jobs.json")" || {
    say "cap: m2_x1 not started; C5 and C5b read not tested"
    if [ -f "$R/m2_fallback/verdict.json" ]; then
      must "read verdict (X1 dropped)" $PY $D/read_m2.py verdict "$R/m2_fallback/s6_rows.jsonl" "$R/m2_verdict_final.json" --pick "$R/m2_pick/pick.json" --fallback --x1-dropped
    else
      must "read verdict (X1 dropped)" $PY $D/read_m2.py verdict "$R/m2_verdict/s6_rows.jsonl" "$R/m2_verdict_final.json" --pick "$R/m2_pick/pick.json" --x1-dropped
    fi
    return 0; }
  must "run m2_x1" $PY $D/v5.py run --jobs "$R/m2_x1/jobs.json" --out "$R/m2_x1" --workers "$W"
  if [ -f "$R/m2_fallback/verdict.json" ]; then
    must "read verdict with X1" $PY $D/read_m2.py verdict "$R/m2_fallback/s6_rows.jsonl" "$R/m2_verdict_final.json" --pick "$R/m2_pick/pick.json" --fallback --x1 "$R/m2_x1/s6_rows.jsonl"
  else
    must "read verdict with X1" $PY $D/read_m2.py verdict "$R/m2_verdict/s6_rows.jsonl" "$R/m2_verdict_final.json" --pick "$R/m2_pick/pick.json" --x1 "$R/m2_x1/s6_rows.jsonl"
  fi
  say "M2 final PR-28 line: $(val "$R/m2_verdict_final.json" '["pr28"]')"
}

( ev2 ) || say "EV part 2 ended early"
x1
say "DONE part 2"
