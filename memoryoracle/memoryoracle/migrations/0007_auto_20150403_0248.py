# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('memoryoracle', '0006_program_path'),
    ]

    operations = [
        migrations.CreateModel(
            name='Executable',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('name', models.TextField(default=None)),
                ('path', models.TextField(default='./a.out')),
            ],
            options={
                'db_table': 'executable',
            },
        ),
        migrations.CreateModel(
            name='Type',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('name', models.TextField(default=None)),
            ],
            options={
                'db_table': 'type',
                'managed': True,
            },
        ),
        migrations.RemoveField(
            model_name='execution',
            name='id_commit',
        ),
        migrations.RemoveField(
            model_name='program',
            name='path',
        ),
        migrations.AlterField(
            model_name='commit',
            name='name',
            field=models.TextField(default=None),
        ),
        migrations.AlterField(
            model_name='execution',
            name='name',
            field=models.TextField(default=None),
        ),
        migrations.AlterField(
            model_name='memory',
            name='name',
            field=models.TextField(default=None),
        ),
        migrations.AlterField(
            model_name='objectfile',
            name='name',
            field=models.TextField(default=None),
        ),
        migrations.AlterField(
            model_name='program',
            name='name',
            field=models.TextField(default=None),
        ),
        migrations.AlterField(
            model_name='sourcefile',
            name='name',
            field=models.TextField(default=None),
        ),
        migrations.AlterField(
            model_name='symbol',
            name='name',
            field=models.TextField(default=None),
        ),
        migrations.AddField(
            model_name='executable',
            name='id_commit',
            field=models.ForeignKey(to='memoryoracle.Commit'),
        ),
        migrations.AddField(
            model_name='execution',
            name='id_executable',
            field=models.ForeignKey(to='memoryoracle.Executable', default=None),
        ),
    ]
