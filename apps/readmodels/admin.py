from django.contrib import admin

from .models import PayoutReadModel


@admin.register(PayoutReadModel)
class PayoutReadModelAdmin(admin.ModelAdmin):
    list_display = ("payout_id", "status", "amount", "last_event_id")
    search_fields = ("payout_id",)
    list_filter = ("status",)
