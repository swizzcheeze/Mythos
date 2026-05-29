"""
Creation session service — per-world interactive creation workflows.

Each session is scoped to a (world, session_id) pair, fixing the
global-session bug from the original where world switches leaked state.
"""

from __future__ import annotations

import uuid
from typing import Any

# ── Template definitions ───────────────────────────────────────────────────

TEMPLATES: dict[str, dict[str, Any]] = {
    "character": {
        "sections": {
            "Basic Info": ["Name", "Age/Era", "Occupation/Role", "Physical Description"],
            "Core Identity": ["Primary Motivation", "Fatal Flaw", "Greatest Fear", "Defining Trait"],
            "Background": ["Origin Story", "Formative Event", "Relationships", "Current Status"],
            "Abilities": ["Skills/Powers", "Weaknesses", "Equipment/Tools", "Special Abilities"],
            "Development": ["Character Arc", "Internal Conflict", "External Conflict", "Potential Endings"],
        },
        "prompts": [
            "What secret does this character keep from everyone?",
            "How would they react under extreme pressure?",
            "What would they sacrifice everything for?",
            "What's the one thing they refuse to do, no matter what?",
        ],
        "entity_type": "character",
    },
    "world": {
        "sections": {
            "Core Identity": ["World Name", "Central Theme", "Tone/Atmosphere", "Era/Timeline"],
            "Geography": ["Major Regions", "Landforms", "Climate Zones", "Natural Wonders"],
            "Cultures": ["Dominant Cultures", "Languages", "Shared Traditions", "Cultural Conflicts"],
            "History & Myth": ["Founding Event", "Myths/Legends", "Cataclysms", "Turning Points"],
            "Economy & Resources": ["Key Resources", "Trade Hubs", "Scarce Commodities", "Economic Tensions"],
            "Magic / Technology": ["Systems", "Limitations", "Unique Innovations", "Forbidden Knowledge"],
            "Factions & Power": ["Major Factions", "Power Balance", "Hidden Influences", "Emerging Threats"],
            "Ecology": ["Biome Types", "Keystone Species", "Environmental Pressures", "Extinction Risks"],
            "Conflicts & Tensions": ["Active Conflicts", "Rising Tensions", "Moral Dilemmas", "Imminent Crises"],
            "Hooks": ["Adventure Hooks", "Mysteries", "Unanswered Questions", "Future Arcs"],
        },
        "prompts": [
            "What unseen force quietly shapes the world's destiny?",
            "Which region holds a secret that could rewrite history?",
            "What resource is on the brink of collapse and why?",
            "What contradiction defines this world's identity?",
        ],
        "entity_type": "world",
    },
    "location": {
        "sections": {
            "Geography": ["Name", "Type (city/wilderness/realm)", "Climate/Weather", "Notable Landmarks"],
            "Atmosphere": ["Mood/Tone", "Sensory Details", "Unique Features", "Dangers"],
            "History": ["Founding/Creation", "Major Events", "Current State", "Legends/Myths"],
            "Inhabitants": ["Population", "Factions/Groups", "Power Structure", "Cultural Practices"],
            "Resources": ["Economy", "Technology Level", "Magic/Special Properties", "Strategic Value"],
        },
        "prompts": [
            "What's the most dangerous thing about this place?",
            "What secret does the location itself hide?",
            "How has this place changed over time?",
            "What makes people want to come here — or flee?",
        ],
        "entity_type": "location",
    },
    "faction": {
        "sections": {
            "Identity": ["Name", "Type (guild/cult/army/corporation)", "Symbol/Colors", "Motto"],
            "Structure": ["Leadership", "Hierarchy", "Size/Reach", "Recruitment"],
            "Goals": ["Primary Objective", "Long-term Vision", "Hidden Agenda", "Methods"],
            "Resources": ["Wealth", "Military/Power", "Influence", "Technology/Magic"],
            "Relations": ["Allies", "Enemies", "Neutrals", "Internal Divisions"],
        },
        "prompts": [
            "What does this faction do in the shadows that no one knows about?",
            "What would cause this organization to collapse from within?",
            "How do they justify morally questionable actions?",
            "What's their greatest achievement and worst failure?",
        ],
        "entity_type": "faction",
    },
    "magic_system": {
        "sections": {
            "Fundamentals": ["Source of Power", "How it's Accessed", "Who Can Use It", "Learning Process"],
            "Mechanics": ["Limitations", "Costs/Consequences", "Forbidden Practices", "Power Scaling"],
            "Applications": ["Combat Uses", "Utility Uses", "Ritual/Ceremonial", "Everyday Life"],
            "Society": ["Cultural Attitude", "Legal Status", "Famous Practitioners", "Organizations"],
            "Metaphysics": ["Theoretical Limits", "Unexplained Phenomena", "Dangerous Knowledge", "Ultimate Power"],
        },
        "prompts": [
            "What's the terrible price for using the most powerful magic?",
            "How does magic corruption or madness manifest?",
            "What happens when someone breaks the fundamental rules?",
            "What's the one thing magic absolutely cannot do?",
        ],
        "entity_type": "magic_system",
    },
    "creature": {
        "sections": {
            "Biology": ["Species Name", "Size/Appearance", "Habitat", "Lifespan"],
            "Behavior": ["Intelligence Level", "Social Structure", "Diet", "Reproduction"],
            "Abilities": ["Natural Weapons", "Special Powers", "Senses", "Defenses"],
            "Interaction": ["Threat Level", "Communication", "Domestication", "Value to Humans"],
            "Lore": ["Origin Myth", "Cultural Significance", "Famous Specimens", "Extinction Status"],
        },
        "prompts": [
            "What's the most terrifying thing about encountering this creature?",
            "How has humanity adapted to its existence?",
            "What happens if you kill one?",
            "What ancient warning do people tell about this creature?",
        ],
        "entity_type": "creature",
    },
    "artifact": {
        "sections": {
            "Description": ["Name", "Appearance", "Size/Weight", "Materials"],
            "Power": ["Primary Function", "Secondary Effects", "Activation Method", "Limitations"],
            "History": ["Creator/Origin", "Previous Owners", "Famous Uses", "Current Location"],
            "Curse": ["Hidden Cost", "Corruption Effect", "Binding Condition", "Destruction Method"],
            "Significance": ["Cultural Impact", "Who Seeks It", "Prophecies", "True Purpose"],
        },
        "prompts": [
            "What terrible truth does the artifact reveal to its bearer?",
            "How does it change those who possess it?",
            "What's the one thing you must never do with it?",
            "Why was it really created, beyond the obvious purpose?",
        ],
        "entity_type": "artifact",
    },
    "event": {
        "sections": {
            "Overview": ["Event Name", "Type (war/catastrophe/celebration)", "Date/Era", "Scale"],
            "Cause": ["Trigger Event", "Underlying Tensions", "Key Players", "Point of No Return"],
            "Course": ["Major Turning Points", "Duration", "Casualties/Impact", "Key Battles/Moments"],
            "Aftermath": ["Winners/Losers", "Territorial Changes", "Long-term Effects", "Lessons Learned"],
            "Memory": ["How it's Commemorated", "Competing Narratives", "Unresolved Issues", "Prophecy/Repetition"],
        },
        "prompts": [
            "What truth about the event has been suppressed or forgotten?",
            "Who secretly benefited from the tragedy?",
            "How did this event change the world irreversibly?",
            "What would have happened if it never occurred?",
        ],
        "entity_type": "event",
    },
    "culture": {
        "sections": {
            "Identity": ["Name", "Population", "Geographic Range", "Defining Characteristic"],
            "Values": ["Core Beliefs", "Taboos", "Virtues", "Coming-of-Age"],
            "Daily Life": ["Economy", "Gender Roles", "Family Structure", "Education"],
            "Arts": ["Music/Dance", "Visual Arts", "Literature/Storytelling", "Architecture"],
            "Spirituality": ["Religion/Philosophy", "Rituals", "Death Customs", "Sacred Sites"],
        },
        "prompts": [
            "What do outsiders misunderstand about this culture?",
            "What shameful secret does the entire culture keep?",
            "How do they view death and the afterlife?",
            "What would be considered the highest honor?",
        ],
        "entity_type": "culture",
    },
    "conflict": {
        "sections": {
            "Stakes": ["What's at Risk", "Who's Involved", "Why Now", "Scope"],
            "Sides": ["Protagonist Forces", "Antagonist Forces", "Neutral Parties", "Hidden Players"],
            "Resources": ["Military Strength", "Economic Power", "Magic/Technology", "Morale"],
            "Escalation": ["Initial Dispute", "Provocations", "Point of No Return", "Total War"],
            "Resolution": ["Possible Outcomes", "Victory Conditions", "Compromise Options", "Pyrrhic Scenarios"],
        },
        "prompts": [
            "What would make both sides realize they've already lost?",
            "What secret alliance could change everything?",
            "How might the conflict end in unexpected tragedy?",
            "What's the one thing neither side will negotiate?",
        ],
        "entity_type": "conflict",
    },
    "ritual": {
        "sections": {
            "Purpose": ["Intent", "What It Achieves", "Who Performs It", "When/Where"],
            "Requirements": ["Materials", "Participants", "Location", "Timing"],
            "Procedure": ["Preparation Steps", "Core Ceremony", "Incantations/Actions", "Duration"],
            "Cost": ["Sacrifice Required", "Energy Drain", "Side Effects", "Taboo Breaking"],
            "Consequences": ["Immediate Effects", "Long-term Changes", "Failure Results", "Unforeseen Outcomes"],
        },
        "prompts": [
            "What happens if the ritual is interrupted halfway?",
            "What's the terrible truth about why this ritual exists?",
            "How does performing it change the ritualist forever?",
            "What forbidden variation of this ritual exists?",
        ],
        "entity_type": "ritual",
    },
}


