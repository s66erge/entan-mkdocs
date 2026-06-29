# MkDocs

MkDocs is a static site generator that's geared towards project documentation. It takes Markdown files and builds them into a static website.
For full documentation visit [mkdocs.org](https://www.mkdocs.org).

## Initial Installation

### Windows

```pwsh
#| file:  setup/mkdocs.ps1 
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

```yaml
#| file:  mkdocs.yml 
site_name: Gong system and apps for Vipassane centers
site_url: https://s66erge.github.io/entan-mkdocs
repo_url: https://github.com/s66erge/entan-mkdocs

plugins:
  - search
#  - entangled
  - mermaid2:
      arguments:
         securityLevel: 'loose' 

markdown_extensions:
  - attr_list
  - md_in_html
  - toc:
      permalink: "#"
  - pymdownx.highlight:
      linenums: true 
      use_pygments: true
      anchor_linenums: true
      line_spans: __span
      pygments_lang_class: true
  #- pymdownx.inlinehilite
  - pymdownx.snippets
  - pymdownx.superfences:
      custom_fences:
        - name: mermaid
          class: mermaid
          format: !!python/name:pymdownx.superfences.fence_code_format
          #format: !!python/name:mermaid2.fence_mermaid

theme:
  #name: readthedocs
  name: material
  features:
    - content.code.annotate # (1)
    #- navigation.instant
    - navigation.top
    #- navigation.tab
    - navigation.path
    - content.code.copy
  # icon:
    # annotation: material/plus-circle-outline
  palette:
    #Palette toggle for light mode
    - scheme: default
      toggle:
        icon: material/brightness-7 
        name: Switch to dark mode
      code_theme: github

    # Palette toggle for dark mode
    - scheme: slate
      toggle:
        icon: material/brightness-4
        name: Switch to light mode
      code_theme: material-dark

extra_css:
  - stylesheets/extra.css
#  - stylesheets/native.css
#  - stylesheets/one-dark.css

#extra_javascript:
#    - https://unpkg.com/mermaid/dist/mermaid.min.js

docs_dir: docs
watch:
  - docs

#Bash
#pygmentize -L styles
#To generate a CSS file for your Markdown project (for example, using monokai), use:

#Bash example
#pygmentize -S monokai -f html -a .highlight > monokai.css

```

Note: to use the 'material' theme, add '' under 'readthedocs'

## Project layout

    mkdocs.yml    # The configuration file.
    docs/
        index.md  # The documentation homepage.
        ...       # Other markdown pages, images and other files.
