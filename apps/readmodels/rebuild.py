"""Utility to rebuild read models from the event log."""

from __future__ import annotations

from django.db import transaction

from apps.events.models import Event
from apps.events.projector import project
from apps.readmodels.models import PayoutReadModel


def rebuild_all() -> int:
    """Drop and rebuild read models from scratch."""
    with transaction.atomic():
        PayoutReadModel.objects.all().delete()

    count = 0
    for event in Event.objects.order_by("id"):
        project(event)
        count += 1
    return count
