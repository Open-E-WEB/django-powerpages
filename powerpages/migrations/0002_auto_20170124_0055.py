# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-01-24 00:55
from __future__ import unicode_literals

from django.db import migrations, models
import powerpages.dbfields


class Migration(migrations.Migration):

    dependencies = [
        ('powerpages', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='page',
            name='description',
            field=models.TextField(blank=True, default='', verbose_name='Description'),
        ),
        migrations.AlterField(
            model_name='page',
            name='keywords',
            field=models.TextField(blank=True, default='', verbose_name='Keywords'),
        ),
        migrations.AlterField(
            model_name='page',
            name='page_processor',
            field=powerpages.dbfields.PageProcessorField(default='powerpages.DefaultPageProcessor', help_text='Python program used to render this page.', max_length=128, verbose_name='Page Processor'),
        ),
        migrations.AlterField(
            model_name='page',
            name='template',
            field=models.TextField(blank=True, default='', help_text="Parent's template is used as the base template for current page.", verbose_name='Template'),
        ),
        migrations.AlterField(
            model_name='page',
            name='title',
            field=models.CharField(blank=True, default='', max_length=512, verbose_name='Title'),
        ),
    ]
