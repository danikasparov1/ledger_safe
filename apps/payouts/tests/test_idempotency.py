from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from apps.payouts.models import Payout


class PayoutIdempotencyTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_idempotent_create_same_key(self):
        url = reverse("payout-create")
        headers = {"HTTP_IDEMPOTENCY_KEY": "abc"}
        res1 = self.client.post(url, {"amount": "10.00"}, **headers, format="json")
        res2 = self.client.post(url, {"amount": "10.00"}, **headers, format="json")
        self.assertEqual(res1.status_code, 200)
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res1.data["payout_id"], res2.data["payout_id"])

    def test_conflicting_amount_rejected(self):
        url = reverse("payout-create")
        headers = {"HTTP_IDEMPOTENCY_KEY": "abc2"}
        self.client.post(url, {"amount": "5.00"}, **headers, format="json")
        res = self.client.post(url, {"amount": "6.00"}, **headers, format="json")
        self.assertEqual(res.status_code, 409)

    def test_status_progression(self):
        payout = Payout.objects.create(idempotency_key="xyz", amount=Decimal("3.00"))
        payout.status = Payout.Status.COMPLETED
        payout.ledger_transaction_id = "11111111-1111-1111-1111-111111111111"
        payout.save()
        url = reverse("payout-create")
        headers = {"HTTP_IDEMPOTENCY_KEY": "xyz"}
        res = self.client.post(url, {"amount": "3.00"}, **headers, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["status"], Payout.Status.COMPLETED)
