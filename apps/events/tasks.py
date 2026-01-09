from celery import shared_task

from apps.events.models import Event
from apps.events.projector import project_unpublished


@shared_task
def project_outbox_batch(limit: int = 200) -> int:
    queryset = Event.objects.filter(published=False).order_by("id")[:limit]
    return project_unpublished(queryset)
