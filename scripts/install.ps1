# ============================================================================
# Mythos World Engine Installer for Windows
# ============================================================================
# Installation script for Windows (PowerShell).
# Requires PowerShell 5.1+ (built into Windows 10+).
#
# Usage (PowerShell):
#   iex (irm https://raw.githubusercontent.com/swizzcheeze/Mythos/main/scripts/install.ps1)
#
# Or download and run with options:
#   .\install.ps1 -Method local -Port 8013
#
# Options:
#   -Method docker|local       Install method (default: docker)
#   -Variant cuda|cpu|rocm     Docker variant (default: cuda, auto-detected)
#   -Port PORT                 Backend port (default: 8013)
#   -NoStart                   Skip running after install
#   -SkipHealthcheck           Skip post-install healthcheck
# ============================================================================

param(
    [ValidateSet("docker","local")]
    [string]$Method = "docker",

    [ValidateSet("cuda","cpu","rocm")]
    [string]$Variant = "cuda",

    [string]$Port = "8013",

    [switch]$NoStart,
    [switch]$SkipHealthcheck
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$RepoUrl = "https://github.com/swizzcheeze/Mythos.git"
$InstallDir = Join-Path $pwd.Path "Mythos"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
function Write-Color($Text, $Color = "White") {
    Write-Host $Text -ForegroundColor $Color
}
function Info($msg)  { Write-Color "  [INFO] $msg" Cyan }
function Ok($msg)    { Write-Color "  [OK]   $msg" Green }
function Warn($msg)  { Write-Color "  [WARN] $msg" Yellow }
function Err($msg)   { Write-Color "  [ERROR] $msg" Red }
function Header($title) {
    Write-Host ""
    Write-Host "  ═══ $title ═══" -ForegroundColor DarkCyan
    Write-Host ""
}

# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------
Header "Mythos World Engine Installer"

Write-Color "  OS:    Windows ($($env:PROCESSOR_ARCHITECTURE))" Cyan
Write-Color "  Mode:  $Method" Cyan
Write-Host ""

# ---------------------------------------------------------------------------
# Dependency checks
# ---------------------------------------------------------------------------
Header "Checking dependencies"

# Git
try {
    $gitVer = (git --version) -replace 'git version ', ''
    Ok "git $gitVer"
} catch {
    Err "git is required but not found."
    Write-Host "  Install it from https://git-scm.com/downloads"
    exit 1
}

# Docker (only for docker method)
if ($Method -eq "docker") {
    try {
        $dockerVer = (docker --version) -replace 'Docker version ', '' -replace ',',''
        Ok "Docker $dockerVer"
    } catch {
        Err "Docker is required for -Method docker but not found."
        Write-Host "  Install it from https://docs.docker.com/get-docker/"
        Write-Host "  Or use -Method local to run without Docker."
        exit 1
    }

    try {
        $null = docker info 2>&1
        Ok "Docker daemon is running"
    } catch {
        Err "Docker daemon is not running. Start Docker Desktop first."
        exit 1
    }

    try {
        $composeVer = (docker compose version --short 2>&1)
        Ok "docker compose $composeVer"
    } catch {
        Warn "docker compose not found. Trying docker-compose..."
        try {
            $null = docker-compose --version 2>&1
            Ok "docker-compose (legacy)"
        } catch {
            Err "docker compose is required but not found."
            exit 1
        }
    }
}

# Python (for local method or healthcheck)
if ($Method -eq "local" -or -not $SkipHealthcheck) {
    $pythonBin = $null
    foreach ($py in @("python3.11", "python3", "python")) {
        try {
            $ver = & $py -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>&1
            if ($ver -and $ver -match '^3\.1') {
                $pythonBin = $py
                break
            }
        } catch { }
    }
    if ($pythonBin) {
        Ok "Python $ver ($pythonBin)"
    } else {
        Warn "Python 3.11+ not found. Local method may not work."
        $pythonBin = "python"
    }
}

# Node.js (for healthcheck)
try {
    $nodeVer = (node --version)
    Ok "Node.js $nodeVer"
} catch {
    Warn "Node.js not found (optional). Healthcheck script uses node."
}

# ---------------------------------------------------------------------------
# Clone / update repo
# ---------------------------------------------------------------------------
Header "Repository"

if (Test-Path (Join-Path $InstallDir ".git")) {
    Info "Repo already exists at $InstallDir — pulling latest..."
    Push-Location $InstallDir
    git pull origin main 2>$null
    Pop-Location
    Ok "Repository up to date"
} else {
    Info "Cloning Mythos into $InstallDir..."
    git clone $RepoUrl $InstallDir
    Ok "Cloned"
}
$repoPath = (Resolve-Path $InstallDir).Path
Set-Location $repoPath
Write-Color "  Path: $repoPath" Gray

# ---------------------------------------------------------------------------
# Environment file
# ---------------------------------------------------------------------------
Header "Configuration"

if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Ok "Created .env from .env.example"
    }
} else {
    Ok ".env already exists"
}

# Set port in .env
if ($Port -ne "8013") {
    if (Select-String -Path ".env" -Pattern "^MYTHOS_PORT=" -Quiet) {
        (Get-Content ".env") -replace "^MYTHOS_PORT=.*", "MYTHOS_PORT=$Port" | Set-Content ".env"
    } else {
        Add-Content ".env" "`n# Custom port`nMYTHOS_PORT=$Port"
    }
    Ok "Set MYTHOS_PORT=$Port in .env"
}

