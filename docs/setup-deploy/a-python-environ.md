# The python environment

To set up and manage the virtual Python environment for this project, we use the [uv tool](https://docs.astral.sh/uv/).

## Installation and configuration

``` {.pwsh file= setup/environ.ps1}
scoop install main/uv
uv python install
uv pip install -r requirements.txt
.venv\Scripts\activate.ps1

```

## Commands

