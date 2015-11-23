# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('radio', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='song',
            name='emotions',
        ),
        migrations.AddField(
            model_name='song',
            name='angry',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='song',
            name='happy',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='song',
            name='party',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='song',
            name='rdio_key',
            field=models.CharField(max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='song',
            name='relaxed',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='song',
            name='sad',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='song',
            name='total_responses',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='song',
            name='artist',
            field=models.CharField(max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='song',
            name='language',
            field=models.CharField(max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='song',
            name='title',
            field=models.CharField(max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='song',
            name='year',
            field=models.IntegerField(null=True),
        ),
    ]
