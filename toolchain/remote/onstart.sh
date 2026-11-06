#!/bin/bash
# vast.ai template on-start script: builds the toolchain in the background while the machine boots, so a deploy only ships code and runs the checks.
# Paste the whole file into the template's On-start Script field. The pins are a copy of toolchain/requirements_lock.txt; bootstrap.sh re-applies the shipped lock anyway.
P=/home/catalin/work/phd
T=$P/phd_speed_harmo_v5b1_toolchain
build() {
  export DEBIAN_FRONTEND=noninteractive PATH=$HOME/.local/bin:$PATH
  apt-get update -qq && apt-get install -y -qq --no-install-recommends ca-certificates curl tmux rsync procps
  command -v uv || curl -LsSf https://astral.sh/uv/install.sh | sh
  uv python install 3.14.4
  [ -x $T/venv/bin/python ] || "$(uv python find 3.14.4)" -m venv $T/venv
  cat > $T/lock.txt <<'EOF'
absl-py==2.5.1
cloudpickle==3.1.2
cma==4.5.0
contourpy==1.4.0
cycler==0.12.1
eclipse-sumo==1.27.1
Farama-Notifications==0.0.6
filelock==4.0.7
fonttools==4.66.1
fsspec==2026.9.0
grpcio==1.85.1
gymnasium==1.2.3
iniconfig==2.3.0
Jinja2==3.1.6
kiwisolver==1.5.1
libsumo==1.27.1
Markdown==3.11.3
MarkupSafe==3.0.3
matplotlib==3.11.2
mpmath==1.3.0
networkx==3.7
numpy==2.5.3
packaging==26.3
pandas==3.0.6
pettingzoo==1.27.0
pillow==12.3.0
pluggy==1.6.0
protobuf==7.36.2
Pygments==2.21.0
pyparsing==3.3.3
pytest==9.1.1
python-dateutil==2.9.0.post0
sb3_contrib==2.8.0
scipy==1.18.1
setuptools==81.0.0
six==1.17.0
stable_baselines3==2.8.0
sumo-data==1.27.1
sumolib==1.27.1
sympy==1.14.0
tensorboard==2.21.0
tensorboard-data-server==0.7.2
torch==2.11.0+cpu
traci==1.27.1
typing_extensions==4.16.0
Werkzeug==3.1.9
EOF
  $T/venv/bin/python -m pip install -q -r $T/lock.txt --extra-index-url https://download.pytorch.org/whl/cpu && touch $T/ready
}
if [ ! -e $T/ready ]; then
  mkdir -p $T $P/v5b1_runs/jobs
  (trap '' HUP; build > $P/onstart.log 2>&1; rm -f $P/.onstart_running) &
  echo $! > $P/.onstart_running
fi
# The base image's own start-up, as in the stock template.
entrypoint.sh
