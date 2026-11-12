import json
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from .models.ai_use import (
    AISystem,
    AIUse,
    AIUseStatusObservation,
    Assessment,
    Deployment,
    Institution,
    Source,
)
from .models.tags import AreaTag, GenericTag, TaggedArea, TaggedGeneric


class RegistryDataExportTests(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="Instytucja testowa")
        self.system = AISystem.objects.create(
            name="System testowy",
            comments="[POC IMPORT ID: SYSTEM-001]",
        )
        self.deployment = Deployment.objects.create(
            institution=self.institution,
            ai_system=self.system,
            comments="[POC IMPORT ID: DEPLOYMENT-001]",
        )
        self.ai_use = AIUse.objects.create(
            deployment=self.deployment,
            name="Zastosowanie testowe",
            published=True,
            comments="[POC IMPORT ID: USE-001]",
        )
        self.ai_use.areas.add("Administracja")
        self.ai_use.tags.add("OCR")

        self.assessment = Assessment.objects.create(
            ai_use=self.ai_use,
            assessment_type="dpia",
            status="yes",
            comment="Ocena wykonana",
        )
        self.status = AIUseStatusObservation.objects.create(
            ai_use=self.ai_use,
            observed_on=date(2026, 1, 15),
            usage_status="in_use",
            authority_ai_status="confirmed",
            comment="Status potwierdzony",
        )
        self.source = Source.objects.create(
            title="Źródło testowe",
            url="https://example.org/source",
            notes="Publiczna uwaga do źródła",
        )
        self.source.systems.add(self.system)
        self.source.deployments.add(self.deployment)
        self.source.ai_uses.add(self.ai_use)
        self.source.assessments.add(self.assessment)
        self.status.sources.add(self.source)

    def test_export_omits_internal_comments_and_round_trips(self):
        public_id = self.ai_use.public_id

        with TemporaryDirectory() as temp_dir:
            snapshot_path = Path(temp_dir) / "registry.json"
            call_command(
                "export_registry_data",
                output=snapshot_path,
                verbosity=0,
            )

            records = json.loads(snapshot_path.read_text(encoding="utf-8"))
            self.assertTrue(records)
            self.assertTrue(
                all(record["model"].startswith("home.") for record in records)
            )

            for model_name in (
                "home.aisystem",
                "home.deployment",
                "home.aiuse",
            ):
                record = next(
                    record for record in records if record["model"] == model_name
                )
                self.assertNotIn("comments", record["fields"])

            source_record = next(
                record for record in records if record["model"] == "home.source"
            )
            self.assertEqual(
                source_record["fields"]["notes"],
                "Publiczna uwaga do źródła",
            )

            TaggedArea.objects.all().delete()
            TaggedGeneric.objects.all().delete()
            AIUseStatusObservation.objects.all().delete()
            Source.objects.all().delete()
            Assessment.objects.all().delete()
            AIUse.objects.all().delete()
            Deployment.objects.all().delete()
            AISystem.objects.all().delete()
            Institution.objects.all().delete()
            AreaTag.objects.all().delete()
            GenericTag.objects.all().delete()

            call_command("loaddata", snapshot_path, verbosity=0)

        restored_use = AIUse.objects.get(public_id=public_id)
        self.assertEqual(restored_use.comments, "")
        self.assertEqual(restored_use.deployment.comments, "")
        self.assertEqual(restored_use.deployment.ai_system.comments, "")
        self.assertEqual(list(restored_use.areas.names()), ["Administracja"])
        self.assertEqual(list(restored_use.tags.names()), ["OCR"])

        restored_source = Source.objects.get(title="Źródło testowe")
        self.assertEqual(restored_source.notes, "Publiczna uwaga do źródła")
        self.assertTrue(restored_source.ai_uses.filter(pk=restored_use.pk).exists())
        self.assertTrue(
            restored_use.status_observations.get()
            .sources.filter(pk=restored_source.pk)
            .exists()
        )

    def test_export_refuses_unpublished_ai_uses(self):
        AIUse.objects.create(
            deployment=self.deployment,
            name="Szkic",
            published=False,
        )

        with TemporaryDirectory() as temp_dir:
            snapshot_path = Path(temp_dir) / "registry.json"
            with self.assertRaisesMessage(CommandError, "unpublished AI use"):
                call_command(
                    "export_registry_data",
                    output=snapshot_path,
                    verbosity=0,
                )

            self.assertFalse(snapshot_path.exists())

    @patch("home.management.commands.export_registry_data.call_command")
    def test_export_validates_the_serialized_snapshot(self, mock_dumpdata):
        def write_snapshot(*args, **kwargs):
            kwargs["stdout"].write(
                json.dumps(
                    [
                        {
                            "model": "home.aiuse",
                            "pk": 999,
                            "fields": {
                                "published": False,
                            },
                        }
                    ]
                )
            )

        mock_dumpdata.side_effect = write_snapshot

        with TemporaryDirectory() as temp_dir:
            snapshot_path = Path(temp_dir) / "registry.json"
            with self.assertRaisesMessage(CommandError, "serialized snapshot"):
                call_command(
                    "export_registry_data",
                    output=snapshot_path,
                    verbosity=0,
                )

            self.assertFalse(snapshot_path.exists())
