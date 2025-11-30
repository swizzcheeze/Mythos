# 🌟 Mythos World Engine

> **AI-Powered Creative Writing & Worldbuilding Toolkit**

Transform your storytelling with composite archetype synthesis, persistent multi-world lore, interactive creation sessions, and creative constraints—accessible through LM Studio (MCP).

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![MCP](https://img.shields.io/badge/MCP-2024--10--07-green.svg)](https://modelcontextprotocol.io/)
[![CI Healthcheck](https://github.com/swizzcheeze/Mythos/actions/workflows/ci.yml/badge.svg)](https://github.com/swizzcheeze/Mythos/actions/workflows/ci.yml)

---

## ✨ Features

### 🧬 Multi-Framework & Blended Character Analysis
Analyze characters through **22 storytelling frameworks** or blend several (e.g. `Fantasy + Horror + Jungian`). Frameworks: Jungian, Disney, James Cameron, General, Fantasy, Gothic, Dark Gothic, Romance, Mystery, Adventure, Norse, Mythological, Greek, Horror, Sci-Fi, Quantum Physics, Medieval, C.S. Lewis, Stephen King, Alfred Hitchcock, Japanese, Korean.

Now powered by lightweight semantic scoring (token + synonym overlap) for more meaningful archetype selection with confidence and tension metrics. Random fallback only used when semantic signal is weak (flagged via `low_signal_fallback`).

Use `mythos_multi_archetype_analysis` for composite synthesis with per-framework confidence and a diversity tension metric.

### 📖 Persistent Lore Database & Multi-World Workspaces
Per-world JSON storage (default + custom worlds). Tools to create/select/list/wipe worlds. Each world has independent `lore_db.json` and `sessions.json`.

### 🛠 Interactive Creation Sessions
Iterative, persistent templates (character, location, faction, magic_system, creature, artifact, event, culture, conflict, ritual, world). Start → update fields → preview (finalize) → optionally commit as lore.

### 💡 Creative Constraint Generator
Break writer’s block with thematic prompts (Sacrifice, Transformation, Time) styled to any genre.

### 🔌 Seamless LM Studio Integration
MCP protocol (2024-10-07), structured JSON-RPC, robust error handling, healthcheck script.

---

## 🚀 Quick Demo (Composite Blend)

```jsonc
// Composite multi-framework analysis
{
  "character_name": "Aria Nyx",
  "description": "A soulbound mage haunted by ancestral echoes, navigating collapsing timelines.",
  "styles": "Fantasy + Horror + Jungian"
}
```

Returns primary/secondary archetypes from each framework plus a synthesis summary.

---

## 🛠️ Tool Highlights

| Tool | Purpose |
|------|---------|
| `mythos_archetype_analysis` | Single-framework character analysis |
| `mythos_multi_archetype_analysis` | Composite blended archetype synthesis |
| `mythos_creation_mode` | One-shot static template guide |
| `mythos_creation_session_start/update/get/finalize/list` | Interactive persistent creation workflow |
| `mythos_create_lore_entry` / `mythos_update_lore_entry` | Add & edit lore |
| `mythos_list_lore_entries` | Search & tag filter lore entries |
| `mythos_wipe_lore_db` | Irreversibly wipe active world lore |
| `mythos_create_world` / `mythos_select_world` / `mythos_list_worlds` | Multi-world management |
| `mythos_get_inspiration` | Thematic creative constraints |
| `mythos_list_archetype_styles` | Enumerate frameworks |
| `mythos_list_tools` | Human-readable catalog |
| `mythos_roleplay_start` | Generate a persona prompt for in-character roleplay |

---

## 📦 Installation (Summary)
See [INSTALLATION.md](INSTALLATION.md) for full setup.

```powershell
# Start backend (build + run detached)
docker compose up --build -d

# Run healthcheck (backend probe + MCP negotiation + sample tool calls)
node .\mcp-healthcheck.js
```

Configure LM Studio MCP to point at `mythos-bridge.js` and set `MYTHOS_MCP_PROTOCOL=2024-10-07`.

Path examples (adjust for your system):
| OS | Example Command Args |
|----|----------------------|
| Windows | `"C:\\path\\to\\mythos\\mythos-bridge.js"` |
| macOS | `/Users/you/path/mythos/mythos-bridge.js` |
| Linux | `/home/you/mythos/mythos-bridge.js` |

If using LM Studio config JSON, replace `<drive>` placeholder with your actual absolute path. Relative paths may fail if LM Studio launches from a different working directory.

---

## 🩺 Healthcheck & Reliability
`mcp-healthcheck.js` now performs phased validation with timeouts and early aborts:

1. Backend `/healthz` probe (fails fast if container not running)
2. MCP `initialize` (verifies protocol version `2024-10-07` & bridge identity)
3. `tools/list` (ensures tool schema synchronization)
4. Sample `tools/call` sequence:
  - `mythos_archetype_analysis` (checks semantic fields: `confidence_primary`, `confidence_secondary`, `tension_score`)
  - `mythos_multi_archetype_analysis` (verifies composite fields: `analyses`, `composite_tension_metric`)
  - Creation session lifecycle: start → update → finalize → list
  - Roleplay: generate persona instructions from the started character session

Timeouts (defaults):
```
INIT_TIMEOUT_MS = 4000
TOOLS_TIMEOUT_MS = 4000
CALLS_TIMEOUT_MS = 8000
```

Early abort triggers:
- 404 on any tool endpoint (schema mismatch or backend not updated)
- Timeout expiry per phase

Result codes:
- Exit `0` = all phases passed
- Non-zero = phase or endpoint failure (see console diagnostics)

Use this script in CI or pre-commit hooks to guard against tool drift or backend startup regressions.

---

## 🎯 Use Cases
- Writers: Layered archetype tension maps for protagonists
- Game Designers: World-per-project isolated lore + sessions
- Screenwriters: Cross-genre archetype blending (e.g. Sci-Fi Horror)
- RPG Masters: Rapid ritual, faction, creature templates
- Worldbuilders: Parallel universes with independent persistent data

---

## 🏗️ Architecture

```
LM Studio → MCP stdio → mythos-bridge.js → HTTP → FastAPI → world_data JSON
```

**Components**
- `mythos-bridge.js` – MCP JSON-RPC bridge
- `mythos_backend.py` – FastAPI service (analysis, sessions, worlds, lore)
- `world_data/lore_db.json` – Default world lore
- `world_data/sessions.json` – Default world creation sessions
- `world_data/worlds/<name>/lore_db.json` – Per-world lore
- `world_data/worlds/<name>/sessions.json` – Per-world creation sessions
- `mcp-healthcheck.js` – Protocol & tool validation

```
mythos/
├── mythos-bridge.js
├── mcp-healthcheck.js
├── docker-compose.yml
├── mythos_backend/
│   ├── Dockerfile
│   ├── mythos_backend.py
│   └── requirements.txt
└── world_data/
    ├── lore_db.json
    ├── sessions.json
    └── worlds/
        └── <world>/
            ├── lore_db.json
            └── sessions.json
```

---

## 📖 Documentation
- [Installation Guide](INSTALLATION.md)
- Roleplay quick test (HTTP):
  ```powershell
  Invoke-WebRequest -Uri http://localhost:8001/call/mythos_roleplay_start -Method POST -ContentType 'application/json' -Body '{"character_name":"Seren Valis","bio":"Quiet scholar of forbidden runes.","style":"Fantasy"}'
  ```
- FastAPI docs: `http://localhost:8001/docs` (running)
- Agent / development patterns: `.github/copilot-instructions.md`

---

## 🎭 Roleplay Usage

- Purpose: Generate a persona prompt and instructions to roleplay as your character.

- HTTP (backend directly):
  ```powershell
  # From a character session
  $body = @{ session_id = 'YOUR_SESSION_ID' } | ConvertTo-Json
  Invoke-RestMethod -Uri "http://localhost:8001/call/mythos_roleplay_start" -Method Post -Body $body -ContentType "application/json"

  # Without a session (name + bio)
  $body = @{ character_name = 'Seren Valis'; bio = 'Quiet scholar of forbidden runes.'; style = 'Fantasy' } | ConvertTo-Json
  Invoke-RestMethod -Uri "http://localhost:8001/call/mythos_roleplay_start" -Method Post -Body $body -ContentType "application/json"
  ```

- MCP Bridge (LM Studio):
  - Call the tool `mythos_roleplay_start` with either:
    - `session_id` from a `character` creation session, or
    - `character_name` + optional `bio` and `style`.
  - The bridge shows a friendly formatted view by default; set `MYTHOS_SHOW_JSON=1` to receive raw JSON.

- Output structure:
  - `persona`: `{ name, style, traits[], background[] }`
  - `instructions`: prompt text suitable as a system/assistant instruction

Tips
- Keep responses concise by default; ask for longer outputs when needed.
- Adjust `style` (e.g., Noir, Sci-Fi) for tone changes.

---

## 🧪 CI Notes

- Pipeline Focus: Run `mcp-healthcheck.js` after starting the backend to validate MCP negotiation and core tool calls.
- Backend Start: Prefer `uvicorn mythos_backend:app --host 127.0.0.1 --port 8001` with a short `/healthz` readiness loop before healthcheck.
- Env Toggles (Bridge):
  - `MYTHOS_MCP_PROTOCOL=2024-10-07` (LM Studio rejects newer versions)
  - `MYTHOS_SHOW_JSON=1` (force raw JSON for reliable parsing)
  - `MYTHOS_COLOR=0` (disable ANSI for clean logs)
- Early Abort: Treat the first HTTP 404 from any `tools/call` as a schema drift or missing endpoint.
- Common Failures:
  - Backend not reachable → ensure docker service up and port 8001 mapped.
  - Tool validation 422 → align bridge input schemas with backend Pydantic required fields.
  - Protocol mismatch → enforce `2024-10-07`.
- Artifacts: Optionally archive healthcheck console output and backend logs to aid debugging.

---

## 🔄 Workflow Examples
**Interactive Creation Session**
1. `mythos_creation_session_start` (template_type="character")
2. `mythos_creation_session_update` (fill sections incrementally)
3. `mythos_creation_session_finalize` (preview without saving)
4. `mythos_create_lore_entry` (commit when ready)

**Multi-World Switch**
**Semantic Archetype Analysis**
```jsonc
{
  "character_name": "Seren Valis",
  "description": "A scholar of forbidden runes whose quiet compassion battles a growing cosmic dread.",
  "style": "Gothic"
}
```
Response now includes:
- `confidence_primary` / `confidence_secondary`: normalized semantic scores
- `tension_score`: difference indicating internal friction potential
- `low_signal_fallback`: true if random heuristic used (weak semantic match)

1. `mythos_create_world` (name="Eldoria")
2. `mythos_select_world` (name="Eldoria")
3. Build lore & sessions independently

---

## 🧪 Semantic Metrics Explained
- `confidence_primary` / `confidence_secondary`: Overlap-based normalized scores; higher = stronger textual alignment.
- `tension_score`: Absolute difference between confidences; higher = more internal conflict potential.
- `low_signal_fallback`: True when description provides insufficient semantic signal (heuristic threshold).
- `composite_tension_metric`: Variance of primary scores across blended frameworks—measures diversity of driving forces.

---

## 🌐 GitHub Repository
Source hosted at: https://github.com/swizzcheeze/Mythos

Suggested initial commit & push (if not already versioned):
```powershell
git init
git add .
git commit -m "feat: initial public release with semantic scoring & robust healthcheck"
git branch -M main
git remote add origin https://github.com/swizzcheeze/Mythos.git
git push -u origin main
```

For ongoing changes use conventional commits (e.g., `feat:`, `fix:`, `docs:`).

---

## 🔒 Private Repository Notice
If this repository is now set to Private:
- Access is restricted to approved collaborators; submit access requests via issue or direct contact.
- Generated lore and session JSON files may include internally sensitive creative IP—do not redistribute externally.
- Forking: Create private forks only; public forks are disabled once visibility changes.
- CI & Tokens: Ensure any GitHub Actions secrets have least-privilege (`repo` scope PAT if required) and rotate on collaborator changes.
- External Sharing: Share excerpts (e.g., archetype metrics) only after manual review to avoid leaking full world data context.
- Licensing: MIT still applies internally; outbound publication of code requires maintainer approval to prevent inadvertent exposure of narrative assets.
- Backups: Use encrypted storage for world_data exports when archiving.

To revert to public visibility (if needed): use GitHub Settings → Change visibility or:
```powershell
gh repo edit swizzcheeze/Mythos --visibility public --accept-visibility-change-consequences
```

---

---

## 🤝 Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md) for workflow & standards.

Ideas & PRs welcome:
- Enhanced semantic NLP (embeddings, clustering)
- Vector lore search & retrieval Augmented Generation
- Export pipelines (Markdown world bible, PDF anthology)
- Additional cultural / genre frameworks
- Session advisory / auto-fill heuristics

---

## 📜 License
MIT – see [LICENSE](LICENSE)

---

## 🙏 Acknowledgments
Powered by FastAPI, Model Context Protocol, and narrative design traditions.

---

## 📞 Support
- Health: `node .\mcp-healthcheck.js`
- Backend logs: `docker compose logs -f mythos-backend`
- Protocol mismatch: ensure `MYTHOS_MCP_PROTOCOL=2024-10-07`
- Stalled analysis: check semantic threshold / description richness

---

**Happy Worldbuilding!** 🌍✨

