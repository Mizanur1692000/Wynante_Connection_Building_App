from rest_framework import serializers
from .constants import CONNECTION_TYPE_KEYS

class ConnectionDistributionSerializer(serializers.Serializer):
    highest_connection_type = serializers.ChoiceField(choices=CONNECTION_TYPE_KEYS)
    distribution = serializers.DictField(child=serializers.IntegerField(min_value=0, max_value=100))
    pair_key = serializers.CharField()
    message_count = serializers.IntegerField(min_value=0)


class ProfileInputSerializer(serializers.Serializer):
    # Mandatory session_id: all functional endpoints require it
    session_id = serializers.CharField(required=True, allow_blank=False)
    about_me = serializers.CharField(allow_blank=True, required=False)
    interests = serializers.CharField(allow_blank=True, required=False)
    looking_for = serializers.CharField(allow_blank=True, required=False)
    education = serializers.CharField(allow_blank=True, required=False)
    occupation = serializers.CharField(allow_blank=True, required=False)
    relationship_status = serializers.CharField(allow_blank=True, required=False)
    limit = serializers.IntegerField(min_value=1, required=False, help_text="Limit the number of recent posts/comments to analyze.")
