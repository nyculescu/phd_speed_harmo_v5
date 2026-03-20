#!/bin/bash
# =============================================================================
# Remote Deployment Script for phd_speed_harmo_v5
# =============================================================================
# Run this on a fresh Ubuntu 22.04+ machine to set up everything needed
# to execute launch_training.sh.
#
# Usage:
#   bash deploy_remote.sh
#
# Prerequisites: sudo access (or root), internet connection.
# =============================================================================
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC_COL='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC_COL} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC_COL} $*"; }
error() { echo -e "${RED}[ERROR]${NC_COL} $*"; exit 1; }

# ── Configuration ────────────────────────────────────────────────────────────
REPO_URL="git@github.com:nyculescu/phd_speed_harmo_v5.git"
BRANCH="main"
INSTALL_DIR="${INSTALL_DIR:-/workspace/phd_speed_harmo_v5}"
PYTHON_VERSION="3.12"

# ── Step 1: System packages ──────────────────────────────────────────────────
info "Updating system packages..."
sudo apt-get update -qq 2>/dev/null || apt-get update -qq

info "Installing base system dependencies..."
sudo apt-get install -y -qq \
    software-properties-common \
    build-essential \
    git \
    curl \
    wget \
    python3-pip \
    python3-venv \
    libxml2-dev \
    libxslt1-dev \
    tmux \
    2>/dev/null || apt-get install -y -qq \
    software-properties-common build-essential git curl wget \
    python3-pip python3-venv libxml2-dev libxslt1-dev tmux 2>/dev/null

# Check Python
if command -v python${PYTHON_VERSION} &>/dev/null; then
    PY_CMD="python${PYTHON_VERSION}"
elif command -v python3 &>/dev/null; then
    PY_CMD="python3"
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    warn "python${PYTHON_VERSION} not found, using python3 ($(python3 --version))"
else
    error "No Python 3 found. Install Python 3.10+ manually."
fi

info "Python: $($PY_CMD --version)"

# ── Step 2: Install SUMO ────────────────────────────────────────────────────
if ! command -v sumo &>/dev/null; then
    info "Installing SUMO..."
    sudo add-apt-repository -y ppa:sumo/stable 2>/dev/null || add-apt-repository -y ppa:sumo/stable
    sudo apt-get update -qq 2>/dev/null || apt-get update -qq
    sudo apt-get install -y -qq sumo sumo-tools 2>/dev/null || apt-get install -y -qq sumo sumo-tools
else
    info "SUMO already installed: $(sumo --version 2>/dev/null | head -1)"
fi

# Set SUMO_HOME
SUMO_HOME_PATH="/usr/share/sumo"
if [ ! -d "$SUMO_HOME_PATH" ]; then
    SUMO_HOME_PATH=$(dirname "$(dirname "$(which sumo)")")/share/sumo 2>/dev/null || true
fi

if [ ! -d "$SUMO_HOME_PATH" ]; then
    error "Could not find SUMO_HOME directory. Check SUMO installation."
fi

# Add SUMO_HOME to bashrc
if ! grep -q "SUMO_HOME" ~/.bashrc 2>/dev/null; then
    info "Adding SUMO_HOME to ~/.bashrc..."
    cat >> ~/.bashrc << EOF

# SUMO environment
export SUMO_HOME="$SUMO_HOME_PATH"
export PATH="\$SUMO_HOME/bin:\$PATH"
EOF
fi

export SUMO_HOME="$SUMO_HOME_PATH"
export PATH="$SUMO_HOME/bin:$PATH"

info "SUMO_HOME=$SUMO_HOME"
info "SUMO version: $(sumo --version 2>/dev/null | head -1)"

# ── Step 3: Clone the repository ─────────────────────────────────────────────
if [ -d "$INSTALL_DIR/.git" ]; then
    info "Repository already exists at $INSTALL_DIR. Pulling latest..."
    cd "$INSTALL_DIR"
    git fetch origin
    git checkout "$BRANCH"
    git pull origin "$BRANCH"
else
    info "Cloning repository..."
    git clone -b "$BRANCH" "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# ── Step 4: Create virtual environment ────────────────────────────────────────
if [ ! -d ".venv" ]; then
    info "Creating Python virtual environment..."
    $PY_CMD -m venv .venv
else
    info "Virtual environment already exists."
fi

source .venv/bin/activate

# ── Step 5: Install Python dependencies ───────────────────────────────────────
info "Upgrading pip..."
pip install --upgrade pip setuptools wheel -q

info "Installing Python requirements..."
pip install -r requirements.txt -q

# ── Step 6: Run smoke test ────────────────────────────────────────────────────
info "Running smoke test..."
echo ""
$PY_CMD tests/test_smoke_training.py
SMOKE_EXIT=$?

if [ $SMOKE_EXIT -ne 0 ]; then
    error "Smoke test failed! Fix the issues above before training."
fi

# ── Step 7: Verify installation ───────────────────────────────────────────────
echo ""
echo "=========================================="
echo " Deployment Verification"
echo "=========================================="

PY_VER=$(python --version 2>&1)
echo "  Python:     $PY_VER"

SUMO_VER=$(sumo --version 2>/dev/null | head -1 || echo "NOT FOUND")
echo "  SUMO:       $SUMO_VER"
echo "  SUMO_HOME:  $SUMO_HOME"

for pkg in stable_baselines3 sb3_contrib gymnasium torch traci; do
    VER=$(python -c "import $pkg; print($pkg.__version__)" 2>/dev/null || echo "MISSING")
    printf "  %-20s %s\n" "$pkg:" "$VER"
done

CORES=$(nproc)
RAM_GB=$(awk '/MemTotal/ {printf "%.0f", $2/1024/1024}' /proc/meminfo)
echo ""
echo "  CPU cores:  $CORES"
echo "  RAM:        ${RAM_GB} GB"

# Recommend n_envs
if [ "$CORES" -ge 100 ]; then
    RECOMMENDED_ENVS=24
    MODE="remote"
elif [ "$CORES" -ge 20 ]; then
    RECOMMENDED_ENVS=5
    MODE="local"
else
    RECOMMENDED_ENVS=2
    MODE="local"
fi
echo "  Recommended --n-envs: $RECOMMENDED_ENVS (mode: $MODE)"

echo "=========================================="
echo ""

deactivate

# ── Step 8: Final instructions ────────────────────────────────────────────────
info "Deployment complete!"
echo ""
echo "To run the full training suite:"
echo ""
echo "  cd $INSTALL_DIR"
echo "  source .venv/bin/activate"
echo "  export SUMO_HOME=\"$SUMO_HOME_PATH\""
echo ""
echo "  # Quick test (2 min):"
echo "  bash launch_training.sh test"
echo ""
echo "  # Full training (~9h on 128-core, ~42h on 30-core):"
echo "  nohup bash launch_training.sh $MODE > training.log 2>&1 &"
echo "  tail -f training.log"
echo ""
echo "  # TensorBoard monitoring:"
echo "  tensorboard --logdir training_runs/ --bind_all --port 6006"
echo ""
echo "Run inside tmux so it survives SSH disconnects:"
echo "  tmux new -s v5train"
echo "  bash launch_training.sh $MODE"
echo "  # Ctrl+B, D to detach; tmux attach -t v5train to reattach"
echo ""
