# -*- coding: utf-8 -*-

from django import template


register = template.Library()


@register.simple_tag
def get_magic_number():
    return '42'
