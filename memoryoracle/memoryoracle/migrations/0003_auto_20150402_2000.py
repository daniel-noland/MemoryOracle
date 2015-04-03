# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('memoryoracle', '0002_auto_20150402_2000'),
    ]

    operations = [
        migrations.AlterField(
            model_name='commit',
            name='id',
            field=models.CharField(primary_key=True, serialize=False, max_length=36, default='6eda6197-045e-489d-8251-2b56db6fee0b'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='execution',
            name='id',
            field=models.CharField(primary_key=True, serialize=False, max_length=36, default='6eda6197-045e-489d-8251-2b56db6fee0b'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='memory',
            name='id',
            field=models.CharField(primary_key=True, serialize=False, max_length=36, default='6eda6197-045e-489d-8251-2b56db6fee0b'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='objectfile',
            name='id',
            field=models.CharField(primary_key=True, serialize=False, max_length=36, default='6eda6197-045e-489d-8251-2b56db6fee0b'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='program',
            name='id',
            field=models.CharField(primary_key=True, serialize=False, max_length=36, default='6eda6197-045e-489d-8251-2b56db6fee0b'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='sourcefile',
            name='id',
            field=models.CharField(primary_key=True, serialize=False, max_length=36, default='6eda6197-045e-489d-8251-2b56db6fee0b'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='symbol',
            name='id',
            field=models.CharField(primary_key=True, serialize=False, max_length=36, default='6eda6197-045e-489d-8251-2b56db6fee0b'),
            preserve_default=True,
        ),
    ]
