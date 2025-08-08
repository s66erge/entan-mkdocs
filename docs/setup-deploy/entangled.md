# Entangled

Entangled is a tool to manage code snippets in Markdown files. It allows you to tangle code from Markdown files into separate source files and stitch changes back into the Markdown files.
For full documentation visit:

- [user documentation](https://entangled.github.io/#about)
- [installation / configuration](https://github.com/entangled/entangled.py).

## Installation

``` {.pwsh file= setup/entangled.ps1}
scoop install pandoc
uv pip install entangled-cli
```

And the vscode extension 'Entangled VSCode' for editing the entangled files.
It requires Pandoc to be installed.

## Configuration

``` {.toml file= entangled.toml}

version = "2.0"
watch_list = ["docs/**/*.md"]
hooks = ["build"]

#[markers]
#open="^(?P<indent>\\s*)```(?P<properties>.*)$"
#close="^(?P<indent>\\s*)```\\s*$"

[[languages]]
name = "Powershell"
identifiers =  ["powershell", "pwsh"]
comment = { open = "#" }

[[languages]]
name = "XML"
identifiers = ["xml", "html", "svg"]
comment = { open = "<!--", close = "-->" }

[[languages]]
name = "mermaid"
identifiers =  ["mermaid"]
comment = { open = "%%" }

[[languages]]
name = "yaml"
identifiers =  ["yaml"]
comment = { open = "#" }

[[languages]]
name = "toml"
identifiers =  ["toml"]
comment = { open = "#" }

```

## Commands

see: entangled --help

usage: **entangled [-h] [-d] [-v] {tangle,stitch,sync,watch,status} ...**

positional arguments: {tangle,stitch,sync,watch,status}

    tangle              Tangle codes from Markdown
                        [-h], [-s] only show, [--force] force tangle  
  
    stitch              Stitch code changes back into the Markdown
                        [-h], [--force] force stitch, [-s] 
  
    sync                Be smart wether to tangle or stich
  
    watch               Keep a loop running, watching for changes.
                        !!! does not work on windows !!!  
    status

options:

  -h, --help            show this help message and exit

  -d, --debug           enable debug messages
  
  -v, --version         show version number

## Project layout

    mkdocs.yml    # The configuration file.
    docs/
        index.md  # The documentation homepage.
        ...       # Other markdown pages, images and other files.
