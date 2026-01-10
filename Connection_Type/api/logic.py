import numpy as np

CONNECTION_PROFILES = {
    "Social": {
        "emotional_warmth": 0.6,
        "romantic_language": 0.2,
        "task_focus": 0.2,
        "spiritual_reference": 0.1
    },
    "Romantic": {
        "emotional_warmth": 0.8,
        "romantic_language": 0.8,
        "formality": 0.1
    },
    "Spiritual": {
        "spiritual_reference": 0.8,
        "emotional_warmth": 0.6,
        "romantic_language": 0.1
    },
    "Professional": {
        "task_focus": 0.8,
        "formality": 0.7,
        "romantic_language": 0.0
    }
}

def similarity(features, profile):
    return 1 - np.mean([abs(features.get(k, 0.0) - v) for k, v in profile.items()])

def connection_type_scores_raw(features: dict) -> dict:
    """Return independent per-type scores (0..1) without normalization.

    - Computes similarity per class
    - Applies soft rule boosts
    - Clamps each score to [0, 1]
    """
    base = {k: similarity(features, v) for k, v in CONNECTION_PROFILES.items()}
    boosted = dict(base)

    if features.get("task_focus", 0) > 0.8:
        boosted["Professional"] = boosted.get("Professional", 0) + 0.5
    if features.get("spiritual_reference", 0) > 0.7:
        boosted["Spiritual"] = boosted.get("Spiritual", 0) + 0.5

    # Clamp to [0, 1]
    for k in boosted:
        boosted[k] = max(0.0, min(1.0, boosted[k]))

    return boosted


def connection_type_scores_raw(features: dict) -> dict:
    """Return independent per-type scores (0..1) without normalization.

    - Computes similarity per class
    - Applies soft rule boosts
    - Clamps each score to [0, 1]
    """
    base = {k: similarity(features, v) for k, v in CONNECTION_PROFILES.items()}
    boosted = dict(base)

    if features.get("task_focus", 0) > 0.8:
        boosted["Professional"] = boosted.get("Professional", 0) + 0.5
    if features.get("spiritual_reference", 0) > 0.7:
        boosted["Spiritual"] = boosted.get("Spiritual", 0) + 0.5

    # Clamp to [0, 1]
    for k in boosted:
        boosted[k] = max(0.0, min(1.0, boosted[k]))

    return boosted
