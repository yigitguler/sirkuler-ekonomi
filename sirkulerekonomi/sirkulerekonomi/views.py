from django.http import HttpResponse
from django.conf import settings


def robots_txt(request):
    base = getattr(settings, 'SITE_BASE_URL', 'https://sirkulerekonomi.com').rstrip('/')
    sitemap_url = base + '/sitemap.xml'
    content = f'''User-agent: *
Allow: /

Sitemap: {sitemap_url}
'''
    return HttpResponse(content, content_type='text/plain; charset=utf-8')
