# Future imports
from __future__ import annotations

# Standard libs
from typing import Optional
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Union
    from django.db.models import Model
    from wagtail.admin.panels import Panel

# Third Party
from wagtail import VERSION as WAGTAIL_VERSION
from wagtail.snippets.models import register_snippet as wagtail_register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet


def register_snippet(
    registerable: Union[Model, SnippetViewSet], viewset: Optional[SnippetViewSet] = None
) -> None:
    if WAGTAIL_VERSION < (5, 0) and hasattr(registerable, "model"):
        wagtail_register_snippet(registerable.model, viewset=registerable)
    else:
        wagtail_register_snippet(registerable, viewset)


class CompatibleSnippetViewSetMixin(SnippetViewSet):
    pass


if WAGTAIL_VERSION < (5, 0):
    # Third Party
    from wagtail.admin.viewsets import viewsets
    from wagtail.contrib.modeladmin.options import ModelAdmin
    from wagtail.snippets.views.snippets import CreateView
    from wagtail.snippets.views.snippets import EditView

    def get_edit_handler(self: CompatibleSnippetViewSetMixin) -> Panel:
        return ModelAdmin.get_edit_handler(self)

    class CompatiblePanelViewMixin:
        def get_panel(self: CreateView) -> Panel:
            return next(
                viewset.get_edit_handler()
                for viewset in viewsets.viewsets
                if viewset.model is self.model
            )

    CompatibleSnippetViewSetMixin.add_view_class = type(
        "CreateView", (CompatiblePanelViewMixin, CreateView), {}
    )
    CompatibleSnippetViewSetMixin.edit_view_class = type(
        "EditView", (CompatiblePanelViewMixin, EditView), {}
    )
    CompatibleSnippetViewSetMixin.get_edit_handler = get_edit_handler
    CompatibleSnippetViewSetMixin.get_form_fields_exclude = lambda self: []
