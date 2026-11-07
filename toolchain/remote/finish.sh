#!/bin/bash
# Finisher for an unattended rented machine (V442): when no job session is left (or at the deadline), copy every run back to the laptop, then destroy the instance.
# It works without Claude, so a session that runs out of tokens does not leave the machine billing. Nothing is destroyed unless every copy succeeded.
# usage: finish.sh "SSH COMMAND" INSTANCE_ID DEADLINE_EPOCH
T=$1; ID=$2; END=$3
R=$(dirname "$(realpath "$0")"); P=/home/catalin/work/phd; LOG=$P/v5b1_runs/finish.log
say() { echo "$(date '+%F %T') $1" >> "$LOG"; }
say "watching $T (instance $ID) until no job session is left, deadline $(date -d @"$END" '+%F %T')"
while :; do
  # Every tmux session except the login one is a job; an unreachable host counts as busy until the deadline.
  if out=$(timeout 90 bash "$R/remote.sh" status "$T" 2>/dev/null); then
    left=$(printf '%s\n' "$out" | awk -F: '/ windows \(created/ && $1 != "ssh_tmux" {print $1}' | tr '\n' ' ')
    [ -z "$left" ] && { say "all jobs ended"; break; }
  fi
  [ "$(date +%s)" -ge "$END" ] && { say "deadline reached with jobs: ${left:-unknown}"; break; }
  sleep 300
done
ok=1
for run in round1 round2 jobs; do
  for try in 1 2 3; do
    if timeout 3600 bash "$R/remote.sh" fetch "$T" "$run" >> "$LOG" 2>&1; then say "fetched $run"; continue 2; fi
    say "fetch $run failed (try $try)"; sleep 60
  done
  ok=0
done
if [ $ok -eq 1 ]; then
  if grep -q DONE "$P/v5b1_runs/round1_remote/out/status.txt" 2>/dev/null; then
    # Round 1 finished remotely, so the laptop's frozen fallback is no longer needed.
    systemctl --user thaw r1-chain 2>/dev/null; systemctl --user stop r1-chain 2>/dev/null && say "laptop r1-chain stopped (remote round 1 DONE)"
  else
    say "remote round 1 not DONE: laptop r1-chain left frozen for the author"
  fi
  "$P/vastai_venv/bin/python" "$R/vast.py" destroy "$ID" --yes >> "$LOG" 2>&1 && say "instance $ID destroyed" || say "DESTROY FAILED: destroy $ID by hand"
else
  say "a fetch failed: instance $ID NOT destroyed; it is still billing"
fi
