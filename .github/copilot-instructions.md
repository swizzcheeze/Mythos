# Mythos World Engine - AI Agent Instructions

## Architecture Overview

This is a **two-component MCP (Model Context Protocol) bridge system**:
1. **mythos-bridge.js**: Node.js stdio bridge implementing MCP protocol 2024-10-07 for LM Studio
2. **mythos_backend**: FastAPI service (Docker) providing creative writing tools via HTTP

**Data flow**: LM Studio → MCP stdio → mythos-bridge.js → HTTP → FastAPI backend → persistent JSON storage

## Critical Patterns

### MCP Protocol Negotiation
- **ALWAYS use `2024-10-07`** for `protocolVersion` (NOT `2024-11-01` - LM Studio rejects newer versions)
- Protocol version is env-configurable: `MYTHOS_MCP_PROTOCOL` in `mythos-bridge.js`
- Bridge implements three MCP methods: `initialize`, `tools/list`, `tools/call`
- All responses are JSON-RPC 2.0 over stdio with newline-delimited messages

### Tool Schema Synchronization
**Bridge tools must mirror backend Pydantic models exactly**:
- `mythos-bridge.js` `tools[]` array defines MCP tool schemas
- `mythos_backend.py` Pydantic models define FastAPI validation
- **Keep `required` fields in sync**: If backend makes a field optional with `Field(default=...)`, update bridge schema description to say "Optional"
- Tags pattern: `tags: List[str] = Field(default=[])` in backend = NOT in `required[]` in bridge

### Error Handling Strategy
- **HTTP 422 from backend**: Pydantic validation failure - check required fields match between bridge and backend
- **Connection refused on 8001**: Backend not running - user must `docker compose up`
- **MCP protocol errors**: Wrap all `tools/call` logic in try/catch to return proper JSON-RPC errors with request ID (not generic parse errors)

Example from `mythos-bridge.js`:
```javascript
try {
  const result = await handleToolCall(request.params.name, request.params.arguments || {});
  process.stdout.write(JSON.stringify({
    jsonrpc: '2.0',
    id: request.id,
    result: { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] }
  }) + '\n');
} catch (err) {
  process.stdout.write(JSON.stringify({
    jsonrpc: '2.0',
    id: request.id,
    error: { code: -32000, message: err?.error || 'Tool call failed', data: err?.details || String(err) }
  }) + '\n');
}
```

### Healthcheck Reliability (mcp-healthcheck.js)
Phased validation with timeouts ensures fast feedback before LM Studio usage:
1. Backend `/healthz` probe (fast fail if container not running)
2. MCP `initialize` (protocolVersion must be `2024-10-07`)
3. `tools/list` (schema enumeration)
4. Sample `tools/call` sequence (semantic fields + session lifecycle)

Timeout constants (adjust if running in slow CI):
```
INIT_TIMEOUT_MS = 4000
TOOLS_TIMEOUT_MS = 4000
CALLS_TIMEOUT_MS = 8000
```
Early abort conditions:
- First 404 from any tool endpoint (indicates backend missing endpoint or mismatch)
- Per-phase timeout expiration

Exit codes:
- `0` success; non-zero indicates phase failure or endpoint error.

When adding new critical tools, optionally extend the sample calls in the healthcheck to assert presence of expected keys.

### Lightweight Semantic Scoring
Single and multi-archetype analyses use token + synonym overlap (threshold `0.08`); below threshold triggers `low_signal_fallback` and random heuristic selection (marked explicitly).

Returned metrics:
- `confidence_primary`, `confidence_secondary`: normalized overlap scores.
- `tension_score`: intra-framework difference.
- `composite_tension_metric`: variance of primary scores across blended frameworks.
- `low_signal_fallback`: boolean flag for heuristic selection.

## Creative Writing & Worldbuilding Tools

### Core & Extended Tooling
1. **mythos_archetype_analysis** – Single-framework character analysis.
2. **mythos_multi_archetype_analysis** – Composite archetype blending (e.g. `Fantasy + Horror + Jungian`).
3. **mythos_create_lore_entry / mythos_update_lore_entry** – Persistent lore CRUD (tags optional; always load/save around world context).
4. **mythos_get_inspiration** – Thematic constraint prompts (Sacrifice / Transformation / Time).
5. **mythos_creation_mode** – Static template reference (one-shot).
6. **mythos_creation_session_start / update / get / finalize / list** – Interactive, persistent creation workflow with per-world `sessions.json`.
7. **World Management** – `mythos_create_world`, `mythos_select_world`, `mythos_list_worlds`, `mythos_wipe_lore_db`.
8. **Discovery** – `mythos_list_tools`, `mythos_list_lore_entries`, `mythos_list_archetype_styles`.

### Multi-Archetype Blending Pattern
- Accepts free-form composite string: delimiters supported (`+`, `,`, `/`, `with`, `and`).
- Fuzzy matching: case-insensitive, partial prefix accepted (`jung` → `Jungian`).
- Safety cap (`max_frameworks`) prevents runaway combinatorics (default 5).
- Output: array of per-framework primary/secondary archetypes + composite summary + synthesis suggestion.

