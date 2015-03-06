# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Commit',
            fields=[
                ('id', models.CharField(serialize=False, max_length=36, primary_key=True)),
                ('vcs_hash', models.CharField(blank=True, max_length=200)),
            ],
            options={
                'managed': False,
                'db_table': 'commit',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Instance',
            fields=[
                ('id', models.CharField(serialize=False, max_length=36, primary_key=True)),
            ],
            options={
                'managed': False,
                'db_table': 'instance',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Program',
            fields=[
                ('id', models.CharField(serialize=False, max_length=36, primary_key=True)),
                ('path', models.CharField(max_length=200, unique=True)),
            ],
            options={
                'managed': False,
                'db_table': 'program',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Value',
            fields=[
                ('id', models.CharField(serialize=False, max_length=36, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('value', models.TextField(blank=True)),
            ],
            options={
                'managed': False,
                'db_table': 'value',
            },
            bases=(models.Model,),
        ),
    ]
