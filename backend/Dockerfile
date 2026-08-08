FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /srv/app

RUN addgroup --system app && adduser --system --ingroup app app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN mkdir -p /data/uploads && chown -R app:app /data/uploads

USER app
EXPOSE 8000
# Runs migrations before serving so the image is self-sufficient under any
# orchestrator (docker-compose overrides this with the same steps today,
# but a plain `docker run`/Render/k8s launch of this image alone must also
# migrate on boot rather than starting against a stale schema).
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${API_WORKERS:-1} --proxy-headers --forwarded-allow-ips=*"]
