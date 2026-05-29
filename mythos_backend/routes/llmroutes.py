"""
LLM inference routes.

POST /llm/generate   → text generation
POST /llm/critique   → critique/analysis
GET  /llm/providers  → list available providers
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from mythos_backend.core.llm import get_llm_for_critique, get_llm_for_generation, invoke_llm
from mythos_backend.models.request import LLMRequest

router = APIRouter(prefix="/llm", tags=["llm"])


@router.post("/generate")
def llm_generate(req: LLMRequest):
    """Generate text using the configured LLM provider."""
    try:
        llm = get_llm_for_generation(model=req.model, temperature=req.temperature)
        result = invoke_llm(llm, req.prompt)
        return {"result": result, "model": req.model, "provider": _provider_name(llm)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {e}")


@router.post("/critique")
def llm_critique(req: LLMRequest):
    """Run critique/analysis using the configured LLM provider."""
    try:
        llm = get_llm_for_critique(model=req.model or None, temperature=req.temperature)
        result = invoke_llm(llm, req.prompt)
        return {"result": result, "model": req.model, "provider": _provider_name(llm)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Critique failed: {e}")


@router.get("/providers")
def list_providers():
    from mythos_backend.core.llm import get_provider_state, LLM_PROVIDER
    state = get_provider_state()
    return {
        "active_provider": LLM_PROVIDER,
        "available": state,
    }


def _provider_name(llm) -> str:
    if isinstance(llm, dict):
        return llm.get("provider", "unknown")
    return "ollama"
