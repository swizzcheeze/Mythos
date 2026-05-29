# 🤖 Mythos Agent User Guide

Welcome! This guide shows you how to interact with the Mythos World Engine Agent—a creative writing and worldbuilding AI assistant integrated with LM Studio via the Model Context Protocol (MCP).

---

## 📋 Table of Contents

1. [Getting Started](#getting-started)
2. [Core Workflows](#core-workflows)
3. [Tool Categories](#tool-categories)
4. [Common Tasks](#common-tasks)
5. [Tips & Best Practices](#tips--best-practices)
6. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Prerequisites

- **LM Studio** running with a local LLM model loaded
- **Mythos backend** running (`docker compose up -d`)
- **Embedding service** running in a separate terminal (`python embedding_service.py`)
- **MCP bridge configured** in LM Studio pointing to `mythos-bridge.js`

### Health Check

Before starting, verify the system is ready:

```powershell
node .\mcp-healthcheck.js
```

Expected output shows `[OK]` for all phases. If you see warnings or errors, check:
- Backend container is running: `docker compose ps`
- Embedding service is running: Visit `http://localhost:8002/health`
- MCP protocol version is set to `2024-10-07` (not newer)
- Local LLM (Ollama) is reachable: `http://localhost:11434` and backend `/ollama/health` reports `connected: true` when using local models

---

## Core Workflows

### 1. Character Archetype Analysis

**Goal**: Understand your character through storytelling frameworks.

#### Single-Framework Analysis

Ask the agent:
> *"Analyze the character Seren Valis, a quiet scholar of forbidden runes, through the Gothic framework."*

**What happens:**
- Agent calls `mythos_archetype_analysis`
- Returns primary/secondary archetypes with confidence scores
- Tension score shows internal character conflict potential
- `low_signal_fallback` flag indicates if result is heuristic-based

**Example response:**
```
Primary Archetype: The Hermit (confidence: 0.687)
Secondary Archetype: The Shadow (confidence: 0.520)
Tension Score: 0.167 (moderate internal conflict)
```

#### Multi-Framework Composite Analysis

Ask the agent:
> *"Blend Fantasy, Horror, and Jungian archetypes for a character who's a cursed mage caught between worlds."*

**What happens:**
- Agent calls `mythos_multi_archetype_analysis`
- Returns archetypes from **each framework** separately
- Shows composite summary and synthesis suggestion
- Composite tension metric measures diversity across frameworks

**Use this for:**
- Cross-genre character development
- Finding tension between conflicting archetypes
- Understanding multi-layered personalities

---

### 2. Building a World with Persistent Lore

**Goal**: Create and manage a cohesive fictional world with searchable knowledge.

#### Step 1: Create or Select a World

Ask the agent:
> *"Create a new world called 'Eldoria' for my fantasy novel."*

**What happens:**
- Agent calls `mythos_create_world` with your world name
- World is isolated with its own lore database and vector index
- All subsequent work stays in this world unless you switch

#### Step 2: Add Lore Entries

Ask the agent:
> *"Add this lore entry to Eldoria: topic='The Sundering', content='A cataclysmic event 500 years ago that split the continent...'"*

**What happens:**
- Agent calls `mythos_create_lore_entry`
- Entry is saved with a unique ID and timestamps
- Automatically embedded using semantic search model
- Added to FAISS index for fast retrieval

**Tags optional:**
```
topic: "The Sundering"
content: "A cataclysmic event..."
tags: ["history", "magic", "apocalyptic"]
```

#### Step 3: Search Your Lore Semantically

Ask the agent:
> *"Search my Eldoria lore: find entries about 'magical catastrophes and continental division'."*

**What happens:**
- Agent calls `mythos_semantic_lore_search`
- Query is embedded and compared to all lore entries
- Returns top results ranked by semantic similarity (0-1 score)
- Shows matching entries even if keywords don't match exactly

**Example results:**
```
Query: "magical catastrophes and continental division"
Found 3 results:

1. The Sundering (similarity: 0.682)
   Preview: "A cataclysmic event 500 years ago that split..."

2. Age of Ruin (similarity: 0.541)
   Preview: "When the mages attempted to reshape reality..."

3. Continent Wars (similarity: 0.398)
   Preview: "Ancient territorial conflicts between kingdoms..."
```

---

### 3. Interactive Character Creation Sessions

**Goal**: Build characters step-by-step with persistent templates.

#### Start a Session

Ask the agent:
> *"Start a character creation session for my fantasy world."*

**What happens:**
- Agent calls `mythos_creation_session_start`
- Returns a session ID and template structure
- Session is saved (can be resumed later)

#### Update Session Fields

Ask the agent:
> *"Update my character session: set the name to 'Aria', background to 'Orphaned princess with hidden magic', and personality to 'Reserved but determined'."*

**What happens:**
- Agent calls `mythos_creation_session_update`
- Fills in provided fields
- Returns progress (how many fields are complete)

#### Preview Before Committing

Ask the agent:
> *"Finalize and preview my character session without saving."*

**What happens:**
- Agent calls `mythos_creation_session_finalize`
- Shows complete character preview
- You can review before committing

#### Commit to Lore

Ask the agent:
> *"Save this character as a lore entry called 'Character Profile: Aria'."*

**What happens:**
- Agent calls `mythos_create_lore_entry` with the finalized character data
- Character is now part of your world's lore
- Searchable and indexed for semantic queries

Behind the scenes, creation sessions can go through one or more internal "draft → critique → revise" passes using your configured LLMs (e.g., `llama3`). This agentic loop is stateful and checkpointed to disk so that even long-running sessions remain consistent across restarts.

---

### 4. Creative Constraint Generator

**Goal**: Break writer's block with thematic prompts.

Ask the agent:
> *"Give me a creative prompt themed around 'Transformation' in the Horror genre."*

**What happens:**
- Agent calls `mythos_get_inspiration`
- Returns thematic constraint tailored to your genre
- Designed to spark creative ideas

**Constraint themes:**
- **Sacrifice**: What must be given up?
- **Transformation**: What changes fundamentally?
- **Time**: How does history or fate intervene?

---

### 5. Roleplay Mode

**Goal**: Bring your character to life through interactive roleplay.

#### Start Roleplay

Ask the agent:
> *"Let me roleplay as my character Seren Valis, the scholar of forbidden runes."*

Or reference an existing session:
> *"Start roleplay with my character session [SESSION_ID]."*

**What happens:**
- Agent calls `mythos_roleplay_start`
- Returns a persona prompt with:
  - Character name, style, traits, background
  - System instructions for in-character responses
- Agent adopts the character's voice for subsequent messages

#### Conduct the Roleplay

**In character, the agent responds to your prompts.** Examples:

> *"Seren, a dangerous artifact has appeared in the city. What do you do?"*

Agent (as Seren):
> *"My hand trembles. The rune patterns match those in the forbidden texts... patterns I thought were lost. I must examine this carefully, away from prying eyes. Come, we need to reach my study before the city watch arrives."*

#### Exit Roleplay

Ask the agent:
> *"End roleplay mode."*

The agent returns to its normal assistant voice.

Internally, roleplay persona prompts are derived from the same structured session data used for creation workflows, ensuring that the in-character voice reflects the traits and background you developed.

---

## Tool Categories

### 🧬 Character Analysis Tools

| Tool | Purpose | Input | Output |
|------|---------|-------|--------|
| `mythos_archetype_analysis` | Single-framework character analysis | name, description, framework | primary/secondary archetype, confidence, tension |
| `mythos_multi_archetype_analysis` | Composite framework blending | name, description, styles (e.g., "Fantasy+Horror") | per-framework archetypes, composite tension |
| `mythos_roleplay_start` | Generate persona for roleplay | character_name, bio, style OR session_id | persona, system instructions |

### 📖 Lore & World Tools

| Tool | Purpose | Input | Output |
|------|---------|-------|--------|
| `mythos_create_lore_entry` | Add entry to world lore | topic, content, tags (optional), world | entry_id, embedded status |
| `mythos_update_lore_entry` | Update existing entry | id, updates, world | updated entry |
| `mythos_list_lore_entries` | Search/list entries by tags | tags, world | matching entries |
| `mythos_semantic_lore_search` | Search by meaning | query, top_k, world | ranked results with similarity scores |
| `mythos_create_world` | Create isolated world | name | world_name, status |
| `mythos_select_world` | Switch active world | name | active_world_name |
| `mythos_list_worlds` | See all worlds | (none) | world names, entry counts |
| `mythos_wipe_lore_db` | Delete all world lore | world (optional) | confirmation |

### 🛠️ Creation Session Tools

| Tool | Purpose | Input | Output |
|------|---------|-------|--------|
| `mythos_creation_session_start` | Begin template workflow | template_type (character/location/faction/etc.), world | session_id, template fields |
| `mythos_creation_session_update` | Fill session fields | session_id, field updates, world | progress (filled/total fields) |
| `mythos_creation_session_get` | View session state | session_id, world | current field values |
| `mythos_creation_session_finalize` | Preview before commit | session_id, world | complete preview |
| `mythos_creation_session_list` | See all sessions | world | sessions with progress |

### 💡 Utility Tools

| Tool | Purpose |
|------|---------|
| `mythos_get_inspiration` | Creative constraint prompts |
| `mythos_creation_mode` | One-shot static template guide |
| `mythos_list_archetype_styles` | Available frameworks (22 total) |
| `mythos_list_tools` | Complete tool catalog |
| `mythos_list_lore_entries` | Browse all lore entries |

---

## LLM Configuration (Ollama)

When using local models via Ollama, the backend and internal agentic loop use a simple configuration layer driven by environment variables. These are typically set in `docker-compose.yml` or your shell before starting the backend.

| Variable | Scope | Purpose | Default |
|----------|-------|---------|---------|
| `MYTHOS_OLLAMA_BASE_URL` | Backend | Base URL for Ollama HTTP API | `http://host.docker.internal:11434` |
| `MYTHOS_GENERATOR_MODEL` | Backend | Model for drafting content (generator agent) | `llama3` |
| `MYTHOS_CRITIC_MODEL` | Backend | Model for critique/feedback (critic agent) | `llama3` |

**Common patterns:**

- To switch both generator and critic to `mistral`:

  ```powershell
  $env:MYTHOS_GENERATOR_MODEL = 'mistral'
  $env:MYTHOS_CRITIC_MODEL    = 'mistral'
  docker compose up -d
  ```

- To keep `llama3` as the main drafting model but use a more conservative critic:

  ```powershell
  $env:MYTHOS_GENERATOR_MODEL = 'llama3'
  $env:MYTHOS_CRITIC_MODEL    = 'mistral'
  docker compose up -d
  ```

You can verify connectivity and active models at any time via:

```powershell
Invoke-WebRequest -Uri "http://localhost:8001/ollama/health"
Invoke-WebRequest -Uri "http://localhost:8001/ollama/models"
```

---

## Common Tasks

### Task 1: Design a Multi-Genre Protagonist

```
1. Ask: "Start a character creation session for a sci-fi world."
2. Ask: "Analyze this character through Fantasy+Sci-Fi+Horror."
3. Agent shows composite archetypes.
4. Ask: "Update my session: name='Kael', background='Abandoned on an alien world'..."
5. Ask: "Finalize and preview."
6. Ask: "Save as lore in my world."
```

### Task 2: Build a Faction with Consistent Lore

```
1. Ask: "Create a world for my tabletop campaign."
2. Ask: "Start a creation session for 'faction'."
3. Ask: "Update session: name='The Obsidian Order', purpose='Seek forbidden knowledge'..."
4. Ask: "Add lore entries about the faction's history, beliefs, rituals."
5. Ask: "Search my lore: 'secret magical societies'."
   → Semantic search shows related entries.
```

### Task 3: Explore Character Tension Through Archetypes

```
1. Ask: "Analyze my character through Jungian framework."
   → Returns primary/secondary with tension_score.
2. If tension_score is low (character seems flat):
   - Try a different framework.
   - Or ask: "What archetypes would create more internal conflict for this character?"
3. Use tension_score to plan character arcs (high tension = strong character growth potential).
```

### Task 4: Find Inspiration When Stuck

```
1. Ask: "Give me a 'Sacrifice' constraint prompt for Gothic genre."
2. Agent returns a thematic prompt.
3. Use it to spark a new scene or plot twist.
4. Ask: "Add this inspired idea to my lore."
```

### Task 5: Roleplay a Complex Character

```
1. Ask: "Start roleplay as my character [name]."
2. Agent generates persona from your character data.
3. Ask in-character questions: "What do you fear most?"
4. Agent responds in character.
5. Collect dialogue and motivations for your writing.
```

---

## Tips & Best Practices

### ✅ Do

- **Be specific with descriptions.** More details = better semantic matching and archetype analysis.
  - ❌ *"Analyze a warrior character"*
  - ✅ *"Analyze Kael, a battle-scarred warrior haunted by a massacre he couldn't prevent, seeking redemption through self-sacrifice."*

- **Use multiple frameworks** to discover character depth.
  - Try 2-3 different blended frameworks to see how archetypes shift.
  - High composite tension often signals interesting multi-layered characters.

- **Tag your lore entries** for easy organization.
  - Tags help you filter later and add semantic context.
  - Examples: `["history", "magic", "characters", "conflicts"]`

- **Review semantic search results carefully.**
  - Similarity scores (0-1) show relevance strength.
  - Scores above 0.5 are typically good matches.
  - Low-scoring results might inspire unexpected connections.

- **Use sessions for complex templates.**
  - Creation sessions are meant for iterative workflows.
  - Start a session, step away, come back later and resume.
  - Preview before committing to avoid mistakes.

- **Combine tools creatively.**
  - Create a character → analyze it → roleplay as it → save to lore.
  - Search lore → inspire new characters → add them back.
  - Use multi-framework analysis to find contradictions in your world's factions.

### ❌ Don't

- **Don't expect perfect matches from semantic search.**
  - Embeddings work on meaning, not keywords.
  - If you need exact keyword matches, ask the agent to list lore entries instead.

- **Don't wipe lore unless you're sure.**
  - `mythos_wipe_lore_db` is irreversible.
  - Always ask to list entries first if unsure.

- **Don't create multiple worlds without purpose.**
  - Worlds are isolated. If you want cross-world lore, keep it in one world.
  - Use tags and semantic search to organize within a world.

- **Don't skip the preview step.**
  - Always finalize and preview a session before saving.
  - Catches typos and incomplete fields early.

- **Don't rely solely on frameworks.**
  - Archetypes are tools for inspiration, not prescriptive.
  - Use them to challenge expectations, not limit creativity.

---

## Troubleshooting

### Issue: Agent says "Tool not found" or "connection error"

**Solution:**
1. Run the healthcheck: `node .\mcp-healthcheck.js`
2. Check backend is running: `docker compose ps`
3. Check embedding service is running: Visit `http://localhost:8002/health`
4. Verify LM Studio MCP protocol is set to `2024-10-07`

### Issue: Semantic search returns no results

**Possible causes:**
- World has no lore entries yet. Create some first.
- Query is too specific or uses jargon not in your lore.
- Embedding service is down.

**Solutions:**
1. Ask agent to list all entries in the world first.
2. Try a broader query: Instead of "ancient prophecies of the Sundering", try "ancient magic prophecies".
3. Check embedding service: `curl http://localhost:8002/health`

### Issue: Archetype analysis returns "low_signal_fallback: true"

**What it means:** Your character description was too vague for semantic scoring. Result is randomly selected.

**Solution:** Provide more specific details about the character:
- What are their conflicts?
- What do they fear or desire?
- How do they interact with others?

More context = better archetype matches.

### Issue: Character session keeps losing data

**Possible causes:**
- Session is not being saved (app crashed).
- World was switched mid-session.
- Incorrect session_id used.

**Solutions:**
1. Always get session_id from `creation_session_start` response.
2. Don't switch worlds mid-session.
3. Ask agent: "What is my current session_id?"

### Issue: Embedding service takes a long time or crashes

**Possible causes:**
- Model is loading for the first time (normal, ~2-5 seconds).
- System running out of memory.
- Service not responding to backend calls.

**Solutions:**
1. Restart the embedding service: Stop and run `python embedding_service.py` again.
2. Check system memory: Task Manager → Performance.
3. Run healthcheck to verify connection: `node .\mcp-healthcheck.js`

### Issue: "host.docker.internal not found" error

**What it means:** Docker container can't reach the host embedding service.

**Solution:**
1. Verify extra_hosts in `docker-compose.yml`:
   ```yaml
   extra_hosts:
     - "host.docker.internal:host-gateway"
   ```
2. Restart container: `docker compose restart mythos_backend`
3. Or run embedding service inside a container (see `docker-compose.yml` for notes).

---

## Quick Reference

### Fastest Character Analysis Flow

```
User: "Analyze [character name] through [framework]."
User: "Now blend [framework1]+[framework2]+[framework3] for the same character."
User: "What archetype combination would create maximum tension?"
```

### Fastest Lore Building Flow

```
User: "Create world [world_name]."
User: "Add lore: topic='[title]', content='[description]', tags='[tags]'."
User: "Add more entries..."
User: "Search lore: '[thematic query]'."
```

### Fastest Creative Workflow

```
User: "Inspire me with a '[constraint theme]' prompt for [genre]."
User: "Start a character session inspired by that prompt."
User: "Update my session: [field updates]."
User: "Roleplay as this character."
```

---

## Next Steps

- **Explore frameworks:** Ask "List all archetype frameworks."
- **Experiment with blends:** Try unusual combinations (e.g., "Sci-Fi + Greek + Romance").
- **Build complex worlds:** Use tags and semantic search to organize large lore databases.
- **Roleplay deeply:** Use character sessions as basis for rich roleplay scenarios.
- **Iterate creatively:** Use archetype feedback to refine character designs.

Happy worldbuilding! 🌍✨

---

**Need help?** Check [README.md](README.md), [INSTALLATION.md](INSTALLATION.md), or the troubleshooting section above.
