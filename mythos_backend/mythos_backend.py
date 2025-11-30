import json
import random
import os
import uuid
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# --- Configuration & State ---
# Path defined by Docker Compose to point to the host volume mount for persistence
# Keeping backward-compat: default world uses this exact path/file
LORE_DB_BASE_PATH = os.getenv("LORE_DB_PATH", "world_data/lore_db.json")
ACTIVE_WORLD_NAME = "default"

def _current_db_path() -> str:
    """Return the active world's lore DB file path.
    - default world uses the legacy LORE_DB_BASE_PATH directly
    - other worlds live under <base_dir>/worlds/<name>/lore_db.json
    """
    if ACTIVE_WORLD_NAME == "default":
        return LORE_DB_BASE_PATH
    base_dir = os.path.dirname(LORE_DB_BASE_PATH)
    return os.path.join(base_dir, "worlds", ACTIVE_WORLD_NAME, "lore_db.json")

ARCHETYPE_DEFINITIONS = {
    "Jungian": {
        "Hero": "The protagonist, usually driven by a mission to save the day.",
        "Shadow": "The dark side, representing repressed traits and the unknown potential.",
        "Anima/Animus": "The unconscious feminine/masculine qualities that influence the opposite gender in the ego.",
        "Wise Old Man/Woman": "The guide or sage, offering wisdom and a solution to the central dilemma."
    },
    "Disney": {
        "The Dreamer": "An optimistic character who believes in magic, wishes, and the power of dreams to transform reality.",
        "The Villain": "A charismatic antagonist driven by vanity, greed, or a desire for control, often with tragic backstory.",
        "The Sidekick": "A loyal companion providing comic relief, emotional support, and unexpected wisdom at key moments.",
        "The Mentor": "A wise guide who sacrifices or steps back to let the protagonist discover their own strength."
    },
    "James Cameron": {
        "The Warrior": "A battle-hardened fighter who discovers humanity through connection and sacrifice.",
        "The Corporate Antagonist": "A ruthless, profit-driven entity that exploits nature or technology without moral restraint.",
        "The Indigenous Sage": "A character deeply connected to nature/tradition, representing harmony and ecological balance.",
        "The Tech Operator": "A skilled pilot or technician who bridges humanity and advanced technology/machinery."
    },
    "General": {
        "The Everyman": "An ordinary person thrust into extraordinary circumstances, relatable and grounded.",
        "The Mentor": "A guide figure who provides wisdom, training, or magical assistance to the protagonist.",
        "The Trickster": "A cunning character who bends rules, providing chaos that ultimately serves a greater purpose.",
        "The Guardian": "A protector whose loyalty and strength shield others, often at great personal cost."
    },
    "Fantasy": {
        "The Chosen One": "Destined hero with latent magical powers, often marked by prophecy or birthright.",
        "The Dark Lord": "An ancient evil seeking dominion, representing corruption of power and immortality's curse.",
        "The Quest Companion": "A diverse ally bringing unique skills (warrior, mage, rogue) essential to the journey.",
        "The Wise Wizard": "An ancient magic user who understands the balance between light and dark, order and chaos."
    },
    "Gothic": {
        "The Haunted Soul": "A tormented character pursued by past sins, supernatural forces, or family curses.",
        "The Byronic Hero": "A brooding, isolated figure with a dark past, attractive yet dangerous and morally ambiguous.",
        "The Innocent": "A pure character whose presence exposes the corruption around them, often leading to tragedy.",
        "The Ancestral Curse": "A legacy of darkness passed through bloodlines, binding characters to inherited doom."
    },
    "Dark Gothic": {
        "The Vampire": "An immortal predator representing seduction, eternal hunger, and the horror of unending existence.",
        "The Mad Scientist": "An obsessive genius who transgresses natural boundaries, creating monsters through forbidden knowledge.",
        "The Ghost": "A restless spirit bound to a location or person, unable to move on due to unresolved trauma.",
        "The Corrupted Priest": "A fallen religious figure whose faith twisted into fanaticism, hypocrisy, or demonic possession."
    },
    "Romance": {
        "The Star-Crossed Lover": "A passionate character whose love is forbidden by society, fate, or circumstance.",
        "The Protector": "Someone who falls in love while guarding or rescuing another, torn between duty and desire.",
        "The Rival-to-Lover": "An antagonist whose opposition masks attraction, creating tension that transforms into romance.",
        "The Second Chance": "A character seeking redemption through love, haunted by past relationship failures or losses."
    },
    "Mystery": {
        "The Detective": "A brilliant investigator driven by justice, logic, and an obsessive need to solve puzzles.",
        "The Red Herring": "A character designed to mislead, whose suspicious behavior conceals innocence or irrelevance.",
        "The Hidden Culprit": "An unexpected villain whose ordinary facade masks guilt, motive perfectly concealed.",
        "The Witness": "Someone who knows crucial information but is silenced, threatened, or unreliable due to trauma."
    },
    "Adventure": {
        "The Explorer": "A fearless adventurer driven by discovery, treasure, or the thrill of the unknown.",
        "The Reluctant Hero": "An ordinary person forced into danger, growing into courage through trials and necessity.",
        "The Rival Adventurer": "A competing treasure hunter or explorer whose methods clash but goals may align.",
        "The Local Guide": "A native expert whose knowledge of terrain, culture, or danger becomes essential for survival."
    },
    "Norse": {
        "The Berserker": "A warrior consumed by battle rage, channeling primal fury at the cost of control and sanity.",
        "The Völva": "A seeress who reads fate through runes and visions, bound by the immutable threads of wyrd.",
        "The Oath-Breaker": "One cursed by broken vows, hunted by gods and men, seeking impossible redemption.",
        "The Skald": "A poet-warrior whose words shape reality, preserving glory or casting curses through saga."
    },
    "Mythological": {
        "The Demigod": "Half-mortal, half-divine, struggling between human weakness and godly ambition.",
        "The Titan": "An ancient primordial force representing chaos, nature, or primal power before civilization.",
        "The Oracle": "A conduit for prophecy whose visions burden them with knowledge they cannot change.",
        "The Trickster God": "A divine shapeshifter who disrupts order, teaching through chaos and deception."
    },
    "Greek": {
        "The Tragic Hero": "A noble figure whose fatal flaw (hamartia) leads to inevitable downfall despite good intentions.",
        "The Fury": "A vengeful spirit embodying divine retribution, punishing hubris and injustice without mercy.",
        "The Philosopher-King": "A wise ruler who governs through reason, justice, and understanding of truth.",
        "The Labyrinth Keeper": "Guardian of mysteries and forbidden knowledge, testing heroes through impossible trials."
    },
    "Horror": {
        "The Final Girl": "A survivor whose moral purity and resourcefulness allow escape from unspeakable evil.",
        "The Harbinger": "A cryptic stranger who warns of coming doom, ignored until it's too late.",
        "The Possessed": "An innocent vessel corrupted by malevolent force, losing autonomy to darkness.",
        "The Unseen Terror": "An entity whose true form remains hidden, more terrifying for what isn't shown."
    },
    "Sci-Fi": {
        "The Synthetic": "An artificial being questioning consciousness, humanity, and the nature of existence.",
        "The Xenobiologist": "A scientist bridging humanity and alien life, translating the incomprehensible.",
        "The Post-Human": "An evolved or augmented being who has transcended biological limitations.",
        "The Time Paradox": "A character caught in causal loops, their actions creating their own existence or doom."
    },
    "Quantum Physics": {
        "The Observer": "One whose perception collapses probability waves, making reality through observation.",
        "The Entangled": "Two beings connected across space-time, sharing states and fates instantaneously.",
        "The Superposition": "A character existing in multiple states simultaneously until forced to choose one path.",
        "The Uncertainty": "Someone who cannot know both position and momentum, perpetually incomplete in understanding."
    },
    "Medieval": {
        "The Knight-Errant": "A wandering warrior bound by chivalric code, seeking worthy quests and honorable combat.",
        "The Sovereign": "A monarch balancing divine right, feudal duty, and the burden of the crown.",
        "The Heretic": "A truth-seeker branded blasphemer, challenging church doctrine at peril of stake.",
        "The Plague Doctor": "A healer walking the line between medicine and superstition amid death's shadow."
    },
    "C.S. Lewis": {
        "The Redeemed Sinner": "A flawed character saved by grace, transformed through sacrifice and unconditional love.",
        "The Aslan Figure": "A Christ-like sacrificial hero whose death brings resurrection and restoration.",
        "The Pevensie": "An ordinary person called to extraordinary destiny, growing through trials in a magical realm.",
        "The Screwtape": "A tempter who reveals evil's banality through bureaucratic corruption of virtue."
    },
    "Stephen King": {
        "The Small-Town Everyman": "An ordinary person in a familiar setting confronting supernatural or cosmic horror.",
        "The Psychic Child": "A young protagonist with paranormal gifts, vulnerable yet powerful against evil.",
        "The Corrupted Writer": "An artist whose creativity becomes a conduit for darkness, obsession, or madness.",
        "The Returned": "Someone who came back wrong—from death, the past, or another realm—bringing trauma."
    },
    "Alfred Hitchcock": {
        "The Wrong Man": "An innocent caught in circumstances beyond control, paranoia mounting as escape narrows.",
        "The Blonde": "A cool, elegant figure concealing dark secrets or dangerous obsessions beneath grace.",
        "The Voyeur": "An observer whose watching crosses ethical lines, implicated in the horror they witness.",
        "The Mother": "A dominating maternal figure whose love becomes suffocating control or psychological prison."
    },
    "Japanese": {
        "The Ronin": "A masterless samurai torn between honor and survival, seeking purpose after losing their lord.",
        "The Yokai": "A supernatural spirit—trickster, guardian, or vengeful—embodying nature's mysterious power.",
        "The Salary Man": "A modern archetype ground down by corporate duty, seeking meaning in conformity's cracks.",
        "The Onryo": "A vengeful ghost bound by wrongful death, unable to rest until justice or revenge."
    },
    "Korean": {
        "The Han-Bearer": "One carrying deep sorrow (han) from historical trauma, injustice, or generational pain.",
        "The Chaebol Heir": "A privileged successor to corporate dynasty, torn between duty and personal desire.",
        "The Mudang": "A shaman mediating between living and dead, channeling spirits through ritual and trance.",
        "The Jeong-Keeper": "Someone bound by deep emotional connection (jeong), loyalty transcending logic or self."
    }
}

