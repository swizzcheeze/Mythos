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

## 🚀 Quick Start

Two ways to get running. Pick one.

---

### Option A — One-Line Install (Development / Local Python)

Runs locally with Python. No Docker. Best for development or if you don't need GPU embeddings.

```bash
# Linux / macOS / Git Bash
curl -fsSL https://raw.githubusercontent.com/swizzcheeze/Mythos/main/scripts/install.sh | bash

# Windows PowerShell
iex (irm https://raw.githubusercontent.com/swizzcheeze/Mythos/main/scripts/install.ps1)
```

This clones the repo, creates a venv, installs dependencies, and starts the backend on port 8013.

---

### Option B — Docker (Recommended for Production)

Runs in an isolated container. NVIDIA CUDA by default, CPU and AMD ROCm variants available.

```powershell
git clone https://github.com/swizzcheeze/Mythos.git
cd Mythos
docker compose up -d
```

That's it. The container exposes port 8013 and `world_data/` is auto-created on first startup.

**Docker variants** (edit `docker-compose.yml` → `dockerfile` line):

| Variant | Dockerfile | Size | Use Case |
|---|---|---|---|
| **NVIDIA CUDA** (default) | `mythos_backend/Dockerfile` | ~4GB | NVIDIA GPU for local embeddings |
| **CPU only** | `mythos_backend/Dockerfile.cpu` | ~150MB | No GPU, or cloud LLM providers |
| **AMD ROCm** | `mythos_backend/Dockerfile.rocm` | ~8GB | Linux + AMD GPU |

For CPU/ROCm, comment out the `devices` block under `deploy.resources.reservations`.

**Change the port:**
```powershell
$env:MYTHOS_PORT = "9090"; docker compose up -d
```

---

### For Both Options: Verify Backend

```bash
curl http://localhost:8013/healthz
# Should return: {"status":"ok","version":"2.0.0"}
```

---

### Register as a Hermes Agent Plugin (Required for Either Option)

Mythos integrates natively with **Hermes Agent** by Nous Research as an MCP plugin. All 21 `mythos_*` tools become available in every Hermes session — worlds, lore, archetype analysis, roleplay personas.

**Hermes Agent** is an open-source AI agent framework by [Nous Research](https://github.com/NousResearch/hermes-agent). It runs in your terminal, Discord, Telegram, and 10+ other platforms. If you don't have it installed yet, check out the [Hermes Agent docs](https://hermes-agent.nousresearch.com/docs) or join the [Nous Research Discord](https://discord.gg/nousresearch) for support.

After the backend is running, register the MCP bridge:

**Step 1** — Run the setup script from inside the Mythos repo:

```powershell
cd Mythos
.\scripts\setup-hermes-plugin.ps1        # Windows
bash scripts/setup-hermes-plugin.sh      # Linux/macOS
```

This checks dependencies, starts the backend (if not running), and registers the bridge.

**Or do it manually:**

```bash
cd Mythos
echo "Y" | hermes mcp add mythos --command node --args "$(pwd)/mythos-bridge.js"
```

**Step 2** — Restart Hermes Agent. All `mythos_*` tools are now available.

**Step 3** — Verify:

```
hermes mcp test mythos
```

---

## ⚡ What Is This?

Mythos is a **worldbuilding co-pilot** for creative writers, tabletop game masters, and worldbuilders. It persists your fictional worlds, characters, factions, and lore in a searchable knowledge base — then lets you analyze, create, and roleplay through any MCP-compatible AI client (Hermes Agent, LM Studio, etc.).

**v2.0 Rebuild**: The entire backend was rewritten to fix a critical entity type discrimination bug (characters saved as worlds, personas as lore, etc.), add per-world data isolation, and follow modern FastAPI patterns. The bridge layer has 21 validated tool endpoints. It integrates natively as a Hermes Agent MCP plugin.

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
Guided templates for 11 entity types:

```
Start → Fill Sections → Preview → Save as Entity
```

### 🎭 Roleplay Mode
Generate character persona prompts from creation sessions. The persona carries values, flaws, fears, secrets — all of it.

### 🔌 Multi-LLM Support
Works out of the box with Ollama. For cloud providers, add API keys to `.env`.

| Provider | Config |
|----------|--------|
| **Ollama** (default) | `MYTHOS_LLM_PROVIDER=ollama` |
| **Anthropic** | `MYTHOS_LLM_PROVIDER=anthropic` |
| **OpenRouter** | `MYTHOS_LLM_PROVIDER=openrouter` |
| **Groq** | `MYTHOS_LLM_PROVIDER=groq` |
| **xAI (Grok)** | `MYTHOS_LLM_PROVIDER=xai` |
| **Google Gemini** | `MYTHOS_LLM_PROVIDER=gemini` |

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
│  └──────────┘ └──────────┘ └──────────────┘        │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐        │
│  │/archetypes│ │  /llm   │ │ /embeddings  │        │
│  └──────────┘ └──────────┘ └──────────────┘        │
└─────────────────────────────────────────────────────┘
```

**Design decisions:** discriminated union entities, per-world isolation, atomic file I/O, bridge dispatch.

---

## 🔧 Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `MYTHOS_PORT` | `8013` | Backend port (Docker + bridge) |
| `MYTHOS_LLM_PROVIDER` | `ollama` | LLM provider |
| `MYTHOS_OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama endpoint |
| `MYTHOS_OLLAMA_MODEL` | `llama3` | Default model |
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

Mythos v2.0 is functional but still needs more real-world testing. Core CRUD, creation sessions, archetype analysis, and roleplay mode are solid. Edge cases, concurrent access under load, and the embedding/FAISS pipeline could use more exercise. Issues welcome.

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
| `scripts/install.sh` | One-line install — Linux/macOS/Git Bash |
| `scripts/install.ps1` | One-line install — Windows |
| `scripts/setup-hermes-plugin.sh` | Hermes MCP registration — Linux/macOS |
| `scripts/setup-hermes-plugin.ps1` | Hermes MCP registration — Windows |
| `AGENTS.md` | Agent-facing setup guide |

---

## Acknowledgments

This project was built in close collaboration with **OWL-Alpha** (OpenRouter) and **Hermes Agent** by [Nous Research](https://github.com/NousResearch/hermes-agent). The v2.0 architectural rewrite — fixing the core discrimination bug, adding per-world isolation, building the MCP bridge, and productionizing the entire stack — was a joint effort across multiple sessions and model providers.

Without Nous Research and the Hermes Agent ecosystem, this project would not exist as it does today.

- [Hermes Agent on GitHub](https://github.com/NousResearch/hermes-agent)
- [Hermes Agent Documentation](https://hermes-agent.nousresearch.com/docs)
- [Nous Research Discord](https://discord.gg/nousresearch)

---

## License

MIT — see [LICENSE](LICENSE)
