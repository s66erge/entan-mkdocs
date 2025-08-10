# ~/~ begin <<docs/setup-deploy/a-python-environ.md#setup/environ.sh>>[init]
curl -LsSf https://astral.sh/uv/install.sh | sh
uv python install
uv venv
uv pip install -r requirements.txt
# ~/~ end
