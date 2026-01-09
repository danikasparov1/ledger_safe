"""Management command to run the event projector manually.

Usage: `python manage.py run_projector [--limit N]`
"""
from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.events.models import Event
from apps.events.projector import project_unpublished


class Command(BaseCommand):
    help = "Project unpublished events into read models"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=200, help="Maximum events to process")

    def handle(self, *args, **options):
        limit = options.get("limit") or 200
        qs = Event.objects.filter(published=False).order_by("id")[:limit]
        count = project_unpublished(qs)
        self.stdout.write(self.style.SUCCESS(f"Projected {count} event(s)"))
