# Future imports
from __future__ import annotations

# Standard libs
from copy import copy
from importlib import reload
import time
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union
from typing import cast

RecusiveListStrOrTuple = List[Union[str, Tuple[str, "RecusiveListStrOrTuple"]]]
# Django imports
from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.template import Context
from django.template import Template
from django.template.loader import get_template
from django.test import Client
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.utils import translation
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

# Third Party
from bs4 import BeautifulSoup
from bs4 import NavigableString
from bs4 import Tag

__all__ = ["WMPTests"]

# wagtail / parler
from wmp_tests.models import Food

EXTRA_SETTINGS = {
    "CUSTOM_TABS_LABELS": dict(
        WAGTAIL_PARLER_DEFAULT_TAB_HEADING=_("%(utf8_flag)s %(translated_label)s"),
        WAGTAIL_PARLER_DEFAULT_TAB_HEADING_UNSTRANLATED=_("%(utf8_flag)s %(translated_label)s 🔴"),
        WAGTAIL_PARLER_DEFAULT_TAB_HEADING_TRANLATED=_("%(utf8_flag)s %(translated_label)s 🟢"),
        PARLER_LANGUAGES={
            None: (
                {
                    "code": "fr",
                    "translated_label": _("Français"),  # custom add
                    "untranslated_label": "Français",  # custom add
                    "utf8_flag": "🇫🇷",  # custom add
                },
                {
                    "code": "en",
                    "translated_label": _("Anglais"),  # custom add
                    "untranslated_label": "English",  # custom add
                    "utf8_flag": "🇬🇧",  # custom add
                },
                {
                    "code": "es",
                    "translated_label": _("Espagnol"),  # custom add
                    "untranslated_label": "Español",  # custom add
                    "utf8_flag": "🇪🇸",  # custom add
                },
            ),
            "default": {
                "fallbacks": ["fr"],
                "hide_untranslated": False,  # the default; let .active_translations() return fallbacks too.
            },
        },
    )
}


