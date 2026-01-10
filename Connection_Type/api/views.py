from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ConnectionDistributionSerializer
from .services.inference import infer_pair_connection

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
