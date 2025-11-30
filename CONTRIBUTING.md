# Contributing Guide

Thank you for your interest in improving Mythos World Engine! This guide outlines workflow, quality expectations, and patterns that keep the project reliable and MCP-compatible.

## Core Principles
- **Deterministic JSON**: Avoid renaming or removing existing top-level response fields without version bump & changelog entry.
- **Schema Sync**: Backend Pydantic models and bridge tool `inputSchema.required[]` must match exactly to prevent 422 errors.
- **Fail Fast**: Healthcheck should surface regressions quickly (timeouts, early 404 aborts, semantic field presence checks).

## Development Workflow
1. Fork & clone: `git clone https://github.com/swizzcheeze/Mythos`
2. Create feature branch: `git checkout -b feat/<short-descriptor>`
3. Start backend: `docker compose up --build -d`
4. Implement changes (backend + bridge + docs).
5. Run healthcheck: `node mcp-healthcheck.js`
6. Add/Update tests in healthcheck if new critical fields introduced.
7. Update `CHANGELOG.md` (Added / Changed / Fixed).
8. Commit using Conventional Commits.
9. Push & open Pull Request.

## Conventional Commit Examples
- `feat: add eldritch framework definitions`
- `fix: align lore update required fields with bridge schema`
- `docs: explain composite tension metric`
- `chore: bump FastAPI version`

## Adding a New Tool
1. Backend (`mythos_backend.py`):
   - Define Pydantic model (use `Field(default=...)` for optional fields)
   - Implement endpoint: `@app.post("/call/mythos_new_tool")`
2. Bridge (`mythos-bridge.js`):
   - Add tool entry to `tools[]` with matching required fields
3. Healthcheck (`mcp-healthcheck.js`):
   - Optionally add a validation call verifying key output fields
4. Documentation:
   - Update README feature list & Installation guide if needed
5. Test: `node mcp-healthcheck.js` (should pass all phases)

## Semantic Scoring Extensions
If integrating embeddings:
- Preserve existing confidence fields; add new ones under a nested object (e.g., `semantic_embeddings.confidence_primary`) to avoid breaking downstream parsing.
- Document new metrics in README and CHANGELOG.

## File & State Safety
- Always ensure directories exist before file writes (`world_data/worlds/<name>`).
- Avoid destructive operations without explicit confirmation tokens (pattern: wipe endpoints).

## Performance Guidelines
- Keep per-request processing lightweight (semantic scoring currently token overlap; avoid heavy model inference inside FastAPI path functions).
- Use caching if adding large static frameworks.

## Healthcheck Extension Pattern
Add new IDs sequentially and document expected keys. Fail early on missing critical keys if feature is core (e.g., semantic metrics). Keep timeouts adjustable via constants near top of script.

## Pull Request Checklist
- [ ] Feature / fix implemented and tested locally
- [ ] Healthcheck passes (no timeouts / unexpected 404s)
- [ ] README / INSTALLATION updated where relevant
- [ ] CHANGELOG entry added
- [ ] No unrelated formatting-only changes
- [ ] Conventional commit message

## Code Style
- Python: prefer clear variable names, avoid one-letter except loop indices.
- JavaScript (bridge): keep error handling in try/catch, structured JSON-RPC responses.
- Avoid inline commentary unless clarifying non-obvious logic.

## Licensing
This project is MIT Licensed; include attribution for any significant external data sources if added.

---
**Thank you for helping build richer creative tooling!**
