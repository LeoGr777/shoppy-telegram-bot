# Use official Python 3.11 slim image (small, secure, up-to-date)
FROM python:3.11-slim

# Environment settings:
# - Prevent Python from writing .pyc files
# - Force stdout/stderr to be unbuffered (logs show immediately)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory inside container
WORKDIR /app

# Copy only metadata first to leverage Docker build cache
COPY pyproject.toml /app/

# Copy the rest of the project files
COPY . /app

# Install dependencies and the project itself
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Create a non-root app user with fixed UID/GID to match the host folder
# Note: Adjust APP_UID/APP_GID if you ever need different IDs.
ARG APP_UID=1009
ARG APP_GID=1009
RUN groupadd -g ${APP_GID} appgroup && \
    useradd -m -u ${APP_UID} -g ${APP_GID} appuser && \
    mkdir -p /app/data && \
    chown -R appuser:appgroup /app/data

# Switch to the non-root user
USER appuser

# Optional: simple healthcheck to ensure container is running
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD python -c "print('ok')" || exit 1

# Default command to start your bot
CMD ["python", "main.py"]
