# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('memoryoracle', '0004_auto_20150402_2000'),
    ]

    operations = [
        migrations.AlterField(
            model_name='commit',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='execution',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='memory',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='objectfile',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='program',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='sourcefile',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='symbol',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False),
            preserve_default=True,
        ),
    ]
