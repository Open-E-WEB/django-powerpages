# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django import template


register = template.Library()


@register.simple_tag
def get_magic_number():
    return '42'
