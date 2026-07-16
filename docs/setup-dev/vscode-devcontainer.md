# Local container

2 sets of local docker containers are used to:  
1. develop over the exact same OS  
2. stage a secure system very close to final production   

Both sets use the same `Dockerfile.dev` file and use docker-compose for containers for:   
- postgres server - postgres-18  
- minio server - last dev. version

The production staging files are in `another folder/file`

## Container for developmemt

Built by vscode with:  
- vscode extensions  
- bash  
- direct acces to files in Ubuntu

### It is initiated with the file: `.devcontainer/devcontainer.json`

Note - entangled does not work with json files, need to copy/paste:
`.devcontainer/devcontainer.json`

```json
{
  "name": "My App Dev Environment",
  "dockerComposeFile": "docker-compose.vscodedev.yml", // WITH .env.solaris : see below
  "service": "app", // Tells VS Code to open your terminal inside the 'app' container
  "workspaceFolder": "/workspace",

  "remoteUser": "vscode",
  "containerUser": "vscode",

// 🔽 FORCE THE PATH INTO VS CODE TERMINALS 🔽
  "remoteEnv": {
    "PATH": "/app/.venv/bin:${containerEnv:PATH}"
  },

  // Customizes VS Code inside the container
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-azuretools.vscode-docker",
        "ckolkman.vscode-postgres" // Useful extension to query postgres directly from VS Code
      ]
    }
  },

  // Ensures dependent containers are fully up before VS Code connects
  "forwardPorts": [8000, 5432, 9000, 9001]
}

```

### Which triggers the `docker-compose-vscodedev.yml` file in the same `.devcontainer` folder

The passwords are in the .env.* files (not in Git) in the same folder `.devcontainer`

```yaml
#| file: .devcontainer/docker-compose.vscodedev.yml
services:
  # 1. Your Application Dev Container
  app:
    build:
      context: ..
      dockerfile: Dockerfile.dev # Or point to your standard dev Dockerfile
      target: builder
    hostname: ubuntu-bosgame
    env_file:
      - .env.vscodedev  # including same CONTAINER_NAME 
    volumes:
      - ..:/workspace:cached # Mounts your local project folder into the container
    ports:
      - "8000:8000" # Exposes your app's port to the host machine
    command: sleep infinity # Keeps the container running so VS Code can attach to it
  # 2. PostgreSQL 18 Container
  db:
    image: postgres:18-alpine
    restart: unless-stopped
    env_file:
      - .env.vscodedev
    ports:
      - "5432:5432" # Exposes to your host machine so you can use external GUI tools like DBeaver
    volumes:
      - postgres_data:/var/lib/postgresql

volumes:
  postgres_data: # Persists your database tables even if the container restarts

```

### Which triggers the `Dockerfile.dev` in the app root folder with target `builder`

```dockerfile
#| file: Dockerfile.dev

# ==========================================
# STAGE 1: The Build & Development Stage
# ==========================================
FROM python:3.13-slim AS builder

# Install system dependencies needed for building/testing
RUN apt-get update && apt-get install -y \
    sqlite3 sudo \
    && rm -rf /var/lib/apt/lists/*

# Create the vscode user only for development/testing context if needed
RUN useradd -m -s /bin/bash vscode \
    && echo "vscode ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

WORKDIR /app
ENV PYTHONUNBUFFERED=1

RUN pip install uv==0.10.4
RUN chown -R vscode:vscode /app

USER vscode

COPY --chown=vscode:vscode pyproject.toml uv.lock* ./
RUN uv sync --locked --no-dev --no-editable

# ==========================================
# STAGE 2: The Hardened Production Stage
# ==========================================
FROM python:3.13-slim AS production

# Only install necessary runtime OS dependencies (No 'sudo', no build tools)
RUN apt-get update && apt-get install -y \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Create a locked-down system user with NO sudo rights
RUN useradd -u 10001 -m -s /bin/false appuser

WORKDIR /app
ENV PYTHONUNBUFFERED=1

# Copy the pre-built virtual environment from the builder stage
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy application source code and set ownership to the production user
COPY --chown=appuser:appuser . .

# Switch to the non-root, non-sudo user
USER appuser

EXPOSE 8000
CMD ["./.venv/bin/uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

```

