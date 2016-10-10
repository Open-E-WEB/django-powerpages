# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import os
import sys
import json
import codecs
import itertools
import difflib
import collections
import subprocess

from powerpages.utils.console import Console
from powerpages.models import Page
from powerpages.settings import app_settings


INDEX_FILE_NAME = '_index_.page'

FILE_DELIMITER = '## TEMPLATE SOURCE: ##'
FILE_DELIMITER_LINE = '\n{0}\n'.format(FILE_DELIMITER)


def url_to_path(url, has_children):
    """Generates file system path for given URL"""
    url_pieces = [slug for slug in url.split('/') if slug]
    if url == '/':
        rel_path = INDEX_FILE_NAME
    elif url_pieces and has_children:
        rel_path = os.sep.join(url_pieces + [INDEX_FILE_NAME])
    else:
        file_name = url_pieces.pop()
        if '.' not in file_name:
            file_name = '{0}.page'.format(file_name)
        rel_path = os.sep.join(url_pieces + [file_name])
    return rel_path


def path_to_url(path):
    """Generates URL for given relative file path"""
    url_pieces = [slug for slug in path.split('/') if slug]
    file_name = url_pieces.pop()
    if file_name != INDEX_FILE_NAME:
        if file_name.endswith('.page'):
            file_name, file_ext = os.path.splitext(file_name)
        url_pieces.append(file_name)
        if '.' not in file_name:
            url_pieces.append('')  # to generate trailing slash
    else:
        url_pieces.append('')  # to generate trailing slash
    return '/' + '/'.join(url_pieces)


def generate_diff(current, coming):
    """Generates diff of changes"""
    return u'\n'.join(
        difflib.unified_diff(
            current.splitlines(), coming.splitlines(),
            u"Current content", u"Coming changes"
        )
    )


def normalize_text(s):
    """Normalizes content of a text field"""
    return (s or '').strip().replace('\r', '')


def normalize_line(s):
    """Normalizes content of a field that should be a single line, eg. title"""
    return normalize_text(s).replace('\n', '')


def normalize_template(s):
    """Normalizes content of a template"""
    normalized = normalize_text(s)
    if normalized:
        normalized += '\n'
    return normalized


def normalize_page_fields(data):
    cleaned_data = {
        'alias': data.get('alias'),
        'page_processor_config': data.get('page_processor_config'),
        'template': normalize_template(data.get('template'))
    }
    for f in ('title', 'page_processor'):
        cleaned_data[f] = normalize_text(data.get(f))
    for f in ('description', 'keywords'):
        cleaned_data[f] = normalize_text(data.get(f))
    return cleaned_data


class SyncStatus(object):
    ADDED = 'A'
    MODIFIED = 'M'
    NO_CHANGES = '.'
    DELETED = 'D'
    # Additional status:
    SKIPPED = 's'
    FORCED = '!'
    # Descriptions:
    DESCRIPTIONS = {
        ADDED: u"Added",
        MODIFIED: u"Modified",
        NO_CHANGES: u"No changes",
        DELETED: u"Deleted",
        SKIPPED: u"(skipped)",
        FORCED: u"(forced)",
    }

    @classmethod
    def describe(cls, status):
        """Descriptive version of status"""
        return u" ".join(cls.DESCRIPTIONS[s] for s in status)


class PageFileDumper(object):
    """Class responsible for DUMPING Page instance data INTO file"""

    def __init__(self, page):
        self.page = page

    def relative_path(self):
        """Relative path to file"""
        return url_to_path(self.page.url, self.page.children().exists())

    def absolute_path(self):
        """Absolute path to file"""
        return os.path.join(app_settings.SYNC_DIRECTORY, self.relative_path())

    def page_fields(self):
        """Dictionary of Page fields"""
        page = self.page
        page_fields = {
            'alias': page.alias,
            'title': page.title,
            'description': page.description,
            'keywords': page.keywords,
            'template': page.template,
            'page_processor': page.page_processor,
            'page_processor_config': page.page_processor_config,
        }
        return normalize_page_fields(page_fields)

    @staticmethod
    def dump(page_fields):
        """Converts dict of Page fields into file contents"""
        template_source = page_fields.pop('template') or ''
        page_metadata = json.dumps(
            collections.OrderedDict(
                sorted((k, v) for k, v in page_fields.items())
            ),
            indent=2
        )
        return FILE_DELIMITER_LINE.join(
            (page_metadata, template_source)
        )

    def file_contents(self):
        """Contents of .page file"""
        return self.dump(self.page_fields())

    def file_exists(self):
        """File exists?"""
        return os.path.exists(self.absolute_path())

    def status(self):
        """Synchronization status determined before actual synchronization"""
        if not self.file_exists():
            status = SyncStatus.ADDED
        elif (
            # previous data
            FilePageLoader(self.relative_path()).page_fields() !=
            # is different from current data
            self.page_fields()
        ):
            status = SyncStatus.MODIFIED
        else:
            status = SyncStatus.NO_CHANGES
        return status

    def save(self):
        """Saves Page data into file"""
        # Side effect: remove dirty flag:
        Page.objects.filter(pk=self.page.pk).update(is_dirty=False)
        # Ensure directory:
        dir_path = os.path.dirname(self.absolute_path())
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        # Save file:
        with codecs.open(self.absolute_path(), 'w', encoding='utf-8') as f:
            f.write(self.file_contents())

    def diff(self):
        """Generates diff of changes (normalized)"""
        normalized_current = PageFileDumper.dump(
            FilePageLoader(self.relative_path()).page_fields()
        )
        normalized_coming = self.file_contents()
        return generate_diff(normalized_current, normalized_coming)


