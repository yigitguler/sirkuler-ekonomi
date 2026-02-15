from django.db import migrations


def add_localhost_site(apps, schema_editor):
    Site = apps.get_model('wagtailcore', 'Site')
    if Site.objects.filter(hostname='localhost').exists():
        return
    default_site = Site.objects.filter(is_default_site=True).first()
    if not default_site:
        return
    Site.objects.create(
        hostname='localhost',
        port=8000,
        root_page_id=default_site.root_page_id,
        is_default_site=False,
        site_name='Sirküler Ekonomi (Local)',
    )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0002_create_initial_site'),
    ]

    operations = [
        migrations.RunPython(add_localhost_site, noop),
    ]
