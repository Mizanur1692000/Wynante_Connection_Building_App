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
    return 1 - np.mean(
        [abs(features[k] - v) for k, v in profile.items()]
    )

def classify_connection(features: dict):
    scores = {k: similarity(features, v) for k, v in CONNECTION_PROFILES.items()}

    # Rule overrides
    if features["task_focus"] > 0.8:
        return "Professional", 0.95
    if features["spiritual_reference"] > 0.7:
        return "Spiritual", 0.95

    best = max(scores, key=scores.get)
    confidence = round(scores[best], 2)
    return best, confidence


def connection_type_scores(features: dict) -> dict:
    """Return normalized per-type probabilities (0..1) for all classes.

    Uses similarity to each profile, applies rule-based boosts, then normalizes
    to sum to 1. This enables reporting percentages for all connection types.
    """
    base = {k: similarity(features, v) for k, v in CONNECTION_PROFILES.items()}

    # Apply rule boosts (soft, not hard overrides)
    boosted = dict(base)
    if features.get("task_focus", 0) > 0.8:
        boosted["Professional"] = boosted.get("Professional", 0) + 0.5
    if features.get("spiritual_reference", 0) > 0.7:
        boosted["Spiritual"] = boosted.get("Spiritual", 0) + 0.5

    # Clamp to non-negative and normalize
    for k, v in boosted.items():
        if v < 0:
            boosted[k] = 0.0

    total = sum(boosted.values())
    if total <= 0:
        # Fallback to uniform if all scores are zero/negative
        n = max(1, len(CONNECTION_PROFILES))
        return {k: 1.0 / n for k in CONNECTION_PROFILES}

    return {k: boosted[k] / total for k in CONNECTION_PROFILES}
