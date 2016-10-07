# -*- coding: utf-8 -*-

from django.test import TestCase
from django.core.urlresolvers import reverse

from powerpages.models import Page


class PageModelTestCase(TestCase):

    # def __unicode__(self):

    def test_unicode(self):
        page = Page.objects.create(
            url='/test/',
        )
        self.assertEqual(unicode(page), '/test/')

    # def get_absolute_url(self):

    def test_get_absolute_url(self):
        page = Page.objects.create(
            url='/test/',
        )
        self.assertEqual(page.get_absolute_url(), '/test/')

    # def parent_url(self):

    def test_parent_url_second_level(self):
        page = Page.objects.create(
            url='/a/b/',
        )
        self.assertEqual(page.parent_url(), '/a/')

    def test_parent_url_first_level(self):
        page = Page.objects.create(
            url='/a/',
        )
        self.assertEqual(page.parent_url(), '/')

    def test_parent_url_root(self):
        page = Page.objects.create(
            url='/',
        )
        self.assertEqual(page.parent_url(), '')

    # def parent(self):

    def test_parent_direct_existing(self):
        parent = Page.objects.create(
            url='/a/',
        )
        page = Page.objects.create(
            url='/a/b/',
        )
        self.assertEqual(page.parent(), parent)

    def test_parent_direct_missing_1(self):
        Page.objects.create(
            url='/a/',
        )
        page = Page.objects.create(
            url='/a/b/c/',
        )
        self.assertIsNone(page.parent())  # /a/b/ does not exist

    def test_parent_direct_missing_2(self):
        page = Page.objects.create(
            url='/a/b/',
        )
        self.assertIsNone(page.parent())

    def test_parent_of_root(self):
        page = Page.objects.create(
            url='/',
        )
        self.assertIsNone(page.parent())

    # def children(self):

    def test_children_empty(self):
        page = Page.objects.create(
            url='/c/',
        )
        Page.objects.create(
            url='/a/b/',
        )
        self.assertEqual(list(page.children()), [])

    def test_children_available(self):
        page = Page.objects.create(
            url='/a/',
        )
        child_1 = Page.objects.create(
            url='/a/b/',
        )
        child_2 = Page.objects.create(
            url='/a/d/',
        )
        Page.objects.create(
            url='/a/b/c/',  # grandchild
        )
        Page.objects.create(
            url='/x/',
        )
        self.assertEqual(list(page.children()), [child_1, child_2])

    # def descendants(self):

    def test_descendants_empty(self):
        page = Page.objects.create(
            url='/c/',
        )
        Page.objects.create(
            url='/a/b/',
        )
        self.assertEqual(list(page.descendants()), [])

    def test_descendants_available(self):
        page = Page.objects.create(
            url='/a/',
        )
        child_1 = Page.objects.create(
            url='/a/b/',
        )
        child_2 = Page.objects.create(
            url='/a/d/',
        )
        grandchild_1 = Page.objects.create(
            url='/a/b/c/',  # grandchild
        )
        Page.objects.create(
            url='/x/',
        )
        self.assertEqual(
            list(page.descendants()), [child_1, grandchild_1, child_2]
        )

    # def is_accessible(self):

    def test_is_accessible_default_processor(self):
        page = Page.objects.create(
            url='/test/'
        )
        self.assertTrue(page.is_accessible())

    def test_is_accessible_redirect_processor(self):
        page = Page.objects.create(
            url='/test/', page_processor='powerpages.RedirectProcessor'
        )
        self.assertTrue(page.is_accessible())

    def test_is_accessible_not_found_processor(self):
        page = Page.objects.create(
            url='/test/', page_processor='powerpages.NotFoundProcessor'
        )
        self.assertFalse(page.is_accessible())

    # def get_admin_url(self):

    def test_get_admin_url(self):
        page = Page.objects.create(
            url='/test/'
        )
        self.assertEqual(
            page.get_admin_url(),
            reverse('admin:powerpages_page_change', args=[page.pk])
        )
