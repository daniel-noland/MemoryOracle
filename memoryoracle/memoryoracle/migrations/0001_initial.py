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
                ('id', models.CharField(default='26af7403-b279-458b-b23e-d29570680e90', serialize=False, primary_key=True, max_length=36)),
                ('name', models.CharField(max_length=200)),
                ('vcs_hash', models.CharField(max_length=200, unique=True)),
                ('branch_name', models.CharField(max_length=200)),
            ],
            options={
                'db_table': 'commit',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Execution',
            fields=[
                ('id', models.CharField(default='26af7403-b279-458b-b23e-d29570680e90', serialize=False, primary_key=True, max_length=36)),
                ('name', models.CharField(max_length=200)),
                ('id_commit', models.ForeignKey(to='memoryoracle.Commit')),
            ],
            options={
                'db_table': 'execution',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Memory',
            fields=[
                ('id', models.CharField(default='26af7403-b279-458b-b23e-d29570680e90', serialize=False, primary_key=True, max_length=36)),
                ('name', models.CharField(max_length=200)),
                ('address', models.CharField(max_length=64)),
                ('has_symbol', models.BooleanField(default=False)),
                ('data', models.TextField()),
                ('id_execution', models.ForeignKey(to='memoryoracle.Execution')),
            ],
            options={
                'db_table': 'memory',
                'managed': True,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ObjectFile',
            fields=[
                ('id', models.CharField(default='26af7403-b279-458b-b23e-d29570680e90', serialize=False, primary_key=True, max_length=36)),
                ('name', models.CharField(max_length=200)),
                ('path', models.CharField(max_length=200)),
                ('size', models.BigIntegerField()),
                ('id_commit', models.ForeignKey(to='memoryoracle.Commit')),
            ],
            options={
                'db_table': 'object_file',
                'managed': True,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Program',
            fields=[
                ('id', models.CharField(default='26af7403-b279-458b-b23e-d29570680e90', serialize=False, primary_key=True, max_length=36)),
                ('name', models.CharField(max_length=200)),
            ],
            options={
                'db_table': 'program',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SourceFile',
            fields=[
                ('id', models.CharField(default='26af7403-b279-458b-b23e-d29570680e90', serialize=False, primary_key=True, max_length=36)),
                ('name', models.CharField(max_length=200)),
                ('path', models.CharField(max_length=200)),
                ('size', models.BigIntegerField()),
                ('lines', models.BigIntegerField()),
                ('id_commit', models.ForeignKey(to='memoryoracle.Commit')),
            ],
            options={
                'db_table': 'source_file',
                'managed': True,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Symbol',
            fields=[
                ('id', models.CharField(default='26af7403-b279-458b-b23e-d29570680e90', serialize=False, primary_key=True, max_length=36)),
                ('name', models.CharField(max_length=200)),
                ('id_execution', models.ForeignKey(to='memoryoracle.Execution')),
            ],
            options={
                'db_table': 'symbol',
                'managed': True,
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='commit',
            name='id_program',
            field=models.ForeignKey(to='memoryoracle.Program'),
            preserve_default=True,
        ),
    ]
