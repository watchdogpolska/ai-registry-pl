import uuid
from unittest.mock import patch

from django.db import connection
from django.test import TestCase
from django.urls import reverse

from .models.ai_use import AISystem, AIUse, Deployment, Institution


class Char32UUIDFieldTests(TestCase):
    def test_public_id_stays_char32_with_native_uuid_detection(self):
        institution = Institution.objects.create(name="Test institution")
        ai_system = AISystem.objects.create(name="Test AI system")
        deployment = Deployment.objects.create(
            institution=institution,
            ai_system=ai_system,
        )
        ai_use = AIUse.objects.create(
            name="Test public use",
            deployment=deployment,
            published=True,
        )
        field = AIUse._meta.get_field("public_id")

        with patch.object(connection.features, "has_native_uuid_field", True):
            self.assertEqual(field.db_type(connection), "char(32)")
            self.assertEqual(
                field.get_db_prep_value(ai_use.public_id, connection),
                ai_use.public_id.hex,
            )
            self.assertEqual(
                field.get_db_prep_value(str(ai_use.public_id), connection),
                ai_use.public_id.hex,
            )
            self.assertIsNone(field.get_db_prep_value(None, connection))
            self.assertTrue(AIUse.objects.filter(public_id=ai_use.public_id).exists())
            detail_url = reverse("ai_use_detail", args=[ai_use.public_id])
            self.assertEqual(self.client.get(detail_url).status_code, 200)

    def test_public_id_works_without_native_uuid(self):
        field = AIUse._meta.get_field("public_id")
        value = uuid.uuid4()

        with patch.object(connection.features, "has_native_uuid_field", False):
            self.assertEqual(field.db_type(connection), "char(32)")
            self.assertEqual(field.get_db_prep_value(value, connection), value.hex)
