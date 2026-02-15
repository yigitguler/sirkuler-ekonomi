import os

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

from .base import *  # noqa

DEBUG = False
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'change-me-in-production')

SENTRY_DSN = os.environ.get(
    'SENTRY_DSN',
    'https://6d34ded45aefc62ce6ddd6724d78bf30@o118008.ingest.us.sentry.io/4510889381920768',
)
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        environment='production',
        traces_sample_rate=0.1,
        send_default_pii=False,
    )

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', 'sirkulerekonomi.com,www.sirkulerekonomi.com').split(',')

SITE_BASE_URL = os.environ.get('SITE_BASE_URL', 'https://sirkulerekonomi.com')

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
