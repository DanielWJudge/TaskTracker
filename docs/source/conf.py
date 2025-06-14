# -- Path setup --------------------------------------------------------------
import os
import sys

sys.path.insert(0, os.path.abspath("../../src"))


# -- Project information -----------------------------------------------------
project = "Momentum"
copyright = "2023, Momentum Contributors"
author = "Momentum Contributors"


# -- General configuration ---------------------------------------------------
extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosummary",
    "sphinx.ext.viewcode",
    "sphinx_autodoc_typehints",
    "sphinx_copybutton",
    "sphinxcontrib.autoprogram",
]

myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "html_admonition",
    "html_image",
    "linkify",
    "substitution",
    "tasklist",
]

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of built-in themes.
html_theme = "furo"


# -- Options for autodoc -----------------------------------------------------
autodoc_member_order = "bysource"
autodoc_typehints = "description"
autosummary_generate = True


# -- Options for man page output ---------------------------------------------
man_pages = [
    ("index", "momentum", "Momentum Documentation", ["Momentum Contributors"], 1)
]


# -- Options for GitHub Pages ------------------------------------------------
html_baseurl = "https://DanielWJudge.github.io/momentum/"


# -- Custom sidebar templates, must be a dictionary that maps document names
# to template names.
# This is required for the alabaster theme to work properly
# html_sidebars = {}
