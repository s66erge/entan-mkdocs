# CI/CD — no-touch deploy to a self-managed server

GitHub Actions builds and ships the app to a Linux host over SSH. `master`
auto-deploys **staging**; a version tag deploys **production** behind an
approval gate. Images live in **GHCR**. App secrets stay on the host; GitHub
only holds SSH + deploy credentials.

## Pipeline

| Trigger | Workflow | Result |
| --- | --- | --- |
| every PR + push `master` | `ci.yml` → `checks.yml` | lint (ruff), tests (pytest), tangle-clean, docker build + Trivy scan |
| push `master` | `deploy-staging.yml` | checks → build/push `:staging`,`:sha-*` → deploy `gong-staging` |
| push tag `v*` | `deploy-production.yml` | checks → **approval** → build/push `:vX.Y.Z`,`:latest` → deploy `gong-production` |

`deploy.yml` is the reusable build+SSH-deploy job both environments call. Deploys
are health-gated (`docker compose up -d --wait` on the image's `/healthz`
HEALTHCHECK) and **auto-roll back** to the previous image on failure.

## Cutting a release

```bash
git tag v1.2.3 && git push origin v1.2.3
```

Then approve the `production` environment in the GitHub UI. Rollback = re-tag/redeploy a prior version, or on the host `IMAGE=$(cat .image_previous) docker compose -p gong-production up -d --wait`.

## GitHub configuration (one-time)

- **Environments** → create `staging` and `production`. On `production`, add
  **required reviewers** and restrict deployment branches/tags to `v*`.
- **Environment secrets** (both envs): `SSH_HOST`, `SSH_USER`, `SSH_PRIVATE_KEY`
  (a deploy key with access only to the deploy user).
- **Repository variables**: `STAGING_URL`, `PRODUCTION_URL` (e.g.
  `https://staging.gong.example.org`) — used for the post-deploy smoke test.
- **Branch protection** on `master`: require the `lint` and other `checks` jobs
  + PR review before merge.
- **Actions → General**: workflow permissions default read; GHCR publishing is
  granted per-workflow (`packages: write`).
- Hardening: pin third-party actions to commit SHAs (Dependabot `github-actions`
  keeps them current).

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
  ghcr.io/dhammaorg/eu-digital-gong-web:latest \
  sh -c 'cp -rn /app/data/. /seed/'
```

## Verifying a deploy

```bash
curl -fsS https://<domain>/healthz         # 200 {"status":"ok"}
curl -fsS https://<domain>/readyz          # 200 when db + minio reachable
docker compose -p gong-production ps        # app/db/minio/caddy healthy
```
