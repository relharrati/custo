<#
.SYNOPSIS
    Custo - One-line install:  powershell -c "iex (iwr 'https://github.com/relharrati/custo/raw/master/setup/install.ps1')"
.DESCRIPTION
    Installs Custo on Windows: downloads repo, sets up Python, configures LLM.
    Enhanced with progress indicators, TTY detection, and emerald/blue theme.
#>

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# ── Color Palette (Emerald/Blue) ──────────────────────────────
$ACCENT = [System.ConsoleColor]::Green
$ACCENT_BRIGHT = [System.ConsoleColor]::Cyan
$INFO = [System.ConsoleColor]::DarkGray
$SUCCESS = [System.ConsoleColor]::Cyan
$WARN = [System.ConsoleColor]::Yellow
$ERROR_COLOR = [System.ConsoleColor]::Red
$MUTED = [System.ConsoleColor]::Gray
$BLUE = [System.ConsoleColor]::Blue

# ── Config ────────────────────────────────────────────────────
$Repo = "relharrati/custo"
$Branch = "master"
$InstallDir = if ($env:CUSTO_DIR) { $env:CUSTO_DIR } else { "$env:USERPROFILE\.custo" }
$PYTHON_MIN_MAJOR = 3
$PYTHON_MIN_MINOR = 9
$TAGLINE = "Autonomous operator. Self-hosted AI. Zero friction."

# ── UI Helpers ────────────────────────────────────────────────
function ui_info($msg) {
    Write-Host "· " -ForegroundColor $MUTED -NoNewline
    Write-Host $msg
}

function ui_warn($msg) {
    Write-Host "! " -ForegroundColor $WARN -NoNewline
    Write-Host $msg
}

function ui_success($msg) {
    Write-Host "✓ " -ForegroundColor $SUCCESS -NoNewline
    Write-Host $msg
}

function ui_error($msg) {
    Write-Host "✗ " -ForegroundColor $ERROR_COLOR -NoNewline
    Write-Host $msg
}

function ui_section($title) {
    Write-Host ""
    Write-Host "▸ $title" -ForegroundColor $ACCENT
}

function ui_stage($title) {
    ui_section $title
}

# ── TTY & Interactivity Detection ─────────────────────────────
function is_non_interactive_shell {
    if ($env:NO_PROMPT -eq "1") {
        return $true
    }
    # Check if stdin/stdout are redirected
    if (-not [System.Console]::IsInputRedirected -and -not [System.Console]::IsOutputRedirected) {
        return $false
    }
    return $true
}

function is_tty {
    if ($env:NO_COLOR) {
        return $false
    }
    if (-not [System.Console]::IsInputRedirected -and -not [System.Console]::IsOutputRedirected) {
        return $true
    }
    return $false
}

# ── Spinner ───────────────────────────────────────────────────
function run_with_spinner($title, $scriptBlock) {
    if (is_tty) {
        $frames = @("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏")
        $i = 0
        $running = $true
        
        # Run script in background job
        $job = Start-Job -ScriptBlock $scriptBlock
        
        # Show spinner while running
        while ($running) {
            $state = $job.State
            if ($state -eq "Completed" -or $state -eq "Failed" -or $state -eq "Stopped") {
                $running = $false
            } else {
                Write-Host "`r  $($frames[$i]) $title" -ForegroundColor $MUTED -NoNewline
                $i = ($i + 1) % $frames.Length
                Start-Sleep -Milliseconds 100
            }
        }
        
        # Clear line
        Write-Host "`r" -NoNewline
        Write-Host (" " * 80) -NoNewline
        Write-Host "`r" -NoNewline
        
        # Get result
        $result = Receive-Job -Job $job
        Remove-Job -Job $job
        
        if ($result -is [System.Management.Automation.ErrorRecord]) {
            ui_error "$title failed"
            Write-Host $result.Exception.Message -ForegroundColor $ERROR_COLOR
            return $false
        } else {
            ui_success $title
            return $true
        }
    } else {
        # Non-TTY: just run the script
        ui_info $title
        try {
            & $scriptBlock
            ui_success $title
            return $true
        } catch {
            ui_error "$title failed"
            return $false
        }
    }
}

