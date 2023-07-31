# Standard libs
from typing import List

# Django imports
from django.db import models
from django.utils.translation import gettext_lazy as _

# Third Party
from parler.models import TranslatableModel
from parler.models import TranslatedFields
from wagtail.admin.panels import FieldPanel
from wagtail.admin.panels import ObjectList


class BaseFood(TranslatableModel):
    yum_rating = models.PositiveSmallIntegerField(
        verbose_name=_("Score de miam"), blank=False, null=False
    )
    vegetarian = models.BooleanField(
        verbose_name=_("Vegetarian"),
        blank=False,
        null=False,
        default=False,
    )
    vegan = models.BooleanField(
        verbose_name=_("Vegan"),
        blank=False,
        null=False,
        default=False,
    )
    translations = {
        "name": models.CharField(_("Nom"), max_length=255, blank=False, null=False),
        "summary": models.TextField(_("Résumé"), blank=False, null=False),
        "content": models.TextField(_("Contenu"), blank=False, null=False),
    }

    class Meta:
        abstract = True
        verbose_name = _("Nourriture")
        verbose_name_plural = _("Nourritures")

    def __str__(self) -> str:
        return self.safe_translation_getter("name", any_language=True)

    def available_translations(self) -> List[str]:
        return self.translations.values_list("language_code", flat=True)


class Food(BaseFood):
    translations = TranslatedFields(**BaseFood.translations)

    class Meta:
        verbose_name = _("Nourriture - auto edit handlers")
        verbose_name_plural = _("Nourritures - auto edit handlers")


class FoodWithPanelsInsideModel(BaseFood):
    """
    Because modeladmin can't manage proxy models, we need to duplicate our models to tests
    """

    translations = TranslatedFields(**BaseFood.translations)

    panels = [
        FieldPanel("yum_rating"),
        ObjectList(heading=_("Régime"), children=[FieldPanel("vegetarian"), FieldPanel("vegan")]),
    ]

    class Meta:
        verbose_name = _("Nourriture - panels inside model")
        verbose_name_plural = _("Nourritures - panels inside model")


class FoodWithEditHandler(BaseFood):
    """
    Because modeladmin can't manage proxy models, we need to duplicate our models to tests
    """

    translations = TranslatedFields(**BaseFood.translations)
    edit_handler = ObjectList(
        children=[
            FieldPanel("yum_rating"),
            ObjectList(
                heading=_("Régime"), children=[FieldPanel("vegetarian"), FieldPanel("vegan")]
            ),
        ],
    )

    class Meta:
        verbose_name = _("Nourriture - edit_handler but auto translations")
        verbose_name_plural = _("Nourritures - edit_handler but auto translations")


class FoodWithSpecificEditHandler(BaseFood):
    """
    Because modeladmin can't manage proxy models, we need to duplicate our models to tests
    """

    translations = TranslatedFields(**BaseFood.translations)

    class Meta:
        verbose_name = _("Nourriture - edit__handler with specific i18n handlers")
        verbose_name_plural = _("Nourritures - edit__handler with specific i18n handlers")
