from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ConnectionDistributionSerializer, ProfileInputSerializer
from .services.inference import infer_pair_connection
from .models import PostsComment
from .constants import CONNECTION_TYPE_KEYS
from .feature_extraction import extract_features as extract_features_heuristic
from .logic import connection_type_scores_raw

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

        # Merge all posts/comments from DB (no limit)
        rows = list(PostsComment.objects.all().order_by("-created_at").values("post", "comment"))
        for r in rows:
            if r.get("post"):
                messages.append({"sender": "UserPost", "text": r["post"]})
            if r.get("comment"):
                messages.append({"sender": "UserComment", "text": r["comment"]})

        # Fully AI-based on a single combined corpus (profile + posts/comments)
        def _is_all_zeros(d: dict) -> bool:
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

        features = None
        if LLM_AVAILABLE:
            try:
                features = extract_features_llm(messages)
            except Exception:
                features = None

        if features is None or _is_all_zeros(features):
            features = extract_features_heuristic(messages)

        scores = connection_type_scores_raw(features)
        distribution = _percentages(scores)
        highest = max(scores, key=scores.get)
        return Response({
            "highest_connection_type": highest,
            "distribution": distribution,
            "source": "profile+posts_comments",
            "count_messages": len(messages),
        }, status=status.HTTP_200_OK)


    