# ── Python Detection ──────────────────────────────────────────
function find_python {
    $candidates = @(
        "python3", "python", "py",
        "$env:LOCALAPPDATA\Programs\Python\Python3*\python.exe",
        "$env:ProgramFiles\Python3*\python.exe",
        "$env:ProgramFiles(x86)\Python3*\python.exe"
    )
    
    foreach ($candidate in $candidates) {
        if ($candidate -match "\*") {
            # Handle wildcards
            $matches = Get-ChildItem -Path $candidate -ErrorAction SilentlyContinue
            foreach ($match in $matches) {
                $pythonPath = Join-Path $match.FullName "python.exe"
                if (Test-Path $pythonPath) {
                    try {
                        $version = & $pythonPath -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
                        $major = $version.Split('.')[0] -as [int]
                        $minor = $version.Split('.')[1] -as [int]
                        if ($major -ge $PYTHON_MIN_MAJOR -and ($major -gt $PYTHON_MIN_MAJOR -or $minor -ge $PYTHON_MIN_MINOR)) {
                            return $pythonPath
                        }
                    } catch {}
                }
            }
        } else {
            try {
                $version = & $candidate -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
                if ($version) {
                    $major = $version.Split('.')[0] -as [int]
                    $minor = $version.Split('.')[1] -as [int]
                    if ($major -ge $PYTHON_MIN_MAJOR -and ($major -gt $PYTHON_MIN_MAJOR -or $minor -ge $PYTHON_MIN_MINOR)) {
                        return $candidate
                    }
                }
            } catch {}
        }
    }
    
    return $null
}

function check_python {
    $python = find_python
    if ($python) {
        try {
            $version = & $python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')" 2>$null
            ui_success "Python $version found ($python)"
        } catch {
            ui_success "Python found ($python)"
        }
        return $python
    } else {
        ui_info "Python ${PYTHON_MIN_MAJOR}.${PYTHON_MIN_MINOR}+ not found"
        return $null
    }
}

function install_python {
    ui_info "Downloading Python installer"
    $pythonUrl = "https://www.python.org/ftp/python/3.12.4/python-3.12.4-amd64.exe"
    $installerPath = "$env:TEMP\python-installer.exe"
    
    try {
        Invoke-WebRequest -Uri $pythonUrl -OutFile $installerPath -UseBasicParsing
        ui_info "Running Python installer (silent mode)"
        Start-Process -FilePath $installerPath -ArgumentList "/quiet", "InstallAllUsers=0", "PrependPath=1", "Include_pip=1" -Wait
        Remove-Item $installerPath -Force -ErrorAction SilentlyContinue
        ui_success "Python installed"
        return $true
    } catch {
        ui_error "Python installation failed"
        Write-Host "Install Python 3.9+ from https://python.org"
        return $false
    }
}

# ── pip Installation ──────────────────────────────────────────
function install_pip($python) {
    try {
        & $python -m pip --version 2>$null | Out-Null
        ui_success "pip already available"
        return $true
    } catch {}
    
    ui_info "pip not found, installing it"
    try {
        & $python -m ensurepip --upgrade 2>$null | Out-Null
        ui_success "pip installed"
        return $true
    } catch {
        ui_info "ensurepip failed, trying get-pip.py"
        $getPipUrl = "https://bootstrap.pypa.io/get-pip.py"
        $getPipPath = "$env:TEMP\get-pip.py"
        
        try {
            Invoke-WebRequest -Uri $getPipUrl -OutFile $getPipPath -UseBasicParsing
            & $python $getPipPath 2>$null | Out-Null
            Remove-Item $getPipPath -Force -ErrorAction SilentlyContinue
            ui_success "pip installed"
            return $true
        } catch {
            ui_error "Could not install pip"
            return $false
        }
    }
}

# ── Dependency Installation ───────────────────────────────────
function install_dependencies($python) {
    $packages = @("pyyaml", "rich", "InquirerPy")
    
    ui_info "Installing Python dependencies"
    
    foreach ($pkg in $packages) {
        try {
            & $python -m pip install --quiet --user $pkg 2>$null | Out-Null
            ui_success "$pkg installed"
        } catch {
            ui_warn "Failed to install $pkg"
        }
    }
}

