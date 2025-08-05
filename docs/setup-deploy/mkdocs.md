# Welcome to MkDocs

For full documentation visit [mkdocs.org](https://www.mkdocs.org).

## Installation

``` {.pwsh file= setup/mkdocs.ps1}
uv pip install mkdocs
uv pip install mkdocs-mermaid2-plugin
uv pip install mkdocs-material
uv pip install mkdocs-entangled-plugin

```

## Configuration


``` {.yaml file= mkdocs.yml}
site_name: My Docs
site_url: https://s66erge.github.io/entan-mkdocs
repo_url: https://github.com/s66erge/entan-mkdocs

plugins:
  - search
  - entangled
  - mermaid2:
      arguments:
         securityLevel: 'loose' 

#extra_javascript:
#    - https://unpkg.com/mermaid/dist/mermaid.min.js

markdown_extensions:
  - pymdownx.superfences:
      custom_fences:
        - name: mermaid
          class: mermaid
          format: !!python/name:pymdownx.superfences.fence_code_format
#         format: !!python/name:mermaid2.fence_mermaid
  
theme:
  name: readthedocs
  name: material
  palette: 
    # Palette toggle for light mode
    #- scheme: default
    #  toggle:
    #    icon: material/brightness-7 
    #    name: Switch to dark mode

    # Palette toggle for dark mode
    - scheme: slate
      toggle:
        icon: material/brightness-4
        name: Switch to light mode

  watch:
  - docs

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
