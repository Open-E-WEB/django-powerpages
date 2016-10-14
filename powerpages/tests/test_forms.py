# -*- coding: utf-8 -*-

import yaml

from django.test import TestCase

from powerpages.models import Page
from powerpages.forms import PageAdminForm


class PageFormTestCase(TestCase):

    maxDiff = None

    def test_valid_form_data_default_page_processor_root(self):
        data = {
            'url': '/',
            'alias': 'root',
            'description': 'At vero eos et accusamus et iusto odio',
            'keywords': 'lorem ipsum dolor sit amet',
            'page_processor': 'powerpages.DefaultPageProcessor',
            'page_processor_config': '',
            'template': '<h1>{{ website_page.title }}</h1>\n',
            'title': 'De Finibus Bonorum et Malorum'
        }
        form = PageAdminForm(data, instance=Page())
        self.assertTrue(form.is_valid())
        self.assertEqual(
            form.cleaned_data,
            {
                'url': '/',
                'alias': 'root',
                'description': 'At vero eos et accusamus et iusto odio',
                'keywords': 'lorem ipsum dolor sit amet',
                'page_processor': 'powerpages.DefaultPageProcessor',
                'page_processor_config': None,
                'template': '<h1>{{ website_page.title }}</h1>\n',
                'title': 'De Finibus Bonorum et Malorum'
            },
        )

    def test_valid_form_data_default_page_processor(self):
        Page.objects.create(url='/')
        data = {
            'url': '/test/',
            'alias': 'test-page',
            'description': 'At vero eos et accusamus et iusto odio',
            'keywords': 'lorem ipsum dolor sit amet',
            'page_processor': 'powerpages.DefaultPageProcessor',
            'page_processor_config': '',
            'template': '<h1>{{ website_page.title }}</h1>\n',
            'title': 'De Finibus Bonorum et Malorum'
        }
        form = PageAdminForm(data, instance=Page())
        self.assertTrue(form.is_valid())
        self.assertDictEqual(
            form.cleaned_data,
            {
                'url': '/test/',
                'alias': 'test-page',
                'description': 'At vero eos et accusamus et iusto odio',
                'keywords': 'lorem ipsum dolor sit amet',
                'page_processor': 'powerpages.DefaultPageProcessor',
                'page_processor_config': None,
                'template': '<h1>{{ website_page.title }}</h1>\n',
                'title': 'De Finibus Bonorum et Malorum'
            }
        )

    def test_valid_form_data_redirect_processor(self):
        data = {
            'url': '/test/',
            'alias': 'test-page',
            'description': 'At vero eos et accusamus et iusto odio',
            'keywords': 'lorem ipsum dolor sit amet',
            'page_processor': 'powerpages.RedirectProcessor',
            'page_processor_config': yaml.dump({
                'to url': '/test/'
            }),
            'template': '<h1>{{ website_page.title }}</h1>\n',
            'title': 'De Finibus Bonorum et Malorum'
        }
        form = PageAdminForm(data, instance=Page())
        self.assertTrue(form.is_valid())
        self.assertDictEqual(
            form.cleaned_data,
            {
                'url': '/test/',
                'alias': 'test-page',
                'description': 'At vero eos et accusamus et iusto odio',
                'keywords': 'lorem ipsum dolor sit amet',
                'page_processor': 'powerpages.RedirectProcessor',
                'page_processor_config': {
                    'to url': '/test/'
                },
                'template': '<h1>{{ website_page.title }}</h1>\n',
                'title': 'De Finibus Bonorum et Malorum'
            }
        )

    def test_valid_form_data_normalization(self):
        data = {
            'url': '/test/      ',
            'alias': 'test-page   ',
            'description': 'At vero eos et accusamus et iusto odio\n\n',
            'keywords': '   lorem ipsum dolor sit amet',
            'page_processor': 'powerpages.RedirectProcessor',
            'page_processor_config': {
                'to url': '/test/'
            },
            'template': '\n\t<h1>{{ website_page.title }}</h1>\n   \n\n\r\n',
            'title': '  De Finibus Bonorum et Malorum  \t'
        }
        form = PageAdminForm(data, instance=Page())
        self.assertTrue(form.is_valid())
        self.assertDictEqual(
            form.cleaned_data,
            {
                'url': '/test/',
                'alias': 'test-page',
                'description': 'At vero eos et accusamus et iusto odio',
                'keywords': 'lorem ipsum dolor sit amet',
                'page_processor': 'powerpages.RedirectProcessor',
                'page_processor_config': {
                    'to url': '/test/'
                },
                'template': '<h1>{{ website_page.title }}</h1>\n',
                'title': 'De Finibus Bonorum et Malorum'
            }
        )

    def test_invalid_form_data_unknown_url_name(self):
        data = {
            'url': '/test/',
            'alias': 'test-page',
            'description': 'At vero eos et accusamus et iusto odio',
            'keywords': 'lorem ipsum dolor sit amet',
            'page_processor': 'powerpages.RedirectProcessor',
            'page_processor_config': {
                'to name': 'not-existing-url'
            },
            'template': '<h1>{{ website_page.title }}</h1>\n',
            'title': 'De Finibus Bonorum et Malorum'
        }
        form = PageAdminForm(data, instance=Page())
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors.keys(), ['__all__'])

    def test_invalid_form_data_unknown_parent_template(self):
        # No parent page
        data = {
            'url': '/test/',
            'alias': 'test-page',
            'description': 'At vero eos et accusamus et iusto odio',
            'keywords': 'lorem ipsum dolor sit amet',
            'page_processor': 'powerpages.DefaultPageProcessor',
            'page_processor_config': {
                'base template': "this-template-does-not-exist.html"
            },
            'template': '<h1>{{ website_page.title }}</h1>\n',
            'title': 'De Finibus Bonorum et Malorum'
        }
        form = PageAdminForm(data, instance=Page())
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors.keys(), ['__all__'])

    def test_invalid_form_data_missing_url(self):
        # No parent page
        data = {
            'url': '',
            'alias': 'test-page',
            'description': 'At vero eos et accusamus et iusto odio',
            'keywords': 'lorem ipsum dolor sit amet',
            'page_processor': 'powerpages.DefaultPageProcessor',
            'page_processor_config': None,
            'template': '<h1>{{ website_page.title }}</h1>\n',
            'title': 'De Finibus Bonorum et Malorum'
        }
        form = PageAdminForm(data, instance=Page())
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors.keys(), ['url'])

    def test_invalid_form_data_duplicate_alias(self):
        Page.objects.create(url='/')
        Page.objects.create(url='/test-old/', alias='test-page')
        data = {
            'url': '/test/',
            'alias': 'test-page',
            'description': 'At vero eos et accusamus et iusto odio',
            'keywords': 'lorem ipsum dolor sit amet',
            'page_processor': 'powerpages.DefaultPageProcessor',
            'page_processor_config': {},
            'template': '<h1>{{ website_page.title }}</h1>\n',
            'title': 'De Finibus Bonorum et Malorum'
        }
        form = PageAdminForm(data, instance=Page())
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors.keys(), ['alias'])

    def test_invalid_form_data_malformed_yaml(self):
        data = {
            'url': '/test/',
            'alias': 'test-page',
            'description': 'At vero eos et accusamus et iusto odio',
            'keywords': 'lorem ipsum dolor sit amet',
            'page_processor': 'powerpages.DefaultPageProcessor',
            'page_processor_config': '- BAD [YAML CONFIG}',
            'template': '<h1>{{ website_page.title }}</h1>\n',
            'title': 'De Finibus Bonorum et Malorum'
        }
        form = PageAdminForm(data, instance=Page())
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors.keys(), ['page_processor_config'])
