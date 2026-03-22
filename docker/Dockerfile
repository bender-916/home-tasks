# ============================================
# Stage 1: Builder
# ============================================
FROM python:3.11-slim-bookworm AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (Docker cache)
COPY backend/requirements.txt .

# Create virtualenv and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ============================================
# Stage 2: Runtime
# ============================================
FROM python:3.11-slim-bookworm AS runtime

# Build arguments
ARG APP_VERSION=1.0.0
ARG BUILD_DATE

# OCI Labels
LABEL org.opencontainers.image.title="Home Tasks" \
      org.opencontainers.image.description="Sistema de reparto de tareas del hogar" \
      org.opencontainers.image.version="${APP_VERSION}" \
      org.opencontainers.image.created="${BUILD_DATE}"

# Create non-root user
RUN groupadd -g 999 apptask && \
    useradd -r -u 999 -g apptask -d /app -s /sbin/nologin apptask

WORKDIR /app

# Copy virtualenv from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=apptask:apptask backend/app ./app
COPY --chown=apptask:apptask backend/wsgi.py .
COPY --chown=apptask:apptask frontend ./frontend

# Create data directory
RUN mkdir -p /data && chown apptask:apptask /data

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=wsgi.py \
    DATABASE_PATH=/data/home_tasks.db \
    FLASK_ENV=production

# Expose port
EXPOSE 5000

# Switch to non-root user
USER apptask

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/health')" || exit 1

# Start command
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "2", "--access-logfile", "-", "--error-logfile", "-", "wsgi:app"]
