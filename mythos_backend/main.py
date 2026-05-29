"""
Mythos Backend — World Building & Lore Management System.

Rebuilt from the ground up with:
  - Pydantic v2 discriminated unions for entity types (fixes "persona saved as world")
  - Per-world data isolation (sessions, entities, vectors)
  - Proper FastAPI lifespan/depends/router architecture
  - No global mutable state — everything scoped via DI
  - Embedding service with retry, caching, and status tracking
  - Configurable LLM providers (Ollama default, supports 5 cloud providers)
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from mythos_backend.core.config import MUTE_HEALTHZ_LOGS
from mythos_backend.core.llm import get_llm_for_generation, get_provider_state
from mythos_backend.routes.admin import router as admin_router
from mythos_backend.routes.archetypes import router as archetypes_router
from mythos_backend.routes.bridge import router as bridge_router
from mythos_backend.routes.embeddings import router as embeddings_router
from mythos_backend.routes.entities import router as entities_router
from mythos_backend.routes.llmroutes import router as llm_router
from mythos_backend.routes.roleplay import router as roleplay_router
from mythos_backend.routes.sessions import router as sessions_router
from mythos_backend.routes.worlds import router as worlds_router
from mythos_backend.services import embedding

log = logging.getLogger("uvicorn.error")

_healthz_filter = None


def _install_healthz_filter():
    if not MUTE_HEALTHZ_LOGS:
        return

    class HealthzFilter(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            return "/healthz" not in record.getMessage()

    for name in ("uvicorn.access", "uvicorn"):
        logging.getLogger(name).addFilter(HealthzFilter())


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: initialize providers, verify Ollama. Shutdown: cleanup."""
    log.info("Mythos Backend starting up...")
    _install_healthz_filter()

    # 1. Verify embedding service (2s timeout — port 8002 may be dead)
    try:
        status = await asyncio.wait_for(
            asyncio.to_thread(embedding.refresh_status), timeout=2.0
        )
        if status.enabled:
            log.info(f"Embedding: {status.source} ({status.model_name})")
        else:
            log.warning("Embedding service not available — semantic search disabled.")
    except asyncio.TimeoutError:
        log.warning("Embedding service check timed out — semantic search disabled.")
    except Exception as e:
        log.warning(f"Embedding service check failed: {e}")

    # 2. Verify LLM provider (3s timeout — ChatOllama init may probe Ollama)
    try:
        state = get_provider_state()
        active = [k for k, v in state.items() if v]
        log.info(f"LLM providers available: {active}")
        test_llm = await asyncio.wait_for(
            asyncio.to_thread(get_llm_for_generation), timeout=3.0
        )
        if hasattr(test_llm, "invoke"):
            log.info("Ollama LLM handle created successfully.")
    except asyncio.TimeoutError:
        log.warning("LLM provider check timed out — will retry on first request.")
    except Exception as e:
        log.warning(f"LLM provider check failed: {e}")

    # 3. Ensure default world exists
    from mythos_backend.services import world_data
    if not world_data.world_exists("default"):
        world_data.create_world("default")
        log.info("Created default world.")
    else:
        count = world_data.entity_count("default")
        log.info(f"Default world loaded: {count} entities.")

    log.info("Mythos Backend ready.")
    yield
    log.info("Mythos Backend shutting down.")


# ── App ──────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Mythos Backend",
    description="World building, lore management, character creation, and archetype analysis.",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS — permissive for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────────────────

app.include_router(entities_router)
app.include_router(sessions_router)
app.include_router(worlds_router)
app.include_router(archetypes_router)
app.include_router(llm_router)
app.include_router(embeddings_router)
app.include_router(roleplay_router)
app.include_router(admin_router)
app.include_router(bridge_router)


# ── Health check ───────────────────────────────────────────────────────────────

@app.get("/healthz")
def healthz():
    return {"status": "ok", "version": "2.0.0"}


@app.get("/")
def root():
    return {
        "service": "Mythos Backend",
        "version": "2.0.0",
        "docs": "/docs",
        "healthz": "/healthz",
    }


# ── CLI entry point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "mythos_backend.main:app",
        host="0.0.0.0",
        port=8013,
        reload=True,
        log_level="info",
    )