# ── Git Detection ─────────────────────────────────────────────
function check_git {
    if (Get-Command git -ErrorAction SilentlyContinue) {
        ui_success "Git already installed"
        return $true
    }
    ui_info "Git not found, installing it now"
    return $false
}

function install_git {
    ui_info "Downloading Git installer"
    $gitUrl = "https://github.com/git-for-windows/git/releases/download/v2.45.1.windows.1/Git-2.45.1-64-bit.exe"
    $installerPath = "$env:TEMP\git-installer.exe"
    
    try {
        Invoke-WebRequest -Uri $gitUrl -OutFile $installerPath -UseBasicParsing
        ui_info "Running Git installer (silent mode)"
        Start-Process -FilePath $installerPath -ArgumentList "/VERYSILENT", "/NORESTART", "/NOCANCEL", "/SP-" -Wait
        Remove-Item $installerPath -Force -ErrorAction SilentlyContinue
        ui_success "Git installed"
        return $true
    } catch {
        ui_error "Git installation failed"
        Write-Host "Install Git from https://git-scm.com"
        return $false
    }
}

# ── Clone/Update Repository ───────────────────────────────────
function clone_or_update_repo {
    if (Test-Path "$InstallDir\.git") {
        ui_info "Updating existing installation at $InstallDir"
        Push-Location "$InstallDir"
        try {
            if (git pull --ff-only 2>$null) {
                ui_success "Repository updated"
            } else {
                ui_warn "Pull failed, continuing anyway"
            }
        } catch {
            ui_warn "Pull failed, continuing anyway"
        }
        Pop-Location
    } else {
        ui_info "Cloning Custo repository"
        try {
            git clone --depth 1 "https://github.com/$Repo.git" "$InstallDir" 2>$null
            if (Test-Path "$InstallDir") {
                ui_success "Cloned to $InstallDir"
            } else {
                ui_error "Clone failed"
                exit 1
            }
        } catch {
            ui_error "Clone failed"
            exit 1
        }
    }
}

# ── Shell Integration ─────────────────────────────────────────
function add_to_path {
    $pathDir = $InstallDir
    $userPath = [Environment]::GetEnvironmentVariable("PATH", "User")
    
    if ($userPath -notlike "*$pathDir*") {
        $newPath = "$pathDir;$userPath"
        [Environment]::SetEnvironmentVariable("PATH", $newPath, "User")
        ui_success "Added to user PATH"
    }
    
    # Add to current session
    $env:PATH = "$pathDir;$env:PATH"
}

function create_alias {
    $python = $args[0]
    $custoBat = Join-Path $InstallDir "custo.bat"
    
    if (Test-Path $custoBat) {
        # PowerShell profile script for persistent alias
        $profileScript = @"

# Custo CLI
Set-Alias custo "$custoBat"
"@
        # Write to user profile for future sessions
        $profileDir = Split-Path $PROFILE -Parent
        if (-not (Test-Path $profileDir)) { 
            New-Item -ItemType Directory -Path $profileDir -Force | Out-Null 
        }
        $existingProfile = if (Test-Path $PROFILE) { Get-Content $PROFILE -Raw -ErrorAction SilentlyContinue } else { "" }
        if ($existingProfile -notlike "*custo*") {
            Add-Content -Path $PROFILE -Value $profileScript -Encoding UTF8
            ui_success "Added to PowerShell profile"
        }
    }
}

# ── Post-Install Verification ─────────────────────────────────
function verify_installation($python) {
    ui_info "Verifying installation"
    
    # Check if custo script exists
    if (-not (Test-Path "$InstallDir\custo")) {
        ui_error "custo script not found"
        return $false
    }
    
    # Check if setup directory exists
    if (-not (Test-Path "$InstallDir\setup")) {
        ui_error "setup directory not found"
        return $false
    }
    
    # Try importing key modules
    try {
        $result = & $python -c @"
import sys
sys.path.insert(0, '$InstallDir')
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
"@ 2>$null
        
        if ($result -match "All modules verified") {
            ui_success "Installation verified"
            return $true
        } else {
            ui_warn "Some modules missing; run 'custo install' to fix"
            return $false
        }
    } catch {
        ui_warn "Verification failed; run 'custo install' to fix"
        return $false
    }
}

