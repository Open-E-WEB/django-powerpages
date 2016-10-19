# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.test import TestCase
from django.utils.six import StringIO

from powerpages.utils.console import Console, ProgressBar


class ConsoleTestCase(TestCase):

    maxDiff = None

    def test_format_default(self):
        console = Console()
        output = console.format('The quick brown fox jumps over the lazy dog')
        self.assertEqual(
            repr(output),
            repr('The quick brown fox jumps over the lazy dog' + ' ' * 37)
        )

    def test_format_fg_color(self):
        console = Console()
        output = console.format(
            'The quick brown fox jumps over the lazy dog', fg_color='RED'
        )
        self.assertEqual(
            repr(output),
            repr(
                '\x1b[31m'
                'The quick brown fox jumps over the lazy dog'
                '\x1b[39m' +
                ' ' * 27
            )
        )

    def test_format_many_options(self):
        console = Console()
        output = console.format(
            'The quick brown fox jumps over the lazy dog',
            fg_color='RED', bg_color='YELLOW', font='BOLD', min_length=10
        )
        self.assertEqual(
            repr(output),
            repr(
                '\x1b[2m\x1b[31m\x1b[43m'
                'The quick brown fox jumps over the lazy dog'
                '\x1b[49m\x1b[39m\x1b[0m'
            )
        )

    def test_write(self):
        stream = StringIO()
        console = Console(stream)
        console.write('The quick brown fox jumps over the lazy dog')
        output = stream.getvalue()
        self.assertEqual(
            repr(output),
            repr('The quick brown fox jumps over the lazy dog')
        )

    def test_new_line(self):
        stream = StringIO()
        console = Console(stream)
        console.new_line('The quick brown fox jumps over the lazy dog')
        output = stream.getvalue()
        self.assertEqual(
            repr(output),
            repr(
                '\r'
                'The quick brown fox jumps over the lazy dog' + ' ' * 37 +
                '\n'
            )
        )

    def test_same_line(self):
        stream = StringIO()
        console = Console(stream)
        console.same_line('The quick brown fox jumps over the lazy dog')
        output = stream.getvalue()
        self.assertEqual(
            repr(output),
            repr(
                '\r'
                'The quick brown fox jumps over the lazy dog' + ' ' * 37
            )
        )

    def test_info(self):
        stream = StringIO()
        console = Console(stream)
        console.info('The quick brown fox jumps over the lazy dog')
        output = stream.getvalue()
        self.assertEqual(
            repr(output),
            repr(
                '\r'
                'The quick brown fox jumps over the lazy dog' + ' ' * 37 +
                '\n'
            )
        )

    def test_warning(self):
        stream = StringIO()
        console = Console(stream)
        console.warning('The quick brown fox jumps over the lazy dog')
        output = stream.getvalue()
        self.assertEqual(
            repr(output),
            repr(
                '\r\x1b[33m'
                'The quick brown fox jumps over the lazy dog'
                '\x1b[39m' + ' ' * 27 + '\n'
            )
        )

    def test_failure(self):
        stream = StringIO()
        console = Console(stream)
        console.failure('The quick brown fox jumps over the lazy dog')
        output = stream.getvalue()
        self.assertEqual(
            repr(output),
            repr(
                '\r\x1b[31m'
                'The quick brown fox jumps over the lazy dog'
                '\x1b[39m' + ' ' * 27 + '\n'
            )
        )

    def test_success(self):
        stream = StringIO()
        console = Console(stream)
        console.success('The quick brown fox jumps over the lazy dog')
        output = stream.getvalue()
        self.assertEqual(
            repr(output),
            repr(
                '\r\x1b[32m'
                'The quick brown fox jumps over the lazy dog'
                '\x1b[39m' + ' ' * 27 + '\n'
            )
        )


class ProgressBarTestCase(TestCase):

    maxDiff = None

    def test_progress_bar_console_no_eta(self):
        stream = StringIO()
        console = Console(stream)
        progress_bar = ProgressBar(console)
        for i in range(1, 51):
            progress_bar.progress(i, 50)
        output = stream.getvalue()
        self.assertEqual(
            [ln.strip() for ln in output.split('\r')],
            [
                '',
                '[#####               ]  20.00% (10 / 50) ETA: ? |',
                '[#########           ]  40.00% (20 / 50) ETA: ? /',
                '[#############       ]  60.00% (30 / 50) ETA: ? -',
                '[#################   ]  80.00% (40 / 50) ETA: ? \\',
                '[#####################] 100.00% (50 / 50) ETA: 0:00:00'
            ]
        )

    def test_progress_bar_stream_no_eta_custom(self):
        stream = StringIO()
        progress_bar = ProgressBar(
            stream,
            template='$progress $percent ($current / $total)',
            progress_brick='*',
            progress_num_bricks=5
        )
        for i in range(1, 51):
            progress_bar.progress(i, 50)
        output = stream.getvalue()
        self.assertEqual(
            [ln.strip() for ln in output.split('\r')],
            [
                '',
                '[*    ]  20.00% (10 / 50)',
                '[**   ]  40.00% (20 / 50)',
                '[***  ]  60.00% (30 / 50)',
                '[**** ]  80.00% (40 / 50)',
                '[*****] 100.00% (50 / 50)'
            ]
        )