#!/bin/bash
# Custo Installation Script

set -e

echo "========================================="
echo "  Custo - Autonomous Operator Installer"
echo "========================================="
echo ""

# Check Python version
echo "[1/6] Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is required. Please install Python 3.9+ and try again."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "Found Python $PYTHON_VERSION"

# Create virtual environment
echo "[2/6] Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "[3/6] Installing dependencies..."
pip install --upgrade pip
pip install -r setup/dependencies.txt

# Initialize configuration
echo "[4/6] Initializing configuration..."
python3 setup/init_config.py

# Setup directories with proper permissions
echo "[5/6] Setting up directories..."
python3 setup/bootstrap.py

# Run first-time setup
echo "[6/6] Running first-time setup..."
python3 setup/first_run.py

echo ""
echo "========================================="
echo "  Installation Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "  1. Edit system/config.yaml with your settings"
echo "  2. Review user/profile.md and set your preferences"
echo "  3. Start the daemon: python daemon/daemon.py --foreground"
echo ""
