"""Double-entry ledger models with immutability guarantees."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal

from django.db import models
from django.db.models import CheckConstraint, Q


class Account(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:  # pragma: no cover - repr helper
        return f"{self.code}"


class LedgerTransaction(models.Model):
    """Immutable logical transaction grouped by idempotency key."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    idempotency_key = models.CharField(max_length=255, unique=True)
    description = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class LedgerEntry(models.Model):
    """Append-only financial record tied to a transaction."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction = models.ForeignKey(LedgerTransaction, on_delete=models.PROTECT)
    account = models.ForeignKey(Account, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    line = models.PositiveSmallIntegerField()
    memo = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            CheckConstraint(check=~Q(amount=0), name="ledger_amount_non_zero"),
            models.UniqueConstraint(
                fields=["transaction", "line"], name="ledger_entry_unique_line"
            ),
        ]


@dataclass(frozen=True)
class EntrySpec:
    account_code: str
    amount: Decimal
    memo: str = ""
