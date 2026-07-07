# Local docker containers

2 sets of local docker containers are used to:  
1. develop over the exact same OS
2. stage a secure system very close to final production   

Both sets include also containers for:  
- postgres server - postgres-18
- minio server - last dev. version


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
  "dockerComposeFile": "docker-compose.yml",
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

### Which triggers the `docker-compose.yml` in the same `.devcontainer` folder

```yml
#| file: .devcontainer/docker-compose.yml

services:
  # 1. Your Application Dev Container
  app:
    build:
      context: ..
      dockerfile: Dockerfile.dev # Or point to your standard dev Dockerfile
      target: builder
    hostname: solaris  
    volumes:
      - ..:/workspace:cached # Mounts your local project folder into the container
    ports:
      - "8000:8000" # Exposes your app's port to the host machine
    environment:
      DATABASE_URL: "postgresql://postgres:${DB_PASSWORD}@db:5432/dev_db"
      MINIO_ROOT_USER: "msDpY3CtaVdHzX2Df8XYdmzt"
      MINIO_ROOT_PASSWORD: "${MINIO_PASSWORD}"
    command: sleep infinity # Keeps the container running so VS Code can attach to it
  # 2. PostgreSQL 18 Container
  db:
    image: postgres:18-alpine
    restart: unless-stopped
    environment:
      POSTGRES_USER: "postgres"
      POSTGRES_PASSWORD: "${DB_PASSWORD}"
      POSTGRES_DB: "dev_db"
    ports:
      - "5432:5432" # Exposes to your host machine so you can use external GUI tools like DBeaver
    volumes:
      - postgres_data:/var/lib/postgresql

  # 3. MinIO (S3-compatible object storage) Container
  minio:
    image: quay.io/minio/minio
    restart: unless-stopped
    ports:
      - "9000:9000" # API port for your app to connect to
      - "9001:9001" # Web Console UI port
    environment:
      MINIO_ROOT_USER: "msDpY3CtaVdHzX2Df8XYdmzt"
      MINIO_ROOT_PASSWORD: "${MINIO_PASSWORD}"
    volumes:
      - minio_data:/data
    command: server /data --console-address ":9001"

volumes:
  postgres_data: # Persists your database tables even if the container restarts
  minio_data:    # Persists your uploaded files/buckets

```


The `builder` container gives the same OS as in production with access to bash and the same vscode tools as in Ubuntu

The `production` container 



## Container for production staging



Execute in a bash session on: ~/develop/entan-mkdocs
```bash
docker compose -f .devcontainer/docker-compose.yml -f .devcontainer/docker-compose.staging.yml up --build

```
