# Django imports
from django.apps import AppConfig

__all__ = ["WMPTestsConfig"]


class WMPTestsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "wmp_tests"
