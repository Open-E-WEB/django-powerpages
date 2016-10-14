# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import os
import tempfile
import shutil
import codecs
import StringIO

from django.test import TestCase
from django.test.utils import override_settings

from powerpages.models import Page
from powerpages.sync import (
    PageFileDumper, FilePageLoader, SyncStatus,
    WebsiteDumpOperation, WebsiteLoadOperation, normalize_page_fields
)


def _file_contents(s, strip_spaces=True):
    s = s.replace(',\n', ', \n')
    return s.strip(' ') if strip_spaces else s


class BaseSyncTestCase(TestCase):
    normalized_content = _file_contents('''{
  "alias": "test-page",
  "description": "At vero eos et accusamus et iusto odio",
  "keywords": "lorem ipsum dolor sit amet",
  "page_processor": "powerpages.RedirectProcessor",
  "page_processor_config": {
    "to url": "/test/"
  },
  "title": "De Finibus Bonorum et Malorum"
}
## TEMPLATE SOURCE: ##
<h1>{{ website_page.title }}</h1>
    ''')

    edited_content = '''
{
      "alias":    "test-page",
      "description": "At vero eos et accusamus et iusto odio",
      "title": "De Finibus Bonorum et Malorum",

      "page_processor_config": {"to url": "/test/"},
      "page_processor": "powerpages.RedirectProcessor",
      "keywords": "lorem ipsum dolor sit amet"
}
## TEMPLATE SOURCE: ##
<h1>{{ website_page.title }}</h1>'''

    simple_content = _file_contents('''{
  "description": "",
  "title": "",
  "alias": null,
  "page_processor_config": null,
  "page_processor": "powerpages.DefaultPageProcessor",
  "keywords": ""
}
## TEMPLATE SOURCE: ##
    ''')

    def setUp(self):
        self.sync_directory = tempfile.mkdtemp()
        self.settings_change = override_settings(
            POWER_PAGES={'SYNC_DIRECTORY': self.sync_directory}
        )
        self.settings_change.enable()

    def tearDown(self):
        self.settings_change.disable()
        shutil.rmtree(self.sync_directory)

    def _make_file(self, relative_path, content, make_dirs=True):
        absolute_path = os.path.join(self.sync_directory, relative_path)
        if make_dirs:
            absolute_dir_path, file_name = os.path.split(absolute_path)
            os.makedirs(absolute_dir_path)
        with codecs.open(absolute_path, 'w', encoding='utf-8') as f:
            f.write(content)


