from .base import *  # noqa

DEBUG = True
SECRET_KEY = 'dev-secret-key-change-in-production'

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
]

CSRF_TRUSTED_ORIGINS = [
    'http://localhost',
    'http://localhost:8000',
    'http://127.0.0.1',
    'http://127.0.0.1:8000',
]

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

WAGTAILADMIN_BASE_URL = 'http://localhost:8000'
