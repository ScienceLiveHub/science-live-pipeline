# Simplified Sphinx configuration
import os
import sys
sys.path.insert(0, os.path.abspath('..'))

# Project information
project = 'Science Live Pipeline'
copyright = '2024, Science Live Team'
author = 'Science Live Team'
release = '0.0.1'

# Extensions - use only myst_nb to avoid conflicts
extensions = [
    'myst_nb',           # This handles both .md files AND notebooks
    'sphinx_autodoc2', 
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx_copybutton', 
    'sphinx.ext.intersphinx',
    'sphinx_design',     # For grid directive
    'sphinxcontrib.mermaid',
]

# Suppress the harmless warnings about duplicate registration
suppress_warnings = [
    'app.add_role',
    'app.add_directive',
]

# MyST Parser settings (configured through myst_nb)
myst_enable_extensions = [
    'colon_fence',
    'deflist',
    'fieldlist',
    'html_admonition',
    'tasklist',
    'attrs_block',
    'substitution',
    'linkify',
]

# Enable additional MyST features
myst_fence_as_directive = [
    "mermaid",  # Enable mermaid diagrams
]

# autodoc2 settings
autodoc2_packages = ["../science_live"]

# Parse docstrings as MyST markdown
autodoc2_docstring_parser_regexes = [
    (r".*", "myst"),
]

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = False

# MyST-NB settings
nb_execution_mode = "off"  # Don't execute notebooks during build

# Intersphinx mapping
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "pandas": ("https://pandas.pydata.org/docs/", None),
}

# HTML output
html_theme = 'sphinx_book_theme'
html_title = 'Science Live Pipeline'

# Files to exclude
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# Let myst_nb handle file type registration automatically
# Don't manually set source_suffix when using myst_nb

# Add CSS file
html_static_path = ['_static']
html_css_files = ['custom.css']
