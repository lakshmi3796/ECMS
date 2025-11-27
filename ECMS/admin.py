from django.contrib import admin
from .models import Recipient, Campaign, DeliveryLog

@admin.register(Recipient)
class RecipientAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("name", "email")
    ordering = ("-created_at",)
    list_per_page = 50

@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ("name", "subject", "scheduled_at", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("name", "subject")
    ordering = ("-created_at",)
    list_per_page = 50
    readonly_fields = ("created_at", "updated_at")

@admin.register(DeliveryLog)
class DeliveryLogAdmin(admin.ModelAdmin):
    list_display = ("campaign", "recipient_email", "status", "processed_at")
    list_filter = ("status", "campaign")
    search_fields = ("recipient_email", "failure_reason")
    ordering = ("-processed_at",)
    list_per_page = 100
    readonly_fields = ("processed_at",)
