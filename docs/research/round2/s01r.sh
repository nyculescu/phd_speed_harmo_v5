#!/bin/bash
# Laptop side of S0 + S1 (V470-V473): rent, deploy, start, then a health and job check every 5 minutes; at the end fetch, verify by
# SHA-256 and destroy. Hard cap $5. Any failure (check, step, stall, lost SSH, cap) fetches what exists, verifies it, destroys the
# instance and writes S01_ALERT; the author reads it in the morning. usage: s01r.sh REF
set -u
REF=${1:?REF}
CAP=5
RUNS=/home/catalin/work/phd/v5b1_runs; WK=$RUNS/measure_s01; F=$RUNS/measure_s01_remote
L=$RUNS/s01_status.txt
TR=/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/toolchain/remote
VPY=/home/catalin/work/phd/vastai_venv/bin/python; VAST=/home/catalin/work/phd/vastai_venv/bin/vastai
say() { echo "$(date '+%F %T') $1" >> "$L"; }
inst() { $VAST show instances --raw 2>/dev/null | $VPY -c "
import json, sys
d = json.load(sys.stdin); d = d if isinstance(d, list) else d['instances']
for i in d:
    if i.get('label') == 'v5b1':
        print(i['id'], i.get('start_date') or 0, i.get('dph_total') or 0)"; }
spent() { $VPY -c "import time; print(round($SPENT0 + max(0, time.time() - $START) / 3600 * $DPH, 2))"; }
bank() { SPENT0=$(spent); START=$(date +%s); }     # a failed attempt's cost stays counted against the cap
# The cheapest offer per effective CPU that fits: no RTX A2000 host (they stalled at "Preparing GPUs", author 2026-11-08), no
# 2014-2017 Xeon or first-generation EPYC, and a projected cost (273 CPU-h on W = effective - 2 workers, plus 0.5 h) under 60 % of the cap.
pick() { $VAST search offers "cpu_arch=amd64 cpu_cores_effective>=48 cpu_ram>=64 disk_space>=40 reliability>0.99 duration>=2 inet_down>=100 rentable=true" -o dph_total --raw 2>/dev/null | $VPY -c "
import json, re, sys
d = json.load(sys.stdin); tried = set(sys.argv[1].split()); slow = re.compile(r'E5-|E7-|Xeon Phi|EPYC 7\\d\\d1')
ok = []
for o in d:
    eff = o.get('cpu_cores_effective') or 0
    if str(o['id']) in tried or 'A2000' in (o.get('gpu_name') or '') or slow.search(o.get('cpu_name') or '') or eff < 48:
        continue
    cost = (273 / (eff - 2) + 0.5) * o['dph_total']
    if cost < 0.6 * $CAP:
        ok.append((o['dph_total'] / eff, o))
if ok:
    o = min(ok, key=lambda x: x[0])[1]
    print(o['id'], f\"{o['id']} {o.get('cpu_name')} {o['cpu_cores_effective']:.0f} CPUs {o.get('gpu_name')} \${o['dph_total']:.3f}/h {o.get('geolocation')}\")" "$1"; }
sums() { find . -path '*/rd' -prune -o -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum; }

destroy_all() {
  local ids; ids=$(inst | cut -d' ' -f1)
  for id in $ids; do
    for _ in 1 2 3; do $VAST destroy instance "$id" -y >> "$L" 2>&1; sleep 30; inst | grep -q "^$id " || break; done
    if inst | grep -q "^$id "; then say "DESTROY NOT CONFIRMED for $id"; echo "destroy of $id not confirmed" >> "$RUNS/S01_ALERT"; else say "instance $id destroyed (absent from the account's list)"; fi
  done
}

fetch_verify() {
  mkdir -p "$F"
  local ok=0
  for _ in 1 2 3; do rsync -a -e "ssh -p $PT -o BatchMode=yes -o ConnectTimeout=20" --exclude rd "$U@$H:$WK/" "$F/" && { ok=1; break; }; sleep 60; done
  [ $ok -eq 1 ] || { say "fetch failed three times"; return 1; }
  ssh -p "$PT" -o BatchMode=yes -o ConnectTimeout=20 "$U@$H" "cd $WK && $(declare -f sums); sums" > "$F.remote_sums" 2>/dev/null || { say "remote checksums failed"; return 1; }
  (cd "$F" && sums) > "$F.local_sums"
  cmp -s "$F.remote_sums" "$F.local_sums" || { say "fetched files differ from the remote ones"; return 1; }
  say "fetched and verified: $(wc -l < "$F.local_sums") files match by SHA-256"
}

finish() {     # finish OK|reason
  if [ -n "${H:-}" ]; then fetch_verify || echo "fetch not verified" >> "$RUNS/S01_ALERT"; fi
  destroy_all
  if [ "$1" = OK ] && [ ! -e "$RUNS/S01_ALERT" ]; then touch "$RUNS/S01_DONE"; say "S01 DONE, spent about \$$(spent)"
  else echo "$1" >> "$RUNS/S01_ALERT"; say "S01 STOPPED: $1; spent about \$$(spent)"; fi
  exit 0
}

say "start: ref $REF, offer picked at rent time (no RTX A2000, no slow CPU, projected cost under \$$CAP), cap \$$CAP"
START=$(date +%s); DPH=0.5; H=; SPENT0=0; tried=; acc=
for attempt in 1 2 3; do
  o=$(pick "$tried"); [ -n "$o" ] || { say "no fitting offer left"; break; }
  read -r OID ODESC <<< "$o"; tried="$tried $OID"
  say "attempt $attempt: offer $ODESC"
  T=$($VPY "$TR/vast.py" rent "$OID" --yes 2>>"$L" | tail -n 1)
  if [[ $T != ssh\ * ]]; then say "offer $OID did not boot or answer SSH"; bank; destroy_all; T=; continue; fi
  read -r ID START DPH <<< "$(inst | head -1)"
  START=${START%.*}; [ "${START:-0}" -gt 0 ] 2>/dev/null || START=$(date +%s)
  read -r -a a <<< "$T"; PT=${a[2]}; U=${a[3]%@*}; H=${a[3]#*@}
  say "rented instance $ID at \$$DPH/h: $T"
  REF=$REF bash "$TR/remote.sh" deploy "$T" > "$RUNS/s01_deploy_$attempt.log" 2>&1
  acc=$(grep -a "ACCEPT PASS" "$RUNS/s01_deploy_$attempt.log" | tail -1)
  [ -n "$acc" ] && break
  say "deploy on $ID did not pass acceptance (s01_deploy_$attempt.log)"; bank; destroy_all; H=; T=
done
[ -n "$acc" ] || finish "no machine booted and deployed in 3 attempts"
q=$(sed -E 's/ACCEPT PASS: ([0-9.]+) CPUs.*/\1/' <<< "$acc"); [[ $q =~ ^[0-9.]+$ ]] || q=$(ssh -p "$PT" -o BatchMode=yes "$U@$H" getconf _NPROCESSORS_ONLN)
W=$(( ${q%.*} - 2 )); [ $W -ge 8 ] || W=8
th=$(ssh -p "$PT" -o BatchMode=yes "$U@$H" getconf _NPROCESSORS_ONLN 2>/dev/null); [[ $th =~ ^[0-9]+$ ]] || th=$W
say "deployed: $acc; workers $W; the dashboard should show about $(( 100 * W / th ))% CPU and about $(( W / 3 + 8 )) GB RAM"

ssh -p "$PT" -o BatchMode=yes "$U@$H" "mkdir -p $RUNS/round2 $RUNS/baseline_v4" || finish "ssh failed"
rsync -a -e "ssh -p $PT -o BatchMode=yes" --exclude rd --exclude 'rd_*' --exclude 'code_*' --exclude local_partial_3ex --exclude 'checks_trial*' \
  --exclude val_laptop_partial "$RUNS/round2/" "$U@$H:$RUNS/round2/" || finish "rsync round2 failed"
rsync -a -e "ssh -p $PT -o BatchMode=yes" "$RUNS/baseline_v4/" "$U@$H:$RUNS/baseline_v4/" || finish "rsync baseline_v4 failed"
bash "$TR/remote.sh" run "$T" s01 "bash docs/research/round2/remote_s01.sh $W" >> "$L" 2>&1 || finish "remote start failed"
say "remote job s01 started"

miss=0; last=; same=0
while sleep 300; do
  st=$(ssh -p "$PT" -o BatchMode=yes -o ConnectTimeout=20 "$U@$H" "tail -1 $WK/status.txt 2>/dev/null; cat $WK/rows_*.jsonl 2>/dev/null | wc -l;
       cut -d' ' -f1 /proc/loadavg; free -g | awk '/Mem:/{print \$3}'; df -BG --output=avail $RUNS | tail -1; tmux has-session -t s01 2>/dev/null && echo RUNNING || echo GONE" 2>/dev/null)
  if [ -z "$st" ]; then miss=$((miss + 1)); say "health: ssh failed ($miss)"; [ $miss -ge 3 ] && finish "no ssh for 3 checks"; continue; fi
  miss=0
  mapfile -t s <<< "$st"
  say "health: rows ${s[1]}/5560, load ${s[2]}, RAM ${s[3]} GB used, disk ${s[4]// /} free, job ${s[5]}, \$$(spent) spent | ${s[0]}"
  grep -q STOPPED <<< "${s[0]}" && finish "remote: ${s[0]}"
  grep -q DONE <<< "${s[0]}" && finish OK
  [ "${s[5]}" = RUNNING ] || finish "remote job ended without DONE"
  $VPY -c "import sys; sys.exit(0 if $(spent) < $CAP else 1)" || finish "cost cap \$$CAP reached"
  if grep -q "start run S0 and S1" <<< "${s[0]}"; then
    if [ "${s[1]}" = "$last" ]; then same=$((same + 1)); else same=0; fi
    [ $same -ge 4 ] && finish "stalled: no new row for 20 minutes"
  fi
  last=${s[1]}
done
