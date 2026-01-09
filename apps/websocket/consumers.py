"""WebSocket consumer for payout updates."""

from __future__ import annotations

from channels.generic.websocket import AsyncJsonWebsocketConsumer


class PayoutConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        payout_id = self.scope["url_route"]["kwargs"]["payout_id"]
        self.group_name = f"payout:{payout_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):  # pragma: no cover - channels lifecycle
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):  # pragma: no cover - no client msgs
        await self.send_json({"echo": content})

    async def send_event(self, event):
        await self.send_json(event["payload"])