class WMPTests(TestCase):
    fixtures = ["test_fixtures.json"]

    def setUp(self) -> None:
        self.client = Client()
        self.client.login(username="admin", password="admin")
        return super().setUp()

    def _check_tabs(self, soup: BeautifulSoup, expected_tabs: List[str]) -> None:
        tabs_list = soup.find("div", class_="w-tabs__list")
        assert isinstance(tabs_list, Tag)
        tabs = tabs_list.find_all("a")
        self.assertEqual(len(tabs), len(expected_tabs))
        texts = [next(tab.children).string.strip() for tab in tabs]
        self.assertEqual(texts, expected_tabs)

    def _check_tab(
        self,
        soup: BeautifulSoup,
        tab_name: str,
        expected_sections: Optional[RecusiveListStrOrTuple] = None,
        expected_fields: Optional[Dict[str, dict]] = None,
    ) -> None:
        tab = soup.find("section", id="tab-%s" % tab_name)
        if not isinstance(tab, Tag):
            raise Exception("section#tab-%s not found" % tab_name)
        if expected_sections is not None:
            self._check_sections(tab, expected_sections)
        if expected_fields:
            self._check_fields(tab, expected_fields)

    def _check_sections(self, container: Tag, expected_sections: RecusiveListStrOrTuple) -> None:
        for expected_section in expected_sections:
            if isinstance(expected_section, tuple):
                expected_section_id, sub_sections = expected_section[0], expected_section[1]
            else:
                expected_section_id = expected_section
                sub_sections = None
            section = container.find("section", id=expected_section_id)
            if not isinstance(section, Tag):
                raise Exception("section#tab-%s not found" % expected_section_id)
            if sub_sections:
                self._check_sections(section, sub_sections)

    def _check_fields(self, container: Tag, expected_fields: Dict[str, dict]) -> None:
        fields_positions = []
        for field_name, opts in expected_fields.items():
            tag_name = opts.get("tag_name", "input")
            input_tag = container.find(tag_name, id="id_%s" % field_name)
            if not isinstance(input_tag, Tag):
                raise Exception("Field %s#%s not found" % (tag_name, field_name))
            self.assertEqual(input_tag["name"], field_name)
            fields_positions.append((field_name, (input_tag.sourceline, input_tag.sourcepos)))
            if "type" in opts:
                self.assertEqual(input_tag["type"], opts["type"])
            if "value" in opts:
                if opts.get("type", None) == "textarea":
                    value = ...
                else:
                    value = input_tag["value"]
                self.assertEqual(value, opts["value"])
        # checks fields order
        fields_as_found_order = [
            field_name for field_name, pos in sorted(fields_positions, key=lambda x: x[1])
        ]
        self.assertEqual(fields_as_found_order, list(expected_fields))

    def _get_soup(self, path, expected_status: int = 200) -> BeautifulSoup:
        resp = self.client.get(path)
        assert isinstance(resp, HttpResponse)
        if expected_status:
            self.assertEqual(resp.status_code, 200)
        return BeautifulSoup(resp.content, "html.parser")

    def test_auto_tabs(self) -> None:
        soup = self._get_soup("/fr/cms/wmp_tests/food/edit/1/")
        expected_tabs = [
            "Untranslated data",
            "French 🟢",
            "English 🟢",
            "Spanish 🔴",
        ]
        self._check_tabs(soup, expected_tabs)

    @override_settings(**EXTRA_SETTINGS["CUSTOM_TABS_LABELS"])
    def test_custom_tabs_labels(self) -> None:
        soup = self._get_soup("/fr/cms/wmp_tests/food/edit/1/")
        expected_tabs = [
            "Untranslated data",
            "🇫🇷 Français 🟢",
            "🇬🇧 Anglais 🟢",
            "🇪🇸 Espagnol 🔴",
        ]
        self._check_tabs(soup, expected_tabs)

    def test_panels_from_model(self) -> None:
        soup = self._get_soup("/fr/cms/wmp_tests/foodwithpanelsinsidemodel/create/")
        expected_tabs = [
            "Untranslated data",
            "French",
            "English",
            "Spanish",
        ]
        self._check_tabs(soup, expected_tabs)
        self._check_tab(
            soup,
            "untranslated_data",
            [
                "panel-child-untranslated_data-yum_rating-section",
                (
                    "panel-child-untranslated_data-regime-section",
                    [
                        "panel-child-untranslated_data-child-regime-vegetarian-section",
                        "panel-child-untranslated_data-child-regime-vegan-section",
                    ],
                ),
            ],
            {
                "yum_rating": {},
                "vegetarian": {},
                "vegan": {},
            },
        )

    def test_edit_handler_from_model(self) -> None:
        soup = self._get_soup("/fr/cms/wmp_tests/foodwithedithandler/create/")
        expected_tabs = [
            "Untranslated data",
            "French",
            "English",
            "Spanish",
        ]
        self._check_tabs(soup, expected_tabs)
        self._check_tab(
            soup,
            "untranslated_data",
            [
                "panel-child-untranslated_data-yum_rating-section",
                (
                    "panel-child-untranslated_data-regime-section",
                    [
                        "panel-child-untranslated_data-child-regime-vegetarian-section",
                        "panel-child-untranslated_data-child-regime-vegan-section",
                    ],
                ),
            ],
            {
                "yum_rating": {},
                "vegetarian": {},
                "vegan": {},
            },
        )

    def test_edit_handler_from_modeladmin(self) -> None:
        soup = self._get_soup("/fr/cms/wmp_tests/foodwithspecificedithandler/create/")
        expected_tabs = [
            "Score de miam",
            "fr: French",
            "en: English",
            "es: Spanish",
            "Régime",
        ]
        self._check_tabs(soup, expected_tabs)
        self._check_tab(soup, "yum_rating", expected_fields={"yum_rating": {}})
        tabs = (
            ("fr", "french"),
            ("en", "english"),
            ("es", "spanish"),
        )
        for locale_code, locale_name in tabs:
            self._check_tab(
                soup,
                f"{locale_code}_{locale_name}",
                [
                    #  panel-child-fr_french-ctranslations_fr_name-section
                    f"panel-child-{locale_code}_{locale_name}-translations_{locale_code}_name-section",
                    (
                        f"panel-child-{locale_code}_{locale_name}-html_content-section",
                        [
                            f"panel-child-{locale_code}_{locale_name}-child-html_content-translations_{locale_code}_summary-section",
                            f"panel-child-{locale_code}_{locale_name}-child-html_content-translations_{locale_code}_content-section",
                        ],
                    ),
                ],
                {
                    f"translations_{locale_code}_name": {},
                    f"translations_{locale_code}_summary": {"tag_name": "textarea"},
                    f"translations_{locale_code}_content": {"tag_name": "textarea"},
                },
            )
        self._check_tab(
            soup,
            "regime",
            [
                "panel-child-regime-vegetarian-section",
                "panel-child-regime-vegan-section",
            ],
            {"vegetarian": {}, "vegan": {}},
        )

    def test_create_translations(self) -> None:
        """checks we can create new translations for an instance"""
        pass

    def test_update_translations(self) -> None:
        """checks we can update existing translations for an instance"""
        pass

    def test_delete_translations(self) -> None:
        """checks we can delete existing translations for an instance"""
        pass

    def test_required_translation(self) -> None:
        """checks that translation matching the default locale is required"""
        pass
