# Django imports
from django.utils.translation import gettext_lazy as _

# Third Party
from wagtail.admin.panels import FieldPanel
from wagtail.admin.panels import ObjectList
from wagtail.contrib.modeladmin.options import ModelAdmin
from wagtail.contrib.modeladmin.options import modeladmin_register
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

# wagtail / parler
from wagtail_parler.handlers import ParlerModelAdminMixin
from wagtail_parler.handlers import ParlerSnippetAdminMixin
from wagtail_parler.handlers import TranslationsList
from wagtail_parler_tests.models import Food
from wagtail_parler_tests.models import FoodWithEditHandler
from wagtail_parler_tests.models import FoodWithPanelsInsideModel
from wagtail_parler_tests.models import FoodWithSpecificEditHandler

specific_edit_handler = ObjectList(
    children=[
        FieldPanel("yum_rating"),
        TranslationsList(
            heading="%(code)s: %(locale)s %(status)s",
            children=[
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


class FoodWithSpecificEditHandlerAdmin(ParlerModelAdminMixin, ModelAdmin):
    model = FoodWithSpecificEditHandler
    edit_handler = specific_edit_handler


modeladmin_register(FoodAdmin)
modeladmin_register(FoodWithPanelsInsideModelAdmin)
modeladmin_register(FoodWithEditHandlerAdmin)
modeladmin_register(FoodWithSpecificEditHandlerAdmin)


# Now, same things but  for Snippets
class FoodAdminSnippet(ParlerSnippetAdminMixin, SnippetViewSet):
    model = Food


class FoodWithPanelsInsideModelAdminSnippet(ParlerSnippetAdminMixin, SnippetViewSet):
    model = FoodWithPanelsInsideModel


class FoodWithEditHandlerAdminSnippet(ParlerSnippetAdminMixin, SnippetViewSet):
    model = FoodWithEditHandler


class FoodWithSpecificEditHandlerAdminSnippet(ParlerSnippetAdminMixin, SnippetViewSet):
    model = FoodWithSpecificEditHandler
    edit_handler = specific_edit_handler


register_snippet(FoodAdminSnippet)
register_snippet(FoodWithPanelsInsideModelAdminSnippet)
register_snippet(FoodWithEditHandlerAdminSnippet)
register_snippet(FoodWithSpecificEditHandlerAdminSnippet)
