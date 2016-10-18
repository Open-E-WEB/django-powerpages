# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json
import hashlib

from django.utils import six


URL_LIST_CACHE = 'powerpages:url_list'
SITEMAP_CONTENT = 'powerpages:sitemap'


def get_cache_name(prefix, name):
    """
    Cache name constructor. Uses the same methods as django cache system
    Examples:
    *) prefix=profile.cache, name=<requestuser.id>
    *) prefix=template.cache.sidebar, name=<requestuser.id>
    """
    return '{0}.{1}'.format(
        prefix, hashlib.md5(six.text_type(name).encode('utf-8')).hexdigest()
    )


def template_source(page_pk):
    """Create cache key for page template"""
    return 'powerpages:template:{0}'.format(page_pk)


def rendered_source_for_user(page_pk, user_id):
    """Create cache key for rendered page source based on current user"""
    return 'powerpages:rendered_source_user:{0}:{1}'.format(page_pk, user_id)


def rendered_source_for_lang(page_pk, lang):
    """Create cache key for rendered page source based on current language"""
    return 'powerpages:rendered_source_lang:{0}:{1}'.format(page_pk, lang)


def url_cache(name, *args, **kwargs):
    """
    Creates cache key for url of CMS page or standard Django URL
    based on hashed serialized name with optional *args and **kwargs
    """
    serialized_url = json.dumps([name, args, kwargs], sort_keys=True)
    return get_cache_name('powerpages:urls', serialized_url)
