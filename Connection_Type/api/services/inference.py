from typing import Dict, List, Tuple
from django.db.models import Q
from ..models import ConversationMessage, ConversationSummary
from ..constants import CONNECTION_TYPE_KEYS
from ..feature_extraction import extract_features as extract_features_heuristic
from ..logic import connection_type_scores_raw

# Optional LLM feature extractor
try:
    from llm_service.llm import extract_features as extract_features_llm
    LLM_AVAILABLE = True
except Exception:
    extract_features_llm = None
    LLM_AVAILABLE = False


def _fetch_pair_messages(user_a_id: int, user_b_id: int) -> List[Dict]:
    """Fetch chronological messages strictly between two users from DB."""
    user_a = min(user_a_id, user_b_id)
    user_b = max(user_a_id, user_b_id)
    qs = ConversationMessage.objects.filter(
        (Q(sender_id=user_a) & Q(receiver_id=user_b)) |
        (Q(sender_id=user_b) & Q(receiver_id=user_a))
    ).order_by("sent_at")

    return list(qs.values("sender_id", "receiver_id", "message", "sent_at"))


def _format_messages(rows: List[Dict]) -> List[Dict[str, str]]:
    """Format DB rows to simple sender/text for feature extraction."""
    return [{"sender": f"User {r['sender_id']}", "text": r["message"]} for r in rows]


def _percentages_independent(scores: Dict[str, float]) -> Tuple[Dict[str, int], str]:
    """Map independent 0..1 scores to 0..100 integers per type.

    Returns (percentages_dict, highest_key) based on the max score.
    """
    clamped = {k: max(0.0, min(1.0, float(scores.get(k, 0.0)))) for k in CONNECTION_TYPE_KEYS}
    perc = {k: int(round(v * 100)) for k, v in clamped.items()}
    highest = max(clamped, key=clamped.get) if clamped else CONNECTION_TYPE_KEYS[0]
    return perc, highest


def infer_pair_connection(user_a_id: int, user_b_id: int) -> Dict:
    """End-to-end inference for a two-user conversation.

    - Fetch conversation from DB
    - Heuristic-first feature extraction; call LLM only if needed
    - Compute deterministic per-type distribution
    - Persist/update summary
    - Return structured output
    """
    rows = _fetch_pair_messages(user_a_id, user_b_id)
    msg_payload = _format_messages(rows)

    # Cache check: if ConversationSummary exists and DB hasn't changed, reuse cached features
    user_a = min(user_a_id, user_b_id)
    user_b = max(user_a_id, user_b_id)
    pair_key = f"{user_a}-{user_b}"
    new_last_message_at = rows[-1]["sent_at"] if rows else None
    new_message_count = len(rows)

    cached = ConversationSummary.objects.filter(pair_key=pair_key).values(
        "last_message_at",
        "message_count",
        "emotional_warmth",
        "romantic_language",
        "spiritual_reference",
        "task_focus",
        "formality",
        "emotional_intensity",
    ).first()

    if cached and cached["last_message_at"] == new_last_message_at and cached["message_count"] == new_message_count:
        cached_features = {
            "emotional_warmth": cached.get("emotional_warmth", 0.0),
            "romantic_language": cached.get("romantic_language", 0.0),
            "spiritual_reference": cached.get("spiritual_reference", 0.0),
            "task_focus": cached.get("task_focus", 0.0),
            "formality": cached.get("formality", 0.0),
            "emotional_intensity": cached.get("emotional_intensity", 0.0),
        }
        scores = connection_type_scores_raw(cached_features)
        distribution, highest = _percentages_independent(scores)
        return {
            "highest_connection_type": highest,
            "distribution": distribution,
            "pair_key": pair_key,
            "message_count": new_message_count,
        }

    # Heuristic-first gate
    heuristic_features = extract_features_heuristic(msg_payload)
    heuristic_scores = connection_type_scores_raw(heuristic_features)
    # Compute margin between top two scores for confidence gating
    sorted_scores = sorted(((k, heuristic_scores.get(k, 0.0)) for k in CONNECTION_TYPE_KEYS), key=lambda x: x[1], reverse=True)
    top_label, top_val = sorted_scores[0]
    second_val = sorted_scores[1][1] if len(sorted_scores) > 1 else 0.0
    margin = top_val - second_val

    USE_HEURISTIC = (top_val >= 0.7 and margin >= 0.15) or not LLM_AVAILABLE

    if USE_HEURISTIC:
        final_features = heuristic_features
    else:
        # Try LLM features, fallback to heuristic on failure or zeros
        llm_features = None
        try:
            llm_features = extract_features_llm(msg_payload)
        except Exception:
            llm_features = None

        def _is_all_zeros(d: Dict[str, float]) -> bool:
            if not d:
                return True
            keys = [
                "emotional_warmth",
                "romantic_language",
                "spiritual_reference",
                "task_focus",
                "formality",
                "emotional_intensity",
            ]
            return all(float(d.get(k, 0.0)) == 0.0 for k in keys)

        final_features = llm_features if llm_features and not _is_all_zeros(llm_features) else heuristic_features

    # Deterministic probability distribution
    scores = connection_type_scores_raw(final_features)
    distribution, highest = _percentages_independent(scores)

    # Confidence as highest percentage
    confidence_pct = distribution.get(highest, 0)

    # Persist/update summary
    last_message_at = new_last_message_at
    message_count = new_message_count

    ConversationSummary.objects.update_or_create(
        pair_key=pair_key,
        defaults={
            "user_a_id": user_a,
            "user_b_id": user_b,
            "last_message_at": last_message_at,
            "message_count": message_count,
            "connection_type": highest,
            "confidence": confidence_pct,
            "emotional_warmth": final_features.get("emotional_warmth", 0.0),
            "romantic_language": final_features.get("romantic_language", 0.0),
            "spiritual_reference": final_features.get("spiritual_reference", 0.0),
            "task_focus": final_features.get("task_focus", 0.0),
            "formality": final_features.get("formality", 0.0),
            "emotional_intensity": final_features.get("emotional_intensity", 0.0),
        }
    )

    return {
        "highest_connection_type": highest,
        "distribution": distribution,
        "pair_key": pair_key,
        "message_count": message_count,
    }
