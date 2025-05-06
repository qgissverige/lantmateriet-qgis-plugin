# Documentation

This project uses [MkDocs](https://www.mkdocs.org/) to generate documentation from Markdown pages and docstrings (documentation in-code).

## Build documentation website

To build it:

```bash
uvx --with-requirements requirements/documentation.txt mkdocs build
```

Then open `site/index.html` in a web browser.

## Write documentation using live render

```bash
uvx --with-requirements requirements/documentation.txt mkdocs serve
```

Then open <http://localhost:8000/lantmateriet-qgis-plugin> in a web browser to see the HTML render updated when a file is saved.
