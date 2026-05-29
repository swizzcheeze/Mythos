"""
Core configuration — replaces the global mutable state in the old backend.

All mutable runtime state lives in app.state, injected via DI.
Environment-only config lives here as module-level constants.
"""

from __future__ import annotations

import os

# Load .env from the project root (two levels up from this file)
try:
    from dotenv import load_dotenv as _load_dotenv
    import pathlib as _pathlib
    _env_path = _pathlib.Path(__file__).resolve().parents[2] / ".env"
    _load_dotenv(dotenv_path=_env_path, override=False)
except ImportError:
    pass

# ── Environment config (immutable after startup) ────────────────────────────

LORE_DB_BASE_PATH: str = os.getenv("LORE_DB_PATH", "world_data/lore_db.json")

# Embedding config
EMBEDDING_SERVICE_URL: str = os.getenv(
    "EMBEDDING_SERVICE_URL", "http://localhost:8002"
)
EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
EMBEDDING_DIM: int = 384
COHERE_API_KEY: str | None = os.getenv("COHERE_API_KEY", None)

# LLM provider config
LLM_PROVIDER: str = os.getenv("MYTHOS_LLM_PROVIDER", "ollama").lower()
OLLAMA_BASE_URL: str = os.getenv(
    "MYTHOS_OLLAMA_BASE_URL", "http://localhost:11434"
)
DEFAULT_OLLAMA_MODEL: str = os.getenv("MYTHOS_OLLAMA_MODEL", "llama3")
DEFAULT_GENERATOR_MODEL: str = os.getenv("MYTHOS_GENERATOR_MODEL", "") or DEFAULT_OLLAMA_MODEL
DEFAULT_CRITIC_MODEL: str = os.getenv("MYTHOS_CRITIC_MODEL", "") or DEFAULT_OLLAMA_MODEL

# Anthropic
ANTHROPIC_API_KEY: str | None = os.getenv("ANTHROPIC_API_KEY", None)
DEFAULT_ANTHROPIC_MODEL: str = os.getenv("MYTHOS_ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")

# OpenRouter
OPENROUTER_API_KEY: str | None = os.getenv("OPENROUTER_API_KEY", None)
DEFAULT_OPENROUTER_MODEL: str = os.getenv(
    "MYTHOS_OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet"
)

# Groq
GROQ_API_KEY: str | None = os.getenv("GROQ_API_KEY", None)
DEFAULT_GROQ_MODEL: str = os.getenv("MYTHOS_GROQ_MODEL", "llama-3.3-70b-versatile")

# xAI
XAI_API_KEY: str | None = os.getenv("XAI_API_KEY", None)
DEFAULT_XAI_MODEL: str = os.getenv("MYTHOS_XAI_MODEL", "grok-beta")

# Gemini
GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY", None)
DEFAULT_GEMINI_MODEL: str = os.getenv("MYTHOS_GEMINI_MODEL", "gemini-1.5-pro")

# Admin
ADMIN_TOKEN: str | None = os.getenv("MYTHOS_ADMIN_TOKEN", None)
MUTE_HEALTHZ_LOGS: bool = os.getenv("MYTHOS_MUTE_HEALTHZ_LOGS", "1") == "1"
