from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("payouts", "0002_rename_payout_status_idx_payouts_pay_status_a5ad2e_idx"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="payout",
            constraint=models.CheckConstraint(
                check=~models.Q(status="completed") | models.Q(ledger_transaction_id__isnull=False),
                name="payout_completed_requires_tx",
            ),
        ),
        migrations.AddConstraint(
            model_name="payout",
            constraint=models.UniqueConstraint(
                fields=["ledger_transaction_id"],
                name="payout_unique_ledger_tx",
                condition=models.Q(ledger_transaction_id__isnull=False),
            ),
        ),
    ]
