"""
Bridge dispatch endpoint — POST /call/{toolName}

This is the MCP bridge integration layer. The mythos-bridge.js MCP server
sends tool calls to /call/{toolName} with the tool's arguments as JSON body.
This module maps tool names to backend operations.

Each handler validates input, calls the appropriate service, and returns
a JSON response that the bridge formats for the LLM.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query

from mythos_backend.core.llm import get_llm_for_generation, get_llm_for_critique, invoke_llm
from mythos_backend.models.entities import SavedEntity, EntityType
from mythos_backend.services import world_data
from mythos_backend.services.archetype import analyze_single, analyze_multi
from mythos_backend.services.embedding import embed_text, get_faiss_index, is_enabled, get_status
from mythos_backend.services.templates import (
    start_session, update_session, get_session_state,
    finalize_session, list_sessions, TEMPLATES,
)

router = APIRouter()


# ── Helpers ────────────────────────────────────────────────────────────────

def _world(request: dict) -> str:
    return request.get("world", "default")


def _ensure_world(world: str) -> None:
    if not world_data.world_exists(world):
        world_data.create_world(world)


def _entity_to_response(e: dict) -> dict:
    """Clean entity dict for bridge response."""
    return {
        "id": e.get("id"),
        "entity_type": e.get("entity_type"),
        "name": e.get("name"),
        "content": e.get("content", "")[:500],
        "tags": e.get("tags", []),
        "world": e.get("world", "default"),
        "created_at": e.get("created_at"),
    }


# ── Tool Handlers ──────────────────────────────────────────────────────────

async def _handle_archetype_analysis(request: dict) -> dict:
    name = request.get("character_name", "")
    desc = request.get("description", "")
    style = request.get("style", "Jungian")
    return analyze_single(name, desc, style)


async def _handle_multi_archetype_analysis(request: dict) -> dict:
    name = request.get("character_name", "")
    desc = request.get("description", "")
    styles = request.get("styles", "Fantasy")
    max_fw = request.get("max_frameworks", 5)
    return analyze_multi(name, desc, styles, max_fw)


async def _handle_create_lore_entry(request: dict) -> dict:
    world = _world(request)
    _ensure_world(world)

    topic = request.get("topic", "")
    content = request.get("content", "")
    tags = request.get("tags", [])

    entity = SavedEntity.validate_python({
        "entity_type": "lore",
        "name": topic,
        "content": content,
        "tags": tags,
        "world": world,
    })
    saved = world_data.create_entity(world, entity)
    return {"entry_id": saved["id"], "topic": topic, "world": world, "status": "created"}


async def _handle_list_lore_entries(request: dict) -> dict:
    world = _world(request)
    search = request.get("search_query")
    tags = request.get("tags")
    entities = world_data.find_entities(world, entity_type="lore", tags=tags, search=search)
    return {"entries": [_entity_to_response(e) for e in entities], "total": len(entities)}


async def _handle_semantic_lore_search(request: dict) -> dict:
    world = _world(request)
    query = request.get("query", "")
    top_k = request.get("top_k", 5)

    # Use cached status — don't re-check on every call
    emb_status = get_status()
    if not emb_status.enabled:
        # Try one refresh but skip slow Cohere check
        import requests as _req
        try:
            _req.get("http://localhost:8002/health", timeout=1)
            emb_status = refresh_status()
        except Exception:
            pass
        if not emb_status.enabled:
            return {"results": [], "embedding_model": "none", "error": "Embedding service not available"}

    # Embed the query
    q_vec = embed_text(query)
    if q_vec is None:
        return {"results": [], "embedding_model": "embed-failed", "error": "Query embedding failed"}

    import numpy as np
    index = get_faiss_index(world)
    if index is None or index.ntotal == 0:
        return {"results": [], "embedding_model": "all-MiniLM-L6-v2", "message": "Index empty. Use POST /embeddings/index to build index first."}

    # Search
    query_vec = np.array([q_vec]).astype(np.float32)
    k = min(top_k, index.ntotal)
    distances, positions = index.search(query_vec, k)

    # Map positions to entity IDs using vector metadata
    from mythos_backend.services.world_data import load_vectors_metadata
    metadata = load_vectors_metadata(world)
    entries_map = {e["index"]: e["id"] for e in metadata.get("entries", [])}

    results = []
    for dist, pos in zip(distances[0], positions[0]):
        eid = entries_map.get(int(pos))
        if eid:
            entity = world_data.get_entity(world, eid)
            if entity:
                similarity = max(0.0, 1.0 - float(dist))
                results.append({
                    "id": eid,
                    "name": entity.get("name", ""),
                    "preview": entity.get("content", "")[:200],
                    "similarity": round(similarity, 3),
                })

    return {"results": results, "embedding_model": "all-MiniLM-L6-v2", "total_indexed": index.ntotal}


async def _handle_creation_session_start(request: dict) -> dict:
    world = _world(request)
    _ensure_world(world)
    template_type = request.get("template_type", "character")
    style = request.get("style", "Fantasy")

    try:
        session = start_session(world, template_type, style)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "session_id": session["id"],
        "template_type": session["template_type"],
        "style": session["style"],
        "sections": session["sections"],
        "creative_prompts": session.get("prompts", []),
        "world": world,
    }


async def _handle_creation_session_update(request: dict) -> dict:
    world = _world(request)
    sid = request.get("session_id", "")
    updates = request.get("updates", {})
    try:
        return update_session(world, sid, updates)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")


async def _handle_creation_session_get(request: dict) -> dict:
    world = _world(request)
    sid = request.get("session_id", "")
    try:
        return get_session_state(world, sid)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")


async def _handle_creation_session_finalize(request: dict) -> dict:
    world = _world(request)
    sid = request.get("session_id", "")
    topic = request.get("topic")
    tags = request.get("tags")

    try:
        result = finalize_session(world, sid, topic=topic, tags=tags)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")

    # Rename proposed_entity → proposed_entry for bridge compatibility
    if "proposed_entity" in result:
        result["proposed_entry"] = result.pop("proposed_entity")
    return result


async def _handle_creation_session_list(request: dict) -> dict:
    world = _world(request)
    limit = request.get("limit")
    sessions = list_sessions(world, limit=limit)
    return {"sessions": sessions, "count": len(sessions), "world": world}


async def _handle_get_inspiration(request: dict) -> dict:
    style = request.get("style", "Fantasy")
    prompts = {
        "Sacrifice": f"In a {style} setting, what must your character give up to achieve their goal? What is the irreversible cost?",
        "Transformation": f"In a {style} world, what fundamental change is your character resisting? What would they become if they surrendered?",
        "Time": f"How does history or fate intervene in your {style} protagonist's life? What deadline looms?",
    }
    import random
    theme = random.choice(list(prompts.keys()))
    return {"theme": theme, "prompt": prompts[theme], "style": style}


async def _handle_list_tools(request: dict) -> dict:
    from mythos_backend.routes.entities import router as er
    # Return tool catalog
    return {"tools": [
        "mythos_archetype_analysis",
        "mythos_multi_archetype_analysis",
        "mythos_create_lore_entry",
        "mythos_list_lore_entries",
        "mythos_semantic_lore_search",
        "mythos_creation_session_start",
        "mythos_creation_session_update",
        "mythos_creation_session_get",
        "mythos_creation_session_finalize",
        "mythos_creation_session_list",
        "mythos_get_inspiration",
        "mythos_list_tools",
        "mythos_roleplay_start",
        "mythos_create_world",
        "mythos_list_worlds",
        "mythos_select_world",
        "mythos_creation_mode",
        "mythos_list_archetype_styles",
        "mythos_update_lore_entry",
        "mythos_wipe_lore_db",
        "mythos_delete_world",
    ]}


async def _handle_roleplay_start(request: dict) -> dict:
    """Generate a roleplay persona from a character ID or session."""
    world = _world(request)
    session_id = request.get("session_id")
    character_name = request.get("character_name")
    bio = request.get("bio", "")
    style = request.get("style", "Fantasy")

    character_data = {
        "name": character_name or "Unknown Character",
        "traits": [],
        "background": [bio] if bio else [],
    }

    if session_id:
        try:
            session = get_session_state(world, session_id)
            filled = session.get("filled", {})
            # Extract character data from session fields
            basic = filled.get("Basic Info", {})
            core = filled.get("Core Identity", {})
            abilities = filled.get("Abilities", {})
            char_bg = filled.get("Background", {})

            character_data["name"] = basic.get("Name", character_name or "Character")
            character_data["traits"] = [
                core.get("Defining Trait", ""),
                core.get("Fatal Flaw", ""),
            ]
            character_data["background"] = [
                char_bg.get("Origin Story", ""),
                char_bg.get("Formative Event", ""),
            ]
            filled_abilities = abilities.get("Skills/Powers", "")
            if filled_abilities:
                if isinstance(filled_abilities, str):
                    character_data["traits"].extend(
                        [s.strip() for s in filled_abilities.split(";") if s.strip()]
                    )
        except (KeyError, HTTPException):
            pass

    instructions = (
        f"You are roleplaying as {character_data['name']} in a {style} world.\n"
        f"Traits: {', '.join(t for t in character_data['traits'] if t)}\n"
        f"Background: {' '.join(b for b in character_data['background'] if b)}\n\n"
        f"Respond in first person. Stay in character. "
        f"Be consistent with the character's traits and background."
    )

    return {"persona": character_data, "instructions": instructions, "world": world}


async def _handle_create_world(request: dict) -> dict:
    name = request.get("name", "")
    if not name:
        raise HTTPException(status_code=400, detail="World name required")
    try:
        world_data.validate_world_name(name)
        _ensure_world(name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"world": name, "status": "created"}


async def _handle_list_worlds(request: dict) -> dict:
    worlds = world_data.list_worlds()
    return {"worlds": worlds, "counts": {w: world_data.entity_count(w) for w in worlds}}


async def _handle_select_world(request: dict) -> dict:
    name = request.get("name", "default")
    create_if_missing = request.get("create_if_missing", False)
    if not world_data.world_exists(name):
        if create_if_missing:
            _ensure_world(name)
        else:
            raise HTTPException(status_code=404, detail=f"World '{name}' not found")
    return {"active_world": name}


async def _handle_creation_mode(request: dict) -> dict:
    """One-shot template guide (non-persistent)."""
    template_type = request.get("template_type", "character")
    style = request.get("style", "Fantasy")
    template = TEMPLATES.get(template_type)
    if not template:
        raise HTTPException(status_code=400, detail=f"Unknown template type: {template_type}. Valid: {list(TEMPLATES.keys())}")
    return {
        "template_type": template_type,
        "style": style,
        "sections": template["sections"],
        "creative_prompts": template["prompts"],
        "note": "This is a static guide. For persistent sessions, use creation_session_start.",
    }


async def _handle_list_archetype_styles(request: dict) -> dict:
    from mythos_backend.models.archetypes import ARCHETYPE_DEFINITIONS
    return {
        "styles": list(ARCHETYPE_DEFINITIONS.keys()),
        "total": len(ARCHETYPE_DEFINITIONS),
    }


async def _handle_update_lore_entry(request: dict) -> dict:
    world = _world(request)
    eid = request.get("id", "")
    updates = {}
    if "topic" in request:
        updates["name"] = request["topic"]
    if "content" in request:
        updates["content"] = request["content"]
    if "tags" in request:
        updates["tags"] = request["tags"]
    updated = world_data.update_entity(world, eid, updates)
    if not updated:
        raise HTTPException(status_code=404, detail="Entity not found")
    return {"entry": _entity_to_response(updated), "status": "updated"}


async def _handle_wipe_lore_db(request: dict) -> dict:
    world = _world(request)
    confirm = request.get("confirm", "")
    if confirm != "CONFIRM":
        raise HTTPException(status_code=400, detail="Pass confirm=CONFIRM to proceed")
    world_data.wipe_world_data(world)
    world_data.reset_vectors(world)
    return {"status": "wiped", "world": world}


async def _handle_delete_world(request: dict) -> dict:
    name = request.get("name", "")
    confirm = request.get("confirm", "")
    if confirm != "CONFIRM":
        raise HTTPException(status_code=400, detail="Pass confirm=CONFIRM to proceed")
    if name == "default":
        raise HTTPException(status_code=400, detail="Cannot delete default world")
    world_data.delete_world(name)
    return {"status": "deleted", "world": name}


# ── Dispatch table ─────────────────────────────────────────────────────────

TOOL_HANDLERS = {
    "mythos_archetype_analysis": _handle_archetype_analysis,
    "mythos_multi_archetype_analysis": _handle_multi_archetype_analysis,
    "mythos_create_lore_entry": _handle_create_lore_entry,
    "mythos_list_lore_entries": _handle_list_lore_entries,
    "mythos_semantic_lore_search": _handle_semantic_lore_search,
    "mythos_creation_session_start": _handle_creation_session_start,
    "mythos_creation_session_update": _handle_creation_session_update,
    "mythos_creation_session_get": _handle_creation_session_get,
    "mythos_creation_session_finalize": _handle_creation_session_finalize,
    "mythos_creation_session_list": _handle_creation_session_list,
    "mythos_get_inspiration": _handle_get_inspiration,
    "mythos_list_tools": _handle_list_tools,
    "mythos_roleplay_start": _handle_roleplay_start,
    "mythos_create_world": _handle_create_world,
    "mythos_list_worlds": _handle_list_worlds,
    "mythos_select_world": _handle_select_world,
    "mythos_creation_mode": _handle_creation_mode,
    "mythos_list_archetype_styles": _handle_list_archetype_styles,
    "mythos_update_lore_entry": _handle_update_lore_entry,
    "mythos_wipe_lore_db": _handle_wipe_lore_db,
    "mythos_delete_world": _handle_delete_world,
}


@router.post("/call/{tool_name}")
async def dispatch_tool(tool_name: str, request: dict):
    """Main dispatch endpoint for MCP bridge tool calls."""
    handler = TOOL_HANDLERS.get(tool_name)
    if not handler:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown tool: {tool_name}. Available: {list(TOOL_HANDLERS.keys())}",
        )
    try:
        return await handler(request)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tool execution failed: {e}")
