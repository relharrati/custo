#!/bin/bash
# Custo Installer for macOS and Linux
# Usage: curl -fsSL --proto '=https' --tlsv1.2 https://github.com/relharrati/custo/raw/master/setup/install.sh | bash

set -euo pipefail

# ── Color Palette (Emerald/Blue) ──────────────────────────────
BOLD='\033[1m'
ACCENT='\033[38;2;16;185;129m'       # emerald-500   #10b981
ACCENT_BRIGHT='\033[38;2;52;211;153m' # emerald-400   #34d399
INFO='\033[38;2;100;116;139m'        # slate-500     #64748b
SUCCESS='\033[38;2;6;182;212m'       # cyan-500      #06b6d4
WARN='\033[38;2;251;191;36m'         # amber-400     #fbbf24
ERROR='\033[38;2;239;68;68m'         # red-500       #ef4444
MUTED='\033[38;2;71;85;105m'         # slate-600     #475569
BLUE='\033[38;2;59;130;246m'         # blue-500      #3b82f6
NC='\033[0m' # No Color

# ── Config ────────────────────────────────────────────────────
REPO="relharrati/custo"
BRANCH="master"
INSTALL_DIR="${CUSTO_DIR:-$HOME/.custo}"
PYTHON_MIN_MAJOR=3
PYTHON_MIN_MINOR=9
TAGLINE="Autonomous operator. Self-hosted AI. Zero friction."
TMPFILES=()

# ── Cleanup ───────────────────────────────────────────────────
cleanup_tmpfiles() {
    local f
    for f in "${TMPFILES[@]:-}"; do
        rm -rf "$f" 2>/dev/null || true
    done
}
trap cleanup_tmpfiles EXIT

mktempfile() {
    local f
    f="$(mktemp)"
    TMPFILES+=("$f")
    echo "$f"
}

# ── TTY & Interactivity Detection ─────────────────────────────
is_non_interactive_shell() {
    if [[ "${NO_PROMPT:-0}" == "1" ]]; then
        return 0
    fi
    if [[ ! -t 0 || ! -t 1 ]]; then
        return 0
    fi
    return 1
}

is_tty() {
    if [[ -n "${NO_COLOR:-}" ]]; then
        return 1
    fi
    if [[ "${TERM:-dumb}" == "dumb" ]]; then
        return 1
    fi
    if [[ -t 2 || -t 1 ]]; then
        return 0
    fi
    if [[ -r /dev/tty && -w /dev/tty ]]; then
        return 0
    fi
    return 1
}

# ── UI Helpers ────────────────────────────────────────────────
ui_info() {
    local msg="$*"
    echo -e "${MUTED}·${NC} ${msg}"
}

ui_warn() {
    local msg="$*"
    echo -e "${WARN}!${NC} ${msg}"
}

ui_success() {
    local msg="$*"
    echo -e "${SUCCESS}✓${NC} ${msg}"
}

ui_error() {
    local msg="$*"
    echo -e "${ERROR}✗${NC} ${msg}"
}

ui_section() {
    local title="$1"
    echo ""
    echo -e "${ACCENT}${BOLD}${title}${NC}"
}

ui_stage() {
    local title="$1"
    ui_section "▸ ${title}"
}

ui_kv() {
    local key="$1"
    local value="$2"
    echo -e "${MUTED}${key}:${NC} ${value}"
}

