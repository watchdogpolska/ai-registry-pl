import csv

from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import F, Prefetch, Q
from django.http import HttpResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import cache_page
from django.views.generic import DetailView, TemplateView, View

from .models.ai_use import (
    AIUse,
    AIUseStatusObservation,
    Assessment,
    Institution,
)
from .models.tags import AreaTag, GenericTag

SORT_OPTIONS = [
    ("use_start", _("daty rozpoczęcia stosowania")),
    ("updated_at", _("daty ostatniej aktualizacji")),
]
SORT_KEYS = [key for key, _ in SORT_OPTIONS]
SORT_DEFAULT = "updated_at"


def get_public_ai_uses():
    return (
        AIUse.objects.filter(
            published=True,
            deployment__isnull=False,
        )
        .select_related(
            "deployment",
            "deployment__institution",
            "deployment__ai_system",
            "deployment__contracting_institution",
        )
        .prefetch_related(
            "areas",
            "tags",
            Prefetch(
                "assessments",
                queryset=Assessment.objects.filter(assessment_type="dpia"),
                to_attr="dpia_assessments",
            ),
            Prefetch(
                "assessments",
                queryset=Assessment.objects.filter(assessment_type="fria"),
                to_attr="fria_assessments",
            ),
            "sources",
            "deployment__sources",
            "deployment__ai_system__sources",
            "assessments__sources",
            Prefetch(
                "status_observations",
                queryset=AIUseStatusObservation.objects.order_by(
                    "-observed_on",
                    "-created_at",
                ),
            ),
        )
    )


def _get_tags_many(request, Model, key, entries, filter_key="aiuse__in"):
    objects = list(
        Model.objects.filter(**{filter_key: entries})
        .distinct()
        .values_list("slug", "name")
    )
    object_dict = {slug: name for slug, name in objects}

    selected_tuples = []
    query_param = request.GET.get(key, "")
    if query_params := query_param.split(","):
        for param in query_params:
            try:
                selected_tuples.append((param, object_dict[param]))
            except KeyError:
                pass

    return objects, selected_tuples


@method_decorator(
    cache_page(settings.HOME_PAGE_CACHE_SECONDS),
    name="dispatch",
)
class HomeView(TemplateView):
    template_name = "home/home_view.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        entries = get_public_ai_uses()
        all_entries_count = entries.count()

        areas, selected_areas = _get_tags_many(self.request, AreaTag, "area", entries)
        tags, selected_tags = _get_tags_many(self.request, GenericTag, "tag", entries)
        institutions, selected_institutions = _get_tags_many(
            self.request,
            Institution,
            "institution",
            entries,
            filter_key="deployments__ai_uses__in",
        )

        if selected_areas:
            selected_area_slugs = [slug for slug, _ in selected_areas]
            entries = entries.filter(areas__slug__in=selected_area_slugs)
        if selected_tags:
            selected_tag_slugs = [slug for slug, _ in selected_tags]
            entries = entries.filter(tags__slug__in=selected_tag_slugs)
        if selected_institutions:
            selected_institution_slugs = [slug for slug, _ in selected_institutions]
            entries = entries.filter(
                deployment__institution__slug__in=selected_institution_slugs
            )

        sort_query = self.request.GET.get("sort", SORT_DEFAULT)
        if sort_query not in SORT_KEYS:
            sort_query = SORT_DEFAULT

        entries = entries.order_by(
            F(sort_query).desc(nulls_last=True),
            "id",
        )

        search = self.request.GET.get("search", "")
        if search:
            entries = entries.filter(
                Q(name__icontains=search)
                | Q(purpose__icontains=search)
                | Q(description__icontains=search)
                | Q(ai_use_description__icontains=search)
                | Q(process_name__icontains=search)
                | Q(process_description__icontains=search)
                | Q(process_stage__icontains=search)
                | Q(decision_or_action__icontains=search)
                | Q(ai_role__icontains=search)
                | Q(human_role__icontains=search)
                | Q(deployment__institution__name__icontains=search)
                | Q(deployment__ai_system__name__icontains=search)
                | Q(deployment__ai_system__purpose__icontains=search)
                | Q(deployment__ai_system__description__icontains=search)
                | Q(deployment__ai_system__developer__icontains=search)
                | Q(deployment__supplier__icontains=search)
            )

        entries = entries.distinct()

        page_query = self.request.GET.get("page", "1")
        paginator = Paginator(entries, 10)
        page_obj = paginator.get_page(page_query)
        paginator.elided_page_range = paginator.get_elided_page_range(
            number=page_obj.number,
            on_each_side=3,
            on_ends=0,
        )

        context["all_entries_count"] = all_entries_count
        context["entries"] = page_obj
        context["sort_query"] = sort_query
        context["sort_options"] = SORT_OPTIONS
        context["filters"] = {
            "areas": areas,
            "tags": tags,
            "institutions": institutions,
            "selected_areas": selected_areas,
            "selected_tags": selected_tags,
            "selected_institutions": selected_institutions,
        }
        context["search"] = search

        return context


