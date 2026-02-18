import base64
import io
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


def _strip_html(html):
    return re.sub(r'<[^>]+>', '', html).strip()


def _parse_body_to_stream_blocks(html):
    """Parse HTML into Wagtail StreamField blocks: heading, paragraph, blockquote."""
    if not (html or '').strip():
        return []
    html = html.strip()
    blocks = []
    block_tags = ('p', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote')
    i = 0
    while i < len(html):
        m = re.search(r'<([a-z][a-z0-9]*)(?:\s[^>]*)?>', html[i:], re.I)
        if not m:
            break
        tag = m.group(1).lower()
        if tag not in block_tags:
            i += m.end()
            continue
        start = i + m.end()
        close = '</' + tag + '>'
        depth = 1
        j = start
        end_pos = -1
        while j < len(html):
            next_close = html.find(close, j)
            if next_close == -1:
                break
            next_open = html.find('<' + tag, j)
            if next_open != -1 and next_open < next_close:
                depth += 1
                j = next_open + 1
            else:
                depth -= 1
                if depth == 0:
                    end_pos = next_close
                    break
                j = next_close + len(close)
        if end_pos == -1:
            i = start
            continue
        inner = html[start:end_pos]
        i = end_pos + len(close)
        if tag == 'p':
            blocks.append(('paragraph', RichText('<p>' + inner + '</p>')))
        elif tag in ('h2', 'h3', 'h4', 'h5', 'h6'):
            blocks.append(('heading', _strip_html(inner)))
        elif tag == 'blockquote':
            blocks.append(('blockquote', _strip_html(inner)))
    if not blocks and html:
        blocks.append(('paragraph', RichText(html)))
    return blocks


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


def _get_image_dimensions(content):
    try:
        from PIL import Image as PILImage
        pil = PILImage.open(io.BytesIO(content))
        return pil.width, pil.height
    except Exception:
        return 1, 1


def _create_cover_image_from_url(url, title):
    content, ext = _fetch_image_from_url(url)
    if content is None:
        return None
    Image = get_image_model()
    name = re.sub(r'[^\w\-]', '-', (title or 'cover')[:50]) + '.' + ext
    image = Image(title=name)
    image.file.save(name, ContentFile(content), save=False)
    w, h = _get_image_dimensions(content)
    image.width = w
    image.height = h
    image.save()
    return image


def _ext_from_data_url(data_url):
    m = re.match(r'data:image/(\w+);base64,', data_url, re.I)
    if m:
        ct = m.group(1).lower()
        if ct == 'jpeg':
            return 'jpg'
        if ct in ('png', 'gif', 'webp'):
            return ct
        return 'jpg'
    return None


def _ext_from_magic(content):
    if content[:8] == b'\x89PNG\r\n\x1a\n':
        return 'png'
    if content[:2] == b'\xff\xd8':
        return 'jpg'
    if content[:6] in (b'GIF87a', b'GIF89a'):
        return 'gif'
    if content[:4] == b'RIFF' and content[8:12] == b'WEBP':
        return 'webp'
    return 'jpg'


def _create_cover_image_from_base64(b64_data, title):
    data = (b64_data or '').strip()
    if not data:
        return None
    ext = None
    if data.startswith('data:'):
        ext = _ext_from_data_url(data)
        if not ext:
            return None
        payload = data.split(',', 1)[1]
    else:
        payload = data
    try:
        content = base64.b64decode(payload)
    except Exception:
        return None
    if not content or len(content) < 12:
        return None
    if ext is None:
        ext = _ext_from_magic(content)
    Image = get_image_model()
    name = re.sub(r'[^\w\-]', '-', (title or 'cover')[:50]) + '.' + ext
    image = Image(title=name)
    image.file.save(name, ContentFile(content), save=False)
    w, h = _get_image_dimensions(content)
    image.width = w
    image.height = h
    image.save()
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
    cover_image_base64 = data.get('cover_image_base64')
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
    if cover_image_base64:
        main_image = _create_cover_image_from_base64(cover_image_base64, title)
        if main_image is None:
            return JsonResponse({'error': 'cover_image_base64 is invalid or not a supported image'}, status=400)
    elif cover_image_url:
        try:
            main_image = _create_cover_image_from_url(cover_image_url, title)
        except (OSError, ValueError, urllib.error.URLError) as e:
            return JsonResponse({'error': 'Invalid cover_image_url: %s' % str(e)}, status=400)
        if main_image is None:
            return JsonResponse({'error': 'cover_image_url did not return a valid image'}, status=400)

    body_blocks = _parse_body_to_stream_blocks(body_html)

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
