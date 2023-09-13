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
from wagtail.snippets.views.snippets import SnippetViewSet

# wagtail / parler
from wagtail_parler import settings as wagtail_parler_settings

# Local Apps
from .forms import build_translations_form


class TranslationsList(ObjectList):
    current_parler_language = None
    initial_parler_heading = None

    def __init__(self, *args, **kwargs):
        self.current_parler_language = kwargs.pop("current_parler_language", None)
        self.initial_parler_heading = kwargs.pop(
            "initial_parler_heading", kwargs.pop("heading", None)
        )
        super().__init__(*args, **kwargs)

    @property
    def clean_name(self):
        """
        A name for this panel, consisting only of ASCII alphanumerics and underscores, suitable for use in identifiers.
        Usually generated from the panel heading. Note that this is not guaranteed to be unique or non-empty; anything
        making use of this and requiring uniqueness should validate and modify the return value as needed.
        """
        if self.current_parler_language:
            return "parler_translations_%s" % self.current_parler_language
        return "parler_translations_all"

    def _set_parler_heading(self, instance):
        current_parler_language = getattr(self, "current_parler_language", None)
        if not current_parler_language:
            return
        conf = None
        for conf in settings.PARLER_LANGUAGES[None]:
            if conf["code"] == current_parler_language:
                break
        if not conf or conf["code"] != current_parler_language:
            return
        handler = self
        locale_labels = dict(settings.LANGUAGES)
        headings_conf = wagtail_parler_settings.HEADINGS_CONF  # type: ignore  pylint: disable=no-member
        if instance and instance.pk:
            if not instance.has_translation(conf["code"]):
                conf_heading = headings_conf["untranslated"]
            else:
                conf_heading = headings_conf["translated"]
        else:
            conf_heading = headings_conf["creating"]
        heading = self.initial_parler_heading
        if not heading or "%(" not in heading:
            heading = conf_heading["label"]
        if "%(" in heading:
            heading = heading % {
                "locale": locale_labels[conf["code"]],
                "status": conf_heading["status"],
                **conf,
            }
        self.heading = heading

    def clone_kwargs(self):
        kwargs = super().clone_kwargs()
        kwargs["current_parler_language"] = getattr(self, "current_parler_language", None)
        kwargs["initial_parler_heading"] = getattr(self, "initial_parler_heading", self.heading)
        return kwargs

    def get_bound_panel(self, instance=None, *args, **kwargs):
        self._set_parler_heading(instance)
        return super().get_bound_panel(instance, *args, **kwargs)


class ParlerAdminWagtailMixin:
    """
    Mixin to manage translations via Parler inside a ModelAdmin or SnippetViewSet
    """

    def _set_translations_handlers(self: ModelAdmin, handlers, base_handler=None):
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
                base_handler = TranslationsList(
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

        for conf in settings.PARLER_LANGUAGES[None]:
            handler = deepcopy(base_handler)
            handler.current_parler_language = conf["code"]
            handler._set_parler_heading(None)
            recurse_child_replace(handler, conf["code"])
            handlers.append(handler)
        return displayed_fields

    def get_edit_handler(self: ModelAdmin):
        """
        Prepare real handlers to be used with this Model Admin.
        """
        base_handlers = super().get_edit_handler()
        displayed_fields = None
        handlers = []
        for handler in base_handlers.children:
            if isinstance(handler, TranslationsList):
                displayed_fields = self._set_translations_handlers(handlers, base_handler=handler)
            else:
                handlers.append(handler)
        if displayed_fields is None:
            handlers = [
                base_handlers.__class__(
                    heading=getattr(base_handlers, "heading", None) or _("Untranslated data"),
                    children=handlers,
                )
            ]
            displayed_fields = self._set_translations_handlers(handlers)
        base_form_class = build_translations_form(
            self.model,
            fields_for_model_kwargs={"fields": displayed_fields},
            base_form=getattr(self, "form", None),
        )
        return TabbedInterface(handlers, base_form_class=base_form_class)


class ParlerModelAdminMixin(ParlerAdminWagtailMixin):
    pass


class ParlerSnippetAdminMixin(ParlerAdminWagtailMixin):
    def get_edit_handler(self: SnippetViewSet):
        return super().get_edit_handler().bind_to_model(self.model)