def load_lore_db() -> List[Dict[str, Any]]:
    """Loads the lore database from a persistent JSON file."""
    # Ensure the directory exists before trying to load/save
    db_path = _current_db_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    try:
        with open(db_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        print(f"Warning: {db_path} is corrupted. Starting with empty database.")
        return []

def save_lore_db(db: List[Dict[str, Any]]):
    """Saves the lore database to a local JSON file for persistence."""
    db_path = _current_db_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    with open(db_path, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

# Initialize database
LORE_DATABASE = load_lore_db()

# --- Semantic Scoring Helpers (lightweight, no external ML deps) ---
_SEMANTIC_SYNONYMS = {
    "power": ["strength", "might", "force"],
    "fear": ["terror", "dread", "anxiety"],
    "magic": ["arcane", "sorcery", "mystic"],
    "death": ["mortality", "doom", "end"],
    "love": ["affection", "devotion", "romance"],
    "rage": ["fury", "anger", "wrath"],
    "wisdom": ["knowledge", "insight", "sagacity"],
    "shadow": ["dark", "hidden", "unknown"],
    "destiny": ["fate", "wyrd", "purpose"],
    "time": ["chronology", "temporal", "era"],
    "spirit": ["soul", "essence", "ghost"],
}

def _semantic_tokenize(text: str) -> List[str]:
    return [t for t in ''.join(c if c.isalnum() else ' ' for c in text).lower().split() if t]

def _expand_tokens(tokens: List[str]) -> set:
    expanded = set(tokens)
    for t in list(tokens):
        if t in _SEMANTIC_SYNONYMS:
            expanded.update(_SEMANTIC_SYNONYMS[t])
    return expanded

def _semantic_score(desc_tokens: List[str], definition: str) -> float:
    if not desc_tokens:
        return 0.0
    def_tokens = _semantic_tokenize(definition)
    desc_set = _expand_tokens(desc_tokens)
    def_set = _expand_tokens(def_tokens)
    overlap = desc_set.intersection(def_set)
    if not overlap:
        return 0.0
    # Weighted score: overlap size / (sqrt(len(desc_set)) * sqrt(len(def_set)))
    import math
    return len(overlap) / (math.sqrt(len(desc_set)) * math.sqrt(len(def_set)))

# --- Pydantic Schemas for Tools ---

class ArchetypeRequest(BaseModel):
    character_name: str = Field(..., description="The name of the character or entity to analyze.")
    description: str = Field(..., description="A brief bio or description of the character.")
    style: str = Field(default="Jungian", description="Archetype style to analyze: 'Jungian', 'Disney', 'James Cameron', 'General', 'Fantasy', 'Gothic', 'Dark Gothic', 'Romance', 'Mystery', 'Adventure', 'Norse', 'Mythological', 'Greek', 'Horror', 'Sci-Fi', 'Quantum Physics', 'Medieval', 'C.S. Lewis', 'Stephen King', 'Alfred Hitchcock', 'Japanese', 'Korean'.")

class LoreEntry(BaseModel):
    topic: str = Field(..., description="The title of the lore entry (e.g., 'The Obsidian War').")
    content: str = Field(..., description="The detailed narrative content.")
    tags: List[str] = Field(default=[], description="Relevant tags (e.g., ['magic', 'location', 'history', 'jungian']).")

class InspirationRequest(BaseModel):
    style: str = Field(None, description="The desired creative style or theme (e.g., 'cosmic horror', 'dark fantasy').")

class LoreSearchRequest(BaseModel):
    search_query: str = Field(None, description="Optional search term to filter lore entries by topic or content.")
    tags: List[str] = Field(default=[], description="Optional tags to filter entries (e.g., ['magic', 'ritual']).")

class CreationModeRequest(BaseModel):
    template_type: str = Field(..., description="Template type: 'character', 'location', 'faction', 'magic_system', 'creature', 'artifact', 'event', 'culture', 'conflict', 'ritual'.")
    style: str = Field(default="Fantasy", description="Creative style/genre for the template (e.g., 'Fantasy', 'Sci-Fi', 'Horror', 'Cyberpunk').")

class LoreUpdateRequest(BaseModel):
    id: int = Field(..., description="Existing lore entry ID to update.")
    topic: str | None = Field(None, description="Updated title (optional).")
    content: str | None = Field(None, description="Updated content (optional).")
    tags: List[str] | None = Field(None, description="Updated tags (optional).")

class WipeRequest(BaseModel):
    confirm: str = Field(..., description="Type 'CONFIRM' to irreversibly wipe the current world's database.")

class WorldCreateRequest(BaseModel):
    name: str = Field(..., description="World name (folder-safe).")
    select_after_create: bool = Field(default=True, description="Whether to make this the active world immediately.")

class WorldSelectRequest(BaseModel):
    name: str = Field(..., description="Existing world name to select ('default' allowed).")
    create_if_missing: bool = Field(default=False, description="Create a new empty world if it does not exist.")

class MultiArchetypeRequest(BaseModel):
    character_name: str = Field(..., description="Name of the character to analyze across multiple frameworks.")
    description: str = Field(..., description="Brief bio or description of the character.")
    styles: str = Field(..., description="Composite style string (e.g. 'Fantasy + Horror + Jungian'). Supports ',', '+', '/', 'with', 'and'.")
    max_frameworks: int = Field(default=5, description="Safety cap on number of frameworks to blend.")

# --- FastAPI Setup ---
app = FastAPI(
    title="Mythos World Engine",
    description="Backend for creative writing, worldbuilding, and character psychology tools.",
    version="1.0.0",
)

# Endpoint to test the health of the container (required by docker-compose healthcheck)
@app.get("/healthz")
def health_check():
    return {"status": "ok", "message": "Mythos Engine running and healthy."}

# --- Tool Endpoints (Called by the mythos-bridge.js) ---

@app.post("/call/mythos_archetype_analysis")
def archetype_analysis(req: ArchetypeRequest):
    """Semantically analyzes a character within a single archetype framework.
    Replaces previous random selection with lightweight semantic scoring.
    """
    style = req.style if req.style in ARCHETYPE_DEFINITIONS else "Jungian"
    definitions = ARCHETYPE_DEFINITIONS[style]

    # --- Lightweight semantic scoring utilities ---
    description = req.description.lower()
    desc_tokens = _semantic_tokenize(description)
    # Build scored list
    scored = []
    for name, definition in definitions.items():
        score = _semantic_score(desc_tokens, definition)
        scored.append((name, score))
    # Sort by descending score
    scored.sort(key=lambda x: x[1], reverse=True)

    low_signal = False
    if not scored or scored[0][1] < 0.08:  # heuristic threshold
        # Fallback to previous random approach if semantic signal weak
        low_signal = True
        primary_archetype = random.choice(list(definitions.keys()))
        secondary_archetype = random.choice(list(definitions.keys()))
        confidence_primary = 0.0
        confidence_secondary = 0.0
    else:
        primary_archetype, primary_score = scored[0]
        # pick the next distinct highest
        secondary_archetype, secondary_score = next(((n, s) for n, s in scored[1:] if n != primary_archetype), (primary_archetype, scored[0][1]))
        # Normalize confidence by dividing by max possible token overlap (approx desc token length)
        confidence_primary = round(primary_score, 3)
        confidence_secondary = round(secondary_score, 3)

    tension_score = round(abs(confidence_primary - confidence_secondary), 3)
    analysis_result = (
        f"{req.character_name} aligns with the **{primary_archetype}** archetype in {style}. "
        f"Secondary influence from **{secondary_archetype}** introduces dynamic tension."
    )
    if low_signal:
        analysis_result += " (Low semantic signal detected; archetypes selected via fallback heuristic.)"

    suggestion = (
        f"Explore how {primary_archetype} traits are stressed when {secondary_archetype} tendencies surface. "
        f"Leverage contrasting values to shape turning points and internal conflict."
    )

    return {
        "style": style,
        "character_name": req.character_name,
        "analysis_result": analysis_result,
        "primary_archetype": primary_archetype,
        "primary_definition": definitions[primary_archetype],
        "secondary_archetype": secondary_archetype,
        "secondary_definition": definitions[secondary_archetype],
        "confidence_primary": confidence_primary,
        "confidence_secondary": confidence_secondary,
        "tension_score": tension_score,
        "low_signal_fallback": low_signal,
        "suggestion": suggestion
    }

@app.post("/call/mythos_multi_archetype_analysis")
def multi_archetype_analysis(req: MultiArchetypeRequest):
    """Blend multiple archetype frameworks using semantic scoring for composite analysis."""
    # Parse styles: split by common separators and filter valid frameworks
    raw = req.styles.lower()
    tokens = [t.strip() for sep in [',', '+', '/', ' with ', ' and '] for t in raw.replace(sep, ',').split(',')]
    # Deduplicate while preserving order
    seen = set()
    resolved = []
    for token in tokens:
        if not token:
            continue
        # Fuzzy match against available keys (case-insensitive)
        match = next((k for k in ARCHETYPE_DEFINITIONS.keys() if k.lower() == token), None)
        if not match:
            # Try partial startswith
            match = next((k for k in ARCHETYPE_DEFINITIONS.keys() if k.lower().startswith(token)), None)
        if match and match not in seen:
            seen.add(match)
            resolved.append(match)
        if len(resolved) >= req.max_frameworks:
            break
    if not resolved:
        return {"error": "No valid frameworks found in styles string.", "available": list(ARCHETYPE_DEFINITIONS.keys())}

    analyses = []
    primary_traits = []
    secondary_traits = []
    all_primary_scores = []
    description_tokens = _semantic_tokenize(req.description.lower())

    for style in resolved:
        defs = ARCHETYPE_DEFINITIONS[style]
        scored = [(name, _semantic_score(description_tokens, definition)) for name, definition in defs.items()]
        scored.sort(key=lambda x: x[1], reverse=True)
        if not scored or scored[0][1] < 0.08:
            # fallback random
            primary, primary_score = random.choice(list(defs.keys())), 0.0
            secondary, secondary_score = random.choice(list(defs.keys())), 0.0
            low_signal = True
        else:
            primary, primary_score = scored[0]
            secondary, secondary_score = next(((n, s) for n, s in scored[1:] if n != primary), (primary, scored[0][1]))
            low_signal = False
        tension = round(abs(primary_score - secondary_score), 3)
        analyses.append({
            "style": style,
            "primary_archetype": primary,
            "primary_definition": defs[primary],
            "secondary_archetype": secondary,
            "secondary_definition": defs[secondary],
            "confidence_primary": round(primary_score, 3),
            "confidence_secondary": round(secondary_score, 3),
            "tension_score": tension,
            "low_signal_fallback": low_signal
        })
        primary_traits.append(primary)
        secondary_traits.append(secondary)
        all_primary_scores.append(primary_score)

    # Composite tension = variance of primary scores (diversity of dominant drives)
    if all_primary_scores:
        mean_score = sum(all_primary_scores) / len(all_primary_scores)
        variance = sum((s - mean_score) ** 2 for s in all_primary_scores) / len(all_primary_scores)
    else:
        variance = 0.0
    composite_tension = round(variance, 3)

    composite_summary = (
        f"{req.character_name} expresses blended archetypal drivers: {', '.join(primary_traits)} (primary) "
        f"counterbalanced by {', '.join(secondary_traits)} (secondary). Diversity tension metric={composite_tension}."
    )
    suggestion = (
        "Use high-tension pairs to script moral dilemmas and turning points."
    )

    return {
        "character_name": req.character_name,
        "requested_styles_raw": req.styles,
        "resolved_frameworks": resolved,
        "framework_count": len(resolved),
        "analyses": analyses,
        "composite_tension_metric": composite_tension,
        "composite_summary": composite_summary,
        "suggestion": suggestion
    }

@app.post("/call/mythos_create_lore_entry")
def create_lore_entry(entry: LoreEntry):
    """Saves a new, structured entry into the world lore database."""
    global LORE_DATABASE
    new_entry = entry.dict()
    new_entry["id"] = len(LORE_DATABASE) + 1
    LORE_DATABASE.append(new_entry)
    save_lore_db(LORE_DATABASE)

    return {
        "status": "success",
        "message": f"New lore entry '{entry.topic}' saved to world database. Total entries: {len(LORE_DATABASE)}.",
        "entry_id": new_entry["id"]
    }

@app.post("/call/mythos_update_lore_entry")
def update_lore_entry(req: LoreUpdateRequest):
    """Updates an existing lore entry by ID. Partial updates supported."""
    global LORE_DATABASE
    entry = next((e for e in LORE_DATABASE if e.get("id") == req.id), None)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Lore entry with id {req.id} not found.")

    if req.topic is not None:
        entry["topic"] = req.topic
    if req.content is not None:
        entry["content"] = req.content
    if req.tags is not None:
        entry["tags"] = req.tags

    save_lore_db(LORE_DATABASE)
    return {"status": "success", "message": f"Entry {req.id} updated.", "entry": entry}

@app.post("/call/mythos_get_inspiration")
def get_inspiration(req: InspirationRequest):
    """Generates a random, creative constraint or prompt."""
    style = req.style or "General"
    
    prompts = [
        f"The hero succeeds, but the true cost is the complete erasure of their past life. (Theme: Sacrifice, Style: {style})",
        f"Design a ritual where a character must transfer a fear to an inanimate object. What are the side effects? (Theme: Transformation, Style: {style})",
        f"Introduce a temporal paradox where the character must prevent an event that has already guaranteed their existence. (Theme: Time, Style: {style})",
    ]
    
    return {
        "inspiration": random.choice(prompts),
        "source": "Creative Constraint Generator",
        "style_hint": style
    }

@app.post("/call/mythos_list_tools")
def list_tools():
    """Returns a user-friendly menu of all available Mythos tools."""
    return {
        "available_tools": [
            {
                "name": "mythos_archetype_analysis",
                "description": "Analyze characters through 10 storytelling frameworks (Jungian, Disney, James Cameron, etc.)",
                "parameters": "character_name, description, style (optional)"
            },
            {
                "name": "mythos_create_lore_entry",
                "description": "Save worldbuilding entries to persistent database",
                "parameters": "topic, content, tags (optional)"
            },
            {
                "name": "mythos_update_lore_entry",
                "description": "Edit an existing lore entry by ID (partial updates supported)",
                "parameters": "id, topic (optional), content (optional), tags (optional)"
            },
            {
                "name": "mythos_get_inspiration",
                "description": "Generate creative writing prompts and constraints",
                "parameters": "style (optional)"
            },
            {
                "name": "mythos_list_archetype_styles",
                "description": "View all 10 archetype frameworks with their character types",
                "parameters": "none"
            },
            {
                "name": "mythos_list_lore_entries",
                "description": "Retrieve saved worldbuilding entries with optional search/filtering",
                "parameters": "search_query (optional), tags (optional)"
            },
            {
                "name": "mythos_creation_mode",
                "description": "Return structured template with sections and creative prompts for interactive creation",
                "parameters": "template_type, style (optional)"
            },
            {
                "name": "mythos_wipe_lore_db",
                "description": "IRREVERSIBLE: Wipe the current world's DB after confirmation",
                "parameters": "confirm ('CONFIRM')"
            },
            {
                "name": "mythos_list_worlds",
                "description": "List available worlds and show the active one",
                "parameters": "none"
            },
            {
                "name": "mythos_create_world",
                "description": "Create a new world workspace (optionally select it)",
                "parameters": "name, select_after_create (optional)"
            },
            {
                "name": "mythos_select_world",
                "description": "Switch active world (optionally create if missing)",
                "parameters": "name, create_if_missing (optional)"
            },
            {
                "name": "mythos_list_tools",
                "description": "Show this menu of available tools",
                "parameters": "none"
            }
        ],
        "message": "Use these tools to enhance your creative writing and worldbuilding!"
    }

@app.post("/call/mythos_list_archetype_styles")
def list_archetype_styles():
    """Returns a comprehensive menu of all archetype frameworks and their character types."""
    styles_menu = {}
    for style_name, archetypes in ARCHETYPE_DEFINITIONS.items():
        styles_menu[style_name] = {
            "archetypes": list(archetypes.keys()),
            "descriptions": archetypes
        }
    
    return {
        "available_styles": list(ARCHETYPE_DEFINITIONS.keys()),
        "total_styles": len(ARCHETYPE_DEFINITIONS),
        "frameworks": styles_menu,
        "message": "Choose a style when using mythos_archetype_analysis to analyze characters through that framework's lens."
    }

@app.post("/call/mythos_list_lore_entries")
def list_lore_entries(req: LoreSearchRequest):
    """Retrieves lore entries from the database with optional search and tag filtering."""
    results = LORE_DATABASE.copy()
    
    # Filter by search query if provided
    if req.search_query:
        query_lower = req.search_query.lower()
        results = [
            entry for entry in results
            if query_lower in entry.get('topic', '').lower() or query_lower in entry.get('content', '').lower()
        ]
    
    # Filter by tags if provided
    if req.tags:
        results = [
            entry for entry in results
            if any(tag in entry.get('tags', []) for tag in req.tags)
        ]
    
    if len(LORE_DATABASE) == 0:
        return {
            "total_entries": 0,
            "filtered_results": 0,
            "entries": [],
            "empty": True,
            "message": "There are no lore entries yet. Shall we start creating one? Use mythos_creation_session_start (character or world) or mythos_create_lore_entry.",
            "suggestion": {
                "start_world_template": "Consider starting a world template session: mythos_creation_session_start { template_type: 'world', style: 'Fantasy' }"
            }
        }
    if len(results) == 0:
        return {
            "total_entries": len(LORE_DATABASE),
            "filtered_results": 0,
            "entries": [],
            "empty_filtered": True,
            "message": "No lore entries matched your filters. Try adjusting search or tags." 
        }
    return {
        "total_entries": len(LORE_DATABASE),
        "filtered_results": len(results),
        "entries": results,
        "message": f"Found {len(results)} lore entries" + (f" matching '{req.search_query}'" if req.search_query else "") + (f" with tags {req.tags}" if req.tags else "")
    }

@app.post("/call/mythos_wipe_lore_db")
def wipe_lore_db(req: WipeRequest):
    """Irreversibly wipe the current world's lore database after confirmation."""
    global LORE_DATABASE
    if req.confirm != "CONFIRM":
        raise HTTPException(status_code=400, detail="Confirmation failed. Pass confirm='CONFIRM' to proceed.")
    LORE_DATABASE = []
    save_lore_db(LORE_DATABASE)
    return {"status": "success", "message": f"World '{ACTIVE_WORLD_NAME}' lore database wiped."}

def _worlds_base_dir() -> str:
    base_dir = os.path.dirname(LORE_DB_BASE_PATH)
    return os.path.join(base_dir, "worlds")

def _world_exists(name: str) -> bool:
    if name == "default":
        return os.path.exists(LORE_DB_BASE_PATH)
    db_path = os.path.join(_worlds_base_dir(), name, "lore_db.json")
    return os.path.exists(db_path)

def _load_world(name: str) -> List[Dict[str, Any]]:
    global ACTIVE_WORLD_NAME
    ACTIVE_WORLD_NAME = name
    return load_lore_db()

@app.post("/call/mythos_list_worlds")
def list_worlds():
    worlds = ["default"]
    base = _worlds_base_dir()
    if os.path.exists(base):
        for entry in os.listdir(base):
            if os.path.isdir(os.path.join(base, entry)):
                worlds.append(entry)
    # count entries per world (best-effort)
    counts = {}
    current = ACTIVE_WORLD_NAME
    for w in worlds:
        try:
            # temporarily switch to read counts without persisting switch
            original = ACTIVE_WORLD_NAME
            globals()["ACTIVE_WORLD_NAME"] = w
            data = load_lore_db()
            counts[w] = len(data)
            globals()["ACTIVE_WORLD_NAME"] = original
        except Exception:
            counts[w] = None
            globals()["ACTIVE_WORLD_NAME"] = current
    total_entries_all = sum(c for c in counts.values() if isinstance(c, int))
    response = {"worlds": worlds, "active_world": ACTIVE_WORLD_NAME, "counts": counts, "message": f"Active world is '{ACTIVE_WORLD_NAME}'. Total worlds: {len(worlds)}"}
    if total_entries_all == 0:
        response["empty_all_worlds"] = True
        response["suggestion"] = {
            "create_lore": "Start a creation session: mythos_creation_session_start { template_type: 'world', style: 'Fantasy' }",
            "create_direct": "Or create a quick lore entry using mythos_create_lore_entry"
        }
    return response

@app.post("/call/mythos_create_world")
def create_world(req: WorldCreateRequest):
    name = req.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="World name cannot be empty.")
    if name == "default":
        raise HTTPException(status_code=400, detail="'default' already exists.")
    base = _worlds_base_dir()
    world_dir = os.path.join(base, name)
    os.makedirs(world_dir, exist_ok=True)
    db_path = os.path.join(world_dir, "lore_db.json")
    if not os.path.exists(db_path):
        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump([], f)
    global LORE_DATABASE, ACTIVE_WORLD_NAME
    if req.select_after_create:
        ACTIVE_WORLD_NAME = name
        LORE_DATABASE = load_lore_db()
        # load sessions for new active world
        globals()['CREATION_SESSIONS'] = load_sessions()
    resp = {"status": "success", "created": True, "active_world": ACTIVE_WORLD_NAME}
    if req.select_after_create:
        resp["next_steps"] = [
            "World is empty. Start world template session: mythos_creation_session_start { template_type: 'world', style: 'Fantasy' }",
            "Or begin with character/faction templates to seed the setting"
        ]
    return resp

@app.post("/call/mythos_select_world")
def select_world(req: WorldSelectRequest):
    name = req.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="World name cannot be empty.")
    exists = _world_exists(name)
    if not exists and not req.create_if_missing:
        raise HTTPException(status_code=404, detail=f"World '{name}' not found.")
    if not exists and req.create_if_missing:
        create_world(WorldCreateRequest(name=name, select_after_create=False))
    global LORE_DATABASE, ACTIVE_WORLD_NAME
    ACTIVE_WORLD_NAME = name
    LORE_DATABASE = load_lore_db()
    globals()['CREATION_SESSIONS'] = load_sessions()
    resp = {"status": "success", "active_world": ACTIVE_WORLD_NAME, "entries": len(LORE_DATABASE)}
    if len(LORE_DATABASE) == 0:
        resp["suggestion"] = {
            "start_world_template": "World has no lore; start world template: mythos_creation_session_start { template_type: 'world', style: 'Fantasy' }"
        }
    return resp

