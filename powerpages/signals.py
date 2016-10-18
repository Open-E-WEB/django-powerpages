# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.dispatch import Signal


page_edited = Signal(providing_args=['page', 'user', 'created'])
