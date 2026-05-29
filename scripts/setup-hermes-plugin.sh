#!/bin/bash
# ============================================================================
# Mythos World Engine — Hermes Agent Plugin Setup
# ============================================================================
# One-command setup: starts the backend and registers Mythos as an MCP server
# in Hermes Agent. Run this after cloning the repo (or from the install script).
#
# Usage:
#   cd Mythos && bash scripts/setup-hermes-plugin.sh
#
# Options:
#   --method docker|local     Backend method (default: docker, falls back to local)
#   --port PORT               Backend port (default: 8013)
#   --skip-start              Don't start the backend (assume it's already running)
#   --force                   Re-register even if mythos MCP server already exists
# ============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

info()  { echo -e "${CYAN}[INFO]${NC} $1"; }
ok()    { echo -e "${GREEN}[OK]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }
header(){ echo -e "\n${BOLD}${CYAN}═══ $1 ═══${NC}\n"; }

# ---------------------------------------------------------------------------
# Args
# ---------------------------------------------------------------------------
METHOD="docker"
PORT="8013"
SKIP_START=false
FORCE=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --method)       METHOD="$2";    shift 2 ;;
        --port)         PORT="$2";      shift 2 ;;
        --skip-start)   SKIP_START=true; shift ;;
        --force)        FORCE=true;     shift ;;
        *)              shift ;;
    esac
done

# ---------------------------------------------------------------------------
# Sanity checks
# ---------------------------------------------------------------------------
header "Mythos — Hermes Agent Plugin Setup"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BRIDGE_PATH="$REPO_DIR/mythos-bridge.js"

if [[ ! -f "$BRIDGE_PATH" ]]; then
    error "mythos-bridge.js not found at $BRIDGE_PATH"
    echo "  Run this script from inside the Mythos repo directory."
    exit 1
fi
ok "Found mythos-bridge.js at $BRIDGE_PATH"

if ! command -v hermes &>/dev/null; then
    error "hermes command not found. Install Hermes Agent first:"
    echo "  curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash"
    exit 1
fi
ok "Hermes Agent found: $(hermes --version 2>/dev/null || echo 'installed')"

if ! command -v node &>/dev/null; then
    error "Node.js is required for the MCP bridge but not found."
    echo "  Install it from https://nodejs.org/"
    exit 1
fi
ok "Node.js found: $(node --version)"

# ---------------------------------------------------------------------------
# Check if already registered
# ---------------------------------------------------------------------------
if hermes mcp list 2>/dev/null | grep -q "mythos"; then
    if [[ "$FORCE" == "true" ]]; then
        warn "Mythos MCP server already registered — re-registering (--force)"
    else
        ok "Mythos MCP server is already registered in Hermes."
        echo "  Use --force to re-register."
        SKIP_REGISTER=true
    fi
fi

# ---------------------------------------------------------------------------
# Start backend
# ---------------------------------------------------------------------------
if [[ "$SKIP_START" == "false" ]]; then
    header "Starting Backend"

    # Check if already running
    if curl -sf "http://127.0.0.1:${PORT}/healthz" &>/dev/null; then
        ok "Backend already running on port $PORT"
    else
        export MYTHOS_PORT="$PORT"

        if [[ "$METHOD" == "docker" ]] && command -v docker &>/dev/null && docker info &>/dev/null 2>&1; then
            info "Starting backend with Docker..."
            cd "$REPO_DIR"
            docker compose up -d
            ok "Docker container started"

            # Wait for health
            TRIES=0
            while [[ $TRIES -lt 15 ]]; do
                if curl -sf "http://127.0.0.1:${PORT}/healthz" &>/dev/null; then
                    break
                fi
                sleep 2
                TRIES=$((TRIES + 1))
            done
        else
            if [[ "$METHOD" == "docker" ]]; then
                warn "Docker not available, falling back to local Python"
            fi
            info "Starting backend locally..."
            cd "$REPO_DIR"

            if [[ ! -d ".venv" ]]; then
                python3 -m venv .venv 2>/dev/null || python -m venv .venv
                source .venv/bin/activate 2>/dev/null || source .venv/Scripts/activate
                pip install -r mythos_backend/requirements.txt -q
            else
                source .venv/bin/activate 2>/dev/null || source .venv/Scripts/activate
            fi

            nohup python -m mythos_backend.main > mythos.log 2>&1 &
            echo $! > .mythos.pid

            TRIES=0
            while [[ $TRIES -lt 15 ]]; do
                if curl -sf "http://127.0.0.1:${PORT}/healthz" &>/dev/null; then
                    break
                fi
                sleep 2
                TRIES=$((TRIES + 1))
            done
        fi

        if curl -sf "http://127.0.0.1:${PORT}/healthz" &>/dev/null; then
            ok "Backend is healthy on port $PORT"
        else
            error "Backend failed to start within 30 seconds."
            echo "  Check logs: docker compose logs mythos_backend (or tail mythos.log)"
            exit 1
        fi
    fi
else
    info "Skipping backend start (--skip-start)"
fi

# ---------------------------------------------------------------------------
# Register MCP server
# ---------------------------------------------------------------------------
if [[ "${SKIP_REGISTER:-false}" == "false" ]]; then
    header "Registering MCP Server"

    info "Registering mythos MCP server with Hermes Agent..."
    echo "Y" | hermes mcp add mythos --command node --args "$BRIDGE_PATH" 2>&1
    ok "MCP server registered"
fi

# ---------------------------------------------------------------------------
# Verify
# ---------------------------------------------------------------------------
header "Verification"

info "Testing MCP connection..."
if hermes mcp test mythos 2>&1 | grep -q "Connection established\|success\|✓"; then
    ok "MCP connection verified"
else
    warn "MCP test returned unexpected output. Try: hermes mcp test mythos"
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
header "Setup Complete"

echo -e "  ${GREEN}Mythos is registered as a Hermes Agent MCP plugin.${NC}\n"
echo -e "  Backend:   ${CYAN}http://127.0.0.1:${PORT}${NC}"
echo -e "  Bridge:    ${CYAN}${BRIDGE_PATH}${NC}"
echo -e "  Tools:     ${CYAN}21 mythos_* tools${NC} available in new Hermes sessions"
echo ""
echo -e "  ${BOLD}Next:${NC} Start a new Hermes session (or use /reload-mcp) to see the tools."
echo ""
