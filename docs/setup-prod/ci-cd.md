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
- **Environment secrets** (both envs): `SSH_HOST`, `SSH_USER`, `SSH_PRIVATE_KEY`
  (a deploy key with access only to the deploy user).
- **Repository variables**: `STAGING_URL`, `PRODUCTION_URL` (e.g.
  `https://staging.gong.example.org`) — used for the post-deploy smoke test.
- **Branch protection** on `master`: require the `lint` and other `checks` jobs
  + PR review before merge.
- **Actions → General**: workflow permissions default read; GHCR publishing is
  granted per-workflow (`packages: write`).
- Hardening (recommended, not yet applied): pin third-party actions to commit
  SHAs. Dependabot (`github-actions`) currently keeps the version tags current.

## Server bootstrap (one-time, per host)

Assumes Docker + Compose v2 installed.

```bash
# deploy user + directories
sudo useradd -m -s /bin/bash deploy && sudo usermod -aG docker deploy
sudo -u deploy mkdir -p /opt/gong/staging /opt/gong/production

# CI deploy key
sudo -u deploy mkdir -p ~deploy/.ssh
echo "<CI deploy public key>" | sudo -u deploy tee -a ~deploy/.ssh/authorized_keys
sudo -u deploy chmod 600 ~deploy/.ssh/authorized_keys

# per-environment secrets file (fill from deploy/env.example, then lock down)
sudo -u deploy cp deploy/env.example /opt/gong/production/.env
sudo -u deploy chmod 600 /opt/gong/production/.env    # edit real values

# firewall + DNS
sudo ufw allow 22,80,443/tcp
# point staging.<domain> and <domain> A-records at this host (Caddy auto-TLS)
```

`compose.yaml` and `Caddyfile` are copied to each `host_dir` by CI on every
deploy, so they stay versioned with the repo.

### One-time data-volume seed

The app persists center databases under `DATA_DIR` (the `app_data` volume). Seed
it once with the template DBs baked into the image, or the first `add_center`
will find no template:

```bash
docker run --rm -v gong-production_app_data:/seed \
  ghcr.io/dhammaorg/eu-digital-gong-web:production \
  sh -c 'cp -rn /app/data/. /seed/'
```

## Verifying a deploy

```bash
curl -fsS https://<domain>/healthz         # 200 {"status":"ok"}
docker compose -p gong-production ps        # app/db/minio/caddy healthy
```
