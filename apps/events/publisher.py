"""Durably publish events to the outbox and websocket."""

from __future__ import annotations

import json

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import Event


def publish_event(event_type: str, payload: dict, *, source: str = "") -> Event:
    event = Event.objects.create(type=event_type, payload=payload, source=source)

    channel_layer = get_channel_layer()
    if channel_layer:
        group = payload.get("channel_group")
        if group:
            # Sanitize group name to conform to Channels' allowed characters
            # Allowed: ASCII alphanumerics, hyphens, underscores, periods; limit length < 100
            import re

            def _sanitize_group(name: str) -> str | None:
                if not isinstance(name, str):
                    return None
                sanitized = re.sub(r"[^A-Za-z0-9_.-]", "-", name)
                # truncate to 99 characters to be safe
                return sanitized[:99]

            safe_group = _sanitize_group(group)
            if safe_group:
                async_to_sync(channel_layer.group_send)(
                    safe_group,
                    {
                        "type": "send.event",
                        "payload": payload,
                    },
                )

    return event
