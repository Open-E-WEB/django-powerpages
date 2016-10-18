# -*- coding: utf-8 -*-

from __future__ import unicode_literals


def context_processor(request):
    return {
        'magic_number': 42
    }
