# Local prod. staging

2 sets of local docker containers are used to:  
1. develop over the exact same OS  
2. stage a secure system very close to final production   


Both sets use the same `Dockerfile.dev` file and use docker-compose for containers for:  
- postgres server: postgres-18  
- minio server: last dev. version

## Another file for staging containers

This file `.devcontainer/docker-compose.staging.yml` replaces `.devcontainer/docker-compose.vscodedev.yml`   

```yaml
#| file: .devcontainer/docker-compose.staging.yml

services:
  # 1. Your Application Staging Container
  app:
    build:
      context: ..
      dockerfile: Dockerfile.dev # Or point to your standard dev Dockerfile
      target: production
    hostname: ubuntu-bosgame
    env_file:
      - .env.staging  # including same CONTAINER_NAME
    volumes:
      - appli_data:/app/data
    ports:
      - "8000:8000" # Exposes your app's port to the host machine
    depends_on:
      db:
        condition: service_healthy
      minio:
        condition: service_healthy
    command: ["./.venv/bin/uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
  # 2. PostgreSQL 18 Container
  db:
    image: postgres:18-alpine
    restart: unless-stopped
    env_file:
      - .env.staging
    ports:
      - "5432:5432" # Exposes to your host machine so you can use external GUI tools like DBeaver
    volumes:
      - postgres_data:/var/lib/postgresql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5
  # 3. MinIO (S3-compatible object storage) Container
  minio:
    image: quay.io/minio/minio
    restart: unless-stopped
    ports:
      - "9000:9000" # API port for your app to connect to
      - "9001:9001" # Web Console UI port
    env_file:
      - .env.staging
    volumes:
      - minio_data:/data
    command: server /data --console-address ":9001"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  appli_data:    # Persists application data
  postgres_data: # Persists your database tables even if the container restarts
  minio_data:    # Persists your uploaded files/buckets


```

Build and started in a bash session on project root: ~/develop/entan-mkdocs
```bash
docker compose -f .devcontainer/docker-compose.staging.yml up --build
```

Stopped from the same bash session
```bash
docker compose -f .devcontainer/docker-compose.staging.yml down
```