class FilePageLoader(object):
    """Class responsible for LOADING Page instance data FROM file"""

    def __init__(self, path):
        self.relative_path = path

    def absolute_path(self):
        """Absolute path to file"""
        return os.path.join(app_settings.SYNC_DIRECTORY, self.relative_path)

    def url(self):
        """URL based on relative file path"""
        return path_to_url(self.relative_path)

    @staticmethod
    def load(file_contents):
        """Converts file contents into dict of Page fields"""
        page_metadata, template_source = \
            file_contents.split(FILE_DELIMITER_LINE, 1)
        page_fields = json.loads(page_metadata)
        page_fields['template'] = template_source
        return page_fields

    def page_fields(self):
        """Dictionary of Page fields"""
        try:
            page_fields = self.load(self.file_contents())
        except ValueError:
            raise RuntimeError(
                u'Bad .page file: {0}'.format(self.relative_path)
            )
        return normalize_page_fields(page_fields)

    def file_contents(self):
        """Contents of .page file"""
        return codecs.open(
            self.absolute_path(), 'r', encoding='utf-8'
        ).read()

    def page(self):
        """Corresponding Page instance"""
        return Page.objects.filter(url=self.url()).first()

    def status(self):
        """Synchronization status determined before actual synchronization"""
        page = self.page()
        if not page:
            status = SyncStatus.ADDED
        elif (
            # Page data in database
            PageFileDumper(page).page_fields() !=
            # is different from file data
            self.page_fields()
        ):
            status = SyncStatus.MODIFIED
        else:
            status = SyncStatus.NO_CHANGES
        return status

    def save(self):
        """Saves file data into Page"""
        url = self.url()
        page_fields = self.page_fields()
        page = Page.objects.filter(url=url).first()
        if not page:
            page = Page(url=url)
        for name, value in page_fields.items():
            setattr(page, name, value)
        page.is_dirty = False  # Remove dirty flag
        page.save()

    def diff(self):
        """Generates diff of changes (normalized)"""
        normalized_current = PageFileDumper(self.page()).file_contents()
        normalized_coming = PageFileDumper.dump(self.page_fields())
        return generate_diff(normalized_current, normalized_coming)


