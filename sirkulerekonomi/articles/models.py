import json
from django.conf import settings
from django.db import models
from wagtail import blocks
from wagtail.models import Page
from wagtail.fields import StreamField
from wagtail.images.blocks import ImageChooserBlock
from wagtail.admin.panels import FieldPanel
from wagtail.search import index


class ArticleIndexPage(Page):
    subpage_types = ['articles.ArticlePage']
    max_count = 1

    class Meta:
        verbose_name = 'Yazı listesi'
        verbose_name_plural = 'Yazı listeleri'

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context['articles'] = ArticlePage.objects.live().child_of(self).select_related('main_image').order_by('-first_published_at')
        return context


class ArticlePage(Page):
    intro = models.CharField(max_length=500, blank=True, verbose_name='Özet')
    meta_keywords = models.CharField(max_length=255, blank=True, verbose_name='Meta keywords')
    main_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name='Kapak görseli'
    )
    body = StreamField([
        ('heading', blocks.CharBlock(form_classname='title', label='Başlık')),
        ('paragraph', blocks.RichTextBlock(label='Paragraf', features=['bold', 'italic', 'link', 'ol', 'ul'])),
        ('image', ImageChooserBlock(label='Görsel')),
        ('blockquote', blocks.BlockQuoteBlock(label='Alıntı')),
    ], use_json_field=True, blank=True, verbose_name='İçerik')

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
        index.SearchField('body'),
    ]

    content_panels = Page.content_panels + [
        FieldPanel('intro'),
        FieldPanel('main_image'),
        FieldPanel('body'),
    ]

    promote_panels = Page.promote_panels + [
        FieldPanel('meta_keywords'),
    ]

    parent_page_types = ['articles.ArticleIndexPage']

    class Meta:
        verbose_name = 'Yazı'
        verbose_name_plural = 'Yazılar'

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        base = getattr(settings, 'SITE_BASE_URL', '').rstrip('/')
        if not base and request:
            base = request.scheme + '://' + request.get_host()
        article_url = (base + self.get_url()) if base else self.full_url
        description = (self.search_description or self.intro or '')[:500]
        schema = {
            '@context': 'https://schema.org',
            '@type': 'NewsArticle',
            'mainEntityOfPage': {'@type': 'WebPage', '@id': article_url},
            'headline': self.title,
            'description': description,
            'datePublished': self.first_published_at.isoformat() if self.first_published_at else None,
            'dateModified': self.last_published_at.isoformat() if getattr(self, 'last_published_at', None) else None,
            'url': article_url,
            'publisher': {
                '@type': 'Organization',
                'name': 'Sirküler Ekonomi',
            },
            'author': {'@type': 'Organization', 'name': 'Sirküler Ekonomi'},
        }
        if self.main_image:
            rend_1200 = self.main_image.get_rendition('width-1200')
            rend_900 = self.main_image.get_rendition('width-900')
            img_url = (base + rend_1200.url) if base and rend_1200.url.startswith('/') else (request.scheme + '://' + request.get_host() + rend_1200.url if request and rend_1200.url.startswith('/') else rend_1200.url)
            schema['image'] = [img_url]
            preload_path = rend_900.url
            context['main_image_preload_url'] = (base + preload_path) if base and preload_path.startswith('/') else (request.scheme + '://' + request.get_host() + preload_path if request and preload_path.startswith('/') else preload_path)
        else:
            context['main_image_preload_url'] = None
        schema = {k: v for k, v in schema.items() if v is not None}
        json_str = json.dumps(schema, ensure_ascii=False)
        context['article_schema_json'] = json_str.replace('</', r'<\/')
        root = base or (request.scheme + '://' + request.get_host() if request else '')
        if root:
            breadcrumb = {
                '@context': 'https://schema.org',
                '@type': 'BreadcrumbList',
                'itemListElement': [
                    {'@type': 'ListItem', 'position': 1, 'name': 'Anasayfa', 'item': root + '/'},
                    {'@type': 'ListItem', 'position': 2, 'name': 'Haberler', 'item': root + '/haberler/'},
                    {'@type': 'ListItem', 'position': 3, 'name': self.title, 'item': article_url},
                ],
            }
            bc_str = json.dumps(breadcrumb, ensure_ascii=False)
            context['breadcrumb_schema_json'] = bc_str.replace('</', r'<\/')
        else:
            context['breadcrumb_schema_json'] = None
        return context

    def get_sitemap_urls(self, request=None):
        urls = super().get_sitemap_urls(request=request)
        lastmod = getattr(self, 'last_published_at', None) or self.latest_revision_created_at
        if lastmod and urls:
            for entry in urls:
                entry['lastmod'] = lastmod
        return urls
