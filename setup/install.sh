#!/bin/bash
# Custo - One-line install:  curl -fsSL https://custo.ai/install.sh | sh
set -euo pipefail

REPO="relharrati/custo"
BRANCH="master"
INSTALL_DIR="${CUSTO_DIR:-$HOME/.custo}"

BOLD='\033[1m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo ""
echo "  ╔═══════════════════════════════════════╗"
echo "  ║     Custo - Autonomous Operator       ║"
echo "  ║        One-Line Installer             ║"
echo "  ╚═══════════════════════════════════════╝"
echo ""

# ── Check Python ───────────────────────────────────────────────
step() { echo -e "${CYAN}▸${NC} $1"; }
fail() { echo -e "  ${BOLD}✗${NC} $1"; exit 1; }
ok()   { echo -e "  ${GREEN}✓${NC} $1"; }

step "Checking Python..."
PYTHON=""
for cmd in python3 python py python3.*; do
  if command -v "$cmd" &>/dev/null; then
    VER=$("$cmd" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || true)
    MAJOR="${VER%%.*}"
    if [ "$MAJOR" -ge 3 ] 2>/dev/null; then
      PYTHON="$cmd"
      break
    fi
  fi
done

if [ -z "$PYTHON" ]; then
  fail "Python 3 not found. Install Python 3.9+ from https://python.org"
fi
ok "Found $PYTHON ($($PYTHON --version 2>&1 | head -1))"

# ── Clone / Download ──────────────────────────────────────────
step "Downloading Custo..."
if [ -d "$INSTALL_DIR" ]; then
  echo "  Updating existing installation at $INSTALL_DIR"
  git -C "$INSTALL_DIR" pull --ff-only 2>/dev/null || true
else
  git clone --depth 1 "https://github.com/$REPO.git" "$INSTALL_DIR"
  ok "Cloned to $INSTALL_DIR"
fi
cd "$INSTALL_DIR"

# ── Install Python deps ────────────────────────────────────────
step "Installing Python dependencies..."
if command -v pip3 &>/dev/null; then
  pip3 install pyyaml 2>&1 | tail -1
elif "$PYTHON" -m pip install pyyaml 2>&1 | tail -1; then
  true
else
  "$PYTHON" -m ensurepip --upgrade 2>/dev/null || true
  "$PYTHON" -m pip install pyyaml 2>&1 | tail -1
fi
ok "Dependencies installed"

# ── Setup ─────────────────────────────────────────────────────
step "Running first-time setup..."
"$PYTHON" setup/init_config.py 2>/dev/null || true
"$PYTHON" setup/first_run.py 2>/dev/null || true
ok "Setup complete"

# ── PATH setup ────────────────────────────────────────────────
INSTALL_SCRIPT="$INSTALL_DIR/custo"
if [ -f "$INSTALL_SCRIPT" ]; then
  chmod +x "$INSTALL_SCRIPT"
fi
if [ ! -f "/usr/local/bin/custo" ] && [ ! -f "$HOME/.local/bin/custo" ]; then
  mkdir -p "$HOME/.local/bin"
  if [ ! -f "$HOME/.local/bin/custo" ]; then
    ln -sf "$INSTALL_SCRIPT" "$HOME/.local/bin/custo" 2>/dev/null || true
    echo ""
    echo -e "  Add to your shell profile:  ${CYAN}export PATH=\"\$HOME/.local/bin:\$PATH\"${NC}"
  fi
fi

echo ""
echo -e "  ${GREEN}${BOLD}Custo installed successfully!${NC}"
echo ""
echo "  Run:  custo setup    — Configure LLM provider"
echo "  Run:  custo chat     — Start chatting"
echo "  Run:  custo doctor   — Health check"
echo ""
