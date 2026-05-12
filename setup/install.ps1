<#
.SYNOPSIS
    Custo - One-line install:  powershell -c "iex (iwr 'https://custo.ai/install.ps1')"
.DESCRIPTION
    Installs Custo on Windows: downloads repo, sets up Python, configures LLM.
#>

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$Repo = "relharrati/custo"
$Branch = "master"
$InstallDir = if ($env:CUSTO_DIR) { $env:CUSTO_DIR } else { "$env:USERPROFILE\.custo" }

Write-Host ""
Write-Host "  ╔═══════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "  ║     Custo - Autonomous Operator       ║" -ForegroundColor Cyan
Write-Host "  ║        One-Line Installer             ║" -ForegroundColor Cyan
Write-Host "  ╚═══════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

function Step($msg) { Write-Host "▸ $msg" -ForegroundColor Cyan }
function Ok($msg)   { Write-Host "  ✓ $msg" -ForegroundColor Green }
function Fail($msg) { Write-Host "  ✗ $msg" -ForegroundColor Red; exit 1 }

# ── Check Python ──────────────────────────────────────────────
Step "Checking Python..."
$Python = $null
foreach ($cmd in @("python3", "python", "py")) {
    try {
        $ver = & $cmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
        $major = $ver.Split('.')[0] -as [int]
        if ($major -ge 3) { $Python = $cmd; break }
    } catch {}
}

if (-not $Python) {
    Fail "Python 3 not found. Install Python 3.9+ from https://python.org"
}
Ok "Found $Python $(& $Python --version 2>&1 | Select-Object -First 1)"

# ── Download ──────────────────────────────────────────────────
Step "Downloading Custo..."
if (Test-Path "$InstallDir") {
    Write-Host "  Updating existing installation at $InstallDir"
    Push-Location "$InstallDir"
    try { & git pull --ff-only 2>$null } catch {}
    Pop-Location
} else {
    $zipUrl = "https://github.com/$Repo/archive/refs/heads/$Branch.zip"
    $zipFile = "$env:TEMP\custo.zip"
    try {
        Invoke-WebRequest -Uri $zipUrl -OutFile $zipFile -UseBasicParsing
        Expand-Archive -Path $zipFile -DestinationPath "$env:TEMP\custo_extracted" -Force
        $extracted = Get-ChildItem "$env:TEMP\custo_extracted" -Directory | Select-Object -First 1
        Move-Item $extracted.FullName $InstallDir -Force
        Remove-Item "$env:TEMP\custo_extracted" -Recurse -Force -ErrorAction SilentlyContinue
        Remove-Item $zipFile -Force -ErrorAction SilentlyContinue
        Ok "Downloaded to $InstallDir"
    } catch {
        # Fallback: git clone
        & git clone --depth 1 "https://github.com/$Repo.git" $InstallDir 2>$null
        if (-not (Test-Path $InstallDir)) { Fail "Download failed. Try: git clone https://github.com/$Repo.git" }
        Ok "Cloned to $InstallDir"
    }
}
Set-Location $InstallDir

# ── Install Python deps ──────────────────────────────────────
Step "Installing Python dependencies..."
try {
    & $Python -m pip install pyyaml 2>&1 | ForEach-Object { Write-Host "  $_" }
    Ok "Dependencies installed"
} catch {
    try {
        & $Python -m ensurepip --upgrade 2>$null
        & $Python -m pip install pyyaml 2>&1 | ForEach-Object { Write-Host "  $_" }
        Ok "Dependencies installed"
    } catch {
        Write-Host "  Could not auto-install pyyaml. Run manually: $Python -m pip install pyyaml" -ForegroundColor Yellow
    }
}

# ── Setup ─────────────────────────────────────────────────────
Step "Running first-time setup..."
$env:CUSTO_NONINTERACTIVE = "1"
try { & $Python setup/init_config.py 2>$null } catch {}
try { & $Python setup/first_run.py 2>$null } catch {}
Remove-Item Env:\CUSTO_NONINTERACTIVE -ErrorAction SilentlyContinue
Ok "Setup complete"
Write-Host "  Run 'custo setup' later for the full TUI configuration wizard." -ForegroundColor Cyan

# ── Ensure custo is callable ─────────────────────────────────
$instDir = $InstallDir
$custoBat = Join-Path $instDir "custo.bat"

if (Test-Path $custoBat) {
    # PowerShell profile script for persistent alias
    $profileScript = @"

# Custo CLI
Set-Alias custo "$custoBat"

"@
    # Write to user profile for future sessions
    $profileDir = Split-Path $PROFILE -Parent
    if (-not (Test-Path $profileDir)) { New-Item -ItemType Directory -Path $profileDir -Force | Out-Null }
    $existingProfile = if (Test-Path $PROFILE) { Get-Content $PROFILE -Raw -ErrorAction SilentlyContinue } else { "" }
    if ($existingProfile -notlike "*custo*") {
        Add-Content -Path $PROFILE -Value $profileScript -Encoding UTF8
        Write-Host "  ✓ Added to PowerShell profile ($PROFILE)" -ForegroundColor Green
    }
}

# ── PATH (user-level, for cmd.exe and future shells) ─────────
$userPath = [Environment]::GetEnvironmentVariable("PATH", "User")
if ($userPath -notlike "*$instDir*") {
    $newPath = "$instDir;$userPath"
    [Environment]::SetEnvironmentVariable("PATH", $newPath, "User")
    Write-Host "  ✓ Added to user PATH (new terminals)" -ForegroundColor Green
}
$env:PATH = "$instDir;$env:PATH"

# ── Instructions for the running session ────────────────────
Write-Host ""
Write-Host "  ⚠  To use 'custo' in this terminal:" -ForegroundColor Yellow
Write-Host "     Set-Alias custo '$custoBat'" -ForegroundColor Cyan
Write-Host "  Or open a new PowerShell window."
Write-Host ""

# ── Done ──────────────────────────────────────────────────────
Write-Host ""
Write-Host "  Custo installed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "  Run:  custo setup    — Configure LLM provider" -ForegroundColor White
Write-Host "  Run:  custo chat     — Start chatting" -ForegroundColor White
Write-Host "  Run:  custo doctor   — Health check" -ForegroundColor White
Write-Host ""
