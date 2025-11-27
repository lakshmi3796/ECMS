from celery import shared_task, group
from django.conf import settings
from django.core.mail import EmailMessage
from django.utils import timezone
from .models import Campaign, Recipient, DeliveryLog
from django.db import transaction

BATCH_SIZE = getattr(settings, "CAMPAIGN_BATCH_SIZE", 500)

@shared_task
def schedule_campaign_send(campaign_id):
    """Kick off campaign: mark in-progress and spawn chunked tasks."""
    campaign = Campaign.objects.get(pk=campaign_id)
    campaign.status = Campaign.STATUS_IN_PROGRESS
    campaign.save(update_fields=["status"])

    recipient_ids = list(
        Recipient.objects.filter(status=Recipient.SUBSCRIBED).values_list("id", flat=True)
    )
    if not recipient_ids:
        # mark complete immediately
        campaign.status = Campaign.STATUS_COMPLETED
        campaign.save(update_fields=["status"])
        return

    chunks = [recipient_ids[i:i+BATCH_SIZE] for i in range(0, len(recipient_ids), BATCH_SIZE)]
    job = group(send_campaign_batch.s(campaign_id, chunk) for chunk in chunks)
    job.apply_async()  # fire-and-forget; Celery manages execution

@shared_task(bind=True, max_retries=3)
def send_campaign_batch(self, campaign_id, recipient_ids):
    campaign = Campaign.objects.get(pk=campaign_id)
    recipients = list(Recipient.objects.filter(id__in=recipient_ids))
    logs = []
    for r in recipients:
        try:
            msg = EmailMessage(
                subject=campaign.subject,
                body=campaign.content,
                to=[r.email],
            )
            # assume HTML; if plain text only set accordingly
            msg.content_subtype = "html"
            msg.send(fail_silently=False)
            logs.append(DeliveryLog(
                campaign=campaign,
                recipient=r,
                recipient_email=r.email,
                status=DeliveryLog.STATUS_SENT
            ))
        except Exception as exc:
            logs.append(DeliveryLog(
                campaign=campaign,
                recipient=r,
                recipient_email=r.email,
                status=DeliveryLog.STATUS_FAILED,
                failure_reason=str(exc)
            ))
    # bulk create logs
    DeliveryLog.objects.bulk_create(logs)

    # After batch created, check if campaign is complete
    maybe_mark_campaign_complete.delay(campaign_id)

@shared_task
def maybe_mark_campaign_complete(campaign_id):
    campaign = Campaign.objects.get(pk=campaign_id)
    total = Recipient.objects.filter(status=Recipient.SUBSCRIBED).count()
    processed = DeliveryLog.objects.filter(campaign=campaign).count()
    if total == 0 or processed >= total:
        campaign.status = Campaign.STATUS_COMPLETED
        campaign.save(update_fields=["status"])
        generate_report_and_email.delay(campaign_id)

@shared_task
def generate_report_and_email(campaign_id):
    import csv
    from io import StringIO
    from django.core.mail import EmailMessage

    campaign = Campaign.objects.get(pk=campaign_id)
    logs_qs = DeliveryLog.objects.filter(campaign=campaign).values(
        'recipient_email', 'status', 'failure_reason', 'processed_at'
    )

    sio = StringIO()
    writer = csv.writer(sio)
    writer.writerow(['recipient_email', 'status', 'failure_reason', 'processed_at'])
    for r in logs_qs.iterator():
        writer.writerow([r['recipient_email'], r['status'], r['failure_reason'] or '', r['processed_at']])

    admin_email = getattr(settings, "ADMIN_EMAIL", None)
    if admin_email:
        msg = EmailMessage(
            subject=f"Campaign Report: {campaign.name}",
            body="Attached campaign report.",
            to=[admin_email]
        )
        msg.attach(f"{campaign.name}-report.csv", sio.getvalue(), "text/csv")
        msg.send()
