# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]
- **New Feature: Multi-Provider LLM Support (6 Providers)** - Unified abstraction layer supporting 6 LLM providers with zero-rebuild switching. All provider SDKs pre-installed in Docker image.
  - **Supported Providers**: Anthropic Claude, OpenRouter (200+ models), Groq (ultra-fast), xAI (Grok), Google Gemini, Ollama (local)
  - **Zero-Rebuild Switching**: Change `MYTHOS_LLM_PROVIDER` environment variable and restart - no `docker compose build` needed!
  - **Abstraction Functions**: `_get_llm_for_generation()`, `_get_llm_for_critique()`, `_invoke_llm()` work with all providers
  - **Environment Variables**: 
    - `MYTHOS_LLM_PROVIDER`: `ollama`, `anthropic`, `openrouter`, `groq`, `xai`, `gemini`
    - API keys: `ANTHROPIC_API_KEY`, `OPENROUTER_API_KEY`, `GROQ_API_KEY`, `XAI_API_KEY`, `GEMINI_API_KEY`
    - Model selection per provider: `MYTHOS_ANTHROPIC_MODEL`, `MYTHOS_OPENROUTER_MODEL`, etc.
  - **Updated Endpoints**: `/ollama/health`, `/ollama/models`, `/ollama/generate` support all 6 providers
  - **Pre-installed Packages**: `anthropic`, `openai` (for OpenRouter/xAI), `groq`, `google-generativeai`
  - **Documentation**: Comprehensive `FRONTIER_MODELS.md` with all providers, `QUICKREF_FRONTIER.md`, `.env.example`
  - **Testing**: `test_frontier_models.py` supports all providers
- New Feature: `mythos_roleplay_start` endpoint and bridge tool to generate persona prompts from character sessions or provided fields. Healthcheck invokes it after session start.
- Multi-world support (`mythos_create_world`, `mythos_select_world`, `mythos_list_worlds`, `mythos_wipe_lore_db`).
- Interactive creation sessions (start / update / get / finalize / list) with persistent JSON storage per world.
- Composite multi-archetype blending (`mythos_multi_archetype_analysis`) with diversity tension metric.
- Lightweight semantic scoring for single and multi-framework analyses (confidence + tension + fallback indicators).
- Expanded frameworks to 22 (Jungian, Disney, James Cameron, General, Fantasy, Gothic, Dark Gothic, Romance, Mystery, Adventure, Norse, Mythological, Greek, Horror, Sci-Fi, Quantum Physics, Medieval, C.S. Lewis, Stephen King, Alfred Hitchcock, Japanese, Korean).
- Healthcheck script (`mcp-healthcheck.js`) with phased validation: /healthz probe, initialize, tools/list, sample tools/call sequence.
- Timeouts and early 404 abort logic in healthcheck for reliability (CI friendly).
- Documentation updates: README, INSTALLATION, developer instructions.
- CHANGELOG and CONTRIBUTING guidelines.

### Changed
- Archetype analysis now semantic (removed pure random selection except fallback).
- Multi-archetype blending enhanced with variance-based composite tension metric.

### Fixed
- Tags optional (`Field(default=[])`) to eliminate 422 validation errors on lore creation without tags.
- Protocol version pinned to `2024-10-07` for LM Studio compatibility.

### Security / Reliability
- Early abort on first 404 during healthcheck prevents misleading partial passes.
- Timeout phases reduce risk of hanging CI jobs.

---

## Versioning Policy
Semantic versioning will be adopted after initial public release. Breaking JSON shape changes will bump the minor version and be documented here.

## Upgrade Guidance
- After pulling new changes, rerun `node mcp-healthcheck.js` to confirm tool schema synchronization.
- For new frameworks, no additional migration—multi-blend automatically incorporates them.

---

## Historical Timeline (Summary)
1. Protocol stabilization & MCP bridge foundation.
2. Lore CRUD & multi-world persistence.
3. Interactive creation sessions.
4. Multi-archetype blending.
5. Semantic scoring integration.
6. Reliability upgrades (timeouts, probes, early abort).

---

