#!/bin/bash
# Round 1 health check every 5 minutes (author, V428). usage: health1.sh out_dir
# One line per check to health.log; any problem also writes HEALTH_ALERT, which wakes Claude. A file THROTTLED means paused workers are expected.
D=$(realpath "$1"); L=$D/health.log; A=$D/HEALTH_ALERT
PAT='^/home/catalin/work/phd/phd_speed_harmo_v5b1_toolchain/venv/bin/python -c from multiprocessing.spawn'
low=0
cpu() { read -r _ a b c d e _ < /proc/stat; t0=$((a+b+c+d+e)); i0=$((d+e)); sleep 10; read -r _ a b c d e _ < /proc/stat; t1=$((a+b+c+d+e)); i1=$((d+e)); echo $(( 100 - 100 * (i1 - i0) / (t1 - t0) )); }
while true; do
  now=$(date '+%F %T'); why=()
  stage=$(grep -a ' start ' "$D/status.txt" | tail -1 | sed 's/^[0-9-]* [0-9:]* start //')
  grep -q 'DONE' "$D/status.txt" && { echo "$now chain DONE" >> "$L"; exit 0; }
  systemctl --user is-active -q r1-chain || why+=("chain unit not active")
  systemctl --user is-active -q r1-guard || why+=("guard unit not active")
  c=$(cpu)
  case "$stage" in
    training*) min=15 ;;
    "stage 0"|validation*|test*) min=30 ;;
    *) min=0 ;;
  esac
  if [ "$c" -lt "$min" ] && [ ! -f "$D/THROTTLED" ]; then low=$((low+1)); else low=0; fi
  [ $low -ge 2 ] && why+=("CPU ${c} % below ${min} % for two checks in '$stage'")
  new=$(find "$D" -type f ! -name health.log ! -name HEALTH_ALERT -mmin -15 -print -quit)
  [ -z "$new" ] && why+=("no file changed for 15 minutes")
  bad=$(grep -aE 'STOPPED|STALLED|FAULT|failed twice' "$D/status.txt" | tail -1)
  [ -n "$bad" ] && why+=("status: $bad")
  paused=0; run=0
  for p in $(pgrep -f "$PAT"); do s=$(awk '{print $3}' /proc/$p/stat 2>/dev/null); [ "$s" = T ] && paused=$((paused+1)) || run=$((run+1)); done
  [ $paused -gt 0 ] && [ ! -f "$D/THROTTLED" ] && why+=("$paused workers paused without a throttle")
  hw=$(grep -l coretemp /sys/class/hwmon/hwmon*/name | head -1 | xargs dirname)     # the sensors btop reads (V431)
  temp=0; csum=0; cn=0
  for t in $hw/temp*_input; do l=$(cat ${t%_input}_label); v=$(( $(cat $t) / 1000 )); case "$l" in Package*) temp=$v ;; Core*) csum=$((csum+v)); cn=$((cn+1)) ;; esac; done
  cmean=$(( cn ? csum / cn : 0 ))
  [ "$temp" -ge 99 ] && why+=("package ${temp} °C")     # near the CPU's throttle point
  mem=$(awk '/MemAvailable/ {print int($2 / 1048576)}' /proc/meminfo)
  [ "$mem" -lt 4 ] && why+=("only ${mem} GB memory available")
  echo "$now stage='$stage' cpu=${c}% workers=${run} paused=${paused} pkg=${temp}C cores_mean=${cmean}C mem_free=${mem}GB ${why[*]:+ALERT: ${why[*]}}" >> "$L"
  [ ${#why[@]} -gt 0 ] && echo "$now ${why[*]}" >> "$A"
  sleep 290
done
