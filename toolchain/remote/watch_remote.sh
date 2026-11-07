#!/bin/bash
# 5-minute health log of every job on the rented machine (V447); writes REMOTE_ALERT on a crash, stop or fault so Claude can wake on it.
# usage: watch_remote.sh "SSH COMMAND"
T=$1; P=/home/catalin/work/phd; LOG=$P/v5b1_runs/remote_health.log; AL=$P/v5b1_runs/REMOTE_ALERT; SEEN=$P/v5b1_runs/remote_events_seen; touch "$SEEN"
read -r -a S <<< "$T"
while :; do
  line=$(timeout 90 "${S[@]}" -o BatchMode=yes -o ConnectTimeout=20 'V=/home/catalin/work/phd/v5b1_runs
    echo "load=$(cut -d" " -f1 /proc/loadavg) mem_free=$(free -g | awk "/Mem/{print \$7}")GB jobs=$(tmux ls 2>/dev/null | cut -d: -f1 | grep -v ssh_tmux | tr "\n" ",") 3e_runs=$(wc -l < $V/round2/cma3e/runs.jsonl 2>/dev/null) 3e_evals=$(cat $V/round2/cma3e/evals.jsonl 2>/dev/null | wc -l) r1=[$(tail -1 $V/round1/out/status.txt | cut -c12-80)] r2=[$(tail -1 $V/round2/status.txt | cut -c12-70)]"
    grep -hE "STOPPED|FAULT|crashed|failed twice|STALLED|ROUND KILL|OUT" $V/round1/out/status.txt $V/round2/status.txt 2>/dev/null | tail -3 | sed "s/^/EVENT /"
    grep -l Traceback $V/jobs/*.log 2>/dev/null | sed "s/^/TRACEBACK /"' 2>/dev/null) || line="UNREACHABLE"
  echo "$(date '+%F %T') ${line//$'\n'/ | }" >> "$LOG"
  # Alert only on events not seen before, so a known, handled event does not re-alert every 5 minutes.
  new=$(grep -E "^(EVENT|TRACEBACK)" <<< "$line" | grep -vxF -f "$SEEN")
  grep -E "^(EVENT|TRACEBACK)" <<< "$line" >> "$SEEN"; sort -u -o "$SEEN" "$SEEN"
  if [ -n "$new" ] || [ "$line" = UNREACHABLE ]; then echo "$(date '+%F %T') ${new:-UNREACHABLE}" > "$AL"; fi
  sleep 300
done
