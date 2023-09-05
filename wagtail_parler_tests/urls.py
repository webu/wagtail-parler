# Django imports
from django.conf.urls.i18n import i18n_patterns
from django.urls import include
from django.urls import path

# Third Party
from wagtail import urls as wagtail_urls
from wagtail.admin import urls as wagtailadmin_urls

urlpatterns = i18n_patterns(
    path("cms/", include(wagtailadmin_urls)),
    path("", include(wagtail_urls)),
)
