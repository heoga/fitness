# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-06-10 05:58
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fitness', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='point',
            name='cadence',
            field=models.FloatField(null=True),
        ),
        migrations.AlterField(
            model_name='point',
            name='heart_rate',
            field=models.FloatField(null=True),
        ),
    ]