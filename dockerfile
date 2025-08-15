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

# Create and switch to a non-root user for better security
RUN useradd -m appuser
USER appuser

# Optional: simple healthcheck to ensure container is running
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD python -c "print('ok')" || exit 1

# Default command to start your bot
CMD ["shoppy-telegram-bot"]
