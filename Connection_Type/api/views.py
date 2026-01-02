from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ConversationRequestSerializer, ConversationAnalysisSerializer
from .models import ConversationAnalysis
from llm_service.llm import extract_features
from .logic import classify_connection

class AnalyzeConnection(APIView):
    def post(self, request):
        serializer = ConversationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        features = extract_features(serializer.validated_data["messages"])
        connection_type, confidence = classify_connection(features)

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