class PageFileDumperTestCase(BaseSyncTestCase):

    def test_relative_path_root(self):
        page = Page.objects.create(
            url='/',
        )
        dumper = PageFileDumper(page)
        self.assertEqual(dumper.relative_path(), '_index_.page')

    def test_relative_path_nested(self):
        page = Page.objects.create(
            url='/a/b/test/',
        )
        dumper = PageFileDumper(page)
        self.assertEqual(dumper.relative_path(), 'a/b/test.page')

    def test_relative_path_txt(self):
        page = Page.objects.create(
            url='robots.txt',
        )
        dumper = PageFileDumper(page)
        self.assertEqual(dumper.relative_path(), 'robots.txt')

    def test_absolute_path(self):
        page = Page.objects.create(
            url='/a/b/test/',
        )
        dumper = PageFileDumper(page)
        self.assertEqual(
            dumper.absolute_path(),
            os.path.join(self.sync_directory, 'a/b/test.page')
        )

    def test_page_fields_default(self):
        page = Page.objects.create(
            url='/a/b/test/',
        )
        dumper = PageFileDumper(page)
        self.assertEqual(
            dumper.page_fields(),
            {
                'alias': None,
                'description': '',
                'keywords': '',
                'page_processor': 'powerpages.DefaultPageProcessor',
                'page_processor_config': None,
                'template': '',
                'title': ''
            }
        )

    def test_page_fields_full(self):
        page = Page.objects.create(
            url='/a/b/test/',
            alias='test-page',
            description='At vero eos et accusamus et iusto odio',
            keywords='lorem ipsum dolor sit amet',
            page_processor='powerpages.RedirectProcessor',
            page_processor_config={
                'to url': '/test/'
            },
            template='<h1>{{ website_page.title }}</h1>\n',
            title='De Finibus Bonorum et Malorum',
        )
        dumper = PageFileDumper(page)
        self.assertEqual(
            dumper.page_fields(),
            {
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

    def test_file_contents_default(self):
        page = Page.objects.create(
            url='/a/b/test/',
        )
        dumper = PageFileDumper(page)
        self.assertEqual(
            dumper.file_contents(),
            _file_contents('''{
  "alias": null,
  "description": "",
  "keywords": "",
  "page_processor": "powerpages.DefaultPageProcessor",
  "page_processor_config": null,
  "title": ""
}
## TEMPLATE SOURCE: ##
            ''')
        )

    def test_file_contents_full(self):
        page = Page.objects.create(
            url='/a/b/test/',
            alias='test-page',
            description='At vero eos et accusamus et iusto odio',
            keywords='lorem ipsum dolor sit amet',
            page_processor='powerpages.RedirectProcessor',
            page_processor_config={
                'to url': '/test/'
            },
            template='<h1>{{ website_page.title }}</h1>\n',
            title='De Finibus Bonorum et Malorum',
        )
        dumper = PageFileDumper(page)
        self.assertEqual(
            dumper.file_contents(),
            _file_contents('''{
  "alias": "test-page",
  "description": "At vero eos et accusamus et iusto odio",
  "keywords": "lorem ipsum dolor sit amet",
  "page_processor": "powerpages.RedirectProcessor",
  "page_processor_config": {
    "to url": "/test/"
  },
  "title": "De Finibus Bonorum et Malorum"
}
## TEMPLATE SOURCE: ##
<h1>{{ website_page.title }}</h1>
            ''')
        )

    def test_file_exists_false(self):
        page = Page.objects.create(
            url='/',
        )
        dumper = PageFileDumper(page)
        self.assertFalse(dumper.file_exists())

    def test_file_exists_true(self):
        page = Page.objects.create(
            url='/',
        )
        open(os.path.join(self.sync_directory, '_index_.page'), 'a').close()
        dumper = PageFileDumper(page)
        self.assertTrue(dumper.file_exists())

    def test_status_added(self):
        page = Page.objects.create(
            url='/a/b/test/',
        )
        dumper = PageFileDumper(page)
        self.assertEqual(dumper.status(), SyncStatus.ADDED)

    def test_status_no_changes(self):
        page = Page.objects.create(
            url='/a/b/test/',
        )
        PageFileDumper(page).save()
        dumper = PageFileDumper(page)
        self.assertEqual(dumper.status(), SyncStatus.NO_CHANGES)

    def test_status_no_changes_saved(self):
        page = Page.objects.create(
            url='/a/b/test/',
        )
        PageFileDumper(page).save()
        page.save()
        dumper = PageFileDumper(page)
        self.assertEqual(dumper.status(), SyncStatus.NO_CHANGES)

    def _test_status_modified(self, **kwargs):
        page = Page.objects.create(
            url='/a/b/test/',
        )
        PageFileDumper(page).save()
        for attr, value in kwargs.items():
            setattr(page, attr, value)
        page.save()
        dumper = PageFileDumper(page)
        self.assertEqual(dumper.status(), SyncStatus.MODIFIED)

    def test_status_modified_template(self):
        self._test_status_modified(template='<h1>TEST</h1>\n')

    def test_status_modified_title(self):
        self._test_status_modified(title='TEST')

    def test_status_modified_description(self):
        self._test_status_modified(description='Test test test.')

    def test_status_modified_keywords(self):
        self._test_status_modified(keywords='test test test')

    def test_status_modified_alias(self):
        self._test_status_modified(alias='test-page')

    def test_status_modified_page_processor(self):
        self._test_status_modified(
            page_processor='powerpages.RedirectProcessor'
        )

    def test_status_modified_page_processor_config(self):
        self._test_status_modified(page_processor_config={'sitemap': False})

    def test_save_file_contents(self):
        page = Page.objects.create(
            url='/a/b/test/',
            alias='test-page',
            description='At vero eos et accusamus et iusto odio',
            keywords='lorem ipsum dolor sit amet',
            page_processor='powerpages.RedirectProcessor',
            page_processor_config={
                'to url': '/test/'
            },
            template='<h1>{{ website_page.title }}</h1>\n',
            title='De Finibus Bonorum et Malorum',
        )
        PageFileDumper(page).save()
        path = os.path.join(self.sync_directory, 'a/b/test.page')
        self.assertTrue(os.path.exists(path))
        with open(path) as f:
            file_contents = f.read()
        self.assertEqual(
            file_contents,
            _file_contents('''{
  "alias": "test-page",
  "description": "At vero eos et accusamus et iusto odio",
  "keywords": "lorem ipsum dolor sit amet",
  "page_processor": "powerpages.RedirectProcessor",
  "page_processor_config": {
    "to url": "/test/"
  },
  "title": "De Finibus Bonorum et Malorum"
}
## TEMPLATE SOURCE: ##
<h1>{{ website_page.title }}</h1>
            ''')
        )

    def test_save_is_dirty(self):
        page = Page.objects.create(
            url='/a/b/test/',
            is_dirty=True
        )
        PageFileDumper(page).save()
        page = Page.objects.get(pk=page.pk)
        self.assertFalse(page.is_dirty)

    def test_diff_template_modified(self):
        page = Page.objects.create(
            url='/a/b/test/',
            template="<p>\nTEST\n<\p>\n"
        )
        PageFileDumper(page).save()
        page.template = "<p>\nCHANGE\n<\p>\n"
        page.save()
        dumper = PageFileDumper(page)
        self.assertEqual(
            dumper.diff(),
            '''--- Current content

+++ Coming changes

@@ -8,5 +8,5 @@

 }
 ## TEMPLATE SOURCE: ##
 <p>
-TEST
+CHANGE
 <\p>'''
        )

    def test_diff_title_modified(self):
        page = Page.objects.create(
            url='/a/b/test/',
            title="TEST"
        )
        PageFileDumper(page).save()
        page.title = "CHANGE"
        page.save()
        dumper = PageFileDumper(page)
        self.assertEqual(
            dumper.diff(),
            _file_contents('''--- Current content

+++ Coming changes

@@ -4,6 +4,6 @@

   "keywords": "",
   "page_processor": "powerpages.DefaultPageProcessor",
   "page_processor_config": null,
-  "title": "TEST"
+  "title": "CHANGE"
 }
 ## TEMPLATE SOURCE: ##''')
        )


class PageFileLoaderTestCase(BaseSyncTestCase):

    def test_data_normalization(self):
        self.assertEqual(
            normalize_page_fields(
                FilePageLoader.load(self.normalized_content)
            ),
            normalize_page_fields(
                FilePageLoader.load(self.edited_content)
            )
        )

    def test_url_root(self):
        loader = FilePageLoader('_index_.page')
        self.assertEqual(loader.url(), '/')

    def test_url_nested(self):
        loader = FilePageLoader('a/b/test.page')
        self.assertEqual(loader.url(), '/a/b/test/')

    def test_relative_path_txt(self):
        loader = FilePageLoader('robots.txt')
        self.assertEqual(loader.url(), '/robots.txt')

    def test_absolute_path(self):
        loader = FilePageLoader('a/b/test.page')
        self.assertEqual(
            loader.absolute_path(),
            os.path.join(self.sync_directory, 'a/b/test.page')
        )

    def test_page_fields_normalized(self):
        path = 'a/b/test.page'
        self._make_file(path, self.normalized_content)
        loader = FilePageLoader(path)
        self.assertEqual(
            loader.page_fields(),
            {
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

    def test_page_fields_edited(self):
        path = 'a/b/test.page'
        self._make_file(path, self.edited_content)
        loader = FilePageLoader(path)
        self.assertEqual(
            loader.page_fields(),
            {
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

    def test_file_contents(self):
        path = 'a/b/test.page'
        self._make_file(path, self.edited_content)
        loader = FilePageLoader(path)
        self.assertEqual(loader.file_contents(), self.edited_content)

    def test_page_existing(self):
        page = Page.objects.create(url='/a/b/test/')
        path = 'a/b/test.page'
        self._make_file(path, self.normalized_content)
        loader = FilePageLoader(path)
        self.assertEqual(loader.page(), page)

    def test_page_non_existing(self):
        path = 'a/b/test.page'
        self._make_file(path, self.normalized_content)
        loader = FilePageLoader(path)
        self.assertIsNone(loader.page())

    def test_status_added(self):
        path = 'a/b/test.page'
        self._make_file(path, self.edited_content)
        loader = FilePageLoader(path)
        self.assertEqual(loader.status(), SyncStatus.ADDED)

    def test_status_no_changes(self):
        path = 'a/b/test.page'
        self._make_file(path, self.edited_content)
        FilePageLoader(path).save()
        loader = FilePageLoader(path)
        self.assertEqual(loader.status(), SyncStatus.NO_CHANGES)

    def _test_status_modified(self, **kwargs):
        path = 'a/b/test.page'
        self._make_file(path, self.edited_content)
        FilePageLoader(path).save()
        page = Page.objects.get(url='/a/b/test/')
        for attr, value in kwargs.items():
            setattr(page, attr, value)
        page.save()
        loader = FilePageLoader(path)
        self.assertEqual(loader.status(), SyncStatus.MODIFIED)

    def test_status_modified_template(self):
        self._test_status_modified(template='<h1>TEST</h1>')

    def test_status_modified_title(self):
        self._test_status_modified(title='TEST')

    def test_status_modified_description(self):
        self._test_status_modified(description='Test test test.')

    def test_status_modified_keywords(self):
        self._test_status_modified(keywords='test test test')

    def test_status_modified_alias(self):
        self._test_status_modified(alias='test-page-2')

    def test_status_modified_page_processor(self):
        self._test_status_modified(
            page_processor='powerpages.NotFoundProcessor'
        )

    def test_status_modified_page_processor_config(self):
        self._test_status_modified(page_processor_config={'sitemap': False})

    def test_diff_template_modified(self):
        path = 'a/b/test.page'
        self._make_file(path, self.edited_content)
        FilePageLoader(path).save()
        page = Page.objects.get(url='/a/b/test/')
        page.template = 'TEST'
        page.save()
        loader = FilePageLoader(path)
        self.assertEqual(
            loader.diff(),
            _file_contents('''--- Current content

+++ Coming changes

@@ -9,4 +9,4 @@

   "title": "De Finibus Bonorum et Malorum"
 }
 ## TEMPLATE SOURCE: ##
-TEST
+<h1>{{ website_page.title }}</h1>''')
        )

    def test_diff_title_modified(self):
        path = 'a/b/test.page'
        self._make_file(path, self.edited_content)
        FilePageLoader(path).save()
        page = Page.objects.get(url='/a/b/test/')
        page.title = 'CHANGE'
        page.save()
        loader = FilePageLoader(path)
        self.assertEqual(
            loader.diff(),
            _file_contents('''--- Current content

+++ Coming changes

@@ -6,7 +6,7 @@

   "page_processor_config": {
     "to url": "/test/"
   },
-  "title": "CHANGE"
+  "title": "De Finibus Bonorum et Malorum"
 }
 ## TEMPLATE SOURCE: ##
 <h1>{{ website_page.title }}</h1>''')
        )


class WebsiteDumpOperationTestCase(BaseSyncTestCase):

    def test_dump_new_file(self):
        Page.objects.create(
            url='/a/b/test/',
            alias='test-page',
            description='At vero eos et accusamus et iusto odio',
            keywords='lorem ipsum dolor sit amet',
            page_processor='powerpages.RedirectProcessor',
            page_processor_config={
                'to url': '/test/'
            },
            template='<h1>{{ website_page.title }}</h1>\n',
            title='De Finibus Bonorum et Malorum',
        )
        stdout = StringIO.StringIO()
        stderr = StringIO.StringIO()
        operation = WebsiteDumpOperation(
            root_url='/a/b/test/',
            stdout=stdout,
            stderr=stderr,
            get_input=lambda p: 'y',
            dry_run=False,
            no_interactive=False,
            quiet=False,
            force=False,
            git_add=False,
            no_color=True,
        )
        operation.run()
        # Check result file:
        path = os.path.join(self.sync_directory, 'a/b/test.page')
        self.assertTrue(os.path.exists(path))
        with codecs.open(path, encoding='utf-8') as f:
            file_contents = f.read()
        self.assertEqual(
            file_contents,
            _file_contents('''{
  "alias": "test-page",
  "description": "At vero eos et accusamus et iusto odio",
  "keywords": "lorem ipsum dolor sit amet",
  "page_processor": "powerpages.RedirectProcessor",
  "page_processor_config": {
    "to url": "/test/"
  },
  "title": "De Finibus Bonorum et Malorum"
}
## TEMPLATE SOURCE: ##
<h1>{{ website_page.title }}</h1>
            ''')
        )
        output = stdout.getvalue()
        # Check stdout:
        self.assertIn('[A] = 1', output)  # 1 file created
        self.assertNotIn('[M] = ', output)  # no modifications
        self.assertNotIn('[D] = ', output)  # no deletions
        # Check stderr:
        self.assertEqual(stderr.getvalue(), '')  # no errors

    def test_dump_modified_file(self):
        page = Page.objects.create(
            url='/a/b/test/',
            alias='test-page',
            description='At vero eos et accusamus et iusto odio',
            keywords='lorem ipsum dolor sit amet',
            page_processor='powerpages.RedirectProcessor',
            page_processor_config={
                'to url': '/test/'
            },
            template='<h1>{{ website_page.title }}</h1>\n',
            title='De Finibus Bonorum et Malorum',
        )
        PageFileDumper(page).save()  # file is created
        page.title = "CHANGE!"
        page.save()
        stdout = StringIO.StringIO()
        stderr = StringIO.StringIO()
        operation = WebsiteDumpOperation(
            root_url='/a/b/test/',
            stdout=stdout,
            stderr=stderr,
            get_input=lambda p: 'y',
            dry_run=False,
            no_interactive=False,
            quiet=False,
            force=False,
            git_add=False,
            no_color=True,
        )
        operation.run()
        # Check result file:
        path = os.path.join(self.sync_directory, 'a/b/test.page')
        self.assertTrue(os.path.exists(path))
        with codecs.open(path, encoding='utf-8') as f:
            file_contents = f.read()
        self.assertEqual(
            file_contents,
            _file_contents('''{
  "alias": "test-page",
  "description": "At vero eos et accusamus et iusto odio",
  "keywords": "lorem ipsum dolor sit amet",
  "page_processor": "powerpages.RedirectProcessor",
  "page_processor_config": {
    "to url": "/test/"
  },
  "title": "CHANGE!"
}
## TEMPLATE SOURCE: ##
<h1>{{ website_page.title }}</h1>
            ''')
        )
        output = stdout.getvalue()
        # Check stdout:
        self.assertNotIn('[A] = ', output)  # no additions
        self.assertIn('[M] = 1', output)  # 1 file modified
        self.assertNotIn('[D] = ', output)  # no deletions
        # Check stderr:
        self.assertEqual(stderr.getvalue(), '')  # no errors

    def test_dump_deleted_file(self):
        # root page:
        root = Page.objects.create(url='/')
        PageFileDumper(root).save()
        # sibling page:
        sibling = Page.objects.create(url='/dummy/')
        PageFileDumper(sibling).save()
        # TODO: handle removing all children

        page = Page.objects.create(
            url='/test/',
            alias='test-page',
            description='At vero eos et accusamus et iusto odio',
            keywords='lorem ipsum dolor sit amet',
            page_processor='powerpages.RedirectProcessor',
            page_processor_config={
                'to url': '/test/'
            },
            template='<h1>{{ website_page.title }}</h1>\n',
            title='De Finibus Bonorum et Malorum',
        )
        PageFileDumper(page).save()  # file is created
        page.delete()
        stdout = StringIO.StringIO()
        stderr = StringIO.StringIO()
        operation = WebsiteDumpOperation(
            root_url='/',
            stdout=stdout,
            stderr=stderr,
            get_input=lambda p: 'y',
            dry_run=False,
            no_interactive=False,
            quiet=False,
            force=False,
            git_add=False,
            no_color=True,
        )
        operation.run()
        # Check result file:
        path = os.path.join(self.sync_directory, 'test.page')
        self.assertFalse(os.path.exists(path))
        output = stdout.getvalue()
        # Check stdout:
        self.assertNotIn('[A] = ', output)  # no additions
        self.assertNotIn('[M] = ', output)  # no modifications
        self.assertIn('[D] = 1', output)  # 1 file deleted
        # Check stderr:
        self.assertEqual(stderr.getvalue(), '')  # no errors


class WebsiteLoadOperationTestCase(BaseSyncTestCase):

    def test_load_new_page(self):
        # root page:
        root = Page.objects.create(url='/')
        PageFileDumper(root).save()
        # sibling page:
        sibling = Page.objects.create(url='/dummy/')
        PageFileDumper(sibling).save()

        self._make_file(
            'test.page',
            _file_contents('''{
  "alias": "test-page",
  "description": "At vero eos et accusamus et iusto odio",
  "keywords": "lorem ipsum dolor sit amet",
  "page_processor": "powerpages.RedirectProcessor",
  "page_processor_config": {
    "to url": "/test/"
  },
  "title": "De Finibus Bonorum et Malorum"
}
## TEMPLATE SOURCE: ##
<h1>{{ website_page.title }}</h1>
            '''),
            make_dirs=False
        )

        stdout = StringIO.StringIO()
        stderr = StringIO.StringIO()
        operation = WebsiteLoadOperation(
            root_url='/',
            stdout=stdout,
            stderr=stderr,
            get_input=lambda p: 'y',
            dry_run=False,
            no_interactive=False,
            quiet=False,
            force=False,
            git_add=False,
            no_color=True,
        )
        operation.run()
        # Check result file:
        page = Page.objects.filter(url='/test/').first()
        self.assertIsNotNone(page)
        self.assertEqual(page.alias, "test-page")
        self.assertEqual(
            page.description, "At vero eos et accusamus et iusto odio"
        )
        self.assertEqual(page.keywords, "lorem ipsum dolor sit amet")
        self.assertEqual(page.page_processor, "powerpages.RedirectProcessor")
        self.assertEqual(page.page_processor_config, {"to url": "/test/"})
        self.assertEqual(page.title, "De Finibus Bonorum et Malorum")
        self.assertEqual(page.template, '<h1>{{ website_page.title }}</h1>\n')

        output = stdout.getvalue()
        # Check stdout:
        self.assertIn('[A] = 1', output)  # 1 page added
        self.assertNotIn('[M] = ', output)  # no modifications
        self.assertNotIn('[D] = ', output)  # no deletions
        # Check stderr:
        self.assertEqual(stderr.getvalue(), '')  # no errors

    def test_load_modified_page(self):
        # root page:
        root = Page.objects.create(url='/')
        PageFileDumper(root).save()
        # sibling page:
        sibling = Page.objects.create(url='/dummy/')
        PageFileDumper(sibling).save()

        Page.objects.create(
            url='/test/',
            alias='test-page',
            description='At vero eos et accusamus et iusto odio',
            keywords='lorem ipsum dolor sit amet',
            page_processor='powerpages.RedirectProcessor',
            page_processor_config={
                'to url': '/test/'
            },
            template='<h1>{{ website_page.title }}</h1>\n',
            title='De Finibus Bonorum et Malorum',
        )
        self._make_file(
            'test.page',
            _file_contents('''{
  "alias": "test-page",
  "description": "At vero eos et accusamus et iusto odio",
  "keywords": "lorem ipsum dolor sit amet",
  "page_processor": "powerpages.RedirectProcessor",
  "page_processor_config": {
    "to url": "/test/"
  },
  "title": "TEST"
}
## TEMPLATE SOURCE: ##
<h1>CHANGE</h1>
            '''),
            make_dirs=False
        )

        stdout = StringIO.StringIO()
        stderr = StringIO.StringIO()
        operation = WebsiteLoadOperation(
            root_url='/',
            stdout=stdout,
            stderr=stderr,
            get_input=lambda p: 'y',
            dry_run=False,
            no_interactive=False,
            quiet=False,
            force=False,
            git_add=False,
            no_color=True,
        )
        operation.run()
        # Check result file:
        page = Page.objects.filter(url='/test/').first()
        self.assertIsNotNone(page)
        self.assertEqual(page.alias, "test-page")
        self.assertEqual(
            page.description, "At vero eos et accusamus et iusto odio"
        )
        self.assertEqual(page.keywords, "lorem ipsum dolor sit amet")
        self.assertEqual(page.page_processor, "powerpages.RedirectProcessor")
        self.assertEqual(page.page_processor_config, {"to url": "/test/"})
        self.assertEqual(page.title, "TEST")
        self.assertEqual(page.template, '<h1>CHANGE</h1>\n')

        output = stdout.getvalue()
        # Check stdout:
        self.assertNotIn('[A] = ', output)  # no additions
        self.assertIn('[M] = 1', output)  # 1 page modified
        self.assertNotIn('[D] = ', output)  # no deletions
        # Check stderr:
        self.assertEqual(stderr.getvalue(), '')  # no errors

    def test_load_deleted_page(self):
        # root page:
        root = Page.objects.create(url='/')
        PageFileDumper(root).save()
        # sibling page:
        sibling = Page.objects.create(url='/dummy/')
        PageFileDumper(sibling).save()

        Page.objects.create(
            url='/test/',
            alias='test-page',
            description='At vero eos et accusamus et iusto odio',
            keywords='lorem ipsum dolor sit amet',
            page_processor='powerpages.RedirectProcessor',
            page_processor_config={
                'to url': '/test/'
            },
            template='<h1>{{ website_page.title }}</h1>\n',
            title='De Finibus Bonorum et Malorum',
        )
        # no file!

        stdout = StringIO.StringIO()
        stderr = StringIO.StringIO()
        operation = WebsiteLoadOperation(
            root_url='/',
            stdout=stdout,
            stderr=stderr,
            get_input=lambda p: 'y',
            dry_run=False,
            no_interactive=False,
            quiet=False,
            force=False,
            git_add=False,
            no_color=True,
        )
        operation.run()
        # Check result file:
        page = Page.objects.filter(url='/test/').first()
        self.assertIsNone(page)

        output = stdout.getvalue()
        # Check stdout:
        self.assertNotIn('[A] = ', output)  # no additions
        self.assertNotIn('[M] = ', output)  # no modifications
        self.assertIn('[D] = 1', output)  # 1 page deleted
        # Check stderr:
        self.assertEqual(stderr.getvalue(), '')  # no errors
