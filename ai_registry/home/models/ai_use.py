import uuid

from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from taggit.managers import TaggableManager

from .base import Timestamped


class AnswerStatus(models.TextChoices):
    YES = "yes", _("Tak")
    NO = "no", _("Nie")
    UNKNOWN = "unknown", _("Brak informacji")
    NOT_APPLICABLE = "not_applicable", _("Nie dotyczy")


class RiskClassification(models.TextChoices):
    UNKNOWN = "unknown", _("Brak informacji")
    NOT_ASSESSED = "not_assessed", _("Nie przeprowadzono kwalifikacji")
    MINIMAL = "minimal", _("Minimalne")
    LIMITED = "limited", _("Ograniczone")
    HIGH = "high", _("Wysokie")
    UNACCEPTABLE = "unacceptable", _("Niedopuszczalne")
    OTHER = "other", _("Inne / niejednoznaczne")


class AssessmentType(models.TextChoices):
    DPIA = "dpia", _("DPIA – ocena skutków dla ochrony danych")
    FRIA = "fria", _("FRIA – ocena skutków dla praw podstawowych")


class SourceType(models.TextChoices):
    FOIA = "foia", _("Wniosek o informację publiczną / korespondencja")
    PUBLIC_BODY = "public_body", _("Strona instytucji publicznej")
    OFFICIAL_DOCUMENT = "official_document", _("Dokument urzędowy")
    MEDIA = "media", _("Media")
    VENDOR = "vendor", _("Dokumentacja producenta / dostawcy")
    OTHER = "other", _("Inne")


class DocumentType(models.TextChoices):
    GENERAL = "general", _("Ogólne źródło informacji")
    USER_MANUAL = "user_manual", _("Podręcznik / instrukcja")
    DPIA = "dpia", _("DPIA")
    FRIA = "fria", _("FRIA")
    PUBLIC_DESCRIPTION = "public_description", _(
        "Publiczny opis systemu lub zastosowania"
    )
    PROCUREMENT = "procurement", _("Zamówienie publiczne")
    OTHER = "other", _("Inne")


class Institution(Timestamped):
    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name=_("Nazwa instytucji"),
    )
    slug = models.SlugField(
        max_length=255,
        unique=True,
        blank=True,
        editable=False,
        verbose_name=_("Slug"),
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name) or "instytucja"
            candidate = base_slug
            counter = 2
            queryset = type(self).objects.all()
            if self.pk:
                queryset = queryset.exclude(pk=self.pk)
            while queryset.filter(slug=candidate).exists():
                candidate = f"{base_slug}-{counter}"
                counter += 1
            self.slug = candidate
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Instytucja")
        verbose_name_plural = _("Instytucje")
        ordering = ["name"]


class UsageStatus(models.TextChoices):
    IN_USE = "in_use", _("W użyciu")
    NOT_IN_USE = "not_in_use", _("Nieużywane")
    PLANNED = "planned", _("Planowane")
    ENDED = "ended", _("Zakończono używanie")
    UNKNOWN = "unknown", _("Brak informacji")


class AuthorityAIStatus(models.TextChoices):
    CONFIRMED = "confirmed", _("Instytucja uznaje za AI")
    DENIED = "denied", _("Instytucja nie uznaje za AI")
    UNCLEAR = "unclear", _("Stanowisko niejednoznaczne")
    NO_INFORMATION = "no_information", _("Brak informacji")


