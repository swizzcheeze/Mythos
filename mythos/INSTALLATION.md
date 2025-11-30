# Installation Guide

## Quick Start

### 1. Start the Backend

```powershell
# Build and start the FastAPI backend
docker compose up --build

# Or run detached
docker compose up --build -d
```

The backend will be available at `http://localhost:8001`.

### 2. Verify Backend Health

```powershell
# Check health endpoint
Invoke-WebRequest -Uri "http://localhost:8001/healthz" | Select-Object StatusCode, Content

# View API docs
start http://localhost:8001/docs
```

### 3. Test MCP Bridge (Phased Healthcheck)

```powershell
# Run comprehensive health check (backend probe + initialize + tools/list + sample calls)
node .\mcp-healthcheck.js
```

Phases & expectations:
1. Backend `/healthz` probe → `[OK] Backend /healthz reachable` (fast fail if container down)
2. MCP `initialize` → protocol version `2024-10-07` reported
3. `tools/list` → shows 18+ tools (count grows as features expand)
4. Sample tool calls:
  - Single-framework analysis (semantic fields present)
  - Multi-framework composite (diversity metric)
  - Creation session lifecycle (start/update/finalize/list)

Timeouts (defaults in script): `INIT_TIMEOUT_MS=4000`, `TOOLS_TIMEOUT_MS=4000`, `CALLS_TIMEOUT_MS=8000`.

Early aborts:
- Any 404 from tool endpoint (schema/back-end mismatch)
- Phase timeout expiry

Exit code `0` indicates full pass; non-zero signals reliability issue.

### 4. Configure LM Studio

Add to your LM Studio MCP configuration (usually in settings or config file):

```json
{
  "mcpServers": {
    "mythos": {
      "command": "node",
      "args": ["<drive>\\mythos\\mythos-bridge.js"],
      "env": {
        "MYTHOS_MCP_PROTOCOL": "2024-10-07"
      }
    }
  }
}
```

Restart LM Studio and verify the `mythos` tools appear in the tools panel.

## Testing & Validation

### Manual Backend Testing (Core)

```powershell
# Test archetype analysis
$body = @{
    character_name = "Kai"
    description = "A temporal hacker haunted by erased timelines"
    style = "James Cameron"
} | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8001/call/mythos_archetype_analysis" -Method Post -Body $body -ContentType "application/json"

# Test lore entry creation
$body = @{
    topic = "Test Ritual"
    content = "A test entry without tags"
} | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8001/call/mythos_create_lore_entry" -Method Post -Body $body -ContentType "application/json"

# Test inspiration generator
$body = @{style = "cyberpunk"} | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8001/call/mythos_get_inspiration" -Method Post -Body $body -ContentType "application/json"
```

### View Lore Database

```powershell
Get-Content .\world_data\lore_db.json | ConvertFrom-Json | Format-List
```

### Multi-World & Sessions Paths

Default world:
```powershell
Get-Content .\world_data\lore_db.json
Get-Content .\world_data\sessions.json
```

Custom world example (`Eldoria`):
```powershell
Get-Content .\world_data\worlds\Eldoria\lore_db.json
Get-Content .\world_data\worlds\Eldoria\sessions.json
```

### Interactive Creation Flow
```powershell
# Start a session
$start = @{ template_type = 'character'; style = 'Fantasy' } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8001/call/mythos_creation_session_start" -Method Post -Body $start -ContentType 'application/json'

# Update a field (replace SESSION_ID accordingly)
$update = @{ session_id = 'SESSION_ID'; updates = @{ 'Basic Info' = @{ 'Name' = 'Aria Nyx' } } } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8001/call/mythos_creation_session_update" -Method Post -Body $update -ContentType 'application/json'

# Finalize preview
$final = @{ session_id = 'SESSION_ID' } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8001/call/mythos_creation_session_finalize" -Method Post -Body $final -ContentType 'application/json'
```

### Multi-Archetype Blend (Semantic + Diversity Metrics)
```powershell
$blend = @{ character_name='Aria Nyx'; description='A soulbound mage haunted by echo timelines.'; styles='Fantasy + Horror + Jungian' } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8001/call/mythos_multi_archetype_analysis" -Method Post -Body $blend -ContentType 'application/json'
```

