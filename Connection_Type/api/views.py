from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ConversationRequestSerializer, ConversationAnalysisSerializer
from .models import ConversationAnalysis, ConversationMessage, ConversationSummary
from .feature_extraction import extract_features
from .logic import classify_connection, connection_type_scores
from collections import defaultdict
from django.utils.dateparse import parse_datetime
from django.db.models import Q

class AnalyzeConnection(APIView):
    def post(self, request):
        serializer = ConversationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        features = extract_features(serializer.validated_data["messages"])
        probs = connection_type_scores(features)
        connection_type = max(probs, key=probs.get)
        confidence = round(probs[connection_type] * 100.0, 2)

        record = ConversationAnalysis.objects.create(
            connection_type=connection_type,
            confidence=confidence,
            emotional_warmth=features["emotional_warmth"],
            romantic_language=features["romantic_language"],
            spiritual_reference=features["spiritual_reference"],
            task_focus=features["task_focus"],
            formality=features["formality"]
        )

        response = ConversationAnalysisSerializer(record)
        return Response(response.data, status=status.HTTP_201_CREATED)


class AnalyzePairFromDB(APIView):
    def get(self, request):
        try:
            a = int(request.query_params.get("user_a_id"))
            b = int(request.query_params.get("user_b_id"))
        except (TypeError, ValueError):
            return Response({
                "detail": "Provide integer query params user_a_id and user_b_id"
            }, status=status.HTTP_400_BAD_REQUEST)

        user_a = min(a, b)
        user_b = max(a, b)

        msgs_qs = ConversationMessage.objects.filter(
            (Q(sender_id=user_a) & Q(receiver_id=user_b)) |
            (Q(sender_id=user_b) & Q(receiver_id=user_a))
        ).order_by("sent_at")

        msgs = list(msgs_qs.values("sender_id", "receiver_id", "message", "sent_at"))
        msg_payload = [
            {"sender": f"User {m['sender_id']}", "text": m["message"]}
            for m in msgs
        ]

        features = extract_features(msg_payload)
        # Use per-type probabilities to compute percentage confidences deterministically
        probs = connection_type_scores(features)
        best_type = max(probs, key=probs.get)
        confidence_pct = round(probs[best_type] * 100.0, 2)

        # Persist/update summary for this pair
        pair_key = f"{user_a}-{user_b}"
        last_message_at = msgs[-1]["sent_at"] if msgs else None
        message_count = len(msgs)
        ConversationSummary.objects.update_or_create(
            pair_key=pair_key,
            defaults={
                "user_a_id": user_a,
                "user_b_id": user_b,
                "last_message_at": last_message_at,
                "message_count": message_count,
                "connection_type": best_type,
                "confidence": confidence_pct,
                "emotional_warmth": features.get("emotional_warmth", 0.0),
                "romantic_language": features.get("romantic_language", 0.0),
                "spiritual_reference": features.get("spiritual_reference", 0.0),
                "task_focus": features.get("task_focus", 0.0),
                "formality": features.get("formality", 0.0),
                "emotional_intensity": features.get("emotional_intensity", 0.0),
            }
        )

        return Response({
            "pair_key": pair_key,
            "connection_type": best_type,
            "confidence": confidence_pct,
        }, status=status.HTTP_200_OK)


class ConnectionTypeDistribution(APIView):
    def get(self, request):
        # Optional filters to ensure results reflect "current" data
        q = ConversationMessage.objects.all()
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        if date_from:
            dt_from = parse_datetime(date_from)
            if dt_from:
                q = q.filter(sent_at__gte=dt_from)
        if date_to:
            dt_to = parse_datetime(date_to)
            if dt_to:
                q = q.filter(sent_at__lte=dt_to)

        qs = list(q.values("sender_id", "receiver_id", "message", "sent_at"))

        conversations = defaultdict(list)
        for row in qs:
            a = row["sender_id"] or 0
            b = row["receiver_id"] or 0
            key = (min(a, b), max(a, b))
            conversations[key].append({
                "sender": f"User {row['sender_id']}",
                "text": row["message"],
                "sent_at": row["sent_at"],
            })

        counts_top = {"Social": 0, "Romantic": 0, "Spiritual": 0, "Professional": 0}
        sums = {"Social": 0.0, "Romantic": 0.0, "Spiritual": 0.0, "Professional": 0.0}

        # Process conversations; optionally limit recent messages per pair
        limit = request.query_params.get("limit_messages_per_pair")
        try:
            limit = int(limit) if limit else None
        except ValueError:
            limit = None

        for key, msgs in conversations.items():
            msgs.sort(key=lambda m: m["sent_at"])  # chronological
            if limit:
                msgs = msgs[-limit:]
            msg_payload = [{"sender": m["sender"], "text": m["text"]} for m in msgs]

            features = extract_features(msg_payload)
            # Aggregate per-type probabilities
            probs = connection_type_scores(features)
            for t, p in probs.items():
                if t in sums:
                    sums[t] += p
            # Also keep a count of the top class for reference
            top = max(probs, key=probs.get)
            if top in counts_top:
                counts_top[top] += 1

        total_conversations = len(conversations)
        if total_conversations == 0:
            percentages = {k: 0.0 for k in sums}
        else:
            # Average probability per type across conversations -> percentage
            percentages = {k: round((v / total_conversations) * 100, 2) for k, v in sums.items()}

        return Response({
            "total_conversations": total_conversations,
            "counts_top": counts_top,
            "percentages": percentages,
        }, status=status.HTTP_200_OK)


class ConnectionTypeDistributionCached(APIView):
    def get(self, request):
        qs = ConversationSummary.objects.all()

        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        min_messages = request.query_params.get("min_messages")

        if date_from:
            dt_from = parse_datetime(date_from)
            if dt_from:
                qs = qs.filter(last_message_at__gte=dt_from)
        if date_to:
            dt_to = parse_datetime(date_to)
            if dt_to:
                qs = qs.filter(last_message_at__lte=dt_to)
        if min_messages:
            try:
                n = int(min_messages)
                qs = qs.filter(message_count__gte=n)
            except ValueError:
                pass

        # Recompute per-type probabilities from cached features to avoid LLM calls
        vals = qs.values(
            "connection_type",
            "emotional_warmth",
            "romantic_language",
            "spiritual_reference",
            "task_focus",
            "formality",
            "emotional_intensity",
        )

        counts_top = {"Social": 0, "Romantic": 0, "Spiritual": 0, "Professional": 0}
        sums = {"Social": 0.0, "Romantic": 0.0, "Spiritual": 0.0, "Professional": 0.0}

        total_conversations = 0
        for row in vals:
            features = {
                "emotional_warmth": row.get("emotional_warmth", 0.0),
                "romantic_language": row.get("romantic_language", 0.0),
                "spiritual_reference": row.get("spiritual_reference", 0.0),
                "task_focus": row.get("task_focus", 0.0),
                "formality": row.get("formality", 0.0),
                "emotional_intensity": row.get("emotional_intensity", 0.0),
            }
            probs = connection_type_scores(features)
            for t, p in probs.items():
                if t in sums:
                    sums[t] += p
            top = max(probs, key=probs.get)
            if top in counts_top:
                counts_top[top] += 1
            total_conversations += 1

        if total_conversations == 0:
            percentages = {k: 0.0 for k in sums}
        else:
            percentages = {k: round((v / total_conversations) * 100, 2) for k, v in sums.items()}

        return Response({
            "total_conversations": total_conversations,
            "counts_top": counts_top,
            "percentages": percentages,
            "source": "cached",
        }, status=status.HTTP_200_OK)