class AISystem(Timestamped):
    name = models.CharField(
        max_length=255,
        verbose_name=_("Nazwa systemu AI"),
    )
    purpose = models.TextField(
        blank=True,
        verbose_name=_("Przeznaczenie systemu"),
        help_text=_("Krótko, np. rozpoznawanie twarzy."),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Opis systemu"),
        help_text=_(
            "Do czego ogólnie cały system służy, jak działa i jakie procesy wspiera?"
        ),
    )
    developer = models.TextField(
        blank=True,
        verbose_name=_("Twórca / producent systemu"),
    )
    gpai_status = models.CharField(
        max_length=20,
        choices=AnswerStatus.choices,
        default=AnswerStatus.UNKNOWN,
        verbose_name=_("Czy system korzysta z modeli GPAI?"),
    )
    gpai_models = models.TextField(
        blank=True,
        verbose_name=_("Modele GPAI i ich producenci"),
    )
    comments = models.TextField(
        blank=True,
        verbose_name=_("Uwagi wewnętrzne"),
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("System AI")
        verbose_name_plural = _("Systemy AI")
        ordering = ["name"]


class Deployment(Timestamped):
    institution = models.ForeignKey(
        Institution,
        on_delete=models.CASCADE,
        related_name="deployments",
        verbose_name=_("Instytucja"),
    )
    ai_system = models.ForeignKey(
        AISystem,
        on_delete=models.CASCADE,
        related_name="deployments",
        verbose_name=_("System AI"),
    )
    supplier = models.TextField(
        blank=True,
        verbose_name=_("Dostawca systemu"),
    )

    gpai_status = models.CharField(
        max_length=20,
        choices=AnswerStatus.choices,
        default=AnswerStatus.UNKNOWN,
        verbose_name=_("Czy to wdrożenie korzysta z modeli GPAI?"),
        help_text=_(
            "Informacja dotyczy konkretnego wdrożenia systemu w danej instytucji."
        ),
    )
    gpai_models = models.TextField(
        blank=True,
        verbose_name=_("Modele GPAI i ich producenci we wdrożeniu"),
    )

    implementation_cost = models.TextField(
        blank=True,
        verbose_name=_("Koszty wytworzenia i wdrożenia"),
        help_text=_("Całkowite łączne koszty brutto ponoszone po stronie organu."),
    )
    implementation_cost_comment = models.TextField(
        blank=True,
        verbose_name=_("Komentarz do kosztów wytworzenia i wdrożenia"),
    )
    annual_maintenance_cost = models.TextField(
        blank=True,
        verbose_name=_("Koszty utrzymania"),
        help_text=_("Koszty brutto ponoszone po stronie organu w ujęciu rocznym."),
    )
    annual_maintenance_cost_comment = models.TextField(
        blank=True,
        verbose_name=_("Komentarz do kosztów utrzymania"),
    )

    license_start = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Początek obowiązywania licencji"),
    )
    license_end = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Koniec obowiązywania licencji"),
    )
    license_comment = models.TextField(
        blank=True,
        verbose_name=_("Komentarz do licencji"),
    )

    user_documentation_status = models.CharField(
        max_length=20,
        choices=AnswerStatus.choices,
        default=AnswerStatus.UNKNOWN,
        verbose_name=_("Czy użytkownicy dysponują podręcznikiem lub instrukcją?"),
    )
    user_documentation_comment = models.TextField(
        blank=True,
        verbose_name=_("Komentarz dotyczący podręcznika / instrukcji"),
    )
    public_information_status = models.CharField(
        max_length=20,
        choices=AnswerStatus.choices,
        default=AnswerStatus.UNKNOWN,
        verbose_name=_("Czy istnieją publicznie dostępne informacje o systemie?"),
    )
    public_information_comment = models.TextField(
        blank=True,
        verbose_name=_("Komentarz dotyczący publicznej wiedzy o systemie"),
    )

    public_procurement_status = models.CharField(
        max_length=20,
        choices=AnswerStatus.choices,
        default=AnswerStatus.UNKNOWN,
        verbose_name=_("Czy wdrożenie było przedmiotem zamówienia publicznego?"),
    )
    public_procurement_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Numer ogłoszenia BZP"),
    )
    public_procurement_number_eu = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Numer ogłoszenia TED"),
    )
    public_procurement_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Data ogłoszenia zamówienia publicznego"),
    )
    contracting_institution = models.ForeignKey(
        Institution,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contracted_deployments",
        verbose_name=_("Zamawiający"),
    )

    comments = models.TextField(
        blank=True,
        verbose_name=_("Uwagi wewnętrzne"),
    )

    def __str__(self):
        return f"{self.institution} – {self.ai_system}"

    class Meta:
        verbose_name = _("Wdrożenie systemu")
        verbose_name_plural = _("Wdrożenia systemów")
        constraints = [
            models.UniqueConstraint(
                fields=["institution", "ai_system"],
                name="unique_ai_system_deployment_per_institution",
            )
        ]
        ordering = ["institution__name", "ai_system__name"]


