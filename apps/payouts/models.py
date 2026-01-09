from __future__ import annotations

import uuid
from decimal import Decimal

from django.db import models
from django.db.models import Q


class Payout(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    idempotency_key = models.CharField(max_length=255, unique=True)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    error = models.TextField(blank=True)
    ledger_transaction_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["status"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=~Q(status="completed") | Q(ledger_transaction_id__isnull=False),
                name="payout_completed_requires_tx",
            ),
            models.UniqueConstraint(
                fields=["ledger_transaction_id"],
                name="payout_unique_ledger_tx",
                condition=Q(ledger_transaction_id__isnull=False),
            ),
        ]

    def __str__(self) -> str:  # pragma: no cover - repr helper
        return f"Payout<{self.id}> {self.status} {self.amount}"

    @property
    def is_terminal(self) -> bool:
        return self.status in {self.Status.COMPLETED, self.Status.FAILED}

    def assert_same_amount(self, amount: Decimal) -> None:
        if Decimal(amount) != self.amount:
            raise ValueError("Idempotent payout must use identical amount")
