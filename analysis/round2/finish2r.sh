#!/bin/bash
# Round 2 (author, 2026-11-07): wait for the rented 3E-X searches, fetch and verify them, swap them in for the frozen local ones,
# destroy the instance, then restart the chain, which skips the passed checks and the finished searches.
# Any failure before the destroy leaves the instance running and writes REMOTE_ALERT. usage: finish2r.sh
set -u
ID=59611488; T="ssh -p 34685 root@70.69.192.6"
SSH=(ssh -o ConnectTimeout=20 -o BatchMode=yes -p 34685 root@70.69.192.6)
RP=/home/catalin/work/phd/v5b1_runs/r2search
D=/home/catalin/work/phd/v5b1_runs/round2; F=/home/catalin/work/phd/v5b1_runs/r2search_remote; C=$D/code_6c49e7e
REMOTE=/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/toolchain/remote/remote.sh
VAST=/home/catalin/work/phd/vastai_venv/bin/vastai
PY=/home/catalin/work/phd/phd_speed_harmo_v5b1_toolchain/venv/bin/python
L=$D/status_remote.txt
say() { echo "$(date '+%F %T') $1" >> "$L"; }
halt() { say "STOPPED: $1; instance $ID left running, goes to the author"; echo "$1" > "$D/REMOTE_ALERT"; exit 2; }
sums() { find . -path '*/rd*' -prune -o -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum; }

say "poller start"
miss=0
while :; do
  st=$("${SSH[@]}" "cat $RP/status.txt 2>/dev/null; tmux has-session -t r2search 2>/dev/null && echo RUNNING; true" 2>/dev/null) || {
    miss=$((miss + 1)); say "ssh failed ($miss)"; [ $miss -ge 6 ] && halt "no ssh for 6 polls"; sleep 600; continue; }
  miss=0
  grep -q FAILED <<< "$st" && halt "remote search failed: $(grep FAILED <<< "$st" | tr '\n' ' ')"
  grep -q DONE <<< "$st" && break
  grep -q RUNNING <<< "$st" || halt "remote job ended without DONE"
  sleep 600
done
say "remote DONE: $(grep -v RUNNING <<< "$st" | tr '\n' ' ')"

ok=0
for i in 1 2 3; do bash "$REMOTE" fetch "$T" r2search >> "$L" 2>&1 && { ok=1; break; }; sleep 60; done
[ $ok -eq 1 ] || halt "fetch failed three times"
"${SSH[@]}" "cd $RP && $(declare -f sums); sums" > "$F.remote_sums" 2>/dev/null || halt "remote checksums failed"
(cd "$F" && sums) > "$F.local_sums"
cmp -s "$F.remote_sums" "$F.local_sums" || halt "fetched files differ from the remote ones"
for c in x1 x2; do
  $PY -c "import json, sys; f = json.load(open(sys.argv[1])); assert 'pick' in f, 'no pick'" "$F/cma3e_$c/final.json" || halt "final.json of $c unreadable"
  [ -s "$F/cma3e_$c/final_runs.jsonl" ] || halt "final_runs.jsonl of $c empty"
done
"${SSH[@]}" "readlink -f /home/catalin/work/phd/code/current; cat /home/catalin/work/phd/v5b1_runs/jobs/r2search.sh" > "$F.provenance" 2>/dev/null
say "fetched and verified: $(wc -l < "$F.local_sums") files match by SHA-256; code $(head -1 "$F.provenance")"

# Frozen tasks die on SIGKILL under the cgroup v2 freezer, so the local searches never resume.
systemctl --user kill -s SIGKILL r2-chain
for _ in $(seq 12); do systemctl --user is-active -q r2-chain || break; sleep 5; done
if systemctl --user is-active -q r2-chain; then systemctl --user thaw r2-chain; systemctl --user stop r2-chain; fi
systemctl --user is-active -q r2-chain && halt "old chain unit would not stop"
systemctl --user reset-failed r2-chain 2>/dev/null
P=$D/local_partial_3ex; mkdir -p "$P"
for x in cma3e_x1 cma3e_x2 cma3e_x1.log cma3e_x2.log; do [ -e "$D/$x" ] && mv "$D/$x" "$P/"; done
for c in x1 x2; do rsync -a --exclude 'rd*' "$F/cma3e_$c" "$D/" && cp "$F/cma3e_$c.log" "$D/"; done
[ -f "$D/cma3e_x1/final.json" ] && [ -f "$D/cma3e_x2/final.json" ] || halt "swap-in failed"
say "local partial searches moved to $P; remote searches in place"

gone() { $VAST show instances --raw 2>/dev/null | $PY -c "import json, sys; d = json.load(sys.stdin); d = d if isinstance(d, list) else d['instances']; sys.exit(any(i['id'] == $ID for i in d))"; }
for i in 1 2 3; do
  $VAST destroy instance $ID -y >> "$L" 2>&1; sleep 30
  gone && break
done
if gone; then say "instance $ID destroyed (absent from the account's instance list)"; else say "DESTROY NOT CONFIRMED"; echo "destroy of $ID not confirmed" > "$D/REMOTE_ALERT"; fi

[ -f "$D/HEALTH_ALERT" ] && mv "$D/HEALTH_ALERT" "$D/HEALTH_ALERT.freeze"
echo "$(date '+%F %T') chain restarted with the rented 3E-X searches in place (author)" >> "$D/status.txt"
systemd-run --user --unit r2-chain --collect --working-directory="$C" /bin/bash "$C/analysis/round2/chain2.sh" "$C" "$D" >> "$L" 2>&1
sleep 3
h=$(date +%H); if [ "$h" -ge 23 ] || [ "$h" -lt 9 ]; then bash "$C/analysis/round2/pace2.sh" night; else bash "$C/analysis/round2/pace2.sh" day; fi
systemctl --user is-active -q r2-chain && say "chain restarted" || { say "chain did not restart, goes to the author"; echo "chain did not restart" > "$D/REMOTE_ALERT"; exit 2; }
touch "$D/REMOTE_DONE"
