# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django_pgjson.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Song',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=500)),
                ('artist', models.CharField(max_length=500)),
                ('year', models.IntegerField()),
                ('language', models.CharField(max_length=500)),
                ('emotions', django_pgjson.fields.JsonField()),
            ],
        ),
    ]
