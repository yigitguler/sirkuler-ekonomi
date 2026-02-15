from django.contrib.syndication.views import Feed
from django.utils.feedgenerator import DefaultFeed
from wagtail.models import Site


class ArticleFeed(Feed):
    feed_type = DefaultFeed
    title = 'Sirküler Ekonomi – Haberler'
    link = '/haberler/'
    description = 'Sürdürülebilirlik ve döngüsel ekonomi haberleri'

    def get_feed(self, obj, request):
        self.request = request
        return super().get_feed(obj, request)

    def items(self):
        from articles.models import ArticlePage
        site = Site.find_for_request(self.request)
        if not site or not site.root_page:
            return ArticlePage.objects.none()
        return ArticlePage.objects.live().descendant_of(site.root_page).order_by('-first_published_at')[:20]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.intro or ''

    def item_link(self, item):
        return item.get_full_url()

    def item_pubdate(self, item):
        return item.first_published_at
