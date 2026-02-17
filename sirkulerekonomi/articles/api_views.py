import json
import re
import urllib.error
import urllib.request
from django.conf import settings
from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from wagtail.images import get_image_model
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


def _fetch_image_from_url(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'SirkulerEkonomi-ArticleAPI/1.0'})
    with urllib.request.urlopen(req, timeout=15) as resp:
        content = resp.read()
        content_type = resp.headers.get('Content-Type', '') or ''
    if not content_type.startswith('image/'):
        return None, 'URL did not return an image'
    ext = 'jpg'
    if 'png' in content_type:
        ext = 'png'
    elif 'gif' in content_type:
        ext = 'gif'
    elif 'webp' in content_type:
        ext = 'webp'
    return content, ext


def _create_cover_image_from_url(url, title):
    content, ext = _fetch_image_from_url(url)
    if content is None:
        return None
    Image = get_image_model()
    name = re.sub(r'[^\w\-]', '-', (title or 'cover')[:50]) + '.' + ext
    image = Image(title=name)
    image.file.save(name, ContentFile(content), save=True)
    return image


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

    meta_title = (data.get('meta_title') or '').strip()[:70]
    if not meta_title:
        return JsonResponse({'error': 'meta_title is required'}, status=400)

    meta_description = (data.get('meta_description') or '').strip()[:500]
    if not meta_description:
        return JsonResponse({'error': 'meta_description is required'}, status=400)

    intro = (data.get('intro') or '')[:500]
    body_html = data.get('body') or ''
    meta_keywords = (data.get('meta_keywords') or '')[:255]
    cover_image_url = (data.get('cover_image_url') or '').strip()
    publish_immediately = data.get('publish_immediately', True)
    if isinstance(publish_immediately, str):
        publish_immediately = publish_immediately.strip().lower() in ('true', '1', 'yes')

    haberler = ArticleIndexPage.objects.filter(slug='haberler', live=True).first()
    if not haberler:
        return JsonResponse({'error': 'Haberler index not found'}, status=404)

    locale = haberler.locale or Locale.objects.first()
    if not locale:
        return JsonResponse({'error': 'No locale configured'}, status=500)

    main_image = None
    if cover_image_url:
        try:
            main_image = _create_cover_image_from_url(cover_image_url, title)
        except (OSError, ValueError, urllib.error.URLError) as e:
            return JsonResponse({'error': 'Invalid cover_image_url: %s' % str(e)}, status=400)
        if main_image is None:
            return JsonResponse({'error': 'cover_image_url did not return a valid image'}, status=400)

    if body_html:
        body_blocks = [('paragraph', RichText(body_html))]
    else:
        body_blocks = []

    article = ArticlePage(
        title=title,
        intro=intro,
        body=body_blocks,
        main_image=main_image,
        locale=locale,
        live=publish_immediately,
    )
    if meta_description:
        article.search_description = meta_description
    if meta_title:
        article.seo_title = meta_title
    if meta_keywords:
        article.meta_keywords = meta_keywords
    haberler.add_child(instance=article)
    revision = article.save_revision()
    if publish_immediately:
        revision.publish()

    base_url = getattr(settings, 'SITE_BASE_URL', '').rstrip('/')
    full_url = f"{base_url}{article.get_url()}" if base_url else article.get_url()

    return JsonResponse({
        'id': article.pk,
        'url': full_url,
        'slug': article.slug,
        'published': publish_immediately,
    }, status=201)