def get_template(template_type: str) -> dict[str, Any] | None:
    return TEMPLATES.get(template_type)


def list_template_types() -> list[str]:
    return list(TEMPLATES.keys())


# ── Session operations (all per-world) ─────────────────────────────────────

def start_session(world: str, template_type: str, style: str = "Fantasy") -> dict:
    """Create a new session in a world. Returns session data."""
    template = TEMPLATES.get(template_type)
    if not template:
        raise ValueError(f"Unknown template type: {template_type}")

    from mythos_backend.services.world_data import put_session

    session_id = str(uuid.uuid4())
    session_data = {
        "id": session_id,
        "template_type": template_type,
        "style": style,
        "sections": template["sections"],
        "prompts": template["prompts"],
        "entity_type": template.get("entity_type", "lore"),
        "filled": {},
        "history": [],
    }
    put_session(world, session_id, session_data)
    return session_data


def update_session(world: str, session_id: str, updates: dict[str, dict]) -> dict:
    """Update session fields. Returns updated session with progress info."""
    from mythos_backend.services.world_data import get_session, put_session

    session = get_session(world, session_id)
    if not session:
        raise KeyError(f"Session {session_id} not found in world '{world}'")

    filled = session.setdefault("filled", {})
    warnings = []

    for section, fields in updates.items():
        if not isinstance(fields, dict):
            warnings.append(
                f"Section '{section}' has non-dict value (got {type(fields).__name__}); "
                f"expected {{field: value}} mapping."
            )
            continue
        fsec = filled.setdefault(section, {})
        valid_fields = session.get("sections", {}).get(section, [])
        for field, value in fields.items():
            fsec[field] = value
            if field not in valid_fields:
                warnings.append(f"Unknown field '{field}' in section '{section}' (stored anyway).")

    session.setdefault("history", []).append({"type": "update", "payload": updates})
    put_session(world, session_id, session)

    # Compute progress
    total = sum(len(f) for f in session["sections"].values())
    completed = sum(
        1
        for sec_fields in filled.values()
        for v in sec_fields.values()
        if (isinstance(v, str) and v.strip())
        or (isinstance(v, list) and any(str(x).strip() for x in v))
    )

    result = {
        "session_id": session_id,
        "progress": {"completed_fields": completed, "total_fields": total},
        "filled": filled,
        "sections": session["sections"],
        "message": "Session updated.",
    }
    if warnings:
        result["warnings"] = warnings
        result["hint"] = "Ensure updates structure is { 'Section Name': { 'Field Name': 'value' } }"
    return result


