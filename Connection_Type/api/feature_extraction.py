import re
from typing import List, Dict


WARMTH_WORDS = {
    "thank", "thanks", "appreciate", "grateful", "happy", "glad", "support",
    "care", "caring", "kind", "kindness", "nice", "friendly", "enjoy", "welcome"
}

ROMANTIC_WORDS = {
    "love", "lover", "lovely", "darling", "babe", "bby", "baby", "sweetheart",
    "honey", "kiss", "kisses", "romantic", "date", "dating", "heart", "xoxo",
    "miss you", "i miss you"
}

SPIRITUAL_WORDS = {
    "god", "allah", "jesus", "bible", "quran", "torah", "temple", "church",
    "mosque", "bless", "blessed", "prayer", "pray", "faith", "spiritual",
    "meditate", "meditation", "soul", "divine"
}

TASK_WORDS = {
    "project", "deadline", "deliverable", "meeting", "meet", "schedule", "plan",
    "task", "todo", "assign", "assignment", "objective", "goal", "kpi", "report",
    "update", "work", "workstream", "status", "document", "review", "sync"
}

FORMALITY_MARKERS = {
    "regards", "best", "sincerely", "dear", "please", "kindly", "mr", "mrs",
    "sir", "madam", "respectfully"
}

INTENSITY_WORDS = {
    "amazing", "awesome", "incredible", "fantastic", "terrible", "awful",
    "furious", "angry", "urgent", "critical", "disaster", "love", "hate"
}


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z']+", text.lower())


def _count_phrases(text: str, phrases: List[str]) -> int:
    t = text.lower()
    return sum(t.count(p) for p in phrases)


def _safe_div(num: float, den: float) -> float:
    return num / den if den > 0 else 0.0


def extract_features(messages: List[Dict[str, str]]) -> Dict[str, float]:
    # Concatenate all texts for pair-level analysis
    texts = [m.get("text", "") for m in messages]
    joined = "\n".join(texts)
    tokens = _tokenize(joined)
    token_set = set(tokens)
    token_count = len(tokens)

    # Feature: emotional_warmth (normalized term frequency)
    warmth_hits = sum(1 for t in tokens if t in WARMTH_WORDS)
    emotional_warmth = min(1.0, _safe_div(warmth_hits, max(1, token_count // 20)))

    # Feature: romantic_language (include multiword phrases)
    romantic_token_hits = sum(1 for t in tokens if t in ROMANTIC_WORDS)
    romantic_phrase_hits = _count_phrases(joined, ["miss you", "i miss you"])
    romantic_raw = romantic_token_hits + romantic_phrase_hits * 2
    romantic_language = min(1.0, _safe_div(romantic_raw, max(1, token_count // 25)))

    # Feature: spiritual_reference
    spiritual_hits = sum(1 for t in tokens if t in SPIRITUAL_WORDS)
    spiritual_reference = min(1.0, _safe_div(spiritual_hits, max(1, token_count // 25)))

    # Feature: task_focus
    task_hits = sum(1 for t in tokens if t in TASK_WORDS)
    task_focus = min(1.0, _safe_div(task_hits, max(1, token_count // 25)))

    # Feature: formality (markers, salutations, closings; penalize contractions)
    formality_hits = sum(1 for t in tokens if t in FORMALITY_MARKERS)
    # crude contraction count lowers formality
    contraction_hits = sum(1 for t in tokens if "'" in t or t.endswith("nt"))
    formality_base = _safe_div(formality_hits, max(1, token_count // 30))
    formality_penalty = min(0.5, _safe_div(contraction_hits, max(1, token_count)))
    formality = max(0.0, min(1.0, formality_base - formality_penalty))

    # Feature: emotional_intensity (exclamations, ALL CAPS words, intensity terms)
    exclamations = joined.count("!")
    caps_words = sum(1 for w in re.findall(r"\b[A-Z]{2,}\b", joined) if len(w) > 2)
    intensity_hits = sum(1 for t in tokens if t in INTENSITY_WORDS)
    intensity_raw = exclamations + caps_words * 0.5 + intensity_hits
    emotional_intensity = min(1.0, _safe_div(intensity_raw, max(1, len(messages))))

    return {
        "emotional_warmth": round(emotional_warmth, 4),
        "romantic_language": round(romantic_language, 4),
        "spiritual_reference": round(spiritual_reference, 4),
        "task_focus": round(task_focus, 4),
        "formality": round(formality, 4),
        "emotional_intensity": round(emotional_intensity, 4),
    }
