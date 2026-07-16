# ~/~ begin <<docs/setup-prod/railway.md#Dockerfile>>[init]

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
# DATA_DIR is preexistant in RAILWAY

# Pre-built virtualenv from the builder stage
COPY --from=builder /app/.venv /app/.venv

# Create the RAILWAY NEEDED directory and hand ownership to appuser (while still running as root)
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

# ~/~ end
