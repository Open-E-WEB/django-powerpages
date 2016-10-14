# -*- coding: utf-8 -*-

"""Bunch of tools to provide nice console output."""

import sys
import math
import re
import datetime
import itertools
import threading


_thread_locals = threading.local()


def total_seconds(time_delta):
    """
    Total number of seconds if given datetime.timedelta object.
    Required due to missing datetime.timedelta.total_seconds() in py26.
    """
    return (
        time_delta.days * 24 * 60 * 60 +
        time_delta.seconds +
        time_delta.microseconds / 1000000.0
    )


class BaseStyle(object):
    """Allows to apply colors to texts printed on console"""

    RESET = ''

    @classmethod
    def style(cls, option, text):
        """Applies styling option to given text"""
        return u"{start}{text}{reset}".format(
            start=getattr(cls, option), text=text, reset=cls.RESET
        )


class ForegroundColor(BaseStyle):
    """Container for foreground console colors (ANSI)"""
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    RESET = '\033[39m'


class BackgroundColor(BaseStyle):
    """Container for background console colors (ANSI)"""
    BLACK = '\033[40m'
    RED = '\033[41m'
    GREEN = '\033[42m'
    YELLOW = '\033[43m'
    BLUE = '\033[44m'
    MAGENTA = '\033[45m'
    CYAN = '\033[46m'
    WHITE = '\033[47m'
    RESET = '\033[49m'


class Font(BaseStyle):
    """Container for font styling (ANSI)"""
    BOLD = '\033[2m'
    RESET = '\033[0m'


class Console(object):
    """Console writing utilities"""

    def __init__(self, stream=None):
        if stream is None:
            stream = sys.stdout
        self.stream = stream

    def format(self, text, template=u"{text:<{min_length}}",
               bg_color=None, fg_color=None, font=None, min_length=80):
        """Formats the output string"""
        if bg_color:
            text = BackgroundColor.style(bg_color, text)
        if fg_color:
            text = ForegroundColor.style(fg_color, text)
        if font:
            text = Font.style(font, text)
        return template.format(text=text, min_length=min_length)

    def write(self, text):
        """Writes text to the output stream"""
        self.stream.write(text)
        self.stream.flush()

    def same_line(self, text, **format_options):
        """Writes text in the same line"""
        format_options['template'] = u'\r{text:<{min_length}}'
        self.write(self.format(text, **format_options))

    def new_line(self, text,  **format_options):
        """Writes text in the new line"""
        format_options['template'] = u'\r{text:<{min_length}}\n'
        self.write(self.format(text, **format_options))

    # Shortcuts:

    def info(self, message):
        """Writes non-formatted line of text into output stream"""
        self.new_line(message)

    def warning(self, message):
        """Writes yellow line of text into output stream"""
        self.new_line(message, fg_color='YELLOW')

    def failure(self, message):
        """Writes red line of text into output stream"""
        self.new_line(message, fg_color='RED')

    def success(self, message):
        """Writes green line of text into output stream"""
        self.new_line(message, fg_color='GREEN')


