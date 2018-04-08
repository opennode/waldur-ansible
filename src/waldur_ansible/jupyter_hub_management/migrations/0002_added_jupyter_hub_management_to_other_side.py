# -*- coding: utf-8 -*-
# Generated by Django 1.11.9 on 2018-04-06 08:51
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('jupyter_hub_management', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='jupyterhubmanagement',
            name='python_management',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='jupyter_hub_management', to='python_management.PythonManagement'),
        ),
    ]
