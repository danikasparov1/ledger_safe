from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Payout",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, serialize=False, editable=False)),
                ("idempotency_key", models.CharField(max_length=255, unique=True)),
                ("amount", models.DecimalField(max_digits=18, decimal_places=2)),
                ("status", models.CharField(max_length=20, choices=[('pending','Pending'),('processing','Processing'),('completed','Completed'),('failed','Failed')], default='pending')),
                ("error", models.TextField(blank=True)),
                ("ledger_transaction_id", models.UUIDField(null=True, blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"indexes": [models.Index(fields=["status"], name="payout_status_idx")]},
        ),
    ]
