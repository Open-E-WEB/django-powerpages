# -*- coding: utf-8 -*-

import json
import hashlib


URL_LIST_CACHE = "website:url_list"
SITEMAP_CONTENT = "website:sitemap"


def get_cache_name(prefix, name):
    """
    Cache name constructor. Uses the same methods as django cache system
    Examples:
    *) prefix=profile.cache, name=<requestuser.id>
    *) prefix=template.cache.sidebar, name=<requestuser.id>
    """
    return u'{0}.{1}'.format(
        prefix, hashlib.md5(unicode(name).encode('utf-8')).hexdigest()
    )


def template_source(page_pk):
    """Create cache key for page template"""
    return 'website:template:%s' % page_pk


def rendered_source_for_user(page_pk, user_id):
    """Create cache key for rendered page source based on current user"""
    return 'website:rendered_source_user:%s:%s' % (page_pk, user_id)


def rendered_source_for_lang(page_pk, lang):
    """Create cache key for rendered page source based on current language"""
    return 'website:rendered_source_lang:%s:%s' % (page_pk, lang)


def url_cache(name, *args, **kwargs):
    """
    Creates cache key for url of CMS page or standard Django URL
    based on hashed serialized name with optional *args and **kwargs
    """
    serialized_url = json.dumps([name, args, kwargs], sort_keys=True)
    return get_cache_name("website:urls", serialized_url)
