# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.test import TestCase
from django.template import Template, Context
from django.utils import six

from powerpages.models import Page


class TemplateTagsTestCase(TestCase):

    maxDiff = None

    def test_page_url_alias(self):
        Page.objects.create(url='/test-page/', alias='test_page')
        template = Template(
            '{% load powerpages_tags %}{% page_url test_page %}'
        )
        context = Context()
        output = template.render(context)
        self.assertEqual(output, '/test-page/')

    def test_page_url_django_view(self):
        Page.objects.create(url='/test-page/', alias='test_page')
        template = Template(
            '{% load powerpages_tags %}{% page_url page path="test-page/" %}'
        )
        context = Context()
        output = template.render(context)
        self.assertEqual(output, '/test-page/')

    def test_current_page_info_edit_mode_enabled(self):
        Page.objects.create(
            url='/', alias='home', title="Home Page",
            template='{% current_page_info %}'
        )
        session = self.client.session
        session['WEBSITE_EDIT_MODE'] = True
        session.save()
        response = self.client.get('/')
        content = response.content
        if not isinstance(content, six.text_type):
            content = content.decode('utf-8')
        self.assertEqual(
            content,
            '''
<link rel="stylesheet" href="/static/powerpages/css/current_page_info.css">
<div class="current-page-info">
<h5>Page Information:</h5>
<ul>
<li><span>Name: </span><strong>Home Page</strong></li>
<li><span>Alias: </span><strong>home</strong></li>
<li><span>ID: </span><strong>1</strong></li>
<li><a href="/admin/powerpages/page/1/change/">edit in Admin &raquo;</a></li>
<li>
<a href="/powerpages-admin/switch-edit-mode/">disable Edit Mode &raquo;</a>
</li>
</ul>
</div>
            '''.strip().replace('\n', '')
        )

    def test_current_page_info_edit_mode_disabled(self):
        Page.objects.create(
            url='/', alias='home', title="Home Page",
            template='{% current_page_info %}'
        )
        # NO EDIT MODE ENABLED
        response = self.client.get('/')
        content = response.content
        if not isinstance(content, six.text_type):
            content = content.decode('utf-8')
        self.assertEqual(content, '')
