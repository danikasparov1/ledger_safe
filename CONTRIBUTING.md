Contributing

Thanks for taking an interest in this repository. This project is an assignment-style codebase (Ledger-Safe Report and Payout Engine). If you'd like to contribute or run the project locally, follow these steps.

Running locally

1. Copy environment file:

   cp .env.example .env

2. Build and start the stack:

   docker compose up --build

3. Create a superuser in the web container (optional):

   docker compose exec web python manage.py createsuperuser

Running tests

- Run the full test suite (uses the compose stack):

  docker compose exec -T web python manage.py test --keepdb

- To run tests without docker, set up a Python venv, install dependencies via `pyproject.toml`, and ensure Postgres + Redis are running and configured in `.env`.

Submitting changes

- Fork the repository, create a feature branch, make changes and tests, and open a PR.
- CI runs automatically and must pass before merge.

Code style

- Keep changes small and well-tested. Prefer explicitness in correctness-critical code.
