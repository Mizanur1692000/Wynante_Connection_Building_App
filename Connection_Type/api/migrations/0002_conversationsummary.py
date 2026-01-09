from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ConversationSummary',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_a_id', models.IntegerField()),
                ('user_b_id', models.IntegerField()),
                ('pair_key', models.CharField(max_length=64, unique=True)),
                ('last_message_at', models.DateTimeField()),
                ('message_count', models.IntegerField(default=0)),
                ('connection_type', models.CharField(choices=[('Social', 'Social'), ('Romantic', 'Romantic'), ('Spiritual', 'Spiritual'), ('Professional', 'Professional')], max_length=50)),
                ('confidence', models.FloatField()),
                ('emotional_warmth', models.FloatField(default=0.0)),
                ('romantic_language', models.FloatField(default=0.0)),
                ('spiritual_reference', models.FloatField(default=0.0)),
                ('task_focus', models.FloatField(default=0.0)),
                ('formality', models.FloatField(default=0.0)),
                ('emotional_intensity', models.FloatField(default=0.0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'indexes': [
                    models.Index(fields=['user_a_id', 'user_b_id'], name='api_conversa_user_a__f7d8d3_idx'),
                    models.Index(fields=['last_message_at'], name='api_conversa_last_me_4a9e27_idx'),
                ],
            },
        ),
    ]
