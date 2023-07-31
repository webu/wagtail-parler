# Standard libs
from copy import deepcopy
import logging

# Django imports
from django.conf import settings
from django.forms.models import fields_for_model
from django.utils.translation import gettext_lazy as _

# Third Party
from wagtail.admin.panels import FieldPanel
from wagtail.admin.panels import ObjectList
from wagtail.admin.panels import TabbedInterface
from wagtail.contrib.modeladmin.options import ModelAdmin
from wagtail.contrib.modeladmin.views import ModelFormView

# wagtail / parler
from wagtail_modeladmin_parler import settings as wmp_settings

# Local Apps
from .forms import build_translations_form


class WagtailParlerCreateViewMixin:
    """
    This mixin ensures the use of `ParlerModelAdminMixin.get_edit_handler` for CreateViews
    """

    def get_edit_handler(self: ModelFormView):
        edit_handler = self.model_admin.get_edit_handler()
        return edit_handler.bind_to_model(self.model_admin.model)


class WagtailParlerEditViewMixin:
    """
    This mixin ensures the use of `ParlerModelAdminMixin.get_edit_handler` for EditViews
    """

    def get_edit_handler(self: ModelFormView):
        edit_handler = self.model_admin.get_edit_handler(self.instance)
        return edit_handler.bind_to_model(self.model_admin.model)


class TranslationsList(ObjectList):
    pass


class ParlerModelAdminMixin:
    """
    Mixin to manage translations via Parler inside a ModelAdmin
    You must define a base_handlers dict wich contains the handlers that will be used
    to build the final handlers used inside a TabbedInterface.
    ex:
    class MyModelAdmin(ParlerModelAdminMixin, ModelAdmin):
        model = MyModel
        # You can personalize your edit_handler
        edit_handler = ObjectList([
            ObjectList(
                heading="Some fields",
                children=[
                    FieldPanel("field1"),
                    FieldPanel("field2"),
                ]
            ),
            ObjectList(
                heading="Some fields",
                # if children is empty, fields will be auto set
                children=[
                    FieldPanel("trans_field1"),
                    FieldPanel("trans_field2"),
                ]
            ),
            ObjectList(
                heading="Some fields",
                children=[
                    FieldPanel("field3"),
                    FieldPanel("field4"),
                ]
            ),
        ])

        # if you set only panels inside your models, it will be auto added as TabbedInterface too

        # if you don't set it inside model nor admin, it will be auto added as TabbedInterface too
    """

    base_handlers = {}

    def _set_translations_handlers(self: ModelAdmin, handlers, instance=None, base_handler=None):
        """
        Build handler for each locale and add it to `handlers` list
        base_handler can be used as a template : all it's children which are FieldPanel
        will have their field_name renamed with `translations_%(language_code)s_%(field_name)s`
        if they exists in the translation Model.
        """
        # TODO get I18nModel in safer way because maybe it'ns not called translations
        I18nModel = self.model._meta.get_field("translations").related_model
        translated_fields = [*fields_for_model(I18nModel).keys()]
        displayed_fields = set()
        if not base_handler or not getattr(base_handler, "children"):
            children = []
            for field_name in translated_fields:
                if field_name != "language_code":
                    children.append(FieldPanel(field_name))
            if not base_handler:
                base_handler = ObjectList(
                    heading="",
                    children=children,
                )
            else:
                base_handler.children = children

        def recurse_child_replace(handler, locale):
            children = getattr(handler, "children", None)
            if not children:
                return
            for child in children:
                if isinstance(child, FieldPanel) and child.field_name in translated_fields:
                    displayed_fields.add(child.field_name)
                    child.field_name = "translations_%s_%s" % (locale, child.field_name)
                if hasattr(child, "children"):
                    recurse_child_replace(child, locale)

        locale_labels = dict(settings.LANGUAGES)
        headings_conf = wmp_settings.HEADINGS_CONF  # type: ignore  pylint: disable=no-member
        for conf in settings.PARLER_LANGUAGES[None]:
            handler = deepcopy(base_handler)
            if instance and instance.pk:
                if not instance.has_translation(conf["code"]):
                    conf_heading = headings_conf["untranslated"]
                else:
                    conf_heading = headings_conf["translated"]
            else:
                conf_heading = headings_conf["creating"]
            if not handler.heading:
                handler.heading = conf_heading["label"]
            if "%(" in handler.heading:
                handler.heading = handler.heading % {
                    "locale": locale_labels[conf["code"]],
                    "status": conf_heading["status"],
                    **conf,
                }

            recurse_child_replace(handler, conf["code"])
            handlers.append(handler)
        return displayed_fields

    def get_edit_handler(self: ModelAdmin, instance=None):
        """
        Prepare real handlers to be used with this Model Admin.
        """
        base_handlers = super().get_edit_handler()
        displayed_fields = None
        handlers = []
        for handler in base_handlers.children:
            if isinstance(handler, TranslationsList):
                displayed_fields = self._set_translations_handlers(handlers, instance, handler)
            else:
                handlers.append(handler)
        if displayed_fields is None:
            handlers = [
                base_handlers.__class__(
                    heading=getattr(base_handlers, "heading", None) or _("Untranslated data"),
                    children=handlers,
                )
            ]
            displayed_fields = self._set_translations_handlers(handlers, instance)
        base_form_class = build_translations_form(
            self.model,
            fields_for_model_kwargs={"fields": displayed_fields},
            base_form=getattr(self, "form", None),
        )
        return TabbedInterface(handlers, base_form_class=base_form_class)

    def edit_view(self: ModelAdmin, request, instance_pk):
        """
        Ensures the class based `EditView` use our `WagtailParlerCreateViewMixin` to force
        the use of our `get_edit_handler` method.
        """
        kwargs = {"model_admin": self, "instance_pk": instance_pk}
        cls_name = self.edit_view_class.__name__ + "Parler"
        view_class = type(cls_name, (WagtailParlerEditViewMixin, self.edit_view_class), {})
        return view_class.as_view(**kwargs)(request)

    def create_view(self: ModelAdmin, request):
        """
        Ensures the class based `CreateView` use our `WagtailParlerCreateViewMixin` to force
        the use of our `get_edit_handler` method.
        """
        kwargs = {"model_admin": self}
        cls_name = self.create_view_class.__name__ + "Parler"
        view_class = type(cls_name, (WagtailParlerCreateViewMixin, self.create_view_class), {})
        return view_class.as_view(**kwargs)(request)
