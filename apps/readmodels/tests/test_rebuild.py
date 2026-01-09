from django.test import TestCase

from apps.events.models import Event
from apps.events.projector import project_unpublished
from apps.readmodels.models import PayoutReadModel
from apps.readmodels.rebuild import rebuild_all


class ReadModelRebuildTests(TestCase):
    def test_project_and_rebuild(self):
        Event.objects.create(type="payout.completed", payload={"payout_id": "123", "amount": "1.00"})
        Event.objects.create(type="payout.failed", payload={"payout_id": "456", "error": "oops"})

        count = project_unpublished(Event.objects.filter(published=False))
        self.assertEqual(count, 2)
        self.assertEqual(PayoutReadModel.objects.count(), 2)

        # Now rebuild from scratch
        rebuild_all()
        self.assertEqual(PayoutReadModel.objects.count(), 2)
