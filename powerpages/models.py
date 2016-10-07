# -*- coding: utf-8 -*-

from django.core.cache import cache
from django.dispatch import receiver
from django.db import models

from powerpages.settings import app_settings
from powerpages.utils.attribute_cache import cache_result_on
from powerpages.dbfields import (
    PageProcessorField, PageProcessorConfigField
)
from powerpages import cachekeys


# Helpers:

class PageURLCache(object):
    """Helps to retrieve Page URL by alias using cache"""

    @staticmethod
    def refresh():
        """
        Build dictionary with relation alias <-> url for regular pages
        so they can be faster accessible from other places
        """
        alias_to_url = dict(
            Page.objects.filter(alias__isnull=False)
                        .values_list('alias', 'url')
        )
        cache.set(
            cachekeys.URL_LIST_CACHE, alias_to_url, app_settings.CACHE_SECONDS
        )
        return alias_to_url

    @staticmethod
    def url_by_alias(page_alias):
        """
        Try to read page url from cache. If it's missing then try to find
        matching page that could be missing in cache. If page is found
        then refresh all url list since it's too old.
        If no matching is found then return None so we can throw any
        exception we want in other places
        """
        if page_alias:
            url_to_alias = cache.get(cachekeys.URL_LIST_CACHE)
            if url_to_alias is None:
                url_to_alias = PageURLCache.refresh()
            url = url_to_alias.get(page_alias)
        else:
            url = None
        return url


# Models:

class Page(models.Model):
    """Webpages and templates."""

    class Meta:
        verbose_name = u"Page"
        verbose_name_plural = u"Pages"
        ordering = ('url',)

    # Identity:
    url = models.CharField(
        verbose_name=u"URL", max_length=1024, null=True
    )
    alias = models.CharField(
        verbose_name=u"Alias", max_length=120, db_index=True,
        null=True, blank=True,
        help_text=u"Unique human-readable codename of page, "
                  u"used in template tags"
    )
    # Meta tags:
    title = models.CharField(
        max_length=512, verbose_name=u"Title", blank=True, default=""
    )
    description = models.TextField(
        verbose_name=u"Description", blank=True, default=""
    )
    keywords = models.TextField(
        verbose_name=u"Keywords", blank=True, default=""
    )
    # Template:
    template = models.TextField(
        verbose_name=u"Template",
        blank=True, default='',
        help_text=u"Parent's template is used as the base template for "
                  u"current page."
    )
    # Page processing
    page_processor = PageProcessorField(
        verbose_name=u"Page Processor", max_length=128,
        default='powerpages.DefaultPageProcessor',
        help_text=u"Python program used to render this page."
    )
    page_processor_config = PageProcessorConfigField(
        verbose_name=u"Page Processor Config", null=True, blank=True,
        help_text=u"Advanced page configuration options as YAML config."
    )
    # Indicates objects saved in Admin:
    is_dirty = models.BooleanField(default=False, editable=False)
    # Change info fields:
    added_at = models.DateTimeField(
        verbose_name=u"Added at", auto_now_add=True
    )
    changed_at = models.DateTimeField(
        verbose_name=u"Changed at", auto_now=True
    )

    def __unicode__(self):
        """URL"""
        return self.url

    def get_absolute_url(self):
        """URL"""
        return self.url

    def parent_url(self):
        """Generates parent Page URL"""
        url = self.url
        if url.endswith('/'):
            url = url[:-1]
        parent_url = url.rsplit('/', 1)[0] + '/'
        return parent_url if self.url != parent_url else ''

    @cache_result_on('_parent')
    def parent(self):
        """Parent Page based on URL"""
        parent_url = self.parent_url()
        if parent_url:
            parent_page = Page.objects.filter(url=parent_url).first()
        else:
            parent_page = None
        return parent_page

    def children(self):
        """Direct descendant Pages based on URL"""
        url_regex = '^{url}[^/]+/?$'.format(url=self.url)
        return Page.objects.filter(url__regex=url_regex)

    def descendants(self):
        """Direct and indirect descendant Pages based on URL"""
        url = self.url
        return Page.objects.filter(url__startswith=url).exclude(url=url)

    def is_accessible(self):
        """Determines if Page can be accessed on URL"""
        page_processor = self.get_page_processor()
        return page_processor and page_processor.is_accessible()

    @models.permalink
    def get_admin_url(self):
        """URL of Page edition view in Admin"""
        return 'admin:powerpages_page_change', [self.pk]


# Signal Receivers:


@receiver(models.signals.post_save, sender=Page)
def page_changed(sender, **kwargs):
    """
    post_save receiver for Page model:
    * clears Page-related cache keys,
    * refresh mappings: alias <-> page real url,
    * clears cache keys related to PageChanges.
    """
    page = kwargs['instance']
    cache_key = cachekeys.template_source(page.pk)
    cache.delete(cache_key)
    PageURLCache.refresh()
