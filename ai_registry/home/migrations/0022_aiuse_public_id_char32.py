import uuid

import home.models.ai_use
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("home", "0021_aiuse_public_id"),
    ]

    operations = [
        migrations.AlterField(
            model_name="aiuse",
            name="public_id",
            field=home.models.ai_use.Char32UUIDField(
                default=uuid.uuid4,
                editable=False,
                unique=True,
            ),
        ),
    ]
