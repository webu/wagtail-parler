from __future__ import annotations

from typing import Dict

from django.conf import settings

from parler.models import TranslatableModel
from wagtail.admin.ui.tables import Column


class LanguagesColumn(Column):
    """
    The language column which can be included in the ``list_display``.
    It also shows untranslated languages
    """

    cell_template_name = "wagtail_parler/tables/languages_cell.html"

    def get_value(self, instance: TranslatableModel) -> Dict:
        languages_labels = {code: label for code, label in settings.LANGUAGES}
        active_languages = instance.get_available_languages()
        current_language = instance.get_current_language()
        languages = {}
        for lang in settings.PARLER_LANGUAGES[None]:
            code = lang["code"]
            language = {
                **lang,
                "current": code == current_language,
                "untranslated": code not in active_languages,
                "label": languages_labels.get(code) or code,
                "code": code,
            }
            languages[code] = language
        return languages
