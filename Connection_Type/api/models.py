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
