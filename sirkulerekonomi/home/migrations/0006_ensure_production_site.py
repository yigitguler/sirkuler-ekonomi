from django.db import migrations


PRODUCTION_HOSTNAME = 'sirkulerekonomi.com'
PRODUCTION_PORT = 443


def ensure_production_site(apps, schema_editor):
    Site = apps.get_model('wagtailcore', 'Site')
    HomePage = apps.get_model('home', 'HomePage')
    home = HomePage.objects.filter(slug='ana-sayfa').first()
    if not home:
        return

    site, created = Site.objects.get_or_create(
        hostname=PRODUCTION_HOSTNAME,
        defaults={
            'port': PRODUCTION_PORT,
            'root_page_id': home.id,
            'is_default_site': True,
            'site_name': 'Sirküler Ekonomi',
        },
    )
    if not created:
        site.port = PRODUCTION_PORT
        site.root_page_id = home.id
        site.is_default_site = True
        site.site_name = 'Sirküler Ekonomi'
        site.save(update_fields=['port', 'root_page_id', 'is_default_site', 'site_name'])

    Site.objects.exclude(hostname=PRODUCTION_HOSTNAME).update(is_default_site=False)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0005_add_english_locale'),
    ]

    operations = [
        migrations.RunPython(ensure_production_site, noop),
    ]
