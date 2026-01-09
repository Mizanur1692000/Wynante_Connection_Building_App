from django.core.management.base import BaseCommand
from django.db import transaction
from collections import defaultdict
from api.models import ConversationMessage, ConversationSummary
from api.feature_extraction import extract_features
from api.logic import connection_type_scores

class Command(BaseCommand):
    help = "Backfill or update ConversationSummary from conversation_messages."

    def add_arguments(self, parser):
        parser.add_argument('--limit-messages-per-pair', type=int, default=50, help='Max recent messages per pair to analyze')
        parser.add_argument('--max-pairs', type=int, default=None, help='Limit number of pairs processed')
        parser.add_argument('--dry-run', action='store_true', help='Run without writing changes')

    def handle(self, *args, **options):
        limit_per_pair = options['limit_messages_per_pair']
        max_pairs = options['max_pairs']
        dry_run = options['dry_run']

        rows = list(ConversationMessage.objects.all().values('sender_id', 'receiver_id', 'message', 'sent_at'))
        conversations = defaultdict(list)
        for r in rows:
            a = r['sender_id'] or 0
            b = r['receiver_id'] or 0
            user_a = min(a, b)
            user_b = max(a, b)
            key = (user_a, user_b)
            conversations[key].append({
                'sender': f"User {r['sender_id']}",
                'text': r['message'],
                'sent_at': r['sent_at'],
            })

        pairs = list(conversations.items())
        if max_pairs is not None:
            pairs = pairs[:max_pairs]

        processed = 0
        created = 0
        updated = 0

        for (user_a, user_b), msgs in pairs:
            msgs.sort(key=lambda m: m['sent_at'])
            if limit_per_pair:
                msgs = msgs[-limit_per_pair:]

            msg_payload = [{"sender": m["sender"], "text": m["text"]} for m in msgs]
            last_message_at = msgs[-1]['sent_at'] if msgs else None
            message_count = len(msgs)

            features = extract_features(msg_payload)
            probs = connection_type_scores(features)
            connection_type = max(probs, key=probs.get)
            confidence = round(probs[connection_type] * 100.0, 2)

            pair_key = f"{user_a}-{user_b}"

            if dry_run:
                self.stdout.write(self.style.NOTICE(
                    f"DRY RUN pair {pair_key}: {connection_type} ({confidence}%) count={message_count}"
                ))
            else:
                with transaction.atomic():
                    obj, is_created = ConversationSummary.objects.update_or_create(
                        pair_key=pair_key,
                        defaults={
                            'user_a_id': user_a,
                            'user_b_id': user_b,
                            'last_message_at': last_message_at,
                            'message_count': message_count,
                            'connection_type': connection_type,
                            'confidence': confidence,
                            'emotional_warmth': features.get('emotional_warmth', 0.0),
                            'romantic_language': features.get('romantic_language', 0.0),
                            'spiritual_reference': features.get('spiritual_reference', 0.0),
                            'task_focus': features.get('task_focus', 0.0),
                            'formality': features.get('formality', 0.0),
                            'emotional_intensity': features.get('emotional_intensity', 0.0),
                        }
                    )
                    if is_created:
                        created += 1
                    else:
                        updated += 1

            processed += 1

        self.stdout.write(self.style.SUCCESS(
            f"Processed={processed}, created={created}, updated={updated}"
        ))
