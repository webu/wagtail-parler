# Django imports
from django.conf import settings
from django.db import transaction
from django.forms import Form
from django.forms.models import ModelForm
from django.forms.models import fields_for_model

# Third Party
from parler.models import TranslatableModelMixin


class AutoParlerModelForm(Form):
    """
    Manage update/create/delete of translations
    """

    # pylint: disable=no-member
    auto_parler_fields = set()
    cleaned_data_for_locales = {}

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("initial", {})
        self._init_i18n_initials(kwargs.get("instance"), kwargs["initial"])
        self.for_user = kwargs.pop("for_user")
        super().__init__(*args, **kwargs)
        # All fields of others locales than the default one must NOT be required
        for conf in settings.PARLER_LANGUAGES[None][1:]:
            for _field_name, i18n_field_name in self.get_localized_fieldnames(conf["code"]):
                self.fields[i18n_field_name].required = False  # type: ignore
                self.fields[i18n_field_name].label += " (%s)" % conf["code"].upper()  # type: ignore

    def _init_i18n_initials(self, instance, initials):
        """
        If instance already has translations, populates the initial content of translated fields
        """
        if not instance or not instance.pk:
            return
        for translation in instance.translations.all():
            language_code = translation.language_code
            for field_name, i18n_field_name in self.get_localized_fieldnames(language_code):
                if hasattr(translation, field_name):
                    initials[i18n_field_name] = getattr(translation, field_name)
        return initials

    def get_localized_fieldnames(self, locale: str):
        """
        Generator of (field_name: str, i18n_field_name:str) to get real field_name for
        the translated model and the current form associated field name.

        param: locale: str: locale code of translation to save/create/delete
        """
        for field_name in self.auto_parler_fields:
            i18n_field_name = "translations_%s_%s" % (locale, field_name)
            yield (field_name, i18n_field_name)

    def _save_locale(self, locale: str):
        """
        Depending sent data, will save/create/delete translation for the given language code

        param: locale: str: locale code of translation to save/create/delete
        return: (None|True|False, int|instance|[instances]:
            for deletion, will return None and the number of translations deleted
            for creation, will return True and the created of translation
            for update, will return False and the updated of translation
        """
        obj = self.instance  # type: ignore
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

    def clean(self):
        """
        Prepare cleaned_data_for_locales of translated fields
        """
        self.cleaned_data_for_locales = {}
        for conf in settings.PARLER_LANGUAGES[None]:
            data = self.cleaned_data_for_locales[conf["code"]] = {}
            for field_name, i18n_field_name in self.get_localized_fieldnames(conf["code"]):
                if i18n_field_name in self.cleaned_data:  # type: ignore
                    data[field_name] = self.cleaned_data[i18n_field_name]  # type: ignore
        return super().clean()  # type: ignore

    @transaction.atomic
    def save(self, *args, **kwargs):
        """
        Save the instance and it's translations
        """
        instance = super().save(*args, **kwargs)  # type: ignore
        for conf in settings.PARLER_LANGUAGES[None]:
            self._save_locale(conf["code"])
        return instance


def build_translations_form(
    model, main_form_meta_attrs=None, fields_for_model_kwargs=None, base_form=None
):
    """
    Build a model form with support of translable fields which are auto added to the form
    """
    if not base_form:
        base_form = ModelForm

    if not main_form_meta_attrs:
        main_form_meta_attrs = {}
    main_form_meta_attrs["model"] = model

    if "exclude" not in main_form_meta_attrs and "fields" not in main_form_meta_attrs:
        main_form_meta_attrs["fields"] = "__all__"

    attrs = {
        "Meta": type("Meta", (), main_form_meta_attrs),
        "auto_parler_fields": set(),
    }
    i18n_model = model._parler_meta.root_model  # pylint: disable=protected-access
    fields_for_model_kwargs = fields_for_model_kwargs or {}
    fields_for_model_kwargs["model"] = i18n_model
    for conf in settings.PARLER_LANGUAGES[None]:
        for field_name, field in fields_for_model(**fields_for_model_kwargs).items():
            attrs["auto_parler_fields"].add(field_name)
            attrs["translations_%s_%s" % (conf["code"], field_name)] = field
    return type("%sForm" % model.__name__, (AutoParlerModelForm, base_form), attrs)
