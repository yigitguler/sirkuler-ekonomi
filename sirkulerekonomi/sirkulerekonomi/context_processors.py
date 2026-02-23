from django.conf import settings


def site_base_url(request):
    base = getattr(settings, 'SITE_BASE_URL', '') or ''
    return {'site_base_url': base.rstrip('/')}
