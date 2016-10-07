# -*- coding: utf-8 -*-

from django.template import TemplateDoesNotExist
from django.template.loaders.base import Loader
from django.core.cache import cache

from powerpages.models import Page
from powerpages import cachekeys


class WebsiteLoader(Loader):
    """
    A custom template loader to load Page templates from the database.
    Inspired by https://github.com/jezdez/django-dbtemplates/
    """

    def load_template_source(self, template_name, template_dirs=None):
        """Load templates from powerpages.Page model instances.
        Works only with templates named:
        page/<page_pk>"""
        try:
            namespace, page_pk = template_name.split('/')
        except ValueError:
            pass
        else:
            if namespace == 'page':
                cachekey = cachekeys.template_source(page_pk)
                display_name = "page:%s" % page_pk
                source = cache.get(cachekey)
                if source is None:
                    try:
                        page = Page.objects.get(pk=page_pk)
                    except Page.DoesNotExist:
                        pass
                    else:
                        page_processor = page.get_page_processor()
                        source = page_processor.get_template_source()
                        cache.set(cachekey, source)
                        display_name = "page:%s" % page_pk
                        return source, display_name
                else:
                    return source, display_name
        raise TemplateDoesNotExist(template_name)