def _build_templates() -> Dict[str, Any]:
    return {
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
                "Hooks": ["Adventure Hooks", "Mysteries", "Unanswered Questions", "Future Arcs"]
            },
            "prompts": [
                "What unseen force quietly shapes the world's destiny?",
                "Which region holds a secret that could rewrite history?",
                "What resource is on the brink of collapse and why?",
                "What contradiction defines this world's identity?"
            ]
        },
        "character": {
            "sections": {
                "Basic Info": ["Name", "Age/Era", "Occupation/Role", "Physical Description"],
                "Core Identity": ["Primary Motivation", "Fatal Flaw", "Greatest Fear", "Defining Trait"],
                "Background": ["Origin Story", "Formative Event", "Relationships", "Current Status"],
                "Abilities": ["Skills/Powers", "Weaknesses", "Equipment/Tools", "Special Abilities"],
                "Development": ["Character Arc", "Internal Conflict", "External Conflict", "Potential Endings"]
            },
            "prompts": [
                "What secret does this character keep from everyone?",
                "How would they react under extreme pressure?",
                "What would they sacrifice everything for?",
                "What's the one thing they refuse to do, no matter what?"
            ]
        },
        "location": {
            "sections": {
                "Geography": ["Name", "Type (city/wilderness/realm)", "Climate/Weather", "Notable Landmarks"],
                "Atmosphere": ["Mood/Tone", "Sensory Details", "Unique Features", "Dangers"],
                "History": ["Founding/Creation", "Major Events", "Current State", "Legends/Myths"],
                "Inhabitants": ["Population", "Factions/Groups", "Power Structure", "Cultural Practices"],
                "Resources": ["Economy", "Technology Level", "Magic/Special Properties", "Strategic Value"]
            },
            "prompts": [
                "What's the most dangerous thing about this place?",
                "What secret does the location itself hide?",
                "How has this place changed over time?",
                "What makes people want to come here—or flee?"
            ]
        },
        "faction": {
            "sections": {
                "Identity": ["Name", "Type (guild/cult/army/corporation)", "Symbol/Colors", "Motto"],
                "Structure": ["Leadership", "Hierarchy", "Size/Reach", "Recruitment"],
                "Goals": ["Primary Objective", "Long-term Vision", "Hidden Agenda", "Methods"],
                "Resources": ["Wealth", "Military/Power", "Influence", "Technology/Magic"],
                "Relations": ["Allies", "Enemies", "Neutrals", "Internal Divisions"]
            },
            "prompts": [
                "What does this faction do in the shadows that no one knows about?",
                "What would cause this organization to collapse from within?",
                "How do they justify morally questionable actions?",
                "What's their greatest achievement and worst failure?"
            ]
        },
        "magic_system": {
            "sections": {
                "Fundamentals": ["Source of Power", "How it's Accessed", "Who Can Use It", "Learning Process"],
                "Mechanics": ["Limitations", "Costs/Consequences", "Forbidden Practices", "Power Scaling"],
                "Applications": ["Combat Uses", "Utility Uses", "Ritual/Ceremonial", "Everyday Life"],
                "Society": ["Cultural Attitude", "Legal Status", "Famous Practitioners", "Organizations"],
                "Metaphysics": ["Theoretical Limits", "Unexplained Phenomena", "Dangerous Knowledge", "Ultimate Power"]
            },
            "prompts": [
                "What's the terrible price for using the most powerful magic?",
                "How does magic corruption or madness manifest?",
                "What happens when someone breaks the fundamental rules?",
                "What's the one thing magic absolutely cannot do?"
            ]
        },
        "creature": {
            "sections": {
                "Biology": ["Species Name", "Size/Appearance", "Habitat", "Lifespan"],
                "Behavior": ["Intelligence Level", "Social Structure", "Diet", "Reproduction"],
                "Abilities": ["Natural Weapons", "Special Powers", "Senses", "Defenses"],
                "Interaction": ["Threat Level", "Communication", "Domestication", "Value to Humans"],
                "Lore": ["Origin Myth", "Cultural Significance", "Famous Specimens", "Extinction Status"]
            },
            "prompts": [
                "What's the most terrifying thing about encountering this creature?",
                "How has humanity adapted to its existence?",
                "What happens if you kill one?",
                "What ancient warning do people tell about this creature?"
            ]
        },
        "artifact": {
            "sections": {
                "Description": ["Name", "Appearance", "Size/Weight", "Materials"],
                "Power": ["Primary Function", "Secondary Effects", "Activation Method", "Limitations"],
                "History": ["Creator/Origin", "Previous Owners", "Famous Uses", "Current Location"],
                "Curse": ["Hidden Cost", "Corruption Effect", "Binding Condition", "Destruction Method"],
                "Significance": ["Cultural Impact", "Who Seeks It", "Prophecies", "True Purpose"]
            },
            "prompts": [
                "What terrible truth does the artifact reveal to its bearer?",
                "How does it change those who possess it?",
                "What's the one thing you must never do with it?",
                "Why was it really created, beyond the obvious purpose?"
            ]
        },
        "event": {
            "sections": {
                "Overview": ["Event Name", "Type (war/catastrophe/celebration)", "Date/Era", "Scale"],
                "Cause": ["Trigger Event", "Underlying Tensions", "Key Players", "Point of No Return"],
                "Course": ["Major Turning Points", "Duration", "Casualties/Impact", "Key Battles/Moments"],
                "Aftermath": ["Winners/Losers", "Territorial Changes", "Long-term Effects", "Lessons Learned"],
                "Memory": ["How it's Commemorated", "Competing Narratives", "Unresolved Issues", "Prophecy/Repetition"]
            },
            "prompts": [
                "What truth about the event has been suppressed or forgotten?",
                "Who secretly benefited from the tragedy?",
                "How did this event change the world irreversibly?",
                "What would have happened if it never occurred?"
            ]
        },
        "culture": {
            "sections": {
                "Identity": ["Name", "Population", "Geographic Range", "Defining Characteristic"],
                "Values": ["Core Beliefs", "Taboos", "Virtues", "Coming-of-Age"],
                "Daily Life": ["Economy", "Gender Roles", "Family Structure", "Education"],
                "Arts": ["Music/Dance", "Visual Arts", "Literature/Storytelling", "Architecture"],
                "Spirituality": ["Religion/Philosophy", "Rituals", "Death Customs", "Sacred Sites"]
            },
            "prompts": [
                "What do outsiders misunderstand about this culture?",
                "What shameful secret does the entire culture keep?",
                "How do they view death and the afterlife?",
                "What would be considered the highest honor?"
            ]
        },
        "conflict": {
            "sections": {
                "Stakes": ["What's at Risk", "Who's Involved", "Why Now", "Scope"],
                "Sides": ["Protagonist Forces", "Antagonist Forces", "Neutral Parties", "Hidden Players"],
                "Resources": ["Military Strength", "Economic Power", "Magic/Technology", "Morale"],
                "Escalation": ["Initial Dispute", "Provocations", "Point of No Return", "Total War"],
                "Resolution": ["Possible Outcomes", "Victory Conditions", "Compromise Options", "Pyrrhic Scenarios"]
            },
            "prompts": [
                "What would make both sides realize they've already lost?",
                "What secret alliance could change everything?",
                "How might the conflict end in unexpected tragedy?",
                "What's the one thing neither side will negotiate?"
            ]
        },
        "ritual": {
            "sections": {
                "Purpose": ["Intent", "What It Achieves", "Who Performs It", "When/Where"],
                "Requirements": ["Materials", "Participants", "Location", "Timing"],
                "Procedure": ["Preparation Steps", "Core Ceremony", "Incantations/Actions", "Duration"],
                "Cost": ["Sacrifice Required", "Energy Drain", "Side Effects", "Taboo Breaking"],
                "Consequences": ["Immediate Effects", "Long-term Changes", "Failure Results", "Unforeseen Outcomes"]
            },
            "prompts": [
                "What happens if the ritual is interrupted halfway?",
                "What's the terrible truth about why this ritual exists?",
                "How does performing it change the ritualist forever?",
                "What forbidden variation of this ritual exists?"
            ]
        }
    }
