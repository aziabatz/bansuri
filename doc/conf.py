import os
import sys

# Apuntar al directorio raíz del proyecto para encontrar el paquete 'bansuri'
sys.path.insert(0, os.path.abspath(".."))

project = "Bansuri"
copyright = "2026, Bansuri Contributors"
author = "Bansuri Contributors"
release = "1.0"

extensions = [
    "sphinx.ext.autodoc",  # Generar documentación desde docstrings
    "sphinx.ext.viewcode",  # Enlaces al código fuente
    "sphinx.ext.napoleon",  # Soporte para docstrings estilo Google/NumPy
    "sphinx.ext.todo",  # Soporte para notas TODO
    "sphinx.ext.autosectionlabel",  # Referencias automáticas a secciones
    "sphinx_rtd_theme",  # Tema Read the Docs
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# Tema visual (puedes cambiarlo a 'sphinx_rtd_theme' si lo instalas)
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
