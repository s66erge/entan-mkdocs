# ~/~ begin <<docs/setup-deploy/a-python-environ.md#setup/environ.ps1>>[init]
scoop install main/uv
uv python install
uv venv
uv pip install -r requirements.txt
.venv\Scripts\activate.ps1
# ~/~ end
