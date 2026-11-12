from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from taggit.admin import Tag

from .models.ai_use import (
    AISystem,
    AIUse,
    AIUseStatusObservation,
    Assessment,
    Deployment,
    Institution,
    Source,
)
from .models.tags import AreaTag, GenericTag

# remove the default taggit.Tag model from the admin
admin.site.unregister(Tag)


class AssessmentInline(admin.TabularInline):
    model = Assessment
    extra = 0
    fields = ("assessment_type", "status", "comment")


class AIUseStatusObservationInline(admin.TabularInline):
    model = AIUseStatusObservation
    extra = 0
    fields = (
        "observed_on",
        "usage_status",
        "authority_ai_status",
        "comment",
    )
    ordering = ("-observed_on",)


@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "updated_at")
    search_fields = ("name",)
    readonly_fields = ("slug",)


@admin.register(AISystem)
class AISystemAdmin(admin.ModelAdmin):
    list_display = ("name", "gpai_status", "updated_at")
    search_fields = ("name", "purpose", "description", "developer", "gpai_models")
    list_filter = ("gpai_status",)
    fieldsets = [
        (
            None,
            {
                "fields": [
                    "name",
                    "purpose",
                    "description",
                    "developer",
                ]
            },
        ),
        (
            _("MODELE OGÓLNEGO PRZEZNACZENIA (GPAI)"),
            {
                "fields": [
                    "gpai_status",
                    "gpai_models",
                ]
            },
        ),
        (
            _("WEWNĘTRZNE"),
            {
                "fields": [
                    "comments",
                ]
            },
        ),
    ]


@admin.register(Deployment)
class DeploymentAdmin(admin.ModelAdmin):
    list_display = ("institution", "ai_system", "gpai_status", "supplier", "updated_at")
    search_fields = (
        "institution__name",
        "ai_system__name",
        "supplier",
        "implementation_cost",
        "annual_maintenance_cost",
    )
    list_filter = (
        "gpai_status",
        "user_documentation_status",
        "public_information_status",
        "public_procurement_status",
    )
    autocomplete_fields = ("institution", "ai_system", "contracting_institution")
    fieldsets = [
        (
            None,
            {
                "fields": [
                    "institution",
                    "ai_system",
                    "supplier",
                ]
            },
        ),
        (
            _("MODELE OGÓLNEGO PRZEZNACZENIA (GPAI)"),
            {
                "fields": [
                    "gpai_status",
                    "gpai_models",
                ]
            },
        ),
        (
            _("KOSZTY"),
            {
                "fields": [
                    "implementation_cost",
                    "implementation_cost_comment",
                    "annual_maintenance_cost",
                    "annual_maintenance_cost_comment",
                ]
            },
        ),
        (
            _("LICENCJA"),
            {
                "fields": [
                    "license_start",
                    "license_end",
                    "license_comment",
                ]
            },
        ),
        (
            _("DOKUMENTACJA I PUBLICZNA WIEDZA"),
            {
                "fields": [
                    "user_documentation_status",
                    "user_documentation_comment",
                    "public_information_status",
                    "public_information_comment",
                ]
            },
        ),
        (
            _("ZAMÓWIENIE PUBLICZNE"),
            {
                "fields": [
                    "public_procurement_status",
                    "public_procurement_number",
                    "public_procurement_number_eu",
                    "public_procurement_date",
                    "contracting_institution",
                ]
            },
        ),
        (
            _("WEWNĘTRZNE"),
            {
                "fields": [
                    "comments",
                ]
            },
        ),
    ]


@admin.register(AIUse)
class AIUseAdmin(admin.ModelAdmin):
    inlines = [AssessmentInline, AIUseStatusObservationInline]
    list_display = (
        "name",
        "get_institution",
        "get_system",
        "risk_classification",
        "published",
        "updated_at",
    )
    list_filter = ("published", "risk_classification")
    search_fields = (
        "name",
        "purpose",
        "description",
        "ai_use_description",
        "process_name",
        "process_description",
        "decision_or_action",
        "ai_role",
        "human_role",
        "deployment__institution__name",
        "deployment__ai_system__name",
    )
    autocomplete_fields = ("deployment",)
    fieldsets = [
        (
            _("ZASTOSOWANIE AI"),
            {
                "fields": [
                    "deployment",
                    "name",
                    "purpose",
                    "description",
                    "ai_use_description",
                    "areas",
                    "tags",
                    "published",
                ]
            },
        ),
        (
            _("PROCES / PROCEDURA"),
            {
                "fields": [
                    "process_name",
                    "process_description",
                    "process_stage",
                    "decision_or_action",
                    "ai_role",
                    "human_role",
                ]
            },
        ),
        (
            _("KWALIFIKACJA RYZYKA"),
            {
                "fields": [
                    "risk_classification",
                    "risk_comment",
                ]
            },
        ),
        (
            _("OKRES STOSOWANIA"),
            {
                "fields": [
                    "use_start",
                    "use_end",
                ]
            },
        ),
        (
            _("WEWNĘTRZNE"),
            {
                "fields": [
                    "comments",
                ]
            },
        ),
    ]

    @admin.display(description=_("Instytucja"))
    def get_institution(self, obj):
        return obj.deployment.institution if obj.deployment else "—"

    @admin.display(description=_("System AI"))
    def get_system(self, obj):
        return obj.deployment.ai_system if obj.deployment else "—"


@admin.register(AIUseStatusObservation)
class AIUseStatusObservationAdmin(admin.ModelAdmin):
    list_display = (
        "ai_use",
        "observed_on",
        "usage_status",
        "authority_ai_status",
        "updated_at",
    )
    list_filter = ("usage_status", "authority_ai_status", "observed_on")
    search_fields = (
        "ai_use__name",
        "ai_use__deployment__institution__name",
        "ai_use__deployment__ai_system__name",
        "comment",
    )
    autocomplete_fields = ("ai_use",)
    filter_horizontal = ("sources",)
    date_hierarchy = "observed_on"


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ("ai_use", "assessment_type", "status", "updated_at")
    list_filter = ("assessment_type", "status")
    search_fields = (
        "ai_use__name",
        "ai_use__deployment__institution__name",
        "comment",
    )
    autocomplete_fields = ("ai_use",)


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ("title", "source_type", "document_type", "date", "updated_at")
    list_filter = ("source_type", "document_type")
    search_fields = ("title", "url", "notes")
    filter_horizontal = ("systems", "deployments", "ai_uses", "assessments")


@admin.register(GenericTag)
class GenericTagAdmin(admin.ModelAdmin):
    fieldsets = (
        (
            None,
            {
                "fields": ("name",),
                "description": (
                    "Tag opisuje bardziej szczegółowo funkcję lub sposób "
                    "wykorzystania sztucznej inteligencji, np. ocena ryzyka, "
                    "rozpoznawanie obiektów, rozpoznawanie tablic rejestracyjnych "
                    "lub identyfikacja biometryczna."
                ),
            },
        ),
    )


@admin.register(AreaTag)
class AreaTagAdmin(admin.ModelAdmin):
    fieldsets = (
        (
            None,
            {
                "fields": ("name",),
                "description": (
                    "Obszar określa szeroką dziedzinę lub kontekst, w którym "
                    "wykorzystywane jest zastosowanie AI, np. edukacja, rolnictwo, "
                    "kontrola graniczna, prewencja lub usługi ogólne."
                ),
            },
        ),
    )
