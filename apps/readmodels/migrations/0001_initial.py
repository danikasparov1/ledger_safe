from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name='PayoutReadModel',
            fields=[
                ('payout_id', models.UUIDField(primary_key=True, serialize=False)),
                ('status', models.CharField(max_length=20)),
                ('last_event_id', models.BigIntegerField(default=0)),
                ('amount', models.DecimalField(max_digits=18, decimal_places=2, default=0)),
            ],
            options={'indexes': [models.Index(fields=['status'], name='payout_read_status_idx')]},
        ),
    ]
