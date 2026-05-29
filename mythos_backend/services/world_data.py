"""
World data service — per-world repository for lore entities and sessions.

All file I/O goes through here. No endpoint does raw file operations.
Each world is fully isolated: world_data/lore_db.json (default) or
world_data/worlds/<name>/lore_db.json.

Thread-safe via per-path file locks. Atomic writes via temp+rename.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
import threading
from typing import Any

from mythos_backend.core.config import LORE_DB_BASE_PATH
from mythos_backend.models.entities import SavedEntity

# ── File lock registry ────────────────────────────────────────────────────
_file_locks: dict[str, threading.Lock] = {}
_file_locks_lock = threading.Lock()


def _lock_for(path: str) -> threading.Lock:
    with _file_locks_lock:
        if path not in _file_locks:
            _file_locks[path] = threading.Lock()
        return _file_locks[path]


# ── Path helpers ──────────────────────────────────────────────────────────

def validate_world_name(name: str) -> str:
    if not name or not isinstance(name, str):
        raise ValueError("World name must be a non-empty string")
    if not re.fullmatch(r"[A-Za-z0-9_\-]{1,64}", name):
        raise ValueError(
            "World name must be 1-64 chars: letters, numbers, underscore, hyphen"
        )
    return name


def _world_dir(world: str) -> str:
    base = os.path.dirname(LORE_DB_BASE_PATH)
    if world == "default":
        return base
    return os.path.join(base, "worlds", world)


def _lore_path(world: str) -> str:
    return os.path.join(_world_dir(world), "lore_db.json")


def _sessions_path(world: str) -> str:
    return os.path.join(_world_dir(world), "sessions.json")


def _vectors_path(world: str) -> str:
    return os.path.join(_world_dir(world), "vectors_metadata.json")


# ── Atomic file I/O ───────────────────────────────────────────────────────

def _read_json(path: str) -> Any:
    """Read JSON file, return None if missing, raise on corruption."""
    lock = _lock_for(path)
    with lock:
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)


def _write_json(path: str, data: Any) -> None:
    """Atomically write JSON data to file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    lock = _lock_for(path)
    with lock:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=os.path.dirname(path),
            delete=False,
            suffix=".tmp",
        ) as tmp:
            json.dump(data, tmp, indent=2, ensure_ascii=False)
            tmp.flush()
            os.fsync(tmp.fileno())
            tmp_path = tmp.name
        os.replace(tmp_path, path)


# ── Lore entity CRUD ──────────────────────────────────────────────────────

def load_entities(world: str = "default") -> list[dict]:
    """Load all entities for a world."""
    raw = _read_json(_lore_path(world))
    if raw is None:
        return []
    if isinstance(raw, list):
        return raw
    return []


def save_entities(world: str, entities: list[dict]) -> None:
    """Overwrite the entity list for a world."""
    _write_json(_lore_path(world), entities)


def create_entity(world: str, entity: SavedEntity) -> dict:
    """Add a new entity to a world. Returns the saved dict."""
    entities = load_entities(world)
    entity_dict = entity.model_dump()
    entity_dict["world"] = world
    entities.append(entity_dict)
    save_entities(world, entities)
    return entity_dict


def get_entity(world: str, entity_id: str) -> dict | None:
    """Get a single entity by ID from a world."""
    entities = load_entities(world)
    return next((e for e in entities if e.get("id") == entity_id), None)


def find_entities(
    world: str,
    entity_type: str | None = None,
    tags: list[str] | None = None,
    search: str | None = None,
) -> list[dict]:
    """Find entities with optional filters."""
    entities = load_entities(world)

    if entity_type:
        entities = [e for e in entities if e.get("entity_type") == entity_type]

    if tags:
        entities = [
            e for e in entities if any(t in e.get("tags", []) for t in tags)
        ]

    if search:
        q = search.lower()
        entities = [
            e
            for e in entities
            if q in e.get("name", "").lower()
            or q in e.get("content", "").lower()
        ]

    return entities