### Interactive Creation Sessions
- Persistent per world: stored in `world_data/sessions.json` (default) or `world_data/worlds/<world>/sessions.json`.
- Finalization produces preview only; commit explicitly via `mythos_create_lore_entry`.
- Session list endpoint returns progress counts (filled field tally vs total).

### Tool Extension Pattern
When adding domain-specific creative tools:
- Define semantic structure in Pydantic model (e.g., `character_name`, `description` for archetypes)
- Return rich JSON with `analysis_result`, `suggestion`, or similar LLM-friendly keys
- Use `Field(default=...)` for optional fields to avoid 422 errors from incomplete LLM calls

## Development Workflows

### Testing End-to-End
```powershell
# 1. Start backend
docker compose up --build

# 2. Run comprehensive health check (initialize → tools/list → tools/call)
node .\mcp-healthcheck.js

# Expected: [OK] messages for protocol negotiation, tool discovery, and sample call
# Tools/call may WARN if backend is down - this is non-fatal in health check
```

### Adding New Tools
1. **Backend** (`mythos_backend.py`):
   - Add Pydantic model with `Field(...)` for required or `Field(default=...)` for optional
   - Create endpoint: `@app.post("/call/mythos_new_tool")`
2. **Bridge** (`mythos-bridge.js`):
   - Add tool definition to `tools[]` array
   - Match `inputSchema.required[]` to Pydantic required fields
3. **Test**: `docker compose up --build` → `node .\mcp-healthcheck.js`

### Debugging
- **LM Studio logs**: Check Developer Logs for `[Plugin(mcp/mythos)]` stderr/stdout
- **Backend logs**: `docker compose logs -f mythos-backend` shows FastAPI requests and errors
- **Bridge stdio**: Run `node mythos-bridge.js` manually, send JSON-RPC via stdin to test protocol

## Persistence & State

- **Lore (default world)**: `world_data/lore_db.json`
- **Lore (custom world)**: `world_data/worlds/<name>/lore_db.json`
- **Sessions (default world)**: `world_data/sessions.json`
- **Sessions (custom world)**: `world_data/worlds/<name>/sessions.json`
- Switching worlds reloads both lore and sessions; creation endpoints always act on active world.
- `mythos_wipe_lore_db` wipes only the active world’s lore (sessions remain unless explicitly removed externally).

## Port Configuration

- **8001**: FastAPI backend (exposed from container internal 8001)
- **1234**: LM Studio inference (not managed by this project)
- Changing backend port requires updates in:
  - `docker-compose.yml` ports mapping
  - `mythos-bridge.js` `BASE_URL` constant
  - `Dockerfile` CMD (internal port stays 8001 unless you change CMD)

## Environment Variables

| Variable | Component | Purpose | Default |
|----------|-----------|---------|---------|
| `MYTHOS_MCP_PROTOCOL` | Bridge | Override MCP protocol version | `2024-10-07` |
| `LORE_DB_PATH` | Backend | Path to lore JSON file | `/app/world_data/lore_db.json` |

## Common Pitfalls

1. **Protocol version mismatch**: LM Studio currently rejects `2024-11-01`. Always use `2024-10-07` or earlier.
2. **422 errors**: Usually caused by missing required fields or type mismatches between bridge schema and backend Pydantic model.
3. **Bridge appears in LM Studio but tools fail**: Backend container is likely not running. Verify with `docker compose ps`.
4. **Parse errors in bridge catch block**: Avoid referencing `request` in the catch - it may be undefined if JSON.parse failed.

## File Structure (Updated)
```
mythos/
├── mythos-bridge.js           # MCP stdio bridge (Node.js)
├── mcp-healthcheck.js         # Protocol & tool sanity checks
├── docker-compose.yml         # Container orchestration
├── mythos_backend/
│   ├── Dockerfile             # Python 3.11-slim
│   ├── mythos_backend.py      # FastAPI: frameworks, sessions, worlds
│   └── requirements.txt       # fastapi, uvicorn[standard], pydantic
└── world_data/
  ├── lore_db.json           # Default world lore
  ├── sessions.json          # Default world sessions
  └── worlds/
    └── <world>/
      ├── lore_db.json
      └── sessions.json
```

## Implementation Notes
- Keep bridge tool list synchronized after adding endpoints (`mythos_multi_archetype_analysis`, session tools, world tools).
- Always guard file IO with directory creation.
- When extending archetype frameworks: add definitions to `ARCHETYPE_DEFINITIONS`; multi-blend automatically picks them up.
- For future NLP upgrades: replace `random.choice` with semantic scoring (e.g., embedding similarity to description).
- Update healthcheck script when new endpoint outputs must be validated (add id mapping + expected keys).
- Preserve JSON shape stability for downstream LLM parsing; avoid renaming top-level metric fields without versioning.

## Extension Ideas
- Session expiration + cleanup endpoint.
- Batch export (Markdown world bible). 
- Vector search for lore + session unification.
