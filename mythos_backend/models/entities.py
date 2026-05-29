"""
Entity models using Pydantic v2 discriminated unions.

Every saved entity has an `entity_type` discriminator field.
This eliminates the "persona saved as world" bug — the type is
enforced at validation time, not left to inference.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, Field, TypeAdapter


class EntityType(str, Enum):
    """Discriminator values for all saved entities."""
    CHARACTER = "character"
    WORLD = "world"
    LORE = "lore"
    FACTION = "faction"
    LOCATION = "location"
    ARTIFACT = "artifact"
    CREATURE = "creature"
    EVENT = "event"
    CULTURE = "culture"
    CONFLICT = "conflict"
    RITUAL = "ritual"
    MAGIC_SYSTEM = "magic_system"


class EntityBase(BaseModel):
    """Base model for every persistent entity."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    entity_type: EntityType
    name: str = Field(..., min_length=1, max_length=256)
    content: str = Field(default="", max_length=50_000)
    tags: list[str] = Field(default_factory=list)
    world: str = Field(default="default")
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class CharacterEntity(EntityBase):
    """A character / NPC / persona."""
    entity_type: Literal[EntityType.CHARACTER] = EntityType.CHARACTER
    aliases: list[str] = Field(default_factory=list)
    traits: list[str] = Field(default_factory=list)
    background: str = Field(default="")
    motivation: str = Field(default="")
    flaws: list[str] = Field(default_factory=list)


class WorldEntity(EntityBase):
    """A world / setting / campaign."""
    entity_type: Literal[EntityType.WORLD] = EntityType.WORLD
    central_theme: str = Field(default="")
    tone: str = Field(default="")
    era: str = Field(default="")


class LoreEntity(EntityBase):
    """Generic lore entry — the default catch-all."""
    entity_type: Literal[EntityType.LORE] = EntityType.LORE
    category: str = Field(default="")


class FactionEntity(EntityBase):
    """A faction / guild / organization."""
    entity_type: Literal[EntityType.FACTION] = EntityType.FACTION
    purpose: str = Field(default="")
    leadership: str = Field(default="")
    allies: list[str] = Field(default_factory=list)
    enemies: list[str] = Field(default_factory=list)


class LocationEntity(EntityBase):
    """A location / region / landmark."""
    entity_type: Literal[EntityType.LOCATION] = EntityType.LOCATION
    loc_type: str = Field(default="")
    climate: str = Field(default="")
    inhabitants: str = Field(default="")


class ArtifactEntity(EntityBase):
    """An item / artifact / object."""
    entity_type: Literal[EntityType.ARTIFACT] = EntityType.ARTIFACT
    powers: str = Field(default="")
    curse: str = Field(default="")
    current_location: str = Field(default="")


class CreatureEntity(EntityBase):
    """A creature / beast / monster."""
    entity_type: Literal[EntityType.CREATURE] = EntityType.CREATURE
    species: str = Field(default="")
    abilities: list[str] = Field(default_factory=list)
    threat_level: str = Field(default="")


class EventEntity(EntityBase):
    """An event / war / cataclysm."""
    entity_type: Literal[EntityType.EVENT] = EntityType.EVENT
    scale: str = Field(default="")
    date_era: str = Field(default="")
    outcome: str = Field(default="")


class CultureEntity(EntityBase):
    """A culture / society."""
    entity_type: Literal[EntityType.CULTURE] = EntityType.CULTURE
    population: str = Field(default="")
    beliefs: list[str] = Field(default_factory=list)


class ConflictEntity(EntityBase):
    """A conflict / war / tension."""
    entity_type: Literal[EntityType.CONFLICT] = EntityType.CONFLICT
    sides: list[str] = Field(default_factory=list)
    stakes: str = Field(default="")


class RitualEntity(EntityBase):
    """A ritual / ceremony."""
    entity_type: Literal[EntityType.RITUAL] = EntityType.RITUAL
    purpose: str = Field(default="")
    requirements: list[str] = Field(default_factory=list)
    cost: str = Field(default="")


class MagicSystemEntity(EntityBase):
    """A magic system / power system."""
    entity_type: Literal[EntityType.MAGIC_SYSTEM] = EntityType.MAGIC_SYSTEM
    source: str = Field(default="")
    limitations: list[str] = Field(default_factory=list)
    costs: list[str] = Field(default_factory=list)


# Discriminated union — Pydantic selects the correct model based on entity_type
_SavedEntityUnion = Union[
    CharacterEntity,
    WorldEntity,
    LoreEntity,
    FactionEntity,
    LocationEntity,
    ArtifactEntity,
    CreatureEntity,
    EventEntity,
    CultureEntity,
    ConflictEntity,
    RitualEntity,
    MagicSystemEntity,
]

# TypeAdapter for validating any entity dict → correct subclass
SavedEntity: TypeAdapter[_SavedEntityUnion] = TypeAdapter(
    Annotated[_SavedEntityUnion, Field(discriminator="entity_type")]
)


class EntityUpdateRequest(BaseModel):
    """Partial update for an existing entity. Only top-level fields."""
    name: str | None = None
    content: str | None = None
    tags: list[str] | None = None
    model_config = {"extra": "allow"}
