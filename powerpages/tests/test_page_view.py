# -*- coding: utf-8 -*-

from django.test import TestCase
from django.test.utils import override_settings
from django.core.cache import cache

from powerpages.models import Page
from powerpages import cachekeys


class PageViewTestCase(TestCase):

    # Default Processor:

    def test_page_view_ok(self):
        Page.objects.create(
            url='/test/',
            template='<h1>Hello world!</h1>'
        )
        response = self.client.get('/test/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<h1>Hello world!</h1>')

    def test_page_view_ok_template_inheritance(self):
        Page.objects.create(
            url='/',
            template="""
            <h1>{% block header %}Root{% endblock %}</h1>
            """
        )
        Page.objects.create(
            url='/a/',
            template="""
            {% block header %}Child{% endblock %}
            """
        )
        Page.objects.create(
            url='/a/b/',
            template="""
            {% block header %}Grand{{ block.super }}{% endblock %}
            """
        )
        root_response = self.client.get('/')
        self.assertEqual(root_response.status_code, 200)
        self.assertContains(root_response, '<h1>Root</h1>')

        child_response = self.client.get('/a/')
        self.assertEqual(child_response.status_code, 200)
        self.assertContains(child_response, '<h1>Child</h1>')

        grandchild_response = self.client.get('/a/b/')
        self.assertEqual(grandchild_response.status_code, 200)
        self.assertContains(grandchild_response, '<h1>GrandChild</h1>')

    def test_page_view_ok_custom_base_template(self):
        root = Page.objects.create(
            url='/',
            template="""
            <h1>{% block header %}Root{% endblock %}</h1>
            """
        )
        Page.objects.create(
            url='/a/',
            template="""
            {% block header %}Child{% endblock %}
            """
        )
        Page.objects.create(
            url='/a/b/',
            template="""
            {% block header %}Grand{{ block.super }}{% endblock %}
            """,
            page_processor_config={
                'base template': 'page/{0}'.format(root.pk)
            }
        )

        grandchild_response = self.client.get('/a/b/')
        self.assertEqual(grandchild_response.status_code, 200)
        self.assertContains(grandchild_response, '<h1>GrandRoot</h1>')

    def test_page_view_ok_page_context(self):
        Page.objects.create(
            url='/',
            template="""<title>{{ website_page.title }}</page>
<meta name="keywords" content="{{ website_page.keywords }}">
<meta name="description" content="{{ website_page.description }}">""",
            title="TITLE",
            description="DESCRIPTION",
            keywords="KEYWORDS"
        )
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            """<title>TITLE</page>
<meta name="keywords" content="KEYWORDS">
<meta name="description" content="DESCRIPTION">"""
        )

    def test_page_view_ok_custom_context_processor(self):
        Page.objects.create(
            url='/',
            template="<h1>Magic Number is {{ magic_number }}!</h1>",
            page_processor_config={
                'context processors': [
                    'powerpages.tests.utils.context_processor'
                ]
            }
        )
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<h1>Magic Number is 42!</h1>")

    def test_page_view_ok_request_context_processor(self):
        Page.objects.create(
            url='/',
            template="<p>HTTP method was: {{ request.method }}</p>",
        )
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<p>HTTP method was: GET</p>")

    def test_page_view_ok_tags_available(self):
        Page.objects.create(
            url='/test/',
            template='<a href="{% page_url other-page %}">Other</a>'
        )
        Page.objects.create(
            url='/other/',
            alias='other-page'
        )
        response = self.client.get('/test/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<a href="/other/">Other</a>')

    def test_page_view_ok_custom_tags(self):
        Page.objects.create(
            url='/test/',
            template="<h1>Magic Number is {% get_magic_number %}!</h1>",
            page_processor_config={
                'tag libraries': ['powerpages_test']
            }
        )
        response = self.client.get('/test/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<h1>Magic Number is 42!</h1>")

    def test_page_view_ok_custom_headers(self):
        Page.objects.create(
            url='/test/',
            page_processor_config={
                'headers': {'X-Magic-Number': '42'}
            }
        )
        response = self.client.get('/test/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['X-Magic-Number'], '42')

    @override_settings(
        CACHES={
            'default': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                'LOCATION': 'powerpages-test'
            }
        }
    )
    def test_page_view_ok_with_cache(self):
        page = Page.objects.create(
            url='/test/',
            template='<h1>Hello world!</h1>',
            page_processor_config={'cache': 15}  # cache for 15 seconds
        )
        cache_key = cachekeys.rendered_source_for_lang(page.pk, 'en')
        self.assertNotIn(cache_key, cache)
        response = self.client.get('/test/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<h1>Hello world!</h1>')
        self.assertIn(cache_key, cache)

    # Not Found Processor:

    def test_page_view_not_found(self):
        Page.objects.create(
            url='/test/',
            template='<h1>Hello world!</h1>',
            page_processor='powerpages.NotFoundProcessor'
        )
        response = self.client.get('/test/')
        self.assertEqual(response.status_code, 404)

    # Redirect Processor:

    def test_page_view_redirect(self):
        Page.objects.create(
            url='/test/',
            template='<h1>Hello world!</h1>',
            page_processor='powerpages.RedirectProcessor',
        )
        response = self.client.get('/test/')
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response['Location'], '/')

    def test_page_view_redirect_to_url(self):
        Page.objects.create(
            url='/old/',
            page_processor='powerpages.RedirectProcessor',
            page_processor_config={'to url': '/new/'}
        )
        Page.objects.create(
            url='/new/',
        )
        response = self.client.get('/old/')
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response['Location'], '/new/')

    def test_page_view_redirect_to_alias(self):
        Page.objects.create(
            url='/old/',
            page_processor='powerpages.RedirectProcessor',
            page_processor_config={'to alias': 'new_page'}
        )
        Page.objects.create(
            url='/new/',
            alias='new_page'
        )
        response = self.client.get('/old/')
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response['Location'], '/new/')

    def test_page_view_redirect_302(self):
        Page.objects.create(
            url='/old/',
            page_processor='powerpages.RedirectProcessor',
            page_processor_config={'to url': '/new/', 'permanent': False}
        )
        Page.objects.create(
            url='/new/',
            alias='new_page'
        )
        response = self.client.get('/old/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/new/')
