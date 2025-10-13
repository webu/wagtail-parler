# Future imports
from __future__ import annotations

from copy import deepcopy

# Standard libs
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any
    from typing import Dict
    from typing import Generator
    from typing import List
    from typing import Optional
    from typing import Set
    from typing import Tuple

    from django.db.models import Model

# Django imports
from django.conf import settings
from django.db import transaction
from django.forms import Form
from django.forms.models import fields_for_model

from parler import appsettings as parler_settings
from wagtail.admin.forms import WagtailAdminModelForm
from wagtail.admin.rich_text.editors.draftail import DraftailRichTextArea


class AutoParlerModelForm(Form):
    """
    Manage update/create/delete of translations
    """

    # pylint: disable=no-member
    auto_parler_fields: Set[str] = set()
    cleaned_data_for_locales: Dict[str, Any] = {}

    def __init__(self, *args: Tuple, **kwargs: Dict) -> None:
        kwargs.setdefault("initial", {})
        self._init_i18n_initials(kwargs.get("instance"), kwargs["initial"])
        self.for_user = kwargs.get("for_user", getattr(self, "for_user", None))
        super().__init__(*args, **kwargs)
        # All fields of others locales than the default one must NOT be required
        for conf in settings.PARLER_LANGUAGES[None][1:]:
            for _fieldname, i18n_fieldname in self.get_localized_fieldnames(conf["code"]):
                self.fields[i18n_fieldname].required = False  # type: ignore
                self.fields[i18n_fieldname].label += " (%s)" % conf["code"].upper()  # type: ignore

    def _init_i18n_initials(self, instance: Model, initials: Dict) -> Optional[Dict]:
        """
        If instance already has translations, populates the initial content of translated fields
        """
        if not instance or not instance.pk:
            return None
        for language_code in instance.get_available_languages(include_unsaved=True):
            translation = instance.get_translation(language_code)
            for field_name, i18n_field_name in self.get_localized_fieldnames(language_code):
                if hasattr(translation, field_name):
                    initials[i18n_field_name] = getattr(translation, field_name)
        # translations = getattr(instance, instance._parler_meta.root_rel_name)
        # for translation in translations.all():
        #     language_code = translation.language_code
        #     for field_name, i18n_field_name in self.get_localized_fieldnames(language_code):
        #         if hasattr(translation, field_name):
        #             initials[i18n_field_name] = getattr(translation, field_name)
        return initials

    def get_localized_fieldnames(self, locale: str) -> Generator:
        """
        Generator of (field_name: str, i18n_field_name:str) to get real field_name for
        the translated model and the current form associated field name.

        param: locale: str: locale code of translation to save/create/delete
        """
        for field_name in self.auto_parler_fields:
            i18n_field_name = "translations_%s_%s" % (locale, field_name)
            yield (field_name, i18n_field_name)

    def _set_locale(self, locale: str) -> List:
        """
        Depending sent data, will save/create/delete translation for the given language code

        Args:
            locale (str): locale code of translation to save/create/delete

        Returns:
            (None|True|False, int|instance|[instances]: for deletion, will return None and the
                number of translations deleted
                for creation, will return True and the created of translation
                for update, will return False and the updated of translation
        """
        obj = self.instance  # type: ignore
        i18n_meta = obj._parler_meta.root
        i18n_model = i18n_meta.model
        locale_cache = obj._translations_cache[i18n_model]
        locale_cache.pop(locale, None)
        data = self.cleaned_data_for_locales.get(locale)
        original_state = obj._state.adding
        if not data or all(not d for d in data.values()):
            obj._state.adding = (
                True  # Hack to avoid fetching from DB in case we empty a translation
            )
            # now, parler will believe there are no translations for this local and will use
            # fallbacks if available
            locale_cache[locale] = obj._get_translated_model(locale, use_fallback=True)
            obj._state.adding = original_state
            return []
        return [t for t in obj._set_translated_fields(locale, **data)]

    def _save_locale(self, locale: str) -> Tuple:
        """
        Depending sent data, will save/create/delete translation for the given language code

        Args:
            locale (str): locale code of translation to save/create/delete

        Returns:
            (None|True|False, int|instance|[instances]: for deletion, will return None and the
                number of translations deleted
                for creation, will return True and the created of translation
                for update, will return False and the updated of translation
        """
        obj = self.instance  # type: ignore

        # We need to empty cache to force deletion / add etc. because _set_locale could have
        # update the locale_cache for preview process.
        trans_exists = obj.has_translation(locale)
        data = self.cleaned_data_for_locales.get(locale)
        if not data or all(not d for d in data.values()):
            return None, obj.delete_translation(locale) if trans_exists else 0
        return (
            not trans_exists,
            [
                obj.save_translation(t)
                for t in obj._set_translated_fields(  # pylint: disable=protected-access
                    locale, **data
                )
            ],
        )

    def clean(self) -> Dict:
        """
        Prepare cleaned_data_for_locales of translated fields
        """
        rich_text_re = re.compile(r'^<p data-block-key="[^"]*"></p>$')
        self.cleaned_data_for_locales = {}
        for conf in settings.PARLER_LANGUAGES[None]:
            data = self.cleaned_data_for_locales[conf["code"]] = {}
            for field_name, i18n_field_name in self.get_localized_fieldnames(conf["code"]):
                if i18n_field_name in self.cleaned_data:  # type: ignore
                    if isinstance(
                        self.fields[i18n_field_name].widget, DraftailRichTextArea
                    ) and rich_text_re.search(self.cleaned_data[i18n_field_name]):
                        data[field_name] = ""  # it's only the default empty <p> tag
                    else:
                        data[field_name] = self.cleaned_data[i18n_field_name]  # type: ignore
        return super().clean()  # type: ignore

    @transaction.atomic
    def save(self, *args: Tuple, **kwargs: Dict) -> Model:
        """
        Save the instance and it's translations
        """
        instance = super().save(*args, **kwargs)  # type: ignore
        if kwargs.get("commit", True):
            for conf in settings.PARLER_LANGUAGES[None]:
                self._save_locale(conf["code"])
        else:
            # disable parler cache for this request because we may be in preview mode
            # and we don't want to retrieve from cache
            parler_settings.PARLER_ENABLE_CACHING = False
            for conf in settings.PARLER_LANGUAGES[None]:
                self._set_locale(conf["code"])
            wagtail_parler_locale_tab = self.data.get("wagtail_parler_locale_tab", None)
            available_codes = [conf["code"] for conf in settings.PARLER_LANGUAGES[None]]
            if not wagtail_parler_locale_tab or wagtail_parler_locale_tab not in available_codes:
                wagtail_parler_locale_tab = self.instance.get_current_language()
            else:
                self.instance.set_current_language(wagtail_parler_locale_tab)
        return instance


