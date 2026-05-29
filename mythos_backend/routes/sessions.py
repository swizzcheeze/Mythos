"""
Session routes — interactive creation workflows, scoped per-world.

Tool schema for the bridge:
  action = "start"    POST /sessions
  action = "update"   POST /sessions/{id}/update
  action = "status"   GET  /sessions/{id}
  action = "finalize" POST /sessions/{id}/finalize
  action = "list"     GET  /sessions
  action = "delete"   DELETE /sessions/{id}
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from mythos_backend.services import embedding, world_data
from mythos_backend.services.templates import (
    finalize_session,
    get_session_state,
    list_sessions,
    start_session,
    update_session,
)

router = APIRouter(prefix="/sessions", tags=["sessions"])


def _resolve_world(world: str = Query(default="default")) -> str:
    return world


@router.get("/templates")
def templates():
    from mythos_backend.services.templates import TEMPLATES
    return {
        "templates": {
            k: {
                "entity_type": v["entity_type"],
                "section_count": len(v["sections"]),
                "sections": list(v["sections"].keys()),
            }
            for k, v in TEMPLATES.items()
        }
    }


@router.post("")
def session_start(body: dict, world: str = Depends(_resolve_world)):
    template_type = body.get("template_type", "character")
    style = body.get("style", "Fantasy")
    try:
        session = start_session(world, template_type, style)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not world_data.world_exists(world):
        world_data.create_world(world)
    return {"session": session, "world": world}


@router.get("/{session_id}")
def session_status(session_id: str, world: str = Depends(_resolve_world)):
    try:
        return get_session_state(world, session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")


@router.post("/{session_id}/update")
def session_update(session_id: str, body: dict, world: str = Depends(_resolve_world)):
    """Fill in session sections. Body: {section_name: {field: value}}."""
    try:
        return update_session(world, session_id, body)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")


@router.post("/{session_id}/finalize")
def session_finalize(session_id: str, body: dict, world: str = Depends(_resolve_world)):
    """Build a preview from the session. Pass save=true to also persist as entity."""
    topic = body.get("topic")
    tags = body.get("tags")
    try:
        result = finalize_session(world, session_id, topic=topic, tags=tags)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")

    if body.get("save"):
        from mythos_backend.models.entities import SavedEntity
        proposed = result["proposed_entity"]
        entity = SavedEntity.validate_python(proposed)
        saved = world_data.create_entity(world, entity)
        if embedding.is_enabled():
            embedding.index_entity(world, saved["id"],
                                   f"{saved.get('name', '')} {saved.get('content', '')}")
        result["saved_entity"] = saved
        result["message"] = "Session finalized and entity saved."
    return result


@router.delete("/{session_id}")
def session_delete(session_id: str, world: str = Depends(_resolve_world)):
    if not world_data.delete_session(world, session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "success", "message": "Session deleted."}


@router.get("")
def session_list(world: str = Depends(_resolve_world), limit: int | None = Query(default=None)):
    return {"sessions": list_sessions(world, limit=limit), "world": world}
