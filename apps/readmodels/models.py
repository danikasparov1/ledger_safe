"""Read models derived from events."""

from __future__ import annotations

from django.db import models


class PayoutReadModel(models.Model):
    payout_id = models.UUIDField(primary_key=True)
    status = models.CharField(max_length=20)
    last_event_id = models.BigIntegerField(default=0)
    amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)

    class Meta:
        indexes = [
            models.Index(fields=["status"], name="payout_read_status_idx"),
        ]
