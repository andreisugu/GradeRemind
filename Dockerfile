# ============================================================
# Stage 1 — Base image
# ============================================================
# python:3.12-slim is Debian-based (not Alpine) so pip wheels
# for compiled packages (lxml etc.) work out-of-the-box.
# It is ~50 MB vs ~1 GB for the full image.
FROM python:3.12-slim

# ============================================================
# Build-time metadata (visible in `docker inspect`)
# ============================================================
LABEL maintainer="GradeRemind" \
      description="Monitorizare automată note GradeRemind" \
      python.version="3.12"

# ============================================================
# Security: run as a non-root user
# ============================================================
# Creates a dedicated system user/group called "appuser".
# Running as root inside a container is a security risk —
# if the process is compromised, the attacker gets root on
# the host (when using --privileged or bind mounts).
RUN groupadd --system appuser && \
    useradd  --system --gid appuser --no-create-home appuser

# ============================================================
# Working directory inside the container
# ============================================================
WORKDIR /app

# ============================================================
# Layer 1 — Install Python dependencies
# ============================================================
# COPY requirements.txt BEFORE the source code so that Docker
# can cache this layer. Re-installing packages only happens
# when requirements.txt actually changes, not on every code edit.
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ============================================================
# Layer 2 — Copy application source code
# ============================================================
# .dockerignore excludes .env, .venv, __pycache__, sessions.json
# and generated data files so they never end up in the image.
COPY main.py .
COPY src/ ./src/

# ============================================================
# Persistent data directory
# ============================================================
# The app writes note_salvate.json, note_log.txt, sessions.json
# and debug_page.html to its CWD (/app).
# Mount a Docker volume or host bind-mount here to keep data
# across container restarts:
#   docker run -v gradremind_data:/app/data ...
# (see README for the full run command with env vars)
RUN mkdir -p /app/data && \
    chown -R appuser:appuser /app

# Declare /app/data as a mountable volume so Docker tracks it.
VOLUME ["/app/data"]

# ============================================================
# Switch to non-root user for runtime
# ============================================================
USER appuser

# ============================================================
# Expose the dashboard port (default 5000, override via .env)
# ============================================================
EXPOSE 5000

# ============================================================
# Health check
# ============================================================
# Docker will mark the container "unhealthy" if the dashboard
# stops responding, enabling auto-restart policies to kick in.
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/login')" || exit 1

# ============================================================
# Entrypoint
# ============================================================
# Use the exec form (JSON array) — this makes Python PID 1 so
# it receives SIGTERM directly and can shut down gracefully.
CMD ["python", "main.py"]
