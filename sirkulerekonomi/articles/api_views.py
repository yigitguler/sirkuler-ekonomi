import json
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from wagtail.models import Locale
from wagtail.rich_text import RichText

from .models import ArticleIndexPage, ArticlePage


def _get_api_secret():
    return getattr(settings, 'ARTICLE_API_SECRET', None) or ''


def _check_auth(request):
    secret = _get_api_secret()
    if not secret:
        return False
    auth = request.headers.get('X-API-Key') or request.headers.get('Authorization')
    if auth and auth.startswith('Bearer '):
        auth = auth[7:]
    return auth == secret


@csrf_exempt
@require_http_methods(['POST'])
def post_article(request):
    if not _check_auth(request):
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    title = (data.get('title') or '').strip()
    if not title:
        return JsonResponse({'error': 'title is required'}, status=400)

    intro = (data.get('intro') or '')[:500]
    body_html = data.get('body') or ''

    haberler = ArticleIndexPage.objects.filter(slug='haberler', live=True).first()
    if not haberler:
        return JsonResponse({'error': 'Haberler index not found'}, status=404)

    locale = haberler.locale or Locale.objects.first()
    if not locale:
        return JsonResponse({'error': 'No locale configured'}, status=500)

    if body_html:
        body_blocks = [('paragraph', RichText(body_html))]
    else:
        body_blocks = []

    article = ArticlePage(
        title=title,
        intro=intro,
        body=body_blocks,
        locale=locale,
        live=True,
    )
    haberler.add_child(instance=article)
    article.save_revision().publish()

    base_url = getattr(settings, 'SITE_BASE_URL', '').rstrip('/')
    full_url = f"{base_url}{article.get_url()}" if base_url else article.get_url()

    return JsonResponse({
        'id': article.pk,
        'url': full_url,
        'slug': article.slug,
    }, status=201)
