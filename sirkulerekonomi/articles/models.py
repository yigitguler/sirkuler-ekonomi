import json
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

    parent_page_types = ['articles.ArticleIndexPage']

    class Meta:
        verbose_name = 'Yazı'
        verbose_name_plural = 'Yazılar'

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        schema = {
            '@context': 'https://schema.org',
            '@type': 'NewsArticle',
            'headline': self.title,
            'description': (self.intro or '')[:500],
            'datePublished': self.first_published_at.isoformat() if self.first_published_at else None,
            'dateModified': self.last_published_at.isoformat() if getattr(self, 'last_published_at', None) else None,
            'url': self.full_url,
            'publisher': {
                '@type': 'Organization',
                'name': 'Sirküler Ekonomi',
            },
        }
        if self.main_image:
            rend = self.main_image.get_rendition('width-1200')
            base = request.scheme + '://' + request.get_host()
            schema['image'] = base + rend.url if rend.url.startswith('/') else rend.url
        schema = {k: v for k, v in schema.items() if v is not None}
        json_str = json.dumps(schema, ensure_ascii=False)
        context['article_schema_json'] = json_str.replace('</', r'<\/')
        return context

    def get_sitemap_urls(self, request=None):
        urls = super().get_sitemap_urls(request=request)
        lastmod = getattr(self, 'last_published_at', None) or self.latest_revision_created_at
        if lastmod and urls:
            for entry in urls:
                entry['lastmod'] = lastmod
        return urls