# ── Spinner ───────────────────────────────────────────────────
run_with_spinner() {
    local title="$1"
    shift
    
    if is_tty; then
        local frames=("⠋" "⠙" "⠹" "⠸" "⠼" "⠴" "⠦" "⠧" "⠇" "⠏")
        local i=0
        local pid
        
        # Run command in background
        "$@" &
        pid=$!
        
        # Show spinner while running
        while kill -0 $pid 2>/dev/null; do
            printf "\r  ${MUTED}%s %s${NC}" "${frames[i]}" "$title"
            i=$(( (i + 1) % ${#frames[@]} ))
            sleep 0.1
        done
        
        # Wait for command to finish
        wait $pid
        local status=$?
        printf "\r  \033[K"  # Clear line
        
        if [[ $status -eq 0 ]]; then
            ui_success "$title"
        else
            ui_error "$title failed"
        fi
        
        return $status
    else
        # Non-TTY: just run the command
        ui_info "$title"
        "$@"
        return $?
    fi
}

# ── Downloader Detection ──────────────────────────────────────
DOWNLOADER=""
detect_downloader() {
    if command -v curl &> /dev/null; then
        DOWNLOADER="curl"
        return 0
    fi
    if command -v wget &> /dev/null; then
        DOWNLOADER="wget"
        return 0
    fi
    ui_error "Missing downloader (curl or wget required)"
    exit 1
}

download_file() {
    local url="$1"
    local output="$2"
    if [[ -z "$DOWNLOADER" ]]; then
        detect_downloader
    fi
    if [[ "$DOWNLOADER" == "curl" ]]; then
        curl -fsSL --proto '=https' --tlsv1.2 --retry 3 --retry-delay 1 --retry-connrefused -o "$output" "$url"
        return
    fi
    wget -q --https-only --secure-protocol=TLSv1_2 --tries=3 --timeout=20 -O "$output" "$url"
}

# ── OS Detection ──────────────────────────────────────────────
detect_os_or_die() {
    OS="unknown"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]] || [[ -n "${WSL_DISTRO_NAME:-}" ]]; then
        OS="linux"
    fi

    if [[ "$OS" == "unknown" ]]; then
        ui_error "Unsupported operating system"
        echo "This installer supports macOS and Linux (including WSL)."
        echo "For Windows, use: iwr -useb https://github.com/relharrati/custo/raw/master/setup/install.ps1 | iex"
        exit 1
    fi

    ui_success "Detected: $OS"
}

# ── Python Detection ──────────────────────────────────────────
parse_python_version_components() {
    local python_bin="${1:-python3}"
    if ! command -v "$python_bin" &> /dev/null; then
        return 1
    fi
    local version major minor
    version="$("$python_bin" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || true)"
    major="${version%%.*}"
    minor="${version#*.}"
    minor="${minor%%.*}"

    if [[ ! "$major" =~ ^[0-9]+$ ]]; then
        return 1
    fi
    if [[ ! "$minor" =~ ^[0-9]+$ ]]; then
        return 1
    fi
    echo "${major} ${minor}"
    return 0
}

python_is_at_least_required() {
    local version_components major minor
    version_components="$(parse_python_version_components "$1" || true)"
    read -r major minor <<< "$version_components"
    if [[ ! "$major" =~ ^[0-9]+$ || ! "$minor" =~ ^[0-9]+$ ]]; then
        return 1
    fi
    if [[ "$major" -gt "$PYTHON_MIN_MAJOR" ]]; then
        return 0
    fi
    if [[ "$major" -eq "$PYTHON_MIN_MAJOR" && "$minor" -ge "$PYTHON_MIN_MINOR" ]]; then
        return 0
    fi
    return 1
}

find_python() {
    local candidates=()
    local candidate
    
    # Try common Python commands
    for candidate in python3 python python3.13 python3.12 python3.11 python3.10 python3.9 py; do
        if command -v "$candidate" &> /dev/null; then
            candidates+=("$candidate")
        fi
    done
    
    # Try specific paths
    candidates+=(
        "/usr/bin/python3"
        "/usr/local/bin/python3"
        "/opt/homebrew/bin/python3"
    )
    
    for candidate in "${candidates[@]}"; do
        if [[ -z "$candidate" || ! -x "$candidate" ]]; then
            continue
        fi
        if python_is_at_least_required "$candidate"; then
            echo "$candidate"
            return 0
        fi
    done
    
    return 1
}

check_python() {
    local python_bin=""
    python_bin="$(find_python || true)"
    
    if [[ -n "$python_bin" ]]; then
        local version
        version="$("$python_bin" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")' 2>/dev/null || true)"
        ui_success "Python $version found ($python_bin)"
        echo "$python_bin"
        return 0
    else
        ui_info "Python ${PYTHON_MIN_MAJOR}.${PYTHON_MIN_MINOR}+ not found"
        return 1
    fi
}

install_python_macos() {
    ui_info "Installing Python via Homebrew"
    if ! run_with_spinner "Installing Python" brew install python3; then
        ui_error "Python installation failed"
        echo "Run: brew install python3"
        exit 1
    fi
    ui_success "Python installed"
}

