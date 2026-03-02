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


def _build_article_url(article):
    base_url = getattr(settings, 'SITE_BASE_URL', '').rstrip('/')
    return (base_url + article.get_url()) if base_url else article.get_url()


def _streamfield_body_to_html(article):
    """Serialize ArticlePage.body StreamField to a single HTML string."""
    parts = []
    base_url = getattr(settings, 'SITE_BASE_URL', '').rstrip('/')
    for block in article.body:
        if block.block_type == 'heading':
            text = str(block.value).strip()
            if text:
                parts.append('<h2>%s</h2>' % _escape_html(text))
        elif block.block_type == 'paragraph':
            rt = block.value
            if hasattr(rt, 'source') and rt.source:
                parts.append(rt.source.strip())
            else:
                parts.append('<p>%s</p>' % _escape_html(str(rt)))
        elif block.block_type == 'blockquote':
            text = str(block.value).strip()
            if text:
                parts.append('<blockquote>%s</blockquote>' % _escape_html(text))
        elif block.block_type == 'image' and block.value:
            img = block.value
            try:
                rend = img.get_rendition('width-1200')
                url = rend.url
                if base_url and url.startswith('/'):
                    url = base_url + url
                parts.append('<img src="%s" alt="%s" />' % (_escape_html(url), _escape_html(img.title or '')))
            except Exception:
                pass
    return ''.join(parts)


def _escape_html(s):
    if not s:
        return ''
    s = str(s)
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def _strip_html(html):
    return re.sub(r'<[^>]+>', '', html).strip()


def _markdown_to_html(md):
    if not (md or '').strip():
        return ''
    import markdown
    return markdown.markdown(md.strip(), extensions=['extra', 'nl2br'])


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


def _get_main_image_url(article, rendition_spec='width-600'):
    if not article.main_image_id:
        return None
    try:
        rend = article.main_image.get_rendition(rendition_spec)
        url = rend.url
        base_url = getattr(settings, 'SITE_BASE_URL', '').rstrip('/')
        if base_url and url.startswith('/'):
            url = base_url + url
        return url
    except Exception:
        return None


@csrf_exempt
@require_http_methods(['GET', 'POST'])
def article_list_or_create(request):
    if not _check_auth(request):
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    if request.method == 'GET':
        return get_article_list(request)
    return post_article(request)


def get_article_list(request):
    limit = min(int(request.GET.get('limit', 20)), 100)
    offset = int(request.GET.get('offset', 0))
    live_param = request.GET.get('live')
    locale_code = (request.GET.get('locale') or '').strip()

    qs = ArticlePage.objects.all().select_related('main_image', 'locale').order_by('-first_published_at')
    if live_param is not None and live_param != '':
        live_val = str(live_param).strip().lower() in ('true', '1', 'yes')
        qs = qs.filter(live=live_val)
    if locale_code:
        qs = qs.filter(locale__language_code=locale_code)

    count = qs.count()
    page = qs[offset:offset + limit]
    results = []
    for article in page:
        results.append({
            'id': article.pk,
            'title': article.title,
            'slug': article.slug,
            'url': _build_article_url(article),
            'intro': article.intro or '',
            'live': article.live,
            'first_published_at': article.first_published_at.isoformat() if article.first_published_at else None,
            'last_published_at': getattr(article, 'last_published_at', None)
            and article.last_published_at.isoformat() or None,
            'locale': article.locale.language_code if article.locale_id else None,
            'main_image_url': _get_main_image_url(article),
        })
    out = {'results': results, 'count': count}
    if offset + len(results) < count:
        out['next_offset'] = offset + limit
    if offset > 0:
        out['previous_offset'] = max(0, offset - limit)
    return JsonResponse(out)


def _get_article_or_404(pk):
    article = ArticlePage.objects.filter(pk=pk).select_related('main_image', 'locale').first()
    if not article:
        return None
    return article


@csrf_exempt
@require_http_methods(['GET', 'PATCH'])
def article_detail(request, id):
    if not _check_auth(request):
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    article = _get_article_or_404(id)
    if not article:
        return JsonResponse({'error': 'Not found'}, status=404)
    if request.method == 'GET':
        return get_article_detail(request, id)
    return patch_article(request, id)


def get_article_detail(request, id):
    article = _get_article_or_404(id)
    if not article:
        return JsonResponse({'error': 'Not found'}, status=404)
    data = {
        'id': article.pk,
        'title': article.title,
        'slug': article.slug,
        'url': _build_article_url(article),
        'intro': article.intro or '',
        'body': _streamfield_body_to_html(article),
        'main_image_url': _get_main_image_url(article, 'width-1200'),
        'meta_title': article.seo_title or '',
        'meta_description': article.search_description or '',
        'meta_keywords': article.meta_keywords or '',
        'live': article.live,
        'first_published_at': article.first_published_at.isoformat() if article.first_published_at else None,
        'last_published_at': getattr(article, 'last_published_at', None) and article.last_published_at.isoformat() or None,
        'locale': article.locale.language_code if article.locale_id else None,
    }
    return JsonResponse(data)


def patch_article(request, id):
    article = _get_article_or_404(id)
    if not article:
        return JsonResponse({'error': 'Not found'}, status=404)
    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    if 'title' in data:
        article.title = (data.get('title') or '').strip()
    if 'meta_title' in data:
        article.seo_title = (data.get('meta_title') or '').strip()[:70]
    if 'meta_description' in data:
        article.search_description = (data.get('meta_description') or '').strip()[:500]
    if 'intro' in data:
        article.intro = (data.get('intro') or '')[:500]
    if 'meta_keywords' in data:
        article.meta_keywords = (data.get('meta_keywords') or '')[:255]
    if 'body' in data:
        body_raw = data.get('body') or ''
        body_html = _markdown_to_html(body_raw)
        article.body = _parse_body_to_stream_blocks(body_html)
    if 'cover_image_url' in data or 'cover_image_base64' in data:
        cover_image_url = (data.get('cover_image_url') or '').strip()
        cover_image_base64 = data.get('cover_image_base64')
        main_image = None
        if cover_image_base64 is not None:
            main_image = _create_cover_image_from_base64(cover_image_base64, article.title)
        elif cover_image_url:
            try:
                main_image = _create_cover_image_from_url(cover_image_url, article.title)
            except (OSError, ValueError, urllib.error.URLError):
                main_image = None
        if main_image is not None:
            article.main_image = main_image
    if 'live' in data:
        live_val = data.get('live')
        if isinstance(live_val, str):
            live_val = live_val.strip().lower() in ('true', '1', 'yes')
        article.live = bool(live_val)

    revision = article.save_revision()
    if article.live and revision:
        revision.publish()

    base_url = getattr(settings, 'SITE_BASE_URL', '').rstrip('/')
    full_url = (base_url + article.get_url()) if base_url else article.get_url()
    return JsonResponse({
        'id': article.pk,
        'url': full_url,
        'slug': article.slug,
        'published': article.live,
    })


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
    body_raw = data.get('body') or ''
    body_html = _markdown_to_html(body_raw)
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
