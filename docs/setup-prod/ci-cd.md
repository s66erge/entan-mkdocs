# CI/CD — deploy to the self-managed server

GitHub Actions builds the app, publishes it to GHCR, and deploys it over SSH to a
Debian host that runs **both** environments as isolated stacks. Public TLS is done
by **Cloudflare**; the origin uses a **self-signed** cert.

- prod: `https://campus-gong.dhamma.org` — compose project `gong-production`, `/opt/gong/production`
- staging: `https://staging-campus-gong.dhamma.org` — compose project `gong-staging`, `/opt/gong/staging`
- host: `helsinki002.server.dhamma.org`, SSH port `2204`, deploy user `server`

## How to deploy

**Staging** — either happens automatically or on demand:
- Merge/push to `master` → auto-deploys staging (`deploy-staging.yml`), or
- **Actions → Deploy → Run workflow → environment `staging` → Run** (`deploy-manual.yml`).

**Production**:
- **Actions → Deploy → Run workflow → environment `production` → Run**.
- Uses the `production` GitHub Environment (see the approval note below).

> While PR #19 is unmerged, the master `Deploy` button and auto-staging still run the
> *old* pipeline. Deploy the new one by dispatching **Deploy** against the
> `feat/cicd-pipeline` ref (`gh workflow run deploy-manual.yml --ref feat/cicd-pipeline -f environment=<env>`)
> until #19 merges.

Rollback = run **Deploy** again against a prior ref/tag, or on the host:
`cd /opt/gong/<env> && IMAGE=$(cat .image_previous) docker compose -p gong-<env> up -d --wait`.

## Pipeline

| Trigger | Workflow | Result |
| --- | --- | --- |
| every PR + push `master` | `ci.yml` → `checks.yml` | ruff, pytest, entangled tangle-clean, docker build + Trivy |
| push `master` | `deploy-staging.yml` | checks → build → deploy `gong-staging` |
| **Actions → Deploy** | `deploy-manual.yml` | pick env → checks → deploy `gong-<env>` |

