# ---------- builder: install wheels and build dependencies ----------
FROM python:3.12-slim AS builder
ENV PYTHONDONTWRITEBYTECODE=1 \     
    PYTHONUNBUFFERED=1

# Install build deps required for some Python packages (e.g., psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only requirements first for layer caching
COPY requirements.txt /app/requirements.txt

# Build wheels into /wheels to speed up final install
RUN pip install --upgrade pip setuptools wheel \
 && pip wheel --wheel-dir /wheels -r /app/requirements.txt

# ---------- final: smaller runtime image ----------
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Create non-root user
RUN groupadd --system app && useradd --system --create-home --gid app app

WORKDIR /app

# Install runtime deps from builder's wheel cache
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*

# Copy application code
COPY . /app

# Fix permissions and switch to non-root user
RUN chown -R app:app /app
USER app

EXPOSE 8000

# Optional healthcheck for Docker (adjust endpoint if different)
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD wget -qO- --timeout=2 http://127.0.0.1:${PORT}${ROUTE_PREFIX:-/api/v1/}/health || exit 1

# Use Gunicorn with Uvicorn workers for robustness.
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", "-w", "4", "-b", "0.0.0.0:8000", "--log-level", "info"]