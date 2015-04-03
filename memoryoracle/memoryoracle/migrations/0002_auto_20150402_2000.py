# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('memoryoracle', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='commit',
            name='id',
            field=models.CharField(serialize=False, default='9b0f3ce4-775c-4690-9588-ff3be5b23d04', max_length=36, primary_key=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='execution',
            name='id',
            field=models.CharField(serialize=False, default='9b0f3ce4-775c-4690-9588-ff3be5b23d04', max_length=36, primary_key=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='memory',
            name='id',
            field=models.CharField(serialize=False, default='9b0f3ce4-775c-4690-9588-ff3be5b23d04', max_length=36, primary_key=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='objectfile',
            name='id',
            field=models.CharField(serialize=False, default='9b0f3ce4-775c-4690-9588-ff3be5b23d04', max_length=36, primary_key=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='program',
            name='id',
            field=models.CharField(serialize=False, default='9b0f3ce4-775c-4690-9588-ff3be5b23d04', max_length=36, primary_key=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='sourcefile',
            name='id',
            field=models.CharField(serialize=False, default='9b0f3ce4-775c-4690-9588-ff3be5b23d04', max_length=36, primary_key=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='symbol',
            name='id',
            field=models.CharField(serialize=False, default='9b0f3ce4-775c-4690-9588-ff3be5b23d04', max_length=36, primary_key=True),
            preserve_default=True,
        ),
    ]