install_python_linux() {
    require_sudo
    
    if command -v apt-get &> /dev/null; then
        run_with_spinner "Updating package index" sudo apt-get update -qq
        run_with_spinner "Installing Python 3" sudo apt-get install -y -qq python3 python3-pip python3-venv
    elif command -v pacman &> /dev/null; then
        if is_root; then
            run_with_spinner "Installing Python 3" pacman -Sy --noconfirm python python-pip
        else
            run_with_spinner "Installing Python 3" sudo pacman -Sy --noconfirm python python-pip
        fi
    elif command -v dnf &> /dev/null; then
        if is_root; then
            run_with_spinner "Installing Python 3" dnf install -y -q python3 python3-pip
        else
            run_with_spinner "Installing Python 3" sudo dnf install -y -q python3 python3-pip
        fi
    else
        ui_error "Could not detect package manager for Python"
        echo "Install Python ${PYTHON_MIN_MAJOR}.${PYTHON_MIN_MINOR}+ from https://python.org"
        exit 1
    fi
    
    ui_success "Python installed"
}

# ── Sudo Handling ─────────────────────────────────────────────
is_root() {
    [[ "$(id -u)" -eq 0 ]]
}

require_sudo() {
    if [[ "$OS" != "linux" ]]; then
        return 0
    fi
    if is_root; then
        return 0
    fi
    if command -v sudo &> /dev/null; then
        if ! sudo -n true >/dev/null 2>&1; then
            ui_info "Administrator privileges required; enter your password"
            sudo -v
        fi
        return 0
    fi
    ui_error "sudo is required for system installs on Linux"
    exit 1
}

# ── Git Detection ─────────────────────────────────────────────
check_git() {
    if command -v git &> /dev/null; then
        ui_success "Git already installed"
        return 0
    fi
    ui_info "Git not found, installing it now"
    return 1
}

install_git() {
    if [[ "$OS" == "macos" ]]; then
        run_with_spinner "Installing Git" brew install git
    elif [[ "$OS" == "linux" ]]; then
        require_sudo
        if command -v apt-get &> /dev/null; then
            run_with_spinner "Installing Git" sudo apt-get install -y -qq git
        elif command -v pacman &> /dev/null; then
            if is_root; then
                run_with_spinner "Installing Git" pacman -Sy --noconfirm git
            else
                run_with_spinner "Installing Git" sudo pacman -Sy --noconfirm git
            fi
        elif command -v dnf &> /dev/null; then
            if is_root; then
                run_with_spinner "Installing Git" dnf install -y -q git
            else
                run_with_spinner "Installing Git" sudo dnf install -y -q git
            fi
        else
            ui_error "Could not detect package manager for Git"
            exit 1
        fi
    fi
    ui_success "Git installed"
}

# ── Homebrew (macOS) ──────────────────────────────────────────
install_homebrew() {
    if [[ "$OS" == "macos" ]]; then
        if ! command -v brew &> /dev/null; then
            ui_info "Homebrew not found, installing"
            run_with_spinner "Installing Homebrew" /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            
            # Add Homebrew to PATH for this session
            if [[ -f "/opt/homebrew/bin/brew" ]]; then
                eval "$(/opt/homebrew/bin/brew shellenv)"
            elif [[ -f "/usr/local/bin/brew" ]]; then
                eval "$(/usr/local/bin/brew shellenv)"
            fi
            ui_success "Homebrew installed"
        else
            ui_success "Homebrew already installed"
        fi
    fi
}

# ── pip Installation ──────────────────────────────────────────
install_pip() {
    local python_bin="$1"
    
    if "$python_bin" -m pip --version &> /dev/null; then
        ui_success "pip already available"
        return 0
    fi
    
    ui_info "pip not found, installing it"
    if run_with_spinner "Installing pip" "$python_bin" -m ensurepip --upgrade 2>/dev/null; then
        ui_success "pip installed"
        return 0
    fi
    
    # Fallback: get-pip.py
    ui_info "ensurepip failed, trying get-pip.py"
    local tmp
    tmp="$(mktempfile)"
    if download_file "https://bootstrap.pypa.io/get-pip.py" "$tmp"; then
        if run_with_spinner "Installing pip via get-pip.py" "$python_bin" "$tmp"; then
            ui_success "pip installed"
            return 0
        fi
    fi
    
    ui_error "Could not install pip"
    exit 1
}

