Release notes - Prepared submission

Summary

This repository implements the Ledger-Safe Report and Payout Engine assignment. Recent updates include:

- Hardened payout execution to guarantee exactly-once behavior (use of `transaction.on_commit` and stronger DB constraints).
- Added DB-level constraints that enforce payout ↔ ledger linkage and immutable double-entry ledger triggers.
- Added automated tests covering idempotency, concurrency, ledger invariants and read-model rebuilds.
- Added CI workflow to run the test matrix using Docker Compose.
- Documentation updates, license and contributing guide.

How to evaluate

1. Build the stack: `docker compose up --build`.
2. Run tests: `docker compose exec -T web python manage.py test --keepdb`.
3. Create a payout and watch worker logs to confirm the end-to-end execution.

Notes

- This is a candidate submission: documented trade-offs and further hardening suggestions are included in the README.
