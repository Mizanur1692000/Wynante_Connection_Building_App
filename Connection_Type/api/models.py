from django.db import models

class ConversationAnalysis(models.Model):
    CONNECTION_TYPES = [
        ('Social', 'Social'),
        ('Romantic', 'Romantic'),
        ('Spiritual', 'Spiritual'),
        ('Professional', 'Professional')
    ]

    connection_type = models.CharField(max_length=50, choices=CONNECTION_TYPES)
    confidence = models.FloatField()
    emotional_warmth = models.FloatField()
    romantic_language = models.FloatField()
    spiritual_reference = models.FloatField()
    task_focus = models.FloatField()
    formality = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.connection_type} ({self.confidence})"


class ConversationMessage(models.Model):
    id = models.AutoField(primary_key=True)
    sender_id = models.IntegerField(null=True, blank=True)
    receiver_id = models.IntegerField(null=True, blank=True)
    message = models.TextField()
    sent_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'conversation_messages'


class ConversationSummary(models.Model):
    CONNECTION_TYPES = [
        ('Social', 'Social'),
        ('Romantic', 'Romantic'),
        ('Spiritual', 'Spiritual'),
        ('Professional', 'Professional')
    ]

    # canonical pair order: user_a_id <= user_b_id
    user_a_id = models.IntegerField()
    user_b_id = models.IntegerField()
    pair_key = models.CharField(max_length=64, unique=True)
    last_message_at = models.DateTimeField()
    message_count = models.IntegerField(default=0)

    # classification result
    connection_type = models.CharField(max_length=50, choices=CONNECTION_TYPES)
    confidence = models.FloatField()

    # cached features
    emotional_warmth = models.FloatField(default=0.0)
    romantic_language = models.FloatField(default=0.0)
    spiritual_reference = models.FloatField(default=0.0)
    task_focus = models.FloatField(default=0.0)
    formality = models.FloatField(default=0.0)
    emotional_intensity = models.FloatField(default=0.0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["user_a_id", "user_b_id"]),
            models.Index(fields=["last_message_at"]),
        ]

    def __str__(self):
        return f"{self.pair_key}: {self.connection_type} ({self.confidence})"