def update_entity(world: str, entity_id: str, updates: dict) -> dict | None:
    """Partial update of an entity. Returns updated entity or None."""
    entities = load_entities(world)
    for i, e in enumerate(entities):
        if e.get("id") == entity_id:
            from datetime import datetime, timezone
            updates["updated_at"] = datetime.now(timezone.utc).isoformat()
            entities[i].update(updates)
            save_entities(world, entities)
            return entities[i]
    return None


def delete_entity(world: str, entity_id: str) -> bool:
    """Delete an entity by ID. Returns True if found and deleted."""
    entities = load_entities(world)
    original_len = len(entities)
    entities = [e for e in entities if e.get("id") != entity_id]
    if len(entities) < original_len:
        save_entities(world, entities)
        return True
    return False


def wipe_world_data(world: str) -> None:
    """Delete ALL entities for a world."""
    save_entities(world, [])


# ── World management ─────────────────────────────────────────────────────

def list_worlds() -> list[str]:
    """List all world names (always includes 'default')."""
    worlds = ["default"]
    base = os.path.join(os.path.dirname(LORE_DB_BASE_PATH), "worlds")
    if os.path.exists(base):
        for entry in os.listdir(base):
            if os.path.isdir(os.path.join(base, entry)):
                worlds.append(entry)
    return worlds


def world_exists(world: str) -> bool:
    if world == "default":
        return os.path.exists(LORE_DB_BASE_PATH)
    return os.path.isdir(os.path.join(_world_dir(world)))


def create_world(world: str) -> None:
    """Create an empty world directory with a fresh lore_db.json."""
    validate_world_name(world)
    os.makedirs(_world_dir(world), exist_ok=True)
    path = _lore_path(world)
    if not os.path.exists(path):
        _write_json(path, [])


def delete_world(world: str) -> None:
    """Delete a world directory and all its data."""
    import shutil
    validate_world_name(world)
    if world == "default":
        raise ValueError("Cannot delete the 'default' world")
    path = _world_dir(world)
    if os.path.isdir(path):
        shutil.rmtree(path)


def entity_count(world: str) -> int:
    return len(load_entities(world))


# ── Creation sessions ─────────────────────────────────────────────────────
# Sessions are stored per-world in sessions.json, keyed by session_id.

def load_sessions(world: str = "default") -> dict[str, dict]:
    """Load all creation sessions for a world."""
    raw = _read_json(_sessions_path(world))
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    return {}


def save_sessions(world: str, sessions: dict[str, dict]) -> None:
    """Save all creation sessions for a world."""
    _write_json(_sessions_path(world), sessions)


def get_session(world: str, session_id: str) -> dict | None:
    """Get a single session by ID from a world."""
    sessions = load_sessions(world)
    return sessions.get(session_id)


def put_session(world: str, session_id: str, data: dict) -> None:
    """Insert or update a session in a world."""
    sessions = load_sessions(world)
    sessions[session_id] = data
    save_sessions(world, sessions)


def delete_session(world: str, session_id: str) -> bool:
    """Delete a session from a world."""
    sessions = load_sessions(world)
    if session_id in sessions:
        del sessions[session_id]
        save_sessions(world, sessions)
        return True
    return False


# ── Vector metadata ───────────────────────────────────────────────────────

def load_vectors_metadata(world: str = "default") -> dict[str, Any]:
    default = {"entries": [], "model_name": "all-MiniLM-L6-v2"}
    raw = _read_json(_vectors_path(world))
    if raw is None:
        return default
    if isinstance(raw, dict):
        return raw
    return default


def save_vectors_metadata(world: str, metadata: dict[str, Any]) -> None:
    _write_json(_vectors_path(world), metadata)


def reset_vectors(world: str) -> None:
    """Remove vector metadata for a world."""
    _write_json(_vectors_path(world), {"entries": [], "model_name": "all-MiniLM-L6-v2"})
