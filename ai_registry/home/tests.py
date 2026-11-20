import io
from datetime import UTC, date, datetime
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from openpyxl import load_workbook

from .models.ai_use import (
    AISystem,
    AIUse,
    AIUseStatusObservation,
    AnswerStatus,
    Assessment,
    Deployment,
    Institution,
    Source,
)


class PublicViewsSmokeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        institution = Institution.objects.create(name="Testowa instytucja")
        system = AISystem.objects.create(
            name="Testowy system",
            gpai_status=AnswerStatus.YES,
            gpai_models="Opis systemu GPAI",
            comments="Wewnętrzne uwagi o systemie",
        )
        deployment = Deployment.objects.create(
            institution=institution,
            ai_system=system,
            gpai_models="Opis wdrożenia GPAI",
            implementation_cost="Około 15 000 zł brutto",
            annual_maintenance_cost="1200",
            license_start=date(2025, 2, 1),
            license_end=date(2026, 2, 1),
            comments="Wewnętrzne uwagi o wdrożeniu",
        )
        cls.ai_use = AIUse.objects.create(
            deployment=deployment,
            name="Testowe zastosowanie",
            use_start=date(2025, 1, 1),
            use_end=date(2026, 1, 31),
            comments="Wewnętrzne uwagi o zastosowaniu",
            published=True,
        )
        cls.ai_use.areas.add("Administracja")
        cls.ai_use.tags.add("OCR")

        AIUseStatusObservation.objects.create(
            ai_use=cls.ai_use,
            observed_on=date(2026, 1, 15),
            usage_status="in_use",
            authority_ai_status="confirmed",
            comment="Aktualny status",
        )
        AIUseStatusObservation.objects.create(
            ai_use=cls.ai_use,
            observed_on=date(2025, 1, 1),
            usage_status="planned",
            authority_ai_status="unclear",
            comment="Stary status",
        )

        cls.ai_use.sources.add(
            Source.objects.create(
                title="Źródło A", url="https://example.org/zastosowanie-a"
            ),
            Source.objects.create(
                title="Źródło B", url="https://example.org/zastosowanie-b"
            ),
        )
        deployment.sources.add(Source.objects.create(title="Źródło bez adresu"))
        system.sources.add(
            Source.objects.create(
                title="Opis systemu", url="https://example.org/system"
            )
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

    def assert_xlsx_response(self, response):
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        workbook = load_workbook(io.BytesIO(response.content))
        self.addCleanup(workbook.close)
        self.assertEqual(workbook.sheetnames, ["Zastosowania AI"])
        return workbook.active

    @patch(
        "home.views.timezone.now",
        return_value=datetime(2026, 11, 20, 23, 25, 9, tzinfo=UTC),
    )
    def test_xlsx_export_is_public_current_registry_snapshot(self, _now):
        self.assertEqual(reverse("xlsx_export"), "/export/data.xlsx")
        response = self.client.get(reverse("xlsx_export"))
        sheet = self.assert_xlsx_response(response)
        self.assertEqual(
            response["Content-Disposition"],
            'attachment; filename="rejestr-zastosowan-ai-20261121_002509.xlsx"',
        )
        rows = list(sheet.values)

        self.assertEqual(len(rows), 2)
        headers = rows[0]
        self.assertEqual(
            headers,
            (
                "Nazwa zastosowania AI",
                "Instytucja",
                "Nazwa systemu AI",
                "Link do rekordu",
                "Przeznaczenie zastosowania",
                "Początek stosowania",
                "Koniec stosowania",
                "Status użycia",
                "Stan na dzień",
                "Stanowisko instytucji: czy to AI?",
                "Komentarz do statusu",
                "Ryzyko AI Act",
                "Komentarz do ryzyka",
                "GPAI – system AI",
                "GPAI – szczegóły systemu",
                "GPAI – wdrożenie",
                "GPAI – szczegóły wdrożenia",
                "Twórca / producent",
                "Dostawca",
                "Obszary",
                "Tagi",
                "Opis zastosowania",
                "Użycie sztucznej inteligencji",
                "Proces / procedura",
                "Opis procesu / procedury",
                "Etap procesu / procedury",
                "Decyzja lub działanie",
                "Rola AI",
                "Rola człowieka",
                "Przeznaczenie systemu",
                "Opis systemu",
                "DPIA – status",
                "DPIA – komentarz",
                "FRIA – status",
                "FRIA – komentarz",
                "Koszt wytworzenia i wdrożenia",
                "Komentarz do kosztu wytworzenia i wdrożenia",
                "Roczny koszt utrzymania",
                "Komentarz do kosztu utrzymania",
                "Początek licencji",
                "Koniec licencji",
                "Komentarz do licencji",
                "Instrukcja / podręcznik",
                "Komentarz do instrukcji / podręcznika",
                "Publiczna wiedza",
                "Komentarz do publicznej wiedzy",
                "Zamówienie publiczne",
                "Źródła zastosowania",
                "Źródła wdrożenia",
                "Źródła systemu",
            ),
        )
        data = dict(zip(headers, rows[1]))
        cells = dict(zip(headers, sheet[2]))

        self.assertEqual(data["Nazwa zastosowania AI"], "Testowe zastosowanie")
        self.assertEqual(data["Instytucja"], "Testowa instytucja")
        self.assertEqual(data["Nazwa systemu AI"], "Testowy system")
        self.assertEqual(
            data["Link do rekordu"],
            f"http://testserver/zastosowania/{self.ai_use.public_id}/",
        )
        self.assertEqual(
            cells["Link do rekordu"].hyperlink.target, data["Link do rekordu"]
        )

        self.assertEqual(data["Status użycia"], "W użyciu")
        for label, value in (
            ("Stan na dzień", datetime(2026, 1, 15)),
            ("Początek stosowania", datetime(2025, 1, 1)),
            ("Koniec stosowania", datetime(2026, 1, 31)),
            ("Początek licencji", datetime(2025, 2, 1)),
            ("Koniec licencji", datetime(2026, 2, 1)),
        ):
            with self.subTest(label=label):
                self.assertEqual(data[label], value)
                self.assertEqual(cells[label].data_type, "d")
                self.assertEqual(cells[label].number_format, "dd.mm.yyyy")
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
        self.assertEqual(data["GPAI – system AI"], "Tak")
        self.assertEqual(data["GPAI – szczegóły systemu"], "Opis systemu GPAI")
        self.assertEqual(data["GPAI – wdrożenie"], "Brak informacji")
        self.assertEqual(data["GPAI – szczegóły wdrożenia"], "Opis wdrożenia GPAI")
        self.assertEqual(
            data["Koszt wytworzenia i wdrożenia"], "Około 15 000 zł brutto"
        )
        self.assertEqual(data["Roczny koszt utrzymania"], "1200")
        self.assertEqual(
            data["Źródła systemu"], "Opis systemu: https://example.org/system"
        )
        self.assertEqual(
            cells["Źródła systemu"].hyperlink.target, "https://example.org/system"
        )
        self.assertEqual(data["Źródła wdrożenia"], "Źródło bez adresu")
        self.assertEqual(
            data["Źródła zastosowania"],
            "Źródło A: https://example.org/zastosowanie-a; "
            "Źródło B: https://example.org/zastosowanie-b",
        )
        self.assertEqual(
            cells["Źródła zastosowania"].hyperlink.target,
            "https://example.org/zastosowanie-a",
        )

        self.assertNotIn("Zaktualizowano", headers)
        self.assertNotIn("Źródła statusu", headers)
        self.assertNotIn("Numer ogłoszenia BZP", headers)
        self.assertNotIn("Niepublikowane zastosowanie", rows[1])
        self.assertNotIn("Uwagi wewnętrzne", headers)
        self.assertNotIn("Wewnętrzne uwagi o zastosowaniu", rows[1])
        self.assertNotIn("Wewnętrzne uwagi o wdrożeniu", rows[1])
        self.assertNotIn("Wewnętrzne uwagi o systemie", rows[1])

    def test_xlsx_export_ignores_filters_search_and_pagination_and_keeps_sort_order(
        self,
    ):
        first_institution = Institution.objects.create(name="A Instytucja")
        system = AISystem.objects.create(
            name="Inny system", gpai_status=AnswerStatus.NOT_APPLICABLE
        )
        deployment = Deployment.objects.create(
            institution=first_institution,
            ai_system=system,
            gpai_status=AnswerStatus.NO,
        )
        AIUse.objects.create(deployment=self.ai_use.deployment, name="A zastosowanie")
        AIUse.objects.create(deployment=deployment, name="Z zastosowanie")
        AIUse.objects.create(deployment=deployment, name="Ukryte", published=False)
        AIUse.objects.create(name="Bez wdrożenia", published=True)
        response = self.client.get(
            reverse("xlsx_export"),
            {
                "institution": self.ai_use.deployment.institution.slug,
                "search": self.ai_use.name,
                "area": "administracja",
                "tag": "ocr",
                "sort": "use_start",
                "page": "99",
            },
        )
        headers, *rows = self.assert_xlsx_response(response).values
        self.assertEqual(
            [row[0] for row in rows],
            ["Z zastosowanie", "A zastosowanie", "Testowe zastosowanie"],
        )
        first_row = dict(zip(headers, rows[0]))
        self.assertEqual(first_row["GPAI – system AI"], "Nie dotyczy")
        self.assertEqual(first_row["GPAI – wdrożenie"], "Nie")
        for label in (
            "Stan na dzień",
            "Początek stosowania",
            "Koniec stosowania",
            "Początek licencji",
            "Koniec licencji",
        ):
            with self.subTest(label=label):
                self.assertIsNone(first_row[label])

    def test_xlsx_export_formats_cells_and_keeps_text_literal(self):
        long_description = "Opis zastosowania " * 100 + "\nDrugi akapit."
        AIUse.objects.filter(pk=self.ai_use.pk).update(
            purpose="=1+2",
            risk_comment="#N/A",
            description=long_description,
        )
        sheet = self.assert_xlsx_response(self.client.get(reverse("xlsx_export")))
        cells = dict(zip((cell.value for cell in sheet[1]), sheet[2]))
        for label, value in (
            ("Przeznaczenie zastosowania", "=1+2"),
            ("Komentarz do ryzyka", "#N/A"),
            ("Opis zastosowania", long_description),
            ("Roczny koszt utrzymania", "1200"),
        ):
            with self.subTest(label=label):
                self.assertEqual(cells[label].value, value)
                self.assertEqual(cells[label].data_type, "s")

        self.assertEqual(sheet.freeze_panes, "A2")
        self.assertEqual(sheet.auto_filter.ref, sheet.dimensions)
        self.assertGreater(sheet.row_dimensions[1].height, 25)
        self.assertTrue(sheet["A1"].font.bold)
        self.assertEqual(sheet["A1"].fill.patternType, "solid")
        self.assertTrue(sheet["A1"].alignment.wrap_text)
        self.assertTrue(cells["Opis zastosowania"].alignment.wrap_text)
        self.assertEqual(cells["Opis zastosowania"].alignment.vertical, "top")
        self.assertEqual(
            sheet.column_dimensions[cells["Opis zastosowania"].column_letter].width, 60
        )
        self.assertGreater(
            sheet.column_dimensions["A"].width, sheet.column_dimensions["B"].width
        )

    def test_xlsx_export_of_empty_registry_has_headers(self):
        AIUse.objects.update(published=False)
        sheet = self.assert_xlsx_response(self.client.get(reverse("xlsx_export")))
        self.assertEqual(sheet.max_row, 1)
        self.assertEqual(sheet["A1"].value, "Nazwa zastosowania AI")
        self.assertEqual(sheet.auto_filter.ref, sheet.dimensions)

    def test_footer_explains_that_xlsx_export_contains_whole_registry(self):
        response = self.client.get(reverse("home_view"), {"search": "brak"})
        self.assertContains(
            response,
            '<a href="/export/data.xlsx">Pobierz cały rejestr (XLSX)</a>',
            html=True,
        )
        self.assertContains(
            response,
            "Plik zawiera wszystkie opublikowane zastosowania, niezależnie od "
            "wybranych filtrów i wyszukiwania.",
        )


class DeploymentGPAIStatusTests(SimpleTestCase):
    def test_effective_status_for_each_system_and_deployment_status(self):
        statuses = (
            AnswerStatus.YES,
            AnswerStatus.NO,
            AnswerStatus.UNKNOWN,
            AnswerStatus.NOT_APPLICABLE,
        )
        labels = {
            AnswerStatus.YES: "Tak",
            AnswerStatus.NO: "Nie",
            AnswerStatus.UNKNOWN: "Brak informacji",
            AnswerStatus.NOT_APPLICABLE: "Nie dotyczy",
        }
        cases = (
            (
                (AnswerStatus.YES, False),
                (AnswerStatus.NO, True),
                (AnswerStatus.YES, False),
                (AnswerStatus.NOT_APPLICABLE, True),
            ),
            (
                (AnswerStatus.YES, True),
                (AnswerStatus.NO, False),
                (AnswerStatus.NO, False),
                (AnswerStatus.NOT_APPLICABLE, True),
            ),
            (
                (AnswerStatus.YES, False),
                (AnswerStatus.NO, False),
                (AnswerStatus.UNKNOWN, False),
                (AnswerStatus.NOT_APPLICABLE, False),
            ),
            (
                (AnswerStatus.YES, True),
                (AnswerStatus.NO, True),
                (AnswerStatus.NOT_APPLICABLE, False),
                (AnswerStatus.NOT_APPLICABLE, False),
            ),
        )
        for system_status, deployment_cases in zip(statuses, cases):
            system = AISystem(gpai_status=system_status)
            for deployment_status, (status, differs) in zip(statuses, deployment_cases):
                with self.subTest(system=system_status, deployment=deployment_status):
                    deployment = Deployment(
                        ai_system=system, gpai_status=deployment_status
                    )
                    self.assertEqual(deployment.effective_gpai_status, status)
                    self.assertEqual(
                        deployment.get_effective_gpai_status_display(), labels[status]
                    )
                    self.assertEqual(
                        deployment.gpai_status_differs_from_system, differs
                    )
                    self.assertEqual(deployment.gpai_status, deployment_status)
                    self.assertEqual(system.gpai_status, system_status)


@override_settings(HOME_PAGE_CACHE_SECONDS=0)
class PublicGPAITooltipTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.system = AISystem.objects.create(name="Testowy system")
        cls.deployment = Deployment.objects.create(
            ai_system=cls.system,
            institution=Institution.objects.create(name="Testowa instytucja"),
        )
        cls.ai_use = AIUse.objects.create(
            name="Testowe zastosowanie",
            deployment=cls.deployment,
        )

    def test_gpai_status_and_tooltip_on_both_public_pages(self):
        cases = (
            ("yes", "unknown", "Opis systemu", "", "Tak"),
            ("yes", "unknown", "", "Opis wdrożenia", "Tak"),
            ("yes", "unknown", "Opis systemu", "Opis wdrożenia", "Tak"),
            ("yes", "yes", "", "", "Tak"),
            ("unknown", "unknown", "Opis systemu", "", "Brak informacji"),
            ("unknown", "not_applicable", "", "Opis wdrożenia", "Nie dotyczy"),
            ("yes", "no", "Opis systemu", "Opis wdrożenia", "Nie (w tym wdrożeniu)"),
            ("no", "yes", "Wspólny opis", "Wspólny opis", "Tak (w tym wdrożeniu)"),
            ("no", "not_applicable", "", "", "Nie dotyczy (w tym wdrożeniu)"),
        )
        tooltip_id = f"gpai-tooltip-{self.ai_use.public_id}"
        urls = (
            reverse("home_view"),
            reverse("ai_use_detail", args=[self.ai_use.public_id]),
        )
        for (
            system_status,
            deployment_status,
            system_text,
            deployment_text,
            label,
        ) in cases:
            AISystem.objects.filter(pk=self.system.pk).update(
                gpai_status=system_status, gpai_models=system_text
            )
            Deployment.objects.filter(pk=self.deployment.pk).update(
                gpai_status=deployment_status, gpai_models=deployment_text
            )
            for url in urls:
                with self.subTest(
                    url=url,
                    system=system_status,
                    deployment=deployment_status,
                    system_text=system_text,
                    deployment_text=deployment_text,
                ):
                    response = self.client.get(url)
                    self.assertContains(
                        response, f'<div class="pill">{label}</div>', html=True
                    )
                    if system_text or deployment_text:
                        self.assertContains(
                            response,
                            f'tabindex="0" aria-describedby="{tooltip_id}"',
                            count=1,
                        )
                        self.assertContains(
                            response, f'id="{tooltip_id}" role="tooltip"', count=1
                        )
                    else:
                        self.assertNotContains(response, tooltip_id)
                    for heading, description in (
                        ("System AI", system_text),
                        ("Wdrożenie", deployment_text),
                    ):
                        if description:
                            self.assertContains(
                                response,
                                '<div class="gpai-tooltip-section">'
                                f"<strong>{heading}</strong><div>{description}</div>"
                                "</div>",
                                count=1,
                                html=True,
                            )
                        else:
                            self.assertNotContains(
                                response, f"<strong>{heading}</strong>"
                            )

    def test_admin_explains_gpai_inheritance_and_combined_descriptions(self):
        self.client.force_login(
            get_user_model().objects.create_superuser(username="redaktor")
        )
        response = self.client.get(
            reverse("admin:home_deployment_change", args=[self.deployment.pk])
        )
        for instruction in (
            "Jeśli wybierzesz „Brak informacji”, w rejestrze wyświetli się "
            "status zapisany przy systemie AI.",
            "Konkretna odpowiedź dla wdrożenia ma pierwszeństwo.",
            "Jeśli system i wdrożenie mają dodatkowe opisy GPAI, oba pojawią się razem.",
        ):
            self.assertContains(response, instruction)


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
