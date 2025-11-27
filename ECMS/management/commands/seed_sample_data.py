from django.core.management.base import BaseCommand
from ECMS.models import Recipient, Campaign
from django.utils import timezone

class Command(BaseCommand):
    help = 'Seed sample recipients and a campaign'

    def handle(self, *args, **options):
        self.stdout.write('Seeding sample data...')

        # Create recipients
        recipients = []
        for i in range(1, 1001):
            recipients.append(
                Recipient(
                    name=f'User {i}',
                    email=f'user{i}@example.com',
                    status=Recipient.SUBSCRIBED,
                )
            )
        Recipient.objects.bulk_create(recipients, ignore_conflicts=True)

        # Create a sample scheduled campaign
        Campaign.objects.create(
            name='Promo November',
            subject='Welcome to our Email Campaign!',
            content='<p>Hello! This is a sample campaign.</p>',
            scheduled_at=timezone.now() + timezone.timedelta(minutes=5),
            status=Campaign.STATUS_SCHEDULED,
        )

        self.stdout.write(self.style.SUCCESS('Sample data seeded successfully.'))
