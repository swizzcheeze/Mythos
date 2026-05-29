# 🌊 Mythos World Engine

> **AI-Powered Creative Writing & Worldbuilding Toolkit**
>
> *Rebuilt from the ground up — type-safe entities, per-world isolation, 22 archetype frameworks, semantic search, and a clean FastAPI backend.*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![MCP](https://img.shields.io/badge/MCP-2025--03--26-green.svg)](https://modelcontextprotocol.io/)
[![CI](https://github.com/swizzcheeze/Mythos/actions/workflows/ci.yml/badge.svg)](https://github.com/swizzcheeze/Mythos/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-teal.svg)](https://fastapi.tiangolo.com/)

---

## TL;DR

**One-line install:**
```bash
# Linux / macOS / Git Bash
curl -fsSL https://raw.githubusercontent.com/swizzcheeze/Mythos/main/scripts/install.sh | bash

# Windows PowerShell
iex (irm https://raw.githubusercontent.com/swizzcheeze/Mythos/main/scripts/install.ps1)
```

**Register with Hermes Agent:**
```bash
cd Mythos
echo "Y" | hermes mcp add mythos --command node --args "$(pwd)/mythos-bridge.js"
```

Restart Hermes — 21 `mythos_*` tools are now available in every session.

Full docs below. Docker, local Python, or Hermes plugin — pick your path.

---

## ⚡ What Is This?

Mythos is a **worldbuilding co-pilot** for creative writers, tabletop game masters, and worldbuilders. It persists your fictional worlds, characters, factions, and lore in a searchable knowledge base — then lets you analyze, create, and roleplay through any MCP-compatible AI client (Hermes Agent, LM Studio, etc.).

**v2.0 Rebuild**: The entire backend was rewritten to fix a critical entity type discrimination bug (characters saved as worlds, personas as lore, etc.), add per-world data isolation, and follow modern FastAPI patterns. The bridge layer has 21 validated tool endpoints.

---

## 🚀 Quick Start

### One-Line Install

```bash
# Linux / macOS / Git Bash / WSL
curl -fsSL https://raw.githubusercontent.com/swizzcheeze/Mythos/main/scripts/install.sh | bash

# Windows PowerShell
iex (irm https://raw.githubusercontent.com/swizzcheeze/Mythos/main/scripts/install.ps1)
```

Options: `--method local` (no Docker), `--variant cpu` (CPU-only image), `--port 9090` (custom port).

### Using Docker (manually)

Three build variants:

| Variant | Dockerfile | Base Image | Size | Use Case |
|---|---|---|---|---|
| **NVIDIA CUDA** (default) | `mythos_backend/Dockerfile` | `nvidia/cuda:12.1.1-runtime-ubuntu22.04` | ~4GB | NVIDIA GPU for local embeddings |
| **CPU only** | `mythos_backend/Dockerfile.cpu` | `python:3.11-slim` | ~150MB | No GPU, or cloud LLM providers |
| **AMD ROCm** | `mythos_backend/Dockerfile.rocm` | `rocm/pytorch:rocm6.2.3_ubuntu22.04_py3.10` | ~8GB | Linux + AMD GPU |

```powershell
git clone https://github.com/swizzcheeze/Mythos.git
cd Mythos
docker compose up -d
```

The container exposes port **8013** by default. `world_data/` is auto-created on first startup.

**Changing the port:** Set `MYTHOS_PORT` before running compose:
```powershell
$env:MYTHOS_PORT = "9090"; docker compose up -d
```

### Using Hermes Agent

Mythos integrates as a native MCP plugin. All 21 tools become available in every Hermes session.

**Step 1: Start the backend** (Docker or local, as above)

**Step 2: Register the MCP server** (run from inside the Mythos repo):

```bash
cd Mythos
echo "Y" | hermes mcp add mythos --command node --args "$(pwd)/mythos-bridge.js"
```

Use the **absolute path** to `mythos-bridge.js`. `echo "Y"` auto-accepts the tool-enable prompt.

**Step 3: Restart Hermes.** All tools are available as `mythos_*`:

- `mythos_create_world`, `mythos_list_worlds`, `mythos_select_world`, `mythos_delete_world`
- `mythos_archetype_analysis`, `mythos_multi_archetype_analysis`
- `mythos_creation_session_start/update/get/finalize/list`
- `mythos_create_lore_entry`, `mythos_list_lore_entries`, `mythos_update_lore_entry`
- `mythos_semantic_lore_search`
- `mythos_roleplay_start`, `mythos_get_inspiration`
- `mythos_wipe_lore_db`, `mythos_list_tools`, `mythos_list_archetype_styles`

Use `hermes mcp test mythos` to verify. Re-run `hermes mcp add` after pulling repo updates.

---

## ✨ Features

### 🧬 22-Archetype Character Analysis
Analyze characters through **22 storytelling frameworks** — or blend them (`Fantasy + Horror + Jungian`).

| Jungian | Disney | James Cameron | Fantasy | Gothic | Dark Gothic |
|---|---|---|---|---|---|
| Romance | Mystery | Adventure | Norse | Mythological | Greek |
| Horror | Sci-Fi | Quantum Physics | Medieval | C.S. Lewis | Stephen King |
| Alfred Hitchcock | Japanese | Korean | General | | |

Each analysis returns **primary/secondary archetypes**, confidence scores, and a **tension metric**.

### 📖 Persistent Multi-World Lore
- Per-world JSON storage — each world has its own `lore_db.json`, `sessions.json`, and FAISS vector index
- Type-safe entity CRUD: characters, worlds, factions, locations, artifacts, creatures, events, cultures, conflicts, rituals, magic systems
- Semantic search across all lore using embeddings (FAISS-backed)

### 🛠 Interactive Creation Sessions
Guided templates for 11 entity types with structured sections and creative prompts:

```
Start → Fill Sections → Preview → Save as Entity
```

### 🎭 Roleplay Mode
Generate character persona prompts from creation sessions. The persona carries values, flaws, fears, secrets, how they act under pressure — all of it.

### 🔌 Multi-LLM Support
Switch providers via env vars — no code changes:

| Provider | Config |
|----------|--------|
| **Ollama** (default) | `MYTHOS_LLM_PROVIDER=ollama` |
| **Anthropic** | `MYTHOS_LLM_PROVIDER=anthropic` |
| **OpenRouter** | `MYTHOS_LLM_PROVIDER=openrouter` |
| **Groq** | `MYTHOS_LLM_PROVIDER=groq` |
| **xAI (Grok)** | `MYTHOS_LLM_PROVIDER=xai` |
| **Google Gemini** | `MYTHOS_LLM_PROVIDER=gemini` |

Works out of the box with Ollama. For cloud providers, add API keys to `.env`.

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────┐
│  AI Client (Hermes Agent / LM Studio / etc.)        │
└──────────────────────┬──────────────────────────────┘
                       │ MCP (stdio JSON-RPC)
                       ▼
┌─────────────────────────────────────────────────────┐
│  mythos-bridge.js  (MCP Server)                     │
│  21 tool endpoints → POST /call/{toolName}          │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP localhost:8013
                       ▼
┌─────────────────────────────────────────────────────┐
│  Mythos Backend v2.0  (FastAPI)                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐        │
│  │ /entities│ │/sessions │ │  /worlds     │        │
│  │ CRUD     │ │ templates│ │  management  │        │
│  └──────────┘ └──────────┘ └──────────────┘        │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐        │
│  │/archetypes│ │  /llm   │ │ /embeddings  │        │
│  │ analysis  │ │generate │ │  + FAISS     │        │
│  └──────────┘ └──────────┘ └──────────────┘        │
└─────────────────────────────────────────────────────┘
```

**Key Design Decisions:**
- **Discriminated union entities** — `entity_type` field enforces correct type at validation time
- **Per-world isolation** — All data scoped to `(world, entity)` pairs
- **Atomic file I/O** — JSON writes use temp+rename with per-path file locks
- **Bridge dispatch** — `/call/{toolName}` maps 21 MCP tool names to typed backend handlers

---

## 🔧 Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `MYTHOS_LLM_PROVIDER` | `ollama` | LLM provider |
| `MYTHOS_OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama endpoint |
| `MYTHOS_OLLAMA_MODEL` | `llama3` | Default model |
| `MYTHOS_PORT` | `8013` | Backend port (Docker + bridge) |
| `EMBEDDING_SERVICE_URL` | `http://localhost:8002` | Embedding service |
| `COHERE_API_KEY` | None | Cohere embedding fallback |
| `OPENROUTER_API_KEY` | None | OpenRouter API key |
| `ANTHROPIC_API_KEY` | None | Anthropic API key |

Copy `.env.example` to `.env` and set keys for cloud providers. Ollama works with no keys.

---

## 🧪 Testing

```bash
# Full healthcheck (validates all 21 MCP tools + backend)
node mcp-healthcheck.js

# Python tests
python -m pytest tests/
```

---

## ⚠️ Status

Mythos v2.0 is functional but still needs more real-world testing. The core CRUD, creation sessions, archetype analysis, and roleplay mode are solid. Edge cases, concurrent access under load, and the embedding/FAISS pipeline could use more exercise. If you find something weird, issues are welcome.

---

## 📁 File Structure

| File | Purpose |
|------|---------|
| `mythos_backend/main.py` | FastAPI app, lifespan, router mounting |
| `mythos_backend/models/entities.py` | Pydantic v2 discriminated union models |
| `mythos_backend/services/world_data.py` | Per-world CRUD, atomic file I/O |
| `mythos_backend/services/embedding.py` | Embedding with retry + FAISS |
| `mythos_backend/services/archetype.py` | 22-framework semantic analysis |
| `mythos_backend/services/templates.py` | Interactive creation sessions |
| `mythos_backend/routes/bridge.py` | MCP dispatch (21 tool handlers) |
| `mythos-bridge.js` | MCP server (stdio JSON-RPC) |
| `scripts/install.sh` | One-line install (Linux/macOS/Git Bash) |
| `scripts/install.ps1` | One-line install (Windows) |
| `scripts/setup-hermes-plugin.sh` | Hermes MCP registration (Linux/macOS) |
| `scripts/setup-hermes-plugin.ps1` | Hermes MCP registration (Windows) |
| `AGENTS.md` | Agent-facing setup guide |

---

## 🙏 Acknowledgments

This project started about a year ago — built with Gemini, ChatGPT, and Claude. It went off track and had fundamental bugs. **OWL-Alpha (OpenRouter) paired with Hermes Agent** fixed it and rebuilt the backend from the ground up into v2.0.

---

## License

MIT — see [LICENSE](LICENSE)
