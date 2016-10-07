# -*- coding=utf-8 -*-

from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class PowerPagesConfig(AppConfig):
    name = 'powerpages'
    verbose_name = _('CMS')

    def ready(self):
        """Register website data and add default templatetags"""
        # Autodiscover website PageProcessors
        from powerpages import autodiscover
        autodiscover()
