# Future imports
from __future__ import annotations

# Standard libs
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

# Django imports
from django.http import HttpResponse
from django.test import Client
from django.test import TestCase
from django.test.utils import override_settings
from django.utils.translation import gettext_lazy as _

# Third Party
from bs4 import BeautifulSoup
from bs4 import NavigableString
from bs4 import Tag
from wagtail_parler_tests.models import Food

__all__ = ["WagtailParlerModelAdminTests", "WagtailParlerSnippetsTests"]

RecusiveListStrOrTuple = List[Union[str, Tuple[str, "RecusiveListStrOrTuple"]]]


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
                "hide_untranslated": False,
            },
        },
    )
}


class WagtailParlerBaseTests:
    fixtures = ["test_fixtures.json"]
    admin_interface = None
    matching_actions = {}

    def setUp(self: TestCase) -> None:
        self.client = Client(enforce_csrf_checks=False)
        self.client.login(username="admin", password="admin")
        return super().setUp()

    def _check_tabs(self: TestCase, soup: BeautifulSoup, expected_tabs: List[str]) -> None:
        tabs_list = soup.find("div", class_="w-tabs__list")
        assert isinstance(tabs_list, Tag)
        tabs = tabs_list.find_all("a")
        self.assertEqual(len(tabs), len(expected_tabs))
        texts = []
        # could be shorter with texts = [next(tab.children).string.strip() for tab in tabs]
        # but wagtail < 4.2 add errors BEFORE the string :(
        for tab in tabs:
            text = ""
            for child in tab.children:
                if isinstance(child, NavigableString) and child.text.strip():
                    text += child.text.strip()
            texts.append(text)
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
                raise Exception("section#%s not found" % expected_section_id)
            if sub_sections:
                self._check_sections(section, sub_sections)

    def _check_fields(self: TestCase, container: Tag, expected_fields: Dict[str, dict]) -> None:
        fields_positions = []
        for field_name, opts in expected_fields.items():
            tag_name = opts.get("tag_name", "input")
            input_tag = container.find(tag_name, id="id_%s" % field_name)
            if not isinstance(input_tag, Tag):
                raise Exception("Field %s#%s not found" % (tag_name, field_name))
            self.assertEqual(input_tag["name"], field_name)
            fields_positions.append((field_name, (input_tag.sourceline, input_tag.sourcepos)))
            for attr_name, attr_value in opts.items():
                if attr_name == "tag_name":
                    continue
                elif attr_value in (True, False, None):
                    self.assertEqual(attr_name in input_tag.attrs, attr_value)
                elif attr_name == "value":
                    if opts.get("tag_name", None) == "textarea":
                        value = ...
                    else:
                        value = input_tag["value"]
                    self.assertEqual(value, attr_value)
                else:
                    self.assertEqual(input_tag[attr_name], attr_value)
        # checks fields order
        fields_as_found_order = [
            field_name for field_name, pos in sorted(fields_positions, key=lambda x: x[1])
        ]
        self.assertEqual(fields_as_found_order, list(expected_fields))

    def _get_admin_soup(self, app_label, model_name, action=None, pk=None):
        url = self._get_admin_url(app_label, model_name, action, pk)
        return self._get_soup(url)

    def _get_admin_url(self, app_label, model_name, action=None, pk=None):
        if self.admin_interface == "modeladmin":
            url = f"/fr/cms/{app_label}/{model_name}/"
        elif self.admin_interface == "snippets":
            url = f"/fr/cms/snippets/{app_label}/{model_name}/"
        else:
            raise Exception("bad admin_interface: %s" % self.admin_interface)
        if action:
            url += "%s/" % self.matching_actions.get(action, action)
            if pk:
                url += "%d/" % pk
        return url

    def _get_soup(self: TestCase, path, expected_status: int = 200) -> BeautifulSoup:
        resp = self.client.get(path)
        assert isinstance(resp, HttpResponse)
        if expected_status:
            self.assertEqual(resp.status_code, 200)
        return BeautifulSoup(resp.content, "html.parser")

    def test_auto_tabs(self) -> None:
        soup = self._get_admin_soup("wagtail_parler_tests", "food", "edit", 1)
        expected_tabs = [
            "Untranslated data",
            "French 🟢",
            "English 🟢",
            "Spanish 🔴",
        ]
        self._check_tabs(soup, expected_tabs)

    @override_settings(**EXTRA_SETTINGS["CUSTOM_TABS_LABELS"])
    def test_custom_tabs_labels(self) -> None:
        soup = self._get_admin_soup("wagtail_parler_tests", "food", "edit", 1)
        expected_tabs = [
            "Untranslated data",
            "🇫🇷 Français 🟢",
            "🇬🇧 Anglais 🟢",
            "🇪🇸 Espagnol 🔴",
        ]
        self._check_tabs(soup, expected_tabs)

    def test_panels_from_model(self) -> None:
        soup = self._get_admin_soup("wagtail_parler_tests", "foodwithpanelsinsidemodel", "add")
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
        soup = self._get_admin_soup("wagtail_parler_tests", "foodwithedithandler", "add")
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
        soup = self._get_admin_soup("wagtail_parler_tests", "foodwithspecificedithandler", "add")
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
            main_id = f"parler_translations_{locale_code}"
            childsection = f"panel-child-{main_id}-child-html_content"
            self._check_tab(
                soup,
                main_id,
                [
                    #  panel-child-fr_french-ctranslations_fr_name-section
                    f"panel-child-{main_id}-translations_{locale_code}_name-section",
                    (
                        f"panel-child-{main_id}-html_content-section",
                        [
                            f"{childsection}-translations_{locale_code}_summary-section",
                            f"{childsection}-translations_{locale_code}_content-section",
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

    def test_create_translations(self: TestCase) -> None:
        """checks we can create new translations for an instance"""
        jelly = Food.objects.get(pk=1)
        self.assertNotIn("es", jelly.get_available_languages())
        edit_url = self._get_admin_url("wagtail_parler_tests", "food", "edit", 1)
        list_url = self._get_admin_url("wagtail_parler_tests", "food")
        data = {
            "yum_rating": "3",
            "vegetarian": "on",
            "vegan": "on",
            "translations_fr_name": "Gelée",
            "translations_fr_summary": "Summary FR",
            "translations_fr_content": "Content FR",
            "translations_fr_qa-count": 1,
            "translations_fr_qa-0-deleted": "",
            "translations_fr_qa-0-order": 0,
            "translations_fr_qa-0-type": "QaBlock",
            "translations_fr_qa-0-id": "8c23eadb-60e0-4271-831d-332dd33ce36b",
            "translations_fr_qa-0-value-text": "Pouvez-vous emmener une « Jelly » dans un avion ?",
            # EN
            "translations_en_name": "Jelly",
            "translations_en_summary": "Summary EN",
            "translations_en_content": "Content EN",
            "translations_en_qa-count": 1,
            "translations_en_qa-0-deleted": "",
            "translations_en_qa-0-order": 0,
            "translations_en_qa-0-type": "QaBlock",
            "translations_en_qa-0-id": "bbc8985f-f249-4ce2-9cab-cee966ffb4aa",
            "translations_en_qa-0-value-text": "Can you bring a Jelly in a plane ?",
            # ES
            "translations_es_name": "Jelly ES",
            "translations_es_qa-count": 1,
            "translations_es_qa-0-deleted": "",
            "translations_es_qa-0-order": 0,
            "translations_es_qa-0-type": "QaBlock",
            "translations_es_qa-0-id": "d2d0ab62-6946-4764-947a-77f58ebfd7ae",
            "translations_es_qa-0-value-text": "QA ES",
        }
        resp = self.client.post(edit_url, data)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, list_url)
        jelly = Food.objects.get(pk=1)
        self.assertIn("es", jelly.get_available_languages())
        self.assertEqual(jelly.get_translation("es").name, "Jelly ES")
        self.assertEqual(
            jelly.get_translation("es").qa.raw_data[0]["value"]["text"],
            "QA ES",
        )

    def test_update_translations(self: TestCase) -> None:
        """checks we can update existing translations for an instance"""
        jelly = Food.objects.get(pk=1)
        self.assertIn("en", jelly.get_available_languages())
        self.assertEqual(jelly.get_translation("en").name, "Jelly")
        edit_url = self._get_admin_url("wagtail_parler_tests", "food", "edit", 1)
        list_url = self._get_admin_url("wagtail_parler_tests", "food")
        data = {
            "yum_rating": "3",
            "vegetarian": "on",
            "vegan": "on",
            "translations_fr_name": "Gelée",
            "translations_fr_summary": "Summary FR",
            "translations_fr_content": "Content FR",
            "translations_fr_qa-count": 1,
            "translations_fr_qa-0-deleted": "",
            "translations_fr_qa-0-order": 0,
            "translations_fr_qa-0-type": "QaBlock",
            "translations_fr_qa-0-id": "8c23eadb-60e0-4271-831d-332dd33ce36b",
            "translations_fr_qa-0-value-text": "Pouvez-vous emmener une « Jelly » dans un avion ?",
            # EN
            "translations_en_name": "Jelly updated",
            "translations_en_summary": "Summary EN",
            "translations_en_content": "Content EN",
            "translations_en_qa-count": 1,
            "translations_en_qa-0-deleted": "",
            "translations_en_qa-0-order": 0,
            "translations_en_qa-0-type": "QaBlock",
            "translations_en_qa-0-id": "bbc8985f-f249-4ce2-9cab-cee966ffb4aa",
            "translations_en_qa-0-value-text": "Can you bring a Jelly in a plane ? Updated",
            # ES
            "translations_es_qa-count": 0,
        }
        resp = self.client.post(edit_url, data)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, list_url)
        jelly = Food.objects.get(pk=1)
        self.assertEqual(jelly.get_translation("en").name, "Jelly updated")
        self.assertEqual(
            jelly.get_translation("en").qa.raw_data[0]["value"]["text"],
            "Can you bring a Jelly in a plane ? Updated",
        )
        self.assertNotIn("es", jelly.get_available_languages())

    def test_delete_translations(self: TestCase) -> None:
        """checks we can delete existing translations for an instance"""
        jelly = Food.objects.get(pk=1)
        self.assertIn("en", jelly.get_available_languages())
        self.assertEqual(jelly.get_translation("en").name, "Jelly")
        edit_url = self._get_admin_url("wagtail_parler_tests", "food", "edit", 1)
        list_url = self._get_admin_url("wagtail_parler_tests", "food")
        data = {
            "yum_rating": "3",
            "vegetarian": "on",
            "vegan": "on",
            "translations_fr_name": "Gelée",
            "translations_fr_summary": "Summary FR",
            "translations_fr_content": "Content FR",
            "translations_fr_qa-count": 0,
            "translations_en_qa-count": 0,
            "translations_es_qa-count": 0,
        }
        resp = self.client.post(edit_url, data)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, list_url)
        jelly = Food.objects.get(pk=1)
        self.assertNotIn("en", jelly.get_available_languages())

    def test_delete_instance(self: TestCase) -> None:
        """checks we can delete existing translations for an instance"""
        delete_url = self._get_admin_url("wagtail_parler_tests", "food", "delete", 1)
        list_url = self._get_admin_url("wagtail_parler_tests", "food")
        resp = self.client.post(delete_url)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, list_url)
        with self.assertRaises(Food.DoesNotExist):
            Food.objects.get(pk=1)

    def test_required_translation(self) -> None:
        """checks that translation matching the default locale is required"""
        soup = self._get_admin_soup("wagtail_parler_tests", "food", "add")
        self._check_tab(
            soup,
            "parler_translations_fr",
            [
                "panel-child-parler_translations_fr-translations_fr_name-section",
            ],
            {
                "translations_fr_name": {"required": True},
                "translations_fr_summary": {"tag_name": "textarea", "required": True},
                "translations_fr_content": {"tag_name": "textarea", "required": True},
            },
        )


class WagtailParlerModelAdminTests(WagtailParlerBaseTests, TestCase):
    admin_interface = "modeladmin"
    matching_actions = {"add": "create"}


class WagtailParlerSnippetsTests(WagtailParlerBaseTests, TestCase):
    admin_interface = "snippets"
