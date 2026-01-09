from decimal import Decimal

from django.db import DatabaseError, IntegrityError, connection, transaction
from django.test import TestCase

from apps.ledger.models import EntrySpec
from apps.ledger.services import LedgerError, post_transaction


class LedgerInvariantTests(TestCase):
    def test_requires_two_entries(self):
        with self.assertRaises(LedgerError):
            post_transaction(
                idempotency_key="k1",
                description="bad",
                entries=[EntrySpec(account_code="a", amount=Decimal("1"))],
            )

    def test_requires_balance_zero(self):
        with self.assertRaises(LedgerError):
            post_transaction(
                idempotency_key="k2",
                description="unbalanced",
                entries=[
                    EntrySpec(account_code="a", amount=Decimal("1")),
                    EntrySpec(account_code="b", amount=Decimal("1")),
                ],
            )

    def test_enforces_balance_at_db(self):
        # First insert valid transaction
        tx = post_transaction(
            idempotency_key="k3",
            description="ok",
            entries=[
                EntrySpec(account_code="a", amount=Decimal("1")),
                EntrySpec(account_code="b", amount=Decimal("-1")),
            ],
        )
        # Attempt to tamper should fail due to trigger; force constraint check immediately
        with self.assertRaises(DatabaseError):
            with transaction.atomic():
                tx.ledgerentry_set.create(
                    account=tx.ledgerentry_set.first().account,
                    amount=Decimal("1"),
                    line=5,
                )
                with connection.cursor() as cursor:
                    cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")

    def test_idempotency_key_returns_existing(self):
        tx1 = post_transaction(
            idempotency_key="k4",
            description="first",
            entries=[
                EntrySpec(account_code="a", amount=Decimal("2")),
                EntrySpec(account_code="b", amount=Decimal("-2")),
            ],
        )
        tx2 = post_transaction(
            idempotency_key="k4",
            description="second",
            entries=[
                EntrySpec(account_code="a", amount=Decimal("2")),
                EntrySpec(account_code="b", amount=Decimal("-2")),
            ],
        )
        self.assertEqual(tx1.id, tx2.id)
