"""
Embedding service routes.

GET  /embeddings/status   → service health + stats
POST /embeddings/embed    → embed a single text
POST /embeddings/index    → re-index all entities in a world
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from mythos_backend.services import embedding, world_data

router = APIRouter(prefix="/embeddings", tags=["embeddings"])


def _resolve_world(world: str = Query(default="default")) -> str:
    return world


@router.get("/status")
def embedding_status():
    status = embedding.refresh_status()
    return {
        "enabled": status.enabled,
        "source": status.source,
        "model_name": status.model_name,
        "last_error": status.last_error,
        "total_embeddings": status.total_embeddings,
        "failed_embeddings": status.failed_embeddings,
    }


@router.post("/embed")
def embed_text(body: dict):
    text = body.get("text", "")
    if not text:
        raise HTTPException(status_code=400, detail="text is required")
    vec = embedding.embed_text(text)
    if vec is None:
        raise HTTPException(status_code=503, detail="Embedding service unavailable")
    return {"embedding": vec.tolist(), "dim": len(vec)}


@router.post("/index")
def index_world(world: str = Depends(_resolve_world)):
    """Re-index all entities in a world into the FAISS index."""
    if not embedding.is_enabled():
        raise HTTPException(status_code=503, detail="Embedding service not available")

    entities = world_data.load_entities(world)
    embedding.reset_faiss_index(world)
    world_data.reset_vectors(world)

    indexed = 0
    failed = 0
    for entity in entities:
        text = f"{entity.get('name', '')} {entity.get('content', '')}"
        if embedding.index_entity(world, entity["id"], text):
            indexed += 1
        else:
            failed += 1

    return {
        "status": "success",
        "world": world,
        "indexed": indexed,
        "failed": failed,
        "total": len(entities),
    }