`deploy.yml` is the reusable build+deploy job. It builds from **`Dockerfile-nonRailway`**
(the multi-stage, non-root image; the plain `Dockerfile` is Railway's), pushes to
GHCR, Trivy-scans, scps `deploy/compose.yaml`, then over SSH: `docker compose up -d
--wait` (gated on the image's `/healthz` HEALTHCHECK) with **auto-rollback** to the
previous image, and a server-side **edge→app** ingress check. There is no public-URL
smoke test — public reachability is a front-proxy concern, not per-deploy.

## Architecture

- **Isolation:** each env has its own compose project, volumes, Postgres, MinIO, `.env`,
  **edge network** (`gong-<env>-edge`), rollback state, and resource limits. A staging
  deploy/crash/rollback cannot touch prod.
- **Ingress:** one shared **edge Caddy** (`gong-edge`, `/opt/gong/edge`) joined to both
  edge networks, routing by hostname to `gong-<env>-app-1:8000`. Deployed once at
  bootstrap; never touched by app deploys.
- **TLS:** the edge Caddy serves a **self-signed** cert (`tls internal`) — no ACME.
  **Cloudflare** (orange cloud, SSL mode **Full**) terminates public TLS and connects to
  the origin over HTTPS, accepting the self-signed cert.
- **Front HAProxy:** the public IP is a shared dhamma.org HAProxy. It must route
  `campus-gong.dhamma.org` and `staging-campus-gong.dhamma.org` to this host on 443
  (SNI/TCP passthrough → `helsinki002:443`), or Cloudflare's origin must point at the
  host directly. Without this the host isn't publicly reachable.

## One-time prerequisites (checklist)

GitHub:
- Repo **secret** `SSH_KEY` (deploy private key for `server`).
- Repo **variables** `SSH_ADDRESS`, `SSH_PORT`, `SSH_USER`.
- `production` and `staging` **Environments**. Approval gate for prod: **required
  reviewers needs GitHub Team/Enterprise on a private repo** (not available here). Free
  alternative — set the `production` environment's **deployment branches to `master`
  only** (after #19 merges) so only reviewed/merged code can deploy to prod.

Host (as `server`, who must be in the `docker` group):
- `/opt/gong/{staging,production,edge}` dirs.
- Per-env `/opt/gong/<env>/.env` (chmod 600) with **distinct** DB/MinIO passwords and a
  **real `RESEND_API_KEY`** (login-code emails won't send with the placeholder).
- Edge networks `gong-staging-edge`, `gong-production-edge`.
- Docker daemon log rotation (`/etc/docker/daemon.json`).
- Edge Caddy running (`/opt/gong/edge`, `docker compose -p gong-edge up -d`).
- Cloudflare + HAProxy routing (above).
- Data-volume seed (below).

## Server bootstrap (one-time, per host)

```bash
# deploy user in docker group + dirs (run as an admin/sudoer)
sudo usermod -aG docker server
sudo -u server mkdir -p /opt/gong/staging /opt/gong/production /opt/gong/edge

# CI deploy key -> server's authorized_keys
echo "<SSH_KEY public half>" | sudo -u server tee -a /home/server/.ssh/authorized_keys
sudo -u server chmod 700 /home/server/.ssh && sudo -u server chmod 600 /home/server/.ssh/authorized_keys

# per-env secrets (fill from deploy/env.example; DIFFERENT passwords per env; real RESEND key)
sudo -u server cp deploy/env.example /opt/gong/staging/.env      # edit, chmod 600
sudo -u server cp deploy/env.example /opt/gong/production/.env   # edit, chmod 600

# per-env edge networks (staging & prod share NO network)
docker network create gong-staging-edge
docker network create gong-production-edge

# daemon-wide log rotation (protects the shared disk)
sudo tee /etc/docker/daemon.json <<'JSON'
{ "log-driver": "json-file", "log-opts": { "max-size": "10m", "max-file": "3" } }
JSON
sudo systemctl restart docker

# shared edge Caddy — deployed ONCE (self-signed TLS, routes both hostnames)
sudo -u server cp deploy/edge/compose.yaml deploy/edge/Caddyfile /opt/gong/edge/
cd /opt/gong/edge && docker compose -p gong-edge up -d
```

To change edge routing later, edit `/opt/gong/edge/Caddyfile`, then validate before reload:
```bash
docker exec gong-edge-caddy-1 caddy validate --config /etc/caddy/Caddyfile \
  && docker exec gong-edge-caddy-1 caddy reload --config /etc/caddy/Caddyfile
```

### One-time data-volume seed (per env)

The app persists center databases under `DATA_DIR` (the `app_data` volume). Seed it once
with the template DBs baked into the image, or the first `add_center` finds no template:
```bash
docker run --rm -v gong-production_app_data:/seed \
  ghcr.io/dhammaorg/eu-digital-gong-web:production sh -c 'cp -rn /app/data/. /seed/'
docker run --rm -v gong-staging_app_data:/seed \
  ghcr.io/dhammaorg/eu-digital-gong-web:staging sh -c 'cp -rn /app/data/. /seed/'
```

## Host sizing

Both stacks + shared edge on one box: target **2 vCPU · 8 GB RAM · 40 GB SSD** (Debian 13).
`deploy.resources.limits` in `compose.yaml` cap each env so one can't starve the other; on
a 4 GB box keep those limits and add ~2 GB swap.

## Verifying a deploy

On the host (works regardless of the front proxy):
```bash
docker compose -p gong-staging ps        # app/db/minio healthy
docker compose -p gong-production ps
docker compose -p gong-edge ps           # shared caddy up
# ingress via the self-signed edge:
curl -sk --resolve staging-campus-gong.dhamma.org:443:127.0.0.1 https://staging-campus-gong.dhamma.org/healthz
curl -sk --resolve campus-gong.dhamma.org:443:127.0.0.1        https://campus-gong.dhamma.org/healthz
```
Public HTTPS (`https://<host>/healthz`) works only once Cloudflare + HAProxy route the
hostnames to this box. A redeploy of one env never drops the other's ingress.
