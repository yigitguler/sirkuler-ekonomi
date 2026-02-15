FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# No build-essential needed for pure-Python deps (Django, Wagtail, gunicorn, sentry-sdk)

WORKDIR /app

COPY sirkulerekonomi/requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && pip install -r /tmp/requirements.txt

COPY . /app

RUN adduser --disabled-password --gecos '' django && \
    mkdir -p /app/sirkulerekonomi/static /app/sirkulerekonomi/media /app/sirkulerekonomi/data && \
    chown -R django:django /app
USER django

ENV DJANGO_SETTINGS_MODULE=sirkulerekonomi.settings

CMD ["/app/entrypoint.sh"]
