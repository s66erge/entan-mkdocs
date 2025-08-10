# The python environment

To set up and manage the virtual Python environment for this project, we use the [uv tool](https://docs.astral.sh/uv/).

VSCode extensions:

- Python (from Microsoft)

## Windows

### Initial installation

``` {.pwsh file= setup/environ.ps1}
scoop install main/uv
uv python install
uv venv
uv pip install -r requirements.txt
.venv\Scripts\activate.ps1
```
### VSCode startup

``` {.pwsh file= setup/startup.ps1}
.venv\Scripts\activate.ps1
```

## Linux Mint

### Initial installation

``` {.bash file= setup/environ.sh}
curl -LsSf https://astral.sh/uv/install.sh | sh
uv python install
uv venv
uv pip install -r requirements.txt
```
### VSCode startup

``` bash
source .venv/bin/activate
```

## command

python main.py

