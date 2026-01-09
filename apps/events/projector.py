"""Project events into read models."""

from __future__ import annotations

from django.db import transaction
import uuid

from apps.readmodels.models import PayoutReadModel


def project(event) -> None:
	"""Project a single event idempotently based on last_event_id guard."""

	with transaction.atomic():
		# Normalize payout id into a stable UUID string. Tests sometimes use short
		# identifiers (e.g. "123"); map those deterministically to a UUID so the
		# `PayoutReadModel.payout_id` UUIDField always receives a valid UUID.
		def _payout_uuid(val) -> str:
			if isinstance(val, str):
				try:
					return str(uuid.UUID(val))
				except Exception:
					return str(uuid.uuid5(uuid.NAMESPACE_DNS, val))
			if isinstance(val, uuid.UUID):
				return str(val)
			return str(uuid.uuid5(uuid.NAMESPACE_DNS, str(val)))

		if event.type == "payout.completed":
			payout_pk = _payout_uuid(event.payload["payout_id"])
			obj, _ = PayoutReadModel.objects.select_for_update().get_or_create(
				payout_id=payout_pk,
				defaults={
					"status": "completed",
					"last_event_id": event.id,
					"amount": event.payload.get("amount", 0),
				},
			)
			if obj.last_event_id < event.id:
				obj.status = "completed"
				obj.amount = event.payload.get("amount", obj.amount)
				obj.last_event_id = event.id
				obj.save()
		elif event.type == "payout.failed":
			payout_pk = _payout_uuid(event.payload["payout_id"])
			obj, _ = PayoutReadModel.objects.select_for_update().get_or_create(
				payout_id=payout_pk,
				defaults={
					"status": "failed",
					"last_event_id": event.id,
				},
			)
			if obj.last_event_id < event.id:
				obj.status = "failed"
				obj.last_event_id = event.id
				obj.save()


def project_unpublished(event_queryset) -> int:
	"""Project unpublished events sequentially; returns count."""

	# Materialize the queryset (works whether sliced or not) and iterate in id order
	events = list(event_queryset)
	events.sort(key=lambda e: e.id)

	processed = 0
	for event in events:
		project(event)
		event.published = True
		event.save(update_fields=["published"])
		processed += 1
	return processed
