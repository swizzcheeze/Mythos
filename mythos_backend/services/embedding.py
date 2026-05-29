"""
Embedding service — reliable semantic text embedding with retry and status tracking.

Wraps the external embedding service with:
  - Exponential backoff retry
  - Health check caching (no per-call HTTP hammering)
  - Background indexing with status tracking
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from mythos_backend.core.config import (
    COHERE_API_KEY,
    EMBEDDING_DIM,
    EMBEDDING_MODEL_NAME,
    EMBEDDING_SERVICE_URL,
)

# ── Status tracking ────────────────────────────────────────────────────────
@dataclass
class EmbeddingStatus:
    enabled: bool = False
    model_name: str = EMBEDDING_MODEL_NAME
    source: str = "none"  # "cohere", "external_service", "none"
    last_check: float = 0.0
    last_error: str | None = None
    total_embeddings: int = 0
    failed_embeddings: int = 0


_status = EmbeddingStatus()
_status_lock = threading.Lock()


def get_status() -> EmbeddingStatus:
    with _status_lock:
        return EmbeddingStatus(
            enabled=_status.enabled,
            model_name=_status.model_name,
            source=_status.source,
            last_check=_status.last_check,
            last_error=_status.last_error,
            total_embeddings=_status.total_embeddings,
            failed_embeddings=_status.failed_embeddings,
        )


# ── Health check with caching ──────────────────────────────────────────────

def _check_service(url: str, max_retries: int = 2) -> dict[str, Any] | None:
    """Check embedding service health with exponential backoff."""
    import requests

    for attempt in range(max_retries):
        try:
            resp = requests.get(f"{url}/health", timeout=1)
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(0.3 * (2 ** attempt))
            else:
                with _status_lock:
                    _status.last_error = str(e)
    return None


def refresh_status() -> EmbeddingStatus:
    """Re-check embedding service and update status."""
    with _status_lock:
        # Don't hammer: cache for 30 seconds
        if _status.last_check and (time.time() - _status.last_check) < 30:
            return _status

        # Try Cohere first
        if COHERE_API_KEY:
            try:
                import cohere
                co = cohere.ClientV2(api_key=COHERE_API_KEY)
                # Lightweight test
                co.embed(
                    texts=["test"],
                    model="embed-english-v3.0",
                    input_type="search_document",
                )
                _status.enabled = True
                _status.source = "cohere"
                _status.last_check = time.time()
                _status.last_error = None
                return _status
            except Exception:
                pass

        # Try external service
        data = _check_service(EMBEDDING_SERVICE_URL)
        if data:
            _status.enabled = True
            _status.source = "external_service"
            _status.model_name = data.get("model", _status.model_name)
            _status.last_check = time.time()
            _status.last_error = None
            return _status

        _status.enabled = False
        _status.source = "none"
        _status.last_check = time.time()
        return _status


def is_enabled() -> bool:
    """Quick check — refreshes if stale."""
    status = refresh_status()
    return status.enabled


# ── Embedding generation ───────────────────────────────────────────────────

def embed_text(text: str, max_retries: int = 3) -> np.ndarray | None:
    """Get embedding for a single text with retry."""
    import requests

    with _status_lock:
        _status.total_embeddings += 1

    # Try Cohere
    if COHERE_API_KEY:
        for attempt in range(max_retries):
            try:
                import cohere
                co = cohere.ClientV2(api_key=COHERE_API_KEY)
                response = co.embed(
                    texts=[text],
                    model="embed-english-v3.0",
                    input_type="search_document",
                )
                return np.array(response.embeddings[0], dtype=np.float32)
            except Exception:
                if attempt < max_retries - 1:
                    time.sleep(0.5 * (2 ** attempt))

    # Try external service
    for attempt in range(max_retries):
        try:
            resp = requests.post(
                f"{EMBEDDING_SERVICE_URL}/embed",
                json={"texts": [text], "normalize": False},
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                return np.array(data["embeddings"][0], dtype=np.float32)
        except Exception:
            if attempt < max_retries - 1:
                time.sleep(0.5 * (2 ** attempt))

    with _status_lock:
        _status.failed_embeddings += 1
    return None


# ── FAISS index management ─────────────────────────────────────────────────

_faiss_indices: dict[str, Any] = {}
_faiss_lock = threading.Lock()


def get_faiss_index(world: str) -> Any | None:
    """Get or create FAISS index for a world (GPU if available)."""
    import torch

    gpu_available = torch.cuda.is_available()

    with _faiss_lock:
        if world not in _faiss_indices:
            try:
                import faiss
                cpu_index = faiss.IndexFlatL2(EMBEDDING_DIM)
                if gpu_available:
                    try:
                        res = faiss.StandardGpuResources()
                        _faiss_indices[world] = faiss.index_cpu_to_gpu(
                            res, 0, cpu_index
                        )
                    except Exception:
                        _faiss_indices[world] = cpu_index
                else:
                    _faiss_indices[world] = cpu_index
            except ImportError:
                return None
        return _faiss_indices[world]


def reset_faiss_index(world: str) -> None:
    """Drop the in-memory FAISS index for a world."""
    with _faiss_lock:
        if world in _faiss_indices:
            del _faiss_indices[world]


def index_entity(world: str, entity_id: str, text: str) -> bool:
    """Embed an entity and add it to the world's FAISS index. Returns True on success."""
    embedding = embed_text(text)
    if embedding is None:
        return False

    index = get_faiss_index(world)
    if index is None:
        return False

    from mythos_backend.services.world_data import load_vectors_metadata, save_vectors_metadata

    next_pos = index.ntotal
    index.add(np.array([embedding]))

    metadata = load_vectors_metadata(world)
    metadata["entries"].append({
        "id": entity_id,
        "index": next_pos,
    })
    save_vectors_metadata(world, metadata)
    return True
