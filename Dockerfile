FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc build-essential libjpeg-dev zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

RUN adduser \
    --disabled-password \
    --gecos "" \
    --home /home/django-user \
    django-user

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/vol/web/media /app/vol/web/static && \
    chown -R django-user:django-user /app/vol && \
    chmod -R 755 /app/vol

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

USER django-user

ENTRYPOINT ["/app/entrypoint.sh"]
EXPOSE 8000