class ProgressBar(object):
    """Console progress bar"""
    TEMPLATE = '$progress $percent ($current / $total) $eta $screw'
    PROGRESS_TEMPLATE = '[{bricks: <{num_bricks}}]'
    PROGRESS_BRICK = '#'
    PROGRESS_NUM_BRICKS = 20
    PERCENT_TEMPLATE = '{ratio:7.2%}'
    CURRENT_TEMPLATE = '{current:{num_digits}}'
    TOTAL_TEMPLATE = '{total:{num_digits}}'
    ETA_TEMPLATE = 'ETA: {eta}'  # Estimated Time of Arrival
    SCREW_TEMPLATE = '{screw}'  # rotating ASCII chars
    REFRESH_EVERY = 10

    def __init__(self, console_or_stream=None, **kwargs):
        if isinstance(console_or_stream, Console):
            self.console = console_or_stream
        else:
            self.console = Console(console_or_stream)
        self.template = kwargs.get('template', self.TEMPLATE)
        self.progress_template = \
            kwargs.get('progress_template', self.PROGRESS_TEMPLATE)
        self.progress_brick = kwargs.get('progress_brick', self.PROGRESS_BRICK)
        self.progress_num_bricks = \
            kwargs.get('progress_num_bricks', self.PROGRESS_NUM_BRICKS)
        self.percent_template = \
            kwargs.get('percent_template', self.PERCENT_TEMPLATE)
        self.current_template = \
            kwargs.get('current_template', self.CURRENT_TEMPLATE)
        self.total_template = \
            kwargs.get('total_template', self.TOTAL_TEMPLATE)
        self.eta_template = kwargs.get('eta_template', self.ETA_TEMPLATE)
        self.screw_template = kwargs.get('screw_template', self.SCREW_TEMPLATE)
        self.refresh_every = kwargs.get('refresh_every', self.REFRESH_EVERY)
        self.line_template = self.build_line_template()
        self.start_datetime = None
        self.screw_cycle = itertools.cycle(('|', '/', '-', '\\'))

    def build_line_template(self):
        """Creates line template from other settings"""
        replacements = {
            'progress': self.progress_template,
            'percent': self.percent_template,
            'current': self.current_template,
            'total': self.total_template,
            'eta': self.eta_template,
            'screw': self.screw_template
        }

        def replace(matchobj):
            name = matchobj.group(0)[1:]
            if name not in replacements:
                raise ValueError(
                    u'Unknown ProgressBar.template variable ${0}'.format(name)
                )
            return replacements[name]

        return re.sub('(\$\w+)', replace, self.template)

    def start_timing(self):
        """Manually sets operation's start datetime"""
        self.start_datetime = datetime.datetime.now()

    def end_timing(self):
        """Manually unsets operation's start datetime"""
        self.start_datetime = None

    def refresh_needed(self, current, total):
        """Decides if progress bar should be updated"""
        return current == total or not current % self.refresh_every

    def new_line_needed(self, current, total):
        """Decides if progress bar should write output in new line"""
        return current == total

    def format_message(self, current, total):
        """Creates message to be written on console"""
        if total:
            ratio = float(current) / total
            filled_bricks = int((ratio + 0.05) * self.progress_num_bricks)
            num_digits = int(math.log10(total))
        else:
            ratio = 1.0
            filled_bricks = self.progress_num_bricks
            num_digits = 1
        last_step = total == current
        if last_step:
            eta = datetime.timedelta(0)
        elif ratio and self.start_datetime:
            total_seconds_ = total_seconds(
                datetime.datetime.now() - self.start_datetime
            )
            eta = datetime.timedelta(
                seconds=total_seconds_ / ratio - total_seconds_
            )
        else:
            eta = '?'
        screw = " " if last_step else self.screw_cycle.next()
        return self.line_template.format(
            bricks=self.progress_brick * filled_bricks,
            num_bricks=self.progress_num_bricks,
            ratio=ratio,
            current=current,
            total=total,
            num_digits=num_digits,
            eta=eta,
            screw=screw
        )

    def progress(self, current, total):
        """Updates progress bar with status information"""
        if self.refresh_needed(current, total):
            message = self.format_message(current, total)
            if self.new_line_needed(current, total):
                self.console.new_line(message)
            else:
                self.console.same_line(message)


# Shortcut methods using thread-local ProgressBar and Console instance


def show_progress(current, total=None):
    """Updates progress bar with status information"""
    is_start = current in (0, 1)
    if not hasattr(_thread_locals, 'progress_bar') or is_start:
        _thread_locals.progress_bar = ProgressBar()
    progress_bar = _thread_locals.progress_bar
    if is_start:
        progress_bar.start_timing()
    progress_bar.progress(current, total)


def show_info(message):
    """Writes non-formatted NEW line of text into output stream"""
    if not hasattr(_thread_locals, 'console'):
        _thread_locals.console = Console()
    console = _thread_locals.console
    console.info(message)
