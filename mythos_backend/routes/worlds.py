"""
World management routes.

GET    /worlds              → list all worlds + entity counts
POST   /worlds              → create a new world
DELETE /worlds/{name}       → delete a world (requires admin token)
GET    /worlds/{name}/stats → world statistics
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException

from mythos_backend.core.config import ADMIN_TOKEN
from mythos_backend.services import world_data

router = APIRouter(prefix="/worlds", tags=["worlds"])


def _check_admin(x_admin_token: str | None = Header(None)) -> None:
    if ADMIN_TOKEN is None:
        return
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")


@router.get("")
def list_worlds():
    worlds = world_data.list_worlds()
    return {
        "worlds": [
            {
                "name": w,
                "entity_count": world_data.entity_count(w),
                "exists": world_data.world_exists(w),
            }
            for w in worlds
        ]
    }


@router.post("")
def create_world(body: dict, x_admin_token: str | None = Depends(_check_admin)):
    name = body.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="World name is required.")
    try:
        world_data.validate_world_name(name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if world_data.world_exists(name):
        raise HTTPException(status_code=409, detail=f"World '{name}' already exists.")
    world_data.create_world(name)
    return {"status": "success", "message": f"World '{name}' created.", "name": name}


@router.delete("/{name}")
def delete_world(name: str, x_admin_token: str | None = Depends(_check_admin)):
    if name == "default":
        raise HTTPException(status_code=400, detail="Cannot delete the 'default' world.")
    try:
        world_data.delete_world(name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "success", "message": f"World '{name}' deleted."}


@router.get("/{name}/stats")
def world_stats(name: str):
    if not world_data.world_exists(name):
        raise HTTPException(status_code=404, detail=f"World '{name}' not found.")
    entities = world_data.load_entities(name)
    type_counts: dict[str, int] = {}
    for e in entities:
        t = e.get("entity_type", "unknown")
        type_counts[t] = type_counts.get(t, 0) + 1
    return {
        "name": name,
        "total_entities": len(entities),
        "type_counts": type_counts,
    }
