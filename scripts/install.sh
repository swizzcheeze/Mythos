#!/bin/bash
# ============================================================================
# Mythos World Engine Installer
# ============================================================================
# Installation script for Linux, macOS, Windows (Git Bash / MSYS2 / WSL),
# and Android/Termux.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/swizzcheeze/Mythos/main/scripts/install.sh | bash
#
# Or with options:
#   curl -fsSL ... | bash -s -- --method local --port 8013
#
# Options:
#   --method docker|local     Install method (default: docker)
#   --variant cuda|cpu|rocm   Docker variant (default: cuda, auto-detected)
#   --port PORT               Backend port (default: 8013)
#   --no-start                Skip running after install
#   --skip-healthcheck        Skip post-install healthcheck
# ============================================================================

set -e

# ---------------------------------------------------------------------------
# Colors & formatting
# ---------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

info()  { echo -e "${BLUE}[INFO]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }
ok()    { echo -e "${GREEN}[OK]${NC} $1"; }
header(){ echo -e "\n${BOLD}${CYAN}═══ $1 ═══${NC}\n"; }

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
METHOD="docker"
VARIANT="cuda"
PORT="8013"
NO_START=false
SKIP_HEALTHCHECK=false
REPO_URL="https://github.com/swizzcheeze/Mythos.git"
INSTALL_DIR=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --method)       METHOD="$2";          shift 2 ;;
        --variant)      VARIANT="$2";         shift 2 ;;
        --port)         PORT="$2";            shift 2 ;;
        --no-start)     NO_START=true;        shift ;;
        --skip-healthcheck) SKIP_HEALTHCHECK=true; shift ;;
        *)              warn "Unknown option: $1"; shift ;;
    esac
done

# ---------------------------------------------------------------------------
# Detect OS and architecture
# ---------------------------------------------------------------------------
OS="unknown"
ARCH=$(uname -m 2>/dev/null || echo "unknown")
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" || "$OSTYPE" == "cygwin" ]]; then
    OS="windows"
fi

header "Mythos World Engine Installer"
echo -e "  OS:   ${CYAN}$OS${NC} (${ARCH})"
echo -e "  Mode: ${CYAN}$METHOD${NC}"
echo ""

# ---------------------------------------------------------------------------
# Dependency checks
# ---------------------------------------------------------------------------
header "Checking dependencies"

# Git
if command -v git &>/dev/null; then
    ok "git $(git --version | awk '{print $3}')"
else
    error "git is required but not found."
    echo "  Install it from https://git-scm.com/downloads"
    exit 1
fi

# Docker (only needed for docker method)
if [[ "$METHOD" == "docker" ]]; then
    if command -v docker &>/dev/null; then
        DOCKER_VERSION=$(docker --version 2>/dev/null | awk '{print $3}' | tr -d ',')
        ok "Docker ${DOCKER_VERSION}"
    else
        error "Docker is required for --method docker but not found."
        echo "  Install it from https://docs.docker.com/get-docker/"
        echo "  Or use --method local to run without Docker."
        exit 1
    fi

    # Check if Docker daemon is running
    if ! docker info &>/dev/null; then
        error "Docker daemon is not running. Start Docker Desktop first."
        exit 1
    fi
    ok "Docker daemon is running"

    # Check docker compose
    if docker compose version &>/dev/null; then
        ok "docker compose $(docker compose version 2>/dev/null --short)"
    elif command -v docker-compose &>/dev/null; then
        warn "Using legacy docker-compose. Consider upgrading to Docker Compose v2."
    else
        error "docker compose is required but not found."
        exit 1
    fi
fi

# Python (only needed for local method or healthcheck)
if [[ "$METHOD" == "local" || "$SKIP_HEALTHCHECK" == "false" ]]; then
    PYTHON_BIN=""
    for py in python3.11 python3 python; do
        if command -v "$py" &>/dev/null; then
            PY_VER=$("$py" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
            if [[ "$PY_VER" == 3.1* ]]; then
                PYTHON_BIN="$py"
                break
            fi
        fi
    done
    if [[ -n "$PYTHON_BIN" ]]; then
        ok "Python $($PYTHON_BIN -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")')"
    else
        warn "Python 3.11+ not found. Local method may not work."
        PYTHON_BIN="python3"
    fi