def get_session_state(world: str, session_id: str) -> dict:
    """Get the full state of a session."""
    from mythos_backend.services.world_data import get_session

    session = get_session(world, session_id)
    if not session:
        raise KeyError(f"Session {session_id} not found in world '{world}'")
    return session


def finalize_session(
    world: str,
    session_id: str,
    topic: str | None = None,
    tags: list[str] | None = None,
) -> dict:
    """Build a preview from a session. Returns preview + proposed entity."""
    from mythos_backend.services.world_data import get_session

    session = get_session(world, session_id)
    if not session:
        raise KeyError(f"Session {session_id} not found in world '{world}'")

    lines = [f"Type: {session['template_type']} | Style: {session['style']}"]
    for section, fields in session["sections"].items():
        lines.append(f"\n## {section}")
        for field in fields:
            val = session.get("filled", {}).get(section, {}).get(field)
            if isinstance(val, list):
                cleaned = [str(v).strip() for v in val if str(v).strip()]
                if cleaned:
                    lines.append(f"- {field}:")
                    for item in cleaned:
                        lines.append(f"  - {item}")
                else:
                    lines.append(f"- {{field}}: [ ]")
            elif isinstance(val, str):
                if ";" in val:
                    parts = [p.strip() for p in val.split(";") if p.strip()]
                    if len(parts) > 1:
                        lines.append(f"- {field}:")
                        for item in parts:
                            lines.append(f"  - {item}")
                    else:
                        lines.append(f"- {field}: {parts[0] if parts else '[ ]'}")
                else:
                    lines.append(f"- {field}: {val.strip() if val.strip() else '[ ]'}")
            else:
                lines.append(f"- {field}: [ ]")

    lines.append("\n-- Creative Prompts --")
    for p in session["prompts"]:
        lines.append(f"- {p}")

    preview = "\n".join(lines)
    suggested_tags = tags if tags is not None else [session["template_type"]]
    proposed_topic = topic or f"New {session['template_type'].title()} ({session['style']})"

    return {
        "session_id": session_id,
        "preview": preview,
        "proposed_entity": {
            "entity_type": session.get("entity_type", session["template_type"]),
            "name": proposed_topic,
            "content": preview,
            "tags": suggested_tags,
            "world": world,
        },
        "message": "Preview assembled. Use the entity_type to save via the proper endpoint.",
    }


def list_sessions(world: str, limit: int | None = None) -> list[dict]:
    """List sessions for a world with progress summary."""
    from mythos_backend.services.world_data import load_sessions

    sessions = load_sessions(world)
    result = []
    for s in sessions.values():
        # Skip old-format sessions that don't have the expected structure
        if "id" not in s or "template_type" not in s:
            continue
        filled = s.get("filled", {})
        total = sum(len(f) for f in s.get("sections", {}).values())
        completed = sum(
            1
            for sec_fields in filled.values()
            for v in sec_fields.values()
            if (isinstance(v, str) and v.strip())
            or (isinstance(v, list) and any(str(x).strip() for x in v))
        )
        result.append({
            "id": s["id"],
            "template_type": s["template_type"],
            "style": s["style"],
            "progress": f"{completed}/{total}",
        })
    if limit:
        result = result[:limit]
    return result
