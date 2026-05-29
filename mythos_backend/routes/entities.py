"""
Entity routes — CRUD for typed lore entities.

POST   /entities              → create (discriminated by entity_type)
GET    /entities              → list/search (filter by type, tags, search)
GET    /entities/{id}         → get one
PATCH  /entities/{id}         → partial update
DELETE /entities/{id}         → delete
DELETE /entities              → wipe world (requires confirm + admin token)
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Query

from mythos_backend.core.config import ADMIN_TOKEN
from mythos_backend.models.entities import (
    EntityType,
    SavedEntity,
)
from mythos_backend.services import world_data
from mythos_backend.services.embedding import index_entity, is_enabled

router = APIRouter(prefix="/entities", tags=["entities"])


def _check_admin(x_admin_token: str | None = Header(None)) -> None:
    if ADMIN_TOKEN is None:
        return
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")


def _resolve_world(world: str = Query(default="default")) -> str:
    return world


@router.post("")
def create_entity(body: dict, world: str = Depends(_resolve_world)):
    """Create a new entity. The entity_type field determines the model."""
    entity_type = body.get("entity_type")
    if not entity_type:
        raise HTTPException(
            status_code=422,
            detail="entity_type is required. Valid types: " + ", ".join(
                t.value for t in EntityType
            ),
        )

    # Validate using the discriminated union
    try:
        entity = SavedEntity.validate_python(body)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Validation error: {e}")

    saved = world_data.create_entity(world, entity)

    # Background embed
    if is_enabled():
        index_entity(world, saved["id"], f"{saved.get('name', '')} {saved.get('content', '')}")

    return {
        "status": "success",
        "entity": saved,
        "world": world,
    }


@router.get("")
def list_entities(
    world: str = Depends(_resolve_world),
    entity_type: str | None = Query(default=None),
    search: str | None = Query(default=None),
    tags: list[str] | None = Query(default=None),
):
    """List entities with optional filtering by type, tags, or search."""
    results = world_data.find_entities(world, entity_type=entity_type, tags=tags, search=search)
    return {
        "entities": results,
        "total": len(results),
        "world": world,
    }


@router.get("/{entity_id}")
def get_entity(entity_id: str, world: str = Depends(_resolve_world)):
    """Get a single entity by ID."""
    entity = world_data.get_entity(world, entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return {"entity": entity, "world": world}


@router.patch("/{entity_id}")
def update_entity(entity_id: str, updates: dict, world: str = Depends(_resolve_world)):
    """Partial update of an entity."""
    entity = world_data.update_entity(world, entity_id, updates)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return {"status": "success", "entity": entity, "world": world}


@router.delete("/{entity_id}")
def delete_entity(entity_id: str, world: str = Depends(_resolve_world)):
    """Delete an entity by ID."""
    if not world_data.delete_entity(world, entity_id):
        raise HTTPException(status_code=404, detail="Entity not found")
    return {"status": "success", "message": f"Entity {entity_id[:8]} deleted from world '{world}'."}


@router.delete("")
def wipe_entities(confirm: str, world: str = Depends(_resolve_world), x_admin_token: str | None = Depends(_check_admin)):
    """Wipe all entities in a world. Requires confirm=CONFIRM and admin token."""
    if confirm != "CONFIRM":
        raise HTTPException(status_code=400, detail="Pass confirm=CONFIRM to proceed.")
    world_data.wipe_world_data(world)
    world_data.reset_vectors(world)
    return {"status": "success", "message": f"World '{world}' wiped."}