fi

# Node.js (needed for healthcheck script)
if command -v node &>/dev/null; then
    ok "Node.js $(node --version)"
elif [[ "$SKIP_HEALTHCHECK" == "false" ]]; then
    warn "Node.js not found (optional). Healthcheck script uses node."
fi

# ---------------------------------------------------------------------------
# Clone / update repo
# ---------------------------------------------------------------------------
header "Repository"

# Default install location
if [[ -z "$INSTALL_DIR" ]]; then
    INSTALL_DIR="$(pwd)/Mythos"
fi

if [[ -d "$INSTALL_DIR/.git" ]]; then
    info "Repo already exists at $INSTALL_DIR — pulling latest..."
    cd "$INSTALL_DIR"
    git pull origin main 2>/dev/null || git pull origin master 2>/dev/null || warn "Could not pull latest. Using existing code."
    ok "Repository up to date"
else
    info "Cloning Mythos into $INSTALL_DIR..."
    git clone "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
    ok "Cloned $(git log --oneline -1)"
fi

echo -e "  Path: ${CYAN}$(pwd)${NC}"

# ---------------------------------------------------------------------------
# Environment file
# ---------------------------------------------------------------------------
header "Configuration"

if [[ ! -f .env ]]; then
    if [[ -f .env.example ]]; then
        cp .env.example .env
        ok "Created .env from .env.example"
    fi
else
    ok ".env already exists"
fi

# Set port in .env if different from default
if [[ "$PORT" != "8013" ]]; then
    if grep -q "^MYTHOS_PORT=" .env 2>/dev/null; then
        sed -i.bak "s/^MYTHOS_PORT=.*/MYTHOS_PORT=$PORT/" .env
    else
        echo "" >> .env
        echo "# Custom port" >> .env
        echo "MYTHOS_PORT=$PORT" >> .env
    fi
    ok "Set MYTHOS_PORT=$PORT in .env"
fi

echo -e "  Port: ${CYAN}${PORT}${NC}"
echo -e "  LLM:  ${CYAN}${MYTHOS_LLM_PROVIDER:-ollama}${NC} (change in .env)"

# ---------------------------------------------------------------------------
# Docker: build and start
# ---------------------------------------------------------------------------
if [[ "$METHOD" == "docker" ]]; then
    header "Docker (${VARIANT})"

    # Auto-detect variant if not explicitly set
    if [[ "$VARIANT" == "cuda" ]]; then
        if command -v nvidia-smi &>/dev/null && nvidia-smi &>/dev/null 2>&1; then
            ok "NVIDIA GPU detected — using CUDA variant"
        elif [[ "$OS" == "linux" ]] && lspci 2>/dev/null | grep -qi "amd.*vga\|amd.*display"; then
            warn "AMD GPU detected. Consider --variant rocm for GPU acceleration."
            warn "ROCm is Linux-only. Falling back to CPU variant."
            VARIANT="cpu"
        else
            warn "No NVIDIA GPU detected. Using CPU variant."
            VARIANT="cpu"
        fi
    fi

    DOCKERFILE="mythos_backend/Dockerfile"
    case "$VARIANT" in
        cpu)   DOCKERFILE="mythos_backend/Dockerfile.cpu" ;;
        rocm)  DOCKERFILE="mythos_backend/Dockerfile.rocm"
               if [[ "$OS" != "linux" ]]; then
                   error "ROCm is Linux-only. Use --variant cuda or --variant cpu."
                   exit 1
               fi
               ;;
    esac

    export MYTHOS_PORT="$PORT"

    echo -e "  Dockerfile: ${CYAN}$DOCKERFILE${NC}"
    echo -e "  Port:       ${CYAN}${PORT}${NC}"
    info "Building Docker image..."

    docker compose build --build-arg BUILDKIT_INLINE_CACHE=1
    ok "Image built"

    if [[ "$NO_START" == "false" ]]; then
        info "Starting Mythos..."
        docker compose up -d
        ok "Container started"
    fi

