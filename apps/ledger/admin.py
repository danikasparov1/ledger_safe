from django.contrib import admin

from .models import Account, LedgerTransaction, LedgerEntry


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "name", "created_at")
    search_fields = ("code", "name")


@admin.register(LedgerTransaction)
class LedgerTransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "idempotency_key", "description", "created_at")
    search_fields = ("idempotency_key", "id")


@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    list_display = ("id", "transaction", "account", "amount", "line", "memo", "created_at")
    search_fields = ("transaction__id", "account__code")
    list_filter = ("account",)