# ── Dependency Installation ───────────────────────────────────
install_dependencies() {
    local python_bin="$1"
    local packages=("pyyaml" "rich" "InquirerPy")
    
    ui_info "Installing Python dependencies"
    
    for pkg in "${packages[@]}"; do
        if run_with_spinner "Installing $pkg" "$python_bin" -m pip install --quiet --user "$pkg"; then
            ui_success "$pkg installed"
        else
            ui_warn "Failed to install $pkg"
        fi
    done
}

# ── Clone/Update Repository ───────────────────────────────────
clone_or_update_repo() {
    if [[ -d "$INSTALL_DIR/.git" ]]; then
        ui_info "Updating existing installation at $INSTALL_DIR"
        if run_with_spinner "Pulling latest changes" git -C "$INSTALL_DIR" pull --ff-only 2>/dev/null; then
            ui_success "Repository updated"
        else
            ui_warn "Pull failed, continuing anyway"
        fi
    else
        ui_info "Cloning Custo repository"
        if run_with_spinner "Cloning repository" git clone --depth 1 "https://github.com/$REPO.git" "$INSTALL_DIR"; then
            ui_success "Cloned to $INSTALL_DIR"
        else
            ui_error "Clone failed"
            exit 1
        fi
    fi
}

# ── Shell Integration ─────────────────────────────────────────
add_to_path() {
    local bin_dir="$1"
    if [[ ! -d "$bin_dir" ]]; then
        return 1
    fi
    
    # Add to current session PATH
    if [[ ":${PATH:-}:" != *":${bin_dir}:"* ]]; then
        export PATH="${bin_dir}:${PATH}"
    fi
    
    # Add to shell profile
    local path_line="export PATH=\"${bin_dir}:\$PATH\""
    local wrote_rc=0
    for rc in "$HOME/.bashrc" "$HOME/.zshrc"; do
        if [[ -f "$rc" ]]; then
            if ! grep -q "custo" "$rc" 2>/dev/null; then
                echo "$path_line" >> "$rc"
                wrote_rc=1
            fi
        fi
    done
    
    if [[ "$wrote_rc" -eq 1 ]]; then
        ui_success "Added to shell profile"
    fi
}

create_alias() {
    local python_bin="$1"
    local alias_line="alias custo='$python_bin \"$INSTALL_DIR/custo\"'"
    
    # Create alias for current session
    eval "$alias_line"
    
    # Add to shell profile
    local wrote_rc=0
    for rc in "$HOME/.bashrc" "$HOME/.zshrc"; do
        if [[ -f "$rc" ]]; then
            if ! grep -q "custo" "$rc" 2>/dev/null; then
                echo "$alias_line" >> "$rc"
                wrote_rc=1
            fi
        fi
    done
    
    if [[ "$wrote_rc" -eq 1 ]]; then
        ui_success "Added alias to shell profile"
    fi
}

# ── Post-Install Verification ─────────────────────────────────
verify_installation() {
    local python_bin="$1"
    
    ui_info "Verifying installation"
    
    # Check if custo script exists
    if [[ ! -f "$INSTALL_DIR/custo" ]]; then
        ui_error "custo script not found"
        return 1
    fi
    
    # Check if setup directory exists
    if [[ ! -d "$INSTALL_DIR/setup" ]]; then
        ui_error "setup directory not found"
        return 1
    fi
    
    # Try importing key modules
    if run_with_spinner "Checking Python modules" "$python_bin" -c "
import sys
sys.path.insert(0, '$INSTALL_DIR')
try:
    import yaml
    print('  PyYAML: OK')
except ImportError:
    print('  PyYAML: MISSING')
    sys.exit(1)
try:
    from rich.console import Console
    print('  Rich: OK')
except ImportError:
    print('  Rich: MISSING')
    sys.exit(1)
try:
    from InquirerPy import inquirer
    print('  InquirerPy: OK')
except ImportError:
    print('  InquirerPy: MISSING')
    sys.exit(1)
print('  All modules verified')
"; then
        ui_success "Installation verified"
        return 0
    else
        ui_warn "Some modules missing; run 'custo install' to fix"
        return 1
    fi
}

