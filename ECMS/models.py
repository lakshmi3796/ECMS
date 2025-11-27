from django.db import models
from django.utils import timezone

class Recipient(models.Model):
    SUBSCRIBED = 'sub'
    UNSUBSCRIBED = 'unsub'
    STATUS_CHOICES = [(SUBSCRIBED, 'Subscribed'), (UNSUBSCRIBED, 'Unsubscribed')]

    name = models.CharField(max_length=200, blank=True)
    email = models.EmailField(unique=True, db_index=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=SUBSCRIBED)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email

class Campaign(models.Model):
    STATUS_DRAFT = 'draft'
    STATUS_SCHEDULED = 'scheduled'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_COMPLETED = 'completed'
    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_SCHEDULED, 'Scheduled'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_COMPLETED, 'Completed'),
    ]

    name = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)
    content = models.TextField()  # plain text or HTML
    scheduled_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def total_recipients(self):
        return Recipient.objects.filter(status=Recipient.SUBSCRIBED).count()

    def sent_count(self):
        return self.deliverylog_set.filter(status=DeliveryLog.STATUS_SENT).count()

    def failed_count(self):
        return self.deliverylog_set.filter(status=DeliveryLog.STATUS_FAILED).count()

    def __str__(self):
        return self.name

class DeliveryLog(models.Model):
    STATUS_SENT = 'sent'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = [(STATUS_SENT, 'Sent'), (STATUS_FAILED, 'Failed')]

    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    recipient = models.ForeignKey(Recipient, on_delete=models.SET_NULL, null=True, blank=True)
    recipient_email = models.EmailField(db_index=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    failure_reason = models.TextField(blank=True, null=True)
    attempt = models.IntegerField(default=1)
    processed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=['campaign', 'recipient_email']),
            models.Index(fields=['-processed_at']),
        ]

    def __str__(self):
        return f"{self.recipient_email} - {self.status}"
