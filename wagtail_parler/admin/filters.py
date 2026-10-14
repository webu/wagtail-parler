from django import forms
from django.conf import settings
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

import django_filters

# from django_select2.forms import Select2MultipleWidget
from wagtail.admin.filters import WagtailFilterSet


class TranslationsFilterSet(WagtailFilterSet):
    untranslated = django_filters.MultipleChoiceFilter(
        label=_("À traduire"),
        method="filter_untranslated",
        choices=list(
            (language["code"], language["translated_label"])
            for language in settings.PARLER_LANGUAGES[None]
        ),
        widget=forms.CheckboxSelectMultiple,
        # empty_label="",
    )

    def filter_untranslated(self, queryset, name, value):
        if not value:
            return queryset
        q = None
        for lang in value:
            if q is None:
                q = Q(translations__language_code=lang)
            else:
                q |= Q(translations__language_code=lang)
        return queryset.exclude(q)
