# Future imports
from __future__ import annotations

# Standard libs
import sys
from typing import Dict


class AppSettings:
    def __init__(self) -> None:
        # Django imports
        from django.conf import settings

        self.settings = settings
        self.__name__ = __name__

    @property
    def HEADINGS_CONF(self) -> Dict:
        _translation_status = getattr(self.settings, "WAGTAIL_PARLER_TRANSLATION_STATUS", {}) or {}
        _default_heading = getattr(
            self.settings, "WAGTAIL_PARLER_DEFAULT_TAB_HEADING", "%(locale)s"
        )

        return {
            "creating": {
                "label": _default_heading,
                "status": _translation_status.get("creating", ""),
            },
            "translated": {
                "label": getattr(
                    self.settings,
                    "WAGTAIL_PARLER_DEFAULT_TAB_HEADING_TRANSLATED",
                    _default_heading + " %(status)s",
                ),
                "status": _translation_status.get("translated", "🟢"),
            },
            "untranslated": {
                "label": getattr(
                    self.settings,
                    "WAGTAIL_PARLER_DEFAULT_TAB_HEADING_UNTRANSLATED",
                    _default_heading + " %(status)s",
                ),
                "status": _translation_status.get("untranslated", "🔴"),
            },
        }


# Ugly? Guido recommends this himself ...
# http://mail.python.org/pipermail/python-ideas/2012-May/014969.html
app_settings = AppSettings()
app_settings.__name__ = __name__
sys.modules[__name__] = app_settings  # type: ignore
