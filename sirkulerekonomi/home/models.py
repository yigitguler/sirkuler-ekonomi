from wagtail.models import Page


class HomePage(Page):
    subpage_types = ['articles.ArticleIndexPage']

    class Meta:
        verbose_name = 'Ana Sayfa'
        verbose_name_plural = 'Ana Sayfalar'

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        from articles.models import ArticlePage
        context['articles'] = ArticlePage.objects.live().descendant_of(self).select_related('main_image').order_by('-first_published_at')[:9]
        return context

    def get_sitemap_urls(self, request=None):
        from articles.models import ArticlePage
        urls = super().get_sitemap_urls(request=request)
        latest = ArticlePage.objects.live().descendant_of(self).order_by('-first_published_at').values_list('first_published_at', flat=True).first()
        if latest and urls:
            for entry in urls:
                entry['lastmod'] = latest
        return urls
