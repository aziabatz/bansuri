import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(".."))

# Project information
project = "Bansuri"
copyright = "2026, Ahmed.ZZ (Blackburn)"
author = "Blackburn (Ahmed.ZZ)"
release = "0.1.0"
version = "0.1"

# Extensions
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx.ext.todo",
    "sphinx.ext.autosectionlabel",
    "sphinx_rtd_theme",
    "sphinx_design",
    "sphinxcontrib.mermaid",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "*.egg-info"]

# HTML Theme Configuration
html_theme = "sphinx_rtd_theme"
html_theme_options = {
    # Read the Docs theme options
    "logo_only": False,
    "display_version": True,
    "prev_next_buttons_location": "both",
    "style_external_links": True,
    
    # Colors and styling
    "color_primary": "#1f77b4",
    "color_secondary": "#ff7f0e",
    
    # Typography
    "collapse_navigation": False,
    "sticky_navigation": True,
    "navigation_depth": 4,
    
    # Sidebar
    "includehidden": True,
}

html_static_path = ["_static"]
html_favicon = "image.png"

# Logo
html_logo = "image.png"

# CSS customization
html_css_files = [
    "custom.css",
]

# Syntax highlighting
pygments_style = "sphinx"
highlight_language = "python"

# Napoleon settings (for docstring parsing)
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = False
napoleon_type_aliases = None
napoleon_attr_annotations = True

# Autodoc settings
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": False,
    "show-inheritance": True,
}

# Autosectionlabel settings
autosectionlabel_prefix_document = True

# Todo settings
todo_include_todos = True

# Mermaid diagram settings
mermaid_init_js = """
mermaid.initialize({
  'securityLevel': 'loose',
  'theme': 'default'
});
"""