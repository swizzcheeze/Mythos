"""
Archetype routes — character analysis through storytelling frameworks.

POST /archetypes/analyze         → single-framework analysis
POST /archetypes/analyze-multi   → multi-framework composite
GET  /archetypes/styles          → list all frameworks
"""

from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import APIRouter

from mythos_backend.services.archetype import analyze_multi, analyze_single

router = APIRouter(prefix="/archetypes", tags=["archetypes"])


class ArchetypeAnalysisRequest(BaseModel):
    character_name: str = Field(..., min_length=1, max_length=256)
    description: str = Field(..., min_length=1, max_length=10_000)
    style: str = Field(default="Jungian")


class MultiArchetypeRequest(BaseModel):
    character_name: str = Field(..., min_length=1, max_length=256)
    description: str = Field(..., min_length=1, max_length=10_000)
    styles: str = Field(..., description="Comma-separated list of framework names")
    max_frameworks: int = Field(default=5, ge=1, le=10)


_VALID_STYLES = {
    "Jungian", "Disney", "James Cameron", "General", "Fantasy",
    "Gothic", "Dark Gothic", "Romance", "Mystery", "Adventure",
    "Norse", "Mythological", "Greek", "Horror", "Sci-Fi",
    "Quantum Physics", "Medieval", "C.S. Lewis", "Stephen King",
    "Alfred Hitchcock", "Japanese", "Korean",
}


@router.post("/analyze")
def archetype_analysis(req: ArchetypeAnalysisRequest):
    """Analyze a character through a single archetype framework."""
    style = req.style if req.style in _VALID_STYLES else "Jungian"
    return analyze_single(req.character_name, req.description, style)


@router.post("/analyze-multi")
def multi_archetype_analysis(req: MultiArchetypeRequest):
    """Blend multiple archetype frameworks for composite analysis."""
    return analyze_multi(
        req.character_name,
        req.description,
        req.styles,
        req.max_frameworks,
    )


@router.get("/styles")
def list_styles():
    from mythos_backend.models.archetypes import ARCHETYPE_DEFINITIONS
    return {
        "available_styles": list(ARCHETYPE_DEFINITIONS.keys()),
        "total_styles": len(ARCHETYPE_DEFINITIONS),
        "frameworks": {
            name: list(archetypes.keys())
            for name, archetypes in ARCHETYPE_DEFINITIONS.items()
        },
    }
