from typing import Dict


def _val(features: Dict[str, float], key: str) -> float:
    v = float(features.get(key, 0.0) or 0.0)
    return 0.0 if v < 0 else (1.0 if v > 1 else v)


def connection_type_scores_raw(features: dict) -> dict:
    """Return independent per-type scores (0..1) without normalization.

    New scoring emphasizes tonal cues and interactions:
    - Romantic: romantic_language, emotional_warmth, low formality/task_focus, high intensity
    - Social: emotional_warmth, moderate intensity, low task_focus, light romantic
    - Spiritual: spiritual_reference primary, then warmth and composure
    - Professional: task_focus and formality, dampened by romantic/intensity
    """
    ew = _val(features, "emotional_warmth")
    rl = _val(features, "romantic_language")
    sr = _val(features, "spiritual_reference")
    tf = _val(features, "task_focus")
    fm = _val(features, "formality")
    ei = _val(features, "emotional_intensity")

    # Helper transforms
    low_formality = 1.0 - fm
    low_task = 1.0 - tf
    mid_intensity = 1.0 - abs(ei - 0.5) * 2  # peaks at 0.5, 0 at 0/1

    # Base weighted scores
    romantic = (
        0.45 * rl +
        0.25 * ew +
        0.10 * ei +
        0.10 * low_formality +
        0.10 * low_task
    )

    social = (
        0.40 * ew +
        0.15 * (0.3 <= rl <= 0.6) +  # slight social flirtation
        0.20 * mid_intensity +
        0.15 * low_task +
        0.10 * low_formality
    )
    # Convert boolean term to float if used
    if isinstance(social, bool):
        social = float(social)

    spiritual = (
        0.60 * sr +
        0.15 * ew +
        0.15 * (1.0 - ei) +  # calmer tone
        0.10 * fm
    )

    professional = (
        0.50 * tf +
        0.25 * fm +
        0.10 * (1.0 - rl) +
        0.15 * (1.0 - ei)
    )

    # Interaction boosts/penalties
    # Romantic synergy: high rl and high ew
    if rl > 0.6 and ew > 0.6:
        romantic += 0.20
        professional -= 0.10
        social -= 0.05

    # Passionate romance: very high intensity with romantic cues
    if ei > 0.8 and rl > 0.5:
        romantic += 0.10

    # Friendly warmth: high ew, moderate intensity, low task
    if ew > 0.6 and 0.3 <= ei <= 0.7 and tf < 0.4:
        social += 0.15

    # Spiritual emphasis: strong references with composed tone
    if sr > 0.6 and 0.2 <= (1.0 - ei) <= 0.8:
        spiritual += 0.15

    # Strong professional pattern: task + formality and low romance
    if tf > 0.7 and fm > 0.6 and rl < 0.3:
        professional += 0.20

    # Clamp to [0, 1]
    scores = {
        "Social": max(0.0, min(1.0, social)),
        "Romantic": max(0.0, min(1.0, romantic)),
        "Spiritual": max(0.0, min(1.0, spiritual)),
        "Professional": max(0.0, min(1.0, professional)),
    }

    return scores
