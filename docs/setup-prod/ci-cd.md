# CI/CD — no-touch deploy to a self-managed server

GitHub Actions builds and ships the app to a Linux host over SSH. `master`
auto-deploys **staging**; deploying to **staging or production on demand** is a
one-click dropdown (production behind an approval gate). Images live in **GHCR**.
App secrets stay on the host; GitHub only holds SSH + deploy credentials.

## Pipeline

| Trigger | Workflow | Result |
| --- | --- | --- |
| every PR + push `master` | `ci.yml` → `checks.yml` | lint (ruff), tests (pytest), tangle-clean, docker build + Trivy scan |
| push `master` | `deploy-staging.yml` | checks → build/push `:staging`,`:sha-*` → deploy `gong-staging` |
| **Actions → Deploy** (manual) | `deploy-manual.yml` | pick env → checks → (**approval** if production) → build/push `:sha-*`,`:<env>` → deploy `gong-<env>` |

`deploy.yml` is the reusable build+SSH-deploy job every path calls. Deploys are
health-gated (`docker compose up -d --wait` on the image's `/healthz`
HEALTHCHECK) and **auto-roll back** to the previous image on failure.

## Deploying (staging or production)

No tag to remember. In the GitHub UI:

1. **Actions → Deploy → Run workflow**.
2. Pick the **branch/tag** to deploy in the ref selector.
3. Pick **environment**: `staging` or `production`.
4. **Run**. Production pauses for approval in the `production` environment before it deploys.

`master` also auto-deploys to staging on every merge, so most staging updates
need no clicks. Rollback = run **Deploy** again against a prior ref/tag, or on the
host `IMAGE=$(cat .image_previous) docker compose -p gong-production up -d --wait`.

## GitHub configuration (one-time)

- **Environments** → create `staging` and `production`. On `production`, add
  **required reviewers** so a manual deploy to prod pauses for approval.
- The **Deploy** button (`workflow_dispatch`) only appears once `deploy-manual.yml`
  is on the default branch (`master`).
- **Repository secret**: `SSH_KEY` (a deploy private key for the `deploy` user).
- **Repository variables**: `SSH_ADDRESS`, `SSH_PORT`, `SSH_USER` (one host serves
  both envs, so these are shared at the repo level). Smoke-test domains are baked
  into the deploy workflows.
- **Branch protection** on `master`: require the `lint` and other `checks` jobs
  + PR review before merge.
- **Actions → General**: workflow permissions default read; GHCR publishing is
  granted per-workflow (`packages: write`).
- Hardening (recommended, not yet applied): pin third-party actions to commit
  SHAs. Dependabot (`github-actions`) currently keeps the version tags current.

## Topology — both envs on one host, kept independent

Staging and prod run on the **same host** but are as independent as possible:
separate compose projects (`gong-staging` / `gong-production`), volumes, Postgres,
MinIO, `.env`, **edge networks**, rollback state, and resource limits. A staging
deploy/crash/rollback never touches prod. The only shared piece is the single
`:443` listener → one **shared edge Caddy** (`gong-edge`) that terminates TLS for
both subdomains; it is deployed once and never touched by app deploys.

## Server bootstrap (one-time, per host)

Assumes Docker + Compose v2 installed.

```bash
# deploy user + directories
sudo useradd -m -s /bin/bash deploy && sudo usermod -aG docker deploy
sudo -u deploy mkdir -p /opt/gong/staging /opt/gong/production /opt/gong/edge

# CI deploy key
sudo -u deploy mkdir -p ~deploy/.ssh
echo "<SSH_KEY public half>" | sudo -u deploy tee -a ~deploy/.ssh/authorized_keys
sudo -u deploy chmod 600 ~deploy/.ssh/authorized_keys

# per-environment secrets files — DIFFERENT db/minio passwords per env
sudo -u deploy cp deploy/env.example /opt/gong/staging/.env      # edit, then chmod 600
sudo -u deploy cp deploy/env.example /opt/gong/production/.env   # edit, then chmod 600
sudo -u deploy chmod 600 /opt/gong/{staging,production}/.env

# per-environment edge networks (staging & prod share NO network)
docker network create gong-staging-edge
docker network create gong-production-edge

# daemon-wide log rotation so one env's logs can't fill the shared disk
sudo tee /etc/docker/daemon.json <<'JSON'
{ "log-driver": "json-file", "log-opts": { "max-size": "10m", "max-file": "3" } }
JSON
sudo systemctl restart docker

# shared edge Caddy — deployed ONCE (routes both subdomains, auto-TLS)
sudo -u deploy cp deploy/edge/compose.yaml deploy/edge/Caddyfile /opt/gong/edge/
cd /opt/gong/edge && docker compose -p gong-edge up -d

# firewall + DNS
sudo ufw allow 22,80,443/tcp
# A-records: campus-gong.dhamma.org AND staging-campus-gong.dhamma.org → this host
```

`compose.yaml` is copied to each env `host_dir` by CI on every deploy. The edge
`compose.yaml` + `Caddyfile` are placed once (above). To change routing later,
edit `/opt/gong/edge/Caddyfile`, then validate before reload so a typo can't drop
both sites:

```bash
docker exec gong-edge-caddy-1 caddy validate --config /etc/caddy/Caddyfile \
  && docker exec gong-edge-caddy-1 caddy reload --config /etc/caddy/Caddyfile
```

### One-time data-volume seed

The app persists center databases under `DATA_DIR` (the `app_data` volume). Seed
it once with the template DBs baked into the image, or the first `add_center`
will find no template:

```bash
docker run --rm -v gong-production_app_data:/seed \
  ghcr.io/dhammaorg/eu-digital-gong-web:production \
  sh -c 'cp -rn /app/data/. /seed/'
```

## Host sizing

Both stacks + shared edge on one box ≈ 2× the prod-only figure. Target **2 vCPU ·
8 GB RAM · 40 GB SSD** (Debian 13). The per-service `deploy.resources.limits` in
`compose.yaml` cap each env so one can't starve the other; on a 4 GB box, keep
those limits and add ~2 GB swap.

## Verifying a deploy

```bash
curl -fsS https://campus-gong.dhamma.org/healthz          # prod: 200 {"status":"ok"}
curl -fsS https://staging-campus-gong.dhamma.org/healthz  # staging: 200
docker compose -p gong-production ps                       # app/db/minio healthy
docker compose -p gong-edge ps                             # shared caddy healthy
```

A redeploy of one env must not drop the other's TLS (independent Caddy site blocks).