# ── Interactive Setup Launch ──────────────────────────────────
launch_interactive_setup() {
    local python_bin="$1"
    
    if is_non_interactive_shell; then
        ui_info "Skipping interactive setup (non-interactive shell)"
        ui_info "Run 'custo setup' later to configure"
        return 0
    fi
    
    if ! is_tty; then
        ui_info "Skipping interactive setup (no TTY)"
        ui_info "Run 'custo setup' later to configure"
        return 0
    fi
    
    ui_info "Launching interactive setup wizard"
    echo ""
    
    # Run the TUI setup wizard
    cd "$INSTALL_DIR"
    "$python_bin" setup/tui_setup.py
}

# ── Banner ────────────────────────────────────────────────────
print_banner() {
    echo ""
    echo -e "${ACCENT}${BOLD}"
    echo "  ╔═══════════════════════════════════════════╗"
    echo "  ║         🔮  Custo Installer  🔮          ║"
    echo "  ║   Autonomous Operator • Self-Hosted AI   ║"
    echo "  ╚═══════════════════════════════════════════╝"
    echo -e "${NC}${INFO}  ${TAGLINE}${NC}"
    echo ""
}

print_completion() {
    local is_upgrade="$1"
    
    echo ""
    if [[ "$is_upgrade" == "true" ]]; then
        echo -e "${SUCCESS}${BOLD}🔮 Custo updated successfully!${NC}"
        echo -e "${MUTED}Fresh code, same autonomous energy.${NC}"
    else
        echo -e "${SUCCESS}${BOLD}🔮 Custo installed successfully!${NC}"
        echo -e "${MUTED}Your terminal just got smarter.${NC}"
    fi
    echo ""
    echo -e "${BOLD}Next steps:${NC}"
    echo -e "  ${ACCENT}custo setup${NC}    — Configure LLM provider (interactive)"
    echo -e "  ${ACCENT}custo chat${NC}     — Start chatting"
    echo -e "  ${ACCENT}custo doctor${NC}   — Health check"
    echo -e "  ${ACCENT}custo help${NC}     — All commands"
    echo ""
    echo -e "${MUTED}Docs: https://github.com/$REPO${NC}"
    echo ""
}

# ── Main Installation Flow ────────────────────────────────────
main() {
    print_banner
    
    # Detect OS
    detect_os_or_die
    
    # Check for existing installation
    local is_upgrade=false
    if [[ -d "$INSTALL_DIR/.git" ]]; then
        is_upgrade=true
        ui_info "Existing installation detected, upgrading"
    fi
    
    # Stage 1: Environment
    ui_stage "Preparing environment"
    
    # Homebrew (macOS)
    install_homebrew
    
    # Python
    local python_bin=""
    if python_bin="$(check_python)"; then
        : # Python found
    else
        ui_info "Installing Python"
        if [[ "$OS" == "macos" ]]; then
            install_python_macos
        elif [[ "$OS" == "linux" ]]; then
            install_python_linux
        fi
        
        # Re-check Python
        if ! python_bin="$(check_python)"; then
            ui_error "Python installation failed"
            exit 1
        fi
    fi
    
    # pip
    install_pip "$python_bin"
    
    # Git
    if ! check_git; then
        install_git
    fi
    
    # Stage 2: Installation
    ui_stage "Installing Custo"
    
    # Clone or update repository
    clone_or_update_repo
    
    # Change to install directory
    cd "$INSTALL_DIR"
    
    # Install Python dependencies
    install_dependencies "$python_bin"
    
    # Stage 3: Verification
    ui_stage "Verifying installation"
    
    # Verify installation
    verify_installation "$python_bin"
    
    # Stage 4: Shell Integration
    ui_stage "Configuring shell"
    
    # Add to PATH and create alias
    create_alias "$python_bin"
    
    # Stage 5: Interactive Setup
    ui_stage "Setup"
    
    # Launch interactive setup if TTY available
    launch_interactive_setup "$python_bin"
    
    # Print completion message
    print_completion "$is_upgrade"
}

# ── Entry Point ───────────────────────────────────────────────
if [[ "${CUSTO_INSTALL_SH_NO_RUN:-0}" != "1" ]]; then
    main "$@"
fi