# Building Bansuri Documentation

## Quick Start

Build the documentation locally:

```bash
cd doc
pip install -r requirements.txt
make clean html
```

The built documentation will be in `_build/html/index.html`

## Development Build

For development with auto-reload:

```bash
# Install sphinx-autobuild
pip install sphinx-autobuild

# Start auto-rebuild server
sphinx-autobuild . _build/html
```

Then open http://localhost:8000 in your browser.

## Full Build

```bash
# Clean previous builds
make clean

# Build HTML
make html

# Build PDF (requires LaTeX)
make latexpdf

# Build ePub
make epub
```

## Requirements

- Python 3.8+
- Sphinx 5.0+
- sphinx-rtd-theme 1.2+
- See `requirements.txt` for complete list

## Theme Customization

The documentation uses the **Read the Docs Theme** with custom styling:

- **Colors**: Blue primary (#1f77b4), Orange secondary (#ff7f0e)
- **CSS**: Custom styles in `_static/custom.css`
- **Layout**: Custom template in `_templates/layout.html`

### Modifying Styles

Edit `_static/custom.css` to customize:
- Color scheme
- Typography
- Code highlighting
- Responsive design
- Admonition styling

### Modifying Layout

Edit `_templates/layout.html` to customize:
- Page footer
- Meta tags
- Header elements
- Custom HTML

## Deployment

### ReadTheDocs (Recommended)

1. Push to GitHub
2. Connect repository to ReadTheDocs
3. Configure `.readthedocs.yml` if needed

### Manual Deployment

```bash
# Build HTML
make html

# Deploy _build/html/ to your web server
scp -r _build/html/* user@server:/var/www/docs/
```

## Configuration

Main configuration: `conf.py`

Key settings:
- `project`: Project name
- `html_theme`: Theme to use
- `html_theme_options`: Theme customization
- `extensions`: Sphinx extensions
- `html_css_files`: Custom CSS files

## Troubleshooting

### Build fails with "sphinx_design not found"

```bash
pip install sphinx-design
```

### Build fails with "sphinxcontrib.mermaid not found"

```bash
pip install sphinxcontrib-mermaid
```

### Styles not applied

Clear build cache:

```bash
make clean
make html
```

### Images not showing

Ensure images are in `_static/` and referenced correctly in RST files.

## Documentation Format

All docs are written in reStructuredText (.rst) format.

### Common Markup

```rst
# Heading 1
==========

## Heading 2
----------

### Heading 3
~~~~~~~~~~~~

**Bold text**

*Italic text*

``Inline code``

::

    Code block

.. code-block:: python

    # Python code with syntax highlighting
    print("Hello")

.. note::

    This is a note admonition

.. warning::

    This is a warning admonition

.. table::

   Header 1    Header 2
   =========   =========
   Cell 1      Cell 2
   Cell 3      Cell 4

:doc:`reference` - Link to another document
`External Link <https://example.com>`_
```

## Contributing to Documentation

1. Clone the repository
2. Create a branch: `git checkout -b docs/my-changes`
3. Edit `.rst` files in `doc/`
4. Build locally: `make html`
5. Check changes in `_build/html/`
6. Commit and push
7. Create a Pull Request

## Documentation Structure

```
doc/
├── index.rst                 # Main landing page
├── quickstart.rst           # Getting started guide
├── installation.rst         # Installation instructions
├── concepts.rst             # Core concepts
├── configuration.rst        # Configuration guide
├── reference.rst            # Parameter reference
├── usage.rst                # Usage examples
├── notifications.rst        # Notification features
├── custom-tasks.rst         # Custom task implementation
├── deployment.rst           # Deployment guide
├── troubleshooting.rst      # Troubleshooting
├── architecture.rst         # Architecture overview
├── advanced-config.rst      # Advanced configuration
├── contributing.rst         # Contributing guide
├── api.rst                  # API reference
├── conf.py                  # Sphinx configuration
├── _static/
│   └── custom.css          # Custom styles
├── _templates/
│   └── layout.html         # Custom layout
└── requirements.txt        # Python dependencies
```

## More Information

- [Sphinx Documentation](https://www.sphinx-doc.org)
- [Read the Docs Theme](https://sphinx-rtd-theme.readthedocs.io)
- [reStructuredText Primer](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html)
