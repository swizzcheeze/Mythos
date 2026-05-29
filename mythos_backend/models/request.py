"""
Request/response models for API endpoints.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ArchetypeAnalysisRequest(BaseModel):
    character_name: str = Field(..., min_length=1, max_length=256)
    description: str = Field(..., min_length=1, max_length=10_000)
    style: str = Field(default="Jungian")


class MultiArchetypeRequest(BaseModel):
    character_name: str = Field(..., min_length=1, max_length=256)
    description: str = Field(..., min_length=1, max_length=10_000)
    styles: str = Field(..., description="Comma-separated list of framework names")
    max_frameworks: int = Field(default=5, ge=1, le=10)


class LLMRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=20_000)
    model: str | None = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)


class EmbeddingStatusResponse(BaseModel):
    enabled: bool
    source: str
    model_name: str
    last_error: str | None = None
