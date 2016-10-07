# -*- coding: utf-8 -*-

from optparse import make_option

from django.core.management.base import BaseCommand, CommandError


class BaseDumpLoadCommand(BaseCommand):
    """Base class for website dump / load commands"""

    option_list = BaseCommand.option_list + (
        make_option(
            '--dry-run',
            action='store_true',
            default=False,
            dest='dry_run',
            help=(
                "Performs all operations without changing anything in the "
                "file system / database."
            )
        ),
        make_option(
            '--no-interactive',
            action='store_true',
            default=False,
            dest='no_interactive',
            help=(
                "Do not ask user to confirm changes in file system / database."
            )
        ),
        make_option(
            '--quiet',
            action='store_true',
            default=False,
            dest='quiet',
            help=(
                "Limits displayed output to summary of changes"
            )
        ),
        make_option(
            '-f', '--force',
            action='store_true',
            default=False,
            dest='force',
            help="Allows to overwite changes made in Admin."
        ),
        make_option(
            '--git-add',
            action='store_true',
            default=False,
            dest='git_add',
            help="Add created / removed files to GIT."
        )
    )

    operation_class = None  # must be set in subclass

    def handle(self, root_url='/', **options):
        """Performs the operation"""
        operation = self.operation_class(
            root_url=root_url, error_class=CommandError,
            stdout=self.stdout, stderr=self.stderr, **options
        )
        return operation.run()
