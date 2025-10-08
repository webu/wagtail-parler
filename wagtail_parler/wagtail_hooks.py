from django.templatetags.static import static
from django.utils.html import format_html

from wagtail import hooks


@hooks.register("insert_global_admin_js")
def global_admin_js() -> str:
    return format_html(
        '<script src="{}" type="text/javascript"></script>', static("wagtail_parler/js/admin.js")
    )
