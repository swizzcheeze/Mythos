# Mythos World Engine — Agent Setup Guide

## What This Is

Mythos is an MCP server for worldbuilding, lore management, character creation, and archetype analysis. It exposes 21 tools over stdio JSON-RPC that any MCP-compatible agent can use.

**Architecture:** `mythos-bridge.js` (MCP stdio bridge) → `mythos_backend` (FastAPI on port 8013) → JSON storage + FAISS embeddings.

## Setup (3 Steps)

### Step 1: Clone and start the backend

```bash
git clone https://github.com/swizzcheeze/Mythos.git
cd Mythos
```

**Docker (recommended):**
```bash
docker compose up -d
```

**Or local Python:**
```bash
pip install -r mythos_backend/requirements.txt
python -m mythos_backend.main &
```

Verify the backend is running:
```bash
curl http://localhost:8013/healthz
# Should return: {"status":"ok","version":"2.0.0"}
```

### Step 2: Register the MCP server

The bridge file is `mythos-bridge.js` in the repo root. Register it as a stdio MCP server using the **absolute path**:

```bash
echo "Y" | hermes mcp add mythos --command node --args "/absolute/path/to/Mythos/mythos-bridge.js"
```

Replace `/absolute/path/to/Mythos/` with the actual clone path. Use `$(pwd)/mythos-bridge.js` if you're already in the repo directory:

```bash
echo "Y" | hermes mcp add mythos --command node --args "$(pwd)/mythos-bridge.js"
```

For other MCP clients (LM Studio, Claude Desktop, etc.), add this to their MCP config:

```json
{
  "mythos": {
    "command": "node",
    "args": ["/absolute/path/to/Mythos/mythos-bridge.js"],
    "env": {
      "MYTHOS_PORT": "8013"
    }
  }
}
```

### Step 3: Verify

```bash
hermes mcp test mythos
# Should show: ✓ Connection established
```

All 21 tools are now available prefixed with `mythos_`:

- `mythos_create_world`, `mythos_list_worlds`, `mythos_select_world`, `mythos_delete_world`
- `mythos_archetype_analysis`, `mythos_multi_archetype_analysis`
- `mythos_creation_session_start/update/get/finalize/list`
- `mythos_create_lore_entry`, `mythos_list_lore_entries`, `mythos_update_lore_entry`
- `mythos_semantic_lore_search`
- `mythos_roleplay_start`, `mythos_get_inspiration`
- `mythos_wipe_lore_db`, `mythos_list_tools`, `mythos_list_archetype_styles`

## Pitfalls

1. **Relative paths won't work.** `mythos-bridge.js` must be registered with an absolute path. If the MCP server fails to connect, check the path first.

2. **Backend must be running before the bridge connects.** The bridge tries to reach `http://localhost:8013` on every tool call. If the backend is down, tool calls return connection errors.

3. **Port is configurable.** Set `MYTHOS_PORT` env var to change from the default `8013`. The bridge, backend, and healthcheck all read this variable.

4. **Docker Compose build context.** The `docker-compose.yml` uses `context: .` (repo root), not `context: ./mythos_backend`. The Dockerfile path is `mythos_backend/Dockerfile`.

5. **Three Docker variants.** Default is NVIDIA CUDA. For CPU-only: edit `docker-compose.yml` to use `mythos_backend/Dockerfile.cpu`. For AMD ROCm (Linux only): use `mythos_backend/Dockerfile.rocm`.

6. **Install scripts.** `scripts/install.sh` (Linux/macOS) and `scripts/install.ps1` (Windows) handle clone + backend startup. They do NOT register the MCP server — that's a separate step.

## Quick Reference

```bash
# One-line install (backend only)
curl -fsSL https://raw.githubusercontent.com/swizzcheeze/Mythos/main/scripts/install.sh | bash

# Start backend
docker compose up -d              # Docker
python -m mythos_backend.main &   # Local

# Register with Hermes
echo "Y" | hermes mcp add mythos --command node --args "$(pwd)/mythos-bridge.js"

# Verify
hermes mcp test mythos
curl http://localhost:8013/healthz
```
