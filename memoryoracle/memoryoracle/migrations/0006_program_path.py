# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('memoryoracle', '0005_auto_20150403_0100'),
    ]

    operations = [
        migrations.AddField(
            model_name='program',
            name='path',
            field=models.TextField(default='./a.out'),
            preserve_default=True,
        ),
    ]
