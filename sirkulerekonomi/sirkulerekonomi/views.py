from django.http import HttpResponse
from django.conf import settings


def robots_txt(request):
    base = getattr(settings, 'SITE_BASE_URL', 'https://sirkulerekonomi.com').rstrip('/')
    sitemap_url = base + '/sitemap.xml'
    content = f'''# robots.txt for sirkulerekonomi.com

User-agent: *
Allow: /

# AI Search Engines - Explicit Allow for Better GEO
User-agent: GPTBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: anthropic-ai
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: Bingbot
Allow: /

User-agent: FacebookBot
Allow: /

User-agent: Applebot
Allow: /

# Sitemap
Sitemap: {sitemap_url}
'''
    return HttpResponse(content, content_type='text/plain; charset=utf-8')
