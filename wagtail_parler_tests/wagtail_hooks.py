# Standard libs
from copy import deepcopy

# Django imports
from django.utils.translation import gettext_lazy as _

# Third Party
from wagtail.admin.panels import FieldPanel, ObjectList
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet
from wagtail_modeladmin.options import ModelAdmin, modeladmin_register

# wagtail / parler
from wagtail_parler.handlers import (
    ParlerModelAdminMixin,
    ParlerSnippetAdminMixin,
    TranslationsList,
)
from wagtail_parler_tests.models import (
    Food,
    FoodWithEditHandler,
    FoodWithEmptyEditHandler,
    FoodWithPanelsInsideModel,
    FoodWithSpecificEditHandler,
)

specific_edit_handler = ObjectList(
    children=[
        FieldPanel("yum_rating"),
        TranslationsList(
            heading="%(code)s: %(locale)s %(status)s",  # type: ignore
            children=[  # type: ignore
                FieldPanel("name"),
                ObjectList(
                    heading="HTML content",
                    children=[
                        FieldPanel("summary"),
                        FieldPanel("content"),
                    ],
                ),
            ],
        ),
        ObjectList(heading=_("Régime"), children=[FieldPanel("vegetarian"), FieldPanel("vegan")]),
    ],
)


class FoodAdmin(ParlerModelAdminMixin, ModelAdmin):
    model = Food


class FoodWithPanelsInsideModelAdmin(ParlerModelAdminMixin, ModelAdmin):
    model = FoodWithPanelsInsideModel


class FoodWithEditHandlerAdmin(ParlerModelAdminMixin, ModelAdmin):
    model = FoodWithEditHandler


class FoodWithEmptyEditHandlerAdmin(ParlerModelAdminMixin, ModelAdmin):
    model = FoodWithEmptyEditHandler
    edit_handler = ObjectList(
        children=[
            FieldPanel("yum_rating"),
            TranslationsList(
                heading="%(code)s: %(locale)s %(status)s",  # type: ignore
                # let children empty, it will be auto populated
            ),
            ObjectList(
                heading=_("Régime"), children=[FieldPanel("vegetarian"), FieldPanel("vegan")]
            ),
        ],
    )


class FoodWithSpecificEditHandlerAdmin(ParlerModelAdminMixin, ModelAdmin):
    model = FoodWithSpecificEditHandler
    edit_handler = deepcopy(specific_edit_handler)


modeladmin_register(FoodAdmin)
modeladmin_register(FoodWithPanelsInsideModelAdmin)
modeladmin_register(FoodWithEditHandlerAdmin)
modeladmin_register(FoodWithEmptyEditHandlerAdmin)
modeladmin_register(FoodWithSpecificEditHandlerAdmin)


# Now, same things but  for Snippets
class FoodAdminSnippet(ParlerSnippetAdminMixin, SnippetViewSet):
    model = Food


class FoodWithPanelsInsideModelAdminSnippet(ParlerSnippetAdminMixin, SnippetViewSet):
    model = FoodWithPanelsInsideModel


class FoodWithEditHandlerAdminSnippet(ParlerSnippetAdminMixin, SnippetViewSet):
    model = FoodWithEditHandler


class FoodWithEmptyEditHandlerAdminSnippet(ParlerSnippetAdminMixin, SnippetViewSet):
    model = FoodWithEmptyEditHandler
    edit_handler = ObjectList(
        children=[
            FieldPanel("yum_rating"),
            TranslationsList(
                heading="%(code)s: %(locale)s %(status)s",  # type: ignore
                # let children empty, it will be auto populated
            ),
            ObjectList(
                heading=_("Régime"), children=[FieldPanel("vegetarian"), FieldPanel("vegan")]
            ),
        ],
    )


class FoodWithSpecificEditHandlerAdminSnippet(ParlerSnippetAdminMixin, SnippetViewSet):
    model = FoodWithSpecificEditHandler
    edit_handler = deepcopy(specific_edit_handler)


register_snippet(FoodAdminSnippet)
register_snippet(FoodWithPanelsInsideModelAdminSnippet)
register_snippet(FoodWithEditHandlerAdminSnippet)
register_snippet(FoodWithEmptyEditHandlerAdminSnippet)
register_snippet(FoodWithSpecificEditHandlerAdminSnippet)
