import threading
from decimal import Decimal

from django.db import connections
from django.test import TransactionTestCase, TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from apps.events.models import Event
from apps.events.projector import project
from apps.ledger.models import LedgerEntry, LedgerTransaction
from apps.payouts.models import Payout
from apps.payouts.tasks import execute_payout
from apps.readmodels.models import PayoutReadModel
from apps.readmodels.rebuild import rebuild_all


class PayoutConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.url = reverse("payout-create")

    def tearDown(self):
        connections.close_all()

    @classmethod
    def tearDownClass(cls):  # noqa: D401
        super().tearDownClass()
        connections.close_all()

    def _post(self, results):
        client = APIClient()
        res = client.post(self.url, {"amount": "10.00"}, HTTP_IDEMPOTENCY_KEY="concurrent", format="json")
        results.append(res)
        connections.close_all()

    def test_concurrent_requests_same_key(self):
        results = []
        t1 = threading.Thread(target=self._post, args=(results,))
        t2 = threading.Thread(target=self._post, args=(results,))
        t1.start(); t2.start(); t1.join(); t2.join()

        self.assertEqual(Payout.objects.count(), 1)
        self.assertEqual(results[0].status_code, 200)
        self.assertEqual(results[1].status_code, 200)
        self.assertEqual(results[0].data["payout_id"], results[1].data["payout_id"])

        connections.close_all()


class PayoutTaskIdempotencyTests(TestCase):
    def test_task_reexecution_not_duplicate(self):
        payout = Payout.objects.create(idempotency_key="task-1", amount=Decimal("5.00"))

        execute_payout.apply(args=[str(payout.id)]).get()
        execute_payout.apply(args=[str(payout.id)]).get()

        payout.refresh_from_db()
        self.assertEqual(payout.status, Payout.Status.COMPLETED)
        self.assertIsNotNone(payout.ledger_transaction_id)

        txs = LedgerTransaction.objects.filter(idempotency_key=f"payout:{payout.id}")
        self.assertEqual(txs.count(), 1)
        self.assertEqual(LedgerEntry.objects.filter(transaction=txs.first()).count(), 2)


class EventProjectionTests(TestCase):
    def test_out_of_order_events_do_not_regress(self):
        payout_id = "0d1056f1-5a47-4c47-b021-3a2b8762f200"
        older = Event.objects.create(
            type="payout.failed", payload={"payout_id": payout_id, "error": "boom"}
        )
        newer = Event.objects.create(
            type="payout.completed",
            payload={"payout_id": payout_id, "amount": "12.00"},
        )

        project(newer)
        project(older)

        rm = PayoutReadModel.objects.get(payout_id=payout_id)
        self.assertEqual(rm.status, "completed")
        self.assertEqual(rm.last_event_id, newer.id)

    def test_rebuild_applies_full_log(self):
        payout_id = "1b2c88a2-90bc-4f31-8b3d-2c3a85c8b301"
        Event.objects.create(type="payout.failed", payload={"payout_id": payout_id, "error": "x"})
        Event.objects.create(
            type="payout.completed",
            payload={"payout_id": payout_id, "amount": "7.50"},
        )

        count = rebuild_all()
        self.assertEqual(count, 2)

        rm = PayoutReadModel.objects.get(payout_id=payout_id)
        self.assertEqual(rm.status, "completed")
        self.assertEqual(rm.amount, Decimal("7.50"))
        self.assertGreater(rm.last_event_id, 0)
