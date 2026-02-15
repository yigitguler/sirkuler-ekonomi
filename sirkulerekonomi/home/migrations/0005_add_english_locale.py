from django.db import migrations


def add_english_locale(apps, schema_editor):
    Locale = apps.get_model('wagtailcore', 'Locale')
    if Locale.objects.filter(language_code='en').exists():
        return
    Locale.objects.create(language_code='en')


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0004_set_site_roots_to_homepage'),
        ('wagtailcore', '0096_referenceindex_referenceindex_source_object_and_more'),
    ]

    operations = [
        migrations.RunPython(add_english_locale, noop),
    ]
