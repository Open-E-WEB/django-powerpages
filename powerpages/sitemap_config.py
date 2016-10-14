# -*- coding: utf-8 -*-

from django.core.urlresolvers import reverse

from powerpages.settings import app_settings


class NamedURL(object):
    """Wrapper over named URLs to provide lazy reversion"""

    def __init__(self, name, *args, **kwargs):
        self.name = name
        self.args = args
        self.kwargs = kwargs

    def reverse_url(self):
        """Reverses given URL"""
        return reverse(self.name, args=self.args, kwargs=self.kwargs)


class Sitemap(object):
    """Single sitemap configuration class."""

    protocol = None
    domain = None
    changefreq = None
    priority = None

    class URL(object):
        """Single sitemap URL"""

        def __init__(self, location, lastmod=None, changefreq=None,
                     priority=None):
            self.location = location
            self.lastmod = lastmod
            self.changefreq = changefreq
            self.priority = priority

    def __init__(self, request=None):
        if self.protocol is None:
            if app_settings.SITEMAP_PROTOCOL:
                self.protocol = app_settings.SITEMAP_PROTOCOL
            elif request:
                self.protocol = 'https' if request.is_secure() else 'http'
            else:
                self.protocol = 'http'
        if self.domain is None:
            if app_settings.SITEMAP_DOMAIN:
                self.domain = app_settings.SITEMAP_DOMAIN
            elif request:
                self.domain = request.get_host()
            else:
                self.domain = 'localhost'
        if self.changefreq is None:
            self.changefreq = app_settings.SITEMAP_DEFAULT_CHANGEFREQ
        if self.priority is None:
            self.priority = app_settings.SITEMAP_DEFAULT_PRIORITY

    def get_items(self):
        """To be overriden when dynamic items needed"""
        return getattr(self, 'items', ())

    def get_urls(self):
        """Generator over all URL instances provided by this sitemap."""
        for conf_item in self.get_items():
            url_kwargs = conf_item.copy()
            raw_location = url_kwargs.pop('location')
            if hasattr(raw_location, 'reverse_url'):
                raw_location = raw_location.reverse_url()
            location = "%s://%s%s" % (
                self.protocol, self.domain, raw_location
            )
            if 'changefreq' not in url_kwargs and self.changefreq:
                url_kwargs['changefreq'] = self.changefreq
            if 'priority' not in url_kwargs and self.priority:
                url_kwargs['priority'] = self.priority
            url = self.URL(location, **url_kwargs)
            yield url


class ModelSitemap(Sitemap):
    """
    Single sitemap configuration class with items based on model
    instances from given queryset.
    Subclasses have to contain `queryset` attribute.
    """

    def get_items(self):
        for obj in self.queryset.all():  # working on queryset copy
            yield self.from_instance(obj)

    def get_instance_location(self, obj):
        """Retrieves URL of particular model instance."""
        return obj.get_absolute_url()

    def from_instance(self, obj):
        """Converts model instance into dictionary."""
        return {
            'location': self.get_instance_location(obj),
        }


class URLSet(object):
    """Container for Sitemaps"""

    def __init__(self):
        self.sitemaps = set()

    def add(self, sitemap):
        self.sitemaps.add(sitemap)

    def urls(self, request=None):
        """Generator over all URL instances provided by all sitemaps."""
        for sitemap_class in self.sitemaps:
            sitemap = sitemap_class(request=request)
            for url in sitemap.get_urls():
                yield url


sitemaps = URLSet()
