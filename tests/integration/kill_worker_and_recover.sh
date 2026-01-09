#!/usr/bin/env bash
set -euo pipefail

# Integration helper: kill worker, post payout, restart worker, run projector, verify readmodel
# This script is intended to be run from the repository root and assumes docker-compose is available.

PAYOUT_AMOUNT=${1:-"1.23"}
IDEMP=${2:-integration-$(date +%s)}

echo "Killing worker to simulate failure..."
docker compose kill worker || true
sleep 2

echo "Posting payout (idempotency=${IDEMP})"
curl -s -X POST -H "Content-Type: application/json" -H "Idempotency-Key: ${IDEMP}" -d "{\"amount\": \"${PAYOUT_AMOUNT}\"}" http://localhost:8000/api/payouts/ || true

echo "Restarting worker"
docker compose up -d worker
sleep 2

echo "Run projector to ensure events are projected"
docker compose exec -T web python manage.py run_projector --limit 200 || true

echo "Verify read model"
OUT=$(docker compose exec -T web python manage.py shell -c "from apps.readmodels.models import PayoutReadModel; import sys; qs=PayoutReadModel.objects.filter(amount='$PAYOUT_AMOUNT'); print(qs.count()); sys.stdout.flush()")
echo "ReadModel rows matching amount=${PAYOUT_AMOUNT}: $OUT"

if [ "$OUT" -ge 1 ]; then
  echo "Integration check: OK"
  exit 0
else
  echo "Integration check: FAILED"
  exit 2
fi
