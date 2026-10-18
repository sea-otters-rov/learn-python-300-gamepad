#Requires -Version 5.1
<#
.SYNOPSIS
    One-shot setup of this repo on a Windows machine. Safe to run again.

.DESCRIPTION
      1. checks for VS Code and Python
      2. installs the VS Code extensions the workflow needs
      3. creates .venv with circup, pyserial, and CircuitPython stubs pinned to
         the firmware version
      4. points the `board` stubs at the XIAO RP2350's pin names
      5. seeds board\settings.toml from the example

    It does NOT run circup: board\lib is committed, so a fresh clone already has
    exactly the libraries the board needs. See device-requirements.txt.

.PARAMETER Provision
    Also copy board\ onto an attached XIAO with -Clean, so it matches exactly.
    That DELETES everything else on the board.

.EXAMPLE
    & .\tools\setup.ps1
#>
[CmdletBinding()]
param([switch]$Provision)

$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

# Keep in step with requirements-dev.txt. Stubs are generated per firmware
# release, and a mismatch means autocomplete quietly describes another version.
$CpyVersion = '10.3.1'
$BoardId    = 'seeeduino_xiao_rp2350'

function Step($n, $msg) { Write-Host "`n[$n] $msg" -ForegroundColor Cyan }
function Ok($msg)       { Write-Host "    $msg" -ForegroundColor Green }

# --- 1. preflight -------------------------------------------------------------
Step 1 'Checking prerequisites'
$code = Get-Command code -ErrorAction SilentlyContinue
if (-not $code) {
    Write-Host "    VS Code's 'code' command is not on PATH." -ForegroundColor Red
    Write-Host "    In VS Code: Ctrl+Shift+P -> 'Shell Command: Install code command in PATH'" -ForegroundColor Red
    exit 1
}
Ok "VS Code $(& code --version | Select-Object -First 1)"

$py = Get-Command py -ErrorAction SilentlyContinue
if (-not $py) { $py = Get-Command python -ErrorAction SilentlyContinue }
if (-not $py) {
    Write-Host "    No Python found. Install 3.10+ from python.org and re-run." -ForegroundColor Red
    exit 1
}
Ok "Python $(& $py.Source -V)"

# --- 2. VS Code extensions ----------------------------------------------------
Step 2 'Installing VS Code extensions'
$installed = & code --list-extensions
foreach ($ext in @(
    'ms-python.python',
    'ms-python.vscode-pylance',
    'ms-vscode.vscode-serial-monitor',
    'emeraldwalk.runonsave',
    'charliermarsh.ruff',
    'spmeesseman.vscode-taskexplorer'
)) {
    if ($installed -contains $ext) {
        Ok "$ext (already installed)"
    } else {
        & code --install-extension $ext --force | Out-Null
        Ok "$ext (installed)"
    }
}

# --- 3. virtualenv ------------------------------------------------------------
Step 3 'Creating .venv and installing tooling'
$venv = Join-Path $repo '.venv'
$vpy  = Join-Path $venv 'Scripts\python.exe'
if (-not (Test-Path $vpy)) {
    & $py.Source -m venv $venv
    Ok 'created .venv'
} else {
    Ok '.venv already exists'
}
& $vpy -m pip install --quiet --upgrade pip
& $vpy -m pip install --quiet -r (Join-Path $repo 'requirements-dev.txt')
# --no-deps: only Pylance reads these. Their declared dependency is Blinka, a
# large host-side stack nothing here imports.
& $vpy -m pip install --quiet --no-deps -r (Join-Path $repo 'requirements-intellisense.txt')
Ok "circup, pyserial, CircuitPython $CpyVersion stubs installed"

# --- 4. board-specific stubs --------------------------------------------------
Step 4 "Pointing 'board' stubs at $BoardId"
& (Join-Path $venv 'Scripts\circuitpython_setboard.exe') $BoardId | Out-Null
Ok "board.D10, board.A0, board.I2C etc. will now autocomplete"

# --- 5. settings.toml ---------------------------------------------------------
Step 5 'Seeding board\settings.toml'
$toml   = Join-Path $repo 'board\settings.toml'
$tomlEx = Join-Path $repo 'settings.toml.example'
if (Test-Path $toml) {
    Ok 'board\settings.toml already exists (left alone)'
} else {
    Copy-Item $tomlEx $toml
    Ok 'copied from settings.toml.example -- it is per board, and gitignored'
}

# --- 6. optional: provision the attached board --------------------------------
if ($Provision) {
    Step 6 'Provisioning the attached XIAO'
    & (Join-Path $repo 'tools\sync.ps1') -Clean
}

Write-Host "`nDone." -ForegroundColor Green
Write-Host "  Open this folder in VS Code, then:" -ForegroundColor Green
Write-Host "    - Ctrl+Shift+P -> 'Python: Select Interpreter' -> .venv" -ForegroundColor Green
Write-Host "    - edit board\controller.py and press Ctrl+S" -ForegroundColor Green
