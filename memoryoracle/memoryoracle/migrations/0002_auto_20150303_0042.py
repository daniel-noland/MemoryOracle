# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('memoryoracle', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='commit',
            options={'managed': True},
        ),
        migrations.AlterModelOptions(
            name='instance',
            options={'managed': True},
        ),
        migrations.AlterModelOptions(
            name='program',
            options={'managed': True},
        ),
        migrations.AlterModelOptions(
            name='value',
            options={'managed': True},
        ),
    ]
