# Future imports
from __future__ import annotations

# Standard libs
from copy import deepcopy
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Dict
    from typing import List
    from typing import Optional
    from typing import Set
    from typing import Tuple

    from wagtail.admin.panels import Panel
    from wagtail_modeladmin.options import ModelAdmin

# Django imports
from django.conf import settings
from django.db.models import Model
from django.forms.models import fields_for_model
from django.utils.translation import gettext_lazy as _

# Third Party
from wagtail.admin.panels import FieldPanel
from wagtail.admin.panels import ObjectList
from wagtail.admin.panels import TabbedInterface
from wagtail.snippets.views.snippets import SnippetViewSet

# wagtail / parler
from wagtail_parler import settings as wp_settings

# Local Apps
from .forms import build_translations_form


class TranslationsList(ObjectList):
    def __init__(self, *args: Tuple, **kwargs: Dict):
        self.current_parler_language = kwargs.pop("current_parler_language", None)
        self.initial_parler_heading = kwargs.pop(
            "initial_parler_heading", kwargs.pop("heading", None)
        )
        super().__init__(*args, **kwargs)

    @property
    def clean_name(self) -> str:
        return "parler_translations_%s" % (self.current_parler_language or "all")

    def _set_parler_heading(self, instance: Model) -> None:
        current_parler_language = getattr(self, "current_parler_language", None)
        conf = next(
            conf
            for conf in settings.PARLER_LANGUAGES[None]
            if conf["code"] == current_parler_language
        )
        locale_labels = dict(settings.LANGUAGES)
        headings_conf = wp_settings.HEADINGS_CONF  # type: ignore
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
        if "%(" in heading:  # type: ignore
            heading = heading % {  # type: ignore
                "locale": locale_labels[conf["code"]],
                "status": conf_heading["status"],
                **conf,
            }
        self.heading = heading

    def clone_kwargs(self) -> Dict:
        kwargs = super().clone_kwargs()
        kwargs["current_parler_language"] = getattr(self, "current_parler_language", None)
        kwargs["initial_parler_heading"] = getattr(self, "initial_parler_heading", self.heading)
        return kwargs

    def get_bound_panel(
        self, instance: Model = None, *args: Tuple, **kwargs: Dict
    ) -> ObjectList.BoundPanel:
        self._set_parler_heading(instance)
        return super().get_bound_panel(instance, *args, **kwargs)


class ParlerAdminWagtailMixin:
    """
    Mixin to manage translations via Parler inside a ModelAdmin or SnippetViewSet

    You **SHOULD NOT** use this Mixin directly but ParlerModelAdminMixin or ParlerSnippetAdminMixin
    """

    def _set_translations_handlers(
        self: ModelAdmin, handlers: List, base_handler: Optional[TranslationsList] = None
    ) -> Set[str]:
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
                    heading="",  # type: ignore
                    children=children,  # type: ignore
                )
            else:
                base_handler.children = children

        def recurse_child_replace(handler: Panel, locale: str) -> None:
            for child in handler.children:
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

    def get_edit_handler(self: ModelAdmin) -> TabbedInterface:
        """
        Prepare real handlers to be used with this Model Admin.
        """
        base_handlers = super().get_edit_handler()  # type: ignore
        displayed_fields = None
        handlers: List = []
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
        # currently (wagtail 6), `ModelViewSet.formfield_for_dbfield` returns
        # `db_field.formfield(**kwargs)` instead of using the wagtail registry fields overrides
        # as the WagtailAdminModelForm do via it's Meta.formfield_callback.
        # So we don't want to use ModelViewSet.formfield_for_dbfield BUT if the user
        # defines it's own MyViewSet.formfield_for_dbfield, we must use it (because he knows
        # what he does and it's his responsability to use the wagtail registry fields overrides)
        # sources:
        # - https://github.com/wagtail/wagtail/blob/main/wagtail/admin/viewsets/model.py#L534
        # - https://github.com/wagtail/wagtail/blob/main/wagtail/admin/forms/models.py#L129
        main_form_meta_attrs = {}
        formfield_for_dbfield = getattr(self, "formfield_for_dbfield", None)
        if (
            formfield_for_dbfield
            and formfield_for_dbfield.__func__.__qualname__ != "ModelViewSet.formfield_for_dbfield"
        ):
            main_form_meta_attrs["formfield_callback"] = self.formfield_for_dbfield
        base_form_class = build_translations_form(
            self.model,
            fields_for_model_kwargs={"fields": displayed_fields},
            base_form=getattr(self, "parler_base_form_class", None),
        )
        return TabbedInterface(handlers, base_form_class=base_form_class)


class ParlerModelAdminMixin(ParlerAdminWagtailMixin):
    """
    Mixin to use with ModelAdmin to manage parler translations.
    ex:

    .. code-block:: python

        class SomeModelAdmin(ParlerModelAdminMixin, ModelAdmin):
            model = SomeModel


        class FoodModelAdmin(ParlerModelAdminMixin, ModelAdmin):
            model = Food
            edit_handler = ObjectList(
                children=[
                    FieldPanel("yum_rating"),
                    TranslationsList(
                        heading="%(code)s: %(locale)s %(status)s",  # type: ignore
                        # let children empty, it will be auto populated
                    ),
                    ObjectList(
                        heading=_("Régime"),
                        children=[FieldPanel("vegetarian"), FieldPanel("vegan")]
                    ),
                ],
            )
    """


class ParlerSnippetAdminMixin(ParlerAdminWagtailMixin, SnippetViewSet):
    """
    Mixin to use with SnippetViewSet to manage parler translations.

    If no edit_handler are defined, the default behaviour will create an unstranlated data tab
    then a tab for each language
    You can specify your edit_handler to have more control over how form is built.
    TranslationsList will be duplicated for each language and populated with
    translations fields if no children are given. Of course, you can also configure
    fields manually
    ex:

    .. code-block:: python

        class SomeModelAdminSnippet(ParlerSnippetAdminMixin, SnippetViewSet):
            model = SomeModel


        class FoodAdminSnippet(ParlerSnippetAdminMixin, SnippetViewSet):
            model = Food
            edit_handler = ObjectList(
                children=[
                    FieldPanel("yum_rating"),
                    TranslationsList(
                        heading="%(code)s: %(locale)s %(status)s",
                        # let children empty, it will be auto populated
                    ),
                    ObjectList(
                        heading=_("Régime"),
                        children=[FieldPanel("vegetarian"), FieldPanel("vegan")]
                    ),
                ],
            )
    """

    def get_edit_handler(self: SnippetViewSet) -> TabbedInterface:
        return super().get_edit_handler().bind_to_model(self.model)
