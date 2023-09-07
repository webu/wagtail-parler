# Standard libs
import importlib
from typing import Optional
from typing import Tuple
import warnings

# Django imports
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

# Third Party
from wagtail.blocks.base import Block


class WagtailParlerConfig(AppConfig):
    name = "wagtail_parler"
    verbose_name = _("Wagtail Parler 🧀 🐦")

    def ready(self) -> None:
        if Block.__reduce__.__qualname__ == "object.__reduce__":
            """
            Monkey Patch wagtail to be able to Pickle Blocks.
            FIXME: remove this when related PR will be merged into wagtail.
            It's required when parler cache translations which can have
            StreamValue fields with Blocks as values.
            If Block or it's bases (but object) don't have any __reduce__ method,
            we need one to be able to Pickle instances of Blocks.
            """

            def block_reduce(self: Block) -> Tuple:
                path, args, kwargs = self.deconstruct()
                return unreduce, (path, (args, kwargs))

            Block.__reduce__ = block_reduce
        else:  # pragma: no cover
            warnings.warn(
                "Monkey Patch `block_reduce` is deprecated with this version of Wagtail",
                DeprecationWarning,
                stacklevel=2,
            )


def unreduce(path: str, args_and_kwargs: Optional[Tuple] = None) -> object:
    path_part = path.rsplit(".", 1)
    module = importlib.import_module(path_part[0])
    cls = getattr(module, path_part[1])
    args: Tuple = tuple()
    kwargs = {}
    if args_and_kwargs and len(args_and_kwargs) >= 1:
        args = args_and_kwargs[0]
        if len(args_and_kwargs) >= 2:
            kwargs = args_and_kwargs[1]
    return cls(*args, **kwargs)  # type: ignore
