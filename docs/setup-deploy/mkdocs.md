# MkDocs

MkDocs is a static site generator that's geared towards project documentation. It takes Markdown files and builds them into a static website.
For full documentation visit [mkdocs.org](https://www.mkdocs.org).

## Initial Installation

### Windows

``` {.pwsh file= setup/mkdocs.ps1}
uv pip install mkdocs
uv pip install mkdocs-mermaid2-plugin
uv pip install mkdocs-material
uv pip install mkdocs-entangled-plugin
```

### Linux Mint

``` {.bash file= setup/mkdocs.sh}
uv pip install mkdocs
uv pip install mkdocs-mermaid2-plugin
uv pip install mkdocs-material
uv pip install mkdocs-entangled-plugin
```

## Commands

* `mkdocs new [dir-name]` - Create a new project.
* `mkdocs serve` - Start the live-reloading docs server at http://127.0.0.1:8000/
* `mkdocs build` - Build the documentation site.
* `mkdocs gh-deploy` - Deploy site on the gh-pages branch: see site_url in config. 
* `mkdocs -h` - Print help message and exit.

## Configuration

``` {.yaml file= mkdocs.yml}
site_name: Gong system and apps for Vipassane centers
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
  features:
    - content.code.copy
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

Note: to use the 'material' theme, add '' under 'readthedocs'

## Project layout

    mkdocs.yml    # The configuration file.
    docs/
        index.md  # The documentation homepage.
        ...       # Other markdown pages, images and other files.
