# Local prod. staging

2 sets of local docker containers are used to:  
1. develop over the exact same OS
2. stage a secure system very close to final production   

Both sets include also containers for:  
- postgres server - postgres-18
- minio server - last dev. version

The production staging files are in `another folder/file`

## Container for staging

Override with docker-compose.staging.yml

services:
  app:
    build:
      context: ..
      dockerfile: Dockerfile.dev  # 👈 Points to your single, main Dockerfile
      target: production     # 👈 THIS is how you use the target feature in Compose!
    volumes: !override []
    command: ["./.venv/bin/uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]


Build in a bash session on: ~/develop/entan-mkdocs
```bash
docker compose --env-file .devcontainer/.env -f .devcontainer/docker-compose.yml -f .devcontainer/docker-compose.staging.yml up --build

```
