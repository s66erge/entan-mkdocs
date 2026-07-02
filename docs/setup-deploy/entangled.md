# Entangled

Entangled is a tool to manage code snippets in Markdown files. It allows you to tangle code from Markdown files into separate source files and stitch changes back into the Markdown files.
For full documentation visit:

- [user documentation](https://entangled.github.io/#about)
- [installation / configuration](https://github.com/entangled/entangled.py).

Pandoc needs to be installed for Entangled.

VSCode extensions:

- Markdown All in One
- Markdown Preview Enhanced
- Entangled VSCode : helps for editing the entangled files.


## Initial Installation

### Windows

```pwsh
#| file: setup/entangled.ps1 
scoop install pandoc
uv pip install entangled-cli
```

## Commands

see: entangled --help

## Restoring files when both Markdown and code have changed

When you edited both Markdown and code without the daemon running, you may need to do some tricks to get back into a consistent state.

```
git add . 
git commit -m 'fixed everything'  # save everything you did
entangled tangle --force          # overwrites some changes you made
git restore main.py               # retrieve from latest commit
entangled stitch                  # apply changes back to markdown
git add .
git commit --amend                # amend your commit to perfection
```

## Configuration

```toml
#| file: entangled.toml

version = "2.0"
watch_list = ["docs/**/*.md"]
hooks = ["quarto_attributes"]

[markers]
open="^(?P<indent>\\s*)```(?P<properties>.*)$"
close="^(?P<indent>\\s*)```\\s*$"

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
