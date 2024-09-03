# Standard libs
import os

# Third Party
from wagtail.test.settings import *  # lazy settings ^_^

BASE_PATH = os.path.join(os.path.dirname(__file__), "..")

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True
TIME_ZONE = "Europe/Paris"

# add our apps and remove wagtail test apps
INSTALLED_APPS = [
    "wagtail_parler",
    "wagtail_parler_tests",
    "parler",
    "wagtail_modeladmin",
] + [app for app in INSTALLED_APPS if not app.startswith("wagtail.test")]

MIDDLEWARE = [m for m in MIDDLEWARE if not m.startswith("wagtail.test")]  # remove test middleware
TEMPLATES.pop(1)  # remove jinja via wagtail.test dir
TEMPLATES[0]["OPTIONS"]["context_processors"] = [
    p for p in TEMPLATES[0]["OPTIONS"]["context_processors"] if not p.startswith("wagtail.test")
]
WAGTAILADMIN_RICH_TEXT_EDITORS.pop("custom")  # remove testapp rich_text CustomRichTextArea
ROOT_URLCONF = "wagtail_parler_tests.urls"

AUTH_USER_MODEL = "auth.User"
WAGTAIL_USER_CUSTOM_FIELDS = []
ALLOWED_HOSTS = ["*"]
DEBUG = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "root": {"level": "WARNING", "handlers": ["console"]},
    "handlers": {
        "console": {
            "level": "WARNING",
            "class": "logging.StreamHandler",
        },
        "null": {"class": "logging.NullHandler"},
    },
}
LANGUAGES = [
    ("fr", "French"),
    ("en", "English"),
    ("es", "Spanish"),
]
LANGUAGE_CODE = "fr"
PARLER_LANGUAGES = {
    None: (
        {"code": "fr"},
        {"code": "en"},
        {"code": "es"},
    ),
    "default": {
        "fallbacks": [LANGUAGE_CODE],
    },
}
PARLER_DEFAULT_LANGUAGE_CODE = LANGUAGE_CODE
