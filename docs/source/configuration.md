# Configuration

You can customise the labels of i18n tabs with 3 settings:

* `WAGTAIL_PARLER_DEFAULT_TAB_HEADING`
* `WAGTAIL_PARLER_DEFAULT_TAB_HEADING_UNSTRANLATED`
* `WAGTAIL_PARLER_DEFAULT_TAB_HEADING_TRANLATED`

First one is used when your instance is not yet created. The other ones 
(UNSTRANSLATED and TRANSLATED) are respectively use when your instance is saved and there is 
(or not) an existing translation for the lang displayed in the tab.

Those settings must be a string and can contain some string replacement. ex:

```python
WAGTAIL_PARLER_TRANSLATION_STATUS = {
    "creating": "",
    "untranslated": "🔴",
    "translated": "🟢",
}
WAGTAIL_PARLER_DEFAULT_TAB_HEADING = _("%(utf8_flag)s %(translated_label)s not saved")
WAGTAIL_PARLER_DEFAULT_TAB_HEADING_UNSTRANLATED = _("%(utf8_flag)s %(translated_label)s %(status)s exists")
WAGTAIL_PARLER_DEFAULT_TAB_HEADING_TRANLATED = _("%(utf8_flag)s %(translated_label)s %(status)s not exists")
```

String replacements are done with `locale` (locale label of the tab), `status` (see `WAGTAIL_PARLER_TRANSLATION_STATUS`) and the lang configuration from `PARLER_LANGUAGES`. 
For the exemple above, you MUST have `utf8_flag` and `translated_label` keys inside each lang
configuration set in `PARLER_LANGUAGES`:

```python

PARLER_LANGUAGES = {
    None: (
        {
            "code": "fr",
            "translated_label": _("Français"),  # custom add, lang label in current user language
            "untranslated_label": "Français",  # custom add, lang label in this language
            "utf8_flag": "🇫🇷",  # custom add, a flag of the main country using this lang
        },
        {
            "code": "en",
            "translated_label": _("Anglais"),  # custom add, lang label in current user language
            "untranslated_label": "English",  # custom add, lang label in this language
            "utf8_flag": "🇬🇧",  # custom add, a flag of the main country using this lang
        },
    ),
    "default": {
        "fallbacks": [LANGUAGE_CODE],
        "hide_untranslated": False,  # the default; let .active_translations() return fallbacks too.
    },
}
```
