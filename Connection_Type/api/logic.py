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
