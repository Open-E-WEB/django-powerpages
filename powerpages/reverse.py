# -*- coding: utf-8 -*-

from django.core.cache import cache
from django.core.urlresolvers import reverse

from powerpages.cachekeys import url_cache
from powerpages.models import Page


def reverse_url(name, *args, **kwargs):
    """
    Looks for entry matching given name and optional parameters in cache
    and if it's not present tries to find CMS Page with given name,
    then tries to reverse given name with params to static URL.
    Updates the cache if result has been found and returns URL
    or throws exception.
    """
    # try to get url from cache
    url_key = url_cache(name, *args, **kwargs)
    url = cache.get(url_key, None)

    # try to find CMS Page only if optional params are omitted
    if not url and not args and not kwargs:
        try:
            page = Page.objects.get(alias=name)
            url = page.url
        except Page.DoesNotExist:
            pass

    # try to reverse url by the given name with arguments
    if not url:
        # reverse will throw exception if it fails
        url = reverse(name, args=args, kwargs=kwargs)

    cache.set(url_key, url)

    return url