Response fields of interest:
- `analyses[]`: per-framework primary/secondary archetypes with confidences
- `confidence_primary` / `confidence_secondary`: token+synonym overlap scores
- `tension_score`: intra-framework difference (internal friction potential)
- `composite_tension_metric`: variance across framework primary scores (diversity tension)
- `low_signal_fallback`: true if description lacked semantic signal (random heuristic used)
```

## Configuration

### Environment Variables

#### Backend (Docker)
- `LORE_DB_PATH`: Path to lore database (default: `world_data/lore_db.json`)

#### Bridge (Node.js)
- `MYTHOS_MCP_PROTOCOL`: MCP protocol version (default: `2024-10-07`)

### Override Protocol Version

```powershell
$env:MYTHOS_MCP_PROTOCOL="2024-10-07"
node .\mythos-bridge.js
```

## Troubleshooting

### Error: "Server's protocol version is not supported: 2024-11-01"
**Solution:** The bridge now defaults to `2024-10-07`. Update LM Studio MCP config or set env var:
```powershell
$env:MYTHOS_MCP_PROTOCOL="2024-10-07"
```

### Error: "MCP error -32000: Mythos Backend HTTP Error: 422"
**Cause:** Validation error from FastAPI (e.g., missing required field).

**Solution:** 
- Ensure `topic` and `content` are provided for `mythos_create_lore_entry`
- `tags` is optional and defaults to empty array `[]`
- Check backend logs: `docker compose logs -f`

### Error: "[CRITICAL] Could not connect to Mythos Backend on port 8001"
**Solution:**
```powershell
# Check if backend is running
docker compose ps

# Start if not running
docker compose up -d

# Check backend logs
docker compose logs -f
```

### Bridge Not Appearing in LM Studio
1. Verify LM Studio MCP config path is correct
2. Check LM Studio Developer Logs for stderr output
3. Run health check manually:
   ```powershell
   node .\mcp-healthcheck.js
   ```
4. Restart LM Studio after config changes

### Lore Database Not Persisting
**Cause:** Volume mount misconfiguration.

**Solution:**
```powershell
# Verify volume exists
docker volume ls | Select-String mythos

# Recreate volume
docker compose down -v
docker compose up --build
```

## Development

### Rebuild Backend Only

```powershell
docker compose build mythos-backend
docker compose up -d mythos-backend
```

### Watch Backend Logs

```powershell
docker compose logs -f mythos-backend
```

### Update MCP Protocol

Edit `mythos-bridge.js`:
```javascript
const MCP_PROTOCOL_VERSION = process.env.MYTHOS_MCP_PROTOCOL || '2024-10-07';
```

### Add / Extend Tools (Schema Synchronization)

1. Add Pydantic model in `mythos_backend.py`
2. Create endpoint: `@app.post("/call/mythos_new_tool")`
3. Add tool definition to `mythos-bridge.js` `tools` array
4. Rebuild: `docker compose up --build`
5. Test: `node .\mcp-healthcheck.js` (verifies new tool appears & returns 2xx; update sample calls if you want automated validation)

If you modify required fields (Pydantic `Field(...)` vs `Field(default=...)`), ensure `mythos-bridge.js` tool schema `required[]` matches to avoid 422.

## Port Configuration

| Service | Port | Purpose |
|---------|------|---------|
| FastAPI Backend | 8001 | Tool execution endpoints |
| LM Studio | 1234 | LLM inference server |

To change backend port, update `docker-compose.yml`:
```yaml
ports:
  - "8002:8000"  # Host:Container
```

And update `mythos-bridge.js`:
```javascript
const BASE_URL = 'http://localhost:8002';
```

## File Persistence

Lore and sessions persist per world:

| World | Lore Path | Sessions Path |
|-------|-----------|---------------|
| default | `world_data/lore_db.json` | `world_data/sessions.json` |
| custom `<name>` | `world_data/worlds/<name>/lore_db.json` | `world_data/worlds/<name>/sessions.json` |

**Backup:**
```powershell
Copy-Item .\world_data\lore_db.json .\world_data\lore_db.backup.json
```

**Restore:**
```powershell
Copy-Item .\world_data\lore_db.backup.json .\world_data\lore_db.json
docker compose restart
```

## Architecture

```
mythos/
├── mythos-bridge.js          # MCP stdio bridge for LM Studio
├── mcp-healthcheck.js         # Health check script for MCP protocol
├── docker-compose.yml         # Container orchestration
├── mythos_backend/
│   ├── Dockerfile
│   ├── mythos_backend.py      # FastAPI server (sessions + multi-world + multi-archetype)
│   └── requirements.txt
└── world_data/
  ├── lore_db.json           # Default world lore
  ├── sessions.json          # Default world sessions
  └── worlds/
    └── <world>/
      ├── lore_db.json
      └── sessions.json
```

## Support

For issues related to:
- **MCP Protocol:** Check LM Studio Developer Logs and run `node .\mcp-healthcheck.js`
- **Backend Errors:** Check `docker compose logs -f mythos-backend`
- **Bridge Issues:** Check Node.js version (requires v14+) and run with `--trace-warnings`
- **Phase Timeouts:** Increase constants in `mcp-healthcheck.js` if running under heavy load / slow environments.
