# -*- coding: utf-8 -*-

import datetime

from powerpages import sitemap_config
from powerpages.models import Page

VALID_CHANGEFREQ = (
    '', 'always', 'hourly', 'daily', 'weekly', 'monthly', 'yearly', 'never',
)


class PageSitemap(sitemap_config.Sitemap):
    """Sitemap configuration for powerpages.Page model"""

    def get_items(self):
        for page in Page.objects.all():
            if not page.is_accessible():
                continue  # No sitemap for inaccessible Pages
            page_processor = page.get_page_processor()
            sitemap_settings = page_processor.config.get('sitemap')
            conf_item = {}
            if isinstance(sitemap_settings, dict):
                if 'lastmod' in sitemap_settings:
                    try:
                        lastmod = datetime.datetime.strptime(
                            unicode(sitemap_settings['lastmod']), '%Y-%m-%d'
                        )
                    except ValueError:
                        pass
                    else:
                        conf_item['lastmod'] = lastmod
                if 'priority' in sitemap_settings:
                    try:
                        priority = float(sitemap_settings['priority'])
                    except (ValueError, TypeError):
                        pass
                    else:
                        conf_item['priority'] = priority
                if 'changefreq' in sitemap_settings:
                    changefreq = sitemap_settings['changefreq']
                    if changefreq in VALID_CHANGEFREQ:
                        conf_item['changefreq'] = changefreq
            if sitemap_settings is not None and not sitemap_settings:
                # sitemap settings defined, but false in boolean context
                continue
            conf_item['location'] = page.url
            if 'lastmod' not in conf_item:
                conf_item['lastmod'] = page.changed_at
            yield conf_item


sitemap_config.sitemaps.add(PageSitemap)
