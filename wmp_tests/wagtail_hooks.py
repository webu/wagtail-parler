# Django imports
from django.utils.translation import gettext_lazy as _

# Third Party
from wagtail.admin.panels import FieldPanel
from wagtail.admin.panels import ObjectList
from wagtail.contrib.modeladmin.options import ModelAdmin
from wagtail.contrib.modeladmin.options import ModelAdminGroup
from wagtail.contrib.modeladmin.options import modeladmin_register

# wagtail / parler
from wagtail_modeladmin_parler.handlers import ParlerModelAdminMixin
from wagtail_modeladmin_parler.handlers import TranslationsList

# feelathome specific
from wmp_tests.models import Food
from wmp_tests.models import FoodWithEditHandler
from wmp_tests.models import FoodWithPanelsInsideModel
from wmp_tests.models import FoodWithSpecificEditHandler


class FoodAdmin(ParlerModelAdminMixin, ModelAdmin):
    model = Food


class FoodWithPanelsInsideModelAdmin(ParlerModelAdminMixin, ModelAdmin):
    model = FoodWithPanelsInsideModel


class FoodWithEditHandlerAdmin(ParlerModelAdminMixin, ModelAdmin):
    model = FoodWithEditHandler


class FoodWithSpecificEditHandlerAdmin(ParlerModelAdminMixin, ModelAdmin):
    model = FoodWithSpecificEditHandler
    edit_handler = ObjectList(
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
            ObjectList(
                heading=_("Régime"), children=[FieldPanel("vegetarian"), FieldPanel("vegan")]
            ),
        ],
    )


modeladmin_register(FoodAdmin)
modeladmin_register(FoodWithPanelsInsideModelAdmin)
modeladmin_register(FoodWithEditHandlerAdmin)
modeladmin_register(FoodWithSpecificEditHandlerAdmin)