@app.post("/call/mythos_creation_mode")
def creation_mode(req: CreationModeRequest):
    """Returns an interactive, template-based creation guide for worldbuilding elements."""
    
    templates = _build_templates()
    
    template = templates.get(req.template_type)
    if not template:
        return {
            "error": f"Unknown template type: {req.template_type}",
            "available_templates": list(templates.keys())
        }
    
    return {
        "template_type": req.template_type,
        "style": req.style,
        "sections": template["sections"],
        "creative_prompts": template["prompts"],
        "instructions": f"Use this {req.template_type} template to build your worldbuilding element. Fill in each section systematically, then use the creative prompts to deepen your creation. Consider how this fits into the {req.style} genre.",
        "next_steps": [
            "Fill out each section with 1-3 sentences",
            "Answer the creative prompts to add depth",
            "Consider connections to existing lore",
            f"Use mythos_create_lore_entry to save when complete"
        ]
    }

# --- Interactive Creation Sessions (persistent per world) ---
def _current_sessions_path() -> str:
    """Return path to the sessions.json for the active world."""
    if ACTIVE_WORLD_NAME == "default":
        base_dir = os.path.dirname(LORE_DB_BASE_PATH)
        return os.path.join(base_dir, "sessions.json")
    base_dir = os.path.dirname(LORE_DB_BASE_PATH)
    return os.path.join(base_dir, "worlds", ACTIVE_WORLD_NAME, "sessions.json")

