# Generated by Django 2.0.6 on 2018-06-16 23:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('learn', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='wordprogress',
            name='interval',
            field=models.PositiveIntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='wordprogress',
            name='last_review',
            field=models.PositiveIntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='statistics',
            name='srs_sessions',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='statistics',
            name='total_reviews',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='statistics',
            name='wrong_guesses',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='wordprogress',
            name='easy_factor',
            field=models.FloatField(default=2.5),
        ),
        migrations.AlterField(
            model_name='wordprogress',
            name='total_reviews',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='wordprogress',
            name='wrong_guesses',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
