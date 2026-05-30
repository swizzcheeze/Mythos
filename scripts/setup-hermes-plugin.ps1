# ============================================================================
# Mythos World Engine — Hermes Agent Plugin Setup (Windows)
# ============================================================================
# One-command setup: starts the backend and registers Mythos as an MCP server
# in Hermes Agent.
#
# Usage:
#   cd Mythos; .\scripts\setup-hermes-plugin.ps1
#
# Options:
#   -Method docker|local     Backend method (default: docker, falls back to local)
#   -Port PORT               Backend port (default: 8013)
#   -SkipStart               Don't start the backend (assume it's already running)
#   -Force                   Re-register even if mythos MCP server already exists
# ============================================================================

param(
    [ValidateSet("docker","local")]
    [string]$Method = "docker",

    [string]$Port = "8013",

    [switch]$SkipStart,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

$RepoDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$BridgePath = Join-Path $RepoDir "mythos-bridge.js"

function Write-Color($Text, $Color = "White") { Write-Host $Text -ForegroundColor $Color }
function Info($msg)  { Write-Color "  [INFO] $msg" Cyan }
function Ok($msg)    { Write-Color "  [OK]   $msg" Green }
function Warn($msg)  { Write-Color "  [WARN] $msg" Yellow }
function Err($msg)   { Write-Color "  [ERROR] $msg" Red }
function Header($title) { Write-Host ""; Write-Host "  ═══ $title ═══" -ForegroundColor DarkCyan; Write-Host "" }

# ---------------------------------------------------------------------------
Header "Mythos — Hermes Agent Plugin Setup"
# ---------------------------------------------------------------------------

if (-not (Test-Path $BridgePath)) {
    Err "mythos-bridge.js not found at $BridgePath"
    Write-Host "  Run this script from inside the Mythos repo directory."
    exit 1
}
Ok "Found mythos-bridge.js at $BridgePath"

try {
    $hermesVer = (hermes --version 2>&1)
    Ok "Hermes Agent found"
} catch {
    Err "hermes command not found. Install Hermes Agent first."
    exit 1
}

try {
    $nodeVer = (node --version)
    Ok "Node.js found: $nodeVer"
} catch {
    Err "Node.js is required for the MCP bridge but not found."
    Write-Host "  Install it from https://nodejs.org/"
    exit 1
}

# ---------------------------------------------------------------------------
# Check if already registered
# ---------------------------------------------------------------------------
$skipRegister = $false
$existing = hermes mcp list 2>&1
if ($existing -match "mythos") {
    if ($Force) {
        Warn "Mythos MCP server already registered — re-registering (-Force)"
    } else {
        Ok "Mythos MCP server is already registered in Hermes."
        Write-Host "  Use -Force to re-register."
        $skipRegister = $true
    }
}

# ---------------------------------------------------------------------------
# Start backend
# ---------------------------------------------------------------------------
if (-not $SkipStart) {
    Header "Starting Backend"

    $healthUrl = "http://localhost:$Port/healthz"
    $alreadyRunning = $false
    try {
        $resp = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        if ($resp.StatusCode -eq 200) { $alreadyRunning = $true }
    } catch {}

    if ($alreadyRunning) {
        Ok "Backend already running on port $Port"
    } else {
        $env:MYTHOS_PORT = $Port

        $useDocker = $Method -eq "docker"
        if ($useDocker) {
            try { $null = docker info 2>&1; if ($LASTEXITCODE -ne 0) { $useDocker = $false } }
            catch { $useDocker = $false }
        }

        if ($useDocker) {
            Info "Starting backend with Docker..."
            Push-Location $RepoDir
            docker compose up -d
            Pop-Location
            Ok "Docker container started"
        } else {
            if ($Method -eq "docker") { Warn "Docker not available, falling back to local Python" }
            Info "Starting backend locally..."
            Push-Location $RepoDir

            $venvDir = Join-Path $RepoDir ".venv"
            if (-not (Test-Path $venvDir)) {
                python -m venv $venvDir
                $pipExe = Join-Path $venvDir "Scripts\pip.exe"
                & $pipExe install -r "mythos_backend\requirements.txt" -q
            }

            $pythonExe = Join-Path $venvDir "Scripts\python.exe"
            $proc = Start-Process -FilePath $pythonExe -ArgumentList "-m","mythos_backend.main" -WindowStyleHidden -PassThru
            $proc.Id | Set-Content (Join-Path $RepoDir "mythos.pid")
            Info "Backend started (PID: $($proc.Id))"
            Pop-Location
        }

        # Wait for health
        $healthy = $false
        for ($i = 0; $i -lt 15; $i++) {
            try {
                $resp = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
                if ($resp.StatusCode -eq 200) { $healthy = $true; break }
            } catch {}
            Start-Sleep -Seconds 2
        }

        if ($healthy) { Ok "Backend is healthy on port $Port" }
        else { Err "Backend failed to start within 30 seconds."; exit 1 }
    }
} else {
    Info "Skipping backend start (-SkipStart)"
}

# ---------------------------------------------------------------------------
# Register MCP server
# ---------------------------------------------------------------------------
if (-not $skipRegister) {
    Header "Registering MCP Server"

    Info "Registering mythos MCP server with Hermes Agent..."
    echo "Y" | hermes mcp add mythos --command node --args $BridgePath 2>&1
    Ok "MCP server registered"
}

# ---------------------------------------------------------------------------
# Verify
# ---------------------------------------------------------------------------
Header "Verification"

Info "Testing MCP connection..."
$testResult = hermes mcp test mythos 2>&1
if ($testResult -match "Connection established|success|✓") {
    Ok "MCP connection verified"
} else {
    Warn "MCP test returned unexpected output. Try: hermes mcp test mythos"
}

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
Header "Setup Complete"

Write-Color "  Mythos is registered as a Hermes Agent MCP plugin." Green
Write-Host ""
Write-Host "  Backend:   http://localhost:$Port" -ForegroundColor Cyan
Write-Host "  Bridge:    $BridgePath" -ForegroundColor Cyan
Write-Host "  Tools:     21 mythos_* tools available in new Hermes sessions" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Next: Start a new Hermes session (or use /reload-mcp) to see the tools." -ForegroundColor White
Write-Host ""
