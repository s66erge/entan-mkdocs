# Railway

Railway is a platform that allows you to deploy applications easily. It provides a simple way to host your applications and manage their deployments.

Railway is connected to Github : all changes pushed to Github repo branch 'master' are deployed immediately (+/-) to Railway 'entan-mkdocs', where the 'main.py' file is the entry point.

## Using a dockerfile to drive the build 


## Deplyment run on railway

https://entan-mkdocs-production.up.railway.app

## Railway CLI

### Installation

``` pwsh
scoop install railway
```

### Using it

The Railway CLI is used to:

1. link the local project to a Railway project:
   ``` pwsh
   railway login
   railway link
   ```

2. connect to a service via SSH - using the SSH key on bosgame
   ``` pwsh
   railway ssh -i C:\Users\serge\.ssh\railway_ssh
   ```

3. run the app localy with the Railway project environment variables:
   ``` pwsh
   railway run python main.py
   ```

## The Dockerfile

The `Dockerfile` instructs how to build the railway app:

Multi-stage build: a `builder` stage resolves the locked dependencies with
`uv`, and a hardened `production` stage copies only the virtualenv + app source
and runs as a non-root user. Matches the project's Python 3.13 requirement and
is the image built and shipped by CI (`docker build --target production`).

```dockerfile
#| file: Dockerfile

# ==========================================
# STAGE 1: Build (resolve locked dependencies)
# ==========================================
FROM python:3.13-slim AS builder

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

RUN pip install --no-cache-dir uv==0.10.4

# Copy lockfiles first for layer caching
COPY pyproject.toml uv.lock* ./
RUN uv sync --locked --no-dev --no-editable

# ==========================================
# STAGE 2: Hardened production runtime
# ==========================================
FROM python:3.13-slim AS production

# Runtime OS deps only (no build tools, no sudo)
RUN apt-get update && apt-get install -y --no-install-recommends \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Locked-down non-root user
RUN useradd -u 10001 -m -s /bin/false appuser

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    DATA_DIR="/permanent/data"

# Pre-built virtualenv from the builder stage
COPY --from=builder /app/.venv /app/.venv

# Create the directory and hand ownership to appuser (while still running as root)
RUN mkdir -p "$DATA_DIR" && chown -R appuser:appuser "$DATA_DIR"

# Application source (owned by the runtime user)
COPY --chown=appuser:appuser . .
RUN python -m compileall -q .

USER appuser
EXPOSE 8000

# Liveness probe baked into the image (hits the dependency-free /healthz route)
# HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
#     CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/healthz').status==200 else 1)"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

```

## Resend api key

On the entan-mkdocs service in Railway, [define the variable 'RESEND_API_KEY'](../gong-web-app-code/utilities.md#via-resendcom)

## How to access files in double pane: railway app and Ubuntu/wsl ?

Use WinSCP from windows and select in the stored directories