# ---------------------------------------------------------------------------
# Local: install Python dependencies
# ---------------------------------------------------------------------------
elif [[ "$METHOD" == "local" ]]; then
    header "Local Python Setup"

    VENV_DIR=".venv"

    if [[ ! -d "$VENV_DIR" ]]; then
        info "Creating virtual environment..."
        $PYTHON_BIN -m venv "$VENV_DIR"
        ok "Virtual environment created at $VENV_DIR"
    else
        ok "Virtual environment already exists"
    fi

    info "Installing dependencies..."
    source "$VENV_DIR/bin/activate" 2>/dev/null || source "$VENV_DIR/Scripts/activate"
    pip install --upgrade pip setuptools wheel -q
    pip install -r mythos_backend/requirements.txt -q
    ok "Dependencies installed"

    if [[ "$NO_START" == "false" ]]; then
        export MYTHOS_PORT="$PORT"
        info "Starting Mythos on port $PORT..."
        nohup python -m mythos_backend.main > mythos.log 2>&1 &
        SERVER_PID=$!
        echo $SERVER_PID > .mythos.pid
        info "Backend started (PID: $SERVER_PID, log: mythos.log)"
    fi
fi

# ---------------------------------------------------------------------------
# Healthcheck
# ---------------------------------------------------------------------------
if [[ "$SKIP_HEALTHCHECK" == "false" && "$NO_START" == "false" ]]; then
    header "Health Check"

    info "Waiting for backend to start..."
    HEALTH_URL="http://127.0.0.1:${PORT}/healthz"
    TRIES=0
    MAX_TRIES=15
    while [[ $TRIES -lt $MAX_TRIES ]]; do
        if curl -sf "$HEALTH_URL" &>/dev/null; then
            break
        fi
        sleep 2
        TRIES=$((TRIES + 1))
        echo -n "."
    done
    echo ""

    if [[ $TRIES -lt $MAX_TRIES ]]; then
        ok "Backend is healthy at $HEALTH_URL"

        if command -v node &>/dev/null; then
            info "Running MCP healthcheck..."
            node mcp-healthcheck.js 2>&1
        fi
    else
        warn "Backend did not become healthy within $((MAX_TRIES * 2)) seconds."
        echo "  Check logs:"
        if [[ "$METHOD" == "docker" ]]; then
            echo "    docker compose logs mythos_backend"
        else
            echo "    tail -f mythos.log"
        fi
    fi
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
header "Installation Complete"

echo -e "  ${GREEN}Mythos World Engine is ready.${NC}\n"
echo -e "  Endpoints:"
echo -e "    API:      ${CYAN}http://127.0.0.1:${PORT}${NC}"
echo -e "    Docs:     ${CYAN}http://127.0.0.1:${PORT}/docs${NC}"
echo -e "    Health:   ${CYAN}http://127.0.0.1:${PORT}/healthz${NC}"
echo ""
echo -e "  Manage:"
if [[ "$METHOD" == "docker" ]]; then
    echo -e "    Stop:     ${CYAN}docker compose down${NC}"
    echo -e "    Logs:     ${CYAN}docker compose logs -f mythos_backend${NC}"
    echo -e "    Restart:  ${CYAN}docker compose restart${NC}"
else
    if [[ -f .mythos.pid ]]; then
        echo -e "    Stop:     ${CYAN}kill $(cat .mythos.pid) && rm .mythos.pid${NC}"
    fi
    echo -e "    Logs:     ${CYAN}tail -f mythos.log${NC}"
fi
echo ""
echo -e "  Repo: ${CYAN}${INSTALL_DIR}${NC}"
echo -e "  MCP bridge: configure Hermes Agent to use ${CYAN}mythos-bridge.js${NC}"
echo ""