class Char32UUIDField(models.UUIDField):
    """UUID przechowywany jako CHAR(32), także w nowszej MariaDB."""

    def db_type(self, connection):
        return "char(32)"

    def get_db_prep_value(self, value, connection, prepared=False):
        value = super().get_db_prep_value(value, connection, prepared)
        return value.hex if isinstance(value, uuid.UUID) else value


class AIUse(Timestamped):
    """Central public object representing a particular use of AI."""

    public_id = Char32UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    deployment = models.ForeignKey(
        Deployment,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="ai_uses",
        verbose_name=_("Wdrożenie"),
        help_text=_(
            "Instytucja i system AI, których dotyczy to konkretne zastosowanie."
        ),
    )

    name = models.CharField(
        max_length=255,
        verbose_name=_("Nazwa zastosowania AI"),
    )
    purpose = models.TextField(
        blank=True,
        verbose_name=_("Przeznaczenie zastosowania"),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Opis zastosowania"),
    )
    ai_use_description = models.TextField(
        blank=True,
        verbose_name=_("Użycie sztucznej inteligencji"),
        help_text=_(
            "Do czego w tym zastosowaniu i wspieranym procesie używane są komponenty oparte na AI?"
        ),
    )

    process_name = models.TextField(
        blank=True,
        verbose_name=_("Proces / procedura"),
    )
    process_description = models.TextField(
        blank=True,
        verbose_name=_("Opis procesu / procedury"),
    )
    process_stage = models.TextField(
        blank=True,
        verbose_name=_("Etap procesu / procedury"),
    )
    decision_or_action = models.TextField(
        blank=True,
        verbose_name=_("Decyzja lub działanie"),
        help_text=_(
            "Jaka decyzja, rozstrzygnięcie lub inne działanie organu jest związane z tym zastosowaniem AI?"
        ),
    )
    ai_role = models.TextField(
        blank=True,
        verbose_name=_("Rola AI w procesie"),
    )
    human_role = models.TextField(
        blank=True,
        verbose_name=_("Rola człowieka w procesie"),
    )

    risk_classification = models.CharField(
        max_length=30,
        choices=RiskClassification.choices,
        default=RiskClassification.UNKNOWN,
        verbose_name=_("Kwalifikacja ryzyka według AI Act"),
    )
    risk_comment = models.TextField(
        blank=True,
        verbose_name=_("Komentarz do kwalifikacji ryzyka"),
    )

    areas = TaggableManager(
        through="home.TaggedArea",
        blank=True,
        verbose_name=_("Obszary"),
        help_text=_("Oddzielone średnikami"),
    )
    tags = TaggableManager(
        through="home.TaggedGeneric",
        blank=True,
        verbose_name=_("Tagi"),
        help_text=_("Oddzielone średnikami"),
    )

    use_start = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Początek stosowania"),
    )
    use_end = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Koniec stosowania"),
    )

    published = models.BooleanField(
        default=True,
        verbose_name=_("Opublikowano"),
        help_text=_("Czy zastosowanie ma być widoczne w publicznym rejestrze?"),
    )
    comments = models.TextField(
        blank=True,
        verbose_name=_("Uwagi wewnętrzne"),
    )

    def __str__(self):
        if self.deployment:
            return f"{self.name} – {self.deployment.institution}"
        return self.name

    class Meta:
        verbose_name = _("Zastosowanie AI")
        verbose_name_plural = _("Zastosowania AI")
        ordering = ["-created_at"]


