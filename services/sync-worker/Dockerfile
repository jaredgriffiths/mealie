FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY services/sync-worker/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY services/sync-worker/main.py .

CMD ["python", "main.py"]
