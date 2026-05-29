"""
Cleanup/maintenance routes.

POST /admin/wipe-world      → delete all entities in a world
POST /admin/reset-vectors   → drop FAISS index for a world
GET  /admin/status          → system-wide status overview
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Query

from mythos_backend.core.config import ADMIN_TOKEN
from mythos_backend.services import embedding, world_data

router = APIRouter(prefix="/admin", tags=["admin"])


def _check_admin(x_admin_token: str | None = Header(None)) -> None:
    if ADMIN_TOKEN is None:
        return
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")


def _resolve_world(world: str = Query(default="default")) -> str:
    return world


@router.get("/status")
def system_status():
    from mythos_backend.core.llm import get_provider_state, LLM_PROVIDER
    emb_status = embedding.get_status()
    return {
        "llm": {
            "configured_provider": LLM_PROVIDER,
            "available": get_provider_state(),
        },
        "embeddings": {
            "enabled": emb_status.enabled,
            "source": emb_status.source,
            "model": emb_status.model_name,
            "total_embeddings": emb_status.total_embeddings,
            "failed_embeddings": emb_status.failed_embeddings,
            "last_error": emb_status.last_error,
        },
        "worlds": {
            w: world_data.entity_count(w)
            for w in world_data.list_worlds()
        },
    }


@router.post("/wipe-world")
def wipe_world(world: str = Depends(_resolve_world), x_admin_token: str | None = Depends(_check_admin)):
    if world == "default":
        raise HTTPException(status_code=400, detail="Use DELETE /entities?confirm=CONFIRM for default world.")
    world_data.wipe_world_data(world)
    world_data.reset_vectors(world)
    return {"status": "success", "message": f"World '{world}' wiped.", "world": world}


@router.post("/reset-vectors")
def reset_vectors(world: str = Depends(_resolve_world), x_admin_token: str | None = Depends(_check_admin)):
    embedding.reset_faiss_index(world)
    world_data.reset_vectors(world)
    return {"status": "success", "message": f"Vectors reset for world '{world}'."}
