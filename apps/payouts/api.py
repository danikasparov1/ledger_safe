"""API for initiating idempotent payouts."""

from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.http import HttpRequest
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Payout
from .tasks import execute_payout


class PayoutCreateView(APIView):
    def post(self, request: HttpRequest):
        key = request.headers.get("Idempotency-Key")
        if not key:
            return Response({"error": "Missing Idempotency-Key header"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            amount = Decimal(request.data.get("amount"))
        except Exception:
            return Response({"error": "Invalid amount"}, status=status.HTTP_400_BAD_REQUEST)

        if amount <= 0:
            return Response({"error": "Amount must be positive"}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            payout, created = Payout.objects.select_for_update().get_or_create(
                idempotency_key=key,
                defaults={"amount": amount, "status": Payout.Status.PENDING},
            )

            if not created:
                try:
                    payout.assert_same_amount(amount)
                except ValueError:
                    return Response({"error": "Idempotency key reused with different amount"}, status=status.HTTP_409_CONFLICT)

            should_enqueue = created or payout.status in {Payout.Status.PENDING, Payout.Status.FAILED}

            # Ensure the task is only sent to the broker after the DB transaction commits.
            if should_enqueue:
                transaction.on_commit(lambda: execute_payout.delay(str(payout.id)))

        return Response({"payout_id": str(payout.id), "status": payout.status})
