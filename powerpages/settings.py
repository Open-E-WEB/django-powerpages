# -*- coding: utf-8 -*-

from django.conf import settings
from django.test.signals import setting_changed


DEFAULTS = {
    'CACHE_SECONDS': 60 * 60,  # 1 hour
    'SYNC_DIRECTORY': None,
    'TAG_LIBRARIES': (),
    'SITEMAP_PROTOCOL': None,
    'SITEMAP_DOMAIN': None,
    'SITEMAP_DEFAULT_CHANGEFREQ': None,
    'SITEMAP_DEFAULT_PRIORITY': None,
}


class AppSettings(object):
    """
    A settings object that allows app settings to be accessed by properties.
    Inspired by solution from Django REST Framework.
    """

    def __init__(self, user_settings=None, defaults=None):
        self.user_settings = user_settings
        self.defaults = defaults or DEFAULTS
        self.cache = {}

    def __getattr__(self, attr):
        if attr not in self.defaults:
            raise AttributeError('Invalid app setting "{0}"'.format(attr))
        try:
            value = self.cache[attr]
        except KeyError:
            if self.user_settings is None:
                self.user_settings = getattr(settings, 'POWER_PAGES', {})
            try:
                value = self.user_settings[attr]
            except KeyError:
                value = self.defaults[attr]
            self.cache[attr] = value
        return value


app_settings = AppSettings()


def reload_app_settings(*args, **kwargs):
    if kwargs['setting'] == 'POWER_PAGES':
        app_settings.user_settings = kwargs['value']
        app_settings.cache = {}


setting_changed.connect(reload_app_settings)
