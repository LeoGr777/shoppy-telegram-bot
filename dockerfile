FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
COPY pyproject.toml /app/
COPY . /app
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .
CMD ["python", "main.py"]
