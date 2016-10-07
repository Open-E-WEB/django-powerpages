# -*- coding: utf-8 -*-

from django.dispatch import Signal


page_edited = Signal(providing_args=['page', 'user', 'created'])
