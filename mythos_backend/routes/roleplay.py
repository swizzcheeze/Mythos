"""
Roleplay routes — character-driven conversation, scoped per-world.

POST /roleplay/chat  → send a message to a character
GET  /roleplay/history → get conversation history
"""

from __future__ import annotations

import threading
import uuid
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Query

from mythos_backend.core.llm import get_llm_for_generation, invoke_llm
from mythos_backend.services import world_data

router = APIRouter(prefix="/roleplay", tags=["roleplay"])

# Per-world conversation memory: {world: {session_id: [messages]}}
_conversations: dict[str, dict[str, list[dict]]] = defaultdict(dict)
_lock = threading.Lock()


def _resolve_world(world: str = Query(default="default")) -> str:
    return world


def _get_context(world: str, entity_id: str | None = None, num_results: int = 3) -> str:
    """Build context from world entities for the character."""
    if not entity_id:
        entities = world_data.find_entities(world, entity_type="character", search="")
    else:
        entity = world_data.get_entity(world, entity_id)
        entities = [entity] if entity else []

    parts = []
    for e in entities[:num_results]:
        name = e.get("name", "Unknown")
        content = e.get("content", "")
        traits = e.get("traits", [])
        parts.append(f"Character: {name}\nTraits: {', '.join(traits)}\nBackground: {content}")

    return "\n\n".join(parts) if parts else "No character context found."


@router.post("/chat")
def roleplay_chat(body: dict, world: str = Depends(_resolve_world)):
    """Send a message to a character and get a response."""
    message = body.get("message", "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="message is required")

    character_id = body.get("character_id")
    session_id = body.get("session_id") or str(uuid.uuid4())

    # Build system prompt from character context
    context = _get_context(world, character_id)
    system_prompt = (
        f"You are roleplaying a character in the world '{world}'.\n"
        f"Character context:\n{context}\n\n"
        f"Stay in character. Respond in first person. "
        f"Be consistent with the character's traits and background."
    )

    with _lock:
        history = _conversations[world].setdefault(session_id, [])
        history.append({"role": "user", "content": message})

    # Build full prompt
    messages_text = "\n".join(
        f"{'User' if m['role'] == 'user' else 'Character'}: {m['content']}"
        for m in history[-10:]  # last 10 messages for context
    )
    full_prompt = f"{system_prompt}\n\nConversation so far:\n{messages_text}\n\nCharacter:"

    try:
        llm = get_llm_for_generation(temperature=0.8)
        response = invoke_llm(llm, full_prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {e}")

    with _lock:
        _conversations[world][session_id].append({"role": "assistant", "content": response})

    return {
        "session_id": session_id,
        "world": world,
        "character_id": character_id,
        "response": response,
    }


@router.get("/history/{session_id}")
def roleplay_history(session_id: str, world: str = Depends(_resolve_world)):
    """Get the conversation history for a roleplay session."""
    with _lock:
        history = _conversations.get(world, {}).get(session_id, [])
    return {"session_id": session_id, "world": world, "history": history}


@router.delete("/history/{session_id}")
def clear_roleplay_history(session_id: str, world: str = Depends(_resolve_world)):
    """Clear a roleplay session's history."""
    with _lock:
        if world in _conversations and session_id in _conversations[world]:
            del _conversations[world][session_id]
    return {"status": "success", "message": "Session history cleared."}
