# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
from importlib.metadata import PackageNotFoundError, version as get_version
from pathlib import Path

# Make the package importable without installation (local builds);
# on Read the Docs the package is also pip-installed (see .readthedocs.yaml).
DOCS_SOURCE = Path(__file__).resolve().parent
REPO_ROOT = DOCS_SOURCE.parents[1]
sys.path.insert(0, str(REPO_ROOT))

on_rtd = os.environ.get('READTHEDOCS') == 'True'

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'aeronet_visu'
copyright = '2018-2026, Tristan Harmel'
author = 'Tristan Harmel'
# version defined in aeronet_visu/__init__.py (read by pyproject.toml)
try:
    release = get_version('aeronet_visu')
except PackageNotFoundError:
    release = 'dev'
version = '.'.join(release.split('.')[:2])
today_fmt = '%Y-%m-%d'

# -- General configuration ---------------------------------------------------

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'sphinx.ext.mathjax',
    'sphinx.ext.todo',
    'sphinx.ext.viewcode',
    'sphinx_copybutton',
    'myst_parser',
]

templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ['_build', '_readme.md', '_extra', 'Thumbs.db', '.DS_Store']

# -- Autodoc / autosummary ---------------------------------------------------

autosummary_generate = True
autoclass_content = 'class'
autodoc_typehints = 'description'
# 'members' is set in the autosummary templates (_templates/) to avoid
# documenting objects twice
autodoc_default_options = {
    'member-order': 'bysource',
    'show-inheritance': True,
}
# deprecated package imported (but unused) by visu_main
autodoc_mock_imports = ['dash_table_experiments']

# docstrings use the reST field lists (:param:, :return:), which napoleon
# leaves untouched; NumPy-style docstrings are also supported
napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_use_rtype = False

todo_include_todos = True

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'numpy': ('https://numpy.org/doc/stable', None),
    'pandas': ('https://pandas.pydata.org/docs', None),
    'matplotlib': ('https://matplotlib.org/stable', None),
}

# -- Options for HTML output -------------------------------------------------

html_theme = 'sphinx_book_theme'
pygments_style = 'sphinx'

html_theme_options = {
    'repository_url': 'https://github.com/Tristanovsk/aeronet_visu',
    'repository_branch': 'master',
    'path_to_docs': 'docs/source',
    'use_repository_button': True,
    'use_issues_button': True,
    'use_edit_page_button': True,
    'use_download_button': True,
    'navigation_with_keys': True,
    'show_toc_level': 2,
    'secondary_sidebar_items': ['page-toc', 'edit-this-page'],
}

html_title = 'aeronet_visu'

html_static_path = ['_static']
# files copied as is to the root of the HTML output (static AERONET-OC dashboard)
html_extra_path = ['_extra']
html_show_sourcelink = False
html_last_updated_fmt = today_fmt

htmlhelp_basename = 'aeronet_visu_doc'

# -- MyST (Markdown) ---------------------------------------------------------

myst_enable_extensions = [
    'colon_fence',
    'deflist',
    'dollarmath',
    'html_admonition',
    'html_image',
    'linkify',
    'replacements',
    'smartquotes',
]
