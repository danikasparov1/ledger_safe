from django.db import migrations, models
import uuid


def create_triggers(apps, schema_editor):
    schema_editor.execute(
        """
        CREATE OR REPLACE FUNCTION ledger_assert_balanced() RETURNS trigger AS $$
        DECLARE
            total NUMERIC;
            cnt INT;
        BEGIN
            SELECT COALESCE(SUM(amount),0), COUNT(*) INTO total, cnt FROM ledger_ledgerentry WHERE transaction_id = NEW.transaction_id;
            IF cnt <> 2 THEN
                RAISE EXCEPTION 'ledger transaction %% must have exactly two entries (has %%)', NEW.transaction_id, cnt;
            END IF;
            IF total <> 0 THEN
                RAISE EXCEPTION 'ledger transaction %% not balanced (sum %% )', NEW.transaction_id, total;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE CONSTRAINT TRIGGER ledger_transaction_balanced
        AFTER INSERT OR UPDATE ON ledger_ledgerentry
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW EXECUTE FUNCTION ledger_assert_balanced();

        CREATE OR REPLACE FUNCTION ledger_entry_immutable() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'ledger entries are append-only';
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER ledger_entry_no_update
        BEFORE UPDATE ON ledger_ledgerentry
        FOR EACH ROW EXECUTE FUNCTION ledger_entry_immutable();

        CREATE TRIGGER ledger_entry_no_delete
        BEFORE DELETE ON ledger_ledgerentry
        FOR EACH ROW EXECUTE FUNCTION ledger_entry_immutable();

        CREATE OR REPLACE FUNCTION ledger_transaction_immutable() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'ledger transactions are immutable';
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER ledger_tx_no_update
        BEFORE UPDATE OR DELETE ON ledger_ledgertransaction
        FOR EACH ROW EXECUTE FUNCTION ledger_transaction_immutable();
        """
    )


def drop_triggers(apps, schema_editor):
    schema_editor.execute(
        """
        DROP TRIGGER IF EXISTS ledger_transaction_balanced ON ledger_ledgerentry;
        DROP FUNCTION IF EXISTS ledger_assert_balanced();
        DROP TRIGGER IF EXISTS ledger_entry_no_update ON ledger_ledgerentry;
        DROP TRIGGER IF EXISTS ledger_entry_no_delete ON ledger_ledgerentry;
        DROP FUNCTION IF EXISTS ledger_entry_immutable();
        DROP TRIGGER IF EXISTS ledger_tx_no_update ON ledger_ledgertransaction;
        DROP FUNCTION IF EXISTS ledger_transaction_immutable();
        """
    )


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Account",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, serialize=False, editable=False)),
                ("code", models.CharField(max_length=64, unique=True)),
                ("name", models.CharField(max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="LedgerTransaction",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, serialize=False, editable=False)),
                ("idempotency_key", models.CharField(max_length=255, unique=True)),
                ("description", models.CharField(max_length=255, blank=True)),
                ("metadata", models.JSONField(default=dict, blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="LedgerEntry",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, serialize=False, editable=False)),
                ("amount", models.DecimalField(max_digits=18, decimal_places=2)),
                ("line", models.PositiveSmallIntegerField()),
                ("memo", models.CharField(max_length=255, blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "account",
                    models.ForeignKey(on_delete=models.deletion.PROTECT, to="ledger.account"),
                ),
                (
                    "transaction",
                    models.ForeignKey(on_delete=models.deletion.PROTECT, to="ledger.ledgertransaction"),
                ),
            ],
            options={
                "constraints": [
                    models.CheckConstraint(check=~models.Q(amount=0), name="ledger_amount_non_zero"),
                    models.UniqueConstraint(fields=["transaction", "line"], name="ledger_entry_unique_line"),
                ],
            },
        ),
        migrations.RunPython(create_triggers, drop_triggers),
    ]
