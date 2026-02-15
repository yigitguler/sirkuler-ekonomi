from django.db import migrations


def set_site_roots_to_homepage(apps, schema_editor):
    Site = apps.get_model('wagtailcore', 'Site')
    HomePage = apps.get_model('home', 'HomePage')
    home = HomePage.objects.filter(slug='ana-sayfa').first()
    if not home:
        return
    Site.objects.all().update(root_page_id=home.id)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0003_add_localhost_site'),
    ]

    operations = [
        migrations.RunPython(set_site_roots_to_homepage, noop),
    ]