class BaseSyncOperation(object):
    """Base class for website dump / load operations"""

    status_colors = {
        SyncStatus.DELETED: 'MAGENTA',
        SyncStatus.ADDED: 'GREEN',
        SyncStatus.MODIFIED: 'CYAN',
    }

    def __init__(self, root_url=None, error_class=None,
                 stdout=None, stderr=None, get_input=None, **options):
        self.root_url = root_url or '/'
        self.error_class = error_class or RuntimeError
        self.stdout = stdout or sys.stdout
        self.stderr = stderr or sys.stderr
        self.dry_run = options['dry_run']
        self.no_interactive = options['no_interactive']
        self.quiet = options['quiet']
        self.force = options['force']
        self.git_add = options['git_add']
        self.no_color = options.get('no_color')
        self.console = Console(self.stdout)
        self.get_input = get_input or raw_input

    def status_fg_color(self, status):
        """Determines fg color for status"""
        if self.no_color:
            fg_color = None
        else:
            try:
                base_status, extra_status = status
            except ValueError:
                base_status, extra_status = status, None
            if extra_status == SyncStatus.SKIPPED:
                fg_color = None
            else:
                fg_color = self.status_colors.get(base_status, None)
        return fg_color

    def log(self, message):
        """Writes informative line of text to stdout"""
        if not self.quiet:
            self.console.new_line(message)

    def log_status(self, status, item):
        """Writes informative line about status of given item (in color!)"""
        if not self.quiet:
            message = u"{0} {1}".format(status, item)
            self.console.new_line(
                message, fg_color=self.status_fg_color(status)
            )

    def summary(self, summary_dict):
        """Writes summary line of text to stdout"""
        self.console.new_line(u"SUMMARY:")
        if summary_dict:
            for status, occurrences in summary_dict.items():
                message = u"\t{0} [{1}] = {2}".format(
                    SyncStatus.describe(status), status, occurrences
                )
                self.console.new_line(
                    message, fg_color=self.status_fg_color(status)
                )
        else:
            self.console.new_line(u"\tNo changes!")

    def error(self, message):
        """Stops processing by raising an exception"""
        raise self.error_class(message)

    def confirm(self, *args, **kwargs):
        """Asks user for confirmation, providing boolean output"""
        if self.no_interactive:
            choice = True
        else:
            # Delimiter:
            self.console.new_line(
                u"{s} CONFIRMATION REQUIRED: {s}".format(s='#' * 28)
            )
            # Show diff if available:
            diff = kwargs.get('diff')
            if diff:
                self.console.new_line(u"{s} DIFF {s}".format(s='-' * 37))
                for diff_line in diff.splitlines():
                    if diff_line.startswith('+'):
                        fg_color = 'GREEN'
                    elif diff_line.startswith('-'):
                        fg_color = 'RED'
                    else:
                        fg_color = None
                    self.console.new_line(diff_line, fg_color=fg_color)
                self.console.new_line(u"{s}".format(s='-' * 80))
            # Show other messages:
            message = kwargs.get('message')
            messages = [message] if message else list(args)
            messages.append(
                kwargs.get(
                    'question', u"Do you want to apply this change?"
                )
            )
            for message in messages:
                self.console.new_line(message)
            choice = None
            while choice is None:
                user_text = self.get_input(u"Y/N? ")
                if user_text in ('Y', 'y'):
                    choice = True
                elif user_text in ('N', 'n'):
                    choice = False
            # Delimiter:
            self.console.new_line(u"{s}".format(s='#' * 80))
        return choice

    def run(self):
        """Performs the operation"""
        raise NotImplementedError


class WebsiteDumpOperation(BaseSyncOperation):
    """DUMPS website Pages TO structure of directories and file"""

    def dump_existing_pages(self, root_page, summary):
        """Dumps content of root page and children"""
        valid_paths = set([app_settings.SYNC_DIRECTORY])
        page_iterator = \
            itertools.chain([root_page], root_page.descendants().iterator())
        # Dump content of root page and children:
        for page in page_iterator:
            page_dumper = PageFileDumper(page)
            status = page_dumper.status()
            if status != SyncStatus.NO_CHANGES:
                if status == SyncStatus.ADDED:
                    apply_change = self.confirm(
                        u"Page created: {0}".format(page.url)
                    )
                else:
                    apply_change = self.confirm(
                        u"Page modified: {0}".format(page.url),
                        diff=page_dumper.diff()
                    )
            else:
                apply_change = True
            if not apply_change:
                status += SyncStatus.SKIPPED
            self.log_status(status, page_dumper.relative_path())
            if apply_change and not self.dry_run:
                page_dumper.save()
            # Update the set of valid paths (not to be deleted)
            valid_path = page_dumper.absolute_path()
            while valid_path != app_settings.SYNC_DIRECTORY:
                valid_paths.add(valid_path)
                valid_path = os.path.dirname(valid_path)
            summary[status] += 1
        return valid_paths

    def delete_unused_files(self, root_page, valid_paths, summary):
        """Deletes unused files ONLY in subtree of root"""
        if root_page.children():
            delete_start_path = os.path.dirname(
                PageFileDumper(root_page).absolute_path()
            )
            delete_list = []
            for root, dirs, files in os.walk(delete_start_path, False):
                for file_name in reversed(files):
                    if file_name.startswith('.'):
                        continue
                    path = os.path.join(root, file_name)
                    if path not in valid_paths:
                        delete_list.append(path)
                if root not in valid_paths:
                    delete_list.append(root)
            for delete_path in delete_list:
                relative_path = \
                    os.path.relpath(delete_path, app_settings.SYNC_DIRECTORY)
                status = SyncStatus.DELETED
                apply_change = self.confirm(
                    u"Path to be deleted: {0}".format(relative_path)
                )
                if not apply_change:
                    status += SyncStatus.SKIPPED
                self.log_status(status, relative_path)
                if apply_change and not self.dry_run:
                    if os.path.isdir(delete_path):
                        os.rmdir(delete_path)
                    else:
                        os.remove(delete_path)
                summary[status] += 1

    def add_to_vcs(self, summary):
        if (
            self.git_add and
            (SyncStatus.DELETED in summary or SyncStatus.ADDED in summary) and
            not self.dry_run and
            self.confirm(
                question=(
                    u"Do you want to add created and removed files to GIT?"
                )
            )
        ):
            output, errors = subprocess.Popen(
                ['git', '-C', app_settings.SYNC_DIRECTORY,
                 'add', '-A', app_settings.SYNC_DIRECTORY],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            ).communicate()
            if errors:
                raise self.error(u"Adding file changes to GIT failed!")

    def run(self):
        """Performs the operation"""
        root_page = Page.objects.filter(url=self.root_url).first()
        if not root_page:
            self.error(u'Root page "{0}" not found!'.format(self.root_url))
        summary = collections.defaultdict(int)
        valid_paths = self.dump_existing_pages(root_page, summary)
        self.delete_unused_files(root_page, valid_paths, summary)
        self.summary(summary)
        self.add_to_vcs(summary)


