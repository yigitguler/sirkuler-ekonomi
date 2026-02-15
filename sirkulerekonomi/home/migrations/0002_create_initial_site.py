from django.conf import settings
from django.db import migrations


def create_initial_site(apps, schema_editor):
    Page = apps.get_model('wagtailcore', 'Page')
    Site = apps.get_model('wagtailcore', 'Site')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    Locale = apps.get_model('wagtailcore', 'Locale')
    HomePage = apps.get_model('home', 'HomePage')
    ArticleIndexPage = apps.get_model('articles', 'ArticleIndexPage')

    if HomePage.objects.exists():
        return

    root = Page.objects.filter(depth=1).first()
    if not root:
        page_content_type = ContentType.objects.get(app_label='wagtailcore', model='page')
        root = Page.objects.create(
            title='Root',
            slug='root',
            content_type=page_content_type,
            path='0001',
            depth=1,
            numchild=0,
            url_path='/',
            live=True,
        )
    default_locale = Locale.objects.first()
    if not default_locale:
        default_locale = Locale.objects.create(language_code='tr')

    def next_path(parent_path, parent_numchild):
        return parent_path + format(parent_numchild + 1, '04d')

    home_path = next_path(root.path, root.numchild)
    home_content_type = ContentType.objects.get(app_label='home', model='homepage')
    home = HomePage(
        title='Ana Sayfa',
        slug='ana-sayfa',
        content_type=home_content_type,
        path=home_path,
        depth=2,
        numchild=0,
        url_path='/ana-sayfa/',
        live=True,
        locale=default_locale,
    )
    home.save()

    index_path = next_path(home.path, home.numchild)
    index_content_type = ContentType.objects.get(app_label='articles', model='articleindexpage')
    index = ArticleIndexPage(
        title='Haberler',
        slug='haberler',
        content_type=index_content_type,
        path=index_path,
        depth=3,
        numchild=0,
        url_path='/ana-sayfa/haberler/',
        live=True,
        locale=default_locale,
    )
    index.save()

    root.numchild += 1
    root.save(update_fields=['numchild'])
    home.numchild += 1
    home.save(update_fields=['numchild'])

    base_url = getattr(settings, 'SITE_BASE_URL', 'https://sirkulerekonomi.com')
    hostname = base_url.replace('https://', '').replace('http://', '').split('/')[0].split(':')[0]
    port = 443 if base_url.startswith('https') else 80
    if not Site.objects.filter(hostname=hostname).exists():
        Site.objects.create(
            hostname=hostname,
            port=port,
            root_page_id=home.id,
            is_default_site=True,
            site_name='Sirküler Ekonomi',
        )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ('home', '0001_initial'),
        ('articles', '0001_initial'),
        ('wagtailcore', '0096_referenceindex_referenceindex_source_object_and_more'),
    ]

    operations = [
        migrations.RunPython(create_initial_site, noop),
    ]
