# -*- coding=utf-8 -*-

import copy
from importlib import import_module


default_app_config = 'powerpages.apps.PowerPagesConfig'


def autodiscover():
    """
    Auto-discover INSTALLED_APPS modules:
    * page_processors.py to fill out the default PageProcessorRegistry,
    * sitemap.py to populate sitemap_config.sitemaps.
    Inspired by django.contrib.admin.autodiscover.
    """

    from django.conf import settings
    from django.utils.module_loading import module_has_submodule
    from powerpages import page_processor_registry

    for app in settings.INSTALLED_APPS:
        mod = import_module(app)
        # page processors:
        try:
            before_import_registry = copy.copy(
                page_processor_registry.registry.registry
            )
            import_module('%s.page_processors' % app)
        except:
            page_processor_registry.registry.registry = before_import_registry
            if module_has_submodule(mod, 'page_processors'):
                raise
        # sitemaps:
        try:
            import_module('%s.sitemap' % app)
        except:
            if module_has_submodule(mod, 'sitemap'):
                raise