class WebsiteLoadOperation(BaseSyncOperation):
    """LOADS website Pages FROM structure of directories and file"""

    def page_loaders(self):
        """Builds a list of page loaders"""
        root_path = url_to_path(self.root_url, has_children=False)
        if (
            os.path.exists(
                os.path.join(app_settings.SYNC_DIRECTORY, root_path)
            ) and
            self.root_url != '/'
        ):
            page_loaders = [FilePageLoader(root_path)]
        else:
            root_path = url_to_path(self.root_url, has_children=True)
            if not os.path.exists(
                os.path.join(app_settings.SYNC_DIRECTORY, root_path)
            ):
                self.error(u'Root page "{0}" not found!'.format(self.root_url))
            page_loaders = []
            walk_start = os.path.join(
                app_settings.SYNC_DIRECTORY, os.path.dirname(root_path)
            )
            if walk_start.endswith('/'):
                walk_start = walk_start[:-1]
            for root, dirs, files in os.walk(walk_start):
                for file_name in files:
                    if file_name.startswith('.'):
                        continue
                    absolute_path = os.path.join(root, file_name)
                    relative_path = os.path.relpath(
                        absolute_path, app_settings.SYNC_DIRECTORY
                    )
                    page_loaders.append(FilePageLoader(relative_path))
        return page_loaders

    def load_existing_files(self, summary):
        """Loads pages from existing files"""
        valid_pks = set()
        page_loaders = self.page_loaders()
        for page_loader in page_loaders:
            status = page_loader.status()
            if status != SyncStatus.NO_CHANGES:
                confirm_msgs, confirm_opts = [], {}
                if status == SyncStatus.ADDED:
                    page_is_dirty = False
                    confirm_msgs.append(
                        u"Page created: {0}".format(page_loader.url())
                    )
                else:
                    page_is_dirty = page_loader.page().is_dirty
                    confirm_msgs.append(
                        u"Page modified: {0}".format(page_loader.url())
                    )
                    confirm_opts['diff'] = page_loader.diff()
                    if page_is_dirty:
                        confirm_msgs.append(u"WARNING: Modified in Admin!")
                if page_is_dirty and not self.force:
                    apply_change = False
                else:
                    apply_change = self.confirm(*confirm_msgs, **confirm_opts)
            else:
                page_is_dirty = False
                apply_change = True
            if not apply_change:
                status += SyncStatus.SKIPPED
            elif page_is_dirty:
                status += SyncStatus.FORCED
            self.log_status(status, page_loader.url())
            if apply_change and not self.dry_run:
                page_loader.save()
            # Update the set of valid PKs (not to be deleted)
            loaded_page = page_loader.page()
            if loaded_page:
                valid_pks.add(loaded_page.pk)
            summary[status] += 1
        return valid_pks

    def delete_unused_pages(self, valid_pks, summary):
        """Removes unused pages only in subtree of root"""
        pages_to_delete = Page.objects.filter(
            url__startswith=self.root_url
        ).exclude(
            pk__in=valid_pks
        )
        for page in pages_to_delete:
            status = SyncStatus.DELETED
            confirm_msgs = [
                u"Page to be deleted: {0} ({1})".format(page.url, page.pk)
            ]
            if page.is_dirty:
                confirm_msgs.append(u"WARNING: Modified in Admin!")
            if page.is_dirty and not self.force:
                apply_change = False
            else:
                apply_change = self.confirm(*confirm_msgs)
            if not apply_change:
                status += SyncStatus.SKIPPED
            elif page.is_dirty:
                status += SyncStatus.FORCED
            self.log_status(status, page.url)
            if apply_change and not self.dry_run:
                page.delete()
            summary[status] += 1

    def run(self):
        """Performs the operation"""
        summary = collections.defaultdict(int)
        valid_pks = self.load_existing_files(summary)
        self.delete_unused_pages(valid_pks, summary)
        if self.dry_run:
            self.log(
                u"WARNING: Number of deleted records may be inadequate "
                u"when --dry-run is used!"
            )
        self.summary(summary)
