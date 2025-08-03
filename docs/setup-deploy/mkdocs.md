# Welcome to MkDocs

For full documentation visit [mkdocs.org](https://www.mkdocs.org).

## Installation

``` {.pwsh file=.\install-mkdocs.ps1}
uv pip install mkdocs
uv pip install mkdocs-mermaid2-plugin
uv pip install mkdocs-material
uv pip install mkdocs-entangled-plugin
```

## Commands

* `mkdocs new [dir-name]` - Create a new project.
* `mkdocs serve` - Start the live-reloading docs server at http://127.0.0.1:8000/
* `mkdocs build` - Build the documentation site.
* `mkdocs -h` - Print help message and exit.

## Project layout

    mkdocs.yml    # The configuration file.
    docs/
        index.md  # The documentation homepage.
        ...       # Other markdown pages, images and other files.
