# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
#
# Also note: You'll have to insert the output of 'django-admin.py sqlcustom [app_label]'
# into your database.
from __future__ import unicode_literals

from django.db import models


class Commit(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    id_program = models.ForeignKey('Program', db_column='id_program')
    vcs_hash = models.CharField(max_length=200, blank=True)

    class Meta:
        managed = False
        db_table = 'commit'


class Instance(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    id_commit = models.ForeignKey(Commit, db_column='id_commit', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'instance'


class Program(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    path = models.CharField(unique=True, max_length=200)

    class Meta:
        managed = False
        db_table = 'program'


class Value(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    id_instance = models.ForeignKey(Instance, db_column='id_instance')
    name = models.CharField(max_length=200)
    value = models.TextField(blank=True)

    class Meta:
        managed = False
        db_table = 'value'
