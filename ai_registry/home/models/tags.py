from django.db import models
from django.utils.translation import gettext_lazy as _
from taggit.models import GenericTaggedItemBase, TagBase


def custom_tag_string_parser(tag_string):
    return [t.strip(' "') for t in tag_string.split(";") if t.strip(' "')]


def custom_tag_string_joiner(tags):
    return "; ".join(tag.name for tag in tags)


class GenericTag(TagBase):
    class Meta:
        verbose_name = _("Tag")
        verbose_name_plural = _("Tagi")


class AreaTag(TagBase):
    class Meta:
        verbose_name = _("Obszar")
        verbose_name_plural = _("Obszary")


class TaggedGeneric(GenericTaggedItemBase):
    tag = models.ForeignKey(
        GenericTag,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_items",
    )

    class Meta:
        verbose_name = _("Tag")
        verbose_name_plural = _("Tagi")


class TaggedArea(GenericTaggedItemBase):
    tag = models.ForeignKey(
        AreaTag,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_items",
    )

    class Meta:
        verbose_name = _("Tag obszaru")
        verbose_name_plural = _("Tagi obszarów")
