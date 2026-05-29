# 🌊 Mythos World Engine

> **AI-Powered Creative Writing & Worldbuilding Toolkit**
>
> *Rebuilt from the ground up — type-safe entities, per-world isolation, 22 archetype frameworks, semantic search, and a clean FastAPI backend.*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![MCP](https://img.shields.io/badge/MCP-2024--10--07-green.svg)](https://modelcontextprotocol.io/)
[![CI](https://github.com/swizzcheeze/Mythos/actions/workflows/ci.yml/badge.svg)](https://github.com/swizzcheeze/Mythos/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-teal.svg)](https://fastapi.tiangolo.com/)

---

## ⚡ What Is This?

Mythos is a **worldbuilding co-pilot** for creative writers, tabletop game masters, and worldbuilders. It persists your fictional worlds, characters factions, and lore in a searchable knowledge base — then lets you analyze, create, and roleplay through any MCP-compatible AI client (LM Studio, Hermes Agent, etc.).

**v2.0 Rebuild**: The entire backend was rewritten to fix a critical entity type discrimination bug (characters saved as worlds, personas as lore, etc.), add per-world data isolation, and follow modern FastAPI patterns. The bridge layer now has 21 validated tool endpoints.

---

## ✨ Features

### 🧬 22-Archetype Character Analysis
Analyze characters through **22 storytelling frameworks** — or blend them (`Fantasy + Horror + Jungian`) for composite depth.

| Jungian | Disney | James Cameron | Fantasy | Gothic | Dark Gothic |
|---|---|---|---|---|---|
| Romance | Mystery | Adventure | Norse | Mythological | Greek |
| Horror | Sci-Fi | Quantum Physics | Medieval | C.S. Lewis | Stephen King |
| Alfred Hitchcock | Japanese | Korean | General | | |

Each analysis returns **primary/secondary archetypes**, confidence scores, and a **tension metric** that measures internal character conflict potential.

### 📖 Persistent Multi-World Lore
- Per-world JSON storage — each world has its own `lore_db.json`, `sessions.json`, and FAISS vector index
- Type-safe entity CRUD: characters, worlds, factions, locations, artifacts, creatures, events, cultures, conflicts, rituals, magic systems
- Semantic search across all lore using embeddings (FAISS-backed)
- Create, select, list, and delete isolated world workspaces

### 🛠 Interactive Creation Sessions
Guided templates for 11 entity types with structured sections and creative prompts:

```
Start → Fill Sections → Preview → Save as Entity
```

Each session is persistent and world-scoped. Characters, worlds, factions, magic systems, creatures, artifacts, events, cultures, conflicts, and rituals — all with genre-aware templates.

### 🎭 Roleplay Mode
Generate character persona prompts from your creation sessions. Any MCP-compatible client can use these to stay in-character during interactive storytelling.

### 🔌 Multi-LLM Support
Configured via environment variables — switch between providers without code changes:

| Provider | Config |
|----------|--------|
| **Ollama** (default) | `MYTHOS_LLM_PROVIDER=ollama` |
| **Anthropic** | `MYTHOS_LLM_PROVIDER=anthropic` |
| **OpenRouter** | `MYTHOS_LLM_PROVIDER=openrouter` |
| **Groq** | `MYTHOS_LLM_PROVIDER=groq` |
| **xAI (Grok)** | `MYTHOS_LLM_PROVIDER=xai` |
| **Google Gemini** | `MYTHOS_LLM_PROVIDER=gemini` |

---

## 🚀 Quick Start

### Using Docker (Recommended)

```powershell
# Clone and start
git clone https://github.com/swizzcheeze/Mythos.git
cd Mythos
docker compose up -d

# Verify health
node .\mcp-healthcheck.js
```

### Using Hermes Agent

```bash
# Start the backend locally (no Docker needed)
cd mythos_backend
pip install -r requirements.txt
python main.py

# In Hermes Agent, the mythos-bridge.js MCP server connects to localhost:8001
```

### Local Development

```powershell
cd D:\Mythos
pip install -r mythos_backend\requirements.txt
python -m mythos_backend.main
# → http://localhost:8001/docs
```

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────┐
│  AI Client (LM Studio / Hermes Agent / etc.)    │
└────────────────────┬────────────────────────────┘
                     │ MCP (stdio JSON-RPC)
                     ▼
┌─────────────────────────────────────────────────┐
│  mythos-bridge.js  (MCP Server)                 │
│  21 tool endpoints → POST /call/{toolName}      │
└────────────────────┬────────────────────────────┘
                     │ HTTP localhost:8001
                     ▼
┌─────────────────────────────────────────────────┐
│  Mythos Backend v2.0  (FastAPI)                 │
│                                                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐    │
│  │ /entities│ │/sessions │ │  /worlds     │    │
│  │ CRUD     │ │ templates│ │  management  │    │
│  └──────────┘ └──────────┘ └──────────────┘    │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐    │
│  │/archetypes│ │  /llm   │ │ /embeddings  │    │
│  │ analysis  │ │generate │ │  + FAISS     │    │
│  └──────────┘ └──────────┘ └──────────────┘    │
│                                                 │
│  Services: world_data · embedding · archetype   │
│  Models: Pydantic v2 discriminated unions       │
└─────────────────────────────────────────────────┘
```

### Key Design Decisions

- **Discriminated union entities** — `entity_type` field enforces correct type at validation time. No more "persona saved as world."
- **Per-world isolation** — All data scoped to `(world, entity)` pairs. Zero cross-world leakage.
- **Atomic file I/O** — JSON writes use temp+rename with per-path file locks.
- **No global mutable state** — All config via env vars, all services are stateless functions.
- **Bridge dispatch** — `/call/{toolName}` maps 21 MCP tool names to typed backend handlers.

---

## 🔧 Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `MYTHOS_LLM_PROVIDER` | `ollama` | LLM provider |
| `MYTHOS_OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama endpoint |
| `MYTHOS_OLLAMA_MODEL` | `llama3` | Default model |
| `EMBEDDING_SERVICE_URL` | `http://localhost:8002` | Embedding service |
| `COHERE_API_KEY` | None | Cohere embedding fallback |
| `MYTHOS_ADMIN_TOKEN` | None | Admin auth (None = open) |

---

## 🛠 API Endpoints

### Entity CRUD
```
POST   /entities              → Create (type-safe via entity_type)
GET    /entities              → List/search (filter by type, tags, search)
GET    /entities/{id}         → Get one
PATCH  /entities/{id}         → Partial update
DELETE /entities/{id}         → Delete
```

### Creation Sessions
```
GET    /sessions/templates    → List template types
POST   /sessions              → Start session
GET    /sessions/{id}         → Get state + progress
POST   /sessions/{id}/update  → Fill section fields
POST   /sessions/{id}/finalize → Preview + optional save
DELETE /sessions/{id}         → Delete session
```

### World Management
```
GET    /worlds                → List all worlds + entity counts
POST   /worlds                → Create world
DELETE /worlds/{name}         → Delete world
GET    /worlds/{name}/stats   → World statistics
```

### LLM
```
POST   /llm/generate          → Text generation
POST   /llm/critique          → Critique/analysis
GET    /llm/providers         → Available providers
```

### Full docs at `/docs` (Swagger UI) when running.

---

## 🧪 Testing

```powershell
# Full healthcheck (validates all 21 MCP tools)
node .\mcp-healthcheck.js

# Python tests
python -m pytest tests/
```

---

## 📁 What's in Each File

| File | Purpose |
|------|---------|
| `mythos_backend/main.py` | FastAPI app, lifespan, router mounting |
| `mythos_backend/models/entities.py` | Pydantic v2 discriminated union models |
| `mythos_backend/services/world_data.py` | Per-world CRUD, atomic file I/O |
| `mythos_backend/services/embedding.py` | Embedding with retry + FAISS |
| `mythos_backend/services/archetype.py` | 22-framework semantic analysis |
| `mythos_backend/services/templates.py` | Interactive creation sessions |
| `mythos_backend/routes/bridge.py` | MCP dispatch (21 tool handlers) |
| `mythos_backend/routes/entities.py` | Entity CRUD endpoints |
| `mythos_backend/routes/sessions.py` | Session endpoints |
| `mythos-bridge.js` | MCP server (stdio JSON-RPC) |
| `mythos_backend/Dockerfile` | CUDA-enabled container |

---

## 🙏 Acknowledgments

This project evolved over time — from basic local models doing the heavy lifting, to browser-based workflows with Gemini and Claude, to **OWL (OpenRouter) paired with Hermes Agent** doing the intensive architectural rewrite. The v2.0 rebuild that fixed the core discrimination bug and made the system production-ready was a collaborative effort between human and AI across multiple sessions and model providers.

---

## License

MIT — see [LICENSE](LICENSE)
