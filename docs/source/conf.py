# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information


# Standard libs
import os
import sys

import django

sys.path.insert(0, os.path.abspath("../.."))
os.environ["DJANGO_SETTINGS_MODULE"] = "tests.settings"
django.setup()


from wagtail_modeladmin_parler import __version__ as wmp_version  # noqa

project = "Wagtail ModelAdmin Parler"
copyright = "2023, Webu"
author = "Webu"
release = wmp_version

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    # "sphinx.ext.intersphinx",
    # "sphinx.ext.viewcode",
    # "sphinx.ext.napoleon",
    "myst_parser",
    "sphinx_rtd_theme",
]

templates_path = ["_templates"]
exclude_patterns = []
autodoc_mock_imports = ["django"]

source_suffix = {
    ".rst": "restructuredtext",
    ".txt": "markdown",
    ".md": "markdown",
}

autodoc_default_options = {
    "member-order": "bysource",
    "undoc-members": True,
    "private-members": True,
}
myst_heading_anchors = 3

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
