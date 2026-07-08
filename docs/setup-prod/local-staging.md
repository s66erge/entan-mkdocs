# Local prod. staging

2 sets of local docker containers are used to:  
1. develop over the exact same OS  
2. stage a secure system very close to final production   


Both sets use the same `Dockerfile.dev` file and use docker-compose for containers for:  
- postgres server: postgres-18  
- minio server: last dev. version

The production staging configuration file is an override of the [local dev containers](../setup-dev/vscode-devcontainer.md)

## Override of local dev containers

This file `.devcontainer/docker-compose.staging.yml`  
overrides the file: `.devcontainer/docker-compose.yml`  
and keeps all the other options untouched, including postgres and minio.

```yaml
#| file: .devcontainer/docker-compose.staging.yml

services:
  app:
    build:
      context: ..
      dockerfile: Dockerfile.dev  # 👈 Points to your single, main Dockerfile
      target: production     # 👈 THIS is how you use the target feature in Compose!
      hostname: staging
    volumes: !override []
    command: ["./.venv/bin/uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build in a bash session on project root: ~/develop/entan-mkdocs
```bash
docker compose --env-file .devcontainer/.env.staging -f .devcontainer/docker-compose.yml -f .devcontainer/docker-compose.staging.yml up --build

```
