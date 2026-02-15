import os

# Load concrete settings so that DJANGO_SETTINGS_MODULE can be a package (sirkulerekonomi.settings)
# Switch between development and production via DJANGO_ENV=production
DJANGO_ENV = os.getenv('DJANGO_ENV', 'development').lower()

if DJANGO_ENV == 'production':
    from .production import *  # noqa: F401,F403
else:
    from .development import *  # noqa: F401,F403
