from django.contrib import admin

from .models import Payout


@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    list_display = ("id", "idempotency_key", "status", "amount", "ledger_transaction_id", "created_at")
    search_fields = ("idempotency_key", "id", "ledger_transaction_id")
    list_filter = ("status",)
    readonly_fields = ("created_at", "updated_at")