class Assessment(Timestamped):
    ai_use = models.ForeignKey(
        AIUse,
        on_delete=models.CASCADE,
        related_name="assessments",
        verbose_name=_("Zastosowanie AI"),
    )
    assessment_type = models.CharField(
        max_length=10,
        choices=AssessmentType.choices,
        verbose_name=_("Rodzaj oceny"),
    )
    status = models.CharField(
        max_length=20,
        choices=AnswerStatus.choices,
        default=AnswerStatus.UNKNOWN,
        verbose_name=_("Status"),
    )
    comment = models.TextField(
        blank=True,
        verbose_name=_("Komentarz"),
    )

    def __str__(self):
        return f"{self.get_assessment_type_display()}: {self.ai_use}"

    class Meta:
        verbose_name = _("Ocena")
        verbose_name_plural = _("Oceny")
        constraints = [
            models.UniqueConstraint(
                fields=["ai_use", "assessment_type"],
                name="unique_assessment_type_per_ai_use",
            )
        ]


class AIUseStatusObservation(Timestamped):
    ai_use = models.ForeignKey(
        AIUse,
        on_delete=models.CASCADE,
        related_name="status_observations",
        verbose_name=_("Zastosowanie AI"),
    )
    observed_on = models.DateField(
        verbose_name=_("Stan na dzień"),
        help_text=_(
            "Data, której dotyczy informacja o używaniu systemu i stanowisku instytucji."
        ),
    )
    usage_status = models.CharField(
        max_length=20,
        choices=UsageStatus.choices,
        default=UsageStatus.UNKNOWN,
        verbose_name=_("Status użycia"),
    )
    authority_ai_status = models.CharField(
        max_length=20,
        choices=AuthorityAIStatus.choices,
        default=AuthorityAIStatus.NO_INFORMATION,
        verbose_name=_("Stanowisko instytucji co do kwalifikacji jako AI"),
        help_text=_(
            "Czy instytucja sama uznaje opisywane zastosowanie lub funkcjonalność za AI."
        ),
    )
    comment = models.TextField(
        blank=True,
        verbose_name=_("Komentarz do statusu / kwalifikacji"),
    )
    sources = models.ManyToManyField(
        "Source",
        blank=True,
        related_name="status_observations",
        verbose_name=_("Źródła potwierdzające stan"),
    )

    def __str__(self):
        return (
            f"{self.ai_use} – {self.observed_on}: " f"{self.get_usage_status_display()}"
        )

    class Meta:
        verbose_name = _("Obserwacja statusu zastosowania AI")
        verbose_name_plural = _("Obserwacje statusu zastosowań AI")
        ordering = ["-observed_on", "-created_at"]


class Source(Timestamped):
    title = models.CharField(
        max_length=255,
        verbose_name=_("Nazwa / opis źródła"),
    )
    url = models.URLField(
        max_length=1000,
        blank=True,
        verbose_name=_("URL"),
    )
    source_type = models.CharField(
        max_length=30,
        choices=SourceType.choices,
        default=SourceType.OTHER,
        verbose_name=_("Typ źródła"),
    )
    document_type = models.CharField(
        max_length=30,
        choices=DocumentType.choices,
        default=DocumentType.GENERAL,
        verbose_name=_("Rodzaj dokumentu / informacji"),
    )
    date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Data źródła"),
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_("Uwagi"),
    )

    systems = models.ManyToManyField(
        AISystem,
        blank=True,
        related_name="sources",
        verbose_name=_("Systemy AI"),
    )
    deployments = models.ManyToManyField(
        Deployment,
        blank=True,
        related_name="sources",
        verbose_name=_("Wdrożenia"),
    )
    ai_uses = models.ManyToManyField(
        AIUse,
        blank=True,
        related_name="sources",
        verbose_name=_("Zastosowania AI"),
    )
    assessments = models.ManyToManyField(
        Assessment,
        blank=True,
        related_name="sources",
        verbose_name=_("Oceny"),
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _("Źródło")
        verbose_name_plural = _("Źródła")
        ordering = ["-date", "title"]