$configuredProvider = (Select-String -Path ".env" -Pattern "^MYTHOS_LLM_PROVIDER=" | ForEach-Object { $_ -replace '.*=', '' }) -replace ' '
Write-Color "  Port: $Port" Gray
Write-Color "  LLM:  $($configuredProvider -replace ' ', 'ollama')" Gray

# ---------------------------------------------------------------------------
# Docker: build and start
# ---------------------------------------------------------------------------
if ($Method -eq "docker") {
    Header "Docker ($Variant)"

    # Auto-detect
    if ($Variant -eq "cuda") {
        try {
            $nvidia = nvidia-smi 2>&1
            if ($LASTEXITCODE -eq 0) {
                Ok "NVIDIA GPU detected — using CUDA variant"
            } else { throw }
        } catch {
            Warn "No NVIDIA GPU detected. Using CPU variant."
            $Variant = "cpu"
        }
    }

    $dockerfile = "mythos_backend\Dockerfile"
    switch ($Variant) {
        "cpu"  { $dockerfile = "mythos_backend\Dockerfile.cpu" }
        "rocm" { $dockerfile = "mythos_backend\Dockerfile.rocm"
                 Err "ROCm is Linux-only on Docker. Use -Variant cuda or -Variant cpu."
                 exit 1
               }
    }

    $env:MYTHOS_PORT = $Port

    Write-Color "  Dockerfile: $dockerfile" Gray
    Write-Color "  Port:       $Port" Gray
    Info "Building Docker image..."
    docker compose build --build-arg BUILDKIT_INLINE_CACHE=1
    Ok "Image built"

    if (-not $NoStart) {
        Info "Starting Mythos..."
        docker compose up -d
        Ok "Container started"
    }

# ---------------------------------------------------------------------------
# Local: install Python dependencies
# ---------------------------------------------------------------------------
} elseif ($Method -eq "local") {
    Header "Local Python Setup"

    $venvDir = Join-Path $repoPath ".venv"

    if (-not (Test-Path $venvDir)) {
        Info "Creating virtual environment..."
        & $pythonBin -m venv $venvDir
        Ok "Virtual environment created"
    } else {
        Ok "Virtual environment already exists"
    }

    Info "Installing dependencies..."
    $pipExe = Join-Path $venvDir "bin\pip"
    if ($IsWindows -or $env:OS -eq "Windows_NT") {
        $pipExe = Join-Path $venvDir "Scripts\pip.exe"
    }
    & $pipExe install --upgrade pip setuptools wheel -q
    & $pipExe install -r "mythos_backend\requirements.txt" -q
    Ok "Dependencies installed"

    if (-not $NoStart) {
        $env:MYTHOS_PORT = $Port
        Info "Starting Mythos on port $Port..."
        $logFile = Join-Path $repoPath "mythos.log"
        $proc = Start-Process -FilePath $pythonBin -ArgumentList "-m","mythos_backend.main" -WindowStyleHidden -PassThru
        $proc.Id | Set-Content (Join-Path $repoPath "mythos.pid")
        Info "Backend started (PID: $($proc.Id), log: $logFile)"
    }
}

# ---------------------------------------------------------------------------
# Healthcheck
# ---------------------------------------------------------------------------
if (-not $SkipHealthcheck -and -not $NoStart) {
    Header "Health Check"

    $healthUrl = "http://localhost:$Port/healthz"
    Info "Waiting for backend to start..."

    $trials = 0
    $maxTrials = 15
    $healthy = $false
    while ($trials -lt $maxTrials) {
        try {
            $resp = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
            if ($resp.StatusCode -eq 200) { $healthy = $true; break }
        } catch { }
        Start-Sleep -Seconds 2
        $trials++
        Write-Host "." -NoNewline
    }
    Write-Host ""

    if ($healthy) {
        Ok "Backend is healthy at $healthUrl"

        try {
            Info "Running MCP healthcheck..."
            Push-Location $repoPath
            node mcp-healthcheck.js
            Pop-Location
        } catch {
            Warn "Could not run MCP healthcheck (optional)."
        }
    } else {
        Warn "Backend did not become healthy within $($maxTrials * 2) seconds."
        Write-Host "  Check logs:" -ForegroundColor Yellow
        if ($Method -eq "docker") {
            Write-Host "    docker compose logs mythos_backend"
        } else {
            Write-Host "    Get-Content mythos.log -Tail 20"
        }
    }
}

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
Header "Installation Complete"

Write-Host "  Mythos World Engine is ready." -ForegroundColor Green
Write-Host ""
Write-Host "  Endpoints:"
Write-Host "    API:      http://localhost:$Port" -ForegroundColor Cyan
Write-Host "    Docs:     http://localhost:$Port/docs" -ForegroundColor Cyan
Write-Host "    Health:   http://localhost:$Port/healthz" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Manage:"
if ($Method -eq "docker") {
    Write-Host "    Stop:     docker compose down" -ForegroundColor Cyan
    Write-Host "    Logs:     docker compose logs -f mythos_backend" -ForegroundColor Cyan
    Write-Host "    Restart:  docker compose restart" -ForegroundColor Cyan
} else {
    if (Test-Path "mythos.pid") {
        $pid = Get-Content "mythos.pid"
        Write-Host "    Stop:     Stop-Process -Id $pid" -ForegroundColor Cyan
    }
    Write-Host "    Logs:     Get-Content mythos.log -Wait" -ForegroundColor Cyan
}
Write-Host ""
Write-Host "  Repo: $repoPath" -ForegroundColor Gray
Write-Host "  MCP bridge: configure Hermes Agent to use mythos-bridge.js"
Write-Host ""
