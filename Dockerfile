FROM python:3.11-slim AS builder
WORKDIR /app

# Install into a venv so it's accessible to any user (not root's home dir)
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Final image ────────────────────────────────────────────────────────────
FROM python:3.11-slim
WORKDIR /app

# Non-root user
RUN addgroup --gid 1001 appgroup && \
    adduser --uid 1001 --gid 1001 --disabled-password --gecos "" appuser

# Copy venv (world-readable, at /opt/venv not /root/.local)
COPY --from=builder /opt/venv /opt/venv

# Copy app source
COPY --chown=appuser:appgroup . .

# /opt/venv/bin is accessible to appuser — alembic, uvicorn etc. all work
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH=/app

USER appuser
EXPOSE 8010
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8010"]
