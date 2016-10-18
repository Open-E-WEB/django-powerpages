# -*- coding: utf-8 -*-

from  __future__ import unicode_literals

from django.test import TestCase
from django.contrib.auth.models import User

from powerpages.models import Page
from powerpages.sync import PageFileDumper
from powerpages.admin import website_link, sync_status, save_page
from powerpages.signals import page_edited
from .test_sync import BaseSyncTestCase


class WebsiteLinkTestCase(TestCase):

    maxDiff = None

    def test_no_object(self):
        self.assertIsNone(website_link(None))

    def test_empty_url(self):
        self.assertEqual(
            website_link(Page(url='')),
            '<a href="" style="font-weight: normal;"> &raquo;</a>'
        )

    def test_root_url(self):
        self.assertEqual(
            website_link(Page(url='/')),
            '<a href="/" style="font-weight: normal;">/ &raquo;</a>'
        )

    def test_first_level_url(self):
        self.assertEqual(
            website_link(Page(url='/test/')),
            '<a href="/test/" style="font-weight: normal;">'
            '/<span style="font-weight: bold">test</span>/'
            ' &raquo;</a>'
        )

    def test_second_level_url(self):
        self.assertEqual(
            website_link(Page(url='/nested/test/')),
            '<a href="/nested/test/" style="font-weight: normal;">'
            '/nested/<span style="font-weight: bold">test</span>/'
            ' &raquo;</a>'
        )

    def test_file(self):
        self.assertEqual(
            website_link(Page(url='/robots.txt')),
            '<a href="/robots.txt" style="font-weight: normal;">'
            '/<span style="font-weight: bold">robots.txt</span>'
            ' &raquo;</a>'
        )

    def test_nested_file(self):
        self.assertEqual(
            website_link(Page(url='/nested/robots.txt')),
            '<a href="/nested/robots.txt" style="font-weight: normal;">'
            '/nested/<span style="font-weight: bold">robots.txt</span>'
            ' &raquo;</a>'
        )


class SyncStatusTestCase(BaseSyncTestCase):

    maxDiff = None

    def test_no_object(self):
        self.assertIsNone(sync_status(None))

    def test_file_synced(self):
        page = Page.objects.create(
            url='/test-page/', template='<h1>Test Page</h1>'
        )
        PageFileDumper(page).save()
        self.assertEqual(
            sync_status(page),
            '<span style="color: green">File is synced</span>'
        )

    def test_file_content_differs(self):
        page = Page.objects.create(
            url='/test-page/', template='<h1>Test Page</h1>'
        )
        PageFileDumper(page).save()
        page.title = 'Lorem Ipsum'
        page.save()
        self.assertEqual(
            sync_status(page),
            '<span style="color: orange">File content differs</span>'
        )

    def test_file_is_missing(self):
        page = Page.objects.create(
            url='/test-page/', template='<h1>Test Page</h1>'
        )
        self.assertEqual(
            sync_status(page),
            '<span style="color: red">File is missing</span>'
        )

    def test_file_content_differs_modified_in_admin(self):
        page = Page.objects.create(
            url='/test-page/', template='<h1>Test Page</h1>'
        )
        PageFileDumper(page).save()
        page.title = 'Lorem Ipsum'
        page.is_dirty = True  # modified in Admin
        page.save()
        self.assertEqual(
            sync_status(page),
            '<span style="color:black; font-weight:bold">'
            'Changed in Admin!</span><br>'
            '<span style="color: orange">File content differs</span>'
        )


class SavePageTestCase(TestCase):

    maxDiff = None

    def setUp(self):

        def page_edited_test_handler(sender, **kwargs):
            self.page_edited_kwargs = kwargs

        self.page_edited_kwargs = None
        page_edited.connect(
            page_edited_test_handler, dispatch_uid='test_page_edited',
            weak=False
        )

    def tearDown(self):
        page_edited.disconnect(dispatch_uid='test_page_edited')
        self.page_edited_kwargs = None

    def test_create_page(self):
        page = Page(url='/test-page/')
        user = User.objects.create_user('admin-user')

        save_page(page=page, user=user, created=True)

        self.assertIsNotNone(page.pk)
        self.assertTrue(page.is_dirty)
        self.assertDictContainsSubset(
            {'page': page, 'user': user, 'created': True},
            self.page_edited_kwargs
        )

    def test_modify_page(self):
        page = Page.objects.create(url='/test-page/', title='Lorem')
        page.title = 'Ipsum'
        user = User.objects.create_user('admin-user')

        save_page(page=page, user=user, created=False)

        self.assertEqual(Page.objects.get(pk=page.pk).title, 'Ipsum')
        self.assertTrue(page.is_dirty)
        self.assertDictContainsSubset(
            {'page': page, 'user': user, 'created': False},
            self.page_edited_kwargs
        )
