# -*- coding: utf-8 -*-

import re

from django.test import TestCase
from django.test.utils import override_settings
from django.core.urlresolvers import reverse

from powerpages.models import Page


# TODO: tests for sitemap config options


def parse_sitemap(content):
    urlset_match = re.search(
        r'<urlset[^>]*>(?P<urls>[\s\S]*)</urlset>', content
    )
    if urlset_match:
        results = []
        urlset_content = urlset_match.groupdict()['urls']
        for url_content in re.findall(r'<url>([\s\S]+)</url>', urlset_content):
            results.append(
                dict(
                    re.findall(r'<([^>]+)>([^<]*)</[^>]+>', url_content)
                )
            )
    else:
        results = None
    return results


class PageSitemapTestCase(TestCase):

    def test_sitemap_view_empty(self):
        url = reverse('sitemap')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(parse_sitemap(response.content), [])

    def test_sitemap_defaults(self):
        page = Page.objects.create(
            url='/test/',
        )
        url = reverse('sitemap')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            parse_sitemap(response.content),
            [
                {
                    'loc': 'http://testserver{0}'.format(page.url),
                    'lastmod': page.changed_at.strftime('%Y-%m-%d')
                }
            ]
        )

    def test_sitemap_page_excluded(self):
        Page.objects.create(
            url='/test/',
            page_processor_config={
                'sitemap': False
            }
        )
        url = reverse('sitemap')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(parse_sitemap(response.content), [])

    def test_sitemap_lastmod_per_page(self):
        page = Page.objects.create(
            url='/test/',
            page_processor_config={
                'sitemap': {
                    'lastmod': "2012-12-30",
                }
            }
        )
        url = reverse('sitemap')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            parse_sitemap(response.content),
            [
                {
                    'loc': 'http://testserver{0}'.format(page.url),
                    'lastmod': "2012-12-30",
                }
            ]
        )

    def test_sitemap_changefreq_per_page(self):
        page = Page.objects.create(
            url='/test/',
            page_processor_config={
                'sitemap': {
                    'changefreq': "monthly",
                }
            }
        )
        url = reverse('sitemap')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            parse_sitemap(response.content),
            [
                {
                    'loc': 'http://testserver{0}'.format(page.url),
                    'lastmod': page.changed_at.strftime('%Y-%m-%d'),
                    'changefreq': "monthly"
                }
            ]
        )

    @override_settings(POWER_PAGES={'SITEMAP_DEFAULT_CHANGEFREQ': 'daily'})
    def test_sitemap_changefreq_default(self):
        page = Page.objects.create(
            url='/test/',
        )
        url = reverse('sitemap')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            parse_sitemap(response.content),
            [
                {
                    'loc': 'http://testserver{0}'.format(page.url),
                    'lastmod': page.changed_at.strftime('%Y-%m-%d'),
                    'changefreq': "daily"
                }
            ]
        )

    @override_settings(POWER_PAGES={'SITEMAP_DEFAULT_CHANGEFREQ': 'daily'})
    def test_sitemap_changefreq_per_page_with_default(self):
        page = Page.objects.create(
            url='/test/',
            page_processor_config={
                'sitemap': {
                    'changefreq': "monthly",
                }
            }
        )
        url = reverse('sitemap')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            parse_sitemap(response.content),
            [
                {
                    'loc': 'http://testserver{0}'.format(page.url),
                    'lastmod': page.changed_at.strftime('%Y-%m-%d'),
                    'changefreq': "monthly"  # page config has higher priority
                }
            ]
        )

    def test_sitemap_priority_per_page(self):
        page = Page.objects.create(
            url='/test/',
            page_processor_config={
                'sitemap': {
                    'priority': 0.5,
                }
            }
        )
        url = reverse('sitemap')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            parse_sitemap(response.content),
            [
                {
                    'loc': 'http://testserver{0}'.format(page.url),
                    'lastmod': page.changed_at.strftime('%Y-%m-%d'),
                    'priority': "0.5"
                }
            ]
        )

    @override_settings(POWER_PAGES={'SITEMAP_DEFAULT_PRIORITY': 0.8})
    def test_sitemap_priority_default(self):
        page = Page.objects.create(
            url='/test/',
        )
        url = reverse('sitemap')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            parse_sitemap(response.content),
            [
                {
                    'loc': 'http://testserver{0}'.format(page.url),
                    'lastmod': page.changed_at.strftime('%Y-%m-%d'),
                    'priority': "0.8"
                }
            ]
        )

    @override_settings(POWER_PAGES={'SITEMAP_DEFAULT_PRIORITY': 0.8})
    def test_sitemap_priority_per_page_with_default(self):
        page = Page.objects.create(
            url='/test/',
            page_processor_config={
                'sitemap': {
                    'priority': 0.5,
                }
            }
        )
        url = reverse('sitemap')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            parse_sitemap(response.content),
            [
                {
                    'loc': 'http://testserver{0}'.format(page.url),
                    'lastmod': page.changed_at.strftime('%Y-%m-%d'),
                    'priority': "0.5",  # page config has higher priority
                }
            ]
        )
