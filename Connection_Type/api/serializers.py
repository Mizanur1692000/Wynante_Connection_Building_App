from rest_framework import serializers
from .models import ConversationAnalysis

class MessageSerializer(serializers.Serializer):
    sender = serializers.CharField()
    text = serializers.CharField()

class ConversationRequestSerializer(serializers.Serializer):
    messages = MessageSerializer(many=True)

class ConversationAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConversationAnalysis
        fields = '__all__'