def load_sessions() -> Dict[str, Dict[str, Any]]:
    path = _current_sessions_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        print(f"Warning: sessions file corrupted at {path}; starting empty.")
        return {}

def save_sessions(sessions: Dict[str, Dict[str, Any]]):
    path = _current_sessions_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(sessions, f, indent=2, ensure_ascii=False)

CREATION_SESSIONS: Dict[str, Dict[str, Any]] = load_sessions()

class CreationSessionStartRequest(BaseModel):
    template_type: str = Field(..., description="Template type: character, location, faction, magic_system, creature, artifact, event, culture, conflict, ritual.")
    style: str = Field(default="Fantasy", description="Creative style/genre.")

class CreationSessionUpdateRequest(BaseModel):
    session_id: str = Field(..., description="ID returned by session start.")
    updates: Dict[str, Dict[str, Any]] = Field(
        ..., 
        description="Nested dict of {section: {field: value}}. Values may be string or list of strings; lists are preserved and rendered as bullets in finalize output."
    )

class CreationSessionGetRequest(BaseModel):
    session_id: str = Field(..., description="ID returned by session start.")

class CreationSessionFinalizeRequest(BaseModel):
    session_id: str = Field(..., description="ID returned by session start.")
    topic: str | None = Field(None, description="Optional proposed topic/title for the final lore entry preview.")
    tags: List[str] | None = Field(None, description="Optional tags to suggest alongside the preview.")

