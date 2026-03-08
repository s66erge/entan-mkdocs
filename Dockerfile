FROM python:3.12.8-slim

# Install system dependencies from log
RUN apt-get update && apt-get install -y \
    curl ed sqlite3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV PYTHONUNBUFFERED=1

# Install uv directly (matches Railpack's uv 0.10.4)
RUN pip install uv==0.10.4

# Copy lockfiles first for caching
COPY pyproject.toml uv.lock* ./

# Exact uv sync steps from your log (no mise needed)
RUN uv sync --locked --no-dev --no-editable
# CRITICAL: Activate venv for entire container
ENV PATH="/app/.venv/bin:$PATH"

# Copy app
COPY . .
COPY ./data /app/data

# Bytecode compile (from log)
RUN python -m compileall .

EXPOSE 8000
CMD ["./.venv/bin/uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]