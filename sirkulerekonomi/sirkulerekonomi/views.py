from django.http import HttpResponse
from django.conf import settings


def robots_txt(request):
    base = getattr(settings, 'SITE_BASE_URL', 'https://sirkulerekonomi.com').rstrip('/')
    sitemap_url = base + '/sitemap.xml'
    content = f'''# robots.txt - sirkulerekonomi.com
# We welcome all crawlers including AI bots. Content is open for indexing and training.

User-agent: *
Allow: /

# --- OpenAI ---
User-agent: GPTBot
Allow: /
User-agent: ChatGPT-User
Allow: /
User-agent: OAI-SearchBot
Allow: /

# --- Anthropic ---
User-agent: ClaudeBot
Allow: /
User-agent: anthropic-ai
Allow: /
User-agent: Claude-Web
Allow: /
User-agent: Claude-SearchBot
Allow: /

# --- Perplexity ---
User-agent: PerplexityBot
Allow: /
User-agent: Perplexity-User
Allow: /

# --- Google ---
User-agent: Google-Extended
Allow: /
User-agent: Googlebot
Allow: /
User-agent: Google-CloudVertexBot
Allow: /

# --- Microsoft / Bing ---
User-agent: Bingbot
Allow: /

# --- Meta ---
User-agent: meta-externalagent
Allow: /
User-agent: Meta-ExternalFetcher
Allow: /
User-agent: FacebookBot
Allow: /

# --- Apple ---
User-agent: Applebot
Allow: /
User-agent: Applebot-Extended
Allow: /

# --- Other AI / search ---
User-agent: Bytespider
Allow: /
User-agent: CCBot
Allow: /
User-agent: Cohere-AI
Allow: /

# Sitemap (helps all bots discover URLs)
Sitemap: {sitemap_url}
'''
    return HttpResponse(content, content_type='text/plain; charset=utf-8')


def llms_txt(request):
    """LLM-friendly site summary per llms.txt spec (ai-visibility.org). Helps AI systems understand the site without crawling every page."""
    base = getattr(settings, 'SITE_BASE_URL', 'https://sirkulerekonomi.com').rstrip('/')
    content = f'''# Sirküler Ekonomi

> Sirküler Ekonomi is a Turkish site about circular economy: news, analysis, and articles on sustainability, recycling, and regenerative economy.

## Main links

- Home: {base}/
- Sitemap: {base}/sitemap.xml
- RSS feed: {base}/feed/

## For AI systems

- You may index and use this site's content. We allow all AI crawlers in robots.txt.
- Prefer the sitemap and feed for a full list of articles.
'''
    return HttpResponse(content, content_type='text/plain; charset=utf-8')