class CreationSessionListRequest(BaseModel):
    limit: int | None = Field(None, description="Optional max number of sessions to return.")

@app.post("/call/mythos_creation_session_start")
def creation_session_start(req: CreationSessionStartRequest):
    templates = _build_templates()
    template = templates.get(req.template_type)
    if not template:
        raise HTTPException(status_code=400, detail=f"Unknown template type: {req.template_type}")
    session_id = str(uuid.uuid4())
    CREATION_SESSIONS[session_id] = {
        "id": session_id,
        "template_type": req.template_type,
        "style": req.style,
        "sections": template["sections"],
        "prompts": template["prompts"],
        "filled": {},
        "history": []
    }
    save_sessions(CREATION_SESSIONS)
    return {
        "session_id": session_id,
        "template_type": req.template_type,
        "style": req.style,
        "sections": template["sections"],
        "creative_prompts": template["prompts"],
        "message": "Session started. Iteratively update sections; finalize to preview before saving."
    }

@app.post("/call/mythos_creation_session_update")
def creation_session_update(req: CreationSessionUpdateRequest):
    session = CREATION_SESSIONS.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    filled = session.setdefault("filled", {})
    skipped_fields = []
    for section, fields in (req.updates or {}).items():
        if not isinstance(fields, dict):
            # Auto-correct common LLM mistake: flatten array-as-section to first real section match
            if isinstance(fields, list) and session["sections"].get(section):
                # Model sent {"Section": [values]} instead of {"Section": {"Field": values}}
                # Try to infer: if section has exactly 1 field, assign the array there
                section_fields = session["sections"][section]
                if len(section_fields) == 1:
                    fsec = filled.setdefault(section, {})
                    fsec[section_fields[0]] = fields
                    skipped_fields.append(f"Auto-corrected: '{section}' array mapped to '{section_fields[0]}'.")
                    continue
            skipped_fields.append(f"Section '{section}' has non-dict value (got {type(fields).__name__}); expected {{field: value}} mapping.")
            continue
        # Check if LLM sent field-level arrays incorrectly (common pattern)
        # If a field value is an array but the field name matches a known section field, it's valid
        # If the field name itself contains an array, the LLM sent the wrong structure
        fsec = filled.setdefault(section, {})
        for field, value in (fields or {}).items():
            # Additional heuristic: if multiple fields in this section all have array values,
            # and none of the field names are in the template, the LLM may have sent a flat list
            # Just store as-is; validation already warned about structure
            fsec[field] = value
    session["history"].append({"type": "update", "payload": req.updates})
    total_fields = sum(len(v) for v in session["sections"].values())
    # Count completed if value is a non-empty string OR a non-empty list
    completed = sum(
        1 for s, fs in filled.items() for k, v in fs.items()
        if (isinstance(v, str) and v.strip()) or (isinstance(v, list) and any(str(x).strip() for x in v))
    )
    save_sessions(CREATION_SESSIONS)
    resp = {
        "session_id": req.session_id,
        "progress": {"completed_fields": completed, "total_fields": total_fields},
        "filled": filled,
        "message": "Session updated."
    }
    if skipped_fields:
        resp["warnings"] = skipped_fields
        resp["hint"] = "Ensure updates structure is { 'Section Name': { 'Field Name': 'value or [array]' } }"
    return resp

