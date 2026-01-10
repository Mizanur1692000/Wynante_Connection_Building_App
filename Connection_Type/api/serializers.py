from rest_framework import serializers
from .constants import CONNECTION_TYPE_KEYS

class ConnectionDistributionSerializer(serializers.Serializer):
    highest_connection_type = serializers.ChoiceField(choices=CONNECTION_TYPE_KEYS)
    distribution = serializers.DictField(child=serializers.IntegerField(min_value=0, max_value=100))
    pair_key = serializers.CharField()
    message_count = serializers.IntegerField(min_value=0)
