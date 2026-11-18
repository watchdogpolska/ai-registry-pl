import csv
import io
from datetime import date

from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from .models.ai_use import (
    AISystem,
    AIUse,
    AIUseStatusObservation,
    AnswerStatus,
    Assessment,
    Deployment,
    Institution,
)


class DeploymentGPAITests(SimpleTestCase):
    def test_effective_gpai_status(self):
        for system_status in AnswerStatus:
            for deployment_status in AnswerStatus:
                with self.subTest(system=system_status, deployment=deployment_status):
                    deployment = Deployment(
                        ai_system=AISystem(gpai_status=system_status),
                        gpai_status=deployment_status,
                    )
                    expected = (
                        system_status
                        if deployment_status == AnswerStatus.UNKNOWN
                        else deployment_status
                    )

                    self.assertEqual(deployment.effective_gpai_status, expected)
                    self.assertEqual(
                        deployment.get_effective_gpai_status_display(), expected.label
                    )

    def test_gpai_models_are_inherited_based_on_both_statuses(self):
        system_models = "Model systemu"
        for system_status in AnswerStatus:
            models_for_yes = system_models if system_status == AnswerStatus.YES else ""
            cases = (
                (AnswerStatus.UNKNOWN, system_models),
                (AnswerStatus.YES, models_for_yes),
                (AnswerStatus.NO, ""),
                (AnswerStatus.NOT_APPLICABLE, ""),
            )
            for deployment_status, expected in cases:
                with self.subTest(system=system_status, deployment=deployment_status):
                    deployment = Deployment(
                        ai_system=AISystem(
                            gpai_status=system_status, gpai_models=system_models
                        ),
                        gpai_status=deployment_status,
                    )

                    self.assertEqual(deployment.effective_gpai_models, expected)

    def test_gpai_models_entered_for_deployment_take_precedence(self):
        system = AISystem(gpai_status=AnswerStatus.YES, gpai_models="Model systemu")
        for status in AnswerStatus:
            with self.subTest(status=status):
                deployment = Deployment(
                    ai_system=system,
                    gpai_status=status,
                    gpai_models="Informacja o wdrożeniu",
                )

                self.assertEqual(
                    deployment.effective_gpai_models, "Informacja o wdrożeniu"
                )


class PublicViewsSmokeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        institution = Institution.objects.create(name="Testowa instytucja")
        system = AISystem.objects.create(name="Testowy system")
        deployment = Deployment.objects.create(
            institution=institution,
            ai_system=system,
        )
        cls.ai_use = AIUse.objects.create(
            deployment=deployment,
            name="Testowe zastosowanie",
            published=True,
        )
        cls.ai_use.areas.add("Administracja")
        cls.ai_use.tags.add("OCR")

        AIUseStatusObservation.objects.create(
            ai_use=cls.ai_use,
            observed_on=date(2025, 1, 1),
            usage_status="planned",
            authority_ai_status="unclear",
            comment="Stary status",
        )
        AIUseStatusObservation.objects.create(
            ai_use=cls.ai_use,
            observed_on=date(2026, 1, 15),
            usage_status="in_use",
            authority_ai_status="confirmed",
            comment="Aktualny status",
        )

        Assessment.objects.create(
            ai_use=cls.ai_use,
            assessment_type="dpia",
            status="yes",
            comment="DPIA wykonana",
        )
        Assessment.objects.create(
            ai_use=cls.ai_use,
            assessment_type="fria",
            status="no",
            comment="FRIA niewykonana",
        )

        AIUse.objects.create(
            deployment=deployment,
            name="Niepublikowane zastosowanie",
            published=False,
        )

    def test_home_page(self):
        response = self.client.get(reverse("home_view"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Testowe zastosowanie")

    def test_detail_page(self):
        response = self.client.get(
            reverse("ai_use_detail", args=[self.ai_use.public_id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Testowe zastosowanie")

    def test_detail_filter_links_return_to_registry(self):
        response = self.client.get(
            reverse("ai_use_detail", args=[self.ai_use.public_id])
        )

        self.assertContains(
            response,
            'href="/?institution=testowa-instytucja&amp;page=1#entries"',
        )
        self.assertContains(
            response,
            'href="/?area=administracja&amp;page=1#entries"',
        )
        self.assertContains(
            response,
            'href="/?tag=ocr&amp;page=1#entries"',
        )

    def test_robots_txt(self):
        response = self.client.get(reverse("robots_txt"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/plain")

    def test_csv_export_is_public_current_registry_snapshot(self):
        response = self.client.get(
            reverse("csv_export"),
            {
                "institution": "nieistniejaca",
                "search": "brak",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response["Content-Type"].startswith("text/csv"))
        self.assertEqual(
            response["Content-Disposition"],
            'attachment; filename="rejestr-zastosowan-ai.csv"',
        )

        text = response.content.decode("utf-8-sig")
        rows = list(csv.reader(io.StringIO(text)))

        self.assertEqual(len(rows), 2)
        headers = rows[0]
        data = dict(zip(headers, rows[1]))

        self.assertEqual(data["Nazwa zastosowania AI"], "Testowe zastosowanie")
        self.assertEqual(data["Instytucja"], "Testowa instytucja")
        self.assertEqual(data["Nazwa systemu AI"], "Testowy system")
        self.assertEqual(
            data["Link do rekordu"],
            f"http://testserver/zastosowania/{self.ai_use.public_id}/",
        )

        self.assertEqual(data["Status użycia"], "W użyciu")
        self.assertEqual(data["Stan na dzień"], "2026-01-15")
        self.assertEqual(
            data["Stanowisko instytucji: czy to AI?"],
            "Instytucja uznaje za AI",
        )
        self.assertEqual(data["Komentarz do statusu"], "Aktualny status")
        self.assertNotIn("Stary status", rows[1])

        self.assertEqual(data["Obszary"], "Administracja")
        self.assertEqual(data["Tagi"], "OCR")
        self.assertEqual(data["DPIA – status"], "Tak")
        self.assertEqual(data["DPIA – komentarz"], "DPIA wykonana")
        self.assertEqual(data["FRIA – status"], "Nie")
        self.assertEqual(data["FRIA – komentarz"], "FRIA niewykonana")

        self.assertNotIn("Zaktualizowano", headers)
        self.assertNotIn("Źródła statusu", headers)
        self.assertNotIn("Numer ogłoszenia BZP", headers)
        self.assertNotIn("Niepublikowane zastosowanie", rows[1])

    def test_gpai_information_matches_in_public_views_and_csv(self):
        deployment = self.ai_use.deployment
        system = deployment.ai_system
        system.gpai_status = AnswerStatus.YES
        system.gpai_models = "Testowy model systemu"
        system.save(update_fields=["gpai_status", "gpai_models"])

        cases = (
            (AnswerStatus.UNKNOWN, "", "Tak", "Testowy model systemu"),
            (AnswerStatus.NO, "", "Nie", ""),
            (AnswerStatus.NOT_APPLICABLE, "Wyjaśnienie", "Nie dotyczy", "Wyjaśnienie"),
        )
        for status, models, expected_status, expected_models in cases:
            with self.subTest(status=status):
                deployment.gpai_status = status
                deployment.gpai_models = models
                deployment.save(update_fields=["gpai_status", "gpai_models"])

                tooltip = ""
                if expected_models:
                    tooltip = f"""
                        <div class="pill has-tooltip" tabindex="0">
                            <span>?</span>
                            <div class="pill-tooltip-container" style="display: none">
                                <div class="pill-tooltip">{expected_models}</div>
                            </div>
                        </div>
                    """
                gpai_row = f"""
                    <tr>
                        <td>GPAI:</td>
                        <td><div class="pill">{expected_status}</div>{tooltip}</td>
                    </tr>
                """
                for url in (
                    reverse("home_view"),
                    reverse("ai_use_detail", args=[self.ai_use.public_id]),
                ):
                    self.assertContains(self.client.get(url), gpai_row, html=True)

                response = self.client.get(reverse("csv_export"))
                self.assertEqual(response.status_code, 200)
                rows = csv.DictReader(io.StringIO(response.content.decode("utf-8-sig")))
                self.assertEqual(
                    [(row["GPAI"], row["Modele GPAI"]) for row in rows],
                    [(expected_status, expected_models)],
                )


class AppVersionFooterTests(TestCase):
    @override_settings(
        APP_VERSION="v1.2.3",
        APP_COMMIT="abc1234",
        SOURCE_CODE_URL="https://example.org/repo",
    )
    def test_footer_shows_version_linked_to_commit(self):
        response = self.client.get(reverse("home_view"))
        self.assertContains(response, "wersja v1.2.3")
        self.assertContains(response, 'href="https://example.org/repo/tree/abc1234"')

    @override_settings(
        APP_VERSION="dev",
        APP_COMMIT="",
        SOURCE_CODE_URL="https://example.org/repo",
    )
    def test_footer_links_repository_without_commit(self):
        response = self.client.get(reverse("home_view"))
        self.assertContains(response, "wersja dev")
        self.assertContains(response, 'href="https://example.org/repo"')
