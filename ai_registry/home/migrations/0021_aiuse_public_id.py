import uuid

from django.db import migrations, models


def populate_public_ids(apps, schema_editor):
    AIUse = apps.get_model("home", "AIUse")

    for ai_use in AIUse.objects.filter(public_id__isnull=True):
        ai_use.public_id = uuid.uuid4()
        ai_use.save(update_fields=["public_id"])


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0020_rename_registryentry_aiuse"),
    ]

    operations = [
        migrations.AddField(
            model_name="aiuse",
            name="public_id",
            field=models.UUIDField(
                null=True,
                editable=False,
            ),
        ),
        migrations.RunPython(
            populate_public_ids,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="aiuse",
            name="public_id",
            field=models.UUIDField(
                default=uuid.uuid4,
                editable=False,
                unique=True,
            ),
        ),
    ]
