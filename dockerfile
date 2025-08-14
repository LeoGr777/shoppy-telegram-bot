FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Projektdateien kopieren
COPY pyproject.toml README.* /app/ 2>/dev/null || true
COPY . /app

# Abhängigkeiten + Projekt installieren (PEP 517)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Start: Name MUSS zu [project.scripts] in pyproject.toml passen!
# Beispiel: shoppy-bot = "shoppy_bot.main:main"
CMD ["shoppy-telegram-bot"]
