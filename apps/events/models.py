"""Event outbox for ordered, idempotent projections."""

from __future__ import annotations

import uuid

from django.db import models


class Event(models.Model):
    id = models.BigAutoField(primary_key=True)
    type = models.CharField(max_length=255)
    payload = models.JSONField()
    source = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    published = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["published", "id"], name="event_publish_idx"),
        ]
