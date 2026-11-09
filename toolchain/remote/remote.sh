#!/bin/bash
# Deploy and drive the project on a rented Ubuntu machine over SSH. Nothing secret is copied there: code goes as a git archive of HEAD.
# usage (TARGET is either HOST PORT, or the provider's SSH command pasted in quotes, e.g. "ssh -p 41234 root@ssh5.vast.ai"):
#   remote.sh up TARGET NAME CMD       deploy, check, then start CMD as job NAME: the one command from rental to running
#   remote.sh deploy TARGET            ship HEAD, build the toolchain, run the acceptance checks
#   remote.sh run TARGET NAME CMD      start CMD in tmux session NAME inside the deployed code
#   remote.sh status TARGET            load, memory, jobs, last log lines
#   remote.sh fetch TARGET RUN         copy v5b1_runs/RUN back to the laptop as v5b1_runs/RUN_remote
#   remote.sh code TARGET REF          ship one more commit as code/<sha> (no toolchain build), e.g. a base commit to compare against
# Every shipped snapshot carries COMMIT (the full sha) and MANIFEST (SHA-256 of every file), so code can prove its commit and that
# nothing changed on the host. DATA_EXTRA="path ..." mirrors more run data at the laptop's paths.
# The login user comes from the SSH command, else RUSER, else root.
# REF=<branch or commit> deploys that ref instead of HEAD; CODE=<short sha> runs a job in that deployed snapshot instead of the latest.
#   remote.sh launch NAME CMD          rent the cheapest fitting vast.ai offer (asks first), then up: the one command from nothing to running
set -euo pipefail
cmd=${1:?usage: remote.sh launch|up|deploy|code|run|status|fetch ...}; shift
if [ "$cmd" = launch ]; then
  t=$(/home/catalin/work/phd/vastai_venv/bin/python "$(dirname "$0")/vast.py" rent | tail -n 1)
  exec "$0" up "$t" "$@"
fi
U=
if [[ ${1:-} == ssh\ * ]]; then
  read -r -a a <<< "$1"; shift
  PT=22
  for ((i = 1; i < ${#a[@]}; i++)); do
    case ${a[i]} in
      -p) PT=${a[i+1]}; i=$((i + 1)) ;;
      -L|-i|-o) i=$((i + 1)) ;;
      *@*) U=${a[i]%@*}; H=${a[i]#*@} ;;
    esac
  done
  : "${H:?no user@host in the SSH command}"
else
  H=${1:?HOST}; PT=${2:?PORT}; shift 2
fi
U=${U:-${RUSER:-root}}
P=/home/catalin/work/phd
DATA=($P/v5b1_runs/baseline_v3/conf3/train ${DATA_EXTRA:-})
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
SSH=(ssh -p "$PT" -o StrictHostKeyChecking=accept-new -o ServerAliveInterval=60 "$U@$H")

ship() {
  # code/<sha> with COMMIT and MANIFEST; the manifest is built here from the same archive
  local ref=$1 sha full tmp
  sha=$(git -C "$REPO" rev-parse --short "$ref")
  full=$(git -C "$REPO" rev-parse "$ref")
  tmp=$(mktemp -d)
  git -C "$REPO" archive --format=tar "$ref" | tar -x -C "$tmp"
  (cd "$tmp" && find . -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum) > "$tmp.manifest"
  git -C "$REPO" archive --format=tar "$ref" | "${SSH[@]}" "mkdir -p $P/code/$sha && tar -x -C $P/code/$sha && echo $full > $P/code/$sha/COMMIT"
  "${SSH[@]}" "cat > $P/code/$sha/MANIFEST" < "$tmp.manifest"
  rm -rf "$tmp" "$tmp.manifest"
  echo "$sha"
}

deploy() {
  local ref=${REF:-HEAD} sha
  [ "$ref" != HEAD ] || [ -z "$(git -C "$REPO" status --porcelain)" ] || echo "note: uncommitted changes stay here; only HEAD is shipped" >&2
  echo "deploying $ref" >&2
  sha=$(ship "$ref")
  "${SSH[@]}" "ln -sfn $P/code/$sha $P/code/current"
  # Run data outside the repo that the checks and the incumbent read, mirrored at the laptop's paths.
  tar -C / -cf - "${DATA[@]#/}" | "${SSH[@]}" "tar -x -C /"
  "${SSH[@]}" "bash $P/code/$sha/toolchain/remote/bootstrap.sh $P/code/$sha"
}

run_job() {
  local name=${1:?NAME}; shift
  [ $# -gt 0 ] || { echo "no CMD given for job $name" >&2; exit 1; }
  # cd -P pins the job to the snapshot it started from, so a later deploy does not change its code.
  printf '%s\n' "cd -P $P/code/${CODE:-current}" ". $P/phd_speed_harmo_v5b1_toolchain/env.sh" 'export PYTHONPATH=$PWD' "$*" |
    "${SSH[@]}" "cat > $P/v5b1_runs/jobs/$name.sh && tmux new -d -s $name 'bash $P/v5b1_runs/jobs/$name.sh > $P/v5b1_runs/jobs/$name.log 2>&1'"
  echo "started $name on $H; log at $P/v5b1_runs/jobs/$name.log"
}

case $cmd in
  up) deploy; run_job "$@" ;;
  deploy) deploy ;;
  code) ship "${1:?REF}" ;;
  run) run_job "$@" ;;
  status)
    "${SSH[@]}" "uptime; free -g | head -2; tmux ls 2>/dev/null || echo 'no jobs running'; for f in $P/v5b1_runs/jobs/*.log; do [ -e \"\$f\" ] && { echo \"== \$f\"; tail -n 2 \"\$f\"; }; done"
    ;;
  fetch)
    run=${1:?RUN}
    rsync -az -e "ssh -p $PT" "$U@$H:$P/v5b1_runs/$run/" "$P/v5b1_runs/${run}_remote/"
    echo "copied to $P/v5b1_runs/${run}_remote"
    ;;
  *) echo "unknown command $cmd" >&2; exit 1 ;;
esac
