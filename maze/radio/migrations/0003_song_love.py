# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('radio', '0002_auto_20151119_1832'),
    ]

    operations = [
        migrations.AddField(
            model_name='song',
            name='love',
            field=models.IntegerField(default=0),
        ),
    ]
