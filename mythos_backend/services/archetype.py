"""
Archetype analysis service — semantic scoring across 22 frameworks.

This module is unchanged in logic from the original. It's separated
here for clean architecture. The archetype definitions are large, so
they live in their own module.
"""

from __future__ import annotations

import math
import random

from mythos_backend.models.archetypes import ARCHETYPE_DEFINITIONS


def _semantic_tokenize(text: str) -> list[str]:
    return [
        t
        for t in "".join(c if c.isalnum() else " " for c in text).lower().split()
        if t
    ]


_SYNONYMS: dict[str, list[str]] = {
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


def _expand_tokens(tokens: list[str]) -> set[str]:
    expanded = set(tokens)
    for t in list(tokens):
        if t in _SYNONYMS:
            expanded.update(_SYNONYMS[t])
    return expanded


def _semantic_score(desc_tokens: list[str], definition: str) -> float:
    if not desc_tokens:
        return 0.0
    def_tokens = _semantic_tokenize(definition)
    desc_set = _expand_tokens(desc_tokens)
    def_set = _expand_tokens(def_tokens)
    overlap = desc_set.intersection(def_set)
    if not overlap:
        return 0.0
    return len(overlap) / (math.sqrt(len(desc_set)) * math.sqrt(len(def_set)))


def analyze_single(
    character_name: str,
    description: str,
    style: str,
) -> dict:
    """Analyze a character through a single archetype framework."""
    if style not in ARCHETYPE_DEFINITIONS:
        style = "Jungian"
    definitions = ARCHETYPE_DEFINITIONS[style]
    desc_tokens = _semantic_tokenize(description.lower())

    scored = [
        (name, _semantic_score(desc_tokens, definition))
        for name, definition in definitions.items()
    ]
    scored.sort(key=lambda x: x[1], reverse=True)

    low_signal = False
    if not scored or scored[0][1] < 0.08:
        low_signal = True
        primary = random.choice(list(definitions.keys()))
        secondary = random.choice(list(definitions.keys()))
        conf_primary = 0.0
        conf_secondary = 0.0
    else:
        primary, conf_primary = scored[0]
        secondary, conf_secondary = next(
            ((n, s) for n, s in scored[1:] if n != primary),
            (primary, scored[0][1]),
        )

    tension = round(abs(conf_primary - conf_secondary), 3)
    result_text = (
        f"{character_name} aligns with the **{primary}** archetype in {style}. "
        f"Secondary influence from **{secondary}** introduces dynamic tension."
    )
    if low_signal:
        result_text += " (Low semantic signal detected; archetypes selected via fallback heuristic.)"

    return {
        "style": style,
        "character_name": character_name,
        "analysis_result": result_text,
        "primary_archetype": primary,
        "primary_definition": definitions[primary],
        "secondary_archetype": secondary,
        "secondary_definition": definitions[secondary],
        "confidence_primary": round(conf_primary, 3),
        "confidence_secondary": round(conf_secondary, 3),
        "tension_score": tension,
        "low_signal_fallback": low_signal,
        "suggestion": (
            f"Explore how {primary} traits are stressed when {secondary} tendencies surface. "
            f"Leverage contrasting values to shape turning points and internal conflict."
        ),
    }


def analyze_multi(
    character_name: str,
    description: str,
    styles_str: str,
    max_frameworks: int = 5,
) -> dict:
    """Blend multiple archetype frameworks for composite analysis."""
    raw = styles_str.lower()
    for sep in [",", "+", "/", " with ", " and "]:
        raw = raw.replace(sep, ",")
    tokens = [t.strip() for t in raw.split(",") if t.strip()]

    seen: set[str] = set()
    resolved: list[str] = []
    for token in tokens:
        match = next(
            (k for k in ARCHETYPE_DEFINITIONS if k.lower() == token), None
        )
        if not match:
            match = next(
                (k for k in ARCHETYPE_DEFINITIONS if k.lower().startswith(token)),
                None,
            )
        if match and match not in seen:
            seen.add(match)
            resolved.append(match)
        if len(resolved) >= max_frameworks:
            break

    if not resolved:
        return {
            "error": "No valid frameworks found in styles string.",
            "available": list(ARCHETYPE_DEFINITIONS.keys()),
        }

    desc_tokens = _semantic_tokenize(description.lower())
    analyses = []
    primary_traits = []
    secondary_traits = []
    all_primary_scores = []

    for style in resolved:
        defs = ARCHETYPE_DEFINITIONS[style]
        scored = [
            (name, _semantic_score(desc_tokens, defn))
            for name, defn in defs.items()
        ]
        scored.sort(key=lambda x: x[1], reverse=True)

        if not scored or scored[0][1] < 0.08:
            primary, p_score = random.choice(list(defs.keys())), 0.0
            secondary, s_score = random.choice(list(defs.keys())), 0.0
            low = True
        else:
            primary, p_score = scored[0]
            secondary, s_score = next(
                ((n, s) for n, s in scored[1:] if n != primary),
                (primary, scored[0][1]),
            )
            low = False

        tension = round(abs(p_score - s_score), 3)
        analyses.append({
            "style": style,
            "primary_archetype": primary,
            "primary_definition": defs[primary],
            "secondary_archetype": secondary,
            "secondary_definition": defs[secondary],
            "confidence_primary": round(p_score, 3),
            "confidence_secondary": round(s_score, 3),
            "tension_score": tension,
            "low_signal_fallback": low,
        })
        primary_traits.append(primary)
        secondary_traits.append(secondary)
        all_primary_scores.append(p_score)

    if all_primary_scores:
        mean = sum(all_primary_scores) / len(all_primary_scores)
        variance = sum((s - mean) ** 2 for s in all_primary_scores) / len(all_primary_scores)
    else:
        variance = 0.0

    return {
        "character_name": character_name,
        "requested_styles_raw": styles_str,
        "resolved_frameworks": resolved,
        "framework_count": len(resolved),
        "analyses": analyses,
        "composite_tension_metric": round(variance, 3),
        "composite_summary": (
            f"{character_name} expresses blended archetypal drivers: "
            f"{', '.join(primary_traits)} (primary) counterbalanced by "
            f"{', '.join(secondary_traits)} (secondary). "
            f"Diversity tension metric={round(variance, 3)}."
        ),
        "suggestion": "Use high-tension pairs to script moral dilemmas and turning points.",
    }