class AIUseDetailView(DetailView):
    template_name = "home/ai_use_detail.html"
    context_object_name = "entry"
    slug_field = "public_id"
    slug_url_kwarg = "public_id"

    def get_queryset(self):
        return get_public_ai_uses()


class CSVExportView(View):
    HEADERS = [
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
        "GPAI",
        "Modele GPAI",
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
    ]

    @staticmethod
    def _format_sources(sources):
        values = []
        for source in sources:
            value = source.title
            if source.url:
                value += f": {source.url}"
            values.append(value)
        return "; ".join(values)

    def get(self, request, *args, **kwargs):
        entries = get_public_ai_uses().order_by(
            "deployment__institution__name",
            "name",
        )

        response = HttpResponse(
            content_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": (
                    'attachment; filename="rejestr-zastosowan-ai.csv"'
                )
            },
        )
        response.write("\ufeff")

        writer = csv.writer(response)
        writer.writerow(self.HEADERS)

        for entry in entries:
            deployment = entry.deployment
            ai_system = deployment.ai_system
            latest_status = entry.status_observations.all().first()
            dpia = entry.dpia_assessments[0] if entry.dpia_assessments else None
            fria = entry.fria_assessments[0] if entry.fria_assessments else None
            record_url = request.build_absolute_uri(
                reverse("ai_use_detail", args=[entry.public_id])
            )

            writer.writerow(
                [
                    entry.name,
                    deployment.institution.name,
                    ai_system.name,
                    record_url,
                    entry.purpose,
                    entry.use_start.isoformat() if entry.use_start else "",
                    entry.use_end.isoformat() if entry.use_end else "",
                    (
                        latest_status.get_usage_status_display()
                        if latest_status
                        else "Brak informacji"
                    ),
                    latest_status.observed_on.isoformat() if latest_status else "",
                    (
                        latest_status.get_authority_ai_status_display()
                        if latest_status
                        else "Brak informacji"
                    ),
                    latest_status.comment if latest_status else "",
                    entry.get_risk_classification_display(),
                    entry.risk_comment,
                    deployment.get_gpai_status_display(),
                    deployment.gpai_models,
                    ai_system.developer,
                    deployment.supplier,
                    "; ".join(str(area) for area in entry.areas.all()),
                    "; ".join(str(tag) for tag in entry.tags.all()),
                    entry.description,
                    entry.ai_use_description,
                    entry.process_name,
                    entry.process_description,
                    entry.process_stage,
                    entry.decision_or_action,
                    entry.ai_role,
                    entry.human_role,
                    ai_system.purpose,
                    ai_system.description,
                    dpia.get_status_display() if dpia else "Brak informacji",
                    dpia.comment if dpia else "",
                    fria.get_status_display() if fria else "Brak informacji",
                    fria.comment if fria else "",
                    deployment.implementation_cost,
                    deployment.implementation_cost_comment,
                    deployment.annual_maintenance_cost,
                    deployment.annual_maintenance_cost_comment,
                    (
                        deployment.license_start.isoformat()
                        if deployment.license_start
                        else ""
                    ),
                    (
                        deployment.license_end.isoformat()
                        if deployment.license_end
                        else ""
                    ),
                    deployment.license_comment,
                    deployment.get_user_documentation_status_display(),
                    deployment.user_documentation_comment,
                    deployment.get_public_information_status_display(),
                    deployment.public_information_comment,
                    deployment.get_public_procurement_status_display(),
                    self._format_sources(entry.sources.all()),
                    self._format_sources(deployment.sources.all()),
                    self._format_sources(ai_system.sources.all()),
                ]
            )

        return response


ROBOTS_TXT_CONTENT = """

# Default rules: allow crawling except for the admin panel
User-agent: *
Allow: /
Disallow: /admin/
Crawl-delay: 10

# Meta AI crawlers
User-agent: meta-externalagent
User-agent: meta-webindexer
Disallow: /

# Baidu crawler
User-agent: Baiduspider
Disallow: /

# Applebot-Extended
User-agent: Applebot-Extended
Disallow: /

""".strip()


class RobotsTxtView(View):
    def get(self, request, *args, **kwargs):
        return HttpResponse(ROBOTS_TXT_CONTENT, content_type="text/plain")
