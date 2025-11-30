# Mythos World Engine v1.0.0 Release Notes

Release Date: 2025-11-30
Tag: v1.0.0

## Overview
Initial public release of the Mythos World Engine: an MCP-integrated creative writing and worldbuilding toolkit combining semantic archetype analysis, multi-world lore persistence, and interactive creation sessions.

## Highlights
- 22 archetype frameworks + composite multi-framework blending.
- Lightweight semantic scoring (confidence + tension + variance metrics).
- Interactive creation session lifecycle (start/update/get/finalize/list) with per-world persistence.
- Multi-world management tooling (create/select/list/wipe).
- Robust healthcheck with phased validation, timeouts, and early abort on 404.
- Structured lore CRUD (create/update) with optional tags.
- Creative inspiration generator (thematic constraints).

## New Metrics
- `confidence_primary` / `confidence_secondary`: semantic overlap scores.
- `tension_score`: intra-framework difference.
- `composite_tension_metric`: variance across primary archetypes in blend.
- `low_signal_fallback`: indicates heuristic selection when semantic signal weak.

## Reliability Features
- `/healthz` probe before MCP negotiation.
- Per-phase timeouts (initialize, tools/list, calls).
- Immediate abort on first 404 to surface schema mismatches.

## Upgrade Guidance
Existing local clones should:
1. Pull latest main.
2. Run `docker compose up --build -d`.
3. Execute `node mcp-healthcheck.js` to validate environment.

No migration steps needed for new frameworks; blends auto-detect additions.

## Known Limitations
- Semantic scoring is token/synonym based (no embeddings yet).
- No vector lore search (planned).
- Session expiration/cleanup not implemented.

## Planned (Post-1.0.0)
- Embedding-based semantic similarity.
- Vector search for lore entries.
- World export (Markdown/PDF bible).
- Session advisory / auto-fill heuristics.

## Action Items for Contributors
- Use Conventional Commits.
- Extend healthcheck when adding critical output fields.
- Maintain JSON stability; version bump for breaking changes.

## Thanks
Community feedback welcome—open issues or PRs for frameworks, semantic improvements, and export tooling.

Happy Worldbuilding!
