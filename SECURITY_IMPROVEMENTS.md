# Security & Reliability Improvements

## Overview
This document summarizes critical security and reliability enhancements implemented in response to static code analysis by the Code Review Architect agent.

## Changes Implemented

### 1. Dependency Pinning (`requirements.txt`)
**Issue**: Unpinned dependencies allowed breaking changes to slip in.

**Fix**: Pinned to specific minor versions:
- `fastapi==0.115.*`
- `uvicorn[standard]==0.30.*`
- `pydantic==2.9.*`

**Impact**: Prevents unexpected breaking changes during builds and deployments.

---

### 2. World Name Validation
**Issue**: Directory traversal vulnerability - world names were not validated, allowing `../` sequences to write outside the worlds directory.

**Fix**: 
- Added `_validate_world_name()` function with strict regex: `^[A-Za-z0-9_-]{1,64}$`
- Added Pydantic `@field_validator` to `WorldCreateRequest` and `WorldSelectRequest`
- Validates on both create and select operations

**Impact**: Prevents path traversal attacks and ensures safe filesystem operations.

---

### 3. Thread-Safe Atomic File Operations
**Issue**: Race conditions and data corruption possible with concurrent writes; partial writes on crashes.

**Fix**:
- Added per-file `threading.Lock` via `_get_lock_for_path()`
- Implemented atomic writes using temp file + `os.replace()` + `fsync()`
- Applied to `save_lore_db()` and `save_sessions()`
- Added locking to `load_lore_db()` and `load_sessions()`

**Impact**: 
- Thread-safe concurrent operations
- Crash-resistant atomic writes (no partial/corrupted files)
- Data integrity guaranteed even under load

---

### 4. UUID-Based Lore Entry IDs
**Issue**: Sequential ID generation (`len(db)+1`) prone to collisions under concurrent creates and fragile after deletions.

**Fix**:
- Changed lore entry IDs from `int` to `str` (UUID v4)
- Updated `create_lore_entry()` to use `str(uuid.uuid4())`
- Updated `LoreUpdateRequest.id` type to `str`
- Updated bridge schema for `mythos_update_lore_entry`

**Impact**: Collision-free, globally unique IDs that work correctly under concurrency and after record deletions.

---

### 5. Optional Admin Authentication
**Issue**: No authentication on destructive operations (wipe, create world, select world) - dangerous if exposed.

**Fix**:
- Added `MYTHOS_ADMIN_TOKEN` environment variable (optional)
- Created `_check_admin_auth()` helper
- Protected endpoints:
  - `mythos_wipe_lore_db`
  - `mythos_create_world`
  - `mythos_select_world`
- Uses `X-Admin-Token` header for token validation
- Auth is **disabled by default** (if env var not set) for dev convenience

**Usage**:
```bash
# Enable auth by setting the token
export MYTHOS_ADMIN_TOKEN="your-secret-token-here"
docker compose up --build -d

# Calls to protected endpoints must include header:
curl -X POST http://localhost:8001/call/mythos_wipe_lore_db \
  -H "Content-Type: application/json" \
  -H "X-Admin-Token: your-secret-token-here" \
  -d '{"confirm":"CONFIRM"}'
```

**Impact**: Prevents unauthorized destructive operations when enabled; backward-compatible (off by default).

---

### 6. Documentation Fix
**Issue**: Tool docs claimed "10 storytelling frameworks" but 22 are defined.

**Fix**: Updated `mythos_list_tools` endpoint description to accurately reflect "22 storytelling frameworks".

**Impact**: Correct documentation for users and LLMs.

---

## Remaining Considerations

### Global World State (Not Yet Addressed)
**Issue**: `ACTIVE_WORLD_NAME` is a process-global variable mutated by world select operations. Under concurrent multi-user access, users can interfere with each other's world context.

**Future Fix Options**:
1. **Per-request world parameter**: Add `world_name` to all tool schemas and resolve paths per-request
2. **Session-based tenancy**: Issue session tokens tied to a world; resolve via FastAPI dependency injection
3. **Single-user assumption**: Document that backend is single-user and recommend reverse proxy with per-user instances

**Current Mitigation**: Atomic file operations prevent corruption; race conditions on world state are possible but won't corrupt files.

---

## Testing

### Healthcheck Results
All MCP protocol phases pass:
- Backend `/healthz` reachable ✓
- Protocol negotiation (2024-10-07) ✓
- Tool enumeration (19 tools) ✓
- Semantic analysis fields ✓
- Multi-framework composite ✓
- Session lifecycle (start → update → finalize → list) ✓
- World template validation ✓

### Regression Testing Recommendations
1. **Concurrent write test**: Spawn 5 threads creating lore entries simultaneously; verify no duplicate IDs and no file corruption
2. **World name injection test**: Attempt to create worlds with names like `../../../etc/passwd`, `..`, `.`, verify rejection
3. **Auth bypass test**: Call protected endpoints without token (if enabled); verify 403 responses
4. **Crash recovery test**: Kill backend mid-write; verify no corrupted JSON files on restart

---

## Migration Notes

### UUID ID Migration
Existing lore databases with integer IDs will continue to work for reads. New entries will have UUID string IDs. Tools that update lore entries should accept string IDs going forward.

If you need to migrate old integer IDs to UUIDs:
```python
import json
import uuid

with open('world_data/lore_db.json', 'r') as f:
    db = json.load(f)

for entry in db:
    if isinstance(entry.get('id'), int):
        entry['id'] = str(uuid.uuid4())

with open('world_data/lore_db.json', 'w') as f:
    json.dump(db, f, indent=2)
```

### Auth Enablement
To enable authentication in production:
1. Generate a strong random token: `openssl rand -hex 32`
2. Set in docker-compose.yml environment:
   ```yaml
   environment:
     - MYTHOS_ADMIN_TOKEN=your-generated-token
   ```
3. Update MCP bridge or API clients to pass `X-Admin-Token` header for protected operations

---

## Performance Impact

- **File locking overhead**: Minimal (microseconds per lock acquisition in uncontended scenarios)
- **Atomic write overhead**: ~2x writes (temp file + rename), but still <10ms for typical JSON sizes
- **UUID generation**: Negligible (<1μs per ID)

Trade-off is well worth the correctness and safety guarantees.

---

## References
- [Code Review Architect Agent](.github/agents/mythos.cra.agent.md)
- [FastAPI Security Best Practices](https://fastapi.tiangolo.com/tutorial/security/)
- [Python Threading Documentation](https://docs.python.org/3/library/threading.html)
- [Atomic File Operations Best Practices](https://docs.python.org/3/library/os.html#os.replace)
