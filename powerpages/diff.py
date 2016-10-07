# -*- coding: utf-8 -*-

import difflib
from cStringIO import StringIO

from django.utils.html import escape


class Diff(object):
    """Text diff"""

    CHANGE_CLASSES = {
        '+': "diff-added",
        '-': "diff-removed",
        ' ': None
    }

    def __init__(self):
        self.left_side = None
        self.right_side = None

    def left(self, content, created_at):
        """Creates DiffSide objects and sets it as left side"""
        self.left_side = DiffSide("Old", content, created_at)

    def right(self, content, created_at):
        """Creates DiffSide objects and sets it as right side"""
        self.right_side = DiffSide("New", content, created_at)

    def html_diff(self):
        """Creates unified diff as HTML"""
        if not (self.left_side and self.right_side):
            raise RuntimeError(
                "Both sides of diff must be set before calling html_diff"
            )
        diff_gen = difflib.unified_diff(
            self.left_side.content, self.right_side.content,
            self.left_side.name, self.right_side.name,
            self.left_side.datetime_as_string(),
            self.right_side.datetime_as_string(),
            n=50
        )
        output = StringIO()
        for line in diff_gen:
            if len(line) == 2:
                change, char = line
                change_class = self.CHANGE_CLASSES[change]
                if change_class:
                    marked_line = u'<span class="%s">%s</span>' % (
                        change_class, escape(char)
                    )
                else:
                    marked_line = escape(char)
            else:
                marked_line = u'\n<span class="diff-info">%s</span>\n' % (
                    escape(line[:-2]),
                )
            output.write(marked_line.encode('utf-8'))
        return output.getvalue()


class DiffSide(object):
    """One side of text diff"""

    def __init__(self, name, content, created_at):
        self.name = name
        self.content = content
        self.created_at = created_at

    def datetime_as_string(self):
        """Converts creation datetime to ISO 8601 string."""
        return self.created_at.strftime("%Y-%m-%d %H:%M:%S")
