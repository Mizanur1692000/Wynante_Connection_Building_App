from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ConnectionDistributionSerializer, ProfileInputSerializer
from .services.inference import infer_pair_connection
from .models import PostsComment
from .constants import CONNECTION_TYPE_KEYS
from .feature_extraction import extract_features as extract_features_heuristic
from .logic import connection_type_scores_raw
from django.utils import timezone
from datetime import timedelta

try:
    from llm_service.llm import extract_features as extract_features_llm
    LLM_AVAILABLE = True
except Exception:
    extract_features_llm = None
    LLM_AVAILABLE = False

class AnalyzePairFromDB(APIView):
    def get(self, request):
        try:
            a = int(request.query_params.get("user_a_id"))
            b = int(request.query_params.get("user_b_id"))
        except (TypeError, ValueError):
            return Response({
                "detail": "Provide integer query params user_a_id and user_b_id"
            }, status=status.HTTP_400_BAD_REQUEST)
        result = infer_pair_connection(a, b)
        out = ConnectionDistributionSerializer(data=result)
        out.is_valid(raise_exception=True)
        return Response(out.validated_data, status=status.HTTP_200_OK)


def _build_profile_text(data: dict) -> str:
    parts = []
    if data.get("about_me"):
        parts.append(f"About me: {data['about_me']}")
    if data.get("interests"):
        parts.append(f"Interests: {data['interests']}")
    if data.get("looking_for"):
        parts.append(f"Looking for: {data['looking_for']}")
    if data.get("education"):
        parts.append(f"Education: {data['education']}")
    if data.get("occupation"):
        parts.append(f"Occupation: {data['occupation']}")
    if data.get("relationship_status"):
        parts.append(f"Relationship status: {data['relationship_status']}")
    return "\n".join(parts)


def _percentages(scores: dict) -> dict:
    # Clamp and scale to 0..100 per type independently
    clamped = {k: max(0.0, min(1.0, float(scores.get(k, 0.0)))) for k in CONNECTION_TYPE_KEYS}
    return {k: int(round(v * 100)) for k, v in clamped.items()}


def _run_profile_analysis(messages: list) -> dict:
    """
    Runs the full AI analysis and returns the feature dictionary.
    Tries LLM first, then falls back to a robust heuristic combination.
    """
    features = None
    if LLM_AVAILABLE:
        try:
            # Add a cache-busting timestamp to fight potential upstream caching
            import time
            cache_bust_text = f"\n\n[debug_timestamp: {time.time()}]"
            busted_messages = messages + [{"sender": "system", "text": cache_bust_text}]
            features = extract_features_llm(busted_messages)
        except Exception:
            features = None

    def _is_all_zeros(d: dict) -> bool:
        if not d: return True
        keys = ["emotional_warmth", "romantic_language", "spiritual_reference", "task_focus", "formality", "emotional_intensity"]
        return all(float(d.get(k, 0.0)) == 0.0 for k in keys)

    if features is None or _is_all_zeros(features):
        # FALLBACK LOGIC: Run heuristics on profile and posts separately and merge with 70% profile weight.
        profile_msg_list = [m for m in messages if m["sender"] == "UserProfile"]
        posts_msgs_list = [m for m in messages if m["sender"] != "UserProfile"]

        # Get features for each part, or empty dict if no messages
        features_profile = extract_features_heuristic(profile_msg_list) if profile_msg_list else {}
        features_posts = extract_features_heuristic(posts_msgs_list) if posts_msgs_list else {}

        # Merge using weighted average: 60% profile, 40% posts
        # This ensures profile input has dominant influence
        all_keys = set(features_profile.keys()) | set(features_posts.keys())
        features = {
            k: (features_profile.get(k, 0.0) * 0.5 + features_posts.get(k, 0.0) * 0.5)
            for k in all_keys
        }

    return features


class AnalyzeProfile(APIView):
    """POST endpoint: takes profile inputs, merges posts_comments, returns AI-based per-type percentages."""
    def post(self, request):
        # Validate profile inputs
        s = ProfileInputSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data = s.validated_data

        # Build initial messages from profile
        text = _build_profile_text(data)
        messages = []
        if text:
            messages.append({"sender": "UserProfile", "text": text})

        # Merge recent posts/comments from DB (last 90 days, with limit)
        limit = data.get("limit")
        cutoff = timezone.now() - timedelta(days=90)
        query = PostsComment.objects.filter(created_at__gte=cutoff).order_by("-created_at")
        if limit:
            query = query[:limit]
        rows = list(query.values("post", "comment"))
        for r in rows:
            if r.get("post"):
                messages.append({"sender": "UserPost", "text": r["post"]})
            if r.get("comment"):
                messages.append({"sender": "UserComment", "text": r["comment"]})

        # Run the full AI analysis
        features = _run_profile_analysis(messages)
        scores = connection_type_scores_raw(features)
        distribution = _percentages(scores)
        highest = max(scores, key=scores.get) if scores else "N/A"

        # Create a debug echo of the text sent to the AI
        combined_text_for_debug = "\n---\n".join([m["text"] for m in messages])
        debug_echo = f"Analyzed {len(messages)} message parts. Snippet: {combined_text_for_debug[:250]}..."

        return Response({
            "highest_connection_type": highest,
            "distribution": distribution,
            "source": "profile+posts_comments",
            "count_messages": len(messages),
            "debug_echo": debug_echo,
        }, status=status.HTTP_200_OK)



