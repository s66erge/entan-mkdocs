# MkDocs-Zensical

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

## Project layout

    mkdocs.yml    # The configuration file synced with the configuration code below.
    docs/
        index.md  # The documentation homepage.
        ...       # Other markdown pages, images and other files.

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
  - toc:
      permalink: "#"
  - pymdownx.highlight:
      linenums: true 
      # use_pygments: true
      anchor_linenums: true
      line_spans: __span
      # pygments_lang_class: true
  #- pymdownx.inlinehilite
  - pymdownx.snippets
  - pymdownx.superfences:
      custom_fences:
        - name: mermaid
          class: mermaid
          format: !!python/name:pymdownx.superfences.fence_code_format

theme:
  name: material
  features:
    #- navigation.instant
    - navigation.top
    #- navigation.tab
    - navigation.path
    - content.code.copy
  palette:
    #Palette toggle for light mode
    - scheme: default
      toggle:
        icon: material/brightness-7 
        name: Switch to dark mode

    # Palette toggle for dark mode
    - scheme: slate
      toggle:
        icon: material/brightness-4
        name: Switch to light mode

extra_css:
#  - stylesheets/extra.css
  - stylesheets/rrt.css
#  - stylesheets/fruity.css

#extra_javascript:
#    - https://unpkg.com/mermaid/dist/mermaid.min.js

watch:
  - docs

```

## Creating pygments files to change colors inside code blocke

List loaded styles:  
`pygmentize -L styles`

Generate a CSS file for your Markdown project (for example, using rrt), use:  
`pygmentize -S rrt -f html -a .highlight > rrt.css`

Move the generated file to the `docs/stylesheets` folder and add it to the `extra_css` section of the configuration above.

## Using Zensical

Install vscode zensical extension PLUS

uv add --dev zensical