def build_translations_form(
    model: Model,
    main_form_meta_attrs: Optional[Dict] = None,
    fields_for_model_kwargs: Optional[Dict] = None,
    base_form: Optional[WagtailAdminModelForm] = None,
) -> WagtailAdminModelForm:
    """
    Build a model form with support of translable fields which are auto added to the form
    """
    if not base_form:
        base_form = WagtailAdminModelForm

    if not main_form_meta_attrs:
        main_form_meta_attrs = {}
    main_form_meta_attrs["model"] = model

    if "exclude" not in main_form_meta_attrs and "fields" not in main_form_meta_attrs:
        main_form_meta_attrs["fields"] = "__all__"

    attrs = {
        "Meta": type("Meta", (WagtailAdminModelForm.Meta,), main_form_meta_attrs),
        "auto_parler_fields": set(),
    }
    i18n_model = model._parler_meta.root_model  # pylint: disable=protected-access
    if fields_for_model_kwargs:
        fields_for_model_kwargs = deepcopy(fields_for_model_kwargs)
        fields_for_model_kwargs.pop("defer_required_on_fields", None)
    else:
        fields_for_model_kwargs = {}
    fields_for_model_kwargs["model"] = i18n_model
    for conf in settings.PARLER_LANGUAGES[None]:
        for field_name, field in fields_for_model(**fields_for_model_kwargs).items():
            attrs["auto_parler_fields"].add(field_name)  # type: ignore
            attrs["translations_%s_%s" % (conf["code"], field_name)] = field
    return type("%sForm" % model.__name__, (AutoParlerModelForm, base_form), attrs)
