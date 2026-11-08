#!/bin/bash
# Round 2 (author, 2026-11-07): move the rest of the evaluation to a rented machine, then bring the rows back and destroy it.
# Deploys while the laptop keeps running, then stops the laptop chain, ships the rows done so far and runs remote2_eval.sh there.
# Any failure before the destroy leaves the instance running and writes REMOTE_ALERT. usage: move2r.sh "SSH COMMAND" WORKERS
set -u
T=$1; W=$2
read -r -a a <<< "$T"; PT=22; H=
for ((i = 1; i < ${#a[@]}; i++)); do case ${a[i]} in -p) PT=${a[i+1]}; i=$((i + 1)) ;; -L|-i|-o) i=$((i + 1)) ;; *@*) H=${a[i]#*@} ;; esac; done
SSH=(ssh -o ConnectTimeout=20 -o BatchMode=yes -o StrictHostKeyChecking=accept-new -p "$PT" "root@$H")
RUNS=/home/catalin/work/phd/v5b1_runs; D=$RUNS/round2; F=$RUNS/round2_evalremote
HERE=$(dirname "$(realpath "$0")")
REMOTE=/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/toolchain/remote/remote.sh
VAST=/home/catalin/work/phd/vastai_venv/bin/vastai
PY=/home/catalin/work/phd/phd_speed_harmo_v5b1_toolchain/venv/bin/python
L=$D/status_move.txt
say() { echo "$(date '+%F %T') $1" >> "$L"; }
halt() { say "STOPPED: $1; instance left running, goes to the author"; echo "$1" > "$D/REMOTE_ALERT"; exit 2; }
sums() { find val test band -path '*/rd*' -prune -o -type f -print0 2>/dev/null | LC_ALL=C sort -z | xargs -0 sha256sum; }
rs() { rsync -a --delete -e "ssh -p $PT -o BatchMode=yes" "$@"; }

say "move start: $H:$PT, $W workers"
ID=$($VAST show instances --raw 2>/dev/null | $PY -c "
import json, sys
d = json.load(sys.stdin); d = d if isinstance(d, list) else d['instances']
m = [i['id'] for i in d if i.get('public_ipaddr') == sys.argv[1] or i.get('ssh_host') == sys.argv[1]]
print(m[0] if len(m) == 1 else '')" "$H")
[ -n "$ID" ] || halt "no single vast.ai instance matches $H"
say "instance $ID"

REF=6c49e7e bash "$REMOTE" deploy "$T" > "$D/deploy_remote.log" 2>&1
grep -q "ACCEPT PASS" "$D/deploy_remote.log" || halt "deploy did not pass acceptance (deploy_remote.log)"
say "deployed: $(grep -a 'ACCEPT PASS' "$D/deploy_remote.log" | tail -1)"

systemctl --user stop r2-health r2-guard 2>/dev/null
systemctl --user kill -s SIGKILL r2-chain 2>/dev/null
for _ in $(seq 12); do systemctl --user is-active -q r2-chain || break; sleep 5; done
systemctl --user is-active -q r2-chain && halt "laptop chain would not stop"
systemctl --user reset-failed r2-chain 2>/dev/null
echo "$(date '+%F %T') laptop chain stopped; the rest runs on vast.ai instance $ID (author)" >> "$D/status.txt"
say "laptop chain stopped"

"${SSH[@]}" "mkdir -p $RUNS/round2 $RUNS/round2_remote $RUNS/round1_remote/out $RUNS/baseline_v4 $RUNS/conf3" || halt "ssh failed"
rs --exclude 'rd' --exclude 'rd_*' --exclude 'local_partial_3ex' --exclude 'checks_trial*' "$D/" "root@$H:$D/" || halt "rsync round2 failed"
for x in round2_remote round1_remote/out baseline_v4 conf3; do rs "$RUNS/$x/" "root@$H:$RUNS/$x/" || halt "rsync $x failed"; done
scp -q -P "$PT" -o BatchMode=yes "$HERE/remote2_eval.sh" "root@$H:$RUNS/jobs/remote2_eval.sh" || halt "scp failed"
"${SSH[@]}" "tmux new -d -s r2eval 'bash $RUNS/jobs/remote2_eval.sh $W > $RUNS/jobs/r2eval.log 2>&1'" || halt "remote start failed"
say "remote evaluation started"

miss=0
while sleep 600; do
  st=$("${SSH[@]}" "cat $D/status_remote_eval.txt 2>/dev/null; tmux has-session -t r2eval 2>/dev/null && echo RUNNING; true" 2>/dev/null) || {
    miss=$((miss + 1)); say "ssh failed ($miss)"; [ $miss -ge 6 ] && halt "no ssh for 6 polls"; continue; }
  miss=0
  grep -q STOPPED <<< "$st" && halt "remote: $(grep STOPPED <<< "$st" | tail -1)"
  grep -q DONE <<< "$st" && break
  grep -q RUNNING <<< "$st" || halt "remote job ended without DONE"
done
say "remote DONE"

mkdir -p "$F"
ok=0
for i in 1 2 3; do rs --exclude 'rd' --exclude 'rd_*' --exclude 'code_*' "root@$H:$D/" "$F/" && { ok=1; break; }; sleep 60; done
[ $ok -eq 1 ] || halt "fetch failed three times"
"${SSH[@]}" "cd $D && $(declare -f sums); sums" > "$F.remote_sums" 2>/dev/null || halt "remote checksums failed"
(cd "$F" && sums) > "$F.local_sums"
cmp -s "$F.remote_sums" "$F.local_sums" || halt "fetched files differ from the remote ones"
[ -s "$F/test_result.json" ] && [ -s "$F/val/validation.json" ] || halt "readings missing"
say "fetched and verified: $(wc -l < "$F.local_sums") files match by SHA-256"

[ -d "$D/val" ] && mv "$D/val" "$D/val_laptop_partial"
for x in val test band; do [ -d "$F/$x" ] && cp -a "$F/$x" "$D/"; done
cp "$F/test_result.json" "$F/status_remote_eval.txt" "$F/chain_remote.log" "$D/"
[ -f "$D/test_result.json" ] || halt "swap-in failed"
say "rows and readings in place; laptop partial validation kept as val_laptop_partial"

gone() { $VAST show instances --raw 2>/dev/null | $PY -c "import json, sys; d = json.load(sys.stdin); d = d if isinstance(d, list) else d['instances']; sys.exit(any(i['id'] == $ID for i in d))"; }
for i in 1 2 3; do $VAST destroy instance "$ID" -y >> "$L" 2>&1; sleep 30; gone && break; done
if gone; then say "instance $ID destroyed (absent from the account's instance list)"; else say "DESTROY NOT CONFIRMED"; echo "destroy of $ID not confirmed" > "$D/REMOTE_ALERT"; fi

C=$D/code_6c49e7e
(cd "$C" && PYTHONPATH=$C:$C/docs/research/round2:$C/docs/research/round1 $PY "$HERE/thesis2.py" "$D" "$D/val/validation.json") > "$D/thesis_v459.txt" 2>&1 \
  && say "thesis reading V459 written" || say "thesis reading failed (thesis_v459.txt)"
touch "$D/EVAL_DONE"
