"""Celery tasks for safe payout execution."""

from __future__ import annotations

from decimal import Decimal

from celery import shared_task
from django.db import transaction

from apps.events.publisher import publish_event
from apps.ledger.services import LedgerError, record_payout
from .models import Payout


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=5, max_retries=5)
def execute_payout(self, payout_id: str):
    """Execute payout idempotently and safely under retries.

    Flow:
    1) Lock payout row and move to processing unless already terminal.
    2) Record ledger transaction idempotently keyed by payout id.
    3) Persist completed status + ledger transaction id.
    4) Emit completion/failure event.
    """

    with transaction.atomic():
        payout = Payout.objects.select_for_update().get(id=payout_id)

        if payout.status == Payout.Status.COMPLETED and payout.ledger_transaction_id:
            return

        if payout.status == Payout.Status.FAILED:
            # Allow retries after failure; we re-enter processing state
            pass

        payout.status = Payout.Status.PROCESSING
        payout.error = ""
        payout.save(update_fields=["status", "error", "updated_at"])

    try:
        tx = record_payout(str(payout.id), Decimal(payout.amount))
    except LedgerError as exc:
        # LedgerError is non-retriable invariant breach; record and stop retries
        with transaction.atomic():
            payout = Payout.objects.select_for_update().get(id=payout.id)
            payout.status = Payout.Status.FAILED
            payout.error = str(exc)
            payout.save(update_fields=["status", "error", "updated_at"])

        publish_event(
            "payout.failed",
            {
                "payout_id": str(payout.id),
                "error": str(exc),
                "channel_group": f"payout:{payout.id}",
            },
        )
        return

    with transaction.atomic():
        payout = Payout.objects.select_for_update().get(id=payout.id)
        if payout.status == Payout.Status.COMPLETED and payout.ledger_transaction_id:
            # Another worker finished while we were recording; nothing to do
            return

        payout.status = Payout.Status.COMPLETED
        payout.ledger_transaction_id = tx.id
        payout.save(update_fields=["status", "ledger_transaction_id", "updated_at"])

    publish_event(
        "payout.completed",
        {
            "payout_id": str(payout.id),
            "amount": str(payout.amount),
            "ledger_transaction_id": str(tx.id),
            "channel_group": f"payout:{payout.id}",
        },
    )
