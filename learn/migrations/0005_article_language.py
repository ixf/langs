# Generated by Django 2.0.6 on 2018-06-20 09:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('learn', '0004_remove_wordprogress_last_review'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='language',
            field=models.CharField(default='de', max_length=8),
            preserve_default=False,
        ),
    ]