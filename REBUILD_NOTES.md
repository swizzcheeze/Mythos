# Mythos Backend v2.0 — Rebuild Summary

## What Was Built

This is a ground-up rewrite of the Mythos Backend, fixing the core architectural
problems that made the original unreliable. All 38 API routes have been verified
and the entity type discrimination bug is fixed.

## File Structure

```
mythos_backend/
├── __init__.py
├── main.py                      # FastAPI app, lifespan, router mounting
├── requirements.txt             # Updated deps
├── core/
│   ├── __init__.py
│   ├── config.py                # All env vars, no globals
│   └── llm.py                   # Provider abstraction (Ollama + 5 cloud)
├── models/
│   ├── __init__.py
│   ├── entities.py              # Pydantic v2 discriminated unions (THE FIX)
│   ├── archetypes.py            # 22 framework definitions
│   └── request.py               # Request DTOs
├── services/
│   ├── __init__.py
│   ├── world_data.py            # Per-world CRUD, atomic file I/O
│   ├── embedding.py             # Retry, status tracking, FAISS
│   ├── archetype.py             # Semantic archetype analysis
│   └── templates.py             # Interactive creation sessions
└── routes/
    ├── __init__.py
    ├── entities.py              # CRUD by entity_type discriminator
    ├── sessions.py              # Per-world creation sessions
    ├── worlds.py                # World management
    ├── archetypes.py            # Character analysis
    ├── llmroutes.py             # LLM generation + critique
    ├── embeddings.py            # Embedding health + indexing
    ├── roleplay.py              # Character conversation
    └── admin.py                 # System status + maintenance
```

## How to Run

```bash
cd D:/Mythos
pip install -r mythos_backend/requirements.txt
python -m mythos_backend.main
# Or: uvicorn mythos_backend.main:mythos_backend.main.app --host 0.0.0.0 --port 8000
```

## Configuration (env vars)

| Variable | Default | Purpose |
|----------|---------|---------|
| `MYTHOS_LLM_PROVIDER` | `ollama` | `ollama`, `anthropic`, `openrouter`, `groq`, `xai`, `gemini` |
| `MYTHOS_OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama endpoint |
| `MYTHOS_OLLAMA_MODEL` | `llama3` | Default model |
| `EMBEDDING_SERVICE_URL` | `http://localhost:8002` | External embedding service |
| `COHERE_API_KEY` | None | Cohere fallback for embeddings |
| `MYTHOS_ADMIN_TOKEN` | None | Admin endpoint auth (None = open) |
| `LORE_DB_PATH` | `world_data/lore_db.json` | Lore storage path |

## What Was Fixed

1. **Entity type discrimination** — The Pydantic v2 discriminated union on
   `entity_type` ensures a character is always stored as a character, never
   accidentally as a world. This was the root cause of the "persona saved as
   world" bug.

2. **Per-world isolation** — All data (entities, sessions, vectors) is now
   scoped to a world. Switching worlds no longer leaks state. Each world has
   its own `lore_db.json`, `sessions.json`, and `vectors_metadata.json`.

3. **No global mutable state** — All config is read from env vars at startup.
   All services are stateless functions. Thread safety via per-path file locks.

4. **Atomic file I/O** — All JSON writes use temp+rename to prevent corruption
   on crash or concurrent access.

5. **Embedding service** — Retry with exponential backoff, health check caching
   (no per-call HTTP hammering), status tracking with failure counts.

6. **FastAPI architecture** — Proper `lifespan` context manager (not deprecated
   `on_event`), `APIRouter` per domain, `Depends()` for DI, no `app.logger`
   anti-pattern.

7. **LLM provider abstraction** — Clean handler pattern supporting Ollama
   (default), Anthropic, OpenRouter, Groq, xAI, and Gemini. Auto-fallback to
   Ollama if configured provider unavailable.

## Migration from Old Code

The old `mythos_backend.py` monolith and `mythos_graph.py` are replaced by the
new package. The bridge layer needs these endpoint mapping changes:

| Old Endpoint | New Endpoint | Change |
|---|---|---|
| `POST /save` (ambiguous type) | `POST /entities` (requires `entity_type`) | Now type-safe |
| `GET /search` | `GET /entities?search=` + `entity_type=` filter | Per-world |
| `POST /session/start` | `POST /sessions` | Per-world, returns session |
| `POST /session/update` | `POST /sessions/{id}/update` | Per-world |
| `POST /session/finalize` | `POST /sessions/{id}/finalize` | `save=true` to persist |
| `GET /health` | `GET /healthz` | Same purpose |

Existing world_data JSON files are compatible — the new code reads the same format.
The `entity_type` field is now **required** on creation. Old records without it
will be read as generic dicts (not validated) — add a migration script if needed.

## What's Not Included (Intentional)

- **LangGraph per-world flows** — The original had broken per-world LangGraph.
  The new architecture supports it (all state is per-world), but the actual
  LangGraph workflow definitions need to be rebuilt separately. The LLM route
  provides raw generation/critique endpoints that the bridge can use directly.
- **LangSmith** — Not wired up. Add if you want tracing.
- **Auth** — Admin token only. Add OAuth/JWT if you need user-level auth.
- **sentence-transformers / torch** — Removed from requirements. Embeddings
  are external (Ollama embed or Cohere). Re-add if you want local inference.