@app.post("/call/mythos_creation_session_get")
def creation_session_get(req: CreationSessionGetRequest):
    session = CREATION_SESSIONS.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    return {k: session[k] for k in ["id", "template_type", "style", "sections", "prompts", "filled"]}

@app.post("/call/mythos_creation_session_finalize")
def creation_session_finalize(req: CreationSessionFinalizeRequest):
    session = CREATION_SESSIONS.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
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
                    lines.append(f"- {field}: [ ]")
            elif isinstance(val, str):
                # Detect semicolon-delimited legacy multi-entry strings and expand
                if ';' in val and any(part.strip() for part in val.split(';')):
                    parts = [p.strip() for p in val.split(';') if p.strip()]
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
    suggested_tags = req.tags if req.tags is not None else [session["template_type"]]
    proposed_topic = req.topic or f"New {session['template_type'].title()} ({session['style']})"
    proposed_entry = {"topic": proposed_topic, "content": preview, "tags": suggested_tags}
    session["history"].append({"type": "finalize", "preview_length": len(preview)})
    save_sessions(CREATION_SESSIONS)
    return {
        "session_id": req.session_id,
        "preview": preview,
        "proposed_entry": proposed_entry,
        "message": "Preview assembled. Use mythos_create_lore_entry to commit when ready."
    }

@app.post("/call/mythos_creation_session_list")
def creation_session_list(req: CreationSessionListRequest):
    sessions = list(CREATION_SESSIONS.values())
    if req.limit is not None:
        sessions = sessions[:req.limit]
    return {"active_world": ACTIVE_WORLD_NAME, "count": len(CREATION_SESSIONS), "sessions": [{"id": s["id"], "template_type": s["template_type"], "style": s["style"], "fields_filled": sum(len(v) for v in s.get("filled", {}).values())} for s in sessions]}