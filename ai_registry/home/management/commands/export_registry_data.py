import json
from io import StringIO
from pathlib import Path

from django.conf import settings
from django.core.management import BaseCommand, CommandError, call_command

INTERNAL_FIELDS = {
    "home.aisystem": {"comments"},
    "home.deployment": {"comments"},
    "home.aiuse": {"comments"},
}


class Command(BaseCommand):
    help = (
        "Export registry data as a reusable Django JSON fixture while omitting "
        "internal comment fields."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            type=Path,
            default=settings.BASE_DIR / "data" / "registry.json",
            help="Output path. Defaults to data/registry.json.",
        )

    def handle(self, *args, **options):
        serialized = StringIO()
        call_command(
            "dumpdata",
            "home",
            format="json",
            indent=2,
            use_natural_foreign_keys=True,
            use_natural_primary_keys=True,
            stdout=serialized,
        )

        records = json.loads(serialized.getvalue())
        unpublished_count = sum(
            1
            for record in records
            if record.get("model") == "home.aiuse"
            and record.get("fields", {}).get("published") is False
        )
        if unpublished_count:
            raise CommandError(
                "Registry snapshot export aborted: "
                f"{unpublished_count} unpublished AI use(s) are present in the "
                "serialized snapshot. Review them before exporting data intended "
                "for the repository."
            )

        for record in records:
            fields = record.get("fields", {})
            for field_name in INTERNAL_FIELDS.get(record.get("model"), ()):
                fields.pop(field_name, None)

        output_path = options["output"]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(records, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Exported {len(records)} registry objects to {output_path}"
            )
        )
