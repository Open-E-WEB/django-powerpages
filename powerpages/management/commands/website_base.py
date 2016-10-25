# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from optparse import make_option

from django.core.management.base import BaseCommand, CommandError


class BaseDumpLoadCommand(BaseCommand):
    """Base class for website dump / load commands"""

    operation_class = None  # must be set in subclass

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            default=False,
            dest='dry_run',
            help=(
                "Performs all operations without changing anything in the "
                "file system / database."
            )
        ),
        parser.add_argument(
            '--no-interactive',
            action='store_true',
            default=False,
            dest='no_interactive',
            help=(
                "Do not ask user to confirm changes in file system / database."
            )
        ),
        parser.add_argument(
            '--quiet',
            action='store_true',
            default=False,
            dest='quiet',
            help=(
                "Limits displayed output to summary of changes"
            )
        ),
        parser.add_argument(
            '-f', '--force',
            action='store_true',
            default=False,
            dest='force',
            help="Allows to overwite changes made in Admin."
        ),
        parser.add_argument(
            '--git-add',
            action='store_true',
            default=False,
            dest='git_add',
            help="Add created / removed files to GIT."
        )

    def handle(self, root_url='/', stdout=None, stderr=None, **options):
        """Performs the operation"""
        operation = self.operation_class(
            root_url=root_url, error_class=CommandError,
            stdout=self.stdout, stderr=self.stderr, **options
        )
        return operation.run()
