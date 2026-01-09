"""Ledger domain services enforcing double-entry invariants."""

from __future__ import annotations

from decimal import Decimal
from typing import Iterable, Sequence

from django.db import transaction

from .models import Account, EntrySpec, LedgerEntry, LedgerTransaction


class LedgerError(Exception):
	"""Raised when ledger invariants would be violated."""


def ensure_account(code: str, name: str | None = None) -> Account:
	account, _ = Account.objects.get_or_create(code=code, defaults={"name": name or code})
	return account


def post_transaction(
	*,
	idempotency_key: str,
	description: str,
	entries: Sequence[EntrySpec],
	metadata: dict | None = None,
) -> LedgerTransaction:
	"""
	Persist a balanced double-entry transaction.

	Guards:
	- Exactly two entries
	- Sum equals zero
	- Idempotency by key
	- Immutable ledger enforced by DB triggers (see migration)
	"""

	if len(entries) != 2:
		raise LedgerError("Double-entry requires exactly two legs")

	total = sum((Decimal(e.amount) for e in entries), Decimal("0"))
	if total != Decimal("0"):
		raise LedgerError("Transaction must balance to zero")

	with transaction.atomic():
		tx, created = LedgerTransaction.objects.get_or_create(
			idempotency_key=idempotency_key,
			defaults={"description": description, "metadata": metadata or {}},
		)

		if not created:
			return tx

		for idx, entry in enumerate(entries):
			account = ensure_account(entry.account_code)
			LedgerEntry.objects.create(
				transaction=tx,
				account=account,
				amount=entry.amount,
				line=idx,
				memo=entry.memo,
			)

		return tx


def record_payout(payout_id: str, amount: Decimal) -> LedgerTransaction:
	"""Record a payout by debiting liabilities and crediting cash/bank."""

	return post_transaction(
		idempotency_key=f"payout:{payout_id}",
		description="payout",
		metadata={"payout_id": payout_id},
		entries=[
			EntrySpec(account_code="liability:payouts", amount=-amount, memo="Release liability"),
			EntrySpec(account_code="cash:bank", amount=amount, memo="Cash out"),
		],
	)