# ── Interactive Setup Launch ──────────────────────────────────
function launch_interactive_setup($python) {
    if (is_non_interactive_shell) {
        ui_info "Skipping interactive setup (non-interactive shell)"
        ui_info "Run 'custo setup' later to configure"
        return
    }
    
    if (-not (is_tty)) {
        ui_info "Skipping interactive setup (no TTY)"
        ui_info "Run 'custo setup' later to configure"
        return
    }
    
    ui_info "Launching interactive setup wizard"
    Write-Host ""
    
    # Run the TUI setup wizard
    Push-Location "$InstallDir"
    try {
        & $python setup/tui_setup.py
    } catch {
        ui_warn "Interactive setup failed; run 'custo setup' later"
    }
    Pop-Location
}

# ── Banner ────────────────────────────────────────────────────
function print_banner {
    Write-Host ""
    Write-Host "  ╔═══════════════════════════════════════════╗" -ForegroundColor $ACCENT
    Write-Host "  ║         🔮  Custo Installer  🔮          ║" -ForegroundColor $ACCENT
    Write-Host "  ║   Autonomous Operator • Self-Hosted AI   ║" -ForegroundColor $ACCENT
    Write-Host "  ╚═══════════════════════════════════════════╝" -ForegroundColor $ACCENT
    Write-Host "  $TAGLINE" -ForegroundColor $INFO
    Write-Host ""
}

function print_completion($is_upgrade) {
    Write-Host ""
    if ($is_upgrade) {
        Write-Host "🔮 Custo updated successfully!" -ForegroundColor $SUCCESS
        Write-Host "Fresh code, same autonomous energy." -ForegroundColor $MUTED
    } else {
        Write-Host "🔮 Custo installed successfully!" -ForegroundColor $SUCCESS
        Write-Host "Your terminal just got smarter." -ForegroundColor $MUTED
    }
    Write-Host ""
    Write-Host "Next steps:"
    Write-Host "  custo setup    " -ForegroundColor $ACCENT -NoNewline
    Write-Host "— Configure LLM provider (interactive)"
    Write-Host "  custo chat     " -ForegroundColor $ACCENT -NoNewline
    Write-Host "— Start chatting"
    Write-Host "  custo doctor   " -ForegroundColor $ACCENT -NoNewline
    Write-Host "— Health check"
    Write-Host "  custo help     " -ForegroundColor $ACCENT -NoNewline
    Write-Host "— All commands"
    Write-Host ""
    Write-Host "Docs: https://github.com/$Repo" -ForegroundColor $MUTED
    Write-Host ""
}

# ── Main Installation Flow ────────────────────────────────────
function main {
    print_banner
    
    # Check for existing installation
    $is_upgrade = $false
    if (Test-Path "$InstallDir\.git") {
        $is_upgrade = $true
        ui_info "Existing installation detected, upgrading"
    }
    
    # Stage 1: Environment
    ui_stage "Preparing environment"
    
    # Python
    $python = check_python
    if (-not $python) {
        ui_info "Installing Python"
        if (-not (install_python)) {
            ui_error "Python installation failed"
            exit 1
        }
        
        # Re-check Python
        $python = check_python
        if (-not $python) {
            ui_error "Python installation failed"
            exit 1
        }
    }
    
    # pip
    install_pip $python
    
    # Git
    if (-not (check_git)) {
        install_git
    }
    
    # Stage 2: Installation
    ui_stage "Installing Custo"
    
    # Clone or update repository
    clone_or_update_repo
    
    # Change to install directory
    Set-Location $InstallDir
    
    # Install Python dependencies
    install_dependencies $python
    
    # Stage 3: Verification
    ui_stage "Verifying installation"
    
    # Verify installation
    verify_installation $python
    
    # Stage 4: Shell Integration
    ui_stage "Configuring shell"
    
    # Add to PATH and create alias
    add_to_path
    create_alias $python
    
    # Stage 5: Interactive Setup
    ui_stage "Setup"
    
    # Launch interactive setup if TTY available
    launch_interactive_setup $python
    
    # Print completion message
    print_completion $is_upgrade
}

# ── Entry Point ───────────────────────────────────────────────
if ($env:CUSTO_INSTALL_PS1_NO_RUN -ne "1") {
    main
}